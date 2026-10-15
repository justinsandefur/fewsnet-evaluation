"""Write the survey-gap numbers quoted in the IPC/surveys paper as LaTeX macros.

Output: ../output/cgd_paper/numbers_gaps.tex (\\input by ipc_surveys_draft.tex)
Run after 03_analysis.py and 06_exclusions.py.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "output" / "tables"
OUT = ROOT.parent / "output" / "cgd_paper" / "numbers_gaps.tex"

coef = pd.read_csv(T / "coefficients.csv")
es = pd.read_csv(T / "event_study_onset.csv")
exc = pd.read_csv(T / "exclusions_by_intensity.csv", index_col=0)
merged = pd.read_csv(T / "exclusions_coded_merged.csv")
panel = pd.read_csv(ROOT / "data" / "panel.csv")


def b(outcome, spec, var):
    r = coef[(coef.outcome == outcome) & (coef.spec == spec) & (coef["var"] == var)].iloc[0]
    return r.b, r.se


m = {}
W = "(3) Within country"
for key, out in [("Any", "s_any"), ("Dhs", "s_DHS"), ("Mics", "s_MICS")]:
    for v, nm in [("minor", "Minor"), ("war", "War"), ("downturn", "Down")]:
        est, se = b(out, W, v)
        m[f"gap{key}{nm}"] = f"{-100 * est:.1f}"          # reported as a fall, in points
        m[f"gap{key}{nm}Se"] = f"{100 * se:.1f}"
m["gapBase"] = f"{100 * panel.s_any.mean():.0f}"
m["gapBaseDhs"] = f"{100 * panel.s_DHS.mean():.1f}"
m["gapCountries"] = f"{panel.iso3.nunique()}"
m["gapYearZero"] = f"{panel.year.min()}"
m["gapYearOne"] = f"{panel.year.max()}"
on0 = es.loc[es.k == 0].iloc[0]
m["gapOnsetDrop"] = f"{-100 * on0.b:.0f}"
m["gapOnsetDropSe"] = f"{100 * on0.se:.0f}"
m["exReports"] = f"{int(exc.loc['All', 'reports'])}"
m["exCalm"] = f"{100 * exc.loc['No conflict', 'any_security_exclusion']:.0f}"
m["exMinor"] = f"{100 * exc.loc['Minor (25-999/yr)', 'any_security_exclusion']:.0f}"
m["exWar"] = f"{100 * exc.loc['War (1,000+/yr)', 'any_security_exclusion']:.0f}"
m["exDesignConflict"] = f"{100 * exc.loc['Minor (25-999/yr)', 'areas_excluded_by_design']:.0f}"
m["exCampsSilent"] = f"{100 * exc.loc['All', 'camps_not_mentioned']:.0f}"
u = merged[merged.usable]
m["exCampsOut"] = f"{int(u.camps_out.sum())}"
m["exCampsIn"] = f"{int(u.camps_in.sum())}"
m["exDisplQ"] = f"{int((u.displacement_question == 'yes').sum())}"

# event-study onset count from the panel definition used in 03_analysis.py
p = panel.dropna(subset=["ln_gdppc", "ln_pop"]).sort_values(["iso3", "year"]).copy()   # as in 03_analysis.py
p["calm3"] = p.groupby("iso3").conflict.transform(lambda s: s.shift(1).rolling(3).sum()) == 0
m["gapOnsets"] = f"{p[(p.conflict == 1) & p.calm3].iso3.nunique()}"

lines = ["% Written by side_survey_selection/code/07_numbers_tex.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
OUT.write_text("\n".join(lines) + "\n")
print(OUT); print("\n".join(lines))
