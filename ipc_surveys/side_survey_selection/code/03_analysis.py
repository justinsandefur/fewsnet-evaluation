"""Regressions and figures: what predicts a household survey in a country-year?

Linear probability models, standard errors clustered by country.
  Pooled  : year FE (+ region FE), compares countries with each other
  Within  : country FE + year FE, compares a country's own good and bad years
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT_T = ROOT / "output" / "tables"; OUT_T.mkdir(parents=True, exist_ok=True)
OUT_F = ROOT / "output" / "figures"; OUT_F.mkdir(parents=True, exist_ok=True)

COL = {"s_any": "#3a3a38", "s_DHS": "#2a78d6", "s_MICS": "#eb6834", "s_LSMS": "#1baf7a"}
LAB = {"s_any": "Any of the three", "s_DHS": "DHS", "s_MICS": "MICS", "s_LSMS": "LSMS"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.dpi": 150, "savefig.bbox": "tight"})

df = pd.read_csv(ROOT / "data" / "panel.csv")
df = df.dropna(subset=["ln_gdppc", "ln_pop"]).copy()
df["ln_gdppc_sq"] = (df.ln_gdppc - df.ln_gdppc.mean()) ** 2
df["minor"] = df.conflict - df.war
df["ln_u5mr"] = np.log(df.u5mr)
df = df.sort_values(["iso3", "year"])
for v in ["war", "minor", "downturn", "conflict"]:
    df[f"L_{v}"] = df.groupby("iso3")[v].shift(1)
OUTCOMES = ["s_any", "s_DHS", "s_MICS", "s_LSMS"]


def fit(formula, data):
    d = data.dropna(subset=[c for c in data.columns if c in formula])
    m = smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d.iso3.astype("category").cat.codes})
    return m


SPECS = {
    "(1) Pooled":
        "{y} ~ ln_gdppc + ln_gdppc_sq + ln_pop + minor + war + downturn + C(year)",
    "(2) Pooled + region, need, stability":
        "{y} ~ ln_gdppc + ln_gdppc_sq + ln_pop + ln_u5mr + minor + war + downturn + wgi_stability + C(region) + C(year)",
    "(3) Within country":
        "{y} ~ ln_gdppc + ln_pop + minor + war + downturn + C(iso3) + C(year)",
    "(5) Within country, intensity":
        "{y} ~ ln_gdppc + ln_pop + ln_bd + downturn + C(iso3) + C(year)",
    "(4) Within country, lagged shocks":
        "{y} ~ ln_gdppc + ln_pop + L_minor + L_war + L_downturn + C(iso3) + C(year)",
}
KEEP = ["ln_bd", "ln_gdppc", "ln_gdppc_sq", "ln_pop", "ln_u5mr", "minor", "war", "downturn", "wgi_stability",
        "L_minor", "L_war", "L_downturn"]
NICE = {"ln_bd": "Log(1 + battle deaths per 100k)", "ln_gdppc": "Log GDP per capita", "ln_gdppc_sq": "Log GDP per capita, squared (centred)",
        "ln_pop": "Log population", "ln_u5mr": "Log under-5 mortality rate",
        "minor": "Minor conflict (25-999 battle deaths)", "war": "War (1,000+ battle deaths)",
        "downturn": "GDP per capita fell >2%", "wgi_stability": "Political stability index (WGI, sd units)",
        "L_minor": "Minor conflict, last year", "L_war": "War, last year", "L_downturn": "GDP fell >2%, last year"}

rows, models = [], {}
for y in OUTCOMES:
    for s, f in SPECS.items():
        m = fit(f.format(y=y), df)
        models[(y, s)] = m
        for v in KEEP:
            if v in m.params:
                rows.append(dict(outcome=y, spec=s, var=v, b=m.params[v], se=m.bse[v], p=m.pvalues[v],
                                 n=int(m.nobs), mean=m.model.endog.mean()))
coef = pd.DataFrame(rows)
coef.to_csv(OUT_T / "coefficients.csv", index=False)


def star(p):
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""


# Readable table: one block per outcome, columns = specs
with open(OUT_T / "regressions.md", "w") as fh:
    fh.write("Linear probability models. Outcome = 1 if survey fieldwork began in the country-year. "
             "Coefficients in percentage points; SEs clustered by country in parentheses. All columns include year fixed effects.\n\n")
    for y in OUTCOMES:
        c = coef[coef.outcome == y]
        fh.write(f"### {LAB[y]}  (mean = {100*c['mean'].iloc[0]:.1f}% of country-years)\n\n")
        fh.write("| | " + " | ".join(SPECS) + " |\n|---|" + "---|" * len(SPECS) + "\n")
        for v in KEEP:
            cells = []
            for s in SPECS:
                r = c[(c.spec == s) & (c["var"] == v)]
                cells.append("" if r.empty else f"{100*r.b.iloc[0]:.1f}{star(r.p.iloc[0])} ({100*r.se.iloc[0]:.1f})")
            if any(cells):
                fh.write(f"| {NICE[v]} | " + " | ".join(cells) + " |\n")
        fh.write("| Observations | " + " | ".join(str(int(c[c.spec == s].n.iloc[0])) for s in SPECS) + " |\n")
        fh.write("| Country FE | " + " | ".join("yes" if "Within" in s else "no" for s in SPECS) + " |\n| Region FE | " + " | ".join("yes" if "region" in s else "no" for s in SPECS) + " |\n\n")

# --- Logit check for the pooled spec -----------------------------------------
lg = smf.logit(SPECS["(2) Pooled + region, need, stability"].format(y="s_any"),
               df.dropna(subset=["wgi_stability", "ln_u5mr"])).fit(disp=0, cov_type="cluster",
               cov_kwds={"groups": df.dropna(subset=["wgi_stability", "ln_u5mr"]).iso3.astype("category").cat.codes})
ame = lg.get_margeff().summary_frame()
ame.loc[[k for k in KEEP if k in ame.index]].to_csv(OUT_T / "logit_ame_any.csv")

# --- FEWS NET subsample: food crisis severity, 2011-2023 ----------------------
fw = df[(df.fews_country == 1) & (df.year >= 2011)].copy()
fw["fews_share3"] = fw.fews_share3.fillna(0)
fews_rows = []
for y in OUTCOMES:
    for lab, f in {"Pooled": "{y} ~ fews_share3 + ln_gdppc + ln_pop + war + minor + C(year)",
                   "Within country": "{y} ~ fews_share3 + ln_gdppc + war + minor + C(iso3) + C(year)"}.items():
        m = fit(f.format(y=y), fw)
        fews_rows.append(dict(outcome=y, spec=lab, b=m.params["fews_share3"], se=m.bse["fews_share3"],
                              p=m.pvalues["fews_share3"], n=int(m.nobs), countries=fw.iso3.nunique()))
pd.DataFrame(fews_rows).to_csv(OUT_T / "fewsnet_regressions.csv", index=False)

# --- Event study: conflict onset ---------------------------------------------
# onset = first year with 25+ battle deaths after at least 3 calm years
df["calm3"] = df.groupby("iso3").conflict.transform(lambda s: s.shift(1).rolling(3).sum()) == 0
onsets = df[(df.conflict == 1) & df.calm3][["iso3", "year"]].rename(columns={"year": "onset"})
onsets = onsets.groupby("iso3").onset.min().reset_index()      # first onset per country
ev = df.merge(onsets, on="iso3", how="left")
ev["k"] = ev.year - ev.onset
# reference period = 2-5 years before onset, pooled (single years are noisy: ~55 onsets)
K = list(range(-1, 6))
for k in K:
    ev[f"e{k+1}"] = (ev.k == k).astype(int)
ev["e_pre"] = (ev.k < -5).astype(int)
ev["e_post"] = (ev.k > 5).astype(int)
ev_terms = " + ".join(f"e{k+1}" for k in K) + " + e_pre + e_post"
es = fit(f"s_any ~ {ev_terms} + ln_gdppc + ln_pop + C(iso3) + C(year)", ev)
es_df = pd.DataFrame({"k": [-3.5] + K, "b": [0] + [es.params[f"e{k+1}"] for k in K],
                      "se": [0] + [es.bse[f"e{k+1}"] for k in K]})
es_df.to_csv(OUT_T / "event_study_onset.csv", index=False)
n_onsets = len(onsets)

# ============================== FIGURES =====================================

# Fig 1: survey rate by GDP per capita decile, by program
df["gdp_bin"] = pd.qcut(df.ln_gdppc, 10, labels=False)
b = df.groupby("gdp_bin").agg(gdp=("gdppc", "median"), **{y: (y, "mean") for y in OUTCOMES})
fig, ax = plt.subplots(figsize=(7, 4.2))
for y in OUTCOMES:
    ax.plot(b.gdp, 100 * b[y], marker="o", ms=5, lw=2, color=COL[y], label=LAB[y])
ax.set_xscale("log")
ax.set_xticks([1000, 2000, 5000, 10000, 20000, 50000]); ax.set_xticklabels(["$1k", "$2k", "$5k", "$10k", "$20k", "$50k"])
ax.set_xlabel("GDP per capita (2021 PPP $), median of each tenth of country-years")
ax.set_ylabel("% of country-years with a survey starting")
ax.set_title("Surveys target poorer countries, but thin out at the very bottom", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, fontsize=9, loc="upper right")
fig.savefig(OUT_F / "fig1_survey_rate_by_gdp.png"); plt.close(fig)

# Fig 2: coefficient plot, pooled vs within-country
vars_ = ["war", "minor", "downturn"]
specs_ = ["(1) Pooled", "(2) Pooled + region, need, stability", "(3) Within country"]
fig, axes = plt.subplots(1, 3, figsize=(10, 3.8), sharey=True)
for ax, v in zip(axes, vars_):
    for j, s in enumerate(specs_):
        for i, y in enumerate(OUTCOMES):
            r = coef[(coef.outcome == y) & (coef.spec == s) & (coef["var"] == v)].iloc[0]
            yy = j * 5 + i
            ax.errorbar(100 * r.b, -yy, xerr=196 * r.se, fmt="o", color=COL[y], ms=5, lw=1.5, capsize=0,
                        label=LAB[y] if (j == 0 and v == "war") else None)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_title(NICE[v], loc="left", fontsize=10, color=INK)
    ax.set_xlabel("Change in survey probability (pp)")
axes[0].set_yticks([-(j * 5 + 1.5) for j in range(3)])
axes[0].set_yticklabels(["Pooled,\nyear FE", "Pooled + region,\nchild mortality,\nstability", "Within country\n(country + year FE)"])
fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=9, ncol=4, loc="upper right", bbox_to_anchor=(1, 1.0))
fig.suptitle("Conflict and downturns: effect on the chance a survey starts that year (95% CI)", x=0.01, ha="left",
             fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(OUT_F / "fig2_coefficients.png"); plt.close(fig)

# Fig 3: event study
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.fill_between(es_df.k, 100 * (es_df.b - 1.96 * es_df.se), 100 * (es_df.b + 1.96 * es_df.se), color=COL["s_any"], alpha=.12, lw=0)
ax.plot(es_df.k, 100 * es_df.b, marker="o", color=COL["s_any"], lw=2)
ax.axhline(0, color=INK2, lw=.8); ax.axvline(-0.5, color=INK2, lw=.8, ls=":")
ax.set_xticks([-3.5] + K); ax.set_xticklabels(["2-5 yrs\nbefore\n(reference)"] + [str(k) for k in K])
ax.set_xlabel("Years since conflict onset (first year with 25+ battle deaths after 3 calm years)")
ax.set_ylabel("Survey probability vs. 2-5 years before (pp)")
ax.set_title(f"Survey probability around the start of a conflict ({n_onsets} onsets)", loc="left", color=INK, fontsize=11)
fig.savefig(OUT_F / "fig3_event_study_onset.png"); plt.close(fig)

# Fig 4: how many countries / child deaths have no recent survey? (1995-2020; later years
# are understated because catalogs lag fieldwork by 1-3 years)
d4 = df[(df.year >= 1995) & (df.year <= 2020)].copy()
d4["stale"] = ((d4.since_any.isna()) | (d4.since_any > 5)).astype(int)
d4["grp"] = np.where(d4.conflict == 1, "In conflict that year", "Not in conflict")
cnt = d4.groupby(["year", "grp"]).stale.mean().unstack()
# death-weighted shares are dominated by India's 2005-2015 gap, so show the poorer-country subsample instead
wt = d4[d4.income.isin(["Low income", "Lower middle income"])].groupby(["year", "grp"]).stale.mean().unstack()
fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for ax, tab, ttl in [(axes[0], cnt, "All countries in sample"), (axes[1], wt, "Low and lower-middle income countries only")]:
    for g, c in zip(["In conflict that year", "Not in conflict"], ["#e34948", "#2a78d6"]):
        ax.plot(tab.index, 100 * tab[g], lw=2, color=c)
        ax.annotate(g, (tab.index[-1], 100 * tab[g].iloc[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", color=INK2, fontsize=9)
    ax.set_title(ttl, loc="left", fontsize=10, color=INK)
    ax.set_ylim(0, 100)
axes[0].set_ylabel("% of countries with no DHS/MICS/LSMS\nin the past 5 years")
fig.suptitle("No recent survey: conflict countries vs. the rest", x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(OUT_F / "fig4_stale_coverage.png"); plt.close(fig)
pd.concat({"countries": cnt, "low_lmic": wt}, axis=1).to_csv(OUT_T / "stale_coverage.csv")
sh = wt

# Fig 5: FEWS NET food crisis bins
fw["bin"] = pd.cut(fw.fews_share3, [-0.01, 0, 0.1, 0.25, 1.0], labels=["None", "Up to 10%", "10-25%", "Over 25%"])
b5 = fw.groupby("bin", observed=True).agg(rate=("s_any", "mean"), n=("s_any", "size"))
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.bar(range(len(b5)), 100 * b5.rate, color=COL["s_any"], width=0.6)
for i, (r, n) in enumerate(zip(b5.rate, b5.n)):
    ax.text(i, 100 * r + 0.6, f"{100*r:.0f}%\n(n={n})", ha="center", va="bottom", fontsize=8.5, color=INK2)
ax.set_xticks(range(len(b5))); ax.set_xticklabels(b5.index)
ax.set_xlabel("Share of FEWS NET mapped areas in Crisis or worse (IPC 3+) that year")
ax.set_ylabel("% of country-years with a survey")
ax.set_ylim(0, 100 * b5.rate.max() * 1.35)
ax.set_title(f"FEWS NET countries, 2011-2023 ({fw.iso3.nunique()} countries)", loc="left", color=INK, fontsize=11)
fig.savefig(OUT_F / "fig5_fewsnet_bins.png"); plt.close(fig)

# --- Printed summary ---------------------------------------------------------
pd.set_option("display.width", 200)
print(coef[coef["var"].isin(["ln_bd", "ln_gdppc", "war", "minor", "downturn", "wgi_stability", "ln_u5mr", "L_war", "L_downturn"])]
      .assign(b=lambda d: (100 * d.b).round(1), se=lambda d: (100 * d.se).round(1), p=lambda d: d.p.round(3))
      [["outcome", "spec", "var", "b", "se", "p", "n"]].to_string(index=False))
print("\nLogit AME (any survey):\n", ame.loc[[k for k in KEEP if k in ame.index]].round(3))
print("\nFEWS NET:\n", pd.DataFrame(fews_rows).round(3).to_string(index=False))
print("\nEvent study:\n", es_df.round(3).to_string(index=False))
print("\nStale (countries):\n", cnt.loc[[2000, 2010, 2020]].round(3)); print("Stale (low/LMIC):\n", wt.loc[[2000, 2010, 2020]].round(3))
print("\nFEWS bins:\n", b5)
