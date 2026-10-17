# How Much Does Early Warning Improve Famine Response? An evaluation of FEWS NET

Assesses FEWS NET's usefulness: Type I and Type II errors, what it adds to what donors could otherwise know, whether aid follows it, and a rough benefit-cost calculation.

Paper source: `output/cgd_paper/fewsnet_evaluation.tex`.

## Layout

```
code/      Python: fetching, panel building, analysis, numbers and figures (run from this folder)
stata/     Stata replication of the core estimates
input/     raw and intermediate data (links to the shared store ../_data/input/; not in git)
output/    tables/, figures/ and the paper folder
references/  source notes and literature reviews used in the paper
```

Every path in the code is relative to this folder, so the paper replicates on its own.

## Requirements

- Python 3.9 with the packages in `requirements.txt` (the project's virtual environment is `../.venv`). Run scripts from this folder, e.g. `../.venv/bin/python code/40_paper.py`.
- Stata 19 (StataNow MP), with `reghdfe` and `boottest` from SSC.
- LaTeX (pdflatex, bibtex).

## Data

All sources are public, but several (EM-DAT, ACLED, DHS) do not allow redistribution, and the raw data total several GB, so `input/` is not in git. The fetch scripts below download each source into `input/`. Where a source needs registration (EM-DAT, DHS), the script's docstring says so.

## Hand-built data

These inputs cannot be downloaded again, so they are kept with the code (in the repository under `data/`):

- `data/fewsnet_reports_extracted/`: structured records extracted from 502 FEWS NET reports (Somalia, Ethiopia, Sudan, 2011–2024) by a large language model following `code/51_extraction_instructions.md`. This step cannot be re-run exactly. Copy to `input/reports/extracted/` before running `52`.
- `data/fsnau/`: Somalia FSNAU seasonal nutrition and mortality survey results, partly hand-transcribed (`code/56_transcription_instructions.md`). Copy to `input/fsnau/`.

## Replication

1. Fetch data, then build panels (the scripts in the first two groups below, in numerical order).
2. Run the analysis scripts in numerical order.
3. `40_paper.py` writes every number in the paper to `output/cgd_paper/numbers.tex`; `41_paper_tables.py` writes the tables. Then compile the paper (pdflatex, bibtex, pdflatex twice).

Stata: `stata/` re-estimates every number printed in the paper and its tables (710 of 714 identical at the paper's rounding, 3 bootstrap p-values within draw noise, 1 standard error close, none different). Run `code/90_export_stata.py`, then `stata/00_master.do`; see `stata/README.md`.

## Scripts

**Fetch data**

| Script | What it does |
|---|---|
| `01_fetch_fewsnet.py` | Download FEWS NET food insecurity classifications (current situation and projections) from the FEWS NET Data Warehouse API. |
| `03_fetch_fts.py` | Download all humanitarian funding flows from OCHA's Financial Tracking Service (FTS) public API, one year at a time, and flatten them to a table. |
| `04_fetch_ipc_ch.py` | Download IPC and Cadre Harmonisé classifications from the Humanitarian Data Exchange (HDX). These are the multi-agency analyses (not FEWS NET's own classificati... |
| `05_fetch_gdelt.py` | Monthly news coverage of hunger in FEWS NET countries, from the GDELT DOC 2.0 API (online news, January 2017 onward). |
| `06_fetch_geometries.py` | Download boundaries for every FEWS NET classification unit. |
| `22_fetch_chirps.py` | Monthly CHIRPS rainfall, 1981 on, read remotely from the cloud-optimized GeoTIFFs at 0.2 degree resolution (every 4th pixel of the 0.05 degree grid) for two win... |
| `26_fetch_acled_wfp.py` | Download sub-national conflict and food price data for every country in the outcome panel, from the Humanitarian Data Exchange. |
| `35_fetch_worldpop.py` | WorldPop 2020 population (UN-adjusted, 1 km, unconstrained) for every FEWS NET country. Output: input/worldpop/<ISO3>.tif |
| `50_fetch_reports.py` | Download FEWS NET narrative reports (outlooks, updates, key message updates, remote monitoring reports, alerts) from fews.net and save their main text. |
| `54_fetch_fdw_prices.py` | FEWS NET market prices from the FEWS NET Data Warehouse (FDW), and coverage vs. WFP prices. |
| `60_fetch_subnational_aid.py` | Sub-national humanitarian aid: feasibility probe and first download. |

**Build panels**

| Script | What it does |
|---|---|
| `07_build_panel.py` | Build a clean FEWS NET unit x month panel from the raw API pulls. |
| `18_coverage_history.py` | Reconstruct FEWS NET's country coverage month by month, 2009-2026, from two independent sources, and classify country-level coverage switches as real changes or... |
| `23_outcome_panel.py` | Area-level outcome panel of food insecurity classifications produced independently of FEWS NET: the Cadre Harmonise (West and Central Africa, 2014 on) and the m... |
| `24_area_rainfall.py` | Monthly rainfall for every outcome area (CHIRPS, 0.2 degree), and rainfall shocks for each analysis. |
| `52_text_features.py` | Turn extracted report JSON (input/reports/extracted/*.json) into tables, and match each area mention to FEWS NET mapping units (fnids). |
| `56_fsnau_surveys.py` | FSNAU (Somalia) seasonal nutrition and mortality survey results, 2009-2025. |
| `61_subnational_panel.py` | District x period panel of FEWS NET information and humanitarian aid (Somalia, Sudan). |

**Analysis**

| Script | What it does |
|---|---|
| `02_dhs_inventory.py` | Inventory DHS surveys usable as an outcome source. |
| `08_coverage.py` | Coverage and feasibility diagnostics for the concept note. |
| `10_survey_inventory.py` | Inventory of non-DHS household surveys that could supply child anthropometry: UNICEF's Multiple Indicator Cluster Surveys (MICS), the World Bank's Core Welfare ... |
| `11_survey_coverage.py` | How much does each survey family add to coverage of the world's food crises? |
| `12_errors.py` | Type I and Type II errors in famine warnings, descriptively. |
| `14_survey_fieldwork.py` | Fieldwork dates for non-DHS surveys with child anthropometry, and their overlap with FEWS NET classifications. Extends the DHS figures from 08_coverage.py to MI... |
| `15_instrument.py` | Competing-disasters instrument for humanitarian aid: construction and first stage. |
| `25_slope_did.py` | First-pass test of the missed-warning design: does a local drought raise food insecurity less when FEWS NET is covering the country? |
| `27_shock_index.py` | Combined local shock index (rainfall, conflict, food prices) and the test of whether its effect on food insecurity classifications changes with FEWS NET coverag... |
| `28_flag_release.py` | Do areas FEWS NET said were being held up by aid fall back when aid is cut? |
| `30_need_onsets.py` | Crises defined by need rather than outcome: does early warning raise the chance that aid holds a new emergency back? |
| `31_aid_response.py` | Does humanitarian funding follow FEWS NET's classifications, current or forecast? |
| `32_forecast_value.py` | Does FEWS NET know something the public data don't, and does money follow it? |
| `33_fewsnet_contribution.py` | What would donors know without FEWS NET? FEWS NET's contribution over raw data and other assessments. |
| `34_official_projections.py` | FEWS NET's forecasts against the official multi-agency projections. |
| `36_benefit_cost.py` | A crude benefit-cost calculation for FEWS NET. |
| `53_text_value.py` | Pilot: does the text of FEWS NET's reports carry information its maps don't, and where is FEWS NET short of data? Somalia, Ethiopia, Sudan, 2011-2024. |
| `55_price_value.py` | How much do market prices help forecast food crises, and does price coverage matter? |
| `57_fsnau_value.py` | Do scheduled survey results improve forecasts of measured malnutrition? Somalia, FSNAU seasonal assessments (post-Gu and post-Deyr), 2011-2024. |
| `58_phase_outcomes.py` | Does measured acute malnutrition and mortality rise with the food insecurity phase, outside Somalia? Open survey sources, matched to FEWS NET maps and to IPC / ... |
| `59_survey_value.py` | Would paying for scheduled surveys pay off? A targeting calculation for Somalia. |
| `63_subnational_models.py` | Does aid follow FEWS NET within countries, do its aid flags mark where aid went, and does aid improve outcomes? District x FEWS NET period panels (61_subnationa... |
| `65_survey_voi.py` | If treatment followed surveys, what would surveys be worth? A value-of-information calculation on Somalia's scheduled FSNAU surveys. |
| `66_foodsec_surveys.py` | Do acute food insecurity (AFI) phases track survey-measured household food insecurity? |
| `81_allocation_value.py` | What is FEWS NET's information worth to a planner who allocates a fixed food-aid budget well? |
| `82_value_margins.py` | FEWS NET's value on two margins, in person-months of Crisis averted. |
| `83_displacement.py` | Displacement as an outcome (Somalia, UNHCR PRMN 2016–2023): do FEWS NET's forecasts predict departures, and are warned crises followed by fewer? |
| `90_export_stata.py` | Export analysis-ready CSVs (modules in `code/export_stata/`) and the paper's printed values for the Stata replication in `stata/`. |

**Paper numbers, tables and figures**

| Script | What it does |
|---|---|
| `37_case_maps.py` | Illustrative maps: what the raw signals, FEWS NET's forecast and FEWS NET's later classification (with its aid flag) look like for two food crises. |
| `40_paper.py` | Numbers, figures and tables for the CGD working paper (output/cgd_paper/). |
| `41_paper_tables.py` | LaTeX tables for the CGD working paper (output/cgd_paper/tables/). |
| `42_paper_bootstrap.py` | Wild cluster bootstrap p-values (country clusters, Rademacher, null imposed) for the paper's headline coefficients, where few countries make cluster-robust stan... |

## Provenance

Split out of a single project folder in October 2026; the scripts keep their original numbers, so some are not consecutive. Scripts shared with the other papers in this repository are copied, not linked, so each paper stands alone.
