* 02_foodsec.do
* Phases against household food consumption and coping (paper section 4; code/66_foodsec_surveys.py,
* 40_paper.py fig_foodsec). WFP survey rounds and phone monitoring matched to FEWS NET's phase.
*   means by phase; correlations pooled, within country, within area; the IPC's 20 percent rule;
*   the Cadre Harmonise's own input indicators against the phase its analysts assigned.

do _setup.do
cap log close
log using "$OUT/02_foodsec.log", replace text

import delimited using "$DATA/foodsec.csv", clear varnames(1) case(preserve)
qui tab iso3
res fsFoodCountries r(r)
qui tab area_id
res fsFoodAreas r(r)

foreach ind in fcs_poor_borderline rcsi_19plus {
    local t = cond("`ind'" == "fcs_poor_borderline", "Fcs", "Rcsi")
    preserve
        keep if indicator == "`ind'" & !missing(value, phase)
        bankround ph = phase
        replace ph = min(max(ph, 1), 4)
        foreach p in 1 2 3 4 {
            local tag = word("One Two Three Four", `p')
            qui summarize value if ph == `p'
            res fs`t'`tag' r(mean)
        }
        qui corr value phase
        res fs`t'Corr r(rho)
        * within country and within area: correlate deviations from the group means
        foreach g in iso3 area_id {
            bysort `g': egen mv = mean(value)
            bysort `g': egen mp = mean(phase)
            gen dv = value - mv
            gen dp = phase - mp
            qui corr dv dp
            res fs`t'Corr`=cond("`g'" == "iso3", "Cty", "Area")' r(rho)
            drop mv mp dv dp
        }
        * IPC 20% rule: Phase 1-2 areas with 20%+ of households at Crisis level; Phase 3+ areas below 20%
        gen over = value >= 20 if ph <= 2
        gen under = value < 20 if ph >= 3
        qui summarize over
        res fs`t'LowOver 100 * r(mean)
        qui summarize under
        res fs`t'HighUnder 100 * r(mean)
    restore
}

* Cadre Harmonise input indicators against the CH phase the same analysts assigned
import delimited using "$DATA/ch_inputs.csv", clear varnames(1) case(preserve)
foreach ind in fcs_poor_borderline hhs_3plus rcsi_19plus lcs_crisis_plus {
    local t = cond("`ind'" == "fcs_poor_borderline", "Fcs", cond("`ind'" == "hhs_3plus", "Hhs", ///
              cond("`ind'" == "rcsi_19plus", "Rcsi", "Lcs")))
    qui corr value ipc_phase if indicator == "`ind'"
    res ch`t'Corr r(rho)
    if "`t'" == "Fcs" {
        res chN r(N)
        qui tab iso3 if indicator == "`ind'" & !missing(value, ipc_phase)
        res chCountries r(r)
    }
}

res_save results_02
log close
