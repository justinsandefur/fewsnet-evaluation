* 07_shocks.do
* Do local shocks predict the classifications, and does FEWS NET coverage change what shocks do?
* (paper Section 9 and Appendix D; code/27_shock_index.py)
*
* Unit: Cadre Harmonise / IPC area x analysis month (independent of FEWS NET's own maps). Shocks, all
* measured before the analysis: rainfall deficits (dry6, dry12, drought), political violence (ACLED
* events and deaths, and their change) and cereal price changes (WFP), with missing indicators.
*   1. Within R-squared of the shocks, within area and country x month (shockRsq, shockRsqRain).
*   2. Shock index: the shocks weighted by their coefficients estimated on all OTHER countries
*      (leave-one-country-out), standardised.
*   3. y = index x covered + country-specific index slopes + area FE + country x month FE, before 2025
*      and in 2025-26 (shutdown and staggered restoration). SEs clustered by country.
* Singletons are dropped once per fixed effect in turn (area, then country x month), as in Python.

do _setup.do
cap log close
log using "$OUT/07_shocks.log", replace text

* fe_reg Y XS [if], fes(...) [slopes(...)]  -- Python fe_ols(): singleton rule on fes(), clustered by
* country, variance scaled by G/(G-1) only (reghdfe's (N-1)/(N-K) factor undone). Country-specific
* index slopes are absorbed (same coefficient and clustered SE on ix_cov as with slope regressors,
* which outnumber the clusters and would leave Stata's full variance matrix singular).
cap program drop fe_reg
program fe_reg, eclass
    syntax varlist(fv) [if], fes(string) [slopes(string)]
    gettoken y xs : varlist
    marksample touse, novarlist
    tempvar n
    replace `touse' = 0 if missing(`y')
    foreach f of local fes {
        bys `f': egen `n' = total(`touse')
        replace `touse' = 0 if `n' <= 1
        drop `n'
    }
    reghdfe `y' `xs' if `touse', absorb(`fes' `slopes') vce(cluster iso) keepsingletons tolerance(1e-12)
    tempname V
    matrix `V' = e(V) * (e(N) - e(df_m) - e(df_a) - 1) / (e(N) - 1)
    ereturn repost V = `V'
end

* demean VARS if COND -- residuals from area and country x month effects (the Python within())
cap program drop demean
program demean
    syntax varlist [if]
    foreach v of local varlist {
        cap drop w_`v'
        quietly reghdfe `v' `if', absorb(key cm) resid(w_`v') keepsingletons tolerance(1e-12)
    }
end

import delimited using "$DATA/shock_panel.csv", clear
gen cm = iso3 + "_" + month
ym month
encode iso3, gen(iso)
local F dry6 dry12 drought ln_ev6 ln_fat6 d_ln_ev6 dp12 dp3 miss_conf miss_price

* ============================================================================
* 1. How much of the classifications do local shocks explain? (within R-squared)
* ============================================================================
* sample: singletons (counted on phase3) dropped by area, then by country x month
preserve
    foreach f in key cm {
        bys `f': gen n = _N
        drop if n <= 1
        drop n
    }
    demean share3 `F'
    * no constant: R-squared = 1 - SSR / sum of squared demeaned outcome, as in Python
    quietly regress w_share3 w_dry6 w_dry12 w_drought, noconstant
    display as text "within R2, rainfall: " as result %6.4f e(r2)
    res shockRsqRain 100 * e(r2)
    quietly regress w_share3 w_dry6 w_dry12 w_drought w_ln_ev6 w_ln_fat6 w_d_ln_ev6 w_miss_conf w_dp12 w_dp3 w_miss_price, noconstant
    display as text "within R2, all three: " as result %6.4f e(r2)
    res shockRsq 100 * e(r2)
restore

* ============================================================================
* 2-3. Leave-one-country-out shock index, and the coverage x index interaction
* ============================================================================
foreach y in share3 phase3 {
    preserve
        keep if !missing(`y')
        foreach f in key cm {
            bys `f': gen n = _N
            drop if n <= 1
            drop n
        }
        demean `y' `F'
        local wF
        foreach f of local F {
            local wF `wF' w_`f'
        }
        * index for country c = its raw shocks x weights fitted (within) on all other countries
        gen ix = .
        levelsof iso3, local(cs)
        foreach c of local cs {
            quietly regress w_`y' `wF' if iso3 != "`c'", noconstant
            tempvar xb
            gen `xb' = 0
            foreach f of local F {
                quietly replace `xb' = `xb' + _b[w_`f'] * `f'
            }
            quietly replace ix = `xb' if iso3 == "`c'"
            drop `xb'
        }
        summarize ix
        replace ix = (ix - r(mean)) / r(sd)
        gen ix_cov = ix * covd
        foreach s in Pre Post {
            if "`y'" == "phase3" & "`s'" == "Post" continue
            local sel = cond("`s'" == "Pre", "month <= tm(2024m12)", "month >= tm(2025m1)")
            quietly fe_reg `y' ix_cov if `sel', fes(key cm) slopes(iso#c.ix)
            display as text "`y' `s': index x covered = " as result %7.4f _b[ix_cov] as text " (" as result %6.4f _se[ix_cov] as text "), N = " e(N) ", countries = " e(N_clust)
            local P = cond("`y'" == "phase3", "Phase", "")
            res cov`s'`P'   _b[ix_cov]
            res cov`s'`P'Se _se[ix_cov]
        }
    restore
}

res_save results_07
log close
