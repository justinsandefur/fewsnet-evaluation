"""Data for stata/01_errors.do and 02_need_onsets.do: Type I and Type II errors, famine,
accuracy against "nothing changes", need-defined emergencies and the descriptive counts.

All FEWS NET data are restricted to 2011-2024 (maps up to December 2024, forecasts issued up to
December 2024), as in code/40_paper.py. Months are "YYYY-MM" strings. Writes stata/data/:
  err_cs.csv          FEWS NET current-situation maps, area x month: phase, aid flag
  err_proj.csv        FEWS NET projections (ML1 and ML2), stored as spells to keep the file small:
                      one row per area x report month x run of consecutive forecast months with the
                      same phase and flag; months report_month + lead_from .. report_month + lead_to.
                      (Where the near- and medium-term scenarios overlap, both spells are kept.)
  err_panel.csv       area x map round panel (input/panel/forecast_value_panel.parquet): map, forecast
                      and next map; has_ipc = an official IPC/CH analysis in the last 3 years
                      (fewsnet_contribution_panel); has_geom = the area has a usable polygon (only for the
                      two case-study rounds, Somalia Feb 2017 and Ethiopia Oct 2015, which are mapped)
  err_grfc.csv        GRFC country-years 2016-2024 (selected, with data): people in Phase 3+ and 4+
  err_fts.csv         FTS humanitarian funding by year (usage year), summed over flows by: destination is a
                      FEWS NET country, food security / nutrition cluster, donor is the United States
  err_reports.csv     FEWS NET national reports (pilot countries): whether the report mentions famine risk
  err_report_months.csv  country x report month with any FEWS NET classification (incl. 2025)
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import INP, ROOT, load, periods_to_str  # noqa: E402


def export(out):
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    cs = cs[cs.month.dt.year <= 2024]
    c = cs[["country_code", "fnid", "month", "phase"]].assign(flag=cs.assist_flag.astype(int))
    periods_to_str(c).to_csv(out / "err_cs.csv", index=False)

    # projections as spells
    p = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    p = p[p.report_month.dt.year <= 2024].sort_values(["fnid", "scenario", "report_month", "month"])
    p["flag"] = p.assist_flag.astype(int)
    g = p.groupby(["fnid", "scenario", "report_month"])
    new = (p.lead != g.lead.shift() + 1) | (p.phase != g.phase.shift()) | (p.flag != g.flag.shift())
    p["spell"] = new.cumsum()
    s = p.groupby("spell").agg(fnid=("fnid", "first"), report_month=("report_month", "first"),
                               lead_from=("lead", "min"), lead_to=("lead", "max"),
                               phase=("phase", "first"), flag=("flag", "first"))
    periods_to_str(s).to_csv(out / "err_proj.csv", index=False)

    # area x round panel, with the case-study polygons
    v = pd.read_parquet(INP / "panel" / "forecast_value_panel.parquet")
    q = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet")[["fnid", "r", "ipc_last3"]]
    v = v.merge(q, on=["fnid", "r"], how="left")
    v["has_ipc"] = v.ipc_last3.notna().astype(int)
    case = ((v.country_code == "SO") & (v.r.astype(str) == "2017-02")) | \
           ((v.country_code == "ET") & (v.r.astype(str) == "2015-10"))
    u = gpd.read_file(INP / "fewsnet" / "units.gpkg")[["fnid", "geometry"]].drop_duplicates("fnid")
    u = u[u.fnid.isin(v[case].fnid)].copy()
    u["geometry"] = u.geometry.buffer(0)
    ok = set(u[u.geom_type.isin(["Polygon", "MultiPolygon"])].fnid)
    v["has_geom"] = np.where(case, v.fnid.isin(ok).astype(float), np.nan)
    keep = ["country_code", "fnid", "r", "phase", "fc_phase", "next_phase", "next_flag", "rain_z6",
            "has_ipc", "has_geom"]
    periods_to_str(v[keep]).to_csv(out / "err_panel.csv", index=False)

    # GRFC country-years (as built by 08_coverage.py from the GRFC database)
    gr = pd.read_csv(ROOT / "output" / "tables" / "grfc_country_years.csv")
    gr[gr.year <= 2024][["iso3", "iso2", "year", "p3", "p4plus"]].to_csv(out / "err_grfc.csv", index=False)

    # FTS flows by year x FEWS NET destination x food x US donor (same filters as 08_coverage.funding)
    M08 = load("m08", "08_coverage.py")
    codes = M08.country_codes()
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet")
    f = f[((f.boundary == "incoming") | f.boundary.isna()) & f.status.isin(["paid", "commitment"])]
    f["year"] = pd.to_numeric(f.usage_year.str[:4], errors="coerce")
    names = set(codes[codes.iso2.isin(set(pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet").country_code))].name)
    names |= {"Congo, The Democratic Republic of the", "Democratic Republic of the Congo",
              "occupied Palestinian territory"} & set(f.dest_country.dropna())
    f["to_fews"] = f.dest_country.isin(names).astype(int)
    f["food"] = f.cluster.fillna("").str.contains("Food Security|Nutrition", regex=True).astype(int)
    f["us"] = f.donor.fillna("").str.contains("United States").astype(int)
    f[f.year.between(2011, 2025)].groupby(["year", "to_fews", "food", "us"]).amount_usd.sum() \
        .reset_index().to_csv(out / "err_fts.csv", index=False)

    # national reports: famine risk mentioned (text features, 52_text_features.py)
    r = pd.read_parquet(INP / "reports" / "reports.parquet")
    r = r.assign(famine_risk=r.nat_famine_risk_mentioned.fillna(False).astype(bool).astype(int))
    r[["cc", "month", "famine_risk"]].to_csv(out / "err_reports.csv", index=False)

    # which countries FEWS NET classified in which month (for the 2025 shutdown count)
    d = pd.read_parquet(INP / "fewsnet" / "classifications.parquet", columns=["country_code", "report_month"])
    periods_to_str(d.drop_duplicates().sort_values(["report_month", "country_code"])) \
        .to_csv(out / "err_report_months.csv", index=False)
