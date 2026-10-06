"""Download FEWS NET food insecurity classifications (current situation and
projections) from the FEWS NET Data Warehouse API.

The public API at https://fdw.fews.net/api/ipcphase/ returns one row per
geographic unit x report x scenario, including the near-term (ML1) and
medium-term (ML2) projections, which the fews.net bulk shapefile download
does not include.

Raw pulls are cached month by month in input/fewsnet/raw/, so the script can be
re-run and will only fetch what is missing. Output: input/fewsnet/ipcphase.parquet
"""
import io
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "input" / "fewsnet" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
URL = "https://fdw.fews.net/api/ipcphase/"


def fetch_month(start: pd.Timestamp) -> Path:
    end = start + pd.offsets.MonthEnd(0)
    out = RAW / f"ipcphase_{start:%Y_%m}.csv"
    if out.exists():
        return out
    params = {"format": "csv", "fields": "simple",
              "start_date": f"{start:%Y-%m-%d}", "end_date": f"{end:%Y-%m-%d}"}
    for attempt in range(4):
        try:
            r = requests.get(URL, params=params, timeout=300)
            r.raise_for_status()
            out.write_bytes(r.content)
            return out
        except requests.RequestException as e:
            print(f"  retry {attempt + 1} for {start:%Y-%m}: {e}")
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"failed {start:%Y-%m}")


def main():
    months = pd.date_range("2009-01-01", pd.Timestamp.today().normalize(), freq="MS")
    frames = []
    for m in months:
        path = fetch_month(m)
        df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
        print(f"{m:%Y-%m}: {len(df):>7,} rows")
        if len(df):
            frames.append(df)
        time.sleep(1)
    df = pd.concat(frames, ignore_index=True).drop_duplicates("id")
    df.to_parquet(ROOT / "input" / "fewsnet" / "ipcphase.parquet", index=False)
    print(f"total unique rows: {len(df):,}")


if __name__ == "__main__":
    main()
