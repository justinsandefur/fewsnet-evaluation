# Sub-national humanitarian aid: what can actually be obtained

Feasibility check run 8 October 2026. Everything below was downloaded or queried anonymously; nothing needed an account. Downloads are cached under `input/subnational_aid/<source>/` and `code/60_fetch_subnational_aid.py` re-downloads them. Coverage tables: `input/subnational_aid/coverage_*.csv`. Shares and years below are computed from the downloaded files, not taken from documentation.

## Recommendation

1. **Money by district: OCHA's country pooled funds (CBPF) API.** This is the only consistent US$ series below country level. Every project from 2014–15 to 2026 has admin-1 and (90–100% of projects) admin-2 locations, with budget split by location x cluster. The splits add up to the project budget for about 90% of projects. Coverage is Somalia 2015+, Ethiopia 2015+ (zone and woreda), Sudan 2014+ (locality) and Nigeria 2017+ (LGA). The catch is size: pooled funds are about 3–5% of FTS funding to these countries. Use it for test (a), whether money goes where FEWS NET forecasts within a country. It is a clean test of whether OCHA's own targeting follows FEWS NET's maps.
2. **Who is present, and how widely: OCHA 3W/4W on HDX.** These are partner x activity x district x month records. They are the best broad measure of where the whole response is working, food security and nutrition clusters included. Sudan has locality presence every year from 2014 to 2026. Somalia has district presence 2019–2026. Ethiopia has woreda presence 2017 and 2019–2026, monthly from 2022. Nigeria has LGA presence 2019–2026 (northeast only). Use counts of partners or activities per unit-month for test (a). For test (b), they also show whether any food or nutrition actor was working in a flagged area.
3. **People reached, for test (b) (the "!" flags): patchy, but usable for Somalia and Sudan.**
   - Somalia: 3W individuals reached by district, 2019 to Q1 2021 and Jan–Sep 2024. Cash Working Group individuals and US$ by region (2018–20) and by district (2021–25), monthly. Monitoring matrix by region x cluster, 2017–2019. Response data by region x month, 2014.
   - Sudan: people targeted and reached by locality x sector, 2019–2022 (2018 by state).
   - Ethiopia: severe acute malnutrition (SAM) admissions by woreda x month, 2021–2023 only.
   - Nigeria: very little (people reached by LGA, Nov 2019–2020, filled in about 16% of rows).

   Nothing comparable exists before 2014 except CBPF and Sudan's 3W.
4. **Planned locations of response-plan projects (HPC projects API).** Admin-1 to admin-3 P-codes for 95–100% of projects in 2019–2024 (Somalia 2019–22, Sudan 2019–24, Nigeria 2019–25, Ethiopia 2022 only). Requested US$ is not split by location. FTS links about 30–55% of funding to a project in Somalia, Sudan and Nigeria, so FTS money can be spread over planned districts, but only with an equal-split assumption.
5. **Not worth building on for this question:**
   - FTS flows: country only.
   - CERF: no location fields.
   - IATI: locations exist but carry no money split.
   - AidData: development aid; humanitarian projects appear only in Somalia AIMS, up to 2014–17.
   - Country aid management systems: Somalia's has 8 member-state units; Ethiopia's returns 403; none found for Nigeria.
   - WFP sub-national beneficiaries: not public without a key.

**Suggested next step:** build a Somalia unit x half-year panel for 2015–2026. Match CBPF admin-2 budgets (food security and nutrition clusters separately) and 3W partner counts and individuals reached to FEWS NET units through district P-codes (FEWS NET Somalia units are livelihood-zone x region polygons, so use an area-weighted overlay). Run test (a), money and presence against the forecast, and test (b), reach in "!" areas against same-phase unflagged areas. Then repeat for Sudan (CBPF localities 2014+, 3W 2014+, reach 2019–22).

## Source tables

### 1. OCHA Country-Based Pooled Funds (CBPF) API — `cbpf/`

| access | level | unit | sector | years | countries | gaps |
|---|---|---|---|---|---|---|
| Open OData API, `https://cbpfapi.unocha.org/vo2/odata/<table>?$format=csv`; one call returns all funds (the `poolfundAbbrv` filter is ignored by the V2 tables) | Admin-1 and admin-2 (Somalia region/district; Sudan state/locality; Nigeria state/LGA; Ethiopia region/zone, plus woreda as admin-3 for 70–100% of projects); lat/long for each location | US$ budget by location x cluster (`AdmLocClustBdg1/2`, multi-cluster values separated by `\|\|\|`); planned beneficiaries by location (`AdmLocBenClustAgg`); planned and actual beneficiaries by project (`ProjectSummaryBeneficiaryDetail`) | Cluster: food security, nutrition, health, WASH etc. (`MstClusters`) | Somalia 2015–26; Ethiopia 2015–26 (2013–14 country only); Sudan 2014–26; Nigeria 2017–26; also South Sudan 2015+, Yemen 2015+, Afghanistan 2014+, DRC 2014+ | All 8 | Small: 3–5% of FTS funding (Ethiopia 4.5%, Sudan 5.1%, Somalia 2.9%, Nigeria 2.6%, 2015–24). Budgets are allocations, not spending. Admin-2 budgets don't add up to the project total for about 5–15% of projects (mostly 2013–16 and Sudan 2021+, where the sums are 0). Somalia admin-2 coverage drops to 70–89% in 2019, 2023–25 |

Admin-2 coverage (share of projects; `coverage_cbpf.csv`): Somalia 0.96–0.99 except 2019 (0.70) and 2023–25 (0.79–0.89); Ethiopia 0.61 (2015) to 1.00 (2023+); Sudan 0.92–1.00; Nigeria 0.95–1.00. Allocations per year: Somalia $30–71M, Ethiopia $41–99M, Sudan $32–181M, Nigeria $19–36M.

Older table `ProjectSummary` (vo2): one row per project x cluster x location. It has admin-1 % budget shares. In 2014–2018 it also has "Region -> District -> Village" text in `Location`. The vo1 location endpoints (`Location`, `ProjectLocation...`) return 404.

**CERF** (`cerf/project_All.json`, from `https://cerfgms-webapi.unocha.org/v1/project/All.json`, open): 8,665 projects from 2006 on. Fields cover country, sector amounts, and people planned and reached. There is **no location field**; location endpoints return 404. Only the free-text `projectSummary` mentions regions. Somalia, Ethiopia, Sudan and Nigeria each have 5–59 projects a year.

### 2. OCHA 3W/4W/5W on HDX — `hdx_3w/`

Found with HDX CKAN `package_search`, `fq=groups:<iso3> AND vocab_Topics:"operational presence"`. The list for all 8 countries is in `package_search.json`. The four priority countries are fully downloaded (283 MB).

| country | access | level | unit | sector | years | gaps |
|---|---|---|---|---|---|---|
| Somalia | HDX XLSX/CSV | District (P-codes from 2022) | Partner x activity rows. **Individuals reached** in Q1 2019–Mar 2020 CSVs and Mar 2021 (15–41% of rows filled), Jan–Sep 2024 (75% filled). **US$ transferred** (cash) 2019–21, 2023, 2024. Other files are presence only | All clusters; food security 800–5,600 rows per file, nutrition 800–2,800 | Q1 2016; quarterly 2019; monthly Jan 2020–Mar 2022; Oct 2022; 2023 consolidated; 2024; Jan 2025–Jun 2026 cumulative | Sep–Dec 2020 links point to the defunct humanitarianresponse.info (HTML, not data). Nothing 2011–15 except 2016 Q1 (2015 is a web app only). Reach columns change name and header layout between files |
| Ethiopia | HDX XLSX/CSV | Woreda (P-codes), plus kebele/site and lat/long in many files | Partner x activity x woreda x month; donor named; **no people reached** (one 5W in 2021 has reached and quantity fields) | All clusters, including food and nutrition | Aug 2017; Jan–Jun, Oct, Dec 2019; Mar–Aug 2020; Jun–Aug 2021; monthly Jan 2022–Dec 2024; 2025 (Q1, Apr, Aug, Nov, Dec); Q1 2026 | 2016–18 are web apps only (no file). Food distribution by the government's NDRMC/JEOP may be under-reported |
| Sudan | HDX XLSX | Locality (admin-2 codes) | Organisation x sector x locality presence; June 2023 file has indicator achievement and reached by locality | All sectors | Annual 2014–2022; Apr–Dec 2023; monthly-cumulative 2024–Jul 2026 | Presence only in most years. COVID 4W link (Google) returns 401 |
| Nigeria | HDX XLSX/CSV | LGA (P-codes), ward in 2019–20 | Organisation x activity x LGA x month; **people reached** only in Nov 2019–2020 (16% of rows filled) | All sectors | Nov 2019–2020; quarterly 2020–2026 (gaps: Q4 2021, Q2 2026 only for 2026) | Borno, Adamawa, Yobe only |
| South Sudan, Yemen, Afghanistan, DRC | HDX (listed, not downloaded; re-run with `--all`) | County / district / district / province | Presence | All | South Sudan 2013–26 (88 files), Yemen 2021–26, Afghanistan quarterly 2015–24, DRC 2022–26 | Not inspected |

HDX HAPI (`hdx-hapi-operational-presence`) covers 2025 on only.

### 3. Cluster dashboards and response monitoring (Food Security Cluster, Nutrition Cluster) — `hdx_response/`

fscluster.org and nutritioncluster.net return 403 to scripted requests, and FSNAU (fsnau.org) did not respond. The usable cluster data are the HDX copies:

| dataset | level | unit | sector | years | gaps |
|---|---|---|---|---|---|
| Somalia response data (`srf-2014`) | Region x month | Target, cumulative reached by metric | All clusters | 2014 (and a 2015 overall file) | Region only |
| Somalia monitoring matrix (`total-number-of-people-targeted-and-reached-per-region-and-per-cluster`) | Region, state | People targeted and reached x cluster | All | Nov 2017, Sep 2018, Oct 2019 | 2018 Google-sheet copy returns 401 |
| Somalia Cash Working Group 4Ws (`cash-based-programming-in-somalia`) | Region (2018–20), district (2021–25) | Individuals and US$ transferred, monthly | Cash (mostly food security) | Mar 2018–2025 | Aug 2019 file failed once (retry) |
| Somalia drought targeted/reached | District (P-codes) | Affected, targeted, reached | All | Jul 2023 snapshot | One snapshot |
| Somalia 2026 cluster response monitoring | District | Target, reach, % reach | All | Jan–Mar 2026 | Outside period |
| Somalia SAM admissions | District x month x program site | Admissions, discharges (cured, died, defaulted) | Nutrition | 2015 only | One year (UNICEF) |
| Ethiopia SAM admissions (`ethiopia-malnutrition-prevalence`) | Woreda (P-codes) x month | SAM admissions | Nutrition | Jan–May 2021, Jan–Oct 2022, Jan–Jul 2023 | Short |
| Ethiopia 5W (weekly emergency response) | Admin-3 P-code | Indicator quantities, people reached by group | All | Jan–Jul 2021 | One episode |
| Sudan HRP response monitoring | Locality (P-codes from 2021) | People targeted and reached by sector, food and livelihoods separately | All 9–10 sectors | 2019, 2020, 2021 (full year), Jan–Jun 2022; 2018 by state | Stops after mid-2022 |
| Nigeria NE food assistance / FSL coverage | LGA | Coverage vs gap | Food | Jan–Apr 2019 | One snapshot (zipped shapefile/CSV) |
| Nigeria acute malnutrition | State / domain | Caseload in need of treatment (not admissions) | Nutrition | 2021–2026 | Need, not response |

### 4. WFP

| access | level | unit | sector | years | countries | gaps |
|---|---|---|---|---|---|---|
| VAM DataBridges API returns 401 (key needed); dataviz.vam.wfp.org did not respond; HDX has no WFP beneficiary data by admin unit (only national food-assistance sitrep figures, 2017, and market/rainfall series) | — | — | — | — | — | No public sub-national WFP beneficiary or distribution series found. WFP's IATI activities list locations (see 5) without money by location. Annual Country Reports (PDF) were not opened in this probe |

### 5. IATI (via d-portal SQL) — `iati/`

The official IATI Datastore API needs a subscription key (401), so it was not used. d-portal's open SQL endpoint (`https://d-portal.org/dquery?sql=...`) was used instead. Humanitarian means DAC sector groups 720/730/740. Spending means transaction types D/E, scaled by country percentage. "Sub-national" means the activity has any location row not named as the country.

| access | level | unit | sector | years | countries | gaps |
|---|---|---|---|---|---|---|
| Open SQL (d-portal) | Named places or coordinates (district/town names, region names) | US$ disbursements by activity; **no location percentages** (0 of 26,700 location rows in the 4 countries) | DAC humanitarian codes | 2011–2026 | All | About half the location rows have coordinates only, no name. Share of humanitarian spending in activities with any sub-national location (upper bound): Somalia 15–24% (2011–21), 31–39% (2022–24); Ethiopia 30–65%; Sudan 4–29% (2011–21), 37–43% (2022–24); Nigeria 0–59% rising. Main publishers with locations: WFP, UNHCR, UNICEF, FCDO, USAID (Ethiopia, Nigeria), World Bank. Money can't be split across locations |

### 6. OCHA FTS

All 389,000 cached flows (`input/fts/raw`, 2005–2026) were scanned. The 225 distinct destination `Location` objects are all countries, regions, "Global", or Gaza/West Bank. **There are no admin-1 locations.** The route below country level is the `Project` destination object linked to HPC projects (section 6b).

### 6b. HPC response-plan projects — `hpc_projects/`

| access | level | unit | sector | years | countries | gaps |
|---|---|---|---|---|---|---|
| Open API `api.hpc.tools/v2/public/project/search?planCodes=...` (paged, 100 per page) | Admin-1 to admin-3 with P-codes (e.g. SO18 / SO1801) | Requested US$ per project (not split by location); planned locations | Global cluster | Sub-national from 2019: Somalia 2019–22 (96–98% of projects at admin-2; 2020: 57%), Sudan 2019–24 (42% in 2020, otherwise 94–98%), Nigeria 2019–25 (84–98%), Ethiopia 2022 only (94%) | 4 priority | Before 2019 country only. Somalia 2023+, Sudan 2025+ and Ethiopia (except 2022) have no published projects (project-less plans). Share of FTS US$ linked to a project: Somalia 30–70% 2011–22 and 0 from 2023; Sudan 35–76%; Nigeria 26–53% from 2014; Ethiopia mostly 0 (`coverage_fts_project_link.csv`) |

### 7. AidData (William & Mary) — `aiddata/`

| access | level | unit | sector | years | countries | gaps |
|---|---|---|---|---|---|---|
| GitHub `AidData-WM/public_datasets/geocoded` (zip, open) | Coordinates with precision codes and admin gazetteer | Commitments and disbursements per project (not split by location) | DAC sectors | Somalia AIMS 2000–2014 (end dates to 2017); Nigeria AIMS 1988–2020; World Bank IBRD/IDA 1995–2024 | Somalia AIMS: 1,210 projects, **115 humanitarian (DAC 720/730/740)**. Nigeria AIMS: 365 projects, 0 humanitarian. World Bank: Ethiopia 83, Nigeria 69, South Sudan 5 projects, 0 humanitarian. No Sudan or Ethiopia AIMS release | Development aid; humanitarian aid essentially absent apart from Somalia before 2015 |

### 8. Country aid management systems

| system | access | level | unit | years | gaps |
|---|---|---|---|---|---|
| Somalia AIMS (aims.mop.gov.so, Ministry of Planning) | Open JSON API behind the web app (`aimsapis.mop.gov.so/api/Project/GetProjectTitles`, `/Project/GetLocations/<id>`, `/GetSectors/<id>`, `/GetDisbursements/<id>`); 1,262 projects | 8 member-state units (FGS, Banadir, Galmudug, Hirshabelle, Jubaland, Puntland, South West, Somaliland) with % of funds, often "unattributed" | US$ disbursements by year | Projects carry 2015–2020+ financial years | Coarser than FEWS NET units. Sector list includes Food Security. Includes test records (e.g. "REGRESSION TEST"). Optional step `aims_som` in the script (about 1 hour), not run |
| Ethiopia AMP (amp.mofed.gov.et) | 403 Forbidden; ethiopia.ampsite.net no response | — | — | — | Not accessible |
| Nigeria | No public national AIMS found (the AidData Nigeria AIMS release is the historical copy) | — | — | — | — |

## Coverage by priority country (what exists, by year)

| | money by admin-2 | presence by admin-2/3 | people reached by admin-1/2 | nutrition admissions |
|---|---|---|---|---|
| Somalia | CBPF 2015–26; HPC planned 2019–22; cash US$ 2019–25 | 3W 2016 Q1, 2019–26 | 2014 (region), 2017–19 (region), 2019–Q1 2021 and 2024 (district), cash 2018–25 | 2015 only |
| Ethiopia | CBPF 2015–26 (woreda); HPC 2022 | 4W 2017, 2019–26 | 2021 5W only | SAM by woreda 2021–23 |
| Sudan | CBPF 2014–26; HPC 2019–24 | 3W every year 2014–26 | Locality x sector 2019–22; state 2018 | none found |
| Nigeria (northeast) | CBPF 2017–26; HPC 2019–25 | 3W Nov 2019–26 | Nov 2019–2020 (sparse) | none (caseload estimates only) |

## Notes

- Matching to FEWS NET units: CBPF V2, HPC, the 3Ws from 2020 on, and Sudan monitoring carry OCHA COD P-codes or names that match COD-AB. FEWS NET units are livelihood-zone x admin polygons, so the match needs an area- or population-weighted overlay (the boundaries are in `input/fewsnet/units.gpkg`, population in `input/worldpop/`).
- 3W files are not designed as panels. Column names, header rows (two-row headers in Somalia 2020–21) and sheet names change between releases, and later files are often cumulative (Jan–X). Deduplicate by keeping the latest file per period.
- Presence is not money. A partner counted in a district may be serving a handful of people. For test (b), presence is a weak proxy, so use reach (Somalia, Sudan) or CBPF dollars.
- Selection: pooled-fund allocations are decided by OCHA country offices, so a within-country test of (a) on CBPF is partly a test of whether OCHA's targeting follows FEWS NET's maps (which is the point), not of all donors.
- Not checked: WFP Annual Country Report PDFs (whether they have sub-national tables is untested); Somalia Nutrition Cluster dashboards (Power BI, behind 403); Ethiopia ENCU beyond the HDX copies; South Sudan, Yemen, Afghanistan and DRC 3W contents.
