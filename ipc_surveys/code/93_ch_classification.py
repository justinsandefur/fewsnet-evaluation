"""What does it take, in practice, to be classified in Crisis? The Cadre Harmonise's own chain of evidence.

For current Cadre Harmonise analyses in 2021-2023 (the years whose public file records the evidence), the
CH dataset on HDX (input/foodsec_surveys/ch_hdx/) gives, for each area:
  - household shares by indicator (food consumption groups; dietary diversity, household hunger and reduced
    coping by phase; livelihood coping categories);
  - the analysts' phase for each indicator (*_finalphase);
  - the analysts' phase for each dimension (food consumption, livelihoods, nutrition, mortality);
  - the area phase (phase_class).
Three steps, each compared with a simple rule:
  1. indicator shares -> the analysts' indicator phase: the IPC 20 percent rule (highest phase reached by at
     least 20 percent of households). Food consumption groups are not split by phase, so for them we report the
     median share of households with poor or borderline consumption in areas the analysts put at each phase.
  2. indicator phases -> the food consumption dimension: the least / most severe indicator.
  3. dimension phases -> the area phase: share of areas in Phase 3+ by food consumption x livelihoods phase
     (a saturated model), and how much nutrition and mortality phases add (linear probability model with
     cell effects, standard errors clustered by country).
Excludes the Central African Republic (IPC analyses in the CH file) and rows not flagged for use.

Outputs: output/tables/ch_classification_cells.csv, output/cgd_paper/numbers_ch.tex
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_excel(ROOT / "input" / "foodsec_surveys" / "ch_hdx" / "cadre_harmonise_caf_ipc_mars26.xlsx")
d = d[d.chtype.str.lower().eq("current") & d.usethisperiod.eq("Y") & d.adm0_pcod3.ne("CAF")
      & d.reference_year.between(2021, 2023)].copy()


def shares(cols):
    x = d[cols].astype(float)
    t = x.sum(axis=1)
    return x.where(t.between(0.95, 1.05) | t.between(95, 105)).div(t, axis=0)


def rule20(cols, phases):
    x = shares(cols)
    x.columns = phases
    cum = x.iloc[:, ::-1].cumsum(axis=1).iloc[:, ::-1]                 # share of households in phase p or worse
    out = [max([p for p in phases if r[p] >= 0.2] or [phases[0]]) for _, r in cum.fillna(0).iterrows()]
    return pd.Series(out, index=d.index).where(cum.notna().all(axis=1))


M = {}
# ---- 1. indicator shares -> analysts' indicator phase
IND = {"HDDS": ([f"HDDS_Phase{i}" for i in range(1, 6)], [1, 2, 3, 4, 5], "Hdds"),
       "HHS": ([f"HHS_Phase{i}" for i in range(1, 6)], [1, 2, 3, 4, 5], "Hhs"),
       "rCSI": (["rCSI_Phase1", "rCSI_Phase2", "rCSI_Phase3"], [1, 2, 3], "Rcsi"),
       "LhHCSCat": (["LhHCSCat_NoStrategies", "LhHCSCat_StressStrategies", "LhHCSCat_CrisisStategies",
                     "LhHCSCat_EmergencyStrategies"], [1, 2, 3, 4], "Lcs")}
for k, (cols, ph, tag) in IND.items():
    r, f = rule20(cols, ph), d[f"{k}_finalphase"]
    ok = r.notna() & f.notna()
    M[f"cxRule{tag}"] = f"{100 * (r[ok] == f[ok]).mean():.0f}"
    M[f"cxRule{tag}N"] = f"{ok.sum():,}"
fs = shares(["FCG_Acceptable", "FCG_Borderline", "FCG_Poor"])
pb = (fs.FCG_Poor + fs.FCG_Borderline)[d.FCG_finalphase.notna()]
med = pb.groupby(d.FCG_finalphase[d.FCG_finalphase.notna()]).median()
for p, t in [(1, "One"), (2, "Two"), (3, "Three"), (4, "Four")]:
    M[f"cxFcgMed{t}"] = f"{100 * med.loc[p]:.0f}"

# ---- 2. indicator phases -> food consumption dimension
F = d[["FCG_finalphase", "HDDS_finalphase", "HHS_finalphase", "rCSI_finalphase"]]
fc = d.foodconsumption_phase
ok = fc.notna() & (F.notna().sum(axis=1) >= 2)
M["cxDimN"] = f"{ok.sum():,}"
M["cxDimMin"] = f"{100 * (F.min(axis=1)[ok] == fc[ok]).mean():.0f}"
M["cxDimMax"] = f"{100 * (F.max(axis=1)[ok] == fc[ok]).mean():.0f}"

# ---- 3. dimension phases -> area phase
a = d.dropna(subset=["phase_class", "foodconsumption_phase", "livelihoods_phase"]).copy()
a["p3"] = (a.phase_class >= 3).astype(float)
dims = a[["foodconsumption_phase", "livelihoods_phase", "nutrition_phase", "mortality_phase"]]
M["cxAreaN"] = f"{len(a):,}"
M["cxCountries"] = f"{a.adm0_pcod3.nunique()}"
M["cxAreaFood"] = f"{100 * (a.phase_class == a.foodconsumption_phase).mean():.0f}"
M["cxAreaAboveMax"] = f"{100 * (a.phase_class > dims.max(axis=1)).mean():.0f}"
cells = a.groupby(["foodconsumption_phase", "livelihoods_phase"]).agg(n=("p3", "size"), p3=("p3", "mean")).reset_index()
cells.to_csv(ROOT / "output" / "tables" / "ch_classification_cells.csv", index=False)
for r in cells.itertuples():
    k = f"cxCell{'ABCD'[int(r.foodconsumption_phase) - 1]}{'ABCD'[int(r.livelihoods_phase) - 1]}"
    M[k] = f"{100 * r.p3:.0f}"
    M[k + "N"] = f"{int(r.n):,}"
a["cell"] = a.foodconsumption_phase.astype(int).astype(str) + "x" + a.livelihoods_phase.astype(int).astype(str)
a["nut_obs"], a["nut3"] = a.nutrition_phase.notna().astype(float), (a.nutrition_phase >= 3).astype(float)
a["mort_obs"], a["mort3"] = a.mortality_phase.notna().astype(float), (a.mortality_phase >= 3).astype(float)
g = a.adm0_pcod3.astype("category").cat.codes
m0 = smf.ols("p3 ~ C(cell)", a).fit()
m1 = smf.ols("p3 ~ C(cell) + nut_obs + nut3 + mort_obs + mort3", a).fit(cov_type="cluster", cov_kwds={"groups": g})
M["cxRtwoCells"] = f"{100 * m0.rsquared:.0f}"
M["cxRtwoAll"] = f"{100 * m1.rsquared:.0f}"
M["cxNut"], M["cxNutSe"] = f"{100 * m1.params['nut3']:.0f}", f"{100 * m1.bse['nut3']:.0f}"
M["cxMort"], M["cxMortSe"] = f"{100 * m1.params['mort3']:.0f}", f"{100 * m1.bse['mort3']:.0f}"
M["cxNutN"], M["cxMortN"] = f"{int(a.nut_obs.sum()):,}", f"{int(a.mort_obs.sum()):,}"
x = a[(a.nut3 == 1)]
M["cxNutFoodOneN"] = f"{int((x.foodconsumption_phase == 1).sum()):,}"
M["cxNutFoodOneP"] = f"{100 * x[x.foodconsumption_phase == 1].p3.mean():.0f}"
M["cxNutFoodTwoP"] = f"{100 * x[x.foodconsumption_phase == 2].p3.mean():.0f}"

lines = ["% Written by code/93_ch_classification.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()]
(ROOT / "output" / "cgd_paper" / "numbers_ch.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
