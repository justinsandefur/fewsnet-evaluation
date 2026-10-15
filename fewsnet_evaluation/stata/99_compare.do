* 99_compare.do
* Lines up every number estimated in the do-files with the value the Python pipeline printed in
* the paper (output/cgd_paper/numbers.tex, exported to data/python_numbers.csv) and with the
* table cells (data/python_tables.csv).
*
* status:
*   same          equal once rounded the way the paper rounds it
*   p-value noise bootstrap p-values from different random draws, within 0.03
*   close         within 5% (degrees-of-freedom corrections, tie handling, grid steps)
*   DIFFERENT     look at these
*   not in paper  estimated in Stata but not printed (kept for reference)

do _setup.do
cap log close
log using "$OUT/99_compare.log", replace text

* Stata results (output/results_*.csv, one per do-file)
clear
local files : dir "$OUT" files "results_*.csv"
tempfile st
local first = 1
foreach f of local files {
    preserve
        import delimited using "$OUT/`f'", clear varnames(1) stringcols(1)
        gen source = "`f'"
        if !`first' append using `st'
        save `st', replace
    restore
    local first = 0
}
use `st', clear
rename value stata
duplicates drop name, force

* Python values, as printed (e.g. "1,761" or "0.06")
preserve
    import delimited using "$DATA/python_numbers.csv", clear varnames(1) stringcols(_all)
    cap confirm file "$DATA/python_tables.csv"
    if !_rc {
        tempfile pn
        save `pn'
        import delimited using "$DATA/python_tables.csv", clear varnames(1) stringcols(_all)
        gen in_paper = "1"
        append using `pn'
    }
    rename value py_text
    duplicates drop name, force
    tempfile py
    save `py'
restore
merge 1:1 name using `py', keep(master match)
drop _merge

* compare at the paper's rounding
gen py = real(subinstr(py_text, ",", "", .))
gen decimals = cond(strpos(py_text, "."), strlen(py_text) - strpos(py_text, "."), 0)
gen tol = 0.5 * 10^(-decimals) + 1e-9
gen diff = stata - py
gen is_p = regexm(name, "^boot|^flag(Own|Ipc)P$")      // wild bootstrap p-values
gen status = "same" if abs(diff) <= tol
replace status = "p-value noise" if status == "" & is_p & abs(diff) <= 0.03
replace status = "close" if status == "" & abs(diff) <= max(2 * tol, 0.05 * abs(py))
replace status = "DIFFERENT" if status == "" & !missing(py)
replace status = "not in paper" if missing(py) | in_paper != "1"

display as text _n "{hline 60}" _n "Stata vs Python: " _N " numbers" _n "{hline 60}"
tab status
display as text _n "Everything printed in the paper that is not identical at the paper's rounding:"
format stata %12.4g
list name py_text stata status source if !inlist(status, "same", "not in paper"), noobs clean abbreviate(24)

* printed macros with no Stata estimate (descriptive counts, dates and anything not ported)
preserve
    use `py', clear
    keep if in_paper == "1"
    merge 1:1 name using `st', keep(master) nogenerate keepusing(name)
    display as text _n "Printed in the paper but not estimated in Stata: " _N
    export delimited name py_text using "$OUT/not_covered.csv", replace
restore

sort status name
export delimited name stata py_text status source using "$OUT/compare.csv", replace
log close
