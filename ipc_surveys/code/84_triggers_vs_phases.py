"""Do exogenous triggers (drought, conflict, prices) predict malnutrition and death in surveys
better than food insecurity phases do? Somalia, FSNAU survey domains (rural, IDP, urban), 2015-2026.

Unit: survey domain x season (input/panel/som_need_panel.parquet, built by 69/70).
Outcomes: GAM, SAM, crude death rate (CDR), under-five death rate (U5DR).
Information sets, all observable at the time of the survey:
  base      population type (rural / IDP / urban) and season (Gu / Deyr)
  phase     official IPC share of the population in Phase 3+ for the domain's districts;
            FEWS NET current-situation phase (mean over the domain's units) and its medium-term
            forecast for the survey month (latest report 3-8 months earlier)
  triggers  CHIRPS rainfall anomaly over 6 and 12 months, log ACLED conflict fatalities over
            6 months, log cereal and goat prices (3 months, relative to market means)
  last      the domain's own outcome in its previous survey, plus previous morbidity and
            measles vaccination coverage
Scored out of sample, leaving one season out at a time (R-squared), and leaving one survey domain
out (a place never surveyed; R-squared relative to the season mean). Also: within-domain
regressions (domain effects, season type and a linear trend) of each outcome on standardised triggers and the IPC
share together, and of the IPC share on the triggers (does the phase respond to them?).

Outputs: output/tables/triggers_*.csv, output/cgd_paper/numbers_triggers.tex,
         output/cgd_paper/figures/fig13_triggers_r2.pdf
"""
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
PAPER = ROOT / "output" / "cgd_paper"
OUTCOMES = ["gam", "sam", "cdr", "u5dr"]
TRIG = ["rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat"]

# ------------------------------------------------------------------ panel
p = pd.read_parquet(INP / "panel" / "som_need_panel.parquet")
p["t"] = pd.PeriodIndex(p.month.astype(str), freq="M")
p["deyr"] = p.season_type.astype(str).str.lower().str.startswith("d").astype(int)

cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
cs = cs[cs.country_code == "SO"].copy()
cs["t"] = pd.PeriodIndex(cs.month.astype(str), freq="M")
cs = cs.set_index(["fnid", "t"]).phase.sort_index()
pr = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
pr = pr[(pr.country_code == "SO") & pr.lead.between(3, 8)].copy()
pr["t"] = pd.PeriodIndex(pr.month.astype(str), freq="M")
pr = pr.sort_values("report_month").groupby(["fnid", "t"]).phase.last()


def mean_phase(series, fnids, t, back=0):
    vals = []
    for f in fnids:
        for k in range(back + 1):
            key = (f, t - k)
            if key in series.index:
                vals.append(series.loc[key])
                break
    return np.mean(vals) if vals else np.nan


fn = p.fnids.str.split(";")
p["fews_cs"] = [mean_phase(cs, f, t, back=4) for f, t in zip(fn, p.t)]
p["fews_fc"] = [mean_phase(pr, f, t) for f, t in zip(fn, p.t)]

p = p.sort_values(["domain", "t"])
for v in OUTCOMES + ["morbidity", "measles"]:
    p[f"L_{v}"] = p.groupby("domain")[v].shift(1)
p["season_rank"] = p.groupby("t").ngroup()

SETS = {
    "Base (population type, season)": [],
    "Phases (IPC share 3+, FEWS NET map and forecast)": ["need_p3", "fews_cs", "fews_fc"],
    "Triggers (rain, conflict, prices)": TRIG,
    "Phases + triggers": ["need_p3", "fews_cs", "fews_fc"] + TRIG,
    "Previous survey": ["L_{y}", "L_morbidity", "L_measles"],
    "Previous survey + triggers": ["L_{y}", "L_morbidity", "L_measles"] + TRIG,
}
BASE = ["C(ptype)", "deyr"]


def oos_r2(d, y, xs):
    """Leave-one-season-out R-squared."""
    f = f"{y} ~ " + " + ".join(BASE + xs)
    pred = pd.Series(np.nan, index=d.index)
    for s in d.season_rank.unique():
        tr, te = d[d.season_rank != s], d[d.season_rank == s]
        m = smf.ols(f, tr).fit()
        pred.loc[te.index] = m.predict(te)
    return 1 - ((d[y] - pred) ** 2).sum() / ((d[y] - d[y].mean()) ** 2).sum()


rows = []
for y in OUTCOMES:
    need = [y, "need_p3", "fews_cs", "fews_fc", f"L_{y}", "L_morbidity", "L_measles"] + TRIG
    d = p.dropna(subset=need).copy()          # common sample for every information set
    for lab, xs in SETS.items():
        xs = [x.format(y=y) for x in xs]
        rows.append(dict(outcome=y, info=lab, r2=oos_r2(d, y, xs), n=len(d), seasons=d.season_rank.nunique()))
r2 = pd.DataFrame(rows)
r2.to_csv(TAB / "triggers_oos_r2.csv", index=False)


def lodo_r2(d, y, xs):
    """Leave one domain out, with season effects: how well does each information set predict a place
    that has never been surveyed, beyond the season's average? R-squared relative to the season mean."""
    f = f"{y} ~ " + " + ".join(BASE + xs + ["C(season_id)"])
    pred = pd.Series(np.nan, index=d.index)
    for gdom in d.domain.unique():
        tr, te = d[d.domain != gdom], d[d.domain == gdom]
        te = te[te.season_id.isin(tr.season_id)]
        pred.loc[te.index] = smf.ols(f, tr).fit().predict(te)
    ok = pred.notna()
    base = d[ok].groupby("season_id")[y].transform("mean")
    return 1 - ((d[y][ok] - pred[ok]) ** 2).sum() / ((d[y][ok] - base) ** 2).sum()


LODO_SETS = {"Base": [], "Phases": ["need_p3", "fews_cs", "fews_fc"], "Triggers": TRIG, "Conflict": ["log_fat"],
             "Phases + triggers": ["need_p3", "fews_cs", "fews_fc"] + TRIG}
lrows = []
for y in OUTCOMES:
    d = p.dropna(subset=[y, "need_p3", "fews_cs", "fews_fc"] + TRIG).copy()
    for lab, xs in LODO_SETS.items():
        lrows.append(dict(outcome=y, info=lab, r2=lodo_r2(d, y, xs), n=len(d), domains=d.domain.nunique()))
lodo = pd.DataFrame(lrows)
lodo.to_csv(TAB / "triggers_lodo_r2.csv", index=False)

# ------------------------------------------------------------------ Nigeria (NFSS rounds, 2023-26)
NG = INP / "panel" / "nga_domain_panel.parquet"
ng_rows = []
if NG.exists():
    g = pd.read_parquet(NG)
    g["ptype"] = "rural"
    g["deyr"] = 0
    g["season_rank"] = g.groupby("round_id").ngroup()
    g["lp_cereal"], g["lp_goat"] = g.dp12.fillna(0), 0.0
    for c in ["fews_cs", "fews_fc"]:
        g[c] = g[c].fillna(g.groupby("round_id")[c].transform("mean")).fillna(g[c].mean())
    NSETS = {"Base (population type, season)": [],
             "Phases (IPC share 3+, FEWS NET map and forecast)": ["need_p3", "fews_cs", "fews_fc"],
             "Triggers (rain, conflict, prices)": ["rain_z", "rain12_z", "log_fat", "lp_cereal"],
             "Phases + triggers": ["need_p3", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat", "lp_cereal"],
             "Previous survey": ["L_{y}"],
             "Previous survey + triggers": ["L_{y}", "rain_z", "rain12_z", "log_fat", "lp_cereal"]}
    for y in OUTCOMES:
        for lab, xs in NSETS.items():
            xs = [x.format(y=y) for x in xs]
            need = [y] + (["L_gam", "L_cdr", "L_u5dr"] if "Previous" in lab else [])
            if any(x.startswith("L_") and x not in g.columns for x in xs):
                continue
            d = g.dropna(subset=[y] + [x for x in xs if x.startswith("L_")]).copy()
            d = d.reset_index(drop=True)
            BASE_SAVE = BASE[:]
            BASE[:] = []
            try:
                r2v = oos_r2(d.assign(dummy=1), y, xs if xs else ["dummy"])
            finally:
                BASE[:] = BASE_SAVE
            ng_rows.append(dict(outcome=y, info=lab, r2=r2v, n=len(d), seasons=d.season_rank.nunique()))
ngr = pd.DataFrame(ng_rows)
ngr.to_csv(TAB / "triggers_oos_r2_nga.csv", index=False)

# ------------------------------------------------------------------ within-domain regressions
z = p.copy()
z["trend"] = z.year - 2020
for v in TRIG + ["need_p3", "fews_cs"]:
    z[f"z_{v}"] = (z[v] - z[v].mean()) / z[v].std()
co = []
for y in OUTCOMES + ["morbidity"]:
    for lab, rhs in {"triggers only": [f"z_{v}" for v in TRIG],
                     "phase only": ["z_need_p3"],
                     "both": [f"z_{v}" for v in TRIG] + ["z_need_p3"]}.items():
        d = z.dropna(subset=[y] + rhs)
        # domain effects, season type and a linear trend; season effects would absorb country-wide droughts
        m = smf.ols(f"{y} ~ " + " + ".join(rhs) + " + C(domain) + deyr + trend", d).fit(
            cov_type="cluster", cov_kwds={"groups": d.domain.astype("category").cat.codes})
        for v in rhs:
            co.append(dict(outcome=y, spec=lab, var=v[2:], b=m.params[v], se=m.bse[v], p=m.pvalues[v],
                           n=int(m.nobs), mean=d[y].mean()))
co = pd.DataFrame(co)
co.to_csv(TAB / "triggers_within.csv", index=False)

# does the official phase respond to the triggers?
d = z.dropna(subset=["need_p3"] + [f"z_{v}" for v in TRIG])
mp = smf.ols("need_p3 ~ " + " + ".join(f"z_{v}" for v in TRIG) + " + C(domain) + deyr + trend", d).fit(
    cov_type="cluster", cov_kwds={"groups": d.domain.astype("category").cat.codes})
phase_on = pd.DataFrame({"b": mp.params, "se": mp.bse, "p": mp.pvalues}).loc[[f"z_{v}" for v in TRIG]]
phase_on.to_csv(TAB / "triggers_phase_response.csv")

# ------------------------------------------------------------------ figure
LAB = {"gam": "Acute malnutrition", "sam": "Severe acute\nmalnutrition", "cdr": "Crude death rate",
       "u5dr": "Under-five\ndeath rate"}
COLS = ["#c3c2b7", "#e34948", "#2a78d6", "#4a3aa7", "#1baf7a", "#008300"]
fig, ax = plt.subplots(figsize=(8, 4))
k = len(SETS)
w = 0.8 / k
for j, (lab, c) in enumerate(zip(SETS, COLS)):
    vals = [r2[(r2.outcome == y) & (r2["info"] == lab)].r2.iloc[0] for y in OUTCOMES]
    ax.bar(np.arange(len(OUTCOMES)) + (j - (k - 1) / 2) * w, np.maximum(vals, -0.05), w * 0.92, color=c, label=lab)
ax.axhline(0, color="#52514e", lw=0.8)
ax.set_xticks(range(len(OUTCOMES))); ax.set_xticklabels([LAB[y] for y in OUTCOMES])
ax.set_ylabel("Out-of-sample $R^2$ (leave one season out)")
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
ax.set_ylim(-0.06, max(0.6, r2.r2.max() + 0.15))
fig.savefig(PAPER / "figures" / "fig13_triggers_r2.pdf", bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ numbers
def g(y, lab):
    return r2[(r2.outcome == y) & (r2["info"] == lab)].r2.iloc[0]


def f2(x):
    return f"{x:.2f}".replace("-", "\\textminus{}")


m = {"trN": f"{len(r2.loc[r2.outcome == 'gam'].iloc[:1]) and int(r2[r2.outcome == 'gam'].n.iloc[0])}",
     "trNcdr": f"{int(r2[r2.outcome == 'cdr'].n.iloc[0])}",
     "trSeasons": f"{int(r2[r2.outcome == 'gam'].seasons.iloc[0])}",
     "trYearZero": f"{int(p.year.min())}", "trYearOne": f"{int(p.year.max())}"}
for y, Y in [("gam", "Gam"), ("sam", "Sam"), ("cdr", "Cdr"), ("u5dr", "Ufive")]:
    for lab, L in [("Base (population type, season)", "Base"), ("Phases (IPC share 3+, FEWS NET map and forecast)", "Phase"),
                   ("Triggers (rain, conflict, prices)", "Trig"), ("Phases + triggers", "PhaseTrig"),
                   ("Previous survey", "Last"), ("Previous survey + triggers", "LastTrig")]:
        m[f"tr{Y}{L}"] = f2(g(y, lab))
for y, L in [(y, L) for y in OUTCOMES for L in LODO_SETS]:
    nm = {"Base": "Base", "Phases": "Phase", "Triggers": "Trig", "Conflict": "Conf", "Phases + triggers": "PhaseTrig"}[L]
    Y = {"gam": "Gam", "sam": "Sam", "cdr": "Cdr", "u5dr": "Ufive"}[y]
    m[f"ld{Y}{nm}"] = f2(lodo[(lodo.outcome == y) & (lodo["info"] == L)].r2.iloc[0])
m["ldDomains"] = f"{int(lodo.domains.iloc[0])}"
for y in OUTCOMES:
    m["trSingleConf" + {"gam": "Gam", "sam": "Sam", "cdr": "Cdr", "u5dr": "Ufive"}[y]] = f2(
        oos_r2(p.dropna(subset=[y, "need_p3", "fews_cs", "fews_fc", f"L_{y}", "L_morbidity", "L_measles"] + TRIG), y, ["log_fat"]))
for y, Y in [("gam", "Gam"), ("sam", "Sam"), ("cdr", "Cdr"), ("u5dr", "Ufive"), ("morbidity", "Morb")]:
    for v, V in [("rain_z", "Rain"), ("rain12_z", "Rainyr"), ("log_fat", "Fat"), ("lp_cereal", "Cereal"), ("need_p3", "Pthree")]:
        r = co[(co.outcome == y) & (co.spec == "both") & (co["var"] == v)]
        if len(r):
            dig = 3 if y in ("cdr", "u5dr") else 2
            m[f"tw{Y}{V}"] = f"{r.b.iloc[0]:.{dig}f}".replace("-", "\\textminus{}")
            m[f"tw{Y}{V}Se"] = f"{r.se.iloc[0]:.{dig}f}"
for v, V in [("z_rain_z", "Rain"), ("z_rain12_z", "Rainyr"), ("z_log_fat", "Fat"), ("z_lp_cereal", "Cereal")]:
    m[f"tp{V}"] = f"{100 * phase_on.loc[v, 'b']:.1f}".replace("-", "\\textminus{}")
    m[f"tp{V}Se"] = f"{100 * phase_on.loc[v, 'se']:.1f}"
# effect of a 12-month rainfall DEFICIT of one standard deviation (sign flipped), for the text
for y, Y in [("gam", "Gam"), ("sam", "Sam"), ("cdr", "Cdr"), ("u5dr", "Ufive"), ("morbidity", "Morb")]:
    r = co[(co.outcome == y) & (co.spec == "both") & (co["var"] == "rain12_z")].iloc[0]
    dig = 3 if y in ("cdr", "u5dr") else 1
    m[f"tw{Y}Dry"] = f"{-r.b:.{dig}f}".replace("-", "\\textminus{}")
    m[f"tw{Y}DrySe"] = f"{r.se:.{dig}f}"
m["tpDry"] = f"{-100 * phase_on.loc['z_rain12_z', 'b']:.1f}".replace("-", "\\textminus{}")
for r in ngr.itertuples():
    Y = {"gam": "Gam", "sam": "Sam", "cdr": "Cdr", "u5dr": "Ufive"}[r.outcome]
    L = {"Base (population type, season)": "Base", "Phases (IPC share 3+, FEWS NET map and forecast)": "Phase",
         "Triggers (rain, conflict, prices)": "Trig", "Phases + triggers": "PhaseTrig", "Previous survey": "Last",
         "Previous survey + triggers": "LastTrig"}[r.info]
    m[f"ng{Y}{L}"] = f2(r.r2)
if len(ngr):
    m["ngN"] = f"{int(ngr[(ngr.outcome == 'gam') & (ngr['info'].str.startswith('Base'))].n.iloc[0])}"
    m["ngNlast"] = f"{int(ngr[(ngr.outcome == 'gam') & (ngr['info'] == 'Previous survey')].n.iloc[0])}"
    m["ngRounds"] = f"{int(ngr.seasons.max())}"
lines = ["% Written by code/84_triggers_vs_phases.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
(PAPER / "numbers_triggers.tex").write_text("\n".join(lines) + "\n")

pd.set_option("display.width", 220)
print(r2.pivot(index="info", columns="outcome", values="r2").round(3)[OUTCOMES])
print(r2.groupby("outcome")[["n", "seasons"]].first())
print("NIGERIA\n", ngr.pivot(index="info", columns="outcome", values="r2").round(3) if len(ngr) else "none", ngr.groupby("info").n.first() if len(ngr) else "")
print(lodo.pivot(index="info", columns="outcome", values="r2").round(3)[OUTCOMES])
print(co[co.spec == "both"].assign(b=lambda x: x.b.round(3), se=lambda x: x.se.round(3), p=lambda x: x.p.round(3))
      [["outcome", "var", "b", "se", "p", "n", "mean"]].to_string(index=False))
print("IPC share 3+ on triggers (sd units):\n", phase_on.round(3))
print("coverage: fews_cs", p.fews_cs.notna().mean().round(2), "fews_fc", p.fews_fc.notna().mean().round(2),
      "need_p3", p.need_p3.notna().mean().round(2))
