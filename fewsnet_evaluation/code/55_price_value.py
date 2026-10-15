"""How much do market prices help forecast food crises, and does price coverage matter?

Unit: FEWS NET area x map round r, 2011-2024 (input/panel/forecast_value_panel.parquet).
Price signal: 3- and 12-month log changes in retail staple prices at the nearest
reporting market within 150 km, averaged over months r-3..r-1, from
  WFP    WFP VAM (input/prices/, as in 32_forecast_value.py), and
  FEWS   prices in FEWS NET's data warehouse collected by FEWS NET or the
         government and partner systems it compiles, excluding WFP-sourced
         series (input/prices_fdw/, 54_fetch_fdw_prices.py).

Task: among areas not in Crisis (Phase 3+) at r, predict Crisis+ on the next map
(new crises), and among areas in Crisis, predict Emergency+ (escalation).
Cross-fitted (by year) gradient-boosted models; AUC with and without prices:
  base       country, calendar month, horizon, current and two previous maps,
             national share in Crisis+, rainfall and political violence
  raw        country, calendar month, horizon, rainfall and political violence
             only (what a donor could see without FEWS NET)
  +WFP, +FEWS, +both prices
  +forecast  base plus FEWS NET's own medium-term forecast (for scale)
Scored on all area-rounds and on subsamples by which price sources exist.

Outputs: output/tables/price_value.csv, price_value_coverage.csv;
         input/panel/price_value_preds.parquet (cross-fitted predictions, for bootstrap intervals)
"""
import importlib.util
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SHK = load("shk", "27_shock_index.py")


def fdw_prices():
    """Market x month mean 3- and 12-month log price changes, non-WFP series in FEWS NET's warehouse."""
    d = pd.read_parquet(INP / "prices_fdw/prices.parquet")
    d = d[~d.source_organization.str.contains("WFP", case=False, na=False) & (d.price > 0)]
    d["month"] = pd.PeriodIndex(d.month.astype(str), freq="M")
    d["series"] = d.market_id.astype(str) + "|" + d.cpcv2 + "|" + d.unit.astype(str) + "|" + d.currency.astype(str)
    s = d.groupby(["series", "month"]).agg(lp=("price", lambda x: np.log(x).mean()), market=("market_id", "first"),
                                           lat=("latitude", "first"), lon=("longitude", "first")).reset_index()
    s["mi"] = s.month.astype("int64")
    for k in [3, 12]:
        prev = s[["series", "mi", "lp"]].copy()
        prev["mi"] = prev.mi + k
        s = s.merge(prev.rename(columns={"lp": f"lp_{k}"}), on=["series", "mi"], how="left")
        s[f"dp{k}"] = s.lp - s[f"lp_{k}"]
    m = s.groupby(["market", "month"]).agg(dp12=("dp12", "mean"), dp3=("dp3", "mean"),
                                           lat=("lat", "first"), lon=("lon", "first")).reset_index()
    return m.dropna(subset=["lat", "lon"])


def area_prices(m, units, rounds, tag):
    """Nearest market within 150 km that reported in r-3..r-1 (chosen per round, not once)."""
    c = units.copy()
    c["geometry"] = c.geometry.representative_point()
    c = c.to_crs(6933)
    out = []
    for r in rounds:
        w = m[m.month.isin([r - 1, r - 2, r - 3])].groupby("market").agg(
            dp12=("dp12", "mean"), dp3=("dp3", "mean"), lat=("lat", "first"), lon=("lon", "first")).reset_index()
        w = w.dropna(subset=["dp3", "dp12"], how="all")
        if w.empty:
            continue
        pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat), crs=4326).to_crs(6933)
        j = gpd.sjoin_nearest(c[["fnid", "geometry"]], pts[["dp3", "dp12", "geometry"]], max_distance=150_000)
        j = j.groupby("fnid")[["dp3", "dp12"]].mean().reset_index()
        out.append(j.assign(r=r))
    x = pd.concat(out)
    return x.rename(columns={"dp3": f"dp3_{tag}", "dp12": f"dp12_{tag}"})


RAW = ["cty", "tmonth", "horizon", "rain_z6", "rain_z12", "ln_ev6", "ln_fat6", "d_ln_ev6"]
BASE = ["cty", "phase", "flag", "prev_phase", "prev_flag", "prev2_phase", "prev2_flag", "nat3", "tmonth",
        "horizon", "rain_z6", "rain_z12", "ln_ev6", "ln_fat6", "d_ln_ev6"]


def crossfit(d, y, feats):
    X = d[feats]
    pred = pd.Series(np.nan, index=d.index)
    cat = [feats.index("cty")]
    for yr in sorted(d.yr.unique()):
        te = d.yr == yr
        if d.loc[~te, y].nunique() < 2:
            continue
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
                                           categorical_features=cat, random_state=1)
        m.fit(X[~te], d.loc[~te, y])
        pred[te] = m.predict_proba(X[te])[:, 1]
    return pred


def main():
    p = pd.read_parquet(INP / "panel/forecast_value_panel.parquet")
    p["r"] = pd.PeriodIndex(p.r.astype(str), freq="M")
    p = p[p.r.dt.year <= 2024].dropna(subset=["next_phase"]).copy()
    p["yr"] = p.r.dt.year
    units = gpd.read_file(INP / "fewsnet/units.gpkg")
    units = units[units.fnid.isin(p.fnid)].drop_duplicates("fnid")[["fnid", "geometry"]]
    rounds = sorted(p.r.unique())
    wfp = SHK.wfp_prices()
    print("price changes: WFP markets", wfp.market.nunique(), flush=True)
    fdw = fdw_prices()
    print("price changes: FEWS NET warehouse (non-WFP) markets", fdw.market.nunique(), flush=True)
    pw = area_prices(wfp.rename(columns={"market": "market"}), units, rounds, "wfp")
    pf = area_prices(fdw, units, rounds, "fews")
    p = p.drop(columns=["dp3", "dp12"]).merge(pw, on=["fnid", "r"], how="left").merge(pf, on=["fnid", "r"], how="left")
    for k in ["dp3", "dp12"]:
        p[f"{k}_both"] = p[[f"{k}_wfp", f"{k}_fews"]].mean(axis=1)
    p["has_wfp"], p["has_fews"] = p.dp12_wfp.notna() | p.dp3_wfp.notna(), p.dp12_fews.notna() | p.dp3_fews.notna()
    p["src"] = np.select([p.has_wfp & p.has_fews, p.has_wfp, p.has_fews], ["both", "WFP only", "FEWS only"], "none")
    cov = p.groupby("country_code").src.value_counts(normalize=True).unstack().fillna(0)
    cov.loc["All"] = p.src.value_counts(normalize=True)
    cov.round(3).to_csv(TAB / "price_value_coverage.csv")
    print(cov.round(2), flush=True)

    p["fc_phase"] = p.fc_phase.astype(float)
    tasks = {"new crisis": (p.phase <= 2, (p.next_phase >= 3).astype(int)),
             "escalation": (p.phase == 3, (p.next_phase >= 4).astype(int))}
    models = {"base": BASE,
              "+WFP prices": BASE + ["dp3_wfp", "dp12_wfp"],
              "+FEWS NET prices": BASE + ["dp3_fews", "dp12_fews"],
              "+both": BASE + ["dp3_wfp", "dp12_wfp", "dp3_fews", "dp12_fews"],
              "+forecast": BASE + ["fc_phase"],
              "raw": RAW,
              "raw +WFP prices": RAW + ["dp3_wfp", "dp12_wfp"],
              "raw +FEWS NET prices": RAW + ["dp3_fews", "dp12_fews"],
              "raw +both": RAW + ["dp3_wfp", "dp12_wfp", "dp3_fews", "dp12_fews"],
              "raw +FEWS NET map and forecast": RAW + ["phase", "flag", "fc_phase"]}
    rows, keep = [], []
    for task, (sel, y) in tasks.items():
        d = p[sel].copy()
        d["y"] = y[sel]
        preds = {name: crossfit(d, "y", f) for name, f in models.items()}
        print("fitted", task, flush=True)
        keep.append(d[["fnid", "r", "country_code", "src", "y"]].assign(task=task, **{k: v for k, v in preds.items()}))
        for sub in ["all", "both", "WFP only", "FEWS only", "none"]:
            s = d.index if sub == "all" else d.index[d.src == sub]
            for name, pr in preds.items():
                ok = pr.loc[s].notna()
                yy, pp = d.loc[s, "y"][ok], pr.loc[s][ok]
                rows.append(dict(task=task, sample=sub, model=name, n=len(yy), events=int(yy.sum()),
                                 auc=roc_auc_score(yy, pp) if yy.nunique() == 2 else np.nan))
    kp = pd.concat(keep)
    kp["r"] = kp.r.astype(str)
    kp.to_parquet(INP / "panel/price_value_preds.parquet", index=False)
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "price_value.csv", index=False)
    print(out.pivot_table(index=["task", "sample"], columns="model", values="auc").round(3))
    print(out.groupby(["task", "sample"])[["n", "events"]].first())


if __name__ == "__main__":
    main()
