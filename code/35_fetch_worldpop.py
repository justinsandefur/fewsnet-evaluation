"""WorldPop 2020 population (UN-adjusted, 1 km, unconstrained) for every FEWS NET country.
Output: input/worldpop/<ISO3>.tif"""
import json, time
from pathlib import Path
import pandas as pd, requests
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "worldpop"
codes = pd.DataFrame(json.loads((ROOT / "input" / "fewsnet" / "countries.json").read_text()))
cs = pd.read_parquet(ROOT / "input" / "fewsnet" / "cs_monthly.parquet", columns=["country_code"])
isos = sorted(codes.set_index("iso3166a2").loc[cs.country_code.unique(), "iso3166a3"])
for iso in isos:
    dest = OUT / f"{iso}.tif"
    if dest.exists() and dest.stat().st_size > 10000:
        print(iso, "cached"); continue
    try:
        d = requests.get("https://hub.worldpop.org/rest/data/pop/wpicuadj1km", params={"iso3": iso}, timeout=120).json()["data"]
        rec = [r for r in d if r.get("popyear") == "2020"]
        url = [f for f in rec[0]["files"] if f.lower().endswith(".tif")][0]
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(dest, "wb") as fh:
                for c in r.iter_content(1 << 20): fh.write(c)
        print(iso, round(dest.stat().st_size / 1e6, 1), "MB", flush=True)
    except Exception as e:
        print(iso, "failed", e, flush=True)
    time.sleep(0.5)
