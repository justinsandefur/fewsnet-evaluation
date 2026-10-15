* 02_somalia_first_stage.do
* Where did the cut actually bite?  (memo Section 2, Figures 1-2, first rows of Table 1)
*
* Before asking whether wasting rose more in "exposed" places, check that aid actually fell more
* there. This is the first stage of the instrumental-variables logic: exposure (2024) -> aid lost
* (2025, 2026) -> child wasting. A weak first stage (F well below 10) means a zero in the outcome
* regressions says little about what losing aid does.
*
* Unit: district (74). Each regression is a cross-section: aid lost on one exposure, standard
* errors clustered by the 18 regions. F = squared t-statistic.

do _setup.do
log using "$OUT/02_somalia_first_stage.log", replace text


* ============================================================================
* 1. National totals: how much did delivery fall?
* ============================================================================
* US humanitarian funding to Somalia (FTS, US$ m, by decision date)
import delimited using "$DATA/som_fts.csv", clear
list, noobs
summarize us_musd if year == 2024, meanonly
local us24 = r(mean)
summarize us_musd if year == 2025, meanonly
res UsTwentyFour `us24'
res UsTwentyFive r(mean)
display "US funding fell by " %3.0f 100 * (1 - r(mean) / `us24') "%"

* People reached with food or cash per month (millions) and sites treating severe
* malnutrition, January-June of each year
import delimited using "$DATA/som_delivery_national.csv", clear
list, noobs
foreach y in 2024 2025 2026 {
    summarize fsc_nat if year == `y', meanonly
    local f`y' = r(mean) / 1e6
    summarize otp_nat if year == `y', meanonly
    local o`y' = r(mean)
}
res sumFscHaTf `f2024'
res sumFscHaTv `f2025'
res sumFscHaTs `f2026'
res sumOtpHaTf `o2024'
res sumOtpHaTs `o2026'


* ============================================================================
* 2. District first stage: which exposure predicts where aid fell?
* ============================================================================
use "$OUT/som_districts.dta", clear

* Table 1, top panel: food & cash reached lost per 100 residents, Jan-Jun 2025 (Tv) and 2026 (Ts),
* per s.d. of each exposure.
foreach z in aid_dep us_share agency_loss {
    if "`z'" == "aid_dep"     local zt Dep
    if "`z'" == "us_share"    local zt Us
    if "`z'" == "agency_loss" local zt Loss
    foreach y in 25 26 {
        local yt = cond(`y' == 25, "Tv", "Ts")
        quietly regress fsc_loss`y' `z', vce(cluster region)
        quietly summarize `z' if e(sample)
        local sd = r(sd)
        display as text %-12s "`z'" "  20`y':  b per s.d. = " as result %6.2f _b[`z'] * `sd' ///
            as text "  (se " as result %4.2f _se[`z'] * `sd' as text ")   F = " as result %5.1f (_b[`z'] / _se[`z'])^2
        res ctFs`zt'`yt'   _b[`z'] * `sd'
        res ctFsSe`zt'`yt' _se[`z'] * `sd'
        res ctFsF`zt'`yt'  (_b[`z'] / _se[`z'])^2
    }
}

* Other measures of delivered aid (memo text): F-statistics only.
*   Gu window = Jan-Jun 2025; Ts = Jan-Jun 2026.
*   fsc_plog = proportional food/cash loss; otp_loss = treatment sites lost per 10,000 under-fives;
*   cash_plog = proportional loss of cash transfers; cash_reach_loss = cash recipients lost.
capture program drop fstat
program fstat
    args name y z
    quietly regress `y' `z', vce(cluster region)
    display as text %-16s "`name'" %-18s "`y'" %-12s "`z'" " F = " as result %5.1f (_b[`z'] / _se[`z'])^2
    res `name' (_b[`z'] / _se[`z'])^2
end
fstat dvFFscLIdxGu  fsc_loss25      aid_dep
fstat dvFFscGUsGu   fsc_plog25      us_share
fstat dvFOtpLIdxGu  otp_loss25      aid_dep
fstat dvFOtpLUsGu   otp_loss25      us_share
fstat sumFFscIdxTs  fsc_loss26      aid_dep
fstat sumFFscUsTs   fsc_loss26      us_share
fstat sumFOtpIdxTs  otp_loss26      aid_dep
fstat sumFOtpUsTs   otp_loss26      us_share
fstat fsFLogUs      cash_plog       us_share
fstat fsFReachIdx   cash_reach_loss aid_dep


* ============================================================================
* 3. Figure 2 numbers: food & cash reached per 100 residents per month, by thirds of exposure
* ============================================================================
* (Districts with no food/cash record in 2024 are left out, as in the figure.)
foreach z in aid_dep us_share {
    local zt = cond("`z'" == "aid_dep", "Dep", "Us")
    preserve
        keep if has_fsc24 & !missing(`z')
        * thirds by rank, cut-points at 1 + (n-1)/3 and 1 + 2(n-1)/3; a district exactly on a
        * cut-point goes to the group above (as pandas' qcut does)
        sort `z' dist
        gen rank = _n
        gen third = 1 + (rank >= 1 + (_N - 1) / 3) + (rank >= 1 + 2 * (_N - 1) / 3)
        collapse (sum) fsc24 fsc25 fsc26 pop, by(third)
        foreach y in 24 25 26 {
            gen reach`y' = 100 * fsc`y' / pop
        }
        display as text _n "Food & cash reached per 100 residents, by thirds of `z'"
        list third reach24 reach25 reach26, noobs
        local yn24 Tf
        local yn25 Tv
        local yn26 Ts
        foreach y in 24 25 26 {
            res ftwo`zt'Lo`yn`y'' reach`y'[1]
            res ftwo`zt'Hi`yn`y'' reach`y'[3]
        }
    restore
}

res_save results_02
log close
