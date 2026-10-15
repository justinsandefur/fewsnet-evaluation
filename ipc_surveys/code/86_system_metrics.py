"""How much does the humanitarian information system measure hunger, against malnutrition and death?

Counts, 2022-2025, of
  - area classifications published by the IPC (acute food insecurity, current period) and the
    Cadre Harmonise (current period), from their public area files;
  - nutrition/mortality surveys with mortality results in the open SMART+ repository.
Writes output/cgd_paper/numbers_system.tex. The SMART+ repository is not a census of surveys; it is the
public record, which is what a funder or analyst outside the survey teams can see.
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "input"
Y0, Y1 = 2022, 2025

ipc = pd.read_csv(INP / "ipc" / "ipc_global_area_long.csv", low_memory=False)
ipc = ipc[(ipc["Validity period"] == "current") & (ipc.Phase == "all")]
ipc["year"] = pd.to_datetime(ipc.From).dt.year
n_ipc = ipc[ipc.year.between(Y0, Y1)].drop_duplicates(["Country", "Date of analysis", "Level 1", "Area"]).shape[0]

ch = pd.read_excel(INP / "ipc" / "cadre_harmonise_caf_ipc_mars26.xlsx")
ch = ch[ch.chtype.astype(str).str.lower().str.startswith("current") & ch.reference_year.between(Y0, Y1)]
area_cols = [c for c in ["adm0_name", "adm1_name", "adm2_name", "adm3_name"] if c in ch.columns]
n_ch = ch.drop_duplicates(area_cols + ["exercise_code", "reference_year"]).shape[0]


sm = json.load(open(INP / "smartplus" / "mortality.json"))["surveys"]
sm = pd.DataFrame([{"year": s["surveyYear"], "country": s["geographicCountry"]} for s in sm])
n_mort = int(sm.year.between(Y0, Y1).sum())
n_mort_cty = sm[sm.year.between(Y0, Y1)].country.nunique()

m = {"sysYearZero": Y0, "sysYearOne": Y1, "sysIpc": f"{n_ipc:,}", "sysCh": f"{n_ch:,}",
     "sysClass": f"{n_ipc + n_ch:,}", "sysMort": f"{n_mort:,}",
     "sysMortCountries": f"{n_mort_cty}"}
lines = ["% Written by code/86_system_metrics.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
(ROOT / "output" / "cgd_paper" / "numbers_system.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
