"""Download IPC and Cadre Harmonisé classifications from the Humanitarian Data
Exchange (HDX). These are the multi-agency analyses (not FEWS NET's own
classifications), used as a partly independent comparison and to measure
coverage beyond FEWS NET countries.

Outputs in input/ipc/ .
"""
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "ipc"
OUT.mkdir(parents=True, exist_ok=True)
CKAN = "https://data.humdata.org/api/3/action/package_show"

WANTED = {
    "global-acute-food-insecurity-country-data": [
        "ipc_global_area_long.csv", "ipc_global_national_long.csv"],
    "ipc-country-data": ["all countries"],  # older consolidated file, 2017 onward
    "cadre-harmonise": ["cadre_harmonise_caf_ipc"],
    "fsin-grfc": ["grfc_afi_database"],  # Global Report on Food Crises, 2016 onward
}


def main():
    for pkg, prefixes in WANTED.items():
        res = requests.get(CKAN, params={"id": pkg}, timeout=60).json()["result"]["resources"]
        for r in res:
            if any(r["name"].lower().startswith(p) for p in prefixes):
                dest = OUT / r["name"].lower().replace(" ", "_")
                if not dest.exists():
                    print("downloading", r["name"])
                    dest.write_bytes(requests.get(r["url"], timeout=600).content)
                print(dest.name, f"{dest.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
