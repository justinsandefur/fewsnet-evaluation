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

* FAO DIEM surveys on their own (code/92_diem_numbers.py): by FEWS NET phase (rounded half to even) and
* by the official IPC/CH phase (rounded half up)
import delimited using "$DATA/diem.csv", clear varnames(1) case(preserve)
foreach ind in fcs_poor_borderline rcsi_19plus hhs_3plus lcs_crisis_plus {
    local I = cond("`ind'" == "fcs_poor_borderline", "Fcs", cond("`ind'" == "rcsi_19plus", "Rcsi", ///
              cond("`ind'" == "hhs_3plus", "Hhs", "Lcs")))
    foreach col in fews_cs ipc_phase {
        local P = cond("`col'" == "fews_cs", "", "Ipc")
        preserve
            keep if indicator == "`ind'" & !missing(value, `col')
            if "`col'" == "fews_cs" bankround ph = `col'
            else gen double ph = floor(`col' + 0.5)
            replace ph = min(max(ph, 1), 4)
            foreach p in 1 4 {
                local tag = word("One Two Three Four", `p')
                qui summarize value if ph == `p'
                res dm`I'`P'`tag' r(mean)
            }
            res dm`I'`P'N _N
            qui corr value `col'
            res dm`I'`P'Corr r(rho)
            foreach g in iso3 area_id {
                bysort `g': egen mv = mean(value)
                bysort `g': egen mp = mean(`col')
                gen dv = value - mv
                gen dp = `col' - mp
                qui corr dv dp
                res dm`I'`P'Corr`=cond("`g'" == "iso3", "Cty", "Area")' r(rho)
                drop mv mp dv dp
            }
            gen over = value >= 20 if ph <= 2
            qui summarize over
            res dm`I'`P'LowOver 100 * r(mean)
        restore
    }
}
qui tab iso3
res dmCountries r(r)
qui tab area_id
res dmAreas r(r)
egen byte tr = tag(area_id month)
qui count if tr
res dmRounds r(N)
gen int yr = real(substr(month, 1, 4))
qui summarize yr
res dmYearZero r(min)
res dmYearOne r(max)

res_save results_02
log close
