"""FEWS NET's forecasts against the official multi-agency projections.

Both the Cadre Harmonise (West Africa) and the IPC publish projections for each
area alongside their current-situation analysis. For each official projection
we find FEWS NET's forecast for the same area (overlaid from FEWS NET's areas)
and period, issued in the latest FEWS NET round at or up to 4 months before the
official analysis. Both are scored against the next official current-situation
analysis of the area.

  Cadre Harmonise: March projections for the June-August lean season, scored
                   against the next current analysis (September-December).
                   November projections reach too far ahead for FEWS NET's
                   forecasts and are not used.
  IPC:             first projections, scored against the next current analysis
                   whose mid-point falls after the analysis date and within 4
                   months after the end of the projection period.

Outcome: area in Phase 3+ at the next current analysis.
  y = a official projection (Phase 3+) + b FEWS NET forecast (share of the area
      FEWS NET forecasts in Phase 3+) + c last official current (Phase 3+)
      + FE(country x analysis round), clustered by country
Also AUC for areas not in Crisis at the time: official alone, FEWS NET alone,
both (cross-fitted gradient boosting by year).

Outputs: output/tables/official_projections*.csv, input/panel/official_projections.parquet
"""
import importlib.util
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OP = load("op", "23_outcome_panel.py")
RAIN = load("rain", "24_area_rainfall.py")
DID = load("did", "25_slope_did.py")


def ch_projections():
    d = pd.read_excel(INP / "ipc" / "cadre_harmonise_caf_ipc_mars26.xlsx")
    d = d[d.chtype.str.lower().eq("projected") & d.usethisperiod.eq("Y") & d.exercise_label.eq("Jan-May")
          & d.reference_label.eq("Jun-Aug")].copy()
    d["area_id"] = d.adm2_pcod2.fillna(d.adm1_pcod2)
    d["level"] = np.where(d.adm2_pcod2.notna(), "adm2", "adm1")
    pop = d.population.replace(0, np.nan)
    out = pd.DataFrame({
        "source": "CH", "iso3": d.adm0_pcod3, "area_id": d.area_id, "level": d.level,
        "area_name": d.adm2_name.fillna(d.adm1_name), "adm1_name": d.adm1_name,
        "issued": pd.PeriodIndex([f"{int(y)}-03" for y in d.exercise_year], freq="M"),
        "p_from": pd.PeriodIndex([f"{int(y)}-06" for y in d.reference_year], freq="M"),
        "p_to": pd.PeriodIndex([f"{int(y)}-08" for y in d.reference_year], freq="M"),
        "proj_share3": d.phase35 / pop, "proj_phase": d.phase_class})
    return out.dropna(subset=["area_id", "proj_share3"]).drop_duplicates(["area_id", "issued"])


def ipc_projections(exclude):
    a = pd.read_csv(INP / "ipc" / "ipc_global_area_long.csv", low_memory=False)
    a = a[(a["Validity period"] == "first projection") & ~a.Country.isin(exclude)].copy()
    a["area_id"] = a.Country + "|" + a["Level 1"].fillna("") + "|" + a.Area
    w = a.pivot_table(index=["Country", "area_id", "Level 1", "Area", "Date of analysis", "From", "To"],
                      columns="Phase", values="Percentage", aggfunc="first").reset_index()
    for p in ["2", "3", "4", "5"]:
        if p not in w:
            w[p] = 0.0
    w = w.fillna({"2": 0, "3": 0, "4": 0, "5": 0})
    s3 = w["3"] + w["4"] + w["5"]
    out = pd.DataFrame({
        "source": "IPC", "iso3": w.Country, "area_id": w.area_id, "level": "ipc_area", "area_name": w.Area,
        "adm1_name": w["Level 1"],
        "issued": pd.to_datetime(w["Date of analysis"], format="%b %Y", errors="coerce").dt.to_period("M"),
        "p_from": pd.to_datetime(w.From, errors="coerce").dt.to_period("M"),
        "p_to": pd.to_datetime(w.To, errors="coerce").dt.to_period("M"),
        "proj_share3": s3,
        "proj_phase": OP.area_phase(s3, w["4"] + w["5"], w["5"], w["2"] + s3)})
    return out.dropna(subset=["issued", "p_from", "p_to"])


def fews_for_period(pr, W):
    """FEWS NET's forecast for each projection's area and period, from the latest round at or up to 4 months
    before the official analysis: area-weighted share of the area forecast in Phase 3+, and FEWS NET's current map."""
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    c = pd.read_parquet(INP / "fewsnet" / "classifications.parquet", columns=["scenario", "report_month"])
    n = c[c.scenario == "CS"].groupby("report_month").size()
    rounds = np.array(sorted(n[n > 1000].index))
    fn = W.fnid.unique()
    proj = proj[proj.fnid.isin(fn) & proj.report_month.isin(rounds)]
    cs = cs[cs.fnid.isin(fn) & cs.month.isin(rounds)]
    rows = []
    for (iss, pf, pt), g in pr.groupby(["issued", "p_from", "p_to"]):
        cand = [r for r in rounds if iss - 4 <= r <= iss]
        if not cand:
            continue
        r = max(cand)
        f = proj[(proj.report_month == r) & (proj.month >= pf) & (proj.month <= pt)]
        if f.empty:
            continue
        f = f.groupby("fnid").phase.max().rename("fc_phase")
        cur = cs[cs.month == r].groupby("fnid").phase.max().rename("cur_phase")
        x = W[W.key.isin(g.key)].merge(f, left_on="fnid", right_index=True, how="left") \
             .merge(cur, left_on="fnid", right_index=True, how="left")
        x["wf"], x["nf"] = (x.fc_phase >= 3) * x.w_key, x.fc_phase.notna() * x.w_key
        x["wc"], x["nc"] = (x.cur_phase >= 3) * x.w_key, x.cur_phase.notna() * x.w_key
        k = x.groupby("key")[["wf", "nf", "wc", "nc"]].sum()
        k = k[k.nf > 0.5]
        rows.append(pd.DataFrame({"key": k.index, "issued": iss, "p_from": pf, "p_to": pt, "fews_round": r,
                                  "fews_fc3": (k.wf / k.nf).values, "fews_cur3": (k.wc / k.nc.where(k.nc > 0.5)).values}))
    return pd.concat(rows)


def main():
    outcomes = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    ch = ch_projections()
    ipc = ipc_projections(set(ch.iso3))
    pr = pd.concat([ch, ipc], ignore_index=True)
    print("official projections:", pr.groupby("source").size().to_dict())
    _, pr = RAIN.area_geometries(pr.assign(month=pr.issued))
    _, oc = RAIN.area_geometries(outcomes)
    W = pd.read_parquet(INP / "panel" / "fnid_ipc_overlay.parquet")
    f = fews_for_period(pr, W)
    pr = pr.merge(f, on=["key", "issued", "p_from", "p_to"], how="inner")
    print("with a matching FEWS NET forecast:", pr.groupby("source").size().to_dict())
    # last official current at issue, and next official current after the projection is made
    oc = oc.dropna(subset=["phase"]).copy()
    oc["ph3"] = (oc.phase >= 3).astype(float)
    oc = oc.groupby(["key", "month"]).agg(ph3=("ph3", "max"), share3=("share3", "mean")).reset_index()
    oc["mi"] = oc.month.astype("int64")
    pr["mi"] = pr.issued.astype("int64")
    pr = pd.merge_asof(pr.sort_values("mi"), oc.sort_values("mi")[["key", "mi", "ph3", "share3"]], on="mi",
                       by="key", direction="backward", tolerance=8) \
        .rename(columns={"ph3": "last3", "share3": "last_share3"})
    pr["mi_next"] = pr.mi + 1
    nxt = oc.rename(columns={"mi": "mi_next", "month": "next_month"}).sort_values("mi_next")
    pr = pd.merge_asof(pr.sort_values("mi_next"), nxt[["key", "mi_next", "next_month", "ph3", "share3"]],
                       on="mi_next", by="key", direction="forward", tolerance=14) \
        .rename(columns={"ph3": "next3", "share3": "next_share3"})
    ok = (pr.next_month >= pr.p_from) & (pr.next_month <= pr.p_to + 4)
    pr = pr[ok & pr.next3.notna()].copy()
    pr["proj3"] = (pr.proj_phase >= 3).astype(float)
    pr["cell"] = pr.iso3 + "_" + pr.issued.astype(str)
    pr["year"] = pr.issued.dt.year
    pr.to_parquet(INP / "panel" / "official_projections.parquet", index=False)
    print("scored projections:", pr.groupby("source").size().to_dict(), "countries", pr.iso3.nunique(),
          "years", pr.year.min(), pr.year.max())

    rows = []
    for samp, d in [("all areas", pr), ("not in Crisis at the last analysis", pr[pr.last3 == 0]),
                    ("Cadre Harmonise", pr[pr.source == "CH"]), ("IPC", pr[pr.source == "IPC"])]:
        for spec, xs in [("official projection only", ["proj3"]), ("FEWS NET forecast only", ["fews_fc3"]),
                         ("both", ["proj3", "fews_fc3"]), ("both + last official analysis", ["proj3", "fews_fc3", "last3"]),
                         ("both + last analysis + FEWS NET current map", ["proj3", "fews_fc3", "last3", "fews_cur3"])]:
            dd = d.dropna(subset=xs)
            r, n, G = DID.fe_ols(dd, "next3", xs, ["cell"])
            for t in xs:
                rows.append({"sample": samp, "spec": spec, "term": t, "coef": r.coef[t], "se": r.se[t], "n": n,
                             "countries": G})
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "official_projections.csv", index=False)
    # predictive comparison for areas not in Crisis at the time
    d = pr[(pr.last3 == 0)].dropna(subset=["fews_fc3"]).copy()
    d["cty"] = pd.factorize(d.iso3)[0]
    auc = []
    for lab, feats in [("official projection", ["proj3", "proj_share3", "last_share3", "cty"]),
                       ("FEWS NET forecast", ["fews_fc3", "fews_cur3", "last_share3", "cty"]),
                       ("both", ["proj3", "proj_share3", "fews_fc3", "fews_cur3", "last_share3", "cty"])]:
        pred = pd.Series(np.nan, index=d.index)
        for yr in sorted(d.year.unique()):
            te = d.year == yr
            if d.loc[~te, "next3"].nunique() < 2:
                continue
            m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, categorical_features=[feats.index("cty")],
                                               random_state=1).fit(d.loc[~te, feats], d.loc[~te, "next3"])
            pred[te] = m.predict_proba(d.loc[te, feats])[:, 1]
        ok = pred.notna()
        auc.append({"model": lab, "auc": roc_auc_score(d.next3[ok], pred[ok]), "events": int(d.next3[ok].sum()),
                    "n": int(ok.sum())})
    auc = pd.DataFrame(auc)
    auc.to_csv(TAB / "official_projections_auc.csv", index=False)
    # simple hit rates: new Crisis cases, who saw them coming?
    new = d[d.next3 == 1]
    hits = {"new_crises": len(new), "official_projected": float(new.proj3.mean()),
            "fews_forecast_majority": float((new.fews_fc3 >= 0.5).mean()),
            "either": float(((new.proj3 == 1) | (new.fews_fc3 >= 0.5)).mean()),
            "false_alarm_official": float(d[d.next3 == 0].proj3.mean()),
            "false_alarm_fews": float((d[d.next3 == 0].fews_fc3 >= 0.5).mean())}
    pd.Series(hits).to_csv(TAB / "official_projections_hits.csv")
    pd.set_option("display.width", 220)
    print(R.round(3).to_string())
    print(auc.round(3).to_string())
    print(hits)


if __name__ == "__main__":
    main()
