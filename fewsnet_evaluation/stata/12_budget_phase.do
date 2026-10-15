* 12_budget_phase.do
* FEWS NET's budget, and what a phase means for measured outcomes.
*   1. Contract obligations from USAspending (paper Section 8; budget_and_cg() in 40_paper.py): ob*
*   2. Appendix G, "What does a phase mean?":
*      Somalia's scheduled FSNAU surveys (code/57_fsnau_value.py): correlations and within-zone slopes (fs*, wz*)
*      SMART+ and FDW nutrition surveys (code/58_phase_outcomes.py): slopes with country x year effects (sp*, ng*, fdw*)
*      IPC acute malnutrition vs acute food insecurity phase for the same areas (amnAnyDiag)
*      WFP food security indicators by FEWS NET phase (code/66_foodsec_surveys.py, _foodsec() in 40_paper.py)

do _setup.do
cap log close
log using "$OUT/12_budget_phase.log", replace text

* ============================================================================
* 1. Budget: obligations by fiscal year, summed over awards (US$ million)
* ============================================================================
import delimited using "$DATA/ob_obligations.csv", clear stringcols(1)
summarize usd if award == "7200AA19F00018", meanonly      // the Pillar 1 task order
res obPillarOne r(sum) / 1e6
collapse (sum) usd, by(fy)
tsset fy
tsfill, full                                              // years with no obligations count as 0
replace usd = 0 if missing(usd)
list, noobs clean
summarize usd if inrange(fy, 2017, 2024)
res obAvgLong r(mean) / 1e6
res obMin     r(min) / 1e6
summarize usd if inrange(fy, 2019, 2023), meanonly
res obAvgCore r(mean) / 1e6
summarize usd if fy == 2023, meanonly
res obPeak    r(mean) / 1e6

* ============================================================================
* 2a. Somalia, FSNAU zone x season (surveys with a forecast, a previous round and a map)
* ============================================================================
import delimited using "$DATA/ph_fsnau.csv", clear
res fsN _N
corr gam fc
res fsCorrFc r(rho)
corr gam gam_lag
res fsCorrLag r(rho)
* within zone: GAM / crude death rate on the forecast phase, zone (and season) effects, clustered by zone
egen zone = group(key)
egen season = group(t)
foreach y in gam cdr {
    local Y = proper("`y'")
    quietly reghdfe `y' fc, absorb(zone) vce(cluster zone)
    res wz`Y'Zone _b[fc]
    quietly reghdfe `y' fc, absorb(zone season) vce(cluster zone)
    res wz`Y'ZoneSeason _b[fc]
    display as text "`y' per phase, within zone: " as result %5.2f _b[fc]
}

* ============================================================================
* 2b. SMART+ and FDW surveys: outcome on phase with country x year effects, clustered
*     (Python drops country-years with one survey; reghdfe drops these singletons too)
* ============================================================================
import delimited using "$DATA/ph_surveys.csv", clear stringcols(_all)
destring gam cdr cur ipc, replace
egen cyid = group(cy)
egen clid = group(cluster)
local smart source == "SMART+"
quietly reghdfe gam cur if `smart', absorb(cyid) vce(cluster clid)
res spSlope _b[cur]
quietly reghdfe cdr cur if `smart', absorb(cyid) vce(cluster clid)
res spCdrSlope _b[cur]
quietly reghdfe cdr ipc if `smart', absorb(cyid) vce(cluster clid)
res spCdrSlopeIpc _b[ipc]
quietly reghdfe gam ipc if `smart' & recurring == "True", absorb(cyid) vce(cluster clid)
res ngSlope _b[ipc]                                      // Nigeria's recurring SMART rounds
quietly reghdfe gam cur if source == "FDW", absorb(cyid) vce(cluster clid)
res fdwSlope _b[cur]

* ============================================================================
* 2c. IPC acute malnutrition phase vs acute food insecurity phase, same areas
* ============================================================================
import delimited using "$DATA/ph_amn.csv", clear
keep if !missing(amn_any, afi)
gen afi_bin = min(max(floor(afi + 0.5), 1), 4)          // nearest phase; 4 and 5 pooled
gen amn_bin = min(max(floor(amn_any + 0.5), 1), 4)
tab afi_bin amn_bin
count if afi_bin == amn_bin
res amnAnyDiag 100 * r(N) / _N

* ============================================================================
* 2d. WFP food security indicators (independent of the IPC) by FEWS NET's phase
* ============================================================================
import delimited using "$DATA/ph_foodsec.csv", clear stringcols(2 5)
* WFP's compilation takes precedence over the mVAM files for the same area, month and indicator
gen key = area_id + "|" + month + "|" + indicator
bysort key: egen lit = max(source == "wfp_lit")
drop if source == "mvam_hdx" & lit
preserve
    * phone monitoring: average to area-years so repeated months do not dominate
    keep if source == "wfp_rt"
    drop if missing(area_id, iso3, year, indicator)
    collapse (mean) value fews_cs, by(area_id iso3 year indicator)
    tempfile rt
    save `rt'
restore
keep if inlist(source, "wfp_lit", "mvam_hdx")
append using `rt'
summarize value, meanonly
if r(max) <= 1.5 replace value = 100 * value
egen c1 = tag(iso3)
count if c1
res fsFoodCountries r(N)
* phase rounded to the nearest whole phase (half to even, as pandas does), 4 and 5 pooled
gen ph = round(fews_cs)
replace ph = 2 * round(fews_cs / 2) if abs(fews_cs - floor(fews_cs) - 0.5) < 1e-9
replace ph = min(max(ph, 1), 4)
keep if indicator == "fcs_poor_borderline" & !missing(value, fews_cs)
tabstat value, by(ph) statistics(mean n)
summarize value if ph == 1, meanonly
res fsFcsOne r(mean)
summarize value if ph == 3, meanonly
res fsFcsThree r(mean)

res_save results_12
log close
