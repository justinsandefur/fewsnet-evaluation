* 00_master.do
* Stata replication of "Hunger and Death in Humanitarian Crises" (output/cgd_paper/ipc_surveys_draft.pdf).
*
* Run from the stata/ folder:   cd ".../FEWSNET/ipc_surveys/stata"   then   do 00_master.do
* Inputs:  the CSVs in data/, written by code/91_export_stata.py from the Python pipeline.
* Outputs: logs, results_NN.csv and compare.csv in output/.
* Runtime: about five minutes (mostly the repeated out-of-sample fits in 04 and 06).
*
*   01  phases vs measured malnutrition and death (Somalia's scheduled surveys, SMART+, the IPC's two scales)
*   02  phases vs household food consumption and coping; the Cadre Harmonise's own inputs
*   03  surveys quoted in FEWS NET's reports: coverage, and whether new surveys move the next map
*   04  triggers (rain, conflict, prices) vs phases: out of sample, never-surveyed places, within domains
*   05  where the money goes: funding by cluster, what the system measures, aid vs phases and outcomes
*   06  bounds: counterfactual outcomes without aid
*   07  value of surveys: the treatment-allocation model
*   08  where surveys do not go: survey timing and what reports leave out
*   09  what it takes to be classified in Crisis: the Cadre Harmonise's chain of evidence
*   10  displacement in Somalia: the phase vs displacement, household measures, reassignment, settlements
*   11  compare every number with the value printed in the paper
*
* Figures stay in Python.

clear all
do 01_phase_outcomes.do
do 02_foodsec.do
do 03_report_surveys.do
do 04_triggers.do
do 05_money.do
do 06_bounds.do
do 07_survey_value.do
do 08_survey_gaps.do
do 09_ch_classification.do
do 10_displacement.do
do 11_compare.do
