"""Humanitarian funding by global cluster (destination), OCHA Financial Tracking Service, 2015-2024.
Writes shares of all reported funding (including untagged) as LaTeX macros to
output/cgd_paper/numbers_fts.tex and the table to output/tables/fts_cluster_shares.csv (and amounts to fts_cluster_funding.csv)."""
import json, subprocess
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
rows = []
for yr in range(2015, 2025):
    out = subprocess.run(["curl", "-sf", "--max-time", "120",
                          f"https://api.hpc.tools/v1/public/fts/flow?year={yr}&groupby=globalcluster"],
                         capture_output=True, check=True).stdout
    objs = json.loads(out)["data"]["report3"]["fundingTotals"]["objects"][0]["objectsBreakdown"]
    for o in objs:
        rows.append(dict(year=yr, cluster=o["name"], funding=o["totalFunding"]))
d = pd.DataFrame(rows)
tot = d.groupby("year").funding.sum()
share = d.pivot_table(index="year", columns="cluster", values="funding", aggfunc="sum").fillna(0).div(tot, axis=0)
share.to_csv(ROOT / "output" / "tables" / "fts_cluster_shares.csv")
d.to_csv(ROOT / "output" / "tables" / "fts_cluster_funding.csv", index=False)     # amounts, for the Stata port
pooled = d.groupby("cluster").funding.sum() / d.funding.sum()
tagged = d[~d.cluster.isin(["Not specified", "Multi-sector", "Other"])]
pooled_tagged = tagged.groupby("cluster").funding.sum() / tagged.funding.sum()
m = {"ftsYearZero": "2015", "ftsYearOne": "2024",
     "ftsFood": f"{100 * pooled['Food Security']:.0f}", "ftsHealth": f"{100 * pooled['Health']:.0f}",
     "ftsWash": f"{100 * pooled['Water Sanitation Hygiene']:.0f}", "ftsNutrition": f"{100 * pooled['Nutrition']:.0f}",
     "ftsFoodTag": f"{100 * pooled_tagged['Food Security']:.0f}", "ftsHealthTag": f"{100 * pooled_tagged['Health']:.0f}",
     "ftsWashTag": f"{100 * pooled_tagged['Water Sanitation Hygiene']:.0f}",
     "ftsNutritionTag": f"{100 * pooled_tagged['Nutrition']:.0f}",
     "ftsUntagged": f"{100 * pooled[['Not specified', 'Multi-sector']].sum():.0f}"}
lines = ["% Written by code/85_fts_cluster_shares.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
(ROOT / "output" / "cgd_paper" / "numbers_fts.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
print(share[["Food Security", "Health", "Water Sanitation Hygiene", "Nutrition", "Not specified"]].round(3))
