"""Monthly rainfall for every outcome area (CHIRPS, 0.2 degree), and rainfall
shocks for each analysis.

Geometries:
  CH  district polygons from the March 2023 Cadre Harmonise map (by district
      code); regions (admin 1) built by merging their districts.
  IPC area polygons from each country's latest IPC map, matched to outcome
      records by normalized area name; otherwise unmatched (reported).

Shock for an analysis in month t: total rainfall over the 12 months ending in
t-1, expressed as a z-score against the same 12-month window in 1981-2010 for
that area. Also a 6-month version. Drought = z below -1.

Outputs: input/panel/area_rain_monthly.parquet, input/panel/analysis_panel.parquet,
         output/tables/rain_match_rates.csv
"""
import json
import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio import features
from rasterio.transform import Affine, rowcol

ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
CH_DIR = INP / "chirps"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def grids():
    g = {}
    for box in ["afr", "lac"]:
        m = json.loads((CH_DIR / f"{box}_meta.json").read_text())
        g[box] = (Affine(*m["transform"]), tuple(m["shape"]))
    return g


def area_geometries(outcomes):
    ch = gpd.read_file(INP / "areas" / "ch_current_2023.geojson")
    ch = ch[["adm0_pcod3", "adm1_pcod2", "adm2_pcod2", "geometry"]].drop_duplicates("adm2_pcod2")
    d2 = ch.dropna(subset=["adm2_pcod2"]).rename(columns={"adm2_pcod2": "area_id"})[["area_id", "geometry"]]
    d1 = ch.dissolve(by="adm1_pcod2").reset_index().rename(columns={"adm1_pcod2": "area_id"})[["area_id", "geometry"]]
    chg = pd.concat([d2, d1[~d1.area_id.isin(d2.area_id)]])
    chg["key"] = chg.area_id
    ipc = []
    for f in sorted((INP / "areas" / "ipc").glob("ipc_*.geojson")):
        iso = f.stem.split("_")[1].upper()
        x = gpd.read_file(f)
        if "title" not in x.columns or x.empty:      # some country files are empty (e.g. South Sudan)
            continue
        x = x[["title", "geometry"]]
        x["iso3"] = iso
        ipc.append(x)
    ipc = pd.concat(ipc, ignore_index=True)
    ipc["key"] = ipc.iso3 + "|" + ipc.title.map(norm)
    ipc = ipc.drop_duplicates("key")
    # fallback: region (admin 1) polygons from geoBoundaries, matched on the IPC "Level 1" name
    adm1 = []
    for f in sorted((INP / "areas" / "adm1").glob("*.geojson")):
        x = gpd.read_file(f)
        if "shapeName" not in x.columns:
            continue
        x["key"] = f.stem + "|ADM1|" + x.shapeName.map(norm)
        adm1.append(x[["key", "geometry"]])
    adm1 = pd.concat(adm1).drop_duplicates("key")
    adm2 = []
    for f in sorted((INP / "areas" / "adm2").glob("*.geojson")):
        x = gpd.read_file(f)
        if "shapeName" not in x.columns:
            continue
        x["key"] = f.stem + "|ADM2|" + x.shapeName.map(norm)
        adm2.append(x[["key", "geometry"]])
    adm2 = pd.concat(adm2).drop_duplicates("key")
    geo = gpd.GeoDataFrame(pd.concat([chg[["key", "geometry"]], ipc[["key", "geometry"]], adm1, adm2]), crs=4326)
    o = outcomes.copy()
    o["key"] = np.where(o.source == "CH", o.area_id, o.iso3 + "|" + o.area_name.map(norm))
    o["geo_level"] = np.where(o.source == "CH", "CH district/region", "IPC area")
    k1 = o.iso3 + "|ADM1|" + o.adm1_name.map(norm)
    # IPC areas with no area map: try their region, then the area name as a region name
    k1b = o.iso3 + "|ADM1|" + o.area_name.map(norm)
    keys = set(geo.key)
    miss = (o.source == "IPC") & ~o.key.isin(keys)
    use1 = miss & k1.isin(keys)
    use1b = miss & ~use1 & k1b.isin(keys)
    o.loc[use1, "key"], o.loc[use1, "geo_level"] = k1[use1], "region (admin 1)"
    o.loc[use1b, "key"], o.loc[use1b, "geo_level"] = k1b[use1b], "region (admin 1)"
    # CH records whose codes are not on the 2023 map: match district, then region, by name
    chmiss = (o.source == "CH") & ~o.key.isin(keys)
    k2 = o.iso3 + "|ADM2|" + o.area_name.map(norm)
    u2 = chmiss & (o.level == "adm2") & k2.isin(keys)
    o.loc[u2, "key"], o.loc[u2, "geo_level"] = k2[u2], "CH by name (admin 2)"
    u1 = chmiss & ~u2 & k1.isin(keys)
    o.loc[u1, "key"], o.loc[u1, "geo_level"] = k1[u1], "CH by name (admin 1)"
    u1b = chmiss & ~u2 & ~u1 & k1b.isin(keys)
    o.loc[u1b, "key"], o.loc[u1b, "geo_level"] = k1b[u1b], "CH by name (admin 1)"
    return geo, o


def cell_index(geo, gr):
    """For each area, the flat indices of grid cells it covers (all-touched),
    falling back to the cell containing its centroid."""
    idx = {}
    for box, (tr, shape) in gr.items():
        w, n = tr.c, tr.f
        e, s = w + tr.a * shape[1], n + tr.e * shape[0]
        sub = geo.cx[w:e, s:n]
        for k, gm in zip(sub.key, sub.geometry):
            if k in idx or gm is None or gm.is_empty:
                continue
            mask = features.rasterize([(gm, 1)], out_shape=shape, transform=tr, all_touched=True, dtype="uint8")
            cells = np.flatnonzero(mask)
            if cells.size == 0:
                c = gm.representative_point()
                r, cc = rowcol(tr, c.x, c.y)
                if 0 <= r < shape[0] and 0 <= cc < shape[1]:
                    cells = np.array([r * shape[1] + cc])
            if cells.size:
                idx[k] = (box, cells)
    return idx


def monthly_rain(idx):
    months = pd.period_range("1981-01", "2026-08", freq="M")
    keys = list(idx)
    out = np.full((len(keys), len(months)), np.nan, dtype="float32")
    for j, m in enumerate(months):
        arrs = {}
        for box in ["afr", "lac"]:
            f = CH_DIR / f"{box}_{m.year}_{m.month:02d}.npy"
            if f.exists():
                arrs[box] = np.load(f).ravel()
        for i, k in enumerate(keys):
            box, cells = idx[k]
            if box in arrs:
                v = arrs[box][cells]
                if np.isfinite(v).any():
                    out[i, j] = np.nanmean(v)
    return pd.DataFrame(out, index=keys, columns=months)


def shocks(R, o):
    """Rainfall over the 12 (6) months ending in t-1, against the same window in
    the previous 20 years (a rolling normal that removes slow trends such as the
    Sahel's recovery since the 1980s). z = standardized deviation; ratio =
    rainfall / normal. Drought: z < -1 and ratio < 0.85."""
    cum = {12: R.T.rolling(12, min_periods=12).sum().T, 6: R.T.rolling(6, min_periods=6).sum().T}
    rows = []
    for k, m in o[["key", "month"]].drop_duplicates().itertuples(index=False):
        end = m - 1
        rec = {"key": k, "month": m}
        for w, c in cum.items():
            if k not in c.index or end not in c.columns:
                rec[f"rain_z{w}"], rec[f"rain_ratio{w}"] = np.nan, np.nan
                continue
            ref = c.loc[k, [end - 12 * j for j in range(1, 21) if (end - 12 * j) in c.columns]].dropna()
            v = c.loc[k, end]
            if len(ref) < 15 or ref.std() == 0 or pd.isna(v):
                rec[f"rain_z{w}"], rec[f"rain_ratio{w}"] = np.nan, np.nan
                continue
            rec[f"rain_z{w}"] = (v - ref.mean()) / ref.std()
            rec[f"rain_ratio{w}"] = v / ref.mean() if ref.mean() > 0 else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    outcomes = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    geo, o = area_geometries(outcomes)
    gr = grids()
    idx = cell_index(geo, gr)
    R = monthly_rain(idx)
    R.columns = R.columns.astype(str)
    R.to_parquet(INP / "panel" / "area_rain_monthly.parquet")
    R.columns = pd.PeriodIndex(R.columns, freq="M")
    S = shocks(R, o)
    p = o.merge(S, on=["key", "month"], how="left")
    p["drought"] = ((p.rain_z12 < -1) & (p.rain_ratio12 < 0.85)).astype(float).where(p.rain_z12.notna())
    p.to_parquet(INP / "panel" / "analysis_panel.parquet", index=False)
    print(p.groupby(["source", "geo_level"]).size())
    mr = p.groupby(["source", "iso3"]).agg(rows=("key", "size"), with_rain=("rain_z12", lambda x: x.notna().mean()),
                                           drought_rate=("drought", "mean")).round(3)
    mr.to_csv(TAB / "rain_match_rates.csv")
    print(mr.to_string())
    print(p.groupby("source").rain_z12.apply(lambda x: x.notna().mean()).round(3))


if __name__ == "__main__":
    main()
