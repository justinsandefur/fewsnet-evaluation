* _setup.do -- paths, packages and small helper programs.
* Every do-file runs this first, so each can also be run on its own (from the stata/ folder).

version 19
set more off
set varabbrev off
set type double           // store new variables in full precision

global DATA "data"        // CSVs written by code/90_export_stata.py
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
*   Records one estimate under the name the paper uses for it (the \newcommand names in
*   output/cgd_paper/numbers.tex, or tab_* names for table cells), so 99_compare.do can line
*   Stata up against Python. Values are recorded in the paper's units (e.g. percent, not shares).
cap program drop res
program res
    gettoken name 0 : 0
    cap frame create results str60 name double value
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

* ym VAR
*   Converts a "YYYY-MM" string variable to a Stata monthly date in place.
cap program drop ym
program ym
    args v
    tempvar t
    gen `t' = monthly(`v', "YM")
    drop `v'
    rename `t' `v'
    format `v' %tm
end

* pyse
*   Run right after reghdfe. The Python pipeline (fe_ols in code/25_slope_did.py) scales the
*   cluster-robust variance by G/(G-1) only; reghdfe also multiplies it by (N-1)/(N-K), where K
*   counts the regressors and any fixed effects not nested in the clusters. pyse undoes that factor,
*   so standard errors follow the Python convention (Stata's are up to 3% larger). Coefficients are
*   unchanged.
cap program drop pyse
program pyse, eclass
    tempname V
    matrix `V' = e(V) * (e(N) - e(df_m) - e(df_a) - 1) / (e(N) - 1)
    ereturn repost V = `V'
end
