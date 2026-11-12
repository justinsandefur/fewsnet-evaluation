*** 06_numbers.do: the paper's remaining numbers, then every number in the paper's style (output/numbers.csv).
*** numbers.csv is the record: the Google Doc should show its "text" column.

*** Sample, spread of US-funded share across domains, correlation with aid dependence, attrition
    use "$OUT/panel.dta", clear
    keep if year >= $START
    egen f = tag(domain)
    res nSurveys _N
    count if post
    res nPost r(N)
    egen fr = tag(region)
    count if fr
    res nRegions r(N)
    count if gu26 & !missing(gam, us_share)
    res nGuTs r(N)
    summarize us_share if f, detail
    res usMin 100 * r(min)
    res usMax 100 * r(max)
    res usMed 100 * r(p50)
    res sdUs 100 * r(sd)
    corr z_index us_share if f
    res corrDepUs r(rho)
    egen in24 = max(year == 2024), by(domain)
    egen in26 = max(gu26), by(domain)
    count if f & in24 & in26
    res atIn r(N)
    count if f & in24 & !in26
    res atOut r(N)

*** Table 1 rows not kept in 03
    import delimited using "$OUT/table1.csv", clear
    gsort -high
    foreach p in rural/Rural/1 idp/Idp/1 urban/Urban/1 us_min/Usmin/100 us_max/Usmax/100 loss/Loss/100 ///
        z_index/Dep/1 pre_sam/Sam/1 pre_muac_gam/Muac/1 pre_cdr/Cdr/1 pre_u5dr/Ufivedr/1 post/Postrounds/1 ///
        gu26/GuTwoSix/1 rain_pre/Rain/1 fat_pre/Fat/1 {
            tokenize "`p'", parse("/")
            res tOne`3'Hi `5' * `1'[1]
            res tOne`3'Lo `5' * `1'[2]
    }

*** Figure 1: districts in each group; last month any nutrition site reported USAID funding
    use "$OUT/districts.dta", clear
    keep if !missing(us_share)
    egen med = median(us_share)
    count if us_share > med
    res fDistHi r(N)
    count if us_share <= med
    res fDistLo r(N)
    import delimited using data/usaid_sites.csv, clear
    collapse (sum) usaid, by(year month)
    gen m = ym(year, month)
    summarize m if usaid > 0, meanonly
    res fSitesUsLast r(max)

*** Confidence intervals (wild cluster bootstrap) for table 2 and the sensitivity analyses
    frame est {
        summarize domains if label == "main" & y == "gam", meanonly
        res nDomains r(mean)
        forvalues i = 1/`=_N' {
            if inlist(label[`i'], "main", "binary", "unadjusted") {
                res ci`=nm[`i']'Lo lo[`i']
                res ci`=nm[`i']'Hi hi[`i']
            }
            if rb[`i'] != "" & inlist(term[`i'], "gu26", "post") {
                res rb`=rb[`i']'Ci`=cond(term[`i'] == "post", "p", "")'Lo lo[`i']
                res rb`=rb[`i']'Ci`=cond(term[`i'] == "post", "p", "")'Hi hi[`i']
            }
        }
    }

*** Write each number as the paper prints it (data/doc_numbers.csv holds the numbers as the Doc now prints them): decimals as in the draft, mid-point decimal, true minus,
*** p values to 2 significant figures, counts of children to the nearest 1000; space separates thousands from 10 000
*** (and in rounded counts)
    frame res: save "$OUT/results.dta", replace
    import delimited using data/doc_numbers.csv, clear varnames(1) stringcols(_all)
    rename value paper
    tempfile paper
    save `paper'
    use "$OUT/results.dta", clear
    duplicates drop name, force
    merge 1:1 name using `paper', keep(master match)
    gen stem = substr(name, 1, strlen(name) - 2)
    gen end = substr(name, -2, .)
    preserve
        keep if _merge == 1 & inlist(end, "Lo", "Hi")
        keep stem end value
        reshape wide value, i(stem) j(end) string
        rename stem name
        merge 1:1 name using `paper', keep(match) nogen
        keep if strpos(paper, " to ")
        tempfile ci
        save `ci'
    restore
    keep if _merge == 3
    keep name value paper
    append using `ci'

    gen tpl = cond(strpos(paper, " to "), substr(paper, 1, strpos(paper, " to ") - 1), subinstr(paper, "p=", "", 1))
    gen dec = cond(strpos(tpl, "."), strlen(tpl) - strpos(tpl, "."), 0)
    capture program drop num
    program num
        args out x
        gen `out' = strtrim(strofreal(round(`x', 10^(-dec)), "%20." + string(dec) + "f"))
        replace `out' = strtrim(strofreal(round(`x', 1000), "%20.0fc")) if dec == 0 & abs(real(tpl)) >= 1000 & substr(tpl, -3, .) == "000"
        replace `out' = strtrim(strofreal(`x', "%20.0fc")) if dec == 0 & abs(real(tpl)) >= 10000 & substr(tpl, -3, .) != "000"
        replace `out' = subinstr(`out', "-", "", 1) if real(subinstr(`out', ",", "", .)) == 0
        replace `out' = subinstr(subinstr(subinstr(`out', ",", " ", .), ".", "·", .), "-", "−", .)
    end
    num t value
    num tl valueLo
    num th valueHi
    gen text = cond(strpos(paper, " to "), tl + " to " + th, t)
    gen pd = cond(value >= 0.1, 2, cond(value >= 0.01, 3, 4))
    replace text = "p=" + subinstr(strtrim(strofreal(value, "%6." + string(pd) + "f")), ".", "·", 1) if substr(paper, 1, 2) == "p="
    replace text = "p<0·0001" if substr(paper, 1, 2) == "p=" & value < 0.0001
    replace text = strtrim(string(value, "%tmMonth_CCYY")) if name == "fSitesUsLast"

*** Flag numbers whose printed form differs from the current draft
    gen norm = subinstr(subinstr(subinstr(subinstr(text, " ", "", .), "·", ".", .), "−", "-", .), ",", "", .)
    gen changed = norm != subinstr(paper, " ", "", .)
    sort name
    list name paper text if changed, noobs clean
    keep name text paper changed
    export delimited using "$OUT/numbers.csv", replace

*** Tables 2, S3 and S4 cells in the paper's style: estimate (95% CI); p
    frame est {
        preserve
            gen d = cond(inlist(y, "cdr", "u5dr"), "%5.2f", "%4.1f")
            gen cell = strtrim(strofreal(b, d)) + " (" + strtrim(strofreal(lo, d)) + " to " + strtrim(strofreal(hi, d)) + ")"
            gen pd = cond(p >= 0.1, 2, cond(p >= 0.01, 3, 4))
            gen pcell = "p=" + strtrim(strofreal(p, "%6." + string(pd) + "f")) if !missing(p)
            foreach v in cell pcell {
                replace `v' = subinstr(subinstr(`v', "-0.00", "0.00", .), "-0.0 ", "0.0 ", .)
                replace `v' = subinstr(subinstr(`v', ".", "·", .), "-", "−", .)
            }
            keep label y term cell pcell domains n
            export delimited using "$OUT/table_cells_for_doc.csv", replace
        restore
    }
