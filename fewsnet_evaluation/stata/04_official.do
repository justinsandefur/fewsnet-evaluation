* 04_official.do
* FEWS NET's forecasts against the official IPC / Cadre Harmonise projections
* (paper Section 6.2, Table 3, Figure 4)
*
* Reproduces code/34_official_projections.py and code/42_paper_bootstrap.py (official() and
* bootstrap() in 40_paper.py). Each official projection is matched to FEWS NET's forecast for the
* same area and period (overlay done in Python) and both are scored against the next official
* current-situation analysis: Crisis or worse (Phase 3+), next3.
*   1. Hit and false-alarm rates for areas not in Crisis at the latest official analysis
*   2. Table 3: next3 on the official projection (Phase 3+) and FEWS NET's forecast (share of the
*      area in Phase 3+), country x analysis-round FE, clustered by country
*   3. Wild cluster bootstrap p-values (Rademacher, null imposed, 1,999 draws): only 12-14
*      countries, so cluster-robust standard errors are unreliable. Draws differ from Python's,
*      so p-values agree only up to simulation noise.

do _setup.do
cap log close
log using "$OUT/04_official.log", replace text

import delimited using "$DATA/official.csv", clear
save "$OUT/official.dta", replace


* ============================================================================
* 1. Who saw the new Crises coming?
* ============================================================================
preserve
    keep if last3 == 0 & !missing(fews_fc3)
    res offN _N
    quietly count if next3 == 1
    res offNew r(N)
    quietly tab iso3
    res offCountries r(r)
    quietly summarize year
    res offYears_lo r(min)
    res offYears_hi r(max)
    gen fews = fews_fc3 >= 0.5                  // FEWS NET forecasts most of the area in Crisis+
    gen either = proj3 == 1 | fews
    gen only_fews = proj3 == 0 & fews
    * hit rates among new Crises (next3 = 1), false alarms among areas that stayed out (next3 = 0)
    foreach v in proj3 fews either {
        local k = cond("`v'" == "proj3", "Official", cond("`v'" == "fews", "Fews", "Either"))
        quietly summarize `v' if next3 == 1
        res offHit`k' 100 * r(mean)
        quietly summarize `v' if next3 == 0
        res offFa`k' 100 * r(mean)
    }
    quietly summarize only_fews if next3 == 1
    res offHitOnlyFews 100 * r(mean)
restore


* ============================================================================
* 2. Table 3: head-to-head regressions
* ============================================================================
local s1 proj3
local s2 fews_fc3
local s3 proj3 fews_fc3
local s4 proj3 fews_fc3 last3
local s5 proj3 fews_fc3 last3 fews_cur3
foreach samp in all new {
    forvalues j = 1/5 {
        use "$OUT/official.dta", clear
        if "`samp'" == "new" keep if last3 == 0
        foreach x of local s`j' {
            drop if missing(`x')
        }
        reghdfe next3 `s`j'', absorb(cell) vce(cluster iso3)
        foreach x of local s`j' {
            if "`samp'" == "new" & "`x'" == "last3" continue    // constant 0 in this sample
            local tn = subinstr("`x'", "_", "", .)
            res tab_official_`samp'_`tn'_c`j'   _b[`x']
            res tab_official_`samp'_`tn'se_c`j' _se[`x']
        }
        res tab_official_`samp'_n_c`j' e(N)
        res tab_official_`samp'_g_c`j' e(N_clust)
        local S = cond("`samp'" == "all", "All", "New")
        * headline: column 4 for all areas (controls for the latest official analysis), column 3
        * for areas not in Crisis at the latest analysis
        if ("`samp'" == "all" & `j' == 4) | ("`samp'" == "new" & `j' == 3) {
            res offCoef`S'Fews _b[fews_fc3]
            res offCoef`S'Proj _b[proj3]
            * 3. wild cluster bootstrap p-values
            boottest fews_fc3, reps(1999) weighttype(rademacher) seed(1) nograph
            res bootOff`S'Fews r(p)
            boottest proj3, reps(1999) weighttype(rademacher) seed(1) nograph
            res bootOff`S'Proj r(p)
        }
        if "`samp'" == "all" & `j' == 3 {
            res offNall e(N)
            res offCountriesAll e(N_clust)
        }
    }
}

res_save results_04
log close
