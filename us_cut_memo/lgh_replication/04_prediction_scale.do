*** 04_prediction_scale.do: national prediction gap (table S6) and numbers of children

*** Table S6: for each year, fit GAM on domain effects, season, trend, rainfall, conflict and prices using
*** pre-2025 years other than that year; average the prediction error in the held-out year (domains seen in the fit)
    use "$OUT/panel.dta", clear
    gen deyr = season_type == "Deyr"
    gen trend = year - 2015
    frame create gap year mean_err domains
    forvalues yr = 2017/2026 {
        quietly regress gam i.dom deyr trend $CTRL lp_cereal lp_goat if year != `yr' & year < 2025
        quietly gen fit = e(sample)
        quietly egen known = max(fit), by(domain)
        quietly predict yhat if year == `yr' & known & !missing(gam)
        quietly gen err = gam - yhat
        preserve
            quietly keep if !missing(err)
            collapse (mean) err, by(domain)
            quietly summarize err
            frame post gap (`yr') (r(mean)) (r(N))
        restore
        drop fit known yhat err
    }
    frame gap {
        list, noobs
        export delimited using "$OUT/tableS6_prediction_gap.csv", replace
        summarize mean_err if year == 2025, meanonly
        res scNatTv r(mean)
        summarize mean_err if year == 2026, meanonly
        local nat26 = r(mean)
        res scNatTs `nat26'
    }

*** Scale: Gu 2026 effect of moving from the least exposed tenth of districts to the population-weighted average
*** district, applied to the children aged 6-59 months in the IPC analysis (Jul 2025 - Jun 2026)
    import delimited using data/children.csv, clear
    local kids = value[1]
    use "$OUT/districts.dta", clear
    keep if !missing(us_share, pop)
    summarize us_share [aw = pop], meanonly
    local avg = r(mean)
    sort us_share
    local k = 1 + 0.1 * (_N - 1)
    local p10 = us_share[floor(`k')] + (`k' - floor(`k')) * (us_share[floor(`k') + 1] - us_share[floor(`k')])
    frame est {
        summarize b if label == "main" & y == "gam" & term == "gu26", meanonly
        local b = r(mean)
        summarize lo if label == "main" & y == "gam" & term == "gu26", meanonly
        local lo = r(mean)
        summarize hi if label == "main" & y == "gam" & term == "gu26", meanonly
        local hi = r(mean)
        summarize sd if label == "main" & y == "gam" & term == "gu26", meanonly
        local sd = r(mean)
    }
    local gap = `avg' - `p10'
    res scPp `b' / `sd' * `gap'
    res scPpLo `lo' / `sd' * `gap'
    res scPpHi `hi' / `sd' * `gap'
    res scGap 100 * `gap'
    res scKids `kids' / 1e6
    res scBase 0.13 * `kids'
    res scN `b' / `sd' * `gap' / 100 * `kids'
    res scNLo `lo' / `sd' * `gap' / 100 * `kids'
    res scNHi `hi' / `sd' * `gap' / 100 * `kids'
    res scNatNTs `nat26' / 100 * `kids'
    display as text "Extra wasted children, Gu 2026: " as result %9.0fc `b' / `sd' * `gap' / 100 * `kids' ///
        as text " (" as result %9.0fc `lo' / `sd' * `gap' / 100 * `kids' as text " to " ///
        as result %9.0fc `hi' / `sd' * `gap' / 100 * `kids' as text ")"
    res scPct 100 * `b' / `sd' * `gap' / 13

*** Same for SAM (US-funded share, average district vs least exposed tenth)
    frame est {
        foreach s in b lo hi sd {
            summarize `s' if label == "main" & y == "sam" & term == "gu26", meanonly
            local `s'_sam = r(mean)
        }
    }
    res scNSam `b_sam' / `sd_sam' * `gap' / 100 * `kids'
    res scNSamLo `lo_sam' / `sd_sam' * `gap' / 100 * `kids'
    res scNSamHi `hi_sam' / `sd_sam' * `gap' / 100 * `kids'

*** Agencies lost has a natural zero (a district that lost none): scale the Gu 2026 effect per unit of loss
*** by the population-weighted mean loss
    use "$OUT/districts.dta", clear
    keep if !missing(loss, pop)
    summarize loss [aw = pop], meanonly
    local loss = r(mean)
    res scLoss 100 * `loss'
    use "$OUT/panel.dta", clear
    foreach y in gam sam {
        foreach r in gu25 deyr25 gu26 {
            capture drop x_`r'
            gen x_`r' = loss * `r'
        }
        quietly regress `y' x_gu25 x_deyr25 x_gu26 $CTRL $FE if !missing(loss) & year >= $START, vce(cluster region)
        local t = cond("`y'" == "gam", "", "Sam")
        local b = _b[x_gu26]
        quietly boottest x_gu26, $BOOT
        matrix C = r(CI)
        local lo = C[1, 1]
        local hi = C[rowsof(C), 2]
        res scLossPp`t' `b' * `loss'
        res scLossPpLo`t' `lo' * `loss'
        res scLossPpHi`t' `hi' * `loss'
        res scLossN`t' `b' * `loss' / 100 * `kids'
        res scLossNLo`t' `lo' * `loss' / 100 * `kids'
        res scLossNHi`t' `hi' * `loss' / 100 * `kids'
        if "`y'" == "gam" res scLossPct 100 * `b' * `loss' / 13
    }
