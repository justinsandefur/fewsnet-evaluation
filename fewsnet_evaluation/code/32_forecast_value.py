"""Does FEWS NET know something the public data don't, and does money follow it?

Unit: FEWS NET area x map round r (full Feb/Jun/Oct rounds; quarterly before
2016), 2011-2024. The forecast is the medium-term projection (ML2) issued at r
for the month of the area's next map (about 4 months on).

1. Public part of the forecast. A gradient-boosted model predicts whether the
   forecast puts the area in Crisis or worse (Phase 3+) from information a
   donor could see without the forecast: the area's current and two previous
   FEWS NET maps (phase and aid flag), the country's current share in Crisis+,
   the country and calendar month (seasonality), and local shocks measured
   before r (CHIRPS rainfall vs the previous 20 years; ACLED political
   violence; WFP cereal price changes). Cross-fitted: each year's prediction
   comes from a model fitted on the other years.
   Added judgment = forecast (0/1) minus public prediction.

2. Is the added judgment right? Outcomes at the next map:
     mapped   Phase 3+ on FEWS NET's next map
     need     mapped phase plus one if flagged as held up by aid, 3+
              (FEWS NET's own without-aid counterfactual)
     IPC/CH   Phase 3+ in the next independent Cadre Harmonise / IPC analysis
              (area-weighted overlay)
   y = a public + b added + FE(country x round), clustered by country.
   Aid that prevents crises masks accuracy on mapped outcomes, not on need.
   Also: predictive gain (AUC) from adding the forecast to the public model.

3. Does money follow it? Country x round: humanitarian funding committed over
   the next 6 months (FTS, log) on the country means of the public part and
   the added judgment, with prior funding, country and time fixed effects.

4. Masking. Does the added judgment come true less often on mapped outcomes
   (but not on need) when funding then rose more than usual for the country?

Outputs: output/tables/forecast_value*.csv, output/figures/forecast_value.pdf
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
CACHE = INP / "panel"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DID = load("did", "25_slope_did.py")
RAIN = load("rain", "24_area_rainfall.py")
SHK = load("shk", "27_shock_index.py")
AID = load("aid", "31_aid_response.py")
norm = RAIN.norm


# ------------------------------------------------------------------ panel
def rounds():
    c = pd.read_parquet(INP / "fewsnet" / "classifications.parquet", columns=["scenario", "report_month"])
    n = c[c.scenario == "CS"].groupby("report_month").size()
    return n[n > 1000].index


def area_panel():
    R = rounds()
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    cs = cs[cs.month.isin(R)].sort_values(["fnid", "month"]).copy()
    cs["flag"] = cs.assist_flag.astype(float)
    g = cs.groupby("fnid")
    for k, sh in [("prev", 1), ("prev2", 2), ("next", -1)]:
        cs[f"{k}_month"], cs[f"{k}_phase"], cs[f"{k}_flag"] = g.month.shift(sh), g.phase.shift(sh), g.flag.shift(sh)
    gap = lambda a, b: (a - b).apply(lambda x: x.n if pd.notna(x) else np.nan)
    cs["gap_next"] = gap(cs.next_month, cs.month)
    for k in ["prev", "prev2"]:
        bad = gap(cs.month, cs[f"{k}_month"]) > 8 * (1 if k == "prev" else 2)
        cs.loc[bad, [f"{k}_phase", f"{k}_flag"]] = np.nan
    p = cs[(cs.gap_next > 0) & (cs.gap_next <= 8) & (cs.month.dt.year <= 2024)].copy()
    p = p.rename(columns={"month": "r", "next_month": "target"})
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    ml2 = proj[proj.scenario == "ML2"].rename(columns={"report_month": "r"})
    exact = ml2.rename(columns={"month": "target", "phase": "fc_phase", "assist_flag": "fc_flag"})[
        ["fnid", "r", "target", "fc_phase", "fc_flag"]].drop_duplicates(["fnid", "r", "target"])
    p = p.merge(exact, on=["fnid", "r", "target"], how="left")
    fb = ml2.groupby(["fnid", "r"]).agg(fb_phase=("phase", "max"), fb_flag=("assist_flag", "max")).reset_index()
    p = p.merge(fb, on=["fnid", "r"], how="left")
    p["fc_phase"] = p.fc_phase.fillna(p.fb_phase)
    p["fc_flag"] = p.fc_flag.fillna(p.fb_flag).astype(float)
    p = p.dropna(subset=["fc_phase", "next_phase"])
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    p["iso3"] = p.country_code.map(dict(zip(codes.iso3166a2, codes.iso3166a3)))
    p["f3"] = (p.fc_phase >= 3).astype(float)
    p["a3"] = (p.next_phase >= 3).astype(float)
    p["n3"] = ((p.next_phase + p.next_flag.fillna(0)) >= 3).astype(float)
    p["cur3"] = (p.phase >= 3).astype(float)
    p["nat3"] = p.groupby(["country_code", "r"]).cur3.transform("mean")
    p["tmonth"] = p.target.dt.month
    p["horizon"] = gap(p.target, p.r)
    return p


# ------------------------------------------------------------------ shocks by FEWS NET area
def unit_geoms(fnids):
    u = gpd.read_file(INP / "fewsnet" / "units.gpkg")[["fnid", "geometry"]].drop_duplicates("fnid")
    u = u[u.fnid.isin(fnids)].copy()
    u["geometry"] = u.geometry.buffer(0)
    return u[u.geom_type.isin(["Polygon", "MultiPolygon"])]


def rain_shocks(p, units):
    f = CACHE / "fnid_rain_monthly.parquet"
    if f.exists():
        Rm = pd.read_parquet(f)
    else:
        geo = units.rename(columns={"fnid": "key"})
        idx = RAIN.cell_index(geo, RAIN.grids())
        print("rain cells for", len(idx), "areas", flush=True)
        Rm = RAIN.monthly_rain(idx)
        Rm.columns = Rm.columns.astype(str)
        Rm.to_parquet(f)
    months = pd.PeriodIndex(Rm.columns, freq="M")
    A = Rm.values.astype(float)
    out = []
    for w in [6, 12]:
        cum = pd.DataFrame(A).T.rolling(w, min_periods=w).sum().T.values
        for r in sorted(p.r.unique()):
            e = months.get_loc(r - 1)
            refs = [e - 12 * j for j in range(1, 21) if e - 12 * j >= 0]
            ref = cum[:, refs]
            ok = np.isfinite(ref).sum(1) >= 15
            mu, sd = np.nanmean(ref, 1), np.nanstd(ref, 1, ddof=1)
            z = np.where(ok & (sd > 0), (cum[:, e] - mu) / sd, np.nan)
            out.append(pd.DataFrame({"fnid": Rm.index, "r": r, f"rain_z{w}": z}))
    s = pd.concat(out).groupby(["fnid", "r"]).first().reset_index()
    return s


def districts(a):
    """District polygons keyed to ACLED's districts: OCHA boundaries (COD-AB) matched on district code
    (digits only; prefixes differ, e.g. NER/NE), then on name; geoBoundaries names where COD-AB is absent."""
    import re
    dig = lambda x: re.sub(r"\D", "", str(x))
    out = []
    for iso in sorted(a.iso3.unique()):
        aa = a[a.iso3 == iso].drop_duplicates("Admin2 Pcode")
        zp = INP / "areas" / "codab" / f"{iso.lower()}.geojson.zip"
        if zp.exists():
            x = gpd.read_file(f"zip://{zp}!{iso.lower()}_admin2.geojson")
            x["d"], x["n"] = x.adm2_pcode.map(dig), x.adm2_name.map(norm)
            m1 = aa.assign(d=aa["Admin2 Pcode"].map(dig)).merge(x[["d", "geometry"]], on="d")
            rest = aa[~aa["Admin2 Pcode"].isin(m1["Admin2 Pcode"])]
            m2 = rest.assign(n=rest.Admin2.map(norm)).merge(x[["n", "geometry"]].drop_duplicates("n"), on="n")
            m = pd.concat([m1, m2])
        else:
            fp = INP / "areas" / "adm2" / f"{iso}.geojson"
            if not fp.exists():
                continue
            x = gpd.read_file(fp)
            x["n"] = x.shapeName.map(norm)
            m = aa.assign(n=aa.Admin2.map(norm)).merge(x[["n", "geometry"]].drop_duplicates("n"), on="n")
        print(f"  {iso}: {len(m)}/{len(aa)} ACLED districts placed", flush=True)
        out.append(gpd.GeoDataFrame(m[["Admin2 Pcode", "geometry"]].assign(iso3=iso), crs=4326))
    return gpd.GeoDataFrame(pd.concat(out), crs=4326)


def conflict_shocks(p, units):
    """Events and deaths in the 6 months before each round, apportioned from ACLED districts to FEWS NET
    areas by the share of each district's area that falls in the area."""
    a = SHK.acled()
    a = a[a.Admin2.notna()]
    wf = CACHE / "fnid_acled_weights.parquet"
    if wf.exists():
        W = pd.read_parquet(wf)
    else:
        W = district_weights(a, units, p)
        W.to_parquet(wf, index=False)
    return conflict_from_weights(a, W, p)


def district_weights(a, units, p):
    D = districts(a).to_crs(6933)
    D["geometry"] = D.geometry.buffer(0)
    D["darea"] = D.area
    u = units.copy()
    u["iso3"] = u.fnid.map(p.drop_duplicates("fnid").set_index("fnid").iso3)
    u = u[u.iso3.isin(D.iso3.unique())].to_crs(6933)
    u["uarea"] = u.area
    W = []
    for iso in u.iso3.unique():
        x = gpd.overlay(D[D.iso3 == iso][["Admin2 Pcode", "darea", "geometry"]], u[u.iso3 == iso][["fnid", "uarea", "geometry"]],
                        how="intersection", keep_geom_type=True)
        x["w"] = x.area / x.darea                    # share of the district's events assigned to the area
        x["ucov"] = x.area / x.uarea                  # share of the area covered by placed districts
        W.append(x[["Admin2 Pcode", "fnid", "w", "ucov"]])
    return pd.concat(W)


def conflict_from_weights(a, W, p):
    covered = set(W.groupby("fnid").ucov.sum().loc[lambda v: v > 0.5].index)
    ev = a.groupby(["Admin2 Pcode", "month"])[["Events", "Fatalities"]].sum().reset_index()
    ev = ev.merge(W[["Admin2 Pcode", "fnid", "w"]], on="Admin2 Pcode")
    ev["Events"], ev["Fatalities"] = ev.Events * ev.w, ev.Fatalities * ev.w
    ev = ev.groupby(["fnid", "month"])[["Events", "Fatalities"]].sum()
    allm = pd.period_range("1997-01", "2024-12", freq="M")
    E = ev.Events.unstack().reindex(columns=allm, fill_value=0).fillna(0)
    Fa = ev.Fatalities.unstack().reindex(columns=allm, fill_value=0).fillna(0)
    r6e = E.T.rolling(6, min_periods=1).sum().T
    r6f = Fa.T.rolling(6, min_periods=1).sum().T
    out = []
    for r in sorted(p.r.unique()):
        e = r - 1
        out.append(pd.DataFrame({"fnid": r6e.index, "r": r, "ln_ev6": np.log1p(r6e[e].values),
                                 "ln_fat6": np.log1p(r6f[e].values),
                                 "d_ln_ev6": np.log1p(r6e[e].values) - np.log1p(r6e[e - 12].values)}))
    c = pd.concat(out)
    # areas in placed districts with no recorded events: zero, not missing
    z = pd.MultiIndex.from_product([sorted(covered), sorted(p.r.unique())], names=["fnid", "r"]).to_frame(index=False)
    c = z.merge(c, on=["fnid", "r"], how="left").fillna({"ln_ev6": 0, "ln_fat6": 0, "d_ln_ev6": 0})
    return c, covered


def price_shocks(p, units):
    """Cereal price changes at the WFP market nearest each FEWS NET area (within 150 km), months r-3..r-1."""
    m = SHK.wfp_prices()
    mk = m.drop_duplicates(["iso3", "market"])[["iso3", "market", "lat", "lon"]]
    pts = gpd.GeoDataFrame(mk, geometry=gpd.points_from_xy(mk.lon, mk.lat), crs=4326).to_crs(6933)
    c = units.copy()
    c["geometry"] = c.geometry.representative_point()
    c = c.to_crs(6933)
    j = gpd.sjoin_nearest(c[["fnid", "geometry"]], pts[["iso3", "market", "geometry"]], max_distance=150_000,
                          distance_col="km").drop_duplicates("fnid")[["fnid", "iso3", "market"]]
    print("  areas with a market within 150 km:", round(len(j) / len(c), 3), flush=True)
    x = m.merge(j, on=["iso3", "market"]).groupby(["fnid", "month"])[["dp12", "dp3"]].mean()
    out = []
    for r in sorted(p.r.unique()):
        win = [r - k for k in (1, 2, 3)]
        w = x[x.index.get_level_values(1).isin(win)].groupby(level=0).mean()
        out.append(w.reset_index().assign(r=r))
    return pd.concat(out)


FEATS = ["cty", "phase", "flag", "prev_phase", "prev_flag", "prev2_phase", "prev2_flag", "nat3", "tmonth",
         "horizon", "rain_z6", "rain_z12", "ln_ev6", "ln_fat6", "d_ln_ev6", "dp12", "dp3"]


def crossfit(p, y, feats, label):
    """Out-of-year predictions from a gradient-boosted classifier."""
    X = p[feats].copy()
    pred = pd.Series(np.nan, index=p.index)
    cat = [feats.index("cty")] if "cty" in feats else []
    for yr in sorted(p.r.dt.year.unique()):
        te = p.r.dt.year == yr
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
                                           categorical_features=cat or None, random_state=1)
        m.fit(X[~te], p.loc[~te, y])
        pred[te] = m.predict_proba(X[te])[:, 1]
    print("cross-fitted", label, flush=True)
    return pred


# ------------------------------------------------------------------ IPC / CH overlay
def ipc_check(p, units):
    outcomes = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    geo, o = RAIN.area_geometries(outcomes)
    keys = o[["key", "iso3"]].drop_duplicates("key")
    g = geo.merge(keys, on="key").drop_duplicates("key")
    g = g[g.iso3.isin(p.iso3.unique())].to_crs(6933)
    g["geometry"] = g.geometry.buffer(0)
    g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])]
    g["key_area"] = g.area
    u = units.to_crs(6933)
    inter = gpd.overlay(g[["key", "key_area", "geometry"]], u[["fnid", "geometry"]], how="intersection",
                        keep_geom_type=True)
    inter["w"] = inter.area / inter.key_area
    inter = inter[inter.w > 0.01][["key", "fnid", "w"]]
    m = inter.merge(p[["fnid", "r", "pub3", "added3", "cur3", "iso3"]], on="fnid")
    for v in ["pub3", "added3", "cur3"]:
        m[v + "_w"] = m[v] * m.w
    a = m.groupby(["key", "r", "iso3"]).agg(pub3=("pub3_w", "sum"), added3=("added3_w", "sum"),
                                             fcur3=("cur3_w", "sum"), w=("w", "sum")).reset_index()
    a = a[a.w > 0.5]
    for v in ["pub3", "added3", "fcur3"]:
        a[v] = a[v] / a.w
    o = o.dropna(subset=["phase"]).sort_values("month")
    o["ph3"] = (o.phase >= 3).astype(float)
    oo = o.groupby(["key", "month"]).agg(ph3=("ph3", "max"), share3=("share3", "mean")).reset_index()
    oo["mi"] = oo.month.astype("int64")
    a["mi"] = a.r.astype("int64")
    a = a.sort_values("mi")
    last = pd.merge_asof(a, oo.sort_values("mi")[["key", "mi", "ph3", "share3"]], on="mi", by="key",
                         direction="backward", tolerance=8).rename(columns={"ph3": "ipc_last3", "share3": "ipc_last_share3"})
    nxt = oo.copy()
    nxt["mi"] = nxt.mi - 1                 # strictly after the forecast month
    t = pd.merge_asof(last.sort_values("mi"), nxt.sort_values("mi")[["key", "mi", "ph3", "share3"]], on="mi",
                      by="key", direction="forward", tolerance=7).rename(columns={"ph3": "ipc3", "share3": "ipc_share3"})
    t = t.dropna(subset=["ipc3", "ipc_last3"])
    t["cell"] = t.iso3 + "_" + t.r.astype(str)
    return t


# ------------------------------------------------------------------ main
def main():
    p = area_panel()
    print("area-rounds", len(p), "areas", p.fnid.nunique(), "countries", p.country_code.nunique(), flush=True)
    units = unit_geoms(p.fnid.unique())
    print("with geometry", round(p.fnid.isin(units.fnid).mean(), 3), flush=True)
    rs = rain_shocks(p, units)
    cf, covered = conflict_shocks(p, units)
    pr = price_shocks(p, units)
    p = p.merge(rs, on=["fnid", "r"], how="left").merge(cf, on=["fnid", "r"], how="left") \
         .merge(pr, on=["fnid", "r"], how="left")
    p.loc[~p.fnid.isin(covered), ["ln_ev6", "ln_fat6", "d_ln_ev6"]] = np.nan
    a = SHK.acled()
    start = a[a.Admin2.notna()].groupby("iso3").month.min()      # ACLED coverage begins at different dates
    before = p.r < (p.iso3.map(start) + 18)                       # need 6 months, and 12 more for the change
    p.loc[before.fillna(True), ["ln_ev6", "ln_fat6", "d_ln_ev6"]] = np.nan
    p["cty"] = pd.factorize(p.country_code)[0]
    for v in ["rain_z6", "rain_z12", "ln_ev6", "dp12"]:
        print(f"  share with {v}:", round(p[v].notna().mean(), 3))

    # 1. public part of the forecast, and public-only / public+forecast models of the outcomes
    p["pub3"] = crossfit(p, "f3", FEATS, "forecast")
    p["added3"] = p.f3 - p.pub3
    for y in ["a3", "n3"]:
        p[f"q_{y}"] = crossfit(p, y, FEATS, f"{y} public")
        p[f"qf_{y}"] = crossfit(p, y, FEATS + ["fc_phase", "fc_flag"], f"{y} public+forecast")
    p["cell"] = p.iso3 + "_" + p.r.astype(str)
    p.to_parquet(CACHE / "forecast_value_panel.parquet", index=False)

    rows = []
    # 2. accuracy
    for samp, d in [("all areas", p), ("areas below Crisis now", p[p.phase <= 2])]:
        for y, lab in [("a3", "FEWS NET next map (mapped)"), ("n3", "FEWS NET next map (need: +1 if aid flag)")]:
            r, n, G = DID.fe_ols(d, y, ["pub3", "added3"], ["cell"])
            for t in ["pub3", "added3"]:
                rows.append({"block": "accuracy", "sample": samp, "outcome": lab, "term": t, "coef": r.coef[t],
                             "se": r.se[t], "n": n, "countries": G})
    T = ipc_check(p, units)
    T.to_parquet(CACHE / "forecast_value_ipc.parquet", index=False)
    for samp, d in [("all areas", T), ("areas below Crisis now", T[T.ipc_last3 == 0])]:
        r, n, G = DID.fe_ols(d, "ipc3", ["pub3", "added3", "ipc_last3", "ipc_last_share3"], ["cell"])
        for t in ["pub3", "added3"]:
            rows.append({"block": "accuracy", "sample": samp, "outcome": "Cadre Harmonise / IPC next analysis",
                         "term": t, "coef": r.coef[t], "se": r.se[t], "n": n, "countries": G})
    # predictive gain for new Crisis (areas below Crisis now)
    auc = []
    d = p[p.phase <= 2]
    for y, lab in [("a3", "mapped"), ("n3", "need")]:
        for mdl, col in [("public data only", f"q_{y}"), ("public data + FEWS NET forecast", f"qf_{y}")]:
            dd = d.dropna(subset=[col])
            auc.append({"outcome": lab, "model": mdl, "auc": roc_auc_score(dd[y], dd[col]),
                        "brier": float(((dd[col] - dd[y]) ** 2).mean()), "events": int(dd[y].sum()), "n": len(dd)})
    auc = pd.DataFrame(auc)
    auc.to_csv(TAB / "forecast_value_auc.csv", index=False)
    print(auc.round(3).to_string())

    # 3. funding
    s = AID.panel()
    c = p.groupby(["country_code", "r"]).agg(pub3=("pub3", "mean"), added3=("added3", "mean"), f3=("f3", "mean"),
                                             cur3=("cur3", "mean")).reset_index()
    s = s.merge(c, left_on=["country_code", "report_month"], right_on=["country_code", "r"])
    for col in ["all", "food"]:
        for lab, fes in [("within country (country + time FE)", ["iso3", "round"]), ("across countries (time FE)", ["round"])]:
            r, n, G = DID.fe_ols(s, f"f_{col}", ["pub3", "added3", f"f_{col}_lag"], fes)
            for t in ["pub3", "added3"]:
                rows.append({"block": "funding", "sample": lab, "outcome": f"{col} funding, next 6 months",
                             "term": t, "coef": r.coef[t], "se": r.se[t], "n": n, "countries": G})
    # 4. masking: funding surprise (next-6-month funding relative to prior funding, country and time effects)
    w = DID.within(s.dropna(subset=["f_all", "f_all_lag"]), ["f_all", "f_all_lag"], ["iso3", "round"])
    b = (w.f_all * w.f_all_lag).sum() / (w.f_all_lag ** 2).sum()
    s.loc[w.index, "fund_surprise"] = w.f_all - b * w.f_all_lag
    s["fs_t"] = pd.qcut(s.fund_surprise, 3, labels=["less than usual", "about usual", "more than usual"])
    q = p.merge(s[["country_code", "report_month", "fund_surprise", "fs_t"]],
                left_on=["country_code", "r"], right_on=["country_code", "report_month"], how="inner")
    mask = []
    for y, lab in [("a3", "mapped"), ("n3", "need")]:
        for tl, d in q.groupby("fs_t"):
            r, n, G = DID.fe_ols(d, y, ["pub3", "added3"], ["cell"])
            mask.append({"outcome": lab, "funding": tl, "coef": r.coef["added3"], "se": r.se["added3"], "n": n})
        q["ax"] = q.added3 * q.fund_surprise
        r, n, G = DID.fe_ols(q, y, ["pub3", "added3", "ax"], ["cell"])
        rows.append({"block": "masking", "sample": "all areas", "outcome": lab, "term": "added x funding surprise",
                     "coef": r.coef["ax"], "se": r.se["ax"], "n": n, "countries": G})
    mask = pd.DataFrame(mask)
    mask.to_csv(TAB / "forecast_value_masking.csv", index=False)
    R = pd.DataFrame(rows)
    R["t"] = R.coef / R.se
    R.to_csv(TAB / "forecast_value.csv", index=False)
    pd.set_option("display.width", 230)
    print(R.round(3).to_string())
    print(mask.round(3).to_string())
    desc = {"area_rounds": len(p), "areas": int(p.fnid.nunique()), "countries": int(p.country_code.nunique()),
            "share_forecast_crisis": float(p.f3.mean()), "sd_added": float(p.added3.std()),
            "share_added_gt_half": float((p.added3.abs() > 0.5).mean()),
            "ipc_overlay_rows": len(T), "ipc_countries": int(T.iso3.nunique())}
    (TAB / "forecast_value_key.json").write_text(json.dumps(desc, indent=1))
    print(desc)
    figure(R, auc, mask)


def figure(R, auc, mask):
    fig, ax = plt.subplots(2, 2, figsize=(14, 10))
    # A. predictive gain
    a = ax[0, 0]
    for i, oc in enumerate(["mapped", "need"]):
        for j, mdl in enumerate(["public data only", "public data + FEWS NET forecast"]):
            v = auc[(auc.outcome == oc) & (auc.model == mdl)].auc.iloc[0]
            a.bar(i + (j - 0.5) * 0.36, v, 0.36, color=["#bdbdbd", "#1f4e79"][j], label=mdl if i == 0 else None)
            a.text(i + (j - 0.5) * 0.36, v + 0.005, f"{v:.2f}", ha="center", fontsize=9)
    a.set_xticks([0, 1], ["Area newly in Crisis+\non the next map", "Area newly in Crisis+ by need\n(next map, +1 if aid flag)"])
    a.set_ylim(0.5, 1.0)
    a.set_ylabel("How well the model ranks which areas tip into Crisis\n(AUC: 0.5 = coin flip, 1 = perfect)")
    a.set_title("A. Does FEWS NET's forecast add to public data?", loc="left", fontweight="bold", fontsize=10.5)
    a.legend(fontsize=8.5, frameon=False, loc="upper left")
    # B. accuracy of the added judgment
    a = ax[0, 1]
    acc = R[(R.block == "accuracy") & (R["sample"] == "areas below Crisis now")]
    labs = ["FEWS NET next map (mapped)", "FEWS NET next map (need: +1 if aid flag)", "Cadre Harmonise / IPC next analysis"]
    short = ["FEWS NET's next map", "FEWS NET's next map,\nby need (+1 if aid flag)", "Independent Cadre\nHarmonise / IPC"]
    for i, (lab, sh) in enumerate(zip(labs, short)):
        for j, (t, c, nm) in enumerate([("pub3", "#bdbdbd", "Public part of the forecast"),
                                        ("added3", "#1f4e79", "FEWS NET's added judgment")]):
            r = acc[(acc.outcome == lab) & (acc.term == t)].iloc[0]
            a.errorbar(r.coef, len(labs) - i + (0.15 if j == 0 else -0.15), xerr=1.96 * r.se, fmt="o", color=c,
                       capsize=3, label=nm if i == 0 else None)
    a.set_yticks([3, 2, 1], short)
    a.axvline(0, color="#999", lw=0.8)
    a.set_xlabel("Rise in the chance the area is in Crisis+ next time,\nper unit of the forecast (1 = forecast fully borne out)")
    a.set_title("B. Does FEWS NET's added judgment come true?\n(areas below Crisis now)", loc="left", fontweight="bold",
                fontsize=10.5)
    a.legend(fontsize=8.5, frameon=False, loc="lower right")
    # C. funding
    a = ax[1, 0]
    fu = R[R.block == "funding"]
    items = [(f, s) for s in ["within country (country + time FE)", "across countries (time FE)"] for f in ["all", "food"]]
    for i, (f, s) in enumerate(items):
        for j, (t, c, nm) in enumerate([("pub3", "#bdbdbd", "Public part of the forecast"),
                                        ("added3", "#1f4e79", "FEWS NET's added judgment")]):
            r = fu[(fu.outcome.str.startswith(f)) & (fu["sample"] == s) & (fu.term == t)].iloc[0]
            pct = lambda b: 100 * (np.exp(0.1 * b) - 1)
            a.errorbar(pct(r.coef), len(items) - i + (0.15 if j == 0 else -0.15),
                       xerr=[[pct(r.coef) - pct(r.coef - 1.96 * r.se)], [pct(r.coef + 1.96 * r.se) - pct(r.coef)]],
                       fmt="o", color=c, capsize=3, label=nm if i == 0 else None)
    a.set_yticks([4, 3, 2, 1], [f"{'All' if f == 'all' else 'Food/nutrition'} funding,\n{s.split(' (')[0]}" for f, s in items])
    a.axvline(0, color="#999", lw=0.8)
    a.set_xlabel("% change in funding over the next 6 months per 10-point rise\nin the share of the country's areas forecast in Crisis+")
    a.set_title("C. Does money follow it?", loc="left", fontweight="bold", fontsize=10.5)
    a.legend(fontsize=8.5, frameon=False, loc="upper right")
    # D. masking
    a = ax[1, 1]
    order = ["less than usual", "about usual", "more than usual"]
    for j, (oc, c, nm) in enumerate([("mapped", "#c0392b", "Mapped outcome"), ("need", "#1f4e79", "Need (+1 if aid flag)")]):
        d = mask[mask.outcome == oc].set_index("funding").reindex(order)
        x = np.arange(3) + (j - 0.5) * 0.18
        a.errorbar(x, d.coef, yerr=1.96 * d.se, fmt="o-", color=c, capsize=3, label=nm)
    a.set_xticks(range(3), ["Funding then rose\nless than usual", "About usual", "More than usual"])
    a.set_ylabel("How much of FEWS NET's added judgment comes true\n(coefficient, as in B; all areas)")
    a.set_title("D. Masking test: if aid prevents crises, the red line\n(mapped) should fall where money flowed; blue (need) should not",
                loc="left", fontweight="bold", fontsize=10.5)
    a.legend(fontsize=8.5, frameon=False)
    fig.suptitle("Does FEWS NET know something public data don't, and does money follow it? (2011-2024)", x=0.01,
                 ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    fig.text(0.01, 0.01, textwrap.fill(
        "FEWS NET areas x map rounds. Forecast: Crisis or worse (Phase 3+) in the medium-term projection for the month "
        "of the area's next map. Public part: out-of-year prediction of that forecast from the area's current and two "
        "previous maps (phase and aid flag), the country's current share in Crisis, country and season, and local "
        "rainfall (CHIRPS), political violence (ACLED) and cereal prices (WFP) before the forecast. Added judgment = "
        "forecast minus public part. B: area and country x round comparisons, clustered by country; the Cadre "
        "Harmonise / IPC check also controls for the latest independent analysis. C: country x round, with funding in "
        "the previous 6 months. D: funding surprise = funding in the next 6 months relative to the country's usual "
        "level and recent funding.", 220), fontsize=7.5, color="#555")
    fig.savefig(FIG / "forecast_value.pdf")
    fig.savefig(FIG / "forecast_value.png", dpi=150)


if __name__ == "__main__":
    import sys
    if "figure" in sys.argv:
        figure(pd.read_csv(TAB / "forecast_value.csv"), pd.read_csv(TAB / "forecast_value_auc.csv"),
               pd.read_csv(TAB / "forecast_value_masking.csv"))
    else:
        main()
