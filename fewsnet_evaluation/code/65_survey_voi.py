"""If treatment followed surveys, what would surveys be worth? A value-of-information
calculation on Somalia's scheduled FSNAU surveys.

Each season a planner has B treatment slots for acutely malnourished children in Somalia's
surveyed rural zones and spends them to avert as many deaths as possible, given what it can
see. Two kinds of case per zone: severe (SAM) and moderate (MAM) acute malnutrition.
  cases      zone population x 17% under five x prevalence x incidence factor 2.6
  value      deaths averted per treated child: SAM untreated one-year mortality 10%, cut 70%
             by treatment; MAM 4%, cut 40% (GiveWell's inputs, before its discounts)
  reach      at most 80% of a zone's cases can be treated (access, care-seeking)
The planner ranks (zone, SAM/MAM) cells by predicted deaths averted per slot and fills them,
up to 80% of predicted cases, until B runs out. Slots sent to a cell beyond its true
reachable cases are wasted. Realized deaths averted use the true caseload.

Information sets (predicted SAM and MAM prevalence by zone):
  population   the national mean prevalence (other seasons) everywhere
  forecast     mean prevalence by FEWS NET's forecast phase (other seasons)
  survey       the zone's previous scheduled survey, shrunk toward the mean by a regression
               fitted on other seasons
  oracle       the true prevalence this season
Budgets B: a share c of the average season's true caseload, c from 10 to 100 percent, held
fixed across seasons; and a variant in which the season's budget scales with the caseload
predicted by the surveys (same average).
Redeployment: 0, 50 or 100 percent of slots stranded in zones with fewer cases than
predicted can be moved, once cases materialize, to zones with unmet cases.
Value of surveys = deaths averted with 'survey' minus with 'forecast' (or 'population'),
per season; cost = one survey round in the zones (US$10-30k per survey).

Outputs: output/tables/survey_voi.csv, survey_voi_key.json
"""
import importlib.util
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
U5, INCIDENCE, REACH = 0.17, 2.6, 0.8
VALUE = {"sam": 0.10 * 0.70, "mam": 0.04 * 0.40}
SURVEY_COST = {"low": 10_000, "central": 20_000, "high": 30_000}
COVER = [0.1, 0.2, 0.3, 0.38, 0.5, 0.75, 1.0]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def panel():
    F = load("fs", "57_fsnau_value.py")
    V = load("sv", "59_survey_value.py")
    s = F.build()
    pop = pd.read_parquet(INP / "panel/fnid_population.parquet").set_index("fnid")["pop"]
    s["pop"] = [V.zone_population(f, pop) for f in s.fnids]
    d = s.dropna(subset=["fc", "gam_lag", "sam_lag", "gam", "sam", "pop"]).copy()
    d = d[d["pop"] > 0]
    d["mam"], d["mam_lag"] = (d.gam - d.sam).clip(lower=0), (d.gam_lag - d.sam_lag).clip(lower=0)
    d["ph"] = d.fc.round().clip(2, 4)
    # out-of-season predictions for each information set
    for c in ["sam", "mam"]:
        d[f"{c}_population"], d[f"{c}_forecast"], d[f"{c}_survey"] = np.nan, np.nan, np.nan
        for t in d.t.unique():
            tr, te = d.t != t, d.t == t
            d.loc[te, f"{c}_population"] = d.loc[tr, c].mean()
            d.loc[te, f"{c}_forecast"] = d.loc[te, "ph"].map(d[tr].groupby("ph")[c].mean()).fillna(d.loc[tr, c].mean())
            b = np.polyfit(d.loc[tr, f"{c}_lag"], d.loc[tr, c], 1)
            d.loc[te, f"{c}_survey"] = np.clip(b[1] + b[0] * d.loc[te, f"{c}_lag"], 0, None)
        d[f"{c}_oracle"] = d[c]
    for c in ["sam", "mam"]:
        d[f"{c}_cases"] = d["pop"] * U5 * d[c] / 100 * INCIDENCE
    return d


def allocate(g, info, budget, redeploy=0.0):
    """Greedy (optimal for this linear problem) allocation of slots by predicted value per slot.
    redeploy: share of slots stranded in cells with fewer cases than predicted that can be moved,
    once cases materialize, to cells with unmet cases (in order of true value per slot)."""
    cells = []
    for c in ["sam", "mam"]:
        pred = g["pop"] * U5 * g[f"{c}_{info}"] / 100 * INCIDENCE * REACH
        cells.append(pd.DataFrame({"pred": pred.values, "true": (g[f"{c}_cases"] * REACH).values,
                                   "value": VALUE[c]}))
    x = pd.concat(cells, ignore_index=True).sort_values("value", ascending=False, kind="stable")
    # within the same value class, the planner fills cells in order of predicted size (ties do not matter)
    x = x.sort_values(["value", "pred"], ascending=[False, False])
    left, deaths, treated, stranded = budget, 0.0, 0.0, 0.0
    unmet = []
    for r in x.itertuples():
        a = min(r.pred, left)
        left -= a
        t = min(a, r.true)
        treated += t
        deaths += t * r.value
        stranded += a - t
        unmet.append((r.value, r.true - t))
    # slots never sent out (predicted cases below budget) are also available to move
    spare = redeploy * stranded + redeploy * max(left, 0)
    for v, u in sorted(unmet, key=lambda z: -z[0]):
        if spare <= 0:
            break
        m = min(u, spare)
        spare -= m
        treated += m
        deaths += m * v
    return deaths, treated


def main():
    d = panel()
    seasons = sorted(d.t.unique())
    total = d.groupby("t")[["sam_cases", "mam_cases"]].sum().sum(axis=1)
    pred_total = d.assign(pt=d["pop"] * U5 * (d.sam_survey + d.mam_survey) / 100 * INCIDENCE).groupby("t").pt.sum()
    rows = []
    for c in COVER:
        B = c * total.mean()
        for scaled in [False, True]:
            for rd in [0.0, 0.5, 1.0]:
                for t in seasons:
                    g = d[d.t == t]
                    bt = B * pred_total[t] / pred_total.mean() if scaled else B
                    for info in ["population", "forecast", "survey", "oracle"]:
                        dd, tr = allocate(g, info, bt, rd)
                        rows.append(dict(cover=c, scaled=scaled, redeploy=rd, t=t, info=info, deaths=dd, treated=tr, zones=len(g)))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "survey_voi.csv", index=False)
    S = R.groupby(["cover", "scaled", "redeploy", "info"]).deaths.mean().unstack("info")
    S["survey_vs_forecast"] = S.survey - S.forecast
    S["survey_vs_population"] = S.survey - S.population
    S["survey_share_of_oracle_gain"] = (S.survey - S.forecast) / (S.oracle - S.forecast)
    zones = R.groupby("t").zones.first().mean()
    for lvl, cost in SURVEY_COST.items():
        S[f"cost_per_death_{lvl}"] = (zones * cost) / S.survey_vs_forecast.where(S.survey_vs_forecast > 0)
    print(S.round(1).to_string())
    key = {"seasons": len(seasons), "zones_per_season": float(zones), "zone_seasons": int(len(d)),
           "caseload_per_season": float(total.mean()), "sam_share": float((d.sam / d.gam).mean()),
           "deaths_untargeted_at_38": float(S.loc[(0.38, False, 0.0), "population"]),
           "table": {f"{c}_{'scaled' if sc else 'fixed'}_{rd}": {k: float(v) for k, v in S.loc[(c, sc, rd)].items()}
                     for c, sc, rd in S.index}}
    (TAB / "survey_voi_key.json").write_text(json.dumps(key, indent=1))


if __name__ == "__main__":
    main()
