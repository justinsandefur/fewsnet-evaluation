* 06_bounds.do
* Could aid be hiding the phases' value? (paper section 9, equation 5, Figure 9; code/90_aid_bounds.py)
* Counterfactual outcomes without aid add back the deaths and malnutrition aid would have averted at an
* assumed cost per death c; the horse race of 04 is rerun on them.
*   dose:  all humanitarian aid to Somalia (A per person per six months) allocated in proportion to the IPC
*          Phase 3+ share (worst case for the paper's argument); half of averted deaths under five (share of
*          population 0.19); ten cases of acute malnutrition averted per death
*   flag:  one phase's worth of outcome added in FEWS NET's "!" areas

do _setup.do
cap log close
log using "$OUT/06_bounds.log", replace text

* national aid per person per six months, median over years (as in Python)
import delimited using "$DATA/bounds_national.csv", clear varnames(1)
gen double nat = fts_usd / pop / 2
qui summarize nat, detail
res bdNatPc r(p50)

import delimited using "$DATA/bounds_panel.csv", clear varnames(1) case(preserve)
encode ptype, gen(pt)
egen dom = group(domain)
qui summarize flag
res bdFlag 100 * r(mean)
foreach v in gam cdr u5dr {
    gen double obs_`v' = `v'
}
replace aid_pc = 0 if missing(aid_pc)
replace flag = 0 if missing(flag)
sort dom t

* horse race on the current gam/cdr/u5dr (which may be counterfactual): R2 for phases, triggers, previous survey
cap program drop horse
program horse
    args tag
    foreach y in gam cdr u5dr {
        local Y = cond("`y'" == "gam", "Gam", cond("`y'" == "cdr", "Cdr", "Ufive"))
        qui by dom: gen double L_`y' = `y'[_n - 1]
        qui gen byte s_ = !missing(`y', need_p3, fews_cs, fews_fc, L_`y', L_morbidity, L_measles, ///
                                   rain_z, rain12_z, log_fat, lp_cereal, lp_goat)
        loso `y' i.pt deyr need_p3 fews_cs fews_fc if s_, fold(season_rank)
        global r_`Y'`tag'_Phase = r(r2)
        loso `y' i.pt deyr rain_z rain12_z log_fat lp_cereal lp_goat if s_, fold(season_rank)
        global r_`Y'`tag'_Trig = r(r2)
        loso `y' i.pt deyr L_`y' L_morbidity L_measles if s_, fold(season_rank)
        global r_`Y'`tag'_Last = r(r2)
        drop L_`y' s_
    }
end

* ---- dose version
local costs 0 100000 50000 20000 10000 5000 2500 1000 500 250        // 0 = aid does nothing
local k = 0
foreach c of local costs {
    local ++k
    replace gam = obs_gam
    replace cdr = obs_cdr
    replace u5dr = obs_u5dr
    if `c' > 0 {
        replace cdr = obs_cdr + aid_pc / `c' * 1e4 / 182.5
        replace u5dr = obs_u5dr + 0.5 * aid_pc / `c' / 0.19 * 1e4 / 182.5
        replace gam = obs_gam + 100 * (aid_pc / (`c' / 10)) / 0.19
    }
    horse c`k'
}
* record the no-effect, $5,000 and $1,000 cases; find the highest cost at which phases match each rival
foreach Y in Gam Cdr Ufive {
    foreach pair in "1 None" "6 Fivek" "8 Onek" {
        local kk : word 1 of `pair'
        local nm : word 2 of `pair'
        foreach L in Phase Trig Last {
            res bd`Y'`nm'`L' ${r_`Y'c`kk'_`L'}
        }
    }
    foreach R in Last Trig {
        local brk = .
        local k = 0
        foreach c of local costs {
            local ++k
            if missing(`brk') & ${r_`Y'c`k'_Phase} >= ${r_`Y'c`k'_`R'} local brk = cond(`c' == 0, ., `c')
        }
        if !missing(`brk') res bdBreak`Y'`R' `brk'
    }
}

* ---- FEWS NET flag version: k per phase from the within-zone estimate (W) and the IPC bands (B)
foreach v in W B {
    replace gam = obs_gam + cond("`v'" == "W", 0.8, 5) * flag
    replace cdr = obs_cdr + cond("`v'" == "W", 0.12, 0.45) * flag
    replace u5dr = obs_u5dr + cond("`v'" == "W", 0.25, 1) * flag
    horse flag`v'
    foreach Y in Gam Cdr Ufive {
        foreach L in Phase Trig Last {
            res bd`Y'Flag`v'`L' ${r_`Y'flag`v'_`L'}
        }
    }
}

res_save results_06
log close
