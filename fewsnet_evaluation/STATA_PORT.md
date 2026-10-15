# Stata port: FEWS NET evaluation

Instructions for the chat that ports this paper's core analysis to Stata. Read this file, then `README.md`, then start.

## Goal

Re-estimate every number in `output/cgd_paper/fewsnet_evaluation.tex` that comes from estimation or arithmetic on analysis data in short, commented Stata do-files. Show that they replicate. Python stays for the jobs Stata is bad at, and the Python pipeline must keep working unchanged.

Use `../us_cut_memo/stata/` as the model; it already does this for the US-cuts memo. Copy its structure:

- `stata/_setup.do`: paths and helpers, including `res NAME EXPR`, which records an estimate under the paper's macro name.
- `stata/00_master.do`: runs everything.
- One do-file per analysis.
- `stata/NN_compare.do`: lines every Stata number up against the paper.
- `code/NN_export_stata.py`: writes plain CSVs to `stata/data/`.

## Setup

- Stata: StataNow 19 MP. Command line: `/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do 00_master.do`, run from `stata/`.
- Packages: `reghdfe`/`ftools` and `boottest`, installed from SSC in `_setup.do` if missing.
- Python: `../.venv/bin/python` (Python 3.9), run from this folder. `input/` subfolders are links to the shared data store `../_data/input/`.
- Do not move or rename folders. Keep all paths relative to this paper's folder.

## What stays in Python

Export its results to CSV for Stata where Stata needs them.

- Fetch scripts: `01`–`06`, `22`, `26`, `35`, `50`, `54`, `60`.
- Geospatial and text processing:
  - panel building (`07`, `18`, `23`, `24`);
  - FEWS NET report text (`52`, `53` feature extraction);
  - polygon overlays;
  - WorldPop zonal sums in `36`;
  - maps (`37`).
- Machine-learning predictions: gradient boosting in `32`, `33`, `55` and `53`, cross-fitted by year. Export the out-of-sample predictions, not the models.
- Figures, and the LaTeX table formatting in `41` (or replace it with Stata `esttab`/`file write`, your choice).

## What to port to Stata

These are the core estimates; check `40_paper.py` for every macro each one feeds.

| Python | Paper | What to port |
|---|---|---|
| `12_errors.py` (functions called from `40_paper.py`) | Type II and Type I sections | Onset and warning definitions, the shares by lead time, the outcome breakdown of emergency warnings and the aid-flag shares, by country too |
| `40_paper.py` accuracy block | Section 4 | Forecast vs. "nothing changes" accuracy on `input/panel/forecast_value_panel.parquet` |
| `27_shock_index.py` (+ `25_slope_did.py` `fe_ols`) | Section 9, App. D | Shock-index predictive power and the coverage × shock interaction, with area and country × month fixed effects and country-specific slopes |
| `28_flag_release.py` | Section 9, App. C | Flag × exposed difference-in-differences by horizon; wild cluster bootstrap p-values (`boottest`, Rademacher, null imposed) |
| `30_need_onsets.py` | Section 5 | Need-defined emergencies; early vs. late warning with country × round fixed effects |
| `31_aid_response.py` | Section 7, Fig. 8, Table A1 | Funding on current and forecast shares, pooled to within-country, and the heterogeneity by official coverage (`hetero()` in `40_paper.py`) |
| `32_forecast_value.py`, `33_fewsnet_contribution.py` | Section 6, Table 2 | Accuracy and funding regressions on the exported predictions: contribution coefficients, AUCs (`roctab`), masking test, contribution × funding |
| `34_official_projections.py`, `42_paper_bootstrap.py` | Section 6.2, Table 3 | Head-to-head regressions and hit/false-alarm rates; wild bootstrap p-values |
| `36_benefit_cost.py` | Section 8, Table 4, Fig. 9 | The arithmetic: attribution shares (symmetric formula), deaths, person-years and malnutrition averted, costs per outcome; the Coefficient Giving multiples |
| `53_text_value.py`, `55_price_value.py`, `57_fsnau_value.py`, `59_survey_value.py`, `63_subnational_models.py`, `65_survey_voi.py`, `81_allocation_value.py`, `82_value_margins.py` | text, prices, surveys, sub-national aid, allocation value | The regressions and value calculations, on exported data. Check the paper first: port only what feeds numbers it still prints. |

## Replication check

1. Write `code/NN_export_stata.py` to export, as CSV, the analysis files each do-file needs, plus `python_numbers.csv` (every macro in `output/cgd_paper/numbers.tex`, name and printed value).
2. Each do-file records its estimates with `res` under the macro name used in `numbers.tex`.
3. `NN_compare.do` writes `stata/output/compare.csv` with each number classified as same, p-value noise, close or DIFFERENT, using the same rules as `us_cut_memo/stata/08_compare.do`.
4. Investigate every DIFFERENT. If the Python is wrong, fix the Python, rerun it and say so (the US-cuts port found a bootstrap bug this way).
5. Write `stata/README.md`, as in the US-cuts port. It should include a table of do-files, how well they match, and what is not covered.

## When done

- Rerun `code/40_paper.py` and `code/41_paper_tables.py` if any Python changed. Recompile the paper (`pdflatex`, `bibtex`, `pdflatex` ×2 in `output/cgd_paper/`) and confirm nothing moved unexpectedly.
- Update `README.md` in this folder.
- Push to GitHub: repository `justinsandefur/fewsnet-evaluation`, subfolder `fewsnet_evaluation/`. A standing OK to push exists, so no need to ask.
