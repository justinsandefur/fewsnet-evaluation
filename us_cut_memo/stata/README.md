# Stata replication of the US aid cut memo

These do-files re-estimate the headline numbers in `../output/us_cut_memo/us_cut_memo.pdf` in short, commented Stata code. The Python pipeline in `../code/` still produces the memo and its figures.

## How to run

1. Python builds the data (once). From `us_cut_memo/`, run `code/56`–`80` as usual, then:
   ```
   ../.venv/bin/python code/81_export_stata.py
   ```
   This writes the plain CSVs in `stata/data/`. It does the jobs Stata is bad at: parsing survey PDFs, scraping dashboards, fuzzy-matching organisation and place names, and rainfall windows.
2. In Stata 19 (needs `boottest` and `reghdfe`; `_setup.do` installs them from SSC if missing):
   ```
   cd ".../FEWSNET/us_cut_memo/stata"
   do 00_master.do
   ```
   It takes about two minutes, mostly the Anderson-Rubin grid.

## What each file does

| File | Memo | What it estimates |
|---|---|---|
| `01_somalia_build.do` | §2–3 | Builds district and survey-domain files and constructs the three exposures from their components: US-funded share of partners, agency loss and the aid-dependence index. It checks them against Python to 1e-15. |
| `02_somalia_first_stage.do` | §2, Figs 1–2, Table 1 top | Asks where food, cash and treatment actually fell. It regresses aid lost on each exposure across districts and reports F-statistics. |
| `03_somalia_wasting.do` | §3, Table 1, Fig 3, appendix | The main difference-in-differences: wasting by survey round after the cut, the pooled estimate, all outcomes, the event study, and the robustness checks the memo cites (own trends, interaction with 2024 food insecurity, attrition). |
| `04_somalia_iv_and_prediction.do` | §3, §6 | 2SLS with Anderson-Rubin intervals, and the national gap between actual wasting and what rain, conflict and prices predict. |
| `05_nigeria.do` | §5 | North-east surveillance zones: zone and year fixed effects with wild bootstrap p-values. |
| `06_ethiopia.do` | §5 | First stage on 4W activity, plus FEWS NET Phase 3+ difference-in-differences. |
| `07_scale.do` | §6 | Turns coefficients into numbers of children. |
| `08_compare.do` | – | Lines up every Stata number with the value printed in the memo and writes `output/compare.csv`. |

`_setup.do` holds paths and three small helpers:
- `res` records an estimate under the memo's macro name.
- `res_save` writes the recorded estimates to file.
- `domain_sd` gives the s.d. of an exposure across domains.

## How well it matches

Of 414 numbers, 363 are identical at the memo's rounding. Of the rest:
- **42 are bootstrap p-values** that differ by random-draw noise, usually ±0.01.
- **9 are close:** a few standard errors in the second decimal, one first-stage F (8.9 vs 8.8) and one Anderson-Rubin endpoint (6.5 vs 6.6). These come from degrees-of-freedom details and the grid step.

None differ beyond that.

The port found two problems in the Python code, both fixed in October 2026:
- **Nigeria bootstrap bug.** The wild bootstrap in `code/74_nigeria_us_cut.py` did not re-demean the bootstrap samples by year, so its p-values were too small. Agency loss → severe wasting had been cited at p = 0.02; the correct value is 0.13, and the memo text was revised. Agency loss → crude death rate stays significant (p = 0.02).
- **Missing small-sample factor.** The Nigeria and Ethiopia standard errors (`code/74`, and `dd()` in `code/73`) left out the (n−1)/(n−k) factor. They now include it, as Stata's `regress` does.

## Not covered here (Python only)

These are left out because they are not headline results, or because Stata would only re-run the Python's own data handling:
- displacement (dropped from the memo as an artefact of tracker coverage);
- prices;
- the IPC Phase 3+ outcome for Somalia;
- the relative-magnitudes bound;
- need versus response;
- the figures.
