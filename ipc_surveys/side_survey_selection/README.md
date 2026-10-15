# Do household surveys avoid hard places?

Side project. Unit: country x year, 1990-2023, 143 countries (all current low/middle income plus anything that ever hosted a survey). Outcome: did fieldwork for a DHS (incl. malaria/AIDS surveys), MICS or LSMS start that year. Linear probability models, SEs clustered by country.

## Run

```bash
../.venv/bin/python code/01_fetch.py        # metadata + covariates, ~5 min
../.venv/bin/python code/02_build_panel.py
../.venv/bin/python code/03_analysis.py     # tables -> output/tables, figures -> output/figures
```

## Sources
- DHS Program API (403 household surveys), IHSN + World Bank microdata catalogs for MICS (319 country-years) and LSMS (143)
- WDI: GDP per capita PPP, growth, population, battle deaths (UCDP), under-5 mortality; WGI political stability
- Maddison Project 2023 fills GDP gaps (6% of country-years: Somalia, Syria, Yemen...)
- FEWS NET current-situation maps from the parent project (`../input/fewsnet/cs_monthly.parquet`), 2011+

## Findings (survey starts in 15.8% of country-years; DHS 7.4%, MICS 6.6%, LSMS 2.7%)
1. **Across countries, poverty is targeted.** Survey rate falls steadily with GDP per capita (fig 1). Need wins at the extensive margin: conflict-affected poor countries are *not* more likely to go 5+ years without any survey (fig 4). The long-gap cases are a short list of failed states: Syria, Lebanon, South Sudan, Somalia, Sudan, Afghanistan, Yemen, Myanmar.
2. **Within a country, surveys dodge bad years.** With country and year fixed effects, a minor-conflict year cuts the chance of a survey starting by 5.5 pp and a war year by 6.8 pp (against a 15.8% base, roughly a third to 40% fewer). A GDP-per-capita drop of 2% or more cuts it by about 2 pp. A one-log-point rise in battle deaths per 100k: -2.7 pp (p=0.002).
3. **The timing effect is a postponement, not an exit.** Event study around 54 conflict onsets: -12 pp in the onset year, -10 pp the year after, back to baseline by year 2 (fig 3).
4. **It is mostly DHS.** DHS reacts to conflict and downturns. MICS shows no significant response to either. LSMS reacts to downturns only (-1 to -2 pp, significant), not conflict.
5. **FEWS NET food crisis severity: no detectable effect** (43 countries, 2011-23; fig 5 is suggestive at the top bin, 15% vs 23%, but regressions are flat and noisy).

## Caveats
- Survey catalogs lag 1-3 years and miss some MICS round 1 surveys and sub-national MICS; recent years are under-counted.
- National battle-death thresholds tag large countries (India, Pakistan, Nigeria) as "in conflict" most years. The intensity measure (deaths per 100k) gives the same answer.
- This measures *whether* a survey happens, not *where in the country*. Surveys run in conflict countries often drop insecure clusters (e.g., Burkina Faso DHS 2021). That within-survey exclusion is probably the bigger selection channel and is not captured here.
- Prior work: see `references/lit_survey_selection.md`. The closest is Trommlerová et al. (2026, J. Development Studies): five-year periods, DHS and MICS only, through 2016. It finds conflict the strongest negative predictor.

## Part 2: who is left out *within* surveys (report appendices)

`code/04_fetch_reports.py`, `04b_fetch_mics_ipums.py` download DHS and MICS final reports (PDFs cached outside Dropbox in `~/Library/Caches/survey_reports`). `05_extract_text.py` pulls sampling-design passages into `data/report_text/`. These were coded by LLM coders against `references/exclusion_codebook.md` (`data/exclusion_coding/coded_*.csv`), spot-checked against the text, with fixes in `corrections.csv`. `06_exclusions.py` makes the tables and figs 6-7.

Sample: 190 reports (115 DHS, 75 MICS) from 2000 on: every survey in a country with 25+ battle deaths in the fieldwork year or the two before, plus a random 30+30 from calm low/lower-middle income countries. 170 have usable text. Missing: most MICS round 2 (2000) reports, 2 DHS.

Findings:
1. **Documented exclusions rise with conflict.** Some area or cluster is dropped for insecurity or access in 23% of reports from calm countries, 47% under minor conflict, 65% in war (fig 6). Design-stage exclusion of whole areas: 6% / 19% / 19%.
2. **The biggest holes:**
   - Mali 2012 DHS: the whole north plus 3 cercles of Mopti, 13% of households, and 170 of 585 clusters.
   - Niger 2021 MIS: 10% of the population, in Diffa and Tillabéri.
   - Mali 2015 MIS: 9%.
   - Nigeria 2021 MICS: 20 of 27 Borno LGAs, 71% of Borno's population.
   - Nigeria 2018 DHS: 11 Borno LGAs.
   - Central African Republic 2018 MICS: 99 of 550 enumeration areas.
   - Mali 2023 DHS: about 93 of 500 clusters.
   - Burkina Faso 2021 DHS: 86 of 600.
   - Afghanistan 2010 MICS: 67 of 516.
   - Iraq 2018 MICS: 5 Nainawa districts and Hawija, plus IDPs in camps.
   - Mozambique 2022 DHS: 8 Cabo Delgado districts.
   - Pakistan DHS 2006 and 2012: Federally Administered Tribal Areas (FATA).
   - Indonesia 2003 DHS: Aceh, Maluku, North Maluku and Papua.
   - Uganda 2000 DHS: 4 northern and western districts.
3. **Design-stage exclusion hides the loss.** Iraq 2018 says teams "visited ... all the selected enumeration areas" because the insecure districts were never in the frame (fig 7: high-intensity surveys with zero field losses).
4. **Camps are almost never discussed.** 92% of reports never mention camps. 4 explicitly exclude them (Burkina Faso 2021, Iraq 2018, Guinea 2005, Malawi 2019). 10 include them, mostly special designs: Jordan 2017 Syrian camps, Uganda 2006 IDP stratum, Turkey 2018 Syrian sample, Myanmar 2016, Sierra Leone 2000, and the Palestinian-camp MICS in Lebanon and Syria. Only 6 questionnaires are noted as identifying displacement status.
5. Exclusions are more often documented after 2015 (49% vs 36% of reports), likely both more conflict in survey countries (Sahel) and better reporting.

Caveats: "not mentioned" ≠ "not excluded". Silence on camps usually means camps were outside the census frame without comment. LLM coding was spot-checked on about 10 reports with 1 correction; treat individual cluster counts as approximate.
