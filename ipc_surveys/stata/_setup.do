* _setup.do -- paths, packages and small helper programs.
* Every do-file runs this first, so each can also be run on its own (from the stata/ folder).

version 19
set more off
set varabbrev off
set type double           // store new variables in full precision

global DATA "data"        // CSVs written by code/91_export_stata.py
global OUT  "output"      // logs, results
cap mkdir "$OUT"

cap which reghdfe         // regressions with many fixed effects (Correia)
if _rc {
    ssc install ftools
    ssc install reghdfe
}

* res NAME EXPRESSION
*   Records one estimate under the name the paper uses for it (the \newcommand names in
*   output/cgd_paper/numbers*.tex), so 09_compare.do can line Stata up against Python.
cap program drop res
program res
    gettoken name 0 : 0
    cap frame create results str40 name double value
    frame post results ("`name'") (`0')
end

* res_save FILE  -- writes the estimates recorded so far to output/FILE.csv and starts a fresh list
cap program drop res_save
program res_save
    args file
    frame results: export delimited using "$OUT/`file'.csv", replace
    frame drop results
end

* bankround NEWVAR = EXP
*   Rounds half to even, as Python and pandas do (Stata's round() rounds halves away from zero).
cap program drop bankround
program bankround
    gettoken newvar 0 : 0
    gettoken eq 0 : 0
    tempvar x
    gen double `x' = `0'
    gen double `newvar' = round(`x')
    replace `newvar' = 2 * round(`x' / 2) if abs(`x' - floor(`x') - 0.5) < 1e-9
end

* loso Y [XVARS] [if], fold(VAR) [auc]
*   Leave-one-fold-out OLS: fits Y on XVARS (and a constant) on all folds but one and predicts the
*   fold left out. Returns r(r2) = 1 - SSR/SST (SST around the sample mean; negative when the model
*   predicts worse than the mean) or, with auc, r(auc) for a binary Y. XVARS may include factor variables.
cap program drop loso
program loso, rclass
    syntax varlist(min=1 fv) [if], fold(varname) [auc noCONStant sst0]
    gettoken y xs : varlist
    marksample touse, novarlist
    markout `touse' `y'
    tempvar pred p
    qui gen double `pred' = .
    qui levelsof `fold' if `touse', local(levs)
    foreach s of local levs {
        qui regress `y' `xs' if `touse' & `fold' != `s', `constant'
        qui predict double `p' if `touse' & `fold' == `s', xb
        qui replace `pred' = `p' if `touse' & `fold' == `s'
        drop `p'
    }
    if "`auc'" != "" {
        qui roctab `y' `pred' if `touse'
        return scalar auc = r(area)
    }
    else {
        tempvar e2 d2
        qui summarize `y' if `touse'
        local m = cond("`sst0'" != "", 0, r(mean))
        qui gen double `e2' = (`y' - `pred')^2 if `touse'
        qui gen double `d2' = (`y' - `m')^2 if `touse'
        qui summarize `e2'
        local ssr = r(sum)
        qui summarize `d2'
        return scalar r2 = 1 - `ssr' / r(sum)
    }
    qui count if `touse'
    return scalar N = r(N)
end

* zstd NEWVAR = VAR  -- standardize with the sample s.d. (n-1), as pandas does
cap program drop zstd
program zstd
    gettoken newvar 0 : 0
    gettoken eq 0 : 0
    qui summarize `0'
    gen double `newvar' = (`0' - r(mean)) / r(sd)
end
