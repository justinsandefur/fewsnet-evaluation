* 03_somalia_wasting.do
* Did child wasting rise more where exposure was high?  (memo Section 3, Table 1, Figure 3,
* appendix table of all outcomes)
*
* Difference-in-differences with a continuous exposure, one row per survey domain x round:
*
*   y[d,r] = domain FE + (population type x round) FE + b * exposure[d] x after[r] + controls + e
*
*   y         GAM (% of children 6-59 months with weight-for-height z < -2 or oedema), SAM, ...
*   domain FE soaks up everything fixed about a place (e.g. IDP camps always have more wasting)
*   type x round FE soak up shocks common to all rural, all IDP or all urban domains in a round
*   controls  rain_z   rainfall over the 6 months before the survey (z-score vs 1991-2020)
*             rain12_z same over 12 months
*             log_fat  log(1 + conflict deaths in the domain's districts, 6 months; ACLED)
*   b         extra change in y after the cut per unit of exposure, reported per s.d.
*
* Standard errors are clustered by region (15 clusters in the panel). With so few clusters
* we also report p-values from a wild cluster bootstrap (Webb weights, null imposed, 1,999 draws).

do _setup.do
log using "$OUT/03_somalia_wasting.log", replace text
use "$OUT/som_panel.dta", clear

global FE   "i.dom_id i.type_round"
global CTRL "rain_z rain12_z log_fat"
global BOOT "cluster(region) weight(webb) reps(1999) seed(20251013) nograph"


* ============================================================================
* 1. Table 1: wasting by round after the cut, for each exposure
* ============================================================================
* One regression per exposure x outcome with three separate "after" terms: Gu 2025 (first survey
* after the cut, ~5 months), Deyr 2025 (~10 months) and Gu 2026 (~17 months).
foreach z in z_index us_share agency_loss {
    if "`z'" == "z_index"     local zt Dep
    if "`z'" == "us_share"    local zt Us
    if "`z'" == "agency_loss" local zt Loss
    gen x_gu25  = `z' * gu25
    gen x_deyr25 = `z' * deyr25
    gen x_gu26  = `z' * gu26
    foreach y in gam sam {
        local yt = cond("`y'" == "gam", "Gam", "Sam")
        display as text _n "{hline 70}" _n "`y' on `z' x round" _n "{hline 70}"
        regress `y' x_gu25 x_deyr25 x_gu26 $CTRL $FE, vce(cluster region)
        domain_sd `z'
        local sd = r(sd)
        foreach s in gu25 deyr25 gu26 {
            if "`s'" == "gu25"   local st GuTv
            if "`s'" == "deyr25" local st DyTv
            if "`s'" == "gu26"   local st GuTs
            res ct`zt'`yt'`st'   _b[x_`s'] * `sd'
            res ctSe`zt'`yt'`st' _se[x_`s'] * `sd'
        }
        * bootstrap p-values (the memo reports them for Gu 2026)
        foreach s in gu25 deyr25 gu26 {
            if "`s'" == "gu25"   local st GuTv
            if "`s'" == "deyr25" local st DyTv
            if "`s'" == "gu26"   local st GuTs
            quietly boottest x_`s', $BOOT
            res ctP`zt'`yt'`st' r(p)
            display as text "  `s': b per s.d. = " as result %5.2f _b[x_`s'] * `sd' ///
                as text "  se " as result %4.2f _se[x_`s'] * `sd' as text "  wild p = " as result %4.2f r(p)
        }
    }
    drop x_gu25 x_deyr25 x_gu26
}


* ============================================================================
* 2. Table 1, last column: all rounds after the cut pooled (post = Gu 2025 onward)
* ============================================================================
foreach z in z_index us_share agency_loss {
    if "`z'" == "z_index"     local zt Dep
    if "`z'" == "us_share"    local zt Us
    if "`z'" == "agency_loss" local zt Loss
    gen x_post = `z' * post
    quietly regress gam x_post $CTRL $FE, vce(cluster region)
    domain_sd `z'
    local sd = r(sd)
    res ct`zt'GamPool   _b[x_post] * `sd'
    res ctSe`zt'GamPool _se[x_post] * `sd'
    quietly boottest x_post, $BOOT
    res ctP`zt'GamPool r(p)
    display as text "Pooled, `z': b per s.d. = " as result %5.2f _b[x_post] * `sd' ///
        as text "  se " as result %4.2f _se[x_post] * `sd' as text "  wild p = " as result %4.2f r(p)
    drop x_post
}


* ============================================================================
* 3. Appendix: every outcome, US share and agency loss (first specification in the memo)
* ============================================================================
* Same model, pooled after-period, controls rain_z and log_fat only. Coefficients per 10
* percentage points of exposure (b x 0.1), as in the appendix table.
foreach z in us_share agency_loss {
    local zt = cond("`z'" == "us_share", "Pred", "Loss")
    gen x_post = `z' * post
    foreach y in gam sam muac_gam stunting morbidity cdr u5dr measles vita {
        if "`y'" == "gam"       local yt Gam
        if "`y'" == "sam"       local yt Sam
        if "`y'" == "muac_gam"  local yt Muac
        if "`y'" == "stunting"  local yt Stunt
        if "`y'" == "morbidity" local yt Morb
        if "`y'" == "cdr"       local yt Cdr
        if "`y'" == "u5dr"      local yt Ufive
        if "`y'" == "measles"   local yt Meas
        if "`y'" == "vita"      local yt Vita
        quietly regress `y' x_post rain_z log_fat $FE, vce(cluster region)
        res b`zt'`yt'  _b[x_post] * 0.1
        res se`zt'`yt' _se[x_post] * 0.1
        quietly summarize `y' if e(sample) & post == 0
        res ym`zt'`yt' r(mean)
        quietly boottest x_post, $BOOT
        res p`zt'`yt' r(p)
        display as text %-12s "`z'" %-10s "`y'" " b per 10pp = " as result %6.2f _b[x_post] * 0.1 ///
            as text "  se " as result %5.2f _se[x_post] * 0.1 as text "  wild p = " as result %4.2f r(p)
    }
    drop x_post
}


* ============================================================================
* 4. Aid dependence, alternative specification (memo Section 3: "the most persuasive null")
* ============================================================================
* Round FE common to all domains (camps vs villages then count as variation in dependence), and
* local cereal and goat prices added to the controls. 95% interval = b +/- 1.96 se.
preserve
    gen x_post = z_index * post
    foreach y in gam sam cdr u5dr {
        if "`y'" == "gam"  local yt Gam
        if "`y'" == "sam"  local yt Sam
        if "`y'" == "cdr"  local yt Cdr
        if "`y'" == "u5dr" local yt Ufive
        quietly regress `y' x_post $CTRL lp_cereal lp_goat i.dom_id i.round_id, vce(cluster region)
        res sumIdx`yt'   _b[x_post]
        res sumIdx`yt'Lo _b[x_post] - 1.96 * _se[x_post]
        res sumIdx`yt'Hi _b[x_post] + 1.96 * _se[x_post]
        quietly summarize `y' if e(sample) & post == 0
        res sumIdx`yt'Mean r(mean)
        display as text "Aid dependence, `y': " as result %5.2f _b[x_post] as text "  95% CI [" ///
            as result %5.2f _b[x_post] - 1.96 * _se[x_post] as text ", " as result %5.2f _b[x_post] + 1.96 * _se[x_post] as text "]"
    }
restore


* ============================================================================
* 5. Figure 3: event study by survey round, 2019 onward, 2024 rounds = reference
* ============================================================================
* Each exposure is standardised across domains, so coefficients are pp of wasting per s.d.
* Pre-2024 coefficients near zero support parallel trends; post-2024 ones trace the effect.
preserve
    keep if year >= 2019
    foreach z in z_index us_share agency_loss {
        if "`z'" == "z_index"     local zt Dep
        if "`z'" == "us_share"    local zt Us
        if "`z'" == "agency_loss" local zt Loss
        egen one = tag(domain) if !missing(gam, `z')
        quietly summarize `z' if one
        gen zs = (`z' - r(mean)) / r(sd)
        * interactions with every round except Gu 2024 and Deyr 2024
        gen ref = inlist(season_id, "Gu 2024", "Deyr 2024")
        quietly levelsof season_id if !ref, local(rounds)
        local ev
        foreach r of local rounds {
            local nm = "ev_" + subinstr("`r'", " ", "", .)
            gen `nm' = zs * (season_id == "`r'")
            local ev `ev' `nm'
        }
        quietly regress gam `ev' $CTRL $FE, vce(cluster region)
        display as text _n "Event study, `z' (pp per s.d., relative to 2024):"
        foreach r of local rounds {
            local nm = "ev_" + subinstr("`r'", " ", "", .)
            local tag = subinstr("`r'", " ", "", .)
            display as text "  `r'" _col(16) as result %6.2f _b[`nm'] as text "  (" as result %4.2f _se[`nm'] as text ")"
            res evt`zt'`tag' _b[`nm']
        }
        drop one zs ref ev_*
    }
restore

* ============================================================================
* 6. Robustness checks cited in the memo (Section 3)
* ============================================================================
* (a) Exposure-specific linear trend: add exposure x (year - 2024), so the post-cut effect is
*     measured against each place's own pre-existing trajectory.
gen x_post  = z_index * post
gen x_trend = z_index * (year - 2024)
quietly regress gam x_post x_trend $CTRL $FE, vce(cluster region)
domain_sd z_index
res rbBIdxTrend _b[x_post] * r(sd)
quietly boottest x_post, $BOOT
res rbPIdxTrend r(p)
display as text _n "Aid dependence with its own trend: b per s.d. = " as result %5.2f _b[x_post] * r(sd) ///
    as text "  wild p = " as result %4.2f r(p)
drop x_post x_trend

* (b) Is the US-reliance effect larger where food insecurity was already high? Both the exposure
*     and the 2024 Phase 3+ share are standardised across domains; the triple interaction is the
*     extra effect per s.d. of each.
foreach v in us_share p3share24 {
    quietly summarize `v' if first
    gen s_`v' = (`v' - r(mean)) / r(sd)
}
gen z_post  = s_us_share * post
gen s_post  = s_p3share24 * post
gen zs_post = s_us_share * s_p3share24 * post
quietly regress gam z_post s_post zs_post $CTRL $FE, vce(cluster region)
res siBUsGamZS _b[zs_post]
quietly boottest zs_post, $BOOT
res siPUsGamZS r(p)
display as text "US share x 2024 food insecurity x post: " as result %5.2f _b[zs_post] ///
    as text "  wild p = " as result %4.2f r(p)
drop s_us_share s_p3share24 z_post s_post zs_post

* (c) Attrition: of the domains surveyed in 2024, which were surveyed again in 2025 and in Gu 2026,
*     and do the 2026 survivors differ from the dropped ones? (Welch t-tests)
preserve
    egen gam24 = mean(cond(year == 2024, gam, .)), by(domain)
    egen in24  = max(year == 2024 & !missing(gam)), by(domain)
    egen in25  = max(year == 2025), by(domain)
    egen in26  = max(year == 2026), by(domain)
    keep if first & in24
    count
    res atTfour r(N)
    count if in25
    res atObs r(N)
    foreach v in us_share z_index gam24 {
        if "`v'" == "us_share" local vt Us
        if "`v'" == "z_index"  local vt Idx
        if "`v'" == "gam24"    local vt Gam
        quietly ttest `v', by(in26) unequal
        res atPTs`vt' r(p)
        display as text "Surveyed in Gu 2026 vs dropped, `v': p = " as result %4.2f r(p)
    }
restore

res_save results_03
log close
