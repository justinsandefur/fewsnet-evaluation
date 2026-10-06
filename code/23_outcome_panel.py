"""Area-level outcome panel of food insecurity classifications produced
independently of FEWS NET: the Cadre Harmonise (West and Central Africa,
2014 on) and the multi-agency IPC (elsewhere, 2017 on).

One row per area x analysis (current situation only), with
  share3   share of the area's analysed population in Phase 3 or worse
  share4   share in Phase 4 or worse
  phase    area classification (IPC/CH rule: highest phase with >= 20% of
           the population in that phase or worse)
  month    representative month of the analysis period
  covered  FEWS NET published a report for the country in that month or the
           three months before (API 2011-2026, map archive 2009-2022)

Outputs: input/panel/outcomes.parquet, output/tables/outcome_panel_summary.csv
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
(INP / "panel").mkdir(exist_ok=True)
CH_LABEL_MONTH = {"Jan-May": 3, "Jun-Aug": 7, "Sep-Dec": 11}
IPC_NAME_FIX = {"Congo, DRC": "COD", "Tanzania": "TZA", "Eswatini": "SWZ", "LAC Region (tri-National)": None,
                "Palestine": "PSE"}


def area_phase(s3, s4, s5, s2):
    """Highest phase p with at least 20% of the population in phase p or worse."""
    ph = np.ones(len(s3))
    ph[s2 >= 0.2] = 2
    ph[s3 >= 0.2] = 3
    ph[s4 >= 0.2] = 4
    ph[s5 >= 0.2] = 5
    return ph


def cadre_harmonise():
    d = pd.read_excel(INP / "ipc" / "cadre_harmonise_caf_ipc_mars26.xlsx")
    d = d[d.chtype.str.lower().eq("current") & d.usethisperiod.eq("Y")].copy()
    d["area_id"] = d.adm2_pcod2.fillna(d.adm1_pcod2)
    d["level"] = np.where(d.adm2_pcod2.notna(), "adm2", "adm1")
    d["month"] = pd.PeriodIndex([f"{int(y)}-{CH_LABEL_MONTH.get(l, 6):02d}" for y, l in
                                 zip(d.reference_year, d.reference_label)], freq="M")
    pop = d.population.replace(0, np.nan)
    out = pd.DataFrame({
        "source": "CH", "iso3": d.adm0_pcod3, "area_id": d.area_id, "level": d.level,
        "area_name": d.adm2_name.fillna(d.adm1_name), "adm1_name": d.adm1_name, "adm1_code": d.adm1_pcod2,
        "month": d.month, "population": d.population,
        "share3": d.phase35 / pop, "share4": (d.phase4.fillna(0) + d.phase5.fillna(0)) / pop,
        "phase": d.phase_class})
    return out.dropna(subset=["area_id", "share3"]).drop_duplicates(["area_id", "month"], keep="last")


def ipc_recent(exclude):
    a = pd.read_csv(INP / "ipc" / "ipc_global_area_long.csv", low_memory=False)
    a = a[(a["Validity period"] == "current") & ~a.Country.isin(exclude)].copy()
    a["area_id"] = a.Country + "|" + a["Level 1"].fillna("") + "|" + a.Area
    a["from"] = pd.to_datetime(a.From, errors="coerce")
    a["to"] = pd.to_datetime(a.To, errors="coerce")
    w = a.pivot_table(index=["Country", "area_id", "Level 1", "Area", "from", "to"], columns="Phase",
                      values="Percentage", aggfunc="first").reset_index()
    pop = a[a.Phase == "all"].groupby(["area_id", "from"]).Number.first()
    for p in ["2", "3", "4", "5"]:
        if p not in w:
            w[p] = 0.0
    w = w.fillna({"2": 0, "3": 0, "4": 0, "5": 0})
    mid = w["from"] + (w["to"] - w["from"]) / 2
    out = pd.DataFrame({
        "source": "IPC", "iso3": w.Country, "area_id": w.area_id, "level": "ipc_area",
        "area_name": w.Area, "adm1_name": w["Level 1"], "adm1_code": None,
        "month": mid.dt.to_period("M"),
        "population": w.set_index(["area_id", "from"]).index.map(pop).values,
        "share3": w["3"] + w["4"] + w["5"], "share4": w["4"] + w["5"],
        "phase": area_phase(w["3"] + w["4"] + w["5"], w["4"] + w["5"], w["5"], w["2"] + w["3"] + w["4"] + w["5"])})
    return out


def ipc_older(name2iso, exclude):
    raw = pd.read_excel(INP / "ipc" / "all_countries-2017-2023.xlsx", header=None, skiprows=12)
    d = raw[raw[2].notna() & raw[0].notna()].copy()            # area rows only
    d["iso3"] = d[0].map(lambda n: IPC_NAME_FIX.get(n, name2iso.get(n)))
    d = d[d.iso3.notna() & ~d.iso3.isin(exclude)]
    per = d[10].astype(str).str.split(" - ")
    start = pd.to_datetime(per.str[0], format="%b %Y", errors="coerce")
    end = pd.to_datetime(per.str[-1], format="%b %Y", errors="coerce")
    mid = start + (end - start) / 2
    num = lambda c: pd.to_numeric(d[c], errors="coerce").fillna(0)
    out = pd.DataFrame({
        "source": "IPC", "iso3": d.iso3, "area_id": d.iso3 + "|" + d[1].fillna("").astype(str) + "|" + d[2].astype(str),
        "level": "ipc_area", "area_name": d[2].astype(str), "adm1_name": d[1], "adm1_code": None,
        "month": mid.dt.to_period("M"), "population": pd.to_numeric(d[7], errors="coerce"),
        "share3": num(16) + num(18) + num(20), "share4": num(18) + num(20),
        "phase": pd.to_numeric(d[9], errors="coerce")})
    return out.dropna(subset=["month"])


def coverage_monthly(codes):
    iso2to3 = dict(zip(codes.iso3166a2, codes.iso3166a3))
    cls = pd.read_parquet(INP / "fewsnet" / "classifications.parquet", columns=["country_code", "report_month"])
    api = set(zip(cls.country_code.map(iso2to3), cls.report_month))
    maps = pd.read_csv(INP / "fewsnet" / "coverage_maps.csv")
    mp = set(zip(maps.iso3, pd.PeriodIndex(maps.month, freq="M")))
    return api | mp


def main():
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    name2iso = {**dict(zip(codes.preferred_name, codes.iso3166a3)), **dict(zip(codes.iso_en_name, codes.iso3166a3))}
    ch = cadre_harmonise()
    ch_countries = set(ch.iso3)
    recent = ipc_recent(ch_countries)
    older = ipc_older(name2iso, ch_countries)
    # older file only where the recent file has no analysis for that area-month
    older = older[~older.set_index(["area_id", "month"]).index.isin(recent.set_index(["area_id", "month"]).index)]
    older = older[older.month < pd.Period("2021-01", "M")]
    p = pd.concat([ch, recent, older], ignore_index=True)
    p = p[(p.share3 >= 0) & (p.share3 <= 1.0001)]
    cov = coverage_monthly(codes)
    p["covered"] = [any((i, m - k) in cov for k in range(0, 4)) for i, m in zip(p.iso3, p.month)]
    p["year"] = p.month.dt.year
    p.to_parquet(INP / "panel" / "outcomes.parquet", index=False)
    s = p.groupby(["source", "iso3"]).agg(areas=("area_id", "nunique"), analyses=("month", "nunique"),
                                          first=("year", "min"), last=("year", "max"),
                                          share_covered=("covered", "mean"), mean_share3=("share3", "mean"),
                                          phase4_rate=("phase", lambda x: (x >= 4).mean())).round(3)
    s.to_csv(TAB / "outcome_panel_summary.csv")
    print(s.to_string())
    print(p.groupby("source").agg(rows=("area_id", "size"), areas=("area_id", "nunique")))


if __name__ == "__main__":
    main()
