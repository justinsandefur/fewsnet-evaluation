* 07_survey_value.do
* If treatment followed surveys: the value of Somalia's scheduled survey rounds (paper section 9,
* Figure 10; code/65_survey_voi.py, 59_survey_value.py).
* Each season a planner has B treatment places for acutely malnourished children in the surveyed rural
* zones and places them where it predicts the most deaths averted. Cases = population x 17% under five x
* prevalence x incidence 2.6; at most 80% reachable. Deaths averted per treated child: severe 0.10 x 0.70,
* moderate 0.04 x 0.40. Predictions, each season left out: national mean (population), mean by FEWS NET's
* forecast phase (forecast), regression on the zone's previous survey (survey), the truth (oracle).
* Places sent beyond a cell's true cases are stranded; 0, 50 or 100% of them can be moved afterwards.

do _setup.do
cap log close
log using "$OUT/07_survey_value.log", replace text

import delimited using "$DATA/voi_panel.csv", clear varnames(1) case(preserve)
egen fold = group(t)
bankround ph2 = fc                                // forecast phase, rounded half to even, clipped to 2-4
replace ph2 = min(max(ph2, 2), 4)
assert ph2 == ph
qui summarize fold
local S = r(max)
gen double sg = sam / gam
qui summarize sg
res voiSamShare 100 * r(mean)
res voiSeasons `S'
qui count
local zones = r(N) / `S'
res voiZones `zones'
res svvRound `zones' * 20000                      // one survey round: zones x $20,000

* out-of-season predictions
foreach c in sam mam {
    foreach i in population forecast survey {
        gen double `c'_`i' = .
    }
    forvalues s = 1/`S' {
        qui summarize `c' if fold != `s'
        local mu = r(mean)
        qui replace `c'_population = `mu' if fold == `s'
        foreach p in 2 3 4 {
            qui summarize `c' if fold != `s' & ph == `p'
            qui replace `c'_forecast = cond(r(N) > 0, r(mean), `mu') if fold == `s' & ph == `p'
        }
        qui regress `c' `c'_lag if fold != `s'
        qui replace `c'_survey = max(0, _b[_cons] + _b[`c'_lag] * `c'_lag) if fold == `s'
    }
    gen double `c'_oracle = `c'
    gen double `c'_cases = pop * 0.17 * `c' / 100 * 2.6
    foreach i in population forecast survey oracle {
        gen double p_`c'_`i' = pop * 0.17 * `c'_`i' / 100 * 2.6        // predicted cases
    }
}
gen double cases = sam_cases + mam_cases
bysort fold: egen double season_cases = total(cases)
egen byte tf = tag(fold)
qui summarize season_cases if tf
local meancases = r(mean)

cap mata: mata drop allocate()
mata:
// deaths averted in one season for given predicted and true caseloads, budget and redeployment share
real scalar allocate(real colvector psam, real colvector pmam, real colvector tsam, real colvector tmam,
                     real scalar B, real scalar rd)
{
    real matrix X, U
    real scalar left, deaths, stranded, a, t, spare, m, i, n
    n = rows(psam)
    X = (J(n,1,0.07), psam :* 0.8, tsam :* 0.8, (1::n)) \ (J(n,1,0.016), pmam :* 0.8, tmam :* 0.8, (n+1::2*n))
    X = sort(X, (-1, -2, 4))                        // by value, then predicted size (both descending)
    left = B; deaths = 0; stranded = 0
    U = J(rows(X), 2, .)
    for (i = 1; i <= rows(X); i++) {
        a = min((X[i,2], left)); left = left - a
        t = min((a, X[i,3]))
        deaths = deaths + t * X[i,1]
        stranded = stranded + a - t
        U[i,.] = (X[i,1], X[i,3] - t)
    }
    spare = rd * stranded + rd * max((left, 0))
    for (i = 1; i <= rows(U); i++) {               // unmet cases, already in descending order of value
        if (spare <= 0) break
        m = min((U[i,2], spare)); spare = spare - m
        deaths = deaths + m * U[i,1]
    }
    return(deaths)
}
end

* deaths averted per season by information set, budget share and redeployment (fixed budgets)
tempname R
mata: st_matrix("`R'", J(0, 4, .))
foreach cover in 0.2 0.3 0.38 0.5 {
    foreach rd in 0 0.5 1 {
        foreach info in population forecast survey oracle {
            local tot = 0
            forvalues s = 1/`S' {
                mata: f = st_data(., "fold") :== `s'
                mata: st_local("d", strofreal(allocate(select(st_data(., "p_sam_`info'"), f), ///
                    select(st_data(., "p_mam_`info'"), f), select(st_data(., "sam_cases"), f), ///
                    select(st_data(., "mam_cases"), f), `cover' * `meancases', `rd'), "%20.10f"))
                local tot = `tot' + `d'
            }
            local D_`=subinstr("`cover'", ".", "", .)'_`=subinstr("`rd'", ".", "", .)'_`info' = `tot' / `S'
        }
    }
}

* the paper's numbers: budget for 38% of the caseload; no redeployment (Zero) and all moved (Full)
foreach rd in 0 1 {
    local t = cond(`rd' == 0, "Zero", "Full")
    local gain = `D_038_`rd'_survey' - `D_038_`rd'_forecast'
    res voiGain`t' `gain'
    res voiCost`t' `zones' * 20000 / `gain'
    res voiOracle`t' 100 * `gain' / (`D_038_`rd'_oracle' - `D_038_`rd'_forecast')
}
res voiBase `D_038_0_forecast'
* range of cost per death over budgets of 20-50% and all redeployment assumptions
local lo = .
local hi = .
foreach cover in 02 03 038 05 {
    foreach rd in 0 05 1 {
        local gain = `D_`cover'_`rd'_survey' - `D_`cover'_`rd'_forecast'
        if `gain' > 0 {
            local cpd = `zones' * 20000 / `gain'
            local lo = min(`lo', `cpd')
            local hi = max(`hi', `cpd')
        }
    }
}
res voiRangeLo `lo'
res voiRangeHi `hi'

res_save results_07
log close
