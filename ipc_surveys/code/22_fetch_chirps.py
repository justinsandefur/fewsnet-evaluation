"""Monthly CHIRPS rainfall, 1981 on, read remotely from the cloud-optimized
GeoTIFFs at 0.2 degree resolution (every 4th pixel of the 0.05 degree grid)
for two windows: Africa / Middle East / South Asia, and Central America /
Caribbean / northern South America. Ocean pixels (negative values) are set
to missing. Each month is cached as a .npy array.

Usage: python 22_fetch_chirps.py YYYY [YYYY ...]
Outputs: input/chirps/<box>_<YYYY>_<MM>.npy, input/chirps/<box>_meta.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "chirps"
OUT.mkdir(parents=True, exist_ok=True)
URL = "/vsicurl/https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/cogs/chirps-v2.0.{y}.{m:02d}.cog"
BOXES = {"afr": (-20.0, -36.0, 78.0, 40.0), "lac": (-95.0, -6.0, -60.0, 25.0)}
F = 4  # 0.05 x 4 = 0.2 degrees


def fetch(y, m):
    for box, (w, s, e, n) in BOXES.items():
        out = OUT / f"{box}_{y}_{m:02d}.npy"
        if out.exists():
            continue
        try:
            with rasterio.open(URL.format(y=y, m=m)) as src:
                win = from_bounds(w, s, e, n, src.transform)
                shape = (int(round(win.height / F)), int(round(win.width / F)))
                a = src.read(1, window=win, out_shape=shape, resampling=Resampling.nearest).astype("float32")
                meta = OUT / f"{box}_meta.json"
                if not meta.exists():
                    t = src.window_transform(win) * rasterio.Affine.scale(win.width / shape[1], win.height / shape[0])
                    meta.write_text(json.dumps({"transform": list(t)[:6], "shape": shape}))
        except Exception as ex:
            print(y, m, box, "failed", ex, flush=True)
            continue
        a[a < 0] = np.nan
        np.save(out, a)
    print(y, m, flush=True)


if __name__ == "__main__":
    for y in sys.argv[1:]:
        for m in range(1, 13):
            fetch(int(y), m)
