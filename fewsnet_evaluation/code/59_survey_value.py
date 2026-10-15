"""Would paying for scheduled surveys pay off? A targeting calculation for Somalia.

Each season a nutrition programme can run in half of Somalia's surveyed rural zones.
It chooses the zones with the most predicted cases (population x predicted rate), using either
  survey     the zone's own result in the previous scheduled round, or
  forecast   FEWS NET's forecast phase for the zone (mean acute malnutrition by
             phase, estimated on the other seasons), or
  random     no information (the expected value of a random half).
Children reached: acutely malnourished under-5s in the chosen zones (zone population
x 17 percent under five x measured prevalence x incidence factor 2.6 for the
season's caseload, as in standard caseload planning) x treatment coverage.
Deaths averted per child treated and survey costs come from references/survey_costs.md
(ranges). The value of the surveys is the extra deaths averted by choosing zones with
them rather than with FEWS NET's forecast; their cost is one round of surveys in
every zone. Illustrative: one country, stylized allocation rules. A second rule ranks
zones by malnutrition rate alone (ignoring population), as threshold-based prioritisation does.

Outputs: output/tables/survey_value.csv, survey_value_key.json
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
U5, INCIDENCE = 0.17, 2.6
# references/survey_costs.md: CMAM coverage ~38% (Rogers et al. 2015); deaths averted per acutely
# malnourished child treated: SAM ~1 in 5 of GAM cases, untreated one-year mortality ~10% (SAM) and
# ~4% (MAM), treatment cuts it ~70% and ~40% (GiveWell's inputs, before its discounts); low and high
# bracket these. SMART survey cost per area estimated: ~$15k-21k (UNICEF/ACF 2016; Daher et al. 2018),
# up to ~$30k in South Sudan.
COVERAGE = {"low": 0.25, "central": 0.38, "high": 0.50}
DEATHS_PER_CHILD = {"low": 0.010, "central": 0.027, "high": 0.040}
SURVEY_COST = {"low": 10_000, "central": 20_000, "high": 30_000}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def zone_population(fnids, pop):
    """FEWS NET units from several map vintages can match one zone; use the largest single vintage."""
    ids = pd.Series(fnids.split(";"))
    v = ids.str[2:6]
    sums = pop.reindex(ids).groupby(v.values).sum()
    return float(sums.max()) if len(sums) else np.nan


def main():
    F = load("fs", "57_fsnau_value.py")
    s = F.build()
    pop = pd.read_parquet(INP / "panel/fnid_population.parquet").set_index("fnid")["pop"]
    s["pop"] = [zone_population(f, pop) for f in s.fnids]
    d = s.dropna(subset=["fc", "gam_lag", "pop"]).copy()
    d["cases"] = d["pop"] * U5 * d.gam / 100 * INCIDENCE        # season caseload of acute malnutrition
    # FEWS NET-based prediction: mean measured rate by rounded forecast phase, out of season
    d["ph"] = d.fc.round().clip(2, 4)
    pred = pd.Series(np.nan, index=d.index)
    for t in d.t.unique():
        m = d[d.t != t].groupby("ph").gam.mean()
        pred[d.t == t] = d.loc[d.t == t, "ph"].map(m)
    d["pred_fc"] = pred
    rows, rate_rows = [], []
    for t, g in d.groupby("t"):
        if len(g) < 6:
            continue
        k = len(g) // 2
        g = g.assign(by_survey=g["pop"] * g.gam_lag, by_forecast=g["pop"] * g.pred_fc, by_truth=g.cases)
        top = lambda col: g.nlargest(k, col).cases.sum()           # rank zones by predicted caseload
        # FEWS NET's forecast ties within a phase: break ties at random, average over draws
        rng = np.random.default_rng(int(t * 10))
        fc_draws = [g.assign(r=g.by_forecast * (1 + rng.uniform(0, 1e-6, len(g)))).nlargest(k, "r").cases.sum()
                    for _ in range(200)]
        # a rule that ranks zones by malnutrition rate alone (e.g. prioritising by GAM thresholds)
        rate_fc = np.mean([g.assign(r=g.pred_fc + rng.uniform(0, 1e-6, len(g))).nlargest(k, "r").cases.sum()
                           for _ in range(200)])
        rate_rows.append(dict(t=t, survey=top("gam_lag"), forecast=float(rate_fc)))
        rows.append(dict(t=t, zones=len(g), chosen=k, total=g.cases.sum(), survey=top("by_survey"),
                         forecast=float(np.mean(fc_draws)), random=g.cases.sum() * k / len(g),
                         oracle=top("by_truth"), surveys_cost_units=len(g)))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "survey_value.csv", index=False)
    seasons = len(R)
    extra = (R.survey - R.forecast).sum() / seasons                 # extra cases per season in chosen zones
    extra_rand = (R.forecast - R.random).sum() / seasons
    zones = R.zones.mean()
    out = {"seasons": seasons, "zones_per_season": float(zones),
           "share_reached_survey": float(R.survey.sum() / R.total.sum()),
           "share_reached_forecast": float(R.forecast.sum() / R.total.sum()),
           "share_reached_random": float(R.random.sum() / R.total.sum()),
           "share_reached_oracle": float(R.oracle.sum() / R.total.sum()),
           "extra_cases_per_season": float(extra), "forecast_over_random_cases": float(extra_rand),
           "caseload_per_season": float(R.total.mean())}
    Q = pd.DataFrame(rate_rows)
    extra_rate = (Q.survey - Q.forecast).sum() / seasons
    out["rate_rule_share_survey"] = float(Q.survey.sum() / R.total.sum())
    out["rate_rule_share_forecast"] = float(Q.forecast.sum() / R.total.sum())
    out["rate_rule_extra_cases"] = float(extra_rate)
    for lvl in ["low", "central", "high"]:
        dr = extra_rate * COVERAGE[lvl] * DEATHS_PER_CHILD[lvl]
        out[f"rate_rule_cost_per_death_{lvl}"] = float(zones * SURVEY_COST[{"low": "high", "central": "central", "high": "low"}[lvl]] / dr) if dr > 0 else None
    for lvl in ["low", "central", "high"]:
        deaths = extra * COVERAGE[lvl] * DEATHS_PER_CHILD[lvl]
        cost = zones * SURVEY_COST[{"low": "high", "central": "central", "high": "low"}[lvl]]
        out[f"deaths_{lvl}"] = float(deaths)
        out[f"cost_round_{lvl}"] = float(cost)
        out[f"cost_per_death_{lvl}"] = float(cost / deaths) if deaths > 0 else None
    (TAB / "survey_value_key.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(R.round(0).to_string())


if __name__ == "__main__":
    main()
