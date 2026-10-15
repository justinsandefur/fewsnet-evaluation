"""Feasibility check: could the surveys we have measure the effect of the 2025 US aid cut?

For each aid-receiving country: its 2021-2023 US share of humanitarian funding
(FTS), the 2024->2025 change in humanitarian funding, and counts of independent
outcome surveys by period (2005-14, 2015-19, 2020-24, 2025-26) from every source
already in input/:
  DHS (national, anthropometry + birth-history mortality), MICS/LSMS/FCV
  (World Bank microdata catalog), SMART+ (sub-national SMART, 2022+), FSNAU
  Somalia seasonal SMART, WFP food-security indicators (FCS/rCSI etc.), and
  IPC/CH area classifications (not independent, but the only dense 2025-26 series).

Outputs: output/tables/us_cut_coverage.csv, us_cut_coverage_summary.csv
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
spec = importlib.util.spec_from_file_location("iv", ROOT / "code" / "15_instrument.py")
IV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IV)

PERIODS = [(2005, 2014, "05-14"), (2015, 2019, "15-19"), (2020, 2024, "20-24"), (2025, 2026, "25-26")]


def period(y):
    for a, b, lab in PERIODS:
        if a <= y <= b:
            return lab
    return None


codes, emdat, f, region = IV.load()
iso2to3 = dict(zip(codes.iso3166a2, codes.iso3166a3))
name2iso = {**dict(zip(codes.preferred_name, codes.iso3166a3)), **dict(zip(codes.iso_en_name, codes.iso3166a3)),
            **dict(zip(emdat.Country, emdat.ISO)), **IV.FIX_ISO,
            "Congo Democratic Republic": "COD", "Democratic Republic of the Congo": "COD", "Cote d'Ivoire": "CIV",
            "Côte d'Ivoire": "CIV", "Palestinian Territories": "PSE", "Syria": "SYR", "Tanzania": "TZA",
            "Kyrgyz Republic": "KGZ", "Gambia": "GMB", "Gambia, The": "GMB", "Yemen, Rep.": "YEM",
            "Egypt, Arab Rep.": "EGY", "Congo, Dem. Rep.": "COD", "Congo, Rep.": "COG", "Lao PDR": "LAO",
            "Eswatini": "SWZ", "Turkiye": "TUR", "West Bank and Gaza": "PSE", "Iran, Islamic Rep.": "IRN"}

# --- exposure: US share of humanitarian funding 2021-23, and the 2025 drop -----
f["year"] = f.month.dt.year
f["us"] = f.donor.str.startswith("United States")
pre = f[f.year.between(2021, 2023)]
tot = pre.groupby("iso3").amount_usd.sum()
X = pd.DataFrame({"us_share": pre[pre.us].groupby("iso3").amount_usd.sum().reindex(tot.index).fillna(0) / tot,
                  "hum_2123_musd": tot / 3e6})
y = f.groupby(["iso3", "year"]).amount_usd.sum().unstack()
X["dlog_hum_24_25"] = np.log(y[2025].reindex(X.index).fillna(0) + 1e5) - np.log(y[2024].reindex(X.index).fillna(0) + 1e5)
X = X[X.hum_2123_musd >= 20]          # meaningful humanitarian recipients only

# --- surveys -----------------------------------------------------------------
rows = []
d = pd.read_csv(INP / "dhs" / "dhs_surveys.csv")
d["y"] = pd.to_datetime(d.FieldworkStart).dt.year
d["iso3"] = d.DHS_CountryCode.map({**iso2to3, "BU": "BDI", "NM": "NAM", "LB": "LBR", "MD": "MDG", "OS": "SOM",
                                    "NI": "NER", "BF": "BFA", "TD": "TCD", "SD": "SDN", "SS": "SSD", "YE": "YEM",
                                    "KY": "KGZ", "IA": "IND", "NP": "NPL", "MB": "MDA", "DR": "DOM", "GU": "GTM",
                                    "HT": "HTI", "TL": "TLS", "LS": "LSO", "SZ": "SWZ", "ZA": "ZAF", "AO": "AGO"})
rows.append(d[d.SurveyType == "DHS"].assign(src="DHS")[["iso3", "y", "src"]])

w = pd.read_csv(INP / "surveys" / "survey_inventory.csv")
w["iso3"] = w.country.map(name2iso)
w = w[w.anthro | w.source.eq("MICS")]
rows.append(w.assign(y=w.year_start, src=w.source.str.upper().replace({"FCV": "WB_FCV_anthro"}))[["iso3", "y", "src"]])

for k in ["anthropometry", "mortality"]:
    s = pd.DataFrame(json.loads((INP / "smartplus" / f"{k}.json").read_text())["surveys"])
    rows.append(pd.DataFrame({"iso3": s.countryCode.map(iso2to3), "y": s.surveyYear, "src": f"SMARTplus_{k[:4]}"}))

fs = pd.read_csv(INP / "fsnau" / "surveys.csv")
rows.append(pd.DataFrame({"iso3": "SOM", "y": fs.season_year, "src": "FSNAU_SMART"}))

fi = pd.read_parquet(INP / "foodsec_surveys" / "indicators.parquet")
fi = fi[fi.source != "ch_hdx"].drop_duplicates(["iso3", "year", "source"])   # count country-years, not rows
rows.append(pd.DataFrame({"iso3": fi.iso3, "y": fi.year.astype(int), "src": "WFP_foodsec"}))

o = pd.read_parquet(INP / "panel" / "outcomes.parquet").drop_duplicates(["iso3", "month", "source"])
rows.append(pd.DataFrame({"iso3": o.iso3, "y": o.year.astype(int), "src": "IPC_CH_rounds"}))

S = pd.concat(rows).dropna(subset=["iso3"])
S["p"] = S.y.astype(int).map(period)
S = S.dropna(subset=["p"])
C = S.groupby(["iso3", "src", "p"]).size().unstack(["src", "p"]).fillna(0).astype(int)
C.columns = [f"{a}_{b}" for a, b in C.columns]
C = C.reindex(sorted(C.columns), axis=1)
T = X.join(C, how="left").fillna({c: 0 for c in C.columns})
T["tercile"] = pd.qcut(T.us_share, 3, labels=["low US", "mid US", "high US"])
indep = [c for c in T.columns if c.endswith("25-26") and not c.startswith("IPC")]
T["any_indep_25_26"] = T[indep].sum(axis=1) > 0
T.sort_values("us_share", ascending=False).round(3).to_csv(TAB / "us_cut_coverage.csv")

summ = T.groupby("tercile").agg(
    countries=("us_share", "size"), us_share=("us_share", "median"), dlog_hum=("dlog_hum_24_25", "median"),
    **{c: (c, lambda s: int((s > 0).sum())) for c in sorted(set(T.columns) & set(C.columns))},
    any_indep_25_26=("any_indep_25_26", "sum"))
summ.T.to_csv(TAB / "us_cut_coverage_summary.csv")
pd.set_option("display.width", 250, "display.max_rows", 200, "display.max_columns", 60)
print(summ.T.to_string())
show = ["us_share", "dlog_hum_24_25"] + [c for c in T.columns if c.endswith("20-24") or c.endswith("25-26")]
print(T.sort_values("us_share", ascending=False)[show].round(2).to_string())
