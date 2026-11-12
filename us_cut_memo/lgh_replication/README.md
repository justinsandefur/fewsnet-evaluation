# Replication: child wasting in Somalia after the 2025 US aid withdrawal

Replication package for Sandefur and Kenny, "Child wasting in Somalia after the 2025 withdrawal of US humanitarian assistance: a difference-in-differences analysis of nutrition surveys, 2019–26" (submitted to *The Lancet Global Health*).

This folder is self-contained. It holds the analysis data (`data/`) and the Stata code that produces every estimate, table and figure in the paper and its appendix. It needs Stata 19 and `boottest` (`ssc install boottest`).

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

Standard errors are clustered by region (15 clusters). All p values and 95% CIs come from a restricted wild cluster bootstrap (`boottest`, Webb weights, 9999 replications, seed 20261110); CIs invert the same test, so they agree with the p values. The one exception is figure 2, which shows raw means with normal-approximation CIs across domains.

The estimation sample starts in Gu 2019 (`global START 2019` in `00_master.do`): 481 surveys of 46 domains. Sensitivity row H uses all transcribed rounds from 2015. The national prediction gap (table S6) fits on all rounds before 2025, and figure 2 shows rounds from 2017.

## Data

The CSVs in `data/` are the starting point. They were assembled in Python from public sources by the scripts in `../code/`. That is the only Python in this project that the paper depends on: it reads and reshapes raw files, and it estimates nothing reported in the paper.

| File | Content | Source | Built by (`../code/`) |
|---|---|---|---|
| `panel.csv` | Survey domain × round, Gu 2015 – Gu 2026: GAM, SAM, GAM by MUAC, crude and under-5 death rates, rainfall anomalies (6 and 12 months), log conflict deaths, cereal and goat prices | FSNAU SMART survey reports (transcribed by hand, see `../code/56_transcription_instructions.md`); CHIRPS rainfall; ACLED; WFP market prices (HDX) | `56`, `68`, `69`, `70` |
| `domain_weights.csv` | Survey domain to district population weights | WorldPop; FSNAU domain definitions | `68` |
| `districts.csv` | District population; aid per resident in 2024 (US$, people reached, partners); partners Apr–Oct 2024 and 2025; food and cash reached and SAM treatment sites, Jan–Jun 2024/25/26 | OCHA 3W; Food Security Cluster; Nutrition Cluster | `62`, `68`, `69`, `75` |
| `units2024.csv` | 2024 partners (organisation × sector × district) and their US-funded share | OCHA 3W donor field; UN agencies at their FTS US share | `68` |
| `fts.csv` | Humanitarian funding to Somalia by year, US vs other donors | OCHA Financial Tracking Service | `03`, `68` |
| `usaid_sites.csv` | Nutrition site-months naming USAID as a funder, by district and month | Somalia Nutrition Cluster site reports | `84` |
| `partners.csv` | Humanitarian partners present, by district and month | OCHA 3W | `62`, `84` |
| `national.csv`, `children.csv` | National aid delivered per month; children aged 6–59 months | Food Security and Nutrition Clusters; IPC acute malnutrition analysis 2025/26 | `75`, `81` |
| `doc_numbers.csv` | The numbers as now printed in the manuscript, used only to flag changes in `numbers.csv` | This Stata run, Nov 12, 2026 | |

To rebuild `data/` from the raw sources: run the fetch scripts and `56`–`81` in `../code/` as described in `../README.md`, then `../code/84_lgh_replication_data.py`. Several of these scripts also run analyses for a separate policy memo, which play no part in this paper. Raw inputs are not redistributed (several sources, including ACLED, do not allow it). `panel.csv` holds only domain-level aggregates.

## Use of AI

The Python data-assembly scripts and the Stata do-files were written with the AI assistant Claude (Anthropic), working under the authors' direction. The authors specified the design, data and analyses, and are responsible for the results.
