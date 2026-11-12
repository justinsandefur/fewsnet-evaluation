# Raw inputs

`../fetch.py` downloads every file marked "download" into this folder. The files marked "kept" cannot be downloaded again and are part of the package. Everything else here is not redistributed: several sources (ACLED in particular) do not allow it, and FTS and CHIRPS run to several GB.

| Folder | Content | Source | |
|---|---|---|---|
| `fsnau/surveys.csv` | FSNAU nutrition survey results, one row per survey, 2010-Gu 2026: population, season, fieldwork dates, GAM, SAM, MUAC GAM, death rates; `source_url` gives each row's report | FSNAU (FAO Somalia) seasonal Nutrition Summary pages and reports, fsnau.org. Values were parsed from the reports' tables and checked or transcribed by hand (`hand_transcribed`, `verified_share`); the procedure is in the parent project's `code/56_fsnau_surveys.py` and `code/56_transcription_instructions.md` | kept |
| `fewsnet/ipcphase_so.csv` | FEWS NET classifications for Somalia (used only for unit ids and names) | FEWS NET Data Warehouse, `https://fdw.fews.net/api/ipcphase/?format=csv&fields=simple&country_code=SO` | download |
| `fts/flows_YYYY.json` | Every humanitarian funding flow, by year, 2005-2026 | OCHA Financial Tracking Service public API, `https://api.hpc.tools/v1/public/fts/flow?year=YYYY` (copies of 30 Sep 2026) | download |
| `acled/som.xlsx` | Political violence events and fatalities by district and month | ACLED via HDX, dataset `somalia-acled-conflict-data` (copy of 4 Oct 2026). ACLED terms of use apply; not redistributed | download |
| `prices/wfp_som.csv` | WFP market prices, Somalia | WFP via HDX, `https://data.humdata.org/dataset/wfp-food-prices-for-somalia` | download |
| `ipc/ipc_amn_2025_26.xlsx` | IPC acute malnutrition analysis, Somalia, July 2025-June 2026: children 6-59 months by region | IPC via HDX, dataset `somalia-acute-malnutrition-analysis` (the workbook has since been replaced on HDX by CSV files) | kept |
| `fsc/fsc_som_YYYY_food_cash_reached_district_month.csv` | People reached with food or cash, by district and month, 2024-26 | Food Security Cluster Somalia, WFP public Tableau dashboards `https://analytics.wfp.org/t/Public/views/{2024,2025,2026}_FSC_Dashboards_SOM/ResponseDashboards`, scraped Oct 2026 | kept |
| `nutrition/ona.csv.gz` | Somalia Nutrition Cluster site reports ("DATA from ONA" sheet), 2018-Sep 2026 | Nutrition Cluster programme database, public Google Drive folder `https://drive.google.com/drive/folders/1Dl--uLDcgHhqhhe9qq5y0an9TelgKibe` (file `SOMALIA NUTRITION SERVICES_DATABASE_2018-2026_(September 2026)Final..xlsx`), linked from response.reliefweb.int/somalia/nutrition. Not kept (24 MB); its extract `../source/nutrition_sites.csv` is | |


## geo/ (read by `../extract_geo.py`)

| File | Content | Public source |
|---|---|---|
| `geo/SO_fsc_admin_lhz.geojson` | FEWS NET Somalia classification units (district x livelihood zone; 2009, 2011 and 2016 maps) | FEWS NET Data Warehouse API, `https://fdw.fews.net/api/feature/?format=geojson&country_code=SO&unit_type=fsc_admin_lhz` |
| `geo/SO_idp_camp.geojson` | FEWS NET Somalia IDP-settlement units (points) | same API, `unit_type=idp_camp` |
| `geo/chirps/afr_YYYY_MM.npy`, `afr_meta.json` | CHIRPS v2.0 monthly precipitation, 1981-01 to 2026-08, Africa window (20W-78E, 36S-40N) at 0.2 degrees: every 4th pixel of the 0.05-degree file (nearest-neighbour decimation), negative (ocean) values set to missing. `afr_meta.json` holds the grid's affine transform and shape | Funk et al. (2015), Climate Hazards Center, UC Santa Barbara: `https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/cogs/chirps-v2.0.YYYY.MM.cog`. The grids were made with exactly the code in `fetch_chirps()` in `extract_geo.py`, which downloads any month that is missing (checked: reading the public file reproduces the stored grid bit for bit for 1990-04, 2024-10 and 2026-08). The CHC moved the files in 2026 from `.../products/CHIRPS-2.0/global_monthly/cogs/` (the URL in the original fetch script, now 404) to the URL given here |
| `geo/SOM.tif` | WorldPop 2020 population counts, UN-adjusted, unconstrained, 1 km (`som_ppp_2020_1km_Aggregated_UNadj.tif`) | WorldPop, `https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/SOM/som_ppp_2020_1km_Aggregated_UNadj.tif` (summary page `https://hub.worldpop.org/geodata/summary?id=38869`) |
| `geo/som.geojson.zip` | OCHA Common Operational Dataset, Somalia administrative boundaries (COD-AB v03, valid 2025-01-08); layer `som_admin2.geojson` (90 districts + "Unspecified") | OCHA via HDX, `https://data.humdata.org/dataset/cod-ab-som` |

The FEWS NET unit list and unit names for `unit_district.csv` come from `fewsnet/ipcphase_so.csv` (see the FEWS NET entry). In this working copy the files above are symbolic links to the project's shared cache (`_data/input/`).

## 3w/ (read by `../extract_3w.py`)

OCHA Somalia "who does what where" (3W) operational presence files, HDX dataset `somalia-operational-presence`, https://data.humdata.org/dataset/somalia-operational-presence (dataset id be09b1a5-e457-448f-8d2d-63b0debc1742). File names are as cached by `../../../code/60_fetch_subnational_aid.py`; the HDX download name differs for some.

| File | Content | Public source (HDX resource) |
|---|---|---|
| `3w/3W_Operational_Presence_Dataset_Jan-Nov_2024.xlsx` | Partners by sector, district and month, January-October 2024 (sheet `3W_dataset`) | "3W Operational Presence Dataset Jan-Nov 2024.xlsx", https://data.humdata.org/dataset/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/1176ba40-f695-4edd-ab07-90e08226e52e/download/3w-operational-presence-dataset_november-2024.xlsx |
| `3w/3W_Operational_Presence_Dataset_January_-_December_2025.xlsx` | Partners by sector, district and month, 2025 | "3W Operational Presence Dataset_January - December 2025.xlsx", https://data.humdata.org/dataset/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/18ddb242-5916-484c-bf77-77e022732aaa/download/3w-operational-presence-dataset_january-december-2025.xlsx |
| `3w/3W_Operational_Presence_Dataset_January_-_June_2026.xlsx` | Partners by sector, district and month, January-June 2026 | "3W Operational Presence Dataset_January - June 2026", https://data.humdata.org/dataset/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/046df6fb-2461-4313-9937-e0228478ddbf/download/3w-operational-presence-dataset_january-june-2026_.xlsx |
| `3w/Operational_Partners_Presence_Jan-Sep_2024.xlsx` | Activity rows, January-September 2024: people reached, US$ transferred, donor (sheet `Data`) | "Operational Partners Presence Jan-Sep 2024.xlsx", https://data.humdata.org/dataset/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/fa62e062-29e8-48b2-a5a3-5e7ac96af38f/download/ocha-operational-partners-presence-jan-sep-2024.xlsx |
| `3w/3ws-2023-consolidated.xlsx` | Activity rows, January-March 2023, with donor (sheet `DATA`) | "3ws-2023-consolidated.xlsx", https://data.humdata.org/dataset/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/05ee0b67-40ab-4217-ae29-54d17fb230b5/download/3ws-2023-consolidated-5.xlsx (also posted in dataset `somalia-who-is-doing-what-and-where-3w`) |

Earlier releases for the same months (Q1 2024; Jan-Mar, Jan-Apr, Jan-Aug, Jan-Sep and Jan-Oct 2025) are in the same HDX dataset and are not used: each later release repeats all earlier months of its year. In this working copy the files above are symbolic links to `../../../input/subnational_aid/hdx_3w/som/somalia-operational-presence/`.
