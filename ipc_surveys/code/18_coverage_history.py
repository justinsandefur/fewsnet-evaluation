"""Reconstruct FEWS NET's country coverage month by month, 2009-2026, from two
independent sources, and classify country-level coverage switches as real
changes or gaps in the data API.

Source 1: the published map archive (ALL_HFIC.zip, regional current-situation
shapefiles June 2009 - mid 2023). Older files are dissolved by phase with no
country field, so a country counts as covered in a map if classified polygons
cover at least 25% of its land area (Natural Earth 1:50m boundaries).
Source 2: the data warehouse API panel (07_build_panel.py), 2011-2026.

A switch in the API (a country present one year and absent the next, or the
reverse) is classified as
  real        if the map archive agrees (or the switch is after mid-2023,
              where only the API is available: flagged "API only")
  archive gap if the map archive shows the country covered while the API has
              no data

Outputs: input/fewsnet/coverage_maps.csv (country x map month),
         output/tables/coverage_history.csv (country x year, both sources),
         output/tables/coverage_switches.csv, additions to key_numbers.json
"""
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
THRESH = 0.25


def map_coverage():
    out = INP / "fewsnet" / "coverage_maps.csv"
    if out.exists():
        return pd.read_csv(out)
    z = zipfile.ZipFile(INP / "fewsnet" / "ALL_HFIC.zip")
    shp = sorted(x for x in z.namelist() if x.endswith("_CS.shp"))
    ne = gpd.read_file("zip://" + str(INP / "boundaries" / "ne_50m_admin_0_countries.zip"))
    ne = ne[["ISO_A3_EH", "ADMIN", "geometry"]].rename(columns={"ISO_A3_EH": "iso3"}).to_crs(6933)
    ne["area"] = ne.area
    tmp = tempfile.mkdtemp()
    rows = []
    for x in shp:
        m = re.search(r"_(\d{6})_CS\.shp$", x)
        if not m:
            continue
        month = f"{m.group(1)[:4]}-{m.group(1)[4:]}"
        base = x[:-4]
        for e in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            if base + e in z.namelist():
                z.extract(base + e, tmp)
        g = gpd.read_file(os.path.join(tmp, x))
        if g.crs is None:
            g = g.set_crs(4326)
        g = g[pd.to_numeric(g.CS, errors="coerce").between(1, 5)]
        if g.empty:
            continue
        g = g.to_crs(6933)
        u = gpd.GeoDataFrame(geometry=[g.buffer(0).unary_union], crs=6933)
        inter = gpd.overlay(ne, u, how="intersection")
        inter["share"] = inter.area / inter["area"]
        for r in inter[inter.share >= THRESH].itertuples():
            rows.append({"region_file": x.split("/")[2], "month": month, "iso3": r.iso3, "country": r.ADMIN,
                         "share": round(r.share, 3)})
        print(x.split("/")[-1], (inter.share >= THRESH).sum())
    d = pd.DataFrame(rows)
    d.to_csv(out, index=False)
    return d


def main():
    maps = map_coverage()
    maps["year"] = maps.month.str[:4].astype(int)
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    iso2to3 = dict(zip(codes.iso3166a2, codes.iso3166a3))
    names = dict(zip(codes.iso3166a3, codes.preferred_name))
    cls = pd.read_parquet(INP / "fewsnet" / "classifications.parquet", columns=["country_code", "report_month"])
    cls["iso3"] = cls.country_code.map(iso2to3)
    cls["year"] = cls.report_month.dt.year
    api = cls.groupby(["iso3", "year"]).size().gt(0)
    mp = maps.groupby(["iso3", "year"]).size().gt(0)
    isos = sorted(set(api.index.get_level_values(0)) | set(mp.index.get_level_values(0)))
    years = range(2009, 2027)
    H = pd.MultiIndex.from_product([isos, years], names=["iso3", "year"]).to_frame(index=False)
    H["api"] = H.set_index(["iso3", "year"]).index.map(api).fillna(False).astype(bool)
    H["maps"] = H.set_index(["iso3", "year"]).index.map(mp).fillna(False).astype(bool)
    # the archive ends Oct 2022 (Central Asia: June 2021); beyond that, maps are unavailable
    last = maps.groupby("iso3").region_file.first().map(
        maps.groupby("region_file").year.max()).reindex(H.iso3).values
    H.loc[H.year > np.nan_to_num(last, nan=2022), "maps"] = np.nan
    H["maps_n"] = H.set_index(["iso3", "year"]).index.map(maps.groupby(["iso3", "year"]).size()).fillna(0)
    # best estimate of coverage: maps where available (2009-2023), API otherwise
    # combined series: covered if either source shows the country (each source has its own gaps)
    H["covered"] = (H.api | (H.maps.fillna(0).astype(float) > 0))
    H["country"] = H.iso3.map(names)
    H.to_csv(TAB / "coverage_history.csv", index=False)

    # switches in the API series 2011-2026, classified against the map archive
    sw = []
    for iso, g in H[H.year >= 2011].sort_values("year").groupby("iso3"):
        a = g.set_index("year").api
        mm = g.set_index("year").maps
        for y in a.index[1:]:
            if a[y] != a[y - 1]:
                kind = "API only (after mid-2023)"
                if pd.notna(mm[y]) and pd.notna(mm[y - 1]):
                    kind = "real" if (mm[y] == a[y] and mm[y - 1] == a[y - 1]) else "API gap (maps show coverage)"
                sw.append({"iso3": iso, "country": names.get(iso, iso), "year": y,
                           "direction": "on" if a[y] else "off", "classification": kind,
                           "maps_prev": mm[y - 1], "maps_now": mm[y]})
    S = pd.DataFrame(sw)
    # switches in the map-based series (real coverage changes), 2010-2023
    real = []
    for iso, g in H[(H.year >= 2009) & (H.year <= 2026) & (H.iso3 != "-99")].sort_values("year").groupby("iso3"):
        c = g.set_index("year").covered
        for y in c.index[1:]:
            if c[y] != c[y - 1]:
                real.append({"iso3": iso, "country": names.get(iso, iso), "year": y,
                             "direction": "on" if c[y] else "off"})
    R = pd.DataFrame(real)
    S.to_csv(TAB / "coverage_switches_api.csv", index=False)
    R.to_csv(TAB / "coverage_switches_maps.csv", index=False)
    print(S.classification.value_counts())
    print(R.sort_values(["year", "iso3"]).to_string())
    k = json.loads((TAB / "key_numbers.json").read_text())
    k["coverage_switches_classified"] = S.classification.value_counts().to_dict()
    k["coverage_switches_combined_2010_2026"] = int(len(R))
    k["coverage_switches_combined_pre2025"] = int((R.year <= 2024).sum())
    k["coverage_countries_ever"] = int(H.groupby("iso3").covered.any().sum())
    (TAB / "key_numbers.json").write_text(json.dumps(k, indent=1, default=str))


if __name__ == "__main__":
    main()
