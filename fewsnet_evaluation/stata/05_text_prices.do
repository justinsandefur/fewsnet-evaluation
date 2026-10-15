* 05_text_prices.do
* Which pieces of FEWS NET are worth paying for: its reports and its price data
* (paper Section 6, reports pilot and Appendix table of escalation; pieces() and text_table() in
* 40_paper.py)
*
* Reproduces code/53_text_value.py (pilot on FEWS NET's reports, Somalia, Ethiopia and Sudan) and
* code/55_price_value.py (does price data improve the forecast?).
*   1. Reports table: among areas in Crisis (Phase 3), does the area reach Emergency on the next
*      map (next4) or by need (need4: +1 phase if flagged as held back by aid)? Linear probability,
*      map then text then survey/data-gap features, country x round FE, clustered by region (admin1)
*   2. AUCs, map alone vs map + text: roctab on the cross-fitted predictions exported from Python
*      (penalised logistic regression with country and month-of-year dummies)
*   3. Counts quoted in the text: reports, outlooks, check of the extraction against the maps
*   4. Price data: AUCs from the cross-fitted gradient-boosted predictions (55_price_value.py) and
*      the number of markets in FEWS NET's own price data

do _setup.do
cap log close
log using "$OUT/05_text_prices.log", replace text


* ============================================================================
* 1. Escalation from Crisis: map, text, data  (reports table)
* ============================================================================
import delimited using "$DATA/text_panel.csv", clear
save "$OUT/text_panel.dta", replace
keep if phase == 3 & has_text == 1 & !missing(next_phase, fc_phase)
res txtEscN _N
quietly count if next4 == 1
res txtEscEvents r(N)
quietly summarize fc4 if next4 == 1
res txtEscFcFour 100 * r(mean)                  // share of escalations FEWS NET forecast
quietly summarize next4
res nsEscBase 100 * r(mean)                     // base rate of escalation

local map  fc4 flag fc_flag
local text t_proj4 t_worst4 t_det t_aid_down t_access t_conflict t_rain t_prices t_uncert t_mention
local data s_any s_gam15 s_mort g_any
local x1 `map'
local x2 `map' `text'
local x3 `map' `text' `data'
local j = 0
foreach y in next4 need4 {
    forvalues m = 1/3 {
        local ++j
        reghdfe `y' `x`m'', absorb(cell) vce(cluster cl)
        pyse                                     // Python's standard-error convention (_setup.do)
        foreach v of local x`m' {
            local vn = subinstr("`v'", "_", "", .)
            res tab_text_`vn'_c`j'   _b[`v']
            res tab_text_`vn'se_c`j' _se[`v']
        }
        res tab_text_n_c`j' e(N)
        if "`y'" == "next4" & `m' == 2 {
            res txtAidDown 100 * _b[t_aid_down]
            res txtAccess  100 * _b[t_access]
        }
    }
}


* ============================================================================
* 2. Does the text improve the ranking of escalations?  (cross-fitted predictions)
* ============================================================================
import delimited using "$DATA/text_preds.csv", clear
foreach y in next4 need4 {
    local k = cond("`y'" == "next4", "Map", "Need")
    roctab `y' `y'_map
    res txtAuc`k' r(area)
    roctab `y' `y'_text
    res txtAuc`k'Text r(area)
}


* ============================================================================
* 3. The reports and the extraction check
* ============================================================================
import delimited using "$DATA/text_reports.csv", clear varnames(1)
res txtReports _N
quietly count if rtype == "food-security-outlook"
res txtOutlooks r(N)

* Does the current phase stated in the text match FEWS NET's map for the matched areas?
use fnid r phase using "$OUT/text_panel.dta", clear
tempfile ph
save `ph'
import delimited using "$DATA/text_mentions.csv", clear stringcols(_all)
destring order cur, replace
joinby fnid r using `ph'
* one row per mention: the stated phase (first non-missing) against the range of mapped phases
sort name i order
by name i: egen mx = max(phase)
by name i: egen mn = min(phase)
gen o2 = cond(missing(cur), ., order)
by name i: egen first = min(o2)
by name i: egen c1 = max(cond(order == first, cur, .))
by name i: keep if _n == 1
drop if missing(c1, mx, mn)
gen match = c1 >= mn & c1 <= mx
quietly summarize match
res txtMatch 100 * r(mean)
res txtMatchN r(N)


* ============================================================================
* 4. Price data
* ============================================================================
import delimited using "$DATA/fdw_markets.csv", clear
quietly count if own == 1
res prMarketsFews r(N)                          // markets with series not sourced from WFP

* AUC from ranks (Mann-Whitney, ties averaged): identical to roctab's area, much faster on 150k rows
cap program drop aucrank
program aucrank, rclass
    syntax varlist(min=2 max=2) [if]
    tokenize `varlist'
    marksample touse
    tempvar rk
    egen double `rk' = rank(`2') if `touse'
    quietly summarize `rk' if `touse' & `1' == 1
    local n1 = r(N)
    local s1 = r(sum)
    quietly count if `touse' & `1' == 0
    return scalar area = (`s1' - `n1' * (`n1' + 1) / 2) / (`n1' * r(N))
end

import delimited using "$DATA/price_preds.csv", clear
foreach task in new esc {
    local T = cond("`task'" == "new", "New", "Esc")
    local tl = cond("`task'" == "new", "new crisis", "escalation")
    foreach m in base wfp fews both fc raw rawboth rawmap {
        local M = cond("`m'" == "fc", "Fc", strproper("`m'"))
        if "`m'" == "rawboth" local M RawBoth
        if "`m'" == "rawmap"  local M RawMap
        aucrank y `m' if task == "`tl'" & !missing(`m')
        res pv`T'`M' r(area)
    }
}

res_save results_05
log close
