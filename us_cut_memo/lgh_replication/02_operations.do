*** 02_operations.do: what happened to US funding and US-funded operations
*** (figure 1, figure S1, table S2 and the numbers in the second paragraph of the Results)

*** A. US humanitarian funding to Somalia, by year of decision (OCHA FTS)
    import delimited using data/fts.csv, clear
    keep if year >= 2019
    list year us_musd other_musd, noobs
    foreach y in 2024 2025 {
        summarize us_musd if year == `y', meanonly
        local us`y' = r(mean)
        summarize other_musd if year == `y', meanonly
        local ot`y' = r(mean)
    }
    res fUsTf `us2024'
    res fUsTv `us2025'
    res fUsDrop 100 * (1 - `us2025' / `us2024')
    res fOtDrop 100 * (1 - `ot2025' / `ot2024')
    res fUsShareTf 100 * `us2024' / (`us2024' + `ot2024')
    graph bar us_musd other_musd, over(year, label(labsize(small))) bar(1, color("$HI") lcolor(white)) ///
        bar(2, color(gs9) lcolor(white)) bargap(0) outergap(40) ///
        legend(order(1 "USA" 2 "All other donors") ring(0) pos(11) cols(1) region(lstyle(none)) size(small)) ///
        ylabel(0(200)1400, angle(0) nogrid labsize(small)) ytitle("US{c S|} million", size(small)) ///
        title("A  Humanitarian funding to Somalia, by donor", size(medsmall) pos(11) color(black)) $GR name(A, replace)

*** District groups: US-funded share above vs below the median district
    use "$OUT/districts.dta", clear
    keep if !missing(us_share)
    egen med = median(us_share)
    gen high = us_share > med
    keep dist high
    tempfile grp
    save `grp'

*** B. Nutrition sites naming USAID as a funder, per month, by district group
    import delimited using data/usaid_sites.csv, clear
    merge m:1 dist using `grp', keep(match) nogen
    collapse (sum) usaid, by(high year month)
    reshape wide usaid, i(year month) j(high)
    gen m = ym(year, month)
    format m %tmMon_CCYY
    gen all = usaid0 + usaid1
    summarize all if year == 2024, meanonly
    res fSitesUsTf r(mean)
    summarize all if year == 2025 & month >= 7, meanonly
    res fSitesUsHTwoTv r(mean)
    summarize all if year == 2026, meanonly
    res fSitesUsHOneTs r(mean)
    twoway line usaid1 usaid0 m, lcolor("$HI" "$LO") lwidth(medthick medthick) xline(`=ym(2025, 1)', lpattern(dot) lcolor(black)) ///
        legend(order(1 "Districts with higher US-funded share" 2 "Districts with lower US-funded share") ring(0) pos(7) cols(1) ///
        region(lstyle(none)) size(small)) xlabel(`=ym(2023, 1)'(6)`=ym(2026, 1)', angle(90) labsize(small) nogrid) xtitle("") ///
        ylabel(0(10)40, angle(0) nogrid labsize(small)) ytitle("Site-months reporting USAID funding", size(small)) ///
        title("B  Nutrition sites funded by USAID", size(medsmall) pos(11) color(black)) $GR name(B, replace)
    graph combine A B, rows(1) xsize(7.2) ysize(2.8) graphregion(color(white))
    gexp figure1

*** Figure S1: humanitarian partners present per district (OCHA 3W), by district group
    use `grp', clear
    count if high
    local nhi = r(N)
    local nlo = _N - r(N)
    import delimited using data/partners.csv, clear
    merge m:1 dist using `grp', keep(match) nogen
    collapse (sum) partners, by(high year month)
    replace partners = partners / cond(high, `nhi', `nlo')
    reshape wide partners, i(year month) j(high)
    gen m = ym(year, month)
    format m %tmMon_CCYY
    twoway line partners1 partners0 m, lcolor("$HI" "$LO") lwidth(medthick medthick) xline(`=ym(2025, 1)', lpattern(dot) lcolor(black)) ///
        legend(order(1 "Higher US-funded share" 2 "Lower US-funded share") ring(0) pos(7) cols(1) region(lstyle(none)) size(small)) ///
        xlabel(, angle(90) labsize(small) nogrid) xtitle("") ylabel(0(2)12, angle(0) nogrid labsize(small)) ///
        ytitle("Partners per district", size(small)) $GR xsize(6) ysize(3)
    gexp figureS1_partners

*** Aid delivered nationally, monthly average Jan-Jun
    import delimited using data/national.csv, clear
    foreach y in 24 25 26 {
        summarize fsc_nat if year == 20`y', meanonly
        local f`y' = r(mean) / 1e6
        summarize otp_nat if year == 20`y', meanonly
        local o`y' = r(mean)
    }
    res natFscTf `f24'
    res natFscTv `f25'
    res natFscTs `f26'
    res natOtpTf `o24'
    res natOtpTs `o26'

*** Table S2: did aid delivered fall more where exposure was higher? (district cross-section)
*** fsc = people reached with food or cash per month; otp = sites treating SAM; Jan-Jun of each year.
*** A district missing from a dashboard reached nobody.
    use "$OUT/districts.dta", clear
    foreach v of varlist fsc24-otp26 {
        replace `v' = 0 if missing(`v')
    }
    frame create fs str12 y str12 z double(b lo hi F n)
    foreach y in 25 26 {
        gen fsc_loss`y' = (fsc24 - fsc`y') / pop * 100
        gen otp_loss`y' = (otp24 - otp`y') / (0.19 * pop) * 10000
        foreach x in fsc otp {
            foreach z in us_share loss aid_dep {
                quietly regress `x'_loss`y' `z', vce(cluster region)
                quietly summarize `z' if e(sample)
                local s = r(sd)
                frame post fs ("`x'_loss`y'") ("`z'") (_b[`z'] * `s') ((_b[`z'] - 1.96 * _se[`z']) * `s') ///
                    ((_b[`z'] + 1.96 * _se[`z']) * `s') ((_b[`z'] / _se[`z'])^2) (e(N))
                local zt = cond("`z'" == "us_share", "Us", cond("`z'" == "loss", "Loss", "Dep"))
                res fsF`=proper("`x'")'`zt'`=cond(`y' == 25, "Tv", "Ts")' (_b[`z'] / _se[`z'])^2
            }
        }
    }
    frame fs: list, noobs
    frame fs: export delimited using "$OUT/tableS2_first_stage.csv", replace
    frame drop fs
