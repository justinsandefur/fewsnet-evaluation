* 00_master.do
* Stata replication of "Did the US aid cut hurt? Somalia, Nigeria and Ethiopia"
* (../output/us_cut_memo/us_cut_memo.pdf).
*
* Run from the stata/ folder:   cd ".../FEWSNET/us_cut_memo/stata"   then   do 00_master.do
* Inputs:  the CSVs in data/, written by code/81_export_stata.py from the Python pipeline (code/56-80).
* Outputs: logs, .dta files, results_NN.csv and compare.csv in output/
* Runtime: about two minutes (most of it the Anderson-Rubin grid in 04).
*
*   01  build Somalia district and survey-domain files; construct the three exposures
*   02  first stage: where did food, cash and treatment actually fall?
*   03  wasting: Table 1 by survey round, pooled, all outcomes, event study (Figure 3)
*   04  2SLS with Anderson-Rubin intervals; national prediction gap
*   05  Nigeria (north-east surveillance zones)
*   06  Ethiopia (zones; FEWS NET classifications)
*   07  scale: extra wasted children implied by the estimates
*   08  compare every number with the Python values printed in the memo
*
* Figures stay in Python (code/79_us_cut_figures.py).

clear all
do 01_somalia_build.do
do 02_somalia_first_stage.do
do 03_somalia_wasting.do
do 04_somalia_iv_and_prediction.do
do 05_nigeria.do
do 06_ethiopia.do
do 07_scale.do
do 08_compare.do
