# The 2025 US aid cuts: effects on malnutrition and death (memo)

Asks whether the 2025 withdrawal of US humanitarian aid raised malnutrition and death, in Somalia, Nigeria and Ethiopia.

Paper source: `output/us_cut_memo/us_cut_memo.tex` (`us_cut_memo_v1.tex` is the earlier draft).

## Layout

```
code/      Python: fetching, panel building, analysis, numbers and figures (run from this folder)
stata/     Stata replication of the core estimates
input/     raw and intermediate data (links to the shared store ../_data/input/; not in git)
output/    tables/, figures/ and the paper folder
references/  source notes and literature reviews used in the paper
```

Every path in the code is relative to this folder, so the paper replicates on its own.

## Requirements

- Python 3.9 with the packages in `requirements.txt` (the project's virtual environment is `../.venv`). Run scripts from this folder, e.g. `../.venv/bin/python code/40_paper.py`.
- Stata 19 (StataNow MP), with `reghdfe` and `boottest` from SSC.
- LaTeX (pdflatex, bibtex).

## Data

All sources are public, but several (EM-DAT, ACLED, DHS) do not allow redistribution, and the raw data total several GB, so `input/` is not in git. The fetch scripts below download each source into `input/`. Where a source needs registration (EM-DAT, DHS), the script's docstring says so.

## Hand-built data

These inputs cannot be downloaded again, so they are kept with the code (in the repository under `data/`):

- `code/56_transcription_instructions.md`: how the FSNAU survey table in `input/fsnau/` was transcribed.

## Replication

1. Fetch data, then build panels (the scripts in the first two groups below, in numerical order).
2. Run the analysis scripts in numerical order.
3. Scripts `68`–`80` write `output/us_cut_memo/numbers_*.tex` and the figures; `81_export_stata.py` exports data for the Stata replication. Then compile `us_cut_memo.tex`.

Stata: Done: `stata/` re-estimates the headline numbers and `stata/output/compare.csv` checks them against the memo. See `stata/README.md`.

## Scripts

**Fetch data**

| Script | What it does |
|---|---|
| `01_fetch_fewsnet.py` | Download FEWS NET food insecurity classifications (current situation and projections) from the FEWS NET Data Warehouse API. |
| `03_fetch_fts.py` | Download all humanitarian funding flows from OCHA's Financial Tracking Service (FTS) public API, one year at a time, and flatten them to a table. |
| `04_fetch_ipc_ch.py` | Download IPC and Cadre Harmonisé classifications from the Humanitarian Data Exchange (HDX). These are the multi-agency analyses (not FEWS NET's own classificati... |
| `60_fetch_subnational_aid.py` | Sub-national humanitarian aid: feasibility probe and first download. |

**Build panels**

| Script | What it does |
|---|---|
| `07_build_panel.py` | Build a clean FEWS NET unit x month panel from the raw API pulls. |
| `23_outcome_panel.py` | Area-level outcome panel of food insecurity classifications produced independently of FEWS NET: the Cadre Harmonise (West and Central Africa, 2014 on) and the m... |
| `56_fsnau_surveys.py` | FSNAU (Somalia) seasonal nutrition and mortality survey results, 2009-2025. |
| `62_tidy_3w.py` | Harmonised long tables from the cached OCHA 3W/4W/5W and response-monitoring files. |
| `77_ethiopia_assemble.py` | Ethiopia US-aid-cut data assembly (inventory only, no econometrics). |

**Analysis**

| Script | What it does |
|---|---|
| `57_fsnau_value.py` | Do scheduled survey results improve forecasts of measured malnutrition? Somalia, FSNAU seasonal assessments (post-Gu and post-Deyr), 2011-2024. |
| `67_us_cut_coverage.py` | Feasibility check: could the surveys we have measure the effect of the 2025 US aid cut? |
| `68_somalia_us_cut.py` | Did child wasting rise more in parts of Somalia that relied on US-funded partners? |
| `69_somalia_aid_dependence.py` | Somalia, 2025: did outcomes fall short of prediction more in AID-DEPENDENT places? |
| `70_somalia_need_response.py` | Somalia, 2024-2026: how big was the response, and how much suffering, for a given level of need, before and after the 2025 US aid withdrawal? |
| `71_somalia_first_stage.py` | Somalia: first stage, 2SLS and robustness for the 2025 aid cut (responds to an external review). |
| `72_somalia_ipc_outcome.py` | Somalia: a more proximate outcome for the cash first stage -- current food insecurity. |
| `73_somalia_markets_displacement.py` | Somalia: outcomes closer to cash than wasting -- local prices and displacement. |
| `74_nigeria_us_cut.py` | Nigeria: did outcomes worsen more where aid partners relied on US money, or where partners left? |
| `75_somalia_delivery.py` | Somalia: a fuller first stage from monthly delivered-aid data, and 2SLS by survey season. |
| `76_ethiopia_us_cut.py` | Ethiopia: first stage and food-insecurity outcomes for the 2025 US aid cut (zone level). |
| `80_us_cut_scale.py` | Scale of the estimated effects, and why Somalia, Nigeria and Ethiopia. |

**Export for Stata**

| Script | What it does |
|---|---|
| `81_export_stata.py` | Export analysis-ready CSVs for the Stata replication of the US-cut memo (stata/). |

**Paper numbers, tables and figures**

| Script | What it does |
|---|---|
| `78_us_cut_summary.py` | Summary numbers for the rewritten US-cut memo that are not produced by code/68-76 directly. |
| `79_us_cut_figures.py` | Main-text figures and the core table for the US-cut memo, built to show its four lessons directly. |

## Provenance

Split out of a single project folder in October 2026; the scripts keep their original numbers, so some are not consecutive. Scripts shared with the other papers in this repository are copied, not linked, so each paper stands alone.
