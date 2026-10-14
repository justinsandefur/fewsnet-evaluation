# Literature check: are household surveys selected toward stable, prosperous country-years?

Searched 2026-10-02. "Reg" means a regression was run; "Desc" means descriptive counts only.

## Closest prior work

**1. Trommlerová, de Vries Mecheva & Rieger (2026), "Disease Data and Development: Evidence from DHS and MICS Surveys," *J. Development Studies* 62(10):1873–1895.** https://doi.org/10.1080/00220388.2026.2640890 — **Reg. The closest match by far.**
- Sample: LMICs, 1982–2016.
- Outcomes: whether a country has any DHS or MICS, the number of surveys, and whether a survey happens in each five-year panel period.
- Models: cross-section, plus panel with country and time FE.
- Covariates: economic (GDP pc), demographic, and political (conflict, democracy, UN voting alignment with the US).
- Findings: conflict is a "strong and consistent" negative predictor of whether a DHS or MICS happens. Economic and demographic factors are "relatively weak." Democracy has an inverted-U relationship with USAID-funded DHS. MICS is negatively and convexly associated with voting alongside the US at the UN. Data-quality predictors are unsystematic.
- Caveats: full text was paywalled (403), so I couldn't get coefficient sizes. The time unit is 5 years, not annual. No LSMS or poverty surveys. No shock variables.

**2. Dang, Jolliffe & Carletto (2019), "Data Gaps, Data Incomparability, and Data Imputation," *J. Economic Surveys* 33(3):757–797** (WB PRWP 8282). https://doi.org/10.1111/joes.12307 — **Reg, but only a bivariate cross-section.**
- Regress each country's count of PovcalNet surveys (1981–2014) on log mean survey consumption: slope 2.9 (SE 0.5). A 10% richer country has about 0.3 more surveys.
- They say this makes "missing at random" in global poverty counts untenable.
- No conflict variable, no time dimension.

**3. Masaki & Madson (2023), "Data Gaps in Microdata in the Context of Forced Displacement," WB PRWP 10631.** https://data.unhcr.org/fr/documents/download/106458 — **Reg, cross-section.**
- Outcome: count of microdata sets on forcibly displaced people (refugees and IDPs) per country, post-2010, N=221 datasets, estimated with a negative binomial.
- Covariates: ln GDP pc and ln battle deaths (both averaged over 2010–21), ln number of displaced people, region dummies.
- Finding: conflict intensity is negatively associated with how many datasets exist. Syria, Yemen and Türkiye each host more than 1m displaced people but have no dataset at all.
- Covers displaced-population surveys only.

**4. Burke, Driscoll, Lobell & Ermon (2021), "Using satellite imagery to understand and promote sustainable development," *Science* 371:eabe8628.** https://arxiv.org/abs/2010.06988 — **Desc.**
- Fig. 1 shows, for each country, the frequency of nationally representative livelihood surveys plotted against GDP and against democracy.
- Surveys are rarer in poorer and in less democratic countries ("autocrats ... limit awareness of poor economic progress").
- In half of African countries, 6.5 years or more pass between surveys. 8% of countries have gone more than 15 years without a population census.

## World Bank / institutional documentation (descriptive)

**5. Serajuddin, Uematsu, Wieser, Yoshida & Dabalen (2015), "Data Deprivation: Another Deprivation to End," WB PRWP 7252.** https://ideas.repec.org/p/wbk/wbrwps/7252.html — **Desc**, by region.
- Of 155 countries over 2002–11, 29 had no poverty estimate, 28 had one, and 20 had two widely spaced ones.
- Important confounder: most of the "extremely deprived" countries are **small island states**, where surveys cost more per head. Fragility gets only a passing mention. Any regression needs to control for population.

**6. Corral, Irwin, Krishnan, Mahler & Vishwanath (2020), *Fragility and Conflict: On the Front Lines of the Fight against Poverty*, World Bank.** https://openknowledge.worldbank.org/entities/publication/3c335532-5484-51a4-a16f-78399ab2f025 — **Desc.**
- 71% of people in fragile and conflict-affected states (FCS), more than 500m, have no or outdated poverty data: 74m in places with no estimate at all, and about 400m where the latest survey predates the conflict (Mali, Syria).
- Camps fall outside sampling frames.
- Data gaps on specific indicators, FCS vs. non-FCS developing countries: 89% vs. about 50% lack water data, 38% vs. 9% lack undernourishment data.
- Footnote: "poor economies are generally more data deprived."
- Adjusting for these gaps adds about 17m people to the poverty count in FCS.

**7. Hoogeveen & Pape, eds. (2020), *Data Collection in Fragile States: Innovations from Africa and Beyond*, Palgrave/WB (open access).** https://link.springer.com/book/10.1007/978-3-030-25120-8 — Qualitative.
- Frames a "triple data challenge": fragile states need data most, have the least of it, and are the hardest places to collect it.
- Argues collection is feasible and not necessarily more expensive.
- Documents within-survey gaps: phone surveys, nomads, and displaced people left out of sampling frames.

**8. Dang, Pullinger, Serajuddin & Stacy (2023), "Statistical performance indicators and index," *Scientific Data* 10:146.** https://www.nature.com/articles/s41597-023-01971-0 — A capacity index, not a survey-occurrence regression. It is useful as an outcome or control variable.

**9. Beegle, Christiaensen, Dabalen & Gaddis (2016), *Poverty in a Rising Africa*, ch. 1.** https://openknowledge.worldbank.org/handle/10986/22575 — **Desc.**
- Comparable consumption surveys rose from 13 (1990–99) to 25 (2003–12).
- In 2012 only 25 of 48 African countries had two or more surveys in the past decade.

**10. Alkire & Robson (2022), *Development Studies Research*** (https://doi.org/10.1080/21665095.2022.2141286) **and Kovesdi & Alkire (2026), *Social Indicators Research* 182** (https://doi.org/10.1007/s11205-025-03801-9) — Inventories of which surveys exist for multidimensional poverty measures. **Desc**, no regression on fragility.

**11. UN IGME child mortality reports (2022, 2024).** https://childmortality.org — **Desc.** Recent data are scarcest in FCS, and so uncertainty is widest there. In about 2 of 5 countries the latest mortality data are more than 5 years old.

## Within-survey exclusion and crisis timing (case evidence only)

- **Dianou et al. (2025/26), *Trop. Med. & Int. Health*** (https://doi.org/10.1111/tmi.70176). Burkina Faso DHS 2021 surveyed only 5 of 13 regions fully, and dropped 28 of 41 Sahel clusters for insecurity. The DHS misses the mortality reversal that phone surveys pick up.
- **Other insecurity exclusions:**
  - CAR MICS 2018–19: 18% of enumeration areas not visited.
  - Nigeria GHS-Panel 2018–19: rural Borno left out.
  - Iraq: 9 of 10 Nineveh districts left out of the frame.
  - Gaza SMART 2026: 17% of the population left out of the frame.
- **Maxwell & Hailey (2020/21), "Analysing Famine," *J. Humanitarian Affairs* 3(1)** (https://www.manchesteropenhive.com/view/journals/jha/3/1/article-p16.xml) and **Maxwell, Hailey & Naumova (2026), *J. Public Health Policy* 47(S1)** (https://doi.org/10.1057/s41271-026-00639-4). SMART mortality and nutrition data are the most often missing input to IPC analyses, especially where authorities block collection (Yemen, South Sudan, NE Nigeria). Fewer than half of Sudan's planned 2025 SMART surveys took place. Qualitative only.
- **Sandefur & Glassman (2015), *JDS* 51(2):116–132** (https://doi.org/10.1080/00220388.2014.968138). Admin data overstate progress compared with surveys, and survey production is donor-dependent. This is relevant motivation, not a test of selection.
- **Hollyer, Rosendorff & Vreeland, HRV transparency index** (https://hrvtransparency.org). An item-response model of missing WDI data, shown to vary with regime type in capable states. It measures data *reporting*, not survey fieldwork.
- I found no paper on DHS timing relative to elections, and no cross-country regression of census delay on conflict.

## Bottom line

- **Partly done.** Trommlerová et al. (2026) have run "survey exists ~ GDP + conflict + politics" with country FE, for DHS and MICS only, with 5-year periods, through 2016. They find conflict matters and GDP is weak once FE are in. Dang et al. (2019) and Burke et al. (2021) show the income gradient across countries, and Masaki & Madson (2023) show the conflict gradient for surveys of displaced people.
- **Not done, as far as I can find:**
  1. An **annual** country-year panel that pools DHS, MICS, LSMS/poverty surveys (PIP), SMART and censuses, with **survey type** compared side by side. For example, is the conflict penalty larger for consumption surveys than for DHS?
  2. **Shocks**: GDP downturns, disasters, food crises or famine (IPC/FEWS NET phase), and conflict *onset* versus ongoing conflict, using leads and lags to test whether surveys avoid crisis years or follow them.
  3. **Within-country timing** around elections, aid flows or the end of conflict.
  4. **Subnational selection**: matching DHS/LSMS cluster frames and dropped enumeration areas to ACLED events or IPC phases, systematically rather than one case at a time.
  5. Measuring how much this selection biases global poverty or mortality aggregates.
- Controls to include: population or small-island status (Serajuddin), and donor dependence (Trommlerová).
