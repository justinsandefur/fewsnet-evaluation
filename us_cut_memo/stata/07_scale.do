* 07_scale.do
* How many children?  Turning "pp of wasting per unit of exposure" into numbers.  (memo Section 6)
*
* For an exposure with a natural zero -- agency loss: a place that lost no agencies is untreated --
*   extra wasting (pp)  = b (pp per unit of agency loss) x average agency loss (child-weighted)
*   extra children      = extra wasting / 100 x children aged 6-59 months
* with 95% intervals from b +/- 1.96 se. This takes the cross-district estimate literally as a
* national effect. The national prediction gap from 04 (how far wasting ran above what rainfall,
* conflict and prices predict) is the cross-check: unless something else improved nutrition, the
* average effect cannot be much larger than that gap.

do _setup.do
log using "$OUT/07_scale.log", replace text

import delimited using "$DATA/scale_inputs.csv", clear
summarize value if item == "somalia_children_6_59m", meanonly
local kids = r(mean)
summarize value if item == "nigeria_ne_children_u5", meanonly
local kids_nga = r(mean)
res scSomKids `kids' / 1e6
res scNgaKids `kids_nga' / 1e6
display as text "Children 6-59 months, Somalia: " as result %12.0fc `kids'

* children -> program: report one line and record it under the memo's names
capture program drop children
program children
    args tag b se x kids
    local pp = `b' * `x'
    local lo = (`b' - 1.96 * `se') * `x'
    local hi = (`b' + 1.96 * `se') * `x'
    display as text %-14s "`tag'" "  extra wasting " as result %4.1f `pp' as text " pp [" as result %4.1f `lo' ///
        as text ", " as result %4.1f `hi' as text "]  = " as result %9.0fc `pp' / 100 * `kids' as text " children [" ///
        as result %9.0fc `lo' / 100 * `kids' as text ", " as result %9.0fc `hi' / 100 * `kids' as text "]"
    res scSomPp`tag'     `pp'
    res scSomPpLo`tag'   `lo'
    res scSomPpHi`tag'   `hi'
    res scSomKids`tag'   `pp' / 100 * `kids'
    res scSomKidsLo`tag' `lo' / 100 * `kids'
    res scSomKidsHi`tag' `hi' / 100 * `kids'
end


* ============================================================================
* 1. Somalia
* ============================================================================
* average exposure across districts, weighted by population
use "$OUT/som_districts.dta", clear
keep if !missing(us_share, agency_loss)
summarize agency_loss [aw = pop], meanonly
local loss = r(mean)
summarize us_share [aw = pop], meanonly
local us_mean = r(mean)
* US share in the least-exposed tenth of districts (pandas' linear-interpolation percentile)
sort us_share
local pos = 1 + 0.1 * (_N - 1)
local p10 = us_share[floor(`pos')] + (`pos' - floor(`pos')) * (us_share[floor(`pos') + 1] - us_share[floor(`pos')])
res scSomLoss 100 * `loss'
display as text "Average agency loss: " as result %4.1f 100 * `loss' as text "%"

* re-estimate the Gu 2026 and pooled coefficients (per unit of exposure, not per s.d.)
use "$OUT/som_panel.dta", clear
global FE   "i.dom_id i.type_round"
global CTRL "rain_z rain12_z log_fat"
foreach z in agency_loss us_share {
    gen x_gu25_`z' = `z' * gu25
    gen x_deyr25_`z' = `z' * deyr25
    gen x_gu26_`z' = `z' * gu26
}
quietly regress gam x_gu25_agency_loss x_deyr25_agency_loss x_gu26_agency_loss $CTRL $FE, vce(cluster region)
children LossTs `=_b[x_gu26_agency_loss]' `=_se[x_gu26_agency_loss]' `loss' `kids'
quietly regress sam x_gu25_agency_loss x_deyr25_agency_loss x_gu26_agency_loss $CTRL $FE, vce(cluster region)
children LossTsSam `=_b[x_gu26_agency_loss]' `=_se[x_gu26_agency_loss]' `loss' `kids'
gen x_post = agency_loss * post
quietly regress gam x_post $CTRL $FE, vce(cluster region)
children LossPool `=_b[x_post]' `=_se[x_post]' `loss' `kids'
* US reliance: compare the average district with the least-exposed tenth
quietly regress gam x_gu25_us_share x_deyr25_us_share x_gu26_us_share $CTRL $FE, vce(cluster region)
children UsTs `=_b[x_gu26_us_share]' `=_se[x_gu26_us_share]' `=`us_mean' - `p10'' `kids'

* baseline: about 13% of children wasted before the cut
res scSomBaseWasted 0.13 * `kids'
frame results: summarize value if name == "scSomKidsLossTs", meanonly
frame results: local extra = r(mean)
res scSomPctIncLossTs 100 * `extra' / (0.13 * `kids')
display as text "Baseline wasted: " as result %9.0fc 0.13 * `kids' as text "; Gu 2026 estimate adds " ///
    as result %3.0f 100 * `extra' / (0.13 * `kids') as text "%"

* national cross-check: wasting above prediction (from 04)
preserve
    import delimited using "$OUT/results_04.csv", clear
    foreach t in Tv Ts {
        summarize value if name == "scSomPpNat`t'", meanonly
        local nat`t' = r(mean)
    }
restore
res scSomKidsNatTv `natTv' / 100 * `kids'
res scSomKidsNatTs `natTs' / 100 * `kids'
display as text "National excess over prediction: 2025 " as result %4.1f `natTv' as text " pp = " ///
    as result %7.0fc `natTv' / 100 * `kids' as text " children; 2026 " as result %4.1f `natTs' ///
    as text " pp = " as result %7.0fc `natTs' / 100 * `kids' as text " children"


* ============================================================================
* 2. Nigeria (north-east): same calculation with the zone agency-loss estimate
* ============================================================================
import delimited using "$DATA/nga_zones.csv", clear
keep if region == "NE"
egen zone_id = group(zone)
egen first = tag(zone)
summarize loss25 if first
local sd = r(sd)
local loss_nga = r(mean)
res scNgaLoss 100 * `loss_nga'
gen x_post = (loss25 - r(mean)) / `sd' * post
foreach y in gam {
    quietly regress `y' x_post i.zone_id i.year, vce(cluster zone_id)
    * b is per s.d. of loss; divide by the s.d. to get per unit, multiply by the average loss
    local pp = _b[x_post] / `sd' * `loss_nga'
    local lo = (_b[x_post] - 1.96 * _se[x_post]) / `sd' * `loss_nga'
    local hi = (_b[x_post] + 1.96 * _se[x_post]) / `sd' * `loss_nga'
    res scNgaKidsPool   `pp' / 100 * `kids_nga'
    res scNgaKidsLoPool `lo' / 100 * `kids_nga'
    res scNgaKidsHiPool `hi' / 100 * `kids_nga'
    display as text "Nigeria NE: " as result %4.1f `pp' as text " pp = " as result %7.0fc `pp' / 100 * `kids_nga' ///
        as text " children [" as result %7.0fc `lo' / 100 * `kids_nga' as text ", " as result %7.0fc `hi' / 100 * `kids_nga' as text "]"
}


* ============================================================================
* 3. Why these three countries: US humanitarian funding, 2024 (FTS)
* ============================================================================
import delimited using "$DATA/us_funding_2024.csv", clear
gsort -us
list iso3 us total share rank in 1/12, noobs
foreach c in SOM NGA ETH {
    local ct = proper(substr("`c'", 1, 1)) + lower(substr("`c'", 2, 2))
    summarize us if iso3 == "`c'", meanonly
    res scUs`ct' r(mean)
    summarize share if iso3 == "`c'", meanonly
    res scShare`ct' 100 * r(mean)
}

res_save results_07
log close
