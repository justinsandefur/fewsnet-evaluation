"""Do areas FEWS NET said were being held up by aid fall back when aid is cut?

FEWS NET marks an area "!" when it judges that humanitarian assistance is
keeping the area at least one phase better than it would otherwise be. If that
judgment is right, areas flagged before the 2025 US aid cut should deteriorate
more afterwards than unflagged areas that started in the same phase, and more
so where the US paid for a larger share of the aid.

Units of observation are same-season pairs: an area's classification in a
baseline month and in the same calendar month one or two years later.

  A. FEWS NET's own maps (current situation, Feb/Jun/Oct), by FEWS NET area.
     Ethiopia, which holds a large share of the flags, has no IPC analyses,
     so this is the only version that includes it. FEWS NET scores both ends.
  B. Independent classifications (Cadre Harmonise and IPC), with FEWS NET's
     flags overlaid on each area (area-weighted share of the area flagged in
     the latest FEWS NET map at or before the baseline analysis).

  change = b flag + d flag x exposed + t flag x exposed x US share
           + flag x US share + FE(country x baseline month x horizon x baseline phase)

exposed = the later classification falls in 2025 or after (baseline before
2025). Pairs that end before 2025 are placebos: they show how flagged areas
normally evolve. US share = US share of the country's humanitarian funding in
2021-23 (FTS). Standard errors clustered by country, with wild cluster
bootstrap p-values (few clusters).

Outputs: output/tables/flag_release_*.csv, output/figures/flag_release.pdf
"""
import importlib.util
import json
import textwrap
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DID = load("did", "25_slope_did.py")
RAIN = load("rain", "24_area_rainfall.py")
IV = load("iv", "15_instrument.py")
EXPOSED_FROM = pd.Period("2025-01", "M")


def us_share():
    """US share of humanitarian funding to each recipient, 2021-23 (FTS)."""
    _, _, f, _ = IV.load()
    f = f[f.month.dt.year.between(2021, 2023)]
    us = f.donor.str.startswith("United States")
    return (f[us].groupby("iso3").amount_usd.sum() / f.groupby("iso3").amount_usd.sum()).rename("us_share")


def fews_maps():
    c = pd.read_parquet(INP / "fewsnet" / "classifications.parquet")
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    cs = c[c.scenario == "CS"]
    n = cs.groupby("report_month").size()
    cs = cs[cs.report_month.isin(n[n > 1000].index)]          # full map rounds only
    cs = cs.groupby(["fnid", "report_month"]).agg(phase=("phase", "max"), flag=("assist", "max"),
                                                  cc=("country_code", "first")).reset_index()
    cs["iso3"] = cs.cc.map(dict(zip(codes.iso3166a2, codes.iso3166a3)))
    cs["flag"] = cs.flag.astype(float)
    return cs


def pairs_fews(cs):
    out = []
    for h in [12, 24]:
        later = cs[["fnid", "report_month", "phase"]].copy()
        later["report_month"] = later.report_month - h
        x = cs.merge(later.rename(columns={"phase": "phase1"}), on=["fnid", "report_month"])
        x["h"] = h
        out.append(x)
    x = pd.concat(out)
    x["m1"] = x.report_month + x.h
    x["dphase"] = x.phase1 - x.phase
    x["worse"] = (x.dphase > 0).astype(float)
    x["to4"] = (x.phase1 >= 4).astype(float)
    x["exposed"] = ((x.m1 >= EXPOSED_FROM) & (x.report_month < EXPOSED_FROM)).astype(float)
    x["cell"] = x.iso3 + "_" + x.report_month.astype(str) + "_" + x.h.astype(str) + "_" + x.phase.astype(str)
    x["unit"] = x.fnid
    x["hm"] = x.h
    x = x[x.report_month < EXPOSED_FROM]     # baselines after the cut began would already show its effect
    return x[x.phase.between(2, 3)]          # flags are given almost only to Phase 2 and 3 areas


def overlay_flags(cs, geo, o):
    """Area-weighted share of each outcome area flagged, and FEWS NET phase, by FEWS NET map month."""
    units = gpd.read_file(INP / "fewsnet" / "units.gpkg")[["fnid", "geometry"]].drop_duplicates("fnid")
    units = units[units.fnid.isin(cs.fnid)].to_crs(6933)
    units["fnid_area"] = units.area
    keys = o[["key", "iso3"]].drop_duplicates("key")
    g = geo.merge(keys, on="key").drop_duplicates("key").to_crs(6933)
    g = g[g.iso3.isin(cs.iso3.unique())]
    g["geometry"] = g.geometry.buffer(0)
    units["geometry"] = units.geometry.buffer(0)
    g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])]
    units = units[units.geom_type.isin(["Polygon", "MultiPolygon"])]
    g["key_area"] = g.area
    inter = gpd.overlay(g[["key", "key_area", "geometry"]], units[["fnid", "geometry"]], how="intersection",
                        keep_geom_type=True)
    inter["w"] = inter.area / inter.key_area
    inter = inter[inter.w > 0.01][["key", "fnid", "w"]]
    m = inter.merge(cs[["fnid", "report_month", "flag", "phase"]], on="fnid")
    m["wf"], m["wp"] = m.w * m.flag, m.w * m.phase
    a = m.groupby(["key", "report_month"]).agg(wf=("wf", "sum"), wp=("wp", "sum"), w=("w", "sum")).reset_index()
    a = a[a.w > 0.5]
    a["flag"], a["fews_phase"] = a.wf / a.w, a.wp / a.w
    return a[["key", "report_month", "flag", "fews_phase"]]


def pairs_ipc(o, fl):
    o = o.copy()
    o["q"] = o.month.dt.quarter
    o["year"] = o.month.dt.year
    a = o.groupby(["key", "iso3", "source", "year", "q"]).agg(share3=("share3", "mean"), phase=("phase", "max"),
                                                              month=("month", "max")).reset_index()
    # flag from the latest FEWS NET map at or up to 4 months before the baseline analysis (maps come every
    # 4 months, so before 2025 every analysis has one; a fixed maximum age keeps flag-to-outcome time comparable)
    a = a.sort_values("month")
    fl = fl.sort_values("report_month")
    a["mi"] = a.month.astype("int64")
    fl = fl.assign(mi=fl.report_month.astype("int64"), fmi=fl.report_month.astype("int64"))
    a = pd.merge_asof(a, fl[["key", "mi", "fmi", "flag", "fews_phase"]], on="mi", by="key", direction="backward",
                      tolerance=4)
    a["flag_age"] = a.mi - a.fmi
    out = []
    for h in [1, 2]:
        later = a[["key", "year", "q", "share3", "phase", "month"]].copy()
        later["year"] = later.year - h
        x = a.merge(later.rename(columns={"share3": "share3_1", "phase": "phase1", "month": "m1"}),
                    on=["key", "year", "q"])
        x["h"] = h
        out.append(x)
    x = pd.concat(out).dropna(subset=["flag", "share3", "share3_1"])
    x = x[x.month < EXPOSED_FROM]            # baselines after the cut began would already show its effect
    x["dshare3"] = x.share3_1 - x.share3
    x["dphase"] = x.phase1 - x.phase
    x["worse"] = (x.dphase > 0).astype(float)
    x["exposed"] = ((x.m1 >= EXPOSED_FROM) & (x.month < EXPOSED_FROM)).astype(float)
    x["fp"] = x.fews_phase.round().clip(1, 4).astype(int)
    x["cell"] = (x.iso3 + "_" + x.source + "_" + x.year.astype(str) + "_" + x.q.astype(str) + "_" + x.h.astype(str)
                 + "_" + x.phase.astype(str) + "_" + x.fp.astype(str))
    x["unit"] = x.key
    x["m0"] = x.month
    x["hm"] = 12 * x.h
    return x


def wild_p(d, y, xs, test, fes, reps=999, seed=1):
    """Wild cluster (Rademacher) bootstrap p-value for one coefficient, null imposed."""
    d = d.dropna(subset=[y] + xs).copy()
    for fe in fes:
        d = d[d.groupby(fe)[y].transform("size") > 1]
    w = DID.within(d, [y] + xs, fes)
    X, Y = w[xs].values, w[y].values
    g = pd.factorize(d.iso3)[0]
    G = g.max() + 1
    def tstat(Yv):
        XtXi = np.linalg.pinv(X.T @ X)
        b = XtXi @ X.T @ Yv
        u = Yv - X @ b
        S = np.zeros((G, X.shape[1]))
        np.add.at(S, g, X * u[:, None])
        V = XtXi @ (S.T @ S) @ XtXi * G / (G - 1)
        j = xs.index(test)
        return b[j] / np.sqrt(V[j, j])
    t0 = tstat(Y)
    keep = [i for i, v in enumerate(xs) if v != test]
    Xr = X[:, keep]
    br = np.linalg.lstsq(Xr, Y, rcond=None)[0]
    fit, ur = Xr @ br, Y - Xr @ br
    rng = np.random.default_rng(seed)
    ts = np.array([tstat(fit + ur * rng.choice([-1.0, 1.0], G)[g]) for _ in range(reps)])
    return float((np.abs(ts) >= abs(t0)).mean())


def estimate(x, ys, label, us):
    x = x.copy()
    x["us"] = x.iso3.map(us)
    x["us_c"] = x.us - us.reindex(x.iso3.unique()).mean()
    x["fx"] = x.flag * x.exposed
    x["fu"] = x.flag * x.us_c
    x["fxu"] = x.fx * x.us_c
    rows = []
    for hz, xh in [("12 months", x[x.hm == 12]), ("24 months", x[x.hm == 24]), ("pooled", x)]:
        for y in ys:
            for spec, xs, d in [("flagged x exposed", ["flag", "fx"], xh),
                                ("+ US share", ["flag", "fx", "fu", "fxu"], xh.dropna(subset=["us"]))]:
                if d.fx.sum() == 0:
                    continue
                r, n, G = DID.fe_ols(d, y, xs, ["cell"])
                for t in ["fx", "fxu"]:
                    if t in xs:
                        rows.append({"version": label, "horizon": hz, "outcome": y, "spec": spec, "term": t,
                                     "coef": r.coef[t], "se": r.se[t], "wild_p": wild_p(d, y, xs, t, ["cell"]),
                                     "n": n, "countries": G, "n_flagged_exposed": int((d.fx > 0).sum()),
                                     "flag_gap_unexposed": r.coef["flag"]})
    return pd.DataFrame(rows)


def by_year(x, y):
    """Flagged-minus-unflagged change, by year of the later classification."""
    x = x.copy()
    x["yr"] = x.m1.dt.year
    yrs = sorted(x.yr.unique())
    xs = []
    for t in yrs:
        x[f"f{t}"] = x.flag * (x.yr == t)
        if x[f"f{t}"].sum() > 0:
            xs.append(f"f{t}")
    r, n, G = DID.fe_ols(x, y, xs, ["cell"])
    r["year"] = [int(s[1:]) for s in r.index]
    r["n_flagged"] = [int((x.flag > 0)[x.yr == t].sum()) for t in r.year]
    return r.reset_index(drop=True)


def main():
    us = us_share()
    cs = fews_maps()
    A = pairs_fews(cs)
    print("A pairs", len(A), "flagged", int(A.flag.sum()), "exposed flagged", int((A.flag * A.exposed).sum()))
    print(A[A.exposed == 1].groupby("iso3").agg(n=("flag", "size"), flagged=("flag", "sum")).query("flagged>0"))
    outcomes = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    geo, o = RAIN.area_geometries(outcomes)
    fl = overlay_flags(cs, geo, o)
    B = pairs_ipc(o, fl)
    print("B pairs", len(B), "with any flag", int((B.flag > 0).sum()), "exposed with flag",
          int(((B.flag > 0) & (B.exposed == 1)).sum()))
    print(B[(B.exposed == 1) & (B.flag > 0)].groupby("iso3").size())
    R = pd.concat([estimate(A, ["dphase", "worse", "to4"], "A. FEWS NET's own later maps", us),
                   estimate(B, ["dshare3", "dphase", "worse"], "B. Cadre Harmonise / IPC", us)])
    R.to_csv(TAB / "flag_release.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.round(4).to_string())
    def split(x, y):
        return pd.concat([by_year(x[x.hm == hm], y).assign(hm=hm) for hm in [12, 24]], ignore_index=True)
    ya, yb, ys = split(A, "dphase"), split(B, "dphase"), split(B, "dshare3")
    ya.to_csv(TAB / "flag_release_by_year_fews.csv", index=False)
    yb.to_csv(TAB / "flag_release_by_year_ipc_phase.csv", index=False)
    ys.to_csv(TAB / "flag_release_by_year_ipc_share.csv", index=False)
    for d in [ya, yb, ys]:
        print(d.round(3).to_string())
    # strictest like-for-like: October maps only, 12 months ahead (the only exposed 12-month comparison)
    oc = by_year(A[(A.hm == 12) & (A.report_month.dt.month == 10)], "dphase")
    oc.to_csv(TAB / "flag_release_by_year_fews_oct12.csv", index=False)
    print("October -> October, FEWS NET maps:\n", oc.round(3).to_string())
    # raw means for the exposed cohort: flagged vs unflagged, same baseline phase
    e = A[A.exposed == 1]
    print(e.groupby(["phase", "flag"]).agg(n=("dphase", "size"), dphase=("dphase", "mean"), worse=("worse", "mean")).round(3))
    figure(ya, yb, ys)


def figure(ya, yb, ys):
    fig, ax = plt.subplots(1, 3, figsize=(16, 5.4))
    for a, d, ylab, title in [
        (ax[0], ya, "Extra change in phase, flagged vs unflagged areas\n(same country, map month and starting phase)",
         "A. FEWS NET's own maps (incl. Ethiopia)"),
        (ax[1], yb, "Extra change in area phase,\nflagged vs unflagged areas",
         "B. Cadre Harmonise / IPC: area phase"),
        (ax[2], ys, "Extra change in share of population in Crisis or worse,\nflagged vs unflagged areas",
         "C. Cadre Harmonise / IPC: share in Crisis+")]:
        for hm, off, mk, lab in [(12, -0.17, "o", "12 months later"), (24, 0.17, "s", "24 months later")]:
            dd = d[d.hm == hm]
            for i, r in enumerate(dd.itertuples()):
                c = "#c0392b" if r.year >= 2025 else ("#1f4e79" if hm == 12 else "#6baed6")
                a.errorbar(r.year + off, r.coef, yerr=1.96 * r.se, fmt=mk, color=c, capsize=2, ms=5,
                           label=lab if i == 0 else None)
                a.annotate(f"{r.n_flagged}", (r.year + off, r.coef + 1.96 * r.se), xytext=(0, 2),
                           textcoords="offset points", ha="center", fontsize=6, color="#777")
        a.legend(fontsize=7.5, loc="upper left", frameon=False)
        a.axhline(0, color="#999", lw=0.8)
        a.axvline(2024.5, color="#c0392b", lw=0.8, ls="--")
        a.text(2024.4, a.get_ylim()[0], "US aid cut ", color="#c0392b", fontsize=8, va="bottom", ha="right")
        a.set_xlabel("Year of the later classification")
        a.set_ylabel(ylab, fontsize=9)
        a.set_title(title, loc="left", fontweight="bold", fontsize=10.5)
    fig.suptitle("Did areas FEWS NET said were held up by aid deteriorate once aid was cut?", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0.1, 1, 0.95))
    fig.text(0.01, 0.01, textwrap.fill(
        "Flagged = FEWS NET marked the area '!' (humanitarian assistance keeping it at least one phase better) in the "
        "baseline map. Circles: change over 12 months; squares: over 24 months (same calendar month). Each point compares the change in flagged and unflagged areas that started in the same phase, "
        "country and month (FEWS NET areas in Phase 2-3 in panel A; in B and C, the flag is the share of the Cadre "
        "Harmonise / IPC area covered by flagged FEWS NET areas in a map made at most 4 months before the baseline analysis). Baselines are all before 2025. Red: later classification in 2025-26, after the US "
        "aid cut; blue: earlier years, the normal evolution of flagged areas. Small numbers: flagged observations. "
        "95% intervals clustered by country.", 240), fontsize=7.5, color="#555")
    fig.savefig(FIG / "flag_release.pdf")
    fig.savefig(FIG / "flag_release.png", dpi=150)


if __name__ == "__main__":
    main()
