"""FAO DIEM household surveys against food insecurity phases: the numbers quoted in the paper.

FAO's Data in Emergencies monitoring surveys (2023-2026; input/fao_diem/, matched to FEWS NET's map and to
the official IPC/CH phase by 66_foodsec_surveys.py) give four household indicators the IPC reference table
uses: poor or borderline food consumption, rCSI 19+, moderate or severe hunger (household hunger score 2+,
IPC HHS Phase 3+), and crisis or emergency livelihood coping. For each indicator and each phase measure:
means by phase (rounded, 1-4+), correlations pooled, within country and within area over time, and the
IPC 20 percent rule (share of areas classified Phase 1-2 where 20 percent or more of households are at
Crisis level or worse; share of Phase 3+ areas below 20 percent).

Output: output/cgd_paper/numbers_diem.tex
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
m = pd.read_parquet(ROOT / "input" / "foodsec_surveys" / "matched.parquet")
m = m[m.source == "fao_diem"]
IND = {"fcs_poor_borderline": "Fcs", "rcsi_19plus": "Rcsi", "hhs_3plus": "Hhs", "lcs_crisis_plus": "Lcs"}
PH = {"fews_cs": "", "ipc_phase": "Ipc"}


def f2(x):
    return f"{x:.2f}".replace("-", "\\textminus{}")


M = {"dmAreas": f"{m.area_id.nunique():,}", "dmCountries": f"{m.iso3.nunique()}",
     "dmRounds": f"{m[['area_id', 'month']].drop_duplicates().shape[0]:,}",
     "dmYearZero": f"{m.year.min()}", "dmYearOne": f"{m.year.max()}"}
for ind, I in IND.items():
    for col, P in PH.items():
        x = m[m.indicator == ind].dropna(subset=["value", col])
        ph = np.floor(x[col] + 0.5).clip(1, 4) if col == "ipc_phase" else x[col].round().clip(1, 4)
        for p, tag in [(1, "One"), (2, "Two"), (3, "Three"), (4, "Four")]:
            M[f"dm{I}{P}{tag}"] = f"{x.value[ph == p].mean():.0f}"
        M[f"dm{I}{P}N"] = f"{len(x):,}"
        M[f"dm{I}{P}Corr"] = f2(x.value.corr(x[col]))
        for g, G in [("iso3", "Cty"), ("area_id", "Area")]:
            v = x.value - x.groupby(g).value.transform("mean")
            q = x[col] - x.groupby(g)[col].transform("mean")
            M[f"dm{I}{P}Corr{G}"] = f2(v.corr(q))
        M[f"dm{I}{P}LowOver"] = f"{100 * (x.value[ph <= 2] >= 20).mean():.0f}"
        M[f"dm{I}{P}HighUnder"] = f"{100 * (x.value[ph >= 3] < 20).mean():.0f}"
lines = ["% Written by code/92_diem_numbers.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()]
(ROOT / "output" / "cgd_paper" / "numbers_diem.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
