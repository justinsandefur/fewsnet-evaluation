# Handoff: IPC phases vs. surveys (companion piece)

*Written 14 October 2026, when this material was hived off the FEWS NET evaluation
("How Much Does Early Warning Improve Famine Response?"). That chat now focuses only on the FEWS NET
evaluation; use this file to start or continue the companion piece in another chat.*


## Status, 14 October 2026 (later)

- `output/cgd_paper/ipc_surveys_draft.tex` is now a standalone paper: "Counting Hunger, Missing Deaths: What Food Insecurity Phases Tell Us About Malnutrition and Mortality" (26 pp, compiles clean).
- New sections:
  - why the link is weak (health breakdown, what kills);
  - where surveys don't go (survey timing + exclusions, from `side_survey_selection/`);
  - old debates;
  - implications (IPC, not FEWS NET).
- New macro files:
  - `numbers_gaps.tex` (from `side_survey_selection/code/07_numbers_tex.py`);
  - `numbers_fts.tex` (from `code/71_fts_cluster_shares.py`, FTS funding by cluster 2015–24).
- New figure `fig12_survey_exclusions.pdf` (from `side_survey_selection/code/06_exclusions.py`).
- Literature on old debates: `references/lit_old_debates.md`. Its 48 new BibTeX entries were appended to `references.bib`. The bib has case-duplicate keys (e.g. `checchi2022sae`/`Checchi2022SAE`); cite the first-defined one.
- Still open:
  - items 1, 2 and 6 above;
  - Charles wants the "target downstream outcomes / deaths wherever they happen" proposal reviewed by practitioners before it is pushed hard.

## The question

What do IPC / FEWS NET acute food insecurity phases actually measure? We compare them with outcomes measured
independently in surveys: household food consumption and coping, child acute malnutrition and mortality.
A second part asks whether paying for more nutrition surveys would pay off.

The working title in the draft is "What Do Food Insecurity Phases Measure? IPC Classifications Against Household
and Nutrition Surveys". The draft hasn't been edited as a standalone paper yet.

**Headline:**
- Phases track household food insecurity, loosely.
- They are a weak guide to child malnutrition and a poor guide to mortality.
- The IPC's reference bands for malnutrition and death rates per phase are far steeper than the measured
  gradients.
- Scheduled surveys predict malnutrition far better than phases do.
- If treatment programmes followed surveys, Somalia's surveys would avert deaths at roughly $1,200–2,200 each.

## Where things are

| What | Path |
|---|---|
| Draft paper (compiles, 21 pp) | `output/cgd_paper/ipc_surveys_draft.tex` / `.pdf` |
| Pre-split full paper (has all the original text) | GitHub `justinsandefur/fewsnet-evaluation`, commit `fe81ed4`, `paper/fewsnet_evaluation.tex` |
| Numbers (LaTeX macros, shared with main paper) | `output/cgd_paper/numbers.tex` (written by `code/40_paper.py`) |
| Figures | `output/cgd_paper/figures/fig9a`–`fig9h`, `fig9_fsnau`, `fig8_information`, `fig10_voi` |
| Bibliography | `output/cgd_paper/references.bib` (shared) |

The draft `\input`s the shared `numbers.tex` and figures. Cross-references to the main paper show as `??`
(`sec:bcr`, `sec:money`).

### Code (all in `code/`, run with `.venv/bin/python`)

| Script | Does |
|---|---|
| `56_fsnau_surveys.py` (+ `56_transcription_instructions.md`) | Somalia FSNAU seasonal nutrition/mortality surveys 2009–2025, from the fsnau.org portal and PDF reports, to `input/fsnau/surveys.csv` |
| `57_fsnau_value.py` | FSNAU zones matched to FEWS NET units (`input/fsnau/crosswalk.csv`). Does FEWS NET's forecast or the previous survey predict GAM? Out-of-sample R², AUC for critical GAM, within-zone fixed effects. Outputs `output/tables/fsnau_value*` |
| `58_phase_outcomes.py` | Outside Somalia: SMART+ dashboard API, FEWS NET Data Warehouse nutrition values (Burkina Faso, Mauritania only), IPC acute malnutrition (AMN) files from HDX. Phase vs GAM/CDR; AMN vs acute food insecurity (AFI) agreement. Outputs `phase_outcomes*` |
| `59_survey_value.py` | Coarse targeting rule: choose half of the zones by survey vs forecast. Outputs `survey_value*` |
| `65_survey_voi.py` | Value of information: a planner allocates SAM/MAM treatment by zone; the survey vs forecast vs population vs oracle information sets; redeployment variants. Outputs `survey_voi*` |
| `66_foodsec_surveys.py` | Household FCS / rCSI / HHS from JRC HFID (WFP columns only), WFP mVAM on HDX, and CH direct-evidence indicators, matched to FEWS NET and IPC/CH phases. Outputs `foodsec_*` |
| `52_text_features.py`, `53_text_value.py` | Survey results quoted in FEWS NET reports (Somalia, Ethiopia, Sudan). Does a new survey move the next map? |
| `40_paper.py` functions | `phase_outcomes()`, `fig_phase_singles()` (fig9a–f), `_foodsec()` / `fig_foodsec()` (fig9g–h, with the IPC 20% rule shading), `fig_fsnau()`, `fig_voi()`, `fig_information()`, `pieces()` |

### Data (`input/`)

- `fsnau/`: surveys, crosswalk, coverage, transcribed PDFs.
- `foodsec_surveys/`: `hfid`, `mvam_hdx`, `ch_hdx`, `wfp_martini`, plus `matched.parquet` and `indicators.parquet`.
- `smartplus/`, `fdw_nutrition/`, `ipc_amn/`, `surveys/`.
- `panel/fnid_population.parquet` (WorldPop by FEWS NET unit).

### Literature notes (`references/`)

- `lit_phase_outcomes.md`: the IPC bands' origins and the literature on food insecurity vs wasting.
- `novelty_check.md`: no study we found systematically tests the bands against survey outcomes.
- `survey_repositories.md`: which survey data are public.
- `survey_costs.md`: SMART cost of about $15–21k per domain, up to $30k.
- `excess_deaths.csv`: crisis death tolls.
- `lit_shocks_nutrition.md`, `lit_humanitarian_data.md`.

## Key results (current values in `numbers.tex`)

### Household food insecurity (WFP surveys + mVAM, 478 areas, 29 countries, 2011–2024)

- **Food consumption by phase.** The share of households with poor or borderline food consumption is
  28 / 35 / 47 / 46% in areas FEWS NET maps as Phase 1 / 2 / 3 / 4+.
- **Severe coping by phase.** The share with rCSI ≥ 19 is 33 / 35 / 49 / 45%.
- **Correlation with phase:**

  | Indicator | All areas | Within country | Within area |
  |---|---|---|---|
  | Food consumption | 0.41 | 0.27 | 0.15 |
  | Coping | 0.35 | 0.25 | 0.25 |

- **IPC 20% household rule** (borderline food consumption = Crisis; rCSI ≥ 19 = Crisis):
  - 71% (food consumption) and 78% (coping) of areas mapped Phase 1–2 have too many households in
    Crisis-level conditions for their phase.
  - Only 5% and 4% of areas mapped Crisis+ have too few.
  - So the phases look too *mild* in Minimal/Stressed areas.
  - Possible link to Lentz et al. (2025), who find IPC undercounts acute hunger by about a fifth. Not yet
    written up.
- **CH analysts' own inputs, 2021–23** (2,805 area-analyses, 18 countries). Correlation with the phase the
  same analysts assigned:

  | Indicator | Correlation |
  |---|---|
  | Food consumption | 0.33 |
  | Household hunger | 0.34 |
  | Livelihood coping | 0.15 |
  | rCSI | 0.04 |

  A phase is a convergence-of-evidence judgment, not a formula.
- **Draft abstract sentence** dropped from the FEWS NET abstract; it belongs here: "47 percent of households
  in areas FEWS NET mapped in Crisis had poor or borderline food consumption…"

### Malnutrition and mortality

- **Somalia FSNAU scheduled surveys** (329 zone-seasons, 29 zones, 28 seasons). These are the cleanest test,
  because the timing is fixed, not alarm-driven.
  - Mean GAM is 13 / 13 / 15% in zones forecast Stressed / Crisis / Emergency+.
  - The forecast correlates 0.10 with measured GAM; the zone's own survey six months earlier correlates 0.66.
  - Out of sample, R² is 0.42 with the previous survey and about 0 with the forecast.
  - AUC for critical GAM is 0.75 with the previous survey and 0.47 with the forecast.
- **Within zones**, one phase worse than usual goes with:

  | Outcome | Without / with season effects | Bands imply |
  |---|---|---|
  | GAM | 0.8 / 0.5 points | 5–10 points |
  | CDR (per 10,000 per day) | 0.12 / 0.08 | 0.45–0.75 |
  | U5DR | 0.25 / 0.14 | — |

- **FEWS NET barely responds to surveys.** A zone whose last survey showed 10 more points of GAM is forecast
  0.09 of a phase worse.
- **SMART+** (2022–26, 246 surveys, 167 in FEWS NET maps):
  - GAM is 9 / 10 / 11 / 18% by phase; the Phase 4 jump comes from about a dozen ad hoc surveys in Ethiopia.
  - The slope is 1.8 points per phase (SE 0.5).
  - CDR is flat by FEWS NET phase (slope 0.00) and rises 0.17 per IPC/CH phase.
- **Other recurring rounds:** Nigeria's UNICEF rounds give 2.7 points per CH phase; the Burkina Faso and
  Mauritania national rounds give 3.3 per FEWS NET phase.
- **The IPC's two scales** (AMN vs AFI) put an area in the same phase only 35% of the time (1,427 areas).
- **Excess deaths per person in Phase 3+** (per 10,000 per day):
  - Somalia 2017–18 and 2022: about 0.15–0.2.
  - Northeast Nigeria 2016–19: 0.9.
  - Somalia 2010–12 famine: 1.1–1.9.

  IPC-band arithmetic would have predicted about 2–5× Somalia 2022's toll.
- **Calibration used in the FEWS NET paper's lives appendix**, per phase step below Famine:
  - CDR: 0.15 (range 0.07–0.25).
  - GAM: 1.5 points (range 0.6–2.5).
  - Emergency to Famine: 1.5 (range 0.9–1.9).

### Surveys in FEWS NET reports (Somalia, Ethiopia, Sudan, 2011–24; 263 survey results quoted)

- **Survey coverage** is uneven. Among areas FEWS NET mapped in Emergency, a survey from the previous 12
  months is quoted for 67% in Ethiopia, 54% in Somalia and 14% in Sudan.
- **A new survey moves the next map upward**, by 8.8 percentage points (SE 3.1), against a base of 10%. It
  never moves the map downward.
- **Reassuring surveys** (GAM < 15%) move the map up about as much as alarming ones: 14.8 vs 11.9 points.
- **Reading:** the *decision to survey* is the signal. Surveys aren't placed at random, so only scheduled
  surveys can score the value of survey content.

### Would paying for surveys pay off? (Somalia, `65_survey_voi.py`)

- **The causal chain:**
  1. Surveys give information (link holds: strong).
  2. The information improves warnings (weak; FEWS NET barely responds).
  3. Warnings move aid (mostly outside FEWS NET; nutrition programmes size their caseloads from survey
     prevalence).
  4. Aid saves lives (strong for SAM treatment, about $4–7k per death averted on GiveWell's inputs).
- **The coarse rule fails.** Choosing which half of the zones to serve gives almost no gain (73% vs 73% of
  cases), because caseload follows population.
- **Value of information:** 12 zones, 26 seasons, budget of 38% of caseload (typical coverage).
  - Survey-based planning averts 122–168 more deaths a season than forecast-based planning.
  - That is 13–27% of the oracle gain.
  - A survey round costs about $240k, so each extra death averted costs about $1,400–1,900 ($700–2,900
    across assumptions; $1,200–2,200 across budgets of 20–50%).
  - Most of the value comes from locating SAM cases.
- **Upper bound in one sense:** it assumes programmes act on surveys.
- **Lower bound in another:** it gives no credit for sizing the response, detecting famine, or evaluation.

## Guidance from Justin (carry over)

- **Charles Kenny's angle:** the "more humanitarian data" pitch is a nascent CGD ask, possibly a Coefficient
  Giving grant.
- **Figure style:** single-panel, high-granularity figures in the style of `fig9a_phase_gam`:
  - every survey as a jittered point;
  - IPC bands or 20%-rule ranges as grey boxes;
  - means with 95% CIs.
  - Justin found multi-panel tables and figures hard to parse.
  - Earlier feedback: fewer figures, more detail, a clearer message.
  - Fig 10 (VOI) x-axis was unclear; it's now labelled "treatment places as a share of all acutely
    malnourished children in the surveyed zones".
- **Be explicit** that malnutrition and mortality are *not* what the IPC/AFI scale is designed to classify.
  Food consumption and coping are the like-for-like test.
- **Numbers:** no hard-coded numbers in the paper; use LaTeX macros generated by code.
- **Writing:** few acronyms, plain language, define technical terms (e.g. ROC/AUC) or replace them with
  plain statements.
- **Byline and footnote:**
  - The byline follows the FEWS NET paper: Claude Opus 5.5 first, then Charles Kenny (CGD), then Justin
    Sandefur (Coefficient Giving).
  - The footnote counts the human prompts and words that directed the work.
  - Never count the "U.S. aid withdrawal impact analysis" session (4207d5f7).
- **No email data requests** ("will take weeks"). No account creation or API keys.
- **GitHub:** standing permission to push to `justinsandefur/fewsnet-evaluation`.
  - The repo isn't a local git dir: clone to scratchpad, copy files in, commit with a co-author line, push.
  - Don't push `paper/fewsnetsaveslives.docx`, `*.fls`, `*.fdb_latexmk` or figure PNGs (except
    `fig_case_*.png`).

## Open items / next steps

1. **Decide whether to decouple the code.** `40_paper.py` still writes both papers' numbers and figures (a
   full run takes about 4 minutes). A standalone `code/70_ipc_surveys_paper.py` writing its own `numbers`
   file would decouple them.
2. **Verify the IPC household-indicator thresholds** against the IPC manual 3.1 reference table: borderline
   FCS → Phase 3, poor → 4+, rCSI ≥ 19 → Phase 3.
3. **Frame the 71–78% "too mild" finding** against Lentz et al. (2019, 2025).
4. **Rewrite as a standalone paper.** It needs an introduction, a data section, the IPC/FEWS NET background
   imported from the main paper, and a conclusion. Figures 9c, 9d and 9e could become appendix figures.
5. **Sudan:** almost no surveys were quoted for its Emergency areas, which is the clearest case for
   independent repeated surveys (Kenny 2026 humanitarian-data piece).
6. **Cross-check nutrition surveys against DHS** (in `input/dhs`) where timing allows.
