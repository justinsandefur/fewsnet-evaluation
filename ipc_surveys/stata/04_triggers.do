* 04_triggers.do
* Do drought, conflict and prices predict malnutrition and death better than the phases?
* (paper section 8, Figure 8; code/84_triggers_vs_phases.py). Somalia survey domains x seasons, 2015-2026;
* Nigeria's nutrition surveillance rounds, 2023-2026.
*   1. Out-of-sample R-squared, leaving one season out, for each information set (equation 2)
*   2. Leaving one domain out: a place never surveyed, scored against the season mean
*   3. Within domains: outcomes on standardized triggers and the IPC share (equation 3), and the IPC
*      share on the triggers

do _setup.do
cap log close
log using "$OUT/04_triggers.log", replace text

import delimited using "$DATA/triggers_som.csv", clear varnames(1) case(preserve)
encode ptype, gen(pt)
egen dom = group(domain)
egen sid = group(season_id)
qui summarize year
res trYearZero r(min)
res trYearOne r(max)

local trig rain_z rain12_z log_fat lp_cereal lp_goat
local phases need_p3 fews_cs fews_fc
local base i.pt deyr

* ------------------------------------------------------------ 1. leave one season out
foreach y in gam sam cdr u5dr {
    local Y = cond("`y'" == "gam", "Gam", cond("`y'" == "sam", "Sam", cond("`y'" == "cdr", "Cdr", "Ufive")))
    local last L_`y' L_morbidity L_measles
    gen byte s_`y' = !missing(`y', need_p3, fews_cs, fews_fc, L_`y', L_morbidity, L_measles, ///
                               rain_z, rain12_z, log_fat, lp_cereal, lp_goat)   // same rows for every set
    loso `y' `base' if s_`y', fold(season_rank)
    res tr`Y'Base r(r2)
    if "`y'" == "gam" {
        res trN r(N)
        qui tab season_rank if s_`y'
        res trSeasons r(r)
    }
    loso `y' `base' `phases' if s_`y', fold(season_rank)
    res tr`Y'Phase r(r2)
    loso `y' `base' `trig' if s_`y', fold(season_rank)
    res tr`Y'Trig r(r2)
    loso `y' `base' `phases' `trig' if s_`y', fold(season_rank)
    res tr`Y'PhaseTrig r(r2)
    loso `y' `base' `last' if s_`y', fold(season_rank)
    res tr`Y'Last r(r2)
    loso `y' `base' `last' `trig' if s_`y', fold(season_rank)
    res tr`Y'LastTrig r(r2)
    loso `y' `base' log_fat if s_`y', fold(season_rank)
    res trSingleConf`Y' r(r2)
}

* ------------------------------------------------------------ 2. leave one domain out
* Train on all other domains (with season effects); predict the domain left out in seasons the others
* cover; R-squared relative to the season's mean outcome.
cap program drop lodo
program lodo, rclass
    syntax varlist(fv) [if]
    gettoken y xs : varlist
    marksample touse, novarlist
    tempvar pred p intr sm e2 d2
    qui gen double `pred' = .
    qui levelsof dom if `touse', local(doms)
    foreach g of local doms {
        qui regress `y' `xs' i.sid if `touse' & dom != `g'
        qui bysort sid: egen byte `intr' = max(`touse' & dom != `g')
        qui predict double `p' if `touse' & dom == `g' & `intr', xb
        qui replace `pred' = `p' if `touse' & dom == `g' & `intr'
        drop `p' `intr'
    }
    qui bysort sid: egen double `sm' = mean(cond(!missing(`pred'), `y', .))
    qui gen double `e2' = (`y' - `pred')^2 if !missing(`pred')
    qui gen double `d2' = (`y' - `sm')^2 if !missing(`pred')
    qui summarize `e2'
    local ssr = r(sum)
    qui summarize `d2'
    return scalar r2 = 1 - `ssr' / r(sum)
end
foreach y in gam sam cdr u5dr {
    local Y = cond("`y'" == "gam", "Gam", cond("`y'" == "sam", "Sam", cond("`y'" == "cdr", "Cdr", "Ufive")))
    gen byte l_`y' = !missing(`y', need_p3, fews_cs, fews_fc, rain_z, rain12_z, log_fat, lp_cereal, lp_goat)
    lodo `y' `base' if l_`y'
    res ld`Y'Base r(r2)
    lodo `y' `base' `phases' if l_`y'
    res ld`Y'Phase r(r2)
    lodo `y' `base' `trig' if l_`y'
    res ld`Y'Trig r(r2)
    lodo `y' `base' log_fat if l_`y'
    res ld`Y'Conf r(r2)
    lodo `y' `base' `phases' `trig' if l_`y'
    res ld`Y'PhaseTrig r(r2)
}

* ------------------------------------------------------------ 3. within domains (domain effects, season type, trend)
gen trend = year - 2020
foreach v in `trig' need_p3 {
    zstd z_`v' = `v'
}
foreach y in gam sam cdr u5dr morbidity {
    local Y = cond("`y'" == "gam", "Gam", cond("`y'" == "sam", "Sam", cond("`y'" == "cdr", "Cdr", ///
              cond("`y'" == "u5dr", "Ufive", "Morb"))))
    regress `y' z_rain_z z_rain12_z z_log_fat z_lp_cereal z_lp_goat z_need_p3 i.dom deyr trend, vce(cluster dom)
    foreach v in rain_z rain12_z log_fat lp_cereal need_p3 {
        local V = cond("`v'" == "rain_z", "Rain", cond("`v'" == "rain12_z", "Rainyr", cond("`v'" == "log_fat", "Fat", ///
                  cond("`v'" == "lp_cereal", "Cereal", "Pthree"))))
        res tw`Y'`V' _b[z_`v']
        res tw`Y'`V'Se _se[z_`v']
    }
    res tw`Y'Dry -_b[z_rain12_z]                 // a 12-month rainfall deficit of one s.d.
    res tw`Y'DrySe _se[z_rain12_z]
}
* does the IPC share respond to the triggers? (percentage points per s.d.)
regress need_p3 z_rain_z z_rain12_z z_log_fat z_lp_cereal z_lp_goat i.dom deyr trend, vce(cluster dom)
foreach v in rain_z rain12_z log_fat lp_cereal {
    local V = cond("`v'" == "rain_z", "Rain", cond("`v'" == "rain12_z", "Rainyr", cond("`v'" == "log_fat", "Fat", "Cereal")))
    res tp`V' 100 * _b[z_`v']
    res tp`V'Se 100 * _se[z_`v']
}
res tpDry -100 * _b[z_rain12_z]

* ------------------------------------------------------------ Nigeria, NFSS rounds (no population-type or season terms)
import delimited using "$DATA/triggers_nga.csv", clear varnames(1) case(preserve)
egen fold = group(round_id)
gen lp_cereal = cond(missing(dp12), 0, dp12)
foreach v in fews_cs fews_fc {                                 // FEWS NET missing in 2025: round mean, then overall
    bysort round_id: egen m_`v' = mean(`v')
    qui summarize `v'
    replace `v' = cond(!missing(m_`v'), m_`v', r(mean)) if missing(`v')
}
local trig rain_z rain12_z log_fat lp_cereal
foreach y in gam sam cdr u5dr {
    local Y = cond("`y'" == "gam", "Gam", cond("`y'" == "sam", "Sam", cond("`y'" == "cdr", "Cdr", "Ufive")))
    loso `y', fold(fold)
    res ng`Y'Base r(r2)
    if "`y'" == "gam" res ngN r(N)
    loso `y' need_p3 fews_cs fews_fc, fold(fold)
    res ng`Y'Phase r(r2)
    loso `y' `trig', fold(fold)
    res ng`Y'Trig r(r2)
    loso `y' need_p3 fews_cs fews_fc `trig', fold(fold)
    res ng`Y'PhaseTrig r(r2)
    cap confirm variable L_`y'
    if !_rc {
        loso `y' L_`y' if !missing(L_`y'), fold(fold)
        res ng`Y'Last r(r2)
        if "`y'" == "gam" res ngNlast r(N)
        loso `y' L_`y' `trig' if !missing(L_`y'), fold(fold)
        res ng`Y'LastTrig r(r2)
    }
}
qui tab fold
res ngRounds r(r)

res_save results_04
log close
