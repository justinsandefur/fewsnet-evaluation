* 04_somalia_iv_and_prediction.do
* Two ways to scale the null for aid dependence.  (memo Sections 3 and 6)
*
* Part 1. Two-stage least squares, Gu 2025 surveys.
*   Aid dependence (Z) predicts where food and cash fell (X; 02_somalia_first_stage.do). If losing
*   aid raised wasting, wasting should have risen in proportion. 2SLS divides the reduced form
*   (Z -> wasting) by the first stage (Z -> X). With a first-stage F near 10 the usual 2SLS
*   interval is unreliable, so we report the Anderson-Rubin (AR) interval: the set of effects
*   beta0 for which Z does not predict (wasting - beta0 * X). It stays valid however weak Z is.
*
* Part 2. Prediction gap (placebo in time).
*   Fit wasting on domain effects, season, a trend, rainfall, conflict and prices using pre-2025
*   years only, leaving out one year at a time, and average the prediction error in the held-out
*   year. Was 2025 or 2026 unusually far above prediction compared with 2017-2024?

do _setup.do
log using "$OUT/04_somalia_iv_and_prediction.log", replace text
use "$OUT/som_panel.dta", clear

global FE   "i.dom_id i.type_round"
global CTRL "rain_z rain12_z log_fat"


* ============================================================================
* 1. 2SLS with Anderson-Rubin intervals
* ============================================================================
* Sample: 2015 - Gu 2025 (Deyr 2025 dropped: the delivered-aid windows are Jan-Jun 2025).
* X and Z enter interacted with the Gu 2025 indicator.
*   name        X (domain average of district values)                      Z
*   FscLIdx     food & cash reached lost per 100 residents, Jan-Jun 2025   aid dependence
*   ReachIdx    cash recipients lost per 100 residents per month           aid dependence
*   LogUs       proportional loss of cash transfers                        US share of partners
* The memo reports the effect at the average loss: beta x mean of X in Gu 2025.

capture program drop ar_iv
program ar_iv
    args name y x z
    preserve
    keep if year <= 2025 & !deyr25
    gen xp = `x' * gu25
    gen zp = `z' * gu25
    quietly regress `y' xp zp $CTRL $FE              // defines the common estimation sample
    keep if e(sample)

    * first stage: F on the excluded instrument
    quietly regress xp zp $CTRL $FE, vce(cluster region)
    local F = (_b[zp] / _se[zp])^2
    * 2SLS
    quietly ivregress 2sls `y' (xp = zp) $CTRL $FE, vce(cluster region)
    local beta = _b[xp]
    local se   = _se[xp]
    quietly summarize `x' if gu25
    local xbar = r(mean)

    * Anderson-Rubin set: grid of beta0 values; keep those where the test that Z does not predict
    * y - beta0 * x is not rejected at 5% (F test with G-1 denominator degrees of freedom).
    local span = max(40 * abs(`se'), 4 * abs(`beta'), 2)
    local lo = .
    local hi = .
    forvalues i = 0/2000 {
        local b0 = `beta' - `span' + 2 * `span' * `i' / 2000
        quietly gen u = `y' - `b0' * xp
        quietly regress u zp $CTRL $FE, vce(cluster region)
        quietly test zp
        if r(p) > 0.05 {
            if `lo' == . local lo = `b0'
            local hi = `b0'
        }
        drop u
    }
    display as text _n "`name': first-stage F = " as result %4.1f `F' ///
        as text "   2SLS beta = " as result %6.3f `beta' as text " (se " as result %5.3f `se' as text ")"
    display as text "   effect at mean loss (" as result %5.2f `xbar' as text "): " ///
        as result %5.1f `beta' * `xbar' as text " pp of wasting, AR 95% set [" ///
        as result %5.1f `lo' * `xbar' as text ", " as result %5.1f `hi' * `xbar' as text "]"
    restore
    * names as in the memo's numbers_*.tex
    if "`name'" == "FscLIdx" {
        res dvIvFFscLIdxGamGu    `F'
        res dvIvAtFscLIdxGamGu   `beta' * `xbar'
        res dvIvAtLoFscLIdxGamGu `lo' * `xbar'
        res dvIvAtHiFscLIdxGamGu `hi' * `xbar'
    }
    else {
        res ivAtMean`name'Gam   `beta' * `xbar'
        res ivAtMeanLo`name'Gam `lo' * `xbar'
        res ivAtMeanHi`name'Gam `hi' * `xbar'
    }
end

ar_iv FscLIdx  gam fsc_loss25      aid_dep
ar_iv ReachIdx gam cash_reach_loss aid_dep
ar_iv LogUs    gam cash_plog       us_share


* ============================================================================
* 2. Prediction gap: was wasting above what rain, conflict and prices predict?
* ============================================================================
gen deyr  = season_type == "Deyr"
gen trend = year - 2015
tempfile gaps
postfile G year mean_err domains using `gaps'
forvalues yr = 2017/2026 {
    * fit on pre-2025 years other than the held-out year
    quietly regress gam i.dom_id deyr trend $CTRL lp_cereal lp_goat if year != `yr' & year < 2025
    * predict for the held-out year, domains seen in the fit only
    quietly gen insample = e(sample)
    quietly egen known = max(insample), by(domain)
    quietly predict yhat if year == `yr' & known & !missing(gam)
    quietly gen err = gam - yhat
    preserve
        quietly keep if !missing(err)
        collapse (mean) err, by(domain)          // average error per domain, then across domains
        quietly summarize err
        post G (`yr') (r(mean)) (r(N))
    restore
    drop insample known yhat err
}
postclose G
preserve
    use `gaps', clear
    display as text _n "Wasting minus prediction (pp), by held-out year:"
    list, noobs
    summarize mean_err if year == 2025, meanonly
    res scSomPpNatTv r(mean)
    summarize mean_err if year == 2026, meanonly
    res scSomPpNatTs r(mean)
    summarize mean_err if year < 2025
    display as text "s.d. of the 2017-2024 gaps: " as result %4.2f r(sd)
restore

res_save results_04
log close
