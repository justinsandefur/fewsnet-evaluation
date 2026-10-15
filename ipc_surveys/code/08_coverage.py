"""Coverage and feasibility diagnostics for the concept note.

No microdata are used. The script answers:
  1. What share of the world's food crises (as counted by the Global Report
     on Food Crises) does FEWS NET cover, and what share has a DHS survey with
     child anthropometry and GPS in the same country-year?
  2. For each DHS survey in a FEWS NET country since 2011, how much of the
     fieldwork happened in places FEWS NET classified as Crisis or worse, and
     had those places been forecast in advance?
  3. A replication of the standard self-consistency check: how often does a
     FEWS NET projection match FEWS NET's own later classification, compared
     with a naive "no change" forecast?
  4. Humanitarian funding: share going to FEWS NET countries, the food
     sector, and from the United States; the largest single emergencies.
  5. News coverage (if the GDELT pull has been run).

Outputs: output/tables/*.csv, output/tables/key_numbers.json, output/figures/*.pdf
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
TAB.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
KEY = {}

# DHS uses its own two-letter codes; these differ from ISO 3166.
DHS_TO_ISO2 = {"BU": "BI", "MD": "MG", "NI": "NE", "NC": "NI", "GU": "GT", "NM": "NA",
               "OS": "SO", "LB": "LR", "IA": "IN", "KY": "KG", "TJ": "TJ", "MB": "MD",
               "DR": "DO", "EK": "GQ", "KM": "KM", "ES": "SV", "SZ": "SZ"}

plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False})
C1, C2, C3 = "#1f4e79", "#c55a11", "#a6a6a6"


def country_codes() -> pd.DataFrame:
    path = INP / "fewsnet" / "countries.json"
    if not path.exists():
        path.write_text(requests.get("https://fdw.fews.net/api/country/?format=json",
                                     timeout=120).text)
    c = pd.DataFrame(json.loads(path.read_text()))
    return c[["iso3166a2", "iso3166a3", "preferred_name"]].rename(
        columns={"iso3166a2": "iso2", "iso3166a3": "iso3", "preferred_name": "name"})


def load():
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    dhs = pd.read_csv(INP / "dhs" / "dhs_surveys.csv")
    dhs["iso2"] = dhs.DHS_CountryCode.replace(DHS_TO_ISO2)
    dhs["anthro"] = dhs.n_wasted.fillna(0) > 0
    for c in ["FieldworkStart", "FieldworkEnd"]:
        dhs[c] = pd.to_datetime(dhs[c])
    return cs, proj, dhs


# ---------------------------------------------------------------- 1. GRFC
def grfc_coverage(cs, dhs, codes):
    g = pd.read_excel(INP / "ipc" / "grfc_afi_database_2016-2025_september_update.xlsx")
    g.columns = [c.strip() for c in g.columns]
    g = g.rename(columns={"ISO Code 3": "iso3", "Year of reference": "year",
                          "Population in Phase 3 or above #": "p3",
                          "Population in Phase 4 #": "p4", "Population Phase 5 #": "p5",
                          "Countries/territories": "name_grfc", "Source": "source"})
    # Countries the report selected as food crises and for which it had data
    g = g[g["Selection in the GRFC"].astype(str).str.upper().str.startswith("Y")
          & g["Data availability"].astype(str).str.upper().str.startswith("Y")]
    for c in ["p3", "p4", "p5"]:
        g[c] = pd.to_numeric(g[c], errors="coerce")
    g = g.merge(codes[["iso2", "iso3"]], on="iso3", how="left")
    # A few territories share a country code with sub-groups; keep one row per
    # country-year, summing populations when the report splits a country.
    g = g.groupby(["iso3", "iso2", "year"], dropna=False).agg(
        name=("name_grfc", "first"), source=("source", "first"),
        p3=("p3", "sum"), p4=("p4", "sum"), p5=("p5", "sum")).reset_index()

    fy = cs.assign(year=cs.month.dt.year).groupby(["country_code", "year"]).size()
    g["fews"] = [(i, y) in fy.index for i, y in zip(g.iso2, g.year)]

    d = dhs[dhs.anthro & dhs.gps_file]
    dy = {(r.iso2, y) for r in d.itertuples()
          for y in range(r.FieldworkStart.year, r.FieldworkEnd.year + 1)}
    g["dhs_same_year"] = [(i, y) in dy for i, y in zip(g.iso2, g.year)]
    since = d[d.FieldworkStart >= "2011-01-01"].groupby("iso2").size()
    g["dhs_any_since_2011"] = g.iso2.isin(since.index)
    g["p4plus"] = g.p4.fillna(0) + g.p5.fillna(0)
    g.to_csv(TAB / "grfc_country_years.csv", index=False)

    rows = []
    for label, sub in [("all years 2016-2025", g), ("2016-2024 (pre-cut)", g[g.year <= 2024])]:
        tot3, tot4 = sub.p3.sum(), sub.p4plus.sum()
        rows.append({
            "window": label, "country_years": len(sub), "countries": sub.iso3.nunique(),
            "share_cy_fews": sub.fews.mean(),
            "share_p3_fews": sub.loc[sub.fews, "p3"].sum() / tot3,
            "share_p4_fews": sub.loc[sub.fews, "p4plus"].sum() / tot4,
            "share_p3_dhs_same_year": sub.loc[sub.dhs_same_year, "p3"].sum() / tot3,
            "share_p3_fews_and_dhs_same_year": sub.loc[sub.fews & sub.dhs_same_year, "p3"].sum() / tot3,
            "share_p4_fews_and_dhs_same_year": sub.loc[sub.fews & sub.dhs_same_year, "p4plus"].sum() / tot4,
            "share_p4_countries_with_any_dhs_since_2011": sub.loc[sub.dhs_any_since_2011, "p4plus"].sum() / tot4,
        })
    summ = pd.DataFrame(rows)
    summ.to_csv(TAB / "coverage_summary.csv", index=False)
    KEY["grfc"] = summ.round(3).to_dict("records")

    # Which countries carry the Phase 4+ caseload without any usable DHS survey?
    holes = (g[~g.dhs_any_since_2011].groupby(["iso3", "name"])
               .agg(p4plus=("p4plus", "sum"), p3=("p3", "sum"), fews=("fews", "max"))
               .sort_values("p4plus", ascending=False).reset_index())
    holes["share_of_all_p4plus"] = holes.p4plus / g.p4plus.sum()
    holes.head(15).to_csv(TAB / "holes_no_dhs.csv", index=False)
    KEY["holes_top"] = holes.head(8)[["name", "share_of_all_p4plus", "fews"]].round(3).to_dict("records")

    # Figure: Phase 3+ population by year and coverage status
    by = g.groupby("year").apply(lambda x: pd.Series({
        "FEWS NET and DHS survey that year": x.loc[x.fews & x.dhs_same_year, "p3"].sum(),
        "FEWS NET only": x.loc[x.fews & ~x.dhs_same_year, "p3"].sum(),
        "Not covered by FEWS NET": x.loc[~x.fews, "p3"].sum()})) / 1e6
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    bottom = np.zeros(len(by))
    for col, colr in zip(by.columns, [C2, C1, C3]):
        ax.bar(by.index, by[col], bottom=bottom, color=colr, label=col, width=0.75)
        bottom += by[col].values
    ax.set_ylabel("People in Crisis or worse (millions)")
    ax.set_xticks(by.index)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "coverage_grfc.pdf")
    plt.close(fig)
    by.to_csv(TAB / "coverage_by_year.csv")
    return g


# ---------------------------------------------------------------- 2. DHS x FEWS NET
def monthly_status(cs, proj):
    """FEWS NET publishes a current-situation map only three times a year
    (four before 2016), so for any calendar month we assemble:
      cs_recent: the latest current-situation phase from the past 0-3 months
      ml1:       the near-term projection covering the month (made 0-3 months before)
      ml2:       the medium-term projection covering the month (made 4-8 months before)
    """
    carry = pd.concat([cs.assign(month=cs.month + k, age=k) for k in range(4)])
    carry = (carry.sort_values("age").drop_duplicates(["fnid", "month"])
                  [["country_code", "fnid", "month", "phase"]].rename(columns={"phase": "cs_recent"}))
    def latest(sc):
        x = proj[proj.scenario == sc].sort_values("report_month")
        return (x.drop_duplicates(["fnid", "month"], keep="last")
                 [["country_code", "fnid", "month", "phase"]].rename(columns={"phase": sc.lower()}))
    grid = carry.merge(latest("ML1"), on=["country_code", "fnid", "month"], how="outer") \
                .merge(latest("ML2"), on=["country_code", "fnid", "month"], how="outer")
    return grid


def dhs_overlap(cs, proj, dhs):
    fews_cc = set(cs.country_code)
    d = dhs[dhs.anthro & dhs.iso2.isin(fews_cc) & (dhs.FieldworkEnd >= "2011-01-01")].copy()
    grid = monthly_status(cs, proj)
    out = []
    for s in d.itertuples():
        months = pd.period_range(s.FieldworkStart, s.FieldworkEnd, freq="M")
        c = grid[(grid.country_code == s.iso2) & grid.month.isin(months)]
        mid = s.FieldworkStart + (s.FieldworkEnd - s.FieldworkStart) / 2
        # share of under-5s whose first 1,000 days (from conception) fall in
        # the FEWS NET era (classifications start January 2011)
        born_after = np.clip(((mid - pd.Timestamp("2011-10-01")).days / 30.4) / 60, 0, 1)
        has = c.cs_recent.notna()
        out.append({
            "survey": s.SurveyId, "country": s.CountryName, "iso2": s.iso2,
            "fieldwork": f"{s.FieldworkStart:%Y-%m} to {s.FieldworkEnd:%Y-%m}",
            "gps": s.gps_file, "n_wasting": s.n_wasted, "n_stunting": s.n_stunted,
            "unit_months": int(has.sum()),
            "share_phase3plus": (c.cs_recent[has] >= 3).mean() if has.any() else np.nan,
            "share_phase4plus": (c.cs_recent[has] >= 4).mean() if has.any() else np.nan,
            "share_with_ml1": c.ml1[has].notna().mean() if has.any() else np.nan,
            "share_ml1_3plus": (c.ml1[has] >= 3).mean() if has.any() else np.nan,
            "share_with_ml2": c.ml2[has].notna().mean() if has.any() else np.nan,
            "share_ml2_3plus": (c.ml2[has] >= 3).mean() if has.any() else np.nan,
            "share_born_in_fews_era": born_after,
            "n_areas_3plus": int(c.loc[c.cs_recent >= 3, "fnid"].nunique()),
            "n_areas_4plus": int(c.loc[c.cs_recent >= 4, "fnid"].nunique()),
            "n_areas": int(c.loc[has, "fnid"].nunique()),
        })
    o = pd.DataFrame(out)
    o["est_children_phase3plus"] = (o.n_wasting * o.share_phase3plus).round()
    o["est_children_phase4plus"] = (o.n_wasting * o.share_phase4plus).round()
    o["est_children_stunting_cohort"] = (o.n_stunting * o.share_born_in_fews_era).round()
    o.to_csv(TAB / "dhs_fews_overlap.csv", index=False)
    ok = o[o.gps & (o.unit_months > 0)]
    KEY["dhs"] = {
        "surveys_anthro_in_fews_countries_2011on": int(len(o)),
        "with_gps_and_fews_data": int(len(ok)),
        "countries": int(ok.iso2.nunique()),
        "children_measured": int(ok.n_wasting.sum()),
        "est_children_in_phase3plus_units": int(ok.est_children_phase3plus.sum()),
        "est_children_in_phase4plus_units": int(ok.est_children_phase4plus.sum()),
        "surveys_with_any_phase4plus": int((ok.share_phase4plus > 0).sum()),
        "surveys_with_phase3plus_share_over_10pct": int((ok.share_phase3plus > 0.10).sum()),
        "est_children_stunting_cohort": int(ok.est_children_stunting_cohort.sum()),
        "areas_3plus_during_fieldwork": int(ok.n_areas_3plus.sum()),
        "areas_4plus_during_fieldwork": int(ok.n_areas_4plus.sum()),
        "areas_during_fieldwork": int(ok.n_areas.sum()),
        "median_share_with_ml1": float(ok.share_with_ml1.median()),
        "median_share_with_ml2": float(ok.share_with_ml2.median()),
    }

    # Figure: each survey, share of fieldwork unit-months in Crisis or worse
    p = ok.sort_values("share_phase3plus")
    fig, ax = plt.subplots(figsize=(5.5, max(3, 0.12 * len(p))))
    y = np.arange(len(p))
    ax.barh(y, p.share_phase3plus, color=C1, label="Crisis or worse (Phase 3+)")
    ax.barh(y, p.share_phase4plus, color=C2, label="Emergency or worse (Phase 4+)")
    ax.set_yticks(y)
    names = p.country.replace({"Congo Democratic Republic": "DR Congo"})
    ax.set_yticklabels(names + " " + p.fieldwork.str[:4], fontsize=6.5)
    ax.set_xlabel("Share of FEWS NET map areas during fieldwork months")
    ax.set_xlim(0, 1)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "dhs_fieldwork_phase.pdf")
    plt.close(fig)
    return o


# ---------------------------------------------------------------- 3. self-consistency
def self_consistency(cs, proj):
    """Projection made in report month r for target months m, scored against
    the current-situation classification later published for month m. The
    naive benchmark forecasts that the phase at the time of the report persists."""
    p = proj[proj.lead >= 1].merge(cs[["fnid", "month", "phase"]].rename(columns={"phase": "actual"}),
                                   on=["fnid", "month"])
    base = cs[["fnid", "month", "phase"]].rename(columns={"month": "report_month", "phase": "at_report"})
    p = p.merge(base, on=["fnid", "report_month"], how="left")
    # One score per projection: the most severe outcome during the window,
    # which is how FEWS NET maps the projected phase.
    q = p.groupby(["country_code", "fnid", "scenario", "report_month"]).agg(
        proj=("phase", "first"), actual=("actual", "max"), at_report=("at_report", "first"),
        assist=("assist_flag", "first")).reset_index().dropna(subset=["at_report"])
    q["hit"] = q.proj == q.actual
    q["naive_hit"] = q.at_report == q.actual
    q["new3"] = (q.at_report < 3) & (q.actual >= 3)
    rows = []
    for sc, x in q.groupby("scenario"):
        rows.append({
            "scenario": sc, "n": len(x), "accuracy": x.hit.mean(), "naive_accuracy": x.naive_hit.mean(),
            "within_one_phase": ((x.proj - x.actual).abs() <= 1).mean(),
            "accuracy_when_actual_3plus": x.loc[x.actual >= 3, "hit"].mean(),
            "accuracy_when_actual_4plus": x.loc[x.actual >= 4, "hit"].mean(),
            "n_new_crises": int(x.new3.sum()),
            "share_new_crises_forecast": (x.loc[x.new3, "proj"] >= 3).mean(),
            "false_alarm_rate": ((x.proj >= 3) & (x.actual < 3) & (x.at_report < 3)).sum()
                                / max(1, ((x.actual < 3) & (x.at_report < 3)).sum()),
            "share_under_predicted": (x.proj < x.actual).sum() / max(1, (~x.hit).sum()),
        })
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "self_consistency.csv", index=False)
    KEY["self_consistency"] = r.round(3).to_dict("records")
    conf = pd.crosstab(q[q.scenario == "ML2"].proj, q[q.scenario == "ML2"].actual)
    conf.to_csv(TAB / "confusion_ml2.csv")
    x = q[q.scenario == "ML2"].assign(hit4=lambda d: d.hit.where(d.actual >= 4),
                                      caught=lambda d: (d.proj >= 3).where(d.new3))
    bycountry = x.groupby("country_code").agg(
        n=("hit", "size"), accuracy=("hit", "mean"), naive=("naive_hit", "mean"),
        accuracy_when_4plus=("hit4", "mean"), new_crises=("new3", "sum"),
        share_new_crises_forecast=("caught", "mean")).round(3)
    bycountry.to_csv(TAB / "self_consistency_by_country.csv")
    return q


# ---------------------------------------------------------------- 4. funding
def funding(cs, codes):
    path = INP / "fts" / "fts_flows.parquet"
    if not path.exists():
        print("FTS not yet downloaded; skipping")
        return None
    f = pd.read_parquet(path)
    f = f[(f.boundary == "incoming") | f.boundary.isna()]
    f = f[f.status.isin(["paid", "commitment"])]
    f["year"] = pd.to_numeric(f.usage_year.str[:4], errors="coerce")
    KEY["fts_flows"] = int(len(f))
    fews_names = set(codes[codes.iso2.isin(set(cs.country_code))].name)
    fews_names |= {"Congo, The Democratic Republic of the", "Democratic Republic of the Congo",
                   "occupied Palestinian territory"} & set(f.dest_country.dropna())
    f["to_fews"] = f.dest_country.isin(fews_names)
    f["food"] = f.cluster.fillna("").str.contains("Food Security|Nutrition", regex=True)
    f["us"] = f.donor.fillna("").str.contains("United States")
    f["has_decision_date"] = f.decision_date.notna()
    y = f[f.year.between(2011, 2025)].groupby("year").apply(lambda x: pd.Series({
        "total_bn": x.amount_usd.sum() / 1e9,
        "share_to_fews_countries": x.loc[x.to_fews, "amount_usd"].sum() / x.amount_usd.sum(),
        "share_food_nutrition": x.loc[x.food, "amount_usd"].sum() / x.amount_usd.sum(),
        "us_share_of_food_to_fews": x.loc[x.food & x.to_fews & x.us, "amount_usd"].sum()
                                    / max(1, x.loc[x.food & x.to_fews, "amount_usd"].sum()),
        "share_sector_unspecified": x.loc[x.cluster.isna(), "amount_usd"].sum() / x.amount_usd.sum(),
        "share_with_decision_date": x.loc[x.has_decision_date, "amount_usd"].sum() / x.amount_usd.sum(),
    }))
    y.to_csv(TAB / "funding_by_year.csv")
    KEY["funding"] = y.round(3).reset_index().to_dict("records")
    # Largest single named emergencies each year (the "competing crises")
    e = (f[f.emergency.notna() & f.year.between(2005, 2025)]
         .groupby(["year", "emergency"]).amount_usd.sum().reset_index())
    tot = f.groupby("year").amount_usd.sum()
    e["share_of_year"] = e.amount_usd / e.year.map(tot)
    top = e.sort_values("share_of_year", ascending=False).groupby("year").head(2) \
        .sort_values(["year", "share_of_year"], ascending=[True, False])
    top.to_csv(TAB / "largest_emergencies.csv", index=False)
    KEY["mega_emergencies"] = top[top.share_of_year > 0.05].round(3).to_dict("records")

    # Figure: monthly commitments (by decision date) for food and nutrition in
    # FEWS NET countries vs. all other humanitarian funding, 2010-2025.
    f["dmonth"] = pd.to_datetime(f.decision_date, errors="coerce").dt.to_period("Q")
    q = f[f.dmonth.notna() & (f.dmonth >= pd.Period("2010Q1")) & (f.dmonth <= pd.Period("2025Q4"))]
    s1 = q[q.food & q.to_fews].groupby("dmonth").amount_usd.sum() / 1e9
    s2 = q[~(q.food & q.to_fews)].groupby("dmonth").amount_usd.sum() / 1e9
    fig, ax = plt.subplots(figsize=(5.5, 2.9))
    x = s2.index.to_timestamp()
    ax.plot(x, s2.values, color=C3, lw=1.2, label="All other humanitarian funding")
    ax.plot(s1.index.to_timestamp(), s1.values, color=C1, lw=1.5,
            label="Food and nutrition, FEWS NET countries")
    top = max(s1.max(), s2.max()) * 1.25
    ax.set_ylim(0, top)
    for d, lab in [("2010-01", "Haiti"), ("2014-08", "Ebola"), ("2020-03", "COVID-19"),
                   ("2022-02", "Ukraine"), ("2023-10", "Gaza")]:
        ax.axvline(pd.Timestamp(d), color=C2, lw=0.7, ls=":")
        ax.text(pd.Timestamp(d), top * 0.99, " " + lab, fontsize=6.5, color=C2, va="top", ha="left")
    ax.set_ylabel("US$ billion per quarter")
    ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    fig.tight_layout()
    fig.savefig(FIG / "funding_quarterly.pdf")
    plt.close(fig)
    pd.DataFrame({"food_fews": s1, "other": s2}).to_csv(TAB / "funding_quarterly.csv")
    return f


# ---------------------------------------------------------------- 5. news
def news(cs, g):
    path = INP / "news" / "gdelt_monthly.csv"
    if not path.exists():
        print("GDELT not yet downloaded; skipping")
        return None
    n = pd.read_csv(path)
    n["year"] = n.month.str[:4].astype(int)
    # Coverage per person in need: articles per year relative to the number of
    # people in Emergency or worse that year (Global Report on Food Crises).
    ny = n.groupby(["iso2", "scope", "year"]).articles.sum().reset_index()
    need = g.groupby(["iso2", "year"]).agg(p4plus=("p4plus", "sum"), p3=("p3", "sum")).reset_index()
    m = ny.merge(need, on=["iso2", "year"])
    m = m[m.year.between(2017, 2025)]
    pooled = m.groupby(["iso2", "scope"]).agg(articles=("articles", "sum"), p4plus=("p4plus", "sum"),
                                              p3=("p3", "sum")).reset_index()
    pooled["per_100k_p3"] = pooled.articles / pooled.p3 * 1e5
    pooled["per_100k_p4"] = pooled.articles / pooled.p4plus.where(pooled.p4plus > 0) * 1e5
    pooled.to_csv(TAB / "news_per_person.csv", index=False)
    us = pooled[pooled.scope == "us"].dropna(subset=["per_100k_p3"]).sort_values("per_100k_p3")
    KEY["news_per_person_us"] = us[["iso2", "articles", "per_100k_p3"]].round(1).to_dict("records")
    fig, ax = plt.subplots(figsize=(5.5, max(2.5, 0.16 * len(us))))
    names = g.drop_duplicates("iso2").set_index("iso2").name.str.replace(
        r" \(.*\)|Republic of the |Democratic Republic of the ", "", regex=True)
    ax.barh(us.iso2.map(names).fillna(us.iso2), us.per_100k_p3, color=C1)
    ax.set_xscale("log")
    ax.set_xlabel("US online articles on hunger per 100,000 people in Crisis or worse, 2017-2025")
    fig.tight_layout()
    fig.savefig(FIG / "news_per_person.pdf")
    plt.close(fig)
    return m


def outage():
    """The 2025 shutdown and staggered restart, and country-level coverage
    switches in the archive (some of which are gaps in the archive rather
    than real changes in coverage)."""
    d = pd.read_parquet(INP / "fewsnet" / "classifications.parquet",
                        columns=["country_code", "report_month"])
    by = d.groupby("report_month").country_code.agg(lambda x: set(x))
    m = lambda s: by.get(pd.Period(s, "M"), set())
    before = m("2024-10")
    dark = [str(p) for p in pd.period_range("2025-01", "2025-07", freq="M") if not m(str(p))]
    first = m("2025-08")
    oct25 = m("2025-10")
    later = {cc: next((str(p) for p in by.index if p > pd.Period("2025-10", "M") and cc in by[p]), "not yet")
             for cc in before - oct25}
    y = (d.assign(y=d.report_month.dt.year).groupby(["country_code", "y"]).size()
           .unstack(fill_value=0) > 0)
    switches = int((y.astype(int).diff(axis=1).abs().iloc[:, 1:] > 0).sum().sum())
    KEY["outage"] = {"countries_before": len(before), "dark_months": dark,
                     "restart_aug25": sorted(first), "n_restart_aug25": len(first),
                     "n_oct25": len(oct25), "restored_later": later,
                     "coverage_switches_2011_2026": switches}
    pd.Series(later).to_csv(TAB / "outage_restoration.csv")


def main():
    codes = country_codes()
    cs, proj, dhs = load()
    KEY["fews_panel"] = {
        "countries": int(cs.country_code.nunique()), "units": int(cs.fnid.nunique()),
        "unit_months": int(len(cs)), "first": str(cs.month.min()), "last": str(cs.month.max()),
        "share_unit_months_3plus": float((cs.phase >= 3).mean()),
        "share_unit_months_4plus": float((cs.phase >= 4).mean()),
        "unit_months_phase5": int((cs.phase == 5).sum()),
        "share_assist_flag": float(cs.assist_flag.mean()),
    }
    g = grfc_coverage(cs, dhs, codes)
    dhs_overlap(cs, proj, dhs)
    self_consistency(cs, proj)
    funding(cs, codes)
    news(cs, g)
    outage()
    (TAB / "key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))
    print(json.dumps(KEY, indent=1, default=str))


if __name__ == "__main__":
    main()
