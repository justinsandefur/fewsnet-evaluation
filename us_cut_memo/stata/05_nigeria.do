* 05_nigeria.do
* Nigeria: did nutrition worsen more in north-east zones whose aid partners relied on US money,
* or lost more partners?  (memo Section 5)
*
* Outcomes: UNICEF/NBS nutrition surveillance (NFSS), fielded every August-September on 10 fixed
* zones of Borno, Yobe and Adamawa, 2023-2026. Post = 2025 and 2026.
* Exposures (zone, weighted by children under five across the zone's LGAs):
*   us_share  US-funded share of 2024 partners (nutrition, health, food, WASH; OCHA 3W, Apr-Jun 2024;
*             organisations are US-funded if they held a USAID/State award in Nigeria in FY2023-25)
*   loss25    partner loss, Apr-Jun 2025 vs Apr-Jun 2024
* Model: zone FE + year FE + b * exposure (s.d.) x post. Only 10 clusters, so p-values are from
* the wild cluster bootstrap (Webb weights, null imposed).

do _setup.do
log using "$OUT/05_nigeria.log", replace text


* ============================================================================
* 1. First stage (LGA level): did partners leave more where they were US-funded?
* ============================================================================
import delimited using "$DATA/nga_lgas.csv", clear
regress loss25 us_share, vce(robust)
res ngFsF (_b[us_share] / _se[us_share])^2
display as text "First-stage F = " as result %4.1f (_b[us_share] / _se[us_share])^2 ///
    as text "  -> US-funded partners did not leave more than others"


* ============================================================================
* 2. Zone difference-in-differences
* ============================================================================
import delimited using "$DATA/nga_zones.csv", clear
keep if region == "NE"
egen zone_id = group(zone)

* average wasting in the north-east by year (memo text). Number names are mangled because the memo's
* macros cannot contain digits: 2023 = CACD, 2024 = CACE, 2025 = CACF, 2026 = CACG.
foreach y in 2023 2024 2025 2026 {
    quietly summarize gam if year == `y'
    local tag = subinstr(subinstr(subinstr(subinstr("`y'", "2", "C", .), "0", "A", .), "3", "D", .), "4", "E", .)
    local tag = subinstr(subinstr("`tag'", "5", "F", .), "6", "G", .)
    res ngNeGam`tag' r(mean)
    display as text "NE mean GAM `y': " as result %4.1f r(mean)
}

* standardise exposures across zones
foreach v in us_share loss25 {
    egen first = tag(zone)
    quietly summarize `v' if first
    gen z_`v' = (`v' - r(mean)) / r(sd)
    drop first
}

* Two samples: all four rounds (2023-2026), and 2025 as the only post year ("Tf" in the memo's names).
foreach z in z_us_share z_loss25 {
    local zt = cond("`z'" == "z_us_share", "Us", "Loss")
    gen x_post = `z' * post
    foreach y in gam sam muac_gam stunting underweight cdr u5dr {
        if "`y'" == "gam"         local yt Gam
        if "`y'" == "sam"         local yt Sam
        if "`y'" == "muac_gam"    local yt Muac
        if "`y'" == "stunting"    local yt Stunt
        if "`y'" == "underweight" local yt Uwt
        if "`y'" == "cdr"         local yt Cdr
        if "`y'" == "u5dr"        local yt Ufive
        foreach s in all 2025 {
            local st = cond("`s'" == "all", "", "Tf")
            quietly regress `y' x_post i.zone_id i.year if "`s'" == "all" | year != 2026, vce(cluster zone_id)
            local b = _b[x_post]
            local se = _se[x_post]
            quietly boottest x_post, cluster(zone_id) weight(webb) reps(9999) seed(20251013) nograph
            res ngB`zt'`yt'`st'  `b'
            res ngSe`zt'`yt'`st' `se'
            res ngP`zt'`yt'`st'  r(p)
            display as text %-12s "`z'" %-12s "`y'" %-6s "`s'" " b per s.d. = " as result %6.2f `b' ///
                as text "  se " as result %5.2f `se' as text "  wild p = " as result %4.2f r(p)
        }
    }
    drop x_post
}

res_save results_05
log close
