# Replication: child wasting in Somalia after the 2025 US aid withdrawal

Replication package for Sandefur and Kenny, "Child wasting in Somalia after the 2025 withdrawal of US humanitarian assistance: a difference-in-differences analysis of nutrition surveys, 2019–26" (submitted to *The Lancet Global Health*).

This folder is self-contained. It holds the analysis data (`data/`), the Stata code that produces every estimate, table and figure in the paper and its appendix, and the code that builds the data from public sources (`build/`). It needs Stata 19 and `boottest` (`ssc install boottest`).

```
cd lgh_replication
do 00_master.do
```

The run takes about two minutes and writes everything to `output/`.

## What each do-file does

| File | Does | Paper |
|---|---|---|
| `00_master.do` | Settings, the helpers (`res` keeps a number, `did` runs the difference-in-differences, `gexp` saves a figure) and the run order | |
| `01_build.do` | District exposures (US-funded share, agencies lost, aid dependence), then domain exposures, then the analysis panel | |
| `02_operations.do` | US funding, USAID-funded nutrition sites, partners present, aid delivered by exposure | Figure 1, figure S1, table S2 |
| `03_estimates.do` | Raw means, event studies, main estimates, sensitivity analyses, attrition, list of domains | Table 1, figures 2–4, table 2, figures S2–S3, tables S1, S3–S5 |
| `04_prediction_scale.do` | National prediction gap; numbers of children, by US-funded share and by agencies lost | Table S6 and the counts of children |
| `06_numbers.do` | Remaining numbers (sample sizes, CIs, table 1 rows); writes every number in the paper's style | |

## Output

| File | Content |
|---|---|
| `numbers.csv` | Every number in the text, as the paper prints it (mid-point decimal, true minus, p values to 2 significant figures). Column `paper` is the number now in the manuscript (`data/doc_numbers.csv`), and `changed` flags any that differ |
| `table1.csv`, `table2_for_doc.csv`, `table_cells_for_doc.csv` | Table 1; cells of table 2 and tables S3–S4 |
| `tableS1_domains.csv`, `tableS2_first_stage.csv`, `tableS5_attrition.csv`, `tableS6_prediction_gap.csv` | Appendix tables |
| `estimates.csv`, `event_studies.csv` | Every difference-in-differences and event-study coefficient, with bootstrap CI and p value |
| `figure1`–`figure4`, `figureS1_partners`, `figureS2_event_binary`, `figureS3_event_exposures` (`.pdf`, `.png`) | Paper figures. `figureS_event_sam*` are SAM versions, not in the paper |
| `replication.log` | Full log |

## Inference

Standard errors are clustered by region (15 clusters). All p values and 95% CIs come from a restricted wild cluster bootstrap (`boottest`, Webb weights, 9999 replications, seed 20261110); CIs invert the same test, so they agree with the p values. Two exceptions: table S2 (district cross-section) reports cluster-robust CIs (b ± 1·96 SE) and F statistics, and figure 2 shows raw means with normal-approximation CIs across domains.

The estimation sample starts in Gu 2019 (`global START 2019` in `00_master.do`): 481 surveys of 46 domains. Sensitivity row H uses all transcribed rounds from 2015. The national prediction gap (table S6) fits on all rounds before 2025, and figure 2 shows rounds from 2017.

## Data

`00_master.do` starts from the analysis files in `data/`. These are built from public sources by the code in `build/`, in two steps. Python is used only where Stata is a poor tool. Every rule and calculation is in Stata.

1. **Python** (`build/*.py`, about 650 lines; Python 3.9 with pandas, geopandas, rasterio, shapely, requests) reads the raw files and writes tidy extracts to `build/source/`. It does no analysis:
   - `fetch.py` downloads the raw files into `build/raw/`.
   - `extract_surveys.py` matches each FSNAU survey to the livelihood-zone units or town it covers (name matching) and reads its fieldwork month.
   - `extract_3w.py` reads OCHA's 3W spreadsheets. It writes partners present by month, people reached and US$ in 2024, and each donor named in the 2023-24 files, classified as US, another donor, or a UN agency (free text).
   - `extract_geo.py` averages CHIRPS rainfall and sums WorldPop population over FEWS NET units, and assigns units to districts (map work).
   - `extract_other.py` keeps the Somalia rows of the FTS funding flows and the columns used from the Nutrition Cluster site reports.
2. **Stata** (`build/build_data.do`) builds every file in `data/` from those extracts:
   - which surveys count, and the domain-to-district weights;
   - the rainfall z-scores, conflict deaths and price controls;
   - each partner's US-funded share, with its fallbacks for missing donors;
   - partners per district, aid per resident, and aid delivered.

To rebuild from scratch, from `lgh_replication/`:

```
python build/fetch.py
python build/extract_surveys.py; python build/extract_geo.py; python build/extract_3w.py; python build/extract_other.py
stata -b do build/build_data.do
stata -b do 00_master.do
```

Downloading every FTS year and the CHIRPS months takes a few GB and an hour or two. The rebuild reproduces `data/` exactly, except for the rainfall z-scores, which differ from the earlier version by at most 0·00001 (single vs double precision). It changes no number in the paper. Sources that are updated over time (FTS, ACLED, WFP prices) may differ slightly if downloaded again. Sources and dates are in `build/raw/SOURCES.md`. Files that cannot be downloaded again are kept in the package:
- the FSNAU survey table, transcribed from FSNAU's reports;
- the Food Security Cluster dashboard extracts;
- the IPC workbook.

| File in `data/` | Content | Source |
|---|---|---|
| `panel.csv` | Survey domain × round, Gu 2015 – Gu 2026: GAM, SAM, GAM by MUAC, crude and under-5 death rates, rainfall anomalies (6 and 12 months), log conflict deaths, cereal and goat prices | FSNAU SMART survey reports; CHIRPS; ACLED; WFP market prices |
| `domain_weights.csv` | Survey domain to district population weights | FEWS NET units; WorldPop |
| `districts.csv` | District population; aid per resident in 2024 (US$, people reached, partners); partners Apr–Oct 2024 and 2025; food and cash reached and SAM treatment sites, Jan–Jun 2024/25/26 | OCHA 3W; Food Security Cluster; Nutrition Cluster |
| `units2024.csv` | 2024 partners (organisation × sector × district) and their US-funded share | OCHA 3W donor field; UN agencies at their FTS US share |
| `fts.csv` | Humanitarian funding to Somalia by year, US vs other donors | OCHA Financial Tracking Service |
| `usaid_sites.csv` | Nutrition site-months naming USAID as a funder, by district and month | Somalia Nutrition Cluster site reports |
| `partners.csv` | Humanitarian partners present, by district and month | OCHA 3W |
| `national.csv`, `children.csv` | National aid delivered per month; children aged 6–59 months | Food Security and Nutrition Clusters; IPC acute malnutrition analysis 2025/26 |
| `doc_numbers.csv` | The numbers as now printed in the manuscript, used only to flag changes in `numbers.csv` | This Stata run, Nov 12, 2026 |

### Known issues in the data construction (kept so the paper's numbers are reproduced)

- **Price regions.** WFP's region names are matched to region codes with a lookup that sends several regions' prices to the wrong region (for example Bay's prices to Lower Juba). The price controls enter only table S6. `build/source/wfp_admin1.csv` holds both the mapping used (`region_as_used`) and the correct one (`region`); `global PRICE_REGION "region"` before `build/build_data.do` uses the correct one. With it, table S6's 2025 and 2026 gaps are 1·0 and 1·4 (not 0·9 and 1·5), and the national count is 55 000 (not 59 000). Nothing else changes.
- **Rainfall at the coast.** The rainfall grid takes every 4th CHIRPS pixel, so 17 small coastal units have no rainfall and two Jamaame units miss some months. Domains average over their other units, and missing months count as zero in the sums.
- **2024 reach.** Some partners appear to report running totals in OCHA's monthly 2024 activity file, so summing months may overstate people reached. This enters only the aid-dependence index.
- **District codes.** Eight 3W rows carry a wrong or broken district code (four Banadir districts swapped, four `#REF!`); `extract_3w.py` corrects them. One IDP settlement (Dhobley) has no district.

## Use of AI

The Python scripts in `build/` and the Stata do-files were written with the AI assistant Claude (Anthropic), working under the authors' direction. The authors specified the design, data and analyses, and are responsible for the results.
