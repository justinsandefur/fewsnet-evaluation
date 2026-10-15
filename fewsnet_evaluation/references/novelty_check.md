# Novelty check: has anyone compared survey GAM/mortality with the AFI phase of the same area?

Compiled 2026-10-08. This was an adversarial search for counterexamples to the claim we want to make in the paper:

> "We know of no study that systematically compares measured child acute malnutrition (GAM) or mortality (CDR, U5DR) from surveys with the IPC/Cadre Harmonisé/FEWS NET acute food insecurity (AFI) phase of the same area."

It builds on `lit_phase_outcomes.md` and `lit_fewsnet_accuracy.md` §E and does not repeat their entries except where something new was found.

**Verification tags**
- [V-full]: I read the full text in this session.
- [V-abs]: I read only the abstract, a catalogue record or a search extract.
- [NV]: not verified.

**Access.** ipcinfo.org, medRxiv, ScienceDirect, Springer and UNOCHA returned 403. IPC documents were read from Wayback Machine copies (web.archive.org `id_` URLs). medRxiv S-MED was read the same way. Europe PMC supplied the PMC full texts.

**Search coverage**
- About 45 web searches in English and French, covering:
  - IPC/CH/FEWS NET phase × GAM/SAM/MUAC/wasting/CDR/U5DR, with variants such as "concordance", "kappa", "cross-tabulation", "mismatch", "divergence", "validation", "predictive validity", "ecological", "DHS-linked" and "thesis/mémoire";
  - "Cadre Harmonisé malnutrition aiguë corrélation", "relation insécurité alimentaire malnutrition aiguë SMART", and Sahel "convergence" analyses;
  - Global Report on Food Crises (GRFC) nutrition chapters, ENN Field Exchange, IPC Global Support Unit (GSU) guidance, FSNAU, FEWS NET nutrition reports, the Global Nutrition Cluster (GNC), CDC/LSHTM mortality work, and Kenya NDMA.
- OpenAlex searches (about 12 queries).
- Forward citations of Reusken et al. 2025 (Semantic Scholar).
- The reference list of Reusken et al. 2025.
- A Wayback CDX listing of about 2,950 archived ipcinfo.org documents.

---

## 1. Verdict

**The claim survives in substance but must be qualified. Two things come close.**

**(a) The IPC Global Support Unit's April 2024 guidance note on AFI–acute malnutrition (AMN) linkages** [V-full]
- It reports phase-concordance counts from two settings:
  - Karamoja 2020: only 3 of 9 districts were in corresponding AFI and AMN phases.
  - Burkina Faso (CH vs IPC AMN): 22 of 53 provinces were in different phases.
- It also cites an unpublished Guatemala analysis that found an "inverse relationship" between AFI and AMN phases.
- It refers to an internal IPC "AFI-AMN literature review discussion note", which I could not locate.
- The IPC AMN phase is a binned survey GAM (WHZ cut-offs of 5/10/15/30%). This is therefore a direct, if anecdotal, AFI-phase-vs-GAM comparison.
- It is not systematic. There are two examples, no statistics, and no denominator across countries. The note explicitly says it "is not intended to provide information on how to find correlations or associations".

**(b) Reusken et al. (2025, BMJ Public Health)** [V-full]
- The study regresses district GAM in Somalia (FSNAU, 74 districts, 2017–2021) on a set of candidate covariates.
- That set includes the share of the district population in IPC Phase 3+, interpolated from twice-yearly IPC analyses.
- Results:
  - Contemporaneous IPC 3+ share: p ≤ 0.01 in simple and multiple linear regression, with a "nonlinear" non-parametric shape.
  - 6-month lag: p ≤ 0.01 in simple regression, p > 0.3 in multiple regression.
- No effect size is reported in the main text. The IPC variable is not discussed.
- This is one country, a forecasting exercise, and it uses the population share rather than the area phase. It is still a regression of survey GAM on IPC Phase 3+ share across areas and over time, so "no study … regresses" would be false without a qualifier.

**Nothing else I found does this.**
- I found no peer-reviewed paper, working paper, thesis or agency report that, across areas and countries:
  - tabulates or regresses survey GAM, CDR or U5DR on AFI phase; or
  - scores FEWS NET or IPC projections against later anthropometry or mortality.
- This includes the IPC's commissioned Accuracy Study (2024) [V-full]: its AMN chapter compares AMN consensus phases with WHZ- and MUAC-implied phases and never compares them with AFI.
- The 2023 Elrha/R2HC scoping review [V-full] concludes that the food insecurity–mortality link "in humanitarian contexts specifically cannot be answered with the current body of evidence".
- The S-MED paper [V-full] says "less is known about linking early warning signals for famine with the evolving malnutrition and mortality situation".
- The 2015 FSNAU internal review [V-full] lists the food-security/acute-malnutrition relationship as something that "needs to be explored".
- The **mortality** half of the claim is the strongest. In every study found, IPC phase appears only as:
  - a baseline definition (Checchi & Robinson 2013);
  - a "visual inspection" cross-check (Warsame et al. 2023); or
  - a map overlay (S-MED; Ratnayake et al. 2025).
- No study regresses or tabulates CDR or U5DR on phase.

### Suggested sentence for the paper

Long version:
> "We know of no study that systematically compares survey-measured child wasting or mortality with the IPC, Cadre Harmonisé or FEWS NET acute food insecurity phase of the same area across countries, or that scores these classifications against subsequently measured anthropometry or mortality. The closest evidence is fragmentary. The IPC's own guidance notes that acute food insecurity and acute malnutrition phases frequently diverge — for example, only 3 of 9 Karamoja districts matched in 2020 — but reports no systematic statistics (IPC 2024). A Somalia forecasting study includes the district share of the population in IPC Phase 3+ among many candidate predictors of GAM (Reusken et al. 2025). Mortality studies use IPC phase only to define baseline periods or as a visual cross-check (Checchi and Robinson 2013; Warsame et al. 2023)."

Short version, for the introduction:
> "To our knowledge, no study has systematically compared survey-measured acute malnutrition or mortality with the acute food insecurity phase assigned to the same area; the closest evidence consists of anecdotal concordance counts in IPC guidance (IPC 2024) and a single-country forecasting model in which the IPC Phase 3+ population share is one of many predictors of GAM (Reusken et al. 2025)."

**Wording to avoid**
- "No study has ever compared GAM with IPC phase" (false given IPC 2024 and Reusken 2025).
- "No study regresses GAM on IPC" (false given Reusken 2025).
- Saying our Somalia correlation is the "first quantification" is defensible only as "first published cross-area correlation of SMART GAM with the AFI area phase". Reusken reports significance levels, not a correlation or slope, for the population share.

---

## 2. Near-misses and partial counterexamples, ranked by closeness

### A. Closest items: partial counterexamples that need a qualifier

**A1. IPC Global Partnership / Global Support Unit (April 2024). *Exploring linkages between Acute Food Insecurity and Acute Malnutrition.* IPC Guidance Note, 12 pp. Rome: IPC GSU.** https://www.ipcinfo.org/fileadmin/user_upload/ipcinfo/docs/IPC-Guidance-Note-linkages-AFI-and-AMN.pdf (read via Wayback) [V-full]
- **What it does.** It is guidance for analysts on explaining AFI–AMN phase divergence. It defines divergence as a difference of 2 or more phases and says a 1-phase difference is "not unusual in any setting".
- **The counts it reports (p. 2):**
  - Karamoja, Uganda 2020: "only three districts were classified in corresponding phases across both scales" (of 9).
  - Burkina Faso CH: "of the 53 provinces … 22 provinces showed different phases compared to the IPC AMN".
  - It adds that divergences "have been observed in all countries where comparable data on AFI and AMN classifications exists", and that some areas stay in high AMN phases "regardless of the changes in IPC AFI phase classification".
- **Other evidence it cites (p. 3):**
  - "Another analysis between AFI and AMN phases in Guatemala shows an inverse relationship". This is unpublished; I did not find it [NV].
  - "Based on the existing academic and grey literature, the relationship between acute food insecurity and acute malnutrition is unclear (see AFI-AMN literature review discussion note)". I did not find the note in the archived ipcinfo document list [NV].
- **Single-area examples:**
  - Sierra Leone 2022, Kailahun: AFI Phase 3 vs AMN Phase 1.
  - Burkina Faso 2022, Balé and Banwa: AFI Phase 1 vs AMN Phase 3.
- **Why it is not systematic:** two examples, no cross-tab across all areas, no statistic. The note says it "is not intended to provide information on how to find correlations or associations".
- **Related.** The FAO OED (2022) evaluation of the IPC Global Strategic Programme (GSP) [V-full, p. ~50 table] says "joint AFI-AMN briefs published in 2022 explore interactions/linkages among the AFI and AMN scales, for Yemen, Uganda, Kenya, Cabo Delgado - Mozambique (not yet published)". These are presumably the source of the Karamoja figures. I did not find them published [NV].

**A2. Reusken, M., Coffey, C., Cruijssen, F., Melenberg, B. & van Wanrooij, C. (2025). Identification of factors associated with acute malnutrition in children under 5 years and forecasting future prevalence: assessing the potential of statistical and machine learning methods. *BMJ Public Health* 3: e001460.** https://doi.org/10.1136/bmjph-2024-001460 [V-full, PMC11883882]
- **Sample:** Somalia, FSNAU GAM by district, 74 districts.
  - Statistical analysis: Jul 2017–Jul 2021, 3,584 monthly observations.
  - Forecasting: 65 districts × 9 biannual periods.
  - The IPC 3+ share comes from IPC analyses (two per year), linearly interpolated to monthly.
- **Table 3:**
  - IPC 3+ share, lag 0: simple linear regression p ≤ 0.01; non-parametric test "nonlinear"; multiple linear regression p ≤ 0.01.
  - Lag 6: p ≤ 0.01 simple, "nonlinear", p > 0.3 multiple.
  - Coefficients are only in the online supplement, which I did not read. The main text never discusses IPC, except in the conclusion's list of factors.
- **Finding:** the 6-month lag of GAM dominates. The random forest predicts direction correctly 72.9% of the time, against 37.3% for a naive forecast.
- It cites no prior IPC–GAM study.
- Forward citations (Semantic Scholar, 4 papers) contain no IPC–GAM follow-up.

### B. Comparisons of outcomes and phases that are anecdotal, visual or country-level

**B1. Ratnayake, R., Ouchtar, Y., Ahmed, Y.A., Mohamoud, J.H., Jelle, M., Seal, A., Dirie, N.I., Palmer, J. & Checchi, F. (2025). The Somalia Mortality Estimation Database (S-MED): a bird's eye view of mortality and its determinants. *medRxiv* 10.1101/2025.09.07.25335291.** [V-full via Wayback]
- **What it does:**
  - It overlays IPC Phase 4/5 maps (Dec 2022) on above-threshold CDR and U5DR (Fig. 5C) and says S-MED could "show the overlap" between them.
  - Narrative only: excess CDR "up to 0.09" per 10,000/day in 2017–18 "across areas classified as relatively modest IPC Phase 3".
- **No statistic.**
- **Gap statement (Discussion):** "Less is known about linking early warning signals for famine with the evolving malnutrition and mortality situation demonstrated through field studies."

**B2. Warsame, A., Frison, S. & Checchi, F. (2023). Drought, armed conflict and population mortality in Somalia, 2014–2018. *PLOS Global Public Health* 3(4): e0001136.** [V-full; see lit_phase_outcomes.md §2.2]
- Regional excess death rates "correlated broadly", "on visual inspection", with the early-2017 projected IPC 3–4 share. No coefficient is reported.

**B3. LSHTM / SIMAD / UNICEF / WHO / FSNAU (Jan 2025). *From insight to action: an update on mortality patterns in Somalia.*** [V-full; see lit_phase_outcomes.md §2.4]
- North-eastern regions had lower mortality despite "comparatively similar" projected IPC shares. One sentence, no statistic.

**B4. Checchi, F. & Robinson, W.C. (2013). *Mortality among populations of southern and central Somalia affected by severe food insecurity and famine during 2010–2012.* FAO/FSNAU & FEWS NET.** [V-full; lit_phase_outcomes.md §2.1]
- IPC 1–2 status is used only to select 12 baseline surveys. There is a qualitative observation that survey CDR did not rise in the 2008–09 AFI crisis.

**B5. Vuylsteke, S. (2021). *When Aid Goes Awry, Part 2.1 — A Data Case Study: Famine in Yemen.* Sana'a Center for Strategic Studies, 27 Oct 2021.** https://sanaacenter.org/files/When_Aid_Goes_Awry_02_A_Data_Case_Study_en.pdf [V-full]
- **Context given:** Yemen's 2017 IPC projection put large areas in Phase 4.
- **The juxtaposition:** the report notes that SMART surveys in 2016–17 (only 5 surveys in 2016 and 3 in 2017) found "none of the 18 governorates assessed showed a death rate (crude or under-5) of 1 or above per 10,000 people per day".
- This is one country, a narrative juxtaposition, and no statistic.

**B6. Al Sharjabi, S.J., Al-Jawaldeh, A., El Hajj Hassan, O. & Dureab, F. (2024). Understanding the Food and Nutrition Insecurity Drivers in Some Emergency-Affected Countries in the Eastern Mediterranean Region from 2020 to 2024. *Nutrients* 16(22): 3853.** https://doi.org/10.3390/nu16223853 [V-full, PMC11597532]
- **Sample:** 10 countries, **country-level**, 2020–24.
- **What it does:** a descriptive side-by-side of the IPC Phase 3+ share and median GAM from IPC AMN reports.
- **Claim:** "the linkage between food insecurity and malnutrition levels has a similar trend in almost all countries". No statistic, and the comparison is not area-level.

**B7. Hassan, M., Saif, K., Ijaz, M.S., Sarfraz, Z., Sarfraz, A., Robles-Velasco, K. & Chérrez-Ojeda, I. (2023). Mean temperature and drought projections in Central Africa: a population-based study of food insecurity, childhood malnutrition and mortality, and infectious disease. *IJERPH* 20(3): 2697.** https://doi.org/10.3390/ijerph20032697 [V-abs]
- Maps IPC AFI and shows Global Hunger Index (GHI) wasting and mortality by country side by side. No comparison analysis.

**B8. IPC Famine Review Committee reports, and the Somalia 2011 famine declaration (Salama et al. 2012, *Global Food Security* 1: 13–19).** [see lit_phase_outcomes.md §4.1]
- Case-by-case juxtaposition of phase with measured GAM and CDR for famine-reviewed areas. Not systematic.

**B9. Janin, P. (coord.) et al. (18 Feb 2025). *Insécurité alimentaire au Sahel central (PASAS) — rapport final.* IRD.** https://horizon.documentation.ird.fr/exl-doc/pleins_textes/2025-12/010095718.pdf [V-full, skimmed]
- Narrative and graphs of national food insecurity and malnutrition trends across four Sahel crises (Niger, Mali, Burkina Faso). There is no area-level phase × GAM analysis.

### C. Classification-system studies that stop short of outcomes

**C1. Lentz, E., Baylis, K., Michelson, H. & Kim, C. (May 2024). *IPC Accuracy Study: Analyzing the internal consistency of IPC AFI and AMN analyses.* IPC GSU, 93 pp.** https://www.ipcinfo.org/fileadmin/user_upload/ipcinfo/docs/IPC_Accuracy_Study.pdf (Wayback) [V-full]
- **AFI section:** the outcomes are household indicators only. Survey GAM and CDR are not used.
- **AMN section (Ch. 5):** a "proof of concept" on 203 classifications from Kenya (2020–22) and South Sudan (2022). It compares AMN consensus phase with WHZ- and MUAC-implied phases.
- **The study never cross-tabulates AFI against AMN or GAM.** It recommends future "modeling [of] AFI and AMN outcome indicators".

**C2. Michelson, H., Lentz, E., Armstrong, J. & Korpi, K. (2026). The integrated food security phase classification system: seven defining characteristics. *Food Policy* 142: 103134.** https://doi.org/10.1016/j.foodpol.2026.103134 [V-abs; full text 403]
- From the extracts: the AFI–AMN relationship "is not consistent", with the Somalia 2025 example (AFI Phase 3, AMN Phase 4). This is a viewpoint, not a tabulation.

**C3. Lentz, Michelson, Baylis & Zhou (2019), *World Development*; Lentz et al. (2025), *Nature Food*; Rose & Collins (2025); Machefer et al. (2025).** [see lit_fewsnet_accuracy.md]
- They compare phases with household food-security indicators only (FCS, rCSI, HDDS). There is no anthropometry or mortality.

**C4. Seyffer et al. (2026), AGILE GIScience Series 7: 17.** [lit_fewsnet_accuracy.md §7]
- Compares FEWS NET and IPC classifications with each other. No outcomes.

### D. Household- or community-level food insecurity vs wasting, without the area phase (the evidence underneath)

**D1. Young, H. & Marshak, A. (2017/2018). *Persistent Global Acute Malnutrition.* Feinstein International Center, Tufts University.** [V-full; lit_phase_outcomes.md §3.1]
- Case studies.
- Northern Bahr el Ghazal had GAM above 15% "even when classified green on the IPC". This is a single-area anecdote.

**D2. McDonald, C. (March 2017). *Nutrition Causal Analysis in Niger: Report of Key Findings.* FEWS NET.** https://fews.net/sites/default/files/documents/reports/FEWS%20NET%20NCA%20Research%20in%20Niger%20-%20Final%20Report%20of%20Key%20Findings.pdf [V-full]
- **What it is:** FEWS NET-commissioned. This is the "FEWS NET Niger analysis" that Young & Marshak cite.
- **Sample:** Maradi and Zinder, 2 rounds in 2015, 1,702 children, SMART-based.
- **Finding:** household HFIAS or FCS "was not independently associated with the odds of being wasted or becoming wasted". The report adds that "in a typical year, the prevalence of child wasting is a poor indicator of the household food security situation".
- **Limitation:** household-level only, not area phase.

**D3. Luc, G., Keita, M., Houssoube, F., et al. (2023). Community clustering of food insecurity and malnutrition associated with systemic drivers in Chad. *Food and Nutrition Bulletin* 44(2 suppl): S69–S82.** [V-abs; lit_phase_outcomes.md §3.2]
- Wasting hotspots are not the food-insecurity hotspots, at the village level.

**D4. Luc, G., Keita, M., Bazongo, B., Diarra, B., Virchenko, A., Okley, C., Seyvet, T., Ngongang Mbunang, Y., Molla, D., Dujanovic, D., Nur, A., Marshak, A., Rahim, A. & Osman, A.M. (2024). Special focus: Wasting patterns in Somalia. *Field Exchange* 72.** https://doi.org/10.6084/m9.figshare.25552191 [V-abs (ENN page summary)]
- **Sample:** FSNAU household surveys 2014–21, 85,837 children, 27,520 households.
- **Measure:** household FCS, not IPC phase.
- **Findings:**
  - The two wasting peaks (May–June and November) do not track food insecurity, and wasting falls in the lean season.
  - Wasting shows minimal year-to-year variation.
- IPC is mentioned only as background.

**D5. Moradi et al. (2019), *Nutrition* 62: 52–60.** [V-abs]
- Household food insecurity vs wasting: OR 1.04 (0.96–1.12).

**D6. Maitra, C. (2018). *A review of studies examining the link between food insecurity and malnutrition.* Technical Paper. Rome: FAO.** http://www.fao.org/3/CA1447EN/ca1447en.pdf [V-full]
- **Scope:** 120 studies of experience-based household scales.
- **Finding:** only 3 of 15 wasting studies found a positive association.
- **Zero mentions** of IPC, CH or FEWS NET.

**D7. Annan, R.A., et al. (July 2023). *Food insecurity, maternal and child malnutrition, morbidity and mortality linkages in humanitarian contexts: a scoping review.* Elrha / R2HC, 62 pp.** https://alnap.org/documents/19223/Lit-Review-Food-insecurity-Health-.pdf [V-full; full author list not captured]
- **Scope:** 48 studies included.
- **Use of IPC:** only as context.
- **Mortality finding:** "Just two studies reported the linkage between food insecurity and mortality … both … conducted in LMICs and not in humanitarian contexts. This implies that the linkage between food insecurity and mortality in humanitarian contexts specifically cannot be answered with the current body of evidence".

**D8. Brown, M.E., Backer, D., Billing, T., White, P., Grace, K., Doocy, S. & Huth, P. (2020). Empirical studies of factors associated with child malnutrition: highlighting the evidence about climate and conflict shocks. *Food Security* 12(6): 1241–1252.** https://doi.org/10.1007/s12571-020-01041-y [V-abs]
- 90 statistical studies. "Wasting … is substantially understudied".
- The abstract lists no IPC or FEWS NET phase predictor. These are the same authors as the FEWS NET validation work (Backer & Billing 2021).

**D9. FSNAU (17 Sept 2015). *Internal Review of Existing FSNAU Tools & Methods and Recommendations for Improvement.*** https://fsnau.org/downloads/Internal-Review-of-Existing-FSNAU-Tools-Methods-and-Recommendations-for-Improvement-September-2015.pdf [V-full, 5 pp.]
- States that the "relationship between a range of multiple food security related indicators such as Coping Strategies Index (CSI) and acute malnutrition needs to be explored based on time-series data from nutrition surveys". This is an acknowledged gap inside the Somalia system.

### E. Malnutrition and mortality prediction models that omit IPC phase (absence confirmed)

- **Checchi et al. 2022** (BMC Nutrition, Somalia and South Sudan), **Checchi et al. 2026** (PLOS GPH, Kenya), **Checchi et al. 2022** (Pop Health Metrics) and **Checchi et al. 2023** (PNAS, Nigeria). IPC phase is absent from the candidate predictors [V-full; lit_phase_outcomes.md §2].
- **Mohamed, J. et al. (2024).** Predicting the short and long term effects of food price inflation, armed conflicts, and climate variability on global acute malnutrition in Somalia. *J Health Popul Nutr* 43: 68. https://doi.org/10.1186/s41043-024-00557-9 [V-abs]. National ARDL model on conflict, inflation and climate. No IPC.
- **Silva e Silva, L., et al. (FAO) (draft, 2 Mar 2026).** *AI-augmented spatio-temporal modelling of acute malnutrition risks … South Sudan.* ICAS-X abstract [V-full, 4 pp.]. Covers 150,799 children, 2015–24, with household, environment and conflict covariates. No IPC phase.
- **South Sudan Nutrition Cluster / REACH (Feb 2021).** *Predictive modelling techniques to estimate the burden of acute malnutrition … in the absence of anthropometric data.* GNC workshop slides [V-full]. Predicts child-level GAM from FSNMS household indicators. No IPC phase.
- **Constenla-Villoslada et al. (2025, PNAS)** [V-full by earlier agent]. Notes that the IPC's coarse scale makes it "less well-suited" for targeting high-GAM communities but does not test IPC against GAM.
- **Mason et al. (2012, IJERPH)** [V-full, PMC3367278]. Cites the IPC manual for thresholds only.

### F. Searched and not found (documented negatives)

- **GRFC 2026** (80-page edition, text-searched) [V-full]. Nutrition crises are classified at country level from AMN Phase 3+. There is no area-level AFI × AMN cross-tab.
- **IPC Global Brief Series 2017, "IPC Acute Malnutrition Classification"** [V-full]. Mentions an "IPC Harmonization Working Group". No data.
- **IPC AMN Addendum (11 Nov 2016)** [V-full]. Repeats "do not always match". No data.
- **IPC 2015 proceedings on the value added of the chronic and nutrition scales** [V-full]. Nothing.
- **Global Network Against Food Crises (Jan 2024, June 2023), "Famine and protracted IPC/CH Emergency analysis."** Lists districts meeting AFI Phase 4+ together with GAM ≥ 20% (search extract) [V-abs; PDF 403]. Threshold screening, not a comparison.
- **Chad: OCHA "Note d'Analyse sur les résultats du Cadre Harmonisé et de l'enquête SMART 2022" (20 Jan 2023)** [NV, 403]. The title suggests a side-by-side of CH and SMART by province for one country and round. **Worth checking by hand.** At most it would be a single-country descriptive juxtaposition.
- **Others with nothing relevant:**
  - Wageningen (2022) *From insight to foresight* [V-full grep];
  - IFPRI Discussion Paper 2442 on Nigeria (Kirui et al. 2026) [V-full grep, no CH];
  - FEWS NET (2006) *Understanding nutrition data … in Niger* [V-full grep];
  - the Kenya NDMA drought-phase vs MUAC literature, where I found no validation study.
- **No theses found**, in English or French.

---

## 3. BibTeX for the important new items

These are new keys. For reusable keys already in lit_phase_outcomes.md and lit_fewsnet_accuracy.md, use: `reusken2025`, `youngmarshak2017`, `warsame2023`, `checchi2022malnut`, `moradi2019`, `luc2023chad`, `lentz2024ipcaccuracy`, `lentz2019`, `ipc2016amn`, `checchirobinson2013` (if defined).

```bibtex
@techreport{ipc2024linkages,
  author      = {{IPC Global Partnership}},
  title       = {Exploring Linkages between Acute Food Insecurity and Acute Malnutrition},
  institution = {IPC Global Support Unit},
  type        = {IPC Guidance Note},
  address     = {Rome},
  year        = {2024},
  month       = apr,
  url         = {https://www.ipcinfo.org/fileadmin/user_upload/ipcinfo/docs/IPC-Guidance-Note-linkages-AFI-and-AMN.pdf}
}

@article{ratnayake2025smed,
  author  = {Ratnayake, Ruwan and Ouchtar, Yasmine and Ahmed, Y. A. and Mohamoud, J. H. and Jelle, Mohamed and Seal, Andrew and Dirie, N. I. and Palmer, Jennifer and Checchi, Francesco},
  title   = {The {Somalia Mortality Estimation Database (S-MED)}: a Bird's Eye View of Mortality and its Determinants},
  journal = {medRxiv},
  year    = {2025},
  note    = {Preprint, posted 8 September 2025},
  doi     = {10.1101/2025.09.07.25335291}
}

@techreport{mcdonald2017nca,
  author      = {McDonald, Christine},
  title       = {Nutrition Causal Analysis in {Niger}: Report of Key Findings},
  institution = {Famine Early Warning Systems Network (FEWS NET)},
  address     = {Washington, DC},
  year        = {2017},
  month       = mar,
  url         = {https://fews.net/sites/default/files/documents/reports/FEWS%20NET%20NCA%20Research%20in%20Niger%20-%20Final%20Report%20of%20Key%20Findings.pdf}
}

@techreport{maitra2018,
  author      = {Maitra, Chandana},
  title       = {A Review of Studies Examining the Link between Food Insecurity and Malnutrition},
  institution = {Food and Agriculture Organization of the United Nations},
  type        = {Technical Paper},
  address     = {Rome},
  year        = {2018},
  url         = {http://www.fao.org/3/CA1447EN/ca1447en.pdf}
}

@techreport{annan2023elrha,
  author      = {Annan, Reginald A. and others},
  title       = {Food Insecurity, Maternal and Child Malnutrition, Morbidity and Mortality Linkages in Humanitarian Contexts},
  institution = {Elrha, Research for Health in Humanitarian Crises (R2HC)},
  type        = {Scoping review},
  year        = {2023},
  month       = jul,
  note        = {Full author list not verified},
  url         = {https://alnap.org/documents/19223/Lit-Review-Food-insecurity-Health-.pdf}
}

@techreport{luc2024fex,
  author      = {Luc, Gwenaelle and Keita, Moussa and Bazongo, B. and Diarra, Brahima and Virchenko, A. and Okley, Claudia and Seyvet, T. and Ngongang Mbunang, Y. and Molla, Daniel and Dujanovic, D. and Nur, A. and Marshak, Anastasia and Rahim, A. and Osman, Abdullahi M.},
  title       = {Special Focus: Wasting Patterns in {Somalia}},
  institution = {Emergency Nutrition Network},
  type        = {Field Exchange},
  number      = {72},
  year        = {2024},
  doi         = {10.6084/m9.figshare.25552191}
}

@article{alsharjabi2024,
  author  = {Al Sharjabi, Salwa Jamal and Al-Jawaldeh, Ayoub and El Hajj Hassan, Ola and Dureab, Fekri},
  title   = {Understanding the Food and Nutrition Insecurity Drivers in Some Emergency-Affected Countries in the {Eastern Mediterranean Region} from 2020 to 2024},
  journal = {Nutrients},
  year    = {2024},
  volume  = {16},
  number  = {22},
  pages   = {3853},
  doi     = {10.3390/nu16223853}
}

@techreport{vuylsteke2021,
  author      = {Vuylsteke, Sarah},
  title       = {When Aid Goes Awry, Part 2.1: A Data Case Study: Famine in {Yemen}},
  institution = {Sana'a Center for Strategic Studies},
  year        = {2021},
  month       = oct,
  url         = {https://sanaacenter.org/files/When_Aid_Goes_Awry_02_A_Data_Case_Study_en.pdf}
}

@techreport{fsnau2015review,
  author      = {{Food Security and Nutrition Analysis Unit -- Somalia}},
  title       = {Internal Review of Existing {FSNAU} Tools \& Methods and Recommendations for Improvement},
  institution = {FAO/FSNAU},
  address     = {Nairobi},
  year        = {2015},
  month       = sep,
  url         = {https://fsnau.org/downloads/Internal-Review-of-Existing-FSNAU-Tools-Methods-and-Recommendations-for-Improvement-September-2015.pdf}
}

@techreport{faooed2022ipc,
  author      = {{FAO Office of Evaluation}},
  title       = {Evaluation of the Integrated Food Security Phase Classification ({IPC}) Global Strategic Programme ({GSP}) 2019--2022},
  institution = {Food and Agriculture Organization of the United Nations},
  type        = {Programme Evaluation Series},
  number      = {10/2022},
  address     = {Rome},
  year        = {2022}
}

@article{brown2020foodsec,
  author  = {Brown, Molly E. and Backer, David and Billing, Trey and White, Peter and Grace, Kathryn and Doocy, Shannon and Huth, Paul},
  title   = {Empirical studies of factors associated with child malnutrition: highlighting the evidence about climate and conflict shocks},
  journal = {Food Security},
  year    = {2020},
  volume  = {12},
  number  = {6},
  pages   = {1241--1252},
  doi     = {10.1007/s12571-020-01041-y}
}

@article{michelson2026,
  author  = {Michelson, Hope and Lentz, Erin and Armstrong, John and Korpi, Kaija},
  title   = {The integrated food security phase classification system: seven defining characteristics},
  journal = {Food Policy},
  year    = {2026},
  volume  = {142},
  pages   = {103134},
  doi     = {10.1016/j.foodpol.2026.103134}
}
```
