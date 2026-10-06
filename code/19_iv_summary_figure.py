"""Summary chart: first-stage strength of every instrument tested for
humanitarian aid to FEWS NET countries (15_instrument.py, 16_crowdout_diagnostics.py,
17_iv_alternatives.py). Output: output/figures/iv_first_stage_summary.pdf"""
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB, FIG = ROOT / "output" / "tables", ROOT / "output" / "figures"
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 11, "axes.titleweight": "bold",
                     "axes.titlelocation": "left"})
fs = pd.read_csv(TAB / "iv_first_stage.csv")
alt = pd.read_csv(TAB / "iv_alternatives.csv")
fx = pd.read_csv(TAB / "iv_fx.csv")
cq = pd.read_csv(TAB / "iv_country_quarterly.csv")
us = pd.read_csv(TAB / "iv_us_cut.csv")
g = lambda d, q: d.query(q).iloc[0]
rows = [
    ("Competing natural disasters (funding-based), monthly", g(fs, "spec=='FEWS NET countries' and instrument=='z_fund'"), "expected"),
    ("Competing natural disasters (EM-DAT deaths), monthly", g(fs, "spec=='FEWS NET countries' and instrument=='z_dis'"), "expected"),
    ("Competing disasters incl. war onsets, monthly", g(fs, "spec=='FEWS NET countries' and instrument=='z_fund_war'"), "expected"),
    ("Competing disasters, within-year shifts, lags 1-2 qtrs", cq.query("spec=='within-year shifts, lags 1-2'").iloc[0].rename({"joint_F_excluded_lags": "F"}), "expected"),
    ("Donor exchange rates", g(fx, "lag_quarters==0"), "expected"),
    ("Donor budgets elsewhere (leave-out), all sectors", g(alt, "instrument.str.startswith('A.') and outcome=='all sectors' and sample=='2011-2024'", ), "reallocation"),
    ("Donor budgets elsewhere (leave-out), food & nutrition", g(alt, "instrument.str.startswith('A.') and outcome=='food and nutrition' and sample=='2011-2024'"), "reallocation"),
    ("US fiscal-year timing x US share", g(alt, "instrument.str.startswith('B.')"), "unexpected"),
    ("UN Security Council seat", g(alt, "instrument.str.startswith('C.')"), "unexpected"),
    ("Oil price x Gulf donor share", g(alt, "instrument.str.startswith('E.') and outcome=='all donors'"), "unexpected"),
    ("2025 US cut x US share (36 FEWS NET countries)", g(us, "sample=='FEWS NET countries' and outcome=='all donors'"), "expected"),
    ("2025 US cut x US share (58 recipients)", g(us, "sample=='All recipients' and outcome=='all donors'"), "expected"),
]
d = pd.DataFrame([{"label": l, "F": float(r["F"]), "sign": s} for l, r, s in rows])
d.to_csv(TAB / "iv_first_stage_summary.csv", index=False)
col = {"expected": "#1f4e79", "reallocation": "#2a9d8f", "unexpected": "#c55a11"}
fig, ax = plt.subplots(figsize=(10, 6))
y = range(len(d))[::-1]
ax.barh(list(y), d.F, color=[col[s] for s in d.sign])
for yi, F in zip(y, d.F):
    ax.text(F + 0.2, yi, f"{F:.1f}", va="center", fontsize=8.5)
ax.axvline(10, color="black", lw=1, ls="--")
ax.text(10.2, len(d) - 0.6, "conventional\nthreshold for a\nusable instrument\n(F = 10)", fontsize=8.5, va="top")
ax.set_yticks(list(y))
ax.set_yticklabels(d.label, fontsize=9)
ax.set_xlabel("First-stage F-statistic (strength of the instrument's effect on humanitarian aid)")
ax.set_title("Which instruments move humanitarian aid to famine-prone countries?")
ax.set_xlim(0, 15)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=col["expected"], label="Sign as expected"),
                   Patch(color=col["reallocation"], label="Negative: aid reallocated to crises elsewhere"),
                   Patch(color=col["unexpected"], label="Sign opposite to the literature")],
          frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.45), fontsize=8.5)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.text(0.01, 0.01, textwrap.fill(
    "Dependent variable: log humanitarian commitments to the country (UN Financial Tracking Service), 2011-2024, "
    "44 FEWS NET countries unless stated; country and time fixed effects; standard errors clustered by country. The 2025 "
    "US cut is a single cross-section: change in aid 2024-2025 on the 2021-2023 US share. Scripts 15-17.", 170),
    fontsize=8, color="#555")
fig.savefig(FIG / "iv_first_stage_summary.pdf")
print(d.round(2).to_string())
