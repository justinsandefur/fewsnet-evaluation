"""Download WFP's subnational rainfall series (CHIRPS aggregated to admin 1 and
admin 2 units, dekadal, 1981 on, with long-run averages) from the Humanitarian
Data Exchange, for every country in the Cadre Harmonise / IPC outcome panel.

Usage: python 21_fetch_rainfall.py ISO3 [ISO3 ...]   (one process per country
so several can run in parallel). Output: input/rainfall/<iso3>.csv
"""
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "rainfall"
OUT.mkdir(parents=True, exist_ok=True)
CKAN = "https://data.humdata.org/api/3/action/package_show"


def fetch(iso):
    dest = OUT / f"{iso.lower()}.csv"
    if dest.exists() and dest.stat().st_size > 10000:
        return "cached"
    try:
        res = requests.get(CKAN, params={"id": f"{iso.lower()}-rainfall-subnational"}, timeout=120).json()
    except Exception as e:
        return f"metadata error {e}"
    if not res.get("success"):
        return "no dataset"
    full = [r for r in res["result"]["resources"] if r["name"].endswith("-full.csv")]
    if not full:
        return "no full file"
    for attempt in range(3):
        try:
            with requests.get(full[0]["url"], stream=True, timeout=1800) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
                tmp.rename(dest)
            return f"{dest.stat().st_size / 1e6:.0f} MB"
        except Exception as e:
            time.sleep(30)
    return "download failed"


if __name__ == "__main__":
    for iso in sys.argv[1:]:
        print(iso, fetch(iso), flush=True)
