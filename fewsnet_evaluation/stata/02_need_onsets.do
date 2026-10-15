* 02_need_onsets.do
* Reproduces the need-defined emergencies in Section 5 (Python: code/30_need_onsets.py, and the
* need* numbers in appendix() of code/40_paper.py): does early warning raise the chance that aid
* holds a new Emergency back?
*
* Taking FEWS NET's aid flag at face value, the phase without aid ("need") is the mapped phase,
* plus one where the area is flagged as held better by aid. A new Emergency by need: need reaches
* Phase 4+ when the area's previous map (within six months) showed need below 4. It was either
* realised (mapped Phase 4+) or averted (mapped Phase 3 with the flag).
* Each onset is classed by FEWS NET's forecasts for the area for the onset month or the three before:
*   early warning  a forecast issued 4-8 months before reached Emergency need
*   late warning   only forecasts issued 1-3 months before did
* Onsets with no forecast issued 4-8 months before are dropped.
*   averted = a early + b late + FE(country x map month) + e, clustered by country
*
* Needs output/err_cs.dta and output/err_proj.dta from 01_errors.do.

do _setup.do
cap log close
log using "$OUT/02_need_onsets.log", replace text

* onsets of Emergency need
use "$OUT/err_cs.dta", clear
gen need = min(phase + flag, 5)
by id: gen prev_need = need[_n-1]
keep if inrange(gap, 1, 6) & prev_need < 4 & need >= 4
gen averted = phase < 4
rename month t0
keep country_code id t0 averted prev_phase
tempfile on
save `on'

* forecasts for the onset month or the three months before, by lag (months between issue and onset);
* fneed = forecast phase, plus one if the forecast carries the flag
use id report_month month phase fneed using "$OUT/err_proj.dta", clear
expand 4
bysort id report_month month: gen t0 = month + _n - 1
gen k = t0 - report_month
keep if inrange(k, 1, 8)
gen early    = k >= 4 & fneed >= 4
gen late     = k <= 3 & fneed >= 4
gen early_fc = k >= 4
collapse (max) early late early_fc, by(id t0)
merge 1:1 id t0 using `on', keep(match) nogenerate
keep if early_fc
replace late = late * (1 - early)

res needOnsets _N
quietly summarize averted
res needHeld 100 * r(mean)
* averted onsets that were flag switches in areas already mapped in Crisis
gen steady = prev_phase == 3
quietly summarize steady if averted
res needHeldSteady 100 * r(mean)

* early vs no warning, within country x map month
gen cell = country_code + "_" + string(t0, "%tm")
reghdfe averted early late, absorb(cell) vce(cluster country_code)
res needEarly 100 * _b[early]
res needEarlySe 100 * _se[early]

res_save results_02
log close
