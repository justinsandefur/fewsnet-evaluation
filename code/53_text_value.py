"""Pilot: does the text of FEWS NET's reports carry information its maps don't,
and where is FEWS NET short of data? Somalia, Ethiopia, Sudan, 2011-2024.

Inputs: input/reports/{mentions,surveys,gaps,reports}.parquet (52_text_features.py),
        input/panel/forecast_value_panel.parquet (area x map round, 32_forecast_value.py),
        input/fewsnet/proj_monthly.parquet, cs_monthly.parquet.

1. Text features for each area x round r, from reports published in the four
   months up to and including r (the outlook issued with the map, and the
   updates, key message updates and alerts since the previous round):
   projected Emergency, worst case Emergency or Famine, deterioration expected,
   aid expected to fall, access blocked, drivers, uncertainty. Plus the latest
   survey result in the area in the 12 months before r, and any stated data gap.

2. Escalation. Among areas in Crisis (Phase 3) at r, does the area reach
   Emergency (4+) on the next map? Outcome as mapped and by need (mapped phase
   plus one if flagged as held back by aid). Linear probability models with
   country x round fixed effects, clustered by region (admin1); cross-fitted
   AUC (by year) for the map alone versus map plus text.

3. Data. How do FEWS NET's misses vary with whether a recent survey exists,
   whether the reports flag a data gap, and remote monitoring? How much of the
   Crisis+ caseload had any survey in the previous 12 months?

3b. New measurement. Does a survey fielded between the forecast and the next
   map change the next map relative to the forecast (up or down), controlling
   for everything the reports said about the area at r?

4. Surveys as an independent outcome. Survey results quoted in the reports
   (GAM, crude and under-five death rates), matched to areas and months, scored
   against FEWS NET's map at the time and its forecast made 4-8 months earlier.

Outputs: output/tables/text_value_*.csv, output/tables/text_value_key.json
"""
import importlib.util
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
REP = INP / "reports"
PILOT = ["SO", "ET", "SD"]
MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}
ABBR = {m[:3]: i for m, i in MONTHS.items()}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DID = load("did", "25_slope_did.py")


def per(s):
    return pd.PeriodIndex(s.astype(str), freq="M")


def fieldwork_month(s, fallback):
    """'July 2013', 'June-July 2017', 'Dec 2016/Jan 2017' -> last month named; else fallback."""
    if not isinstance(s, str):
        return fallback
    yrs = re.findall(r"(20\d\d)", s)
    mos = [ABBR[w[:3]] for w in re.findall(r"[A-Za-z]+", s.lower()) if w[:3] in ABBR]
    if not yrs:
        return fallback
    try:
        p = pd.Period(f"{yrs[-1]}-{(mos[-1] if mos else 6):02d}", "M")
    except ValueError:
        return fallback
    return p if p <= fallback else fallback


def num(x):
    return pd.to_numeric(x, errors="coerce")


def text_features(panel):
    m = pd.read_parquet(REP / "mentions.parquet").dropna(subset=["fnid"])
    m = m[m.cc.isin(PILOT)].copy()
    m["month"] = per(m.month)
    for c in ["current_phase", "projected_phase", "projected_phase_2", "worst_case_phase"]:
        m[c] = num(m.get(c))
    m["proj_max"] = m[["projected_phase", "projected_phase_2"]].max(axis=1)
    drv = m.drivers.fillna("")
    feats = pd.DataFrame({
        "fnid": m.fnid, "month": m.month,
        "t_mention": 1.0,
        "t_proj4": (m.proj_max >= 4).astype(float),
        "t_worst4": ((m.worst_case_phase >= 4) | (m.proj_max >= 5)).astype(float),
        "t_det": (m.direction == "deteriorate").astype(float),
        "t_aid_down": m.aid_status.isin(["reduced_or_ending", "pipeline_break_expected"]).astype(float),
        "t_access": ((m.aid_status == "access_blocked") | drv.str.contains("access_constraint")).astype(float),
        "t_flag": m.aid_flag_or_held_back.fillna(False).astype(float),
        "t_conflict": drv.str.contains("conflict|displacement").astype(float),
        "t_rain": drv.str.contains("rain_deficit|harvest_poor").astype(float),
        "t_prices": drv.str.contains("prices_high|currency|macro").astype(float),
        "t_disease": drv.str.contains("disease").astype(float),
        "t_uncert": m.uncertainty_language.fillna(False).astype(float),
        "t_specific": m.level.isin(["admin2", "zone"]).astype(float),
    })
    # reports in the 4 months up to r: (r-4, r]
    rounds = panel[["fnid", "r"]].drop_duplicates()
    out = []
    for lag in range(4):
        f = feats.copy()
        f["r"] = f.month + lag
        out.append(f.merge(rounds, on=["fnid", "r"]))
    f = pd.concat(out).drop(columns="month")
    return f.groupby(["fnid", "r"]).max().reset_index()


def survey_table():
    s = pd.read_parquet(REP / "surveys.parquet")
    s = s[s.cc.isin(PILOT) & ~s.planned_not_done.fillna(False).astype(bool)].copy()
    s["rmonth"] = per(s.month)
    s["fw"] = [fieldwork_month(a, b - 1) for a, b in zip(s.fieldwork, s.rmonth)]
    for c in ["gam_pct", "sam_pct", "gam_muac_pct", "cdr", "u5dr", "fcs_poor_pct"]:
        s[c] = num(s[c])
    s["has_result"] = s[["gam_pct", "cdr", "u5dr", "gam_muac_pct", "fcs_poor_pct"]].notna().any(axis=1)
    s = s[s.has_result]
    # the same survey is quoted in several reports: keep one row per area, survey month and values
    s = s.drop_duplicates(["fnid", "fw", "population_group", "gam_pct", "cdr", "u5dr"])
    return s


def survey_features(panel, s):
    s = s.dropna(subset=["fnid"])
    rounds = panel[["fnid", "r"]].drop_duplicates()
    x = rounds.merge(s[["fnid", "fw", "gam_pct", "cdr", "u5dr"]], on="fnid")
    x = x[(x.fw < x.r) & (x.fw >= x.r - 12)]
    g = x.groupby(["fnid", "r"]).agg(s_any=("fw", "size"), s_gam=("gam_pct", "max"),
                                     s_cdr=("cdr", "max"), s_u5dr=("u5dr", "max")).reset_index()
    g["s_any"] = 1.0
    g["s_gam15"] = (g.s_gam >= 15).astype(float)
    g["s_mort"] = ((g.s_cdr >= 1) | (g.s_u5dr >= 2)).astype(float)
    return g


def gap_features(panel):
    gp = pd.read_parquet(REP / "gaps.parquet")
    gp = gp[gp.cc.isin(PILOT)].copy()
    gp["month"] = per(gp.month)
    rows = []
    for _, g in gp.iterrows():
        ids = [x for x in (g.fnids or "").split(";") if x]
        if not ids and g.location == "national":
            continue
        rows += [dict(fnid=i, month=g.month, what=g.what) for i in ids]
    gp = pd.DataFrame(rows)
    rounds = panel[["fnid", "r"]].drop_duplicates()
    x = rounds.merge(gp, on="fnid")
    x = x[(x.month <= x.r) & (x.month > x.r - 12)]
    g = x.groupby(["fnid", "r"]).agg(g_any=("what", "size"),
                                     g_access=("what", lambda w: (w == "access").any())).reset_index()
    g["g_any"] = 1.0
    g["g_access"] = g.g_access.astype(float)
    return g


def admin1():
    u = pd.read_parquet(INP / "fewsnet/ipcphase.parquet", columns=["fnid", "geographic_unit_full_name"])
    u = u.drop_duplicates("fnid").dropna()
    u["adm1"] = u.geographic_unit_full_name.str.rsplit(",", n=3, expand=True)[2].str.strip()
    return u[["fnid", "adm1"]]


def build():
    p = pd.read_parquet(INP / "panel/forecast_value_panel.parquet")
    p = p[p.country_code.isin(PILOT) & (p.r.dt.year <= 2024)].copy() if hasattr(p.r, "dt") else \
        p[p.country_code.isin(PILOT)].copy()
    p["r"] = per(p.r)
    p = p[p.r.dt.year <= 2024]
    p = p.merge(admin1(), on="fnid", how="left")
    p["cl"] = p.country_code + "_" + p.adm1.fillna("na")
    p["cell"] = p.country_code + "_" + p.r.astype(str)
    p["next4"] = (p.next_phase >= 4).astype(float)
    p["need4"] = ((p.next_phase + p.next_flag.fillna(0)) >= 4).astype(float)
    p["fc4"] = (p.fc_phase >= 4).astype(float)
    p["fc_flag"] = p.fc_flag.astype(float)
    p["flag"] = p.flag.astype(float)
    tf = text_features(p)
    s = survey_table()
    sf = survey_features(p, s)
    gf = gap_features(p)
    p = p.merge(tf, on=["fnid", "r"], how="left").merge(sf, on=["fnid", "r"], how="left") \
         .merge(gf, on=["fnid", "r"], how="left")
    tcols = [c for c in p if c.startswith(("t_", "s_any", "s_gam15", "s_mort", "g_"))]
    p[tcols] = p[tcols].fillna(0.0)
    # rounds with at least one extracted report for the country (others have no text by construction)
    rep = pd.read_parquet(REP / "reports.parquet")
    rep = rep[rep.cc.isin(PILOT)]
    rep["month"] = per(rep.month)
    have = set()
    for _, x in rep.iterrows():
        for lag in range(4):
            have.add((x.cc, x.month + lag))
    p["has_text"] = [(c, r) in have for c, r in zip(p.country_code, p.r)]
    return p, s


TEXT = ["t_proj4", "t_worst4", "t_det", "t_aid_down", "t_access", "t_conflict", "t_rain",
        "t_prices", "t_uncert", "t_mention"]
DATA = ["s_any", "s_gam15", "s_mort", "g_any"]


def escalation(p):
    d = p[(p.phase == 3) & p.has_text].dropna(subset=["next_phase", "fc_phase"])
    rows = []
    for y in ["next4", "need4"]:
        for name, xs in [("map", ["fc4", "flag", "fc_flag"]),
                         ("map+text", ["fc4", "flag", "fc_flag"] + TEXT),
                         ("map+text+data", ["fc4", "flag", "fc_flag"] + TEXT + DATA)]:
            r, n, G = DID.fe_ols(d, y, xs, ["cell"], cluster="cl")
            for x, v in r.iterrows():
                rows.append(dict(outcome=y, model=name, var=x, coef=v.coef, se=v.se, n=n, clusters=G))
    return pd.DataFrame(rows), d


def auc(d, y, xs, return_pred=False):
    """Cross-fitted by year logistic AUC, with country x month-of-year dummies."""
    d = d.copy()
    d["yr"] = d.r.dt.year
    X = pd.get_dummies(d[xs + ["country_code"]].assign(moy=d.r.dt.month.astype(str)),
                       columns=["country_code", "moy"], dtype=float)
    pred = pd.Series(np.nan, index=d.index)
    for yr in d.yr.unique():
        tr, te = d.yr != yr, d.yr == yr
        if d.loc[tr, y].nunique() < 2:
            continue
        m = LogisticRegression(max_iter=2000, C=1.0).fit(X[tr], d.loc[tr, y])
        pred[te] = m.predict_proba(X[te])[:, 1]
    ok = pred.notna()
    if return_pred:
        return pred
    return roc_auc_score(d.loc[ok, y], pred[ok]) if d.loc[ok, y].nunique() == 2 else np.nan


def data_tables(p):
    d = p[p.has_text].dropna(subset=["next_phase", "fc_phase"])
    esc = d[(d.phase <= 3) & (d.next_phase >= 4)]
    rows = []
    for v in ["s_any", "g_any", "g_access", "t_access"]:
        for val in [0.0, 1.0]:
            e = esc[esc[v] == val]
            rows.append(dict(split=v, value=val, escalations=len(e),
                             warned_fc4=e.fc4.mean() if len(e) else np.nan,
                             warned_text=((e.fc4 + e.t_proj4 + e.t_worst4) > 0).mean() if len(e) else np.nan))
    # survey coverage of the Crisis+ caseload (area-rounds; population weights where available)
    pop = pd.read_parquet(INP / "panel/fnid_population.parquet") if (INP / "panel/fnid_population.parquet").exists() else None
    c = d[d.phase >= 3].copy()
    if pop is not None and "pop" in pop:
        c = c.merge(pop[["fnid", "pop"]], on="fnid", how="left")
    else:
        c["pop"] = 1.0
    c["pop"] = c["pop"].fillna(c["pop"].median())
    cov = c.groupby("country_code").apply(lambda g: pd.Series({
        "areas_crisis_plus": len(g),
        "share_with_survey_12m": g.s_any.mean(),
        "pop_share_with_survey_12m": np.average(g.s_any, weights=g["pop"]),
        "share_with_gap_flag": g.g_any.mean()})).reset_index()
    cov4 = d[d.phase >= 4].groupby("country_code").s_any.mean().rename("emergency_share_with_survey").reset_index()
    return pd.DataFrame(rows), cov.merge(cov4, on="country_code", how="left")


def survey_validation(s):
    """GAM / death rates against FEWS NET's map at the time and its forecast 4-8 months earlier."""
    s = s.dropna(subset=["fnid"])
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet", columns=["fnid", "month", "phase", "assist_flag"])
    cs = cs.sort_values("month")
    pr = pd.read_parquet(INP / "fewsnet/proj_monthly.parquet")
    pr = pr[pr.country_code.isin(PILOT) & pr.lead.between(4, 8)]
    pr = pr.groupby(["fnid", "month"]).phase.max().rename("fc_4_8").reset_index()
    x = s[["cc", "fnid", "fw", "gam_pct", "cdr", "u5dr", "population_group", "level"]].copy()
    x = x.rename(columns={"fw": "month"})
    x["month_ts"] = x.month.dt.to_timestamp()
    cs["month_ts"] = cs.month.dt.to_timestamp()
    x = pd.merge_asof(x.sort_values("month_ts"), cs[["fnid", "month_ts", "phase", "assist_flag"]].sort_values("month_ts"),
                      on="month_ts", by="fnid", direction="backward", tolerance=pd.Timedelta(days=150))
    x = x.merge(pr, on=["fnid", "month"], how="left")
    # one row per survey (collapse fnid duplicates to the max phase across matched units)
    x["sid"] = x.cc + x.month.astype(str) + x.gam_pct.astype(str) + x.cdr.astype(str) + x.u5dr.astype(str)
    g = x.groupby("sid").agg(cc=("cc", "first"), month=("month", "first"), gam=("gam_pct", "first"),
                             cdr=("cdr", "first"), u5dr=("u5dr", "first"), phase=("phase", "max"),
                             fc=("fc_4_8", "max"), level=("level", "first")).reset_index()
    g["gam15"] = (g.gam >= 15).astype(float).where(g.gam.notna())
    g["mort"] = ((g.cdr >= 1) | (g.u5dr >= 2)).astype(float).where(g.cdr.notna() | g.u5dr.notna())
    by_phase = g.groupby("phase").agg(n=("sid", "size"), gam_mean=("gam", "mean"), gam15=("gam15", "mean"),
                                      n_mort=("mort", "count"), mort=("mort", "mean")).reset_index()
    by_fc = g.groupby("fc").agg(n=("sid", "size"), gam_mean=("gam", "mean"), gam15=("gam15", "mean"),
                                n_mort=("mort", "count"), mort=("mort", "mean")).reset_index()
    # Type I/II against anthropometry: very high GAM (>=15) vs forecast Emergency
    v = g.dropna(subset=["gam15", "fc"])
    t = dict(n=len(v), crit=int(v.gam15.sum()),
             miss=float(1 - v[v.gam15 == 1].fc.ge(4).mean()) if v.gam15.sum() else np.nan,
             miss_crisis=float(1 - v[v.gam15 == 1].fc.ge(3).mean()) if v.gam15.sum() else np.nan,
             false_alarm=float(1 - v[v.fc >= 4].gam15.mean()) if (v.fc >= 4).any() else np.nan)
    return g, by_phase, by_fc, t


CTRL = ["fc4", "t_det", "t_worst4", "t_proj4", "t_access", "t_conflict", "t_rain", "t_prices",
        "t_mention", "s_any", "flag", "fc_flag"]


def new_measurement(p, s):
    """Surveys fielded after the forecast (r) and up to the next map: do they move the next map?"""
    d = p[p.has_text & (p.phase <= 3)].dropna(subset=["next_phase", "fc_phase"]).copy()
    d["tgt"] = per(d.target)
    ss = s.dropna(subset=["fnid"])[["fnid", "fw", "gam_pct"]]
    x = d[["fnid", "r", "tgt"]].merge(ss, on="fnid")
    x = x[(x.fw > x.r) & (x.fw <= x.tgt)].drop_duplicates(["fnid", "r"])[["fnid", "r"]]
    x["new_s"] = 1.0
    d = d.merge(x, on=["fnid", "r"], how="left")
    d["new_s"] = d.new_s.fillna(0.0)
    d["err"] = d.next_phase - d.fc_phase
    d["up"], d["down"] = (d.err > 0).astype(float), (d.err < 0).astype(float)
    rows = []
    for y, sample in [("up", d), ("down", d), ("next4", d[d.phase == 3])]:
        for ctrl in ["fc4 only", "all text"]:
            xs = ["new_s"] + (["fc4"] if ctrl == "fc4 only" else CTRL)
            r, n, G = DID.fe_ols(sample, y, xs, ["cell"], cluster="cl")
            rows.append(dict(outcome=y, controls=ctrl, coef=r.loc["new_s", "coef"], se=r.loc["new_s", "se"],
                             n=n, clusters=G, base=sample[y].mean(), share_new=sample.new_s.mean()))
    c = d[d.phase == 3]
    groups = {"escalated_unforecast": c[(c.next_phase >= 4) & (c.fc4 == 0)],
              "escalated_forecast": c[(c.next_phase >= 4) & (c.fc4 == 1)],
              "no_escalation": c[c.next_phase < 4]}
    shares = {k: dict(n=len(g), share_new_survey=g.new_s.mean()) for k, g in groups.items()}
    return pd.DataFrame(rows), shares


def misses_fe(p):
    """Among escalations to Emergency, is FEWS NET less likely to have forecast Emergency where
    the reports flag access problems or data gaps? Within country x round."""
    e = p[p.has_text & (p.phase <= 3) & (p.next_phase >= 4)].dropna(subset=["fc_phase"])
    rows = []
    for v in ["t_access", "g_access", "g_any", "s_any", "t_conflict"]:
        r, n, G = DID.fe_ols(e, "fc4", [v], ["cell"], cluster="cl")
        rows.append(dict(var=v, coef=r.loc[v, "coef"], se=r.loc[v, "se"], n=n, mean=e[v].mean(),
                         raw_gap=e[e[v] == 1].fc4.mean() - e[e[v] == 0].fc4.mean()))
    return pd.DataFrame(rows)


def extraction_check(p):
    """Does the current phase stated in the text match FEWS NET's map for the matched units?"""
    m = pd.read_parquet(REP / "mentions.parquet").dropna(subset=["fnid"])
    m = m[m.level.isin(["admin2", "unit", "zone"]) & m.cc.isin(PILOT)].copy()
    m["r"] = per(m.month)
    m["cur"] = num(m.current_phase)
    j = m.merge(p[["fnid", "r", "phase"]], on=["fnid", "r"])
    j = j.groupby(["name", "i"]).agg(cur=("cur", "first"), mx=("phase", "max"), mn=("phase", "min")).dropna()
    return float(((j.cur >= j.mn) & (j.cur <= j.mx)).mean()), int(len(j))


def main():
    p, s = build()
    key = {"areas_rounds": int(len(p)), "rounds_with_text": int(p.has_text.sum())}
    reg, d = escalation(p)
    reg.to_csv(TAB / "text_value_escalation.csv", index=False)
    for y in ["next4", "need4"]:
        base = ["fc4", "flag", "fc_flag"]
        key[f"auc_{y}_map"] = auc(d, y, base)
        key[f"auc_{y}_text"] = auc(d, y, base + TEXT)
        key[f"auc_{y}_textdata"] = auc(d, y, base + TEXT + DATA)
    pr = d[["fnid", "r", "country_code", "next4", "need4"]].copy()
    for y in ["next4", "need4"]:
        pr[f"{y}_map"] = auc(d, y, ["fc4", "flag", "fc_flag"], return_pred=True)
        pr[f"{y}_text"] = auc(d, y, ["fc4", "flag", "fc_flag"] + TEXT, return_pred=True)
    pr["r"] = pr.r.astype(str)
    pr.to_parquet(REP / "text_value_preds.parquet", index=False)
    key["esc_n"] = int(len(d))
    key["esc_events"] = int(d.next4.sum())
    key["esc_fc4_share"] = float(d[d.next4 == 1].fc4.mean())
    key["esc_text_share"] = float(((d.fc4 + d.t_proj4 + d.t_worst4) > 0)[d.next4 == 1].mean())
    key["nonesc_text_share"] = float(((d.fc4 + d.t_proj4 + d.t_worst4) > 0)[d.next4 == 0].mean())
    nm, shares = new_measurement(p, s)
    nm.to_csv(TAB / "text_value_new_survey.csv", index=False)
    key["new_survey_groups"] = shares
    mf = misses_fe(p)
    mf.to_csv(TAB / "text_value_misses_fe.csv", index=False)
    key["extract_match"], key["extract_match_n"] = extraction_check(p)
    misses, cov = data_tables(p)
    misses.to_csv(TAB / "text_value_misses_by_data.csv", index=False)
    cov.to_csv(TAB / "text_value_survey_coverage.csv", index=False)
    g, by_phase, by_fc, t = survey_validation(s)
    g.to_csv(TAB / "text_value_surveys.csv", index=False)
    by_phase.to_csv(TAB / "text_value_surveys_by_phase.csv", index=False)
    by_fc.to_csv(TAB / "text_value_surveys_by_forecast.csv", index=False)
    key.update({f"survey_{k}": v for k, v in t.items()})
    key["surveys_total"] = int(len(g))
    key["surveys_by_country"] = g.cc.value_counts().to_dict()
    (TAB / "text_value_key.json").write_text(json.dumps(key, indent=1, default=float))
    pd.set_option("display.width", 200)
    print(json.dumps(key, indent=1, default=float))
    print(reg[reg["var"].isin(["fc4"] + TEXT + DATA)].pivot_table(index="var", columns=["outcome", "model"], values="coef").round(3))
    print(nm.round(3)); print(mf.round(3))
    print(misses.round(2)); print(cov.round(2)); print(by_phase.round(2)); print(by_fc.round(2))


if __name__ == "__main__":
    main()
