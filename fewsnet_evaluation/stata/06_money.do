* 06_money.do
* Does humanitarian funding follow FEWS NET's maps or its forecasts?  (paper Section 7, Figure 8,
* Table A1; heterogeneity by official coverage)
*
* Country x FEWS NET map round panel, 2011-2024 (code/31_aid_response.py). Outcome: log humanitarian
* funding committed (FTS, all sectors or food and nutrition) in the 6 months after the map. Regressors:
* share of the country's areas in Crisis+ (Phase 3+) or Emergency+ (4+) on the current map and in the
* medium-term (4-8 month) forecast, in the same regression. Specifications run from a pooled regression
* to within-country (prior 6-month funding, country and map-round fixed effects). Effects are reported
* as % change in funding per 10 percentage points: 100 (exp(0.1 b) - 1). SEs clustered by country.
*
* As in the Python fe_ols(), singletons are dropped once per fixed effect in turn (not iterated), and
* the regression is then run on that sample with reghdfe, keepsingletons.

do _setup.do
cap log close
log using "$OUT/06_money.log", replace text

* fe_reg Y XS, fes(FE1 FE2 ...)  -- the Python fe_ols(): sample, singleton rule, clustered by country.
*   Python scales the cluster-robust variance by G/(G-1) only; reghdfe also multiplies by
*   (N-1)/(N-K), K = regressors + non-nested fixed effects + 1. That factor is undone here, so the
*   standard errors are the Python ones (Stata's own are up to 3% larger with map-round effects).
cap program drop fe_reg
program fe_reg, eclass
    syntax varlist, fes(string)
    gettoken y xs : varlist
    tempvar touse n
    gen byte `touse' = !missing(`y') & !missing(`=subinstr(trim("`xs'"), " ", ",", .)')
    foreach f of local fes {
        bys `f': egen `n' = total(`touse')
        replace `touse' = 0 if `n' <= 1
        drop `n'
    }
    tempname V
    if "`fes'" == "one" {          // pooled: plain OLS with a constant
        regress `y' `xs' if `touse', vce(cluster iso)
        matrix `V' = e(V) * (e(N) - e(df_m) - 1) / (e(N) - 1)
    }
    else {
        reghdfe `y' `xs' if `touse', absorb(`fes') vce(cluster iso) keepsingletons
        matrix `V' = e(V) * (e(N) - e(df_m) - e(df_a) - 1) / (e(N) - 1)
    }
    ereturn repost V = `V'
end

* ============================================================================
* 1. Country x round panel
* ============================================================================
import delimited using "$DATA/aid_panel.csv", clear
ym report_month
encode country_code, gen(iso)
gen round = report_month
gen one = 1
tempfile panel
save `panel'

* ============================================================================
* 2. Funding on current and forecast shares, together (Figure 8, Table A1 columns 1-2)
* ============================================================================
foreach col in all food {
    local K = cond("`col'" == "all", "All", "Food")
    foreach k in 3 4 {
        local KK = cond(`k' == 3, "Three", "Four")
        * pooled, no controls ("one" = a constant)  /  within-country: prior funding, country + round FE
        foreach s in Pool Within {
            if "`s'" == "Pool"   quietly fe_reg f_`col' s`k'_cs s`k'_ml2, fes(one)
            if "`s'" == "Within" quietly fe_reg f_`col' s`k'_cs s`k'_ml2 f_`col'_lag, fes(iso round)
            foreach t in cs ml2 {
                local T = cond("`t'" == "cs", "Cur", "Fc")
                local b = _b[s`k'_`t']
                local se = _se[s`k'_`t']
                display as text "`col' `k'+ `s' `t': b = " as result %7.3f `b' as text " (" as result %5.3f `se' as text ")"
                res aid`K'`KK'`T'`s'       100 * (exp(0.1 * `b') - 1)
                res aid`K'`KK'`T'`s'Ci_lo  100 * (exp(0.1 * (`b' - 1.96 * `se')) - 1)
                res aid`K'`KK'`T'`s'Ci_hi  100 * (exp(0.1 * (`b' + 1.96 * `se')) - 1)
                * Table A1 (Crisis+, within-country): coefficient per 10 points
                if `k' == 3 & "`s'" == "Within" {
                    local rk = cond("`t'" == "cs", "cur", "fc")
                    res tab_money_`rk'_`col'    10 * `b'
                    res tab_money_`rk'_`col'_se 10 * `se'
                }
            }
            if `k' == 3 & "`s'" == "Within" {
                res tab_money_n_`col'         e(N)
                res tab_money_countries_`col' e(N_clust)
            }
        }
    }
}

* ============================================================================
* 3. Which part of the forecast moves money? (Table A1 columns 3-6)
* ============================================================================
* Country-round means over FEWS NET areas of the predictable part of the Crisis+ forecast (b_) and
* FEWS NET's contribution beyond it (c_), from public raw data (b_, c_) or raw data plus the latest
* Cadre Harmonise / IPC (bi_, ci_); and the share of areas with an official analysis (for section 4).
import delimited using "$DATA/contrib_areas.csv", clear
ym r
gen has_ipc = !missing(ipc_last3)
collapse (mean) b_fc3 c_fc3 bi_fc3 ci_fc3 has_ipc, by(country_code r)
rename r report_month
merge 1:1 country_code report_month using `panel', keep(match) nogenerate
tempfile both
save `both'

foreach bl in raw rawipc {
    local p = cond("`bl'" == "raw", "", "i")
    foreach col in all food {
        quietly fe_reg f_`col' b`p'_fc3 c`p'_fc3 f_`col'_lag, fes(iso round)
        display as text "`bl' `col': base " as result %6.3f _b[b`p'_fc3] as text "  contribution " as result %6.3f _b[c`p'_fc3]
        res tab_money_base_`bl'_`col'       10 * _b[b`p'_fc3]
        res tab_money_base_`bl'_`col'_se    10 * _se[b`p'_fc3]
        res tab_money_contrib_`bl'_`col'    10 * _b[c`p'_fc3]
        res tab_money_contrib_`bl'_`col'_se 10 * _se[c`p'_fc3]
        res tab_money_n_`bl'_`col'          e(N)
        res tab_money_countries_`bl'_`col'  e(N_clust)
    }
}

* ============================================================================
* 4. Heterogeneity: does money follow FEWS NET's contribution more where official analyses are scarce?
* ============================================================================
* hi = more than half the country's FEWS NET areas have a Cadre Harmonise / IPC analysis
use `both', clear
gen hi = has_ipc > 0.5
summarize hi, meanonly
res hetShareHigh 100 * r(mean)
gen cx = c_fc3 * hi
gen bx = b_fc3 * hi
foreach col in all food {
    local K = cond("`col'" == "all", "All", "Food")
    quietly fe_reg f_`col' b_fc3 c_fc3 bx cx f_`col'_lag, fes(iso round)
    display as text "`col': contribution where coverage low " as result %6.3f _b[c_fc3] ///
        as text ", extra where high " as result %6.3f _b[cx] as text " (" as result %5.3f _se[cx] as text ")"
    res het`K'Low    100 * (exp(0.1 * _b[c_fc3]) - 1)
    res het`K'High   100 * (exp(0.1 * (_b[c_fc3] + _b[cx])) - 1)
    res het`K'Diff   _b[cx]
    res het`K'DiffSe _se[cx]
}

res_save results_06
log close
