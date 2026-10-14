# Codebook: who did the survey leave out?

One row per survey report. Code only what the extracted text supports; quote the key sentence with its page number. Use "not mentioned" (not "no") when the report is silent.

| Field | Values | Meaning |
|---|---|---|
| `frame_excl_camps` | yes / no / not mentioned | Sampling frame or design explicitly leaves out refugee or IDP camps / settlements |
| `camps_included` | yes / no / not mentioned | Camps or displaced people explicitly included (e.g., own stratum, oversample) |
| `excl_insecure_ex_ante` | yes / no / not mentioned | Whole areas (regions, districts, zones) excluded at design stage for insecurity/inaccessibility |
| `excl_insecure_areas` | free text | Which areas, e.g. "Borno: 8 LGAs" |
| `excl_pop_share` | number or blank | Share of national population in excluded areas, % — only if the report states it or gives numbers to compute it |
| `clusters_dropped_fieldwork` | integer or blank | Selected clusters not interviewed during fieldwork for security/access reasons (incl. those replaced) |
| `clusters_selected` | integer or blank | Total clusters selected |
| `clusters_replaced` | yes / no / not mentioned | Insecure clusters replaced by substitutes |
| `excl_other` | free text | Other population exclusions (nomads, institutional population, islands, flooding, epidemic, etc.) |
| `displacement_question` | yes / no / not mentioned | Questionnaire identifies displaced/refugee status |
| `quote` | text | Key sentence(s), with [p#] |
| `confidence` | high / medium / low | Low if text extraction looks incomplete |
