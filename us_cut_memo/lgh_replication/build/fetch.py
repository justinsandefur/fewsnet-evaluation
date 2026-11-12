"""Download the public raw files into raw/ (skips files already there). No processing.

Several sources are updated over time (FTS, ACLED, WFP prices, the FEWS NET archive), so a new download can
differ slightly from the copies used for the paper (downloaded September-October 2026). CHIRPS rainfall is
downloaded by extract_geo.py. Files that cannot be downloaded again are kept in the package (raw/SOURCES.md).
"""
import json
import time
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parent / "raw"
HDX = "https://data.humdata.org/dataset"
FILES = {
    # OCHA 3W operational presence (HDX dataset somalia-operational-presence)
    "3w/3W_Operational_Presence_Dataset_Jan-Nov_2024.xlsx": f"{HDX}/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/1176ba40-f695-4edd-ab07-90e08226e52e/download/3w-operational-presence-dataset_november-2024.xlsx",
    "3w/3W_Operational_Presence_Dataset_January_-_December_2025.xlsx": f"{HDX}/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/18ddb242-5916-484c-bf77-77e022732aaa/download/3w-operational-presence-dataset_january-december-2025.xlsx",
    "3w/3W_Operational_Presence_Dataset_January_-_June_2026.xlsx": f"{HDX}/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/046df6fb-2461-4313-9937-e0228478ddbf/download/3w-operational-presence-dataset_january-june-2026_.xlsx",
    "3w/Operational_Partners_Presence_Jan-Sep_2024.xlsx": f"{HDX}/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/fa62e062-29e8-48b2-a5a3-5e7ac96af38f/download/ocha-operational-partners-presence-jan-sep-2024.xlsx",
    "3w/3ws-2023-consolidated.xlsx": f"{HDX}/be09b1a5-e457-448f-8d2d-63b0debc1742/resource/05ee0b67-40ab-4217-ae29-54d17fb230b5/download/3ws-2023-consolidated-5.xlsx",
    # WFP market prices; OCHA district boundaries
    "prices/wfp_som.csv": f"{HDX}/26727d1b-af49-4323-9215-c2ac479abb87/resource/39614bfb-0f9c-4800-8997-e68e41a38ced/download/wfp_food_prices_som.csv",
    "geo/som.geojson.zip": f"{HDX}/ec140a63-5330-4376-a3df-c7ebf73cfc3c/resource/79f7f826-6028-4650-b8f7-2d5e53032955/download/som_admin_boundaries.geojson.zip",
    # WorldPop 2020 population, 1 km, UN-adjusted
    "geo/SOM.tif": "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/SOM/som_ppp_2020_1km_Aggregated_UNadj.tif",
    # FEWS NET: Somalia's classifications (for unit names) and unit maps
    "fewsnet/ipcphase_so.csv": "https://fdw.fews.net/api/ipcphase/?format=csv&fields=simple&country_code=SO",
    "geo/SO_fsc_admin_lhz.geojson": "https://fdw.fews.net/api/feature/?format=geojson&country_code=SO&unit_type=fsc_admin_lhz",
    "geo/SO_idp_camp.geojson": "https://fdw.fews.net/api/feature/?format=geojson&country_code=SO&unit_type=idp_camp",
}


def get(url, dest):
    dest = RAW / dest
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print("downloading", dest.relative_to(RAW), flush=True)
    with requests.get(url, stream=True, timeout=900) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)


def acled():
    """ACLED political violence by district and month (HDX; the file name carries its date, so look it up)."""
    res = requests.get("https://data.humdata.org/api/3/action/package_show",
                       params={"id": "somalia-acled-conflict-data"}, timeout=120).json()["result"]["resources"]
    get(next(x["url"] for x in res if "political_violence" in x["name"].lower()), "acled/som.xlsx")


def fts(first=2005, last=2026):
    """Every FTS flow, one JSON file per year, from the public API (about 1.5 GB in all)."""
    for year in range(first, last + 1):
        dest = RAW / "fts" / f"flows_{year}.json"
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        flows, url, params = [], "https://api.hpc.tools/v1/public/fts/flow", {"year": year, "limit": 1000}
        while url:
            j = requests.get(url, params=params, timeout=300).json()
            flows += j["data"]["flows"]
            url, params = j["meta"].get("nextLink"), None
            time.sleep(0.5)
        dest.write_text(json.dumps(flows))
        print(f"FTS {year}: {len(flows)} flows", flush=True)


if __name__ == "__main__":
    for dest, url in FILES.items():
        get(url, dest)
    acled()
    fts()
