# Somalia first stage: district-level data on aid actually delivered, 2024 vs 2025

Search run 13 October 2026. The goal was a district (admin-2), ideally monthly, measure of aid delivered in Somalia in 2024 and 2025, to serve as the first stage for the US-cut design. All files below were downloaded anonymously, with no login, form or request. New files are under `input/subnational_aid/firststage/<source>/`. The scraping and extraction scripts are in `input/subnational_aid/firststage/_code/`. Files that an earlier session had already downloaded (`hdx_3w/`, `hdx_response/`, `usaspending/`) are referenced in place and were not changed.

## Bottom line

Two open sources give a comparable district x month panel for 2024 and 2025:

- the **Food Security Cluster (FSC) response dashboard** (food and cash), and
- the **Nutrition Cluster ONA site-month database** (OTP, TSFP and SC admissions, reporting sites, stockouts).

Neither is published as a data file. I recovered both:

- **FSC:** scraped from the public WFP Tableau dashboard. District sums match the dashboard's monthly totals exactly.
- **Nutrition:** found in a public Google Drive folder linked from the cluster's ReliefWeb Response page.

Both show large 2025 declines with a lot of variation across districts:

- **FSC:** the median district's 2025 food and cash reach is 43% below its 2024 level (interquartile range −71% to −16%).
- **Nutrition:** sites reporting fell from about 1,100–1,290 a month in early 2024 to about 700–1,070 in 2025.

---

## 1. Food Security Cluster response (food, cash, vouchers)

### 1a. FSC Somalia "Interactive Response Dashboards", WFP Tableau. **Downloaded (scraped).**

**Source.** Public views at `https://analytics.wfp.org/t/Public/views/{2024|2025|2026}_FSC_Dashboards_SOM/ResponseDashboards`, linked from fscluster.org/somalia ("Country Dashboard 2025"). The workbook is a Tableau story with these tabs:

- Homepage
- Partners' Presence
- Food & Cash assistance – Monthly Response (SO1)
- Livelihood assistance – Cumulative (SO2)
- two gap-analysis tabs

The site disables "export data". I read the values the dashboard itself renders: one session per month, the story's Month filter set to that month, then the "MROS1 Response map" worksheet read. Scripts: `_code/tab4.py`, `tab5.py`, `tab6.py`, `tparse2.py`.

**Files** (`firststage/fsc_tableau/`):

| file | content |
|---|---|
| `fsc_som_2024_food_cash_reached_district_month.csv` | 848 district-months, 70 districts, Jan–Dec 2024 |
| `fsc_som_2025_food_cash_reached_district_month.csv` | 646 district-months, 70 districts, Jan–Dec 2025 |
| `fsc_som_2026_food_cash_reached_district_month.csv` | 279 district-months, Jan–Aug 2026 (Sep–Dec not yet reported) |
| `..._by_donor.csv` (2024, 2025) | same, split by the donor the reporting partner entered |
| `..._WFP.csv` (2024, 2025) | WFP as reporting organisation only |

- **Variables:** month, admin1, admin2, admin2 P-code, people reached (SO1: emergency food and cash/voucher assistance), number of implementing partners.
- **Level and time:** district x month. People reached is a monthly count, not cumulative.
- **Validation:** for every month, the district sum equals the dashboard's monthly total. Examples: Jan 2025 = 1,000,710; Jan 2024 = 1,660,085.
- **Totals:** 17.0 m person-months in 2024 against 11.1 m in 2025. 60 of 70 districts fell.
- **Cross-check:** the 2024 totals agree with the OCHA/ICCG 2024 4W in section 1b (Food Security, Jan 2024: 1.69 m).

**Comparability, 2024 vs 2025: good.**

- Same workbook design, same indicator, same partner 5W reporting system, same P-codes.
- Coverage rules can shift (which partners report). Track the partner-count column.
- 2024 includes the late-2024 scale-down (Oct 2024: 0.70 m), so do not treat 2024 as a flat baseline.
- Districts with zero reach in a month are absent from the map, not reported as 0. Fill zeros for districts reached in other months.

**Donor split: weak for identifying US money.**

- Most WFP reach carries a blank or garbled donor label ("-??", "Saturday, December 30, 1899") or "Other"/"Multiple Donor".
- Explicit BHA-labelled reach is small: 2024 roughly 14k–466k a month, falling after April; 2025 roughly 20k–99k.
- The donor and WFP selections are missing for Dec 2024 and Nov 2025. In those months the selector sheet was empty for this method.

**Also in the workbook, not scraped:**

- livelihood (SO2) cumulative response by district
- partner presence by district
- breakdowns by modality, activity, population group and donor

The same scripts can fetch them by changing the story point and worksheet name.

**Contact for the underlying 5W file:** FSC Somalia coordination, info.somalia@fscluster.org.

### 1b. OCHA/ICCG 2024 4W, record level, recovered from a pivot cache. **Derived file.**

The HDX "Cash Based Programming in Somalia" resource "Somalia_CWG_4Ws Final Dataset 2024" (`hdx_response/som/cwg_4w/cwg_4w_2024.xlsx`, already in the project) looks like a pivot-table summary. Its Excel pivot cache, however, holds the full **inter-cluster 4W data**: 111,504 records. I extracted it (`_code/pivotcache.py`):

- `firststage/cwg_4w/som_4w_2024_records_from_pivotcache.csv`
  - **Variables:** reporting month, cluster (all clusters), reporting organisation, implementing partner, **donor**, programme, activity, status, modality (cash/voucher, in-kind, MPCA, safety nets), transfer value, **US$ transferred**, **individuals and households reached**, region, district and P-codes.
  - **Coverage:** Jan–Dec 2024, 72 districts, 309 organisations.
  - **Totals:** Food Security 17.4 m individuals and US$201 m. MPCA 6.0 m and US$60 m. Nutrition rows exist, but reach is sparse (0.46 m).
- `firststage/cwg_4w/som_2024_district_cluster_reach_from_pivotcache.csv`: district x cluster cumulative reach against HNRP targets, monthly cumulative columns.

**The 2025 equivalent:**

- `cwg_4w_2025.xlsx` has no pivot cache.
- It holds only pivot outputs: national monthly by cluster, and district x organisation x cluster totals.
- It covers Jan–Jun 2025 only, although HDX lists the dataset as running to June 2025.

**Comparability:** the record-level data exist only for 2024. For 2025, use the FSC dashboard (1a) for food security. The full 2025 4W would have to be requested from OCHA Somalia (ochasomalia@un.org; ICCG information management).

### 1c. Already in the project (unchanged): OCHA 3W operational presence, 2024–Jun 2026

`hdx_3w/som/somalia-operational-presence/`:

- `3W_Operational_Presence_Dataset_Jan-Nov_2024.xlsx`
- `..._January_-_December_2025.xlsx`
- `..._January_-_June_2026.xlsx`

Unit: organisation x cluster x district x month presence, with no volumes. Comparable across 2024 and 2025 once 2024 is collapsed to unique organisation x cluster x district x month: roughly 1,000–1,200 rows a month in 2024 against 700–1,100 in 2025.

Two cautions:

- The 2025 files use 88–89 district codes, against 72 in 2024. Check the P-code vintage before comparing.
- Presence is not volume. It is useful as a partner-count first stage.

The 2026 HNRP cluster response monitoring file (`hdx_response/som/somalia-2026-hnrp-...`) has district reach, but only for Jan–Mar 2026. No 2024 or 2025 version is on HDX.

---

## 2. Nutrition Cluster: admissions, sites and stockouts

### 2a. Somalia Nutrition Cluster ONA programme database, 2018–Sep 2026. **Downloaded.**

**Source.** "Nutrition Cluster Programme Data – ONA Raw Data", a public Google Drive folder (`https://drive.google.com/drive/folders/1Dl--uLDcgHhqhhe9qq5y0an9TelgKibe`) linked from `https://response.reliefweb.int/somalia/nutrition`. The folder holds one file, `SOMALIA NUTRITION SERVICES_DATABASE_2018-2026_(September 2026)Final..xlsx`.

That file is **290 MB**, above the ~100 MB limit. I did not know the size until it had downloaded. I extracted the raw sheet and then deleted the xlsx, so nothing over the limit is stored.

**File:** `firststage/nutrition_cluster_ona/som_nutrition_ona_site_month_2018-2026.csv.gz` (24 MB). It is the full "DATA from ONA" sheet: 119,116 rows x 359 columns, built by `_code/ona_extract.py`.

- **Unit:** facility (site) x reporting month. Fields include region, district, district P-code, site type (fixed/mobile), organisation and implementing organisation.
- **Admissions:** OTP, SC and TSFP admissions by sex and admission type. Pre-computed SAM and MAM totals are included.
- **Programme flows:** beginning- and end-of-month caseloads; recovered, died, defaulted and transferred.
- **Other services:** BSFP, MCHN, IYCF, micronutrients, vitamin A and screening counts.
- **Stockout days:** RUTF, SC supplies and RUSF/Plumpy'Doz/SuperCereal.
- **Funding source:** UNICEF cash/supplies, Other, plus free text such as "BHA", "USAID", "BHA THROUGH CARE", "WFP" or "SHF".
- **Coverage:** 2023: 21,485 rows; 2024: 15,108; 2025: 12,395; Jan–Sep 2026: 7,732. Reports come from all 84–86 districts every month.

| | sites reporting a month | SAM admissions a month | MAM admissions a month |
|---|---|---|---|
| 2023 | 1,270–1,700 | 45–59k | — |
| 2024 | 990–1,290 | 37–51k | 32–83k |
| 2025 | 710–1,070 | 30–47k | 26–79k |

Site-months whose free-text funding field names a US source (BHA, USAID, OFDA): about 40–70 a month in early 2024, against 10–40 in 2025.

**Comparability, 2024 vs 2025: good.**

- Same ONA form and the same columns throughout.
- "Sites reporting" is a proxy for functioning sites. A missing report is not necessarily a closure.
- The funding-source field is mostly coarse (UNICEF/Other). The free text names US funding for only about 3–4% of rows.

**Other Nutrition Cluster products (not downloaded):**

- The Power BI Nutrition Cluster Response Dashboard, which runs from January 2019, is a public "publish to web" view: `https://app.powerbi.com/view?r=eyJrIjoiMTM0N2NjOGYt...`, on the same page. Not needed, since the ONA file is the underlying data.

### 2b. Nutrition Cluster 3W matrix. **Downloaded, low value.**

`firststage/nutrition_cluster_3w/som_nutrition_cluster_3w_matrix.xlsx`, a Google Sheet export. It lists about 1,900 sites with organisation, district, coordinates and the services offered (OTP, TSFP, SC, BSFP etc.). It has **no date or reporting period**, so it cannot show change over time.

---

## 3. OCHA reporting on 2025 funding-cut impacts

### Downloaded (`firststage/ocha_cuts_reports/`)

**`Cost_of_Inaction_July_2025.pdf`** (OCHA, data as of May–July 2025):

- Nutrition Cluster reach Jan–May 2025: 1.26 m, against 2.06 m in Jan–May 2024 (−39%). Eight districts reported no SAM admissions.
- FSC reach Jan–May: 1.23 m against 2.38 m (−48%).
- Over 150 health facilities closed in H1 2025:
  - South West State: 40 facilities closed; mobile outreach teams down from 74 to 25.
  - Puntland: 79 facilities stopped functioning, including all 29 public health units.
  - Garbahaarey: 2 MCH centres closed.
  - South Gaalkacyo: services disrupted for more than 372,000 people.
- Banadir: 20 TSFP sites closing.
- MPCA Q2 2025: 287,300 people assisted.
- Child protection: response shrank from 45 districts (February) to 23 (June).
- WASH: 60 or more boreholes non-functional across 15 districts.

**`Monthly_Humanitarian_Update_Sept-Oct_2025_Final.pdf`:**

- Supplementary feeding sites fell from 617 to 300.
- More than 200 health facilities closed or non-functional.
- Food assistance: 1.1 m people in August, falling to 350,000 in November.
- District detail:
  - Galmudug: 10 health facilities closed. Nutrition sites in Cadaado and Cabudwaaq lost support. Therapeutic feeding centres in Balanbal and Cabudwaaq closed. Two more sites in Cabudwaaq and one in Dhuusamareeb closed.
  - Hiraan: OTP, SC and TSFP suspended in Buloburte and Jalalaqsi.
  - Hirshabelle: more than 60 nutrition sites closed in June.
  - Bari: TSFP suspended at 25 sites.

### What does not exist publicly

I found no OCHA table listing suspended or closed sites by district.

The figures above are narrative, mixing district- and state-level detail, and not systematic. Use them only as validation or anecdote. The ONA site-month file (2a) is the systematic version for nutrition.

### Other sources not downloaded

- **Health Cluster:** a public Power BI dashboard (`https://app.powerbi.com/view?r=eyJrIjoiOTIwYzc1YzAt...`, linked from `https://response.reliefweb.int/somalia/health`) and Google Drive bulletin folders. The November 2025 Health Cluster bulletin PDF timed out twice and was not saved. A facility-functionality list (HeRAMS/DHIS2) would have to be requested from WHO Somalia / the Health Cluster coordinator.
- **ReliefWeb API:** now requires an approved `appname`, so report searches were done through the web pages.

---

## 4. REACH household and key-informant surveys

### 4a. REACH Somalia MSNA. **Downloaded** from the REACH Resource Centre (no login)

On HDX, both 2025 phases are "request data" (HDX Connect), but the same files are open on repository.impact-initiatives.org.

Files are in `firststage/reach_msna/`:

| file | round | households | districts | interview dates |
|---|---|---|---|---|
| `REACH-SOM_2023_MSNA_Clean-Data.xlsx` | 2023 | 10,336 | 59 | Jul–Aug 2023 |
| `REACH_MSNA_2024_clean-dataset_HH-data_Somalia_final.xlsx` | 2024 | 12,233 | 64 (`admin_2`, names) | 14 May–17 Jul 2024 |
| `REACH_SOM2503_Clean_Dataset_MSNA_July_2025.xlsx` | 2025 phase 1 | 1,134 | 13 | 12–28 Jul 2025 |
| `REACH_SOM2503_Clean_data_MSNA_2025_Phase2.xlsx` | 2025 phase 2 | 6,988 | 33 (`admin_2`, P-codes) | 20 Sep–15 Oct 2025 |

The 2024, 2025 phase 1 and 2025 phase 2 results tables are also downloaded.

**Assistance variables:**

- `aap_received_assistance_12m` and `aap_received_assistance_date` (past 30 days, 1–3, 4–6 or 7–12 months)
- `fsl_source_food/food_aid`, `assistance_in_kind`, `assistance_cva`
- `cm_income_source/assistance`
- barriers to assistance

**Headline rates (unweighted):**

- 2024: 32% of households received any aid in the past 12 months; 17% in the past 3 months.
- 2025 phase 2: 56% and 26%.

The 2025 rates are higher because phase 2 sampled the 33 priority, high-need districts. That is a sample-composition effect, not a sign that aid rose.

**Comparability: poor for a 2024-vs-2025 district panel.**

- One cross-section a year, at different times of year.
- Different district samples. Phase 2 = priority districts. Phase 1 = 13 districts (urban/FSN focus).
- 2024 identifies districts by name, 2025 by P-code.
- To use it, map names to P-codes (the COD-AB crosswalk is in `input/areas`), keep the overlapping districts and apply the weights. Not done here.
- It is one round a year, not monthly. Best used as a household-level check, not as the main first stage.

### 4b. REACH Humanitarian Situation Monitoring (HSM, hard-to-reach). **Downloaded.**

`firststage/reach_hsm/` has six rounds:

| round | KI rows | districts |
|---|---|---|
| Mar 2024 | 2,013 | 25 |
| Jul 2024 | 979 | 15 |
| Dec 2024 | 1,660 | 24 |
| May 2025 | 1,866 | 24 |
| Jan 2026 | 3,457 | 41 |
| Apr 2026 | 1,787 | 41 |

- **Unit:** settlement x key informant.
- **Same questions in every round:** `receive_aid`, `common_aid`, and `barriers_aid/aid_stopped`.
- **Share of KIs saying the settlement received aid:** 18% (Mar 2024), 9% (Jul 2024), 7% (Dec 2024 onward).
- **Share reporting "aid stopped":** 15–23% in 2024–May 2025, then 28% in Jan–Apr 2026.

This is a usable secondary, settlement-level series for hard-to-reach districts. It is not monthly and covers only about 15–41 districts.

---

## 5. Lists of terminated vs retained US awards naming Somalia partners

**No open, complete list was found.**

- **HigherGov:** posts only the first tranche of about 230 awards (13 Feb 2025). It has no Somalia rows, and its xlsx needs a subscription.
- **Congressional list:** KFF and CGD (Sandefur and Kenny, 26 March 2025) analysed the terminated/retained list shared with Congress. The award-level file was not posted. CGD gives Somalia a cut of $113 m, 22% of the country programme. Congressional Democrats (May 2026, June 2026 letters) report that the State Department never sent a final list with country fields. Ask the CGD co-authors or HFAC/SFRC Democratic staff for the Congress list.
- **Already in the project:** `input/usaspending/som_awards_fy22_25.csv` (461 Somalia awards; not modified). 38 awards have end dates between 20 Jan and 30 Jun 2025, totalling $380 m. They include:
  - WFP IDA award 720BHA23IO00022, $193 m, ending 19 Mar 2025
  - BHA awards to "Miscellaneous Foreign Awardees", ending Jan–Mar 2025
  - DT Global stabilisation (USAID), ending 12 Mar 2025

  Moved-up end dates are a noisy indicator of termination.
- **Already in the project:** country-level cut estimates in `../USAID budgets/input/usaidcuts - country.csv`. Somalia disbursements fall from $757 m (2024) to $388 m (2025).
- **Partner-level exposure:** the best open route is the donor field in the 2024 4W records (1b: "BHA", "USAID", "BHA/USAID" on about 7,000 records) and in the nutrition ONA free text (2a). Together they give a pre-period district measure of US-funded activity, a Bartik-style exposure.

---

## 6. WFP district-level beneficiaries

- **No standalone open WFP district x month file exists** (see `references/wfp_subnational.md`; Annual Country Reports are national).
- WFP's district-month reach is available through the FSC dashboard: `fsc_tableau/fsc_som_{2024,2025}_food_cash_reached_district_month_WFP.csv`. WFP is the reporting organisation for about 85–90% of FSC SO1 reach (Jan 2025: 906k of 1.0 m). Dec 2024 and Nov 2025 are missing in the WFP and donor splits only.
- WFP rows are also in the 2024 4W records (1b).
- The CWG Power BI and WFP "Somalia Cash Dashboard 2023" Tableau are linked from `response.reliefweb.int/somalia/somalia-cash-working-group`. Not scraped.
- **To ask:** WFP Somalia VAM/M&E for distribution data (district x month x modality).

---

## Ranked recommendation: district-level 2024-vs-2025 delivered-aid measure

1. **FSC monthly food and cash reach by district** (`fsc_tableau/fsc_som_2024_*.csv`, `fsc_som_2025_*.csv`; 2026 to August).
   - **Why:** the largest aid flow; district x month, 70 districts; the same system and indicator in both years; validated against dashboard totals; 2026 included for persistence.
   - **Use:** log people reached per district-month (or per capita), with zeros filled.
2. **Nutrition Cluster ONA site-month database** (`nutrition_cluster_ona/som_nutrition_ona_site_month_2018-2026.csv.gz`).
   - **Why:** a district x month nutrition first stage from 2018 to 2026, with the same form throughout:
     - number of sites reporting (a functional-site proxy)
     - OTP/TSFP admissions
     - RUTF/RUSF stockout days
   - Its long pre-period allows event-study pre-trends. It sits closest to the child-nutrition outcome.
   - **Caveat:** admissions mix supply and need. Sites reporting and stockouts are the cleaner supply measures.
3. **Pre-period US exposure, as the instrument side:** the donor field in the 2024 inter-cluster 4W records (`cwg_4w/som_4w_2024_records_from_pivotcache.csv`), plus the ONA funding free text.
   - **Why:** gives district shares of 2024 activity funded by BHA/USAID, to interact with the 2025 cut.
   - **Supplement:** OCHA 3W presence (2024–2026, partner counts) as an extensive margin.
