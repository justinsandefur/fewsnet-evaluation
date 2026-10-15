# Literature review: measured mortality and acute malnutrition across IPC/CH/FEWS NET acute food insecurity phases

Compiled 2026-10-07 for the FEWS NET working paper's benefit-cost section. This file does not repeat lit_fewsnet_accuracy.md §E (no systematic validation of phases against outcomes) or lit_shocks_nutrition.md (shocks and wasting; Checchi & Robinson 2013 headline numbers; cash and wasting RCTs; Venkat et al. seasonality). It adds evidence on the **levels** of GAM, CDR and U5DR observed by phase, and on how to turn phases into deaths.

**How each entry was checked.**
- [V-full]: numbers read from the full text (PDF or HTML) in this session.
- [V-abs]: only an abstract, publisher metadata, a press release, or a search-engine extract of the text.
- [NV]: not verified.

ipcinfo.org, medRxiv, thelancet.com, sciencedirect.com and lshtm.ac.uk all blocked automated access. IPC Famine Review Committee (FRC) reports were therefore read from ReliefWeb, FSNAU or UCL Discovery copies.

---

## Summary

**1. No one has published a systematic table of survey outcomes by AFI phase.**
- Neither the IPC Global Support Unit, FEWS NET, FSNAU nor the academic literature publishes a cross-area table or regression of SMART/DHS GAM, CDR or U5DR on the AFI phase (current or projected).
- The IPC's own position, stated when it created the separate acute-malnutrition (AMN) scale in 2016, is that AFI levels and acute malnutrition "do not always match", in both directions. Current IPC guidance treats a one-phase AFI–AMN gap as "not unusual".
- FEWS NET's 2018 nutrition and mortality guidance tells analysts to read GAM *relative to the zone's usual seasonal level*. It also says to use GAM as AFI evidence only when food-consumption gaps explain it.
- So the system is not built to produce a cross-zone gradient in GAM levels by phase, and nobody has checked whether one exists.
- The Somalia result (r = 0.10 with the phase, 0.66 with the zone's lagged GAM) appears to be the first explicit quantification.

**2. The Somalia result is consistent with the literature; it is not an anomaly.**
- Household level: a meta-analysis finds that household food insecurity predicts stunting and underweight but **not wasting** (OR 1.04, 95% CI 0.96–1.12; Moradi et al. 2019).
- Chad, Darfur, South Sudan, Niger: community- and zone-level studies find wasting hotspots that do not coincide with food-insecurity hotspots (Young & Marshak 2017; Luc et al. 2023).
- Somalia forecasting:
  - The 6-month lag of district GAM is the dominant linear predictor, while the share in IPC 3+ enters only nonlinearly (Reusken et al. 2025).
  - Multi-sector covariate models of SMART GAM perform "disappointingly" (Checchi et al. 2022).
- Kenya: in NDMA sentinel data, predictive skill "depends heavily on autocorrelation" of the outcome (Constenla-Villoslada et al. 2025).
- Wasting peaks track temperature and disease seasons more than the hunger gap (Venkat et al. 2023).
- The counter-evidence is limited to famine-level extremes (Somalia 2011: GAM above 30% in most famine strata) and to large transfers at the margin.

**3. The IPC mortality bands are not empirically calibrated, and measured CDRs in Phase 4/5 areas usually sit one band lower.**
- Where the bands come from:
  - Toole & Waldman's (1990) "doubling" of a 1980s Sub-Saharan baseline of 0.44.
  - Hakewill & Moren's (1991) camp tiers, with the famine cut lowered from 5 to 2 on CDC advice.
  - Refugee-camp wasting–mortality regressions from the 1980s–90s (log CMR = −2.05 + 0.875·log wasting, R² = 0.59, n = 80).
  - Young & Jaspars (2009) document all of this. No calibration against AFI outcomes was ever done.
- Measured CDRs since 2017:
  - Every Famine or Risk-of-Famine review either measured non-trauma CDRs in the 0.3–1.9 range or had no mortality data at all.
  - Examples: Baidoa 2022, 1.1–1.84; Zamzam 2024, 1.9; Western Nuba 2024, 0.86–1.07; North Darfur 2024, 0.32–1.88 with GAM of 28–33%; Gaza June 2024, 0.55.
  - Only Somalia 2011 measured CDRs above 2 in every famine-declared stratum (2.1–6.1).
- Model-based estimates for Somalia:
  - In the 2022 crisis (5.6–6.7m in IPC 3+, two districts projected to reach Famine), the national CDR was **0.33→0.38**, and the worst regional mean (Bay) was **0.49**. That is below the IPC Phase 3 floor.
  - In 2017–18 regional CDR ranged from 0.33 to 0.60.
  - South-central Somalia's *no-crisis* baseline was already 0.5–0.8 in 2010–12.
  - North-eastern regions had much lower mortality than south-central regions despite "comparatively similar" IPC population shares (LSHTM 2025).

**4. The crisis-mortality models do not use IPC phase as a predictor, so IPC's predictive power for mortality is essentially untested.**
- The LSHTM small-area models cover Somalia 2010–12, 2014–18 and 2015–24, South Sudan 2013–18, northeast Nigeria 2016–19, and the malnutrition models for Somalia, South Sudan and Kenya.
- None includes IPC phase as a candidate predictor. I confirmed this in the repositories' parameter files.
- IPC enters only as a baseline definition (IPC 1–2 periods, Checchi & Robinson 2013) or as a visual cross-check. Warsame et al. (2023) report that regional excess death rates "correlated broadly" with the early-2017 IPC 3–4 share.
- The predictors that do survive are conflict, measles and other epidemics, SAM admissions, terms of trade (2010–12 only), water prices and livelihood.

**5. What could defensibly replace the IPC bands in a cost-per-death calculation.**
- I divided documented excess-death tolls by the IPC 3+ population (rough; see the table in §5). The implied excess CDR per person in Phase 3+:
  - **Somalia non-famine droughts** (2017–18; 2022): **≈0.15–0.21 per 10,000/day**. That is ≈5.5–7.7 excess deaths per 1,000 Phase-3+ person-years, or 0.5–1.4% of the Phase 3+ population over the whole crisis.
  - **Somalia 2010–12 famine**: **≈1.1–1.9 per 10,000/day** (≈40–68 per 1,000 per year).
  - **Northeast Nigeria 2016–19** (conflict-driven): **≈0.9**.
- Naive IPC-band arithmetic, e.g. Oxfam's (0.5–0.99 − 0.22) × Phase 3+ population, would have predicted ≈68,000–188,000 excess deaths in Somalia in 2022. LSHTM's model estimate is 36,200–43,000.
- **Recommendation:**
  - Central case: excess CDR ≈ **0.2 per 10,000/day** for the Phase 3+ population (Phases 3 and 4 pooled) in non-famine crises, sensitivity range 0.1–0.5.
  - Use the IPC Phase 4/5 bands (≈1–2+) only for famine-type episodes with access denial, displacement and epidemics (Somalia 2011).
  - Treat the gain from a phase transition as a modest *increment over the zone's own baseline*, not as a jump to the next IPC band.
- **For child malnutrition:**
  - Do not map phases to GAM levels.
  - Model GAM as zone baseline plus a small phase effect. The Somalia data suggest about 0–2 percentage points from Stressed to Emergency+.
  - If GAM must be converted to deaths, Mason et al. (2012), from 1,175 Horn of Africa surveys, give U5DR rising ≈1.2–1.4 per 10,000/day per 10 percentage points of GAM, with a relationship that has shifted downward since 2005.

---
## 1. Outcomes tabulated against the AFI phase: IPC's and FEWS NET's own technical work

**1.1 IPC Nutrition Working Group / Global Support Unit (2016). *IPC for Acute Malnutrition: Concepts, Tools, and Procedures to be used to Classify Areas based on Acute Malnutrition.* Cleared by the IPC Technical Advisory Group and endorsed by the IPC Steering Committee, Rome, 24 June 2016.** https://www.nutritioncluster.net/sites/nutritioncluster.com/files/2020-03/IPC-for-Acute-Malnutriton-Concepts-and-Tools-Cleared-by-TAG-and-Endorsed-by-SC.pdf [V-full]
- The founding rationale for a separate AMN scale. The Background section (p. 1) states that "one of the lessons learned" from IPC implementation is that AFI levels and acute malnutrition prevalence "do not always match". Some settings have high food insecurity and low acute malnutrition, and others the reverse. The reason given is that acute malnutrition "is influenced by many different factors other than food security", some of them protective.
- The AMN scale grew out of the FSNAU Somalia nutrition classification tool.
- No statistics are given. The "mismatch" is presented as an analysts' observation, not as a tabulation.

**1.2 IPC guidance on AFI–AMN linkages, and Michelson, Lentz, Armstrong & Korpi (2026). "The integrated food security phase classification system: seven defining characteristics." *Food Policy* 142: 103134.** https://doi.org/10.1016/j.foodpol.2026.103134. IPC note: "Exploring linkages between Acute Food Insecurity and Acute Malnutrition", https://www.ipcinfo.org/ipcinfo-website/resources/resources-details/en/c/1156938/ [V-abs: search-engine extracts only; both pages returned 403]
- According to the extracts, IPC guidance treats a one-phase difference between the AFI and AMN scales as "not unusual", because the two are driven by different factors. It reserves a formal "linkage" analysis for AFI–AMN differences of two or more phases. It also states that acute malnutrition "can manifest either before or after" acute food insecurity.
- The extracts give an example from Somalia in 2025: regions on the Ethiopian border were AFI Phase 3 while their AMN was Phase 4.
- I found **no published IPC GSU tabulation of AFI-phase × AMN-phase concordance** across areas, and no tabulation of SMART GAM by AFI phase. The IPC Accuracy Study (2024; entry 14 in lit_fewsnet_accuracy.md) treats AMN only as a "proof of concept" and tests internal consistency, not agreement between AFI and AMN.

**1.3 FEWS NET (January 2018). *Integrating Acute Malnutrition and Mortality into Scenario Development.* Scenario Development Guidance Document. Washington, DC: FEWS NET.** https://fews.net/global/guidance-documents/january-2018-0 (PDF at /print) [V-full, 48 pp.]
- Quotes IPC 2.0 (p. 18): nutrition and mortality may be used as evidence for an AFI phase *only* where "household food consumption deficits" are "an explanatory factor". Malnutrition from disease outbreaks or poor health access "should not be used as evidence for an IPC classification", and neither should excess deaths from violence.
- Instructs analysts to compare current GAM with "usual" levels for the same area and season, using the DHS/MICS and the FEWS NET nutrition database (pp. 18–19; Annex VI). The protocol for projecting GAM (Annex VII, p. 43) starts from usual seasonal levels and then reasons about the UNICEF framework's causes: diet, disease, care practices and WASH.
- A worked example (p. 18) notes that GAM of about 14% in an area can be typical and does not by itself signal Phase 4.
- *Implication for us:* by construction, FEWS NET reads GAM relative to a zone's own baseline. A cross-zone gradient in GAM *levels* by phase is therefore not something the system is designed to produce. This fits the Somalia finding that GAM is predicted by the zone's previous survey (r = 0.66) and hardly at all by the phase (r = 0.10).

**1.4 FSNAU / FEWS NET (7 Sept 2013). "Food Security and Nutrition Outlook: Despite improvements, 870,000 likely in Crisis and Emergency (IPC Phase 3 and 4) through December."** https://fsnau.org/in-focus/food-security-and-nutrition-outlook-despite-improvements-870000-likely-crisis-and-emergency [V-full]
- An example of the decoupling in Somalia. The IPC 3–4 population was at its lowest since the 2011 famine, yet GAM exceeded 15% in "18 out of 42 population groups surveyed", and "one out of six" under-5s were estimated to be acutely malnourished.

**1.5 Checchi & Robinson (2013), survey trends** (full entry under 2.1) [V-full]
- From 2007–2012 survey data: "no increase is apparent [in survey CDR/U5DR] during the 2008-2009 period of food security stress", although 2008–09 was a severe AFI crisis in Somalia. Acute malnutrition surveys show the same pattern (pp. 38–39). Only the 2011 famine stands out.

**1.6 Somalia Mortality Estimation Database (S-MED): Ratnayake, R., Ouchtar, Y., Ahmed, Y.A., Mohamoud, J.H., Jelle, M., Seal, A., Dirie, N.I., Palmer, J. & Checchi, F. (2025). "The Somalia Mortality Estimation Database (S-MED): a bird's eye view of mortality and its determinants." medRxiv 10.1101/2025.09.07.25335291.** [V-abs: Europe PMC abstract; full text blocked]
- S-MED compiles SMART mortality, morbidity, IPC and environmental data for real-time use. A search-engine extract of the full text says that by October 2022 S-MED could show "overlap" between IPC Phase 4 areas and above-threshold CDR/U5DR. I could not verify any quantitative concordance statistic. Worth requesting the database: it is the natural source for a CDR-by-phase table in Somalia.

## 2. Mortality estimation using (or not using) IPC phase as a predictor

**2.1 Checchi, F. & Robinson, W.C. (2013). *Mortality among populations of southern and central Somalia affected by severe food insecurity and famine during 2010–2012.* Rome/Washington: FAO/FSNAU and FEWS NET.** https://fsnau.org/downloads/Somalia_Mortality_Estimates_Final_Report_8May2013_upload.pdf [V-full; core numbers already in lit_shocks_nutrition.md §4]
New points relevant here:
- **The IPC phase is used only to define a baseline, not as a predictor.** "Method 2" takes as baseline the surveys done in populations "entirely classified" as IPC 1–2. Only 12 such surveys existed (p. 43). The predictive model's regressors (Table 6, pp. 40–41) are region, conflict rate, livelihood, epidemics, presence of WFP, and terms of trade (with a steep rise in mortality below 10,000 kcal per daily wage when WFP is absent). The IPC phase is not among them.
- **The baseline CDR was already within the IPC Phase 3 band.** The counterfactual no-crisis CDR for south-central Somalia "oscillate[d] between 0.5 and 0.8", against a sub-Saharan Africa 2010 average of 0.37 (pp. 8–9). The peak for all strata combined was about 2.5 (June–July 2011). Individual surveys reached CDR 5–6 and U5DR 10–15.

**2.2 Warsame, A., Frison, S. & Checchi, F. (2023). "Drought, armed conflict and population mortality in Somalia, 2014–2018: A statistical analysis." *PLOS Global Public Health* 3(4): e0001136.** https://doi.org/10.1371/journal.pgph.0001136 [V-full, PMC10096495]
- The final model's predictors were conflict, the SAM admission rate, measles and malaria. **The IPC phase was not a predictor.** The authors report only that, "on visual inspection", regional excess death rates "correlated broadly" with the early-2017 projected share of the population in IPC 3–4 (Fig 6). No coefficient is given.
- Excess deaths in Jan 2017–Dec 2018 were **44,700 (95% CI 37,600–52,000)** in the most likely scenario, and 163,800 in the pessimistic one. Only about 21% were under-5s.
- Regional CDR ranged from **0.33 to 0.60** per 10,000/day, and the increase in CDR was "'only' about 15%". This was in a year when about 3.1–3.2 million people were in IPC 3–4 (FSNAU, May and Aug 2017).
- The authors conclude that "even at moderate levels of population stress (for example, IPC phase 3), excess mortality accrues".
- Terms of trade, the key predictor in 2010–12, showed "no consistent association" with mortality in 2017–18.

**2.3 LSHTM / UNICEF / WHO / FSNAU / SIMAD (March 2023). *From insight to action: examining mortality in Somalia.* Brief.** https://fsnau.org/downloads/Examining-Mortality-in-Somalia-From-Insight-to-Action-2023.pdf [V-full, 6 pp.]
- Somalia 2022: **43,000 excess deaths** relative to 2015–16 (21,800 under-5s), or 24,200 relative to 2019–21. National CDR rose **from 0.33 to 0.38** per 10,000/day over 2022. The highest regional means were Bay **0.49**, Banadir 0.46 and Bakool 0.42.
- Even in the regions projected to face Famine, **mean CDR stayed below the IPC Phase 3 floor of 0.5**. Some surveys in Baidoa, Burhakaba, Middle Shabelle and the Mogadishu IDP camps did exceed Phase 4 thresholds (FSNAU multi-partner technical release, 13 Dec 2022).
- The brief states that "most deaths ... do not occur in the relatively small pockets categorized as ... IPC phase 5, but in the much larger sections of the population exposed to IPC phases 3 and 4 over protracted periods". It adds that areas facing risk of famine "had higher mortality".
- Model predictors were conflict, SAM admissions, measles, malaria, terms of trade and others. IPC phase is not listed.

**2.4 LSHTM / SIMAD / UNICEF / WHO / FSNAU (Jan 2025). *From insight to action: an update on mortality patterns in Somalia.* Brief.** https://www.unicef.org/somalia/media/5166/file/From%20insight%20to%20action,%20an%20update%20on%20mortality%20patterns%20in%20Somalia_January%202025.pdf.pdf (UN Somalia press release, 21 Jan 2025: https://somalia.un.org/en/288200-new-study-estimates-71000-drought-related-%E2%80%9Cexcess%E2%80%9D-deaths-may-have-occurred-somalia-between) [V-full]
- Jan 2022–Jun 2024: **71,100 excess deaths (range 28,200–125,100)**, "41%" among under-5s. The brief also gives an internally inconsistent under-5 figure of "about 67,500", so flag it. Revised year totals are 36,200 for 2022 and 38,500 for 2023. The estimate draws on 496 SMART surveys.
- Key passage for us: north-eastern regions "have seen relatively lower mortality than south-central regions, despite being projected back in 2022 by the [IPC] to have comparatively similar percentages of their populations in critical or acute food insecurity situations". **The same phase mix was associated with very different mortality.**
- Peer-reviewed version: Ouchtar, Y., Ali, ..., Warsame, A., ..., Watson, O., Checchi, F. (2026). "Drought-attributable mortality in Somalia, 2015–2024: a retrospective and modelling study." *Lancet Regional Health – Africa*, article 100072. https://doi.org/10.1016/j.lanafr.2026.100072 [V-abs: title and authors via Crossref; full text blocked. One search extract gives 64,500 (91%) of the 71,100 as under-5s, which contradicts the brief's 41%. Check before citing either share.]

**2.5 Checchi, F., Testa, A., Gimma, A., Koum-Besson, E. & Warsame, A. (2022). "A method for small-area estimation of population mortality in settings affected by crises." *Population Health Metrics* 20: 4.** https://doi.org/10.1186/s12963-022-00283-6 [V-full, PMC8751462]
- The predictor table covers Somalia 2010–12, South Sudan 2013–18, Somalia 2014–18 and Nigeria 2016–19. The food-security domain is represented only by livelihood type, terms of trade and staple cereal prices. **The IPC phase is not a candidate predictor in any of the four applications.**
- GitHub `francescochecchi/mortality_small_area_estimation`: I inspected `som_analysis_parameters.xlsx` and `som_predictor_data.xlsx` [V-full]. The candidate predictors are ACLED events and fatalities, attacks on aid workers, AWD, IDPs, livelihood, malaria, measles, SPI, rainfall, SAM admissions, SAM quality, terms of trade, cash and ration coverage, and others. **There is no IPC variable.** Forced in: conflict, malaria, measles, SAM admissions (lag 2).
- South Sudan: about 383,000 excess deaths, Dec 2013–Apr 2018, about half violent (Checchi, Testa, Warsame, Quach & Burns, LSHTM, Sept 2018) [V-abs].

**2.6 Checchi, F., Frison, S., Warsame, A., et al. (2022). "Can we predict the burden of acute malnutrition in crisis-affected countries? Findings from Somalia and South Sudan." *BMC Nutrition* 8: 92.** https://doi.org/10.1186/s40795-022-00563-2 [V-full, PMC9421106]; GitHub `francescochecchi/acute_malnutrition_predictive_models` [V-full: parameter files inspected]
- Data: 85 SMART surveys in Somalia (2014–18) and 175 in South Sudan (2015–18). The IPC phase is **not among the candidate predictors** (repo `predictor_parameters` sheet). Food security enters only through terms of trade and water prices.
- Predictive performance was "disappointing", and the models are "not usable for action". In Somalia, the random-forest model for GAM had 95% CI coverage of 59.6% (LOOCV) and 56.7% (holdout). At the 15% threshold it had sensitivity 72.0% and specificity 59.1%.
- The most useful predictors were livelihood, measles, NDVI, terms of trade and water price. Pastoralist and displaced livelihoods had *better* anthropometry than agriculturalists.
- The authors suspect that the missing factors are IYCF practices, WASH and health-service use.
- *Implication:* even rich multi-sector covariates explain little of the cross-survey variation in GAM in Somalia. A flat phase–GAM gradient is therefore unsurprising.

**2.7 Checchi, F., AbuKoura, R., Kadiyala, S., Nyawo, M. & Maina, L. (2026). "Predicting the burden of acute malnutrition in drought-prone regions of Kenya." *PLOS Global Public Health* 6: e0004485. https://doi.org/10.1371/journal.pgph.0004485 (preprint medRxiv 10.1101/2025.03.19.25324283).** [V-abs; authors and journal details as reported by the research sub-agent]. The authors report only "moderate performance".; GitHub `ken_malnut_prediction` [V-full: predictor metadata inspected]
- Six ASAL counties, 2015–19, 79 survey strata, 44,218 children. Predictors are ACLED, WFP prices, MAM/SAM admissions, morbidity, vaccination, service use and schooling. **No IPC phase or NDMA drought phase is in the predictor workbook.**

**2.8 Checchi, F., Jarvis, C.I., van Zandvoort, K. & Warsame, A. (2023). "Mortality among populations affected by armed conflict in northeast Nigeria, 2016 to 2019." *PNAS* 120(30): e2217601120.** https://doi.org/10.1073/pnas.2217601120 [V-full, PMC10372555]
- **490,900 excess deaths (95% CI 377,500–599,500)**, Apr 2016–Dec 2019, 47% of them under-5s. Mean CDR was 0.73 (2016), 0.71 (2017), 0.42 (2018) and 0.32 (2019). The survey median was 0.55, against a national projection of 0.34.
- Predictors were livelihood, maize price, humanitarian actor presence and vaccination geo-coverage. The IPC/CH phase was not used. In mid-2016, about 34% of the 3 states' roughly 12m people were projected in CH phases 3–5.

## 3. The food security–acute malnutrition link more generally

Items 3.1–3.14 were compiled by a research sub-agent, which checked each against the source to the level stated in its tag. I re-checked Reusken et al. against the full text.

**3.1 Young, H. & Marshak, A. (2017; cover dated Jan 2018). *Persistent Global Acute Malnutrition: A discussion paper on the scope of the problem, its drivers, and recommendations for policy, practice, and research.* Feinstein International Center, Tufts University.** https://medbox.org/index.php/dl/5e148832db60a2044c2d4c99 [V-full]
- "Persistent GAM" means the >15% threshold is exceeded repeatedly for years.
- "evidence in protracted persistent GAM settings indicates that food security may not be the main driver". The case studies "frequently show little correlation with trends in food insecurity or cereal prices".
- Kanem (Chad): GAM was above 15% in 15 of 17 surveys (1992–2015), even at harvest.
- Northern Bahr el Ghazal (South Sudan): GAM was above 15% in almost every survey from 2005 to 2014, even when the area was "classified green on the IPC".
  - An ACF causal analysis in Aweil East (2011) found "no correlation among malnutrition, household hunger scale, and food consumption score".
- Niger (Maradi/Zinder): a FEWS NET-commissioned analysis (2014–16) found food security was not associated with GAM.
- Sila (Chad): "no correlation between child WHZ and food insecurity indicators". Wasting was associated with cattle density, water and hygiene (see also Marshak, Young, Bontrager & Boyd 2017, *Food Nutr Bull* 38: 115–127, [V-abs]).

**3.2 Luc, G., Keita, M., Houssoube, F., et al. (incl. Marshak, A., Osman, A.M.) (2023). "Community clustering of food insecurity and malnutrition associated with systemic drivers in Chad." *Food and Nutrition Bulletin* 44(2 suppl): S69–S82.** https://doi.org/10.1177/03795721231189970 [V-abs]
- Kanem and Bahr el Ghazal, 2021: 86 villages, 7,002 households, 6,136 children.
- Wasting and food insecurity were each spatially clustered, but "communities with a high prevalence of child wasting were not those with the highest levels of food insecurity". **This is the closest published analogue to the Somalia result.**
- A related cluster RCT (Luc et al., medRxiv 2026, [V-abs, not peer reviewed]) protected dry-season milk through livestock feeding. It found GAM of 22.2% vs 47.4% at the dry-season peak (aOR 0.29). That points to a milk/zoonotic channel rather than general food access.

**3.3 Moradi, S., Mirzababaei, A., Mohammadi, H., et al. (2019). "Food insecurity and the risk of undernutrition complications among children and adolescents: a systematic review and meta-analysis." *Nutrition* 62: 52–60.** https://doi.org/10.1016/j.nut.2018.11.029 [V-abs]
- 21 studies, 55,173 individuals. Household food insecurity is associated with:
  - stunting: OR 1.17 (1.09–1.25);
  - underweight: OR 1.17 (1.01–1.36);
  - **wasting: OR 1.04 (0.96–1.12), i.e. no association.**

**3.4 Reusken, M., Coffey, C., Cruijssen, F., Melenberg, B. & van Wanrooij, C. (2025). "Identification of factors associated with acute malnutrition in children under 5 years and forecasting future prevalence." *BMJ Public Health* 3: e001460.** https://doi.org/10.1136/bmjph-2024-001460 [V-full, PMC11883882]
- Somalia, district-level FSNAU GAM, biannual, 2017–2021. Candidate inputs include the percentage of the population in IPC Phase 3+.
- "The 6-month lag of GAM is very highly associated with GAM itself ... This relationship is characterised as linear." IPC 3+ is among the associated factors, but the association is nonlinear.
- The random forest forecasts the direction of change correctly 72.9% of the time, against 37.3% for a naive forecast. MAE is 0.502 vs 1.004 (naive) and 0.562 (exponential smoothing), on the paper's preprocessed scale.
- *Note:* this is the only Somalia study found that puts IPC share and lagged GAM in the same model. It matches the 0.66 vs 0.10 contrast.

**3.5 Constenla-Villoslada, S., Liu, Y., McBride, L., Ouma, C., Mutanda, N. & Barrett, C.B. (2025). "High-frequency monitoring enables machine learning-based forecasting of acute child malnutrition for early warning." *PNAS* 122: e2416161122.** https://doi.org/10.1073/pnas.2416161122 [V-full, by sub-agent]
- Kenya NDMA monthly ward-level MUAC data.
- Out-of-sample R² at 1, 3, 6 and 12 months ahead:
  - secondary/remote-sensing data only: 0.39, 0.29, 0.19, 0.12;
  - lagged outcome only: 0.53, 0.32, 0.23, 0.15.
- "Predictive skill depends heavily on autocorrelation." Earlier studies based on infrequent anthropometry average an out-of-sample R² of about 0.08–0.11.

**3.6 Kinyoki, D.K., Berkley, J.A., Moloney, G.M., Kandala, N.-B. & Noor, A.M. (2015). "Predictors of the risk of malnutrition among children under the age of 5 years in Somalia." *Public Health Nutrition* 18(17): 3125–3133.** https://doi.org/10.1017/S1368980015001913 [V-abs]
- FSNAU surveys 2007–2010; wasting was 21%. The authors conclude that "infection and climatic variations are likely to be key drivers".
- Companion space-time mapping paper (Kinyoki et al. 2016, *Spatial and Spatio-temporal Epidemiology* 16: 77–87, [V-abs]): "minimal variation in wasting from year-to-year", with persistent hotspots (Gedo 37%, Bay 32%, Nugaal 25%).
- Conflict and wasting: Kinyoki et al. 2017, *BMJ Global Health* 2: e000262, OR 1.37 [V-abs].

**3.7 Venkat, A., Marshak, A., Young, H. & Naumova, E.N. (2023). "Seasonality of acute malnutrition in African drylands: evidence from 15 years of SMART surveys." *Food and Nutrition Bulletin* 44(2 suppl).** https://doi.org/10.1177/03795721231178344 [V-abs; already in lit_shocks_nutrition.md]
- The main wasting peak is April–May, at the temperature peak before the rains, rather than in the lean season.
- Marshak, Young & Naumova (2023, *Food Nutr Bull* 44: S109–S118, [V-abs]): in eastern Chad, +1°C in monthly temperature raises the odds of wasting by 5% and of severe wasting by 12%.

**3.8 Mertens, A., Benjamin-Chung, J., Colford, J.M., et al. (2023). "Child wasting and concurrent stunting in low- and middle-income countries." *Nature* 621: 558–567.** https://doi.org/10.1038/s41586-023-06480-z [V-abs]
- Wasting is highly dynamic: 5.6% of children were wasted at 24 months, but 29.2% had ever been wasted.
- Incidence peaks at 0–3 months, and seasonal swings in mean WLZ exceed 0.5 z in high-rainfall settings. Prenatal and maternal determinants are emphasised.

**3.9 Bliss, J., et al. (2016). "Factors associated with the risk of acute malnutrition among children in households targeted by an emergency cash transfer program [Niger]." *Food and Nutrition Bulletin* 37: 387–400.** https://doi.org/10.1177/0379572116654772 [V-abs]
- Child illness: HR 1.79 (1.10–2.92). The food-expenditure pathway was not supported.

**3.10 Hirvonen, K., Sohnesen, T.P. & Bundervoet, T. (2020). "Impact of Ethiopia's 2015 drought on child undernutrition." *World Development* 131: 104964.** [V-full of the 2018 IFPRI ESSP working paper, by sub-agent]
- The drought "did not lead to widespread increases" in acute undernutrition.
- Caveat: self-reported hunger did not rise either, and aid doubled. This is a case of response neutralising the shock, not of food insecurity rising without any wasting.

**3.11 Fenn, B., Morris, S.S. & Frost, C. (2004). "Do childhood growth indicators in developing countries cluster? Implications for intervention strategies." *Public Health Nutrition* 7: 829–834.** https://doi.org/10.1079/PHN2004632 [V-abs]
- 58 DHS surveys. The median intra-cluster correlation is 0.032 for wasting and 0.054 for stunting. Wasting is "determined at the household, or even individual, level", so area labels carry little information about it.

**3.12 Bilukha, O. & Leidman, E. (2018). "Concordance between estimates of wasting measured by weight-for-height and by MUAC for classification of severity of nutrition crisis." *BMC Nutrition* 4: 24.** https://doi.org/10.1186/s40795-018-0232-0 [V-abs]
- 733 surveys. WHZ and MUAC prevalence correlate at ρ = 0.55 (R² = 0.36). Even two anthropometric definitions of GAM agree only moderately, which is a measurement ceiling on any phase–GAM gradient.

**3.13 Machefer, M., Ronco, M., Thomas, A.C., et al. (2025). "A monthly sub-national Harmonized Food Insecurity Dataset for comprehensive analysis and predictive modeling." *Scientific Data* 12: 741.** https://doi.org/10.1038/s41597-025-05034-4 [V-full, by sub-agent]
- The dataset is in *Scientific Data*. The *Global Food Security* 2025 paper (vol. 45: 100859) is a separate ML-forecasting review.
- **Neither contains nutrition or mortality outcomes.** It reports that FEWS NET phase correlates with IPC/CH phase at r = 0.61, and IPC/CH phase with real-time FCS at r = 0.02.
- Lentz et al. (2019, Malawi) is confirmed to be about household food-security outcomes only, not anthropometry (see lit_fewsnet_accuracy.md).

**3.14 Counter-evidence (food access does matter at the margin, or at the extreme)**
- Somalia 2011: GAM above 30% in most famine strata (§4.1).
- REFANI Pakistan: double-value cash cut the odds of wasting (lit_shocks_nutrition.md).
- Fenn et al. (2021, *BMJ Nutrition, Prevention & Health* 4: 235–242, [V-full by sub-agent]): a roughly 50% ration cut in Chad camps was followed by a WHZ decline.
- Zhou et al. (2026, *Journal of Public Health Policy* 47: 82–96, [V-abs]): in Yemen, malnutrition seasonality "could be synchronized" with the food-insecurity peak.
- I did not verify a "Lancet wasting series 2023/24" [NV]. Do not cite it without checking.

## 4. Are the IPC mortality and GAM bands borne out?

**4.1 Observed outcomes in Phase 4/5 and famine-reviewed areas.** Compiled by a sub-agent from the primary FRC and FSNAU reports [V-full unless noted]; I spot-checked the Somalia Dec 2022 figures and the Young & Jaspars regression. Rates are per 10,000/day, excluding trauma unless noted.

| Case | Classification | CDR (95% CI) | U5DR | GAM (WHZ unless noted) | Source |
|---|---|---|---|---|---|
| Somalia Jul–Aug 2011, famine strata (Lower/Middle Shabelle, Bay, Bakool, Afgoye and Mogadishu IDPs) | Famine | 2.11–6.12 | 5.2–20.3 | 28.7–58.3% | FEWS NET/FSNAU famine declaration deck, 2 Sept 2011 |
| Somalia 2011, non-famine strata (Gedo, Juba, Hiran) | Phase 4 | 1.21–1.94 | — | 31–43% | same |
| Somalia 2017 Bay agropastoral | Phase 4 | 2.43 | 4.65 | 19.1% | FSNAU Jilaal survey results, 29 May 2017 |
| Somalia 2017 N. Inland Pastoral | Phase 4 | 0.77 | — | 25.7% | same |
| Somalia Jul 2022 Baidoa/Burhakaba rural | Phase 4, Famine projected | 1.69 (1.04–2.75) | 3.72 | 24.9% | IPC FRC Somalia, Sept 2022 |
| Somalia Oct 2022 Baidoa IDPs | Phase 4 (FRC) | 1.84 (1.24–2.73) | 4.86 | 21.2% | IPC FRC Somalia, Dec 2022 |
| Somalia Oct 2022 rural Baidoa/Burhakaba | Phase 4 | 1.16 (0.83–1.67) | 1.95 | 19.3% | same |
| South Sudan 2017 Leer/Mayendit | Famine "likely" | no survey | — | MUAC screening only | FEWS NET Outlook Feb/June 2017 [V-abs] |
| South Sudan Pibor 2020 | Famine Likely | "no household survey data" | judged "plausible" > threshold | MUAC 17–21.4% (+10 points to convert to WHZ) | IPC FRC Nov 2020 |
| Tigray 2021 | Risk of Famine | no mortality data | — | screening only | IPC FRC July 2021 |
| Gaza Jun 2024 | Risk of Famine | 0.55 (0.31–0.96), all-cause | 0.72 | MUAC ~1% north | IPC FRC June 2024 |
| Gaza Aug 2025 | Famine (reasonable evidence) | no current survey; ~1 for Oct 2023–Jan 2025; thresholds "inferred" exceeded | — | MUAC ≥15% | IPC FRC Aug 2025 |
| Sudan Zamzam Jan 2024 | Famine (reasonable evidence) | 1.9 (1.5–2.4) non-trauma; 2.5 incl. trauma | 2.0 | MUAC 23.1% | IPC FRC July 2024 |
| Sudan W. Nuba 2024 | Famine | IDPs 1.07 (0.73–1.57); residents 0.86 | — | 36.3% / 31.2% | IPC FRC Dec 2024 |
| Sudan N. Darfur Aug–Sep 2024 | Famine / Risk | 0.32–1.88 | 0.71–1.75 | 27.9–33.3% | IPC FRC Dec 2024 |
| NE Nigeria 2016–17 | Phase 3–4 / Famine retrospectively | up to 1.36 | up to 2.63 | 6.4–14.3% | Leidman et al. 2017, MMWR 66(48): 1332–5 [V-full by sub-agent] |

What the table shows:
- **Since 2017, measured non-trauma CDR in famine-reviewed areas has been in the Phase 3–4 range (0.3–1.9) or missing.**
- GAM above 30% coexists with CDR of 0.3–1.1 (North Darfur, Western Nuba).
- CDR above 2 can sit inside a Phase 4 classification (Bay 2017).
- FRCs repeatedly *infer* that Phase 5 mortality "has crossed" the threshold after the survey date.
- On 4 June 2024, the FRC explicitly refused to extrapolate the Somalia 2011 GAM–mortality relationship to Gaza.

**4.2 Young, H. & Jaspars, S. (2009). *Review of Nutrition and Mortality Indicators for the IPC: Reference Levels and Decision-making.* SCN Task Force on Assessment, Monitoring and Evaluation / Feinstein International Center / ODI.** https://cdn.odi.org/media/documents/5636.pdf [V-full; key passages spot-checked]
- **This is the key source on the evidence base for the thresholds.** Mortality thresholds "are based on the health profiles of IDPs and refugees in camp situations in the 1990's".
  - 1/10,000/day is Toole & Waldman's (1990) doubling of the Sub-Saharan baseline of 0.44.
  - Hakewill & Moren (1991) set >1 "very serious", >2 "out of control" and >5 "famine".
  - IPC adopted 2 for Famine on CDC's recommendation. The authors recommended returning to >5.
- The GAM–mortality evidence is from refugee and displaced camps:
  - Nieburg et al. (1992): mortality 12× and 40× higher at 20% and 40% wasting than below 5%.
  - ACC/SCN (1994): log CMR = −2.05 + 0.875·log(wasting), R² = 0.59, n = 80.
  - Mason (2002): 10% wasting ≈ CMR 1.
- They reject livelihood-specific GAM reference levels because of "insufficient evidence".
- **No calibration of GAM or CDR against food-security phase is presented anywhere.**

**4.3 IPC Technical Manual v1.1 (FAO/IPC 2008), ch. 4 "IPC Reference Table – Technical Guidelines."** https://www.fao.org/4/i0275e/i0275e02.pdf [V-full by sub-agent]
- The CDR bands cite four sources:
  - Sphere 2004 (doubling of baseline);
  - UNICEF 2003, giving a Sub-Saharan baseline of 0.44 and emergency at 0.9;
  - SCN 2004;
  - a personal recommendation from CDC (Brennan & Bilukha, 2006).
- These bands have carried forward unchanged to Technical Manual 3.1: Phase 3 0.5–1; Phase 4 1–2 or more than twice the reference; Phase 5 >2. I could not open the 3.1 PDF; its bands are as given in the task and quoted by Oxfam 2022.

**4.4 Checchi, F. & Roberts, L. (2005). *Interpreting and using mortality data in humanitarian emergencies: a primer for non-epidemiologists.* HPN Network Paper 52. London: ODI.** https://odihpn.org/wp-content/uploads/2005/09/networkpaper052.pdf [V-full by sub-agent]
- "Baseline, non-crisis CMRs in most of Sub-Saharan Africa are in the range 0.3–0.6 per 10,000 per day, with a probable current average of 0.44."
- Sphere emergency thresholds by region: Sub-Saharan Africa 0.9 (under-5: 2.3); South Asia 0.5; Latin America 0.3.
- Checchi's 2018 report for the Global Health Cluster (*Estimation of population mortality in crisis-affected populations*, LSHTM, [V-full by sub-agent]) calls fixed CDR thresholds "arbitrary". What matters is excess rate × duration × population.

**4.5 Mason, J.B., White, J.M., Heron, L., Carter, J., Wilkinson, C. & Spiegel, P. (2012). "Child acute malnutrition and mortality in populations affected by displacement in the Horn of Africa, 1997–2009." *Int. J. Environ. Res. Public Health* 9(3): 791–806.** https://doi.org/10.3390/ijerph9030791 [V-full; key figure spot-checked]
- 1,175 surveys. U5MR rises "1.2 to 1.4/10,000/day" per 10 points of GAM.
- The curve shifted down after 2005: for pastoralists, U5MR at 20% GAM fell from about 1.5 to about 1.
- Optimal GAM cut-offs for predicting U5MR above 1–2 are 20–25% for pastoralists and 10–15% for agriculturalists.
- GAM is a weak screen: at 20% GAM, sensitivity 0.61, specificity 0.67, PPV 0.38.
- *Use:* this is the best available GAM→mortality slope if the paper needs to convert malnutrition into deaths.

**4.6 Heudtlass, P., Speybroeck, N. & Guha-Sapir, D. (2016). "Excess mortality in refugees, internally displaced persons and resident populations in complex humanitarian emergencies (1998–2012) – insights from operational data." *Conflict and Health* 10: 15.** https://doi.org/10.1186/s13031-016-0082-9 [V-abs]
- 1,759 CE-DAT CDR estimates. Median ratio of observed to baseline CDR: refugees 0.94, IDPs 2.5, residents 1.51.
- This is a useful benchmark for "typical" crisis excess, about +50% for residents. It is **not** analysed by food-security phase or GAM. I found no CE-DAT study relating CDR to IPC phase.

**4.7 Howe, P. & Devereux, S. (2004). "Famine intensity and magnitude scales: a proposal for an instrumental definition of famine." *Disasters* 28(4): 353–372.** [V-abs; already in lit_humanitarian_data.md]
- Intensity levels:

| Level | CDR | Wasting |
|---|---|---|
| Food crisis | 0.5–1 | 10–20% |
| Famine | 1–5 | 20–40% |
| Severe famine | 5–15 | ≥40% |
| Extreme famine | ≥15 | — |

- On this scale, IPC Phase 5 (>2, GAM >30%) sits inside H&D's "famine" level.

**4.8 de Zwarte, I., de Waal, A. & Lumey, L.H. (2026). "Rethinking current famine classification: insights from history." *The Lancet*.** [V-abs; in lit_humanitarian_data.md]
- Argues that the CDR benchmarks were built for rural African baselines and are miscalibrated for other demographic profiles, such as Gaza.
## 5. Converting phases into deaths: what the documented crises imply

**5.1 Oxfam (Sept 2022). "Hunger likely to claim a life every 36 seconds in drought-stricken East Africa over next three months." Press release, notes to editors.** https://www.oxfam.ca/?p=41511 [V-full]
- This is the IPC-band conversion applied directly. Oxfam takes the Phase 3 CDR of 0.5–0.99, subtracts a "normal" 0.22, and multiplies by everyone in IPC 3+ (31.4m in Kenya, Somalia and Ethiopia). The result is 880–2,421 deaths/day.
- Applied to Somalia alone in 2022 (about 6.7m projected in IPC 3+), the same formula gives about **68,000–188,000 excess deaths per year**. LSHTM's model-based estimate is **36,200–43,000**, a factor of roughly 2–5 lower, *even though Oxfam ignored the higher Phase 4/5 bands*.

**5.2 Ratio of excess deaths to Phase 3+ population (my calculations from the verified figures above; the denominators are point-in-time IPC 3+ counts, so they are rough)**

| Crisis | Excess deaths (period) | IPC/CH 3+ population | Deaths / P3+ pop. | Implied excess CDR among P3+ (per 10,000/day) |
|---|---|---|---|---|
| Somalia 2010–12 famine | 258,000 (Oct 2010–Apr 2012, ~19 mo) | 2.4m (early 2011) to 4.0m (Sept 2011) | 6.5–10.8% | 1.1–1.9 |
| Somalia 2017–18 | 44,700 (24 mo) | 3.1–3.2m (2017) | 1.4% | ~0.19 |
| Somalia 2022 | 36,200–43,000 (12 mo) | 5.6m (updated Oct–Dec) to 6.7m (projected) | 0.5–0.8% | 0.15–0.21 |
| NE Nigeria 2016–19 (conflict) | 490,900 (45 mo) | ~4.1m (34% of ~12m, mid-2016) | ~12% | ~0.9 |
| IPC bands (minus a 0.22–0.33 baseline) | — | — | — | Phase 3: ~0.2–0.8; Phase 4: ~0.7–1.8; Phase 5: >1.7 |

Caveats: excess deaths also occur among people *not* in Phase 3+, which biases the ratio up. Phase 3+ counts fluctuate within a crisis, and peak counts bias it down. The counterfactuals differ: 2015–16 for 2022, and modelled no-drought baselines for 2010–12.

**5.3 Other benchmarks for the conversion**
- **Somalia 2010–12, by phase.** Excess mortality "began to rise well before" famine was declared, "including in areas where famine was not declared" (Checchi & Robinson 2013, p. 9). Using IPC 1–2 surveys as the baseline (their Method 2) gives a *higher* toll, because even "normal" south-central Somalia had CDR 0.5–0.8.
- **Share of deaths by phase.** In 2022, "most deaths ... do not occur in the relatively small pockets categorized as ... IPC phase 5, but in the much larger sections of the population exposed to IPC phases 3 and 4 over protracted periods" (LSHTM 2023). For a cost-effectiveness analysis, the population-weighted Phase 3–4 excess rate is therefore what matters. The Phase 5 band matters much less.
- **Typical crisis excess.** CE-DAT operational data give a median observed/baseline CDR of 1.51 for crisis-affected resident populations (Heudtlass et al. 2016). Against a 0.3–0.4 baseline, that is an excess of about 0.15–0.2 per 10,000/day, close to the Somalia 2017/2022 per-Phase-3+ figure.
- **Duration and response.** Warsame et al. (2023) attribute the lower 2017–18 toll, relative to 2011, to "a lesser effect on food security" and a "more proactive and far-reaching humanitarian response". So the per-phase death rate is itself conditional on response, which is the mechanism the paper's benefit-cost calculation is trying to value. An empirical per-phase rate from a responded-to crisis (2017, 2022) is closer to a *with-response* rate. The 2011 rate (≈1.1–1.9) is closer to a *without-response* rate.

**5.4 Suggested parameterisation for the paper**

| Parameter | Central | Range | Basis |
|---|---|---|---|
| Excess CDR, per Phase 3+ person, non-famine crisis with response | 0.2 /10,000/day (≈7 per 1,000 person-years) | 0.1–0.5 | Somalia 2017–18 and 2022 (§5.2); CE-DAT resident median (§4.6); IPC Phase 3 band less baseline as the upper end |
| Excess CDR, per Phase 3+ person, famine-type crisis without timely response | 1.5 /10,000/day | 0.9–1.9 | Somalia 2010–12 (§5.2); NE Nigeria 0.9 |
| Baseline CDR to subtract when using IPC bands | 0.3–0.5 (Somalia south-central 0.5–0.8) | — | Checchi & Roberts 2005; Checchi & Robinson 2013 |
| GAM by phase | zone baseline + 0–2 points from Phase 2 to Phase 4+ | — | Somalia FSNAU data (this paper); Reusken et al. 2025; Moradi et al. 2019 |
| U5DR per 10 points of GAM | +1.2–1.4 /10,000/day | lower after 2005 | Mason et al. 2012 |

The IPC reference-table bands are best treated as an **upper bound**. The defensible point estimate for Phase 3–4 populations is roughly an order of magnitude below a literal reading of the Phase 4 band.

---
## BibTeX

```bibtex
@techreport{ipc2016amn,
  author      = {{IPC Nutrition Working Group}},
  title       = {{IPC} for Acute Malnutrition: Concepts, Tools, and Procedures to be used to Classify Areas based on Acute Malnutrition},
  institution = {IPC Global Support Unit},
  address     = {Rome},
  year        = {2016},
  month       = jun,
  note        = {Cleared by the IPC Technical Advisory Group and endorsed by the IPC Steering Committee},
  url         = {https://www.nutritioncluster.net/sites/nutritioncluster.com/files/2020-03/IPC-for-Acute-Malnutriton-Concepts-and-Tools-Cleared-by-TAG-and-Endorsed-by-SC.pdf}
}

@techreport{fewsnet2018nutmort,
  author      = {{FEWS NET}},
  title       = {Integrating Acute Malnutrition and Mortality into Scenario Development},
  institution = {Famine Early Warning Systems Network},
  type        = {Scenario Development Guidance Document},
  address     = {Washington, DC},
  year        = {2018},
  month       = jan,
  url         = {https://fews.net/global/guidance-documents/january-2018-0}
}

@techreport{youngjaspars2009,
  author      = {Young, Helen and Jaspars, Susanne},
  title       = {Review of Nutrition and Mortality Indicators for the Integrated Food Security Phase Classification ({IPC}): Reference Levels and Decision-making},
  institution = {SCN Task Force on Assessment, Monitoring and Evaluation; Feinstein International Center; Humanitarian Policy Group, ODI},
  year        = {2009},
  month       = sep,
  url         = {https://cdn.odi.org/media/documents/5636.pdf}
}

@techreport{youngmarshak2017,
  author      = {Young, Helen and Marshak, Anastasia},
  title       = {Persistent Global Acute Malnutrition: A Discussion Paper on the Scope of the Problem, its Drivers, and Recommendations for Policy, Practice, and Research},
  institution = {Feinstein International Center, Tufts University},
  address     = {Boston},
  year        = {2017}
}

@article{warsame2023,
  author  = {Warsame, Abdihamid and Frison, Severine and Checchi, Francesco},
  title   = {Drought, armed conflict and population mortality in {Somalia}, 2014--2018: A statistical analysis},
  journal = {PLOS Global Public Health},
  year    = {2023},
  volume  = {3},
  number  = {4},
  pages   = {e0001136},
  doi     = {10.1371/journal.pgph.0001136}
}

@techreport{lshtm2023somalia,
  author      = {{London School of Hygiene \& Tropical Medicine} and {UNICEF} and {WHO}},
  title       = {From Insight to Action: Examining Mortality in {Somalia}},
  institution = {LSHTM, UNICEF, WHO, Federal Government of Somalia, FAO-FSNAU, SIMAD University},
  year        = {2023},
  month       = mar,
  url         = {https://fsnau.org/downloads/Examining-Mortality-in-Somalia-From-Insight-to-Action-2023.pdf}
}

@article{ouchtar2026,
  author  = {Ouchtar, Y. and others and Checchi, Francesco},
  title   = {Drought-attributable mortality in {Somalia}, 2015--2024: a retrospective and modelling study},
  journal = {The Lancet Regional Health -- Africa},
  year    = {2026},
  pages   = {100072},
  doi     = {10.1016/j.lanafr.2026.100072},
  note    = {Crossref surnames: Ouchtar, Ali, Ahmed, Adam, Dirie, Warsame, Yusuf, Grundy, Watson, Checchi; full text not read}
}

@article{checchi2022sae,
  author  = {Checchi, Francesco and Testa, Adrienne and Gimma, Amy and Koum-Besson, Emilie and Warsame, Abdihamid},
  title   = {A method for small-area estimation of population mortality in settings affected by crises},
  journal = {Population Health Metrics},
  year    = {2022},
  volume  = {20},
  pages   = {4},
  doi     = {10.1186/s12963-022-00283-6}
}

@article{checchi2022malnut,
  author  = {Checchi, Francesco and Frison, S{\'e}verine and Warsame, Abdihamid and Abebe, Kiross Tefera and Achen, Jasinta and Ategbo, Eric Alain and Ayoya, Mohamed Ag and Kassim, Ismail and Ndiaye, Biram and Nyawo, Mara},
  title   = {Can we predict the burden of acute malnutrition in crisis-affected countries? {Findings} from {Somalia} and {South Sudan}},
  journal = {BMC Nutrition},
  year    = {2022},
  volume  = {8},
  pages   = {92},
  doi     = {10.1186/s40795-022-00563-2}
}

@article{checchi2023nigeria,
  author  = {Checchi, Francesco and Jarvis, Christopher I. and van Zandvoort, Kevin and Warsame, Abdihamid},
  title   = {Mortality among populations affected by armed conflict in northeast {Nigeria}, 2016 to 2019},
  journal = {Proceedings of the National Academy of Sciences},
  year    = {2023},
  volume  = {120},
  number  = {30},
  pages   = {e2217601120},
  doi     = {10.1073/pnas.2217601120}
}

@article{reusken2025,
  author  = {Reusken, M. and Coffey, C. and Cruijssen, F. and Melenberg, B. and van Wanrooij, C.},
  title   = {Identification of factors associated with acute malnutrition in children under 5 years and forecasting future prevalence},
  journal = {BMJ Public Health},
  year    = {2025},
  volume  = {3},
  pages   = {e001460},
  doi     = {10.1136/bmjph-2024-001460},
}

@article{mason2012,
  author  = {Mason, J. B. and White, J. M. and Heron, L. and Carter, J. and Wilkinson, C. and Spiegel, P.},
  title   = {Child acute malnutrition and mortality in populations affected by displacement in the {Horn of Africa}, 1997--2009},
  journal = {International Journal of Environmental Research and Public Health},
  year    = {2012},
  volume  = {9},
  number  = {3},
  pages   = {791--806},
  doi     = {10.3390/ijerph9030791}
}

@techreport{checchiroberts2005,
  author      = {Checchi, Francesco and Roberts, Les},
  title       = {Interpreting and Using Mortality Data in Humanitarian Emergencies: A Primer for Non-epidemiologists},
  institution = {Humanitarian Practice Network, Overseas Development Institute},
  type        = {HPN Network Paper},
  number      = {52},
  address     = {London},
  year        = {2005}
}

@article{moradi2019,
  author  = {Moradi, S. and Mirzababaei, A. and Mohammadi, H. and others},
  title   = {Food insecurity and the risk of undernutrition complications among children and adolescents: A systematic review and meta-analysis},
  journal = {Nutrition},
  year    = {2019},
  volume  = {62},
  pages   = {52--60},
  doi     = {10.1016/j.nut.2018.11.029}
}

@article{luc2023chad,
  author  = {Luc, G. and Keita, M. and Houssoube, F. and others},
  title   = {Community clustering of food insecurity and malnutrition associated with systemic drivers in {Chad}},
  journal = {Food and Nutrition Bulletin},
  year    = {2023},
  volume  = {44},
  number  = {2\_suppl},
  pages   = {S69--S82},
  doi     = {10.1177/03795721231189970},
}

@techreport{ipcfrc2022somaliadec,
  author      = {{IPC Famine Review Committee}},
  title       = {Somalia: Famine Review of the {IPC} Acute Food Insecurity and Acute Malnutrition Analyses (December 2022)},
  institution = {IPC Global Partners},
  year        = {2022},
  month       = dec,
  url         = {https://fsnau.org/downloads/IPC-Famine-Review-Report-Somalia_Dec2022.pdf}
}

@techreport{ipcfrc2024sudandec,
  author      = {{IPC Famine Review Committee}},
  title       = {Sudan: Famine Review Committee Report (December 2024)},
  institution = {IPC Global Partners},
  year        = {2024},
  month       = dec,
  url         = {https://reliefweb.int/attachments/be986af3-2c0a-4e02-bd40-a3345d8eff6d/IPC_Famine_Review_Committee_Report_Sudan_Dec2024.pdf}
}
```
