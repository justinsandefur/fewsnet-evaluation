* 08_survey_gaps.do
* Where household surveys do not go (paper section 10; side_survey_selection/code/03_analysis.py, 06_exclusions.py).
*   A. Does a DHS, MICS or LSMS start in a country-year? Country and year effects, clustered by country;
*      event study around conflict onsets.
*   B. What DHS and MICS reports say they left out, by conflict intensity.

do _setup.do
cap log close
log using "$OUT/08_survey_gaps.log", replace text

* ============================================================== A. survey timing
import delimited using "$DATA/gaps_full.csv", clear varnames(1) case(preserve)
qui summarize s_any
res gapBase 100 * r(mean)
qui summarize s_DHS
res gapBaseDhs 100 * r(mean)
qui tab iso3
res gapCountries r(r)
qui summarize year
res gapYearZero r(min)
res gapYearOne r(max)

import delimited using "$DATA/gaps_panel.csv", clear varnames(1) case(preserve)
egen cid = group(iso3)
* within country: a year of minor conflict / war / economic downturn (reported as a fall, in points)
foreach y in s_any s_DHS s_MICS {
    local Y = cond("`y'" == "s_any", "Any", cond("`y'" == "s_DHS", "Dhs", "Mics"))
    regress `y' ln_gdppc ln_pop minor war downturn i.cid i.year if in_s3, vce(cluster cid)
    foreach v in minor war downturn {
        local V = cond("`v'" == "minor", "Minor", cond("`v'" == "war", "War", "Down"))
        res gap`Y'`V' -100 * _b[`v']
        res gap`Y'`V'Se 100 * _se[`v']
    }
}
* event study: first conflict onset after three calm years; reference period 2-5 years before
egen byte has_onset = tag(iso3) if !missing(onset)
qui count if has_onset
res gapOnsets r(N)
gen k = year - onset
forvalues j = 0/6 {                                  // e0..e6 = years -1..5 relative to onset
    gen byte e`j' = (k == `j' - 1)
}
gen byte e_pre = (k < -5) & !missing(k)
gen byte e_post = (k > 5) & !missing(k)
regress s_any e0-e6 e_pre e_post ln_gdppc ln_pop i.cid i.year if in_ev, vce(cluster cid)
res gapOnsetDrop -100 * _b[e1]
res gapOnsetDropSe 100 * _se[e1]

* ============================================================== B. survey reports
import delimited using "$DATA/exclusions.csv", clear varnames(1) case(preserve)
keep if usable == "True"
res exReports _N
gen intensity = cond(bd3 / 3 <= 24, 1, cond(bd3 / 3 <= 999, 2, 3))    // none, minor, war
foreach i in 1 2 3 {
    local L = word("Calm Minor War", `i')
    qui summarize any_security_excl if intensity == `i'
    res ex`L' 100 * r(mean)
}
qui summarize ex_ante if intensity == 2
res exDesignConflict 100 * r(mean)
qui summarize camps_silent
res exCampsSilent 100 * r(mean)
qui count if camps_out == 1
res exCampsOut r(N)
qui count if camps_in == 1
res exCampsIn r(N)
qui count if displacement_question == "yes"
res exDisplQ r(N)

res_save results_08
log close
