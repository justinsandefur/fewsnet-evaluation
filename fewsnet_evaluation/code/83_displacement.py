"""Displacement as an outcome: Somalia, 2016-2023.

UNHCR's Protection and Return Monitoring Network (PRMN) records people newly displaced each week, with
the district they left, the district they reached and the reason (drought, conflict/insecurity,
flood, other), April 2016 - August 2023 (input/displacement/prmn/). We count departures by origin
district and month, all reasons and drought-related only. Displacement is an outcome neither FEWS NET
nor the IPC produces, so it is a check on FEWS NET's forecasts that does not share its analysts.

1. Do FEWS NET's forecasts predict displacement?  District x FEWS NET round. FEWS NET's map and forecast,
   and the split of the forecast into the part public data predict (b_fc3) and FEWS NET's own
   contribution (c_fc3), from 33_fewsnet_contribution.py, are averaged over the FEWS NET areas covering
   each district (weights: share of the district's area in each area, from 32_forecast_value.py's
   overlay of OCHA districts). Outcome: log(1 + departures from the district over the six months after
   the round).
     log(1 + dep_next6) = a log(1 + dep_prev6) + b_b b_fc3 + b_c c_fc3 + district FE + round FE
   clustered by district. Out of sample (gradient boosting cross-fitted by year): R-squared for
   log departures from public data and past departures, with and without FEWS NET's map and forecast.

2. Does warning keep people home?  Need-defined Crisis and Emergency onsets in Somalia (30_need_onsets.py:
   need = mapped phase + 1 if flagged as held back by aid). Departures from the FEWS NET area (district
   departures apportioned by area share) over the 6 and 12 months after the onset, against early
   warning (forecast issued 4-8 months before reached the level), late warning (1-3 months) or none,
   and against whether the onset was averted (held back by aid on FEWS NET's own account).
     log(1 + dep_post) = a log(1 + dep_pre6) + b_e early + b_l late + month FE
   clustered by region (first administrative level).

Outputs: output/tables/displacement_forecast.csv, displacement_onsets.csv, displacement_oos.csv,
         displacement_key.json; input/panel/displacement_district_rounds.parquet,
         input/panel/displacement_onsets.parquet
"""
import importlib.util
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
FIRST, LAST = pd.Period("2016-04", "M"), pd.Period("2023-08", "M")   # full PRMN months
ALIAS = {"baidoa": "SO2401", "xarardheere": "SO1805", "kismayo": "SO2801",
         "badhan": "SO1503", "dhahar": "SO1503", "lasqoray": "SO1503"}   # Badhan, Dhahar: split from Laasqoray
AREA_VARS = ["cur3", "fc3", "b_fc3", "c_fc3", "bi_fc3", "ci_fc3", "flag", "rain_z6", "rain_z12", "ln_ev6", "d_ln_ev6", "dp12"]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())


def departures():
    """Monthly departures by origin district (OCHA pcode): all reasons, drought-related, conflict."""
    d = pd.read_excel(INP / "displacement" / "prmn" / "prmn.xlsx")
    m = pd.read_csv(INP / "displacement" / "prmn" / "prmn_map.csv")
    code = {norm(a): b for a, b in zip(m.CurrentMapDistrict, m.admin2_pcode)}
    code.update({norm(a): b for a, b in zip(m.admin2_name, m.admin2_pcode)})
    code.update(ALIAS)
    d["pcode"] = d["Previous (Departure) District"].map(norm).map(code)
    d["month"] = pd.to_datetime(d["Month End"], dayfirst=True).dt.to_period("M")
    n = d["Number of Individuals"]
    unmatched = n[d.pcode.isna()].sum() / n.sum()
    d = d[d.pcode.notna() & d.month.between(FIRST, LAST)]
    d["dep"] = d["Number of Individuals"]
    d["dep_drought"] = d.dep.where(d.Reason == "Drought related", 0)
    d["dep_conflict"] = d.dep.where(d.Reason == "Conflict/Insecurity", 0)
    g = d.groupby(["pcode", "month"])[["dep", "dep_drought", "dep_conflict"]].sum()
    months = pd.period_range(FIRST, LAST, freq="M")
    codes = sorted(set(m.admin2_pcode) | set(g.index.get_level_values(0)))
    g = g.reindex(pd.MultiIndex.from_product([codes, months], names=["pcode", "month"]), fill_value=0)
    return g.reset_index(), float(unmatched), float(d.dep.sum())


def district_population():
    """WorldPop 2020 people per Somalia district (OCHA boundaries)."""
    import geopandas as gpd
    import rasterio
    from rasterio.mask import mask
    x = gpd.read_file(f"zip://{INP / 'areas' / 'codab' / 'som.geojson.zip'}!som_admin2.geojson")
    out = {}
    with rasterio.open(INP / "worldpop" / "SOM.tif") as src:
        x = x.to_crs(src.crs)
        for r in x.itertuples():
            a, _ = mask(src, [r.geometry], crop=True, nodata=0)
            if np.clip(a, 0, None).sum() == 0:      # districts smaller than a pixel (e.g. Bondhere, Mogadishu)
                a, _ = mask(src, [r.geometry], crop=True, nodata=0, all_touched=True)
            out[r.adm2_pcode] = float(np.clip(a, 0, None).sum())
    return pd.Series(out, name="pop")


def _fe(d, y, xs, fes, cl):
    """OLS with fixed effects absorbed by alternating projections; cluster-robust SEs scaled by G/(G-1),
    singletons dropped once per fixed effect (the conventions of fe_ols in 25_slope_did.py)."""
    d = d.dropna(subset=[y] + xs).copy()
    for f in fes:                                   # drop singletons once per fixed effect
        d = d[d.groupby(f)[y].transform("size") > 1]
    cols = [y] + xs
    Z = d[cols].astype(float).copy()
    for _ in range(200):
        old = Z.values.copy()
        for f in fes:
            Z = Z - Z.groupby(d[f].values).transform("mean")
        if np.abs(Z.values - old).max() < 1e-10:
            break
    X, Y = Z[xs].values, Z[y].values
    XtX = np.linalg.inv(X.T @ X)
    b = XtX @ X.T @ Y
    e = Y - X @ b
    G = d[cl].nunique()
    meat = np.zeros((len(xs), len(xs)))
    for _, idx in d.groupby(cl).indices.items():
        s = X[idx].T @ e[idx]
        meat += np.outer(s, s)
    V = XtX @ meat @ XtX * G / (G - 1)
    return pd.Series(b, xs), pd.Series(np.sqrt(np.diag(V)), xs), len(d), G


def district_rounds(dep, pop):
    """District x FEWS NET round: FEWS NET and public signals averaged over the areas covering the district."""
    P = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet")
    P = P[P.country_code == "SO"].copy()
    P["r"] = pd.PeriodIndex(P.r.astype(str), freq="M")
    P["flag"] = P.assist_flag.astype(float)
    W = pd.read_parquet(INP / "panel" / "fnid_acled_weights.parquet").rename(columns={"Admin2 Pcode": "pcode"})
    W = W[W.pcode.str.startswith("SO")]
    x = P[["fnid", "r"] + AREA_VARS].merge(W[["pcode", "fnid", "w"]], on="fnid")
    rows = []
    for (pc, r), g in x.groupby(["pcode", "r"]):
        rec = {"pcode": pc, "r": r, "wsum": g.w.sum()}
        for v in AREA_VARS:
            ok = g[v].notna()
            rec[v] = np.average(g.loc[ok, v], weights=g.loc[ok, "w"]) if ok.any() and g.loc[ok, "w"].sum() > 0 else np.nan
        rows.append(rec)
    D = pd.DataFrame(rows)
    D = D[D.wsum > 0.5]                                # district at least half covered by mapped areas
    wide = {c: dep.set_index(["pcode", "month"])[c].unstack() for c in ["dep", "dep_drought", "dep_conflict"]}
    cum = {c: w.cumsum(axis=1) for c, w in wide.items()}
    for c in cum:
        cum[c].insert(0, FIRST - 1, 0.0)

    def s(c, pc, t, a, b):
        lo, hi = t + a, t + b
        if lo < FIRST or hi > LAST or pc not in cum[c].index:
            return np.nan
        return cum[c].at[pc, hi] - cum[c].at[pc, lo - 1]
    for c in ["dep", "dep_drought", "dep_conflict"]:
        D[f"{c}_next6"] = [s(c, pc, r, 1, 6) for pc, r in zip(D.pcode, D.r)]
        D[f"{c}_prev6"] = [s(c, pc, r, -6, -1) for pc, r in zip(D.pcode, D.r)]
        D[f"ln_{c}_next6"], D[f"ln_{c}_prev6"] = np.log1p(D[f"{c}_next6"]), np.log1p(D[f"{c}_prev6"])
    D["pop"] = D.pcode.map(pop)
    D["region"] = D.pcode.str[:4]
    D["round"] = D.r.astype(str)
    D["yr"] = D.r.dt.year
    D["tmonth"] = D.r.dt.month
    return D.dropna(subset=["dep_next6", "dep_prev6"]).reset_index(drop=True)


def oos(D, y):
    """Cross-fitted (by year) R-squared for y: public signals and past departures, with and without FEWS NET."""
    pub = ["rain_z6", "rain_z12", "ln_ev6", "d_ln_ev6", "dp12", "tmonth", f"ln_{y}_prev6", "lpop"]
    D = D.assign(lpop=np.log(D["pop"]))
    out = {}
    for name, feats in [("public", pub), ("public + FEWS NET", pub + ["cur3", "fc3"])]:
        pred = pd.Series(np.nan, index=D.index)
        for yr in sorted(D.yr.unique()):
            te = D.yr == yr
            m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=1)
            m.fit(D.loc[~te, feats], D.loc[~te, f"ln_{y}_next6"])
            pred[te] = m.predict(D.loc[te, feats])
        t = D[f"ln_{y}_next6"]
        out[name] = 1 - ((t - pred) ** 2).sum() / ((t - t.mean()) ** 2).sum()
    return out


def onsets(dep):
    """Need-defined onsets in Somalia with departures from the FEWS NET area before and after."""
    E = pd.read_parquet(INP / "panel" / "need_onsets.parquet")
    E = E[E.country_code == "SO"].copy()
    E["month"] = pd.PeriodIndex(E.month.astype(str), freq="M")
    W = pd.read_parquet(INP / "panel" / "fnid_acled_weights.parquet").rename(columns={"Admin2 Pcode": "pcode"})
    W = W[W.pcode.str.startswith("SO") & W.fnid.isin(E.fnid)]
    # departures from each area: district departures x share of the district's area inside it
    a = dep.merge(W[["pcode", "fnid", "w"]], on="pcode")
    for c in ["dep", "dep_drought"]:
        a[c] = a[c] * a.w
    A = a.groupby(["fnid", "month"])[["dep", "dep_drought"]].sum()
    cum = {c: A[c].unstack().cumsum(axis=1) for c in ["dep", "dep_drought"]}
    for c in cum:
        cum[c].insert(0, FIRST - 1, 0.0)

    def s(c, f, t, lo, hi):
        lo, hi = t + lo, t + hi
        if lo < FIRST or hi > LAST or f not in cum[c].index:
            return np.nan
        return cum[c].at[f, hi] - cum[c].at[f, lo - 1]
    for c in ["dep", "dep_drought"]:
        for nm, lo, hi in [("pre6", -6, -1), ("post6", 1, 6), ("post12", 1, 12)]:
            E[f"{c}_{nm}"] = [s(c, f, t, lo, hi) for f, t in zip(E.fnid, E.month)]
            E[f"ln_{c}_{nm}"] = np.log1p(E[f"{c}_{nm}"])
    main = W.sort_values("w", ascending=False).drop_duplicates("fnid").set_index("fnid").pcode
    E["region"] = E.fnid.map(main).str[:4]
    E["mcell"] = E.month.astype(str)
    E["early"] = E.group_ph.str.startswith("early").astype(float)
    E["late"] = E.group_ph.str.startswith("late").astype(float)
    return E.dropna(subset=["dep_pre6", "region"])


def main():
    dep, unmatched, total = departures()
    pop = district_population()
    D = district_rounds(dep, pop)
    D.to_parquet(INP / "panel" / "displacement_district_rounds.parquet", index=False)
    key = {"unmatched_share": unmatched, "departures_total": total,
           "months": [str(FIRST), str(LAST)], "districts": int(D.pcode.nunique()), "rounds": int(D.r.nunique()),
           "district_rounds": int(len(D)), "years": [int(D.yr.min()), int(D.yr.max())],
           "dep_per_year_median_share": float((D.dep_next6 * 2 / D["pop"]).median()),
           "dep_per_year_p90_share": float((D.dep_next6 * 2 / D["pop"]).quantile(0.9)),
           "drought_share": float(D.dep_drought_next6.sum() / D.dep_next6.sum())}
    rows = []
    for y in ["dep", "dep_drought", "dep_conflict"]:
        for spec, xs in [("map and forecast", ["cur3", "fc3"]), ("forecast split", ["b_fc3", "c_fc3"]),
                         ("forecast split, + IPC", ["bi_fc3", "ci_fc3"])]:
            b, se, n, G = _fe(D, f"ln_{y}_next6", xs + [f"ln_{y}_prev6"], ["pcode", "round"], "pcode")
            for t in xs + [f"ln_{y}_prev6"]:
                rows.append(dict(outcome=y, spec=spec, term=t, coef=b[t], se=se[t], n=n, clusters=G))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "displacement_forecast.csv", index=False)
    O = pd.DataFrame([dict(outcome=y, model=k, r2=v) for y in ["dep", "dep_drought"] for k, v in oos(D, y).items()])
    O.to_csv(TAB / "displacement_oos.csv", index=False)
    # simple correlations within round (as the IPC-surveys paper reports for the IPC)
    for y in ["dep", "dep_drought"]:
        v = ["fc3", "cur3", f"ln_{y}_next6"]
        dm = D[v] - D.groupby("round")[v].transform("mean")
        key[f"corr_fc3_{y}"] = float(np.corrcoef(dm.fc3.astype(float), dm[f"ln_{y}_next6"].astype(float))[0, 1])
        key[f"corr_cur3_{y}"] = float(np.corrcoef(dm.cur3.astype(float), dm[f"ln_{y}_next6"].astype(float))[0, 1])

    E = onsets(dep)
    E.to_parquet(INP / "panel" / "displacement_onsets.parquet", index=False)
    rows = []
    for lvl in ["Emergency", "Crisis"]:
        e = E[E.onset == lvl]
        for y in ["dep", "dep_drought"]:
            for post in ["post6", "post12"]:
                for spec, xs in [("warning", ["early", "late"]), ("averted", ["averted"])]:
                    b, se, n, G = _fe(e, f"ln_{y}_{post}", xs + [f"ln_{y}_pre6"], ["mcell"], "region")
                    for t in xs:
                        rows.append(dict(onset=lvl, outcome=y, window=post, spec=spec, term=t, coef=b[t], se=se[t],
                                         n=n, clusters=G, mean_post=float(e[f"{y}_{post}"].mean())))
        key[f"onsets_{lvl}"] = int(len(e))
        key[f"onsets_{lvl}_early"] = int(e.early.sum())
        key[f"onsets_{lvl}_averted"] = int(e.averted.sum())
    pd.DataFrame(rows).to_csv(TAB / "displacement_onsets.csv", index=False)
    (TAB / "displacement_key.json").write_text(json.dumps(key, indent=1))
    pd.set_option("display.width", 200)
    print(json.dumps(key, indent=1))
    print(R.round(3).to_string())
    print(O.round(3).to_string())
    print(pd.read_csv(TAB / "displacement_onsets.csv").round(3).to_string())


if __name__ == "__main__":
    main()
