"""Section 8 ("What is FEWS NET worth?") and Appendices G-H: inputs for stata/10_benefit_cost.do,
11_value_margins.do and 12_budget_phase.do.

Writes to stata/data/:
  bc_flagged.csv        flagged ("!") FEWS NET area-rounds 2011-2024: area, country, round, phase, months
                        until the next map (capped), WorldPop population (zonal sums stay in Python, 36)
  bc_contrib.csv        area x round FEWS NET contribution (c_fc3, ci_fc3) and whole forecast (fc3) (33)
  bc_outcomes.csv       official IPC/CH areas: phase and shares of people in Phase 3+ / 4+
  bc_calibration.csv    phase -> crude death rate and GAM, both calibrations (constants of 36)
  bc_betas.csv          funding responses: A1-A5 (36) and the food-funding betas for the envelope (82)
  vm_areas.csv          official area x round (81): population, actual Phase 3+ share, latest official
                        share, and the cross-fitted gradient-boosted predictions s_public, s_fews
  vm_fts.csv            OCHA FTS food security + nutrition funding by country (iso2) and month
  vm_countries.csv      iso3 -> iso2, and whether FEWS NET mapped the country 2011-2024
  vm_aid.csv            country x FEWS NET round: log food funding over the next six months (31)
  ob_obligations.csv    FEWS NET contract obligations by award and fiscal year (USAspending)
  ph_fsnau.csv          Somalia FSNAU zone x season panel (57)
  ph_surveys.csv        SMART+ / FDW surveys matched to FEWS NET and IPC/CH phases (58)
  ph_amn.csv            IPC acute malnutrition areas with the acute food insecurity phase (58)
  ph_foodsec.csv        WFP food security indicators matched to FEWS NET's phase (66)
Table cells of output/cgd_paper/tables/benefit.tex -> python_tables_worth.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import INP, TAB, load, periods_to_str, table_refs  # noqa: E402


def benefit_cost(out):
    BC = load("bc", "36_benefit_cost.py")
    _, fl = BC.flagged_rounds()
    pop = BC.populations(sorted(fl.fnid.unique()))
    fl = fl.merge(pop, on="fnid", how="left")
    periods_to_str(fl[["fnid", "country_code", "month", "phase", "months", "pop"]]).to_csv(out / "bc_flagged.csv", index=False)
    P = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet",
                        columns=["fnid", "r", "country_code", "c_fc3", "ci_fc3", "fc3"])
    periods_to_str(P).to_csv(out / "bc_contrib.csv", index=False)
    o = pd.read_parquet(INP / "panel" / "outcomes.parquet", columns=["phase", "share3", "share4"])
    o.to_csv(out / "bc_outcomes.csv", index=False)
    rows = []
    for cal, (cdr, gam) in BC.CAL.items():
        for lv in cdr:
            for ph in range(1, 6):
                rows.append((cal, lv, ph, cdr[lv][ph], gam[lv][ph]))
    pd.DataFrame(rows, columns=["calib", "level", "phase", "cdr", "gam"]).to_csv(out / "bc_calibration.csv", index=False)
    # funding responses (same lookups as 36_benefit_cost.py and 82_value_margins.py)
    C = pd.read_csv(TAB / "fewsnet_contribution.csv")
    C = C[(C.block == "funding") & (C.spec == "forecast") & (C.term == "contrib_fc3")]
    gb = lambda b, f: C[(C.baseline == b) & (C["sample"] == f"{f} funding, within country")].coef.iloc[0]
    Pq = pd.read_csv(TAB / "aid_response_pooled.csv")
    gf = lambda f: Pq[(Pq.funding == f) & (Pq.phase == "3+") & (Pq.vars == "together") & (Pq.term == "forecast")
                      & (Pq.spec == "+ country FE (within-country)")].coef.iloc[0]
    ipc = "raw data + latest Cadre Harmonise / IPC"
    pd.DataFrame([("A1", "ci_fc3", gb(ipc, "all")), ("A2", "c_fc3", gb("raw data", "all")),
                  ("A3", "c_fc3", gb("raw data", "food")), ("A4", "fc3", gf("all")), ("A5", "fc3", gf("food")),
                  ("env_raw", "c_fc3", gb("raw data", "food")), ("env_ipc", "ci_fc3", gb(ipc, "food"))],
                 columns=["attribution", "x", "beta"]).to_csv(out / "bc_betas.csv", index=False)
    # Table 4 (benefit.tex): central budget, attributions A1-A3
    R = pd.read_csv(TAB / "benefit_cost.csv")
    R = R[(R.budget == "central") & R.attribution.isin(["A1", "A2", "A3"])]
    refs = []
    for a in ["A1", "A2", "A3"]:
        x = R[R.attribution == a].set_index("mortality")
        refs.append((f"tab_benefit_{a}_share", round(100 * x.loc["central", "mean_share_attributed"], 1)))
        for m in ["low", "central", "high"]:
            refs.append((f"tab_benefit_{a}_deaths_{m}", BC_r2(x.loc[m, "deaths_per_year"])))
            refs.append((f"tab_benefit_{a}_costdeath_{m}", BC_r2(x.loc[m, "cost_per_death"])))
        refs.append((f"tab_benefit_{a}_emerg", BC_r2(x.loc["central", "emergency_person_years"])))
        refs.append((f"tab_benefit_{a}_costemerg", BC_r2(x.loc["central", "budget_usd"] / x.loc["central", "emergency_person_years"])))
        w, cw = x.child_wasting_years, x.budget_usd / x.child_wasting_years
        refs += [(f"tab_benefit_{a}_wast_lo", BC_r2(w.min())), (f"tab_benefit_{a}_wast_hi", BC_r2(w.max())),
                 (f"tab_benefit_{a}_costwast_lo", BC_r2(cw.min())), (f"tab_benefit_{a}_costwast_hi", BC_r2(cw.max()))]
    table_refs(out, "worth", refs)


def BC_r2(v):
    """Two significant figures, as printed in the table (41_paper_tables.py)."""
    from math import floor, log10
    d = -int(floor(log10(abs(v)))) + 1
    return round(v, d)


def value_margins(out):
    AV = load("av", "81_allocation_value.py")
    k = pd.read_parquet(INP / "panel/fewsnet_contribution_ipc_areas.parquet")
    k["r"] = pd.PeriodIndex(k.r.astype(str), freq="M")
    k = k[(k.r.dt.year <= 2024)].dropna(subset=["ipc_share3", "ipc_pop"]).copy()
    k = k[k.ipc_pop > 0].reset_index(drop=True)
    k["yr"], k["y"] = k.r.dt.year, k.ipc_share3.clip(0, 1)
    k["s_public"] = AV.crossfit(k, AV.PUBLIC)          # gradient boosting, cross-fitted by year
    k["s_fews"] = AV.crossfit(k, AV.FEWS)
    k["order"] = np.arange(len(k))                     # row order (81 breaks ties in the greedy sort by it)
    periods_to_str(k[["order", "key", "iso3", "r", "yr", "ipc_pop", "ipc_share3", "ipc_last_share3",
                      "s_public", "s_fews"]]).to_csv(out / "vm_areas.csv", index=False)
    E = load("e", "12_errors.py")
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    F = E.fts_monthly(codes).reset_index()
    periods_to_str(F[["iso2", "month", "food"]]).to_csv(out / "vm_fts.csv", index=False)
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet", columns=["country_code", "month"])
    fews_cc = set(cs[cs.month.dt.year.between(2011, 2024)].country_code)
    c = codes[["iso3166a3", "iso3166a2"]].rename(columns={"iso3166a3": "iso3", "iso3166a2": "iso2"})
    c["fews"] = c.iso2.isin(fews_cc).astype(int)
    missing = sorted(fews_cc - set(c.iso2))
    c = pd.concat([c, pd.DataFrame({"iso3": "", "iso2": missing, "fews": 1})], ignore_index=True)
    c.to_csv(out / "vm_countries.csv", index=False)
    a = pd.read_csv(TAB / "aid_response_panel.csv", usecols=["country_code", "report_month", "f_food"])
    a.to_csv(out / "vm_aid.csv", index=False)


def budget_phase(out):
    ob = json.loads((TAB / "fewsnet_obligations.json").read_text())
    pd.DataFrame([(a, int(y), v) for a, d in ob.items() for y, v in d.items()],
                 columns=["award", "fy", "usd"]).to_csv(out / "ob_obligations.csv", index=False)
    f = pd.read_csv(TAB / "fsnau_value_panel.csv")
    f[["key", "t", "gam", "cdr", "gam_lag", "fc", "cur", "after"]].to_csv(out / "ph_fsnau.csv", index=False)
    s = pd.read_csv(TAB / "phase_outcomes_surveys.csv")
    s[["source", "sid", "iso2", "recurring", "cluster", "cy", "gam", "cdr", "cur", "ipc"]].to_csv(out / "ph_surveys.csv", index=False)
    a = pd.read_csv(TAB / "phase_outcomes_amn_areas.csv")
    a[["iso3", "area", "amn_any", "afi"]].to_csv(out / "ph_amn.csv", index=False)
    m = pd.read_parquet(INP / "foodsec_surveys/matched.parquet")
    m = m[m.independent_of_ipc & m.indicator.isin(["fcs_poor_borderline", "rcsi_19plus"]) & m.fews_cs.notna()]
    periods_to_str(m[["source", "area_id", "iso3", "year", "month", "indicator", "value", "fews_cs"]]).to_csv(
        out / "ph_foodsec.csv", index=False)


def export(out):
    benefit_cost(out)
    value_margins(out)
    budget_phase(out)
