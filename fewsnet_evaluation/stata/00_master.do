* 00_master.do
* Stata replication of "How Much Does Early Warning Improve Famine Response?"
* (output/cgd_paper/fewsnet_evaluation.pdf).
*
* Run from the stata/ folder:   do 00_master.do
*   or in batch:                stata-mp -b do 00_master.do
* Inputs:  the CSVs in data/, written by code/90_export_stata.py from the Python pipeline.
* Outputs: logs, .dta files, results_NN.csv, compare.csv and not_covered.csv in output/
*
*   01  coverage, accuracy, Type II and Type I errors, famine, case studies   (Sections 2-5)
*   02  need-defined emergencies: does early warning help aid hold them back? (Section 5)
*   03  what FEWS NET adds beyond public data: AUCs, Table 2, funding, masking (Section 6, App. B)
*   04  head to head with the official projections: Table 3, wild bootstrap   (Section 6.2)
*   05  FEWS NET's reports and price data                                     (Section 6, App. F)
*   06  does funding follow the maps or the forecasts? Table A1               (Section 7, App. E)
*   07  local shocks and FEWS NET coverage                                    (Section 9, App. D)
*   08  aid flags and the 2025 shutdown                                       (Section 9, App. C)
*   09  aid within Somalia and Sudan                                          (App. I)
*   10  benefit-cost arithmetic in lives, Table 4                             (App. H)
*   11  value on two margins: reallocation and the envelope                   (Section 8)
*   12  FEWS NET's budget; what a phase means for malnutrition and death      (Section 8, App. G)
*   99  compare every number with the Python values printed in the paper
*
* Figures and the gradient-boosted predictions stay in Python.

clear all
foreach f in 01_errors 02_need_onsets 03_contribution 04_official 05_text_prices 06_money ///
             07_shocks 08_flags 09_subnational 10_benefit_cost 11_value_margins 12_budget_phase {
    clear all
    do `f'.do
}
do 99_compare.do
