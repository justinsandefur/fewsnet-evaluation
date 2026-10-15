* 10_compare.do
* Lines up every number estimated in 01-09 with the value the Python pipeline wrote into the paper
* (output/cgd_paper/numbers*.tex, exported to data/python_numbers.csv by code/91_export_stata.py).
*
* status:
*   same          equal once rounded the way the paper rounds it
*   close         within 5% (small differences in degrees-of-freedom corrections)
*   DIFFERENT     look at these
*   not printed   estimated here but not printed in the current draft

do _setup.do
cap log close
log using "$OUT/10_compare.log", replace text

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

preserve
    import delimited using "$DATA/python_numbers.csv", clear varnames(1) stringcols(_all)
    rename value py_text
    duplicates drop name, force
    tempfile py
    save `py'
restore
merge 1:1 name using `py', keep(master match)
drop _merge

gen py = real(subinstr(py_text, ",", "", .))
gen decimals = cond(strpos(py_text, "."), strlen(py_text) - strpos(py_text, "."), 0)
gen tol = 0.5 * 10^(-decimals) + 1e-9
* round-number thousands printed with commas (e.g. 1,900; 240,000) are rounded to two significant figures
replace tol = 0.5 * 10^(floor(log10(abs(py))) - 1) if strpos(py_text, ",") & mod(py, 100) == 0
gen diff = stata - py
gen status = "same" if abs(diff) <= tol
replace status = "close" if status == "" & abs(diff) <= max(2 * tol, 0.05 * abs(py))
replace status = "DIFFERENT" if status == "" & !missing(py)
replace status = "not printed" if printed != "1" & status != "DIFFERENT"
replace status = "DIFFERENT (not printed)" if printed != "1" & status == "DIFFERENT"

* known, explained differences
gen note = ""
replace note = "a" if regexm(name, "^(voi|svvRound)")

display as text _n "{hline 60}" _n "Stata vs Python: " _N " numbers" _n "{hline 60}"
tab status
display as text _n "Everything printed in the paper that is not identical at its rounding:"
format stata %12.3f
list name py_text stata status note if inlist(status, "close", "DIFFERENT"), noobs clean abbreviate(20)
display as text _n "Notes:" _n ///
    "  a  The value-of-information numbers depend on FEWS NET unit populations (input/panel/fnid_population.parquet)," _n ///
    "     a cache shared by the three papers. They replicate only with the full cache; see README.md."

export delimited name stata py_text status note source using "$OUT/compare.csv", replace
log close
