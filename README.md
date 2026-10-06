# False Alarms and Missed Emergencies: An Evaluation of the Famine Early Warning Systems Network

Replication code and paper source for Claude Opus 5.5, Charles Kenny and Justin Sandefur (2026), *False Alarms and Missed Emergencies: An Evaluation of the Famine Early Warning Systems Network*. Working draft.

The paper scores FEWS NET's 2011–2024 maps and forecasts against independent IPC and Cadre Harmonisé assessments, and links them to humanitarian funding. It covers missed emergencies (Type II errors), false alarms (Type I errors), FEWS NET's information beyond what donors could otherwise know, and a rough benefit-cost calculation.

The paper is fully AI generated. Claude Opus 5.5 (Anthropic) assembled the data, wrote the code, ran the analysis and drafted the text under human direction.

## Contents

```
code/    Python scripts, numbered in run order (see code/README.md for what each does)
paper/   LaTeX source, bibliography, generated numbers (numbers.tex), tables and figures, and the compiled PDF
```

The raw data are not included. They total about 5 GB, and several sources do not allow redistribution. Every source is public; the fetch scripts download them.

## Data sources

| Source | How to get it | Script |
|---|---|---|
| FEWS NET classifications and forecasts | FEWS NET Data Warehouse API (fdw.fews.net), no key needed | `01_fetch_fewsnet.py` |
| FEWS NET map archive (2009–2022) | shapefiles.fews.net | `06_fetch_geometries.py`, `18_coverage_history.py` |
| Humanitarian funding | OCHA Financial Tracking Service API | `03_fetch_fts.py` |
| IPC and Cadre Harmonisé analyses, Global Report on Food Crises | Humanitarian Data Exchange / IPC | `04_fetch_ipc_ch.py` |
| Rainfall | CHIRPS monthly (Climate Hazards Center) | `22_fetch_chirps.py` |
| Political violence | ACLED sub-national aggregates on the Humanitarian Data Exchange (non-commercial use with attribution) | `26_fetch_acled_wfp.py` |
| Food prices | WFP market prices on the Humanitarian Data Exchange | `26_fetch_acled_wfp.py` |
| Population | WorldPop 2020, UN-adjusted, 1 km | `35_fetch_worldpop.py` |
| Administrative boundaries | geoBoundaries; OCHA COD-AB (Humanitarian Data Exchange) | `06_fetch_geometries.py`, `24_area_rainfall.py`, `32_forecast_value.py` |
| Disasters (IV exploration only) | EM-DAT, manual download after free registration, saved to `input/em-dat/` | `15_instrument.py` |
| Survey inventories (coverage section of earlier drafts) | DHS Program API, MICS and World Bank microdata catalogs | `02_dhs_inventory.py`, `10_survey_inventory.py` |

## Reproducing the paper

Python 3.9 with the packages in `requirements.txt`. Run from the repository root, so that scripts write to `input/` and `output/`.

1. Fetch data: `01`, `03`, `04`, `06`, `22`, `26`, `35` (plus the boundary downloads described in `code/README.md`).
2. Build panels: `07`, `18`, `23`, `24`.
3. Core analyses: `12` (Type I and II errors), `27` (coverage changes), `28` (2025 shutdown), `30` (need-defined emergencies), `31` (funding), `32` and `33` (FEWS NET's distinctive information), `34` (official projections), `36` (benefit-cost), `37` (case maps).
4. Paper: `40_paper.py` (numbers and figures), `41_paper_tables.py`, `42_paper_bootstrap.py`, then compile `paper/fewsnet_evaluation.tex` with pdflatex and bibtex.

Scripts `02`, `05`, `08`–`11`, `13`–`21`, `25`, `29` belong to earlier stages of the project (survey coverage, news coverage, instrumental-variable designs and first-pass tests). They are kept for completeness; the paper discusses the ones that bear on its results.

## License

Code: MIT (see `LICENSE`). Paper text and figures: © the authors.
