* 01_errors.do
* Reproduces the descriptive sections of the paper: how much of the world's food crises FEWS NET
* covers (Section 2), how accurate its forecasts are against "nothing changes" (Section 4), the
* Type II section (were new Emergencies forecast?), the Type I section (what happened to areas
* forecast to be in Emergency, and how often FEWS NET flags that aid held them back), famine
* warnings, the two case studies, and the data counts quoted along the way.
* Python: code/40_paper.py coverage(), type2(), type1(), famine_errors(), cases(), with the event
* definitions in code/12_errors.py. All FEWS NET data are 2011-2024 (before the 2025 shutdown).
*
* Saves output/err_cs.dta and output/err_proj.dta for 02_need_onsets.do.

do _setup.do
cap log close
log using "$OUT/01_errors.log", replace text

* nvals VAR: number of distinct values, in r(n)
cap program drop nvals
program nvals, rclass
    tempvar t
    egen `t' = tag(`1')
    quietly count if `t'
    return scalar n = r(N)
end


* ============================================================================
* 1. Build: current-situation maps and projections, area x month
* ============================================================================

* Current-situation maps: one row per area x month, phase 1-5 and FEWS NET's aid flag ("!": aid
* keeps the area at least one phase better than it would otherwise be).
import delimited using "$DATA/err_cs.csv", clear varnames(1) stringcols(1 2 3)
ym month
egen id = group(fnid)
res csAreaMonths _N
nvals fnid
res csAreas r(n)
nvals country_code
res csCountries r(n)
sort id month
by id: gen prev_phase = phase[_n-1]            // the area's previous map, however long ago
by id: gen prev_flag  = flag[_n-1]
by id: gen gap = month - month[_n-1]           // months since that map
compress
save "$OUT/err_cs.dta", replace
keep fnid id
duplicates drop
tempfile ids
save `ids'

* Projections, issued in report month r for months r + lead (near-term ML1 and medium-term ML2).
* Stored as spells; expand to one row per forecast month. Where ML1 and ML2 overlap (leads 0-2
* only) keep the more severe.
import delimited using "$DATA/err_proj.csv", clear varnames(1) stringcols(1 2)
ym report_month
merge m:1 fnid using `ids', keep(master match) nogenerate
replace id = -_n if missing(id)                // areas never mapped: keep them apart (no event uses them)
gen spell = _n
expand lead_to - lead_from + 1
bysort spell: gen lead = lead_from + _n - 1
gen month = report_month + lead
format month %tm
gen fneed = min(phase + flag, 5)               // forecast "need": phase, plus one if flagged (02_need_onsets.do)
collapse (max) phase fneed, by(id report_month month)
gen lead = month - report_month
compress
save "$OUT/err_proj.dta", replace


* ============================================================================
* 2. Type II: were new Emergencies forecast?
* ============================================================================

* An onset: the map shows Emergency or worse (Phase 4+) and the area's previous map, within six
* months, showed Crisis or better. The comparison group: same condition, but the area stayed
* below Emergency.
use "$OUT/err_cs.dta", clear
keep if inrange(gap, 1, 6) & prev_phase <= 3
gen onset = phase >= 4
count if onset
res tIIonsets r(N)
keep country_code id month onset
rename month t0
tempfile ev
save `ev'

* For each event (area, month t0) and issue lag k = 1..8: the most severe phase that a report
* issued in t0 - k forecast for the area for any month from t0 - 3 to t0. (Forecast windows follow
* FEWS NET's seasonal calendar, so a forecast issued well ahead often covers the run-up.)
use id report_month month phase using "$OUT/err_proj.dta", clear
expand 4
bysort id report_month month: gen t0 = month + _n - 1
gen k = t0 - report_month
keep if inrange(k, 1, 8)
collapse (max) fc = phase, by(id t0 k)
merge m:1 id t0 using `ev', keep(match) nogenerate
gen fc4 = fc >= 4
gen fc3 = fc >= 3

* the curve: share forecast Emergency (and Crisis) by lag, onsets vs comparison areas
preserve
    collapse (mean) fc4 fc3, by(onset k)
    list, sepby(onset) noobs
    foreach k in 1 4 8 {
        quietly summarize fc4 if onset & k == `k'
        local w = word("one . . four . . . eight", `k')
        res tIIlead`w' 100 * r(mean)
    }
    quietly summarize fc3 if onset & k == 4
    res tIIleadfourCrisis 100 * r(mean)
    quietly summarize fc4 if !onset                 // unweighted average over the 8 lags
    res tIIcontrolEmergency 100 * r(mean)
restore

keep if onset

* onsets never forecast even as Crisis at any lag
preserve
    collapse (max) fc3, by(id t0)
    quietly summarize fc3
    res tIInoWarning 100 * (1 - r(mean))
restore

* early warning (issued 4-8 months before): the most severe such forecast
preserve
    keep if k >= 4
    collapse (max) fc, by(id t0)
    replace fc = min(fc, 4)
    tab fc
    quietly count
    local n = r(N)
    quietly count if fc == 4
    local e = r(N) / `n'
    quietly count if fc == 3
    local c = r(N) / `n'
    quietly count if fc <= 2
    res tIIearlyEmergency 100 * `e'
    res tIIearlyCrisis 100 * `c'
    res tIIearlyStressed 100 * r(N) / `n'
    res tIIearlyMiss 100 * (1 - `e')
    res tIIearlyCrisisPlus 100 * (`e' + `c')
restore

* episodes: all areas in one country whose Emergency began in the same month
preserve
    egen ep = group(country_code t0)
    quietly summarize ep
    res tIIepisodes r(max)
    * at each lag, the share of an episode's areas forecast in Emergency is usually all or none
    collapse (mean) share = fc4 (count) n = fc4, by(country_code t0 k)
    keep if n >= 2
    gen extreme = inlist(share, 0, 1)
    quietly summarize extreme
    res tIIdotsExtreme 100 * r(mean)
restore


* ============================================================================
* 3. Type I: what happened to areas forecast to be in Emergency?
* ============================================================================

* A warning: the latest medium-term forecast (issued 4-8 months before) for a month with a map
* puts the area in Emergency or worse.
use id report_month month phase lead using "$OUT/err_proj.dta", clear
keep if inrange(lead, 4, 8)
bysort id month (report_month): keep if _n == _N
rename phase fc
keep id month fc
tempfile latest
save `latest'
use "$OUT/err_cs.dta", clear
merge 1:1 id month using `latest', keep(match) nogenerate

* aid flag among areas mapped in Crisis that had not been warned of Emergency
quietly summarize flag if fc < 4 & phase == 3
res tIflagUnwarnedCrisis 100 * r(mean)

preserve
    keep if fc >= 4
    res tIwarnings _N
    gen came    = phase >= 4
    gen flag3   = phase == 3 & flag
    gen noflag3 = phase == 3 & !flag
    gen better  = phase <= 2
    quietly summarize came
    local came = r(mean)
    quietly summarize flag3
    local flag3 = r(mean)
    res tIcame 100 * `came'
    res tIflagged 100 * `flag3'
    res tIfailed 100 * (1 - `came')
    res tIfailFlagShare 100 * `flag3' / (1 - `came')     // Python divides the rounded percentages
    quietly summarize noflag3
    res tIunflagged 100 * r(mean)
    quietly summarize better
    res tIbetter 100 * r(mean)
    quietly summarize flag if phase == 3
    res tIflagShareOfCrisis 100 * r(mean)
    * flagged false alarms whose previous map already carried the flag
    gen prev_flagged = prev_flag == 1               // no previous map counts as not flagged
    quietly summarize prev_flagged if flag3
    res tIflaggedAlreadyFlagged 100 * r(mean)
restore

* Famine: forecasts of Phase 5, 4-8 months ahead, and what followed
preserve
    keep if fc >= 5
    res famWarn _N
    gen flag4 = phase == 4 & flag                 // Emergency, flagged as held back by aid
    quietly summarize flag4
    res famFlag 100 * r(mean)
restore
use "$OUT/err_cs.dta", clear
keep if phase >= 5
nvals fnid
res famMappedUnits r(n)                            // areas ever mapped in Famine


* ============================================================================
* 4. Accuracy against "nothing changes" (area x map round panel)
* ============================================================================

* fc_phase: FEWS NET's medium-term forecast; next_phase: its next map; phase: the current map
import delimited using "$DATA/err_panel.csv", clear varnames(1) stringcols(1 2 3)
gen hit   = fc_phase == next_phase
gen naive = phase == next_phase
gen change = next_phase != phase
quietly summarize hit
res accForecast 100 * r(mean)
quietly summarize naive
res accNaive 100 * r(mean)
quietly summarize change
res shareChanges 100 * r(mean)
quietly summarize hit if change
res accChanges 100 * r(mean)

* the analysis panel: areas, countries, rounds, and how many have a recent official IPC/CH analysis
res panelAreaRounds _N
nvals fnid
res panelAreas r(n)
nvals country_code
res panelCountries r(n)
quietly summarize has_ipc
res shareWithIndependent 100 * r(mean)

* the two case studies (areas with a mapped polygon): Somalia, forecast Feb 2017;
* Ethiopia, forecast Oct 2015
foreach c in "So SO 2017-02" "Et ET 2015-10" {
    tokenize `c'
    preserve
        keep if country_code == "`2'" & r == "`3'" & has_geom == 1
        res case`1'Areas _N
        quietly count if fc_phase >= 4
        res case`1'FcFour r(N)
        quietly count if next_phase >= 4
        res case`1'NextFour r(N)
        quietly count if phase >= 4
        res case`1'CurFour r(N)
        quietly summarize next_flag
        res case`1'Flags r(sum)
        res case`1'FlagShare 100 * r(mean)
        quietly summarize rain_z6
        res case`1'Rain r(mean)
    restore
}


* ============================================================================
* 5. Coverage, funding and the shutdown
* ============================================================================

* Global Report on Food Crises, 2016-2024: share of people in Phase 3+ and 4+ in country-years
* FEWS NET mapped
use "$OUT/err_cs.dta", clear
gen year = year(dofm(month))
keep country_code year
duplicates drop
rename country_code iso2
tempfile fy
save `fy'
import delimited using "$DATA/err_grfc.csv", clear varnames(1)
merge m:1 iso2 year using `fy', keep(master match)
gen fews = _merge == 3
nvals iso3
res covCountries r(n)
foreach v in p3 p4plus {
    quietly summarize `v'
    local tot = r(sum)
    quietly summarize `v' if fews
    local s_`v' = r(sum) / `tot'
}
res covPthree 100 * `s_p3'
res covPfour 100 * `s_p4plus'

* FTS humanitarian funding, 2011-2024: average yearly share going to FEWS NET countries, and the
* US share of food and nutrition funding to them
import delimited using "$DATA/err_fts.csv", clear varnames(1)
keep if inrange(year, 2011, 2024)
gen a_fews = amount_usd * to_fews
gen a_food = amount_usd * to_fews * food
gen a_us   = amount_usd * to_fews * food * us
collapse (sum) amount_usd a_fews a_food a_us, by(year)
gen share_fews = a_fews / amount_usd
gen us_food = a_us / max(1, a_food)
quietly summarize share_fews
res ftsShareFews 100 * r(mean)
quietly summarize us_food
res ftsUsFoodShare 100 * r(mean)

* countries FEWS NET classified in October 2024, before the shutdown
import delimited using "$DATA/err_report_months.csv", clear varnames(1)
count if report_month == "2024-10"
res outBefore r(N)

* famine risk in FEWS NET's reports: months between the first mention (in the 12 months before)
* and the famine (Somalia July 2011; Sudan June 2024)
import delimited using "$DATA/err_reports.csv", clear varnames(1)
ym month
foreach c in "So SO 2011m7" "Sd SD 2024m6" {
    tokenize `c'
    quietly summarize month if cc == "`2'" & famine_risk == 1 & month < tm(`3') & month >= tm(`3') - 12
    res famRiskLead`1' tm(`3') - r(min)
}

res_save results_01
log close
