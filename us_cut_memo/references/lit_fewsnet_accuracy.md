# Literature review: accuracy of FEWS NET projections and IPC/CH classifications

Compiled 2026-09-30 for the FEWS NET concept note. Scope: (a) evaluations of FEWS NET projection accuracy; (b) evaluations of IPC / Cadre Harmonisé (CH) classification accuracy and consistency; (c) statistical / ML food-crisis forecasting that benchmarks against FEWS NET; (d) the politics of IPC classification; (e) validation of phases against independent outcomes (anthropometry, mortality, household surveys).

**Verification key.** [V-full] = numbers read from the full text in this session. [V-abs] = verified from abstract / publisher metadata only. [V-sec] = reported via a secondary source (named). [NV] = not verified in this session (from prior knowledge; check before citing).

---

## A. Direct evaluations of FEWS NET projection accuracy

All studies in this section score FEWS NET projections against **FEWS NET's own later "Current Situation" (CS) classification**, not against an independent outcome. That point matters for everything below.

### 1. Choularton & Krishnamurthy (2019): Ethiopia
- **Citation:** Choularton, R.J. & Krishnamurthy, P.K. (2019). How accurate is food security early warning? Evaluation of FEWS NET accuracy in Ethiopia. *Food Security* 11(2): 333–344. https://doi.org/10.1007/s12571-019-00909-y (open access, CC-BY)
- **Method/findings:** Ethiopia, Jan 2011 to Jun 2017. Compares FEWS NET projected IPC-compatible phases with later CS classifications by area. Reports "high levels of accuracy in the system overall", with accuracy higher in the west and lower in the food-insecure northeast (thin data, high vulnerability). Accuracy fell significantly during the 2015/16 El Niño, and forecasting of transitions from food security into crisis was mixed. [V-abs] I could not get the full text (Springer blocked automated access), so **I have no headline percentage for this paper**. The companion Greater Horn paper (item 2) puts Ethiopia at about 85%.
- **Relevance:** First peer-reviewed accuracy study. It shows that accuracy is worst where and when it matters most: extreme climate events and the most vulnerable zones.

### 2. Krishnamurthy, Choularton & Kareiva (2020): Greater Horn of Africa
- **Citation:** Krishnamurthy, P.K., Choularton, R.J. & Kareiva, P. (2020). Dealing with uncertainty in famine predictions: How complex events affect food security early warning skill in the Greater Horn of Africa. *Global Food Security* 26: 100374. https://doi.org/10.1016/j.gfs.2020.100374
- **Method/findings:** Covers 2011–2019 in six countries. Compares **ML2 (medium-term) projections** against later CS, after adding back the humanitarian-assistance adjustment. Accuracy by country: South Sudan 80%, Ethiopia and Somalia 85%, Sudan 90%, Kenya 92%, Uganda 95%. By livelihood: cropping 95%, agropastoral 82%, pastoral 78%. **63% of errors were under-estimates ("missed crises") and 37% false alarms.** Of 3,014 transitions into IPC 3+, **65% (1,949) were correctly anticipated.** Areas with frequent transitions were forecast better (R = 0.84), and one-off crises tended to be missed. 79% of errors were linked to drought mis-forecasts, 13% to conflict. Accuracy correlates with seasonal climate-forecast skill (R = 0.49) and negatively with conflict (R = −0.33). Conflict-affected South Sudan counties scored below 70%, some as low as 52%. Strong-ENSO years scored 64% vs 84% in other years. [V-full, from the dissertation chapter (Krishnamurthy Reddiar 2020, UCLA, https://escholarship.org/uc/item/22b4c3x1). The published version may differ slightly. Areas "consistently food secure" were excluded from the sample.]
- **Relevance:** The most useful published breakdown of error direction and crisis-onset detection. Note that it finds **net under-prediction**, which contradicts Backer & Billing's over-projection finding. The difference probably comes from sample definition (areas that are always food secure dropped) and the humanitarian-assistance adjustment.

### 3. Backer & Billing (2021): 25 African countries
- **Citation:** Backer, D. & Billing, T. (2021). Validating Famine Early Warning Systems Network projections of food security in Africa, 2009–2020. *Global Food Security* 29: 100510. https://doi.org/10.1016/j.gfs.2021.100510. Companion data: Backer & Billing (2021) *Data in Brief* 36: 106999, https://doi.org/10.1016/j.dib.2021.106999
- **Method/findings:** Grid-cell comparison of projections with later CS for 25 African countries, 2009–2020. **84% accurate overall.** Accuracy is above 93% at the lowest phase and "drops sharply with ascending food insecurity, biasing toward over-projection". Over-projection is partly linked to humanitarian responses between reporting cycles, but "even taking those responses into account, over-projection at more serious levels of food insecurity persists to an extent". The patterns also correlate with climate and conflict. Recommends ongoing validation, more transparency and informed use. The paper also notes that FEWS NET ran its own validation but chose not to publish it. [V-abs for the headline numbers. The claim about FEWS NET's unpublished internal validation comes from a search snippet: V-sec, confirm in the full text.]
- **Relevance:** The standard citation for "FEWS NET is about 84% accurate". Headline accuracy is inflated by the large share of stable Phase 1–2 cells, and skill is weakest in the high phases.

### 4. Bertetti, Agnolucci, Calzadilla & Capra (2024): "independent evaluation"
- **Citation:** Bertetti, M., Agnolucci, P., Calzadilla, A. & Capra, L. (2024). An independent evaluation of the Famine Early Warning Systems Network food security projections. arXiv:2410.09384. https://arxiv.org/abs/2410.09384 (preprint; journal publication not verified)
- **Method/findings:** 24 African countries plus Yemen, Feb 2016 to Sep 2023. Compares **ML1 (near-term) only** with the next report's CS at admin-by-livelihood-zone level. **78% accuracy overall; 98.7% within ±1 phase.** Somalia scores 57% and South Sudan 60%; Uganda and Cameroon about 92%. Accuracy was about 3 points lower from 2020 onward, with COVID-era over-estimation. **Naive baselines score close to FEWS NET:** last-period persistence 76%, max of previous two 74%, same period last year 67%. There is no breakdown of error direction, no Phase 3+ or transition analysis, and no treatment of the humanitarian-assistance flag. The authors considered and rejected validating against FCS. [V-full, via arXiv HTML]
- **Relevance:** **The key persistence-baseline result: FEWS NET beats "no change" by only about 2 percentage points on overall accuracy.** Despite the title, the ground truth is still FEWS NET's own CS.

### 5. Andrée, Chamorro, Kraay, Spencer & Wang (2020): World Bank "Predicting Food Crises"
- **Citation:** Andrée, B.P.J., Chamorro, A., Kraay, A., Spencer, P. & Wang, D. (2020). *Predicting Food Crises*. World Bank Policy Research Working Paper 9412. https://documents1.worldbank.org/curated/en/304451600783424495/pdf/Predicting-Food-Crises.pdf. Data: World Bank Microdata Library, catalog 3811 (https://microdata.worldbank.org/index.php/catalog/3811).
- **Method/findings:** Uses FEWS NET data for 1,162 admin-2 districts in 21 countries, 2009–2020. Target is **onset of crisis (IPC 3+) in districts previously below crisis**. Outcomes and outlooks are both netted of humanitarian assistance using FEWS NET's "!" flag. Binarised FEWS NET outlooks as a benchmark (Table 3): **near-term FNR 74.3%, FPR 1.4%; medium-term FNR 79.4%, FPR 2.2%.** In other words, FEWS NET outlooks missed about three-quarters of new crisis onsets but almost never raised a false alarm. Transitions into crisis made up 5.3% of observations, while outlooks projected a transition only 3.2% of the time. A random forest with a false-alarm-averse weighting (w = 1/3) cut FNR to about 20% at 4-, 8- and 12-month horizons with FPR of about 7%. [V-full]
- **Relevance:** **The strongest quantitative evidence of systematic conservatism in FEWS NET on crisis onset.** It is also the template for ML benchmarking. Note that both the target and the benchmark are FEWS NET products.

### 6. Wang, Andrée, Chamorro & Spencer (2020 / 2022): follow-ups
- **Citations:** Wang, D., Andrée, B.P.J., Chamorro, A. & Spencer, P.G. (2020). *Stochastic Modeling of Food Insecurity*. World Bank PRWP 9413. https://documents1.worldbank.org/curated/en/911801600788869914/pdf/Stochastic-Modeling-of-Food-Insecurity.pdf; and Wang et al. (2022). Transitions into and out of food insecurity: A probabilistic approach with panel data evidence from 15 countries. *World Development* 159: 106035. https://doi.org/10.1016/j.worlddev.2022.106035
- **Findings:** Markov-type models of FEWS NET IPC transitions. Dynamics are asymmetric and path-dependent: worsening is more likely than recovery. [V-abs] No FEWS NET accuracy numbers found in the abstracts.
- **Relevance:** Explains why persistence baselines are hard to beat.

### 7. Seyffer et al. (2026): FEWS NET vs IPC in Somalia
- **Citation:** Seyffer, F., Schauss, A., Tirai, S., Maurer, M., Lautenbach, S. & Zipf, A. (2026). Food insecurity projections for anticipatory action: A comparative spatiotemporal analysis of FEWS NET and the IPC in Somalia. *AGILE GIScience Series* 7: 17. https://doi.org/10.5194/agile-giss-7-17-2026
- **Findings:** Somalia, 2017–2025. The two systems' current assessments are very consistent. Their projections diverge: FEWS NET projects Emergency and Famine more often. **Projection-vs-later-assessment agreement is 61.8% for FEWS NET and 64.5% for IPC.** Both show a "precautionary" tendency to over-project severe phases. [V-sec, from the HeiGIT summary page; horizon details not verified]
- **Relevance:** In the hardest context, both systems' projections do little better than a coin-flip-plus. It is also the first paired comparison of FEWS NET and IPC projections.

### 8. FEWS NET internal / USAID assessments
- I found **no publicly posted FEWS NET "accuracy assessment" report**. FEWS NET publishes methods guidance: scenario development, price projections, and integrating malnutrition and mortality (https://fews.net/about/projections; https://fews.net/sites/default/files/documents/reports/Guidance_Document_Scenario_Development_2018.pdf; https://fews.net/sites/default/files/documents/reports/Guidance_Document_Malnutrition_2018.pdf). Backer & Billing reportedly state that FEWS NET ran an internal validation and did not release it [V-sec]. A FEWS NET science overview exists (Funk et al. 2019, *BAMS* 100(6): 1011–1027 [NV]), but it is not an accuracy evaluation. **Treat "FEWS NET internal accuracy reports" as unverified / not public.**

---

## B. ML / statistical forecasting benchmarked against FEWS NET

### 9. Lentz, Michelson, Baylis & Zhou (2019): Malawi
- **Citation:** Lentz, E.C., Michelson, H., Baylis, K. & Zhou, Y. (2019). A data-driven approach improves food insecurity crisis prediction. *World Development* 122: 399–409. https://doi.org/10.1016/j.worlddev.2019.06.008. Code/data: https://github.com/zhou100/WD-Early-Warning-Food-Insecurity
- **Method/findings:** **The rare study whose outcome is independent household survey data.** Village-cluster means of FCS, HDDS and rCSI from the Malawi LSMS/IHS 2010–11 (training) and 2013 (out-of-sample). Predictors are prices, rainfall, geography and demographics, fitted by OLS and lasso. The benchmark ("Class 0") uses the **IPC (FEWS NET) zone classification as the only predictor**. Out of sample, the IPC classification explains **0.0% of variation in HDDS, 0.5% of log FCS and 1.6% of rCSI**. The model explains 64%, 65% and 12%. For the most food-insecure clusters, IPC identifies 0–10%, the model 83–99%. [V-full]
- **Relevance:** **The most direct existing evidence that IPC phases (as produced by FEWS NET) barely track household-survey food security.** It covers one country and two survey rounds, and cluster means of household indicators are not the IPC's area-level construct.

### 10. Balashankar, Subramanian & Fraiberger (2023): news streams
- **Citation:** Balashankar, A., Subramanian, L. & Fraiberger, S.P. (2023). Predicting food crises using news streams. *Science Advances* 9(9): eabm3449. https://doi.org/10.1126/sciadv.abm3449
- **Findings:** Deep-learning features from 11.2 million news articles, July 2009 to July 2020, 21 countries, district level. News indicators "substantially improve" predictions of FEWS NET IPC phase up to 12 months ahead compared with models without text. Builds on the Andrée et al. random-forest set-up. [V-abs; specific AUC/recall gains not verified]
- **Relevance:** The target is again FEWS NET's own classification.

### 11. Busker et al. (2024): Horn of Africa XGBoost
- **Citation:** Busker, T., van den Hurk, B., de Moel, H., van den Homberg, M., van Straaten, C., Odongo, R.A. & Aerts, J.C.J.H. (2024). Predicting food-security crises in the Horn of Africa using machine learning. *Earth's Future* 12(8): e2023EF004211. https://doi.org/10.1029/2023EF004211
- **Findings:** Trained on FEWS NET CS using more than 20 datasets. R² > 0.6 at 3 months. **Only 20% of crisis onsets in pastoral zones (n = 96) and 20–50% in agro-pastoral zones (n = 22) were predicted at 3-month lead.** Compared with FEWS NET's 8-month outlooks over 2019–2022, performance was similar in pastoral and agro-pastoral zones and clearly worse than FEWS NET in cropping zones. [V-abs]
- **Relevance:** ML does not clearly beat FEWS NET, and crisis onsets are hard for everyone.

### 12. Machefer et al. (2025): JRC harmonised dataset and ML limits
- **Citations:** Machefer, M., Ronco, M., Thomas, A.-C., Assouline, M., Rabier, M., Corbane, C. & Rembold, F. (2025). A monthly sub-national Harmonized Food Insecurity Dataset for comprehensive analysis and predictive modeling. arXiv:2501.06076. https://arxiv.org/abs/2501.06076. Also Machefer, M., Thomas, A.-C., Meroni, M., Veiga Lopez Pena, J.M., Ronco, M., Corbane, C. & Rembold, F. (2025). Potential and limitations of machine learning modeling for forecasting Acute Food Insecurity. *Global Food Security* 45: 100859. https://doi.org/10.1016/j.gfs.2025.100859
- **Findings (HFID):** 311,838 records, 80 countries, 2007 onward. Harmonises IPC/CH, FEWS NET, WFP FCS and rCSI. **12,618 area-months have both FEWS NET and IPC/CH phases (22 countries). FEWS NET phases run systematically lower than IPC/CH.** Correlations of phase with FCS: 0.73 (FEWS) and 0.53 (IPC/CH) using literature/survey FCS; about 0.02 using WFP real-time FCS. rCSI correlations are 0.45 and 0.39. [V-full, via arXiv HTML] **Findings (GFS paper):** not verified. Access to the full text was blocked.
- **Relevance:** Useful infrastructure. Correlations between phase and household indicators are moderate at best and near zero for real-time monitoring data.

### 13. Other forecasting studies (lower priority)
- Constenla-Villoslada, S., Liu, Y., McBride, L., Ouma, C., Mutanda, N. & Barrett, C.B. (2025). High-frequency monitoring enables machine learning–based forecasting of acute child malnutrition for early warning. *PNAS* 122(23): e2416161122. https://doi.org/10.1073/pnas.2416161122. Forecasts **child anthropometry** (Kenya NDMA sentinel sites) rather than IPC phase, and notes that earlier models "exhibited low predictive skill" for acute malnutrition. [V-abs] It is relevant as a model for anthropometric outcomes, but it does not validate FEWS NET.
- Herteux, J. et al. (2024). Forecasting trends in food security with real time data. *Communications Earth & Environment* 5. https://doi.org/10.1038/s43247-024-01698-9. Forecasts WFP HungerMap FCS 60 days ahead in Mali, Nigeria, Syria and Yemen. No FEWS NET benchmark. [V-abs]
- Pedersen, T.D.S. (2026). CERES: A probabilistic early warning system for acute food insecurity. arXiv:2603.09425. Commits to public prospective verification. Only in-sample checks so far. [V-abs]
- Ahn, Y. et al. (2023). HungerGist. arXiv:2311.10953. News-only model. [V-abs]
- Mehboob, S. et al. (2026). Beyond prediction: Data, baselines, explanation, and causation in machine learning for food insecurity. *Food Safety and Health*. https://doi.org/10.1002/fsh3.70122. A review arguing that ML work must benchmark against **persistence and climatology** under blocked validation. [V-abs]

---

## C. IPC / CH accuracy, consistency and undercounting

### 14. Lentz, Baylis, Michelson & Kim (2024): IPC Accuracy Study (commissioned by IPC)
- **Citation:** Lentz, E., Baylis, K., Michelson, H. & Kim, C. (2024). *IPC Accuracy Study: Analyzing the internal consistency of the IPC AFI and AMN analyses.* IPC Global Support Unit. https://www.ipcinfo.org/ipcinfo-website/resources/resources-details/en/c/1156988/ (page blocked to automated fetch)
- **Findings:** The first external accuracy study commissioned by the IPC, in 2022. It treats IPC outcomes as latent, so it tests **internal consistency** only. Technical Working Groups classify fewer people as food insecure when the underlying indicators are noisier. **No evidence of systematic over- or under-prediction of IPC projections relative to later current analyses.** Acute malnutrition results are only "proof of concept". [V-sec, from search snippets and the Rose & Collins 2025 description]

### 15. Lentz, Baylis, Michelson & Kim (2025): Nature Food undercount paper
- **Citation:** Lentz, E., Baylis, K., Michelson, H. & Kim, C. (2025). Official estimates of global food insecurity undercount acute hunger. *Nature Food* 6(12): 1196–1208. https://doi.org/10.1038/s43016-025-01267-z (PMC12717001). Commentary: Barrett, C.B. (2025). Second best underestimates of malnutrition in an era of multiplying food crises. *Nature Food* (News & Views). https://doi.org/10.1038/s43016-025-01274-0
- **Findings:** About 10,000 subnational IPC analyses, 33 countries, 2017–2023. The counterfactual is the average of the TWG's own input indicators (FCS, HDDS, HHS, LCS, rCSI). **IPC counts 226.9m people in Phase 3+; the indicator average gives 293.1m. The gap of 66.2m is about one in five of the true total (29% relative to the IPC figure).** There are 46% more areas just under the 20% Phase-3 threshold than the counterfactual predicts (bunching). About 46% of areas classified as Phase 2 "should probably" be Phase 3+. Undercounting grows when indicators disagree. A worst-indicator ("right to food") benchmark implies undercounting of more than one in two. The paper does not compare with anthropometry or mortality, does not mention FEWS NET, and does not analyse projections. [V-full, via PMC]
- **Relevance:** Strong evidence of **downward consensus bias in current classifications**. The benchmark is the IPC's own inputs, not independent outcomes.

### 16. Rose & Collins (2025): CARI–IPC alignment (WFP-sponsored)
- **Citation:** Rose, D. & Collins, S. (2025). *Examining the Alignment of the CARI and IPC Food Security Assessment Systems.* Tulane / WFP VAM. https://sph.tulane.edu/sites/default/files/2025-11/cari_ipc_alignment_study.pdf
- **Findings:** 1,044 areas in 11 countries. Area-level alignment is "moderate". CARI gives **42% mean prevalence in high-risk classes vs 29% in IPC Phase 3–4 (14-point gap)**, with a regression slope of 0.40 and R² of 0.38. At country level, CARI detects Phase 3+ countries with 80% sensitivity and 86% specificity. Directionally consistent with the IPC Accuracy Study in 7 of 8 overlapping countries: IPC is more conservative. [V-full]

### 17. FAO Office of Evaluation (2022): Evaluation of the IPC
- FAO (2022). *Evaluation of the Integrated Food Security Phase Classification (IPC)*. Programme Evaluation Series 10/2022. https://openknowledge.fao.org/server/api/core/bitstreams/0895bc1b-af40-434d-866b-56d80230f70d/content. [NV: not read; located via search only]

---

## D. Politics of classification, and the Somalia 2011 retrospectives

### 18. Maxwell & Hailey (2020 report; 2021 article)
- **Citations:** Maxwell, D. & Hailey, P. (2020). *The Politics of Information and Analysis in Famines and Extreme Emergencies: Synthesis of Findings from Six Case Studies.* Feinstein International Center, Tufts. https://fic.tufts.edu/wp-content/uploads/PIA-Synthesis-Report_May-13.pdf. Also Maxwell, D. & Hailey, P. (2021). Analysing famine: The politics of information and analysis in food security crises. *Journal of Humanitarian Affairs* 3(1): 16–27. https://doi.org/10.7227/JHA.055
- **Findings:** Six cases (Ethiopia, Kenya, Nigeria, Somalia, South Sudan, Yemen), based on key-informant interviews 2017–2019. The data most often missing were **mortality** (South Sudan, Nigeria, Yemen, Kenya), population, displacement, and **nutrition (almost all cases)**. Mortality is "the most politically charged" information, and its absence "makes any judgement of famine a matter of speculation". In Nigeria (2016), a likely famine was identified **retrospectively by FEWS NET**, not by the Cadre Harmonisé. "The politics of information and analysis are the most fraught where technical capacity and data quality are the weakest." [V-full for the report excerpts; V-abs for the article]
- **Follow-up:** Maxwell, D., Hailey, P. & Naumova, E. (2026). Data for famine and extreme emergencies: challenges and opportunities. *Journal of Public Health Policy* 47(S1): 148–160. https://doi.org/10.1057/s41271-026-00639-4. Points to a "left-skewed but truncated" distribution of phase populations with almost no Phase 5, and to structural missingness of SMART data. [V-sec, via PMC summary]

### 19. Somalia 2011 (*Global Food Security* special issue, vol. 1(1), 2012)
- Hillbruner, C. & Moloney, G. (2012). When early warning is not enough: Lessons learned from the 2011 Somalia famine. *GFS* 1(1): 20–28. https://doi.org/10.1016/j.gfs.2012.08.001. FEWS NET and FSNAU warnings were timely and of high quality. The failure was the **lack of incentives for early action**. [V-abs]
- Maxwell, D. & Fitzpatrick, M. (2012). The 2011 Somalia famine: Context, causes, and complications. *GFS* 1(1): 5–12. https://doi.org/10.1016/j.gfs.2012.07.002 [V-abs, citation only]
- Salama, P., Moloney, G., Bilukha, O.O., Talley, L., Maxwell, D., Hailey, P., Hillbruner, C., Masese-Mwirigi, L., Odundo, E. & Golden, M.H. (2012). Famine in Somalia: Evidence for a declaration. *GFS* 1(1): 13–19. https://doi.org/10.1016/j.gfs.2012.08.002. The first FEWS NET drought warning came in **August 2010**. FEWS NET, FSNAU and WFP first raised the possibility of famine in **March 2011**. Famine was declared on 20 July 2011. In 16 SMART surveys, **GAM exceeded 30% in 11 and CDR exceeded 2/10,000/day in 5**. [V-full] This is the clearest case where the famine phase was **confirmed by independent anthropometry and mortality**, and the forecast was directionally right.
- Checchi, F. & Robinson, W.C. (2013). *Mortality among populations of southern and central Somalia affected by severe food insecurity and famine during 2010–2012.* FAO/FSNAU and FEWS NET. Estimates about **258,000 excess deaths**, about half of them children under 5. [NV: figure also cited in the Hillbruner & Moloney search snippet]

### 20. Recent political episodes (news sources; not peer-reviewed)
- **Gaza, Dec 2024:** FEWS NET issued an alert that famine thresholds were likely being crossed in north Gaza and **withdrew it after the US ambassador to Israel (Jacob Lew) and USAID objected publicly** (AP/VOA, 26 Dec 2024: https://www.voanews.com/a/us-says-it-pushed-retraction-of-famine-warning-for-north-gaza-/7915491.html). IPC later published a Famine Review Committee (FRC) confirmation of famine in Gaza Governorate (Aug 2025) and a "Response to issues raised" document (https://www.ipcinfo.org/fileadmin/user_upload/ipcinfo/docs/Response_to_Issues_Raised_Following_IPC_Famine_Classification_in_the_Gaza_Strip.pdf). [V-sec for the retraction; FRC details NV]
- **Tigray, 2021:** The IPC found about 350,000–400,000 people in Phase 5 (catastrophe), but no famine classification was made. Mark Lowcock said the Ethiopian government slowed "the whole declaration system" (Devex: https://www.devex.com/news/mark-lowcock-ethiopian-government-blocked-tigray-famine-declaration-103410). [V-sec]
- **Sudan 2024:** FRC famine finding for Zamzam camp (Aug 2024); the government withdrew from the IPC in Dec 2024. [NV]
- **FEWS NET shutdown, 2025:** FEWS NET went offline in early 2025 during the USAID funding freeze (NPR, 21 Feb 2025: https://www.npr.org/sections/goats-and-soda/2025/02/21/nx-s1-5301043/famine-usaid-warning-ethiopia; NPR follow-up 1 Sep 2026). [V-sec]
- Jaspars, S. & Kuol, L. (2024). Famine and food security: new trends and systems or politics as usual? *Disasters* 49(1). https://doi.org/10.1111/disa.12669. Special-issue introduction. [V-abs]

---

## E. Validation against independent outcomes (anthropometry, mortality, household surveys): the claimed gap

What I found:
1. **Lentz et al. (2019), Malawi.** IPC/FEWS NET zone phase vs LSMS household FCS, HDDS and rCSI, out of sample. IPC explains roughly 0–2% of variation. **This is the only study I found that tests FEWS NET/IPC classifications against independent household survey outcomes out of sample.**
2. **HFID (Machefer et al. 2025).** Cross-sectional correlations between phase and FCS/rCSI (0.4–0.7 for survey-based indicators, about 0 for WFP real-time FCS). But the survey FCS is often an input to the same IPC analysis, so this is not independent.
3. **Lentz et al. (2025, Nature Food); IPC Accuracy Study (2024); Rose & Collins (2025).** Compare the consensus phase with household indicators. These are the TWG's own inputs (or WFP's CARI from the same surveys), so they test aggregation and consensus bias, not predictive validity.
4. **Salama et al. (2012).** An anthropometry and mortality confirmation of one famine declaration (Somalia 2011). This is a case study, not a systematic validation.
5. **Household food-security indicator comparability** (the underlying measurement problem): Maxwell, D., Vaitla, B. & Coates, J. (2014). How do indicators of household food insecurity measure up? An empirical comparison from Ethiopia. *Food Policy* 47: 107–116. https://doi.org/10.1016/j.foodpol.2014.04.003 [DOI NV]. Seven indicators gave very different prevalence levels but were moderately correlated and showed similar trends. Vaitla, B., Coates, J., Glaeser, L., Hillbruner, C., Biswal, P. & Maxwell, D. (2017). The measurement of household food security: Correlation and latent variable analysis of alternative indicators in a large multi-country dataset. *Food Policy* 68: 193–205. https://doi.org/10.1016/j.foodpol.2017.02.006. FCS/HDDS and rCSI/HHS load on two different dimensions. [V-abs]
6. **Constenla-Villoslada et al. (2025, PNAS).** Forecast anthropometry directly, but they do not test whether FEWS NET/IPC phases predict it.

What I did **not** find, despite targeted searches: any systematic study linking FEWS NET or IPC area phases (current or projected) to **subsequent DHS or SMART child wasting (GAM), under-5 or crude mortality**, or independent household consumption surveys, across many countries. I also found no Headey paper on this. IPC acute malnutrition (AMN) phases are *defined* by GAM, so any AFI-vs-AMN comparison inside IPC is partly definitional. **The gap claimed in the concept note appears to be real.** Caveat: my web-search budget ran out before a final sweep of DHS-linkage papers, grey literature from FSNAU/UNICEF, and the full texts of Machefer et al. (2025, GFS) and the IPC Accuracy Study.

---

## Synthesis (about 450 words)

**What is known.** At least five quantitative evaluations of FEWS NET projections exist: Choularton & Krishnamurthy 2019, Krishnamurthy et al. 2020, Backer & Billing 2021, Andrée et al. 2020 and Bertetti et al. 2024. They agree that headline phase accuracy is high: 78–92% depending on sample, horizon and region, and nearly all errors are within one phase. They also agree that skill falls exactly where it matters. It is lower in pastoral and conflict-affected zones (Somalia 57–62%, South Sudan 60–80%), during strong ENSO years (64% vs 84%), and at higher severity. Evaluations of IPC/CH classifications show a parallel pattern in levels: consensus estimates sit below what the TWGs' own indicators imply (about 66m people, or one in five, missing globally), with bunching just below the 20% Phase-3 threshold.

**Main critiques.**
1. **Self-validation.** Every FEWS NET accuracy study uses FEWS NET's own later Current Situation as ground truth. The same analysts, the same convergence-of-evidence method and the same data gaps produce both the forecast and the "outcome". Agreement therefore partly measures internal consistency.
2. **Persistence baselines.** Phases are highly autocorrelated. Once the benchmark is "no change", FEWS NET's edge nearly vanishes: 78% vs 76% for last-period persistence (Bertetti et al.). Headline accuracy is dominated by stable Phase 1–2 areas.
3. **Conservatism on onsets.** Scored on *new* crises, FEWS NET outlooks miss about 74–79% of transitions into IPC 3+ while almost never raising a false alarm (Andrée et al.). Krishnamurthy et al. find 35% of transitions to 3+ missed and 63% of all errors being under-predictions. The IPC consensus-undercount results point the same way.
4. **Aid-conditional forecasts.** Projections assume planned assistance, and outcomes are affected by assistance delivered. Over-projection at high phases (Backer & Billing; Seyffer et al. for Somalia) may reflect successful response, false alarms, or both. The "!" flag is a coarse fix, and the studies disagree on the net direction of bias depending on how they handle it.
5. **Extremes and politics.** Famine-level outcomes are rare, data-poor and politically contested (Tigray, Gaza, Sudan, Nigeria 2016). Missing mortality and nutrition data are the norm in precisely those cases (Maxwell & Hailey).

**The genuine gap.** No systematic, multi-country study validates FEWS NET or IPC phases, current or projected, against **independent outcomes**: DHS/SMART wasting, mortality surveys, or household consumption surveys not used in the analysis. The closest is Lentz et al. (2019). In one country, IPC zone phases explained essentially none (≤2%) of the out-of-sample variation in LSMS household food-security measures. ML forecasting work does not fill the gap, because it almost always trains and scores on FEWS NET's own classifications. A study linking geocoded DHS/SMART anthropometry and mortality to contemporaneous and lagged FEWS NET/IPC phases, with persistence and ML baselines and explicit handling of humanitarian assistance, would be new.

---

## BibTeX

```bibtex
@article{choularton2019,
  author  = {Choularton, Richard J. and Krishnamurthy, P. Krishna},
  title   = {How accurate is food security early warning? Evaluation of {FEWS NET} accuracy in {Ethiopia}},
  journal = {Food Security},
  volume  = {11},
  number  = {2},
  pages   = {333--344},
  year    = {2019},
  doi     = {10.1007/s12571-019-00909-y}
}

@article{krishnamurthy2020,
  author  = {Krishnamurthy, P. Krishna and Choularton, Richard J. and Kareiva, Peter},
  title   = {Dealing with uncertainty in famine predictions: How complex events affect food security early warning skill in the {Greater Horn of Africa}},
  journal = {Global Food Security},
  volume  = {26},
  pages   = {100374},
  year    = {2020},
  doi     = {10.1016/j.gfs.2020.100374}
}

@phdthesis{krishnamurthy2020diss,
  author = {Krishnamurthy Reddiar, Prasanna Krishna},
  title  = {Food Security Tipping Points: Using remote sensing to improve famine early warning systems},
  school = {University of California, Los Angeles},
  year   = {2020},
  url    = {https://escholarship.org/uc/item/22b4c3x1}
}

@article{backer2021,
  author  = {Backer, David and Billing, Trey},
  title   = {Validating {Famine Early Warning Systems Network} projections of food security in {Africa}, 2009--2020},
  journal = {Global Food Security},
  volume  = {29},
  pages   = {100510},
  year    = {2021},
  doi     = {10.1016/j.gfs.2021.100510}
}

@article{backer2021data,
  author  = {Backer, David and Billing, Trey},
  title   = {Visualizing trends in food security across {Africa}, 2009--2020: Data and animations at a grid-cell level},
  journal = {Data in Brief},
  volume  = {36},
  pages   = {106999},
  year    = {2021},
  doi     = {10.1016/j.dib.2021.106999}
}

@misc{bertetti2024,
  author        = {Bertetti, Marco and Agnolucci, Paolo and Calzadilla, Alvaro and Capra, Licia},
  title         = {An independent evaluation of the {Famine Early Warning Systems Network} food security projections},
  year          = {2024},
  eprint        = {2410.09384},
  archivePrefix = {arXiv},
  url           = {https://arxiv.org/abs/2410.09384}
}

@techreport{andree2020,
  author      = {Andr{\'e}e, Bo Pieter Johannes and Chamorro, Andres and Kraay, Aart and Spencer, Phoebe and Wang, Dieter},
  title       = {Predicting Food Crises},
  institution = {World Bank},
  type        = {Policy Research Working Paper},
  number      = {9412},
  year        = {2020},
  url         = {https://documents1.worldbank.org/curated/en/304451600783424495/pdf/Predicting-Food-Crises.pdf}
}

@techreport{wang2020,
  author      = {Wang, Dieter and Andr{\'e}e, Bo Pieter Johannes and Chamorro, Andres and Spencer, Phoebe Girouard},
  title       = {Stochastic Modeling of Food Insecurity},
  institution = {World Bank},
  type        = {Policy Research Working Paper},
  number      = {9413},
  year        = {2020}
}

@article{wang2022,
  author  = {Wang, Dieter and Andr{\'e}e, Bo Pieter Johannes and Chamorro, Andres and Spencer, Phoebe Girouard},
  title   = {Transitions into and out of food insecurity: A probabilistic approach with panel data evidence from 15 countries},
  journal = {World Development},
  volume  = {159},
  pages   = {106035},
  year    = {2022},
  doi     = {10.1016/j.worlddev.2022.106035}
}

@article{seyffer2026,
  author  = {Seyffer, F. and Schauss, A. and Tirai, S. and Maurer, M. and Lautenbach, S. and Zipf, A.},
  title   = {Food insecurity projections for anticipatory action: A comparative spatiotemporal analysis of {FEWS NET} and the {IPC} in {Somalia}},
  journal = {AGILE: GIScience Series},
  volume  = {7},
  pages   = {17},
  year    = {2026},
  doi     = {10.5194/agile-giss-7-17-2026}
}

@article{lentz2019,
  author  = {Lentz, Erin C. and Michelson, Hope and Baylis, Katherine and Zhou, Yang},
  title   = {A data-driven approach improves food insecurity crisis prediction},
  journal = {World Development},
  volume  = {122},
  pages   = {399--409},
  year    = {2019},
  doi     = {10.1016/j.worlddev.2019.06.008}
}

@article{balashankar2023,
  author  = {Balashankar, Ananth and Subramanian, Lakshminarayanan and Fraiberger, Samuel P.},
  title   = {Predicting food crises using news streams},
  journal = {Science Advances},
  volume  = {9},
  number  = {9},
  pages   = {eabm3449},
  year    = {2023},
  doi     = {10.1126/sciadv.abm3449}
}

@article{busker2024,
  author  = {Busker, Tim and van den Hurk, Bart and de Moel, Hans and van den Homberg, Marc and van Straaten, Chiem and Odongo, Rhoda A. and Aerts, Jeroen C. J. H.},
  title   = {Predicting food-security crises in the {Horn of Africa} using machine learning},
  journal = {Earth's Future},
  volume  = {12},
  number  = {8},
  pages   = {e2023EF004211},
  year    = {2024},
  doi     = {10.1029/2023EF004211}
}

@misc{machefer2025hfid,
  author        = {Machefer, M{\'e}lissande and Ronco, Michele and Thomas, Anne-Claire and Assouline, Michael and Rabier, Melanie and Corbane, Christina and Rembold, Felix},
  title         = {A monthly sub-national Harmonized Food Insecurity Dataset for comprehensive analysis and predictive modeling},
  year          = {2025},
  eprint        = {2501.06076},
  archivePrefix = {arXiv}
}

@article{machefer2025ml,
  author  = {Machefer, M{\'e}lissande and Thomas, Anne-Claire and Meroni, Michele and Veiga Lopez Pena, Jose Manuel and Ronco, Michele and Corbane, Christina and Rembold, Felix},
  title   = {Potential and limitations of machine learning modeling for forecasting Acute Food Insecurity},
  journal = {Global Food Security},
  volume  = {45},
  pages   = {100859},
  year    = {2025},
  doi     = {10.1016/j.gfs.2025.100859}
}

@article{constenla2025,
  author  = {Constenla-Villoslada, Sof{\'i}a and Liu, Yanyan and McBride, Linden and Ouma, Collins and Mutanda, Nicholas and Barrett, Christopher B.},
  title   = {High-frequency monitoring enables machine learning--based forecasting of acute child malnutrition for early warning},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {122},
  number  = {23},
  pages   = {e2416161122},
  year    = {2025},
  doi     = {10.1073/pnas.2416161122}
}

@article{herteux2024,
  author  = {Herteux, Joschka and R{\"a}th, Christoph and Martini, Giulia and Baha, Amine and Koupparis, Kyriacos and Lauzana, Ilaria and Piovani, Duccio},
  title   = {Forecasting trends in food security with real time data},
  journal = {Communications Earth \& Environment},
  volume  = {5},
  year    = {2024},
  doi     = {10.1038/s43247-024-01698-9}
}

@misc{pedersen2026,
  author        = {Pedersen, Tom Danny S.},
  title         = {{CERES}: A Probabilistic Early Warning System for Acute Food Insecurity},
  year          = {2026},
  eprint        = {2603.09425},
  archivePrefix = {arXiv}
}

@article{mehboob2026,
  author  = {Mehboob, S. and Abdullah, A. and Kumar, G. and Memon, S. and Afghan, N.},
  title   = {Beyond Prediction: Data, Baselines, Explanation, and Causation in Machine Learning for Food Insecurity},
  journal = {Food Safety and Health},
  year    = {2026},
  doi     = {10.1002/fsh3.70122}
}

@techreport{lentz2024ipcaccuracy,
  author      = {Lentz, Erin and Baylis, Kathy and Michelson, Hope and Kim, Chungmann},
  title       = {{IPC} Accuracy Study: Analyzing the internal consistency of the {IPC} {AFI} and {AMN} analyses},
  institution = {IPC Global Support Unit},
  year        = {2024},
  url         = {https://www.ipcinfo.org/ipcinfo-website/resources/resources-details/en/c/1156988/}
}

@article{lentz2025,
  author  = {Lentz, Erin and Baylis, Kathy and Michelson, Hope and Kim, Chungmann},
  title   = {Official estimates of global food insecurity undercount acute hunger},
  journal = {Nature Food},
  volume  = {6},
  number  = {12},
  pages   = {1196--1208},
  year    = {2025},
  doi     = {10.1038/s43016-025-01267-z}
}

@article{barrett2025,
  author  = {Barrett, Christopher B.},
  title   = {Second best underestimates of malnutrition in an era of multiplying food crises},
  journal = {Nature Food},
  year    = {2025},
  doi     = {10.1038/s43016-025-01274-0}
}

@techreport{rose2025,
  author      = {Rose, Diego and Collins, Shalean},
  title       = {Examining the Alignment of the {CARI} and {IPC} Food Security Assessment Systems},
  institution = {Tulane University / World Food Programme VAM},
  year        = {2025},
  url         = {https://sph.tulane.edu/sites/default/files/2025-11/cari_ipc_alignment_study.pdf}
}

@techreport{fao2022ipc,
  author      = {{FAO Office of Evaluation}},
  title       = {Evaluation of the Integrated Food Security Phase Classification ({IPC})},
  institution = {Food and Agriculture Organization of the United Nations},
  type        = {Programme Evaluation Series},
  number      = {10/2022},
  year        = {2022}
}

@techreport{maxwell2020pia,
  author      = {Maxwell, Daniel and Hailey, Peter},
  title       = {The Politics of Information and Analysis in Famines and Extreme Emergencies: Synthesis of Findings from Six Case Studies},
  institution = {Feinstein International Center, Tufts University},
  year        = {2020},
  url         = {https://fic.tufts.edu/wp-content/uploads/PIA-Synthesis-Report_May-13.pdf}
}

@article{maxwell2021,
  author  = {Maxwell, Daniel and Hailey, Peter},
  title   = {Analysing Famine: The Politics of Information and Analysis in Food Security Crises},
  journal = {Journal of Humanitarian Affairs},
  volume  = {3},
  number  = {1},
  pages   = {16--27},
  year    = {2021},
  doi     = {10.7227/JHA.055}
}

@article{maxwell2026,
  author  = {Maxwell, Daniel and Hailey, Peter and Naumova, Elena},
  title   = {Data for famine and extreme emergencies: challenges and opportunities},
  journal = {Journal of Public Health Policy},
  volume  = {47},
  number  = {S1},
  pages   = {148--160},
  year    = {2026},
  doi     = {10.1057/s41271-026-00639-4}
}

@article{hillbruner2012,
  author  = {Hillbruner, Chris and Moloney, Grainne},
  title   = {When early warning is not enough---Lessons learned from the 2011 {Somalia} Famine},
  journal = {Global Food Security},
  volume  = {1},
  number  = {1},
  pages   = {20--28},
  year    = {2012},
  doi     = {10.1016/j.gfs.2012.08.001}
}

@article{maxwell2012,
  author  = {Maxwell, Daniel and Fitzpatrick, Merry},
  title   = {The 2011 {Somalia} famine: Context, causes, and complications},
  journal = {Global Food Security},
  volume  = {1},
  number  = {1},
  pages   = {5--12},
  year    = {2012},
  doi     = {10.1016/j.gfs.2012.07.002}
}

@article{salama2012,
  author  = {Salama, Peter and Moloney, Grainne and Bilukha, Oleg O. and Talley, Leisel and Maxwell, Daniel and Hailey, Peter and Hillbruner, Christopher and Masese-Mwirigi, Louise and Odundo, Elijah and Golden, Michael H.},
  title   = {Famine in {Somalia}: Evidence for a declaration},
  journal = {Global Food Security},
  volume  = {1},
  number  = {1},
  pages   = {13--19},
  year    = {2012},
  doi     = {10.1016/j.gfs.2012.08.002}
}

@techreport{checchi2013,
  author      = {Checchi, Francesco and Robinson, W. Courtland},
  title       = {Mortality among populations of southern and central {Somalia} affected by severe food insecurity and famine during 2010--2012},
  institution = {FAO/FSNAU and FEWS NET},
  year        = {2013},
  note        = {Not verified in this session}
}

@article{jaspars2024,
  author  = {Jaspars, Susanne and Kuol, Luka},
  title   = {Famine and food security: new trends and systems or politics as usual? An introduction},
  journal = {Disasters},
  volume  = {49},
  number  = {1},
  year    = {2024},
  doi     = {10.1111/disa.12669}
}

@article{maxwell2014,
  author  = {Maxwell, Daniel and Vaitla, Bapu and Coates, Jennifer},
  title   = {How do indicators of household food insecurity measure up? An empirical comparison from {Ethiopia}},
  journal = {Food Policy},
  volume  = {47},
  pages   = {107--116},
  year    = {2014},
  note    = {DOI not verified: 10.1016/j.foodpol.2014.04.003}
}

@article{vaitla2017,
  author  = {Vaitla, Bapu and Coates, Jennifer and Glaeser, Laura and Hillbruner, Christopher and Biswal, Preetish and Maxwell, Daniel},
  title   = {The measurement of household food security: Correlation and latent variable analysis of alternative indicators in a large multi-country dataset},
  journal = {Food Policy},
  volume  = {68},
  pages   = {193--205},
  year    = {2017},
  doi     = {10.1016/j.foodpol.2017.02.006}
}

@article{funk2019,
  author  = {Funk, Chris and others},
  title   = {Recognizing the {Famine Early Warning Systems Network}: Over 30 years of drought early warning science advances and partnerships promoting global food security},
  journal = {Bulletin of the American Meteorological Society},
  volume  = {100},
  number  = {6},
  pages   = {1011--1027},
  year    = {2019},
  note    = {Not verified in this session}
}
```
