* 10_displacement.do
* Is the IPC measuring displacement instead? Somalia, 2016-2023 (paper section 7, Table 2, Appendix
* Figure; code/94_displacement.py). Displacement: UNHCR PRMN records (origin district, reason, numbers).
*   A. districts x survey seasons: correlations with the Phase 3+ share within season; out-of-sample R2
*      (leave one season out) for each outcome; what predicts the Phase 3+ share
*   B. regions x months: household food consumption and coping, rainfall and violence vs departures
*   C. counting the displaced at home (reassignment) and the assumed-death-rate stress test
*   D. displaced settlements: own district's phase, origin districts' phase, number of arrivals

do _setup.do
cap log close
log using "$OUT/10_displacement.log", replace text

* ------------------------------------------------------------ the records
import delimited using "$DATA/prmn_records.csv", clear varnames(1)
res dpRecords _N
qui summarize n
local tot = r(sum)
res dpPeople `tot' / 1e6
qui summarize n if reason == "Drought related"
res dpDroughtShare 100 * r(sum) / `tot'
qui summarize n if reason == "Conflict/Insecurity"
res dpConflictShare 100 * r(sum) / `tot'

* ============================================================ A. districts x seasons
import delimited using "$DATA/disp_district.csv", clear varnames(1) case(preserve)
egen sid = group(period)
egen did = group(unit)
res dpAN _N
qui tab unit
res dpADistricts r(r)
qui tab period
res dpASeasons r(r)
* within-season correlations with the Phase 3+ share
foreach v in need_p3 gam cdr u5dr l_drought_next l_conflict_next l_drought_prev {
    bysort sid: egen double m_ = mean(`v')
    gen double w_`v' = `v' - m_
    drop m_
}
foreach pair in "gam Gam" "cdr Cdr" "u5dr Ufive" "l_drought_next DrNext" "l_conflict_next CoNext" "l_drought_prev DrPrev" {
    local v : word 1 of `pair'
    local K : word 2 of `pair'
    qui corr w_`v' w_need_p3
    res dpCorr`K' r(rho)
}
* out of sample: every variable demeaned by season; log population in every model; leave one season out
preserve
    foreach v in gam cdr u5dr l_drought_next l_conflict_next need_p3 fews_cs fews_fc rain_z rain12_z log_fat {
        bysort sid: egen double m_ = mean(`v')
        replace `v' = `v' - m_
        drop m_
    }
    foreach pair in "gam Gam" "cdr Cdr" "u5dr Ufive" "l_drought_next DrNext" "l_conflict_next CoNext" {
        local y : word 1 of `pair'
        local K : word 2 of `pair'
        loso `y' l_pop, fold(sid) sst0
        res dpR`K'Pop r(r2)
        loso `y' l_pop need_p3, fold(sid) sst0
        res dpR`K'Ipc r(r2)
        loso `y' l_pop fews_cs fews_fc, fold(sid) sst0
        res dpR`K'Fews r(r2)
        loso `y' l_pop rain_z rain12_z log_fat, fold(sid) sst0
        res dpR`K'Trig r(r2)
    }
restore
* what predicts the Phase 3+ share (standardized; between districts with season effects, within with district effects)
foreach v in l_drought_prev l_conflict_prev gam cdr u5dr rain12_z rain_z log_fat {
    zstd z_`v' = `v'
}
local rhs z_l_drought_prev z_l_conflict_prev z_gam z_cdr z_u5dr z_rain12_z z_rain_z z_log_fat l_pop
foreach F in B W {
    if "`F'" == "B" regress need_p3 `rhs' i.sid, vce(cluster did)
    else regress need_p3 `rhs' i.sid i.did, vce(cluster did)
    foreach pair in "l_drought_prev Dr" "l_conflict_prev Co" "gam Gam" "cdr Cdr" "u5dr Ufive" {
        local v : word 1 of `pair'
        local V : word 2 of `pair'
        res dpP`F'`V' 100 * _b[z_`v']
        res dpP`F'`V'Se 100 * _se[z_`v']
    }
}

* ============================================================ B. regions x months
import delimited using "$DATA/disp_region.csv", clear varnames(1) case(preserve)
egen rid = group(reg)
egen qid = group(q)
egen tid = group(t)
res dpBN _N
qui tab reg
res dpBRegions r(r)
qui tab t
res dpBMonths r(r)
gen double per1000 = drought / pop * 1000
qui summarize per1000
res dpBMean r(mean)
* out of sample, leaving one quarter out; within regions: with region effects, scored against region means
cap program drop oosb
program oosb, rclass
    syntax varlist, [within]
    gettoken y xs : varlist
    tempvar pred p e2 d2 base
    qui gen double `pred' = .
    qui levelsof qid, local(qs)
    foreach q of local qs {
        if "`within'" != "" qui regress `y' `xs' i.rid if qid != `q'
        else qui regress `y' `xs' if qid != `q'
        qui predict double `p' if qid == `q', xb
        qui replace `pred' = `p' if qid == `q'
        drop `p'
    }
    if "`within'" != "" qui bysort rid: egen double `base' = mean(`y')
    else {
        qui summarize `y'
        qui gen double `base' = r(mean)
    }
    qui gen double `e2' = (`y' - `pred')^2
    qui gen double `d2' = (`y' - `base')^2
    qui summarize `e2'
    local ssr = r(sum)
    qui summarize `d2'
    return scalar r2 = 1 - `ssr' / r(sum)
end
foreach pair in "y_drought Dr" "y_allmv All" {
    local y : word 1 of `pair'
    local Y : word 2 of `pair'
    foreach set in "Hh fcs rcsi" "Rain rain6 rain12" "Viol lfat3 lfat12" "All fcs rcsi rain6 rain12 lfat3 lfat12" {
        gettoken k xs : set
        oosb `y' `xs'
        res dpB`Y'`k' r(r2)
        oosb `y' `xs', within
        res dpB`Y'`k'W r(r2)
    }
}
foreach v in fcs rcsi rain6 rain12 lfat3 lfat12 {
    zstd z_`v' = `v'
}
regress y_drought z_fcs z_rcsi z_rain6 z_rain12 z_lfat3 z_lfat12 i.rid, vce(cluster rid)
res dpBWFcs _b[z_fcs]
res dpBWFcsSe _se[z_fcs]
res dpBWRain _b[z_rain6]
res dpBWRainSe _se[z_rain6]
regress y_drought z_fcs z_rcsi z_rain6 z_rain12 z_lfat3 z_lfat12 i.rid i.tid, vce(cluster rid)
res dpBWTFcs _b[z_fcs]
res dpBWTFcsSe _se[z_fcs]
res dpBWTRain _b[z_rain6]
res dpBWTRainSe _se[z_rain6]

* ============================================================ C. counting the displaced at home
import delimited using "$DATA/disp_reassign.csv", clear varnames(1) case(preserve)
egen sid = group(season)
res dpCN _N
qui tab dist
res dpCDistricts r(r)
qui tab season
res dpCSeasons r(r)
foreach w in 6 12 {
    local W = cond(`w' == 6, "Six", "Twelve")
    gen double sh`w' = left`w' / pop
    qui summarize sh`w', detail
    res dpCLeftMed`W' 100 * r(p50)
    * 90th percentile, interpolated linearly between order statistics (as pandas does)
    preserve
        qui keep if !missing(sh`w')
        sort sh`w'
        local h = (_N - 1) * 0.9 + 1
        local lo = floor(`h')
        local q = sh`w'[`lo'] + (`h' - `lo') * (sh`w'[min(`lo' + 1, _N)] - sh`w'[`lo'])
    restore
    res dpCLeftNinety`W' 100 * `q'
}
cap program drop wdm
program wdm                                   // demean by season (over non-missing values)
    args v
    tempvar m
    bysort sid: egen double `m' = mean(`v')
    gen double w_`v' = `v' - `m'
end
foreach v in p3 gam cdr u5dr gam_star6 gam_star12 cdr_star6 cdr_star12 u5dr_star6 u5dr_star12 sh12 {
    wdm `v'
}
foreach pair in "gam Gam" "cdr Cdr" "u5dr Ufive" {
    local c : word 1 of `pair'
    local K : word 2 of `pair'
    qui corr w_`c' w_p3 if !missing(`c')
    res dpCStay`K' r(rho)
    foreach w in 6 12 {
        local W = cond(`w' == 6, "Six", "Twelve")
        qui corr w_`c'_star`w' w_p3 if !missing(`c', `c'_star`w')
        res dpCAll`K'`W' r(rho)
    }
}
qui corr w_sh12 w_p3
res dpCLeftCorr r(rho)
* stress test: everyone who left in the past year dies at rate X (per 10,000 per day)
foreach pair in "1 One" "2 Two" "5 Five" "10 Ten" {
    local X : word 1 of `pair'
    local L : word 2 of `pair'
    gen double y_ = (1 - sh12) * cdr + sh12 * `X'
    wdm y_
    qui corr w_y_ w_p3 if !missing(cdr)
    res dpCStress`L' r(rho)
    drop y_ w_y_
}
qui corr w_cdr w_p3 if !missing(cdr)
res dpCStressNone r(rho)

* ============================================================ D. displaced settlements
import delimited using "$DATA/disp_settlements.csv", clear varnames(1) case(preserve)
egen dom = group(domain)
egen sid = group(season)
res dpDN _N
qui tab domain
res dpDSettlements r(r)
qui tab season
res dpDSeasons r(r)
foreach pair in "gam Gam" "cdr Cdr" "u5dr Ufive" {
    local c : word 1 of `pair'
    local K : word 2 of `pair'
    qui corr `c' local_p3
    res dpDOwn`K' r(rho)
    qui corr `c' origin_p3
    res dpDOrigin`K' r(rho)
    qui corr `c' l_arr
    res dpDArr`K' r(rho)
    regress `c' local_p3 origin_p3 l_arr i.sid, vce(cluster dom)
    res dpDArrB`K' _b[l_arr]
    res dpDArrB`K'Se _se[l_arr]
}

res_save results_10
log close
