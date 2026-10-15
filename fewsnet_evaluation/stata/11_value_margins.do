* 11_value_margins.do
* FEWS NET's value on two margins, in person-months of Crisis averted (paper Section 8 and
* Appendix H; code/81_allocation_value.py and 82_value_margins.py; macros vm* and env*).
*
* 1. Reallocation. In each country and round a planner holds rations for 30% of the people actually
*    in Phase 3+ and places them greedily by predicted value per ration. Each area has two segments:
*    up to its predicted Phase 3+ population a ration is worth tau + (1 - tau) x s_pred, beyond that
*    (1 - tau) x s_pred. People reached in Crisis = tau x min(x, n_true) + (1 - tau) x x x s_true.
*    tau = 0 (random targeting within areas) or 0.5 (halfway to perfect). s_pred comes from
*    gradient-boosted predictions cross-fitted by year (Python): public information, the same plus
*    FEWS NET, or the actual share (oracle). Value of FEWS NET = reached with FEWS NET - with public,
*    x 4 months per round, per year; scaled to all FEWS NET countries by food funding.
* 2. The envelope. Share of food funding that followed FEWS NET's distinctive information:
*    1 - exp(-b x) (x >= 0) or -(1 - exp(b x)) (x < 0), funding-weighted over country-rounds.

do _setup.do
cap log close
log using "$OUT/11_value_margins.log", replace text

local MONTHS 4
local COVER 0.3
local RATION 22.5                 // US$ per full ration-month: low 20, high 25
local BUDGET 45e6                 // FEWS NET budget: low 35, high 65 million

* ============================================================================
* 1. Reallocation
* ============================================================================
import delimited using "$DATA/vm_areas.csv", clear
gen double y = min(max(ipc_share3, 0), 1)
gen double s_oracle = y
egen a1 = tag(key)
count if a1
res vmAreas r(N)
egen c1 = tag(iso3)
count if c1
res vmCountries r(N)
summarize yr, meanonly
res vmYears_lo r(min)
res vmYears_hi r(max)
drop a1 c1
* country-rounds with at least 3 areas and someone in Phase 3+
gen cell = iso3 + "_" + r
bysort cell: gen n_areas = _N
gen double ny = ipc_pop * y
bysort cell: egen double need = total(ny)
keep if n_areas >= 3 & need > 0
tempfile areas
save `areas'

* greedy allocation by country-round, for each targeting rule and information set
* (results: people in Crisis reached, summed over country-rounds)
cap frame drop S
frame create S str7 targeting str7 info double(reached need) years
foreach t in random half {
    local tau = cond("`t'" == "random", 0, 0.5)
    foreach info in public fews oracle {
        use `areas', clear
        rename yr year
        quietly {
            expand 2
            bysort order: gen seg = _n
            gen double v   = cond(seg == 1, `tau' + (1 - `tau') * s_`info', (1 - `tau') * s_`info')
            gen double cap = cond(seg == 1, ipc_pop * s_`info', ipc_pop - ipc_pop * s_`info')
            gen double negv = -v
            sort cell negv order seg                     // highest value first; ties in the original order
            by cell: gen double before = sum(cap) - cap
            gen double a = cond(v > 0, max(0, min(cap, `COVER' * need - before)), 0)
            collapse (sum) x = a, by(cell order ipc_pop y need year)
            gen double got = `tau' * min(x, ipc_pop * y) + (1 - `tau') * x * y
            collapse (sum) reached = got, by(cell need year)
        }
        egen yt = tag(year)
        count if yt
        local years = r(N)
        summarize reached, meanonly
        local reached = r(sum)
        summarize need, meanonly
        frame post S ("`t'") ("`info'") (`reached') (r(sum)) (`years')
    }
}
* cells, years and need (the same for every allocation)
keep cell need year
gen iso3 = substr(cell, 1, strpos(cell, "_") - 1)
tempfile cells
save `cells'
summarize need, meanonly
local need_pm_year = r(sum) * `MONTHS' / `years'
res vmNeed `need_pm_year' / 1e6

* --- food funding (OCHA FTS): all FEWS NET countries vs the sample -------------------------------
import delimited using "$DATA/vm_countries.csv", clear stringcols(_all)
destring fews, replace
preserve
    keep if fews == 1
    duplicates drop iso2, force
    res vmFewsCountries _N
    keep iso2
    tempfile fewscc
    save `fewscc'
restore
keep if iso3 != ""
keep iso3 iso2
duplicates drop iso3, force
tempfile i32
save `i32'

import delimited using "$DATA/vm_fts.csv", clear stringcols(1 2)
gen year = real(substr(month, 1, 4))
collapse (sum) food, by(iso2 year)
tempfile fts
save `fts'
use `cells', clear
levelsof year, local(yrs)
local yrs : subinstr local yrs " " ",", all
* all FEWS NET countries: mean over years of total food funding
use `fts', clear
merge m:1 iso2 using `fewscc', keep(match) nogenerate
keep if inlist(year, `yrs')
collapse (sum) food, by(year)
summarize food, meanonly
local food_all = r(mean)
* sample country-years (years without funding count as 0)
use `cells', clear
merge m:1 iso3 using `i32', keep(master match) nogenerate
preserve
    * implied coverage: food funding / cost of full rations for everyone in Phase 3+
    drop if iso2 == ""
    collapse (sum) need, by(iso2 year)
    merge 1:1 iso2 year using `fts', keep(master match) nogenerate
    replace food = 0 if missing(food)
    summarize food, meanonly
    local f = r(sum)
    summarize need, meanonly
    local n = r(sum) * `MONTHS'
    res vmCover   100 * `f' / (`n' * 22.5)
    res vmCoverLo 100 * `f' / (`n' * 25)
    res vmCoverHi 100 * `f' / (`n' * 20)
restore
keep iso2 year
duplicates drop
merge 1:1 iso2 year using `fts', keep(match) nogenerate
collapse (sum) food, by(year)
local nyrs : word count `: subinstr local yrs "," " ", all'
summarize food, meanonly
local food_samp = r(sum) / `nyrs'
local scale = `food_all' / `food_samp'
res vmFoodAll    `food_all' / 1e9
res vmFoodSample `food_samp' / 1e9
res vmScale      `scale'

* --- value of FEWS NET's information under the fixed budget --------------------------------------
frame S {
    gen double share = reached / (need * `COVER')
    list, noobs clean
    foreach t in random half {
        local T = cond("`t'" == "random", "Rand", "Half")
        foreach info in public fews oracle {
            summarize reached if targeting == "`t'" & info == "`info'", meanonly
            local `info' = r(mean)
            summarize share if targeting == "`t'" & info == "`info'", meanonly
            local sh_`info' = r(mean)
        }
        local g = (`fews' - `public') * `MONTHS' / `years'          // person-months a year
        local fews_share_`t' = `sh_fews'
        res vm`T'Gain       `g' / 1e6
        res vm`T'GainAll    `g' * `scale' / 1e6
        res vm`T'ShareNeed  100 * `g' / `need_pm_year'
        res vm`T'PctMore    100 * `g' / (`sh_public' * `COVER' * `need_pm_year')
        res vm`T'Pub        100 * `sh_public'
        res vm`T'Fews       100 * `sh_fews'
        res vm`T'OracleGain 100 * (`fews' - `public') / (`oracle' - `public')
        res vm`T'Aid        `g' * `RATION' / 1e6
        res vm`T'AidAll     `g' * `scale' * `RATION' / 1e6
        res vm`T'Ratio      `g' * `RATION' / `BUDGET'
        res vm`T'RatioAll   `g' * `scale' * `RATION' / `BUDGET'
        res vm`T'RatioAllLo `g' * `scale' * 20 / 65e6
        res vm`T'RatioAllHi `g' * `scale' * 25 / 35e6
        res vm`T'CostPm     `BUDGET' / (`g' * `scale')
    }
}

* ============================================================================
* 2. The envelope: food funding that followed FEWS NET's distinctive information
* ============================================================================
import delimited using "$DATA/bc_betas.csv", clear
forvalues i = 1/`=_N' {
    local b_`=attribution[`i']' = beta[`i']
}
res envBeta 10 * `b_env_raw'                                  // percent per 10 points
import delimited using "$DATA/bc_contrib.csv", clear
collapse (mean) c_fc3 ci_fc3, by(country_code r)
tempfile cr
save `cr'
import delimited using "$DATA/vm_aid.csv", clear
rename report_month r
merge 1:1 country_code r using `cr', keep(match) nogenerate
gen double food_usd = exp(f_food) - 1
foreach k in raw ipc {
    local x = cond("`k'" == "raw", "c_fc3", "ci_fc3")
    gen double bx = `b_env_`k'' * `x'
    gen double sym = cond(bx >= 0, 1 - exp(-bx), -(1 - exp(bx))) * food_usd if !missing(bx, food_usd)
    gen double pos = cond(bx >= 0, 1 - exp(-bx), 0) * food_usd if !missing(bx, food_usd)
    gen double den = food_usd if !missing(bx, food_usd)
    foreach v in sym pos den {
        summarize `v', meanonly
        local `v' = r(sum)
    }
    local env_`k' = `sym' / `den'
    local envpos_`k' = `pos' / `den'
    drop bx sym pos den
}
res envShareRaw    100 * `env_raw'
res envShareIpc    100 * `env_ipc'
res envSharePosRaw 100 * `envpos_raw'
* in dollars and person-months: extra money x share of rations reaching people in Crisis (with FEWS NET)
res envUsdLo `env_ipc' * `food_all' / 1e6
res envUsdHi `env_raw' * `food_all' / 1e6
res envPmLo  `env_ipc' * `food_all' / `RATION' * `fews_share_random' / 1e6
res envPmHi  `env_raw' * `food_all' / `RATION' * `fews_share_half' / 1e6

res_save results_11
log close
