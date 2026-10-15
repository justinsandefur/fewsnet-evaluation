"""Somalia, 2025: did outcomes fall short of prediction more in AID-DEPENDENT places?

68_somalia_us_cut.py could not find a location-specific US shock: US-funded partners did not
exit more than others, because about half of all humanitarian money in Somalia (and ~70% of
WFP's and UNICEF's) was American and every channel was cut. This script treats the cut as a
shock to ALL humanitarian aid and asks whether places that depended more on aid in 2024 did
worse in 2025.

Aid dependence (district, 2024, fixed before the cut; Banadir one unit):
  usd_pc       cash and in-kind transfers reported in OCHA's 2024 3W (US$ per person)
  reach_pc     people reached per month in food security, nutrition, health and WASH, per person
  partners_pc  partners present in those sectors (Apr-Oct 2024 monthly average) per 100,000 people
  index        mean of the three standardised logs (main measure)
  flag23       share of FEWS NET units flagged "!" (aid keeping the area at least one phase better)
               in the Feb and Jun 2023 current-situation maps (FEWS NET hardly used the flag in 2024)
Population: FEWS NET unit populations (2016 units) summed to districts. Survey domains take the
population-weighted mean of their districts.

Two tests.
  1. Difference-in-differences: outcome on domain and season effects + index x post + rainfall,
     conflict and prices. Variant A: season effects common to all domains (so camps vs villages
     count as variation in dependence); variant B: season effects specific to rural / camp / town.
  2. Prediction gap (placebo in time). For each year Y = 2017..2025, fit wasting on domain effects,
     season, trend, rainfall (6 and 12 months), conflict and prices using the pre-2025 years other
     than Y; take each domain's prediction error in Y. The 2025 gap between more- and less-
     dependent domains (slope of error on the index; and above- minus below-median) is ranked
     against the same gap in 2017-2024.

Outputs: output/tables/som_aiddep_*.csv, som_aiddep_key.json, output/figures/som_aiddep_*.pdf,
         output/us_cut_memo/numbers_aiddep.tex
"""
import importlib.util
import json
import re
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
AID = INP / "subnational_aid"
spec = importlib.util.spec_from_file_location("m68", ROOT / "code" / "68_somalia_us_cut.py")
M68 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M68)
dist_key, SECTORS = M68.dist_key, M68.SECTORS
KEY = {}
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#8a8a8a"
OUTCOMES = ["gam", "sam", "muac_gam", "muac_sam", "stunting", "morbidity", "cdr", "u5dr", "measles", "vita"]


# ------------------------------------------------------------------ aid dependence
def district_pop():
    fx = pd.read_csv(AID / "tidy" / "fews_admin2_som.csv")
    fx = fx[fx.vintage == "2016C3"]
    pop = pd.read_parquet(INP / "panel" / "fnid_population.parquet").set_index("fnid")["pop"]
    fx["pop"] = fx.fnid.map(pop)
    fx["dist"] = fx.admin2_pcode.map(dist_key)
    return fx.groupby("dist")["pop"].sum()


def dependence():
    pop = district_pop()
    r = pd.read_parquet(AID / "tidy" / "reach_som.parquet")
    r = r[(r.series == "som_3w") & (r.period_start.dt.year == 2024) & ~r.cumulative]
    r["dist"] = r.admin2_pcode.map(dist_key)
    usd = r[r.measure == "usd"].groupby("dist").value.sum()
    rr = r[(r.measure == "reached") & r.cluster.isin(SECTORS)]
    months = rr.period_start.nunique()
    reach = rr.groupby("dist").value.sum() / months
    o = pd.read_parquet(AID / "tidy" / "org_presence_som.parquet")
    o = o[(o.period_type == "month") & o.cluster.isin(SECTORS) & (o.period_start.dt.year == 2024) &
          o.period_start.dt.month.between(4, 10)]
    o["dist"] = o.admin2_pcode.map(dist_key)
    partners = o.groupby(["dist", "period_start"]).apply(lambda s: s[["org", "cluster"]].drop_duplicates().shape[0]) \
        .groupby("dist").mean()
    D = pd.DataFrame({"pop": pop})
    D["usd_pc"] = usd.reindex(D.index).fillna(0) / D["pop"]
    D["reach_pc"] = reach.reindex(D.index).fillna(0) / D["pop"]
    D["partners_pc"] = partners.reindex(D.index).fillna(0) / D["pop"] * 1e5
    # FEWS NET "!" flag, 2023 current-situation maps
    f = pd.read_parquet(INP / "fewsnet" / "ipcphase.parquet")
    f = f[(f.country_code == "SO") & (f.scenario_name == "Current Situation") &
          f.reporting_date.astype(str).str[:7].isin(["2023-02", "2023-06"])]
    fx = pd.read_csv(AID / "tidy" / "fews_admin2_som.csv")
    fd = dict(zip(fx.fnid, fx.admin2_pcode.map(dist_key)))
    upop = pd.read_parquet(INP / "panel" / "fnid_population.parquet").set_index("fnid")["pop"]
    f["dist"], f["w"] = f.fnid.map(fd), f.fnid.map(upop).fillna(1.0)
    f["flag"] = f.is_allowing_for_assistance.astype(float)
    D["flag23"] = f.groupby("dist").apply(lambda s: np.average(s.flag, weights=s.w))
    D = D[D["pop"] > 0]
    z = lambda s: (s - s.mean()) / s.std()
    lg = lambda s: np.log(s + s[s > 0].min() / 2)
    D["index"] = (z(lg(D.usd_pc)) + z(lg(D.reach_pc)) + z(lg(D.partners_pc))) / 3
    KEY["dep_corr"] = D[["usd_pc", "reach_pc", "partners_pc", "flag23"]].apply(lg).corr().round(2).to_dict()
    KEY["dep_totals"] = {"usd_musd": float(usd.sum() / 1e6), "reach_monthly_m": float(reach.sum() / 1e6),
                         "months_reach": int(months)}
    D.to_csv(TAB / "som_aiddep_districts.csv")
    return D


def domain_dep(p, D):
    cols = ["index", "usd_pc", "reach_pc", "partners_pc", "flag23"]
    rows = []
    for r in p.drop_duplicates("domain").itertuples():
        w = pd.Series({k: v for k, v in json.loads(r.dists).items() if k not in (None, "null")})
        rec = {"domain": r.domain}
        for c in cols:
            v = D[c].reindex(w.index)
            ok = v.notna()
            rec["dep_" + c] = float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan
        rows.append(rec)
    X = pd.DataFrame(rows)
    # standardise across domains so coefficients are per standard deviation of dependence
    for c in cols:
        s = X["dep_" + c] if c in ("index", "flag23") else np.log(X["dep_" + c] + X["dep_" + c][X["dep_" + c] > 0].min() / 2)
        X["z_" + c] = (s - s.mean()) / s.std()
    return p.merge(X, on="domain")


# ------------------------------------------------------------------ prices
def add_prices(p):
    pr = pd.read_csv(INP / "prices" / "som.csv", low_memory=False)
    pr = pr[~pr.date.astype(str).str.startswith("#")]
    pr["usdprice"] = pd.to_numeric(pr.usdprice, errors="coerce")
    pr = pr[pr.pricetype.eq("Retail") & pr.usdprice.gt(0)]
    pr["t"] = pd.PeriodIndex(pd.to_datetime(pr.date), freq="M")
    names = pd.read_csv(AID / "tidy" / "admin2_names_som.csv").dropna(subset=["admin1_pcode"])
    a1 = {re.sub(r"[^a-z]", "", n.lower()): c for n, c in zip(names.admin1, names.admin1_pcode)}
    a1.update({re.sub(r"[^a-z]", "", n.lower()): c for n, c in zip(names.admin1_raw.astype(str), names.admin1_pcode)})
    a1.update({"hiraan": "SO20", "hiran": "SO20", "galgaduud": "SO19", "galgadud": "SO19", "woqooyigalbeed": "SO12",
               "banadir": "SO22", "banaadir": "SO22", "lowershabelle": "SO23", "middleshabelle": "SO21",
               "lowerjuba": "SO28", "middlejuba": "SO27", "nugaal": "SO17", "nugal": "SO17"})
    pr["reg"] = pr.admin1.astype(str).str.lower().str.replace(r"[^a-z]", "", regex=True).map(a1)
    out = {}
    for lab, pat in [("cereal", r"^(Sorghum \(red\)|Sorghum \(white\)|Maize \(white\))$"), ("goat", r"^Livestock \(Goat\)$")]:
        q = pr[pr.commodity.str.contains(pat, regex=True)].dropna(subset=["reg"])
        # log price relative to the market x commodity mean, averaged by region-month
        q["lp"] = np.log(q.usdprice)
        q["lp"] = q.lp - q.groupby(["market", "commodity"]).lp.transform("mean")
        out[lab] = q.groupby(["reg", "t"]).lp.mean()
    vals = {k: [] for k in out}
    for r in p.itertuples():
        regs = pd.Series({k[:4]: 0.0 for k in json.loads(r.dists) if k not in (None, "null")})
        for d, w in json.loads(r.dists).items():
            if d not in (None, "null"):
                regs[d[:4]] += w
        for k, s in out.items():
            xs, ws = [], []
            for reg, w in regs.items():
                if reg in s.index.get_level_values(0):
                    ss = s.loc[reg]
                    v = ss[(ss.index > r.month - 3) & (ss.index <= r.month)]
                    if len(v):
                        xs.append(v.mean())
                        ws.append(w)
            vals[k].append(np.average(xs, weights=ws) if xs else np.nan)
    for k in vals:
        p[f"lp_{k}"] = vals[k]
        KEY[f"price_cov_{k}"] = float(p[f"lp_{k}"].notna().mean())
        p[f"lp_{k}"] = p[f"lp_{k}"].fillna(p.groupby("year")[f"lp_{k}"].transform("mean")).fillna(0)
    return p


def add_rain12(p):
    rain = pd.read_parquet(INP / "panel" / "fnid_rain_monthly.parquet")
    rain = rain[rain.index.str.startswith("SO")]
    cols = list(rain.columns)
    out = []
    for r in p.itertuples():
        ids = [f for f in r.fnids.split(";") if f in rain.index]
        end = str(r.month)
        if not ids or end not in cols:
            out.append(np.nan)
            continue
        j = cols.index(end)
        win = rain.loc[ids, cols[j - 11:j + 1]].sum(axis=1)
        C = pd.concat([rain.loc[ids, cols[cols.index(f"{yy}-{end[5:]}") - 11:cols.index(f"{yy}-{end[5:]}") + 1]].sum(axis=1)
                       for yy in range(1991, 2021)], axis=1)
        out.append(((win - C.mean(axis=1)) / C.std(axis=1).replace(0, np.nan)).mean())
    p["rain12_z"] = out
    p["rain12_z"] = p.rain12_z.fillna(p.rain12_z.mean())
    return p


# ------------------------------------------------------------------ estimation
CTRL = ["rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat"]


def did(p, exp, y, typed):
    d = p.dropna(subset=[y, exp]).copy()
    X = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
    tfe = (d.ptype + ":" + d.season_id) if typed else d.season_id
    X = X.join(pd.get_dummies(tfe, prefix="t", drop_first=True, dtype=float))
    X["treat"] = d[exp] * d.post
    for c in CTRL:
        X[c] = d[c]
    X.insert(0, "const", 1.0)
    X = X.loc[:, X.std() > 0].assign(const=1.0)
    yy, g = d[y].values, d.region.values
    b, se, _ = M68.ols_cl(X, yy, g)
    j = list(X.columns).index("treat")
    return dict(b=b[j], se=se[j], p_wild=M68.wild_p(X, yy, g, "treat"), n=len(d), post_n=int(d.post.sum()),
                ymean_pre=d[d.post == 0][y].mean())


def prediction_gaps(p, y, exp="z_index"):
    d = p.dropna(subset=[y]).copy()
    d["trend"] = d.year - 2015
    d["deyr"] = (d.season_type == "Deyr").astype(float)
    feats = ["deyr", "trend"] + CTRL
    rows, err_rows = [], []
    for yr in range(2017, 2027):
        tr = d[(d.year != yr) & (d.year < 2025)]
        te = d[(d.year == yr) & d.domain.isin(tr.domain)].copy()
        doms = sorted(tr.domain.unique())
        Xf = lambda z: np.column_stack([pd.get_dummies(z.domain, dtype=float).reindex(columns=doms, fill_value=0.0).values,
                                        z[feats].values])
        b = np.linalg.lstsq(Xf(tr), tr[y].values, rcond=None)[0]
        te["err"] = te[y].values - Xf(te) @ b
        e = te.groupby("domain").agg(err=("err", "mean"), dep=(exp, "first"))
        slope = np.polyfit(e.dep, e.err, 1)[0]
        hi = e.dep > d.drop_duplicates("domain")[exp].median()
        rows.append(dict(year=yr, mean_err=e.err.mean(), slope=slope, gap=e[hi].err.mean() - e[~hi].err.mean(),
                         err_hi=e[hi].err.mean(), err_lo=e[~hi].err.mean(), domains=len(e)))
        err_rows.append(te.assign(year=yr)[["domain", "year", "season_id", "err", exp]])
    S = pd.DataFrame(rows)
    pre = S[S.year < 2025]
    s25 = S[S.year == 2025].iloc[0]
    rank = lambda c, r: int((pre[c].abs() >= abs(r[c])).sum())
    out = dict(slope25=float(s25.slope), gap25=float(s25.gap), mean25=float(s25.mean_err),
               slope_rank=rank("slope", s25), gap_rank=rank("gap", s25), mean_rank=rank("mean_err", s25),
               slope_pre_sd=float(pre.slope.std()), gap_pre_sd=float(pre.gap.std()),
               err_hi25=float(s25.err_hi), err_lo25=float(s25.err_lo), n_placebo=len(pre))
    if (S.year == 2026).any():
        s26 = S[S.year == 2026].iloc[0]
        out.update(gap26=float(s26.gap), mean26=float(s26.mean_err), gap_rank26=rank("gap", s26),
                   mean_rank26=rank("mean_err", s26), err_hi26=float(s26.err_hi), err_lo26=float(s26.err_lo),
                   domains26=int(s26.domains))
    return S, out, pd.concat(err_rows)


def main():
    D = dependence()
    p = pd.read_parquet(INP / "panel" / "som_uscut_panel.parquet")
    # dists column was dropped from the saved panel; rebuild it
    q = M68.survey_panel()
    p = p.merge(q[["domain", "season_id", "dists"]], on=["domain", "season_id"], how="left")
    p = add_rain12(add_prices(p))
    p = domain_dep(p, D)
    KEY["domains"], KEY["rows"] = int(p.domain.nunique()), int(len(p))
    dom = p.drop_duplicates("domain")
    KEY["dep_by_type"] = dom.groupby("ptype").z_index.mean().round(2).to_dict()
    KEY["corr_index_uspred"] = float(dom.z_index.corr(dom.E_pred))
    KEY["corr_index_loss"] = float(dom.z_index.corr(dom.E_loss))
    md = D.dropna(subset=["index"]).join(pd.read_csv(TAB / "som_uscut_districts.csv", index_col=0)[["E_loss", "E_pred"]])
    KEY["corr_index_loss_dist"] = float(md["index"].corr(md.E_loss))
    p["idp"] = (p.ptype == "IDP").astype(float)
    p.drop(columns=["dists"]).to_parquet(INP / "panel" / "som_aiddep_panel.parquet", index=False)

    rows = []
    for exp in ["z_index", "z_usd_pc", "z_reach_pc", "z_partners_pc", "z_flag23", "idp"]:
        for y in (OUTCOMES if exp == "z_index" else ["gam"]):
            for typed in ([False, True] if exp != "idp" else [False]):
                r = did(p, exp, y, typed)
                rows.append(dict(exposure=exp, outcome=y, season_fe="by type" if typed else "common", **r))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "som_aiddep_did.csv", index=False)

    G, gaps = [], {}
    for y in ["gam", "sam", "muac_gam", "cdr", "u5dr", "measles", "vita"]:
        S, k, E = prediction_gaps(p, y)
        S["outcome"] = y
        G.append(S)
        gaps[y] = k
        if y == "gam":
            E.to_csv(TAB / "som_aiddep_errors_gam.csv", index=False)
    G = pd.concat(G)
    G.to_csv(TAB / "som_aiddep_gaps.csv", index=False)
    KEY["gaps"] = gaps
    figures(G, p)
    (TAB / "som_aiddep_key.json").write_text(json.dumps(KEY, indent=1, default=float))
    write_numbers(R, gaps)
    pd.set_option("display.width", 220, "display.max_rows", 200)
    print(json.dumps({k: v for k, v in KEY.items() if k != "gaps"}, indent=1, default=float))
    R["se"] = R.se
    print(R.round(3).to_string())
    print(G[G.outcome == "gam"].round(2).to_string())
    print(pd.DataFrame(gaps).T.round(2).to_string())


def figures(G, p):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    g = G[G.outcome == "gam"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    ax = axes[0]
    ax.plot(g.year, g.err_hi, color=ORANGE, marker="o", ms=4, label="More aid-dependent")
    ax.plot(g.year, g.err_lo, color=BLUE, marker="o", ms=4, label="Less aid-dependent")
    ax.axhline(0, color=GREY, lw=0.8)
    ax.axvline(2024.5, color=GREY, ls=":", lw=0.8)
    ax.set_title("Wasting minus prediction (points)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8.5)
    ax.set_xticks(range(2017, 2027, 2))
    ax = axes[1]
    cols = [ORANGE if y == 2025 else GREY for y in g.year]
    ax.bar(g.year, g.gap, color=cols, width=0.7)
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_title("Gap: more minus less dependent", fontsize=9.5)
    ax.set_xticks(range(2017, 2027, 2))
    fig.tight_layout()
    fig.savefig(FIG / "som_aiddep_gaps.pdf")
    plt.close(fig)


def write_numbers(R, gaps):
    M = {}
    f2 = lambda x: f"{x:.2f}"
    f1 = lambda x: f"{x:.1f}"
    M["AdDomains"] = KEY["domains"]
    M["AdUsd"] = f"{KEY['dep_totals']['usd_musd']:.0f}"
    M["AdCorrUsReach"] = f2(KEY["dep_corr"]["usd_pc"]["reach_pc"])
    M["AdCorrUsdPartners"] = f2(KEY["dep_corr"]["usd_pc"]["partners_pc"])
    M["AdCorrReachPartners"] = f2(KEY["dep_corr"]["reach_pc"]["partners_pc"])
    M["AdCorrFlag"] = f2(np.mean([KEY["dep_corr"]["flag23"][c] for c in ["usd_pc", "reach_pc", "partners_pc"]]))
    M["AdCorrLoss"] = f2(KEY["corr_index_loss_dist"])
    M["AdCorrUs"] = f2(KEY["corr_index_uspred"])
    for t, v in KEY["dep_by_type"].items():
        M[f"AdType{ {'rural': 'Rural', 'IDP': 'Idp', 'urban': 'Urban'}[t] }"] = f1(v)
    en = {"z_index": "Idx", "z_usd_pc": "Usd", "z_reach_pc": "Reach", "z_partners_pc": "Part", "z_flag23": "Flag", "idp": "Idp"}
    on = {"gam": "Gam", "sam": "Sam", "muac_gam": "Muac", "muac_sam": "MuacSam", "stunting": "Stunt", "morbidity": "Morb",
          "cdr": "Cdr", "u5dr": "Ufive", "measles": "Meas", "vita": "Vita"}
    for r in R.itertuples():
        t = en[r.exposure] + on[r.outcome] + ("T" if r.season_fe == "by type" else "")
        M[f"b{t}"], M[f"se{t}"], M[f"p{t}"] = f2(r.b), f2(r.se), f2(r.p_wild)
        M[f"ym{t}"] = f1(r.ymean_pre)
    for y, k in gaps.items():
        t = on[y]
        M[f"gapSlope{t}"], M[f"gapGap{t}"] = f2(k["slope25"]), f2(k["gap25"])
        M[f"gapMean{t}"] = f1(k["mean25"]) if abs(k["mean25"]) >= 1 else f2(k["mean25"])
        M[f"gapSlopeRank{t}"], M[f"gapGapRank{t}"], M[f"gapMeanRank{t}"] = k["slope_rank"], k["gap_rank"], k["mean_rank"]
        M[f"gapSd{t}"] = f2(k["gap_pre_sd"])
        M[f"gapHi{t}"], M[f"gapLo{t}"] = f1(k["err_hi25"]), f1(k["err_lo25"])
        if "gap26" in k:
            M[f"gapGapTs{t}"], M[f"gapMeanTs{t}"] = f2(k["gap26"]), (f1(k["mean26"]) if abs(k["mean26"]) >= 1 else f2(k["mean26"]))
            M[f"gapGapRankTs{t}"], M[f"gapMeanRankTs{t}"] = k["gap_rank26"], k["mean_rank26"]
            M[f"gapHiTs{t}"], M[f"gapLoTs{t}"], M[f"gapDomTs{t}"] = f1(k["err_hi26"]), f1(k["err_lo26"]), k["domains26"]
    M["gapN"] = gaps["gam"]["n_placebo"]
    (ROOT / "output" / "us_cut_memo" / "numbers_aiddep.tex").write_text(
        "% generated by code/69_somalia_aid_dependence.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))


if __name__ == "__main__":
    main()
