* 10_benefit_cost.do
* What is FEWS NET worth in lives?  The benefit-cost arithmetic of code/36_benefit_cost.py
* (paper Section 8 and Appendix H, Table 4 "benefit.tex"; macros bc*, d*, whole*, ipc*, cal*).
*
* Chain:  in every area-round FEWS NET flags "!" (aid holds the area one phase better),
*   deaths averted   = population x months x 30.4 x (CDR[phase+1] - CDR[phase]) / 10,000
*   wasting averted  = population x 0.17 (under fives) x months/12 x (GAM[phase+1] - GAM[phase])
*   people kept out of Crisis+ / Emergency+ = person-years x (s3[phase+1] - s3[phase]), with s3, s4 the
*                      shares of people in Phase 3+ / 4+ by area phase in the official IPC/CH data
* FEWS NET's share of the aid in the country-round, x = its mean contribution (or whole forecast):
*   A = 1 - exp(-b x) if x >= 0,  -(1 - exp(b x)) if x < 0          (symmetric)
* Totals are per year (14 years, 2011-2024); cost per outcome = FEWS NET budget / outcome.
* Two calibrations of what a phase means: "evidence" (main) and "ipcbands" (IPC reference table).

do _setup.do
cap log close
log using "$OUT/10_benefit_cost.log", replace text

local YEARS 14
local U5 0.17

* r2 X: X rounded to two significant figures (as the paper prints costs and counts)
cap program drop r2
program r2, rclass
    args x
    return scalar v = round(`x', 10^(floor(log10(abs(`x'))) - 1))
end

* --- calibration constants: phase -> crude death rate (per 10,000/day) and GAM share --------------
import delimited using "$DATA/bc_calibration.csv", clear
forvalues i = 1/`=_N' {
    local c = calib[`i']
    local l = level[`i']
    local p = phase[`i']
    local cdr_`c'_`l'_`p' = cdr[`i']
    local gam_`c'_`l'_`p' = gam[`i']
}
foreach l in Lo Mid Hi {
    local lv = cond("`l'" == "Lo", "low", cond("`l'" == "Mid", "central", "high"))
    res calCdr`l' `cdr_evidence_`lv'_2' - `cdr_evidence_`lv'_1'
    res calFam`l' `cdr_evidence_`lv'_5' - `cdr_evidence_`lv'_4'
    res calGam`l' 100 * (`gam_evidence_`lv'_2' - `gam_evidence_`lv'_1')
}

* --- shares of people in Phase 3+ / 4+ by area phase (official IPC / CH) ---------------------------
import delimited using "$DATA/bc_outcomes.csv", clear
keep if inrange(phase, 1, 5)
forvalues p = 1/5 {
    summarize share3 if phase == `p', meanonly
    local s3_`p' = r(mean)
    summarize share4 if phase == `p', meanonly
    local s4_`p' = r(mean)
}
local s3_5 = max(cond(missing(`s3_5'), 0.9, `s3_5'), 0.9)     // Famine: at least 90% / 60%
local s4_5 = max(cond(missing(`s4_5'), 0.6, `s4_5'), 0.6)
res bcSthreeStressed 100 * `s3_2'
res bcSthreeCrisis   100 * `s3_3'
res bcSthreeEmerg    100 * `s3_4'

* --- funding responses (log points per unit of contribution) -------------------------------------
import delimited using "$DATA/bc_betas.csv", clear
forvalues i = 1/`=_N' {
    local b_`=attribution[`i']' = beta[`i']
    local x_`=attribution[`i']' = x[`i']
}
res bcBetaOne   10 * `b_A1'         // percent more funding per 10 points
res bcBetaThree 10 * `b_A3'

* --- country-round mean contribution / forecast --------------------------------------------------
import delimited using "$DATA/bc_contrib.csv", clear
collapse (mean) c_fc3 ci_fc3 fc3, by(country_code r)
rename r month
tempfile cr
save `cr'

* --- flagged area-rounds -------------------------------------------------------------------------
import delimited using "$DATA/bc_flagged.csv", clear
res bcFlaggedRounds _N
merge m:1 country_code month using `cr', keep(master match) nogenerate
keep if !missing(pop, c_fc3)
display as text "Flagged area-rounds used: " as result _N
gen double person_days = pop * months * 30.4
gen p = floor(min(max(phase, 1), 4))
gen cf = p + 1
foreach s in s3 s4 {
    gen double `s'_p = .
    gen double `s'_cf = .
    forvalues k = 1/5 {
        replace `s'_p  = ``s'_`k'' if p == `k'
        replace `s'_cf = ``s'_`k'' if cf == `k'
    }
}
gen double crisis_py = person_days / 365 * (s3_cf - s3_p)
gen double emerg_py  = person_days / 365 * (s4_cf - s4_p)
gen double people = pop * months / 12
summarize people, meanonly
res bcPeople r(sum) / `YEARS' / 1e6
summarize crisis_py, meanonly
res bcGrossCrisis r(sum) / `YEARS' / 1e6
count if p == 2
res bcPhaseTwo 100 * r(N) / _N
count if p == 3
res bcPhaseThree 100 * r(N) / _N
tempfile have
save `have'

* --- both calibrations ---------------------------------------------------------------------------
* results: one row per calibration x attribution x mortality scenario
cap frame drop bc
frame create bc str9 calib str3 attr str7 mort double(share deaths crisis emerg wast)
foreach c in evidence ipcbands {
    use `have', clear
    foreach l in low central high {
        foreach v in cdr gam {
            gen double `v'_p = .
            gen double `v'_cf = .
            forvalues k = 1/5 {
                replace `v'_p  = ``v'_`c'_`l'_`k'' if p == `k'
                replace `v'_cf = ``v'_`c'_`l'_`k'' if cf == `k'
            }
        }
        gen double deaths_`l'  = person_days * (cdr_cf - cdr_p) / 1e4
        gen double wasting_`l' = pop * `U5' * months / 12 * (gam_cf - gam_p)
        drop cdr_* gam_*
        summarize deaths_`l', meanonly
        local gross_`l' = r(sum) / `YEARS'
    }
    local K = cond("`c'" == "evidence", "bc", "ipc")
    res `K'GrossCons `gross_low' / 1e3
    res `K'GrossMid  `gross_central' / 1e3
    res `K'GrossUp   `gross_high' / 1e3
    summarize deaths_central, meanonly
    local dc = r(sum)
    foreach a in A1 A2 A3 A4 A5 {
        * share of the aid attributable to FEWS NET (missing where x is missing, as in Python)
        gen double bx = `b_`a'' * `x_`a''
        gen double A = cond(bx >= 0, 1 - exp(-bx), -(1 - exp(bx))) if !missing(bx)
        foreach v in deaths_low deaths_central deaths_high wasting_low wasting_central wasting_high crisis_py emerg_py {
            gen double t = A * `v'
            summarize t, meanonly
            local s_`v' = r(sum)
            drop t
        }
        foreach l in low central high {
            frame post bc ("`c'") ("`a'") ("`l'") (`s_deaths_central' / `dc') (`s_deaths_`l'' / `YEARS') ///
                (`s_crisis_py' / `YEARS') (`s_emerg_py' / `YEARS') (`s_wasting_`l'' / `YEARS')
        }
        drop bx A
    }
}

* --- headline numbers ----------------------------------------------------------------------------
frame change bc
gen double cost = 45e6 / deaths if deaths > 0                  // central budget, $45 million a year
gen distinct = inlist(attr, "A1", "A2", "A3")
format share %6.4f
format deaths crisis emerg wast cost %12.0fc
list if calib == "evidence", noobs sepby(attr) abbreviate(10)

* mm LO HI EXPR IF: records min and max of EXPR over the rows IF, to two significant figures
*   ("." in place of a name skips it)
cap program drop mm
program mm
    args lo hi expr cond
    tempvar v
    gen double `v' = `expr' if `cond'
    summarize `v', meanonly
    local mn = r(min)
    local mx = r(max)
    r2 `mn'
    local a = r(v)
    r2 `mx'
    local b = r(v)
    if "`lo'" != "." res `lo' `a'
    if "`hi'" != "." res `hi' `b'
    drop `v'
end

local E `"calib == "evidence""'
local C `"calib == "evidence" & mort == "central""'
local I `"calib == "ipcbands""'
foreach a in One Two Three {
    local n = cond("`a'" == "One", "A1", cond("`a'" == "Two", "A2", "A3"))
    summarize share if `C' & attr == "`n'", meanonly
    res bcShare`a' 100 * r(mean)
}
summarize share if `C' & distinct, meanonly
res dShareLo 100 * r(min)
res dShareHi 100 * r(max)
mm bcDistinctLo bcDistinctHi   cost        `"`E' & distinct"'
mm dDeathsLo dDeathsHi         deaths      `"`E' & distinct"'
mm dEmergLo dEmergHi           emerg       `"`C' & distinct"'
mm dCostEmergLo dCostEmergHi   45e6/emerg  `"`C' & distinct"'
mm dCrisisLo dCrisisHi         crisis      `"`C' & distinct"'
mm dCostCrisisLo dCostCrisisHi 45e6/crisis `"`C' & distinct"'
mm dWastLo dWastHi             wast        `"`C' & distinct"'
mm dCostWastLo dCostWastHi     45e6/wast   `"`C' & distinct"'
mm wholeLo wholeHi             cost        `"`E' & !distinct"'
* across the budget range ($35-65 million): cheapest = low budget / most deaths, dearest = high / fewest
gen double cost_lo = 35e6 / deaths if deaths > 0
gen double cost_hi = 65e6 / deaths if deaths > 0
mm dCostBudgetLo . cost_lo `"`E' & distinct"'
mm . dCostBudgetHi cost_hi `"`E' & distinct"'
* IPC reference bands instead
mm ipcDistinctLo ipcDistinctHi cost   `"`I' & distinct"'
mm ipcDeathsLo ipcDeathsHi     deaths `"`I' & distinct"'
res bcBudget 45
res bcBudgetLow 35
res bcBudgetHigh 65

* --- Table 4 (benefit.tex): central budget, A1-A3 --------------------------------------------------
* (min = max for a single cell; mm records it rounded to two significant figures)
gen double costemerg = 45e6 / emerg
foreach a in A1 A2 A3 {
    summarize share if `C' & attr == "`a'", meanonly
    res tab_benefit_`a'_share 100 * r(mean)
    foreach l in low central high {
        mm tab_benefit_`a'_deaths_`l' . deaths       `"`E' & attr == "`a'" & mort == "`l'""'
        mm tab_benefit_`a'_costdeath_`l' . cost      `"`E' & attr == "`a'" & mort == "`l'""'
    }
    mm tab_benefit_`a'_emerg . emerg                 `"`C' & attr == "`a'""'
    mm tab_benefit_`a'_costemerg . costemerg         `"`C' & attr == "`a'""'
    mm tab_benefit_`a'_wast_lo tab_benefit_`a'_wast_hi         wast      `"`E' & attr == "`a'""'
    mm tab_benefit_`a'_costwast_lo tab_benefit_`a'_costwast_hi 45e6/wast `"`E' & attr == "`a'""'
}
frame change default

res_save results_10
log close
