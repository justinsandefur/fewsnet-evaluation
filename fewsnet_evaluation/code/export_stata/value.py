"""Section 6 (does FEWS NET know something others don't?), Tables 2, 3 and the reports table:
data for stata/03_contribution.do, 04_official.do and 05_text_prices.do.

The gradient-boosted (and, for the reports, penalised logistic) predictions stay in Python and are
exported as out-of-sample predictions; Stata does the regressions, AUCs and arithmetic.

  contrib_ipc_areas.csv   Cadre Harmonise / IPC area x FEWS NET round (33_fewsnet_contribution.py, part B):
                          next independent analysis in Crisis+ (ipc3), latest one (ipc_last3), and for each
                          baseline (_r raw data, _i raw data + latest CH/IPC) the cross-fitted prediction of
                          ipc3 without (q) and with (qf) FEWS NET, and FEWS NET's contribution c_cur3, c_fc3
                          (signal minus its cross-fitted baseline prediction). Recomputed here with the same
                          code and seeds as 33 (that script does not save them).
  contrib_panel.csv       FEWS NET area x round: forecast fc3, its baseline predictions (b_fc3 raw, bi_fc3
                          raw + IPC) and contributions (c_fc3, ci_fc3)
  fv_panel.csv            FEWS NET area x round (32_forecast_value.py): outcomes a3 (mapped) and n3 (need),
                          public part of the forecast pub3 and added judgment added3, cell = country x round
  val_aid_panel.csv       country x round: log humanitarian funding next 6 months and previous 6 months
                          (31_aid_response.py panel())
  official.csv            official projections scored against the next official analysis (34)
  text_panel.csv          pilot area x round, Somalia/Ethiopia/Sudan, with report-text and survey features (53)
  text_preds.csv          cross-fitted escalation predictions, map alone and map + text (53)
  text_mentions.csv       area mentions in the reports with the stated current phase (extraction check)
  text_reports.csv        the pilot reports (country, type)
  price_preds.csv         cross-fitted predictions with and without price data (55)
  fdw_markets.csv         markets in FEWS NET's price warehouse, flagged if any series is not WFP-sourced
Table reference values: python_tables_value.csv (Tables 2 and 3 and the reports table).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import INP, TAB, load, periods_to_str, table_refs  # noqa: E402


def contribution_ipc():
    M33 = load("m33", "33_fewsnet_contribution.py")
    k = pd.read_parquet(INP / "panel" / "fewsnet_contribution_ipc_areas.parquet")
    k["cell"] = k.iso3 + "_" + k.r.astype(str)
    out = k[["key", "r", "iso3", "cell", "ipc3", "ipc_last3", "cur3", "fc3"]].copy()
    for bl, feats in [("r", M33.RAW), ("i", M33.RAW + ["ipc_last3", "ipc_last_share3"])]:
        out[f"q_{bl}"] = M33.crossfit(k, "ipc3", feats)
        out[f"qf_{bl}"] = M33.crossfit(k, "ipc3", feats + ["cur3", "fc3"])
        for s in ["cur3", "fc3"]:
            out[f"c_{s}_{bl}"] = k[s] - M33.crossfit(k, s, feats, binary=False)
    return periods_to_str(out)


def export(out):
    # --- 03_contribution.do
    contribution_ipc().to_csv(out / "contrib_ipc_areas.csv", index=False)
    p = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet")
    periods_to_str(p[["country_code", "iso3", "fnid", "r", "fc3", "b_fc3", "c_fc3", "bi_fc3", "ci_fc3"]]) \
        .to_csv(out / "contrib_panel.csv", index=False)
    f = pd.read_parquet(INP / "panel" / "forecast_value_panel.parquet")
    periods_to_str(f[["country_code", "iso3", "fnid", "r", "cell", "a3", "n3", "pub3", "added3"]]) \
        .to_csv(out / "fv_panel.csv", index=False)
    AID = load("aid", "31_aid_response.py")
    s = AID.panel()
    periods_to_str(s[["country_code", "report_month", "iso3", "round", "f_all", "f_all_lag", "f_food", "f_food_lag"]]) \
        .to_csv(out / "val_aid_panel.csv", index=False)

    # --- 04_official.do
    o = pd.read_parquet(INP / "panel" / "official_projections.parquet")
    periods_to_str(o[["source", "iso3", "cell", "year", "next3", "proj3", "proj_share3", "fews_fc3", "fews_cur3",
                      "last3"]]).to_csv(out / "official.csv", index=False)

    # --- 05_text_prices.do
    M53 = load("m53", "53_text_value.py")
    t, _ = M53.build()
    cols = ["fnid", "country_code", "r", "cell", "cl", "phase", "next_phase", "fc_phase", "has_text", "next4",
            "need4", "fc4", "flag", "fc_flag"] + M53.TEXT + M53.DATA
    t = periods_to_str(t[cols])
    t["has_text"] = t.has_text.astype(int)
    t.to_csv(out / "text_panel.csv", index=False)
    pd.read_parquet(INP / "reports" / "text_value_preds.parquet").to_csv(out / "text_preds.csv", index=False)
    m = pd.read_parquet(INP / "reports" / "mentions.parquet").dropna(subset=["fnid"])
    m = m[m.level.isin(["admin2", "unit", "zone"]) & m.cc.isin(M53.PILOT)].copy()
    m["cur"] = pd.to_numeric(m.current_phase, errors="coerce")
    m["order"] = np.arange(len(m))              # pandas' groupby().first() takes the first non-missing value
    m[["order", "name", "i", "fnid", "month", "cur"]].rename(columns={"month": "r"}) \
        .assign(r=lambda x: x.r.astype(str).str[:7]).to_csv(out / "text_mentions.csv", index=False)
    rep = pd.read_parquet(INP / "reports" / "reports.parquet")
    rep[rep.cc.isin(M53.PILOT)][["cc", "type"]].rename(columns={"type": "rtype"}).to_csv(out / "text_reports.csv", index=False)
    pv = pd.read_parquet(INP / "panel" / "price_value_preds.parquet")
    ren = {"base": "base", "+WFP prices": "wfp", "+FEWS NET prices": "fews", "+both": "both", "+forecast": "fc",
           "raw": "raw", "raw +WFP prices": "rawwfp", "raw +FEWS NET prices": "rawfews", "raw +both": "rawboth",
           "raw +FEWS NET map and forecast": "rawmap"}
    pv.rename(columns=ren).to_csv(out / "price_preds.csv", index=False)
    fp = pd.read_parquet(INP / "prices_fdw/prices.parquet", columns=["source_organization", "market_id"])
    fp["own"] = (~fp.source_organization.str.contains("WFP", case=False, na=False)).astype(int)
    fp.groupby("market_id").own.max().reset_index().to_csv(out / "fdw_markets.csv", index=False)

    # --- table reference values, as printed
    rows = []
    fmt = lambda v, d=3: f"{v:.{d}f}"
    R = pd.read_csv(TAB / "fewsnet_contribution.csv")
    R = R[R.block.str.startswith("accuracy") & (R["sample"] == "areas not in Crisis at last analysis")]
    cols = [("raw data", "current map"), ("raw data", "forecast"), ("raw data", "both"),
            ("raw data + latest Cadre Harmonise / IPC", "current map"),
            ("raw data + latest Cadre Harmonise / IPC", "forecast"), ("raw data + latest Cadre Harmonise / IPC", "both")]
    for j, (bl, sp) in enumerate(cols, 1):
        d = R[(R.baseline == bl) & (R.spec == sp)]
        for term, tn in [("c_cur3", "cur"), ("c_fc3", "fc")]:
            x = d[d.term == term]
            if len(x):
                rows += [(f"tab_contribution_{tn}_c{j}", fmt(x.coef.iloc[0])), (f"tab_contribution_{tn}se_c{j}", fmt(x.se.iloc[0]))]
        rows += [(f"tab_contribution_q_c{j}", fmt(d.q_coef.iloc[0], 2)), (f"tab_contribution_n_c{j}", f"{int(d.n.iloc[0]):,}"),
                 (f"tab_contribution_g_c{j}", str(int(d.countries.iloc[0])))]
    O = pd.read_csv(TAB / "official_projections.csv")
    specs = ["official projection only", "FEWS NET forecast only", "both", "both + last official analysis",
             "both + last analysis + FEWS NET current map"]
    for samp, sk in [("all areas", "all"), ("not in Crisis at the last analysis", "new")]:
        d = O[O["sample"] == samp]
        for j, sp in enumerate(specs, 1):
            for term in ["proj3", "fews_fc3", "last3", "fews_cur3"]:
                if sk == "new" and term == "last3":       # constant 0 in this sample; not in the table
                    continue
                x = d[(d.spec == sp) & (d.term == term)]
                if len(x):
                    tn = term.replace("_", "")
                    rows += [(f"tab_official_{sk}_{tn}_c{j}", fmt(x.coef.iloc[0])), (f"tab_official_{sk}_{tn}se_c{j}", fmt(x.se.iloc[0]))]
            x = d[d.spec == sp].iloc[0]
            rows += [(f"tab_official_{sk}_n_c{j}", f"{int(x.n):,}"), (f"tab_official_{sk}_g_c{j}", str(int(x.countries)))]
    E = pd.read_csv(TAB / "text_value_escalation.csv")
    tcols = [("next4", "map"), ("next4", "map+text"), ("next4", "map+text+data"),
             ("need4", "map"), ("need4", "map+text"), ("need4", "map+text+data")]
    for j, (y, mdl) in enumerate(tcols, 1):
        d = E[(E.outcome == y) & (E.model == mdl)]
        for x in d.itertuples():
            v = x.var.replace("_", "")
            rows += [(f"tab_text_{v}_c{j}", fmt(x.coef)), (f"tab_text_{v}se_c{j}", fmt(x.se))]
        rows.append((f"tab_text_n_c{j}", f"{int(d.n.iloc[0]):,}"))
    table_refs(out, "value", rows)
