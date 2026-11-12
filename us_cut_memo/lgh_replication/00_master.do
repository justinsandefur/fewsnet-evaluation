*** Replication code for Kenny & Sandefur (2026), "Child wasting in Somalia after the 2025 withdrawal of US humanitarian assistance"
*** Written for Stata 19. Needs boottest (ssc install boottest).
*** README.md documents data sources. Every estimate, table and figure in the paper comes from this run.

    version 19
    clear all
    set more off
    set type double
    set scheme stcolor
    graph set window fontface "Helvetica"
    global OUT "output"
    capture mkdir "$OUT"
    capture log close
    log using "$OUT/replication.log", replace text

*** Controls, FE and wild bootstrap settings 
    global CTRL "rain_z rain12_z log_fat"
    global FE   "i.dom i.type_round"
    global BOOT "cluster(region) weight(webb) reps(9999) seed(20261110) nograph"
    global START 2019

*** Figure style: colours for higher / lower US-funded share, and the plot region used by every figure
    global HI "178 24 43"
    global LO "33 102 172"
    global GR "graphregion(color(white) margin(small)) plotregion(color(white) lstyle(none))"

*** gexp NAME: save the current graph as output/NAME.pdf and output/NAME.png (the PNG goes in the Google Doc)
    capture program drop gexp
    program gexp
        graph export "$OUT/`1'.pdf", replace
        graph export "$OUT/`1'.png", replace width(2400)
    end

*** res NAME VALUE: keep a number under its name in the paper; 06_numbers.do writes them all to numbers.csv
    capture program drop res
    program res
        gettoken name 0 : 0
        capture frame create res str40 name double value
        frame post res ("`name'") (`0')
    end

*** Small program so we don't have to write out the DiD specification each time
*** Outcome is Y, treatment is exposure x each post-cut round
*** Runs versions by post-cut round and pooling all post-cut rounds
    capture program drop did
    program did
        syntax varname [if], z(varname) label(string) [ctrl(string) fe(string) trend binary from(integer $START)]
        if "`ctrl'" == "" local ctrl "$CTRL"
        if "`ctrl'" == "none" local ctrl ""
        if "`fe'" == "" local fe "$FE"
        marksample touse
        markout `touse' `z'
        quietly replace `touse' = 0 if year < `from'
        tempvar f
        egen `f' = tag(domain) if `touse'
        quietly summarize `z' if `f'
        local sd = cond("`binary'" != "", 1, r(sd))
        local nd = r(N)
        capture drop x_*
        foreach r in gu25 deyr25 gu26 post {
            gen x_`r' = `z' / `sd' * `r'
        }
        if "`trend'" != "" gen x_trend = `z' / `sd' * (year - 2024)
        capture frame create est str60 label str10 y str8 term double(b se p n domains sd lo hi)
        foreach model in "x_gu25 x_deyr25 x_gu26" "x_post" {
            quietly regress `varlist' `model' `=cond("`trend'" != "", "x_trend", "")' `ctrl' `fe' if `touse', vce(cluster region)
            local N = e(N)
            foreach x of local model {
                local b = _b[`x']
                local se = _se[`x']
                quietly boottest `x', $BOOT
                matrix C = r(CI)
                frame post est ("`label'") ("`varlist'") ("`=substr("`x'", 3, .)'") (`b') (`se') (r(p)) (`N') (`nd') (`sd') ///
                    (C[1, 1]) (C[rowsof(C), 2])
            }
        }
        drop x_*
    end

    do 01_build.do
    do 02_operations.do
    do 03_estimates.do
    do 04_prediction_scale.do
    do 06_numbers.do
    log close
