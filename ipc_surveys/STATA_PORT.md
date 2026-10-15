# Stata port: IPC phases vs. surveys

Instructions for the chat that ports this paper's core analysis to Stata. Read this file, then `README.md` and `HANDOFF.md`, then start.

## Goal

Re-estimate every number in `output/cgd_paper/ipc_surveys_draft.tex` that comes from estimation or arithmetic on analysis data in short, commented Stata do-files. Show that they replicate. Python stays for the jobs Stata is bad at, and the Python pipeline must keep working unchanged.

Use `../us_cut_memo/stata/` as the model; it already does this for the US-cuts memo. Copy its structure:

- `stata/_setup.do`: paths and helpers, including `res NAME EXPR`, which records an estimate under the paper's macro name.
- `stata/00_master.do`: runs everything.
- One do-file per analysis.
- `stata/NN_compare.do`: lines every Stata number up against the paper.
- `code/NN_export_stata.py`: writes plain CSVs to `stata/data/`.

## Setup

- Stata: StataNow 19 MP. Command line: `/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do 00_master.do`, run from `stata/`.
- Packages: `reghdfe`/`ftools` and `boottest` from SSC.
- Python: `../.venv/bin/python`, run from this folder. `input/` subfolders are links to the shared data store `../_data/input/`.
- Do not move or rename folders. Keep all paths relative to this paper's folder.

## Numbers the paper reads

The paper reads these macro files from `output/cgd_paper/`, each from one script:

| Macro file | Script |
|---|---|
| `numbers_triggers.tex` | `84` |
| `numbers_fts.tex` | `85` |
| `numbers_system.tex` | `86` |
| `numbers_aidneed.tex` | `87` |
| `numbers_xc.tex` | `89` |
| `numbers_bounds.tex` | `90` |
| `numbers_gaps.tex` | `side_survey_selection/code/07_numbers_tex.py` |
| `numbers.tex` | `40_paper.py` (shared with the FEWS NET evaluation; this paper uses only some of its macros) |

## What stays in Python

- Fetch scripts: `01`–`06`, `22`, `26`, `35`, `50`, `54`, `60`, and the side project's `01`, `04`, `04b`.
- PDF and text extraction: `side_survey_selection/code/05`.
- Survey parsing (`56`, `66` file handling) and panel building with geospatial matching (`07`, `23`, `24`, `61`, `62`, `64`, `88`).
- Machine-learning predictions, if any; export the predictions.
- Figures.

## What to port to Stata

| Python | Paper | What to port |
|---|---|---|
| `58_phase_outcomes.py` | phases vs. GAM and death rates | Phase → malnutrition and mortality regressions, within-zone and persistence results |
| `66_foodsec_surveys.py` | phases vs. household indicators | Phase vs. FCS / rCSI / HHS regressions |
| `84_triggers_vs_phases.py` | triggers vs. phases | Out-of-sample R² comparisons and within-domain regressions (reproduce the fold structure exactly) |
| `85_fts_cluster_shares.py` | funding by cluster | Shares by cluster and year (tabulation) |
| `86_system_metrics.py` | what the system measures | Counts |
| `87_aid_vs_need.py`, `89_cross_country_aid.py` | where the money goes | Aid on phase counts vs. deaths/GAM; R² comparisons |
| `90_aid_bounds.py` | bounds | The bounding arithmetic |
| `57_fsnau_value.py`, `59_survey_value.py`, `65_survey_voi.py` | value of surveys | Value-of-information calculations |
| `side_survey_selection/code/02_build_panel.py`, `03_analysis.py` | where surveys don't go | Survey-timing regressions and event study (the panel build can stay in Python; export the panel) |

Check the draft first and port only what feeds numbers it still prints. `HANDOFF.md` lists open issues. Note especially the possible ACLED name-matching bug in `27_shock_index.py`: `88_nigeria_panels.py` matches on P-codes instead.

## Replication check

1. Export the analysis files and `python_numbers.csv` (every macro in the `numbers_*.tex` files above, name and printed value).
2. Each do-file records estimates with `res` under the macro name.
3. `NN_compare.do` writes `stata/output/compare.csv` (same, p-value noise, close, DIFFERENT), using the same rules as `us_cut_memo/stata/08_compare.do`.
4. Investigate every DIFFERENT. Fix the Python if it is wrong, and say so.
5. Write `stata/README.md`, as in the US-cuts port.

## When done

- Rerun the changed Python scripts and recompile the draft. Update `README.md`.
- Push to GitHub: repository `justinsandefur/fewsnet-evaluation`, subfolder `ipc_surveys/`. A standing OK to push exists.
