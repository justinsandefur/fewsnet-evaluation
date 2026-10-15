"""Export analysis-ready CSVs for the Stata replication of the IPC/surveys paper (stata/).

Python keeps the jobs Stata is bad at: fetching, parsing survey PDFs and dashboards, matching survey
domains and districts to FEWS NET's mapping units, rainfall and conflict windows, and figures. This script
writes the results of that work as plain tables; the do-files in stata/ re-estimate every number the
paper prints from them.

Run after the analysis scripts (57, 58, 53, 65, 66, 84-90 and side_survey_selection/code/03, 06).
Writes stata/data/*.csv:
  fsnau_panel.csv        Somalia scheduled surveys, zone x season, as used by 57 (forecast, map, lags, outcomes)
  fsnau_all.csv          every rural FSNAU SMART survey (57's build), for the under-five death rate lag
  fsnau_count.csv        number of FSNAU survey results assembled (one row)
  smartplus.csv          SMART+ and FDW surveys matched to FEWS NET and IPC/CH phases (58)
  amn_areas.csv          areas with both an IPC food-insecurity and an acute-malnutrition phase (58)
  foodsec.csv            WFP household indicators matched to FEWS NET's phase (as in 40_paper._foodsec)
  ch_inputs.csv          Cadre Harmonise input indicators and the CH phase (66)
  newsurvey.csv          area-rounds for the new-survey regression (53.new_measurement)
  coverage.csv           area-rounds for survey coverage of Emergency areas (53.data_tables)
  report_surveys.csv     survey results quoted in FEWS NET's reports (53.survey_validation)
  triggers_som.csv       Somalia survey domain x season panel (84)
  triggers_nga.csv       Nigeria survey domain x round panel (84)
  aidneed.csv            district/LGA x season aid panel (87)
  xc_aid.csv             country x year funding panel (89)
  fts_cluster.csv        FTS funding by year and cluster (85)
  system_ipc.csv, system_ch.csv, system_smart.csv   classification and survey lists (86)
  bounds_panel.csv       Somalia domain panel with aid per person and FEWS NET flag (90)
  voi_panel.csv          Somalia zone x season panel for the value-of-information model (65)
  gaps_panel.csv         country x year survey panel with estimation-sample flags (side project 03)
  exclusions.csv         coded survey-report exclusions (side project 06)
  python_numbers.csv     every \\newcommand in output/cgd_paper/numbers*.tex and whether the draft prints it
"""
import contextlib
import importlib.util
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, PAPER = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "cgd_paper"
SIDE = ROOT / "side_survey_selection"
OUT = ROOT / "stata" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def load(name, file, quiet=True):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    if quiet:
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(m)
    else:
        spec.loader.exec_module(m)
    return m


def write(df, name):
    df.to_csv(OUT / name, index=False)
    print(f"{name:22s} {len(df):7,d} rows")


# ------------------------------------------------------------------ 57: Somalia scheduled surveys
def fsnau():
    write(pd.read_csv(TAB / "fsnau_value_panel.csv"), "fsnau_panel.csv")
    F = load("m57", "57_fsnau_value.py")
    s = F.build()
    write(s[["key", "t", "gam", "sam", "cdr", "u5dr"]], "fsnau_all.csv")
    write(pd.DataFrame({"n_results": [len(pd.read_csv(INP / "fsnau/surveys.csv"))]}), "fsnau_count.csv")


# ------------------------------------------------------------------ 58: other surveys, IPC's two scales
def smartplus():
    s = pd.read_csv(TAB / "phase_outcomes_surveys.csv")
    write(s[["source", "sid", "iso2", "month", "gam", "cdr", "u5dr", "recurring", "cluster", "cur", "fc", "ipc", "cy"]],
          "smartplus.csv")
    a = pd.read_csv(TAB / "phase_outcomes_amn_areas.csv")
    write(a[["iso3", "area", "afi", "amn_any"]], "amn_areas.csv")


# ------------------------------------------------------------------ 66 / 40: household indicators
def foodsec():
    P = load("m40", "40_paper.py")
    d, _ = P._foodsec()
    write(d[["area_id", "iso3", "indicator", "value", "phase", "group"]], "foodsec.csv")
    m = pd.read_parquet(INP / "foodsec_surveys/matched.parquet")
    c = m[(m.source == "ch_hdx")][["iso3", "area_id", "indicator", "value", "ipc_phase"]]
    write(c, "ch_inputs.csv")


# ------------------------------------------------------------------ 53: surveys in FEWS NET's reports
def reports():
    T = load("m53", "53_text_value.py")
    p, s = T.build()
    # new_measurement(): same steps as 53, keeping the estimation sample
    d = p[p.has_text & (p.phase <= 3)].dropna(subset=["next_phase", "fc_phase"]).copy()
    d["tgt"] = T.per(d.target)
    ss = s.dropna(subset=["fnid"])[["fnid", "fw", "gam_pct"]]
    x = d[["fnid", "r", "tgt"]].merge(ss, on="fnid")
    x = x[(x.fw > x.r) & (x.fw <= x.tgt)].groupby(["fnid", "r"]).gam_pct.max().rename("new_gam").reset_index()
    x["new_s"] = 1.0
    d = d.merge(x, on=["fnid", "r"], how="left")
    d["new_s"] = d.new_s.fillna(0.0)
    d["new_crit"] = (d.new_gam >= 15).astype(float)
    d["new_ok"] = (d.new_gam < 15).astype(float)
    d["err"] = d.next_phase - d.fc_phase
    d["up"], d["down"] = (d.err > 0).astype(float), (d.err < 0).astype(float)
    d["next4"] = (d.next_phase >= 4).astype(float) if "next4" not in d else d.next4
    keep = ["fnid", "cell", "cl", "phase", "fc_phase", "next_phase", "up", "down", "next4", "new_s", "new_crit",
            "new_ok"] + T.CTRL
    write(d[[c for c in dict.fromkeys(keep) if c in d]].assign(r=d.r.astype(str)), "newsurvey.csv")
    c = p[p.has_text].dropna(subset=["next_phase", "fc_phase"])
    write(c[["country_code", "phase", "s_any"]], "coverage.csv")
    write(pd.read_csv(TAB / "text_value_surveys.csv")[["sid", "cc"]], "report_surveys.csv")


# ------------------------------------------------------------------ 84: triggers vs phases
def triggers():
    T = load("m84", "84_triggers_vs_phases.py")
    p = T.p.copy()
    cols = ["domain", "ptype", "season_id", "season_rank", "deyr", "year", "t", "gam", "sam", "cdr", "u5dr", "morbidity",
            "measles", "need_p3", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat",
            "L_gam", "L_sam", "L_cdr", "L_u5dr", "L_morbidity", "L_measles"]
    write(p[cols].assign(t=p.t.astype(str)), "triggers_som.csv")
    g = pd.read_parquet(INP / "panel" / "nga_domain_panel.parquet")
    write(g[["domain", "round_id", "month", "gam", "sam", "cdr", "u5dr", "need_p3", "fews_cs", "fews_fc", "rain_z",
             "rain12_z", "log_fat", "dp12", "L_gam", "L_cdr", "L_u5dr"]], "triggers_nga.csv")


# ------------------------------------------------------------------ 85-87, 89: money
def money():
    D = pd.read_parquet(INP / "panel" / "aidneed_panel.parquet")
    write(D[["country", "unit", "period", "pop", "usd", "partners", "reach", "need_p3", "fews_cs", "fews_fc", "rain_z",
             "rain12_z", "log_fat", "lp_cereal", "gam", "sam", "cdr", "u5dr"]], "aidneed.csv")
    write(pd.read_csv(TAB / "xc_aid_panel.csv"), "xc_aid.csv")
    write(pd.read_csv(TAB / "fts_cluster_funding.csv"), "fts_cluster.csv")
    # 86: the classification and survey lists it counts
    ipc = pd.read_csv(INP / "ipc" / "ipc_global_area_long.csv", low_memory=False)
    ipc = ipc[(ipc["Validity period"] == "current") & (ipc.Phase == "all")]
    ipc = ipc.assign(year=pd.to_datetime(ipc.From).dt.year)[["Country", "Date of analysis", "Level 1", "Area", "year"]]
    write(ipc.rename(columns={"Date of analysis": "date", "Level 1": "level1"}), "system_ipc.csv")
    ch = pd.read_excel(INP / "ipc" / "cadre_harmonise_caf_ipc_mars26.xlsx")
    ch = ch[ch.chtype.astype(str).str.lower().str.startswith("current")]
    write(ch[["adm0_name", "adm1_name", "adm2_name", "adm3_name", "exercise_code", "reference_year"]], "system_ch.csv")
    sm = json.load(open(INP / "smartplus" / "mortality.json"))["surveys"]
    write(pd.DataFrame([{"year": s["surveyYear"], "country": s["geographicCountry"]} for s in sm]), "system_smart.csv")


# ------------------------------------------------------------------ 90: bounds
def bounds():
    b = pd.read_csv(TAB / "aidbounds_panel.csv")
    cols = ["domain", "ptype", "season_id", "season_rank", "deyr", "t", "gam", "cdr", "u5dr", "morbidity", "measles",
            "need_p3", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat", "L_morbidity",
            "L_measles", "aid_pc", "aid_pc_obs", "flag", "nat_pc"]
    write(b[cols], "bounds_panel.csv")
    # national humanitarian aid per person per six months, by year (90: FTS for Somalia / population / 2)
    sub = pd.read_parquet(INP / "panel" / "subnational_SOM.parquet")
    sub["tp"] = pd.PeriodIndex(sub.t, freq="M")
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet", columns=["amount_usd", "status", "flow_type", "boundary",
                                                                     "dest_country", "usage_year"])
    f = f[f.status.isin(["paid", "commitment"]) & (f.flow_type == "Standard") & (f.boundary == "incoming") &
          (f.dest_country == "Somalia") & f.usage_year.astype(str).str.fullmatch(r"\d{4}")]
    fts_year = f.groupby(f.usage_year.astype(int)).amount_usd.sum()
    som_pop = sub.groupby("tp").pop.sum().groupby(lambda t: t.year).max()
    write(pd.DataFrame({"fts_usd": fts_year, "pop": som_pop.reindex(fts_year.index)}).rename_axis("year").reset_index(),
          "bounds_national.csv")


# ------------------------------------------------------------------ 65: value of information
def voi():
    V = load("m65", "65_survey_voi.py")
    d = V.panel()
    write(d[["key", "t", "pop", "fc", "ph", "gam", "sam", "mam", "sam_lag", "mam_lag"]], "voi_panel.csv")


# ------------------------------------------------------------------ side project: where surveys go
def gaps():
    df = pd.read_csv(SIDE / "data" / "panel.csv")
    df = df.dropna(subset=["ln_gdppc", "ln_pop"]).copy()          # as in side_survey_selection/code/03_analysis.py
    df["minor"] = df.conflict - df.war
    df = df.sort_values(["iso3", "year"])
    # 03's fit() drops rows missing any column whose name appears in the formula string; replicate
    f3 = "s_any ~ ln_gdppc + ln_pop + minor + war + downturn + C(iso3) + C(year)"
    df["in_s3"] = df[[c for c in df.columns if c in f3]].notna().all(axis=1).astype(int)
    df["calm3"] = (df.groupby("iso3").conflict.transform(lambda s: s.shift(1).rolling(3).sum()) == 0).astype(int)
    on = df[(df.conflict == 1) & (df.calm3 == 1)][["iso3", "year"]].groupby("iso3").year.min().rename("onset")
    df = df.merge(on, on="iso3", how="left")
    fev = "s_any ~ e0 + e1 + e2 + e3 + e4 + e5 + e6 + e_pre + e_post + ln_gdppc + ln_pop + C(iso3) + C(year)"
    base_cols = [c for c in df.columns if c in fev and c not in ("onset",)]
    df["in_ev"] = df[base_cols].notna().all(axis=1).astype(int)
    full = pd.read_csv(SIDE / "data" / "panel.csv")
    write(df[["iso3", "year", "s_any", "s_DHS", "s_MICS", "ln_gdppc", "ln_pop", "conflict", "minor", "war", "downturn",
              "calm3", "onset", "in_s3", "in_ev"]], "gaps_panel.csv")
    write(full[["iso3", "year", "s_any", "s_DHS"]], "gaps_full.csv")
    write(pd.read_csv(SIDE / "output" / "tables" / "exclusions_coded_merged.csv")[
        ["id", "program", "bd3", "usable", "any_security_excl", "ex_ante", "sec_drops", "camps_out", "camps_in",
         "camps_silent", "displacement_question"]], "exclusions.csv")


# ------------------------------------------------------------------ the numbers the paper prints
def numbers():
    tex = (PAPER / "ipc_surveys_draft.tex").read_text()
    used = set(re.findall(r"\\([A-Za-z]+)\{\}", tex))
    rows = []
    for f in sorted(PAPER.glob("numbers*.tex")):
        for k, v in re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$", f.read_text(), flags=re.M):
            rows.append(dict(name=k, value=v.replace("\\textminus{}", "-").replace("\\$", "").replace("\\,", ""),
                             file=f.name, printed=int(k in used)))
    write(pd.DataFrame(rows).drop_duplicates("name", keep="last"), "python_numbers.csv")


if __name__ == "__main__":
    for f in [fsnau, smartplus, foodsec, reports, triggers, money, bounds, voi, gaps, numbers]:
        f()
