# Old debates the paper steps into

Compiled 2026-10-14 for the Sandefur & Kenny CGD paper. This file extends `lit_phase_outcomes.md` (outcome levels by phase, IPC band origins, Somalia/LSHTM mortality models, conversion of phases into deaths) and `novelty_check.md` (whether anyone has compared survey GAM or mortality with AFI phase). **It does not repeat their entries.** Where a work is covered there, I point to it and add only the "debate" framing.

**The paper's five claims, as used below**
- **(a)** IPC/FEWS NET phases track household food insecurity, loosely, but are a weak guide to child acute malnutrition and a poor guide to mortality. The IPC's reference bands for GAM and CDR are much steeper than measured gradients.
- **(b)** Excess crisis mortality and morbidity is mostly about basic health breaking down, not food consumption. Targeting on food insecurity therefore targets a small part of the problem.
- **(c)** More scheduled nutrition/mortality surveys would measure and predict deaths, and redirecting aid on that basis could raise welfare within current budgets.
- **(d)** Concern should be with deaths wherever they happen, not mainly in camps.
- **(e)** The target of reform should be the IPC, not FEWS NET.

**Verification tags**
- [V-full]: I read the full text in this or an earlier session.
- [V-abs]: I read the abstract, publisher or Crossref/OpenAlex metadata, or a secondary summary.
- [V-meta]: I confirmed only that the work exists (Crossref, OpenAlex or a catalogue), with no substantive reading.
- [NV]: not verified.

All DOIs below were resolved through the Crossref API on 2026-10-14 unless marked otherwise.

---

## 0. The five links the authors flagged

**L1. de Zwarte, I., de Waal, A. & Lumey, L.H. (2026). "Rethinking current famine classification: insights from history." *The Lancet* 407: 755–757 (Correspondence, published online 13 Feb 2026).** https://doi.org/10.1016/S0140-6736(26)00214-X. Bib key: `deZwarte2026Lancet` (already in the bib). [V-abs]
- **Access.** thelancet.com returned 403. I read the Crossref record, the World Peace Foundation summary (https://worldpeacefoundation.org/publication/rethinking-current-famine-classification-insights-from-history/) and the Columbia Mailman press release (14 Feb 2026).
- **Argument.** The IPC's absolute mortality thresholds (CDR > 2, U5DR > 4 per 10,000/day) were built for rural African baselines. They therefore miss, or recognise late, famine in low-baseline populations.
- **Gaza.** The pre-October 2023 baseline was below 0.1 per 10,000/day. Reaching Phase 5 would need a more than 20-fold rise in non-trauma deaths, against a 6–7-fold rise in rural Somalia or South Sudan.
  - About 95% of Gaza was in Phase 3+ from Dec 2023 to Oct 2025.
  - The FRC delayed its determination for lack of mortality data.
  - The August 2025 Famine classification was "retracted" in mid-December 2025.
- **Historical evidence.**
  - In the Dutch Hunger Winter (March 1945), urban infant mortality reached about 3.4 per 10,000/day, roughly 4 times the pre-war level, and mortality at ages 1–4 rose 7-fold to 0.5 per 10,000/day. Both are below the IPC under-5 famine threshold.
  - Large relative rises often fell on ages 5–14, not on under-5s: USSR 1922, Greece 1941–44 and Darfur 1984–85.
  - Mortality lags food deprivation by about 3 months. Births fall sharply, by about 50% in the extreme-famine provinces of Ukraine.
- **Recommendation.** Systematically collect "more sensitive" early famine indicators, such as births, birthweight and relative rises by age group.
- **How it bears on us.**
  - **Agrees** that the IPC mortality bands are not calibrated, and that absolute thresholds are the wrong object; it argues for relative-to-baseline readings.
  - **Points in the opposite direction on Gaza.** Their worry is that the bands are *too insensitive* in a low-baseline urban population. Our worry is that in high-baseline rural Phase 3–4 populations, the bands *overstate* the mortality that the phase implies.
  - Both points follow from one fact: the bands are absolute while baselines and disease environments differ. We should say so explicitly, so that we are not read as arguing that famine is over-declared.
  - **Their remedy differs from ours.** They want earlier non-mortality indicators of starvation. We want more direct measurement of mortality and its health drivers.

**L2. Young, H. & Marshak, A. (2017; cover dated January 2018). *Persistent Global Acute Malnutrition: A discussion paper on the scope of the problem, its drivers, and recommendations for policy, practice, and research.* Feinstein International Center, Tufts University.** https://www.medbox.org/document/persistent-global-acute-malnutrition. Bib key: `youngmarshak2017` (already in the bib). [V-full in lit_phase_outcomes.md §3.1]
- **Key numbers.**
  - Kanem (Chad): GAM above 15% in 15 of 17 surveys, 1992–2015.
  - Northern Bahr el Ghazal: GAM above 15% in almost every survey from 2005 to 2014, "even when classified green on the IPC".
  - Food security "may not be the main driver" in persistent-GAM settings.
  - The named drivers are disease, WASH, livestock and milk, and care.
- **Debate it belongs to:** Debate 2 (malnutrition is not only about food).
- **How it bears on us:** this is the most direct precedent for (a) and part of (b) on the nutrition side. It is case-study based and does not quantify the phase–GAM gradient. We **extend** it with a cross-area, phase-level quantification.

**L3. IPC resource page c/1156988 = Lentz, E., Baylis, K., Michelson, H. & Kim, C. (May 2024). *IPC Accuracy Study: Analyzing the internal consistency of IPC AFI and AMN analyses.* IPC Global Support Unit.** https://www.ipcinfo.org/ipcinfo-website/resources/resources-details/en/c/1156988/ (read via Wayback snapshot of 29 Jul 2025). PDF: https://www.ipcinfo.org/fileadmin/user_upload/ipcinfo/docs/IPC_Accuracy_Study.pdf. Bib key: `lentz2024ipcaccuracy` (already in the bib). [V-full of the landing page this session; full PDF V-full in novelty_check.md C1]
- **What it is:** the first external accuracy study the IPC has commissioned, launched in 2022. Because IPC outcomes are "latent constructs", it says there is no true measure of accuracy, so it tests **internal consistency** against the Technical Manual 3.1.
- **Findings.**
  - Household food-security indicators are "not highly concordant".
  - Consensus severity is consistent with the manual.
  - Technical Working Groups (TWGs) on average **under-classify** the Phase 3+ population relative to reference points.
  - Treatment of indicators is "idiosyncratic", which raises comparability questions.
  - TWGs classify fewer people when indicators are noisier.
  - Projections show no systematic bias against later current analyses.
  - Acute malnutrition is covered only as a "proof of concept".
- **Recommendations:** review indicator thresholds, pair automated analysis with documentation, and repeat the study in five years.
- **How it bears on us.**
  - It is the IPC's own evaluation, and it **never validates phases against outcomes** (GAM or mortality). The only benchmark is the IPC's own manual.
  - That is the gap our argument fills, and it supports (e): the reform target is the IPC's definitions and reference table, which the accuracy study takes as given.
  - **Tension:** Lentz et al. (2025, *Nature Food*; `lentz2025`) push the other way, saying the IPC undercounts acute hunger. Our point is not about headcounts of the food insecure. It is about what the phases imply for deaths.

**L4. Maxwell, D., Adan, G., Hailey, P., Day, M.S., Odhiambo, S.B.J., Kaindi, L., Njiru, J., Venkat, A. & Marshak, A. (2023). "Using the household hunger scale to improve analysis and classification of severe food insecurity in famine-risk conditions: Evidence from three countries." *Food Policy* 118: 102449.** https://doi.org/10.1016/j.foodpol.2023.102449. This is ScienceDirect PII S0306919223000477, confirmed via the doi.org redirect. [V-abs: OpenAlex metadata, Feinstein newsroom summary 20 Jul 2023, Knowledge4Policy abstract extract; full text 403]
- **Data:** household surveys in seven severely food-insecure areas of South Sudan, Kenya and Somalia.
- **Question:** can the Household Hunger Scale (HHS) separate Phase 4 from Phase 5 and serve as an "anchor" indicator across the scale?
- **Answer:**
  - HHS performs "reasonably well" overall.
  - It **over-classifies severity, especially at the lower end of the scale**.
  - It flags very food-insecure households but may need more information to separate Phase 4 from Phase 5.
  - A few added questions or observations could help.
- **Context in the abstract:** common indicators "often produce very different prevalence estimates".
- **Debate it belongs to:** Debate 4 (IPC measurement), within the household-indicator tradition (Maxwell, Vaitla & Coates 2014; Vaitla et al. 2017).
- **How it bears on us.**
  - It shows how the IPC reform debate is framed by insiders: better *food* indicators for distinguishing Phase 4 from Phase 5.
  - It reinforces that the household indicators disagree with each other.
  - We argue that refining food-consumption measurement at the top of the scale is second-order if the welfare-relevant outcomes (wasting, deaths) are only loosely tied to the scale. The paper is a useful foil, not an opponent.

**L5. Luc, G., Keita, M., Bazongo, B., Diarra, B., Virchenko, A., Okley, C., Seyvet, T., Ngongang Mbunang, Y., Molla, D., Dujanovic, D., Nur, A., Marshak, A., Rahim, A. & Osman, A.M. (2024). "Special focus: Wasting patterns in Somalia." *Field Exchange* 72 (April 2024), Emergency Nutrition Network.** https://www.ennonline.net/fex/72/special-focus-wasting-patterns-somalia ; https://doi.org/10.6084/m9.figshare.25552191. Bib key: `luc2024fex` (defined in novelty_check.md, not yet in the cgd bib). [V-full of the ENN web text this session; ResearchGate 403]
- **Data:** FSNAU rural household surveys 2014–2021 (July and December rounds), 85,837 children aged 6–59 months in 27,520 households, plus ACF surveys, NDVI, ACLED and IPC.
- **Measures:** wasting is WHZ < −2. Food insecurity is the household Food Consumption Score (FCS).
- **Findings.**
  - Wasting and food insecurity both cluster at village level.
  - Wasting peaks twice, around **May/June and November**, and **declines during the lean season**, so it does not track the food-insecurity calendar.
  - Year-to-year variation in wasting 2014–21 is "minimal" compared with seasonal variation.
  - Boys are more vulnerable than girls.
  - No correlation coefficients are reported.
- **Recommendation:** "move beyond food-centred approaches".
- **Note:** the article itself does not analyse disease or WASH.
- **How it bears on us.**
  - It is the most direct Somalia precedent for our finding that GAM is weakly related to the food-insecurity phase and strongly related to the zone's own history. It works at household and village level with FCS, not with the area IPC phase.
  - We **extend** it to the classification itself.
  - The minimal year-to-year variation is consistent with our r = 0.66 with lagged GAM.

---

## Debate 1. Do famine victims die of starvation or of disease? (the "health crisis model")

**Core references**
- **de Waal, A. (1989). *Famine That Kills: Darfur, Sudan, 1984–1985.* Oxford: Clarendon Press.** Revised edition: Oxford University Press, 2005, https://doi.org/10.1093/oso/9780195181630.001.0001. [V-meta; argument V-abs from publisher and ALNAP summaries]
- **de Waal, A. (1989). "Famine mortality: a case study of Darfur, Sudan 1984–5." *Population Studies* 43(1): 5–24.** https://doi.org/10.1080/0032472031000143826 [V-abs]
  - The crude death rate (CDR) trebled to about 40 per 1,000.
  - Excess deaths were mostly a seasonal spike in *child* deaths from diarrhoea, measles and malaria.
  - Water supply predicted mortality differentials; wealth did not.
  - Excess mortality is explained by "severe localised health crises", which "conflicts with the established 'starvation model'".
  - People also went hungry deliberately to protect livelihoods (the book).
- **Mokyr, J. & Ó Gráda, C. (2002). "What do people die of during famines: the Great Irish Famine in comparative perspective." *European Review of Economic History* 6(3): 339–363.** https://doi.org/10.1017/S1361491602000163 [V-full of the Northwestern working-paper version]
  - The 1851 census reports only 20,402 starvation deaths for 1845–50. Most excess deaths in Ireland, Saratov 1918–22 and nineteenth-century India were from infection (fever, dysentery and diarrhoea, cholera, malaria). In Bengal 1943–44, malaria was the main killer.
  - **The key counterpoint:** in the well-documented European famines of the 1940s (the Warsaw ghetto, western Netherlands 1944–45, Greece 1941–42), *starvation* accounted for a large share and infection for relatively little.
  - The authors also cite Sudan camps in the mid-1980s: malaria 17%, diarrhoea 27% and respiratory disease 23% of deaths (Mercer 1992).
- **Ó Gráda, C. (2007). "Making famine history." *Journal of Economic Literature* 45(1): 5–38.** https://doi.org/10.1257/jel.45.1.5 [V-meta]. Also Ó Gráda (2009), *Famine: A Short History*, ch. 4 (`ograda2009famine`).
- **Sen, A. (1981). *Poverty and Famines*** (`sen1981poverty`). Entitlement failure, not food availability decline. Sen is about *why people lose access to food*. De Waal's critique is that Sen still assumes deaths follow from that lost access.
- **de Waal, A. (2018). *Mass Starvation*** (`deWaal2018mass`). Updated history: famine deaths collapsed after the 1980s, and modern famines are mostly man-made and political.
- **Young, H. & Jaspars, S. (1995). "Nutrition, disease and death in times of famine." *Disasters* 19(2): 94–109.** https://doi.org/10.1111/j.1467-7717.1995.tb00361.x [V-abs]
  - The malnutrition–mortality association is strong in camps but varies "considerably" across places and times, mainly because of the "prevailing patterns of morbidity".
  - A degraded health environment "raise[s] the threshold of nutritional status" associated with higher mortality risk.

**What was argued**
- De Waal overturned the "starvation model", in which famine deaths are caused by malnutrition from lack of food. He replaced it with a "health crisis model": social disruption, migration, crowding and bad water spread infectious disease, and the excess deaths are mostly children dying of diarrhoea, measles and malaria.
- Economic historians (Mokyr & Ó Gráda; Dyson; Maharatna) found the same disease-dominated profile in pre-antibiotic Ireland, India and Russia. The exception is urban European famines with good sanitation, where literal starvation dominated.

**Where it stands**
- This is now consensus in humanitarian public health. It is restated in the Sphere standards, Salama et al. (2004), Checchi's mortality work and de Waal (2018).
- The live controversy has moved to **settings where starvation proper matters**: Gaza and besieged cities, where baselines are low and WASH was initially good. There, the Mokyr–Ó Gráda European pattern may apply. De Zwarte et al. (2026) invoke exactly these European famines.

**How our argument relates**
- **(b) restates de Waal**, applied to the IPC era. It is 35 years old, so it should be cited as the intellectual origin, not presented as a new insight.
- **What is new** is the quantitative link to the *classification system*. If deaths are health-driven, a scale built on food consumption will be a poor predictor of them, and we show that it is.
- **Caveat to add:** the health-crisis model is context-dependent. In low-disease-baseline, siege-type settings (Gaza, possibly El Fasher) the food channel may dominate. Our argument is strongest for rural, high-disease-burden Africa, where most IPC Phase 3+ people live.

---

## Debate 2. Malnutrition is not (only) about food: what does wasting measure?

**Core references**
- **UNICEF (1990). *Strategy for Improved Nutrition of Children and Women in Developing Countries.* UNICEF Policy Review E/ICEF/1990/L.6. New York: UNICEF.** [V-meta from memory and secondary citations; NV for exact document number]
  - The original conceptual framework: immediate causes (inadequate dietary intake *and* disease); underlying causes (household food security, care, health services and a healthy environment); basic causes.
- **UNICEF (2020). *UNICEF Conceptual Framework on Maternal and Child Nutrition.*** https://www.unicef.org/documents/conceptual-framework-nutrition [V-meta]. An update that keeps diets and care as immediate determinants, with "food, practices and services" as underlying ones.
- **Young, H. & Jaspars, S. (1995). "Nutritional assessments, food security and famine." *Disasters* 19(1): 26–36.** https://doi.org/10.1111/j.1467-7717.1995.tb00330.x [V-abs]
  - Malnutrition is not simply a late indicator of famine.
  - In late famine, health-environment collapse shifts the risk–nutrition relationship.
  - Nutrition surveys should analyse *causes*, not just prevalence.
- **Young, H. & Jaspars, S. (2006). *The Meaning and Measurement of Acute Malnutrition in Emergencies: A Primer for Decision-Makers.* HPN Network Paper 56. London: ODI.** https://odihpn.org/publication/the-meaning-and-measurement-of-acute-malnutrition-in-emergencies-a-primer-for-decision-makers/ ; PDF mirror https://www.unhcr.org/au/sites/en-au/files/legacy-pdf/45f6c16f2.pdf [V-abs]
  - GAM prevalence is "one of the most widely used indicators of the severity of humanitarian crises".
  - The paper warns against reading it without causal analysis.
- **Young, H. & Jaspars, S. (2009). *Review of Nutrition and Mortality Indicators for the IPC*** (`youngjaspars2009`; see lit_phase_outcomes §4.2).
- **Young, H., Borrel, A., Holland, D. & Salama, P. (2004). "Public nutrition in complex emergencies." *The Lancet* 364(9448): 1899–1909.** https://doi.org/10.1016/S0140-6736(04)17447-3 [V-meta]
  - The "public nutrition" approach links food, health and care, and moves beyond feeding programmes.
- **Marshak, A., Young, H., Bontrager, E.N. & Boyd, E.M. (2017). "The relationship between acute malnutrition, hygiene practices, water and livestock, and their program implications in eastern Chad." *Food and Nutrition Bulletin* 38(1): 115–127.** https://doi.org/10.1177/0379572116681682 [V-abs]
- **Already covered elsewhere, not repeated:**
  - Young & Marshak 2017 (L2); Luc et al. 2023 and 2024 (L5); Venkat et al. 2023 seasonality (`venkat2023seasonality`); Moradi et al. 2019 (wasting OR 1.04); Maitra 2018 (3 of 15 wasting studies positive); McDonald 2017 (FEWS NET Niger nutrition causal analysis); Kinyoki et al. 2015.
  - See lit_phase_outcomes §3 and novelty_check D.
- **Measurement sub-debate (WHZ vs MUAC).**
  - Grellety, E. & Golden, M.H. (2016). "Weight-for-height and mid-upper-arm circumference should be used independently to diagnose acute malnutrition: policy implications." *BMC Nutrition* 2: 10. https://doi.org/10.1186/s40795-016-0049-7 [V-meta]
  - Bilukha & Leidman (2018) find ρ = 0.55 between the two prevalences (lit_phase_outcomes §3.12).
  - This matters for the FRCs, which now accept MUAC ≥ 15% as a famine proxy (Gaza 2025, Sudan 2024).
- **Counter-evidence (food matters at the margin).**
  - Isanaka, S. et al. (2009). "Effect of preventive supplementation with ready-to-use therapeutic food on the nutritional status, mortality, and morbidity of children aged 6 to 60 months in Niger." *JAMA* 301(3): 277–285. https://doi.org/10.1001/jama.2008.1018 [V-meta]
  - Langendorf et al. 2014 (`langendorf2014preventing`); the cash–wasting RCTs (lit_shocks_nutrition.md).

**What was argued**
- Since the UNICEF framework (1990), nutritionists have agreed that wasting has two immediate causes, intake and disease, and many underlying ones.
- The Tufts/Feinstein school (Young, Jaspars, Marshak) has argued for 30 years that humanitarian practice nonetheless treats high GAM as a food problem calling for food aid. They point to persistent GAM in Chad, Darfur and South Sudan that does not respond to food aid or harvests.

**Where it stands**
- The conceptual point is uncontested.
- The **operational** debate is live. IPC created a separate Acute Malnutrition (AMN) scale in 2016 precisely because AFI and AMN "do not always match" (`ipc2016amn`, `ipc2024linkages`).
- FEWS NET's 2018 guidance tells analysts *not* to use disease-driven malnutrition as AFI evidence (`fewsnet2018nutmort`). The system has therefore acknowledged the disconnect by decoupling the scales, not by changing what drives resource allocation.

**How our argument relates**
- **(a) on GAM restates** the Feinstein position and the IPC's own 2016 rationale.
- **We extend it** by quantifying the gradient across all classified areas (Somalia r = 0.10 vs 0.66).
- We also draw the allocation implication. The IPC's response was to build a second scale, but funding headlines (the GRFC "people in Phase 3+") and agency targeting still run on the AFI scale.
- We should **cite this tradition generously**. Young, Jaspars and Marshak are likely reviewers, and they will see (a) and (b) as their own argument.

---

## Debate 3. Food-first response: does humanitarian money follow food insecurity rather than mortality risk?

**Core references**
- **Darcy, J. & Hofmann, C.-A. (2003). *According to Need?*** (`DarcyHofmann2003`, HPG Report 15).
  - Needs assessments are often shaped to justify pre-chosen responses, especially food aid. There is no common metric of severity across sectors.
  - Darcy and Hofmann call for mortality and malnutrition as cross-sectoral "outcome" indicators.
  - Already summarised in lit_humanitarian_data.md §5.
- **Barrett, C.B. & Maxwell, D.G. (2005). *Food Aid After Fifty Years: Recasting Its Role.* London: Routledge.** [V-meta]. Food aid driven by donor surplus and institutional inertia rather than need.
- **Barrett, C.B. (2010). "Measuring food insecurity." *Science* 327(5967): 825–828.** https://doi.org/10.1126/science.1182768 [V-meta]
- **Maxwell, D., Stobaugh, H., Parker, J. & McGlinchy, M. (2013). *Response Analysis and Response Choice in Food Security Crises: A Roadmap.* HPN Network Paper 73. London: ODI.** [V-meta; author list and number from memory, check before citing]. The literature on "response analysis": choosing a modality after assessment, rather than defaulting to food.
- **Spiegel, P.B., Checchi, F., Colombo, S. & Paik, E. (2010). "Health-care needs of people affected by conflict: future trends and changing frameworks." *The Lancet* 375(9711): 341–345.** https://doi.org/10.1016/S0140-6736(09)61873-0 [V-meta]
  - Future crises will be more urban and protracted, with more non-communicable disease (NCD). Health responses must move beyond the camp model.
- **Lancet series "Health in humanitarian crises" (2017).**
  - Spiegel, P.B. (2017). "The humanitarian system is not just broke, but broken: recommendations for future humanitarian action." *The Lancet* (online 8 June 2017). https://doi.org/10.1016/S0140-6736(17)31278-3 [V-meta]
  - Blanchet, K., Ramesh, A., Frison, S., Warren, E., Hossain, M., Smith, J. et al. (2017). "Evidence on public health interventions in humanitarian crises." *The Lancet* 390(10109): 2287–2296. https://doi.org/10.1016/S0140-6736(16)30768-1 [V-meta]
  - Checchi et al. (2017) (`Checchi2017Lancet`): minimal public-health information was timely "only in a small minority" of crises.
- **Salama, P., Assefa, F., Talley, L., Spiegel, P., van der Veen, A. & Gotway, C.A. (2001). "Malnutrition, measles, mortality, and the humanitarian response during a famine in Ethiopia." *JAMA* 286(5): 563–571.** https://doi.org/10.1001/jama.286.5.563 [V-abs; DOI confirmed via Crossref]
  - Gode, 2000: CDR 3.1 (95% CI 2.4–3.8), U5DR 6.7.
  - Measles, alone or combined with malnutrition, accounted for 22% of under-5 deaths.
  - A measles campaign was not mounted until August 2000, after the bulk of food aid.
  - This is the canonical case of a food-focused response missing the killer.
- **Funding shares by sector (OCHA FTS).** My pull of the FTS public API (`/v1/public/fts/flow?groupby=globalcluster`), 14 Oct 2026. Shares of reported funding with a cluster tag:

| Year | Total ($bn) | Food Security | Health | Nutrition | WASH |
|---|---|---|---|---|---|
| 2019 | 23.0 | 28% | 6% | 6% | 3.5% |
| 2022 | 39.2 | 33% | 14% | 5.6% | 3.9% |
| 2024 | 34.7 | 29% | 10% | 5% | 4.3% |

  - The 2022 health share is inflated by COVID and Ukraine.
  - Food Security is consistently the single largest cluster, receiving 2–5 times as much as Health and 7–9 times as much as WASH.
  - **Caveat:** "Not specified" and "Multi-sector" absorb 15–35%, flows can be multi-tagged, and shares of *requirements* or *coverage* were not pulled.

**What was argued**
- A long ODI/HPG critique, from Darcy & Hofmann (2003) through the Response Analysis work, holds that assessments are supply-driven and that food aid is the default response.
- The public-health literature (Toole & Waldman, Salama, Spiegel, Checchi) has argued since 1990 that the measures that cut mortality are measles vaccination, WASH, diarrhoea and malaria case management, and selective feeding, with general rations as one item among several.
- The MSF "Refugee Health" ten priorities (1997) put food fourth, after assessment, measles immunisation and water/sanitation.

**Where it stands**
- The critique is accepted rhetorically. Cash has largely displaced in-kind food (Barrett & Maxwell's agenda won), but food security is still the largest funding line.
- The 2025–26 "hyper-prioritisation" exercises rank by IPC severity and people in need, and so **still channel through the food-security lens**.
- Health and WASH remain the chronically underfunded clusters.

**How our argument relates**
- **(b) and (c) extend this debate with a new lever.** Earlier critiques blamed agency mandates and donor surplus. We point to the *information system*: the dominant severity metric (IPC AFI) is food-based, so prioritisation inherits a food-first bias even when the modality is cash.
- To our knowledge no one has tied the funding-share critique to the classification system's weak link with mortality. That is the paper's contribution here.
- **Do not overclaim** that food aid does not save lives. Somalia 2011, Checchi & Robinson's WFP-presence effect and the terms-of-trade effect show it does at the extreme (lit_phase_outcomes §2.1).

---

## Debate 4. Critiques of the IPC: politics, consensus, thresholds and famine declarations

**Core references (new here)**
- **Howe & Devereux (2004)** (`HoweDevereux2004`). The intellectual origin of an instrumental, threshold-based definition of famine. Its intensity scale used CDR and wasting cut-offs (lit_phase_outcomes §4.7).
- **Hillbruner & Moloney (2012)** (`hillbruner2012`) and **Maxwell & Fitzpatrick (2012)** (`maxwell2012`). Somalia 2011: "when early warning is not enough". The warning was accurate; the failure was response.
- **Maxwell & Hailey (2020, 2021)** (`maxwell2020pia`, `maxwell2021`). Politics of information: governments and agencies contest IPC numbers, and consensus is negotiated.
- **Maxwell, Khalif, Hailey & Checchi (2020).** "Determining famine: multi-dimensional analysis for the twenty-first century." *Food Policy* 92: 101832 (`Maxwell2020determining`). Argues for a multi-dimensional famine determination, as in the FRC "reasonable evidence" standard.
- **Buchanan-Smith, M., Cocking, J. & Sharp, S. (2021). *Independent Review of the IPC South Sudan.* HPG commissioned report. London: ODI.** https://cdn.odi.org/media/documents/ODI_HPG_IPC_South_Sudan_report_final_BXOKlof.pdf [V-abs]
  - The Oct/Nov 2020 South Sudan analysis broke down when the Technical Working Group (TWG) could not agree on six counties, including Pibor.
- **Buchanan-Smith, M., Cocking, J. & Moallin, Z. (2023). *Independent Review of the Integrated Food Security Phase Classification (IPC) in Somalia.* HPG commissioned report. London: ODI.** https://odi.org/en/publications/independent-review-of-the-ipc-in-somalia/ [V-abs]
  - Launched June 2023 after concerns from five donor agencies.
  - A *process* review covering consensus, communication and governance, not a technical one.
- **Maxwell et al. (2023), HHS** (L4). **Lentz et al. (2024) Accuracy Study** (L3). **Lentz et al. (2019)** (`lentz2019`) and **(2025)** (`lentz2025`). **Michelson et al. (2026)** (novelty_check C2).
- **Household measurement:** Maxwell, Vaitla & Coates (2014) (`maxwell2014`); Vaitla et al. (2017) (`vaitla2017`). Food-security indicators correlate only modestly with each other.
- **Famine Review Committee controversies, 2024–26.**
  - IPC FRC (4 June 2024). *FEWS NET Gaza analysis review.* https://www.un.org/unispal/wp-content/uploads/2024/06/IPC_Famine_Review_Committee_Report_Gaza_June2024.pdf [V-abs]
    - The FRC did **not find FEWS NET's May 2024 analysis "plausible"**. FEWS NET had judged it "possible, if not likely" that famine was occurring in North Gaza in April. The FRC cited "uncertainty and lack of convergence of the supporting evidence".
  - Gaza: Famine classified in August 2025 (`IPC2025Gaza`) and downgraded in December 2025 (de Zwarte et al. 2026; lit_humanitarian_data §2).
  - Sudan FRC 2024 (`FRC2024Sudan`, `ipcfrc2024sudandec`). Famine in Zamzam was found on MUAC and partial mortality data. The government withdrew from the IPC in December 2024.
  - De Zwarte et al. (2026) (L1).

**What was argued**
Three strands:
- **Politics and governance** (Maxwell & Hailey; Buchanan-Smith reviews). Consensus breaks down, and governments suppress or contest results.
- **Measurement** (Lentz et al.; Maxwell–Vaitla–Coates; HHS). Household indicators disagree, and TWGs under-classify.
- **Famine thresholds** (Howe & Devereux; Young & Jaspars 2009, who recommended raising the Famine CDR cut-off back to 5; de Zwarte et al., who say the cut-offs are too insensitive for low-baseline populations). Much of the 2024–26 public fight was over whether there was *enough mortality data* to declare famine.

**Where it stands**
- The IPC has absorbed the critiques procedurally: FRCs, the "reasonable evidence" standard, the separate AMN scale, the Accuracy Study and the HHS work.
- **No critique tests whether phases predict outcomes.** Every one takes the reference table as the standard and asks whether analysts apply it consistently or politically. The FRC debates treat mortality as *evidence for* classification, never as the *object the classification should predict*.

**How our argument relates**
- **(a) and (e) are new relative to this debate.** We are not saying the IPC is political or inconsistently applied. We are saying the scale is weakly related to the outcomes it is implicitly used to rank, even when applied correctly.
- The Gaza June 2024 episode supports (e) in an unexpected way: on the same data, FEWS NET and the IPC FRC disagreed. That shows the classification *rules*, not the forecaster, are what bind.
- **Risk:** the threshold critique is politically charged (Gaza, Sudan). We should state that our critique is about the Phase 3–4 bulk of the distribution, where most deaths occur (LSHTM 2023), and not about famine declaration.

---

## Debate 5. Measuring mortality in crises: ad hoc surveys, surveillance or models?

**Core references (new here)**
- **Checchi, F. & Roberts, L. (2008). "Documenting mortality in crises: what keeps us from doing better?" *PLoS Medicine* 5(7): e146.** https://doi.org/10.1371/journal.pmed.0050146 [V-meta]. Companion to the 2005 HPN primer (`checchiroberts2005`).
- **Prudhon, C. & Spiegel, P.B. (2007). "A review of methodology and analysis of nutrition and mortality surveys conducted in humanitarian emergencies from October 1993 to April 2004." *Emerging Themes in Epidemiology* 4: 10.** https://doi.org/10.1186/1742-7622-4-10 [V-meta]. Survey quality was poor before the SMART methodology.
- **Spiegel, P.B., Salama, P., Maloney, S. & van der Veen, A. (2004). "Quality of malnutrition assessment surveys conducted during famine in Ethiopia." *JAMA* 292(5): 613–618.** https://doi.org/10.1001/jama.292.5.613 [V-meta; co-authors from memory]
- **SMART (2006). *Measuring Mortality, Nutritional Status, and Food Security in Crisis Situations: SMART Methodology*, Version 1.** [V-meta]. Standardised the cluster survey that underlies most GAM and CDR data used in IPC/AMN.
- **Heudtlass, P., Speybroeck, N. & Guha-Sapir, D. (2016)**, *Conflict and Health* 10: 15 (see Debate 7). Uses the CE-DAT operational database.
- **Checchi et al. 2017 Lancet; 2022 small-area estimation; 2022 malnutrition prediction; Checchi & Robinson 2013.** Covered in lit_phase_outcomes §2. Keys `Checchi2017Lancet`, `checchi2022sae`, `checchi2022malnut`, `checchi2013`.
- **Ratnayake et al. 2025 (S-MED)** (`ratnayake2025smed`) and **Palmer et al. 2025** (`Palmer2025mortality`). Real-time Somalia mortality database; politics of measuring mortality.
- **Recent calls for mortality counting.**
  - Khatib, R., McKee, M. & Yusuf, S. (2024). "Counting the dead in Gaza: difficult but essential." *The Lancet* 404(10449): 237–238. https://doi.org/10.1016/S0140-6736(24)01169-3 [V-meta]. Indirect deaths could be several times direct deaths.
  - Dahab, M. et al. (2024). "War-time mortality in Sudan: a capture-recapture analysis." Preprint, Sudan Research Group / LSHTM, Nov 2024. https://www.lshtm.ac.uk/newsevents/news/2024/invisible-and-severe-death-toll-sudan-conflict-revealed [V-abs: press coverage; full author list NV]. About 61,000 deaths in Khartoum State in 14 months, 26,000 of them violent.
  - De Zwarte et al. (2026) (L1).
- **Conflict-deaths sub-debate (direct vs indirect).**
  - Coghlan, B. et al. (2006). "Mortality in the Democratic Republic of Congo: a nationwide survey." *The Lancet* 367(9504): 44–51. https://doi.org/10.1016/S0140-6736(06)67923-3 [V-meta]. The IRC 3.9m, and later 5.4m, excess-death estimates are mostly from disease.
  - Human Security Report Project (2011). *Human Security Report 2009/2010: The Causes of Peace and the Shrinking Costs of War.* New York: Oxford University Press. [V-abs from press coverage]. Argues the IRC baseline was too low.
  - Geneva Declaration Secretariat (2008). *Global Burden of Armed Violence.* Geneva. https://www.smallarmssurvey.org/sites/default/files/resources/GBAV_fullreport.pdf [V-abs]. At least 200,000 indirect conflict deaths a year against 52,000 direct, a rough 4:1 ratio.
  - Degomme, O. & Guha-Sapir, D. (2010). "Patterns of mortality rates in Darfur conflict." *The Lancet* 375(9711): 294–300. https://doi.org/10.1016/S0140-6736(09)61967-X [V-abs]. About 298,000 excess deaths (95% CI 178,000–462,000), 2003–08; more than 80% were **not** violent, mainly diarrhoea in displaced populations.
  - Depoortere, E., Checchi, F. et al. (2004). "Violence and mortality in West Darfur, Sudan (2003–04): epidemiological evidence from four surveys." *The Lancet* 364(9442): 1315–1320. https://doi.org/10.1016/S0140-6736(04)17187-0 [V-meta]

**What was argued**
- From the 1990s through the 2000s, crisis mortality was measured by retrospective cluster surveys of variable quality (Prudhon & Spiegel; Spiegel 2004). SMART (2006) standardised them.
- Checchi and Roberts argued that surveys are too sparse, late and unrepresentative. They pushed prospective surveillance and, later, statistical small-area estimation (LSHTM).
- A parallel fight over DRC, Darfur and Iraq numbers made "excess mortality" politically toxic. Disputes over baselines (HSRP vs IRC) recur in every big estimate.

**Where it stands**
- There is consensus that data are too thin. Checchi et al. (2017) found essential information timely in only a small minority of crises. The 2025 US aid cuts made this worse (DHS, FEWS NET pause, ACF "No data, no response"; lit_humanitarian_data §2).
- Somalia's S-MED and the LSHTM model estimates are the frontier, but they are retrospective, and in them IPC phase is not a predictor (lit_phase_outcomes §2).
- Real-time mortality surveillance is still mostly an aspiration outside camps.

**How our argument relates**
- **(c) restates the Checchi/Roberts call for more and better mortality data.**
- **It extends that call** in two ways:
  - It frames surveys as a *forecasting input* with allocative value: lagged GAM predicts GAM (r = 0.66), and surveys plus covariates predict mortality, so more surveys mean better targeting. The earlier literature makes the case for surveys mainly as advocacy, accountability and evidence for classification.
  - It makes an explicit value-of-information or cost-benefit case (survey_costs.md) that the mortality-measurement literature does not.
- **Note the tension with Checchi et al. (2022).** Covariate models of GAM performed "disappointingly", so the case for (c) rests on survey *frequency* (autocorrelation; Constenla-Villoslada et al. 2025) more than on rich covariate models.
- The direct-vs-indirect conflict-deaths literature (DRC, Darfur) is strong independent support for (b): even in the most violent conflicts, most excess deaths are disease deaths among the displaced and residents.

---

## Debate 6. Early warning, early action and the value of information

**Core references**
- **Coughlan de Perez, E., van den Hurk, B., van Aalst, M.K., Jongman, B., Klose, T. & Suarez, P. (2015). "Forecast-based financing: an approach for catalyzing humanitarian action based on extreme weather and climate forecasts." *Natural Hazards and Earth System Sciences* 15(4): 895–904.** https://doi.org/10.5194/nhess-15-895-2015 [V-meta]
- **Gros, C. et al. (2019). "Household-level effects of providing forecast-based cash in anticipation of extreme weather events: quasi-experimental evidence from humanitarian interventions in the 2017 floods in Bangladesh." *International Journal of Disaster Risk Reduction* 41: 101275.** https://doi.org/10.1016/j.ijdrr.2019.101275 [V-meta]
- **Christian, P., Dunsch, F., Heirman, J., Kelley, E., Kondylis, F., Lane, G. et al. (2025). "Fast action for floods: RCT evidence on forecast-based cash transfers from Bangladesh and Nepal." NBER Working Paper 34414.** https://doi.org/10.3386/w34414 [V-meta]
- **Already in the bib, not repeated:** Pople et al. (2026) (`pople2026early`); Cabot Venton et al. (2012) (`cabotventon2012economics`); Maxwell, Day & Hailey (2023) on whether famine declarations raise funding (`MaxwellDayHailey2023`); Hillbruner & Moloney (2012); Coughlan de Perez et al. (2019) (`coughlandeperez2019rain`); Clarke & Dercon (2016) *Dull Disasters?* [NV for bib].
- **Coverage of nutrition programmes (CMAM):** Rogers et al. (2015) (`rogers2015coverage`), median SAM programme coverage below 40% in 21 countries; Isanaka et al. (2021) incidence correction (`isanaka2021icf`).

**What was argued**
- The anticipatory-action literature, from Start Network, OCHA/CERF, IFRC and the World Bank FAM, argues that acting on forecasts is cheaper and more effective than reacting.
- Its evidence base is mostly floods, with cash to households; the outcomes are consumption, assets and wellbeing.
- The food-crisis version (Somalia 2011; Maxwell & Hailey) stresses that warnings were accurate but response was late. The bottleneck is political will, not information.

**Where it stands**
- Anticipatory action is mainstream: CERF AA frameworks, OCHA pilots.
- There is still little evidence on **mortality or child-nutrition outcomes** of anticipatory food-crisis action.
- No formal value-of-information analysis of *outcome surveys* for targeting appears in this literature. The closest are the predictive-model papers (Constenla-Villoslada et al. 2025; Checchi et al. 2022) and the WFP "cost of inaction" studies.

**How our argument relates**
- **(c) extends the early-warning literature in a new direction.** That literature asks whether forecasts of *food insecurity* trigger action. We ask whether action is targeted at the *outcome* that matters.
- Hillbruner & Moloney's "early warning is not enough" is consistent with us: the problem is not forecast skill (FEWS NET is decent), but what is forecast and how it maps to deaths.
- **Novel:** a VOI framing that treats nutrition/mortality surveys as the scarce input.

---

## Debate 7. Camps vs everywhere else: where do crisis deaths happen?

**Core references**
- **Toole, M.J. & Waldman, R.J. (1990). "Prevention of excess mortality in refugee and displaced populations in developing countries." *JAMA* 263(24): 3296–3302.** https://doi.org/10.1001/jama.1990.03440240086021 [V-abs]
  - CDRs in the acute phase reached up to about 60 times expected.
  - Excess deaths were concentrated among children aged 1–14.
  - Measles, diarrhoea, acute respiratory infection (ARI) and malaria were the main killers, made deadlier by malnutrition.
  - Relief often failed on basic food, water, sanitation and measles immunisation.
  - Their "doubling of baseline" is the origin of the CDR 1 emergency threshold that the IPC inherited (lit_phase_outcomes §4.2).
- **Toole, M.J. & Waldman, R.J. (1997). "The public health aspects of complex emergencies and refugee situations." *Annual Review of Public Health* 18: 283–312.** https://doi.org/10.1146/annurev.publhealth.18.1.283 [V-abs]. African CDRs reached as high as 80 times baseline, with the same four killers.
- **Moore, P.S., Marfin, A.A., Quenemoen, L.E., Gessner, B.D., Miller, D.S., Toole, M.J. et al. (1993). "Mortality rates in displaced and resident populations of central Somalia during 1992 famine." *The Lancet* 341(8850): 935–938.** https://doi.org/10.1016/0140-6736(93)91223-9 [V-meta]
- **Goma Epidemiology Group (1995). "Public health impact of Rwandan refugee crisis: what happened in Goma, Zaire, in July, 1994?" *The Lancet* 345(8946): 339–344.** https://doi.org/10.1016/S0140-6736(95)90338-0 [V-meta]. Cholera and dysentery killed about 50,000 in a month, the defining camp disaster.
- **Médecins Sans Frontières (1997). *Refugee Health: An Approach to Emergency Situations.* London: Macmillan.** [V-meta]. The "ten priorities".
- **Salama, P., Spiegel, P., Talley, L. & Waldman, R. (2004). "Lessons learned from complex emergencies over past decade." *The Lancet* 364(9447): 1801–1813.** https://doi.org/10.1016/S0140-6736(04)17405-9 [V-abs]
  - Responses improved, "especially inside camps", and SAM case-fatality fell.
  - The authors call for renewed attention to ARI, diarrhoea, malaria, measles, neonatal causes and malnutrition in conflict-affected populations, deaths that "occur outside camps" and across regions and borders.
- **Heudtlass, P., Speybroeck, N. & Guha-Sapir, D. (2016). "Excess mortality in refugees, internally displaced persons and resident populations in complex humanitarian emergencies (1998–2012) – insights from operational data." *Conflict and Health* 10: 15.** https://doi.org/10.1186/s13031-016-0082-9 [V-abs]
  - 1,759 CE-DAT CDR estimates. Median ratio to baseline:
    - refugees **0.94** (not different from host baseline);
    - IDPs **2.5**;
    - residents **1.51**.
  - Non-violent (infectious) excess deaths outnumber violent ones "even in exceptionally brutal conflicts".
- **Spiegel et al. (2010)** (Debate 3). The shift to urban, non-camp and protracted settings.
- **UNHCR (2009). *UNHCR Policy on Refugee Protection and Solutions in Urban Areas.* Geneva.** [V-abs: secondary]. About one-third of refugees live in camps. See also UNHCR (2014) *Policy on Alternatives to Camps* [V-meta].
- **LSHTM (2023)** (`lshtm2023somalia`). "Most deaths ... do not occur in the relatively small pockets categorized as ... IPC phase 5, but in the much larger sections of the population exposed to IPC phases 3 and 4."
- **Degomme & Guha-Sapir (2010)** (Debate 5). Displacement raised diarrhoea mortality in Darfur.

**What was argued**
- The 1980s–90s evidence base (CDC/Epicentre camp surveys, Toole & Waldman) was built in camps. The IPC mortality and GAM reference levels come from it (Young & Jaspars 2009).
- From the early 2000s, Salama et al. and Spiegel et al. argued that the burden had moved outside camps, and that camp populations served by agencies often do *better* than residents. Heudtlass et al. confirm this: refugees sit at about baseline.
- De Waal's Darfur and Ethiopia work adds that relief camps themselves concentrated disease.

**Where it stands**
- Public-health consensus accepts that most displaced people live outside camps and that resident populations carry a large share of excess deaths.
- Operationally, though:
  - SMART and FRC evidence still comes disproportionately from IDP camps and sites (Zamzam 2024, Baidoa IDPs 2022, Mogadishu IDPs 2011).
  - Access constraints push measurement and delivery toward reachable sites.
  - Famine findings are often camp-based.

**How our argument relates**
- **(d) largely restates** Salama et al. (2004) and Heudtlass et al. (2016). Cite them rather than present (d) as new.
- **The new part** is the link to the IPC: its mortality bands are calibrated on 1980s–90s camp data, while the IPC is applied to whole rural livelihood zones whose baselines and death profiles differ. That is one reason the bands are too steep for Phase 3–4 populations (a).
- We should also note that our survey data are partly camp-weighted (FSNAU IDP strata).

---

## Additional debates worth flagging

**A. Should malnutrition prevalence be an early or late famine indicator?** (Young & Jaspars 1995a; Howe & Devereux 2004; FEWS NET 2018 guidance)
- IPC treats GAM as a Phase 5 criterion, alongside food consumption and CDR. FEWS NET tells analysts to use GAM as AFI evidence only when food consumption explains it.
- Our finding that GAM is weakly tied to the AFI phase is consistent with the FEWS NET rule. It also implies that the IPC's "two of three" famine rule combines indicators that do not co-move.

**B. Absolute vs relative thresholds** (Checchi & Roberts 2005; Checchi 2018 for the Global Health Cluster; Sphere regional baselines; de Zwarte et al. 2026)
- The IPC's Phase 4 band already says CDR 1–2 "or > 2× reference". Phase 3 and 5 do not use a relative form.
- Our evidence that south-central Somalia's *no-crisis* CDR (0.5–0.8) already sat in the Phase 3 band is the same point as de Zwarte's Gaza point, mirrored. **Use both** to argue for baseline-relative excess-mortality bands.

**C. Food-availability vs entitlement vs health** (Sen 1981; de Waal 1989; Devereux 2009)
- Devereux, S. (2009). "Why does famine persist in Africa?" *Food Security* 1(1): 25–35. https://doi.org/10.1007/s12571-008-0005-8 [V-meta]. Contemporary famines are mainly about political failure.
- Our (b) is closer to de Waal's health model than to Sen. That is worth saying in one sentence, since economists will read through Sen.

---

## Where we are restating vs where we are novel

**Restating; cite the originals prominently**
- (b) Crisis deaths are mostly disease deaths. This is de Waal (1989); Toole & Waldman (1990, 1997); Mokyr & Ó Gráda (2002); Salama et al. (2001, 2004); Degomme & Guha-Sapir (2010); Heudtlass et al. (2016).
- (a, GAM half) Wasting is driven by more than food, and AFI and AMN diverge. This is the UNICEF framework (1990); Young & Jaspars (1995, 2006, 2009); Young & Marshak (2017); Luc et al. (2023, 2024); and the IPC's own 2016 and 2024 documents.
- (c, partly) The call for more mortality and nutrition data is Checchi & Roberts (2005, 2008); Checchi et al. (2017); the S-MED team; ACF (2025); Bauer & Chia (2026).
- (d) Deaths are mostly outside camps. This is Salama et al. (2004); Spiegel et al. (2010); Heudtlass et al. (2016).
- The IPC CDR bands are uncalibrated. This is Young & Jaspars (2009) and de Zwarte et al. (2026). Our addition is the evidence that they are too steep *in Phase 3–4*, not merely uncalibrated.

**Plausibly novel**
1. A cross-area quantification of how weakly the AFI phase predicts measured GAM and mortality, alongside the zone's own lagged outcome. See novelty_check.md: nobody has done this systematically.
2. Locating the food-first bias in **the classification system**. Earlier critiques located it in agency mandates or donor surplus food. The point holds even after the shift to cash, and even in "hyper-prioritisation".
3. A **value-of-information** case for scheduled outcome surveys as a targeting input within fixed budgets, rather than as advocacy or accountability evidence.
4. **(e) IPC, not FEWS NET, as the reform target.**
   - The IPC-critique literature is about politics, consensus and internal consistency.
   - The FEWS NET literature is about forecast accuracy against the IPC.
   - No one has argued that a good forecaster of a poorly specified target is the wrong place to intervene. The Gaza June 2024 FEWS NET–FRC disagreement is a useful illustration.
5. A unified reading of the threshold debate. The IPC bands are absolute and camp-derived, so they are too insensitive in low-baseline urban sieges (de Zwarte et al.) and too steep for high-baseline rural Phase 3–4 populations (us).

**Where we may be contested**
- **The Feinstein school** will say this is their argument. Pre-empt by citing it and positioning our work as quantification and an allocation argument.
- **The IPC GSU** will say the AMN scale already handles malnutrition. Answer: the AMN scale does not drive the headline numbers or prioritisation.
- **Famine and Gaza advocates** may read us as saying famine is over-declared. Make clear the claim concerns Phase 3–4 bulk mortality.
- **Food-aid defenders** will point to Somalia 2011 and the RUTF/cash–wasting RCTs. Concede that food matters at the extreme and at the margin.
- **Checchi et al. (2022)** found covariate models of GAM "not usable for action". Our (c) must rest on survey frequency and autocorrelation, not on rich models.

---

## BibTeX

**Reused keys already in `output/cgd_paper/references.bib`** (do not redefine):
`deZwarte2026Lancet`, `youngmarshak2017`, `youngjaspars2009`, `lentz2024ipcaccuracy`, `lentz2025`, `lentz2019`, `sen1981poverty`, `ograda2009famine`, `deWaal2018mass`, `DarcyHofmann2003`, `Checchi2017Lancet`, `checchi2022sae`, `checchi2022malnut`, `checchi2013`, `checchiroberts2005`, `ratnayake2025smed`, `Palmer2025mortality`, `lshtm2023somalia`, `HoweDevereux2004`, `hillbruner2012`, `maxwell2012`, `maxwell2020pia`, `maxwell2021`, `Maxwell2020determining`, `MaxwellDayHailey2023`, `maxwell2014`, `vaitla2017`, `IPC2025Gaza`, `FRC2024Sudan`, `ipcfrc2024sudandec`, `ipc2016amn`, `ipc2024linkages`, `fewsnet2018nutmort`, `venkat2023seasonality`, `luc2023chad`, `moradi2019`, `mason2012`, `rogers2015coverage`, `isanaka2021icf`, `pople2026early`, `cabotventon2012economics`, `coughlandeperez2019rain`, `langendorf2014preventing`, `salama2012`.

**Housekeeping note.** The cgd bib already has duplicate entries for the same works under different keys:
- `checchi2013` / `ChecchiRobinson2013Somalia` / `checchi2013mortality`
- `maxwell2012` / `maxwell2012somalia`
- `hillbruner2012` / `hillbruner2012early`
- `deWaal2018mass` / `dewaal2018mass`
- `HoweDevereux2004` / `howe2004famine`
- `maxwell2020pia` / `MaxwellHailey2020PIA`
- `lentz2025` / `Lentz2025undercount`

Worth consolidating.

**New entries** (keys checked: no clash with the cgd bib):

```bibtex
@article{maxwell2023hhs,
  author  = {Maxwell, Daniel and Adan, Guhad and Hailey, Peter and Day, Matthew S. and Odhiambo, Stephen B. J. and Kaindi, Lilian and Njiru, James and Venkat, Aishwarya and Marshak, Anastasia},
  title   = {Using the household hunger scale to improve analysis and classification of severe food insecurity in famine-risk conditions: Evidence from three countries},
  journal = {Food Policy},
  year    = {2023},
  volume  = {118},
  pages   = {102449},
  doi     = {10.1016/j.foodpol.2023.102449}
}

@techreport{luc2024fex,
  author      = {Luc, Gwenaelle and Keita, Moussa and Bazongo, B. and Diarra, Brahima and Virchenko, A. and Okley, Claudia and Seyvet, T. and Ngongang Mbunang, Y. and Molla, Daniel and Dujanovic, D. and Nur, A. and Marshak, Anastasia and Rahim, A. and Osman, Abdullahi M.},
  title       = {Special Focus: Wasting Patterns in {Somalia}},
  institution = {Emergency Nutrition Network},
  type        = {Field Exchange},
  number      = {72},
  year        = {2024},
  doi         = {10.6084/m9.figshare.25552191},
  url         = {https://www.ennonline.net/fex/72/special-focus-wasting-patterns-somalia}
}

@book{dewaal1989famine,
  author    = {de Waal, Alex},
  title     = {Famine that Kills: {Darfur}, {Sudan}, 1984--1985},
  publisher = {Clarendon Press},
  address   = {Oxford},
  year      = {1989},
  note      = {Revised edition, Oxford University Press, 2005}
}

@article{dewaal1989popstud,
  author  = {de Waal, Alex},
  title   = {Famine mortality: a case study of {Darfur}, {Sudan} 1984--5},
  journal = {Population Studies},
  year    = {1989},
  volume  = {43},
  number  = {1},
  pages   = {5--24},
  doi     = {10.1080/0032472031000143826}
}

@article{mokyr2002,
  author  = {Mokyr, Joel and {\'O} Gr{\'a}da, Cormac},
  title   = {What do people die of during famines: the {Great Irish Famine} in comparative perspective},
  journal = {European Review of Economic History},
  year    = {2002},
  volume  = {6},
  number  = {3},
  pages   = {339--363},
  doi     = {10.1017/S1361491602000163}
}

@article{ograda2007jel,
  author  = {{\'O} Gr{\'a}da, Cormac},
  title   = {Making Famine History},
  journal = {Journal of Economic Literature},
  year    = {2007},
  volume  = {45},
  number  = {1},
  pages   = {5--38},
  doi     = {10.1257/jel.45.1.5}
}

@article{toole1990,
  author  = {Toole, Michael J. and Waldman, Ronald J.},
  title   = {Prevention of excess mortality in refugee and displaced populations in developing countries},
  journal = {JAMA},
  year    = {1990},
  volume  = {263},
  number  = {24},
  pages   = {3296--3302},
  doi     = {10.1001/jama.1990.03440240086021}
}

@article{toole1997,
  author  = {Toole, Michael J. and Waldman, Ronald J.},
  title   = {The public health aspects of complex emergencies and refugee situations},
  journal = {Annual Review of Public Health},
  year    = {1997},
  volume  = {18},
  pages   = {283--312},
  doi     = {10.1146/annurev.publhealth.18.1.283}
}

@article{salama2004,
  author  = {Salama, Peter and Spiegel, Paul and Talley, Leisel and Waldman, Ronald},
  title   = {Lessons learned from complex emergencies over past decade},
  journal = {The Lancet},
  year    = {2004},
  volume  = {364},
  number  = {9447},
  pages   = {1801--1813},
  doi     = {10.1016/S0140-6736(04)17405-9}
}

@article{salama2001,
  author  = {Salama, Peter and Assefa, Fitsum and Talley, Leisel and Spiegel, Paul and van der Veen, Albertien and Gotway, Carol A.},
  title   = {Malnutrition, measles, mortality, and the humanitarian response during a famine in {Ethiopia}},
  journal = {JAMA},
  year    = {2001},
  volume  = {286},
  number  = {5},
  pages   = {563--571},
  doi     = {10.1001/jama.286.5.563}
}

@article{gomaeg1995,
  author  = {{Goma Epidemiology Group}},
  title   = {Public health impact of {Rwandan} refugee crisis: what happened in {Goma}, {Zaire}, in {July}, 1994?},
  journal = {The Lancet},
  year    = {1995},
  volume  = {345},
  number  = {8946},
  pages   = {339--344},
  doi     = {10.1016/S0140-6736(95)90338-0}
}

@article{moore1993,
  author  = {Moore, Patrick S. and Marfin, Anthony A. and Quenemoen, Linda E. and Gessner, Bradford D. and Miller, D. S. and Toole, Michael J. and others},
  title   = {Mortality rates in displaced and resident populations of central {Somalia} during 1992 famine},
  journal = {The Lancet},
  year    = {1993},
  volume  = {341},
  number  = {8850},
  pages   = {935--938},
  doi     = {10.1016/0140-6736(93)91223-9}
}

@article{youngjaspars1995nutrition,
  author  = {Young, Helen and Jaspars, Susanne},
  title   = {Nutrition, Disease and Death in Times of Famine},
  journal = {Disasters},
  year    = {1995},
  volume  = {19},
  number  = {2},
  pages   = {94--109},
  doi     = {10.1111/j.1467-7717.1995.tb00361.x}
}

@article{youngjaspars1995assess,
  author  = {Young, Helen and Jaspars, Susanne},
  title   = {Nutritional Assessments, Food Security and Famine},
  journal = {Disasters},
  year    = {1995},
  volume  = {19},
  number  = {1},
  pages   = {26--36},
  doi     = {10.1111/j.1467-7717.1995.tb00330.x}
}

@techreport{youngjaspars2006,
  author      = {Young, Helen and Jaspars, Susanne},
  title       = {The Meaning and Measurement of Acute Malnutrition in Emergencies: A Primer for Decision-Makers},
  institution = {Humanitarian Practice Network, Overseas Development Institute},
  type        = {HPN Network Paper},
  number      = {56},
  address     = {London},
  year        = {2006},
  url         = {https://odihpn.org/publication/the-meaning-and-measurement-of-acute-malnutrition-in-emergencies-a-primer-for-decision-makers/}
}

@article{young2004public,
  author  = {Young, Helen and Borrel, Annalies and Holland, Diane and Salama, Peter},
  title   = {Public nutrition in complex emergencies},
  journal = {The Lancet},
  year    = {2004},
  volume  = {364},
  number  = {9448},
  pages   = {1899--1909},
  doi     = {10.1016/S0140-6736(04)17447-3}
}

@techreport{unicef1990,
  author      = {{UNICEF}},
  title       = {Strategy for Improved Nutrition of Children and Women in Developing Countries},
  institution = {United Nations Children's Fund},
  type        = {UNICEF Policy Review},
  number      = {E/ICEF/1990/L.6},
  address     = {New York},
  year        = {1990}
}

@misc{unicef2020framework,
  author       = {{UNICEF}},
  title        = {{UNICEF} Conceptual Framework on Maternal and Child Nutrition},
  howpublished = {United Nations Children's Fund, New York},
  year         = {2020},
  url          = {https://www.unicef.org/documents/conceptual-framework-nutrition}
}

@article{marshak2017chad,
  author  = {Marshak, Anastasia and Young, Helen and Bontrager, Elizabeth N. and Boyd, Erin M.},
  title   = {The Relationship Between Acute Malnutrition, Hygiene Practices, Water and Livestock, and Their Program Implications in Eastern {Chad}},
  journal = {Food and Nutrition Bulletin},
  year    = {2017},
  volume  = {38},
  number  = {1},
  pages   = {115--127},
  doi     = {10.1177/0379572116681682}
}

@article{grellety2016whz,
  author  = {Grellety, Emmanuel and Golden, Michael H.},
  title   = {Weight-for-height and mid-upper-arm circumference should be used independently to diagnose acute malnutrition: policy implications},
  journal = {BMC Nutrition},
  year    = {2016},
  volume  = {2},
  pages   = {10},
  doi     = {10.1186/s40795-016-0049-7}
}

@article{isanaka2009rutf,
  author  = {Isanaka, Sheila and Nombela, Nohelly and Djibo, Ali and Poupard, Marie and Van Beckhoven, Dominique and Gaboulaud, Val{\'e}rie and Guerin, Philippe J. and Grais, Rebecca F.},
  title   = {Effect of Preventive Supplementation With Ready-to-Use Therapeutic Food on the Nutritional Status, Mortality, and Morbidity of Children Aged 6 to 60 Months in {Niger}: A Cluster Randomized Trial},
  journal = {JAMA},
  year    = {2009},
  volume  = {301},
  number  = {3},
  pages   = {277--285},
  doi     = {10.1001/jama.2008.1018}
}

@book{barrettmaxwell2005,
  author    = {Barrett, Christopher B. and Maxwell, Daniel G.},
  title     = {Food Aid After Fifty Years: Recasting Its Role},
  publisher = {Routledge},
  address   = {London},
  year      = {2005}
}

@article{barrett2010measuring,
  author  = {Barrett, Christopher B.},
  title   = {Measuring Food Insecurity},
  journal = {Science},
  year    = {2010},
  volume  = {327},
  number  = {5967},
  pages   = {825--828},
  doi     = {10.1126/science.1182768}
}

@article{devereux2009,
  author  = {Devereux, Stephen},
  title   = {Why does famine persist in {Africa}?},
  journal = {Food Security},
  year    = {2009},
  volume  = {1},
  number  = {1},
  pages   = {25--35},
  doi     = {10.1007/s12571-008-0005-8}
}

@article{spiegel2010,
  author  = {Spiegel, Paul B. and Checchi, Francesco and Colombo, Sandro and Paik, Eugene},
  title   = {Health-care needs of people affected by conflict: future trends and changing frameworks},
  journal = {The Lancet},
  year    = {2010},
  volume  = {375},
  number  = {9711},
  pages   = {341--345},
  doi     = {10.1016/S0140-6736(09)61873-0}
}

@article{spiegel2017,
  author  = {Spiegel, Paul B.},
  title   = {The humanitarian system is not just broke, but broken: recommendations for future humanitarian action},
  journal = {The Lancet},
  year    = {2017},
  note    = {Published online 8 June 2017},
  doi     = {10.1016/S0140-6736(17)31278-3}
}

@article{blanchet2017,
  author  = {Blanchet, Karl and Ramesh, Anita and Frison, Severine and Warren, Emily and Hossain, Mazeda and Smith, James and others},
  title   = {Evidence on public health interventions in humanitarian crises},
  journal = {The Lancet},
  year    = {2017},
  volume  = {390},
  number  = {10109},
  pages   = {2287--2296},
  doi     = {10.1016/S0140-6736(16)30768-1}
}

@book{msf1997,
  author    = {{M{\'e}decins Sans Fronti{\`e}res}},
  title     = {Refugee Health: An Approach to Emergency Situations},
  publisher = {Macmillan},
  address   = {London},
  year      = {1997}
}

@article{checchiroberts2008,
  author  = {Checchi, Francesco and Roberts, Les},
  title   = {Documenting Mortality in Crises: What Keeps Us from Doing Better?},
  journal = {PLoS Medicine},
  year    = {2008},
  volume  = {5},
  number  = {7},
  pages   = {e146},
  doi     = {10.1371/journal.pmed.0050146}
}

@article{prudhon2007,
  author  = {Prudhon, Claudine and Spiegel, Paul B.},
  title   = {A review of methodology and analysis of nutrition and mortality surveys conducted in humanitarian emergencies from {October} 1993 to {April} 2004},
  journal = {Emerging Themes in Epidemiology},
  year    = {2007},
  volume  = {4},
  pages   = {10},
  doi     = {10.1186/1742-7622-4-10}
}

@article{spiegel2004jama,
  author  = {Spiegel, Paul B. and Salama, Peter and Maloney, Susan and van der Veen, Albertien},
  title   = {Quality of Malnutrition Assessment Surveys Conducted During Famine in {Ethiopia}},
  journal = {JAMA},
  year    = {2004},
  volume  = {292},
  number  = {5},
  pages   = {613--618},
  doi     = {10.1001/jama.292.5.613},
  note    = {Co-authors after Spiegel not verified}
}

@techreport{smart2006,
  author      = {{SMART}},
  title       = {Measuring Mortality, Nutritional Status, and Food Security in Crisis Situations: {SMART} Methodology, Version 1},
  institution = {Standardized Monitoring and Assessment of Relief and Transitions},
  year        = {2006},
  month       = apr
}

@article{heudtlass2016,
  author  = {Heudtlass, Peter and Speybroeck, Niko and Guha-Sapir, Debarati},
  title   = {Excess mortality in refugees, internally displaced persons and resident populations in complex humanitarian emergencies (1998--2012) -- insights from operational data},
  journal = {Conflict and Health},
  year    = {2016},
  volume  = {10},
  pages   = {15},
  doi     = {10.1186/s13031-016-0082-9}
}

@article{coghlan2006,
  author  = {Coghlan, Benjamin and Brennan, Richard J. and Ngoy, Pascal and Dofara, David and Otto, Brad and Clements, Mark and Stewart, Tony},
  title   = {Mortality in the {Democratic Republic of Congo}: a nationwide survey},
  journal = {The Lancet},
  year    = {2006},
  volume  = {367},
  number  = {9504},
  pages   = {44--51},
  doi     = {10.1016/S0140-6736(06)67923-3}
}

@book{hsrp2010,
  author    = {{Human Security Report Project}},
  title     = {Human Security Report 2009/2010: The Causes of Peace and the Shrinking Costs of War},
  publisher = {Oxford University Press},
  address   = {New York},
  year      = {2011}
}

@techreport{gbav2008,
  author      = {{Geneva Declaration Secretariat}},
  title       = {Global Burden of Armed Violence},
  institution = {Geneva Declaration on Armed Violence and Development},
  address     = {Geneva},
  year        = {2008},
  url         = {https://www.smallarmssurvey.org/sites/default/files/resources/GBAV_fullreport.pdf}
}

@article{degomme2010,
  author  = {Degomme, Olivier and Guha-Sapir, Debarati},
  title   = {Patterns of mortality rates in {Darfur} conflict},
  journal = {The Lancet},
  year    = {2010},
  volume  = {375},
  number  = {9711},
  pages   = {294--300},
  doi     = {10.1016/S0140-6736(09)61967-X}
}

@article{depoortere2004,
  author  = {Depoortere, Evelyn and Checchi, Francesco and Broillet, France and Gerstl, Sibylle and Minetti, Andrea and Gayraud, Olivia and others},
  title   = {Violence and mortality in {West Darfur}, {Sudan} (2003--04): epidemiological evidence from four surveys},
  journal = {The Lancet},
  year    = {2004},
  volume  = {364},
  number  = {9442},
  pages   = {1315--1320},
  doi     = {10.1016/S0140-6736(04)17187-0}
}

@article{khatib2024,
  author  = {Khatib, Rasha and McKee, Martin and Yusuf, Salim},
  title   = {Counting the dead in {Gaza}: difficult but essential},
  journal = {The Lancet},
  year    = {2024},
  volume  = {404},
  number  = {10449},
  pages   = {237--238},
  doi     = {10.1016/S0140-6736(24)01169-3}
}

@unpublished{dahab2024,
  author = {Dahab, Maysoon and others},
  title  = {War-time mortality in {Sudan}: a capture-recapture analysis},
  note   = {Preprint, Sudan Research Group / London School of Hygiene \& Tropical Medicine, November 2024. Full author list not verified},
  year   = {2024},
  url    = {https://www.lshtm.ac.uk/newsevents/news/2024/invisible-and-severe-death-toll-sudan-conflict-revealed}
}

@article{coughlandeperez2015,
  author  = {Coughlan de Perez, Erin and van den Hurk, Bart and van Aalst, Maarten K. and Jongman, Brenden and Klose, Thorsten and Suarez, Pablo},
  title   = {Forecast-based financing: an approach for catalyzing humanitarian action based on extreme weather and climate forecasts},
  journal = {Natural Hazards and Earth System Sciences},
  year    = {2015},
  volume  = {15},
  number  = {4},
  pages   = {895--904},
  doi     = {10.5194/nhess-15-895-2015}
}

@article{gros2019,
  author  = {Gros, Clemens and Bailey, Meghan and Schwager, Saroja and Hassan, Ahmadul and Zingg, Raymond and Uddin, Muhammad Mamtaz and others},
  title   = {Household-level effects of providing forecast-based cash in anticipation of extreme weather events: Quasi-experimental evidence from humanitarian interventions in the 2017 floods in {Bangladesh}},
  journal = {International Journal of Disaster Risk Reduction},
  year    = {2019},
  volume  = {41},
  pages   = {101275},
  doi     = {10.1016/j.ijdrr.2019.101275}
}

@techreport{christian2025floods,
  author      = {Christian, Paul and Dunsch, Felipe and Heirman, Jonas and Kelley, Erin and Kondylis, Florence and Lane, Gregory and others},
  title       = {Fast Action for Floods: {RCT} Evidence on Forecast-based Cash Transfers from {Bangladesh} and {Nepal}},
  institution = {National Bureau of Economic Research},
  type        = {NBER Working Paper},
  number      = {34414},
  year        = {2025},
  doi         = {10.3386/w34414}
}

@techreport{buchanansmith2021,
  author      = {Buchanan-Smith, Margie and Cocking, Jane and Sharp, Sam},
  title       = {Independent Review of the {IPC} {South Sudan}},
  institution = {Humanitarian Policy Group, ODI},
  type        = {HPG commissioned report},
  address     = {London},
  year        = {2021},
  month       = sep,
  url         = {https://cdn.odi.org/media/documents/ODI_HPG_IPC_South_Sudan_report_final_BXOKlof.pdf}
}

@techreport{buchanansmith2023,
  author      = {Buchanan-Smith, Margie and Cocking, Jane and Moallin, Zainab},
  title       = {Independent Review of the Integrated Food Security Phase Classification ({IPC}) {Somalia}},
  institution = {Humanitarian Policy Group, ODI},
  type        = {HPG commissioned report},
  address     = {London},
  year        = {2023},
  url         = {https://odi.org/en/publications/independent-review-of-the-ipc-in-somalia/}
}

@techreport{ipcfrc2024gazajune,
  author      = {{IPC Famine Review Committee}},
  title       = {{FEWS NET} Gaza Analysis: Famine Review Committee Conclusions and Recommendations},
  institution = {IPC Global Partners},
  year        = {2024},
  month       = jun,
  url         = {https://www.un.org/unispal/wp-content/uploads/2024/06/IPC_Famine_Review_Committee_Report_Gaza_June2024.pdf}
}

@techreport{unhcr2009urban,
  author      = {{UNHCR}},
  title       = {{UNHCR} Policy on Refugee Protection and Solutions in Urban Areas},
  institution = {United Nations High Commissioner for Refugees},
  address     = {Geneva},
  year        = {2009},
  month       = sep
}
```
