"""Summarise the hand-coded (LLM-assisted) exclusion data from DHS/MICS report appendices.

Input : data/exclusion_coding/coded_*.csv (one row per report; codebook in references/)
Output: output/tables/exclusions_*.csv|md, output/figures/fig6_*.png, fig7_*.png
"""
from pathlib import Path
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT_T, OUT_F = ROOT / "output" / "tables", ROOT / "output" / "figures"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.dpi": 150, "savefig.bbox": "tight"})

c = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "data" / "exclusion_coding" / "coded_*.csv")))])
c = c.drop_duplicates("id", keep="last").set_index("id")
# manual corrections after spot-checking the agent coding against report text
for _, r in pd.read_csv(ROOT / "data" / "exclusion_coding" / "corrections.csv").iterrows():
    c.loc[r.id, r.field] = r.value
c = c.reset_index()
s = pd.read_csv(ROOT / "data" / "report_sample.csv")
panel = pd.read_csv(ROOT / "data" / "panel.csv")[["iso3", "year", "pop"]]
d = s.merge(c, on="id", how="inner").merge(panel, on=["iso3", "year"], how="left")
d["bd3_per100k"] = d.bd3 / (3 * d["pop"]) * 1e5        # avg annual battle deaths per 100k, t-2..t
d["intensity"] = pd.cut(d.bd3 / 3, [-1, 24, 999, np.inf],
                        labels=["No conflict", "Minor (25-999/yr)", "War (1,000+/yr)"])

no_reason = d.excl_other.fillna("").str.contains("reason not stated", case=False)
drops = pd.to_numeric(d.clusters_dropped_fieldwork, errors="coerce")
sel = pd.to_numeric(d.clusters_selected, errors="coerce")
d["sec_drops"] = np.where(no_reason, 0, drops.fillna(0))
d["sec_drop_share"] = d.sec_drops / sel
d["ex_ante"] = (d.excl_insecure_ex_ante == "yes").astype(int)
d["any_security_excl"] = ((d.ex_ante == 1) | (d.sec_drops > 0)).astype(int)
d["camps_out"] = (d.frame_excl_camps == "yes").astype(int)
d["camps_in"] = (d.camps_included == "yes").astype(int)
d["camps_silent"] = ((d.frame_excl_camps != "yes") & (d.camps_included != "yes")).astype(int)
d["usable"] = d.confidence.isin(["high", "medium"])
d.to_csv(OUT_T / "exclusions_coded_merged.csv", index=False)

u = d[d.usable]
tab = u.groupby("intensity", observed=True).agg(
    reports=("id", "size"),
    any_security_exclusion=("any_security_excl", "mean"),
    areas_excluded_by_design=("ex_ante", "mean"),
    clusters_lost_to_insecurity=("sec_drops", lambda x: (x > 0).mean()),
    camps_excluded=("camps_out", "mean"), camps_included=("camps_in", "mean"),
    camps_not_mentioned=("camps_silent", "mean"))
tab.loc["All"] = [len(u)] + [u[k].mean() for k in ["any_security_excl", "ex_ante"]] + \
    [(u.sec_drops > 0).mean()] + [u[k].mean() for k in ["camps_out", "camps_in", "camps_silent"]]
tab.to_csv(OUT_T / "exclusions_by_intensity.csv")
by_prog = u.groupby("program").agg(reports=("id", "size"), any_security_exclusion=("any_security_excl", "mean"),
                                   camps_mentioned=("camps_silent", lambda x: 1 - x.mean()))
by_prog.to_csv(OUT_T / "exclusions_by_program.csv")

worst = d[(d.any_security_excl == 1) | (d.camps_out == 1) | (d.camps_in == 1)].copy()
worst = worst.sort_values(["ex_ante", "sec_drop_share"], ascending=False)
worst[["id", "name", "program", "year", "excl_insecure_areas", "excl_pop_share", "sec_drops",
       "clusters_selected", "frame_excl_camps", "camps_included", "quote"]].to_csv(OUT_T / "exclusions_cases.csv", index=False)

# --- Figure 6: share of rows with any documented security exclusion, by intensity
fig, ax = plt.subplots(figsize=(6.5, 3.6))
t = tab.drop("All")
x = np.arange(len(t))
ax.bar(x - 0.2, 100 * t.any_security_exclusion, 0.38, color="#e34948", label="Some area or cluster dropped (insecurity or access)")
ax.bar(x + 0.2, 100 * (1 - t.camps_not_mentioned), 0.38, color="#2a78d6", label="Report mentions camps at all")
for i, n in enumerate(t.reports):
    ax.text(i, -9, f"n={int(n)}", ha="center", color=INK2, fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(t.index); ax.set_ylim(-12, 100)
ax.set_ylabel("% of survey reports")
ax.set_xlabel("Battle deaths in the country, fieldwork year and two years before")
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
fig.savefig(OUT_F / "fig6_exclusions_by_intensity.png")
fig.savefig(ROOT.parent / "output" / "cgd_paper" / "figures" / "fig12_survey_exclusions.pdf"); plt.close(fig)

# --- Figure 7: cluster loss share vs conflict intensity, labelled
p = d[d.usable & sel.notna()].copy()
p["y"] = 100 * p.sec_drop_share.fillna(0)
p["x"] = np.log10(1 + p.bd3_per100k)
fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(p.x, p.y, s=28, color=np.where(p.ex_ante == 1, "#e34948", "#2a78d6"),
           edgecolor="white", linewidth=0.8, zorder=3)
lab = p[(p.y >= 8) | (p.bd3_per100k >= 10)].sort_values("x")
for j, (_, r) in enumerate(lab.iterrows()):
    ax.annotate(f"{r['name'].split(',')[0]} {r.year}", (r.x, r.y), xytext=(4, 4 if j % 2 else -10), textcoords="offset points",
                fontsize=7.5, color=INK2)
ax.set_xticks(np.log10(1 + np.array([0, 1, 10, 100])))
ax.set_xticklabels(["0", "1", "10", "100"])
ax.set_xlabel("Battle deaths per 100k people per year (fieldwork year and two before)")
ax.set_ylabel("% of selected clusters not surveyed\nfor security or access reasons")
ax.scatter([], [], color="#e34948", label="Also excluded whole areas by design")
ax.scatter([], [], color="#2a78d6", label="No design-stage exclusion reported")
ax.legend(frameon=False, fontsize=8.5, loc="upper right")
ax.set_title("Clusters lost in the field, by conflict intensity", loc="left", color=INK, fontsize=11)
fig.savefig(OUT_F / "fig7_cluster_loss_vs_intensity.png"); plt.close(fig)

pd.set_option("display.width", 200)
print(tab.round(2)); print(by_prog.round(2))
print("usable", len(u), "of", len(d))
print(worst[["id", "excl_insecure_areas", "excl_pop_share", "sec_drops", "clusters_selected"]].head(25).to_string())
