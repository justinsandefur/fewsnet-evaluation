* 09_subnational.do
* Does aid follow FEWS NET within Somalia and Sudan, and do its aid flags mark where aid went?
* (paper section on sub-national aid and the Somalia / Sudan table; code/63_subnational_models.py)
*
* District x FEWS NET period panels, 2014-2024. Aid = pooled-fund (CBPF) food security, nutrition and
* cash allocations, asinh US$. Fixed effects for district and period; SEs clustered by district.
*   A   allocation: aid on the share of the district forecast in Crisis+ (fc3), controlling for the
*       current map (cs3); dynamic (lagged aid), Anderson-Hsiao (first differences, lag instrumented
*       with the second lag), predictable part vs FEWS NET's contribution, placebo (next round's forecast)
*   A2  people reached (annual, 3W) on the forecast
*   B   aid flags on aid, partner presence and people reached; flag persistence
*   C   shift-share instrument (base-period share x asinh fund envelope): first-stage F only
* Singletons dropped once per fixed effect in turn (as in Python ols(); not in the IV).

do _setup.do
cap log close
log using "$OUT/09_subnational.log", replace text

* fe_reg Y XS, fes(...)  -- Python ols(): singleton rule, clustered by district, variance scaled by
* G/(G-1) only (reghdfe's (N-1)/(N-K) factor undone)
cap program drop fe_reg
program fe_reg, eclass
    syntax varlist [if], fes(string)
    gettoken y xs : varlist
    marksample touse
    tempvar n
    foreach f of local fes {
        bys `f': egen `n' = total(`touse')
        replace `touse' = 0 if `n' <= 1
        drop `n'
    }
    reghdfe `y' `xs' if `touse', absorb(`fes') vce(cluster dist) keepsingletons tolerance(1e-12)
    tempname V
    matrix `V' = e(V) * (e(N) - e(df_m) - e(df_a) - 1) / (e(N) - 1)
    ereturn repost V = `V'
end

* tabcell ROW ISO VAR [MACRO]: record a table cell (coefficient and SE) and optionally the paper's macro
cap program drop tabcell
program tabcell
    args row ik v mac
    res tab_subnat_`row'_`ik'    _b[`v']
    res tab_subnat_`row'_`ik'_se _se[`v']
    if "`mac'" != "" {
        res `mac'   _b[`v']
        res `mac'Se _se[`v']
    }
end

foreach iso in SOM SDN {
    local t  = cond("`iso'" == "SOM", "So", "Sd")
    local ik = cond("`iso'" == "SOM", "so", "sd")

    * ========================================================================
    * District x period panel (Python prep())
    * ========================================================================
    import delimited using "$DATA/sub_`iso'.csv", clear
    ym t
    keep if inrange(year(dofm(t)), 2014, 2024)
    encode key, gen(dist)
    sort dist t
    gen aid_usd = cbpf_fs + cbpf_nut + cbpf_cash
    gen aid = asinh(aid_usd)
    gen aid_any = aid_usd > 0 & !missing(aid_usd)
    by dist: gen aid_l1 = aid[_n-1]
    by dist: gen aid_l2 = aid[_n-2]
    by dist: gen aid_f1 = aid[_n+1]
    by dist: gen fc3_f1 = fc3[_n+1]
    gen d_aid    = aid - aid_l1
    gen d_aid_l1 = aid_l1 - aid_l2
    by dist: gen d_fc3 = fc3 - fc3[_n-1]
    by dist: gen d_cs3 = cs3 - cs3[_n-1]
    gen tt = t
    * shift-share instrument: district share of aid in the first six periods x asinh(fund envelope)
    egen tg = group(t)
    gen in_base = tg <= 6
    bys dist: egen base = total(aid_usd * in_base)
    egen base_all = total(aid_usd * in_base)
    gen share = base / base_all
    gen Z = share * asinh(envelope)
    bys t: egen nat_num = total(cs3 * pop)
    bys t: egen nat_den = total(pop)
    gen share_x_nat = share * nat_num / nat_den
    * partners present (food security + nutrition), missing if neither is recorded
    gen pres = cond(missing(pres_fs), 0, pres_fs) + cond(missing(pres_nut), 0, pres_nut) if !missing(pres_fs) | !missing(pres_nut)
    sort dist t

    quietly levelsof dist
    res sub`t'Districts r(r)
    res tab_subnat_districts_`ik' r(r)
    quietly levelsof t
    res sub`t'Periods r(r)
    res tab_subnat_periods_`ik' r(r)
    summarize aid_any, meanonly
    res sub`t'AidShare 100 * r(mean)

    * ========================================================================
    * A. Allocation
    * ========================================================================
    quietly fe_reg aid fc3 cs3, fes(dist tt)
    tabcell 1 `ik' fc3 sub`t'Fc
    quietly fe_reg aid fc3 cs3 aid_l1, fes(dist tt)
    tabcell 2 `ik' fc3
    quietly fe_reg aid c_fc3 b_fc3 cs3, fes(dist tt)
    tabcell 4 `ik' b_fc3 sub`t'Base
    tabcell 5 `ik' c_fc3 sub`t'Contrib
    quietly fe_reg aid fc3 cs3 fc3_f1, fes(dist tt)
    tabcell 6 `ik' fc3_f1 sub`t'Plac
    quietly fe_reg aid_any fc3 cs3, fes(dist tt)
    tabcell 7 `ik' fc3 sub`t'Any
    res sub`t'AnyPct 100 * _b[fc3]
    quietly fe_reg pres fc3 cs3, fes(dist tt)
    tabcell 8 `ik' fc3 sub`t'Pres

    * Anderson-Hsiao: first differences, period effects, lagged change in aid instrumented by aid two
    * periods back. Python scales the cluster variance by G/(G-1); ivregress (without small) does not.
    quietly ivregress 2sls d_aid d_fc3 d_cs3 i.tt (d_aid_l1 = aid_l2), vce(cluster dist)
    res tab_subnat_3_`ik'    _b[d_fc3]
    res tab_subnat_3_`ik'_se _se[d_fc3] * sqrt(e(N_clust) / (e(N_clust) - 1))

    * ========================================================================
    * B. Aid flags
    * ========================================================================
    quietly fe_reg flag aid cs3 phase, fes(dist tt)
    tabcell 10 `ik' aid sub`t'FlagAid
    quietly fe_reg flag aid_l1 aid aid_f1 cs3 phase, fes(dist tt)
    tabcell 13 `ik' aid_f1
    quietly fe_reg flag_next aid flag cs3 phase, fes(dist tt)
    res sub`t'FlagPersist   _b[flag]
    res sub`t'FlagPersistSe _se[flag]
    quietly fe_reg flag pres cs3 phase if !missing(pres), fes(dist tt)
    tabcell 11 `ik' pres sub`t'FlagPres

    * ========================================================================
    * C. Shift-share IV, base periods dropped: first-stage F (cluster-robust Wald, one instrument)
    * ========================================================================
    preserve
        keep if !in_base & !missing(phase_next, aid, Z, cs3, fc3, share_x_nat)
        quietly reghdfe aid Z cs3 fc3 share_x_nat, absorb(dist tt) vce(cluster dist) keepsingletons tolerance(1e-12)
        local F = (_b[Z] / _se[Z])^2 * (e(N) - 1) / (e(N) - e(df_m) - e(df_a) - 1)
        display as text "`iso' first-stage F = " as result %5.1f `F'
        res sub`t'IvF `F'
    restore

    * ========================================================================
    * District x year panel: people reached (3W), annual aid flag share
    * ========================================================================
    import delimited using "$DATA/sub_`iso'_annual.csv", clear
    encode key, gen(dist)
    gen yy = year
    gen reach = asinh(reach_fs + reach_nut)
    gen reach_pc = (reach_fs + reach_nut) / pop if pop > 0
    * cap at the 99th percentile (linear interpolation between order statistics, as pandas does)
    sort reach_pc
    quietly count if !missing(reach_pc)
    local h = (r(N) - 1) * 0.99 + 1
    local q99 = reach_pc[floor(`h')] + (`h' - floor(`h')) * (reach_pc[floor(`h') + 1] - reach_pc[floor(`h')])
    replace reach_pc = min(reach_pc, `q99') if !missing(reach_pc)
    quietly fe_reg reach fc3 cs3, fes(dist yy)
    tabcell 9 `ik' fc3 sub`t'Reach
    quietly fe_reg flag reach cs3 phase, fes(dist yy)
    tabcell 12 `ik' reach sub`t'FlagReach
    quietly fe_reg flag reach_pc cs3 phase, fes(dist yy)
    res sub`t'FlagReachPc   _b[reach_pc]
    res sub`t'FlagReachPcSe _se[reach_pc]
    local bpc = _b[reach_pc]
    summarize reach_pc
    res sub`t'FlagReachSd 100 * `bpc' * r(sd)
    summarize flag, meanonly
    res sub`t'FlagMean 100 * r(mean)
}

res_save results_09
log close
