* 01_somalia_build.do
* Builds the two Somalia analysis files:
*   output/som_districts.dta   one row per district (74; Banadir is one unit)
*   output/som_panel.dta       one row per survey domain x survey round (715 rows, 2015 - Gu 2026)
*
* The outcome data are FSNAU's SMART nutrition surveys, run twice a year after the Gu (Apr-Jun) and
* Deyr (Oct-Dec) rains. A "domain" is a surveyed population: a rural livelihood zone, or the IDP or
* urban population of a town. The US cut began with the stop-work order of 24 January 2025, so
* rounds from Gu 2025 onward are "post".
*
* Three exposures, all measured in 2024, before the cut:
*   us_share     (Python: E_pred)  US-funded share of 2024 aid partners
*   agency_loss  (Python: E_loss)  share of partners that disappeared, Apr-Oct 2025 vs Apr-Oct 2024
*   aid_dep      (Python: index)   aid dependence: how much aid per person the district got in 2024
* and measures of aid actually delivered, which tell us where the cut bit (02_somalia_first_stage.do).

do _setup.do
log using "$OUT/01_somalia_build.log", replace text


* ============================================================================
* 1. District exposures
* ============================================================================

* (a) US-funded share of partners.
*     The 2024 OCHA "3W" lists who works where. A unit is one organisation in one sector (nutrition,
*     health, food security, WASH) in one district. u is the US-funded share of that unit, read off
*     the donor named in the 3W: 1 for USAID/BHA/State, 0 for other donors, and for UN agencies
*     their 2023-24 US funding share in Somalia (WFP 69%, UNICEF 71%). Units with no usable donor
*     take their organisation's average, or else their organisation type's average (imputed = true).
*     The district's exposure is the average u across its units.
import delimited using "$DATA/som_units2024.csv", clear
tab imputed
collapse (mean) us_share = u (count) n_units = u, by(dist)
tempfile us
save `us'

import delimited using "$DATA/som_districts.csv", clear
merge 1:1 dist using `us', nogen keep(master match)
gen region = substr(dist, 1, 4)          // admin-1 region: the cluster for standard errors

* (b) Agency loss: 1 - (partners present Apr-Oct 2025) / (partners present Apr-Oct 2024),
*     counting organisation x sector pairs per month in the same four sectors.
gen agency_loss = 1 - cond(missing(partners25), 0, partners25) / partners24

* (c) Aid dependence index: the average of three standardised logs, each per resident in 2024 --
*     US$ of transfers (usd_pc), people reached per month (reach_pc), partners per 100,000 (partners_pc).
*     A small constant (half the smallest positive value) keeps districts with zero in the log.
foreach v in usd_pc reach_pc partners_pc {
    quietly summarize `v' if `v' > 0
    gen l_`v' = ln(`v' + r(min) / 2)
    egen z_`v' = std(l_`v')
}
gen aid_dep = (z_usd_pc + z_reach_pc + z_partners_pc) / 3
drop l_* z_*

* (d) Aid actually delivered (the "first stage" outcomes). Monthly averages for January-June of
*     each year: fsc = people reached with food or cash (Food Security Cluster dashboard),
*     otp = sites treating severe malnutrition (Nutrition Cluster). A district missing from a
*     dashboard reached nobody that year, so missing = 0.
foreach v of varlist fsc24 fsc25 fsc26 otp24 otp25 otp26 {
    gen has_`v' = !missing(`v')
    replace `v' = 0 if missing(`v')
}
foreach y in 25 26 {
    * people reached with food or cash, lost per 100 residents per month (positive = loss)
    gen fsc_loss`y' = (fsc24 - fsc`y') / pop * 100
    * proportional loss: minus the log change (+100 people so small districts don't dominate)
    gen fsc_plog`y' = -(ln(fsc`y' + 100) - ln(fsc24 + 100))
    * treatment sites lost per 10,000 children under five (under-fives = 19% of population)
    gen otp_loss`y' = (otp24 - otp`y') / (0.19 * pop) * 10000
}
* cash transfers (Cash Working Group 4W), Jan-Jun 2025 vs Jan-Jun 2024
gen cash_abs  = cash24 - cash25                                 // US$ lost per resident
gen cash_plog = -(ln(cash25 + 0.05) - ln(cash24 + 0.05))         // proportional loss
gen cash_reach_loss = cashreach24 - cashreach25                  // recipients lost per 100 per month

label var us_share    "US-funded share of 2024 partners"
label var agency_loss "Share of partners lost, 2025 vs 2024"
label var aid_dep     "Aid dependence index, 2024"
label var fsc_loss25  "Food/cash reached lost per 100 residents, Jan-Jun 2025 vs 2024"
label var fsc_loss26  "Food/cash reached lost per 100 residents, Jan-Jun 2026 vs 2024"
save "$OUT/som_districts.dta", replace

* Correlations between exposures across districts: the three measure different things.
pwcorr aid_dep us_share agency_loss, obs


* ============================================================================
* 2. Domain exposures: population-weighted average over the domain's districts
* ============================================================================
* Each survey domain covers one or more districts (weights w = the domain's population share in
* each district). Districts with a missing value are skipped and the weights re-normalised.
import delimited using "$DATA/som_domain_weights.csv", clear
merge m:1 dist using "$OUT/som_districts.dta", keep(master match) nogen ///
    keepusing(us_share agency_loss aid_dep fsc_loss25 cash_plog cash_reach_loss p3share24)
local dvars us_share agency_loss aid_dep fsc_loss25 cash_plog cash_reach_loss p3share24
foreach v of local dvars {
    gen wx_`v' = w * `v'
    gen w_`v'  = w * !missing(`v')
}
collapse (sum) wx_* w_*, by(domain)
foreach v of local dvars {
    gen `v' = wx_`v' / w_`v' if w_`v' > 0
}
keep domain `dvars'
tempfile dom
save `dom'


* ============================================================================
* 3. Survey panel
* ============================================================================
import delimited using "$DATA/som_panel.csv", clear
merge m:1 domain using `dom', keep(master match) nogen

* aid dependence is used standardised across domains (mean 0, s.d. 1)
egen first = tag(domain)
quietly summarize aid_dep if first
gen z_index = (aid_dep - r(mean)) / r(sd)
label var z_index "Aid dependence (s.d. across domains)"

* Fixed effects:
*   dom_id      survey domain (absorbs everything fixed about a place)
*   type_round  population type (rural / IDP / urban) x survey round (absorbs shocks common to,
*               say, all IDP camps in Deyr 2024)
egen dom_id     = group(domain)
egen type_round = group(ptype season_id)
egen round_id   = group(season_id)

* timing
gen gu25   = season_id == "Gu 2025"
gen deyr25 = season_id == "Deyr 2025"
gen gu26   = season_id == "Gu 2026"
gen rorder = year + 0.5 * (season_type == "Deyr")       // chronological order of rounds
tab season_id post

save "$OUT/som_panel.dta", replace

* Check: the domain exposures built here are the ones Python built.
import delimited using "$DATA/python_domain_exposures.csv", clear
rename (e_pred e_loss z_index) (py_us_share py_agency_loss py_z_index)
merge 1:m domain using "$OUT/som_panel.dta", nogen
foreach v in us_share agency_loss z_index {
    gen gap = abs(`v' - py_`v')
    quietly summarize gap
    display as text "`v': largest gap vs Python = " as result r(max)
    assert r(max) < 1e-6
    drop gap
}
use "$OUT/som_panel.dta", clear

* Correlation of exposures across domains (memo: ctCorr*)
preserve
    keep if first
    corr z_index us_share
    res ctCorrDepUs r(rho)
    corr z_index agency_loss
    res ctCorrDepLoss r(rho)
    corr us_share agency_loss
    res ctCorrUsLoss r(rho)
restore

res_save results_01
log close
