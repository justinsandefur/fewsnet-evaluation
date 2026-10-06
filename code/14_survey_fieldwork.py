"""Fieldwork dates for non-DHS surveys with child anthropometry, and their
overlap with FEWS NET classifications. Extends the DHS figures from
08_coverage.py to MICS, UNHCR refugee-camp surveys and LSMS.

Dates come from the World Bank Microdata Library metadata (coll_dates). Where
only years are given, the whole of those years is used and the survey is
flagged as having approximate dates.

Outputs: input/surveys/fieldwork_dates.csv, output/tables/all_surveys_fews_overlap.csv,
         output/figures/coverage_grfc.pdf (redrawn with all survey types),
         output/figures/survey_fieldwork_phase.pdf
"""
import importlib.util
import json
import textwrap
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
API = "https://microdata.worldbank.org/index.php/api/catalog"
spec = importlib.util.spec_from_file_location("cov", ROOT / "code" / "08_coverage.py")
COV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(COV)

plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 11, "axes.titleweight": "bold",
                     "axes.titlelocation": "left"})
FAM_COL = {"DHS (GPS)": "#1f4e79", "MICS (region)": "#2a9d8f", "UNHCR camps": "#e9c46a",
           "LSMS (GPS)": "#8c8c8c"}


def coll_dates(idno: str):
    cache = INP / "surveys" / "meta" / f"{idno}.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        try:
            j = requests.get(f"{API}/{idno}", timeout=120).json()
        except (requests.RequestException, ValueError):
            j = {}
        cache.write_text(json.dumps(j))
        time.sleep(0.3)
    j = json.loads(cache.read_text())
    cd = (j.get("dataset", {}).get("metadata", {}).get("study_desc", {}).get("study_info", {})
            .get("coll_dates") or [])
    starts = [d.get("start", "") for d in cd if d.get("start")]
    ends = [d.get("end", "") or d.get("start", "") for d in cd if d.get("start")]
    if not starts:
        return None, None, True
    s, e = min(starts), max(ends)
    approx = len(s) < 7 or len(e) < 7
    s = pd.Period(s[:7] if len(s) >= 7 else s[:4] + "-01", "M")
    e = pd.Period(e[:7] if len(e) >= 7 else e[:4] + "-12", "M")
    return s, e, approx


def fieldwork_table():
    s = pd.read_csv(TAB / "anthro_surveys_2011on.csv")
    other = s[s.family != "DHS (GPS)"].copy()
    rows = []
    for r in other.itertuples():
        a, b, approx = coll_dates(r.survey)
        rows.append({**r._asdict(), "start": a, "end": b, "approx_dates": approx})
    o = pd.DataFrame(rows).drop(columns=["Index"])
    o.loc[o.start.isna(), "start"] = o.loc[o.start.isna(), "year"].apply(lambda y: pd.Period(f"{int(y)}-01", "M"))
    o.loc[o.end.isna(), "end"] = o.loc[o.end.isna(), "year"].apply(lambda y: pd.Period(f"{int(y)}-12", "M"))
    dhs = pd.read_csv(INP / "dhs" / "dhs_surveys.csv")
    dhs = dhs[(dhs.n_wasted.fillna(0) > 0) & dhs.gps_file]
    d = s[s.family == "DHS (GPS)"].merge(dhs[["SurveyId", "FieldworkStart", "FieldworkEnd"]],
                                         left_on="survey", right_on="SurveyId")
    d["start"] = pd.to_datetime(d.FieldworkStart).dt.to_period("M")
    d["end"] = pd.to_datetime(d.FieldworkEnd).dt.to_period("M")
    d["approx_dates"] = False
    out = pd.concat([d[["family", "iso3", "year", "survey", "start", "end", "approx_dates"]],
                     o[["family", "iso3", "year", "survey", "start", "end", "approx_dates"]]], ignore_index=True)
    out.to_csv(INP / "surveys" / "fieldwork_dates.csv", index=False)
    return out


def overlap(surveys, codes):
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    grid = COV.monthly_status(cs, proj)
    iso3to2 = dict(zip(codes.iso3166a3, codes.iso3166a2))
    names = dict(zip(codes.iso3166a3, codes.preferred_name))
    rows = []
    for s in surveys.itertuples():
        cc = iso3to2.get(s.iso3)
        months = pd.period_range(s.start, s.end, freq="M")
        c = grid[(grid.country_code == cc) & grid.month.isin(months)]
        has = c.cs_recent.notna()
        if not has.any():
            continue
        rows.append({"family": s.family, "survey": s.survey, "iso3": s.iso3, "country": names.get(s.iso3, s.iso3),
                     "start": str(s.start), "end": str(s.end), "approx_dates": s.approx_dates,
                     "share3": (c.cs_recent[has] >= 3).mean(), "share4": (c.cs_recent[has] >= 4).mean(),
                     "areas3": int(c.loc[has & (c.cs_recent >= 3), "fnid"].nunique())})
    o = pd.DataFrame(rows)
    o.to_csv(TAB / "all_surveys_fews_overlap.csv", index=False)
    return o


def fig_fieldwork(o):
    o = o.copy()
    o["label"] = o.country.str.replace("Democratic Republic of the Congo", "DR Congo") \
        .str.replace("Central African Republic", "C. African Rep.") + " " + o.start.str[:4]
    o = o.sort_values("share3")
    fig, ax = plt.subplots(figsize=(10, max(6, 0.2 * len(o))))
    y = np.arange(len(o))
    ax.barh(y, o.share3, color=[FAM_COL[f] for f in o.family], height=0.75)
    ax.barh(y, o.share4, color="#c80000", height=0.35)
    ax.set_yticks(y)
    ax.set_yticklabels([l + (" *" if a else "") for l, a in zip(o.label, o.approx_dates)], fontsize=7.5)
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_xticklabels([f"{v:.0%}" for v in np.linspace(0, 1, 6)])
    ax.set_xlabel("Share of the country's FEWS NET map areas in Crisis or worse during the survey's fieldwork")
    ax.set_title("How much of each survey's fieldwork took place in a food crisis?")
    from matplotlib.patches import Patch
    h = [Patch(color=c, label=f"{f.split(' (')[0].replace('UNHCR camps', 'UNHCR refugee-camp')} survey: "
               "share of areas in Crisis or worse (Phase 3+)") for f, c in FAM_COL.items() if f in set(o.family)]
    h.append(Patch(color="#c80000", label="Thin red bar: share of areas in Emergency or worse (Phase 4+)"))
    ax.legend(handles=h, frameon=False, loc="lower right", fontsize=8.5)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.text(0.01, 0.005, textwrap.fill("Surveys since 2011 that measured children's weight and height, in countries with FEWS NET "
             "maps during fieldwork. * Fieldwork months not published in the catalogue; the whole survey year is used. "
             "Shares count map areas, not people.\nSources: DHS Program; World Bank Microdata Library (MICS, UNHCR, "
             "LSMS); FEWS NET.", 170), fontsize=8, color="#555")
    fig.savefig(FIG / "survey_fieldwork_phase.pdf")
    plt.close(fig)


def fig_coverage(surveys):
    g = pd.read_csv(TAB / "grfc_country_years.csv")
    sy = {}
    for s in surveys.itertuples():
        for y in range(s.start.year, s.end.year + 1):
            sy.setdefault((s.iso3, y), set()).add(s.family)
    def cat(r):
        f = sy.get((r.iso3, r.year), set())
        if not r.fews:
            return "Not covered by FEWS NET"
        if "DHS (GPS)" in f or "LSMS (GPS)" in f:
            return "FEWS NET, and a DHS (or LSMS) survey in the field"
        if "MICS (region)" in f:
            return "FEWS NET, and a MICS survey in the field"
        if "UNHCR camps" in f:
            return "FEWS NET, and a UNHCR camp survey in the field"
        return "FEWS NET only, no survey measuring children"
    g["cat"] = g.apply(cat, axis=1)
    order = [("FEWS NET, and a DHS (or LSMS) survey in the field", FAM_COL["DHS (GPS)"]),
             ("FEWS NET, and a MICS survey in the field", FAM_COL["MICS (region)"]),
             ("FEWS NET, and a UNHCR camp survey in the field", FAM_COL["UNHCR camps"]),
             ("FEWS NET only, no survey measuring children", "#9dc3e6"),
             ("Not covered by FEWS NET", "#d9d9d9")]
    t = g.groupby(["year", "cat"]).p3.sum().unstack(fill_value=0) / 1e6
    fig, ax = plt.subplots(figsize=(10, 5.2))
    bottom = np.zeros(len(t))
    for c, col in order:
        if c in t:
            ax.bar(t.index, t[c], bottom=bottom, color=col, label=c, width=0.75)
            bottom += t[c].values
    ax.set_xticks(t.index)
    ax.set_ylabel("People in Crisis or worse (millions)")
    ax.set_title("Who counted the world's hungry, and did anyone measure their children?")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.text(0.01, 0.005, textwrap.fill("People in Crisis or worse (IPC Phase 3+) by country-year, from the Global Report on Food "
             "Crises database, 2016-2025. A survey is counted if its fieldwork fell in that year and it measured "
             "children's weight and height.\nYear-to-year changes partly reflect which countries had data. "
             "Sources: Global Report on Food Crises; FEWS NET; DHS Program; World Bank Microdata Library.", 170),
             fontsize=8, color="#555")
    fig.savefig(FIG / "coverage_grfc.pdf")
    plt.close(fig)
    tot3, tot4 = g.p3.sum(), g.p4plus.sum()
    shares = {c: {"p3": round(g.loc[g.cat == c, "p3"].sum() / tot3, 3),
                  "p4": round(g.loc[g.cat == c, "p4plus"].sum() / tot4, 3)} for c, _ in order}
    return shares


def main():
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    s = fieldwork_table()
    o = overlap(s, codes)
    fig_fieldwork(o)
    shares = fig_coverage(s)
    k = json.loads((TAB / "key_numbers.json").read_text())
    k["fieldwork_all"] = {
        "surveys": int(len(o)), "by_family": o.family.value_counts().to_dict(),
        "approx_dates": int(o.approx_dates.sum()),
        "areas3_by_family": o.groupby("family").areas3.sum().to_dict(),
        "surveys_share3_over_10pct_by_family": o[o.share3 > 0.1].family.value_counts().to_dict(),
        "surveys_any4_by_family": o[o.share4 > 0].family.value_counts().to_dict(),
    }
    k["coverage_same_year"] = shares
    (TAB / "key_numbers.json").write_text(json.dumps(k, indent=1, default=str))
    print(json.dumps({x: k[x] for x in ["fieldwork_all", "coverage_same_year"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
