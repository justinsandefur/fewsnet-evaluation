"""Do acute food insecurity (AFI) phases track survey-measured household food insecurity?

Sub-national survey indicators (food consumption score, coping, hunger scale, dietary
diversity, livelihood coping) for FEWS NET countries, 2011-2024, matched to FEWS NET's
current map and forecast and to the official IPC / Cadre Harmonise (CH) phase for the
same area and month.

Sources (raw files in input/foodsec_surveys/<source>/; `fetch` re-downloads them)
  hfid       EU JRC Harmonized Food Insecurity Dataset (Machefer et al. 2025, Sci Data 12:741;
             HDX 'harmonized-food-insecurity-dataset-hfid', Zenodo 10.5281/zenodo.15017473, CC BY).
             Only its WFP columns are used here (its IPC/CH and FEWS NET phase columns are not):
               fcs_lit / rcsi_lit  WFP face-to-face surveys (CFSVA, EFSA and similar) compiled by
                                   Martini et al. 2022 (Nature Food; Zenodo 6953981), 2007-2021;
                                   share of households with insufficient (poor + borderline) food
                                   consumption, and with rCSI >= 19.
               fcs_rt / rcsi_rt    WFP real-time phone monitoring (mVAM / HungerMap LIVE), 2018 -
                                   May 2024; same two prevalences, daily values averaged by month.
             Values are admin-1 prevalences that HFID repeats over every admin-2 unit; they are
             collapsed back to admin 1 here. Sample sizes are not given.
  mvam_hdx   WFP mVAM databank files on HDX ('wfp-food-security-indicators-for-<country>',
             CC BY-IGO), 2015-2020, phone surveys: share poor FCS (FCG==1), poor+borderline
             (FCG<=2), mean FCS, mean rCSI, mean HDDS, by survey stratum (region, district or
             group of districts). Strata spanning several districts ("A-B-C") are the union of
             the named units; camps and unnamed strata are dropped.
  ch_hdx     Cadre Harmonise consolidated dataset (HDX 'cadre-harmonise', FSNWG): the "direct
             evidence" outcome indicators recorded with each current CH classification,
             2021-2023 only (earlier rows are blank): share poor / poor+borderline FCS, HDDS,
             HHS and rCSI phase shares, livelihood coping categories. These are the CH
             analysts' own inputs (household surveys, mostly WFP/government ENSAN and SAP
             rounds), not independent of the CH phase, and the CH phase attached to the
             same record is used as the official phase.

Not used (see code/README.md and the report): WFP HungerMap API (key needed), World Bank
LSMS-ISA / EHCVM / high-frequency phone surveys (free registration on the Microdata Library),
REACH MSNA household data (HDX 'request data'), IPC indicator worksheets (not public; the
IPC Population Tracking Tool exports phases and populations only), FSNAU zone indicators
(one season of FCS/coping/HHS in the Gu 2016 nutrition technical report, not transcribed).

Matching
  Every survey area gets a polygon (HFID: GADM polygons shipped with HFID; mVAM: names
  matched to geoBoundaries admin 1/2, then to HFID's GADM units; CH: CH district/region
  polygons via 24_area_rainfall.area_geometries). FEWS NET units (all vintages) are
  assigned to the area if their representative point lies inside it (or, for areas
  smaller than a unit, the unit containing the area's representative point).
  FEWS NET current situation: the nearest map within 4 months before or after the survey
  month (ties go to the earlier map); mean phase over the units, share of units in Phase 3+,
  share flagged "!". Forecast: the projection for the survey month from the latest report
  issued 3-8 months earlier (nearest lead per unit), mean phase and share 3+.
  Official IPC/CH: areas from input/panel/outcomes.parquet overlaid on the survey polygon;
  the analysis nearest the survey month within 4 months; phase is area-weighted, share
  of population in Phase 3+ is population-weighted. CH-source rows use their own record.

Usage: 66_foodsec_surveys.py [fetch]
Outputs: input/foodsec_surveys/indicators.parquet (one row per area x period x indicator)
         input/foodsec_surveys/areas.gpkg (survey-area polygons)
         input/foodsec_surveys/matched.parquet (indicators + FEWS NET / IPC-CH phases)
         output/tables/foodsec_phase.csv (means by phase), foodsec_phase_key.json
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
FS = INP / "foodsec_surveys"
HFID_URL = "https://data.humdata.org/dataset/f069706c-b7c8-47d8-a1d8-27b93c0832d2/resource/"
HFID_FILES = {"hfid_hv1.csv": "afc6e37c-185e-4e8f-ad96-e790f37a92c0/download/hfid_hv1.csv",
              "simplified_hfid_geom.gpkg": "43aef484-cc3e-4205-856b-028be786223b/download/simplified_hfid_geom.gpkg",
              "hdx_metadata_hfid.txt": "f92a63df-38a0-43c7-b567-b920883f06a8/download/hdx_metadata_hfid.txt"}
MARTINI = ("https://zenodo.org/api/records/6953981/files/Machine%20learning%20can%20guide%20food%20security"
           "%20efforts%20when%20primary%20data%20is%20not%20available.zip/content")
MVAM_ISO3 = {"chad": "TCD", "democratic-republic-of-the-congo": "COD", "kingdom-of-eswatini": "SWZ", "guinea": "GIN",
             "haiti": "HTI", "iraq": "IRQ", "lesotho": "LSO", "liberia": "LBR", "madagascar": "MDG", "malawi": "MWI",
             "mozambique": "MOZ", "nigeria": "NGA", "sierra-leone": "SLE", "syrian-arab-republic": "SYR",
             "yemen": "YEM", "zambia": "ZMB", "zimbabwe": "ZWE"}          # 'eswatini.csv' duplicates kingdom-of-eswatini
LIT_MODE = "WFP surveys (face-to-face per HFID; the Yemen series matches mVAM phone data)"
CH_LABEL_MONTH = {"Jan-May": 3, "Jun-Aug": 7, "Sep-Dec": 11}             # as in 23_outcome_panel.py
IND_LABEL = {
    "fcs_poor": "Share of households with poor food consumption (%)",
    "fcs_poor_borderline": "Share with poor or borderline food consumption (%)",
    "fcs_mean": "Mean food consumption score",
    "rcsi_mean": "Mean reduced coping strategies index",
    "rcsi_19plus": "Share with rCSI 19 or more (%)",
    "hhs_3plus": "Share with moderate or severe hunger, HHS 2+ (IPC Phase 3+) (%)",
    "hhs_4plus": "Share with severe hunger, HHS 4+ (IPC Phase 4+) (%)",
    "hdds_mean": "Mean household dietary diversity score",
    "hdds_phase3plus": "Share with HDDS in IPC Phase 3+ range (%)",
    "lcs_crisis_plus": "Share using crisis or emergency livelihood coping (%)",
}
HIGHER_WORSE = {k: k not in ("fcs_mean", "hdds_mean") for k in IND_LABEL}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


# ------------------------------------------------------------------ fetch
def fetch():
    (FS / "hfid").mkdir(parents=True, exist_ok=True)
    for f, u in HFID_FILES.items():
        (FS / "hfid" / f).write_bytes(requests.get(HFID_URL + u, timeout=600).content)
    d = FS / "mvam_hdx"
    d.mkdir(exist_ok=True)
    r = requests.get("https://data.humdata.org/api/3/action/package_search",
                     params={"q": "name:wfp-food-security-indicators*", "rows": 100}, timeout=60).json()["result"]
    urls = []
    for p in r["results"]:
        for x in p["resources"]:
            n = p["name"].replace("wfp-food-security-indicators-for-", "")
            urls.append((n, x["url"]))
            (d / f"{n}.csv").write_bytes(requests.get(x["url"], timeout=300).content)
    pd.DataFrame(urls).to_csv(d / "urls.txt", sep=" ", index=False, header=False)
    c = FS / "ch_hdx"
    c.mkdir(exist_ok=True)
    p = requests.get("https://data.humdata.org/api/3/action/package_show?id=cadre-harmonise", timeout=60).json()["result"]
    for x in p["resources"]:
        if x["format"] in ("XLSX", "PDF"):
            (c / Path(x["url"]).name).write_bytes(requests.get(x["url"], timeout=300).content)
    m = FS / "wfp_martini"            # upstream of HFID fcs_lit / rcsi_lit (kept for reference, not used)
    m.mkdir(exist_ok=True)
    (m / "martini2022.zip").write_bytes(requests.get(MARTINI, timeout=1800).content)


# ------------------------------------------------------------------ indicators
def iso_maps():
    h = pd.read_csv(FS / "hfid" / "hfid_hv1.csv", usecols=["iso2", "iso3", "ADMIN0"]).drop_duplicates("iso3")
    to2 = dict(zip(h.iso3, h.iso2))
    to2.update({"SWZ": "SZ", "NAM": "NA"})
    return to2, dict(zip(h.iso3, h.ADMIN0))


def hfid():
    d = pd.read_csv(FS / "hfid" / "hfid_hv1.csv")
    d = d.rename(columns={"ADMIN0": "country", "ADMIN1": "adm1_name", "fcs_rt mean": "fcs_rt", "rcsi_rt mean": "rcsi_rt"})
    out = []
    for col, ind, src, mode in [("fcs_lit", "fcs_poor_borderline", "wfp_lit", LIT_MODE),
                                ("rcsi_lit", "rcsi_19plus", "wfp_lit", LIT_MODE),
                                ("fcs_rt", "fcs_poor_borderline", "wfp_rt", "phone (mVAM)"),
                                ("rcsi_rt", "rcsi_19plus", "wfp_rt", "phone (mVAM)")]:
        x = d[d[col].notna()].drop_duplicates(["iso3", "adm1_name", "year_month"])
        out.append(pd.DataFrame({
            "iso3": x.iso3, "country": x.country, "adm1_name": x.adm1_name, "adm2_name": None,
            "adm1_pcode": None, "adm2_pcode": None, "area_id": "HFID|" + x.iso3 + "|" + x.adm1_name.astype(str),
            "level": "adm1", "source": src, "mode": mode, "month": pd.PeriodIndex(x.year_month, freq="M"),
            "indicator": ind, "value": 100 * x[col].values, "n": np.nan}))
    o = pd.concat(out, ignore_index=True)
    o["period_start"], o["period_end"] = o.month, o.month
    return o


def mvam():
    keep = {"FCG==1": ("fcs_poor", 100), "FCG<=2": ("fcs_poor_borderline", 100), "FCS": ("fcs_mean", 1),
            "rCSI": ("rcsi_mean", 1), "HDDS": ("hdds_mean", 1)}
    out = []
    for f in sorted((FS / "mvam_hdx").glob("*.csv")):
        if f.stem not in MVAM_ISO3:
            continue
        d = pd.read_csv(f, skiprows=[1])
        d = d[d.Demographic.isna() & d.Variable.isin(keep) & d.AdminStrata.notna() & d.Mean.notna()].copy()
        if d.empty:
            continue
        d["strata"] = d.AdminStrata.str.strip()
        d = d[d.strata.map(norm) != norm(d.ADM0_NAME.iloc[0])]
        d["month"] = pd.PeriodIndex(pd.to_datetime(d.SvyDate), freq="M")
        d = d.groupby(["ADM0_NAME", "strata", "month", "Variable"], as_index=False).Mean.mean()
        iso = MVAM_ISO3[f.stem]
        out.append(pd.DataFrame({
            "iso3": iso, "country": d.ADM0_NAME, "adm1_name": d.strata, "adm2_name": None, "adm1_pcode": None,
            "adm2_pcode": None, "area_id": "MVAM|" + iso + "|" + d.strata, "level": "stratum", "source": "mvam_hdx",
            "mode": "phone (mVAM)", "month": d.month, "indicator": d.Variable.map(lambda v: keep[v][0]),
            "value": d.Mean * d.Variable.map(lambda v: keep[v][1]), "n": np.nan}))
    o = pd.concat(out, ignore_index=True)
    o["period_start"], o["period_end"] = o.month, o.month
    return o


def ch():
    f = FS / "ch_hdx" / "cadre_harmonise_caf_ipc_mars26.xlsx"
    d = pd.read_excel(f)
    d = d[d.chtype.str.lower().eq("current") & d.usethisperiod.eq("Y") & d.adm0_pcod3.ne("CAF")].copy()
    d["area_id"] = d.adm2_pcod2.fillna(d.adm1_pcod2)
    d["month"] = pd.PeriodIndex([f"{int(y)}-{CH_LABEL_MONTH.get(l, 6):02d}" for y, l in
                                 zip(d.reference_year, d.reference_label)], freq="M")

    def s(*cols):
        v = sum(d[c].astype(float) for c in cols)
        return v.where(d[list(cols)].notna().all(axis=1))

    tot = {"fcs": s("FCG_Poor", "FCG_Borderline", "FCG_Acceptable"),
           "hdds": s(*[f"HDDS_Phase{i}" for i in range(1, 6)]), "hhs": s(*[f"HHS_Phase{i}" for i in range(1, 6)]),
           "lcs": s("LhHCSCat_NoStrategies", "LhHCSCat_StressStrategies", "LhHCSCat_CrisisStategies",
                    "LhHCSCat_EmergencyStrategies"), "rcsi": s("rCSI_Phase1", "rCSI_Phase2", "rCSI_Phase3")}
    vals = {"fcs_poor": ("fcs", s("FCG_Poor")), "fcs_poor_borderline": ("fcs", s("FCG_Poor", "FCG_Borderline")),
            "hdds_phase3plus": ("hdds", s("HDDS_Phase3", "HDDS_Phase4", "HDDS_Phase5")),
            "hhs_3plus": ("hhs", s("HHS_Phase3", "HHS_Phase4", "HHS_Phase5")),
            "hhs_4plus": ("hhs", s("HHS_Phase4", "HHS_Phase5")),
            "lcs_crisis_plus": ("lcs", s("LhHCSCat_CrisisStategies", "LhHCSCat_EmergencyStrategies")),
            "rcsi_19plus": ("rcsi", s("rCSI_Phase3"))}
    out = []
    pop = d.population.replace(0, np.nan)
    for ind, (g, v) in vals.items():
        t = tot[g]
        # shares are percentages summing to ~100; rows summing to ~1 are fractions; others are dropped
        v = np.where(t.between(0.95, 1.05), v * 100, np.where(t.between(95, 105), v, np.nan))
        out.append(pd.DataFrame({
            "iso3": d.adm0_pcod3, "country": d.adm0_name, "adm1_name": d.adm1_name, "adm2_name": d.adm2_name,
            "adm1_pcode": d.adm1_pcod2, "adm2_pcode": d.adm2_pcod2, "area_id": "CH|" + d.area_id.astype(str),
            "level": np.where(d.adm2_pcod2.notna(), "adm2", "adm1"), "source": "ch_hdx",
            "mode": "CH analysis input", "month": d.month, "indicator": ind, "value": v, "n": np.nan,
            "ch_phase": d.phase_class, "ch_share3": d.phase35 / pop, "ch_pop": d.population,
            "ch_area": d.area_id}))
    o = pd.concat(out, ignore_index=True).dropna(subset=["value"])
    o["period_start"], o["period_end"] = o.month, o.month       # survey timing approximate: the CH cycle
    return o.drop_duplicates(["area_id", "month", "indicator"], keep="last")


def indicators():
    to2, _ = iso_maps()
    d = pd.concat([hfid(), mvam(), ch()], ignore_index=True)
    d["iso2"] = d.iso3.map(to2)
    d["year"] = d.month.dt.year
    d = d[d.year.between(2011, 2024)]
    d["independent_of_ipc"] = d.source.ne("ch_hdx")
    d["ipc_note"] = np.where(d.source.eq("ch_hdx"),
                             "CH analysts' own direct-evidence input for this classification",
                             "WFP survey; not produced by IPC/CH or FEWS NET, but may have been used as evidence")
    d["indicator_label"] = d.indicator.map(IND_LABEL)
    return d.reset_index(drop=True)


# ------------------------------------------------------------------ geometry
def gazetteer():
    """Named polygons by country: geoBoundaries admin 1/2 (input/areas) and HFID's GADM units."""
    rows = []
    for lvl in ("adm1", "adm2"):
        for f in sorted((INP / "areas" / lvl).glob("*.geojson")):
            x = gpd.read_file(f)
            if "shapeName" in x:
                rows.append(gpd.GeoDataFrame({"iso3": f.stem, "name": x.shapeName, "src": f"gb_{lvl}"},
                                             geometry=x.geometry.values, crs=4326))
    g = hfid_geom()
    g1 = g.dissolve(by=["iso3", "ADMIN1"]).reset_index()
    rows.append(gpd.GeoDataFrame({"iso3": g1.iso3, "name": g1.ADMIN1, "src": "gadm_adm1"}, geometry=g1.geometry.values, crs=4326))
    g2 = g.dropna(subset=["ADMIN2"])
    rows.append(gpd.GeoDataFrame({"iso3": g2.iso3, "name": g2.ADMIN2, "src": "gadm_adm2"}, geometry=g2.geometry.values, crs=4326))
    z = pd.concat(rows, ignore_index=True)
    z["n"] = z.name.map(norm)
    return gpd.GeoDataFrame(z, crs=4326)


_HG = None


def hfid_geom():
    global _HG
    if _HG is None:
        g = gpd.read_file(FS / "hfid" / "simplified_hfid_geom.gpkg")
        iso = pd.read_csv(FS / "hfid" / "hfid_hv1.csv", usecols=["ADMIN0", "iso3"]).drop_duplicates("ADMIN0")
        g = g.merge(iso, on="ADMIN0", how="left")
        g["geometry"] = g.geometry.buffer(0)
        _HG = g
    return _HG


def find_name(Z, name):
    n = norm(name)
    if not n:
        return None
    for src in ("gb_adm1", "gadm_adm1", "gb_adm2", "gadm_adm2"):
        h = Z[(Z.src == src) & (Z.n == n)]
        if len(h):
            return h.geometry.union_all() if hasattr(h.geometry, "union_all") else h.geometry.unary_union
    best = Z.n.map(lambda o: SequenceMatcher(None, n, o).ratio())
    if len(best) and best.max() >= 0.88:
        h = Z[best == best.max()].iloc[:1]
        return h.geometry.iloc[0]
    return None


def area_geoms(d):
    """One polygon per area_id; how it was found."""
    out = {}
    # HFID admin 1: dissolve its GADM units
    g = hfid_geom()
    g1 = g.dissolve(by=["iso3", "ADMIN1"]).reset_index()
    g1["area_id"] = "HFID|" + g1.iso3 + "|" + g1.ADMIN1.astype(str)
    for a, geom in zip(g1.area_id, g1.geometry):
        out[a] = (geom, "HFID GADM polygon")
    # mVAM strata: names, then hyphen/and-separated components
    Z = gazetteer()
    for a in d.loc[d.source == "mvam_hdx", "area_id"].unique():
        _, iso, strata = a.split("|", 2)
        Zc = Z[Z.iso3 == iso]
        geom = find_name(Zc, strata)
        how = "name"
        if geom is None:
            parts = [p for p in re.split(r"\s*-\s*|\s+and\s+|/", strata) if p.strip()]
            gs = [find_name(Zc, p) for p in parts] if len(parts) > 1 else [None]
            if all(x is not None for x in gs):
                geom, how = gpd.GeoSeries(gs, crs=4326).union_all() if hasattr(gpd.GeoSeries, "union_all") else \
                    gpd.GeoSeries(gs, crs=4326).unary_union, "union of named units"
        if geom is not None:
            out[a] = (geom, how)
    # CH areas
    rain = load("rain", "24_area_rainfall.py")
    c = d[d.source == "ch_hdx"].drop_duplicates("area_id")
    fake = pd.DataFrame({"source": "CH", "iso3": c.iso3, "area_id": c.ch_area, "level": c.level,
                         "area_name": c.adm2_name.fillna(c.adm1_name), "adm1_name": c.adm1_name})
    geo, o = rain.area_geometries(fake)
    gk = geo.drop_duplicates("key").set_index("key").geometry
    for a, k, lv in zip("CH|" + o.area_id.astype(str), o.key, o.geo_level):
        if k in gk.index:
            out[a] = (gk[k], lv)
    for r in c.itertuples():          # codes and names not on the CH map: geoBoundaries / GADM by name
        if r.area_id not in out:
            geom = find_name(Z[Z.iso3 == r.iso3], r.adm2_name if isinstance(r.adm2_name, str) else r.adm1_name)
            if geom is not None:
                out[r.area_id] = (geom, "CH by name (gazetteer)")
    return gpd.GeoDataFrame({"area_id": list(out), "how": [v[1] for v in out.values()]},
                            geometry=[v[0].buffer(0) for v in out.values()], crs=4326)


# ------------------------------------------------------------------ matching
def fews_units(A, iso_of):
    """area_id -> FEWS NET fnids (all vintages)."""
    u = gpd.read_file(INP / "fewsnet" / "units.gpkg")[["fnid", "country_code", "geometry"]]
    u = u[u.geometry.notna()].copy()
    u["geometry"] = u.geometry.buffer(0)
    rp = u.copy()
    rp["geometry"] = u.geometry.representative_point()
    pairs = []
    for iso2, Ac in A.assign(iso2=A.area_id.map(iso_of)).groupby("iso2"):
        uc, rc = u[u.country_code == iso2], rp[rp.country_code == iso2]
        if uc.empty:
            continue
        j = gpd.sjoin(rc, Ac[["area_id", "geometry"]], predicate="within")[["fnid", "area_id"]]
        got = set(j.area_id)
        rest = Ac[~Ac.area_id.isin(got)].copy()
        if len(rest):
            rest["geometry"] = rest.geometry.representative_point()
            k = gpd.sjoin(rest[["area_id", "geometry"]], uc, predicate="within")[["fnid", "area_id"]]
            j = pd.concat([j, k])
        pairs.append(j)
    return pd.concat(pairs, ignore_index=True).drop_duplicates()


def fews_phases(rows, pairs):
    """rows: key, area_id, month. Current map nearest within +-4 months; forecast lead 3-8."""
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet", columns=["fnid", "month", "phase", "assist_flag"])
    pr = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet", columns=["fnid", "report_month", "month", "phase", "lead"])
    pr = pr[pr.lead.between(3, 8)]
    x = rows[["key", "area_id", "month"]].merge(pairs, on="area_id")
    # current situation
    c = x.merge(cs.rename(columns={"month": "cs_month"}), on="fnid")
    c["diff"] = (c.cs_month - c.month).map(lambda v: v.n)
    c = c[c["diff"].abs() <= 4]
    c["ad"], c["after"] = c["diff"].abs(), (c["diff"] > 0).astype(int)
    best = c.sort_values(["ad", "after"]).drop_duplicates("key")[["key", "cs_month"]]
    c = c.merge(best, on=["key", "cs_month"])
    cur = c.groupby("key").agg(fews_cs=("phase", "mean"), fews_cs_max=("phase", "max"),
                               fews_cs3=("phase", lambda p: (p >= 3).mean()),
                               fews_flag=("assist_flag", "mean"), fews_cs_month=("cs_month", "first"),
                               fews_cs_gap=("diff", "first"), fews_units=("fnid", "nunique"))
    # forecast
    f = x.merge(pr, on=["fnid", "month"])
    lastrep = f.groupby("key").report_month.max().rename("lr")
    f = f.merge(lastrep, on="key")
    f = f[f.report_month == f.lr].sort_values("lead").drop_duplicates(["key", "fnid"])
    fc = f.groupby("key").agg(fews_fc=("phase", "mean"), fews_fc3=("phase", lambda p: (p >= 3).mean()),
                              fews_fc_lead=("lead", "min"))
    return cur.join(fc, how="outer")


def official_phases(rows, A):
    """IPC/CH areas overlapping the survey polygon; nearest analysis within +-4 months."""
    rain = load("rain", "24_area_rainfall.py")
    geo, o = rain.area_geometries(pd.read_parquet(INP / "panel" / "outcomes.parquet"))
    o = o.dropna(subset=["phase"])
    g = geo[geo.key.isin(o.key)].drop_duplicates("key").copy()
    g["geometry"] = g.geometry.buffer(0)
    g = g.merge(o[["key", "iso3"]].drop_duplicates("key"), on="key")
    g = g.to_crs(6933)
    g["karea"] = g.area
    Ap = A.to_crs(6933)
    w = gpd.overlay(Ap[["area_id", "geometry"]], g[["key", "iso3", "karea", "geometry"]], how="intersection",
                    keep_geom_type=True)
    w["ia"] = w.area
    w["share_of_key"] = w.ia / w.karea
    w["wt"] = w.ia / w.groupby("area_id").ia.transform("sum")
    w = w[w.wt > 0.05]
    fine = ~w.key.str.contains(r"\|ADM1\|")
    has_fine = w[fine].area_id.unique()
    w = w[fine | ~w.area_id.isin(has_fine)][["area_id", "key", "ia", "share_of_key"]]
    x = rows[["key", "area_id", "month"]].rename(columns={"key": "rk"}).merge(w, on="area_id")
    x = x.merge(o[["key", "source", "month", "phase", "share3", "population"]].rename(columns={"month": "om"}), on="key")
    x["diff"] = (x.om - x.month).map(lambda v: v.n)
    x = x[x["diff"].abs() <= 4]
    x["ad"], x["after"] = x["diff"].abs(), (x["diff"] > 0).astype(int)
    best = x.sort_values(["ad", "after"]).drop_duplicates("rk")[["rk", "om", "source"]]
    x = x.merge(best, on=["rk", "om", "source"])
    x["pw"] = x.population.fillna(0) * x.share_of_key.clip(upper=1)
    x["ph_w"], x["p3_w"], x["s3_w"] = x.phase * x.ia, (x.phase >= 3) * x.ia, x.share3 * x.pw
    a = x.groupby("rk").agg(ia=("ia", "sum"), ph=("ph_w", "sum"), p3=("p3_w", "sum"), s3=("s3_w", "sum"),
                            pw=("pw", "sum"), ipc_source=("source", "first"), ipc_month=("om", "first"))
    out = pd.DataFrame({"ipc_phase": a.ph / a.ia, "ipc_area3": a.p3 / a.ia,
                        "ipc_share3": (a.s3 / a.pw).where(a.pw > 0), "ipc_source": a.ipc_source,
                        "ipc_month": a.ipc_month})
    out.index.name = "key"
    return out


# ------------------------------------------------------------------ analysis
def phase_bin(p):
    b = np.floor(p + 0.5).clip(1, 4)
    return b.map(lambda v: np.nan if pd.isna(v) else ("4+" if v >= 4 else str(int(v))))


def summarize(m):
    rows, key = [], {}
    m = m.copy()
    m["fews_cs_sub"] = m.fews_cs.where(m.fews_level.eq("sub-national"))
    m["group"] = np.where(m.source == "ch_hdx", "ch_hdx (IPC input)", "independent (" + m.source + ")")
    # pooled WFP sources: the same admin-1 x month x indicator can appear twice (HFID's "literature"
    # Yemen series is the mVAM phone series also on HDX); keep mvam_hdx, then wfp_lit, then wfp_rt
    pr = {"mvam_hdx": 0, "wfp_lit": 1, "wfp_rt": 2}
    ind_ = m[m.independent_of_ipc].assign(an=lambda z: z.adm1_name.map(norm), o=lambda z: z.source.map(pr))
    ind_ = ind_.sort_values("o").drop_duplicates(["iso3", "an", "month", "indicator"]).drop(columns=["an", "o"])
    groups = [("independent, all WFP sources", ind_)] + list(m.groupby("group"))
    for gname, g in groups:
        for ind, gi in g.groupby("indicator"):
            for col, lab in [("fews_cs", "FEWS NET current"), ("fews_cs_sub", "FEWS NET current, sub-national maps"),
                             ("fews_fc", "FEWS NET forecast"), ("ipc_phase", "IPC/CH phase")]:
                x = gi.dropna(subset=[col, "value"]).copy()
                if len(x) < 5:
                    continue
                x["bin"] = phase_bin(x[col])
                for b, xb in x.groupby("bin"):
                    rows.append(dict(group=gname, indicator=ind, phase_measure=lab, phase=b, n=len(xb),
                                     areas=xb.area_id.nunique(), mean=xb.value.mean(), sd=xb.value.std(),
                                     median=xb.value.median()))
                # correlations: pooled, within country (country-demeaned), within area over time
                xc = x.assign(v=x.value - x.groupby("iso3").value.transform("mean"),
                              p=x[col] - x.groupby("iso3")[col].transform("mean"))
                xa = x.assign(v=x.value - x.groupby("area_id").value.transform("mean"),
                              p=x[col] - x.groupby("area_id")[col].transform("mean"))
                sgn = 1 if HIGHER_WORSE[ind] else -1
                key.setdefault(gname, {}).setdefault(ind, {})[lab] = dict(
                    n=int(len(x)), areas=int(x.area_id.nunique()), countries=int(x.iso3.nunique()),
                    corr=float(x.value.corr(x[col])), spearman=float(x.value.corr(x[col], method="spearman")),
                    corr_within_country=float(xc.v.corr(xc.p)),
                    corr_within_area=float(xa.v.corr(xa.p)) if xa.p.std() > 0 else None,
                    sign_if_tracking=sgn)
                if col == "fews_cs" and len(x) >= 30:
                    key[gname][ind][lab]["by_country"] = {
                        c: dict(n=int(len(z)), areas=int(z.area_id.nunique()), corr=float(z.value.corr(z[col])))
                        for c, z in x.groupby("iso3") if len(z) >= 20 and z[col].std() > 0}
                if col == "ipc_phase":
                    y = x.dropna(subset=["ipc_share3"])
                    if len(y) >= 5:
                        key[gname][ind]["IPC/CH share 3+"] = dict(
                            n=int(len(y)), corr=float(y.value.corr(100 * y.ipc_share3)),
                            corr_within_country=float((y.value - y.groupby("iso3").value.transform("mean")).corr(
                                y.ipc_share3 - y.groupby("iso3").ipc_share3.transform("mean"))))
        # same sample: rows with both a FEWS NET current phase and an IPC/CH phase
        for ind, gi in g.groupby("indicator"):
            y = gi.dropna(subset=["value", "fews_cs", "ipc_phase"])
            if len(y) >= 20:
                key[gname][ind]["same_sample"] = dict(
                    n=int(len(y)), corr_fews=float(y.value.corr(y.fews_cs)), corr_ipc=float(y.value.corr(y.ipc_phase)),
                    corr_fews_ipc=float(y.fews_cs.corr(y.ipc_phase)),
                    within_country_fews=float((y.value - y.groupby("iso3").value.transform("mean")).corr(
                        y.fews_cs - y.groupby("iso3").fews_cs.transform("mean"))),
                    within_country_ipc=float((y.value - y.groupby("iso3").value.transform("mean")).corr(
                        y.ipc_phase - y.groupby("iso3").ipc_phase.transform("mean"))))
    return pd.DataFrame(rows), key


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch()
    d = indicators()
    d.drop(columns=["ch_area"]).to_parquet(FS / "indicators.parquet", index=False)
    A = area_geoms(d)
    A.to_file(FS / "areas.gpkg", driver="GPKG")
    iso2 = d.drop_duplicates("area_id").set_index("area_id").iso2
    unmatched = sorted(set(d.area_id) - set(A.area_id))
    d = d[d.area_id.isin(A.area_id)]
    pairs = fews_units(A, iso2.get)
    # one lookup per area x month
    rows = d[["area_id", "month"]].drop_duplicates().reset_index(drop=True)
    rows["key"] = rows.area_id + "@" + rows.month.astype(str)
    F = fews_phases(rows, pairs)
    F["fews_level"] = np.where(F.fews_cs.notna() | F.fews_fc.notna(), "sub-national", None)
    # remote-monitoring countries are mapped as one national unit (fnid = ISO2, no polygon): fallback
    nat = pd.DataFrame({"area_id": A.area_id, "fnid": A.area_id.map(iso2.get)}).dropna()
    Fn = fews_phases(rows[~rows.key.isin(F.dropna(subset=["fews_level"]).index)], nat)
    Fn["fews_level"] = "national"
    F = pd.concat([F.dropna(subset=["fews_level"]), Fn])
    O = official_phases(rows[~rows.area_id.str.startswith("CH|")], A[~A.area_id.str.startswith("CH|")])
    m = d.merge(rows, on=["area_id", "month"]).merge(F, left_on="key", right_index=True, how="left") \
        .merge(O, left_on="key", right_index=True, how="left")
    isch = m.source == "ch_hdx"
    m.loc[isch, "ipc_phase"] = m.loc[isch, "ch_phase"]
    m.loc[isch, "ipc_share3"] = m.loc[isch, "ch_share3"]
    m.loc[isch, "ipc_area3"] = (m.loc[isch, "ch_phase"] >= 3).astype(float)
    m.loc[isch, "ipc_source"] = "CH (same record)"
    m.loc[isch, "ipc_month"] = m.loc[isch, "month"]
    m = m.merge(A[["area_id", "how"]].rename(columns={"how": "geo_match"}), on="area_id", how="left")
    m["fews_units"] = m.fews_units.fillna(0)
    m = m.drop(columns=["key", "ch_area"])
    for c in ["fews_cs_month", "ipc_month"]:
        m[c] = m[c].astype(str).replace({"NaT": None, "nan": None})
    m.to_parquet(FS / "matched.parquet", index=False)

    tab, key = summarize(m)
    TAB.mkdir(parents=True, exist_ok=True)
    tab.to_csv(TAB / "foodsec_phase.csv", index=False)
    cov = d.groupby(["source", "iso3"]).agg(y0=("year", "min"), y1=("year", "max"), areas=("area_id", "nunique"),
                                             area_months=("month", "size")).reset_index()
    mm = m.drop_duplicates(["area_id", "month"])
    key["coverage"] = dict(
        indicator_rows=int(len(d)),
        area_periods=int(d[["area_id", "month"]].drop_duplicates().shape[0]),
        by_source={s: dict(rows=int((d.source == s).sum()), countries=int(d[d.source == s].iso3.nunique()),
                           area_periods=int(d[d.source == s][["area_id", "month"]].drop_duplicates().shape[0]),
                           matched_fews_cs=int(mm[(mm.source == s)].fews_cs.notna().sum()),
                           matched_fews_fc=int(mm[(mm.source == s)].fews_fc.notna().sum()),
                           matched_ipc=int(mm[(mm.source == s)].ipc_phase.notna().sum()),
                           matched_both=int((mm[(mm.source == s)].fews_cs.notna() &
                                             mm[(mm.source == s)].ipc_phase.notna()).sum()))
                   for s in d.source.unique()},
        geo_unmatched_areas=len(unmatched), geo_unmatched=unmatched)
    cov.to_csv(TAB / "foodsec_coverage.csv", index=False)
    (TAB / "foodsec_phase_key.json").write_text(json.dumps(key, indent=1, default=str))
    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 400)
    print(json.dumps(key["coverage"], indent=1))
    print(tab.round(1).to_string())


if __name__ == "__main__":
    main()
