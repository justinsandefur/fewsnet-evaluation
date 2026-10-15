* 06_ethiopia.do
* Ethiopia: did US-reliant zones lose more aid, and did food insecurity rise more there?
* (memo Section 5)
*
* Exposure (zone, 2024):
*   us_share  share of OCHA 4W activity rows with a US donor (USAID/BHA/State), all sectors
*   us_nut    the same, nutrition rows only
*   jeop24    share of the zone's food-assistance woredas served by JEOP, the USAID-funded
*             Catholic Relief Services consortium (the clearest single US channel)
* First stage: change in 4W activity rows, 2025 vs 2024 (log), by sector.
* Outcome: share of woredas in IPC Phase 3+ in FEWS NET's current-situation maps, by zone and round
* (Oct 2023 - Jun 2026; FEWS NET published nothing on Ethiopia Feb-May 2025). These classifications
* are sticky and partly reflect assistance itself; nutrition surveys are not available publicly on
* both sides of the cut.

do _setup.do
log using "$OUT/06_ethiopia.log", replace text


* ============================================================================
* 1. First stage: did activity fall more in US-reliant zones?
* ============================================================================
import delimited using "$DATA/eth_zones.csv", clear
foreach x in dlog_all dlog_food dlog_nutrition dlog_health dlog_partners {
    if "`x'" == "dlog_all"       local xt All
    if "`x'" == "dlog_food"      local xt Food
    if "`x'" == "dlog_nutrition" local xt Nut
    if "`x'" == "dlog_health"    local xt Hea
    if "`x'" == "dlog_partners"  local xt Part
    foreach z in us_share us_nut jeop24 {
        if "`z'" == "us_share" local zt Us
        if "`z'" == "us_nut"   local zt UsNut
        if "`z'" == "jeop24"   local zt Jeop
        quietly regress `x' `z', vce(cluster region)
        res etF`xt'`zt' (_b[`z'] / _se[`z'])^2
        display as text %-16s "`x'" %-10s "`z'" " b = " as result %6.2f _b[`z'] ///
            as text "  F = " as result %5.1f (_b[`z'] / _se[`z'])^2
    }
}
tempfile zones
save `zones'


* ============================================================================
* 2. National: share of woredas in Phase 3+, October 2024 vs October 2025
* ============================================================================
import delimited using "$DATA/eth_national.csv", clear
list month share3, noobs
summarize share3 if month == "2024-10", meanonly
res etNatOctTf r(mean)
summarize share3 if month == "2025-10", meanonly
res etNatOctTv r(mean)


* ============================================================================
* 3. Difference-in-differences: Phase 3+ share on exposure x post, zone and round FE
* ============================================================================
import delimited using "$DATA/eth_zone_rounds.csv", clear
merge m:1 zone using `zones', keep(match) nogen keepusing(us_share us_nut jeop24)
gen post = month >= "2025-01"
egen zone_id  = group(zone)
egen round_id = group(month)
egen first = tag(zone)
foreach z in us_share us_nut jeop24 {
    if "`z'" == "us_share" local zt Us
    if "`z'" == "us_nut"   local zt UsNut
    if "`z'" == "jeop24"   local zt Jeop
    quietly summarize `z' if first
    local sd = r(sd)
    gen x_post = `z' * post
    quietly regress share3 x_post i.zone_id i.round_id, vce(cluster region)
    res etDPthree`zt'   _b[x_post] * `sd'
    res etDsePthree`zt' _se[x_post] * `sd'
    display as text "Phase 3+ share on `z' (pp per s.d.): " as result %5.2f _b[x_post] * `sd' ///
        as text "  (se " as result %4.2f _se[x_post] * `sd' as text ")"
    drop x_post
}

res_save results_06
log close
