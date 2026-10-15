* 08_flags.do
* Did areas FEWS NET flagged as held up by aid deteriorate once US aid was cut in 2025?
* (paper Section 9 and Appendix C; code/28_flag_release.py)
*
* Units: same-season pairs, an area's classification at a baseline before 2025 and 12 months later.
*   A. FEWS NET's own maps (FEWS NET areas in Phase 2-3 at baseline; flag = 0/1 "!" on the baseline map)
*   B. Cadre Harmonise / IPC areas (flag = share of the area under flagged FEWS NET areas in a map
*      made at most 4 months before the baseline analysis)
* exposed = the later classification falls in 2025 or after.
*   change in phase = b flag + d flag x exposed + FE(country x baseline month x horizon x phase)
* d is the extra deterioration of flagged areas after the cut; b (flagged vs unflagged change in
* normal years) is the placebo. SEs clustered by country; wild cluster bootstrap p-values (boottest:
* Rademacher weights, null imposed, 999 draws, as in Python, but different random draws).

do _setup.do
cap log close
log using "$OUT/08_flags.log", replace text

import delimited using "$DATA/flag_pairs.csv", clear
keep if hm == 12
encode iso3, gen(iso)
gen fx = flag * exposed

foreach v in A B {
    local K = cond("`v'" == "A", "Own", "Ipc")
    preserve
        keep if version == "`v'" & !missing(dphase)
        * singletons in the comparison cell dropped (as in Python fe_ols)
        bys cell: drop if _N == 1
        quietly reghdfe dphase flag fx, absorb(cell) vce(cluster iso)
        * Python scales the clustered variance by G/(G-1) only; undo reghdfe's (N-1)/(N-K) for the SE
        local se = _se[fx] * sqrt((e(N) - e(df_m) - e(df_a) - 1) / (e(N) - 1))
        display as text "`v': flag x exposed = " as result %6.3f _b[fx] as text " (" as result %5.3f `se' ///
            as text "), placebo flag gap = " as result %6.3f _b[flag] as text ", N = " e(N) ", countries = " e(N_clust)
        res flag`K'         _b[fx]
        res flag`K'Se       `se'
        res flag`K'Placebo  _b[flag]
        boottest fx, reps(999) weighttype(rademacher) seed(1) nograph
        res flag`K'P        r(p)
    restore
}

res_save results_08
log close
