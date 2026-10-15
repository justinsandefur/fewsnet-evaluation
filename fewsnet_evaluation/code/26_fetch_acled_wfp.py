"""Download sub-national conflict and food price data for every country in the
outcome panel, from the Humanitarian Data Exchange.

  ACLED: political violence events and fatalities by admin-2 district and
         month (ACLED's public sub-national aggregates; non-commercial use
         with attribution, see the TOU sheet in each file).
  WFP:   market food prices (market, coordinates, commodity, price type,
         currency, local and USD price, date).

Outputs: input/acled/hdx/<iso3>.xlsx, input/prices/<iso3>.csv
"""
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "input"
(INP / "acled" / "hdx").mkdir(parents=True, exist_ok=True)
(INP / "prices").mkdir(parents=True, exist_ok=True)
API = "https://data.humdata.org/api/3/action"


def find_package(iso, q, test):
    r = requests.get(f"{API}/package_search", params={"q": q, "fq": f"groups:{iso.lower()}", "rows": 50,
                                                      "fl": "name"}, timeout=120).json()["result"]["results"]
    hits = [p["name"] for p in r if test(p["name"])]
    return hits[0] if hits else None


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return "cached"
    with requests.get(url, stream=True, timeout=900) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for c in r.iter_content(1 << 20):
                fh.write(c)
    return f"{dest.stat().st_size / 1e6:.1f} MB"


def main():
    isos = sorted(pd.read_parquet(INP / "panel" / "outcomes.parquet").iso3.unique())
    for iso in isos:
        for kind, q, test, pick, dest in [
            ("ACLED", "acled conflict data", lambda n: n.endswith("-acled-conflict-data"),
             lambda x: "political_violence" in x["name"].lower(), INP / "acled" / "hdx" / f"{iso.lower()}.xlsx"),
            ("WFP", "wfp food prices", lambda n: n.startswith("wfp-food-prices-for-"),
             lambda x: "wfp_food_prices_" in x["url"].lower() and x["url"].lower().endswith(".csv"),
             INP / "prices" / f"{iso.lower()}.csv")]:
            try:
                name = find_package(iso, q, test)
                if not name:
                    print(kind, iso, "no package", flush=True)
                    continue
                res = requests.get(f"{API}/package_show", params={"id": name}, timeout=120).json()["result"]["resources"]
                r = [x for x in res if pick(x)]
                print(kind, iso, download(r[0]["url"], dest) if r else "no resource", flush=True)
            except Exception as e:
                print(kind, iso, "failed", e, flush=True)
            time.sleep(0.3)


if __name__ == "__main__":
    main()
