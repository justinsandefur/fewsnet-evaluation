"""Bounding the survey-vs-phase horse race for the effect of aid.

The problem. Aid follows the phases more than the surveys. If aid works, it lowers malnutrition and
death where the phases sent it, so phases will look like worse predictors of outcomes than they are of
the outcomes that would have occurred without aid (their 'false alarms' may be successes). We cannot
estimate the effect of aid here. Instead we add back the deaths and malnutrition that aid would have
averted under stated assumptions, rebuild counterfactual no-aid outcomes Y*, and rerun the out-of-sample
horse race of 84_triggers_vs_phases.py on Y*. Somalia, FSNAU survey domains, 2015-2026.

Two versions.
 A. Aid dose. Main version (worst case for our argument): all humanitarian funding reported to FTS for
    Somalia, half the year's total per person, allocated across domains in proportion to the IPC Phase 3+
    share, so that aid lines up exactly with the phases. Robustness: observed OCHA pooled-fund budgets in
    the domain's districts over the six months before the survey, scaled up to the FTS total (lumpy).
    Aid of a dollars per person averts a / c deaths per person, where c is the cost per death averted;
    half of averted deaths are children under five (as in Somalia 2022); and a / c_g cases of acute
    malnutrition per person, with c_g = c / 10 (about one death per ten cases treated). We vary c from
    infinity (aid does nothing) down to $250 per death averted and record where the horse race flips.
 B. FEWS NET's '!' flag. FEWS NET marks areas where it judges aid keeps the population at least one
    phase better. Y* adds k times the flagged share of the domain's population, where k is one phase's
    worth of outcome: (i) our within-zone estimate (Section 5) and (ii) the IPC reference bands
    (5 points of GAM, 0.45 deaths per 10,000 per day, 1 under-five death per 10,000 per day).
Outputs: output/tables/aidbounds_*.csv, output/cgd_paper/numbers_bounds.tex,
         output/cgd_paper/figures/fig16_bounds.pdf
"""
import importlib.util
import io
import contextlib
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, PAPER = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "cgd_paper"
U5_SHARE, HALF = 0.19, 182.5
CASES_PER_DEATH = 10


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    return m


T = load("m84", "84_triggers_vs_phases.py")
M68 = load("m68", "68_somalia_us_cut.py")
p = T.p.copy()
dists = M68.survey_panel()[["domain", "season_id", "dists"]]
p = p.merge(dists, on=["domain", "season_id"], how="left")

# --- aid per person before the survey, and the '!' flag share
sub = pd.read_parquet(INP / "panel" / "subnational_SOM.parquet")
sub["dist"] = sub.key.map(M68.dist_key)
sub["tp"] = pd.PeriodIndex(sub.t, freq="M")
f = pd.read_parquet(INP / "fts" / "fts_flows.parquet", columns=["amount_usd", "status", "flow_type", "boundary",
                                                                 "dest_country", "usage_year"])
f = f[f.status.isin(["paid", "commitment"]) & (f.flow_type == "Standard") & (f.boundary == "incoming") &
      (f.dest_country == "Somalia") & f.usage_year.astype(str).str.fullmatch(r"\d{4}")]
fts_year = f.groupby(f.usage_year.astype(int)).amount_usd.sum()
cbpf_year = sub.groupby(sub.tp.dt.year).cbpf_all.sum()
scale = (fts_year / cbpf_year).replace([np.inf], np.nan)
scale = scale.fillna(scale.median())
pop_d = sub.groupby("dist").pop.mean()

aid_pc, flag = [], []
for r in p.itertuples():
    w = {k: v for k, v in json.loads(r.dists).items() if k not in (None, "null") and k in pop_d.index} \
        if isinstance(r.dists, str) else {}
    if not w:
        aid_pc.append(np.nan); flag.append(np.nan); continue
    lo, hi = r.t - 6, r.t - 1
    a = sub[sub.dist.isin(w) & (sub.tp >= lo) & (sub.tp <= hi)].groupby("dist").cbpf_all.sum()
    pc = sum(v * a.get(k, 0.0) / pop_d[k] for k, v in w.items()) / sum(w.values())
    aid_pc.append(pc * scale.get(r.t.year, scale.median()))
    fl = sub[sub.dist.isin(w) & (sub.tp <= r.t)].sort_values("tp").groupby("dist").flag.last()
    flag.append(sum(v * fl.get(k, 0.0) for k, v in w.items()) / sum(w.values()))
p["aid_pc_obs"], p["flag"] = aid_pc, flag
# Main dose version: the worst case for our argument. All humanitarian aid to Somalia in the six months
# before the survey (half the year's FTS total per person) is allocated in proportion to the IPC Phase 3+
# share, so aid -- and the outcomes it averts -- line up exactly with the phases.
som_pop = sub.groupby("tp").pop.sum().groupby(lambda t: t.year).max()
nat_pc = (fts_year / som_pop.reindex(fts_year.index)).dropna() / 2
p["nat_pc"] = p.t.apply(lambda t: nat_pc.get(t.year, nat_pc.median()))
rel = p.need_p3 / p.groupby("season_id").need_p3.transform("mean")
p["aid_pc"] = p.nat_pc * rel

p.drop(columns=["dists", "fnids"], errors="ignore").assign(t=p.t.astype(str)).to_csv(
    TAB / "aidbounds_panel.csv", index=False)                       # analysis panel, for the Stata port
SETS = {"Phases": ["need_p3", "fews_cs", "fews_fc"], "Triggers": T.TRIG,
        "Previous survey": ["L_{y}", "L_morbidity", "L_measles"]}
OUT = ["gam", "cdr", "u5dr"]


def horse(q):
    """OOS R2 for each information set, on q's (counterfactual) outcomes, common sample."""
    q = q.sort_values(["domain", "t"]).copy()
    res = {}
    for y in OUT:
        q[f"L_{y}"] = q.groupby("domain")[y].shift(1)
        d = q.dropna(subset=[y, "need_p3", "fews_cs", "fews_fc", f"L_{y}", "L_morbidity", "L_measles"] + T.TRIG)
        for lab, xs in SETS.items():
            res[(y, lab)] = T.oos_r2(d, y, [x.format(y=y) for x in xs])
    return res, len(d)


def add_dose(q, c):
    q = q.copy()
    a = q.aid_pc.fillna(0)
    if np.isfinite(c):
        deaths_pc = a / c                                   # deaths averted per person over six months
        q["cdr"] = q.cdr + deaths_pc * 1e4 / HALF
        q["u5dr"] = q.u5dr + 0.5 * deaths_pc / U5_SHARE * 1e4 / HALF
        q["gam"] = q.gam + 100 * (a / (c / CASES_PER_DEATH)) / U5_SHARE
    return q


rows = []
COSTS = [np.inf, 100000, 50000, 20000, 10000, 5000, 2500, 1000, 500, 250]
for c in COSTS:
    res, n = horse(add_dose(p, c))
    for (y, lab), v in res.items():
        rows.append(dict(version="dose", cost=c, outcome=y, info=lab, r2=v, n=n))
    res, n = horse(add_dose(p.assign(aid_pc=p.aid_pc_obs), c))
    for (y, lab), v in res.items():
        rows.append(dict(version="dose, observed pooled funds", cost=c, outcome=y, info=lab, r2=v, n=n))
STEPS = {"within-zone estimate": {"gam": 0.8, "cdr": 0.12, "u5dr": 0.25},
         "IPC bands": {"gam": 5.0, "cdr": 0.45, "u5dr": 1.0}}
for lab_k, k in STEPS.items():
    q = p.copy()
    for y in OUT:
        q[y] = q[y] + k[y] * q.flag.fillna(0)
    res, n = horse(q)
    for (y, lab), v in res.items():
        rows.append(dict(version=f"flag: {lab_k}", cost=np.nan, outcome=y, info=lab, r2=v, n=n))
B = pd.DataFrame(rows)
B.to_csv(TAB / "aidbounds_r2.csv", index=False)

# breakdown: cheapest cost per death at which phases still do worse than the previous survey / triggers
brk = {}
for y in OUT:
    d = B[(B.version == "dose") & (B.outcome == y)].pivot(index="cost", columns="info", values="r2").sort_index(ascending=False)
    for rival in ["Previous survey", "Triggers"]:
        flips = d[d["Phases"] >= d[rival]]
        brk[(y, rival)] = flips.index.max() if len(flips) else np.nan     # highest cost at which phases win
summary = dict(aid_pc_mean=float(p.aid_pc.mean()), aid_pc_median=float(p.aid_pc.median()),
               nat_pc=float(nat_pc.median()),
               flag_mean=float(p.flag.mean()), scale_median=float(scale.median()))

# --- figure: two stacked panels, malnutrition (cost per case averted) and under-five deaths (cost per death)
xs = [c for c in COSTS if np.isfinite(c)]
xpos = list(range(len(xs) + 1))


def xpos_of(c):                       # position of cost c on the categorical axis (log-interpolated)
    for i in range(len(xs) - 1):
        hi, lo = xs[i], xs[i + 1]
        if lo <= c <= hi:
            return i + 1 + (np.log(hi) - np.log(c)) / (np.log(hi) - np.log(lo))


sty = {"Phases": ("#e34948", "o"), "Triggers": ("#2a78d6", "s"), "Previous survey": ("#1baf7a", "^")}
LBL = {"Phases": "Phases (IPC share 3+, FEWS NET map and forecast)", "Triggers": "Triggers (rain, conflict, prices)",
       "Previous survey": "Previous survey"}
fig, axes = plt.subplots(2, 1, figsize=(7, 9.2))
panels = [("gam", "A. Acute malnutrition", "Assumed cost per case of acute malnutrition averted by all humanitarian aid",
           CASES_PER_DEATH, "best-evidenced\ntreatment,\n$400-700 per case"),
          ("u5dr", "B. Under-five death rate", "Assumed cost per death averted by all humanitarian aid", 1,
           "best-evidenced\ntreatment,\n$4,000-7,000 per death")]
for ax, (y, ttl, xl, div, band) in zip(axes, panels):
    ax.axvspan(xpos_of(7000), xpos_of(4000), color="#e4e3df", alpha=0.8, lw=0)
    ax.text((xpos_of(7000) + xpos_of(4000)) / 2, 0.47, band, fontsize=7.5, color="#52514e", ha="center", va="top")
    d = B[(B.version == "dose") & (B.outcome == y)]
    for lab, (col, mk) in sty.items():
        v = [d[(d.cost == c) & (d["info"] == lab)].r2.iloc[0] for c in COSTS]
        ax.plot(xpos, v, "-", color=col, marker=mk, ms=5, lw=1.8, label=LBL[lab])
    ax.set_xticks(xpos)
    ax.set_xticklabels(["No effect"] + [f"${int(c / div):,}" for c in xs], rotation=30, ha="right", fontsize=8.5)
    ax.set_xlabel(xl, fontsize=9)
    ax.set_ylabel("Out-of-sample $R^2$, outcomes without aid")
    ax.set_title(ttl, loc="left", fontsize=10.5)
    ax.axhline(0, color="#52514e", lw=0.8)
    ax.set_ylim(-0.12, 0.5)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
fig.tight_layout(h_pad=2.5, rect=(0, 0.05, 1, 1))
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, fontsize=8.5, loc="lower center", ncol=1, bbox_to_anchor=(0.5, -0.01))
fig.savefig(PAPER / "figures" / "fig16_bounds.pdf", bbox_inches="tight"); plt.close(fig)


# --- numbers
def f2(x):
    return f"{x:.2f}".replace("-", "\\textminus{}")


m = {"bdNatPc": f"{summary['nat_pc']:.0f}", "bdAidPc": f"{summary['aid_pc_median']:.0f}", "bdAidPcMean": f"{summary['aid_pc_mean']:.0f}",
     "bdScale": f"{summary['scale_median']:.0f}", "bdFlag": f"{100 * summary['flag_mean']:.0f}"}
Y = {"gam": "Gam", "cdr": "Cdr", "u5dr": "Ufive"}
for y in OUT:
    for rival, R in [("Previous survey", "Last"), ("Triggers", "Trig")]:
        v = brk[(y, rival)]
        m[f"bdBreak{Y[y]}{R}"] = "none" if pd.isna(v) else ("no effect" if not np.isfinite(v) else f"\\${int(v):,}")
    for c, C in [(np.inf, "None"), (5000, "Fivek"), (1000, "Onek")]:
        for lab, L in [("Phases", "Phase"), ("Triggers", "Trig"), ("Previous survey", "Last")]:
            m[f"bd{Y[y]}{C}{L}"] = f2(B[(B.version == "dose") & (B.cost == c) & (B.outcome == y) & (B["info"] == lab)].r2.iloc[0])
    for k, K in [("flag: within-zone estimate", "FlagW"), ("flag: IPC bands", "FlagB")]:
        for lab, L in [("Phases", "Phase"), ("Triggers", "Trig"), ("Previous survey", "Last")]:
            m[f"bd{Y[y]}{K}{L}"] = f2(B[(B.version == k) & (B.outcome == y) & (B["info"] == lab)].r2.iloc[0])
lines = ["% Written by code/90_aid_bounds.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
(PAPER / "numbers_bounds.tex").write_text("\n".join(lines) + "\n")

pd.set_option("display.width", 200)
print(summary)
print(B[B.version == "dose"].pivot_table(index=["outcome", "cost"], columns="info", values="r2").round(3))
print(B[B.version == "dose, observed pooled funds"].pivot_table(index=["outcome", "cost"], columns="info", values="r2").round(3))
print(B[~B.version.str.startswith("dose")].pivot_table(index=["outcome", "version"], columns="info", values="r2").round(3))
print({k: v for k, v in brk.items()})
