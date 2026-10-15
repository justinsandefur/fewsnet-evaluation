"""Illustrative maps: what the raw signals, FEWS NET's forecast and FEWS NET's later
classification (with its aid flag) look like for two food crises.

  Somalia: failed October-December 2016 rains, conflict; forecast issued February 2017
           for the following months; classification June 2017.
  Ethiopia: El Nino drought; forecast issued October 2015; classification February 2016.

Outputs: output/cgd_paper/figures/fig_case_somalia.pdf, fig_case_ethiopia.pdf
"""
import importlib.util
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap, TwoSlopeNorm
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "input"
FIG = ROOT / "output" / "cgd_paper" / "figures"
spec = importlib.util.spec_from_file_location("fv", ROOT / "code" / "32_forecast_value.py")
FV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(FV)
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10.5})
IPC_COLORS = ["#cdfacd", "#fae61e", "#e67800", "#c80000", "#640000"]
IPC_NAMES = ["1 Minimal", "2 Stressed", "3 Crisis", "4 Emergency", "5 Famine"]
CMAP = ListedColormap(IPC_COLORS)
NORM = BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5, 5.5], 5)

CASES = [
    {"name": "somalia", "cc": "SO", "r": "2017-02", "title": "Somalia, 2016-17",
     "second": ("ln_ev6", "B. Political violence\n(log events)", "Reds")},
    {"name": "ethiopia", "cc": "ET", "r": "2015-10", "title": "Ethiopia, 2015-16",
     "second": ("phase", "B. Classification\nwhen forecast, Oct 2015", "ipc")},
]


def month_name(p):
    return pd.Period(p, "M").strftime("%b %Y")


def draw(case):
    p = pd.read_parquet(INP / "panel" / "forecast_value_panel.parquet")
    d = p[(p.country_code == case["cc"]) & (p.r.astype(str) == case["r"])].copy()
    units = FV.unit_geoms(d.fnid.unique())
    g = units.merge(d, on="fnid")
    tgt = g.target.mode().iloc[0]
    fig, ax = plt.subplots(1, 4, figsize=(12, 4.0))
    # A. rainfall
    a = ax[0]
    g.plot(column="rain_z6", ax=a, cmap="BrBG", norm=TwoSlopeNorm(0, -2.5, 2.5), edgecolor="white", linewidth=0.1,
           legend=True, legend_kwds={"shrink": 0.6, "orientation": "horizontal", "pad": 0.02})
    a.set_title("A. Rainfall anomaly\n(std. dev. from normal)", fontsize=10, loc="left")
    # B. conflict or prices
    col, title, cm = case["second"]
    a = ax[1]
    if cm == "ipc":
        g.plot(column=col, ax=a, cmap=CMAP, norm=NORM, edgecolor="white", linewidth=0.1)
        fl0 = g[g.flag == 1]
        if len(fl0):
            fl0.plot(ax=a, facecolor="none", edgecolor="black", hatch="////", linewidth=0.3)
    elif g[col].notna().any():
        vmin, vmax = (0, max(g[col].quantile(0.98), 1)) if col == "ln_ev6" else (-0.6, 0.6)
        g.plot(column=col, ax=a, cmap=cm, vmin=vmin, vmax=vmax, edgecolor="white", linewidth=0.1, legend=True,
               missing_kwds={"color": "#eeeeee"}, legend_kwds={"shrink": 0.6, "orientation": "horizontal", "pad": 0.02})
    a.set_title(title, fontsize=10, loc="left")
    # C. forecast
    a = ax[2]
    g.plot(column="fc_phase", ax=a, cmap=CMAP, norm=NORM, edgecolor="white", linewidth=0.1)
    a.set_title(f"C. Forecast for {month_name(tgt)}\n(issued {month_name(case['r'])})", fontsize=10, loc="left")
    # D. later classification with aid flag
    a = ax[3]
    g.plot(column="next_phase", ax=a, cmap=CMAP, norm=NORM, edgecolor="white", linewidth=0.1)
    fl = g[g.next_flag == 1]
    if len(fl):
        fl.plot(ax=a, facecolor="none", edgecolor="black", hatch="////", linewidth=0.3)
    a.set_title(f"D. Classification,\n{month_name(tgt)}", fontsize=10, loc="left")
    for a in ax:
        a.set_axis_off()
    handles = [Patch(color=c, label=n) for c, n in zip(IPC_COLORS, IPC_NAMES)] + \
              [Patch(facecolor="white", edgecolor="black", hatch="////", label="Held back by aid (!)")]
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, fontsize=10, bbox_to_anchor=(0.5, -0.03))
    fig.suptitle(case["title"], x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(FIG / f"fig_case_{case['name']}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"fig_case_{case['name']}.png", dpi=220, bbox_inches="tight")
    s = {"areas": len(g), "fc4": int((g.fc_phase >= 4).sum()), "cur4": int((g.phase >= 4).sum()),
         "next4": int((g.next_phase >= 4).sum()), "next3": int((g.next_phase >= 3).sum()), "flags": int(g.next_flag.sum()),
         "flag_share": float(g.next_flag.mean()), "rain_z6": float(g.rain_z6.mean()), "target": str(tgt),
         "fc3": int((g.fc_phase >= 3).sum()), "cur3": int((g.phase >= 3).sum())}
    print(case["name"], s)
    return s


if __name__ == "__main__":
    import json
    out = {c["name"]: draw(c) for c in CASES}
    (ROOT / "output" / "tables" / "case_maps.json").write_text(json.dumps(out, indent=1))
