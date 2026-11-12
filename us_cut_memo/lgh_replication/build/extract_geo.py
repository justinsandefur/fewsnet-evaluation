"""Rainfall, population and district for each Somali FEWS NET unit (geospatial steps only, no analysis).

Reads
  raw/geo/SO_fsc_admin_lhz.geojson  FEWS NET Somalia units (district x livelihood zone, 2009/2011/2016 maps)
  raw/geo/SO_idp_camp.geojson       FEWS NET Somalia IDP-settlement units (points, named after their town)
  raw/geo/chirps/afr_YYYY_MM.npy    CHIRPS v2.0 monthly rainfall (mm), Africa window at 0.2 degrees,
                                    one grid per month 1981-01 to 2026-08; afr_meta.json gives the grid.
                                    A missing month is downloaded from the public CHIRPS file (fetch_chirps)
  raw/geo/SOM.tif                   WorldPop 2020 population, UN-adjusted, 1 km
  raw/geo/som.geojson.zip           OCHA COD-AB Somalia boundaries (v03), admin-2 layer
  raw/fewsnet/ipcphase_so.csv       FEWS NET classifications for Somalia (only the list of Somali unit ids and names)
Writes
  source/unit_rain.csv        fnid, month (YYYY-MM), rain: mean monthly rainfall over the unit's grid cells
  source/unit_population.csv  fnid, pop: people living inside the unit (missing for IDP point units)
  source/unit_district.csv    fnid, vintage, unit_name, admin1_pcode, admin1, admin2_pcode, admin2

Rainfall shocks, weights and everything else are computed in Stata.
"""
import json
import re
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from rasterio.mask import mask
from rasterio.transform import Affine, rowcol
from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
GEO, OUT = HERE / "raw" / "geo", HERE / "source"
CHIRPS_URL = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/cogs/chirps-v2.0.{y}.{m:02d}.cog"
MONTHS = pd.period_range("1981-01", "2026-08", freq="M")


def read_units(file):
    """FEWS NET units in one geojson file (as downloaded from the FEWS NET API): fnid, name, geometry."""
    feats = json.loads((GEO / file).read_text())["features"]
    rows = [{"fnid": f["properties"]["fnid"], "name": f["properties"]["name"], "geometry": shape(f["geometry"])}
            for f in feats if f.get("geometry")]
    return gpd.GeoDataFrame(rows, crs="EPSG:4326").drop_duplicates("fnid")


def units():
    """Somali FEWS NET unit polygons, one row per unit id (fnid)."""
    u = read_units("SO_fsc_admin_lhz.geojson")
    u["geometry"] = u.geometry.buffer(0)     # repair invalid polygons (self-intersections)
    return u


def fetch_chirps(y, m):
    """Download one month of CHIRPS and keep every 4th pixel (0.05 -> 0.2 degrees) in the Africa window.
    This is how the grids in raw/geo/chirps were made (originally by ../../code/22_fetch_chirps.py)."""
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds
    with rasterio.open("/vsicurl/" + CHIRPS_URL.format(y=y, m=m)) as src:
        win = from_bounds(-20.0, -36.0, 78.0, 40.0, src.transform)
        dims = (int(round(win.height / 4)), int(round(win.width / 4)))
        a = src.read(1, window=win, out_shape=dims, resampling=Resampling.nearest).astype("float32")
        meta = GEO / "chirps" / "afr_meta.json"
        if not meta.exists():
            t = src.window_transform(win) * Affine.scale(win.width / dims[1], win.height / dims[0])
            meta.write_text(json.dumps({"transform": list(t)[:6], "shape": dims}))
    a[a < 0] = np.nan                        # ocean pixels are negative: set to missing
    np.save(GEO / "chirps" / f"afr_{y}_{m:02d}.npy", a)


def rain(u):
    """Monthly rainfall averaged over the grid cells each unit touches."""
    for p in MONTHS:                         # download any month not already in raw/geo/chirps
        if not (GEO / "chirps" / f"afr_{p.year}_{p.month:02d}.npy").exists():
            fetch_chirps(p.year, p.month)
    meta = json.loads((GEO / "chirps" / "afr_meta.json").read_text())
    tr, dims = Affine(*meta["transform"]), tuple(meta["shape"])
    # 1. for each unit, the grid cells it touches (or, if none, the cell holding an interior point)
    cells = {}
    for fnid, g in zip(u.fnid, u.geometry):
        m = features.rasterize([(g, 1)], out_shape=dims, transform=tr, all_touched=True, dtype="uint8")
        c = np.flatnonzero(m)
        if c.size == 0:
            pt = g.representative_point()
            r, cc = rowcol(tr, pt.x, pt.y)
            c = np.array([r * dims[1] + cc])
        cells[fnid] = c
    # 2. each month, the mean over those cells (ignoring ocean cells; missing if all are ocean)
    rows = []
    for p in MONTHS:
        a = np.load(GEO / "chirps" / f"afr_{p.year}_{p.month:02d}.npy").ravel()
        for fnid, c in cells.items():
            v = a[c]
            rows.append((fnid, str(p), np.nanmean(v) if np.isfinite(v).any() else np.nan))
    return pd.DataFrame(rows, columns=["fnid", "month", "rain"])


def population(u, idp):
    """WorldPop people inside each unit polygon (pixels whose centre lies inside the polygon)."""
    rows = []
    with rasterio.open(GEO / "SOM.tif") as src:
        for fnid, g in zip(u.fnid, u.geometry):
            a, _ = mask(src, [g], crop=True, all_touched=False)
            v = a[0].astype(float)
            v = v[(v > 0) & (v != src.nodata)] if src.nodata is not None else v[v > 0]
            rows.append((fnid, float(v.sum())))
    rows += [(fnid, np.nan) for fnid in idp.fnid]   # IDP units are points: no population
    return pd.DataFrame(rows, columns=["fnid", "pop"])


def districts(idp):
    """OCHA admin-2 district of every Somali FEWS NET unit (all map vintages).
    District x livelihood-zone units carry the district P-code in their id: SO yyyy C3 RR DD zz -> SORRDD.
    IDP units are named after their town and are matched to the district of the same name.
    The 17 Banadir (Mogadishu) districts are pooled as SO22, as in the aid data."""
    z = zipfile.ZipFile(GEO / "som.geojson.zip")
    cod = pd.DataFrame([f["properties"] for f in json.loads(z.read("som_admin2.geojson"))["features"]])
    cod = cod[cod.adm2_pcode != "Unspecified"].reset_index(drop=True)
    cod.loc[len(cod)] = {"adm1_pcode": "SO22", "adm1_name": "Banadir", "adm2_pcode": "SO22", "adm2_name": "Banadir"}
    a1 = dict(zip(cod.adm1_pcode, cod.adm1_name))
    a2 = dict(zip(cod.adm2_pcode, cod.adm2_name))
    by_name = {n.lower(): c for c, n in a2.items()}
    # town spellings in the FEWS NET IDP names that differ from the OCHA names
    by_name.update({"laasanood": "SO1401", "dolo": "SO2605", "qarhdo": "SO1606", "mogadishu": "SO22"})
    idp_name = dict(zip(idp.fnid, idp.name))
    # every Somali unit id in the FEWS NET classifications
    f = pd.read_csv(HERE / "raw" / "fewsnet" / "ipcphase_so.csv", encoding="utf-8-sig", low_memory=False,
                    usecols=["fnid", "country_code", "geographic_unit_name"])
    f = f[f.country_code == "SO"].drop_duplicates("fnid")
    rows = []
    for fnid, name in zip(f.fnid, f.geographic_unit_name):
        m = re.fullmatch(r"SO(\d{4}C3)(\d{2})(\d{2})\d{2}", fnid)
        if m:                                           # district x livelihood-zone unit
            vintage, p2 = m.group(1), "SO" + m.group(2) + m.group(3)
            p2 = "SO22" if p2.startswith("SO22") else p2
        else:                                           # IDP settlement, or the whole country ("SO")
            vintage, p2 = "SO-other", by_name.get(str(idp_name.get(fnid, "")).lower())
        rows.append({"fnid": fnid, "vintage": vintage, "unit_name": name,
                     "admin1_pcode": p2[:4] if p2 else None, "admin1": a1.get(p2[:4]) if p2 else None,
                     "admin2_pcode": p2, "admin2": a2.get(p2)})
    return pd.DataFrame(rows).sort_values("fnid")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    u = units()
    idp = read_units("SO_idp_camp.geojson")
    r = rain(u)
    r.to_csv(OUT / "unit_rain.csv", index=False)
    p = population(u, idp)
    p.to_csv(OUT / "unit_population.csv", index=False)
    d = districts(idp)
    d.to_csv(OUT / "unit_district.csv", index=False)
    print(f"unit_rain.csv {len(r):,} rows ({r.fnid.nunique()} units x {r.month.nunique()} months); "
          f"unit_population.csv {len(p)} units; unit_district.csv {len(d)} units, "
          f"{d.admin2_pcode.isna().sum()} without a district")
