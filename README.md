# Famine early warning, humanitarian aid and measurement: replication code for three papers

Replication code, Stata files and paper source for three papers from one project. Each sits in its own self-contained folder with its own README.

| Folder | Paper |
|---|---|
| [`fewsnet_evaluation/`](fewsnet_evaluation/) | How Much Does Early Warning Improve Famine Response? An evaluation of the Famine Early Warning Systems Network (FEWS NET) |
| [`ipc_surveys/`](ipc_surveys/) | Hunger and Death in Humanitarian Crises: IPC food insecurity phases vs. survey measures of malnutrition and death |
| [`us_cut_memo/`](us_cut_memo/) | The 2025 US aid cuts: effects on malnutrition and death in Somalia, Nigeria and Ethiopia (memo) |

Each folder contains:

- `code/`: Python, numbered in run order. It covers fetching data, building panels, the paper's numbers (as LaTeX macros) and the figures.
- `stata/`: the Stata replication of the core estimates. `00_master.do` runs it, and a compare step lines every Stata number up against the paper. See `stata/README.md`.
- `data/`: hand-built inputs that cannot be downloaded again: LLM-extracted report records, transcribed survey tables and crosswalks.
- `output/`: tables, figures and the paper source and PDF.
- `references/`: source notes and literature reviews.

Scripts shared by several papers are copied into each, so each folder replicates on its own.

The raw data are not included. They total several GB, and several sources (EM-DAT, ACLED, DHS) do not allow redistribution. Every source is public, and the fetch scripts in each paper's `code/` download them. Some exported analysis files contain aggregates derived from ACLED (political violence events and fatalities by area and period); ACLED data are from the Armed Conflict Location & Event Data Project (acleddata.com).

These papers are fully AI generated. Claude Opus 5.5 assembled the data, wrote the code, ran the analysis and drafted the text under human direction.

Code: MIT licence (`LICENSE`). Paper text and figures: © the authors.
