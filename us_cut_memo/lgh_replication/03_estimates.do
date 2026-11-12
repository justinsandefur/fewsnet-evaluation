*** 03_estimates.do: table 1, figures 2-4, table 2, tables S3-S5, figure S2

    use "$OUT/panel.dta", clear
    egen in26 = max(gu26), by(domain)

*** Table 1: domains before the cut (2019-24), by higher (1) vs lower (0) US-funded share
    preserve
        keep if year >= $START
        gen surveys = 1
        gen rain_pre = rain_z if year >= 2019 & !post
        gen fat_pre = exp(log_fat) - 1 if year >= 2019 & !post
        collapse (sum) surveys post gu26 (mean) rain_pre fat_pre, by(high)
        tempfile rows
        save `rows'
    restore
    preserve
        foreach v in gam sam muac_gam cdr u5dr {
            egen pre_`v' = mean(cond(year >= 2019 & !post, `v', .)), by(domain)
        }
        keep if first & in_s
        gen rural = ptype == "rural"
        gen idp = ptype == "IDP"
        gen urban = ptype == "urban"
        gen us_min = us_share
        gen us_max = us_share
        collapse (count) domains = dom (sum) rural idp urban (mean) us_share loss z_index pre_* ///
            (min) us_min (max) us_max, by(high)
        merge 1:1 high using `rows', nogen
        gsort -high
        list, noobs
        export delimited using "$OUT/table1.csv", replace
        res tOneDomainsHi domains[1]
        res tOneDomainsLo domains[2]
        res tOneUsshareHi 100 * us_share[1]
        res tOneUsshareLo 100 * us_share[2]
        res tOneGamHi pre_gam[1]
        res tOneGamLo pre_gam[2]
        res tOneSurveysHi surveys[1]
        res tOneSurveysLo surveys[2]
    restore

*** Survey rounds as integers for graph labels: x = 2 * year (Gu) or 2 * year + 1 (Deyr)
    gen x = round(2 * t)
    global RND
    forvalues k = 4034/4052 {
        label define rnd `k' "`=cond(mod(`k', 2) == 0, "Gu", "Deyr")' `=floor(`k' / 2)'", add
        global RND `"$RND `k' "`=cond(mod(`k', 2) == 0, "Gu", "Deyr")' `=floor(`k' / 2)'""'
        if `k' == 4037 global RND19
        if `k' >= 4038 global RND19 `"$RND19 `k' "`=cond(mod(`k', 2) == 0, "Gu", "Deyr")' `=floor(`k' / 2)'""'
    }
    label values x rnd

*** Figure 2: mean GAM by survey round and group, 2017-26, with 95% CIs
    preserve
        keep if year >= 2017 & !missing(gam)
        collapse (mean) m = gam (sd) s = gam (count) n = gam, by(x season_id high)
        gen lo = m - 1.96 * s / sqrt(n)
        gen hi = m + 1.96 * s / sqrt(n)
        foreach r in "Gu 2026" "Gu 2025" {
            summarize m if season_id == "`r'" & high == 1, meanonly
            res rawHi`=cond("`r'" == "Gu 2026", "GuTs", "GuTv")' r(mean)
            summarize m if season_id == "`r'" & high == 0, meanonly
            res rawLo`=cond("`r'" == "Gu 2026", "GuTs", "GuTv")' r(mean)
        }
        label values x rnd
        gen xj = x + cond(high, 0.12, -0.12)
        summarize hi, meanonly
        local top = ceil(r(max))
        local bot = 6
        twoway (scatteri `top' 4049.5 `top' 4052.5, recast(area) base(`bot') color(gs15) lwidth(none)) ///
            (rspike lo hi xj if high, lcolor("$HI")) (connected m xj if high, lcolor("$HI") mcolor("$HI") msymbol(O) msize(small) lwidth(medthick)) ///
            (rspike lo hi xj if !high, lcolor("$LO")) (connected m xj if !high, lcolor("$LO") mcolor("$LO") msymbol(O) msize(small) lwidth(medthick)), ///
            legend(order(3 "Domains with higher US-funded share" 5 "Domains with lower US-funded share") ring(0) pos(1) cols(1) ///
            region(lstyle(none)) size(small)) xlabel($RND, angle(90) labsize(small) nogrid) xtitle("") ///
            ylabel(`bot'(2)`top', angle(0) nogrid labsize(small)) yscale(range(`bot' `top')) ytitle("GAM prevalence (%)", size(small)) ///
            $GR xsize(7.2) ysize(3)
        gexp figure2
    restore
    summarize gam if year >= 2019 & !post & high, meanonly
    res rawPreHi r(mean)
    summarize gam if year >= 2019 & !post & !high, meanonly
    res rawPreLo r(mean)
    summarize gam if year >= 2019 & !post, meanonly
    res yMeanGam r(mean)

*** Figures 3, S2 and S3: event studies by survey round from 2019; the two 2024 rounds are the reference.
*** Exposure per SD across domains (or the binary higher/lower group). 95% CIs and the joint test that all
*** pre-cut (2019-23) coefficients are zero are from the wild cluster bootstrap.
    frame create ev str8 y str10 v double(t x b lo hi pjoint)
    foreach spec in gam/us_share gam/high sam/us_share sam/high gam/loss gam/z_index {
        tokenize "`spec'", parse("/")
        local y `1'
        local v `3'
        local sfx = cond("`y'" == "sam", "Sam", "")
        preserve
            keep if year >= 2019 & !missing(`y', `v')
            egen f19 = tag(domain)
            quietly summarize `v' if f19
            gen zs = cond("`v'" == "high", `v', (`v' - r(mean)) / r(sd))
            levelsof t if year != 2024, local(rounds)
            local ev
            local pre
            foreach r of local rounds {
                local k = round(`r' * 10)
                gen ev`k' = zs * (t == `r')
                local ev `ev' ev`k'
                if `r' < 2024 local pre `pre' (ev`k')
            }
            quietly regress `y' `ev' $CTRL $FE, vce(cluster region)
            quietly boottest `pre', $BOOT
            local pjoint = r(p)
            if "`v'" == "us_share" res evPreP`sfx' `pjoint'
            if "`v'" == "high" res evPrePbin`sfx' `pjoint'
            foreach r of local rounds {
                local k = round(`r' * 10)
                quietly boottest ev`k', $BOOT
                matrix C = r(CI)
                frame post ev ("`y'") ("`v'") (`r') (round(2 * `r')) (_b[ev`k']) (C[1, 1]) (C[rowsof(C), 2]) (`pjoint')
            }
            frame post ev ("`y'") ("`v'") (2024) (4048) (0) (0) (0) (`pjoint')
            frame post ev ("`y'") ("`v'") (2024.5) (4049) (0) (0) (0) (`pjoint')
        restore
    }
    frame ev {
        forvalues k = 4034/4052 {
            label define rnd `k' "`=cond(mod(`k', 2) == 0, "Gu", "Deyr")' `=floor(`k' / 2)'", add
        }
        label values x rnd
        export delimited using "$OUT/event_studies.csv", replace
        foreach sfx in "" Sam {
            local yy = cond("`sfx'" == "", "gam", "sam")
            summarize b if y == "`yy'" & v == "us_share" & t == 2026, meanonly
            res evGuTs`sfx' r(mean)
            summarize lo if y == "`yy'" & v == "us_share" & t == 2026, meanonly
            res evCiGuTsLo`sfx' r(mean)
            summarize hi if y == "`yy'" & v == "us_share" & t == 2026, meanonly
            res evCiGuTsHi`sfx' r(mean)
            summarize b if y == "`yy'" & v == "us_share" & t < 2024, meanonly
            res evPreMin`sfx' r(min)
            res evPreMax`sfx' r(max)
        }

*** One panel per outcome and exposure; shading marks the rounds after the cut
        capture program drop evplot
        program evplot
            syntax, y(string) v(string) ytitle(string) [title(string) color(string) name(string) bot(real -99) top(real -99)]
            if "`color'" == "" local color black
            if `top' == -99 {
                summarize hi if y == "`y'" & v == "`v'", meanonly
                local top = ceil(r(max))
                summarize lo if y == "`y'" & v == "`v'", meanonly
                local bot = floor(r(min))
            }
            local xl `"xlabel($RND19, angle(90) labsize(small) nogrid)"'
            twoway (scatteri `top' 4049.5 `top' 4052.5, recast(area) base(`bot') color(gs15) lwidth(none)) ///
                (rspike lo hi x if y == "`y'" & v == "`v'", lcolor("`color'") lwidth(medthick)) ///
                (scatter b x if y == "`y'" & v == "`v'", mcolor("`color'") msize(medsmall)), ///
                yline(0, lcolor(black) lwidth(thin) lpattern(solid)) `xl' xtitle("") legend(off) ///
                ylabel(`bot'(1)`top', angle(0) nogrid labsize(small)) yscale(range(`bot' `top')) ytitle("`ytitle'", size(small)) ///
                title("`title'", size(medsmall) color(black)) $GR name(`name', replace)
        end
        evplot, y(gam) v(us_share) ytitle("Difference in GAM, percentage points per SD")
        graph display, xsize(7.2) ysize(3)
        gexp figure3
        evplot, y(gam) v(high) ytitle("Difference in GAM, percentage points")
        graph display, xsize(7.2) ysize(3)
        gexp figureS2_event_binary
        evplot, y(sam) v(us_share) ytitle("Difference in SAM, percentage points per SD")
        graph display, xsize(7.2) ysize(3)
        gexp figureS_event_sam
        evplot, y(sam) v(high) ytitle("Difference in SAM, percentage points")
        graph display, xsize(7.2) ysize(3)
        gexp figureS_event_sam_binary

*** Figure S3: the three exposures side by side, per SD, same scale
        summarize lo if y == "gam" & inlist(v, "us_share", "loss", "z_index"), meanonly
        local bot = floor(r(min))
        summarize hi if y == "gam" & inlist(v, "us_share", "loss", "z_index"), meanonly
        local top = ceil(r(max))
        local o `"y(gam) ytitle("GAM (pp) per SD of exposure") bot(`bot') top(`top')"'
        evplot, `o' v(z_index) title("Aid dependence") color(230 97 1) name(z_index)
        evplot, `o' v(us_share) title("US-funded share of agencies") color($LO) name(us_share)
        evplot, `o' v(loss) title("Agencies lost, 2024 to 2025") color(27 120 55) name(loss)
        graph combine z_index us_share loss, rows(1) ycommon xsize(7.6) ysize(3.5) graphregion(color(white))
        gexp figureS3_event_exposures
    }

*** Table 2 and table S3: main estimates (per SD of US-funded share), binary, unadjusted
    foreach y in gam sam muac_gam cdr u5dr {
        did `y', z(us_share) label(main)
        did `y', z(high) binary label(binary)
    }
    did gam, z(us_share) ctrl(none) label(unadjusted)

*** Figure 4 and table S4: sensitivity of the Gu 2026 (and pooled) GAM estimate
    did gam, z(us_share) fe(i.dom i.round_id) label(C: round fixed effects common to all domains)
    did gam, z(us_share) trend label(D: exposure-specific linear trend)
    did gam if ptype == "rural", z(us_share) label(E: rural livelihood zones only)
    did gam if ptype != "rural", z(us_share) label(F: towns only (IDP and urban))
    did gam if substr(domain, -4, .) != "SO22", z(us_share) label(G: excluding Banadir (Mogadishu))
    did gam, z(us_share) from(2015) label(H: since 2015)
    did gam, z(us_share_obs) label(I: no imputed donors)
    did gam if in26, z(us_share) label(J: domains surveyed in Gu 2026 only)
    did gam, z(loss) label(K: agencies lost (alternative exposure))
    did gam, z(z_index) label(L: aid dependence (alternative exposure))

    frame est {
        list label y term b lo hi p domains if term == "gu26" | term == "post", noobs sepby(label) abbreviate(12)
        export delimited using "$OUT/estimates.csv", replace

*** Table 2 cells in the paper's number style (mid-point decimals, true minus), to paste into the Google Doc
        preserve
            keep if inlist(label, "main", "binary", "unadjusted")
            gen d = cond(inlist(y, "cdr", "u5dr"), "%5.2f", "%4.1f")
            gen cell = strtrim(strofreal(b, d)) + " (" + strtrim(strofreal(lo, d)) + " to " + strtrim(strofreal(hi, d)) + ")"
            gen pcell = "p=" + strtrim(strofreal(p, cond(p >= 0.1, "%4.2f", cond(p >= 0.01, "%5.3f", "%6.4f"))))
            replace cell = subinstr(subinstr(cell, ".", "·", .), "-", "−", .)
            replace pcell = subinstr(pcell, ".", "·", .)
            keep label y term cell pcell
            export delimited using "$OUT/table2_for_doc.csv", replace
        restore

*** keep the paper's numbers (table 2, figure 4)
        gen nm = cond(y == "gam", "Gam", cond(y == "sam", "Sam", cond(y == "muac_gam", "Muac", cond(y == "cdr", "Cdr", "Ufive"))))
        replace nm = nm + cond(label == "binary", "Bin", cond(label == "unadjusted", "Unadj", "")) ///
            + cond(term == "gu25", "GuTv", cond(term == "deyr25", "DyTv", cond(term == "gu26", "GuTs", "Pool")))
        gen rb = cond(label == "main" & y == "gam", "A", cond(label == "unadjusted", "B", substr(label, 1, 1)))
        replace rb = "" if strlen(rb) != 1 | !strpos("ABCDEFGHIJKL", rb)
        forvalues i = 1/`=_N' {
            if inlist(label[`i'], "main", "binary", "unadjusted") {
                res b`=nm[`i']' b[`i']
                res p`=nm[`i']' p[`i']
            }
            if rb[`i'] != "" & term[`i'] == "gu26" {
                res rb`=rb[`i']'B b[`i']
                res rb`=rb[`i']'P p[`i']
            }
            if rb[`i'] != "" & term[`i'] == "post" {
                res rb`=rb[`i']'Bp b[`i']
                res rb`=rb[`i']'Pp p[`i']
            }
        }

*** Figure 4: forest plot of the Gu 2026 estimate across specifications A-J, with estimate (95% CI) at right
        preserve
            keep if rb != "" & term == "gu26" & !inlist(rb, "K", "L")
            sort rb
            gen name = ""
            local i 0
            foreach t in "Main specification" "No rainfall or conflict controls" "Survey round effects common to all domains" ///
                "Exposure-specific linear trend" "Rural livelihood zones only" "Towns only (IDP and urban)" ///
                "Excluding Banadir (Mogadishu)" "Since 2015" "Donor recorded for every partner (no imputation)" ///
                "Domains surveyed in Gu 2026 only" {
                local ++i
                replace name = "`t' (n=" + string(domains) + ")" in `i'
            }
            gen cell = strtrim(strofreal(b, "%4.1f")) + " (" + strtrim(strofreal(lo, "%4.1f")) + " to " + strtrim(strofreal(hi, "%4.1f")) + ")"
            replace cell = subinstr(cell, "-0.0 ", "0.0 ", .)
            replace cell = subinstr(subinstr(cell, ".", "·", .), "-", "−", .)
            gen pos = _N - _n + 1
            forvalues i = 1/`=_N' {
                label define fl `=pos[`i']' "`=name[`i']'", add
            }
            label values pos fl
            summarize hi, meanonly
            local hmax = ceil(r(max))
            local right = `hmax' + 0.5
            summarize lo, meanonly
            local left = min(0, floor(r(min)))
            gen xr = `right'
            twoway (rspike lo hi pos, horizontal lcolor(black) lwidth(medthick)) (scatter pos b, mcolor(black) msymbol(square) msize(medsmall)) ///
                (scatter pos xr, msymbol(none) mlabel(cell) mlabpos(3) mlabsize(small) mlabcolor(black)), ///
                xline(0, lcolor(black) lpattern(solid)) xline(`=b[1]', lpattern(dot) lcolor(black)) ylabel(1/`=_N', valuelabel angle(0) labsize(small) nogrid) ///
                xlabel(`left'(1)`hmax', labsize(small) nogrid) xscale(range(`left' `=`right' + 3')) ytitle("") legend(off) ///
                xtitle("Difference in GAM prevalence in Gu 2026 (percentage points) per SD of exposure", size(small)) $GR xsize(7.2) ysize(3.4)
            gexp figure4
        restore
    }

*** Table S5: domains surveyed in 2024 that were, vs were not, surveyed again in Gu 2026 (Welch t tests)
    preserve
        egen in24 = max(year == 2024), by(domain)
        egen gam24 = mean(cond(year == 2024, gam, .)), by(domain)
        egen gam23 = mean(cond(year == 2023, gam, .)), by(domain)
        gen dgam = gam24 - gam23
        keep if first & in24
        replace us_share = 100 * us_share
        replace loss = 100 * loss
        frame create s5 str10 var double(surveyed not_surveyed p n_surveyed n_not)
        foreach v in us_share loss z_index gam24 dgam {
            quietly ttest `v', by(in26) unequal
            frame post s5 ("`v'") (r(mu_2)) (r(mu_1)) (r(p)) (r(N_2)) (r(N_1))
        }
        frame s5 {
            list, noobs
            export delimited using "$OUT/tableS5_attrition.csv", replace
        }
        frame drop s5
    restore

*** Table S1: every survey domain, by population type and US-funded share. Surveys are counted from Gu 2019
*** (the estimation sample) and from 2015 (all transcribed rounds).
    preserve
        egen n_all = count(gam), by(domain)
        egen n_s = count(cond(year >= $START, gam, .)), by(domain)
        egen n_post = total(post & !missing(gam)), by(domain)
        egen gu26_any = max(gu26 & !missing(gam)), by(domain)
        keep if first
        gen type = cond(ptype == "rural", "Rural", cond(ptype == "IDP", "IDP", "Urban"))
        gen us_pct = round(100 * us_share)
        gen group = cond(high, "Higher", "Lower")
        gen loss_pct = round(100 * loss)
        gen surveyed_gu26 = cond(gu26_any, "Yes", "No")
        gsort ptype -us_share
        keep population_group type region us_pct group loss_pct n_s n_all n_post surveyed_gu26
        order population_group type region us_pct group loss_pct n_s n_all n_post surveyed_gu26
        export delimited using "$OUT/tableS1_domains.csv", replace
    restore
