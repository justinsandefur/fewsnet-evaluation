"""Crises defined by need rather than outcome: does early warning raise the
chance that aid holds a new emergency back?

FEWS NET's "!" flag says humanitarian assistance keeps an area at least one
phase better than it would otherwise be. Taking that at face value, the phase
without aid ("need") is the mapped phase plus one for flagged areas. A new
emergency by need is an area whose need reaches Emergency (Phase 4+) after its
previous map (within 6 months) showed need below Emergency. It is either
  - a realised Emergency (mapped Phase 4+), or
  - an averted one (mapped Phase 3 with the flag: Emergency held back by aid).
Same for Crisis (need 3+: mapped 3+, or 2 with the flag).

Each onset is classed by FEWS NET's earlier forecasts for the area:
  early warning  a forecast issued 4-8 months before reached the level
  late warning   only forecasts issued 1-3 months before did
  no warning     none did (onsets with no forecast issued 4-8 months before
                 are excluded)
under two definitions of "reached the level": the forecast phase itself, or
the forecast's need (forecasts carry the flag too).

  averted = a early + b late + FE(country x map month) + e, clustered by country

Caveat: forecast and flag come from the same analysts, so a forecast of
"Phase 3!" followed by a map of "Phase 3!" may be consistency, not aid working.
The forecast-phase definition avoids that channel.

Outputs: output/tables/need_onsets*.csv, output/figures/need_onsets.pdf
"""
import importlib.util
import textwrap
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
spec = importlib.util.spec_from_file_location("did", ROOT / "code" / "25_slope_did.py")
DID = importlib.util.module_from_spec(spec)
spec.loader.exec_module(DID)
GROUPS = ["no warning", "late warning (1-3 months)", "early warning (4-8 months)"]


def need(phase, flag):
    return np.minimum(phase + flag.astype(float), 5)


def onsets(cs, level):
    c = cs.sort_values(["fnid", "month"]).copy()
    c["need"] = need(c.phase, c.assist_flag)
    g = c.groupby("fnid")
    c["prev_need"], c["prev_month"] = g.need.shift(), g.month.shift()
    gap = (c.month - c.prev_month).apply(lambda x: x.n if pd.notna(x) else np.nan)
    e = c[(gap > 0) & (gap <= 6) & (c.prev_need < level) & (c.need >= level)].copy()
    e["averted"] = (e.phase < level).astype(float)
    e["level"] = level
    return e


def classify(e, proj, level):
    ev = e[["fnid", "month"]].drop_duplicates().rename(columns={"month": "t0"})
    p = proj[["fnid", "month", "report_month", "phase", "assist_flag"]].merge(ev, on="fnid")
    lag = (p.t0 - p.report_month).apply(lambda x: x.n)
    to = (p.t0 - p.month).apply(lambda x: x.n)
    p = p[(lag >= 1) & (lag <= 8) & (to >= 0) & (to <= 3)].assign(lag=lag)
    p["fneed"] = need(p.phase, p.assist_flag)
    agg = p.assign(early_ph=(p.lag >= 4) & (p.phase >= level), late_ph=(p.lag <= 3) & (p.phase >= level),
                   early_nd=(p.lag >= 4) & (p.fneed >= level), late_nd=(p.lag <= 3) & (p.fneed >= level),
                   early_fc=p.lag >= 4,
                   early_flagged=(p.lag >= 4) & (p.fneed >= level) & (p.phase < level)) \
        .groupby(["fnid", "t0"])[["early_ph", "late_ph", "early_nd", "late_nd", "early_fc", "early_flagged"]] \
        .max().astype(float).reset_index().rename(columns={"t0": "month"})
    e = e.merge(agg, on=["fnid", "month"], how="inner")
    e = e[e.early_fc == 1]
    for d in ["ph", "nd"]:
        e[f"late_{d}"] = e[f"late_{d}"] * (1 - e[f"early_{d}"])
        e[f"group_{d}"] = np.select([e[f"early_{d}"] == 1, e[f"late_{d}"] == 1], GROUPS[:0:-1], GROUPS[0])
    return e


def main():
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    cs = cs[cs.month.dt.year <= 2024]
    out = []
    for level, name in [(4, "Emergency"), (3, "Crisis")]:
        e = classify(onsets(cs, level), proj, level)
        e["onset"] = name
        out.append(e)
    E = pd.concat(out, ignore_index=True)
    E["cell"] = E.country_code + "_" + E.month.astype(str)
    E["iso3"] = E.country_code
    E.to_parquet(INP / "panel" / "need_onsets.parquet", index=False)

    raw, rows = [], []
    for onset in ["Emergency", "Crisis"]:
        d = E[E.onset == onset]
        for dfn, lab in [("ph", "forecast phase"), ("nd", "forecast need (phase + flag)")]:
            r = d.groupby(f"group_{dfn}").agg(n=("averted", "size"), averted=("averted", "mean"),
                                               countries=("country_code", "nunique")).reindex(GROUPS)
            r["onset"], r["warning_defn"] = onset, lab
            raw.append(r.reset_index().rename(columns={f"group_{dfn}": "group"}))
            res, n, G = DID.fe_ols(d, "averted", [f"early_{dfn}", f"late_{dfn}"], ["cell"])
            for t in [f"early_{dfn}", f"late_{dfn}"]:
                rows.append({"onset": onset, "warning_defn": lab, "term": t.split("_")[0], "coef": res.coef[t],
                             "se": res.se[t], "n": n, "countries": G})
        # early warnings that themselves came flagged ("3!" forecast) vs unflagged forecasts of the level
        w = d[d.early_nd == 1]
        rows.append({"onset": onset, "warning_defn": "early warnings: forecast already flagged",
                     "term": "share averted | flagged forecast", "coef": w[w.early_flagged == 1].averted.mean(),
                     "se": np.nan, "n": int((w.early_flagged == 1).sum()), "countries": np.nan})
        rows.append({"onset": onset, "warning_defn": "early warnings: forecast of the level itself",
                     "term": "share averted | unflagged forecast", "coef": w[w.early_flagged == 0].averted.mean(),
                     "se": np.nan, "n": int((w.early_flagged == 0).sum()), "countries": np.nan})
    raw = pd.concat(raw)
    R = pd.DataFrame(rows)
    raw.to_csv(TAB / "need_onsets_raw.csv", index=False)
    R.to_csv(TAB / "need_onsets.csv", index=False)
    pd.set_option("display.width", 220)
    print(raw.round(3).to_string())
    print(R.round(3).to_string())
    print("Emergency-need onsets by country (n, share averted):")
    em = E[E.onset == "Emergency"]
    print(em.groupby("country_code").averted.agg(["size", "mean"]).sort_values("size", ascending=False).round(2).head(12))
    figure(raw, R)


def figure(raw, R):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    cols = {"no warning": "#bdbdbd", "late warning (1-3 months)": "#6baed6", "early warning (4-8 months)": "#1f4e79"}
    for a, onset in zip(ax, ["Emergency", "Crisis"]):
        for i, dfn in enumerate(["forecast phase", "forecast need (phase + flag)"]):
            r = raw[(raw.onset == onset) & (raw.warning_defn == dfn)].set_index("group")
            for j, g in enumerate(GROUPS):
                v, n = r.loc[g, "averted"], r.loc[g, "n"]
                se = np.sqrt(v * (1 - v) / max(n, 1))
                a.bar(i + (j - 1) * 0.27, 100 * v, 0.27, color=cols[g], yerr=196 * se, capsize=2,
                      label=g if i == 0 else None)
                a.text(i + (j - 1) * 0.27, 1, f"n={int(n)}", ha="center", fontsize=7, color="white" if j == 2 else "#333")
        lv = "Emergency (Phase 4)" if onset == "Emergency" else "Crisis (Phase 3)"
        held = "Phase 3 with the aid flag" if onset == "Emergency" else "Phase 2 with the aid flag"
        est = []
        for dfn in ["forecast phase", "forecast need (phase + flag)"]:
            c = R[(R.onset == onset) & (R.warning_defn == dfn) & (R.term == "early")].iloc[0]
            est.append(f"early vs none: {100 * c.coef:+.0f} pp (s.e. {100 * c.se:.0f})")
        a.set_xticks([0, 1], [f"Warning: forecast phase\nreached the level\n{est[0]}",
                              f"Warning: forecast phase\n(+1 if flagged) reached it\n{est[1]}"], fontsize=8.5)
        a.set_ylabel(f"Share held back by aid\n(mapped as {held}) (%)")
        a.set_title(f"{'A' if onset == 'Emergency' else 'B'}. New needs at {lv} or worse", loc="left",
                    fontweight="bold", fontsize=10.5)
        a.set_ylim(0, a.get_ylim()[1] * 1.2)
        a.legend(fontsize=8, frameon=False, loc="upper left")
    fig.suptitle("Taking FEWS NET's aid flag at face value: are crises it warned of early more often held back by aid?",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.text(0.01, 0.01, textwrap.fill(
        "FEWS NET current-situation maps 2011-2024. Need = mapped phase, plus one where FEWS NET flags that humanitarian "
        "assistance keeps the area at least one phase better. A new need is an area whose need reaches the level when "
        "its previous map (within 6 months) was below it; it is either realised (mapped at the level) or held back by "
        "aid (mapped one phase lower with the flag). Warnings: forecasts for the onset month issued 4-8 months (early) "
        "or only 1-3 months (late) before. Onsets with no forecast issued 4-8 months before are excluded. 95% intervals "
        "for raw shares; estimates in brackets compare onsets in the same country and map round, clustered by country.",
        200), fontsize=7.5, color="#555")
    fig.savefig(FIG / "need_onsets.pdf")
    fig.savefig(FIG / "need_onsets.png", dpi=150)


if __name__ == "__main__":
    main()
