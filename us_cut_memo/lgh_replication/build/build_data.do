*** build_data.do: build the analysis data in data/ from the extracts in build/source/ and the raw files in build/raw/
*** Run from lgh_replication/:  do build/build_data.do
*** Python (build/extract_*.py) only reads, parses, matches names and does the map work; every rule below is in Stata.

    version 19
    clear all
    set more off
    set type double
    if "$DATA" == "" global DATA "data"
*** Prices are assigned to regions with WFP's region names; "region_as_used" reproduces the mapping used so far
*** (see README: it puts several regions' prices in the wrong region); "region" is the correct one
    if "$PRICE_REGION" == "" global PRICE_REGION "region_as_used"
    global SRC "build/source"
    global RAW "build/raw"
    capture mkdir "$DATA"
    tempfile agency dons org_u typ units pres dpop reach usd prt fsc otp dw du upop wfpreg rz6 acled price grp f6

*** Small lookup files
    import delimited using "$SRC/unit_population.csv", clear encoding("utf-8") varnames(1) stringcols(1)
    save `upop'
    import delimited using "$SRC/wfp_admin1.csv", clear encoding("utf-8") varnames(1) stringcols(_all)
    save `wfpreg'

*** dist(): Banadir's 17 districts (reported separately from 2025) count as one district, SO22
    capture program drop distkey
    program distkey
        args out in
        gen `out' = cond(substr(`in', 1, 4) == "SO22", "SO22", `in')
    end

*** monthnum(): month name (any case) -> 1-12
    capture program drop monthnum
    program monthnum
        args out in
        gen `out' = .
        local i 0
        foreach m in january february march april may june july august september october november december {
            local ++i
            replace `out' = `i' if strlower(strtrim(`in')) == "`m'"
        }
    end

*** ============================================================ 1. Humanitarian funding (OCHA FTS)
*** Flows to Somalia: paid or committed, entering the country (boundary "incoming" or blank), by year of decision
    import delimited using "$SRC/fts_somalia.csv", clear encoding("utf-8") varnames(1) stringcols(_all) bindquote(strict) maxquotedrows(unlimited)
    destring amount_usd, replace
    keep if inlist(status, "paid", "commitment") & inlist(boundary, "incoming", "") & amount_usd > 0 & !missing(amount_usd)
    gen year = real(substr(decision_date, 1, 4))
    gen us = substr(donor, 1, 13) == "United States"

*** US share of each UN agency's funding in Somalia, 2023-24: used for UN agencies named as a partner's donor
    preserve
        keep if inrange(year, 2023, 2024)
        frame create ag str8 agency double share
        foreach p in "unicef|Children's Fund" "wfp|World Food Programme" "unhcr|High Commissioner for Refugees" ///
            "iom|International Organization for Migration" "fao|Food and Agriculture Organization" ///
            "unfpa|Population Fund" "who|World Health Organization" {
            gettoken k pat : p, parse("|")
            local pat = substr("`pat'", 2, .)
            quietly summarize amount_usd if strpos(recipient, "`pat'")
            local tot = r(sum)
            quietly summarize amount_usd if strpos(recipient, "`pat'") & us
            frame post ag ("`k'") (cond(`tot' > 0, r(sum) / `tot', 0))
        }
        frame ag: save `agency'
        frame drop ag
    restore

*** fts.csv: US and other donors, US$ million, 2019-2025
    keep if inrange(year, 2019, 2025)
    collapse (sum) amount_usd, by(year us)
    replace amount_usd = amount_usd / 1e6
    reshape wide amount_usd, i(year) j(us)
    rename (amount_usd0 amount_usd1) (other_musd us_musd)
    export delimited year other_musd us_musd using "$DATA/fts.csv", replace

*** ============================================================ 2. US-funded share of each 2024 partner (OCHA 3W donor field)
*** donors_3w.csv: one row per 3W row and donor named in it, classified in Python as US (1), another donor (0)
*** or a UN agency (its US share); rows naming no usable donor appear once with an empty class.
    import delimited using "$SRC/donors_3w.csv", clear encoding("utf-8") varnames(1) stringcols(_all) bindquote(strict) maxquotedrows(unlimited)
    rename donor_class agency
    merge m:1 agency using `agency', keep(master match) nogen
    gen v = cond(agency == "us", 1, cond(agency == "nonus", 0, share))
    collapse (mean) u = v (first) org org_type cluster dist, by(file_year row_id)
    save `dons'

*** Fallback 1: the organisation's own average over 2023-24 rows that name a donor
    preserve
        keep if !missing(u)
        collapse (mean) u_org = u, by(org)
        save `org_u'
    restore

*** Organisation type (UN, INGO, NNGO, ...): most common type the organisation gives in 2024 (ties: first alphabetically)
    preserve
        keep if file_year == "2024"
        replace org_type = strupper(strtrim(org_type))
        keep if org_type != ""
        contract org org_type
        gsort org -_freq org_type
        by org: keep if _n == 1
        keep org org_type
        rename org_type type
        save `typ'
    restore

*** Units = organisation x sector x district in the 2024 file, in nutrition, health, food security and WASH
    keep if file_year == "2024" & inlist(cluster, "nutrition", "health", "food_security", "wash")
    collapse (mean) u_rows = u, by(dist org cluster)
    merge m:1 org using `org_u', keep(master match) nogen
*** Fallback 2: a UN agency that names no donor takes its own US share
    gen agency = ""
    replace agency = "unicef" if org == "united nations childrens fund"
    replace agency = "wfp" if org == "world food programme"
    replace agency = "unhcr" if org == "united nations high commissioner for refugees"
    replace agency = "iom" if org == "international organization for migration"
    replace agency = "fao" if org == "food and agriculture organization"
    replace agency = "unfpa" if org == "united nations population fund"
    replace agency = "who" if org == "world health organization"
    merge m:1 agency using `agency', keep(master match) nogen
    gen u = cond(!missing(u_rows), u_rows, cond(!missing(u_org), u_org, share))
    merge m:1 org using `typ', keep(master match) nogen
    replace type = "OTHER" if type == ""
*** Fallback 3: the average for the organisation's type, else the average of all units
    gen imputed = cond(missing(u), "True", "False")
    egen type_mean = mean(u), by(type)
    summarize u, meanonly
    replace u = cond(!missing(type_mean), type_mean, r(mean)) if missing(u)
    sort dist org cluster
    export delimited dist org cluster type u imputed using "$DATA/units2024.csv", replace

*** ============================================================ 3. Partners present (OCHA 3W, monthly)
*** presence_3w.csv: organisation x sector x district x month, 2024-26, the four sectors
    import delimited using "$SRC/presence_3w.csv", clear encoding("utf-8") varnames(1) stringcols(1 2 3) bindquote(strict)
    distkey dist admin2_pcode
    drop if dist == ""
    duplicates drop dist org cluster year month, force
    save `pres'

*** partners.csv: partners (organisation x sector pairs) per district and month
    contract dist year month, freq(partners)
    sort dist year month
    export delimited using "$DATA/partners.csv", replace

*** Partners per district, monthly average April-October 2024 and 2025
    use `pres', clear
    keep if inrange(month, 4, 10) & inlist(year, 2024, 2025)
    contract dist year month
    collapse (mean) partners = _freq, by(dist year)
    reshape wide partners, i(dist) j(year)
    rename (partners2024 partners2025) (partners24 partners25)
    save `prt'

*** ============================================================ 4. District population and aid per resident, 2024
*** Population: WorldPop summed over FEWS NET's 2016 livelihood units, units assigned to districts
    import delimited using "$SRC/unit_district.csv", clear encoding("utf-8") varnames(1) stringcols(_all) bindquote(strict)
    keep fnid vintage admin2_pcode
    distkey dist admin2_pcode
    save `du'
    keep if vintage == "2016C3"
    merge 1:1 fnid using `upop', keep(master match) nogen
    drop if dist == ""
    collapse (sum) pop, by(dist)
    keep if pop > 0
    save `dpop'

*** 3W reach, 2024: US$ transferred (all sectors) and people reached per month (the four sectors)
    import delimited using "$SRC/reach_3w_2024.csv", clear encoding("utf-8") varnames(1) stringcols(1 2 3 4) bindquote(strict)
    distkey dist admin2_pcode
    preserve
        keep if measure == "usd"
        collapse (sum) usd = value, by(dist)
        save `usd'
    restore
    keep if measure == "reached" & inlist(cluster, "nutrition", "health", "food_security", "wash")
    egen tm = tag(period_start)
    count if tm
    local months = r(N)
    collapse (sum) reach = value, by(dist)
    replace reach = reach / `months'
    save `reach'

*** ============================================================ 5. Aid delivered, January-June 2024, 2025, 2026
*** Food Security Cluster: people reached with food or cash, district x month (WFP dashboard).
*** A district reached in any year counts as zero in any month it is absent.
    forvalues y = 2024/2026 {
        import delimited using "$RAW/fsc/fsc_som_`y'_food_cash_reached_district_month.csv", clear encoding("utf-8") varnames(1) stringcols(_all) bindquote(strict)
        destring reached, replace ignore(",") force
        monthnum m month
        gen year = `y'
        distkey dist admin2_pcode
        if `y' > 2024 append using `fsc'
        save `fsc', replace
    }
    preserve
        keep year m
        drop if missing(m)
        duplicates drop
        tempfile ym
        save `ym'
    restore
    drop if dist == ""
    collapse (sum) fsc = reached, by(dist year m)
    tempfile f0
    save `f0'
    keep dist
    duplicates drop
    cross using `ym'
    merge 1:1 dist year m using `f0', nogen
    replace fsc = 0 if missing(fsc)
    keep if inrange(m, 1, 6)
    save `fsc', replace
    tempfile fscnat
    collapse (sum) fsc_nat = fsc, by(year)
    replace fsc_nat = fsc_nat / 6
    save `fscnat'

*** Nutrition Cluster: sites treating severe acute malnutrition (OTP), district x month
    import delimited using "$SRC/nutrition_sites.csv", clear encoding("utf-8") varnames(1) stringcols(_all) bindquote(strict) maxquotedrows(unlimited)
    gen year = real(substr(period, 1, 4))
    gen mname = substr(period, 6, .)
    monthnum m mname
    drop if missing(year, m)
    replace dist = "nan" if dist == ""
    distkey d dist
    replace dist = d
    drop d
    preserve
*** usaid_sites.csv: site reports naming USAID or its Bureau for Humanitarian Assistance as a source of funds
        keep if year >= 2023 & (year < 2026 | m <= 6)
        foreach v in funds funds_other {
            replace `v' = "nan" if `v' == ""
        }
        gen usaid = ustrregexm(strlower(funds_other + " " + funds), "usaid|\bbha\b|ofda|\bffp\b|united states|\busg\b")
        collapse (sum) usaid, by(dist year m)
        rename m month
        sort dist year month
        export delimited using "$DATA/usaid_sites.csv", replace
    restore
    gen otp_site = otp == "True" | strpos(activities, "OTP") > 0
    keep if inrange(year, 2024, 2026) & inrange(m, 1, 6)
    collapse (sum) otp = otp_site, by(dist year m)
    save `otp'
    tempfile otpnat
    egen tm = tag(year m)
    collapse (sum) otp_nat = otp tm, by(year)
    replace otp_nat = otp_nat / tm
    keep year otp_nat
    merge 1:1 year using `fscnat', nogen
    order year fsc_nat otp_nat
    export delimited year fsc_nat otp_nat using "$DATA/national.csv", replace

*** ============================================================ 6. districts.csv
    use `fsc', clear
    collapse (mean) fsc, by(dist year)
    reshape wide fsc, i(dist) j(year)
    tempfile fscw
    save `fscw'
    use `otp', clear
    collapse (mean) otp, by(dist year)
    reshape wide otp, i(dist) j(year)
    tempfile otpw
    save `otpw'
    use `dpop', clear
    foreach f in usd reach {
        merge 1:1 dist using ``f'', keep(master match) nogen
        replace `f' = 0 if missing(`f')
        gen `f'_pc = `f' / pop
    }
    merge 1:1 dist using `prt', keep(master match) nogen
    gen partners_pc = cond(missing(partners24), 0, partners24) / pop * 1e5
    merge 1:1 dist using `fscw', keep(master match) nogen
    merge 1:1 dist using `otpw', keep(master match) nogen
    rename (fsc2024 fsc2025 fsc2026 otp2024 otp2025 otp2026) (fsc24 fsc25 fsc26 otp24 otp25 otp26)
    sort dist
    export delimited dist pop usd_pc reach_pc partners_pc partners24 partners25 fsc24 fsc25 fsc26 otp24 otp25 otp26 ///
        using "$DATA/districts.csv", replace

*** ============================================================ 7. children.csv (IPC acute malnutrition analysis, Jul 2025 - Jun 2026)
    import excel using "$RAW/ipc/ipc_amn_2025_26.xlsx", clear allstring
    keep if strtrim(A) == "Total"
    gen item = "somalia_children_6_59m"
    gen value = real(B)
    gen source = "IPC acute malnutrition analysis Jul 2025-Jun 2026, Total row"
    keep in 1
    export delimited item value source using "$DATA/children.csv", replace

*** ============================================================ 8. Survey panel
*** Surveys kept: SMART surveys reporting GAM, matched to a domain; not partner NGOs' own surveys or summary rows
    import delimited using "$SRC/surveys.csv", clear encoding("utf-8") varnames(1) stringcols(_all) bindquote(strict) maxquotedrows(unlimited)
    destring row season_year gam sam muac_gam cdr u5dr, replace
    keep if method == "SMART" & !missing(gam) & domain != ""
    drop if ustrregexm(population_group, "\b(ACF|SCI|CARE|INTERSOS|EPHCO|Concern)\b|\(SCI\)|Wordwide")
    drop if ustrregexm(population_group, "^(median|mean|average)$", 1)
    gen t = monthly(month, "YM")
    gen ptype = substr(domain, 1, strpos(domain, "|") - 1)
    gen season_id = season_type + " " + string(season_year)
    gen year = season_year
    gen post = year >= 2025

*** Domain -> FEWS NET units (for rainfall) and domain -> district weights (for conflict, prices and exposures)
    preserve
        keep domain fnids dist
        duplicates drop domain, force
        tempfile dom
        save `dom'
    restore

*** Several surveys of one domain in one season (e.g. two Mogadishu urban samples): average them
    sort domain ptype season_id season_type year post row
    collapse (mean) gam sam muac_gam cdr u5dr (first) t population_group, by(domain ptype season_id season_type year post)
    gen gid = _n
    save `grp'

*** Units: rural domains list their units; a town domain takes every unit in its district
    use `dom', clear
    preserve
        keep if fnids != ""
        split fnids, parse(";") gen(f)
        keep domain f*
        drop fnids
        reshape long f, i(domain) j(k)
        drop if f == ""
        rename f fnid
        keep domain fnid
        tempfile ru
        save `ru'
    restore
    keep if dist != ""
    keep domain dist
    joinby dist using `du'
    keep domain fnid
    append using `ru'
    duplicates drop
    tempfile dunits
    save `dunits'

*** Weights: rural domains weight districts by their units' population (1 where unknown); towns are one district.
*** Weights are rounded to 4 decimals.
    use `ru', clear
    merge m:1 fnid using `upop', keep(master match) nogen
    replace pop = 1 if missing(pop)
    merge m:1 fnid using `du', keep(master match) nogen keepusing(dist)
    drop if dist == ""
    collapse (sum) pop, by(domain dist)
    egen tot = total(pop), by(domain)
    gen w = round(pop / tot, 0.0001)
    keep domain dist w
    tempfile rw
    save `rw'
    use `dom', clear
    keep if dist != ""
    gen w = 1
    keep domain dist w
    append using `rw'
    sort domain dist
    save `dw'
    export delimited domain dist w using "$DATA/domain_weights.csv", replace

*** ------------------------------------------------------------ rainfall anomalies
*** For each unit and month: rainfall over the last 6 (12) months, as a z-score against the same months of
*** 1991-2020. A domain-round takes the mean z-score of its units in the survey's target month.
    import delimited using "$SRC/unit_rain.csv", clear encoding("utf-8") varnames(1) stringcols(1 2)
    gen t = monthly(month, "YM")
*** Months without rainfall data count as zero in the sums (as in the original Python; affects two Jamaame units).
*** Units with no rainfall data at all get no z-score.
    replace rain = 0 if missing(rain)
    egen u = group(fnid)
    tsset u t
    gen r6 = rain + L1.rain + L2.rain + L3.rain + L4.rain + L5.rain
    gen r12 = r6 + L6.rain + L7.rain + L8.rain + L9.rain + L10.rain + L11.rain
    gen mo = month(dofm(t))
    gen yr = year(dofm(t))
    foreach w in 6 12 {
        egen mu`w' = mean(cond(inrange(yr, 1991, 2020), r`w', .)), by(u mo)
        egen sd`w' = sd(cond(inrange(yr, 1991, 2020), r`w', .)), by(u mo)
        gen z`w' = (r`w' - mu`w') / sd`w' if sd`w' > 0
    }
    keep fnid t z6 z12
    save `rz6'

    use `grp', clear
    keep gid domain t
    joinby domain using `dunits'
    merge m:1 fnid t using `rz6', keep(master match) nogen
    collapse (mean) rain_z = z6 rain12_z = z12, by(gid)
    tempfile rain
    save `rain'

*** ------------------------------------------------------------ conflict deaths (ACLED), last 6 months
    import excel using "$RAW/acled/som.xlsx", sheet("Data") firstrow clear allstring
    rename (Admin2Pcode Month Year Fatalities) (pcode mname yname fat)
    destring yname fat, replace
    monthnum mo mname
    gen t = ym(yname, mo)
    distkey dist pcode
    drop if dist == ""
    collapse (sum) fat, by(dist t)
    rename t ta
    save `acled'
    use `grp', clear
    keep gid domain t
    joinby domain using `dw'
    joinby dist using `acled'
    keep if ta > t - 6 & ta <= t
    gen wf = w * fat
    collapse (sum) tot = wf, by(gid)
    tempfile fat
    save `fat'

*** ------------------------------------------------------------ assemble; region = admin-1 region with most weight
    use `dw', clear
    gen region = substr(dist, 1, 4)
    collapse (sum) w, by(domain region)
    gsort domain -w region
    by domain: keep if _n == 1
    keep domain region
    tempfile reg
    save `reg'

    use `grp', clear
    merge 1:1 gid using `rain', keep(master match) nogen
    merge 1:1 gid using `fat', keep(master match) nogen
    gen log_fat = ln(1 + cond(missing(tot), 0, tot))
    summarize rain_z, meanonly
    replace rain_z = r(mean) if missing(rain_z)
    merge m:1 domain using `reg', keep(master match) nogen
    keep if year >= 2015
    summarize rain12_z, meanonly
    replace rain12_z = r(mean) if missing(rain12_z)

*** ------------------------------------------------------------ food prices (WFP), last 3 months
*** Retail prices of sorghum and maize (cereal) and goats, in US$; log price relative to its market x commodity
*** mean, averaged by region and month. A domain-round takes the weighted mean over its regions of the average
*** over the 3 months to the survey. Missing values: the year's mean, else 0.
    save `grp', replace
    import delimited using "$RAW/prices/wfp_som.csv", clear encoding("utf-8") varnames(1) stringcols(_all) bindquote(strict)
    drop if substr(date, 1, 1) == "#"
    destring usdprice, replace force
    keep if pricetype == "Retail" & usdprice > 0 & !missing(usdprice)
    merge m:1 admin1 using `wfpreg', keep(master match) nogen keepusing($PRICE_REGION)
    rename $PRICE_REGION reg
    gen good = cond(inlist(commodity, "Sorghum (red)", "Sorghum (white)", "Maize (white)"), "cereal", ///
        cond(commodity == "Livestock (Goat)", "goat", ""))
    keep if good != "" & reg != ""
    gen lp = ln(usdprice)
    egen mlp = mean(lp), by(market commodity)
    replace lp = lp - mlp
    gen tp = mofd(date(substr(date, 1, 10), "YMD"))
    collapse (mean) lp, by(good reg tp)
    save `price'
    use `dw', clear
    gen reg = substr(dist, 1, 4)
    collapse (sum) w, by(domain reg)
    tempfile rw2
    save `rw2'
    use `grp', clear
    keep gid domain t year
    joinby domain using `rw2'
    joinby reg using `price'
    keep if tp > t - 3 & tp <= t
    collapse (mean) lp (first) w year, by(gid good reg)
    gen wlp = w * lp
    collapse (sum) wlp w (first) year, by(gid good)
    gen lp_ = wlp / w
    keep gid good lp_
    reshape wide lp_, i(gid) j(good) string
    tempfile lp
    save `lp'
    use `grp', clear
    merge 1:1 gid using `lp', keep(master match) nogen
    foreach g in cereal goat {
        egen ym = mean(lp_`g'), by(year)
        gen lp_`g'_f = cond(!missing(lp_`g'), lp_`g', cond(!missing(ym), ym, 0))
        drop ym lp_`g'
        rename lp_`g'_f lp_`g'
    }

    sort gid
    export delimited domain ptype season_id season_type year post region population_group gam sam muac_gam cdr u5dr ///
        rain_z rain12_z log_fat lp_cereal lp_goat using "$DATA/panel.csv", replace
