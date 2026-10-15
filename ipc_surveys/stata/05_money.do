* 05_money.do
* Where the money goes (paper sections 1, 7 and 8; code/85, 86, 87, 89).
*   A. Humanitarian funding by cluster, 2015-2024 (OCHA FTS)
*   B. What the system measures: IPC/CH classifications vs public mortality surveys, 2022-2025
*   C. Within Somalia and Nigeria: which information predicts where aid goes (out of sample), the
*      horse race between and within locations (equation 4), and how much aid would have to move
*   D. Across countries: funding against Phase 3+ people, under-five deaths and battle deaths

do _setup.do
cap log close
log using "$OUT/05_money.log", replace text

* ============================================================== A. funding by cluster
import delimited using "$DATA/fts_cluster.csv", clear varnames(1)
qui summarize year
res ftsYearZero r(min)
res ftsYearOne r(max)
qui summarize funding
local tot = r(sum)
qui summarize funding if !inlist(cluster, "Not specified", "Multi-sector", "Other")
local tagged = r(sum)
foreach c in "Food Security" "Health" "Water Sanitation Hygiene" "Nutrition" {
    local t = cond("`c'" == "Food Security", "Food", cond("`c'" == "Health", "Health", ///
              cond("`c'" == "Nutrition", "Nutrition", "Wash")))
    qui summarize funding if cluster == "`c'"
    res fts`t' 100 * r(sum) / `tot'
    res fts`t'Tag 100 * r(sum) / `tagged'
}
qui summarize funding if inlist(cluster, "Not specified", "Multi-sector")
res ftsUntagged 100 * r(sum) / `tot'

* ============================================================== B. what the system measures
res sysYearZero 2022                               // the window counted (2022-2025)
res sysYearOne 2025
import delimited using "$DATA/system_ipc.csv", clear varnames(1) stringcols(_all)
destring year, replace
keep if inrange(year, 2022, 2025)
duplicates drop country date level1 area, force
local n_ipc = _N
import delimited using "$DATA/system_ch.csv", clear varnames(1) stringcols(_all)
destring reference_year, replace
keep if inrange(reference_year, 2022, 2025)
duplicates drop adm0_name adm1_name adm2_name adm3_name exercise_code reference_year, force
res sysIpc `n_ipc'
res sysCh _N
res sysClass `n_ipc' + _N
import delimited using "$DATA/system_smart.csv", clear varnames(1)
keep if inrange(year, 2022, 2025)
res sysMort _N
qui tab country
res sysMortCountries r(r)

* ============================================================== C. Somalia and Nigeria
import delimited using "$DATA/aidneed.csv", clear varnames(1) case(preserve)
egen uid = group(country unit)
egen pid = group(country period)
foreach v in need_p3 fews_cs fews_fc rain_z rain12_z log_fat lp_cereal gam sam cdr u5dr usd partners reach pop {
    cap destring `v', replace force
}
local scale_usd 1
local scale_partners 100000
local scale_reach 1000
local i_phase need_p3 fews_cs fews_fc
local i_trig rain_z rain12_z log_fat lp_cereal
local i_surv gam sam cdr u5dr

foreach cty in Somalia Nigeria {
    local C = cond("`cty'" == "Somalia", "Som", "Nga")
    foreach aid in usd partners reach {
        local A = cond("`aid'" == "usd", "Usd", cond("`aid'" == "partners", "Prt", "Rch"))
        qui count if country == "`cty'" & !missing(`aid')
        if r(N) == 0 continue                       // e.g. no people-reached data for Nigeria
        * --- 1. out-of-sample prediction of each location's share of aid within the season
        preserve
            keep if country == "`cty'" & !missing(`aid', pop, need_p3, fews_cs, fews_fc, rain_z, rain12_z, log_fat, ///
                    gam, cdr, u5dr) & pop > 0
            qui count
            local n = r(N)
            qui tab pid
            local np = r(r)
            if `n' >= 30 & `np' >= 3 {
                qui count if !missing(lp_cereal)
                if r(N) / _N > 0.5 {
                    qui summarize lp_cereal
                    replace lp_cereal = r(mean) if missing(lp_cereal)
                }
                else replace lp_cereal = 0
                qui summarize sam
                replace sam = r(mean) if missing(sam)
                gen double y = log(1 + `aid' / pop * `scale_`aid'')
                gen double lpop = log(pop)
                foreach v in y need_p3 fews_cs fews_fc rain_z rain12_z log_fat lp_cereal gam sam cdr u5dr {
                    bysort pid: egen double m_ = mean(`v')
                    replace `v' = `v' - m_
                    drop m_
                }
                res ar`C'`A'N _N
                res ar`C'`A'Periods `np'
                qui tab uid
                res ar`C'`A'Units r(r)
                loso y lpop, fold(pid) sst0
                res ar`C'`A'Base r(r2)
                loso y lpop `i_phase', fold(pid) sst0
                res ar`C'`A'Phase r(r2)
                loso y lpop `i_trig', fold(pid) sst0
                res ar`C'`A'Trig r(r2)
                loso y lpop `i_phase' `i_trig', fold(pid) sst0
                res ar`C'`A'PhaseTrig r(r2)
                loso y lpop `i_surv', fold(pid) sst0
                res ar`C'`A'Surv r(r2)
                loso y lpop `i_surv' `i_trig', fold(pid) sst0
                res ar`C'`A'SurvTrig r(r2)
            }
        restore
        * --- 2. horse race, between locations (season-demeaned) and within locations (location + season effects)
        preserve
            keep if country == "`cty'" & !missing(`aid', pop, need_p3, gam, cdr, u5dr) & pop > 0
            if _N >= 30 {
                gen double y = log(1 + `aid' / pop * `scale_`aid'')
                gen double lpop = log(pop)
                * between: everything demeaned by season, need and outcomes then standardized
                foreach v in y need_p3 gam cdr u5dr {
                    bysort pid: egen double m_ = mean(`v')
                    gen double b_`v' = `v' - m_
                    drop m_
                }
                bysort pid: egen double m_ = mean(lpop)
                foreach v in need_p3 gam cdr u5dr {
                    zstd zb_`v' = b_`v'
                }
                regress b_y lpop zb_need_p3 zb_gam zb_cdr zb_u5dr, vce(cluster uid)
                foreach v in need_p3 gam cdr u5dr {
                    local V = cond("`v'" == "need_p3", "Pthree", cond("`v'" == "gam", "Gam", cond("`v'" == "cdr", "Cdr", "Ufive")))
                    res hr`C'`A'`V' _b[zb_`v']
                    res hr`C'`A'`V'Se _se[zb_`v']
                }
                * within
                qui tab uid
                if r(r) >= 10 {
                    foreach v in need_p3 gam cdr u5dr {
                        zstd zw_`v' = `v'
                    }
                    regress y lpop zw_need_p3 zw_gam zw_cdr zw_u5dr i.uid i.pid, vce(cluster uid)
                    foreach v in need_p3 gam cdr u5dr {
                        local V = cond("`v'" == "need_p3", "Pthree", cond("`v'" == "gam", "Gam", cond("`v'" == "cdr", "Cdr", "Ufive")))
                        res hrW`C'`A'`V' _b[zw_`v']
                        res hrW`C'`A'`V'Se _se[zw_`v']
                    }
                }
            }
        restore
        * --- 3. share of aid that would have to move to match each need measure (average over seasons)
        preserve
            keep if country == "`cty'" & !missing(`aid', pop)
            gen double deaths = cdr * pop * 182.5 / 1e4
            gen double u5deaths = u5dr * pop * 0.19 * 182.5 / 1e4
            gen double maln = gam / 100 * pop * 0.19
            gen double p3 = need_p3 * pop
            bysort pid: egen double tot_aid = total(`aid')
            bysort pid: gen n_p = _N
            keep if tot_aid > 0 & n_p >= 4
            foreach need in p3 deaths u5deaths maln pop {
                local N = cond("`need'" == "p3", "Pthree", cond("`need'" == "deaths", "Deaths", ///
                          cond("`need'" == "u5deaths", "Ufive", cond("`need'" == "maln", "Maln", "Pop"))))
                gen byte ok = !missing(`need')
                bysort pid: egen n_ok = total(ok)
                bysort pid: egen double s_aid = total(cond(ok, `aid', .))
                bysort pid: egen double s_need = total(cond(ok, `need', .))
                gen double ad = abs(`aid' / s_aid - `need' / s_need) if ok & n_ok >= 4 & s_need > 0
                bysort pid: egen double D = total(ad / 2)
                bysort pid: egen byte valid = max(!missing(ad))
                egen byte tagp = tag(pid)
                qui summarize D if tagp & valid
                if r(N) > 0 res dis`C'`A'`N' 100 * r(mean)
                drop ok n_ok s_aid s_need ad D valid tagp
            }
        restore
    }
}

* ============================================================== D. across countries
import delimited using "$DATA/xc_aid.csv", clear varnames(1)
res xcN _N
qui tab iso3
res xcCountries r(r)
qui summarize year
res xcYearZero r(min)
res xcYearOne r(max)
* share of funding that would have to move between countries, by year, averaged
foreach v in p3 u5deaths battle pop {
    local N = cond("`v'" == "p3", "Pthree", cond("`v'" == "u5deaths", "Ufive", cond("`v'" == "battle", "Battle", "Pop")))
    bysort year: egen double sf = total(funding)
    bysort year: egen double sv = total(`v')
    gen double ad = abs(funding / sf - `v' / sv) / 2
    bysort year: egen double D = total(ad)
    egen byte ty = tag(year)
    qui summarize D if ty
    res xcDis`N' 100 * r(mean)
    drop sf sv ad D ty
}
* within-year regression of log funding (all variables demeaned by year), clustered by country
gen double y = log(funding)
gen double l_p3 = log(p3)
gen double l_u5deaths = log(u5deaths)
gen double l_pop = log(pop)
gen double l_battle = log(1 + battle)
egen cid = group(iso3)
foreach v in y l_p3 l_u5deaths l_pop l_battle {
    bysort year: egen double m_ = mean(`v')
    replace `v' = `v' - m_
    drop m_
}
regress y l_pop l_p3 l_u5deaths l_battle, vce(cluster cid)
res xcElastPthree _b[l_p3]
res xcElastPthreeSe _se[l_p3]
res xcElastUfive _b[l_u5deaths]
res xcElastUfiveSe _se[l_u5deaths]
res xcElastBattle _b[l_battle]
res xcElastBattleSe _se[l_battle]
loso y l_pop, fold(year) sst0
res xcRtwoPop r(r2)
loso y l_pop l_p3, fold(year) sst0
res xcRtwoPthree r(r2)
loso y l_pop l_u5deaths, fold(year) sst0
res xcRtwoUfive r(r2)
loso y l_pop l_battle, fold(year) sst0
res xcRtwoBattle r(r2)
loso y l_pop l_p3 l_u5deaths l_battle, fold(year) sst0
res xcRtwoAll r(r2)

res_save results_05
log close
