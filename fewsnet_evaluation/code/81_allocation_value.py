"""What is FEWS NET's information worth to a planner who allocates a fixed food-aid budget well?

Unit: official IPC / Cadre Harmonise area x FEWS NET map round (33_fewsnet_contribution.py
saves the panel: FEWS NET's map and forecast overlaid on official areas, public signals, the
latest official analysis, and the share of the population in Phase 3+ at the next official
analysis, which is independent of FEWS NET's own maps).

The planner. In each country and round it has R rations, each covering one person's food
gap for a month, and places them across the country's areas to keep as many people as
possible out of Crisis. By the IPC's definition, a person in Crisis has a food consumption
gap that a ration closes; a ration given to someone who would not have been in Crisis averts
nothing. The budget R is a share c of the country's actual Phase 3+ population in that
round (c = 25, 50, 75, 100 percent), the same whatever the planner knows.

What a ration reaches inside an area depends on targeting within the area:
  random     rations go to people at random: each reaches someone in Crisis with probability
             equal to the area's actual Phase 3+ share; at most one ration per resident
  perfect    rations reach people in Crisis first: each reaches someone in Crisis, up to the
             area's actual Phase 3+ population
  half       a mix, half of each
The planner predicts each area's Phase 3+ share and allocates greedily by predicted value per
ration (the optimal rule for this linear problem), using:
  public     rainfall, conflict, prices, country, season, and the latest official analysis
             (where one exists): what donors would know without FEWS NET
  + FEWS NET the same plus FEWS NET's current map and forecast for the area
  persistence the latest official analysis alone
  oracle     the actual share (the best any information could do)
  population population only (every area gets the country's average share)
Predictions are gradient-boosted regressions, cross-fitted by year.

Value of FEWS NET's information = people reached in Crisis with '+ FEWS NET' minus with
'public', per round, summed to a year. Each round covers about four months, so people
reached x 4 = person-months of Crisis averted, under the fixed budget.

Outputs: output/tables/allocation_value.csv, allocation_value_key.json
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
RAW = ["cty", "tmonth", "rain_z6", "rain_z12", "ln_ev6", "ln_fat6", "d_ln_ev6", "dp12", "dp3"]
PUBLIC = RAW + ["ipc_last3", "ipc_last_share3"]
FEWS = PUBLIC + ["cur3", "fc3"]
COVER = [0.25, 0.3, 0.5, 0.75, 1.0]
TARGET = {"random": 0.0, "half": 0.5, "perfect": 1.0}
MONTHS_PER_ROUND = 4
# references/ration_costs.md: full 2,100 kcal ration, all-in cost to donors, per person-month
RATION = {"low": 20.0, "central": 22.5, "high": 25.0}
BUDGET = {"low": 35e6, "central": 45e6, "high": 65e6}       # FEWS NET, as in 36_benefit_cost.py


def crossfit(d, feats):
    X = d[feats]
    pred = pd.Series(np.nan, index=d.index)
    cat = [feats.index("cty")] if "cty" in feats else None
    for yr in sorted(d.yr.unique()):
        te = d.yr == yr
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
                                          categorical_features=cat, random_state=1)
        m.fit(X[~te], d.loc[~te, "y"])
        pred[te] = m.predict(X[te])
    return pred.clip(0, 1)


def allocate(pop, s_true, s_pred, R, tau):
    """Greedy allocation of R rations across areas by predicted value per ration.
    Each area has two segments: up to its predicted Phase 3+ population a ration is worth
    tau + (1 - tau) * s_pred; beyond that (up to population), (1 - tau) * s_pred.
    Realized: tau * min(x, n_true) + (1 - tau) * x * s_true."""
    n_pred = pop * s_pred
    segs = []
    for i in range(len(pop)):
        segs.append((tau + (1 - tau) * s_pred[i], i, n_pred[i]))
        if tau < 1:
            segs.append(((1 - tau) * s_pred[i], i, pop[i] - n_pred[i]))
    segs.sort(key=lambda z: -z[0])
    x = np.zeros(len(pop))
    left = R
    for v, i, cap in segs:
        if left <= 0 or v <= 0:
            break
        a = min(cap, left)
        x[i] += a
        left -= a
    n_true = pop * s_true
    return float((tau * np.minimum(x, n_true) + (1 - tau) * x * s_true).sum())


def implied_coverage(R):
    """Food security and nutrition funding (OCHA FTS) as a share of what full rations for the
    Phase 3+ population would cost, by country-year, pooled."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("e", ROOT / "code" / "12_errors.py")
    e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e)
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    i32 = dict(zip(codes.iso3166a3, codes.iso3166a2))
    F = e.fts_monthly(codes).reset_index()
    F["year"] = F.month.dt.year
    x = R[(R.cover == R.cover.min()) & (R.targeting == "random")].assign(iso2=lambda d: d.iso3.map(i32))
    need = x.groupby(["iso2", "year"]).need.sum() * MONTHS_PER_ROUND
    food = F.groupby(["iso2", "year"]).food.sum().reindex(need.index).fillna(0)
    return {k: float(food.sum() / (need.sum() * v)) for k, v in RATION.items()}, float(food.sum() / R.year.nunique())


def main():
    k = pd.read_parquet(INP / "panel/fewsnet_contribution_ipc_areas.parquet")
    k["r"] = pd.PeriodIndex(k.r.astype(str), freq="M")
    k = k[(k.r.dt.year <= 2024)].dropna(subset=["ipc_share3", "ipc_pop"]).copy()
    k = k[k.ipc_pop > 0].reset_index(drop=True)
    k["yr"], k["y"] = k.r.dt.year, k.ipc_share3.clip(0, 1)
    k["s_public"] = crossfit(k, PUBLIC)
    k["s_fews"] = crossfit(k, FEWS)
    k["s_persist"] = k.ipc_last_share3.fillna(k.groupby(["iso3", "r"]).y.transform("mean"))
    k["s_oracle"] = k.y
    k["cell"] = k.iso3 + "_" + k.r.astype(str)
    k["s_population"] = k.groupby("cell").s_public.transform(lambda v: np.average(v, weights=k.loc[v.index, "ipc_pop"]))
    infos = ["population", "public", "fews", "persist", "oracle"]
    rows = []
    for cell, g in k.groupby("cell"):
        if len(g) < 3:
            continue
        need = float((g.ipc_pop * g.y).sum())
        if need <= 0:
            continue
        pop, st = g.ipc_pop.values.astype(float), g.y.values
        for c in COVER:
            for tn, tau in TARGET.items():
                row = dict(cell=cell, iso3=g.iso3.iloc[0], r=str(g.r.iloc[0]), year=int(g.yr.iloc[0]), areas=len(g),
                           need=need, cover=c, targeting=tn)
                for info in infos:
                    row[info] = allocate(pop, st, g[f"s_{info}"].values, c * need, tau)
                rows.append(row)
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "allocation_value.csv", index=False)
    S = R.groupby(["cover", "targeting"])[infos + ["need"]].sum()
    for info in infos:
        S[f"{info}_share"] = S[info] / (S.need * S.index.get_level_values("cover"))   # share of rations reaching people in Crisis
    S["fews_gain"] = S.fews - S.public
    S["fews_gain_pct"] = 100 * S.fews_gain / S.public
    S["fews_share_of_oracle_gain"] = (S.fews - S.public) / (S.oracle - S.public)
    years = R.year.nunique()
    S["fews_gain_person_months_per_year"] = S.fews_gain * MONTHS_PER_ROUND / years
    pd.set_option("display.width", 250)
    print(S.round(3).to_string())
    cov, food_per_year = implied_coverage(R)
    for (c, t) in S.index:
        g = S.loc[(c, t), "fews_gain_person_months_per_year"]
        for lv in ["low", "central", "high"]:
            S.loc[(c, t), f"aid_equiv_{lv}"] = g * RATION[lv]
        S.loc[(c, t), "cost_per_pm_central"] = BUDGET["central"] / g if g > 0 else np.nan
        S.loc[(c, t), "ratio_central"] = g * RATION["central"] / BUDGET["central"]
        S.loc[(c, t), "ratio_low"] = g * RATION["low"] / BUDGET["high"]
        S.loc[(c, t), "ratio_high"] = g * RATION["high"] / BUDGET["low"]
    key_extra = {"implied_coverage": cov, "food_funding_per_year": food_per_year}
    print(S[["fews_gain_person_months_per_year", "cost_per_pm_central", "ratio_central", "ratio_low", "ratio_high"]].round(2))
    key = {**key_extra, "areas": int(k.key.nunique()), "area_rounds": int(len(k)), "countries": int(k.iso3.nunique()),
           "country_rounds": int(R.cell.nunique()), "years": years, "year_range": [int(k.yr.min()), int(k.yr.max())],
           "need_per_round_mean": float(R.drop_duplicates("cell").need.mean()),
           "table": {f"{c}_{t}": {kk: float(v) for kk, v in S.loc[(c, t)].items()} for c, t in S.index}}
    (TAB / "allocation_value_key.json").write_text(json.dumps(key, indent=1))
    print(json.dumps({k_: v for k_, v in key.items() if k_ != "table"}, indent=1))


if __name__ == "__main__":
    main()
