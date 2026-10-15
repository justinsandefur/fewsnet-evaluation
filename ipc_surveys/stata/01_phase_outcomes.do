* 01_phase_outcomes.do
* Phases against measured malnutrition and death (paper sections 5-6; code/57_fsnau_value.py, 58_phase_outcomes.py).
*   A. Somalia's scheduled FSNAU surveys: means by forecast phase, correlations, out-of-sample
*      R-squared and AUC (leave one season out), within-zone slopes, does the forecast use the last survey.
*   B. SMART+ and national survey rounds: means by phase, slopes with country-by-year effects.
*   C. The IPC's two scales (food insecurity vs acute malnutrition) for the same areas.

do _setup.do
cap log close
log using "$OUT/01_phase_outcomes.log", replace text

* ============================================================== A. Somalia
import delimited using "$DATA/fsnau_count.csv", clear varnames(1)
res fsAll n_results[1]

import delimited using "$DATA/fsnau_panel.csv", clear varnames(1) case(preserve)
egen fold = group(t)                                       // survey season
egen zone = group(key)
res fsN _N
qui tab key
res fsZones r(r)
qui tab t
res fsSeasons r(r)
qui summarize gam
res fsGam r(mean)
qui summarize crit
res fsCrit 100 * r(mean)
qui summarize lead, detail
res fsLead r(p50)

* mean GAM by FEWS NET's forecast phase (rounded half to even, as in Python, and clipped to 2-4)
bankround fcr = fc
replace fcr = min(max(fcr, 2), 4)
foreach ph in 2 3 4 {
    local tag = word("x Two Three Four", `ph')
    qui summarize gam if fcr == `ph'
    res fsGam`tag' r(mean)
}

* correlations with the forecast, the map published after the survey, and the zone's previous survey
qui corr gam fc
res fsCorrFc r(rho)
qui corr gam gam_lag
res fsCorrLag r(rho)
qui corr gam after
res fsCorrAfter r(rho)

* out of sample, leave one season out: R-squared for GAM, AUC for critical GAM (15%+)
loso gam fc fc3 fc4 gu, fold(fold)
res fsRtwoFc r(r2)
loso gam gam_lag gu, fold(fold)
res fsRtwoLag r(r2)
loso gam fc fc3 fc4 gam_lag gu, fold(fold)
res fsRtwoBoth r(r2)
loso crit fc fc3 fc4 gu, fold(fold) auc
res fsAucFc r(auc)
loso crit gam_lag gu, fold(fold) auc
res fsAucLag r(auc)

* does FEWS NET's forecast respond to the last survey? (season effects, clustered by zone; per 10 points)
areg fc gam_lag cur, absorb(fold) vce(cluster zone)
res fsFcOnLag 10 * _b[gam_lag]
res fsFcOnLagSe 10 * _se[gam_lag]

* within zones: one phase worse than usual (forecast) -> outcomes; zone effects, then zone + season
foreach y in gam cdr u5dr {
    local Y = cond("`y'" == "gam", "Gam", cond("`y'" == "cdr", "Cdr", "Ufive"))
    reghdfe `y' fc, absorb(zone) vce(cluster zone)
    res wz`Y'Zone _b[fc]
    res wz`Y'ZoneSe _se[fc]
    reghdfe `y' fc, absorb(zone fold) vce(cluster zone)
    res wz`Y'ZoneSeason _b[fc]
    res wz`Y'ZoneSeasonSe _se[fc]
}

* under-five death rate: previous survey vs forecast (lag from all rural surveys, six months earlier)
preserve
    import delimited using "$DATA/fsnau_all.csv", clear varnames(1) case(preserve)
    gen double t_next = round(t + 0.5, 0.5)
    keep key t_next u5dr
    rename (t_next u5dr) (t u5_lag)
    duplicates drop key t, force
    tempfile lag
    save `lag'
restore
gen double t_r = round(t, 0.5)
drop t
rename t_r t
merge m:1 key t using `lag', keep(master match) nogen
keep if !missing(u5dr, u5_lag)
loso u5dr fc fc3 fc4 gu, fold(fold)
res fsMortFc r(r2)
loso u5dr u5_lag gu, fold(fold)
res fsMortLag r(r2)

* ============================================================== B. other surveys
import delimited using "$DATA/smartplus.csv", clear varnames(1) case(preserve)
gen byte smart = source == "SMART+"
gen byte rounds = smart & recurring == "True"
gen byte fdw = source == "FDW"
egen cyid = group(cy)
egen clid = group(cluster)
gen double bin = min(max(floor(cur + 0.5), 1), 5) if !missing(cur)   // phase bins: round the area mean phase
replace bin = 4 if bin == 5                                 // 4+ pools Emergency and Famine
qui count if smart
res spN r(N)
qui count if smart & !missing(cur)
res spNfews r(N)
foreach b in 1 2 3 4 {
    local tag = word("One Two Three Four", `b')
    qui summarize gam if smart & bin == `b'
    res spGam`tag' r(mean)
    qui summarize cdr if smart & bin == `b'
    res spCdr`tag' r(mean)
}
qui count if fdw
res fdwN r(N)
* slopes with country-by-year effects, clustered by survey area (singletons dropped, as in Python)
reghdfe gam cur if smart, absorb(cyid) vce(cluster clid)
res spSlope _b[cur]
res spSlopeSe _se[cur]
reghdfe cdr cur if smart, absorb(cyid) vce(cluster clid)
res spCdrSlope _b[cur]
res spCdrSlopeSe _se[cur]
reghdfe cdr ipc if smart, absorb(cyid) vce(cluster clid)
res spCdrSlopeIpc _b[ipc]
res spCdrSlopeIpcSe _se[ipc]
reghdfe gam ipc if rounds, absorb(cyid) vce(cluster clid)
res ngSlope _b[ipc]
res ngSlopeSe _se[ipc]
reghdfe gam cur if fdw, absorb(cyid) vce(cluster clid)
res fdwSlope _b[cur]
res fdwSlopeSe _se[cur]

* ============================================================== C. the IPC's two scales
import delimited using "$DATA/amn_areas.csv", clear varnames(1) case(preserve)
keep if !missing(afi, amn_any)
gen afi_bin = min(max(floor(afi + 0.5), 1), 4)
gen amn_bin = min(max(floor(amn_any + 0.5), 1), 4)
tab afi_bin amn_bin
res amnAnyN _N
qui count if afi_bin == amn_bin
res amnAnyDiag 100 * r(N) / _N

res_save results_01
log close
