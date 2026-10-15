* _setup.do -- paths, packages and three small helper programs.
* Every do-file runs this first, so each can also be run on its own (from the stata/ folder).

version 19
set more off
set varabbrev off
set type double           // store new variables in full precision

global DATA "data"        // CSVs written by code/81_export_stata.py
global OUT  "output"      // logs, .dta files, results
cap mkdir "$OUT"

cap which boottest        // wild cluster bootstrap (Roodman et al.)
if _rc ssc install boottest
cap which reghdfe         // regressions with many fixed effects (Correia)
if _rc {
    ssc install ftools
    ssc install reghdfe
}

* res NAME EXPRESSION
*   Records one estimate under the name the memo uses for it (the \newcommand names in
*   output/us_cut_memo/numbers_*.tex), so 08_compare.do can line Stata up against Python.
cap program drop res
program res
    gettoken name 0 : 0                  // first word = name; the rest = the value (any expression)
    cap frame create results str40 name double value
    frame post results ("`name'") (`0')
end

* res_save FILE
*   Writes the estimates recorded so far to output/FILE.csv and starts a fresh list.
cap program drop res_save
program res_save
    args file
    frame results: export delimited using "$OUT/`file'.csv", replace
    frame drop results
end

* domain_sd VAR
*   Standard deviation of VAR across survey domains in the last estimation sample (one value per
*   domain). Coefficients are multiplied by this to express effects "per s.d. of exposure".
cap program drop domain_sd
program domain_sd, rclass
    args v
    tempvar first
    egen `first' = tag(domain) if e(sample)
    quietly summarize `v' if `first' == 1
    return scalar sd = r(sd)
end
