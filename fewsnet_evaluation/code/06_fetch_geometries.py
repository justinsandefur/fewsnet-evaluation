"""Download boundaries for every FEWS NET classification unit.

FEWS NET classifies "food security classification" (FSC) units: livelihood
zones, admin zones, combined admin x livelihood zones, remote-monitoring
admin zones, urban areas and camps. Each unit has a stable FNID and a
validity period, so boundary changes across report vintages are handled by
joining on FNID rather than on names.

Output: input/fewsnet/units.gpkg (one layer, all countries and vintages)
"""
import json
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "input" / "fewsnet" / "geo_raw"
RAW.mkdir(parents=True, exist_ok=True)
URL = "https://fdw.fews.net/api/feature/"
UNIT_TYPES = ["fsc_admin_lhz", "fsc_admin", "fsc_lhz", "fsc_rm_admin",
              "fsc_urban", "idp_camp", "livelihood_zone"]


def fetch(cc: str, ut: str) -> list:
    path = RAW / f"{cc}_{ut}.geojson"
    if not path.exists():
        r = requests.get(URL, params={"format": "geojson", "country_code": cc,
                                      "unit_type": ut}, timeout=600)
        r.raise_for_status()
        path.write_bytes(r.content)
        time.sleep(1)
    return json.loads(path.read_text()).get("features", [])


def main():
    panel = pd.read_parquet(ROOT / "input" / "fewsnet" / "ipcphase.parquet",
                            columns=["country_code", "fnid"])
    needed = set(panel.fnid.dropna())
    rows = []
    for cc in sorted(panel.country_code.dropna().unique()):
        for ut in UNIT_TYPES:
            feats = fetch(cc, ut)
            for f in feats:
                p = f["properties"]
                if p["fnid"] in needed and f.get("geometry"):
                    rows.append({"fnid": p["fnid"], "name": p["name"], "country_code": cc,
                                 "unit_type": p["unit_type_code"],
                                 "start_date": p["start_date"], "end_date": p["end_date"],
                                 "layer": p["layer_name"], "geometry": shape(f["geometry"])})
            print(cc, ut, len(feats))
    g = gpd.GeoDataFrame(rows, crs="EPSG:4326").drop_duplicates("fnid")
    g.to_file(ROOT / "input" / "fewsnet" / "units.gpkg", driver="GPKG")
    missing = needed - set(g.fnid)
    print(f"{len(g):,} units with geometry; {len(missing):,} FNIDs in panel lack geometry")


if __name__ == "__main__":
    main()
