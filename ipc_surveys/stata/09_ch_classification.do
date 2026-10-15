* 09_ch_classification.do
* What it takes to be classified in Crisis: the Cadre Harmonise's own chain of evidence, 2021-2023
* (paper section 6, Table 1; code/93_ch_classification.py).
*   1. indicator shares -> analysts' indicator phase: agreement with the IPC 20 percent rule
*   2. indicator phases -> food consumption dimension: the least / most severe indicator
*   3. dimension phases -> area phase: Phase 3+ by food consumption x livelihoods (saturated), and what
*      nutrition and mortality phases add (cell effects, clustered by country)

do _setup.do
cap log close
log using "$OUT/09_ch_classification.log", replace text

import delimited using "$DATA/ch_class.csv", clear varnames(1) case(preserve)

* 20 percent rule: highest phase p such that the share of households in phase p or worse is >= 20%
* (shares rescaled to sum to one; rows not summing to ~1 or ~100 are dropped)
cap program drop rule20
program rule20
    args out vars
    local k : word count `vars'
    tempvar tot
    egen double `tot' = rowtotal(`vars'), missing
    gen double `out' = .
    local ok "(inrange(`tot', 0.95, 1.05) | inrange(`tot', 95, 105))"
    forvalues j = 1/`k' {                                // phase j: cumulative share from j to k
        tempvar c`j'
        gen double `c`j'' = 0
        forvalues i = `j'/`k' {
            local v : word `i' of `vars'
            replace `c`j'' = `c`j'' + cond(missing(`v'), 0, `v') / `tot'
        }
        replace `out' = `j' if `ok' & `c`j'' >= 0.2
    }
    replace `out' = 1 if `ok' & missing(`out')
    foreach v of local vars {                            // all categories must be reported
        replace `out' = . if missing(`v')
    }
end
rule20 r_hdds "HDDS_Phase1 HDDS_Phase2 HDDS_Phase3 HDDS_Phase4 HDDS_Phase5"
rule20 r_hhs "HHS_Phase1 HHS_Phase2 HHS_Phase3 HHS_Phase4 HHS_Phase5"
rule20 r_rcsi "rCSI_Phase1 rCSI_Phase2 rCSI_Phase3"
rule20 r_lcs "LhHCSCat_NoStrategies LhHCSCat_StressStrategies LhHCSCat_CrisisStategies LhHCSCat_EmergencyStrategies"
foreach pair in "hdds HDDS Hdds" "hhs HHS Hhs" "rcsi rCSI Rcsi" "lcs LhHCSCat Lcs" {
    local a : word 1 of `pair'
    local b : word 2 of `pair'
    local t : word 3 of `pair'
    gen byte same = r_`a' == `b'_finalphase if !missing(r_`a', `b'_finalphase)
    qui summarize same
    res cxRule`t' 100 * r(mean)
    res cxRule`t'N r(N)
    drop same
}
* food consumption groups: median share poor or borderline by the analysts' phase for the indicator
egen double fcgtot = rowtotal(FCG_Poor FCG_Borderline FCG_Acceptable), missing
gen double pb = (FCG_Poor + FCG_Borderline) / fcgtot if inrange(fcgtot, 0.95, 1.05) | inrange(fcgtot, 95, 105)
foreach p in 1 2 3 4 {
    local t = word("One Two Three Four", `p')
    qui summarize pb if FCG_finalphase == `p', detail
    res cxFcgMed`t' 100 * r(p50)
}

* 2. the food consumption dimension against its indicators' phases
egen nind = rownonmiss(FCG_finalphase HDDS_finalphase HHS_finalphase rCSI_finalphase)
egen mn = rowmin(FCG_finalphase HDDS_finalphase HHS_finalphase rCSI_finalphase)
egen mx = rowmax(FCG_finalphase HDDS_finalphase HHS_finalphase rCSI_finalphase)
gen byte dimok = !missing(foodconsumption_phase) & nind >= 2
qui count if dimok
res cxDimN r(N)
qui summarize foodconsumption_phase if dimok
gen byte eqmin = mn == foodconsumption_phase if dimok
gen byte eqmax = mx == foodconsumption_phase if dimok
qui summarize eqmin
res cxDimMin 100 * r(mean)
qui summarize eqmax
res cxDimMax 100 * r(mean)

* 3. area phase against dimension phases
keep if !missing(phase_class, foodconsumption_phase, livelihoods_phase)
res cxAreaN _N
qui tab adm0_pcod3
res cxCountries r(r)
gen p3 = phase_class >= 3
gen byte eqfood = phase_class == foodconsumption_phase
qui summarize eqfood
res cxAreaFood 100 * r(mean)
egen dmax = rowmax(foodconsumption_phase livelihoods_phase nutrition_phase mortality_phase)
gen byte above = phase_class > dmax
qui summarize above
res cxAreaAboveMax 100 * r(mean)
forvalues f = 1/4 {
    forvalues l = 1/4 {
        qui summarize p3 if foodconsumption_phase == `f' & livelihoods_phase == `l'
        if r(N) > 0 {
            local k = substr("ABCD", `f', 1) + substr("ABCD", `l', 1)
            res cxCell`k' 100 * r(mean)
            res cxCell`k'N r(N)
        }
    }
}
egen cell = group(foodconsumption_phase livelihoods_phase)
egen cid = group(adm0_pcod3)
gen nut_obs = !missing(nutrition_phase)
gen nut3 = nutrition_phase >= 3 & !missing(nutrition_phase)
gen mort_obs = !missing(mortality_phase)
gen mort3 = mortality_phase >= 3 & !missing(mortality_phase)
regress p3 i.cell
res cxRtwoCells 100 * e(r2)
regress p3 i.cell nut_obs nut3 mort_obs mort3, vce(cluster cid)
res cxRtwoAll 100 * e(r2)
res cxNut 100 * _b[nut3]
res cxNutSe 100 * _se[nut3]
res cxMort 100 * _b[mort3]
res cxMortSe 100 * _se[mort3]
qui count if nut_obs
res cxNutN r(N)
qui count if mort_obs
res cxMortN r(N)
qui summarize p3 if nut3 & foodconsumption_phase == 1
res cxNutFoodOneN r(N)
res cxNutFoodOneP 100 * r(mean)
qui summarize p3 if nut3 & foodconsumption_phase == 2
res cxNutFoodTwoP 100 * r(mean)

res_save results_09
log close
