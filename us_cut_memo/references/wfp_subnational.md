# WFP food assistance below country level: what exists (Somalia, Sudan, Ethiopia, Nigeria, 2015–2024)

Checked October 2026. Follows section 4 of `references/subnational_aid.md`. Code: `code/64_wfp_subnational.py`. Documents: `input/subnational_aid/wfp_acr/` (`index.csv` lists every ACR/SPR with its URL; `text/` holds the page text; `<iso3>/sitreps/` holds the sampled situation reports and dashboards; `reliefweb_wfp_reports.csv` lists 802 WFP sitreps, country briefs and dashboards on ReliefWeb, 2015 to Jan 2025).

## Bottom line

1. **WFP's own reports have no sub-national tables of beneficiaries, tonnage or cash.** This holds for the Annual Country Reports (2018/19–2025), the Standard Project Reports (2015–2019), the monthly country briefs, the situation reports and the emergency dashboards. Beneficiaries, tonnage and cash-based transfers are reported nationally, by activity, sex and age. Regions show up in three ways only:
   - narrative sentences, about 0–13 per report, often for several regions at once;
   - outcome-indicator tables (food consumption score, coping index) that some ACRs tag with a region;
   - map graphics: a binary "LGAs targeted" map, or bubbles for people assisted by region.

   Building a district panel from the PDFs would mean hand-coding scattered sentences that are not comparable across years. **Not worth it.**
2. **The usable WFP-specific sub-national series is WFP's own reporting to the OCHA 3W/4W/5W files**, which the pipeline already caches. In those files, WFP is the reporting organisation on 1–57% of rows. `code/64_wfp_subnational.py` keeps only WFP rows, using 62's parsers, P-code matching and de-duplication. It writes `input/subnational_aid/tidy/wfp_<iso3>.parquet`. Every row comes from a spreadsheet; none is hand-transcribed.
   - **Somalia:** district presence 2016 Q1 and 2019–2026; **individuals reached** 2016 Q1, every quarter of 2019, Jan–Mar 2020, Mar 2021 and monthly Jan–Sep 2024; **US$** 2023 (Jan–Mar) and Jan–Sep 2024.
   - **Sudan:** locality presence 2014–2026 (annual until 2019, then snapshots, monthly from 2024); reach only Apr–Jun 2023.
   - **Ethiopia:** zone presence Aug 2017, 2019–2026 (monthly 2022–24).
   - **Nigeria:** LGA presence Dec 2019–2025, monthly most months.
3. **It can extend the district panel, mainly for Somalia.** WFP reach by district gives a WFP-only version of 61's reach variable for 2019 and 2024, and WFP presence gives a WFP-only version of the presence variable. Everywhere else the WFP data are presence (activity rows), not volumes.

## 1. Annual Country Reports and Standard Project Reports

The ACR template has been the same across countries since 2018. National tables: beneficiaries by sex/age/residence/programme, food and cash-based transfers planned versus actual by strategic outcome (mt; US$), and outcome indicators. Some outcome-indicator tables carry `Location: <region>`. Those are survey outcomes such as FCS, rCSI and MAD, not assistance. Sub-national quantities of assistance appear only in narrative text.

SPRs (2015–2018/19, one per project) have the same structure: national "Annex: Resource Inputs", beneficiary tables by project, and outcome indicators. Some outcome tables carry location text such as "ALL REGIONS EXCEPT …" or "REGIONS COVERED BY JOINT RESILIENCE PROGRAMME (GEDO, TOGHDEER, BARI)". Regions get only qualitative mentions.

| country | year | document (file in `wfp_acr/`) | sub-national WFP figures | level / measure / page |
|---|---|---|---|---|
| Somalia | 2016 | SPR PRRO 200844 (`som/spr_2016_PRRO200844_56edbe85.pdf`) | none quantitative | Regions named in narrative (FFA "in all regions except Middle Juba …"); outcome tables by region group |
| Somalia | 2018 | SPR PRRO 200844 (`som/spr_2018_PRRO200844_WFP-0000103929.pdf`) | none | — |
| Somalia | 2019 | ACR SO01 (`som/acr_2019_SO01_WFP-0000113843.pdf`); SPR Jan–Mar 2019 | none | 1 narrative sentence (flood-affected Puntland) |
| Somalia | 2020 | ACR SO01 | safety-net reach in "21 districts" (p. 3); one-off rations Somaliland 37,000 children | narrative, 5 sentences |
| Somalia | 2021 | ACR SO01 | outcome tables for Banadir (pp. 50–72), Garowe/Hargeisa (p. 49) | admin-1/town; FCS-type outcomes, not assistance |
| Somalia | 2022–2025 | ACR SO02 + 4-page summaries | 1–3 sentences per year (e.g. 2024 p. 21: FFT for 5,000 people in Bay and Galgaduud, 28 mt and US$240,000) | narrative only; the summaries' maps show offices, not beneficiaries |
| Sudan | 2015–2017 | SPRs (PRRO 200808, EMOPs) not downloaded | — | Given the template, would be national (Ethiopia and Somalia SPRs checked) |
| Sudan | 2018 | ACR SD01 (`sdn/acr_2018_SD01_WFP-0000104230.pdf`) | p. 11: drought response by state (e.g. 5,030 in North Kordofan, 9,670 in Gedaref); 100,000 IDPs in North Darfur | admin-1, narrative, 6 sentences |
| Sudan | 2019–2023 | ACR SD02 | 0–3 sentences per year (2021 p. 24: SFSP cash to 304,649 people in Khartoum, West and North Darfur; 2023 p. 18: 133,000 resilience beneficiaries across seven states) | narrative; some footnotes list target states (2021 p. 34) |
| Sudan | 2024 | ACR SD02 | p. 3: 357,000 hot meals in Khartoum; Khartoum/Gezira digital cash 150,000 | narrative, 11 sentences |
| Sudan | 2025 | ACR SD02 | 2 sentences | — |
| Ethiopia | 2017 | SPR PRRO 200712, PRRO 200700 (`eth/spr_2017_*.pdf`) | WFP's relief caseload is the Somali Region (3.7 m targeted, p. 15); R4 in 11 woredas of Tigray | admin-1, narrative |
| Ethiopia | 2019–2020 | ACR ET01/ET02 | 2019: relief to over 2 m in Oromia and Somali; FFV in Amhara | narrative, 1–11 sentences |
| Ethiopia | 2021–2025 | ACR ET02 | narrative (2021 p. 14: ration cuts for 2.4 m in Somali Region; 2022 p. 18: 365,259 mt to 6.3 m people in Afar, Amhara, Somali, Tigray combined); **outcome tables by region** (Somali, Amhara, Afar, Tigray, Gambela; 2021 pp. 42–79, 2022 pp. 46–87, 2023 pp. 50–101, 2024 pp. 50–98, 2025 pp. 50–102) | admin-1; outcomes (FCS, rCSI, MAD), not assistance |
| Nigeria | 2016–2018 | Regional EMOP 200777 SPRs not downloaded | — | — |
| Nigeria | 2019–2020 | ACR NG01 | 2020 p. 14: transfer values by LGA (Maiduguri/Jere, Damaturu); Abuja/Kano/Lagos COVID-19 response 153,000 | narrative |
| Nigeria | 2021–2025 | ACR NG01/NG02 | 2021 p. 27: livelihoods cash to 69,800 people in Borno; outcome tables for Borno/Yobe (2021 pp. 40–61; 2022 pp. 45–64; 2023 pp. 35–54; 2024–25 Yobe only) | admin-1; outcomes |

Not on the WFP ACR pages: ACR 2018 for Somalia, Ethiopia and Nigeria (they were still on PRRO/EMOP SPRs; Somalia's 2018 SPR was found on docs.wfp.org), and the Sudan ACR summary for 2024. 2015–2017 SPRs exist on docs.wfp.org under hash IDs, but there is no index. The document search (docs.wfp.org/api/documents/?search=) and the WFP library (wfp.tind.io) return 403 or a bot challenge.

## 2. Situation reports, country briefs and dashboards

ReliefWeb lists 802 WFP items on the four countries, 2015 to Jan 2025 (`reliefweb_wfp_reports.csv`):
- Country briefs: monthly, about 2 pages.
- Sitreps: Somalia 2015, 2017, 2020, 2022–23; Sudan 2023–24; Ethiopia 2015–18 and 2020–23; Nigeria 2016–24 (many are ETS telecom reports).
- Emergency dashboards: Nigeria 2016–22; Ethiopia drought 2016–17; Northern Ethiopia 2022–23.
- Many "Operation Overview" items are Logistics Cluster products.

One sitrep per country-year was sampled (21 files), plus the dashboard types (`<iso3>/sitreps/`):

| country | product (sampled) | sub-national content | usable? |
|---|---|---|---|
| Somalia | Drought sitrep #4 (May 2017); famine-prevention sitreps (Sep 2022, Apr 2023); El Niño update (Nov 2015) | Narrative mentions only (e.g. 2,400 displaced people assisted in Mahadey district). The 2017 map shows offices | No |
| Somalia | "Somalia Cash Dashboard 2023" | Cash Working Group, all partners, by district. Already in the 3W/CWG data | Not WFP-specific |
| Sudan | External sitreps 2023–24, country briefs 2016–22 | State names with occasional figures (e.g. about 80,000 reached in Khartoum, Jul 2023) | No (scattered) |
| Sudan | Food Security & Livelihoods Sector dashboards 2017–19, SNAP dashboards 2018 | Sector (all partners) and safety-net monitoring | Not WFP-specific |
| Ethiopia | Drought emergency dashboards 2016–17 | National relief rounds (dispatch/distribution %), national people assisted | No |
| Ethiopia | **Northern Ethiopia emergency dashboards, May 2022–Feb 2023 (about 9 issues)** | **People assisted by WFP in Tigray, Afar and Amhara, by activity (food distribution, nutrition, refugees), monthly**, plus people targeted per round. Admin-1 only, read off the map graphic | Hand-transcribable (about 9 × 3 regions × 3 activities). Admin-1 is coarser than FEWS NET units; not done |
| Ethiopia | TSFP (MAM treatment) food-movement update, May 2017 | Mt dispatched/delivered by region (Somali, Oromia, Amhara, SNNPR) for Jan–May; woreda maps of delivery timeliness (categorical) | One-off; no |
| Nigeria | Emergency dashboards 2016–22 | "WFP targeted LGAs" map (binary shading, about 30 LGAs) as an image; IDP figures | Presence only, as an image. The 3W data gives LGA presence directly |
| Nigeria | External sitreps 2016–23 | LGA mentions with new-arrival counts (e.g. Bama 3,389, Dikwa 2,597, Jul 2018) | No |

HungerMap is national. DataBridges needs an API key (not requested). No public WFP country-office dashboard with district beneficiaries was found.

## 3. WFP rows of the OCHA 3W/4W/5W files (the extractable part)

`wfp_<iso3>.parquet` is long: `iso3, admin1, admin1_pcode, admin2, admin2_pcode, period_start, period_end, period_type, cluster, measure, value, cumulative, latest_window, source_file, page (NA), hand_transcribed (False)`. The measures are:
- `activity_rows`: WFP activity rows in the unit, a presence/intensity count;
- `reached`: individuals reached, summed over activity rows;
- `usd`: US$ transferred.

`wfp_coverage.csv` summarises country × year × measure. File-by-file decisions are in `wfp_log_<iso3>.txt`.

| country | measure | periods | admin-2 units with WFP | notes |
|---|---|---|---|---|
| Somalia | activity_rows | 2016 Q1; 2019 Q1–Q4; monthly Jan–Aug 2020; Mar and Sep 2021; 2022 (Jan–Mar, Oct, drought file); 2023; monthly 2024–Jun 2026 | 61–83 districts (of 74–90) | 98–100% matched to COD-AB |
| Somalia | reached | 2016 Q1 (11 districts); 2019 Q1–Q4 (73–74); Jan–Mar 2020 (73); Mar 2021 (2); **monthly Jan–Sep 2024 (68)** | | 2019–21 figures are cumulative over an activity's duration (62's rule). 2024 is by reporting month: 1.1–2.5 m people a month |
| Somalia | usd | Jan–Mar 2023 (US$136 m); monthly Jan–Sep 2024 (US$182 m) | 68 | Cash and voucher transfers |
| Sudan | activity_rows | annual 2014–2019 (45–92 localities); snapshots Aug and Nov 2020, Mar and Dec 2021, Jul 2022, Apr–Dec 2023; monthly 2024–Jul 2026 (125–161) | | Presence only |
| Sudan | reached | Apr–Jun 2023 (39 localities, 1.22 m) | | One file |
| Ethiopia | activity_rows | Aug 2017; Jun, Oct and Dec 2019; Mar–Aug 2020; Jun–Aug 2021; monthly 2022–2023; 10 months 2024; 2025; Q1 2026 | 15–60 zones | Zone level (COD-AB admin-2). Woreda is in the files but not kept. No volumes. WFP rows are few in 2024 (the 2023–24 distribution pause) |
| Nigeria | activity_rows | Dec 2019; monthly 2020–2025 (about 9–12 months a year) | 32–45 LGAs | Borno, Adamawa, Yobe (plus Katsina, Sokoto, Zamfara in some files). 100% matched. No volumes (people-reached column empty for WFP) |

Caveats:
- WFP rows include activities WFP reports for its cooperating partners. Partners may also report the same activities under their own name, so do not add WFP and partner rows together.
- `activity_rows` depends on how finely a given 3W release splits activities. Compare it within a release series, or use presence (more than 0) as the variable.
- Somalia reach 2019–20 comes from quarterly cumulative 3Ws with only 15–41% of rows filled overall. WFP rows are filled better (about 99% in Q2 and Q4 2019 and Jan–Mar 2020), but only 2% in Q3 2019.
- May–Aug 2020 Somalia files are presence-only in 62's manifest. WFP rows there do carry reach values; 62 does not use them.

## Recommendation

- **Do not build a panel from ACRs, SPRs, sitreps or dashboards.** Coverage is a handful of narrative figures per country-year, at admin-1, for different activities each year, and mostly about multi-region totals. The only consistent PDF series is the Northern Ethiopia dashboards (admin-1, 2022–23). It could be hand-transcribed in about an hour if a Tigray/Afar/Amhara check is wanted, but it cannot be matched to FEWS NET livelihood-zone units.
- **Do use `wfp_<iso3>.parquet`.**
  - For Somalia, add WFP-only reach (2019, Jan–Mar 2020, Jan–Sep 2024) and US$ (2023 Q1, 2024) to `subnational_SOM`. Join on `admin2_pcode`, map through `fews_admin2_som.csv`, and use the same area-weighting as 61's `attach_3w`. This gives a WFP-specific "aid in the district" measure for test (b): reach in "!" areas against same-phase unflagged areas. WFP is the main food-assistance actor: it reports 57% of all rows in the Jan–Sep 2024 Somalia 3W, nearly all of them food security or multipurpose cash.
  - For Sudan, WFP locality presence 2014–2026 can replace "any food-security partner" as a sharper presence variable.
  - Ethiopia and Nigeria have no district panel yet (61 covers SOM/SDN only, and 62 builds the FEWS NET crosswalk only for SOM/SDN). Their WFP presence files are ready once a `fews_admin2_eth/nga` crosswalk exists.
- To get WFP *volumes* by district for 2015–2024 in all four countries, ask WFP directly. Options: VAM DataBridges API key (free on request), the country offices' COMET/SCOPE distribution reports, or the Food Security Cluster's partner-level 5W. That data is not public.
