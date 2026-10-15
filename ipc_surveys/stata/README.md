# Stata replication: Hunger and Death in Humanitarian Crises

These do-files re-estimate every number in `output/cgd_paper/ipc_surveys_draft.pdf` that comes from estimation or arithmetic on analysis data, in short, commented Stata code. The Python pipeline in `code/` is unchanged and still produces the paper and its figures.

## How to run

1. **Build the data in Python (once).** Run the analysis scripts as usual (see `../README.md`), then:
   ```
   ../.venv/bin/python code/91_export_stata.py
   ```
   This writes plain CSVs to `stata/data/`.

   Python keeps the jobs Stata is bad at:
   - fetching data;
   - parsing survey PDFs and dashboards;
   - matching survey domains and districts to FEWS NET's mapping units;
   - rainfall and conflict windows;
   - figures.

2. **Run the do-files in Stata 19.** They need `reghdfe` and `ftools`; `_setup.do` installs both from SSC if missing.
   ```
   cd ".../FEWSNET/ipc_surveys/stata"
   do 00_master.do
   ```
   It takes about 20 seconds. Batch mode: `stata-mp -b do 00_master.do`.

## What each file does

| File | Paper | Python | What it estimates |
|---|---|---|---|
| `01_phase_outcomes.do` | §5–6, Figs 3–4, appendix | `57`, `58` | **Somalia's scheduled surveys:** means by forecast phase, correlations, leave-one-season-out R² and AUC, within-zone slopes, and whether the forecast uses the last survey. **SMART+ and national rounds:** means by phase and slopes with country-by-year effects. **The IPC's two scales:** how often they agree. |
| `02_foodsec.do` | §4, Figs 1–2 | `66`, `40`, `92` | Household food consumption and coping by FEWS NET phase: correlations pooled, within country and within area. The IPC's 20 percent rule. The Cadre Harmonisé's own inputs against its phase. FAO DIEM surveys on their own, against FEWS NET's and the official phase (`92`). |
| `03_report_surveys.do` | §9 | `53` | Survey coverage of Emergency areas. Whether a new survey moves FEWS NET's next map (cell fixed effects, clustered by region). |
| `04_triggers.do` | §9, Fig 8, eqs 2–3 | `84` | Triggers against phases: out-of-sample R² leaving one season out (the same folds), leaving one domain out, within-domain regressions, and whether the IPC share responds to the triggers. The Nigeria replication. |
| `05_money.do` | §1, §7–8, eq 4 | `85`, `86`, `87`, `89` | Funding by cluster. Classifications against public mortality surveys. Which information predicts where aid goes, the horse race between and within locations, and how much aid would have to move. The cross-country funding regression. |
| `06_bounds.do` | §9, eq 5, Fig 9 | `90` | Counterfactual outcomes without aid, the breakdown cost per death, and the FEWS NET flag version. |
| `07_survey_value.do` | §9, Fig 10 | `65`, `59` | The treatment-allocation model (greedy allocation, in Mata): extra deaths averted and the cost per death. |
| `08_survey_gaps.do` | §10, Fig 11 | `side_survey_selection/code/03`, `06` | Survey timing on conflict and downturns (country and year effects), the conflict-onset event study, and what survey reports leave out. |
| `09_ch_classification.do` | §6, Table 1 | `93` | The Cadre Harmonisé's chain of evidence. The 20 percent rule against the analysts' phase for each indicator; the dimension against its indicators; the area phase by food consumption × livelihoods; and what nutrition and mortality phases add. |
| `10_compare.do` | – | – | Lines up every Stata number with the value printed in the paper. Writes `output/compare.csv`. |

**Helpers in `_setup.do`:**
- `res` records an estimate under the paper's macro name, and `res_save` writes the recorded estimates to file.
- `loso` fits leave-one-fold-out OLS and returns out-of-sample R² or AUC.
- `bankround` rounds half to even, as Python does.
- `zstd` standardizes with the n−1 standard deviation.

## How well it matches

All 265 numbers the draft prints are identical at the paper's rounding. Another 380 estimates are computed but not printed in the current draft; `compare.csv` lists them as "not printed".

Three Stata choices produce standard errors that differ slightly from the Python code, but none shows at the paper's rounding:
- **Somalia within-zone slopes and the SMART+ slopes:** `reghdfe` cluster-robust standard errors include degrees-of-freedom factors that the Python code leaves out.
- **New-survey regression:** same reason.
- **Python's half-to-even rounding of phase bins:** handled by `bankround`.

## A data problem the port found

The value-of-information numbers (§9) first failed to replicate. The Python model, rerun, did not reproduce the paper either. The cause was the shared population cache, `_data/input/panel/fnid_population.parquet`, rather than the Stata port or the paper.

- **What happened.** `code/36_benefit_cost.py`'s `populations()` used to rewrite the cache with exactly the mapping units it was asked for. A run of the FEWS NET paper's copy of that script on 15 October 2026 shrank the cache from about 10,500 units to 3,619, dropping Somali units the value-of-information model needs. The model then gave smaller zone populations and different numbers: 4,808 instead of 5,651 deaths averted by forecast-based planning.
- **The fix in this paper's code.** `code/36_benefit_cost.py` now adds missing units to the cache instead of replacing it. The cache was rebuilt as a superset of every FEWS NET unit: 19,408 units, of which 19,246 have a population.
- **Result.** Python and Stata both reproduce the paper's values again.
- **Still unfixed.** `../fewsnet_evaluation/code/36_benefit_cost.py` still has the old behaviour and should get the same fix.

## Not covered here (Python only)

- Figures.
- Fetching and parsing.
- Matching surveys, districts and FEWS NET units.
- Building the panels: `07`, `23`, `24`, `56`, `61`, `62`, `64`, `68`–`70` and `88` (Nigeria).
- Coding survey-report exclusions from PDFs (side project `04`–`06`).
