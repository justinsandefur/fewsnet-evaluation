# Ethiopia: data for a within-country test of the 2025 US aid cut

Checked 13 October 2026. The question: did zones or woredas that relied more on US-funded aid before the 24 January 2025 stop-work order get less aid afterwards (first stage), and did their child nutrition or food security get worse (outcomes)? This memo lists what exists for Ethiopia, where it is saved, and what would have to be requested. Somalia (code/68-73) is the template.

Code: `code/77_ethiopia_assemble.py` (run `.venv/bin/python -I code/77_ethiopia_assemble.py`). Raw downloads: `input/ethiopia/<source>/`. Tidy files: `input/ethiopia/tidy/`.

Geography: OCHA COD-AB v04 (valid 2025-01-01), `input/ethiopia/hdx_cod_ab/eth_admin_boundaries.xlsx`: 15 regions, 107 zones (admin-2, `ET0101`...), 1,148 woredas (admin-3, `ET010101`...). The 2023-25 regional splits (SNNP into Central, South, South West Ethiopia and Sidama) changed some zone P-codes. All tidy files use v04 zone codes. Older rows are mapped by woreda P-code where valid in v04, then by unique woreda name, then by zone name (aliases in the script). Match rates: 4W 99.6-100%, CBPF 98.5% of US$, SMART 94%.

## Bottom line

| Item | Before Jan 2025 | After Jan 2025 | Level | Usable for a DiD? |
|---|---|---|---|---|
| SMART/SMART+ anthropometry and mortality | SMART+ 2023: 12, 2024: 31 (plus ENCU registry 2023: 11, 2024: 4, overlapping) | 2025: 5 (2 are IDP camps); 2026 to May: 3 | zone / livelihood zone | **No, too thin after the cut.** 3 non-camp zone surveys in 2025 |
| FEWS NET woreda classifications (phase, "!" flag) | Oct 2024 (and every 4 months before) | Oct 2025, Feb 2026, Jun 2026 | woreda (1,141 units) | **Yes, as a secondary outcome.** Same-season Oct 2024 vs Oct 2025. Not independent of aid (the "!" flag is about aid) |
| SAM admissions (TFP) | woreda x month, 2021 to Jul 2023 | none public | woreda | No (gap 2023-25) |
| Food security indicators (FCS, rCSI) | WFP real-time admin-1 to 2023 (project copy) | needs HungerMap API key | region | No |
| OCHA 4W (partner x activity x woreda x month, **donor field**) | monthly 2022-24 | Jan-Apr, Aug, Nov-Dec 2025; Jan-Mar 2026 | woreda | **Yes, first stage / exposure.** Donor field missing for 30% of 2025 rows |
| Food-assistance operator by woreda (JEOP vs WFP vs government), from 4W food rows | monthly 2022-24 | Jan-Mar, Nov-Dec 2025; Jan-Mar 2026 | woreda | **Yes, exposure.** JEOP: 0 woredas Feb 2025, then resumed and took over 52 WFP woredas (to Jul 2025) |
| EHF (CBPF) allocations | 2015-24 | 2025, 2026 | zone and woreda | Yes, but small (US is not an EHF donor; it is a backfill channel) |
| HNO people in need | 2024 by woreda, overall and by cluster | **none on HDX/HPC for 2025-26** | woreda | Pre-period need only |
| OCHA humanitarian access by woreda | Jan 2024-Nov 2024 bi-monthly (back to 2021 in older files) | Feb 2025-Aug 2026 | woreda | Yes, as a control (Amhara conflict) |

Judgment: an Ethiopia version of the Somalia design is feasible **for the first stage and for FEWS NET classification outcomes, not for anthropometric outcomes** with public data. See the last section.

## A. Outcomes

### A1. SMART / SMART+ nutrition surveys

**SMART+ platform** (`input/smartplus/anthropometry.json`, `mortality.json`; already in the project). 51 Ethiopia surveys: 2023 (12), 2024 (31), 2025 (5), 2026 (3, to May). Variables in `keystats`: GAM, MAM, SAM by WHZ and MUAC (with 95% CI), stunting, underweight, overweight; CDR and U5DR (per 10,000/day) with CI and death counts. Other modules (FCS, rCSI, HHS, WASH, IYCF, vaccination) are listed as collected but values are not in the JSON. Admin names are given at region and zone level (some in Amharic), occasionally woreda; lat/long given.

Post-cut surveys (all of them):
- Jan 2025, Oromia, Guji (Hambela Wamena woreda), REACH rapid SMART: GAM 6.2%.
- Jun 2025, Oromia, East Hararge, **Qoloji IDP site** (EPHI): GAM 11.2%.
- Jun 2025, Central Ethiopia, Guraghe (THP-E): GAM 2.1%.
- Aug 2025, Amhara, North Shewa, **Debre Berhan IDP camp** (EPHI): GAM 9.1%.
- Dec 2025, Oromia, West Hararge (BGO/IRC): GAM 7.4%.
- Feb 2026, Afar Zone 1 (EPHI): GAM 19.0%. Jan/Feb 2026 and May 2026, Amhara North Wello (Amhara DRMC): GAM 8.3%, 12.3%.

So only North Wello (2024: 8.7%; 2026: 8.3%, 12.3%) and East/West Hararge have a same-zone before/after pair. That is not a design.

**ENCU assessment registry** (`input/subnational_aid/hdx_response/eth/ethiopia-malnutrition-prevalence/ENCU_Assessment_registry_2024.xlsx`, HDX `ethiopia-malnutrition-prevalence`, last resource Jan 2025). 395 rows, one per woreda covered by a survey, 2017-Mar 2024 (23 rows have a placeholder year 2001). Has woreda P-codes, partner, coverage type (woreda / zone / livelihood zone), date, GAM/SAM (WHZ, MUAC), women's MUAC, CDR, U5DR, IYCF, vaccination, stage of alert. Collapsed to 117 surveys. 2023 Somali rows record GAM as 0.15/0.20/0.21 (fractions or placeholders, flagged, not rescaled). Overlaps heavily with SMART+ for 2023-24 (`possible_duplicate`). There is no 2025 version on HDX.

**FEWS NET Data Warehouse nutrition catalogue** (`input/fdw_nutrition/survey.csv`). 490 Ethiopia entries (479 SMART, plus DHS etc.), all public, geographic units are woredas/zones with FEWS NET fnids. **Years end in 2018** (names 2004-2018). `values.csv` holds no Ethiopia values (only Mauritania and Burkina Faso). The API (`fdw.fews.net/api/nutritionindicatorvalue/?country_code=ET&format=json`) returns an empty list, while the same call for MR returns data, so Ethiopia values are not served openly. Useful for long-run history only.

**UNHCR SENS** (HDX `unhcr-eth-2024-sens-*`, `unhcr-eth-2023-am-sens`): refugee camps (Gambella, Assosa, Jijiga, Afar, Amhara, Mirqaan), 2023-24 microdata via UNHCR microdata library (registration needed). Camps, not zones; not downloaded.

Tidy file: `input/ethiopia/tidy/smart_surveys.csv` (168 rows). One row per survey: source, organisation, raw region/zone/woreda, COD-AB region and zone names, `zone_pcode` (semicolon-separated if several zones), `woreda_pcodes` (registry only), year, month, `post_cut` (Feb 2025 on), `idp_or_camp`, GAM/SAM WHZ, GAM/SAM MUAC, stunting (SMART+), CDR, U5DR, lat/long, `possible_duplicate`, `flag`.

What to request: ENCU (EDRMC/EPHI) 2025-26 assessment registry and survey reports. ENCU publishes quarterly bulletins (see the web-search section below) but the registry spreadsheet has not been posted since early 2024.

### A2. Food security indicators (FCS, rCSI, HHS)

- WFP real-time monitoring (HungerMap/mVAM) FCS and rCSI: admin-1, 2021-23 in the project (`input/foodsec_surveys/indicators.parquet`, source `wfp_rt`). The HungerMap API (`api.hungermapdata.org/v1/foodsecurity/...`) returns 401 without a key; v2 endpoints return 503. Admin-1 is too coarse anyway.
- WFP Annual Country Reports 2021-2025: outcome tables (FCS, rCSI) by region for beneficiary samples only (`references/wfp_subnational.md`).
- SMART+ surveys list FCS/rCSI/HHS as collected but the platform JSON does not carry the values.
- No HDX dataset with zone-level FCS/rCSI for 2024-26 was found.
- **FEWS NET classifications** are the only area-level food-insecurity series on both sides of the cut: `input/fewsnet/cs_monthly.parquet`, country `ET`, woreda units (fnid `ET2023...`, 1,141 units), current-situation maps every four months to Oct 2024, then none until **Oct 2025**, then Feb and Jun 2026 (the FEWS NET outage). Phase 3+ woredas: 144 in Oct 2024, 205 in Oct 2025, 216 in Feb 2026; "!" flags 64, 61, 27. Oct 2024 vs Oct 2025 is a same-season comparison. Caveat (from the Somalia work): classifications are sticky and partly reflect assistance, so treat as a secondary outcome.
- IPC: Ethiopia has no IPC analysis since 2021 (`input/ethiopia/hdx_ipc/ipc_eth_area_long.csv` covers May-Sep 2021 only).

What to request: WFP Ethiopia VAM (DataBridges key) for FSMS/mVAM by zone; REACH/IMPACT if any Ethiopia MSNA 2024-25 exists.

### A3. SAM/MAM admissions (TFP/TSFP)

- In the project: ENCU SAM (TFP/OTP) admissions by woreda x month, Jan-May 2021, Jan-Oct 2022, Jan-Jul 2023 (`input/subnational_aid/hdx_response/eth/ethiopia-malnutrition-prevalence/SAM_*.xlsx`; 2022 file has COD admin-2/3 P-codes; 2023 file has OCHA admin-3 names and P-codes).
- Nothing on HDX after Jul 2023. UNICEF's HDX dataset `number-of-admissions-for-treatment-of-severe-acute-malnutrition-sam` is a national COVID-era sitrep series.
- TSFP (MAM) admissions by woreda were never posted on HDX.

What to request: ENCU / Nutrition Cluster Ethiopia (UNICEF-led) monthly TFP and TSFP admissions by woreda, Aug 2023-2025. These are compiled monthly from the DHIS2/ENCU reporting and would be the best outcome-plus-first-stage series (admissions measure both need and service availability).

## B. Exposure / first stage

### B1. OCHA Ethiopia 4W (already cached, now harmonised)

Source: HDX `ethiopia-operational-presence` (OCHA Ethiopia), cached in `input/subnational_aid/hdx_3w/eth/ethiopia-operational-presence/`. Files used: Jan 2022-Mar 2026 (May and June 2022 files have no donor/woreda sheet and are skipped). Months available: 2022 (10), 2023 (12), 2024 (12), 2025 (Jan, Feb, Mar, Apr, Aug, Nov, Dec), 2026 (Jan-Mar).

Unit: one row per partner x activity x woreda x month. Fields: reporting month, project status (ongoing/completed/planned/suspended), **donor** (name and, from 2025, acronym), programme organisation (e.g. WFP, JEOP, EDRMC, UNICEF), implementing partner and type, region, zone, woreda, woreda P-code, cluster, activity, lat/long. **No beneficiaries or money.**

Comparability:
- Row counts are not volumes. Reporting changed in Aug 2023 and again in Jan 2024 (rows fell from ~7,000-18,000 to ~3,000 a month, woredas covered from ~800 to ~400). 2024 and 2025 are similar in format (~2,500-3,600 rows a month), so 2024 vs 2025 is the cleanest comparison.
- US-funded share of rows with a known donor: 26% (2022), 29% (2023), 37% (2024), 22% (2025), 29% (2026).
- **Donor field is missing for ~30% of 2025-26 rows** (0% in 2024), and for **all nutrition rows in 2025-26**. So the US share cannot be measured post-cut for nutrition; use 2024 donor shares as exposure and 2025 presence/partner counts as the first-stage outcome.
- US-funded rows did not disappear: "Bureau of Humanitarian Assistance" is the second-largest named donor in 2025 (3,524 rows). Of 122 implementing partners with US-funded rows in 2024, 91 still report in 2025. The 4W may lag terminations (partners report "ongoing" projects), so treat it as an upper bound on continuing presence.
- First look: 2024 US share by zone does not predict the 2024-25 change in rows or partners (correlation -0.01 and -0.07 across 98 zones). This is descriptive, not a test.

Tidy files:
- `input/ethiopia/tidy/eth_4w_rows.parquet`: 250,790 harmonised rows with `zone_pcode` (COD v04), `us_funded`, `donor_missing`, `sector_group` (food / nutrition / health / wash / agriculture / other), `ym`.
- `input/ethiopia/tidy/exposure_4w_zone_month.csv`: zone x month counts: rows, partners, woredas, US rows, US partners, donor-missing rows, and rows/partners/US rows for food, nutrition, health, WASH.
- `input/ethiopia/tidy/exposure_4w_zone_2024.csv`: one row per zone: mean monthly counts 2023, 2024, 2025, 2026; `us_share_rows_2024` (US rows / donor-known rows), log changes 2024 to 2025.

### B2. Who delivered food in each woreda: JEOP vs WFP vs government

The 4W food-cluster rows name the programme organisation, which in Ethiopia is the food "operator": JEOP (CRS-led consortium, USAID/BHA), WFP (multiple donors, US the largest), or the government (EDRMC/RDMC, "Government Pipeline", some World Bank). This is the JEOP coverage list we were looking for.

Food rows by operator and year: JEOP 1,102 (2022), 861 (2023), 803 (2024), 306 (2025), 168 (2026 Q1); WFP 1,294, 1,162, 388, 149, 19; government 5,428, 4,503, 541, 267 (plus 23 World Bank-funded), 170. JEOP woredas per reporting month: ~110-120 in 2022, 45 in mid-2023 and 25 in Aug-Nov 2023 (the aid-diversion pause), ~90-100 in Apr-Sep 2024, 26-66 in Oct-Dec 2024, 71 (Jan 2025), 0 (Feb 2025), 53 (Mar 2025), 73 (Nov 2025), 61 (Dec 2025), 75-91 (Jan-Feb 2026). No food rows at all in the Apr and Aug 2025 files.

2024 JEOP zones (woredas served by JEOP / all food-served woredas): Tigray Central 22/22, Eastern 17/17, South Eastern 8/8, Southern 6/8; Amhara North Wello 12/16, Wag Hamra 8/8, South Gondar 4/13; Oromia East Bale 7/7, Bale 5/5, Borena 4/10, East Borena 4/9, East and West Hararge 3 each, West Arsi 2; Dire Dawa rural 4/4; Somali Liban 2/6; South Omo 1. WFP's food caseload is the Somali region (and refugees); government covers most of Oromia and Amhara.

Interpretation: JEOP kept reporting under BHA through Q1 2026, so the US food channel in Ethiopia was not switched off in the 4W. The exposure is regional (Tigray and northern Amhara are JEOP areas), so a design would compare JEOP woredas with government woredas inside Amhara and Oromia, and Tigray with neighbouring Afar/Amhara.

Tidy files:
- `input/ethiopia/tidy/food_operator_woreda_month.csv`: zone, woreda (COD P-code where valid), month, 0/1 for JEOP, WFP, GOV, GOV_WB, OTHER.
- `input/ethiopia/tidy/exposure_food_operator_zone_year.csv`: zone x year: food-served woredas in total and by operator, food rows by operator, `jeop_share_woredas`, number of COD woredas in the zone.

Not in the 4W: tonnage, beneficiaries per round, or distribution dates. Those are in Food Cluster dashboards (see web section) and JEOP/WFP internal reports.

### B3. EHF (Ethiopia Humanitarian Fund, CBPF)

Source: `input/subnational_aid/cbpf/ProjectSummaryAggV2.csv` (OCHA CBPF API, fetched Oct 2026; fund 53), plus HDX `ethiopia-cbpf-allocations-and-contributions` (`input/ethiopia/hdx_cbpf/`: contributions and a project summary to 2026). Project-location rows with admin-1/2/3 names and budget split by cluster at admin-2. Allocations matched to zones: 2023 $60m, 2024 $63m, 2025 $44m, 2026 $104m (so far).

The US is **not** an EHF donor (2020-26 contributors: Germany, Netherlands, Denmark, Finland, Canada, Sweden, Ireland, etc.; total paid $62m in 2024, $33m in 2025, $130m in 2026). EHF is therefore a measure of non-US backfill, not of US exposure.

Tidy files: `input/ethiopia/tidy/cbpf_eth_location_rows.csv` (project x location x cluster, US$), `input/ethiopia/tidy/exposure_cbpf_zone_year.csv` (zone x allocation year, US$ by food / nutrition / health / WASH / MPC / other / all).

### B4. Other exposure sources checked

- HDX HAPI operational presence for Ethiopia (`input/ethiopia/hdx_hapi/hdx_hapi_operational_presence_eth.csv`): admin-2, organisation x sector, **2026 only** (959 rows). Useful as a 2026 cross-check, nothing earlier.
- HPC response-plan projects (`input/ethiopia/hdx_hrp_projects/heth22-eth-projects.csv`): Ethiopia HRP 2022 only; no Ethiopia HRP registered on HPC for 2025 or 2026 (checked `api.hpc.tools/v1/public/plan/year/2025` and `2026`: only the regional refugee and migrant plans list Ethiopia).
- HRP 2023 and 2024 targets (`input/ethiopia/hdx_hrp/`): planned targets by location, not delivery.
- IRC Ethiopia project woredas by sector and **donor** (Jan 2024, Aug 2024 shapefiles, `input/ethiopia/hdx_irc_projects/`): one large US partner's footprint. Useful as a spot check of 4W donor coding.
- "People reached" by woreda (HDX `ethiopia-pin-targeted-reached-by-location-and-cluster`): drought response, May 2023 only (already in the project).
- Food assistance reached by zone (HDX `number-of-people-reached-with-food-assistance-in-e`): 2017 only (already in the project).
- 150 hotspot woredas (`input/ethiopia/hdx_hotspot_woredas/150-hotspot-woredas.xlsx`): undated list with woreda P-codes; older hotspot classifications (2019, 2020) on HDX.
- IATI (HDX `iati-eth`): activity-level, mostly national locations; not pursued.
- FTS: country only.

## C. Need: HNO people in need

- 2024 HNO, woreda level: overall PiN by population group (`input/ethiopia/hdx_hno/ethiopia-2024-humanitairan-needs-overview_hxl.xlsx`, 1,143 woredas, 21.4m) and PiN and targets by cluster and woreda (`eth_hpc_needs_api_2024.csv`; food security, nutrition, health, WASH, etc.).
- 2025: the HDX resource `eth_hpc_needs_api_2025.csv` is empty (one national GHO estimate row). The global HPC HNO 2026 file has no Ethiopia rows. Ethiopia's 2025 and 2026 plans were not registered on HPC. No zone-level PiN for 2025-26 was found on HDX.
- HDX HAPI humanitarian needs for Ethiopia: national only (2024).

Tidy files: `hno_pin_woreda_2024.csv`, `hno_cluster_pin_woreda_2024.csv`, `hno_pin_zone_2024.csv` (overall PiN plus `pin_fsc`, `pin_nut`, `tgt_fsc`, `tgt_nut`, etc.).

For 2025-26 need, use FEWS NET classifications (A2) or request the 2025 HNRP woreda PiN tables from OCHA Ethiopia.

## D. Controls

- OCHA humanitarian access by woreda: `input/ethiopia/hdx_access/` (2021-Aug 2026). Tidy: `input/ethiopia/tidy/access_woreda_bimonthly_2024_2025.csv` (woreda x round, Jan 2024-Dec 2025, categories accessible / partial / hard to reach / restrictions). ~25% of woredas partially accessible in 2025, mostly Amhara and Oromia conflict areas.
- Population: COD-PS 2022 admin-2/3 and 2026 table (`input/ethiopia/hdx_cod_ps/`).
- Woreda and zone spelling variants (`input/ethiopia/hdx_woreda_spelling/`).

## E. Web search: Food Cluster, ENCU, JEOP, EDRMC

These came from an open-web search (not HDX). Everything listed here is saved locally. No login was needed.

**Food Cluster Ethiopia** (`input/ethiopia/fscluster_ethiopia/`, 49 files from fscluster.org/ethiopiafsc/documents):
- **Operator-by-woreda maps for Tigray and Amhara**, monthly Mar-May 2024 (`*Partners_Presence_Map*`). Each woreda is labelled and coloured by operator and partner (JEOP-CARE, JEOP-FH, JEOP-WV, WFP-SP, EDRMC/RDRMC, none). They could be transcribed by hand to check the 4W food-operator table.
- Tigray monthly dashboards, 2023-24: people assisted by operator and zone.
- National dashboards: Dec 2023, 2024 annual, **Q1-Q4 2025**, 2025 annual. These show monthly people reached by operator. Woreda dots are coloured by operator but the woredas are not named.
- The Priority Response note (June 2024) gives the quarterly JEOP/WFP/EDRMC caseload split and says JEOP targets Priority-1 hotspot woredas.
- JEOP monthly early-warning reports cover Aug 2022-Nov 2023 (about 100 JEOP woredas).
- JEOP 1.0 final evaluation (`input/ethiopia/jeop_evaluations_dec/`): 80-127 woredas, 55 of them in Tigray. The annex listing them is not in the PDF.

**Key facts for the design** (Food Cluster Q1 2025 dashboard; ACAPS, 13 March 2025; news coverage in `input/ethiopia/jeop_2025_policy_news/`):
- January 2025: JEOP reached 1.0m of 1.5m planned.
- **February 2025: JEOP reached 0** (about 2m people missed because of the freeze), while WFP and EDRMC woredas were served. The 4W agrees: JEOP woredas fell from 71 in January to 0 in February and back to 53 in March.
- March 2025: JEOP reached 1.4m.
- WFP cut rations to 65%.
- **Between January and June 2025, WFP's Tigray, Amhara and Afar food areas were handed to JEOP at the donor's request**: 52 woredas and 1.2m people, completed 15 July 2025. So the US-exposed set of woredas *grew* during 2025. US food aid had a one-month gap, not a termination.
- JEOP was still operating in August 2026, according to FEWS NET's July and September 2026 updates. There were warnings of funding ending in June 2026 and of a pipeline break in September 2026.

**ENCU / nutrition** (`input/ethiopia/encu_nutrition_cluster_reliefweb/`):
- **2024 year-end bulletin:** monthly national SAM admissions; a woreda choropleth of cumulative 2024 SAM admissions (binned, vector); the Jan 2024 hotspot map (214 Priority-1, 309 Priority-2 and 80 Priority-3 woredas).
- **Jan-Mar 2025 bulletin:** SAM admissions by region; woreda maps of JEOP vs WFP MAM/TSFP partners in Q1 2025; "TSFP suspended in most parts of the country since March 2025"; RUTF pipeline break expected after July.
- **March 2025 advocacy note:** nutrition work stopped in Amhara, Oromia, Tigray, Afar and Somali after the stop-work order. USAID/BHA funded about 90% of RUTF (ACAPS).
- The vector maps could be matched by geometry to COD woreda polygons to recover the binned values.
- No ENCU bulletin after Q1 2025, no 2025 registry and no zone-level OTP/TSFP admissions were found openly. They sit behind Power BI dashboards linked from response.reliefweb.int/ethiopia/nutrition.

**SMART+ API** (`input/ethiopia/smartplus_aggregator/`, api.smartplusapp.org/v1): the same 51 Ethiopian surveys as the project JSON, plus 86 report files (.docx/.pdf). The reports may hold FCS, rCSI, HHS and woreda breakdowns that the JSON lacks. Index: `ethiopia_smartplus_survey_index.csv`.

**EDRMC** (`input/ethiopia/edrmc_bulletins/`):
- 30 monthly early-warning bulletins, May 2023-Nov 2025, with patchy zone-level mentions of nutrition and food.
- The hotspot woreda classification for Jan 2021 (xlsx). Lists for 2024-25 are not online.

**Existing analyses:**
- No sub-national study of the 2025 US cuts in Ethiopia was found.
- Saved: ACAPS (Mar 2025), WFP country briefs (Jan and Jul 2025), Refugees International on the JEOP cutoff.
- FEWS NET published nothing on Ethiopia from February to May 2025.

**Requests worth making:**
1. Food Cluster Ethiopia (ethiopia.foodcluster@fscluster.org): woreda x round operator, planned and reached beneficiaries, and tonnage, 2023-2025. These are the data behind their Power BI dashboards.
2. ENCU/EDRMC and UNICEF: monthly OTP and TSFP admissions by woreda, Aug 2023-2025; the 2025-26 assessment registry; hotspot priority lists for 2024 and 2025.
3. OCHA Ethiopia: 2025 and 2026 HNRP woreda PiN tables.
4. WFP Ethiopia VAM: FSMS/mVAM FCS and rCSI by zone (DataBridges key).
5. CRS/JEOP: woreda list by round and the early-warning dashboard (login needed).

## F. Is a within-Ethiopia design feasible?

**First stage: yes, at woreda/zone x month.** Two measures cover both sides of the cut:
- **US food exposure.** The 4W food rows give JEOP vs WFP vs government operator by woreda and month from 2022 to Q1 2026. They show the February 2025 JEOP gap, which cross-checks against the Food Cluster dashboards.
- **US-donor share of all 4W activity in 2024**, with partner and activity counts in 2025.

But the treatment is unusual:
- The US food channel paused for one month and then expanded, taking over WFP's northern woredas.
- The larger and longer cut was in nutrition: TSFP suspended from March 2025, and an RUTF pipeline that was 90% funded by BHA. The 4W cannot attribute nutrition activity to donors in 2025, because the donor field is blank.
- The JEOP/WFP/government split is largely regional (Tigray and northern Amhara vs Somali vs Oromia), so region x time effects absorb much of it.

**Outcomes: not with public anthropometry.**
- SMART+ has only 5 surveys in 2025 (two in IDP camps) and 3 in 2026, in different zones from the 2024 surveys.
- SAM admissions stop in July 2023.
- No zone-level FCS or rCSI is public.
- The only area outcome on both sides is FEWS NET's woreda classification: Oct 2024 vs Oct 2025, same season, 1,141 woredas, with "!" flags. It is usable as a secondary outcome with the caveats from Somalia (sticky, not independent of aid).

**Recommendation:**
- Treat Ethiopia as a first-stage and FEWS NET-outcome exercise now.
- Make the ENCU admissions request (item 2 above). It is what would allow a real nutrition test: woreda x month admissions, with JEOP/TSFP exposure.
