# Stata replication of the FEWS NET evaluation

These do-files re-estimate every number in `output/cgd_paper/fewsnet_evaluation.pdf` that comes from estimation or arithmetic on analysis data, in short, commented Stata code. They cover:

- every numeric macro printed in the text;
- the cells of Tables 2, 3, 4, A1, the reports table and the Somalia/Sudan table.

The Python pipeline in `code/` is unchanged in what it does and still produces the paper, its numbers and its figures.

## How to run

1. Python builds the data (once).
   - Run the pipeline as described in `../README.md`, ending with `code/40_paper.py` and `code/41_paper_tables.py`.
   - Then, from `fewsnet_evaluation/`:
     ```
     ../.venv/bin/python code/90_export_stata.py
     ```
   - This writes plain CSVs to `stata/data/`, one module in `code/export_stata/` per group of do-files. It also writes `python_numbers.csv` and `python_tables.csv`, the values printed in the paper and its tables.
   - It takes about 20 minutes. Most of that is re-running the gradient-boosted predictions with the pipeline's own functions and seeds, because some scripts do not save them.
   - `stata/data/` (about 200 MB) is not in git. Parts of it derive from ACLED and other sources that cannot be redistributed.
2. In Stata 19 (needs `reghdfe`/`ftools` and `boottest`; `_setup.do` installs them from SSC if missing), from `stata/`:
   ```
   do 00_master.do
   ```
   In batch: `/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do 00_master.do`. It takes about half a minute.

## What stays in Python

These are the jobs Stata is bad at:

- fetching data;
- building panels;
- polygon overlays;
- WorldPop zonal sums;
- extracting features from FEWS NET's reports;
- the gradient-boosted and penalised-logit predictions, cross-fitted by year (exported as out-of-sample predictions, not models);
- maps and figures.

Stata takes those outputs and redoes the rest from near-raw data. For example, `01_errors.do` rebuilds onsets, warnings and lead times from the raw current-situation maps and projections.

## What each file does

| File | Paper | What it estimates | Numbers |
|---|---|---|---|
| `01_errors.do` | §§2–5 | Coverage of the world's crises, accuracy against "nothing changes", Type II (were new Emergencies forecast, by lead), Type I (what happened to Emergency warnings, aid flags), famine, the two case studies, data counts | 60 |
| `02_need_onsets.do` | §5 | Need-defined Emergencies (mapped phase + aid flag); early vs. late warning with country × round FE | 5 |
| `03_contribution.do` | §6, Table 2, App. B | AUCs with and without FEWS NET; Table 2; funding on FEWS NET's contribution and the predictable part; what the baseline captures; masking test | 32 + 34 cells |
| `04_official.do` | §6.2, Table 3 | Hit and false-alarm rates vs. the official projections; Table 3; wild cluster bootstrap p-values | 20 + 60 cells |
| `05_text_prices.do` | §6, App. F | Reports pilot: escalation regressions (reports table), AUCs with text; price-data AUCs | 18 + 138 cells |
| `06_money.do` | §7, Table A1 | Funding on current and forecast shares, pooled to within-country; heterogeneity by official coverage | 14 + 36 cells |
| `07_shocks.do` | §9, App. D | Within-R² of local shocks; leave-one-country-out shock index; coverage × shock interaction | 8 |
| `08_flags.do` | §9, App. C | Aid flags and the 2025 shutdown: flag × exposed difference-in-differences, placebo, wild bootstrap | 5 |
| `09_subnational.do` | App. I | Somalia and Sudan district panels: allocation, Anderson–Hsiao, aid flags, shift-share first stage | 25 + 56 cells |
| `10_benefit_cost.do` | App. H, Table 4 | Benefit-cost arithmetic in lives, both calibrations; symmetric attribution | 56 + 39 cells |
| `11_value_margins.do` | §8 | Greedy allocation of a fixed budget (reallocation margin); implied coverage; scaling to all countries; the envelope | 46 |
| `12_budget_phase.do` | §8, App. G | FEWS NET contract obligations; what a phase means for malnutrition and death (FSNAU, SMART+, FDW, IPC AMN vs. AFI) | 21 |
| `99_compare.do` | – | Lines up every Stata number with the value printed in the paper; writes `output/compare.csv` and `output/not_covered.csv` | |

`_setup.do` holds paths and four helpers:

- `res NAME EXPR` records an estimate under the paper's macro name, or `tab_*` for a table cell.
- `res_save` writes the recorded estimates.
- `ym` converts YYYY-MM strings to Stata months.
- `pyse` applies Python's standard-error convention (below).

## How well it matches

Of the 310 numbers printed in the paper's text and 363 table cells:

| Status | Count |
|---|---|
| Identical at the paper's rounding | 670 |
| Bootstrap p-values differing only by random draws | 3 |
| Different | 0 |

The three bootstrap p-values:

| Number | Python | Stata |
|---|---|---|
| `bootOffAllFews` | 0.003 | 0.001 |
| `bootOffNewFews` | 0.006 | 0.005 |
| `flagOwnP` | 0.43 | 0.42 |

With 12–14 country clusters, both Python and Stata sample Rademacher weights rather than enumerating them.

The port found one Python bug, now fixed. `code/40_paper.py` divided two already-rounded percentages to get the share of failed Emergency warnings that FEWS NET attributes to aid. The paper printed 56 percent; the correct figure is 57. The same function now builds the other derived numbers (`tIIearlyMiss`, `tIIearlyCrisisPlus`, `aucRawPct`, `aucRawFewsPct`) from unrounded values too, which leaves them unchanged.

## Conventions worth knowing

- **Standard errors.**
  - Python's `fe_ols` (`code/25_slope_did.py`) scales the cluster-robust variance by G/(G−1) only.
  - `reghdfe` also multiplies it by (N−1)/(N−K), where K counts any fixed effects not nested in the clusters. This makes Stata's standard errors up to 3% larger where map-round or country × round effects cut across the clusters.
  - The do-files undo that factor (`pyse`, or the `fe_reg` wrapper in `06_money.do`) so that the numbers line up. Without it, one funding confidence bound (`moneyRawFoodContribCi`, 11 to 59) would print as 10 to 60.
- **Singletons.** As in the Python `fe_ols`, singleton groups are dropped once per fixed effect in turn, not iteratively.
- **Wild bootstrap.** `boottest` with Rademacher weights and the null imposed (999 or 1,999 draws). After `reghdfe` with two absorbed fixed-effect sets, use `regress` with dummies instead.
- **AUCs** are computed on the exported predictions with `roctab`, or with a rank-based helper (`aucrank` in `05_text_prices.do`) on large files, since the two give the same area.

## Not covered

- **Two dates:** the months FEWS NET first raised famine risk (`famRiskSo`, `famRiskSd`). The lead times derived from them are covered.
- **The predictions themselves:** gradient boosting and penalised logit. Stata uses the exported out-of-sample predictions. The AUCs, coefficients and allocations computed from them match Python exactly, which confirms that the export reproduces the pipeline.
- **Figures.**
- **Two parts of `81_allocation_value.py`:** the "population" and "persistence" information sets and the "perfect targeting" rule. They feed only Figure 11's extra markers.
- **Companion papers:** macros in `numbers.tex` for material that moved to the IPC-vs-surveys paper (`in_paper = 0` in `python_numbers.csv`).
