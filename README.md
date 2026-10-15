# FEWS NET evaluation and companion paper: replication code

Replication code, Stata files and paper source for two papers. Each sits in its own self-contained folder with its own README.

| Folder | Paper |
|---|---|
| [`fewsnet_evaluation/`](fewsnet_evaluation/) | How Much Does Early Warning Improve Famine Response? An evaluation of the Famine Early Warning Systems Network (FEWS NET) |
| [`ipc_surveys/`](ipc_surveys/) | Hunger and Death in Humanitarian Crises: IPC food insecurity phases vs. survey measures of malnutrition and death |

Each folder contains:

- `code/`: Python, numbered in run order. It covers fetching data, building panels, the analysis, the paper's numbers (as LaTeX macros) and the figures.
- `stata/`: the Stata replication of the core estimates (done for `ipc_surveys/`; in progress for `fewsnet_evaluation/`, see its `STATA_PORT.md`).
- `data/`: hand-built inputs that cannot be downloaded again: LLM-extracted report records, transcribed survey tables and crosswalks.
- `output/`: tables, figures and the paper source and PDF (`output/cgd_paper/`).
- `references/`: source notes and literature reviews.

Scripts shared by both papers are copied into each, so each folder replicates on its own. A third paper from the same project, on the 2025 US aid cuts, is maintained separately.

The raw data are not included. They total several GB, and several sources (EM-DAT, ACLED, DHS) do not allow redistribution. Every source is public, and the fetch scripts in each paper's `code/` download them.

These papers are fully AI generated. Claude Opus 5.5 assembled the data, wrote the code, ran the analysis and drafted the text under human direction.

Code: MIT licence (`LICENSE`). Paper text and figures: © the authors.
