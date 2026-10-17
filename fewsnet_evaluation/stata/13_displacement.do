* 13_displacement.do
* Displacement as an outcome, Somalia 2016-2023 (paper Sections 3, 5 and 6; code/83_displacement.py).
* Departures by district of origin from UNHCR's Protection and Return Monitoring Network.
*   1. District x FEWS NET round: log(1 + departures over the next six months) on FEWS NET's map and
*      forecast (averaged over the district), or on the forecast split into the part public data
*      predict and FEWS NET's contribution, with log(1 + departures over the previous six months),
*      district and round FE, clustered by district. Effects in % per 10 percentage points.
*   2. Need-defined onsets: log(1 + departures from the area over the next 6 or 12 months) on early
*      and late warning (none = baseline), or on "averted" (held back by aid on FEWS NET's account),
*      with log(1 + departures over the previous six months) and map-round FE, clustered by region.
* The out-of-sample R-squared (gradient boosting) stays in Python.

do _setup.do
cap log close
log using "$OUT/13_displacement.log", replace text

* ---------------------------------------------------------------- data description
import delimited using "$DATA/disp_totals.csv", clear
res dispTotal        total[1] / 1e6
res dispDroughtShare 100 * drought_share[1]

import delimited using "$DATA/disp_rounds.csv", clear
encode pcode, gen(dist)
encode round, gen(rnd)
quietly levelsof pcode
res dispDistricts r(r)
quietly levelsof round
res dispRounds r(r)
res dispN _N
gen share_yr = dep_next6 * 2 / pop
quietly summarize share_yr, detail
res dispMedShare 100 * r(p50)

* ---------------------------------------------------------------- 1. forecasts and displacement
foreach c in dep dep_drought dep_conflict {
    gen ln_`c'_next6 = ln(1 + `c'_next6)
    gen ln_`c'_prev6 = ln(1 + `c'_prev6)
}
local Y_dep All
local Y_dep_drought Drought
local Y_dep_conflict Conflict
foreach c in dep dep_drought dep_conflict {
    local Y `Y_`c''
    * map and forecast together
    reghdfe ln_`c'_next6 cur3 fc3 ln_`c'_prev6, absorb(dist rnd) vce(cluster dist)
    pyse
    foreach x in cur3 fc3 {
        local nm = cond("`x'" == "cur3", "Cur", "Fc")
        res disp`Y'`nm'       100 * (exp(0.1 * _b[`x']) - 1)
        res disp`Y'`nm'Ci_lo  100 * (exp(0.1 * (_b[`x'] - 1.96 * _se[`x'])) - 1)
        res disp`Y'`nm'Ci_hi  100 * (exp(0.1 * (_b[`x'] + 1.96 * _se[`x'])) - 1)
    }
    * the forecast split: public-data part and FEWS NET's contribution (raw data; then + IPC)
    foreach pre in "" i {
        reghdfe ln_`c'_next6 b`pre'_fc3 c`pre'_fc3 ln_`c'_prev6, absorb(dist rnd) vce(cluster dist)
        pyse
        local list = cond("`pre'" == "", "b c", "c")
        foreach t of local list {
            local nm = cond("`t'" == "b", "Base", cond("`pre'" == "", "Contrib", "ContribIpc"))
            local x `t'`pre'_fc3
            res disp`Y'`nm'       100 * (exp(0.1 * _b[`x']) - 1)
            res disp`Y'`nm'Ci_lo  100 * (exp(0.1 * (_b[`x'] - 1.96 * _se[`x'])) - 1)
            res disp`Y'`nm'Ci_hi  100 * (exp(0.1 * (_b[`x'] + 1.96 * _se[`x'])) - 1)
        }
    }
}

* ---------------------------------------------------------------- 2. does warning keep people home?
import delimited using "$DATA/disp_onsets.csv", clear
encode mcell, gen(mc)
encode region, gen(reg)
foreach w in pre6 post6 post12 {
    gen ln_dep_`w' = ln(1 + dep_`w')
}
foreach lvl in Emergency Crisis {
    local L = cond("`lvl'" == "Emergency", "Em", "Cr")
    quietly count if onset == "`lvl'"
    res dispOn`L' r(N)
    quietly count if onset == "`lvl'" & early == 1
    res dispOn`L'Early r(N)
    quietly count if onset == "`lvl'" & averted == 1
    res dispOn`L'Averted r(N)
    foreach w in post6 post12 {
        local W = cond("`w'" == "post6", "Six", "Twelve")
        reghdfe ln_dep_`w' early late ln_dep_pre6 if onset == "`lvl'", absorb(mc) vce(cluster reg)
        pyse
        res dispOn`L'Early`W'    100 * (exp(_b[early]) - 1)
        res dispOn`L'Early`W'Se  _se[early]
        reghdfe ln_dep_`w' averted ln_dep_pre6 if onset == "`lvl'", absorb(mc) vce(cluster reg)
        pyse
        res dispOn`L'Averted`W'   100 * (exp(_b[averted]) - 1)
        res dispOn`L'Averted`W'Se _se[averted]
    }
}

res_save results_13
log close
