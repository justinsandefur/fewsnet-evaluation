* 03_report_surveys.do
* Surveys quoted in FEWS NET's reports, Somalia, Ethiopia and Sudan (paper section 9; code/53_text_value.py).
*   Coverage: share of areas mapped Emergency with a survey quoted in the previous 12 months.
*   New surveys: does a survey fielded between FEWS NET's forecast and its next map move that map?
*   Linear probability model with country-by-round cells, controls for the forecast and everything the
*   reports said about the area, clustered by first-level administrative area.

do _setup.do
cap log close
log using "$OUT/03_report_surveys.log", replace text

import delimited using "$DATA/report_surveys.csv", clear varnames(1)
res svTotal _N

import delimited using "$DATA/coverage.csv", clear varnames(1) case(preserve)
foreach c in ET SO SD {
    qui summarize s_any if country_code == "`c'" & phase >= 4
    res svEmerg`c' 100 * r(mean)
}

import delimited using "$DATA/newsurvey.csv", clear varnames(1) case(preserve)
egen cellid = group(cell)
egen clid = group(cl)
local ctrl fc4 t_det t_worst4 t_proj4 t_access t_conflict t_rain t_prices t_mention s_any flag fc_flag
qui summarize up
res nsUpBase 100 * r(mean)
reghdfe up new_s `ctrl', absorb(cellid) vce(cluster clid)
res nsUp 100 * _b[new_s]
res nsUpSe 100 * _se[new_s]
* by what the survey found: acute malnutrition of 15% or more vs less
reghdfe up new_crit new_ok `ctrl', absorb(cellid) vce(cluster clid)
res nsCritUp 100 * _b[new_crit]
res nsOkUp 100 * _b[new_ok]

res_save results_03
log close
