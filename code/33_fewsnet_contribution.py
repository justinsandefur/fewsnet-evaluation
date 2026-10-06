"""What would donors know without FEWS NET? FEWS NET's contribution over raw data
and other assessments.

32_forecast_value.py treated FEWS NET's own current and past maps as "public".
Here the comparison is a world without FEWS NET:
  raw          rainfall (CHIRPS), political violence (ACLED), cereal prices (WFP),
               country and season
  raw + IPC    the same plus the latest Cadre Harmonise / IPC analysis of the area
               (FEWS NET analysts take part in many of these, so this baseline
               already contains some FEWS NET input: an upper bound on what
               donors would have without it)
FEWS NET's signals are its current map and its medium-term forecast (Phase 3+).
FEWS NET's contribution = signal minus its out-of-year prediction from the
baseline (gradient boosting, cross-fitted by year).

1. Accuracy, scored only against independent outcomes: Phase 3+ in the next
   Cadre Harmonise / IPC analysis of the area (FEWS NET signals and shocks
   overlaid onto Cadre Harmonise / IPC areas, area-weighted).
     - AUC for areas tipping into Crisis: baseline vs baseline + FEWS NET
     - y = a baseline prediction of y + b FEWS NET contribution + FE(country x round)
2. Money: country x round funding over the next 6 months (FTS) on the country
   means of FEWS NET's contribution and of the baseline part, with prior
   funding, country and time fixed effects (all 28 FEWS NET countries; raw
   baseline, since Cadre Harmonise / IPC is missing for many).

Outputs: output/tables/fewsnet_contribution*.csv, output/figures/fewsnet_contribution.pdf
"""
import importlib.util
import textwrap
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
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
FV = load("fv", "32_forecast_value.py")
AID = load("aid", "31_aid_response.py")
RAW = ["cty", "tmonth", "rain_z6", "rain_z12", "ln_ev6", "ln_fat6", "d_ln_ev6", "dp12", "dp3"]
SHOCKS = ["rain_z6", "rain_z12", "ln_ev6", "ln_fat6", "d_ln_ev6", "dp12", "dp3"]


def crossfit(d, y, feats, binary=True):
    X = d[feats]
    pred = pd.Series(np.nan, index=d.index)
    cat = [feats.index("cty")] if "cty" in feats else None
    for yr in sorted(d.r.dt.year.unique()):
        te = d.r.dt.year == yr
        if (~te).sum() < 100 or d.loc[~te, y].nunique() < 2:
            continue
        M = HistGradientBoostingClassifier if binary else HistGradientBoostingRegressor
        m = M(max_iter=300, learning_rate=0.08, max_leaf_nodes=31, categorical_features=cat, random_state=1)
        m.fit(X[~te], d.loc[~te, y])
        pred[te] = m.predict_proba(X[te])[:, 1] if binary else m.predict(X[te])
    return pred


def overlay(units, o, isos):
    f = CACHE / "fnid_ipc_overlay.parquet"
    if f.exists():
        return pd.read_parquet(f)
    geo, _ = RAIN.area_geometries(pd.read_parquet(INP / "panel" / "outcomes.parquet"))
    keys = o[["key", "iso3"]].drop_duplicates("key")
    g = geo.merge(keys, on="key").drop_duplicates("key")
    g = g[g.iso3.isin(isos)].to_crs(6933)
    g["geometry"] = g.geometry.buffer(0)
    g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])]
    g["key_area"] = g.area
    u = units.to_crs(6933)
    u["fnid_area"] = u.area
    x = gpd.overlay(g[["key", "key_area", "geometry"]], u[["fnid", "fnid_area", "geometry"]], how="intersection",
                    keep_geom_type=True)
    x["w_key"] = x.area / x.key_area           # share of the Cadre Harmonise / IPC area in the FEWS NET area
    x["w_fnid"] = x.area / x.fnid_area         # share of the FEWS NET area in the Cadre Harmonise / IPC area
    x = x[(x.w_key > 0.01) | (x.w_fnid > 0.01)][["key", "fnid", "w_key", "w_fnid"]]
    x.to_parquet(f, index=False)
    return x


def ipc_history(o):
    o = o.dropna(subset=["phase"]).copy()
    o["ph3"] = (o.phase >= 3).astype(float)
    oo = o.groupby(["key", "month"]).agg(ph3=("ph3", "max"), share3=("share3", "mean")).reset_index()
    oo["mi"] = oo.month.astype("int64")
    return oo.sort_values("mi")


def main():
    p = pd.read_parquet(CACHE / "forecast_value_panel.parquet")
    p["fc3"] = p.f3
    outcomes = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    _, o = RAIN.area_geometries(outcomes)
    units = FV.unit_geoms(p.fnid.unique())
    W = overlay(units, o, p.iso3.unique())
    oo = ipc_history(o)

    # ---------------- A. FEWS NET area level: baseline predictions of FEWS NET's own signals (for funding)
    # latest Cadre Harmonise / IPC at r, as a feature for FEWS NET areas (area-weighted, NaN where none)
    fw = W.merge(oo[["key", "mi", "ph3", "share3"]], on="key")
    p["mi"] = p.r.astype("int64")
    last = []
    for r_, g in p.groupby("mi"):
        h = fw[(fw.mi <= r_) & (fw.mi > r_ - 8)].sort_values("mi").groupby(["key", "fnid"]).last().reset_index()
        h["wp"], h["ws"] = h.w_fnid * h.ph3, h.w_fnid * h.share3
        a = h.groupby("fnid").agg(wp=("wp", "sum"), ws=("ws", "sum"), w=("w_fnid", "sum"))
        a = a[a.w > 0.5]
        last.append(pd.DataFrame({"fnid": a.index.values, "mi": r_, "ipc_last3": (a.wp / a.w).values, "ipc_last_share3": (a.ws / a.w).values}))
    p = p.merge(pd.concat(last), on=["fnid", "mi"], how="left")
    print("FEWS NET area-rounds with a recent Cadre Harmonise / IPC analysis:", round(p.ipc_last3.notna().mean(), 3))
    for s in ["cur3", "fc3"]:
        p[f"b_{s}"] = crossfit(p, s, RAW)                                 # raw baseline
        p[f"bi_{s}"] = crossfit(p, s, RAW + ["ipc_last3", "ipc_last_share3"])  # raw + IPC (NaN where none)
        p[f"c_{s}"], p[f"ci_{s}"] = p[s] - p[f"b_{s}"], p[s] - p[f"bi_{s}"]
        print("cross-fitted baselines for", s, flush=True)
    p.to_parquet(CACHE / "fewsnet_contribution_panel.parquet", index=False)

    # ---------------- B. Cadre Harmonise / IPC area level: accuracy against independent outcomes
    m = W.merge(p[["fnid", "r", "iso3", "cty", "tmonth", "cur3", "fc3"] + SHOCKS], on="fnid")
    agg = {}
    for v in ["cur3", "fc3"] + SHOCKS:
        m[v + "_w"] = m[v] * m.w_key
        m[v + "_n"] = m[v].notna() * m.w_key
        agg[v + "_w"] = (v + "_w", "sum")
        agg[v + "_n"] = (v + "_n", "sum")
    k = m.groupby(["key", "r", "iso3"]).agg(cty=("cty", "first"), tmonth=("tmonth", "first"), w=("w_key", "sum"),
                                             **agg).reset_index()
    k = k[k.w > 0.5]
    for v in ["cur3", "fc3"] + SHOCKS:
        k[v] = (k[v + "_w"] / k[v + "_n"]).where(k[v + "_n"] > 0.25)
    k["mi"] = k.r.astype("int64")
    k = k.sort_values("mi")
    k = pd.merge_asof(k, oo[["key", "mi", "ph3", "share3"]], on="mi", by="key", direction="backward", tolerance=8) \
        .rename(columns={"ph3": "ipc_last3", "share3": "ipc_last_share3"})
    nxt = oo.assign(mi=oo.mi - 1)
    k = pd.merge_asof(k.sort_values("mi"), nxt[["key", "mi", "ph3", "share3"]], on="mi", by="key",
                      direction="forward", tolerance=7).rename(columns={"ph3": "ipc3", "share3": "ipc_share3"})
    k = k.dropna(subset=["ipc3", "cur3", "fc3"]).reset_index(drop=True)
    print("Cadre Harmonise / IPC area-rounds:", len(k), "countries", k.iso3.nunique(), flush=True)
    base = {"raw data": RAW, "raw data + latest Cadre Harmonise / IPC": RAW + ["ipc_last3", "ipc_last_share3"]}
    rows, auc = [], []
    k["cell"] = k.iso3 + "_" + k.r.astype(str)
    for bl, feats in base.items():
        k["q"] = crossfit(k, "ipc3", feats)
        k["q_f"] = crossfit(k, "ipc3", feats + ["cur3", "fc3"])
        for s in ["cur3", "fc3"]:
            k[f"c_{s}"] = k[s] - crossfit(k, s, feats, binary=False)
        for samp, d in [("all areas", k), ("areas not in Crisis at last analysis", k[k.ipc_last3 == 0])]:
            dd = d.dropna(subset=["q", "q_f"])
            for mdl, col in [("baseline", "q"), ("baseline + FEWS NET", "q_f")]:
                auc.append({"baseline": bl, "sample": samp, "model": mdl, "auc": roc_auc_score(dd.ipc3, dd[col]),
                            "events": int(dd.ipc3.sum()), "n": len(dd)})
            for xs, lab in [(["q", "c_fc3"], "forecast"), (["q", "c_cur3"], "current map"),
                            (["q", "c_cur3", "c_fc3"], "both")]:
                r, n, G = DID.fe_ols(dd, "ipc3", xs, ["cell"])
                for t in xs[1:]:
                    rows.append({"block": "accuracy (next Cadre Harmonise / IPC)", "baseline": bl, "sample": samp,
                                 "spec": lab, "term": t, "coef": r.coef[t], "se": r.se[t], "n": n, "countries": G,
                                 "q_coef": r.coef["q"]})
    auc = pd.DataFrame(auc)
    auc.to_csv(TAB / "fewsnet_contribution_auc.csv", index=False)
    pd.set_option("display.width", 240)
    print(auc.round(3).to_string())

    # ---------------- C. money (all FEWS NET countries; raw baseline, and raw + IPC where available)
    s = AID.panel()
    for pref, bl in [("", "raw data"), ("i", "raw data + latest Cadre Harmonise / IPC")]:
        c = p.groupby(["country_code", "r"]).agg(**{f"base_{v}": (f"b{pref}_{v}", "mean") for v in ["cur3", "fc3"]},
                                                 **{f"contrib_{v}": (f"c{pref}_{v}", "mean") for v in ["cur3", "fc3"]}
                                                 ).reset_index()
        ss = s.merge(c, left_on=["country_code", "report_month"], right_on=["country_code", "r"])
        for col in ["all", "food"]:
            for fl, fes in [("within country", ["iso3", "round"]), ("across countries", ["round"])]:
                for sig in ["fc3", "cur3"]:
                    xs = [f"base_{sig}", f"contrib_{sig}", f"f_{col}_lag"]
                    r, n, G = DID.fe_ols(ss, f"f_{col}", xs, fes)
                    for t in xs[:2]:
                        rows.append({"block": "funding", "baseline": bl, "sample": f"{col} funding, {fl}",
                                     "spec": "forecast" if sig == "fc3" else "current map", "term": t,
                                     "coef": r.coef[t], "se": r.se[t], "n": n, "countries": G})
    R = pd.DataFrame(rows)
    R["t"] = R.coef / R.se
    R.to_csv(TAB / "fewsnet_contribution.csv", index=False)
    print(R.round(3).to_string())
    figure(R, auc)


def figure(R, auc):
    fig, ax = plt.subplots(1, 3, figsize=(17, 6.2), gridspec_kw={"width_ratios": [1, 1.1, 1.25]})
    bls = ["raw data", "raw data + latest Cadre Harmonise / IPC"]
    bshort = {"raw data": "Raw data only", "raw data + latest Cadre Harmonise / IPC": "Raw data + latest\nCadre Harmonise / IPC"}
    # A. AUC
    a = ax[0]
    s = auc[auc["sample"] == "areas not in Crisis at last analysis"]
    for i, bl in enumerate(bls):
        for j, (mdl, c) in enumerate([("baseline", "#bdbdbd"), ("baseline + FEWS NET", "#1f4e79")]):
            v = s[(s.baseline == bl) & (s.model == mdl)].auc.iloc[0]
            a.bar(i + (j - 0.5) * 0.36, v, 0.36, color=c, label=("Without FEWS NET" if j == 0 else "Adding FEWS NET's current map and forecast") if i == 0 else None)
            a.text(i + (j - 0.5) * 0.36, v + 0.005, f"{v:.2f}", ha="center", fontsize=9)
    a.set_xticks([0, 1], [bshort[b] for b in bls])
    a.set_ylim(0.5, 1)
    a.set_ylabel("How well areas tipping into Crisis in the next independent\nanalysis are ranked (AUC: 0.5 = coin flip, 1 = perfect)")
    a.set_title("A. Predicting the next independent analysis", loc="left", fontweight="bold", fontsize=10.5)
    a.legend(fontsize=8, frameon=False, loc="upper left")
    # B. accuracy coefficients
    a = ax[1]
    acc = R[(R.block.str.startswith("accuracy")) & (R["sample"] == "areas not in Crisis at last analysis") & (R.spec == "both")]
    y = 0
    ticks = []
    for bl in bls:
        for t, lab, c in [("c_cur3", "current map", "#6baed6"), ("c_fc3", "forecast", "#1f4e79")]:
            r = acc[(acc.baseline == bl) & (acc.term == t)].iloc[0]
            a.errorbar(r.coef, -y, xerr=1.96 * r.se, fmt="o", color=c, capsize=3)
            ticks.append((-y, f"{bshort[bl].replace(chr(10), ' ')}:\nFEWS NET {lab}"))
            y += 1
        y += 0.5
    a.set_yticks([t for t, _ in ticks], [l for _, l in ticks], fontsize=8.5)
    a.axvline(0, color="#999", lw=0.8)
    a.set_xlabel("Rise in the chance the area is in Crisis+ in the next\nindependent analysis, per unit of FEWS NET's contribution")
    a.set_title("B. Is FEWS NET's contribution borne out?\n(areas not in Crisis at the last analysis)", loc="left",
                fontweight="bold", fontsize=10.5)
    # C. funding
    a = ax[2]
    fu = R[(R.block == "funding") & (R.spec == "forecast")]
    items = [(bl, sm) for bl in bls for sm in ["all funding, within country", "food funding, within country"]]
    pct = lambda b: 100 * (np.exp(0.1 * b) - 1)
    for i, (bl, sm) in enumerate(items):
        for j, (t, c, nm) in enumerate([("base_fc3", "#bdbdbd", "Part of the forecast predictable without FEWS NET"),
                                        ("contrib_fc3", "#1f4e79", "FEWS NET's contribution")]):
            r = fu[(fu.baseline == bl) & (fu["sample"] == sm) & (fu.term == t)].iloc[0]
            yy = -i + (0.15 if j == 0 else -0.15)
            a.errorbar(pct(r.coef), yy, xerr=[[pct(r.coef) - pct(r.coef - 1.96 * r.se)], [pct(r.coef + 1.96 * r.se) - pct(r.coef)]],
                       fmt="o", color=c, capsize=3, label=nm if i == 0 else None)
    a.set_yticks([-i for i in range(len(items))],
                 [f"{bshort[bl].replace(chr(10), ' ')}:\n{sm.replace(', within country', '')} (within country)" for bl, sm in items], fontsize=8.5)
    a.axvline(0, color="#999", lw=0.8)
    a.set_xlabel("% change in funding over the next 6 months per 10-point rise\nin the share of the country's areas forecast in Crisis+")
    a.set_title("C. Does money follow FEWS NET's contribution?", loc="left", fontweight="bold", fontsize=10.5)
    a.legend(fontsize=8, frameon=False, loc="upper right", bbox_to_anchor=(1, 1.0))
    a.set_ylim(-len(items) + 0.4, 0.9)
    fig.suptitle("What would donors know without FEWS NET? Its contribution beyond raw data and other assessments (2011-2024)",
                 x=0.01, ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout(rect=(0, 0.1, 1, 0.94))
    fig.text(0.01, 0.01, textwrap.fill(
        "Raw data: rainfall (CHIRPS), political violence (ACLED), cereal prices (WFP), country and season, all before the "
        "forecast. FEWS NET's contribution: its current map or medium-term forecast (Phase 3+) minus an out-of-year "
        "prediction of it from the baseline. A and B: Cadre Harmonise / IPC areas in 24 countries (21 with areas not in Crisis at the last analysis), FEWS NET signals "
        "overlaid by area; outcome is Phase 3+ in the next independent analysis; B compares areas in the same country and "
        "round, controlling for the baseline's own prediction of the outcome, clustered by country. FEWS NET analysts take "
        "part in many Cadre Harmonise / IPC analyses, so neither the baseline nor the outcome is fully independent of it. "
        "C: country x round, 28 countries, with prior funding, country and time fixed effects.", 230),
        fontsize=7.5, color="#555")
    fig.savefig(FIG / "fewsnet_contribution.pdf")
    fig.savefig(FIG / "fewsnet_contribution.png", dpi=150)


if __name__ == "__main__":
    import sys
    if "figure" in sys.argv:
        figure(pd.read_csv(TAB / "fewsnet_contribution.csv"), pd.read_csv(TAB / "fewsnet_contribution_auc.csv"))
    else:
        main()
