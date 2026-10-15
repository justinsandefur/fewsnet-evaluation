# What donors pay for a person-month of food assistance, and how well within-area targeting works

Compiled 14 Oct 2026 with web searches, direct PDF reads, and the OCHA HPC public API. Verification tags follow the project convention:

- **[V-full]**: I read the number in the full text (PDF or HTML) or pulled it from the raw API record in this session.
- **[V-abs]**: I read the number only in an abstract, a landing page, or a search-engine extract.
- **[NV]**: Not verified. The figure came from a search summary or secondary report, and I could not open the original.
- **[derived]**: My own arithmetic on verified inputs. It is not stated in any source.

Unit conventions. A "person-month" is 30.4 days. A "full ration" is 2,100 kcal per person per day (Sphere/WFP standard), or the cash value of the food Minimum Expenditure Basket (MEB) that delivers it. "All-in" means the cost to donors: the transfer plus transport, storage and handling (or cash delivery fees), implementation costs, and direct and indirect support costs.

ReliefWeb, humanitarianaction.info, ipcinfo.org and fsinplatform.org returned 403 to WebFetch. Some fscluster.org PDFs downloaded with curl and a browser user agent. HRP cluster figures came from `api.hpc.tools`.

---

## 1. Parameter table

### A. Cost of a full ration, all-in (WFP)

| Parameter | Central | Range | Source | Verif. |
|---|---|---|---|---|
| WFP Eastern Africa: all-in cost of a **full 2,100 kcal ration**, 2021 | $0.66/person/day (≈ **$20/person-month**) | Sudan $0.98, South Sudan $0.93/day (≈$28–30/pm) | WFP RBN 2023, *Cost of Inaction*, p. 10 ("proportionality rule": actual cost scaled up to 2,100 kcal) | [V-full]; pm [derived] |
| Same, 2022 | $0.83/person/day (≈ **$25/person-month**), +25.7% on 2021 | South Sudan $1.21 (≈$37/pm); Somalia $0.49 (≈$15/pm); Ethiopia $0.46 (≈$14/pm) | WFP RBN 2023, p. 11. The key-findings page says "0.81 cents" per day needed, a typo for USD 0.81 | [V-full]; pm [derived] |
| WFP E. Africa, URT actual spend per beneficiary-day, 2021 | $0.43/day for an average ration of **1,130 kcal (54% of 2,100)** | Kenya $0.15, Somalia $0.17, Sudan $0.27, South Sudan $0.91 | WFP RBN 2023, p. 10 | [V-full] |
| WFP E. Africa, 2022: share of minimum kcal delivered to those assisted | **62%** (spent $0.52/day vs $0.81 needed) | — | WFP RBN 2023, p. 2 | [V-full] |
| WFP global, **unconditional resource transfers (URT)**, all-in daily expenditure per beneficiary, **in-kind food** | 2024: $0.51 (≈$15.5/pm) | 2021 $0.36; 2022 $0.38; 2023 $0.39; 2025 $0.43 (≈$11–16/pm) | WFP APR annex "Expenditure per beneficiary", 2021–2025 editions, table of daily expenditures by programme area | [V-full]; pm [derived] |
| Same, **CBTs (cash/value vouchers)** | 2024: $0.53 (≈$16/pm) | 2021 $0.50; 2022 $0.55; 2023 $0.59; 2025 $0.53 (≈$15–18/pm) | Same | [V-full]; pm [derived] |
| WFP global, all programmes, daily expenditure per beneficiary | 2024: $0.45 (food $0.42, CBT $0.51, vouchers $0.46) | 2021 $0.38 → 2025 $0.43 | APR 2024 annex II-D, table 1; APR 2025 annex | [V-full] |
| WFP global, average URT assistance days per beneficiary per year, 2024 | 125 days (food 120, CBT 140) | — | APR 2024 annex II-D, table 6 | [V-full] |
| WFP URT 2024: **transfer value vs transfer cost**, food | commodity $0.20 + transport/handling $0.20, out of $0.51 all-in. The commodity is ~39% of donor cost, so **≈$2.5 per $1 of food delivered** | — | APR 2024 annex II-D, table 5 | [V-full]; ratio [derived] |
| Same, **CBT** | transfer $0.40 + delivery $0.03, out of $0.53 all-in. **≈$1.33 per $1 of cash delivered** | — | APR 2024 annex II-D, table 5 | [V-full]; ratio [derived] |
| Cash vs food delivery cost per transfer, Yemen (WFP, 2011–12 trial) | cash $4.09 vs food $10.37 per transfer, excluding transfer value | cash $7.24 including beneficiaries' travel | Schwab, Margolies & Hoddinott (AAEA draft); Margolies & Hoddinott 2015 (cash always cheaper per transfer across 4 countries) | [V-abs] |

### B. Cash transfer values for a full food basket (Somalia CWG/FSC)

| Parameter | Central | Range | Source | Verif. |
|---|---|---|---|---|
| Somalia Food TV, **80% of food MEB**, household of 6, per month (July 2022 MEB, valid to Mar 2023) | ~$80/HH (2022 average across regions $82) | $60 (Lower Juba) – $90; Banadir (urban) $130 | Joint CWG/FSC Technical Note, Sept 2022, table | [V-full] |
| Implied **full food MEB** (2,089 kcal rural basket) per person-month | **≈$17/person** (82/0.8/6) | $12.5–27 | Derived from the above | [derived] |
| Somalia MPCA TV (80% of full MEB, HH of 6) | ~$115/HH | $90–180 | Same note; average from the 2024 review | [V-full] |
| Rural food MEB composition | 558 g/person/day, 2,089 kcal (rural); 2,181 kcal (urban) | — | Sept 2022 note, annex 2 | [V-full] |
| Somalia 2025 TVs (in force 1 Jan 2025): Food TV = household gap % × 3-yr average MEB | average Food TV $82/HH; average MPCA $115/HH | Food $70–110/HH; average food-needs gap of the most vulnerable 57% (range 40–70%) | CWG/FSC MEB Review & Gap Analysis, Sept 2024, figs 1–2 | [V-full] |
| Implied full food MEB used in 2025 TVs | ≈$140/HH ≈ **$24/person-month** (82/0.57/6) | — | Derived. Rough: an average of ratios, after trimming and harmonisation | [derived] |
| All-in donor cost of a Somalia full-food-MEB cash transfer | **≈$23/person-month** ($17 × 1.33 WFP CBT overhead) | $17–32 | Derived from rows above | [derived] |
| Earlier Somalia CWG bands (Apr 2022) | MPCA bands $60/70/90/100 per HH | — | Sept 2022 note, background | [V-full] |
| Example NGO implementation: FAO (CERF), Somalia 2022 | $40/HH/month for 6 months (= 80% of food MEB) | — | CERF 22-RR-SOM report (search extract) | [NV] |
| Rohingya (Bangladesh, not FEWS NET): WFP full CBT food entitlement | $12/person/month in 2023, cut to $8, then raised to $10 (Jan 2024) | $12.50 full | WFP/press (search extract) | [NV] |

### C. HRP food security cluster requirement per person targeted (planned, all-in, per year)

From `api.hpc.tools/v2/public/plan/{id}?content=entities`: the food security cluster's `cost` divided by its `target` caseload. **Caveats.** These figures cover a whole plan year and include livelihoods and agriculture inputs. Planned ration size and duration vary: many plans assume 50–75% rations or 3–6 months. They are therefore a **lower bound** on the cost of a full year's full ration.

| Parameter | Central | Range | Source | Verif. |
|---|---|---|---|---|
| FSC requirement ÷ people targeted, 55 FEWS NET-country HRPs, 2019–2024 | median **$107/person/yr** (≈$9/pm if spread over 12 months) | IQR $72–127; min $22 (Afghanistan 2021) to max $205 (Somalia 2024); pooled $96 | OCHA HPC API (raw records) | [V-full]; ratios [derived] |
| Somalia 2023 FSL | $1.10bn / 6.68m targeted = $165/yr | Somalia 2022 $169; 2024 $205 | HPC API, plans 1063/1133/1180 | [V-full] |
| Ethiopia "Food" cluster | 2023: $2.16bn / 20.1m = $108/yr | 2019 $32; 2020 $25; 2022 $85; 2024 $149 | HPC API | [V-full] |
| Yemen FSAC | 2023: $2.2bn / 14.8m = $148/yr | 2019 $118; 2021 $107; 2024 $107 | HPC API | [V-full] |
| Afghanistan FSAC | 2022: $2.66bn / 21.6m = $123/yr | 2021 $22; 2023 $82; 2024 $90 | HPC API | [V-full] |
| South Sudan FSL | 2024: $588m / 3.97m = $148/yr | 2020 $114; 2021 $113 | HPC API | [V-full] |
| Sahel (Burkina, Mali, Chad, Niger), 2020–24 | ~$110–150/yr in 2022–24 | 2020 $37–86 | HPC API | [V-full] |
| **Data errors to exclude:** Nigeria 2024 (target 180,952 against a $340m cost, a typo); Sudan 2024 cost identical to the 2023 original ($581m) | — | — | HPC API | [V-full] |

### D. IPC definitions and ration delivery

| Parameter | Value | Source | Verif. |
|---|---|---|---|
| Household Phase 3 (Crisis) | Households "have food consumption gaps that are reflected by high or above-usual acute malnutrition", OR meet minimum food needs only by depleting livelihood assets or crisis coping | FEWS NET IPC page (IPC 3.1); ACAPS Yemen IPC page | [V-full] |
| Household Phase 4 (Emergency) | "large food consumption gaps which are reflected in very high acute malnutrition and excess mortality", OR gaps mitigated only by emergency strategies and asset liquidation | Same | [V-full] |
| Area classification rule | Area is in a phase when ≥20% of its population is in that phase or worse | FEWS NET IPC page | [V-full] |
| HFA "!" | Area "would likely be at least one phase worse" without current or programmed humanitarian food assistance | FEWS NET IPC page | [V-full] |
| HFA significance thresholds (bag icons) | ≥25% of households meet 25–50% of caloric needs from HFA (lower tier); ≥25% meet ≥50% (upper tier) | FEWS NET IPC page (IPC 3.1 mapping protocol) | [V-full] |
| HEA reference-table cut-offs (survival/livelihood-protection deficit by phase) | I believe Phase 4 ≈ survival deficit ≥20% and Phase 5 ≥50%, but **I could not open the IPC 3.1 manual** | IPC Technical Manual 3.1 | **[NV]**. Do not use until checked |
| Typical delivered ration, WFP E. Africa | 54% of 2,100 kcal (2021); 62% (2022) | WFP RBN 2023 | [V-full] |
| 50% ration cuts | Ethiopia, Kenya, Sudan and South Sudan "forced to introduce 50 percent ration cuts in 2022" | WFP RBN 2023, p. 9 | [V-full] |
| South Sudan ration (Oct 2025) | "All 2.7 million people receiving WFP food assistance get a 50-70 percent ration" | WFP story, 15 Oct 2025 | [V-full] |
| Yemen standard basket and cuts | Standard basket = 1,650 kcal/person/day for 30 days; households got ~45% of it before Sept 2022 and ~65% after; all 13m on reduced rations in 2023; GFA paused in the north in Dec 2023 | WFP Yemen updates and ACR 2023 (search extracts) | [V-abs] |
| Scenario arithmetic in WFP's own planning | At $0.83/day, $2bn buys a full ration for the planned caseload for 3 months, a 50–75% ration for up to 6 months, or a 25% ration for 12 months | WFP RBN 2023, p. 12 | [V-full] |

### E. Within-area targeting accuracy

| Parameter | Central | Range | Source | Verif. |
|---|---|---|---|---|
| Kenya HSNP (cash, arid north): **share food insecure**, beneficiaries vs non-beneficiaries | Community-based targeting 65% vs 47%; social pension 63% vs 63%; dependency ratio 71% vs 70% | — | Sabates-Wheeler, Hurrell & Devereux 2015 (WIDER WP 2014/040, table 7) | [V-full] |
| HSNP poverty targeting | inclusion error 11%; exclusion error 46%, driven by coverage (51%) below the 85% poverty rate. Random allocation would give 15% inclusion error | — | Same, sec. 6.6 | [V-full] |
| HSNP implementation errors (against the programme's own eligibility rules) | inclusion 4–30%, exclusion 17–23% | — | Same, table 4 | [V-full] |
| Niger (RCT of targeting methods, cash safety net) | inclusion errors 36–45% (PMT and food-consumption-score formulas, eligibility cut-off); CBT exclusion error ~42–55%; with 85% poor and 43% coverage, **minimum exclusion error = 49%** | Community-based targeting and the FCS formula are "rather flat along the consumption distribution". Methods differ little on food-insecurity benchmarks | Premand & Schnitzer 2018 (WPS 8412; later published in WBER), tables 7, 9, 11–14, sec. 4 | [V-full] |
| PMT in 9 African countries, targeting the poorest 20% | inclusion error 48%, **exclusion error 81%** | Inclusion 33–100%, exclusion 55–100% across countries. At 40% coverage: inclusion 31%, exclusion 36% | Brown, Ravallion & van de Walle 2016/2018, sec. 4 | [V-full] (NBER WP version) |
| Phone-data ML targeting, Togo (humanitarian cash) | exclusion errors 4–21% lower than geographic targeting; 9–35% higher than a hypothetical registry | — | Aiken et al. 2022 *Nature* | [V-abs] |
| Ethiopia food aid 1996 | strongest determinant of current receipt = past years of receipt; aid concentrated in Tigray "regardless of household food needs" | — | Clay, Molla & Habtewold 1999; Jayne et al. 2002 | [V-abs] (FEX summary; JDE abstract) |
| Ethiopia (180-village RCT on community targeting) | leaders minimise exclusion at the cost of inclusion; when budgets are cut they cut transfer size rather than numbers | — | Abay, Berhane, Gilligan, Tafere & Taffesse 2024 (IFPRI DP 2289) | [V-abs] |
| Somalia post-delivery diversion (IDP gatekeepers) | "widespread and systemic", found in all 55 IDP sites surveyed (UN 2023); gatekeepers take "up to 60%" in some cases | — | UN Somalia aid diversion review 2023; EUAA country report (search extracts) | [NV] |

---

## 2. Annotated notes

### 2.1 Which number to use as "cost per person-month of a full ration"

I suggest a **central value of $20–25 per person-month, all-in**, with a range of **$14–37**:

- **Best direct estimate: WFP RBN 2023.** It scales WFP's actual 2021–22 URT costs in nine East African countries to a 2,100 kcal ration. The result is $0.66/day in 2021 and $0.83/day in 2022, or $20 and $25 per person-month. These include all WFP cost layers. The country spread is wide: Somalia and Ethiopia came to about $14–15 per month, while South Sudan, with air drops, river and road logistics and hyperinflation, came to $28–37. One caveat on method: the "proportionality rule" scales total cost linearly with kcal, but fixed costs make this overstate the cost of a ration increase somewhat.
- **Cash cross-check: Somalia CWG.** The food transfer value is set at 80% of the costed 2,100 kcal food MEB, which implies a full food basket of about $17 per person per month (range $12.5–27) at July 2022 prices. Adding WFP's 2024 global CBT delivery and support overhead (all-in ÷ transfer = 1.33) gives about $23 per person-month. That agrees with the RBN in-kind figure.
- **What WFP actually spends.** URT runs about $0.40–0.55 per beneficiary-day, or $11–18 per person-month. This buys a ration of only about 55–65% of 2,100 kcal on average, so it is not a full ration. Dividing $16 by 0.6 gives about $26 per full-ration person-month, consistent with the RBN number [derived].
- **Modality.** Cash is cheaper to deliver: overhead is about 33% on top of the transfer, against about 150% for in-kind, where transport and handling are as large as the commodity value. But cash transfer values are pegged to local retail prices of the MEB, so per-person-month totals end up similar ($16 vs $15.5 per person-month in WFP URT 2024). The modality matters more for in-kind delivery in remote or inaccessible areas, for example South Sudan.
- **HRP cluster requirements** imply a median of only $107 per targeted person per year (about $9 per month if spread over 12 months). Read this as **people × months × ration-fraction**, not a full-ration price. Most HRPs plan reduced rations, seasonal (3–6 month) assistance and livelihood inputs. Do not use it as a full-ration unit cost. Its use is as an indicator of planned intensity: $107/yr ÷ $22/pm ≈ 5 full-ration person-months per targeted person per year [derived].

### 2.2 From "full ration" to "gap closed"

IPC phases are defined by gaps, not by a set kcal deficit. Phase 3 means "food consumption gaps" and Phase 4 means "large" gaps. The only quantitative kcal anchors in the IPC 3.1 mapping protocol are the HFA thresholds: households meeting 25–50%, or ≥50%, of caloric needs from assistance. A transparent parameterisation is:

cost per person-month of gap closed = (full-ration cost) × (gap share closed) ÷ (1 − leakage to non-needy)

- If a Phase 3 household's gap is 25–50% of needs and a Phase 4 household's is 50%+, closing the gap costs about $5–12 per person-month in Phase 3 and $11–25 in Phase 4, at $22 per full ration, *before* targeting losses [derived].
- In practice WFP delivers roughly a 50–65% ration. So a typical delivered "person-month" already closes about half a full ration's worth of gap, and per-beneficiary spending figures ($11–18/pm) correspond to that partial ration.

### 2.3 Targeting within areas

- The evidence on **within-area targeting of the food insecure** says it is weak. In the HSNP, the share of food-insecure households barely differs between beneficiaries and non-beneficiaries under categorical targeting (63% vs 63%; 71% vs 70%), and differs by about 18 points under community-based targeting (65% vs 47%). In Niger, community and FCS methods are almost flat across the consumption distribution. PMT does somewhat better on consumption but not on food-insecurity benchmarks.
- **Where coverage is below need, exclusion is dominated by the budget**: Niger has a mechanical minimum of 49%, and HSNP has 46% exclusion against 11% inclusion. When most people in an area are needy (as in IPC 3+ areas), inclusion errors are low *by construction*: a random draw gives 15% in HSNP.
- **Suggested bounds for the BOTEC:**
  - Share of aid reaching the truly needy within a targeted area: about the area's IPC 3+ prevalence plus 0–20 percentage points.
  - Inclusion error ("leakage"): about 30–50% when the needy share is 20–40%, and 10–20% when the needy share is above 70%.
  - Exclusion of the needy in a covered area: about 40–80%, set mostly by coverage.
  - Add post-delivery diversion as a separate haircut. For Somalia IDP settings it is documented as systemic, but there is no reliable point estimate. Use 0–30% as a sensitivity range, not a parameter [derived judgement].
- Brown et al. note that PMT and similar methods are "particularly deficient in reaching the poorest". Exclusion error at a 20% target share averaged 81% across 9 African countries. This argues against assuming that targeting concentrates aid among Phase 4/5 households within a mixed-phase area.

### 2.4 Things that look like data but are not

- WFP's "annual expenditure per beneficiary" ($50–51, 2023–24) is all-in total spending divided by beneficiaries. It includes school feeding, nutrition and service delivery. Do not convert it to a monthly figure.
- The "$0.43 per person per day" in WFP's 2025 "42 million" plan is a one-meal-a-day average across 43 countries, not a full ration (search extract, [NV]).
- Sudan 2023/2024 HRP FSL cost per targeted person ($39–51) is anomalously low. The 2024 cost is a carry-over of the pre-war 2023 figure. Exclude it.

---

## 3. BibTeX

```bibtex
@techreport{wfp2023costinaction,
  author      = {{World Food Programme}},
  title       = {Impacts of the Cost of Inaction on {WFP} Food Assistance in {Eastern Africa} (2021 \& 2022)},
  institution = {WFP Regional Bureau Nairobi (RAM) and Corporate Planning and Performance Division},
  year        = {2023},
  month       = apr,
  url         = {https://docs.wfp.org/api/documents/WFP-0000148305/download}
}
@techreport{wfp2025apr2024annexIID,
  author      = {{World Food Programme}},
  title       = {Annual Performance Report for 2024, Annex {II-D}: Expenditure per Beneficiary Analysis},
  institution = {WFP Executive Board},
  year        = {2025},
  url         = {https://executiveboard.wfp.org/document_download/WFP-0000166389}
}
@techreport{wfp2026apr2025annexIID,
  author      = {{World Food Programme}},
  title       = {Annual Performance Report for 2025, Annex {II-D}: Expenditure per Beneficiary Analysis},
  institution = {WFP Executive Board},
  year        = {2026},
  url         = {https://executiveboard.wfp.org/document_download/WFP-0000173790}
}
@techreport{wfp2024apr2023annexIID,
  author      = {{World Food Programme}},
  title       = {Annual Performance Report for 2023, Annex {II-D}: Expenditure per Beneficiary Analysis},
  institution = {WFP Executive Board},
  year        = {2024},
  url         = {https://executiveboard.wfp.org/document_download/WFP-0000158933}
}
@techreport{wfp2023apr2022annexIIID,
  author      = {{World Food Programme}},
  title       = {Annual Performance Report for 2022, Annex {III-D}: Expenditure per Beneficiary Analysis},
  institution = {WFP Executive Board},
  year        = {2023},
  url         = {https://executiveboard.wfp.org/document_download/WFP-0000149272}
}
@techreport{wfp2022apr2021annexIIIE,
  author      = {{World Food Programme}},
  title       = {Annual Performance Report for 2021, Annex {III-E}: Cost per Beneficiary Analysis},
  institution = {WFP Executive Board},
  year        = {2022},
  url         = {https://executiveboard.wfp.org/document_download/WFP-0000139261}
}
@techreport{somaliacwg2022tv,
  author      = {{Somalia Cash Working Group} and {Food Security Cluster}},
  title       = {Recommended Multipurpose Cash Assistance ({MPCA}) and Food Transfer Values for Cash and Voucher Assistance for the Drought and Famine Prevention Response},
  type        = {Joint Technical Note},
  institution = {Somalia CWG/FSC},
  year        = {2022},
  month       = sep,
  url         = {https://fscluster.org/sites/default/files/2024-04/Drought%20Response%20CVA%20Transfer%20Value%20recommendations_September%202022_1.pdf}
}
@techreport{somaliacwg2024gap,
  author      = {{MEB Review and Gap Analysis Task Force (SNBS, CWG, FSC, FSNAU, REACH, FAO, WFP)}},
  title       = {Identifying Gaps in Households' Economic Capacity to Meet Essential Needs and the New Cash and Voucher Assistance Transfer Value Recommendations},
  institution = {Somalia Cash Working Group},
  year        = {2024},
  month       = sep,
  url         = {https://fscluster.org/sites/default/files/documents/Guidance%20Notes%20-%202025%20MPCA%20Transfer%20Value%20-Final%20(1).pdf}
}
@misc{ocha_hpc_api,
  author       = {{UN OCHA}},
  title        = {Humanitarian Programme Cycle public {API}: plan entities, cluster requirements and caseloads},
  howpublished = {\url{https://api.hpc.tools/v2/public/plan/}},
  note         = {Accessed 14 Oct 2026},
  year         = {2026}
}
@misc{fewsnet_ipc,
  author       = {{FEWS NET}},
  title        = {Integrated Phase Classification},
  howpublished = {\url{https://fews.net/about/integrated-phase-classification}},
  note         = {Accessed 14 Oct 2026},
  year         = {2026}
}
@techreport{ipc2021manual,
  author      = {{IPC Global Partners}},
  title       = {Integrated Food Security Phase Classification Technical Manual Version 3.1},
  institution = {IPC Global Partners},
  address     = {Rome},
  year        = {2021}
}
@article{sabateswheeler2015targeting,
  author  = {Sabates-Wheeler, Rachel and Hurrell, Alex and Devereux, Stephen},
  title   = {Targeting Social Transfer Programmes: Comparing Design and Implementation Errors Across Alternative Mechanisms},
  journal = {Journal of International Development},
  volume  = {27},
  number  = {8},
  pages   = {1521--1545},
  year    = {2015},
  doi     = {10.1002/jid.3186}
}
@article{premand2021targeting,
  author  = {Premand, Patrick and Schnitzer, Pascale},
  title   = {Efficiency, Legitimacy, and Impacts of Targeting Methods: Evidence from an Experiment in {Niger}},
  journal = {World Bank Economic Review},
  year    = {2021},
  note    = {Volume/pages not verified. Working paper version read: World Bank Policy Research WP 8412 (2018)}
}
@article{brown2018poor,
  author  = {Brown, Caitlin and Ravallion, Martin and van de Walle, Dominique},
  title   = {A Poor Means Test? {E}conometric Targeting in {Africa}},
  journal = {Journal of Development Economics},
  volume  = {134},
  pages   = {109--124},
  year    = {2018},
  doi     = {10.1016/j.jdeveco.2018.05.004}
}
@article{aiken2022phone,
  author  = {Aiken, Emily and Bellue, Suzanne and Karlan, Dean and Udry, Chris and Blumenstock, Joshua E.},
  title   = {Machine Learning and Phone Data Can Improve Targeting of Humanitarian Aid},
  journal = {Nature},
  volume  = {603},
  number  = {7903},
  pages   = {864--870},
  year    = {2022},
  doi     = {10.1038/s41586-022-04484-9}
}
@article{margolies2015costing,
  author  = {Margolies, Amy and Hoddinott, John},
  title   = {Costing Alternative Transfer Modalities},
  journal = {Journal of Development Effectiveness},
  volume  = {7},
  number  = {1},
  pages   = {1--16},
  year    = {2015},
  doi     = {10.1080/19439342.2014.984745}
}
@article{jayne2002targeting,
  author  = {Jayne, T. S. and Strauss, John and Yamano, Takashi and Molla, Daniel},
  title   = {Targeting of Food Aid in Rural {Ethiopia}: Chronic Need or Inertia?},
  journal = {Journal of Development Economics},
  volume  = {68},
  number  = {2},
  pages   = {247--288},
  year    = {2002}
}
@article{clay1999foodaid,
  author  = {Clay, Daniel C. and Molla, Daniel and Habtewold, Debebe},
  title   = {Food Aid Targeting in {Ethiopia}: A Study of Who Needs It and Who Gets It},
  journal = {Food Policy},
  volume  = {24},
  number  = {4},
  pages   = {391--409},
  year    = {1999}
}
@techreport{abay2024cbt,
  author      = {Abay, Kibrom A. and Berhane, Guush and Gilligan, Daniel O. and Tafere, Kibrom and Taffesse, Alemayehu Seyoum},
  title       = {Targeting Social Assistance in Fragile Settings: An Experiment on Community-Based Targeting},
  type        = {IFPRI Discussion Paper},
  number      = {2289},
  institution = {International Food Policy Research Institute},
  year        = {2024}
}
```

### Gaps and things not verified
- IPC 3.1 manual (HEA deficit thresholds by phase) could not be downloaded: ipcinfo.org and fsinplatform.org returned 403. The phase descriptions come from FEWS NET's page.
- No WFP country-level full-ration cost for Yemen, Afghanistan, Nigeria or the Sahel. Country Annual Country Reports (ACRs) report cost per beneficiary but were not opened.
- The HRP per-person figures use original plan `cost` attachments, not mid-year revisions, and include livelihoods components.
- Somalia diversion shares (up to 60%) and the Yemen ration percentages come from search extracts only.
- Targeting studies are mostly from cash safety nets (Kenya HSNP, Niger), not emergency general food distributions. There is no emergency study that measures inclusion and exclusion errors against IPC household phase.
