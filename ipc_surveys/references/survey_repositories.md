# Public nutrition and mortality survey data in humanitarian crises: what exists?

Compiled 6 Oct 2026 using web searches and direct checks of sites and APIs from a US connection. "Verified" means I loaded the site or API myself on that date. Where I could not load something, the notes say so.

## Summary

**Is there a central repository?** Not any more. CE-DAT (CRED, UCLouvain) was the only global, public, survey-level database of small-area SMART-type nutrition and mortality surveys. It ran from 2003 to about 2015. CRED's own description now says it is "no longer available for public use" because of funding. As of 6 Oct 2026, cedat.be shows only a holding page ("Please stand by while configuration is in progress"). No one has replaced it. Each SMART survey still ends up as a PDF report: on ReliefWeb, on a nutrition cluster page, on the IMPACT/REACH repository, or on a national site such as FSNAU in Somalia.

**Best current public source for survey-level results:** the **SMART+ aggregator/dashboard** run by Action Against Hunger (ACF) Canada with UNICEF. Its backend API is open and needs no login. It returns per-survey GAM/MAM/SAM (WHZ and MUAC), stunting, crude and under-five death rates with confidence intervals, GPS points and admin areas. It currently holds **249 surveys from Sep 2022 to Sep 2026** (184 with mortality modules), but they are concentrated in Nigeria (114), Ethiopia (51) and Mozambique (37). It only covers surveys run on the SMART+ digital platform, and only those the owner chose to share.

**Best historical sources:**
- **FEWS NET's Data Warehouse (FDW)**: 511 public survey records, mostly Ethiopia (483 surveys, 2000–2018), plus Mauritania and Burkina Faso. GAM, SAM, MUAC, stunting, CDR and U5DR at survey level.
- **UNHCR SENS** for refugee camps: about 52 microdata sets from 2012 to 2024, all "licensed" (registration and request), plus PDF reports.
- **Checchi/LSHTM GitHub repositories**: raw ENA exports of the Somalia SMART surveys used in published small-area mortality estimates.

**Biggest gaps:**
1. No global, maintained, public table of subnational GAM/SAM/CDR results since CE-DAT stopped. Every cross-country analysis has to scrape PDFs.
2. Mortality is the weakest. No public repository covers retrospective mortality surveys across crises. The Elrha/ECHO "Mortality Estimation" partnership is building tools and frameworks, not an open data archive. Somalia's S-MED is a single-country effort.
3. IPC Acute Malnutrition (AMN) phases are not in the IPC public API: its "condition" filter takes only A (acute food insecurity) and C (chronic food insecurity). AMN results reach HDX only as manually uploaded per-country Excel files.
4. WFP phone-survey (mVAM) food consumption data was posted openly on HDX until about 2020. HungerMap LIVE now displays it, but its data API returns "Unauthorized" without a key. The JRC's harmonised dataset (HFID) has FCS and rCSI only up to May 2024.
5. Microdata is mostly unavailable, or available only on request: UNHCR SENS is licensed, and agency SMART datasets are mostly unpublished.
6. US funding cuts in 2025 hit the data backbone. DHS lost USAID funding in February 2025 and runs on interim funding. EM-DAT, CRED's disaster database and CE-DAT's sister, faced closure in 2026.

## Table

| Source | Contents | Coverage | Status | Access | URL |
|---|---|---|---|---|---|
| SMART+ aggregator/dashboard (ACF Canada, UNICEF) | Survey-level GAM/MAM/SAM (WHZ, MUAC), stunting, CDR, U5DR with CIs; GPS; list of indicators per survey; quality grade | 249 surveys from Sep 2022 to Sep 2026 in 16 countries (NG 114, ET 51, MZ 37, SY 14, ZM 7, SS 6, CD 4, SO 3, PS 3, others); 184 with mortality | Active (survey dated Sep 2026) | Dashboard is public; the API (`api.smartplusapp.org/v1/dashboard/survey-results/anthropometry` and `/mortality`) is open with no key | dashboard.smartplusapp.org |
| CE-DAT (CRED, UCLouvain) | Survey-level mortality and nutrition indicators from small-area surveys | About 3,300 surveys from 51 countries (2014 paper count) | Discontinued: funded 2003–Jan 2015; site is a holding page | "No longer available for public use"; CRED keeps the data for its own research and offers collaboration | cedat.be |
| FEWS NET Data Warehouse (FDW) | Survey-level GAM/SAM (WHZ), GAM (MUAC), stunting, anaemia, morbidity, CDR, U5DR; admin-unit codes | 511 surveys: Ethiopia 483 (NGO SMART surveys, 2000–2018), Mauritania 18, Burkina Faso 9 | Records last modified Dec 2024; no surveys after about 2018 | Public through the open API (`/api/survey/`, `/api/nutritionindicator/`, `/api/nutritionindicatorvalue/`) | fdw.fews.net/api |
| UNHCR SENS (refugee camps) | Microdata and reports: anthropometry, anaemia, IYCF, food security, WASH; some mortality | About 52 microdata sets (2012–2024) across about 18 countries (TZA, KEN, BGD, ETH, SSD, CMR, TCD, others); HDX mirrors 54 entries | Active (2023–24 surveys added in 2026) | Microdata are "Licensed" (register and request). PDF reports are on data.unhcr.org. The SENS dashboard and Twine could not be loaded | microdata.unhcr.org/index.php/catalog/SENS ; unhcr.org/sens |
| UNHCR Twine | Camp health information system, including a SENS survey database | Refugee camps | Could not verify: `twine.unhcr.org` did not resolve on 6 Oct 2026; the SENS site still points to it | Unknown | twine.unhcr.org |
| FSNAU Somalia (FAO) | Seasonal (Gu/Deyr) nutrition survey results, burden estimates, IPC AMN; mortality studies; monthly EW-EA dashboard | Somalia; survey reports back to 2007–08; latest Post-Gu 2026 (23 Sep 2026) | Active | Free PDFs; the dashboard is public but survey-level tables are mostly PDF only | fsnau.org/products/survey-reports/nutrition ; dashboard.fsnau.org |
| Ethiopia ENCU (EDRMC, UNICEF) | Coordinates and validates woreda SMART surveys | Hundreds of surveys since 2000 | Active as a unit; no public database found | No public database found. Historical results are visible through FDW (2000–2018); recent ENCU surveys are visible on SMART+ | edrmc.gov.et |
| IPC Acute Malnutrition (AMN) | Area-level AMN phases and GAM burden estimates (built from SMART surveys) | About 20+ countries; HDX has 22 "acute-malnutrition" datasets (e.g. Chad, South Sudan in 2026; Yemen and Mozambique last updated 2024) | Active | The IPC API needs a free key and serves acute and chronic food insecurity only, not AMN. AMN reaches HDX as per-country Excel files; PDFs on ipcinfo.org | api.ipcinfo.org ; data.humdata.org |
| HDX (OCHA) | Scattered SMART summaries (e.g. Mali 2014–2019, Yemen 2019), UNHCR SENS metadata, Somalia mortality estimates 2014–18 | Patchy; most SMART items are pre-2021 | Platform active; most nutrition items stale | Open | data.humdata.org |
| ReliefWeb, nutrition clusters, IMPACT repository | Full SMART survey reports (PDF) | Global, 2000s to present | Active | PDFs are open. The ReliefWeb API now requires an approved "appname", so I could not count reports. nutritioncluster.net blocked automated access | reliefweb.int ; nutritioncluster.net ; repository.impact-initiatives.org |
| WFP HungerMap LIVE / VAM | Phone-survey (CATI/mVAM) FCS and rCSI, with model nowcasts where no survey data | About 90 countries displayed; live surveys in about 38 | Active (re-launched as a "modernized" platform) | Can be viewed in the browser; the data API returns 401 without a key; open HDX mVAM files stop around 2020 | hungermap.wfp.org ; dataviz.vam.wfp.org |
| JRC Harmonized Food Insecurity Dataset (HFID) | Monthly subnational IPC/CH phases, FEWS NET phases, WFP FCS and rCSI | 2007 to May 2024 | Last updated Sep 2025 | Open | HDX: harmonized-food-insecurity-dataset-hfid |
| UNICEF/WHO/WB Joint Malnutrition Estimates | National survey estimates (wasting, severe wasting, stunting) plus modelled stunting/overweight | 1,234 data sources from 164 countries (2026 dataset) | Active (2025 report; Mar 2026 data) | Open download (Excel) | who.int (JME latest estimates); data.unicef.org/resources/jme |
| DHS / MICS | National microdata: anthropometry, birth histories (U5MR); DHS GPS cluster points | Many crisis countries but infrequent; rarely in active-conflict zones | DHS: USAID funding ended Feb 2025; ICF keeps the archive, STATcompiler, API and spatial repository on interim funds. MICS7: 50+ surveys, expected to grow 10–20% in 2026 to fill the DHS gap (e.g. Syria 2025–26) | Free registration and request; GPS on request | dhsprogram.com ; mics.unicef.org |
| Checchi/LSHTM repositories | Raw SMART (ENA) survey datasets plus survey metadata used for small-area mortality and malnutrition models | Somalia (91 surveys, 2014–18 analysis); Nigeria branch; also Sudan, Yemen, Tigray, Gaza work | Static replication files (2022–2026) | Open (GitHub) | github.com/francescochecchi/mortality_small_area_estimation ; .../acute_malnutrition_predictive_models |
| Somalia Mortality Estimation Database (S-MED) (SIMAD, LSHTM, E4C) | Mortality from surveys and surveillance; modelled estimates | Somalia | Built 2024–25 (medRxiv Sep 2025) | Described as "open-source, publicly available"; could not verify a data download | ai.simad.edu.so |
| Elrha/UKHIH "Mortality Estimation in Humanitarian Crises" partnership | Methods, toolkits, frameworks (not a data archive) | Multi-crisis | Phase 2 closed; new 2-year phase co-funded by Elrha and ECHO, led by Save the Children with IMPACT and E4C. Previously part-funded by US BHA | Not a data source | elrha.org |

## Notes by source

**SMART / SMART+.** The SMART project (now run by ACF Canada) never had its own public survey database; that role was CE-DAT's. ACF-France reportedly kept an internal repository of about 1,800 surveys from 31 countries (forum report, not verified). SMART+ (launched 2023) digitises data collection in an Android app and sends results to an "aggregator". The public dashboard reads from an open REST API. I pulled per-survey key statistics from it without logging in (e.g. Tigray Eastern Zone, Jul 2023: GAM(WHZ) 10.8% [7.2–15.8], CDR 0.26/10,000/day). Main limits:
- Coverage depends on which countries use SMART+. Most surveys are Nigerian government ones.
- The `share` flag suggests owners can withhold surveys.
- No microdata is exposed.

**CE-DAT.** Run by CRED (UCLouvain) and started in 2003 as an outcome of SMART; the funding was largely US (OFDA). It held about 3,300 surveys from 51 countries. It is the basis for most pre-2015 cross-crisis analyses. Today it is not downloadable; CRED invites collaboration proposals. In the same CRED unit, EM-DAT lost the US funding that covered 90% of its €300k budget in 2025; in June 2026 it was still seeking donors.

**FEWS NET FDW.** I verified this through the public API. 511 survey records are tagged with nutrition or mortality indicators. 503 of them are SMART surveys, almost all Ethiopian NGO surveys (ACF, SC-UK, GOAL, Concern and others) from 2000 to 2018, presumably compiled from ENCU. There are 5,676 nutrition data series (GAM-WHZ 2,602; mortality 1,589; stunting 440; GAM-MUAC 275). Values are public at `/api/nutritionindicatorvalue/?dataseries=<id>`. This is probably the largest open, machine-readable archive of subnational crisis survey results, but it is Ethiopia-heavy and stops around 2018.

**UNHCR SENS / Twine.** The UNHCR Microdata Library lists 52 SENS datasets (Bangladesh, Botswana, Burkina Faso, Cameroon, Chad, Djibouti, Ethiopia, Kenya, Liberia, Malawi, Mozambique, Nepal, Niger, South Sudan, Tanzania, Zambia and others), all "Licensed data files". The HDX entries (54) only point to these. Reports appear on data.unhcr.org. unhcr.org/sens and the SENS data dashboard returned 403 to automated requests, and twine.unhcr.org did not resolve, so I could not verify the current state of Twine.

**FSNAU Somalia.** This is the most complete national crisis-nutrition series anywhere: twice-yearly (Gu/Deyr) district and livelihood surveys since the early 2000s, published as PDFs. The archive pages link to 2007–08 assessment reports, and the Post-Gu 2026 key results and burden estimates came out on 23 Sep 2026. The EW-EA dashboard (latest data Aug 2026) tracks monthly indicators, including nutrition. I did not confirm which nutrition indicators it shows; they are likely health-facility or screening data rather than survey prevalence. I found no machine-readable survey table, apart from the Checchi repositories, which hold the Somalia SMART datasets.

**Ethiopia ENCU.** This government unit sits in EDRMC with UNICEF support and validates woreda SMART surveys. I found no public online database. Some ENCU surveys from 2023 onward appear on SMART+ (organisation "ENCU"), and older surveys are in FDW. EPHI's research repository (rtds.ephi.gov.et) holds some survey reports; I did not assess it.

**IPC AMN.** I verified the IPC public API's OpenAPI spec: the `type`/condition parameter accepts only "A" (acute food insecurity) and "C" (chronic). AMN analyses are therefore only on ipcinfo.org (PDFs, mapping tool) and in HDX country files curated by HDX (e.g. "IPC_Chad_Malnutrition_Oct2025_Sep2026"). The AMN analyses themselves use SMART survey GAM as the main evidence, but they do not publish the underlying survey table.

**HDX.** Searching "SMART survey" returns 51 datasets: a handful of OCHA Mali summaries (2014–2019), Yemen 2019, and UNHCR SENS entries. The Health Cluster has posted "Somalia mortality estimation 2014–2018". There is no systematic SMART summary series.

**WFP.** HungerMap LIVE shows FCS-based "insufficient food consumption" and rCSI from daily CATI phone surveys (about 38 countries, per a WFP abstract) plus model nowcasts. The HungerMap API's food security endpoint returned 401 without a key, and the VAM microdata catalogue (nada.vam.wfp.org) did not respond. The open HDX "WFP food security indicators" (mVAM) files end around 2020. For research, the JRC HFID on HDX is the best open subnational FCS/rCSI panel (2007–May 2024).

**JME / DHS / MICS.** The JME joint dataset (2026 edition) lists 1,234 national survey sources from 164 countries. It is national-level only, but the survey list is a useful census of which crisis countries have recent anthropometry. DHS provides birth-history child mortality and anthropometry with GPS on request; after USAID support ended in Feb 2025 the archive and API continue on interim funding. MICS7 is expanding to fill the DHS gap.

**Academic compilations.** Checchi et al. (LSHTM) publish replication data on GitHub:
- Somalia small-area mortality, based on 91 district SMART surveys from 2014–2018 (raw ENA exports included), with a Nigeria branch.
- Malnutrition prediction models for Somalia and Kenya.
- Sudan capture-recapture, a Tigray RDS mortality survey, and Gaza food and malnutrition models.

These are open but crisis-specific. S-MED (SIMAD, LSHTM, E4C) is described as a public Somalia mortality observatory; I did not find a download.

**Recent initiatives (2025–26).** Kenny (CGD, 30 Sep 2026) points to an "ongoing effort funded by the UK, US, and the EU to track mortality". This is the Elrha/UK Humanitarian Innovation Hub "Mortality Estimation in Humanitarian Crises Systems Innovation Partnership". After a pause in USAID/BHA funding, it has been revived for 2 years with Elrha and ECHO co-funding. It is led by Save the Children with IMPACT Initiatives and Evidence for Change, and Elrha notes that longer-term funding is "not guaranteed". Its outputs are a strategic framework, toolkits and advisory groups, not a public mortality data repository. Kenny calls for a "global, sustained, independent" system of public, representative mortality surveys in IPC 3+ areas. Nothing like that exists now.

## Sources (checked 6 Oct 2026)
- SMART+: smartmethodology.org/smartplus ; api.smartplusapp.org/v1/surveys-overview
- CE-DAT: cedat.be; Guha-Sapir et al., PLoS ONE 2014 (PMC4204814); CRED "past projects" page (via search); resilience.org, 2 Jun 2026 (EM-DAT)
- FDW: fdw.fews.net/api/survey/, /api/nutritionindicator/
- UNHCR: microdata.unhcr.org/index.php/catalog/SENS; HDX organization:unhcr
- FSNAU: fsnau.org/products/survey-reports/nutrition; dashboard.fsnau.org
- IPC: api.ipcinfo.org/openapi.json; HDX "acute-malnutrition" datasets
- JME: who.int JME latest-estimates page
- Checchi: github.com/francescochecchi
- Elrha: elrha.org/news-blogs/strengthening-the-system-a-new-phase-for-mortality-evidence-in-crises ; elrha.org/news-blogs/counting-every-life-why-mortality-evidence-cant-be-optional-in-humanitarian-crises
- Kenny: cgdev.org/blog/we-dont-know-impact-humanitarian-aid-cuts-we-should-fix
