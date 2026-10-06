# Famine early warning project: data pipeline

Everything here uses public data or free APIs. Nothing touches DHS microdata yet.

Setup (Python 3.9+):

```bash
python3 -m venv .venv && .venv/bin/pip install pandas requests geopandas shapely pyproj pyarrow matplotlib openpyxl pymupdf
```

| Script | What it does | Output | Run time |
|---|---|---|---|
| `01_fetch_fewsnet.py` | All FEWS NET classifications and forecasts (current situation, near-term, medium-term) from the FEWS NET Data Warehouse API, month by month, cached | `input/fewsnet/raw/`, `ipcphase.parquet` | ~50 min |
| `02_dhs_inventory.py` | DHS survey list with fieldwork dates, anthropometry, GPS availability, sample sizes | `input/dhs/dhs_surveys.csv` | 1 min |
| `03_fetch_fts.py` | Every humanitarian funding flow in OCHA's Financial Tracking Service, 2005 on | `input/fts/fts_flows.parquet` | ~1 hr |
| `04_fetch_ipc_ch.py` | IPC and Cadre Harmonisé area classifications; Global Report on Food Crises database | `input/ipc/` | 1 min |
| `05_fetch_gdelt.py` | Monthly online news counts on hunger by country, all and US outlets, 2017 on | `input/news/gdelt_monthly.csv` | hours (rate-limited; re-run to fill gaps) |
| `06_fetch_geometries.py` | Boundaries for every FEWS NET mapping unit, all vintages | `input/fewsnet/units.gpkg` | ~20 min |
| `07_build_panel.py` | Clean unit x month panel; projections expanded to target months with lead times | `input/fewsnet/*.parquet` | 1 min |
| `08_coverage.py` | Coverage and feasibility diagnostics, self-consistency replication, figures | `output/tables/`, `output/figures/` | 2 min |
| `10_survey_inventory.py` | MICS, LSMS, CWIQ and conflict-collection surveys from the World Bank Microdata Library; flags child anthropometry and GPS from variable labels (English, French, Spanish) | `input/surveys/survey_inventory.csv` | ~1 hr first run (cached) |
| `11_survey_coverage.py` | Share of the Emergency caseload reached as survey families are added (run after `08`) | `output/tables/survey_tiers*.csv` | seconds |
| `12_errors.py`, `13_errors_detail.py` | Type I / Type II error analysis and figures | `output/figures/t1_*`, `t2_*` | minutes |
| `14_survey_fieldwork.py` | Fieldwork dates for MICS/UNHCR/LSMS; overlap with FEWS NET; coverage figures | `output/figures/coverage_grfc.pdf`, `survey_fieldwork_phase.pdf` | minutes |
| `15_instrument.py` | Competing-disasters instrument (funding-based, EM-DAT-based, war variant) and country-month first stage | `input/iv/panel.parquet`, `output/tables/iv_first_stage.csv` | seconds |
| `16_crowdout_diagnostics.py` | Donor-level crowd-out, timing windows, mega-event plot, within-year quarterly version, exchange-rate instrument, 2025 US cut | `output/tables/iv_*.csv` | seconds |
| `17_iv_alternatives.py` | Donor budget shocks, US fiscal calendar, UN Security Council, oil x Gulf donors; US-cut reduced form on IPC | `output/tables/iv_alternatives.csv` | seconds |
| `18_coverage_history.py` | FEWS NET coverage 2009-2026 from the published map archive (ALL_HFIC.zip) and the API; real vs. spurious switches | `output/tables/coverage_*.csv` | ~6 min |
| `19_iv_summary_figure.py` | First-stage strength across all instruments | `output/figures/iv_first_stage_summary.pdf` | seconds |
| `20_switch_pretrends.py` | Event studies of aid, conflict, disasters and food insecurity around FEWS NET coverage switches | `output/figures/switch_eventstudy.pdf` | seconds |
| `21_fetch_rainfall.py` | (Superseded) WFP subnational rainfall from HDX; no boundaries published, so not matchable to CH districts | `input/rainfall/` | slow |
| `22_fetch_chirps.py` | Monthly CHIRPS rainfall 1981-2026 at 0.2 degrees, read remotely from cloud-optimized GeoTIFFs, Africa/Asia and Latin America windows | `input/chirps/*.npy` | ~2-3 hrs (run years in parallel) |
| `23_outcome_panel.py` | Area-level outcome panel independent of FEWS NET: Cadre Harmonise (2014+) and IPC (2017+), share in Phase 3+/4+, with FEWS NET coverage flag | `input/panel/outcomes.parquet` | seconds |
| `24_area_rainfall.py` | Area polygons (CH districts; IPC areas; admin-1 fallback from geoBoundaries), monthly area rainfall, 12- and 6-month rainfall z-scores | `input/panel/analysis_panel.parquet` | minutes |
| `25_slope_did.py` | First-pass test: does a local drought raise food insecurity less when FEWS NET covers the country? | `output/tables/slope_did.csv` | seconds |
| `26_fetch_acled_wfp.py` | ACLED political violence by district-month (sub-national for 19 response-plan countries) and WFP market prices, from HDX | `input/acled/hdx/`, `input/prices/` | ~10 min |
| `27_shock_index.py` | Combined rainfall/conflict/price shock index (leave-one-country-out weights); predictive power; index x FEWS NET coverage, pre-2025, 2025-26 shutdown, pooled | `output/tables/shock_index_*.csv`, `output/figures/shock_index.pdf` | ~3 min |
| `28_flag_release.py` | Do areas FEWS NET flagged as held up by aid deteriorate after the 2025 cut? By horizon, with placebo years | `output/tables/flag_release*.csv`, `output/figures/flag_release.pdf` | ~2 min |
| `29_warned_onsets.py` | Are crises warned of early more often flagged as held back by aid? | `output/tables/warned_onsets*.csv` | seconds |
| `30_need_onsets.py` | Same, with crises defined by need (phase +1 if flagged) | `output/tables/need_onsets*.csv` | seconds |
| `31_aid_response.py` | Does humanitarian funding follow FEWS NET's current maps and forecasts? Pooled to within-country | `output/tables/aid_response*.csv`, `output/figures/aid_response*.pdf` | ~1 min |
| `32_forecast_value.py` | FEWS NET forecast split into a public part and added judgment; accuracy (own maps, need, IPC/CH), funding, masking test. `figure` argument redraws from tables | `output/tables/forecast_value*.csv`, `output/figures/forecast_value.pdf` | ~40 min first run (rain/conflict caches) |
| `33_fewsnet_contribution.py` | FEWS NET's contribution (current map and forecast) beyond raw data, and beyond raw data + latest Cadre Harmonise / IPC; scored on independent outcomes; funding. `figure` redraws | `output/tables/fewsnet_contribution*.csv`, `output/figures/fewsnet_contribution.pdf` | ~15 min (overlay cached) |
| `34_official_projections.py` | FEWS NET forecasts vs official IPC / Cadre Harmonise projections, scored against the next official analysis | `output/tables/official_projections*.csv` | ~2 min |
| `35_fetch_worldpop.py` | WorldPop 2020 population (UN-adjusted, 1 km) for FEWS NET countries | `input/worldpop/` | ~10 min |
| `36_benefit_cost.py` | Rough benefit-cost: FEWS NET aid flags x population x IPC mortality thresholds x FEWS NET's share of aid (funding regressions) / budget | `output/tables/benefit_cost*.csv`, `output/cgd_paper/figures/fig7_benefit_cost.pdf` | ~1 min (population cached) |
| `37_case_maps.py` | Case-study maps (Somalia 2016-17, Ethiopia 2015-16): rainfall, conflict / current map, FEWS NET forecast, later classification with aid flags | `output/cgd_paper/figures/fig_case_*.png` | ~1 min |
| `40_paper.py` | All numbers (`numbers.tex`) and figures for the CGD working paper | `output/cgd_paper/` | ~2 min |
| `41_paper_tables.py` | LaTeX tables for the CGD working paper | `output/cgd_paper/tables/` | seconds |
| `42_paper_bootstrap.py` | Wild cluster bootstrap p-values for the head-to-head with official projections | `output/cgd_paper/bootstrap.json` | ~1 min |
| `09_numbers_tex.py` | Writes the numbers quoted in the concept note as LaTeX macros (run last: 08, 11, then 09) | `output/concept_note/numbers.tex` | seconds |

Build the note: `cd output/concept_note && latexmk -pdf concept_note.tex`

## Notes on the data

- **FEWS NET timing.** Current-situation maps appear three times a year (four before 2016). The near-term forecast covers the report month and the next three; the medium-term forecast covers the four months after that. `reporting_date` in the API is the report month. Only the medium-term forecast can be scored against a later current-situation map, because the next map falls in its window.
- **The "!" flag.** `is_allowing_for_assistance = True` marks units that would be at least one phase worse without humanitarian assistance. It is a single series, not a second classification.
- **Archive gaps.** The API has nothing before January 2011, and some country-years are missing (Sudan and DR Congo before 2018, Afghanistan 2022, Yemen before 2014). These can be filled from the shapefiles at https://fews.net/data/acute-food-insecurity .
- **FTS geography.** The public flow API gives destination country only, not sub-national location.

## Manual steps still needed

1. DHS microdata and GPS: register at https://dhsprogram.com and request the surveys listed in `output/tables/dhs_fews_overlap.csv` (rows with `gps = True`).
2. ReliefWeb API: request an approved `appname` (https://apidoc.reliefweb.int/parameters#appname).
3. ACLED event-level data (for sub-national conflict outside the 19 response-plan countries): free account and key.
