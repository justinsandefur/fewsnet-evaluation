"""Write output/concept_note/numbers.tex: LaTeX macros for every number quoted
in the concept note, taken from output/tables/key_numbers.json. Re-run after
08_coverage.py so the text never drifts from the data."""
import json

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = json.loads((ROOT / "output" / "tables" / "key_numbers.json").read_text())


def pct(x):
    return f"{100 * x:.0f}\\%"


def n(x, r=None):
    if r:
        x = round(x, r)
    return f"{int(x):,}".replace(",", "{,}")


fp, dh = K["fews_panel"], K["dhs"]
g = K["grfc"][0]
ml2 = next(r for r in K["self_consistency"] if r["scenario"] == "ML2")
m = {
    "fewsUnitMonths": n(fp["unit_months"]),
    "fewsCountries": str(fp["countries"]),
    "fewsUnits": n(fp["units"], -2),
    "fewsAssistShare": pct(fp["share_assist_flag"]),
    "scAcc": pct(ml2["accuracy"]),
    "scNaive": pct(ml2["naive_accuracy"]),
    "scAccFour": pct(ml2["accuracy_when_actual_4plus"]),
    "scNewCrises": pct(ml2["share_new_crises_forecast"]),
    "grfcCountryYears": str(g["country_years"]),
    "grfcShareCY": pct(g["share_cy_fews"]),
    "grfcShareThree": pct(g["share_p3_fews"]),
    "grfcShareFour": pct(g["share_p4_fews"]),
    "holeShareFour": pct(1 - g["share_p4_countries_with_any_dhs_since_2011"]),
    "dhsSurveys": str(dh["with_gps_and_fews_data"]),
    "dhsCountries": str(dh["countries"]),
    "dhsChildren": n(dh["children_measured"], -3),
    "dhsChildrenThree": n(dh["est_children_in_phase3plus_units"], -3),
    "dhsChildrenFour": n(dh["est_children_in_phase4plus_units"], -2),
    "dhsStunting": n(dh["est_children_stunting_cohort"], -3),
    "dhsAreasThree": n(dh["areas_3plus_during_fieldwork"], -2),
    "dhsAreasFour": n(dh["areas_4plus_during_fieldwork"], -1),
    "dhsAreas": n(dh["areas_during_fieldwork"], -2),
    "dhsSurveysThree": str(dh["surveys_with_phase3plus_share_over_10pct"]),
    "dhsSurveysFour": str(dh["surveys_with_any_phase4plus"]),
    "grfcShareThreeDHS": pct(g["share_p3_fews_and_dhs_same_year"]),
    "grfcShareFourDHS": pct(g["share_p4_fews_and_dhs_same_year"]),
}
if "funding" in K:
    f = [r for r in K["funding"] if 2011 <= r["year"] <= 2025]
    tot = sum(r["total_bn"] for r in f)
    m["ftsShareFews"] = pct(sum(r["total_bn"] * r["share_to_fews_countries"] for r in f) / tot)
    m["ftsDecisionShare"] = pct(sum(r["total_bn"] * r["share_with_decision_date"] for r in f) / tot)
    m["ftsFlows"] = n(K.get("fts_flows", 0), -3)
    pre = [r for r in f if r["year"] <= 2024]
    m["usShareFood"] = pct(sum(r["us_share_of_food_to_fews"] for r in pre) / len(pre))
    m["usShareFoodTwentyFive"] = pct(next(r["us_share_of_food_to_fews"] for r in f if r["year"] == 2025))
    m["sectorMissingEarly"] = pct(sum(r["share_sector_unspecified"] for r in f if r["year"] <= 2016)
                                  / len([r for r in f if r["year"] <= 2016]))
    megas = K.get("mega_emergencies", [])
    names = []
    for r in sorted(megas, key=lambda r: -r["share_of_year"]):
        label = f"{r['emergency']} ({int(r['year'])}, {pct(r['share_of_year'])} of that year's funding)"
        if r["emergency"] not in [x[0] for x in names]:
            names.append((r["emergency"], label))
    m["megaList"] = "; ".join(l for _, l in names[:5]).replace("&", "\\&")
else:
    for k in ["ftsShareFews", "ftsDecisionShare", "ftsFlows", "megaList"]:
        m[k] = "[pending]"

news = {r["iso2"]: r for r in K.get("news_per_person_us", [])}
if news:
    for iso, name in [("CD", "Congo"), ("SO", "Somalia"), ("KE", "Kenya"), ("NG", "Nigeria"),
                      ("SD", "Sudan"), ("YE", "Yemen")]:
        m[f"news{name}"] = n(news[iso]["per_100k_p3"]) if iso in news else "[pending]"
    m["newsCountries"] = str(len(news))
tiers = {r["tier"].lstrip("+ "): r for r in K.get("survey_tiers", [])}
if tiers:
    m["tierDHSFour"] = pct(tiers["DHS (GPS)"]["share_p4_any_since_2011"])
    m["tierMICSFour"] = pct(tiers["MICS (region)"]["share_p4_any_since_2011"])
    m["tierCampsFour"] = pct(tiers["UNHCR camps"]["share_p4_any_since_2011"])
    m["tierDHSYear"] = pct(tiers["DHS (GPS)"]["share_p4_within_a_year"])
    m["tierAllYear"] = pct(tiers["UNHCR camps"]["share_p4_within_a_year"])
    m["tierLSMSYear"] = pct(tiers["LSMS (GPS)"]["share_p4_within_a_year"])
    m["tierLSMSFour"] = pct(tiers["LSMS (GPS)"]["share_p4_any_since_2011"])
    m["tierMICSYear"] = pct(tiers["MICS (region)"]["share_p4_within_a_year"])
    fams = {r["family"]: r for r in K["survey_family_counts"]}
    m["micsSurveys"] = str(fams["MICS (region)"]["surveys"])
    m["micsCountries"] = str(fams["MICS (region)"]["countries"])
    m["campSurveys"] = str(fams["UNHCR camps"]["surveys"])
o = K.get("outage")
if o:
    m["outageMonths"] = str(len(o["dark_months"]))
    m["outageCountries"] = str(o["countries_before"])
    m["restartAug"] = str(o["n_restart_aug25"])
    m["restartOct"] = str(o["n_oct25"])
    m["coverageSwitches"] = str(o["coverage_switches_2011_2026"])
# Missed emergencies and false alarms (12_errors.py, 13_errors_detail.py)
ek = TAB_ = ROOT / "output" / "tables"
if (ek / "errors_key_numbers.json").exists():
    e = json.loads((ek / "errors_key_numbers.json").read_text())
    curve = pd.read_csv(ek / "errors_type2_curve.csv")
    on = curve[curve.onset].set_index("lead").share_fc4
    off = curve[~curve.onset].share_fc4.mean()
    m["tTwoOnsets"] = n(e["type2"]["onsets"])
    m["tTwoLeadEight"], m["tTwoLeadFour"], m["tTwoLeadOne"] = pct(on[8]), pct(on[4]), pct(on[1])
    m["tTwoControl"] = pct(off) if off >= 0.005 else "1\\%"
    m["tTwoEverWarned"] = pct(e["type2"]["share_warned_emergency_any_lead"])
    m["tTwoNeverEmergency"] = pct(1 - e["type2"]["share_warned_emergency_any_lead"])
    m["tTwoCrisisOnly"] = pct(e["type2"]["share_warned_crisis_only"])
    m["tTwoNoWarning"] = pct(e["type2"]["share_no_warning_at_all"])
    m["tTwoFromCrisis"] = pct(e["type2"]["share_onsets_from_phase3"])
    m["tOneWarnings"] = n(e["type1"]["warnings"])
    m["tOneFalse"] = pct(e["type1"]["false_alarm_share"])
    fl = {c["cell"]: c["flag"] for c in e["type1"]["flag"]}
    m["tOneFlagFalse"] = pct(fl["Warned, did not happen: realised Crisis (3)"])
    m["tOneFlagOther"] = pct(fl["Not warned, realised Crisis (3)"])
    m["tOneFlagHit"] = pct(fl["Warned, Emergency happened (realised Phase 4+)"])
    ft = pd.read_csv(ek / "errors_flag_over_time.csv").set_index(["rel", "group"])
    m["flagNotEight"], m["flagNotZero"] = pct(ft.loc[(-8, "not"), "flag"]), pct(ft.loc[(0, "not"), "flag"])
    m["flagCameEight"], m["flagCameZero"] = pct(ft.loc[(-8, "came"), "flag"]), pct(ft.loc[(0, "came"), "flag"])
    m["flagCameFour"], m["stillFour"] = pct(ft.loc[(4, "came"), "flag"]), pct(ft.loc[(4, "came"), "p4"])
    d2 = json.loads((ek / "errors_detail_key_numbers.json").read_text())
    m["fundWarnEpisodes"] = str(sum(d2["t1_warning_episodes"].values()))
    m["fundOnsetEpisodes"] = str(sum(d2["t1_onset_episodes"].values()))
cy = K.get("coverage_same_year")
if cy:
    m["sameDHSFour"] = pct(cy["FEWS NET, and a DHS (or LSMS) survey in the field"]["p4"])
    m["sameMICSFour"] = pct(cy["FEWS NET, and a MICS survey in the field"]["p4"])
    m["sameCampFour"] = pct(cy["FEWS NET, and a UNHCR camp survey in the field"]["p4"])
    m["sameNoneFour"] = pct(cy["FEWS NET only, no survey measuring children"]["p4"])
    m["sameOutFour"] = pct(cy["Not covered by FEWS NET"]["p4"])
    fw = K["fieldwork_all"]
    m["fwSurveys"] = str(fw["surveys"])
    m["fwMICS"] = str(fw["by_family"].get("MICS (region)", 0))
    m["fwCamps"] = str(fw["by_family"].get("UNHCR camps", 0))
    m["fwAnyFour"] = str(sum(fw["surveys_any4_by_family"].values()))
out = "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items())
(ROOT / "output" / "concept_note" / "numbers.tex").write_text(out + "\n")
print(out)
