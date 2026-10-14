"""Build a country x year panel, 1990-2023: did a DHS / MICS / LSMS survey start
fieldwork in this country-year, plus GDP, conflict, shocks, child mortality.

Sample: every country the World Bank currently classifies as low or middle income,
plus any other country that ever hosted one of the three survey programs.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FEWS = ROOT.parent / "input" / "fewsnet" / "cs_monthly.parquet"
Y0, Y1 = 1990, 2023

cty = pd.read_csv(RAW / "countries.csv", keep_default_na=False)
name2iso = dict(zip(cty.name, cty.iso3))
iso2to3 = dict(zip(cty.iso2, cty.iso3))

# --- Surveys ----------------------------------------------------------------
# DHS: household surveys only (standard/interim DHS, malaria, AIDS indicator surveys)
dhs = pd.read_csv(RAW / "dhs_surveys_api.csv")
dhs = dhs[dhs.SurveyType.isin(["DHS", "MIS", "AIS"])]
DHS_NAMES = {
    "Bolivia": "BOL", "Cape Verde": "CPV", "Congo": "COG", "Congo Democratic Republic": "COD",
    "Cote d'Ivoire": "CIV", "Egypt": "EGY", "Eswatini": "SWZ", "Gambia": "GMB", "Kyrgyz Republic": "KGZ",
    "Lao People's Democratic Republic": "LAO", "Moldova": "MDA", "Turkey": "TUR", "Yemen": "YEM",
    "Vietnam": "VNM", "Tanzania": "TZA", "Sao Tome and Principe": "STP", "Russia": "RUS",
    "Iran": "IRN", "Korea, Rep.": "KOR", "Kenya": "KEN", "Brazil": "BRA",
    "Nigeria (Ondo State)": "NGA", "Sri Lanka": "LKA", "Venezuela": "VEN",
    "Ukraine": "UKR", "Gaza Strip": "PSE", "West Bank": "PSE", "Palestine": "PSE",
    "Micronesia": "FSM", "Yemen, Rep.": "YEM",
}
dhs["iso3"] = dhs.CountryName.map(lambda n: DHS_NAMES.get(n, name2iso.get(n)))
miss = dhs.loc[dhs.iso3.isna(), "CountryName"].unique()
assert len(miss) == 0, f"unmapped DHS names: {miss}"
dhs["year"] = pd.to_datetime(dhs.FieldworkStart, errors="coerce").dt.year.fillna(dhs.SurveyYear).astype(int)
dhs = dhs[["iso3", "year", "SurveyId"]].assign(program="DHS").rename(columns={"SurveyId": "id"})

# MICS and LSMS: catalog ids start with ISO3_YEAR
def from_catalog(path, program):
    d = pd.read_csv(path)
    d["iso3"] = d.idno.str[:3].str.upper().replace({"KSV": "XKX", "ROM": "ROU", "ZAR": "COD", "TMP": "TLS"})
    d["year"] = pd.to_numeric(d.year_start, errors="coerce")
    # drop harmonised multi-wave panel files (e.g. NGA_2010-2019_NUPD); waves are listed separately
    d = d[~d.idno.str.contains(r"_\d{4}-\d{4}_", regex=True)]
    d = d.dropna(subset=["year"]).astype({"year": int})
    d["id"] = d.iso3 + "_" + d.year.astype(str)
    return d[["iso3", "year", "id"]].drop_duplicates().assign(program=program)

mics = from_catalog(RAW / "mics_catalog.csv", "MICS")
lsms = from_catalog(RAW / "lsms_catalog.csv", "LSMS")
surveys = pd.concat([dhs, mics, lsms])
surveys = surveys[surveys.iso3.isin(cty.iso3)]
surveys.to_csv(ROOT / "data" / "surveys_long.csv", index=False)
print(surveys.groupby("program").size().to_dict(), "surveys;",
      surveys.drop_duplicates(["iso3", "year", "program"]).groupby("program").size().to_dict(), "country-years")

# --- Panel skeleton ---------------------------------------------------------
lmic = set(cty.loc[cty.income.isin(["Low income", "Lower middle income", "Upper middle income"]), "iso3"])
sample = sorted(lmic | set(surveys.iso3))
panel = pd.MultiIndex.from_product([sample, range(Y0, Y1 + 1)], names=["iso3", "year"]).to_frame(index=False)
panel = panel.merge(cty[["iso3", "name", "region", "income"]], on="iso3", how="left")

cnt = surveys.groupby(["iso3", "year", "program"]).size().unstack(fill_value=0)
for p in ["DHS", "MICS", "LSMS"]:
    panel = panel.merge(cnt[[p]].rename(columns={p: f"n_{p}"}).reset_index(), on=["iso3", "year"], how="left")
    panel[f"n_{p}"] = panel[f"n_{p}"].fillna(0)
    panel[f"s_{p}"] = (panel[f"n_{p}"] > 0).astype(int)
panel["s_any"] = panel[["s_DHS", "s_MICS", "s_LSMS"]].max(axis=1)

# --- WDI / WGI --------------------------------------------------------------
wdi = pd.read_csv(RAW / "wdi.csv").rename(columns={
    "NY.GDP.PCAP.PP.KD": "gdppc_ppp", "NY.GDP.PCAP.KD": "gdppc_usd", "NY.GDP.PCAP.KD.ZG": "growth",
    "SP.POP.TOTL": "pop", "VC.BTL.DETH": "battle_deaths", "SH.DTH.MORT": "u5_deaths",
    "SH.DYN.MORT": "u5mr", "SP.POP.0014.TO": "pop_0_14", "PV.EST": "wgi_stability"})
panel = panel.merge(wdi, on=["iso3", "year"], how="left")

# Maddison fills GDP per capita where WDI is missing, scaled to WDI PPP levels by country
mpd = pd.read_excel(RAW / "mpd2023.xlsx", sheet_name="Full data")
mpd = mpd.rename(columns={"countrycode": "iso3", "gdppc": "gdppc_mpd"})[["iso3", "year", "gdppc_mpd"]]
panel = panel.merge(mpd, on=["iso3", "year"], how="left")
ratio = (panel.gdppc_ppp / panel.gdppc_mpd).groupby(panel.iso3).transform("median")
glob_ratio = (panel.gdppc_ppp / panel.gdppc_mpd).median()
panel["gdp_imputed"] = panel.gdppc_ppp.isna().astype(int)
panel["gdppc"] = panel.gdppc_ppp.fillna(panel.gdppc_mpd * ratio.fillna(glob_ratio))
# last resort: constant-USD series scaled to PPP, then carry nearest value within country
r2 = (panel.gdppc_ppp / panel.gdppc_usd).groupby(panel.iso3).transform("median")
panel["gdppc"] = panel.gdppc.fillna(panel.gdppc_usd * r2)
panel["gdppc"] = panel.groupby("iso3").gdppc.transform(lambda s: s.ffill().bfill())
panel["ln_gdppc"] = np.log(panel.gdppc)

# growth: WDI, else computed from the filled level series
g2 = panel.groupby("iso3").gdppc.pct_change() * 100
panel["growth"] = panel.growth.fillna(g2)
panel["downturn"] = (panel.growth < -2).astype(int)          # GDP per capita fell >2%
panel["ln_pop"] = np.log(panel["pop"])

# Battle deaths (UCDP via WDI): WDI leaves zero-conflict years blank
panel["battle_deaths"] = panel.battle_deaths.fillna(0)
panel["bd_per100k"] = panel.battle_deaths / panel["pop"] * 1e5
panel["ln_bd"] = np.log1p(panel.bd_per100k)
panel["conflict"] = (panel.battle_deaths >= 25).astype(int)
panel["war"] = (panel.battle_deaths >= 1000).astype(int)
panel["conflict_cat"] = np.select([panel.war == 1, panel.conflict == 1], ["War (1,000+ deaths)", "Minor conflict (25-999)"],
                                  "No conflict")

# WGI political stability: 1996+, gaps in 1997/99/2001 interpolated within country
panel["wgi_stability"] = panel.groupby("iso3").wgi_stability.transform(
    lambda s: s.interpolate(limit_area="inside"))

# --- FEWS NET food insecurity (2011+) --------------------------------------
fews = pd.read_parquet(FEWS)
fews["iso3"] = fews.country_code.map(iso2to3)
fews["year"] = fews.month.astype(str).str[:4].astype(int)
fews = fews.groupby(["iso3", "year"]).agg(
    fews_share3=("phase", lambda p: (p >= 3).mean()),
    fews_any4=("phase", lambda p: int((p >= 4).any())),
    fews_maxphase=("phase", "max")).reset_index()
panel = panel.merge(fews, on=["iso3", "year"], how="left")
panel["fews_country"] = panel.iso3.isin(fews.iso3).astype(int)

# --- Survey recency (for the "who gets counted" figure) ---------------------
def years_since(s):
    out, last = [], None
    for yr, hit in zip(s.index, s.values):
        if hit:
            last = yr
        out.append(np.nan if last is None else yr - last)
    return pd.Series(out, index=s.index)

panel = panel.sort_values(["iso3", "year"])
for p in ["any", "DHS", "MICS", "LSMS"]:
    panel[f"since_{p}"] = panel.groupby("iso3", group_keys=False).apply(
        lambda g: years_since(g.set_index("year")[f"s_{p}"]).set_axis(g.index))

panel.to_csv(ROOT / "data" / "panel.csv", index=False)
print("panel", panel.shape, "countries", panel.iso3.nunique())
print("GDP imputed share", panel.gdp_imputed.mean().round(3), "still missing", panel.gdppc.isna().sum())
print(panel.groupby("conflict_cat")[["s_any", "s_DHS", "s_MICS", "s_LSMS"]].mean().round(3))
