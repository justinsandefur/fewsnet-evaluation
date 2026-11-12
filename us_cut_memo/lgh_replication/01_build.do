*** 01_build.do: construct the panel used for analysis: exposure by district, then by survey domain

*** US-funded share: mean over 2024 partner cells (organisation x sector), u, the unit's US-funded share
*** (from the 3W donor field; UN agencies at their FTS US share). "_obs" drops units with imputed u.
    import delimited using data/units2024.csv, clear
    gen u_obs = u if imputed == "False"
    collapse (mean) us_share = u us_share_obs = u_obs, by(dist)
    tempfile us
    save `us'

    import delimited using data/districts.csv, clear
    merge 1:1 dist using `us', nogen
    gen region = substr(dist, 1, 4)

*** Agencies lost = 1 - partners present Apr-Oct 2025 / Apr-Oct 2024
    gen loss = 1 - cond(missing(partners25), 0, partners25) / partners24

*** Aid dependence = mean of three standardized measures (US$, people reached, and partners -- each logged, per resident, 2024)
    foreach v in usd_pc reach_pc partners_pc {
        quietly summarize `v' if `v' > 0
        gen l_`v' = ln(`v' + r(min) / 2)
        egen s_`v' = std(l_`v')
    }
    gen aid_dep = (s_usd_pc + s_reach_pc + s_partners_pc) / 3
    drop l_* s_*
    save "$OUT/districts.dta", replace

*** Domain exposure = pop-weighted mean of districts in domain (ignoring missing values)
    import delimited using data/domain_weights.csv, clear
    merge m:1 dist using "$OUT/districts.dta", keep(match master) nogen keepusing(us_share us_share_obs loss aid_dep)
    foreach v in us_share us_share_obs loss aid_dep {
        gen wx_`v' = w * `v'
        gen w_`v' = w * !missing(`v')
    }
    collapse (sum) wx_* w_*, by(domain)
    foreach v in us_share us_share_obs loss aid_dep {
        gen `v' = wx_`v' / w_`v' if w_`v' > 0
    }
    keep domain us_share us_share_obs loss aid_dep
    tempfile dom
    save `dom'

*** Panel: 1 row per survey domain x round
    import delimited using data/panel.csv, clear
    merge m:1 domain using `dom', keep(match master) nogen
    egen first = tag(domain)
    egen in_s = max(year >= $START), by(domain)

*** Aid dependence standardized across domains: "high" = above the median US-funded share within domain type
    quietly summarize aid_dep if first
    gen z_index = (aid_dep - r(mean)) / r(sd)
    egen med = median(cond(first, us_share, .)), by(ptype)
    gen high = us_share > med
    drop med

*** Fixed effects and time controls
    egen dom = group(domain)
    egen type_round = group(ptype season_id)
    egen round_id = group(season_id)
    gen gu25 = season_id == "Gu 2025"
    gen deyr25 = season_id == "Deyr 2025"
    gen gu26 = season_id == "Gu 2026"
    gen t = year + 0.5 * (season_type == "Deyr")
    save "$OUT/panel.dta", replace
