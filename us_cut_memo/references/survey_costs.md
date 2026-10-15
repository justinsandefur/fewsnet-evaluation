# Survey costs vs. SAM treatment: parameters for a cost-effectiveness back-of-the-envelope

Compiled 8 Oct 2026 with web searches and direct reads of the sources. Verification tags follow the project convention:

- **[V-full]**: I read the number in the full text (PDF, HTML or Europe PMC full-text XML) in this session.
- **[V-abs]**: I read the number only in an abstract, publisher metadata, or a search-engine extract.
- **[NV]**: Not verified. The figure came from a search summary or secondary report, and I could not open the original.
- **[derived]**: My own arithmetic on verified inputs. It is not stated in any source.

PMC HTML pages returned a CAPTCHA, so PMC papers were read through the Europe PMC full-text API.

---

## 1. Parameter table

### A. Cost of nutrition and mortality surveys

| Parameter | Central | Range | Source | Verif. |
|---|---|---|---|---|
| SMART survey cost per stratum, **national** surveys, sub-Saharan Africa (2013–15) | $21,100 | — | Daher et al. 2018 (FEX 58), summarising UNICEF/AAH 2016 | [V-full] |
| SMART survey cost per stratum, **small-scale** surveys, SSA (2013–15) | $15,050 | — | Daher et al. 2018 | [V-full] |
| Cost per stratum, by country (national surveys) | — | Tanzania 2014 ~$15,000; Malawi ~$21,000; Burkina Faso ~$21,000; Mali 2015 ~$26,000 (~$19,600 net of partner contributions); Cameroon ~$19,000 + $30–40k consultant | UNICEF & ACF 2016 SMART analytical report | [V-full] |
| Cost per small-scale or regional SMART survey | ~$10,000 (Kenya, DRC) | ~$19,000 (Cameroon, excl. consultant) to $30,000 (South Sudan) | UNICEF & ACF 2016 | [V-full] |
| UNICEF/ACF "sustainable" target cost per stratum | ≤$10,000–15,000 | — | UNICEF & ACF 2016 | [V-full] |
| Whole national SMART survey (28–30 strata), Burkina Faso | ~$640,000 | Mali rounds 2011–15: $67k–$708k depending on coverage | UNICEF & ACF 2016 (Burkina case study, quoted in search extract; Mali table read in full) | [V-full] Mali; [V-abs] Burkina |
| Kenya county SMART surveys, 2018–19 (total cost per survey) | ~KSh 4.4m (≈$43k) | KSh 2.59m (West Pokot) to 7.89m (Turkana) (≈$25k–77k); government share 6–55% | Ndung'u et al. 2021 (FEX 65), Table 1 | [V-full] KSh; [derived] USD at ~KSh 101–103/$ |
| Insecurity raises survey cost | qualitative | Gao and Kidal (Mali) singled out | Daher et al. 2018 | [V-full] |
| FSNAU Somalia: total project budget, Phase VII (2013–16/17) | $26.1m target, $21m secured (≈$5–6m/yr for *all* FSNAU outputs, not only nutrition) | — | FAO OED 2017 final evaluation | [V-full] |
| FSNAU nutrition surveys per year | ~90 (2022: 78 integrated FS/nutrition/mortality SMART + 12 MUAC assessments) | One seasonal round = 29 SMART + 6 MUAC (Post-Gu 2022) | FAO project highlights (via search); FSNAU Nutrition Update Oct 2022 | [NV] for 90 (ReliefWeb 403); [V-full] for 29 + 6 |
| FSNAU per-survey cost | not published | rough upper bound [derived]: under $60k per survey if half the ~$5–6m annual budget went to ~90 surveys. Indicative only | — | [derived] |
| FAO evaluation recommends moving to *annual* rather than biannual nutrition surveys "using mobile devices" to save money | — | — | FAO OED 2017 | [V-full] |
| WFP mVAM remote survey cost per surveyed person | $3–9 | face-to-face $20–40 | WFP 2016 mVAM brief | [V-full] |
| mVAM cost by mode | SMS $5–6; live call/IVR $7–9 per questionnaire | — | Foley 2017 (HIF/Elrha case study) | [V-abs] |
| Phone mortality survey (Malawi RaMMPS): IVR screening cost per completed CATI mortality interview | $17.4 | $8.75 per IVR-identified rural respondent; IVR survey total $21,007 | Gupta/Helleringer et al. 2025 (TMIH, PMC12401643) | [V-full]. Note: screening cost only, CATI interview cost not included |
| Retrospective mortality survey (6-month recall), staff-time cost only, 2008 | $4,400–15,800 per site | 30-day-recall survey $17,000–81,000; "informant method" 33% cheaper than the 6-month survey | Roberts et al. 2011 (PLoS ONE), Table 4 | [V-full] |
| Predictive or small-area models as a substitute for anthropometric surveys | "disappointing performance… not usable for action" | Somalia (85 surveys), South Sudan (175) | Checchi et al. 2022 (BMC Nutrition) | [V-abs] |
| Donor ODA for nutrition data and information systems | $47–89m per year (2017–19), flat | Benchmark recommendation: 4–6% of nutrition spending (~$427–640m/yr) | Farina et al. 2022 (BMJ Glob Health, PMC8905917) | [V-full] |

### B. SAM and MAM treatment: cost, coverage, mortality

| Parameter | Central | Range | Source | Verif. |
|---|---|---|---|---|
| Cost per SAM child treated, Somalia (cost per child *recovered*, initial episode, 2022 USD) | $92 | Mali $191; South Sudan $178 | Puett et al. 2025 (Curr Dev Nutr) | [V-full] |
| Cost per SAM child treated, Ethiopia 2024 (provider) | $171 (Girawa, Oromia) | $325 (Adadle, Somali Region); +$54 caregiver cost → $225–379 economic | Gizaw et al. 2026 (BMC HSR) | [V-full] |
| Cost per child treated, Nigeria (Taimaka, GiveWell model) | $105 | Taimaka's own figures $87–94 | GiveWell Taimaka grant page, Nov 2024 | [V-full] (GiveWell); [NV] for Taimaka's own figures |
| Cost per malnourished child reached, Niger (ALIMA, GiveWell) | $67 | $39 excluding government facility costs and RUTF | GiveWell CMAM intervention report (Mar 2024) | [V-full] |
| Cost per child treated, Niger (Diffa, 2023) | $110 (simplified protocol) | $187 (standard protocol) | Cichon et al. 2023 (Nutrients) | [V-abs] |
| Cost per child admitted, Niger (Mayahi, CHW vs. standard) | $83 | $84 standard; $107–117 per child recovered | Molanes-López et al. 2024 | [V-abs] |
| Cost per child treated, Mali (Gao, conflict setting, RCT) | $179 (CHW + facility) | $210 (simplified) to $272 (facility only) | Cichon et al. 2025 (BMC PH) | [V-abs] |
| Cost per child treated, Mali (Kita, CHW vs. OTP) | $244 | $188–442 | Rogers et al. 2018 (HRH) | [V-abs] |
| Older review range, ambulatory SAM treatment | — | $46–453; large African programmes $129–201 | Expert Rev Pharmacoecon (2010), via search extract | [NV] |
| RUTF carton price (150 × 92 g sachets ≈ one SAM treatment course), UNICEF offshore contracts 2024–26 | ~$40–45 | ~$37–55 (country-office contracts up to ~$59); excludes freight | UNICEF Supply Division RUTF price data (updated 14 Aug 2026) | [V-full] |
| RUTF share of SAM treatment cost | 24–43% | 57.7% (therapeutic foods, Girawa 2024) | Lenters et al. (DCP3 ch. 11); Gizaw et al. 2026 | [V-full] |
| MAM treatment cost per enrollee (Sierra Leone RCT) | $105–112 | $163–179 per recovered child | Griswold et al. 2021 (AJCN) | [V-abs] |
| MAM treatment cost, NE Nigeria (CRS) | $50–66 | — | CRS 2024 cost-efficiency brief | [NV] |
| SAM treatment coverage (CMAM programmes, 2012–13) | 38.3% mean | rural 34.6%, urban 40.9%, camps 74.2%; 33/44 below Sphere | Rogers et al. 2015 (PLoS ONE) | [V-full] |
| Global SAM treatment coverage | ~25% (2016) | MAM 16% (WFP, 2017) | Daures et al. 2020, cited in GiveWell CMAM report | [V-full] secondary |
| Baseline coverage in Gombe, Nigeria | 1% | — | GiveWell Taimaka | [V-full] |
| Mortality HR, severe wasting (WHZ < −3 vs ≥ −1) | 11.63 | 9.84–13.76 | Olofin et al. 2013 | [V-abs] |
| One-year mortality ratio, WHZ −3.5 vs −0.5 (corrects for "aging" of measurements) | 5.61 (MIG) | 3.75 (probit); MUAC 11 vs 14 cm: 4.56 | Roodman 2022, via GiveWell CMAM report | [V-full] secondary |
| Untreated one-year mortality, SAM (GiveWell Niger) | ~10% | MAM ~4% | GiveWell CMAM report | [V-full] |
| Untreated one-year mortality, malnourished 6–59m, Gombe | 4.3% | 3–8% | GiveWell Taimaka | [V-full] |
| Historical untreated SAM CFR (WHO 2007) | 10–20% | recent cohorts < 6% | Search extract (Scorecard/EME review) | [NV] |
| SAM case fatality, Niakhar/Bwamanda cohorts | 6–12% | — | Garenne et al. 2009 | [V-abs] |
| Mortality reduction from treatment vs. none | SAM ~70%, MAM ~40% (Roodman); GiveWell all-cause 45% (Niger), 59% (Gombe) | 15–70% | GiveWell CMAM and Taimaka pages | [V-full] |
| CMAM CFR among treated (community care, oedema) | < 4% | — | Lenters et al. (DCP3) | [V-full] |
| Deaths averted per child treated (GiveWell models) | ~0.026 (Gombe: 1,128 deaths / 43,309 additional children) | ~0.010 (Niger ALIMA: 2,047 / 202,106 reached) | GiveWell | [derived] |
| Cost per death averted, Gombe (Taimaka) | ~$4,000–4,250 | — | GiveWell inputs | [derived] |
| Cost per death averted, Niger (ALIMA) | ~$6,650 | — | GiveWell inputs ($13.6m / 2,047) | [derived] |
| GiveWell cost-effectiveness | 8.8× cash (Taimaka); 11× (ALIMA) | ~13× with option value | GiveWell | [V-full] |
| Cost per life saved / per DALY, CMAM (Zambia) | $1,760 / $53 | $203 per child | Bachmann 2009, via DCP3 | [V-full] secondary |
| Cost per DALY, CMAM (Malawi) | $42 | — | Wilford et al. 2012, via DCP3 | [V-full] secondary |
| Cost per DALY / per life saved, CHW CMAM (Bangladesh) | $26 / $869 | inpatient $1,344 / $45,688 | Puett et al. 2013 (HPP) | [V-abs] + DCP3 [V-full] |
| Cost per DALY, Gao (Mali) | $53–60 (CHW models) | $173 facility-only | Cichon et al. 2025 | [V-abs] |
| MAM treatment ICER, Mali (RUSF vs none) | $9,821 per death averted; $347 per DALY (2015 USD) | — | search extract | [NV] |

### C. Incidence correction factors (prevalence → annual caseload)

| Parameter | Central | Range | Source | Verif. |
|---|---|---|---|---|
| Globally recommended ICF (K) for SAM, 12 months | 1.6 (so caseload = N × P × (1 + K) = 2.6 × prevalent cases) | — | Isanaka et al. 2021 (equations 4–6); derived from 7.5-month episode length | [V-full] |
| Mean untreated duration of a severe wasting episode | 7.5 months | — | Garenne et al. 2009 | [V-abs] |
| ICF, UNICEF-led meta-analysis of 352 sites in 20 countries | 3.6 | 95% CI 3.4–3.9; country range 1.3 (Nigeria) – 30.1 (Burundi) | Isanaka et al. 2021 (BMJ GH) | [V-full] |
| ICF, Mali/Niger/Burkina 2009–12 | 4.82 | 3.15–7.38 | Isanaka et al. 2016 (AJE) | [V-abs] |
| K from PROMIS cohorts | SAM 9.4 (BF), 5.7 (Mali); MAM 4.7 (BF), 5.1 (Mali) | prevalence understates annual SAM burden 7–10× | Barba, Huybregts & Leroy 2020 (AJE) | [V-abs] + FEX [V-full] |
| Niger: observed conversion factors vs. recommended | 2–5× higher | — | Deconinck et al. 2016 | [V-abs] |
| Nigeria: standard K underestimated caseload by | 79.5% | locally estimated K: ~10% error | Bulti et al. 2017 | [V-abs] |
| FSNAU Somalia, 2026 burden estimate | ICF 3.6 (SAM), 2.6 (MAM); SAM burden 492,900, GAM 1,877,900 children in 2026 | 2021 estimate used ICF 1.6 ("prevalence × 2.6") | FSNAU burden tables, 18 May 2026 and 4 Feb 2021 | [V-full] |
| Afghanistan HNO 2020 | prevalence × U5 population × 2.6 | — | Bongassie et al. 2021 (FEX 65) | [V-full] |

---

## 2. Annotated notes

### 2.1 Survey costs

**Best benchmark.** The UNICEF and Action Against Hunger (2016) SMART analytical report covers 11 sub-Saharan countries, and Daher et al. (2018) in *Field Exchange* summarise it. Average costs were **~$21k per stratum for national surveys and ~$15k for small-scale (single-area) surveys** in 2013–15. A "stratum" is one area with its own prevalence estimate, usually a district, livelihood zone or region, with roughly 400–700 children measured. That is the right unit for this back-of-the-envelope: one estimate of GAM, SAM and mortality for one area. Costs scale almost linearly with strata. Fixed costs (consultant, training, equipment) add $30–40k per round where an outside SMART consultant is hired (Cameroon). Insecure areas cost more (South Sudan ~$30k per small-scale survey, against ~$10k in Kenya and DRC). These are 2015 dollars. Inflation since then (~35–40% US CPI) would put a current small-area survey at very roughly **$15–40k** [derived; no 2024–26 costing found].

**Kenya, 2018–19.** County SMART surveys cost KSh 2.6–7.9m (~$25–77k), with Turkana the most expensive. Some counties have several strata, which partly explains the higher per-survey cost compared with the UNICEF per-stratum figure. Counties paid 6–55% of the cost. The same article says the Kenyan government allocated **$7.54m to the nutrition response in 2017 on the basis of the August 2016 analysis**. This is a concrete case of survey results leading to an allocation.

**FSNAU Somalia.** This is the densest surveillance system: two seasonal rounds a year, each with ~29–40 SMART surveys covering IDPs, urban and rural livelihood zones, plus MUAC-only assessments where access is limited. The 2017 FAO evaluation gives the whole-unit budget, **$26.1m for 2013–16 ($21m secured)**. That money also pays for food security, markets, IPC, the dashboard and training, so a nutrition-only share is not published. The evaluation flagged funding gaps and suggested *annual* rather than biannual nutrition surveys as a cost-saving measure. The cost of surveillance therefore binds even in the best-funded system. No FSNAU per-survey cost was found.

**Nigeria NFSS (Borno, Adamawa, Yobe).** NBS and UNICEF run it biannually. Round 15 was fielded in 2025, and the October 2025 report is on ReliefWeb. No published cost per round was found [gap]. **Kenya NDMA sentinel sites**: no cost figure found [gap].

**Remote and phone alternatives.** WFP's own mVAM brief puts remote surveys at **$3–9 per respondent, against $20–40 face-to-face**, with 1–2 weeks' turnaround instead of 6 weeks. These are 2016 figures for food-consumption modules. They cannot measure anthropometry, so they are not a substitute for GAM or SAM. For mortality, RaMMPS Malawi reports IVR screening at $17.4 per completed CATI mortality interview, excluding the interview itself. Roberts et al. (2011) costed staff time for 6-month-recall retrospective mortality surveys at $4.4–15.8k per site in 2008 (excluding transport and equipment). A 30-day-recall survey needs much larger samples and costs $17–81k.

**Modelling as a substitute.** Checchi et al. (2022) tried to predict district-level acute malnutrition in Somalia and South Sudan from conflict, displacement, prices, rainfall, measles and similar data. Performance was "disappointing", and they judged the models "not usable for action". This supports treating surveys as the binding information source for nutrition. Small-area *mortality* estimation (Checchi et al. 2022, *Pop Health Metrics*) works better, but it still needs surveys to train it.

### 2.2 SAM and MAM treatment

**Cost per child.** Recent crisis-setting estimates cluster at **$90–200 per SAM child treated** (Somalia $92 per recovered child, South Sudan $178, Mali $191 [Puett 2025, 2022 USD]; Ethiopia $171–325; Niger $83–187; Gao, Mali $179–272). Low-cost NGO models are $67–105 (GiveWell: ALIMA in Niger, Taimaka in Nigeria). RUTF alone is ~$40–45 per course at UNICEF offshore prices, before freight. MAM treatment costs about $50–110 per child.

**Coverage.** Only about a third of SAM cases are treated in typical programmes (38% mean across 44 SQUEAC assessments in 2012–13; ~25% globally in 2016; 1% in Gombe before Taimaka). In a value-of-information model this matters in two ways. First, survey-driven scale-up has room to reach untreated children. Second, coverage is itself measured only by surveys (SQUEAC/SLEAC).

**Mortality.** Olofin et al. (2013) report a hazard ratio of 11.6 for WHZ < −3. GiveWell now relies on Roodman's (2022) one-year risk ratios (~5–7× for SAM, ~2.5× for MAM). These yield **untreated one-year mortality of ~10% for SAM and ~4% for MAM in Niger**, and a pooled 4.3% for the malnourished in Gombe. Treatment is assumed to cut mortality by ~70% for SAM and ~40% for MAM (GiveWell applies 45–59% after discounts). There is no RCT of treatment against no treatment; these are model-based effects.

**Cost per death averted and per DALY.** From GiveWell inputs [derived]: **~$4,000 (Gombe) to ~$6,650 (Niger) per death averted**, or 0.01–0.026 deaths averted per child treated. Older CMAM studies: $869–1,760 per life saved and $26–53 per DALY (Bangladesh, Zambia, Malawi). Recent conflict-setting RCT (Gao): $53–173 per DALY.

### 2.3 Are allocations driven by surveys?

- **Mechanically, yes, for caseload and targets.** HNO and HRP nutrition caseloads are computed as N × prevalence × (1+K) × coverage target, with prevalence taken from SMART surveys (Afghanistan 2020 HNO, which also prioritised 26 of 34 provinces on GAM ≥ 10–15% plus aggravating factors; FSNAU burden tables; GiveWell's Taimaka model). The Nutrition Cluster's caseload tool uses the same structure.
- **CERF.** The handbook makes rapid-response eligibility for drought or food insecurity depend on current data, including malnutrition prevalence, being significantly worse than the 5-year trend [V-abs, search extract]. No study regressing CERF nutrition allocations on survey GAM was found [gap].
- **Donor practice is looser.** Olin et al. (2014) found that Sida's 2012 humanitarian health decisions did not systematically use needs-assessment data [V-full abstract]. Darcy et al. (2013, Tufts/ACAPS) is the standard reference on evidence use in humanitarian decisions [V-abs; metadata only, findings not read].
- **Kenya** (above) is an explicit case: the government allocated $7.54m in response to the survey-based analysis.
- **Value-of-information studies.** None found that quantify the return on nutrition surveys. ACF's advocacy paper *No data, no response* (Nov 2025) claims that without surveillance, malnutrition-linked child mortality "can increase by 25% to 50%". Its footnotes point only loosely to "FSNAU/FEWS NET" and "simulations by WFP and IPC", with no traceable study [V-full; treat as **unsourced**]. The same paper documents SMART surveys being suspended in West and Central Africa after BHA cuts, and the Sudan Nutrition Cluster receiving 59.7% of a $350.1m 2024 requirement [V-full].
- **ICF error = allocation error.** Bulti et al. (2017) note that using unadjusted or standard-K burden estimates has "a negative impact on allocation of resources". In Nigeria the standard K underestimated caseload by 79.5%. This feeds directly into the back-of-the-envelope, because surveys only improve the *prevalence* term, and errors in K can be as large as the survey sampling error.

### 2.4 Incidence correction factor: definitional trap

Two conventions are in use, and sources mix them:
- **K = 1.6** (Isanaka 2021 notation): incidence = prevalence × K, and annual burden = prevalence × (1 + K) = **2.6 × prevalence**. "1.6" and "2.6" describe the same assumption (12 months / 7.5-month duration = 1.6).
- **Empirical K** is much higher: 3.6 (352 sites), 4.8 (West Africa pooled), 5.7–9.4 (PROMIS cohorts). These empirical Ks are incidence/prevalence, so the burden multiplier would be 4.6–10.4 if prevalent cases are added back. FSNAU's 2026 table states "ICF 3.6 for SAM and 2.6 for MAM". From the table alone I could not tell whether FSNAU multiplies prevalence by K or by (1+K).

---

## 3. BibTeX

```bibtex
@techreport{unicef_aah2016smart,
  author      = {{UNICEF} and {Action Against Hunger}},
  title       = {Implementation of Nutrition Surveys Using {SMART} Methodology in Sub-Saharan Africa: Analytical Report},
  institution = {UNICEF ESARO/WCARO and Action Against Hunger},
  year        = {2016},
  url         = {https://www.unicef.org/esa/media/2046/file/UNICEF-AAH-2016-SMART-Analytical-Report-Sub-Saharan-Africa.pdf}
}
@article{daher2018smart,
  author  = {Daher, Jana and Cassard, Fanny and Gari, Sara and Sauveplane-Stirling, Victoria and Nyawo, Mara and Codjia, Patrick},
  title   = {Implementation of nutrition surveys using {SMART} methodology in sub-Saharan Africa},
  journal = {Field Exchange},
  number  = {58},
  year    = {2018},
  url     = {https://www.ennonline.net/fex/58/smartmethodologyafrica}
}
@article{ndungu2021kenya,
  author  = {Ndung'u, Lydia and Maina-Gathigi, Lucy and Kinyua, Lucy and Ahmed, Hassan Ali and Chirchir, Kibet and Murage, Samuel Mahinda},
  title   = {Streamlining {SMART} survey processes in support of a high quality, nationally owned nutrition information system in {Kenya}},
  journal = {Field Exchange},
  number  = {65},
  year    = {2021},
  url     = {https://www.ennonline.net/fex/65/en/streamlining-smart-survey-processes-support-high-quality-nationally-owned-nutrition}
}
@techreport{fao2017fsnau,
  author      = {{FAO Office of Evaluation}},
  title       = {Final Evaluation of the Project: Food Security and Nutrition Analysis Unit for {Somalia}},
  institution = {Food and Agriculture Organization of the United Nations},
  series      = {Project Evaluation Series},
  year        = {2017},
  url         = {https://www.fao.org/3/bd688e/bd688e.pdf}
}
@techreport{fsnau2026burden,
  author      = {{FSNAU}},
  title       = {Somalia Updated Acute Malnutrition Burden Estimates by Region (January--December 2026)},
  institution = {Food Security and Nutrition Analysis Unit -- Somalia (FAO)},
  year        = {2026},
  month       = may,
  url         = {https://fsnau.org/downloads/Somalia_Updated_Acute_Malnutrition_Burden_Estimates_by_Region_18_May_2026.pdf}
}
@techreport{wfp2016mvam,
  author      = {{World Food Programme}},
  title       = {The mobile Vulnerability Analysis and Mapping ({mVAM}): Summary},
  institution = {WFP},
  year        = {2016},
  url         = {https://cdn.wfp.org/wfp.org/publications/MVAM%202016-02%20v3.pdf}
}
@article{roberts2011informant,
  author  = {Roberts, Bayard and Morgan, Oliver W. and Sultani, Mohammed Ghaus and Nyasulu, Peter and Rwebangila, Sunday and Sondorp, Egbert and Chandramohan, Daniel and Checchi, Francesco},
  title   = {Economic Feasibility of a New Method to Estimate Mortality in Crisis-Affected and Resource-Poor Settings},
  journal = {PLoS ONE},
  volume  = {6},
  number  = {9},
  pages   = {e25175},
  year    = {2011},
  doi     = {10.1371/journal.pone.0025175}
}
@article{checchi2022predict,
  author  = {Checchi, Francesco and Frison, Severine and Warsame, Abdihamid and Abebe, Kiross T. and Achen, Jasinta and Ategbo, Eric Alain and Ayoya, Mohamed Ag and Kassim, Ismail and Ndiaye, Biram and Nyawo, Mara},
  title   = {Can we predict the burden of acute malnutrition in crisis-affected countries? {Findings} from {Somalia} and {South Sudan}},
  journal = {BMC Nutrition},
  volume  = {8},
  year    = {2022},
  doi     = {10.1186/s40795-022-00563-2}
}
@article{farina2022odadata,
  author  = {Farina, Alexandra and Rana, Yashodhara and Flory, Augustin and Borces, Kyle and Snead, Caroline and Heidkamp, Rebecca},
  title   = {Landscape of official development assistance for nutrition data and information systems},
  journal = {BMJ Global Health},
  volume  = {7},
  number  = {3},
  year    = {2022},
  note    = {PMC8905917},
  doi     = {10.1136/bmjgh-2021-007370}
}
@article{puett2025relapse,
  author  = {Puett, Chloe and King, Sarah and Mama Chabi, Sherifath and Mohamud, Feysal Abdisalan and Lamwaka, Nancy and Stobaugh, Heather},
  title   = {The Economic Implications of Relapse Among Children Recovered from Severe Acute Malnutrition: Results from a Multicountry Prospective Study in {Mali}, {Somalia}, and {South Sudan}},
  journal = {Current Developments in Nutrition},
  volume  = {10},
  number  = {1},
  pages   = {107616},
  year    = {2025},
  doi     = {10.1016/j.cdnut.2025.107616}
}
@article{gizaw2026ethiopia,
  author  = {Gizaw, Getu and Siraj, Idris and Adimassie, Mhiret Teshome and Feyisa, Teshome Girma and Mekonnen, Muluneh Girma and Woldetsadik, Tesfatsion and Berhanu, Negalign},
  title   = {Economic cost analysis of severe acute malnutrition treatment in two districts of {Ethiopia}: a cross-sectional study},
  journal = {BMC Health Services Research},
  volume  = {26},
  pages   = {859},
  year    = {2026},
  doi     = {10.1186/s12913-026-14678-w}
}
@article{cichon2023diffa,
  author  = {Cichon, Bernardette and Lopez Ejeda, Noemi and Charle Cuellar, Pilar and others},
  title   = {Cost of Acute Malnutrition Treatment Using a Simplified or Standard Protocol in {Diffa}, {Niger}},
  journal = {Nutrients},
  volume  = {15},
  number  = {17},
  pages   = {3833},
  year    = {2023},
  doi     = {10.3390/nu15173833}
}
@article{cichon2025gao,
  author  = {Cichon, Bernardette and L{\'o}pez-Ejeda, Noemi and Samake, Salimata and others},
  title   = {Cost-effectiveness of decentralising acute malnutrition treatment with a standard or simplified treatment protocol: an economic evaluation in the region of {Gao}, {Mali}},
  journal = {BMC Public Health},
  year    = {2025},
  doi     = {10.1186/s12889-025-21411-5}
}
@article{rogers2018mali,
  author  = {Rogers, Eleanor and Mart{\'i}nez, Karen and Mor{\'a}n, Jos{\'e} Luis Alvarez and Al{\'e}, Franck G. B. and Charle, Pilar and Guerrero, Saul and Puett, Chloe},
  title   = {Cost-effectiveness of the treatment of uncomplicated severe acute malnutrition by community health workers compared to treatment provided at an outpatient facility in rural {Mali}},
  journal = {Human Resources for Health},
  volume  = {16},
  year    = {2018},
  doi     = {10.1186/s12960-018-0273-0}
}
@article{molanes2024mayahi,
  author  = {Molanes-L{\'o}pez, Elisa M. and Ferrer, Josep M. and others and Charle-Cu{\'e}llar, Pilar},
  title   = {Cost-effectiveness of severe acute malnutrition treatment delivered by community health workers in the district of {Mayahi}, {Niger}},
  journal = {Human Resources for Health},
  year    = {2024},
  doi     = {10.1186/s12960-024-00904-1}
}
@article{puett2013bangladesh,
  author  = {Puett, Chloe and Sadler, Kate and Alderman, Harold and Coates, Jennifer and Fiedler, John L. and Myatt, Mark},
  title   = {Cost-effectiveness of the community-based management of severe acute malnutrition by community health workers in southern {Bangladesh}},
  journal = {Health Policy and Planning},
  volume  = {28},
  number  = {4},
  pages   = {386--399},
  year    = {2013},
  doi     = {10.1093/heapol/czs070}
}
@article{griswold2021mam,
  author  = {Griswold, Stacy P. and Langlois, Breanne K. and Shen, Ye and others and Rogers, Beatrice L.},
  title   = {Effectiveness and cost-effectiveness of 4 supplementary foods for treating moderate acute malnutrition: results from a cluster-randomized intervention trial in {Sierra Leone}},
  journal = {American Journal of Clinical Nutrition},
  year    = {2021},
  doi     = {10.1093/ajcn/nqab140}
}
@incollection{lenters_dcp3,
  author    = {Lenters, Lindsey and Wazny, Kerri and Bhutta, Zulfiqar A.},
  title     = {Management of Severe and Moderate Acute Malnutrition in Children},
  booktitle = {Disease Control Priorities, Third Edition, Volume 2: Reproductive, Maternal, Newborn, and Child Health},
  publisher = {World Bank},
  year      = {2016},
  chapter   = {11},
  url       = {https://www.dcp-3.org/sites/default/files/chapters/DCP3%20Malnutrition%20Chapter%20102014_web.pdf}
}
@misc{unicef_rutf_prices,
  author = {{UNICEF Supply Division}},
  title  = {Ready-to-Use Therapeutic Food ({RUTF}) Price Data 2003--2026},
  year   = {2026},
  note   = {Last updated 14 August 2026},
  url    = {https://www.unicef.org/supply/documents/ready-use-therapeutic-food-rutf-price-data}
}
@article{rogers2015coverage,
  author  = {Rogers, Eleanor and Myatt, Mark and Woodhead, Sophie and Guerrero, Saul and Alvarez, Jose Luis},
  title   = {Coverage of Community-Based Management of Severe Acute Malnutrition Programmes in Twenty-One Countries, 2012--2013},
  journal = {PLoS ONE},
  volume  = {10},
  number  = {6},
  pages   = {e0128666},
  year    = {2015},
  doi     = {10.1371/journal.pone.0128666}
}
@article{olofin2013,
  author  = {Olofin, Ibironke and McDonald, Christine M. and Ezzati, Majid and Flaxman, Seth and Black, Robert E. and Fawzi, Wafaie W. and Caulfield, Laura E. and Danaei, Goodarz},
  title   = {Associations of suboptimal growth with all-cause and cause-specific mortality in children under five years: a pooled analysis of ten prospective studies},
  journal = {PLoS ONE},
  volume  = {8},
  number  = {5},
  pages   = {e64636},
  year    = {2013},
  doi     = {10.1371/journal.pone.0064636}
}
@misc{roodman2022anthro,
  author = {Roodman, David},
  title  = {The Association between Anthropometry and Mortality in Children},
  year   = {2022},
  note   = {GiveWell / Open Philanthropy working paper; SSRN 4294284},
  url    = {https://files.givewell.org/files/DWDA%202009/Interventions/Nutrition/Roodman_associationbetweenanthropometryandmortalityinchildren_2022.pdf}
}
@misc{givewell2024cmam,
  author = {{GiveWell}},
  title  = {Community-Based Management of Acute Malnutrition ({CMAM})},
  year   = {2024},
  month  = mar,
  url    = {https://www.givewell.org/international/technical/programs/community-based-management-acute-malnutrition}
}
@misc{givewell2024taimaka,
  author = {{GiveWell}},
  title  = {Taimaka -- Acute Malnutrition Treatment in {Gombe} State, {Nigeria} (November 2024) and Program Monitoring (March 2025)},
  year   = {2025},
  url    = {https://www.givewell.org/research/grants/taimaka-acute-malnutrition-treatment-in-gombe-state-nigeria-november-2024-and-program-monitoring-march-2025}
}
@article{garenne2009,
  author  = {Garenne, Michel and Willie, Douladel and Maire, Bernard and Fontaine, Olivier and Eeckels, Roger and Briend, Andr{\'e} and Van den Broeck, Jan},
  title   = {Incidence and duration of severe wasting in two {African} populations},
  journal = {Public Health Nutrition},
  volume  = {12},
  number  = {11},
  pages   = {1974--1982},
  year    = {2009},
  doi     = {10.1017/S1368980009004972}
}
@article{isanaka2016aje,
  author  = {Isanaka, Sheila and Boundy, Ellen O'Neal and Grais, Rebecca F. and Myatt, Mark and Briend, Andr{\'e}},
  title   = {Improving Estimates of Numbers of Children With Severe Acute Malnutrition Using Cohort and Survey Data},
  journal = {American Journal of Epidemiology},
  volume  = {184},
  number  = {12},
  pages   = {861--869},
  year    = {2016},
  doi     = {10.1093/aje/kww129}
}
@article{isanaka2021icf,
  author  = {Isanaka, Sheila and Andersen, Christopher T. and Cousens, Simon and Myatt, Mark and Briend, Andr{\'e} and Krasevec, Julia and Hayashi, Chika and Mayberry, Amy and Mwirigi, Louise and Guerrero, Saul},
  title   = {Improving estimates of the burden of severe wasting: analysis of secondary prevalence and incidence data from 352 sites},
  journal = {BMJ Global Health},
  volume  = {6},
  number  = {3},
  pages   = {e004342},
  year    = {2021},
  doi     = {10.1136/bmjgh-2020-004342}
}
@article{barba2020k,
  author  = {Barba, Fabrice M. and Huybregts, Lieven and Leroy, Jef L.},
  title   = {Incidence Correction Factors for Moderate and Severe Acute Child Malnutrition From 2 Longitudinal Cohorts in {Mali} and {Burkina Faso}},
  journal = {American Journal of Epidemiology},
  volume  = {189},
  number  = {12},
  pages   = {1623--1627},
  year    = {2020},
  doi     = {10.1093/aje/kwaa139}
}
@article{bulti2017nigeria,
  author  = {Bulti, Assaye and Briend, Andr{\'e} and Dale, Nancy M. and De Wagt, Arjan and Chiwile, Faraja and Chitekwe, Stanley and Isokpunwu, Chris and Myatt, Mark},
  title   = {Improving estimates of the burden of severe acute malnutrition and predictions of caseload for programs treating severe acute malnutrition: experiences from {Nigeria}},
  journal = {Archives of Public Health},
  volume  = {75},
  pages   = {66},
  year    = {2017},
  doi     = {10.1186/s13690-017-0234-4}
}
@article{deconinck2016niger,
  author  = {Deconinck, Hedwig and Pesonen, Anais and Hallarou, Mahaman and G{\'e}rard, Jean-Christophe and Briend, Andr{\'e} and Donnen, Philippe and Macq, Jean},
  title   = {Challenges of Estimating the Annual Caseload of Severe Acute Malnutrition: The Case of {Niger}},
  journal = {PLoS ONE},
  volume  = {11},
  number  = {9},
  pages   = {e0162534},
  year    = {2016},
  doi     = {10.1371/journal.pone.0162534}
}
@article{bongassie2021afg,
  author  = {Bongassie, Beka Teshome and Azimi, Said M. Yaqoob and Gallagher, Maureen L.},
  title   = {Calculating wasting caseloads and geographic prioritisation of nutrition services in the context of limited data in {Afghanistan}},
  journal = {Field Exchange},
  number  = {65},
  year    = {2021},
  url     = {https://www.ennonline.net/fex/65/en/calculating-wasting-caseloads-and-geographic-prioritisation-nutrition-services-context}
}
@article{olin2014sida,
  author  = {Olin, Emma and others},
  title   = {Funding Based on Needs? {A} Study on the Use of Needs Assessment Data by a Major Humanitarian Health Assistance Donor in its Decisions to Allocate Funds},
  journal = {PLoS Currents Disasters},
  year    = {2014},
  doi     = {10.1371/currents.dis.d05f908b179343c8b4705cf44c15dbe9}
}
@techreport{aah2025nodata,
  author      = {{Action Against Hunger}},
  title       = {No Data, No Response: Threatening the Lives of Millions of Children},
  institution = {Action Against Hunger},
  year        = {2025},
  month       = nov,
  url         = {https://actionagainsthunger.ca/app/uploads/2025/11/No-data-no-response_November_2025_VF.pdf}
}
@article{prudhon2007review,
  author  = {Prudhon, Claudine and Spiegel, Paul B.},
  title   = {A review of methodology and analysis of nutrition and mortality surveys conducted in humanitarian emergencies from {October} 1993 to {April} 2004},
  journal = {Emerging Themes in Epidemiology},
  volume  = {4},
  pages   = {10},
  year    = {2007},
  doi     = {10.1186/1742-7622-4-10}
}
```

### Gaps and things not verified
- No 2024–26 SMART costing, no published per-round cost for Nigeria NFSS, Kenya NDMA sentinel sites, or FSNAU per survey.
- No quantitative value-of-information study for nutrition surveys. The ACF "25–50% mortality" claim has no traceable source.
- Bachmann (2009, Zambia) and Wilford et al. (2012, Malawi) are cited only through DCP3. Primary papers not opened.
