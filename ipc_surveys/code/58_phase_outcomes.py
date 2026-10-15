"""Does measured acute malnutrition and mortality rise with the food insecurity phase,
outside Somalia? Open survey sources, matched to FEWS NET maps and to IPC / Cadre
Harmonise (CH) classifications; and IPC acute malnutrition (AMN) phases compared
with IPC acute food insecurity (AFI) phases for the same areas.

Sources
  1. SMART+ (ACF Canada / UNICEF) dashboard API, open: one row per survey domain,
     GAM/SAM by weight-for-height (WHZ) and MUAC, crude and under-five death rates
     (per 10,000 per day) with 95% CIs, a GPS point, survey month. Sep 2022 on.
       api.smartplusapp.org/v1/dashboard/survey-results/{anthropometry,mortality}
     The GPS point is a geocoded place for the domain (often the domain's main
     town), not a boundary, so multi-district domains are matched to one place.
  2. FEWS NET Data Warehouse, /api/nutritionindicatorvalue/?format=csv: only Burkina
     Faso (2003-2017) and Mauritania (2007-2018) values are served anonymously.
     The ~3,400 Ethiopian series (2000-2018) are listed in the public catalogue
     (/api/nutritionindicator/) but every value query for them returns an empty list
     (checked by dataseries, document, unit, country; Oct 2026). The BF/MR rows are
     national SMART rounds, representative by region or province.
  3. IPC AMN files hand-uploaded to HDX (13 country datasets). Few carry the AMN phase
     itself (South Sudan 2025 hotspot table, DR Congo 2024-25 by health zone,
     Nigeria Jan-Apr 2022 by domain). Most carry the GAM prevalence used for the
     classification, by area; for those the AMN phase is derived from the IPC AMN
     GAM thresholds (<5, 5-9.9, 10-14.9, 15-29.9, >=30 percent). Files often report
     combined GAM (WHZ or MUAC), so derived phases are approximate.

Matching
  FEWS NET: SMART+ points are joined to every unit polygon in input/fewsnet/units.gpkg
  (all vintages); the vintage valid at the survey date is the one with a published
  map in the window. FDW admin names are matched to unit names (admin 2, else
  admin 1). Current situation: latest map in the 4 months up to the survey month
  (mean over matched units). Forecast: the projection for the survey month from the
  latest report issued 3-8 months earlier (proj_monthly, lead 3-8; nearest lead per
  unit). IPC/CH: area polygons from 24_area_rainfall.area_geometries; the analysis
  whose representative month is nearest the survey month, within 4 months; area-
  weighted over the survey's footprint (a point for SMART+, the union of matched
  FEWS NET units for FDW).

Caveat on selection: SMART+ surveys are mostly ad hoc (fielded where and when
someone worried and paid), apart from Nigeria's numbered UNICEF rounds (NFSS,
SOKAZA, BENSS), which are reported separately. Selection on alarm probably steepens
the gradient relative to scheduled surveys such as Somalia's FSNAU rounds (57).

Usage: 58_phase_outcomes.py [fetch]     (fetch re-downloads raw sources; build is default)
Outputs: output/tables/phase_outcomes.csv, phase_outcomes_amn.csv, phase_outcomes_key.json,
         phase_outcomes_surveys.csv (survey-level matched panel), phase_outcomes_amn_areas.csv
"""
import importlib.util
import json
import re
import sys
import unicodedata
import warnings
from difflib import SequenceMatcher
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
SP, FDW, AMN = INP / "smartplus", INP / "fdw_nutrition", INP / "ipc_amn"
ISO3 = {"NG": "NGA", "ET": "ETH", "MZ": "MOZ", "SY": "SYR", "ZM": "ZMB", "SS": "SSD", "CD": "COD", "AO": "AGO",
        "SO": "SOM", "PS": "PSE", "KE": "KEN", "PG": "PNG", "NP": "NPL", "GN": "GIN", "CM": "CMR", "BF": "BFA",
        "MR": "MRT"}
RECURRING = r"^(NFSS|SOKAZA|BENSS)"
AMN_DATASETS = ["cameroun-analyse-analyse-ipc-de-la-malnutrition-aigue", "chad-acute-malnutrition",
                "haiti-acutemalnutrition", "mli-malnutrition-aigue", "mozambique-acute-malnutrition",
                "northeast-and-northwest-nigeria-acute-malnutrition", "rdc-ipc-amn",
                "republique-centrafricaine-analyse-de-la-malnutrition-aigue-de-l-ipc",
                "somalia-acute-malnutrition-analysis", "south-sudan-acute-malnutrition", "yemen-acute-malnutrition",
                "nigeria-acute-malnutrition-data", "afg-malnutrition-prevalence"]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()


# ------------------------------------------------------------------ fetch
def fetch():
    for d in (SP, FDW, AMN):
        d.mkdir(parents=True, exist_ok=True)
    for p in ["anthropometry", "mortality"]:
        r = requests.get(f"https://api.smartplusapp.org/v1/dashboard/survey-results/{p}", timeout=180)
        r.raise_for_status()
        (SP / f"{p}.json").write_bytes(r.content)
    for e, f in [("nutritionindicatorvalue", "values.csv"), ("nutritionindicator", "nutritionindicator.csv")]:
        r = requests.get(f"https://fdw.fews.net/api/{e}/?format=csv", timeout=900)
        r.raise_for_status()
        (FDW / f).write_bytes(r.content)
    urls = []
    for ds in AMN_DATASETS:
        p = requests.get(f"https://data.humdata.org/api/3/action/package_show?id={ds}", timeout=60).json()["result"]
        for res in p["resources"]:
            if res["format"] in ("XLSX", "XLS", "CSV"):
                urls.append((ds, res["url"]))
    for ds, u in urls:
        out = AMN / ds / Path(u).name
        out.parent.mkdir(exist_ok=True)
        if not out.exists():
            out.write_bytes(requests.get(u, timeout=120).content)
    pd.DataFrame(urls, columns=["dataset", "url"]).to_csv(AMN / "urls.tsv", sep="\t", index=False, header=False)


# ------------------------------------------------------------------ surveys
def g(d, *ks):
    for k in ks:
        if not isinstance(d, dict):
            return np.nan
        d = d.get(k)
    return d if d is not None else np.nan


def smartplus():
    a = json.loads((SP / "anthropometry.json").read_text())["surveys"]
    m = {s["id"]: s["keystats"] for s in json.loads((SP / "mortality.json").read_text())["surveys"]}
    rows = []
    for s in a:
        k, mk = s["keystats"], m.get(s["id"], {})
        rows.append(dict(
            source="SMART+", sid=f"SP{s['id']}", iso2=s["countryCode"], name=s["surveyName"], org=s["organizationName"],
            share=s["share"], lat=s["latitude"], lon=s["longitude"], adm1=s["administrative_area_level_1"],
            adm2=s["administrative_area_level_2"],
            month=pd.Period(f"{s['surveyYear']}-{s['surveyMonth']:02d}", "M"),
            gam=100 * g(k, "gam", "whz", "all", "prop"), gam_lo=100 * g(k, "gam", "whz", "all", "prop_low"),
            gam_hi=100 * g(k, "gam", "whz", "all", "prop_upp"), sam=100 * g(k, "sam", "whz", "all", "prop"),
            gam_muac=100 * g(k, "gam", "muac", "all", "prop"),
            cdr=g(mk, "crudeMortalityRate", "all", "stat"), cdr_lo=g(mk, "crudeMortalityRate", "all", "stat_low"),
            cdr_hi=g(mk, "crudeMortalityRate", "all", "stat_upp"), u5dr=g(mk, "under5MortalityRate", "stat")))
    d = pd.DataFrame(rows)
    d = d[d.share].drop(columns="share")
    d = d[~d.name.str.strip().str.match(r"(?i)^(toto|test)\b")]      # test entries
    d["recurring"] = d.name.str.upper().str.contains(RECURRING)
    d["iso3"] = d.iso2.map(ISO3)
    d["cluster"] = d.iso2 + "|" + d.adm1.fillna(d.name).map(norm)
    return d


def fdw():
    v = pd.read_csv(FDW / "values.csv", low_memory=False)
    v.columns = [c.lstrip("﻿") for c in v.columns]
    ind = {"PCT_GAM_WHZ_LT-2": "gam", "PCT_SAM_WHZ_LT-3": "sam", "PCT_GAM_MUAC_LT12.5cm": "gam_muac",
           "U5MR": "u5dr", "CDR": "cdr"}
    v = v[v.indicator_abbreviation.isin(ind) & v.value.notna()].copy()
    v["var"] = v.indicator_abbreviation.map(ind)
    # sub-national populations only (drop national and stratum rows coded with the bare country code)
    v = v[v.fnid.str.len() > 2]
    v["population_group"] = v.population_group.fillna("")
    keys = ["country_code", "source_document", "fnid", "population_group", "period_date"]
    w = v.pivot_table(index=keys, columns="var", values="value", aggfunc="mean").reset_index()
    lo = v[v["var"] == "gam"].groupby(keys).agg(gam_lo=("ci95_low", "mean"), gam_hi=("ci95_high", "mean"),
                                                 adm1=("admin_1", "first"), adm2=("admin_2", "first"),
                                                 n_child=("child_sample_size", "first")).reset_index()
    w = w.merge(lo, on=keys, how="left")
    w["month"] = pd.PeriodIndex(pd.to_datetime(w.period_date), freq="M")
    w = w.rename(columns={"country_code": "iso2", "source_document": "name"})
    w["source"], w["org"], w["recurring"] = "FDW", w.name.str.extract(r"\((.*)\)$")[0], True
    w["sid"] = "FDW" + pd.Series(range(len(w))).astype(str)
    w["iso3"] = w.iso2.map(ISO3)
    w["cluster"] = w.iso2 + "|" + w.adm1.map(norm)
    for c in ["cdr", "gam_muac", "u5dr"]:
        if c not in w:
            w[c] = np.nan
    return w[w.gam.notna()]


# ------------------------------------------------------------------ FEWS NET
class Fews:
    def __init__(self):
        self.units = gpd.read_file(INP / "fewsnet/units.gpkg")[["fnid", "country_code", "geometry"]]
        self.cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet")
        pr = pd.read_parquet(INP / "fewsnet/proj_monthly.parquet")
        self.pr = pr[pr.lead.between(3, 8)]
        nm = pd.read_parquet(INP / "fewsnet/ipcphase.parquet", columns=["country_code", "fnid", "geographic_unit_full_name"])
        nm = nm.drop_duplicates("fnid").dropna()
        parts = nm.geographic_unit_full_name.str.split(",").map(lambda p: [x.strip() for x in p[:-1]])
        nm["adm1_n"] = parts.map(lambda p: norm(p[-1]) if len(p) >= 1 else "")
        nm["adm2_n"] = parts.map(lambda p: norm(p[-2]) if len(p) >= 2 else "")
        self.names = nm

    def by_point(self, iso2, lon, lat):
        u = self.units[self.units.country_code == iso2]
        if u.empty or pd.isna(lon):
            return set()
        from shapely.geometry import Point
        p = Point(lon, lat)
        return set(u[u.intersects(p)].fnid)

    def by_name(self, iso2, adm1, adm2):
        U = self.names[self.names.country_code == iso2]
        if U.empty:
            return set(), "none"
        a1, a2 = norm(adm1 or ""), norm(adm2 or "") if isinstance(adm2, str) else ""
        pool = U[U.adm1_n.map(lambda o: bool(o == a1 or (a1 and sim(a1, o) >= 0.85))).astype(bool)] if a1 else U
        if a2:
            hit = pool[pool.adm2_n.map(lambda o: o == a2 or sim(a2, o) >= 0.85).astype(bool)]
            return set(hit.fnid), "admin2"
        return (set(pool.fnid), "admin1") if a1 and len(pool) < len(U) else (set(), "none")

    def phases(self, ids, m):
        """Current map (latest in the 4 months to m) and forecast for m (latest report 3-8 months before)."""
        out = dict(cur=np.nan, cur3=np.nan, fc=np.nan, fc3=np.nan, cur_month=None, fc_lead=np.nan, n_units=0)
        if not ids:
            return out
        c = self.cs[self.cs.fnid.isin(ids) & (self.cs.month <= m) & (self.cs.month >= m - 4)]
        if len(c):
            c = c[c.month == c.month.max()]
            out.update(cur=c.phase.mean(), cur3=(c.phase >= 3).mean(), cur_month=str(c.month.iloc[0]),
                       n_units=c.fnid.nunique())
        f = self.pr[self.pr.fnid.isin(ids) & (self.pr.month == m)]
        if len(f):
            f = f[f.report_month == f.report_month.max()]
            f = f.loc[f.groupby("fnid").lead.idxmin()]
            out.update(fc=f.phase.mean(), fc3=(f.phase >= 3).mean(), fc_lead=int(f.lead.min()))
        return out

    def geom(self, ids):
        u = self.units[self.units.fnid.isin(ids)]
        return u.geometry.union_all() if hasattr(u.geometry, "union_all") else u.geometry.unary_union


# ------------------------------------------------------------------ IPC / CH
class Official:
    def __init__(self):
        rain = load("rain", "24_area_rainfall.py")
        geo, o = rain.area_geometries(pd.read_parquet(INP / "panel" / "outcomes.parquet"))
        o = o.dropna(subset=["phase"])
        self.o = o
        g = geo[geo.key.isin(o.key)].drop_duplicates("key").copy()
        g["geometry"] = g.geometry.buffer(0)
        g = g.merge(o[["key", "iso3"]].drop_duplicates("key"), on="key")
        self.geo = g
        self.area = g.to_crs(6933).set_index("key").area

    def lookup(self, iso3, geom, m, point=False):
        out = dict(ipc=np.nan, ipc3=np.nan, ipc_source=None, ipc_month=None)
        g = self.geo[self.geo.iso3 == iso3]
        if g.empty or geom is None or geom.is_empty:
            return out
        g = g[g.intersects(geom)]
        if g.empty:
            return out
        o = self.o[self.o.key.isin(g.key)].copy()
        o["dist"] = (o.month - m).map(lambda x: x.n).abs()
        o = o[o.dist <= 4]
        if o.empty:
            return out
        o["after"] = (o.month > m).astype(int)
        best = o.sort_values(["dist", "after"]).iloc[0]
        o = o[(o.month == best.month) & (o.source == best.source)]
        keys = g[g.key.isin(o.key)]
        if point:
            # smallest area containing the point
            k = self.area.loc[keys.key].idxmin()
            w = pd.Series(1.0, index=[k])
        else:
            gg = keys.to_crs(6933)
            sg = gpd.GeoSeries([geom], crs=4326).to_crs(6933).iloc[0]
            w = pd.Series(gg.geometry.intersection(sg).area.values, index=keys.key.values)
            w = w[w > 0.05 * w.sum()]
            # where regions and districts both cover the footprint, use the finer level
            fine = [k for k in w.index if "ADM1" not in k]
            w = w.loc[fine] if fine else w
        o = o[o.key.isin(w.index)].groupby("key").agg(phase=("phase", "max"), share3=("share3", "mean"))
        ww = w.reindex(o.index)
        out.update(ipc=float((o.phase * ww).sum() / ww.sum()), ipc3=float(((o.phase >= 3) * ww).sum() / ww.sum()),
                   ipc_source=best.source, ipc_month=str(best.month))
        return out


def attach(s, F, O):
    rows = []
    for r in s.itertuples():
        if r.source == "SMART+":
            ids, how = F.by_point(r.iso2, r.lon, r.lat), "gps"
            if not ids and isinstance(r.adm1, str):
                ids, how = F.by_name(r.iso2, r.adm1, r.adm2)
        else:
            ids, how = F.by_name(r.iso2, r.adm1, r.adm2)
        x = F.phases(ids, r.month)
        x["match"] = how if ids else "none"
        if r.source == "SMART+":
            from shapely.geometry import Point
            geom = Point(r.lon, r.lat) if pd.notna(r.lon) else None
            x.update(O.lookup(r.iso3, geom, r.month, point=True))
        else:
            # footprint: matched FEWS NET units that carried a map in the window
            live = set(F.cs[F.cs.fnid.isin(ids) & (F.cs.month <= r.month) & (F.cs.month >= r.month - 12)].fnid) or ids
            x.update(O.lookup(r.iso3, F.geom(live) if live else None, r.month))
        rows.append(x)
    return pd.concat([s.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


# ------------------------------------------------------------------ AMN files
AMN_THRESH = [5, 10, 15, 30]


def amn_phase(gam):
    return np.where(np.isnan(gam), np.nan, 1 + np.searchsorted(AMN_THRESH, gam, side="right"))


def pct(x):
    """'5,3%' -> 5.3; numbers are returned as given (scale() converts fractions)."""
    if isinstance(x, str):
        x = x.replace(",", ".").replace("\xa0", "").replace(" ", "").strip()
        is_pct = x.endswith("%")
        try:
            v = float(x.rstrip("%"))
        except ValueError:
            return np.nan
        return v if is_pct else (v * 100 if v < 1 else v)
    if pd.isna(x):
        return np.nan
    return float(x) * 100 if float(x) < 1 else float(x)


def scale(s):
    """Percent; values below 1 are read as fractions (GAM under 1 percent is implausible in these files)."""
    s = s.map(pct)
    return s.where(s < 60)


def rd(f, sheet, **kw):
    return pd.read_excel(AMN / f, sheet_name=sheet, header=None, **kw)


def amn_tables():
    """One row per AMN area: iso3, area, adm1, level, gam (percent), amn (explicit phase), start, file."""
    T = []

    def add(iso3, df, start, f, level, area="area", adm1=None, gam=None, amn=None, afi=None):
        d = pd.DataFrame({"iso3": iso3, "area": df[area].astype(str).str.replace("\n", " ").str.strip(),
                          "adm1": df[adm1].astype(str).str.replace("\n", " ").str.strip() if adm1 is not None else None,
                          "gam": scale(df[gam]) if gam is not None else np.nan,
                          "amn": pd.to_numeric(df[amn], errors="coerce") if amn is not None else np.nan,
                          "afi_file": pd.to_numeric(df[afi], errors="coerce") if afi is not None else np.nan})
        d["start"], d["file"], d["level"] = pd.Period(start, "M"), f, level
        d = d[~d.area.str.contains(r"total|^nan$|grand", case=False, regex=True)]
        T.append(d)

    # Afghanistan (provinces)
    f = "afg-malnutrition-prevalence/afghanistan_malnutrition_data_jan-dec2026.xlsx"
    x = rd(f, "SAM_MAM_GAM_Projection2026").iloc[1:]
    add("AFG", x, "2026-01", f, "province", area=0, gam=2)
    f = "afg-malnutrition-prevalence/afghanistan_malnutrition_data_jun2024-may2025.xlsx"
    x = rd(f, "Sheet2").iloc[1:]
    add("AFG", x, "2024-06", f, "province", area=0, gam=2)
    # Cameroon (departements): %MAM + %MAS, local population block only
    f = "cameroun-analyse-analyse-ipc-de-la-malnutrition-aigue/cmr-ipc-novembre2023-decembre2024.xlsx"
    x = rd(f, "Sheet1").iloc[2:]
    stop = x[x[0].astype(str).str.contains("Total|fugi", case=False)].index
    x = x.loc[: stop[0] - 1] if len(stop) else x
    x["g"] = scale(x[3]) + scale(x[5])
    add("CMR", x, "2023-11", f, "departement", area=1, adm1=0, gam="g")
    # Mali (cercles)
    f = "mli-malnutrition-aigue/ipc_mali_acute_malnutrition_june2024_may2025.xlsx"
    x = rd(f, "AMN by Cercle").iloc[3:]
    x["g"] = scale(x[4]) + scale(x[6])
    add("MLI", x, "2024-06", f, "cercle", area=1, adm1=0, gam="g")
    f = "mli-malnutrition-aigue/ipc_mali_acute_malnutrition_nov2025_oct2026.xlsx"
    x = rd(f, "Donnees Cercle").iloc[1:62]
    add("MLI", x, "2025-11", f, "cercle", area=1, adm1=0, gam=3)
    # Mozambique (districts); DA% = acute malnutrition (global)
    f = "mozambique-acute-malnutrition/mozambique-acute-malnutrition.xlsx"
    x = rd(f, "Sheet1").iloc[2:]
    x[0] = x[0].ffill()
    add("MOZ", x, "2024-04", f, "district", area=1, adm1=0, gam=6)
    # Nigeria
    f = "nigeria-acute-malnutrition-data/nigeria_acute-malnutrition-january-to-december-2021.xlsx"
    x = rd(f, "AcuteMalnutrition").iloc[4:]
    add("NGA", x, "2021-01", f, "domain", area=1, gam=2)
    f = "nigeria-acute-malnutrition-data/nigeria_acute-malnutrition-january-to-december-2022.xlsx"
    x = rd(f, "factors")
    y = pd.DataFrame({"area": x.iloc[2, 4:].values, "amn": x.iloc[3, 4:].values}).dropna()
    add("NGA", y, "2022-01", f, "domain", amn="amn")
    lga = []
    for f, sheets, start in [
        ("nigeria-acute-malnutrition-data/nigerian-acute-malnutrition-2024.xlsx", ["North West Nigeria", "North East Nigeria"], "2023-05"),
        ("nigeria-acute-malnutrition-data/nigerian-acute-malnutrition-2024-april-2025.xlsx", ["NORTH-WEST NIGERIA", "NORTH-EAST NIGERIA"], "2024-05"),
        ("nigeria-acute-malnutrition-data/nigerian-acute-malnutrition-2026-april-may-september.xlsx",
         ["NORTH-CENTRAL NIGERIA", "NORTH-WEST NIGERIA", "NORTH-EAST NIGERIA"], "2025-09")]:
        for s in sheets:
            x = rd(f, s)
            h = x[x[0].astype(str).str.strip().isin(["Zone", "Domain"])].index[0]
            x = x.loc[h + 1:]
            x = x[~x[1].astype(str).str.startswith("#") & x[1].notna()]
            x = x[~x[0].astype(str).str.contains("IDP", case=False)]
            x[0] = x[0].astype(str).str.replace("\n", " ").str.replace("Adama-wa", "Adamawa")
            add("NGA", x, start, f, "lga", area=1, adm1=0, gam=3)
            lga.append(x[[0, 1]].rename(columns={0: "domain", 1: "lga"}))
    # Central African Republic (sous-prefectures)
    f = "republique-centrafricaine-analyse-de-la-malnutrition-aigue-de-l-ipc/caf-ipc-estimation-populations-malnutrion-aigue-sep2023aout2024.xlsx"
    x = rd(f, "Sheet1").iloc[2:]
    add("CAF", x, "2023-09", f, "sous-prefecture", area=0, gam=1)
    f = "republique-centrafricaine-analyse-de-la-malnutrition-aigue-de-l-ipc/ipc_car_amn_mar2025_feb2026.xlsx"
    x = rd(f, "Table 1 (2)").iloc[1:]
    x["g"] = scale(x[4]) + scale(x[5])
    add("CAF", x, "2025-03", f, "sous-prefecture", area=0, gam="g")
    # Somalia (regions; median GAM)
    f = "somalia-acute-malnutrition-analysis/somalia-acute-malnutrion-august-2024-july-2025.xlsx"
    x = rd(f, "Sheet1").iloc[2:]
    add("SOM", x, "2024-08", f, "region", area=0, gam=4)
    # Yemen (zones -> districts listed in the caseload sheet)
    f = "yemen-acute-malnutrition/ipc_yemen_acute_food_malnutrition_nov2023_oct2024.xlsx"
    x = rd(f, "Summary pop with AM").iloc[2:]
    add("YEM", x, "2023-11", f, "zone", area=1, adm1=0, gam=3)
    z = rd(f, "TOTAL NUMBER OF CASES OF U5&PLW").iloc[2:]
    z[1] = z[1].ffill()
    yem = z[[1, 2]].dropna().rename(columns={1: "zone", 2: "district"})
    # South Sudan (counties): AMN phase and AFI phase in the same hotspot table
    f = "south-sudan-acute-malnutrition/ipc_ssd_projectionupdate_amn_apriljuly2026.xlsx"
    x = rd(f, "Hotspot counties AFI AMN").iloc[2:]
    x = x[x[2].astype(str).str.strip().isin(["WHZ", "MUAC"])]
    x["g"] = np.where(x[2].astype(str).str.strip() == "WHZ", x[3], np.nan)
    add("SSD", x, "2025-07", f, "county", area=1, adm1=0, gam="g", amn=4, afi=12)
    # DR Congo (health zones; territoire for AFI)
    f = "rdc-ipc-amn/rdc-ipc-amn-july2024-june2025.xlsx"
    x = rd(f, "BESOIN DE TRAITEMENT").iloc[3:]
    x = x[x[2].notna()]
    # prevalence columns in this sheet are not usable (%MAS above %MAM, GAM up to 53 percent); phase only
    add("COD", x, "2024-07", f, "zone de sante", area=1, adm1=0, amn=5)
    d = pd.concat(T, ignore_index=True)
    d.loc[d.gam <= 0, "gam"] = np.nan
    d["amn_derived"] = amn_phase(d.gam.values.astype(float))
    d["amn_any"] = d.amn.fillna(d.amn_derived)
    crosswalks = dict(nga=pd.concat(lga).drop_duplicates(), yem=yem)
    return d, crosswalks


def afi_for_amn(d, cw, O, F):
    """AFI (IPC/CH current) phase for each AMN area: same name; regions/domains/zones via member areas."""
    o = O.o.copy()
    o["an"], o["a1n"] = o.area_name.map(norm), o.adm1_name.map(norm)
    W = pd.read_parquet(INP / "panel" / "fnid_ipc_overlay.parquet")
    nga = cw["nga"].assign(dn=lambda x: x.domain.map(norm), ln=lambda x: x.lga.map(norm))
    yem = cw["yem"].assign(zn=lambda x: x.zone.astype(str).str.replace("\n", " ").map(norm),
                           dn=lambda x: x.district.astype(str).map(norm))
    alias = {"southadamawa": "southernadamawa", "eastborno": "easternborno"}
    d = d.reset_index(drop=True)
    rows = {}
    for (iso, start), grp in d.groupby(["iso3", "start"]):
        oc = o[o.iso3 == iso]
        if oc.empty:
            continue
        ref = start + 1
        months = pd.Series(oc.month.unique())
        dist = months.map(lambda x: abs((x - ref).n))
        mm = months[dist == dist.min()].min() if dist.min() <= 5 else None
        oc = oc[oc.month == mm] if mm is not None else oc.iloc[0:0]
        for r in grp.itertuples():
            rows[r.Index] = {}
            an = norm(r.area)
            sel = oc[oc.an == an]
            if r.level == "domain" and sel.empty:
                dn = alias.get(an, an)
                if "lga" in r.area.lower():
                    sel = oc[oc.an == norm(r.area.lower().replace("(lga)", ""))]
                else:
                    lg = nga[nga.dn == dn].ln
                    sel = oc[oc.an.isin(lg)]
            if r.level == "zone" and sel.empty:
                sel = oc[oc.an.isin(yem[yem.zn == an].dn)]
            if r.level in ("region", "province") and sel.empty:
                sel = oc[oc.a1n == an]
            if r.level == "zone de sante":
                sel = oc[oc.an == an]           # area column holds the territoire
            if sel.empty and len(an) > 3:
                cand = oc[oc.an.map(lambda x: sim(an, x) >= 0.88)]
                sel = cand[cand.a1n.map(lambda x: sim(norm(r.adm1), x) >= 0.7)] if r.adm1 and len(cand) > 1 else cand
            if sel.empty:
                continue
            w = sel.population.fillna(1)
            x = dict(afi=float((sel.phase * w).sum() / w.sum()), afi_max=float(sel.phase.max()),
                     afi_share3=float((sel.share3 * w).sum() / w.sum()), afi_month=str(mm), afi_n=len(sel))
            # FEWS NET current map over the same areas (overlay weights from 33_fewsnet_contribution)
            ww = W[W.key.isin(sel.key)]
            if len(ww):
                c = F.cs[F.cs.fnid.isin(ww.fnid) & (F.cs.month <= ref) & (F.cs.month >= ref - 4)]
                if len(c):
                    c = c[c.month == c.month.max()].merge(ww, on="fnid")
                    x["fews_cur"] = float((c.phase * c.w_key).sum() / c.w_key.sum())
            rows[r.Index] = x
    return d.join(pd.DataFrame.from_dict(rows, orient="index"))


# ------------------------------------------------------------------ statistics
def ci_mean(x):
    x = pd.Series(x).dropna()
    if len(x) < 2:
        return (x.mean() if len(x) else np.nan), np.nan, np.nan
    h = 1.96 * x.std(ddof=1) / np.sqrt(len(x))
    return x.mean(), x.mean() - h, x.mean() + h


def wilson(k, n):
    if n == 0:
        return np.nan, np.nan, np.nan
    p, z = k / n, 1.96
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, c - h, c + h


def phase_bin(x):
    b = np.floor(np.asarray(x, float) + 0.5).clip(1, 5)
    lab = [None if np.isnan(v) else ("4+" if v >= 4 else str(int(v))) for v in b]
    return pd.Series(lab, index=getattr(x, "index", None))


def ols(d, y, x, fe=None, cl="cluster"):
    """y on x (+ fixed effects by `fe`), SE clustered by `cl`."""
    d = d.dropna(subset=[y, x]).copy()
    if fe:
        n_g = d.groupby(fe)[y].transform("size")
        d = d[n_g > 1]
        Y = (d[y] - d.groupby(fe)[y].transform("mean")).values
        X = (d[x] - d.groupby(fe)[x].transform("mean")).values[:, None]
    else:
        Y, X = d[y].values, np.column_stack([d[x].values, np.ones(len(d))])
    if len(d) < 5 or np.allclose(X[:, 0], 0):
        return dict(coef=np.nan, se=np.nan, n=int(len(d)), clusters=0)
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ Y
    u = Y - X @ b
    meat = np.zeros((X.shape[1], X.shape[1]))
    for _, i in d.groupby(cl).indices.items():
        sc = X[i].T @ u[i]
        meat += np.outer(sc, sc)
    G = d[cl].nunique()
    V = XtXi @ meat @ XtXi * G / max(G - 1, 1)
    return dict(coef=float(b[0]), se=float(np.sqrt(V[0, 0])), n=int(len(d)), clusters=int(G))


MEASURES = {"fews_cur": "cur", "fews_fc": "fc", "ipc_ch": "ipc"}


def table(s):
    rows = []
    groups = [("SMART+ all", s[s.source == "SMART+"]), ("SMART+ ad hoc", s[(s.source == "SMART+") & ~s.recurring]),
              ("SMART+ Nigeria rounds", s[(s.source == "SMART+") & s.recurring]), ("FDW (BF, MR)", s[s.source == "FDW"])]
    for gname, d in groups:
        for mname, col in MEASURES.items():
            x = d.dropna(subset=[col]).copy()
            x["bin"] = phase_bin(x[col]).values
            for b, gg in list(x.groupby("bin")) + [("all", x)]:
                r = dict(source=gname, measure=mname, phase=b, n=len(gg))
                r["gam_mean"], r["gam_lo"], r["gam_hi"] = ci_mean(gg.gam)
                r["crit_share"], r["crit_lo"], r["crit_hi"] = wilson(int((gg.gam >= 15).sum()), int(gg.gam.notna().sum()))
                r["n_cdr"] = int(gg.cdr.notna().sum())
                r["cdr_mean"], r["cdr_lo"], r["cdr_hi"] = ci_mean(gg.cdr)
                r["n_u5dr"] = int(gg.u5dr.notna().sum())
                r["u5dr_mean"], r["u5dr_lo"], r["u5dr_hi"] = ci_mean(gg.u5dr)
                r["gam_muac_mean"] = gg.gam_muac.mean()
                rows.append(r)
    return pd.DataFrame(rows), groups


def main():
    if "fetch" in sys.argv:
        fetch()
    TAB.mkdir(parents=True, exist_ok=True)
    F, O = Fews(), Official()
    s = pd.concat([smartplus(), fdw()], ignore_index=True)
    s = attach(s, F, O)
    s["cy"] = s.iso2 + s.month.dt.year.astype(str)
    s.drop(columns=[c for c in ["period_date"] if c in s]).assign(month=s.month.astype(str)).to_csv(
        TAB / "phase_outcomes_surveys.csv", index=False)
    tab, groups = table(s)
    tab.to_csv(TAB / "phase_outcomes.csv", index=False)

    key = {"surveys": {}, "match": {}, "corr": {}, "ols": {}}
    for src, d in s.groupby("source"):
        key["surveys"][src] = {f"{c}": {"n": int(len(x)), "years": f"{x.month.min().year}-{x.month.max().year}"}
                               for c, x in d.groupby("iso2")}
    for gname, d in groups:
        key["match"][gname] = dict(n=int(len(d)), fews_unit=int((d.match != "none").sum()),
                                   fews_cur=int(d.cur.notna().sum()), fews_fc=int(d.fc.notna().sum()),
                                   ipc_ch=int(d.ipc.notna().sum()), with_cdr=int(d.cdr.notna().sum()))
        key["corr"][gname], key["ols"][gname] = {}, {}
        for mname, col in MEASURES.items():
            x = d.dropna(subset=[col, "gam"])
            key["corr"][gname][mname] = dict(
                n=int(len(x)), gam=float(x.gam.corr(x[col])) if len(x) > 4 else None,
                crit=float((x.gam >= 15).astype(float).corr(x[col])) if len(x) > 4 else None,
                cdr=float(x.cdr.corr(x[col])) if x.cdr.notna().sum() > 4 else None)
            key["ols"][gname][mname] = dict(gam_pooled=ols(d, "gam", col), gam_country_year_fe=ols(d, "gam", col, fe="cy"),
                                            cdr_pooled=ols(d, "cdr", col), cdr_country_year_fe=ols(d, "cdr", col, fe="cy"))

    # IPC acute malnutrition vs acute food insecurity
    a, cw = amn_tables()
    a = afi_for_amn(a, cw, O, F)
    a["afi"] = a.afi_file.fillna(a.get("afi"))
    a.assign(start=a.start.astype(str)).to_csv(TAB / "phase_outcomes_amn_areas.csv", index=False)
    rows, amn_key = [], {"areas": int(len(a)), "areas_with_afi": int(a.afi.notna().sum()),
                         "by_country": {k: dict(n=int(len(x)), with_afi=int(x.afi.notna().sum()),
                                                files=int(x.file.nunique()), explicit_amn=int(x.amn.notna().sum()))
                                        for k, x in a.groupby("iso3")}}
    for label, col in [("AMN explicit", "amn"), ("AMN derived from GAM", "amn_derived"), ("AMN any", "amn_any")]:
        x = a.dropna(subset=[col, "afi"]).copy()
        x["afi_bin"] = phase_bin(x.afi).values
        x["amn_bin"] = phase_bin(x[col]).values
        ct = x.groupby(["afi_bin", "amn_bin"]).size().rename("n").reset_index()
        ct["share_of_afi_row"] = ct.n / ct.groupby("afi_bin").n.transform("sum")
        ct["comparison"], ct["row"] = label, "crosstab"
        rows.append(ct)
        st = dict(n=int(len(x)), countries=sorted(x.iso3.unique().tolist()),
                  corr=float(x.afi.corr(x[col])) if len(x) > 4 else None,
                  spearman=float(x.afi.corr(x[col], method="spearman")) if len(x) > 4 else None,
                  exact_agree=float((x.afi_bin == x.amn_bin).mean()) if len(x) else None,
                  amn_worse=float((x[col] > x.afi.round()).mean()) if len(x) else None,
                  afi3_amn3=int(((x.afi >= 2.5) & (x[col] >= 3)).sum()), afi3=int((x.afi >= 2.5).sum()),
                  amn3=int((x[col] >= 3).sum()))
        st["by_country"] = {k: dict(n=int(len(z)), corr=float(z.afi.corr(z[col])) if len(z) > 4 else None,
                                    exact_agree=float((z.afi_bin == z.amn_bin).mean()),
                                    mean_afi=float(z.afi.mean()), mean_amn=float(z[col].mean()))
                            for k, z in x.groupby("iso3")}
        amn_key[label] = st
        rows.append(pd.DataFrame([dict(comparison=label, row="summary", n=st["n"], corr=st["corr"],
                                       spearman=st["spearman"], exact_agree=st["exact_agree"])]))
    # GAM prevalence (from the AMN files) by AFI phase and by FEWS NET phase, area level
    for label, col in [("GAM by AFI phase", "afi"), ("GAM by FEWS NET current phase", "fews_cur")]:
        if col not in a:
            continue
        x = a.dropna(subset=[col, "gam"]).copy()
        x["bin"] = phase_bin(x[col]).values
        for b, gg in list(x.groupby("bin")) + [("all", x)]:
            m_, lo, hi = ci_mean(gg.gam)
            rows.append(pd.DataFrame([dict(comparison=label, row="gam_by_phase", phase=b, n=len(gg), gam_mean=m_,
                                           gam_lo=lo, gam_hi=hi, crit_share=float((gg.gam >= 15).mean()))]))
        amn_key[f"corr_{label}"] = dict(n=int(len(x)), corr=float(x.gam.corr(x[col])) if len(x) > 4 else None)
        x["cl"] = x.iso3 + x.adm1.fillna("").map(norm)
        x["cf"] = x.iso3 + x.file
        amn_key[f"ols_{label}"] = dict(pooled=ols(x, "gam", col, cl="cl"), file_fe=ols(x, "gam", col, fe="cf", cl="cl"))
    pd.concat(rows, ignore_index=True).to_csv(TAB / "phase_outcomes_amn.csv", index=False)
    key["amn"] = amn_key
    key["notes"] = ("SMART+ surveys are mostly ad hoc (fielded when and where someone is worried); Nigeria NFSS/SOKAZA/"
                    "BENSS are numbered recurring rounds. FDW (BF, MR) are national SMART rounds; FDW Ethiopia values "
                    "are not served anonymously. AMN 'derived' phases apply IPC GAM thresholds to (often combined "
                    "WHZ/MUAC) GAM in the HDX files. Phase bins round the area mean phase; 4+ pools 4 and 5.")
    (TAB / "phase_outcomes_key.json").write_text(json.dumps(key, indent=1, default=str))
    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 200)
    print(json.dumps(key["match"], indent=1))
    print(tab[["source", "measure", "phase", "n", "gam_mean", "gam_lo", "gam_hi", "crit_share", "n_cdr", "cdr_mean",
               "u5dr_mean"]].round(2).to_string())
    print(json.dumps({k: key[k] for k in ["corr", "ols", "amn"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
