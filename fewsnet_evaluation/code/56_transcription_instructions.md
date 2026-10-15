# FSNAU survey tables: transcription rules (used by `56_fsnau_surveys.py`)

FSNAU's seasonal nutrition technical reports (2010/11 to 2016/17) give survey results in
region-by-region tables ("Summary of Key Nutrition Findings ...") and, in some years, a
consolidated annex ("Summary of Nutrition Assessments ..."). The layouts change from year to
year and the PDF text layer scrambles them, so these tables were transcribed by reading
the pages (text layer in `input/fsnau/text/<file>.txt`, page images from the PDF in
`input/fsnau/raw/`). Every transcribed row is flagged `hand_transcribed = True` in
`surveys.csv`, and the script checks each transcribed number against the page text.

## Output

One CSV per report at `input/fsnau/transcribed/<pdf file stem>.csv`, one row per survey
(population group) **for the season the report covers only**. Many tables also show the
previous one or two seasons for comparison: do not record those columns.

Columns (leave blank when the document does not give the value; never infer or compute):

| column | content |
|---|---|
| `season` | e.g. `Gu 2013`, `Deyr 2013/14` (the report's season) |
| `file` | PDF file name |
| `page` | PDF page number (1-based, as in `=====PAGE n` of the text file) of the table the values come from |
| `table` | table caption as printed, e.g. `Table 9: Summary of Key Nutrition Findings: Northwest IDPs - Gu 2014` |
| `population_group` | survey name exactly as printed (e.g. `Hargeisa IDPs`, `Bay Agropastoral`, `North Gedo Riverine`) |
| `region` | region(s) if the table or caption names them, else blank |
| `population_type` | `rural`, `urban`, `IDP`, or `mixed` (e.g. a district survey covering town and rural) |
| `fieldwork` | survey month(s) as stated in caption/header/text for this survey, e.g. `July 2014`, `Oct-Nov 2012` |
| `method` | `SMART` (anthropometric cluster survey, the default) or `MUAC rapid` (MUAC-only screening/rapid assessment) or as stated |
| `n_children` | number of children 6-59 months in the anthropometric sample (the `N=` total), if given |
| `n_clusters` | number of clusters, if given |
| `gam`, `gam_lo`, `gam_hi` | Global acute malnutrition, weight-for-height z < -2 and/or oedema, WHO growth standards, %, with 95% CI. If both WHO and NCHS are shown, use WHO. Total, not boys/girls |
| `sam`, `sam_lo`, `sam_hi` | Severe acute malnutrition, WHZ < -3 and/or oedema, WHO, % with CI |
| `muac_gam`, `muac_gam_lo`, `muac_gam_hi` | MUAC < 12.5 cm and/or oedema, % with CI |
| `muac_sam` | MUAC < 11.5 cm and/or oedema, % |
| `cdr`, `cdr_lo`, `cdr_hi` | crude death rate, deaths/10,000/day, with CI |
| `u5dr`, `u5dr_lo`, `u5dr_hi` | under-five death rate, deaths/10,000/day, with CI |
| `notes` | anything odd: printed typos (e.g. `(0.9-3.20` missing bracket), value only in text, CI missing, table says "not done", MUAC-only because of insecurity, etc. |

Rules:

1. Record only what the page shows. Do not use outside knowledge of Somalia survey results.
2. Copy numbers as printed (keep `0.0`, keep apparent typos and explain in `notes`).
3. A survey that appears in both a region table and an annex: take the region table (it has
   the CIs) and note the annex page in `notes` if values differ.
4. If a report also lists surveys done by partners (not FSNAU) and the table includes them,
   record them and say so in `notes` (e.g. `partner survey: ACF`).
5. Include MUAC-only rapid assessments as rows with `method = MUAC rapid`.
6. Statements about areas **not surveyed** (e.g. "no survey in Middle Juba due to insecurity")
   go in a separate file `<pdf file stem>_gaps.txt`, one line each: page number, the area,
   the reason, quoted briefly.
