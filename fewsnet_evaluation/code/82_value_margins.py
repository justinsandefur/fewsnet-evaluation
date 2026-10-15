"""FEWS NET's value on two margins, in person-months of Crisis averted.

1. Reallocation (81_allocation_value.py): with the food-aid budget held fixed, how many more
   people in Crisis a planner reaches by placing aid with FEWS NET's forecasts than with
   public information. Here: denominators, and scaling from the sample of areas with an
   independent official analysis to all FEWS NET countries (by food-aid funding).

2. The envelope (historical influence): how much food and nutrition funding followed FEWS
   NET's distinctive information. For each country and FEWS NET round, the share of the next six
   months' food funding attributable to FEWS NET is 1 - exp(-beta x) for x >= 0 and
   -(1 - exp(beta x)) for x < 0 (as in 36_benefit_cost.py), where x is the country's mean
   distinctive forecast and beta the within-country food-funding response
   (33_fewsnet_contribution.py). Net share = funding-weighted mean. Extra money is converted to
   person-months of Crisis averted at the ration cost and the share of rations that reach people
   in Crisis (81). If the money was new, that is the gain; if it was moved from other crises
   where it would have done as much good, the net gain is close to zero. We report the first as
   an upper bound.

Outputs: output/tables/value_margins.json
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
RATION = {"low": 20.0, "central": 22.5, "high": 25.0}
BUDGET = {"low": 35e6, "central": 45e6, "high": 65e6}
MONTHS_PER_ROUND = 4


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def attribute(bx, form="symmetric"):
    if form == "one-sided-positive":
        return np.where(bx >= 0, 1 - np.exp(-bx), 0.0)
    return np.where(bx >= 0, 1 - np.exp(-bx), -(1 - np.exp(bx)))


def main():
    out = {}
    A = json.loads((TAB / "allocation_value_key.json").read_text())
    T = A["table"]
    R = pd.read_csv(TAB / "allocation_value.csv")
    years = R.year.nunique()
    need_pm_year = R.drop_duplicates("cell").need.sum() * MONTHS_PER_ROUND / years
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    E = load("e", "12_errors.py")
    F = E.fts_monthly(codes).reset_index()
    F["year"] = F.month.dt.year
    # FEWS NET countries (any FEWS NET map 2011-2024) and the sample countries
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet", columns=["country_code", "month"])
    fews_cc = set(cs[cs.month.dt.year.between(2011, 2024)].country_code)
    i32 = dict(zip(codes.iso3166a3, codes.iso3166a2))
    yrs = sorted(R.year.unique())
    food_all = F[F.iso2.isin(fews_cc) & F.year.isin(yrs)].groupby("year").food.sum().mean()
    samp = R.drop_duplicates("cell").assign(iso2=lambda d: d.iso3.map(i32))[["iso2", "year"]].drop_duplicates()
    food_samp = F.merge(samp, on=["iso2", "year"]).groupby("year").food.sum().reindex(yrs).fillna(0).mean()
    scale = food_all / food_samp
    out.update(need_pm_year_sample=float(need_pm_year), food_per_year_all=float(food_all),
               food_per_year_sample=float(food_samp), scale_to_all=float(scale),
               fews_countries=len(fews_cc), sample_countries=int(R.iso3.nunique()), years=[int(min(yrs)), int(max(yrs))])
    # 1. reallocation at realistic coverage
    for t in ["random", "half", "perfect"]:
        v = T[f"0.3_{t}"]
        g = v["fews_gain_person_months_per_year"]
        rations_pm = 0.3 * need_pm_year                           # ration-months a year in the sample
        reached_public = v["public_share"] * rations_pm
        out[f"realloc_{t}"] = dict(
            gain_pm=g, gain_pm_all=g * scale,
            share_of_need=g / need_pm_year,                      # of all person-months in Crisis+
            pct_more_reached=100 * g / reached_public,           # more of the budget reaching people in Crisis
            public_share=v["public_share"], fews_share=v["fews_share"], oracle_share=v["oracle_share"],
            share_of_oracle_gain=v["fews_share_of_oracle_gain"],
            aid_equiv=g * RATION["central"], aid_equiv_all=g * scale * RATION["central"],
            cost_per_pm=BUDGET["central"] / (g * scale), ratio=g * RATION["central"] / BUDGET["central"],
            ratio_all=g * scale * RATION["central"] / BUDGET["central"],
            ratio_all_lo=g * scale * RATION["low"] / BUDGET["high"], ratio_all_hi=g * scale * RATION["high"] / BUDGET["low"])
    # 2. envelope: food funding attributable to FEWS NET's distinctive information
    C = pd.read_csv(TAB / "fewsnet_contribution.csv")
    beta = {bl: C[(C.block == "funding") & (C.spec == "forecast") & (C.term == "contrib_fc3") & (C.baseline == bl)
                  & (C["sample"] == "food funding, within country")].coef.iloc[0]
            for bl in ["raw data", "raw data + latest Cadre Harmonise / IPC"]}
    P = pd.read_parquet(INP / "panel/fewsnet_contribution_panel.parquet", columns=["country_code", "r", "c_fc3", "ci_fc3"])
    P["r"] = pd.PeriodIndex(P.r.astype(str), freq="M")
    cr = P.groupby(["country_code", "r"])[["c_fc3", "ci_fc3"]].mean().reset_index()
    a = pd.read_csv(TAB / "aid_response_panel.csv")
    a["r"] = pd.PeriodIndex(a.report_month.astype(str), freq="M")
    a = a.merge(cr, on=["country_code", "r"])
    a["food_usd"] = np.expm1(a.f_food)
    env = {}
    for bl, col in [("raw data", "c_fc3"), ("raw data + latest Cadre Harmonise / IPC", "ci_fc3")]:
        d = a.dropna(subset=[col])
        for form in ["symmetric", "one-sided-positive"]:
            sh = attribute(beta[bl] * d[col].values, form)
            env[f"{bl}|{form}"] = float((sh * d.food_usd).sum() / d.food_usd.sum())
    out["envelope_share"] = env
    out["beta_food"] = {k: float(v) for k, v in beta.items()}
    for t in ["random", "half"]:
        reach = T[f"0.3_{t}"]["fews_share"]
        for k, s in env.items():
            usd = s * food_all
            out.setdefault(f"envelope_{t}", {})[k] = dict(usd=usd, pm=usd / RATION["central"] * reach,
                                                          ratio=usd / RATION["central"] * reach * RATION["central"] / BUDGET["central"])
    (TAB / "value_margins.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
