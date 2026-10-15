* 08_compare.do
* Lines up every number estimated in 01-07 with the value the Python pipeline wrote into the memo
* (output/us_cut_memo/numbers_*.tex, exported to data/python_numbers.csv).
*
* status:
*   same          equal once rounded the way the memo rounds it
*   p-value noise bootstrap p-values from different random draws, within 0.03
*   close         within 5% (small differences in degrees-of-freedom corrections or grid steps)
*   DIFFERENT     look at these

do _setup.do
log using "$OUT/08_compare.log", replace text

* Stata results
clear
local files : dir "$OUT" files "results_*.csv"
tempfile st
foreach f of local files {
    preserve
        import delimited using "$OUT/`f'", clear varnames(1) stringcols(1)
        gen source = "`f'"
        capture append using `st'
        save `st', replace
    restore
}
use `st', clear
rename value stata
duplicates drop name, force

* Python values (strings as printed in the memo, e.g. "198,000" or "0.06")
preserve
    import delimited using "$DATA/python_numbers.csv", clear varnames(1) stringcols(_all)
    rename value py_text
    duplicates drop name, force
    tempfile py
    save `py'
restore
merge 1:1 name using `py', keep(master match)
tab _merge
drop _merge

* compare at the memo's rounding
gen py = real(subinstr(py_text, ",", "", .))
gen decimals = cond(strpos(py_text, "."), strlen(py_text) - strpos(py_text, "."), 0)
gen tol = 0.5 * 10^(-decimals) + 1e-9
replace tol = 500 if strpos(py_text, ",") | (decimals == 0 & abs(py) >= 1000 & mod(py, 1000) == 0)
gen diff = stata - py
gen is_p = regexm(name, "^(ctP|pPred|pLoss|ngP)")
gen status = "same" if abs(diff) <= tol
replace status = "p-value noise" if status == "" & is_p & abs(diff) <= 0.03
replace status = "close" if status == "" & abs(diff) <= max(2 * tol, 0.05 * abs(py))
replace status = "DIFFERENT" if status == "" & !missing(py)
replace status = "not in memo" if missing(py)


display as text _n "{hline 60}" _n "Stata vs Python: " _N " numbers" _n "{hline 60}"
tab status
display as text _n "Everything that is not identical at the memo's rounding:"
format stata %10.2f
list name py_text stata status if !inlist(status, "same", "not in memo"), noobs clean abbreviate(20)

export delimited name stata py_text status source using "$OUT/compare.csv", replace
log close
