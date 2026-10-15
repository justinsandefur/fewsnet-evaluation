# Does humanitarian funding follow early warnings, or crises and headlines? Literature on news, aid determinants, and instruments

Prepared 2026-09-30 for the FEWS NET famine early warning concept note.

**Verification key.** **[V]** means the citation and the key finding were checked against the paper's text or abstract (publisher page, RePEc, or author PDF). **[V-cit]** means the citation was checked but the quantitative detail comes from a secondary source or from memory. **[UNVERIFIED]** means the item could not be confirmed in this session; check it before citing. Note: the session's web-search budget ran out before the final checks, so a few Section 4 numbers are marked for follow-up.

---

## 1. News coverage of foreign disasters and government response

**Eisensee, T. & Strömberg, D. (2007). "News Droughts, News Floods, and U.S. Disaster Relief." *Quarterly Journal of Economics* 122(2): 693–728.** https://doi.org/10.1162/qjec.122.2.693 ; working-paper PDF: https://igier.unibocconi.eu/sites/default/files/media/attach/Stromberg_180407.pdf **[V]**
- *Design (verified from the text):* The sample is about 5,000 EM-DAT disasters from 1968 to 2002, combined with Vanderbilt TV News Archive coverage (ABC, CBS, NBC, CNN evening news) and USAID/OFDA relief declarations. About 10% of disasters get network coverage and about 20% get OFDA relief. Coverage is instrumented with two measures. The first is "news pressure": the median minutes the first three news segments spend on other top stories in the days after the disaster. The second is the Olympics: 18 Games in the sample period, weighted by Olympic days just after the disaster. They check robustness with the World Series and similar events. Controls include killed and affected, disaster type, and country, month and year fixed effects.
- *Findings:* Two standard deviations more news pressure (2.4 extra minutes) lowers the probability of coverage by 4 pp and the probability of relief by 3 pp. A disaster during the Olympics is about 5% less likely to be covered and 6% less likely to get relief. For equal odds of relief, a disaster at peak news pressure needs about 6 times as many casualties as one at the lowest pressure, and a disaster during the Olympics needs about 3 times as many. The IV effect of coverage on relief is about 68–70 pp for disasters that are marginal in the news decision, but the authors put the average effect at no more than about 16%.
- *The ratios the user asked about (verified wording):* "for every person killed in a volcano disaster, 40,000 people must die in a drought to reach the same probability of media coverage." It also takes about **40 times as many deaths** in an African disaster as in an Eastern European one of similar type and size to get the same expected coverage. (Our World in Data paraphrases this as "45×" relative to Europe; use the paper's 40× vs. Eastern Europe.)
- *Relevance:* This is the key paper for us. The authors quote Andrew Natsios and state directly that famines and droughts are among the *least* newsworthy disasters. They also say the news effect shifts relief *away* from slow-onset food crises. This is the opposite of what FEWS NET-driven early action would require. The design is also a template: "other news" is a plausibly exogenous shifter of attention, which could in principle be used as an instrument for coverage of food crises.

**Strömberg, D. (2007). "Natural Disasters, Economic Development, and Humanitarian Aid." *Journal of Economic Perspectives* 21(3): 199–222.** https://doi.org/10.1257/jep.21.3.199 **[V-cit]**
- A survey of about 7,000 disasters from 1980 to 2004 (2 million killed, 5 billion affected, about US$1 trillion in damage). Poorer countries suffer far more deaths for a given hazard. International relief rises with deaths and affected, but it is also shaped by donor ties such as former colonies, shared language, trade and distance, and by news coverage. *Relevance:* This is the standard framing that relief responds to need but is filtered through ties and media. The detailed coefficients were not re-verified.

**Durante, R. & Zhuravskaya, E. (2018). "Attack When the World Is Not Watching? US News and the Israeli-Palestinian Conflict." *Journal of Political Economy* 126(3): 1085–1133.** https://doi.org/10.1086/697202 **[V]** (volume and pages from memory)
- Israeli attacks are more likely when *predictable* major US news events (for example, scheduled sports or political events) are expected to dominate the next day's news. Palestinian attacks show no such timing. *Relevance:* Actors time unpopular actions around news cycles, which confirms that other news crowds out coverage. It also warns that governments facing famine may time obstruction strategically, as with blocking aid or hiding data.

**Jetter, M. (2017). "The effect of media attention on terrorism." *Journal of Public Economics* 153: 32–48.** https://doi.org/10.1016/j.jpubeco.2017.07.008 **[V-cit]**
- The paper covers 61,132 attack days in 201 countries. It instruments *New York Times* coverage of attacks with same-period **natural disasters in the United States**, which crowd attacks out of the news. One more NYT article is associated with about 1.4 more attacks the following week, or roughly 11–15% more attacks (magnitudes from secondary sources). *Relevance:* This is a second example of "disasters elsewhere crowd out coverage" used as an instrument for *media attention* rather than for aid.

**Besley, T. & Burgess, R. (2002). "The Political Economy of Government Responsiveness: Theory and Evidence from India." *QJE* 117(4): 1415–1451.** https://doi.org/10.1162/003355302320935061 **[V-cit]**
- In a panel of Indian states from 1958 to 1992, public food distribution and calamity relief respond more to falls in food production and to flood damage where newspaper circulation, especially in regional languages, is higher and electoral competition is greater. *Relevance:* A free, local-language press is the domestic accountability channel that makes relief follow need. The specific elasticities were not re-verified.

**Sen, A. (1981). *Poverty and Famines*. Oxford: Clarendon; Sen, A. (1999). *Development as Freedom*. New York: Knopf.** **[V-cit]**
- This is the canonical claim that no substantial famine has occurred in a functioning democracy with a relatively free press, because of the information and incentive roles of the press. Eisensee and Strömberg cite Sen (1984) for the related point that media push relief toward dramatic famines over endemic hunger. Their evidence suggests that internationally, famines are actually *less* newsworthy than rapid-onset disasters.

**Drury, A. C., Olson, R. S. & Van Belle, D. A. (2005). "The Politics of Humanitarian Aid: U.S. Foreign Disaster Assistance, 1964–1995." *Journal of Politics* 67(2): 454–473.** https://doi.org/10.1111/j.1468-2508.2005.00324.x **[V]**
- Using OFDA data, the paper models a two-stage process: whether to give aid, then how much. Both stages are strongly political, shaped by alliances, regime type and *NYT* coverage. They conclude that political factors, not need, are the overriding determinant. *Relevance:* This is the political science counterpart to Eisensee and Strömberg, but without a causal design for media.

**Van Belle, D. A. (2000). "New York Times and Network TV News Coverage of Foreign Disasters: The Significance of the Insignificant Variables." *Journalism & Mass Communication Quarterly* 77(1): 50–70.** **[V-cit]** (volume and pages unverified)
- The NYT's morning international agenda predicts the network evening news agenda (inter-media agenda setting). Many need-related disaster variables do not predict coverage. See also Van Belle, Rioux and Potter (2004), *Media, Bureaucracies, and Foreign Aid* (Palgrave) **[UNVERIFIED details]**. *Relevance:* The NYT can serve as a proxy for coverage.

**Olsen, G. R., Carstensen, N. & Høyen, K. (2003). "Humanitarian Crises: What Determines the Level of Emergency Assistance? Media Coverage, Donor Interests and the Aid Business." *Disasters* 27(2): 109–126.** https://doi.org/10.1111/1467-7717.00223 **[V]**
- These are qualitative case comparisons (for example, Mozambique floods, Kosovo and Angola). Aid levels depend on (i) the intensity of media coverage, (ii) donor security and political interest in the region, and (iii) how strong the NGOs and IOs on the ground are. Media matter most when donor security interests are weak. *Relevance:* This is the origin of the "CNN effect is conditional" view.

**Rost, N. & Clarke, J. N. (2025). "Why do governments fund some humanitarian appeals but not others?" *Development Policy Review* 43(1): e12819.** https://doi.org/10.1111/dpr.12819 **[V-cit]**
- This is a panel of funding to UN appeals. Need, strategic interest and agenda setting all matter, but **media coverage is the most consistent predictor**. Hosted refugees raise funding, while IDPs do not. *Relevance:* It is the closest recent analogue to our question, using appeal-level data (FTS). The effect sizes were not verified.

**Scott, M., Bunce, M. & Wright, K. (2022). "The Influence of News Coverage on Humanitarian Aid: The Bureaucrats' Perspective." *Journalism Studies* 23(2): 167–186.** https://doi.org/10.1080/1461670X.2021.2013129 **[V]**
- The authors interviewed 30 senior aid officials in 16 major donor countries. Most believe *sudden-onset national* coverage can increase emergency allocations, working indirectly through the public, parliaments and NGOs ("bureaucratic mediatisation"). *Relevance:* Slow-onset food crises rarely produce the sudden coverage spike that triggers this mechanism.

**Franks, S. (2006). "How Famine Captured the Headlines." *Media History* 12(3): 235–?** https://doi.org/10.1080/13688800601014025 **[V-cit]**; **Franks, S. (2013). *Reporting Disasters: Famine, Aid, Politics and the Media*. London: Hurst.** **[V]**
- Earlier reports on the 1984 Ethiopia famine, some broadcast a year before, had little effect. The October 1984 Buerk and Amin BBC report broke through because of **timing**: a quiet news moment, an ITV strike, and a newly revamped BBC Six O'Clock News. There was also a provocative angle in EU grain surpluses. It was eventually broadcast by about 425 channels. *Relevance:* This is a qualitative case of the Eisensee and Strömberg mechanism, and of warnings not turning into response until a media event.

**Benthall, J. (1993). *Disasters, Relief and the Media*. London: I.B. Tauris (2nd ed. 2010, Sean Kingston).** **[V]**
- The first book-length study of how the media and relief agencies co-produce disaster narratives and fundraising. It argues that the media select a few emergencies for attention, based on dramatic imagery and agency marketing. It is background and framing for the concept note.

**Forgotten crises indices**
- **CARE International, *Breaking the Silence: The 10 Most Under-Reported Humanitarian Crises* (annual, since 2016).** https://www.care.org/resources/the-10-most-under-reported-crises-of-2025/ **[V]** The method uses Meltwater, which tracks about 345,000 online outlets. CARE lists crises affecting at least 1 million people and ranks them by article counts. In 2025, nearly half of about 5 million crisis articles covered Gaza. The least-reported crises were mostly southern African drought and food crises (Zambia, Malawi, Namibia, Angola, Zimbabwe, Madagascar), plus CAR, Burundi, Honduras and North Korea.
- **European Commission DG ECHO, *Forgotten Crisis Assessment (FCA)* (annual, since about 2004).** https://civil-protection-humanitarian-aid.ec.europa.eu/what/humanitarian-aid/needs-assessment/forgotten-crises_en **[V]** The index combines INFORM risk and severity, media coverage (Europe Media Monitor), humanitarian aid per capita (OCHA FTS) and a qualitative expert assessment. ECHO sets aside at least about 15% of its planned budget for these crises (share from memory, **[UNVERIFIED]**). *Relevance:* This is a ready-made panel of "coverage vs. need vs. funding" we could merge with FEWS NET projections.

**Brown, P. H. & Minty, J. H. (2008). "Media Coverage and Charitable Giving after the 2004 Tsunami." *Southern Economic Journal* 75(1): 9–25.** **[V-cit]**
- Private donations to relief agencies respond strongly to news coverage, with evidence of donor fatigue. Related work: Brown, Harris and Taylor (2012), using PSID data, find that tsunami giving did **not** crowd out later giving to other causes **[V-cit]**. **Deryugina, T. & Marx, B. (2021). "Is the Supply of Charity Inelastic? Evidence from Deadly Tornadoes." *AER: Insights* 3(3): 383–398** finds disaster giving is largely additional, with no evidence it displaces other giving **[V-cit]**. *Relevance:* For private money, crowd-out across causes is weak. This matters for the first stage of any competing-crisis instrument.

---

## 2. Determinants of humanitarian and emergency aid

**Fink, G. & Redaelli, S. (2011). "Determinants of International Emergency Aid—Humanitarian Need Only?" *World Development* 39(5): 741–757.** https://doi.org/10.1016/j.worlddev.2010.09.004 ; WP: https://www.gfdrr.org/sites/default/files/publication/Determinants%20of%20International%20Emergency%20Aid%20-%20Humanitarian%20Need%20Only.pdf **[V]**
- The data cover 270 natural disasters (about 2000–2006) and emergency aid by donor from OCHA FTS. Need is a major determinant, but donors also favor smaller countries, nearby countries, oil exporters and former colonies, and, surprisingly, *less* politically aligned countries. They report bandwagon effects: other donors' aid is instrumented with bilateral distance, and donors follow each other. They also note the 2004 tsunami drew over US$12 bn, about 4 times the emergency aid for all other disasters in their sample. *Relevance:* This establishes herding, which makes a donor's aid endogenous to other donors' aid, and it gives a distance-based IV approach.

**Raschky, P. A. & Schwindt, M. (2012). "On the channel and type of aid: The case of international disaster assistance." *European Journal of Political Economy* 28(1): 119–131.** https://doi.org/10.1016/j.ejpoleco.2011.06.005 **[V-cit]**
- The choice between bilateral and multilateral channels, and between cash and in-kind aid, reflects humanitarian need, donor strategic interest and recipient institutional quality. Donors route more aid through NGOs and multilaterals when recipient governance is poor. See also **Raschky & Schwindt (2016), "Aid, Catastrophes and the Samaritan's Dilemma," *Economica* 83(332): 624–645** **[V-cit]**, which finds that expected disaster aid reduces recipients' prevention efforts.

**Kevlihan, R., DeRouen, K. & Biglaiser, G. (2014). "Is US Humanitarian Aid Based Primarily on Need or Self-Interest?" *International Studies Quarterly* 58(4): 839–854.** https://doi.org/10.1111/isqu.12121 **[V]**
- The study covers OFDA allocations to more than 100 countries from 1989 to 2009, with a selection stage and an amount stage. **Need matters more than self-interest** in the decision to give aid. After 9/11, foreign policy affinity and battle deaths matter more for amounts. *Relevance:* This is a partial counterweight to Drury et al.

**Becerra, O., Cavallo, E. & Noy, I. (2014). "Foreign Aid in the Aftermath of Large Natural Disasters." *Review of Development Economics* 18(3): 445–460.** https://doi.org/10.1111/rode.12095 **[V-cit]**
- For large disasters (1970–2008), ODA rises by a median of about 18% after the event, which is small relative to damages. The size of the surge does not appear to be driven by political or strategic factors.

**Becerra, O., Cavallo, E. & Noy, I. (2015). "Where is the money? Post-disaster foreign aid flows." *Environment and Development Economics* 20(5): 561–586.** https://doi.org/10.1017/S1355770X14000679 **[V]**
- Using DAC bilateral flows, the paper finds that humanitarian aid rises after large disasters, with some reallocation *across sectors within the recipient*. It finds **no evidence that donors reallocate aid between recipient countries** after large disasters. *Relevance:* **This is important for Section 3.** At the annual country level for ODA, the "disaster elsewhere crowds out aid to X" first stage may be weak.

**Bommer, C., Dreher, A. & Perez-Alvarez, M. (2022). "Home bias in humanitarian aid: The role of regional favoritism in the allocation of international disaster relief." *Journal of Public Economics* 208: 104604.** https://doi.org/10.1016/j.jpubeco.2022.104604 **[V-cit]**
- Disasters in the political leader's birth region get more international relief, so leaders capture aid within the country. *Relevance:* Within-country targeting of relief is itself political.

**Dreher, A., Fuchs, A., Parks, B., Strange, A. & Tierney, M. J. (2021). "Aid, China, and Growth: Evidence from a New Global Development Finance Dataset." *AEJ: Economic Policy* 13(2): 135–174.** **[V-cit]** The instrument is Chinese steel and input production interacted with a country's probability of receiving Chinese aid. **Kuziemko, I. & Werker, E. (2006). "How Much Is a Seat on the Security Council Worth?" *JPE* 114(5): 905–930** **[V-cit]**: US and UN aid rise when a country holds a UNSC seat. **Faye, M. & Niehaus, P. (2012). "Political Aid Cycles." *AER* 102(7): 3516–3530** https://doi.org/10.1257/aer.102.7.3516 **[V]**: donors give more aid in election years to aligned incumbents, but only in competitive elections. *Relevance:* This is the core of the political-allocation literature. UNSC membership and election timing are known exogenous-ish shifters of aid, though they are not specific to humanitarian aid.

**Other relevant items (not fully verified).** Findings in PNAS (2021) that "humanitarian need drives multilateral disaster aid" (https://www.pnas.org/doi/10.1073/pnas.2018293118) show UN/CERF allocations track hazard severity and partly *mimic* bilateral aid, meaning bandwagoning rather than crowd-out **[V-cit, authors unverified]**. IMF WP/25/006, "Foreign Aid and (Big) Shocks: Evidence from Natural Disasters" (2025), finds aid rises after disasters, humanitarian aid comes before structural aid, and allocation is shaped by political alignment **[V-cit, authors unverified]**. A 2026 *ISA Global Studies Quarterly* article finds CERF "crowds in" bilateral humanitarian funding (https://academic.oup.com/isagsq/article/6/2/ksag082/8694748) **[UNVERIFIED details]**.

---

## 3. Instruments for aid and the "competing crises" idea

### 3a. Papers that use crises or disasters elsewhere as the instrument

**Mary, S. & Mishra, A. K. (2020). "Humanitarian food aid and civil conflict." *World Development* 126: 104713.** https://doi.org/10.1016/j.worlddev.2019.104713 **[V-cit]** — *This is most likely the paper the user remembers.*
- The sample covers 79 recipient countries from 2002 to 2017, using OECD-reported humanitarian (emergency) food aid. The instrument exploits "between-country humanitarian food aid displacements": the emergence of a **"loud" food crisis elsewhere in the world**, meaning one that attracts media and donor attention, is used to instrument a country's food aid per capita. The logic is that donors shift food aid toward the loud crisis. They find that a 10% increase in humanitarian food aid per capita *reduces* civil-conflict incidence by about 0.2 pp, about 0.9% of the mean. This is the opposite sign to Nunn and Qian. **I could not see the exact construction** of "loudness" (for example, whether it is people affected by disasters elsewhere or media counts) or the first-stage F, so read the paper before relying on it.
- Critique: Koppenberg, Mishra and Hirsch (2023) argue that none of the food aid–conflict studies, including this one, has a compelling identification strategy. The exclusion restriction fails if loud crises elsewhere are regionally correlated with shocks at home (the same El Niño, locusts, or price spikes), or if they affect X through prices and trade.

**Ambaw, D. T. (2018). "Does non-US Emergency Food Aid Increase Civil Conflict in the Recipient Countries?" PhD thesis chapter, University of Adelaide.** **[V-cit via Koppenberg et al. 2023; original not located]**
- The instrument is the occurrence of **natural disasters in other sub-Saharan African countries**. It finds no effect of non-US food aid on conflict. Koppenberg et al. note the exclusion problem: disasters in neighboring countries are spatially correlated with local disasters and affect conflict directly (through refugees, prices and cross-border armed groups).

**Eisensee & Strömberg (2007) and Jetter (2017)**, above, are the cleanest "competing events" designs, but they instrument **coverage**, not aid. Eisensee and Strömberg's Olympics and news-pressure instruments are valid because the competing events are *unrelated to need* and are *not humanitarian claims on the same budget*. That distinction is what matters for our purposes.

### 3b. Evidence on whether the first stage exists (does funding for one crisis crowd out another?)

- **Against strong crowd-out (annual ODA):** Becerra, Cavallo and Noy (2015) find no reallocation across recipients after large disasters. The PNAS 2021 paper finds UN aid bandwagons rather than crowds out. For private giving, Brown, Harris and Taylor (2012) and Deryugina and Marx (2021) find disaster giving is additional, with little diversion.
- **For crowd-out (appeal funding, especially 2022):** Lowcock, Mitchell, Hughes and Pleeck (CGD blog, 7 April 2022) report that Ukraine appeals were 53% funded versus about 4% for all other countries at the time of writing. They also report that the remaining US humanitarian budget faced about a US$1 bn cut relative to 2021. https://www.cgdev.org/blog/war-ukraine-adding-humanitarian-needs-elsewhere-diverting-aid-ukraine-will-make-worse **[V]**. Development Initiatives' "The Ukraine crisis and diverted aid: what we know so far" (2022) documents explicit announcements of diversion by several donors, including Denmark, Sweden, Norway and the UK (https://reliefweb.int/report/world/ukraine-crisis-and-diverted-aid-what-we-know-so-far) **[V-cit; figures not re-read]**. A widely cited comparison: average appeal coverage in early August from 2012 to 2021 was about 47%, versus about 30% for non-Ukraine appeals in 2022 **[V-cit, source attribution uncertain]**. In-donor refugee costs were US$31 bn (14.5% of ODA) in 2022 (OECD). Qualitative sources describe Darfur in 2004–05 as starved of attention while the tsunami was over-funded **[V-cit]**.
- **Reconciliation:** Crowd-out seems to show up (i) in *within-year appeal funding shares and timing*, not in annual ODA totals; (ii) when the competing crisis is very large and politically salient (tsunami, Ukraine); and (iii) for donors with fixed humanitarian budget lines and earmarked reserves, such as ECHO's Emergency Aid Reserve and the US IDA/Title II accounts. I found **no peer-reviewed paper that uses concurrent disasters as an instrument for OCHA FTS humanitarian funding to food crises**. This looks like an open niche, though it may exist in a working paper I could not find.

### 3c. Other instruments for aid (for comparison)

**Nunn, N. & Qian, N. (2014). "US Food Aid and Civil Conflict." *AER* 104(6): 1630–1666.** https://doi.org/10.1257/aer.104.6.1630 **[V]**
- The instrument is lagged US wheat production (a time series) interacted with a country's propensity to receive US food aid (the share of years with any aid, 1971–2006). A 1,000 MT increase in US wheat aid raises civil-conflict incidence by about 0.3 pp in the published version (0.47 pp in the WP). A 10% increase at the mean raises incidence by about 1.14 pp. There is no effect on conflict onset.

**Christian, P. & Barrett, C. B. (2024). "Spurious Regressions and Panel IV Estimation: Revisiting the Causes of Conflict." *Economic Journal* 134(659): 1069–1099.** https://doi.org/10.1093/ej/uead091 ; earlier WP "Revisiting the Effect of Food Aid on Conflict: A Methodological Caution" (2017): https://barrett.dyson.cornell.edu/files/papers/Revisiting%20Food%20Aid%20and%20Conflict%2028%20April%202017(b).pdf **[V]**
- An exogenous time series interacted with an endogenous exposure share is a continuous DiD. It is invalid when there are **heterogeneous nonlinear trends** across exposure groups, which is analogous to failing parallel trends. Placebo test: the wheat-to-food-aid mechanism should vanish after the 1985 and 1996 Farm Bills decoupled purchases from production, yet the first stage and the IV coefficient are equally positive after 1996 and negative in 1985–96. When wheat-driven variation is *randomly reassigned* across countries, 2SLS still almost always gives a positive effect. Monte Carlo simulations show upward bias even when aid truly *reduces* conflict. They recommend detrending by exposure group, randomization inference and period placebos. The EJ version generalizes this to other panel IV papers on conflict.
- Related: Chu, Henderson and Wang (2017), "The Robust Relationship Between US Food Aid and Civil Conflict," *Journal of Applied Econometrics* 32(5): 1027–1032, is a semiparametric replication that supports Nunn and Qian on heterogeneity **[V-cit]**. On shift-share and Bartik designs in general, see Goldsmith-Pinkham, Sorkin and Swift (2020, *AER*) and Borusyak, Hull and Jaravel (2022, *REStud*; practical guide NBER WP 33236, 2024/25) **[V-cit]**.

**Koppenberg, M., Mishra, A. K. & Hirsch, S. (2023). "Food aid and violent conflict: A review and Empiricist's companion." *Food Policy* 121: 102542.** https://doi.org/10.1016/j.foodpol.2023.102542 **[V-cit]** (article number from memory)
- The review concludes that no study in this literature has a compelling identification strategy. It covers Nunn and Qian, Mary and Mishra, Ambaw and others, and calls for subnational data and a focus on mechanisms.

**Werker, E., Ahmed, F. Z. & Cohen, C. (2009). "How Is Foreign Aid Spent? Evidence from a Natural Experiment." *AEJ: Macroeconomics* 1(2): 225–244.** https://doi.org/10.1257/mac.1.2.225 **[V]**
- Oil price shocks change aid from OPEC and Gulf donors to poorer Muslim countries, so the instrument is oil price × Muslim share or ties. Aid is mostly consumed, largely as imported non-capital goods, with no detectable effect on growth or prices. *Relevance:* A donor-budget shock is a cleaner "supply shifter" than recipient-side disasters. The analogue for us is shocks to *donor* humanitarian budgets.

**Ahmed, F. Z. (2016). "Does Foreign Aid Harm Political Rights? Evidence from U.S. Aid." *Quarterly Journal of Political Science* 11(2): 183–217.** https://doi.org/10.1561/100.00015110 **[V]**
- Covering 150 countries from 1972 to 2008, it instruments US aid with the **legislative fragmentation of the US House** interacted with recipient exposure. US aid is found to worsen political rights. (See also Ahmed 2012, *APSR*, "The Perils of Unearned Foreign Income" **[V-cit]**.)

**Dreher, A. & Langlotz, S. (2020). "Aid and growth: New evidence using an excludable instrument." *Canadian Journal of Economics* 53(3): 1162–1198.** https://doi.org/10.1111/caje.12455 **[V]**
- The instrument is donor-government fractionalization interacted with the recipient's probability of receiving aid, with country and year fixed effects. It finds no effect of aid on growth. The same instrument appears in Dreher, Fuchs and Langlotz (2019, *EER* 112: 127–147) on aid and refugee flows **[V-cit]**. This is the design Christian and Barrett's critique applies to.

### 3d. Assessment: "exogenous disasters or crises elsewhere in the same donor-budget year crowd out funding for crisis X"

1. **Relevance (first stage).** This is plausible only for (a) within-year funding to appeals or HRPs, for example FTS funding coverage by month, and (b) crises that compete for the same donor envelope, such as the same donor, the same budget line, or the same region desk. Becerra et al. (2015) find no cross-recipient reallocation in annual ODA, so the instrument is likely to be weak in country-year ODA panels. Use exposure-weighted versions: competing-crisis severity weighted by each donor's pre-period share of crisis X's funding. That is a shift-share with donor shares.
2. **Exclusion.** The instrument violates exclusion when competing crises are (i) spatially correlated with X, through the same climate driver (El Niño or IOD), locusts, regional conflict or cross-border refugees; (ii) operating through global prices, since big crises raise food and fuel prices and freight costs (2022 is the prime example); or (iii) affecting X through agency operational capacity, such as surge staff, pipeline stocks or WFP procurement, rather than through money. Point (iii) arguably changes the estimand but does not strictly violate exclusion if the treatment is "delivered response." Mitigations: use only *geographically distant, rapid-onset* competing shocks (earthquakes and tropical cyclones outside the region), and control for global food prices and region-by-year fixed effects.
3. **Shift-share and Christian–Barrett issues.** If the instrument is a global shock series times a fixed exposure share, it inherits heterogeneous-trend bias. The needed checks are exposure-group-specific trends, randomization inference (permute shock timing), pre-trend and placebo periods, and Borusyak–Hull–Jaravel shock-level inference. With few large shocks (tsunami, Haiti 2010, Pakistan 2010, Ukraine 2022, Türkiye–Syria 2023), effective identification may rest on a handful of events. In that case, event studies are more honest than 2SLS.
4. **Best version.** An Eisensee–Strömberg-style *attention* instrument, such as Olympics, World Cups, or US and EU election or news pressure in the weeks after an IPC or FEWS NET alert. It is exogenous to need and not a claim on the humanitarian budget, so exclusion is more credible than for "disasters elsewhere." The cost is a weaker first stage for slow-onset crises, whose coverage is low in any case.

---

## 4. Early warning to early action: costs of late response and anticipatory action evidence

**Checchi, F. & Robinson, W. C. (2013). *Mortality among populations of southern and central Somalia affected by severe food insecurity and famine during 2010–2012*. FAO/FSNAU and FEWS NET.** https://fews.net/sites/default/files/documents/reports/FSNAU_FEWSNET_PR_050113_FINAL.pdf **[V]**
- An estimated **258,000 excess deaths** between October 2010 and April 2012, including 133,000 children under 5. Excess mortality peaked at about 30,000 per month from May to August 2011, *before and around* the July 2011 famine declaration, even though FEWS NET had issued warnings from mid-2010. This is the canonical case of warning without action. See also Maxwell and Fitzpatrick (2012, *Global Food Security*) and Hillbruner and Moloney (2012, *Global Food Security*) **[V-cit]**.

**2017 Somalia (averted famine)**
- Humanitarian Outcomes (2018), *Rapid Real-Time Review: DFID Somalia Drought Response*. https://humanitarianoutcomes.org/sites/default/files/publications/dfid_somalia_2017_irf_real_time_review_final.pdf **[V-cit]**. Donors scaled up with a "no regrets" posture before any famine declaration, and DFID funding was early and catalytic. The review notes you cannot prove the counterfactual. See also the World Bank/UN *Somalia Drought Impact and Needs Assessment* (2018) **[V-cit]**, and the IAHE Somalia evaluation (2024, GPPi), which covers 2022–23 **[V-cit]**. *Relevance:* The best "early action worked" case, but it is not causally identified.

**Cabot Venton, C., Fitzgibbon, C., Shitarek, T., Coulter, L. & Dooley, O. (2012). *The Economics of Early Response and Disaster Resilience: Lessons from Kenya and Ethiopia*. DFID.** https://assets.publishing.service.gov.uk/media/5a7c12e640f0b645ba3c6878/TEERR_Ethiopia_Report.pdf **[V-cit]** (author list partly from memory)
- Modeled over 20 years. In Ethiopia, early response with commercial destocking cuts total costs and losses by about 41% (US$1,614m to US$950m) in a high-magnitude drought, and saves about US$1.6 bn over 20 years in southern Ethiopia. Resilience investments return about US$2.3–13.2 per US$1 spent. The Kenya figures were not re-verified. The later USAID study (Cabot Venton 2018, *Economics of Resilience to Drought: Ethiopia, Kenya, Somalia*) reportedly finds early response could have saved about 30% of US humanitarian costs over 15 years **[UNVERIFIED numbers]**. *Caveat:* These are simulation models with strong assumptions, not causal estimates.

**Pople, A., Hill, R. V., Dercon, S. & Brunckhorst, B. (2026). "The Importance of Being Early? Anticipatory Cash Transfers for Flood-Affected Households." *World Bank Economic Review* (advance article).** https://doi.org/10.1093/wber/lhag016 ; WP: CSAE WPS/2021-07 **[V]**
- In the 2020 Jamuna floods, WFP sent BDT 4,500 (about US$53) by mobile money to about 23,000 households, 5 days before the flood peak and about 100 days before the standard response. The study compares recipients with similar non-recipients (quasi-experimental; pre-registered AEARCTR-0006576). Recipients were about 36% less likely to go a day without eating, more likely to evacuate people and livestock, borrowed less at high cost, and had better food consumption 3 months later (magnitudes from the WP summary). Even one day of earlier receipt near the peak mattered. A companion study: Gros et al. (2023), *Hydrology Research* 54(11): 1315, on the IFRC/BDRCS program in the same flood **[V-cit]**.

**UN OCHA / CERF anticipatory action pilots (2020–).** https://reliefweb.int/report/somalia/un-ocha-anticipatory-action-lessons-2020-somalia-pilot ; Centre for Disaster Protection learning series **[V-cit]**
- CERF committed up to US$140m for about 12 frameworks. The Somalia framework, with its trigger based on projected food insecurity, activated in June 2020. It spent about US$60m and reached about 2.2 million people in Somalia, Ethiopia and Bangladesh between July 2020 and June 2022, under 6% of CERF spending. Lessons: triggers must be tied to the specific hazard (the Somalia trigger fired on COVID, locust and flood projections), operational readiness is needed, and the learning is mostly process rather than impact evaluation.

**Start Network — Start Fund Anticipation and Start Ready risk pools.** https://startnetwork.org/funds/global-start-fund/start-fund-anticipation **[V-cit]**
- These are pre-arranged NGO financing tools triggered by forecasts. The ARC Replica drought cover in Senegal paid out in late 2019: about US$12.5m to the government and US$10.6m to Start Network (as reported). Risk Pool 4 (2025–26) covers about 812,000 people in 9 countries. Evidence consists mostly of learning reviews, not rigorous impact studies.

**World Bank Famine Action Mechanism (FAM), launched 23 September 2018 with the UN, ICRC, Microsoft, Google and AWS.** https://www.worldbank.org/en/programs/famine-early-action-mechanism **[V]**
- The aim was to link predictive analytics (the "Artemis" models) to pre-arranged financing, because "food security crisis warnings often do not translate into consistent and early responses." The evidence base on its impact is thin, and I found no impact evaluation.

**Lentz, E. C., Michelson, H., Baylis, K. & Zhou, Y. (2019). "A data-driven approach improves food insecurity crisis prediction." *World Development* 122: 399–409.** https://doi.org/10.1016/j.worlddev.2019.06.008 **[V]**
- Statistical models using prices, remotely sensed rainfall, geography and demographics (Malawi) correctly classify 83–99% of the most food-insecure village clusters, and compare well with IPC/FEWS NET projections. Code: https://github.com/zhou100/WD-Early-Warning-Food-Insecurity. *Relevance:* This is the forecast-quality side. If warnings improve but funding does not follow, the bottleneck is the response. (Related: Backer and Billing 2021 on FEWS NET accuracy, and Choularton and Krishnamurthy 2019 on FEWS NET accuracy in Ethiopia, *Food Security* **[UNVERIFIED details]**. Balashankar et al. 2023 *Science Advances*, "Predicting food crises using news streams" **[V-cit]**, shows that news text *leads* IPC changes, which is a useful link to Section 1.)

---

## 5. Synthesis (about 560 words)

**What the news literature implies.** The strongest causal evidence (Eisensee and Strömberg 2007) shows that government disaster relief responds to *coverage*, and that coverage is crowded out by unrelated news. Among the disasters they study, famines and droughts are the *least* newsworthy: it takes 40,000 drought deaths to match the coverage odds of one volcano death, and 40 times the deaths in Africa versus Eastern Europe. The IV effect is concentrated among "marginal" disasters, about 70 pp. Many food crises sit exactly at that margin: severe enough to warrant aid, too slow and too African to make the evening news. Qualitative work (Franks on Ethiopia 1984; Olsen et al. 2003; Scott, Bunce and Wright 2022) and Somalia 2011, where most of the 258,000 deaths came around the time of the declaration, fit this picture. For our analysis, the natural null is that **FTS funding for a FEWS NET-flagged crisis rises only after an IPC 4/5 declaration or a media spike, not at the projection date**. We should measure lags from (i) the first FEWS NET projection of IPC 3+/4+, (ii) the IPC famine or risk-of-famine statement, and (iii) the first surge in news volume (GDELT, Meltwater, or Europe Media Monitor via the ECHO FCA), to funding commitments and disbursements.

**Endogeneity.** Warnings, declarations, coverage and funding all respond to unobserved severity. Donors also herd (Fink and Redaelli 2011; the PNAS 2021 paper), and allocation carries political weight (Drury et al. 2005; Faye and Niehaus 2012; Bommer et al. 2022). A simple regression of funding on warnings mixes these effects together.

**Candidate instruments, ranked.**
1. **Attention shifters à la Eisensee and Strömberg (best exclusion).** Use news pressure, the Olympics, the FIFA World Cup, or major US and European elections in the weeks after a FEWS NET or IPC alert as instruments for coverage, then estimate the reduced form on funding speed. These events have no effect on local need and make no claim on humanitarian budgets. The weakness is the first stage: food-crisis coverage is low at baseline, so we need high-frequency (weekly) data and many alert events across FEWS NET's roughly 30 countries since the 2000s.
2. **Donor-budget supply shocks (Werker et al. 2009; Ahmed 2016; Dreher and Langlotz 2020).** Examples are US appropriations such as the Title II and IDA supplementals, donor-government fractionalization, and fiscal-year timing, interacted with pre-period donor shares for crisis X. These are plausible but subject to Christian and Barrett's heterogeneous-trends critique. They need exposure-specific trends, randomization inference and placebo periods.
3. **Competing crises elsewhere (Mary and Mishra 2020; Ambaw 2018).** This is the user's recalled idea. The first stage is credible only for within-year appeal funding for large, salient shocks (Ukraine 2022 appeals: 53% vs. about 4% funded for everyone else in April 2022), and weak in annual ODA (Becerra et al. 2015). Exclusion is threatened by spatially correlated climate shocks, global price channels (2022), and shared operational capacity. If used, restrict to *distant, rapid-onset* shocks (earthquakes and cyclones outside the region), weight by donor overlap, include region-year fixed effects and global food prices, and report shock-level (Borusyak–Hull–Jaravel) inference. Given how few mega-shocks there are, an **event study around 2004, 2010, 2022 and 2023 is more transparent than 2SLS**.

**Bottom line.** The most defensible design combines (1) and (3) as a descriptive event study. Its message would be: "Holding a FEWS NET warning fixed, crises that coincided with competing news or mega-emergencies got X% less and Y weeks later funding." That can be paired with the cost-of-delay evidence (Pople et al. 2026; Cabot Venton 2012) to turn the delay into lives and dollars.

---

## BibTeX

```bibtex
@article{eisensee2007news,
  author  = {Eisensee, Thomas and Str{\"o}mberg, David},
  title   = {News Droughts, News Floods, and {U.S.} Disaster Relief},
  journal = {Quarterly Journal of Economics},
  year    = {2007},
  volume  = {122},
  number  = {2},
  pages   = {693--728},
  doi     = {10.1162/qjec.122.2.693}
}
@article{stromberg2007natural,
  author  = {Str{\"o}mberg, David},
  title   = {Natural Disasters, Economic Development, and Humanitarian Aid},
  journal = {Journal of Economic Perspectives},
  year    = {2007},
  volume  = {21},
  number  = {3},
  pages   = {199--222},
  doi     = {10.1257/jep.21.3.199}
}
@article{durante2018attack,
  author  = {Durante, Ruben and Zhuravskaya, Ekaterina},
  title   = {Attack When the World Is Not Watching? {US} News and the {I}sraeli-{P}alestinian Conflict},
  journal = {Journal of Political Economy},
  year    = {2018},
  volume  = {126},
  number  = {3},
  pages   = {1085--1133},
  doi     = {10.1086/697202}
}
@article{jetter2017effect,
  author  = {Jetter, Michael},
  title   = {The Effect of Media Attention on Terrorism},
  journal = {Journal of Public Economics},
  year    = {2017},
  volume  = {153},
  pages   = {32--48},
  doi     = {10.1016/j.jpubeco.2017.07.008}
}
@article{besley2002political,
  author  = {Besley, Timothy and Burgess, Robin},
  title   = {The Political Economy of Government Responsiveness: Theory and Evidence from {I}ndia},
  journal = {Quarterly Journal of Economics},
  year    = {2002},
  volume  = {117},
  number  = {4},
  pages   = {1415--1451},
  doi     = {10.1162/003355302320935061}
}
@book{sen1981poverty,
  author    = {Sen, Amartya},
  title     = {Poverty and Famines: An Essay on Entitlement and Deprivation},
  publisher = {Clarendon Press},
  address   = {Oxford},
  year      = {1981}
}
@book{sen1999development,
  author    = {Sen, Amartya},
  title     = {Development as Freedom},
  publisher = {Knopf},
  address   = {New York},
  year      = {1999}
}
@article{drury2005politics,
  author  = {Drury, A. Cooper and Olson, Richard Stuart and Van Belle, Douglas A.},
  title   = {The Politics of Humanitarian Aid: {U.S.} Foreign Disaster Assistance, 1964--1995},
  journal = {Journal of Politics},
  year    = {2005},
  volume  = {67},
  number  = {2},
  pages   = {454--473},
  doi     = {10.1111/j.1468-2508.2005.00324.x}
}
@article{vanbelle2000nyt,
  author  = {Van Belle, Douglas A.},
  title   = {New York Times and Network {TV} News Coverage of Foreign Disasters: The Significance of the Insignificant Variables},
  journal = {Journalism \& Mass Communication Quarterly},
  year    = {2000},
  volume  = {77},
  number  = {1},
  pages   = {50--70},
  note    = {Volume/pages unverified}
}
@article{olsen2003humanitarian,
  author  = {Olsen, Gorm Rye and Carstensen, Nils and H{\o}yen, Kristian},
  title   = {Humanitarian Crises: What Determines the Level of Emergency Assistance? Media Coverage, Donor Interests and the Aid Business},
  journal = {Disasters},
  year    = {2003},
  volume  = {27},
  number  = {2},
  pages   = {109--126},
  doi     = {10.1111/1467-7717.00223}
}
@article{rost2025why,
  author  = {Rost, Nicolas and Clarke, John N.},
  title   = {Why Do Governments Fund Some Humanitarian Appeals but Not Others?},
  journal = {Development Policy Review},
  year    = {2025},
  volume  = {43},
  number  = {1},
  pages   = {e12819},
  doi     = {10.1111/dpr.12819}
}
@article{scott2022influence,
  author  = {Scott, Martin and Bunce, Mel and Wright, Kate},
  title   = {The Influence of News Coverage on Humanitarian Aid: The Bureaucrats' Perspective},
  journal = {Journalism Studies},
  year    = {2022},
  volume  = {23},
  number  = {2},
  pages   = {167--186},
  doi     = {10.1080/1461670X.2021.2013129}
}
@article{franks2006famine,
  author  = {Franks, Suzanne},
  title   = {How Famine Captured the Headlines},
  journal = {Media History},
  year    = {2006},
  volume  = {12},
  number  = {3},
  doi     = {10.1080/13688800601014025}
}
@book{franks2013reporting,
  author    = {Franks, Suzanne},
  title     = {Reporting Disasters: Famine, Aid, Politics and the Media},
  publisher = {Hurst},
  address   = {London},
  year      = {2013}
}
@book{benthall1993disasters,
  author    = {Benthall, Jonathan},
  title     = {Disasters, Relief and the Media},
  publisher = {I.B. Tauris},
  address   = {London},
  year      = {1993}
}
@techreport{care2025silence,
  author      = {{CARE International}},
  title       = {Breaking the Silence: The 10 Most Under-Reported Humanitarian Crises of 2025},
  institution = {CARE International},
  year        = {2026},
  url         = {https://www.care.org/resources/the-10-most-under-reported-crises-of-2025/}
}
@misc{echo_fca,
  author = {{European Commission, DG ECHO}},
  title  = {Forgotten Crisis Assessment},
  year   = {annual},
  url    = {https://civil-protection-humanitarian-aid.ec.europa.eu/what/humanitarian-aid/needs-assessment/forgotten-crises_en}
}
@article{brown2008media,
  author  = {Brown, Philip H. and Minty, Jessica H.},
  title   = {Media Coverage and Charitable Giving after the 2004 Tsunami},
  journal = {Southern Economic Journal},
  year    = {2008},
  volume  = {75},
  number  = {1},
  pages   = {9--25}
}
@article{deryugina2021supply,
  author  = {Deryugina, Tatyana and Marx, Benjamin M.},
  title   = {Is the Supply of Charity Inelastic? {E}vidence from Deadly Tornadoes},
  journal = {American Economic Review: Insights},
  year    = {2021},
  volume  = {3},
  number  = {3},
  pages   = {383--398}
}
@article{fink2011determinants,
  author  = {Fink, G{\"u}nther and Redaelli, Silvia},
  title   = {Determinants of International Emergency Aid---Humanitarian Need Only?},
  journal = {World Development},
  year    = {2011},
  volume  = {39},
  number  = {5},
  pages   = {741--757},
  doi     = {10.1016/j.worlddev.2010.09.004}
}
@article{raschky2012channel,
  author  = {Raschky, Paul A. and Schwindt, Manijeh},
  title   = {On the Channel and Type of Aid: The Case of International Disaster Assistance},
  journal = {European Journal of Political Economy},
  year    = {2012},
  volume  = {28},
  number  = {1},
  pages   = {119--131},
  doi     = {10.1016/j.ejpoleco.2011.06.005}
}
@article{raschky2016samaritan,
  author  = {Raschky, Paul A. and Schwindt, Manijeh},
  title   = {Aid, Catastrophes and the {S}amaritan's Dilemma},
  journal = {Economica},
  year    = {2016},
  volume  = {83},
  number  = {332},
  pages   = {624--645},
  doi     = {10.1111/ecca.12194}
}
@article{kevlihan2014us,
  author  = {Kevlihan, Rob and DeRouen, Karl and Biglaiser, Glen},
  title   = {Is {US} Humanitarian Aid Based Primarily on Need or Self-Interest?},
  journal = {International Studies Quarterly},
  year    = {2014},
  volume  = {58},
  number  = {4},
  pages   = {839--854},
  doi     = {10.1111/isqu.12121}
}
@article{becerra2014foreign,
  author  = {Becerra, Oscar and Cavallo, Eduardo and Noy, Ilan},
  title   = {Foreign Aid in the Aftermath of Large Natural Disasters},
  journal = {Review of Development Economics},
  year    = {2014},
  volume  = {18},
  number  = {3},
  pages   = {445--460},
  doi     = {10.1111/rode.12095}
}
@article{becerra2015where,
  author  = {Becerra, Oscar and Cavallo, Eduardo and Noy, Ilan},
  title   = {Where Is the Money? Post-Disaster Foreign Aid Flows},
  journal = {Environment and Development Economics},
  year    = {2015},
  volume  = {20},
  number  = {5},
  pages   = {561--586},
  doi     = {10.1017/S1355770X14000679}
}
@article{bommer2022home,
  author  = {Bommer, Christian and Dreher, Axel and Perez-Alvarez, Marcello},
  title   = {Home Bias in Humanitarian Aid: The Role of Regional Favoritism in the Allocation of International Disaster Relief},
  journal = {Journal of Public Economics},
  year    = {2022},
  volume  = {208},
  pages   = {104604},
  doi     = {10.1016/j.jpubeco.2022.104604}
}
@article{dreher2021aid,
  author  = {Dreher, Axel and Fuchs, Andreas and Parks, Bradley and Strange, Austin and Tierney, Michael J.},
  title   = {Aid, {C}hina, and Growth: Evidence from a New Global Development Finance Dataset},
  journal = {American Economic Journal: Economic Policy},
  year    = {2021},
  volume  = {13},
  number  = {2},
  pages   = {135--174}
}
@article{kuziemko2006seat,
  author  = {Kuziemko, Ilyana and Werker, Eric},
  title   = {How Much Is a Seat on the Security Council Worth? {F}oreign Aid and Bribery at the {U}nited {N}ations},
  journal = {Journal of Political Economy},
  year    = {2006},
  volume  = {114},
  number  = {5},
  pages   = {905--930}
}
@article{faye2012political,
  author  = {Faye, Michael and Niehaus, Paul},
  title   = {Political Aid Cycles},
  journal = {American Economic Review},
  year    = {2012},
  volume  = {102},
  number  = {7},
  pages   = {3516--3530},
  doi     = {10.1257/aer.102.7.3516}
}
@article{mary2020humanitarian,
  author  = {Mary, S{\'e}bastien and Mishra, Ashok K.},
  title   = {Humanitarian Food Aid and Civil Conflict},
  journal = {World Development},
  year    = {2020},
  volume  = {126},
  pages   = {104713},
  doi     = {10.1016/j.worlddev.2019.104713}
}
@phdthesis{ambaw2018,
  author = {Ambaw, Dessie Tarko},
  title  = {Does Non-{US} Emergency Food Aid Increase Civil Conflict in the Recipient Countries? (thesis chapter)},
  school = {University of Adelaide},
  year   = {2018},
  note   = {Cited in Koppenberg et al. (2023); original not located}
}
@article{nunn2014us,
  author  = {Nunn, Nathan and Qian, Nancy},
  title   = {{US} Food Aid and Civil Conflict},
  journal = {American Economic Review},
  year    = {2014},
  volume  = {104},
  number  = {6},
  pages   = {1630--1666},
  doi     = {10.1257/aer.104.6.1630}
}
@article{christian2024spurious,
  author  = {Christian, Paul and Barrett, Christopher B.},
  title   = {Spurious Regressions and Panel {IV} Estimation: Revisiting the Causes of Conflict},
  journal = {Economic Journal},
  year    = {2024},
  volume  = {134},
  number  = {659},
  pages   = {1069--1099},
  doi     = {10.1093/ej/uead091}
}
@article{chu2017robust,
  author  = {Chu, Chi-Yang and Henderson, Daniel J. and Wang, Le},
  title   = {The Robust Relationship Between {US} Food Aid and Civil Conflict},
  journal = {Journal of Applied Econometrics},
  year    = {2017},
  volume  = {32},
  number  = {5},
  pages   = {1027--1032},
  doi     = {10.1002/jae.2558}
}
@article{koppenberg2023food,
  author  = {Koppenberg, Maximilian and Mishra, Ashok K. and Hirsch, Stefan},
  title   = {Food Aid and Violent Conflict: A Review and Empiricist's Companion},
  journal = {Food Policy},
  year    = {2023},
  volume  = {121},
  pages   = {102542},
  doi     = {10.1016/j.foodpol.2023.102542}
}
@article{werker2009how,
  author  = {Werker, Eric and Ahmed, Faisal Z. and Cohen, Charles},
  title   = {How Is Foreign Aid Spent? {E}vidence from a Natural Experiment},
  journal = {American Economic Journal: Macroeconomics},
  year    = {2009},
  volume  = {1},
  number  = {2},
  pages   = {225--244},
  doi     = {10.1257/mac.1.2.225}
}
@article{ahmed2016does,
  author  = {Ahmed, Faisal Z.},
  title   = {Does Foreign Aid Harm Political Rights? {E}vidence from {U.S.} Aid},
  journal = {Quarterly Journal of Political Science},
  year    = {2016},
  volume  = {11},
  number  = {2},
  pages   = {183--217},
  doi     = {10.1561/100.00015110}
}
@article{dreher2020aid,
  author  = {Dreher, Axel and Langlotz, Sarah},
  title   = {Aid and Growth: New Evidence Using an Excludable Instrument},
  journal = {Canadian Journal of Economics},
  year    = {2020},
  volume  = {53},
  number  = {3},
  pages   = {1162--1198},
  doi     = {10.1111/caje.12455}
}
@article{dreher2019refugee,
  author  = {Dreher, Axel and Fuchs, Andreas and Langlotz, Sarah},
  title   = {The Effects of Foreign Aid on Refugee Flows},
  journal = {European Economic Review},
  year    = {2019},
  volume  = {112},
  pages   = {127--147}
}
@article{goldsmithpinkham2020bartik,
  author  = {Goldsmith-Pinkham, Paul and Sorkin, Isaac and Swift, Henry},
  title   = {Bartik Instruments: What, When, Why, and How},
  journal = {American Economic Review},
  year    = {2020},
  volume  = {110},
  number  = {8},
  pages   = {2586--2624}
}
@article{borusyak2022quasi,
  author  = {Borusyak, Kirill and Hull, Peter and Jaravel, Xavier},
  title   = {Quasi-Experimental Shift-Share Research Designs},
  journal = {Review of Economic Studies},
  year    = {2022},
  volume  = {89},
  number  = {1},
  pages   = {181--213}
}
@misc{lowcock2022ukraine,
  author = {Lowcock, Mark and Mitchell, Ian and Hughes, Sam and Pleeck, Samuel},
  title  = {War in {U}kraine Is Adding to Humanitarian Needs Elsewhere. {D}iverting Aid to {U}kraine Will Make It Worse},
  howpublished = {Center for Global Development blog},
  year   = {2022},
  month  = {April},
  url    = {https://www.cgdev.org/blog/war-ukraine-adding-humanitarian-needs-elsewhere-diverting-aid-ukraine-will-make-worse}
}
@techreport{di2022ukraine,
  author      = {{Development Initiatives}},
  title       = {The {U}kraine Crisis and Diverted Aid: What We Know So Far},
  institution = {Development Initiatives},
  year        = {2022},
  url         = {https://reliefweb.int/report/world/ukraine-crisis-and-diverted-aid-what-we-know-so-far}
}
@techreport{checchi2013mortality,
  author      = {Checchi, Francesco and Robinson, W. Courtland},
  title       = {Mortality among Populations of Southern and Central {S}omalia Affected by Severe Food Insecurity and Famine during 2010--2012},
  institution = {FAO/FSNAU and FEWS NET},
  year        = {2013},
  url         = {https://fews.net/sites/default/files/documents/reports/FSNAU_FEWSNET_PR_050113_FINAL.pdf}
}
@techreport{humanitarianoutcomes2018somalia,
  author      = {{Humanitarian Outcomes}},
  title       = {Rapid Real-Time Review: {DFID} {S}omalia Drought Response},
  institution = {Humanitarian Outcomes for DFID},
  year        = {2018},
  url         = {https://humanitarianoutcomes.org/sites/default/files/publications/dfid_somalia_2017_irf_real_time_review_final.pdf}
}
@techreport{cabotventon2012economics,
  author      = {Cabot Venton, Courtenay and Fitzgibbon, Catherine and Shitarek, Tenna and Coulter, Lorraine and Dooley, Olivia},
  title       = {The Economics of Early Response and Disaster Resilience: Lessons from {K}enya and {E}thiopia},
  institution = {UK Department for International Development},
  year        = {2012},
  url         = {https://assets.publishing.service.gov.uk/media/5a7c12e640f0b645ba3c6878/TEERR_Ethiopia_Report.pdf}
}
@article{pople2026early,
  author  = {Pople, Ashley and Hill, Ruth and Dercon, Stefan and Brunckhorst, Ben},
  title   = {The Importance of Being Early? {A}nticipatory Cash Transfers for Flood-Affected Households},
  journal = {World Bank Economic Review},
  year    = {2026},
  doi     = {10.1093/wber/lhag016},
  note    = {Advance article; earlier CSAE WPS/2021-07}
}
@techreport{ocha2021somalia,
  author      = {{UN OCHA / Centre for Disaster Protection}},
  title       = {{UN OCHA} Anticipatory Action: Lessons from the 2020 {S}omalia Pilot},
  institution = {OCHA},
  year        = {2021},
  url         = {https://reliefweb.int/report/somalia/un-ocha-anticipatory-action-lessons-2020-somalia-pilot}
}
@misc{startnetwork_anticipation,
  author = {{Start Network}},
  title  = {Start Fund Anticipation and Start Ready},
  url    = {https://startnetwork.org/funds/global-start-fund/start-fund-anticipation}
}
@misc{worldbank2018fam,
  author = {{World Bank}},
  title  = {Famine Action Mechanism ({FAM})},
  year   = {2018},
  url    = {https://www.worldbank.org/en/programs/famine-early-action-mechanism}
}
@article{lentz2019data,
  author  = {Lentz, Erin C. and Michelson, Hope and Baylis, Kathy and Zhou, Yang},
  title   = {A Data-Driven Approach Improves Food Insecurity Crisis Prediction},
  journal = {World Development},
  year    = {2019},
  volume  = {122},
  pages   = {399--409},
  doi     = {10.1016/j.worlddev.2019.06.008}
}
```
