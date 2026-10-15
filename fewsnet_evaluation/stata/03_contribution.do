* 03_contribution.do
* Does FEWS NET know something others don't?  (paper Section 6, Table 2, Figures 5-6; Appendix B)
*
* Reproduces code/33_fewsnet_contribution.py and code/32_forecast_value.py as used in the paper
* (contribution(), money(), predictable() and the masking test in appendix() of 40_paper.py).
*
* The world without FEWS NET is a gradient-boosted prediction, cross-fitted by year, from rainfall,
* conflict, prices, country and season ("raw"), optionally plus the latest Cadre Harmonise / IPC
* analysis ("raw + IPC"). Those predictions stay in Python (code/export_stata/value.py); here:
*   1. AUCs for areas tipping into Crisis in the next independent analysis, without and with
*      FEWS NET (roctab on the exported out-of-sample predictions)
*   2. Table 2: next CH/IPC Crisis+ on the baseline's own prediction and FEWS NET's contribution
*      (signal minus its baseline prediction), country x round FE, clustered by country
*   3. Money: funding over the next 6 months on the predictable part and the contribution
*   4. What the baseline captures (predictable())
*   5. Masking test (Appendix B): is FEWS NET's added judgment borne out less often where
*      funding then rose more than usual?
* Standard errors follow the Python convention (pyse in _setup.do) for the funding regressions;
* elsewhere the fixed effects are nested in the clusters and the two conventions agree.

do _setup.do
cap log close
log using "$OUT/03_contribution.log", replace text


* ============================================================================
* 1-2. Accuracy against the next independent analysis (areas not in Crisis at the last one)
* ============================================================================
import delimited using "$DATA/contrib_ipc_areas.csv", clear
keep if ipc_last3 == 0
* suffix r = raw data baseline (columns 1-3 of Table 2), i = raw data + latest CH/IPC (columns 4-6)
local j = 0
foreach bl in r i {
    local k = cond("`bl'" == "r", "Raw", "RawIPC")
    preserve
        keep if !missing(q_`bl', qf_`bl')
        roctab ipc3 q_`bl'
        res auc`k' r(area)
        local a0 = round(r(area), 0.01)
        roctab ipc3 qf_`bl'
        res auc`k'Fews r(area)
        local a1 = round(r(area), 0.01)
        if "`bl'" == "r" {
            res aucRawPct 100 * `a0'
            res aucRawFewsPct 100 * `a1'
            res aucN _N
            quietly count if ipc3 == 1
            res aucEvents r(N)
        }
        * Table 2: current map, forecast, both
        foreach spec in cur fc both {
            local ++j
            local xs = cond("`spec'" == "both", "c_cur3_`bl' c_fc3_`bl'", "c_`spec'3_`bl'")
            reghdfe ipc3 q_`bl' `xs', absorb(cell) vce(cluster iso3)
            foreach t in cur fc {
                cap local b = _b[c_`t'3_`bl']
                if !_rc {
                    res tab_contribution_`t'_c`j'   _b[c_`t'3_`bl']
                    res tab_contribution_`t'se_c`j' _se[c_`t'3_`bl']
                    local T = cond("`t'" == "cur", "Cur", "Fc")
                    if "`spec'" == "both" {
                        res contrib`k'`T'   _b[c_`t'3_`bl']
                        res contrib`k'`T'Se _se[c_`t'3_`bl']
                    }
                }
            }
            res tab_contribution_q_c`j' _b[q_`bl']
            res tab_contribution_n_c`j' e(N)
            res tab_contribution_g_c`j' e(N_clust)
        }
    restore
}


* ============================================================================
* 3. Money: does funding follow FEWS NET's contribution?  (Figure 6B, macros money*)
* ============================================================================
* country x round means of the predictable part and the contribution of the Phase 3+ forecast
import delimited using "$DATA/contrib_panel.csv", clear
collapse (mean) b_fc3 c_fc3 bi_fc3 ci_fc3, by(country_code r)
rename r report_month
tempfile cm
save `cm'
import delimited using "$DATA/val_aid_panel.csv", clear
merge 1:1 country_code report_month using `cm', keep(match) nogenerate
* log funding over the next 6 months, country and round FE, prior 6 months' funding;
* percent change per 10 percentage points = 100 (exp(0.1 b) - 1)
foreach bl in r i {
    local k = cond("`bl'" == "r", "Raw", "RawIPC")
    local pre = cond("`bl'" == "r", "", "i")
    foreach f in all food {
        local F = cond("`f'" == "all", "All", "Food")
        reghdfe f_`f' b`pre'_fc3 c`pre'_fc3 f_`f'_lag, absorb(iso3 round) vce(cluster iso3)
        pyse                                     // Python's standard-error convention (_setup.do)
        foreach t in b c {
            local T = cond("`t'" == "b", "Base", "Contrib")
            local x `t'`pre'_fc3
            res money`k'`F'`T'       100 * (exp(0.1 * _b[`x']) - 1)
            res money`k'`F'`T'Ci_lo  100 * (exp(0.1 * (_b[`x'] - 1.96 * _se[`x'])) - 1)
            res money`k'`F'`T'Ci_hi  100 * (exp(0.1 * (_b[`x'] + 1.96 * _se[`x'])) - 1)
        }
    }
}


* ============================================================================
* 4. What does the raw-data baseline capture?  (predictable())
* ============================================================================
import delimited using "$DATA/contrib_panel.csv", clear
keep if !missing(b_fc3)
gen cm = country_code + "_" + string(real(substr(r, 6, 2)))
* share of the baseline's variance explained by country x calendar month alone
bysort cm: egen fit = mean(b_fc3)
egen mb = mean(b_fc3)
gen double e2 = (b_fc3 - fit)^2
gen double t2 = (b_fc3 - mb)^2
quietly summarize e2
local ssr = r(sum)
quietly summarize t2
res predCountrySeason 100 * (1 - `ssr' / r(sum))
* beyond country and season, how much of the forecast's variation do the shocks pick up?
bysort cm: egen ffit = mean(fc3)
gen wb = b_fc3 - fit
gen wf = fc3 - ffit
correlate wb wf
res predShocksWithin 100 * r(rho)^2
* country x round means: spread of the predictable part and of FEWS NET's contribution
collapse (mean) b_fc3 c_fc3, by(country_code r)
foreach v in b c {
    local k = cond("`v'" == "b", "Base", "Contrib")
    quietly summarize `v'_fc3
    res pred`k'Sd r(sd)
    bysort country_code: egen m_`v' = mean(`v'_fc3)
    gen w_`v' = `v'_fc3 - m_`v'
    quietly summarize w_`v'
    res pred`k'SdWithin r(sd)
}


* ============================================================================
* 5. Masking test (Appendix B, 32_forecast_value.py part 4)
* ============================================================================
* funding surprise: next-6-month funding net of country and round effects and prior funding
import delimited using "$DATA/fv_panel.csv", clear
collapse (mean) pub3, by(country_code r)
rename r report_month
save `cm', replace
import delimited using "$DATA/val_aid_panel.csv", clear
merge 1:1 country_code report_month using `cm', keep(match) nogenerate
encode iso3, gen(iso3_n)
encode round, gen(round_n)
regress f_all f_all_lag i.iso3_n i.round_n
predict fund_surprise, residuals
* terciles, cut points as pandas qcut (linear interpolation between order statistics)
sort fund_surprise
quietly count if !missing(fund_surprise)
local n = r(N)
foreach q in 1 2 {
    local h = `q' / 3 * (`n' - 1) + 1
    local lo = floor(`h')
    local e`q' = fund_surprise[`lo'] + (`h' - `lo') * (fund_surprise[`lo' + 1] - fund_surprise[`lo'])
}
gen fs_t = cond(fund_surprise <= `e1', 1, cond(fund_surprise <= `e2', 2, 3)) if !missing(fund_surprise)
keep country_code report_month fund_surprise fs_t
rename report_month r
save `cm', replace

import delimited using "$DATA/fv_panel.csv", clear
merge m:1 country_code r using `cm', keep(match) nogenerate
* added judgment borne out (coefficient on added3), by tercile of the funding surprise;
* a3 = Crisis+ on the next map as mapped, n3 = by need (+1 phase if flagged as held up by aid)
foreach y in a3 n3 {
    local k = cond("`y'" == "a3", "Mapped", "Need")
    foreach t in 1 3 {
        local T = cond(`t' == 1, "Low", "High")
        reghdfe `y' pub3 added3 if fs_t == `t', absorb(cell) vce(cluster iso3)
        res mask`k'`T' _b[added3]
    }
}
gen ax = added3 * fund_surprise
reghdfe a3 pub3 added3 ax, absorb(cell) vce(cluster iso3)
res maskInter   _b[ax]
res maskInterSe _se[ax]

res_save results_03
log close
