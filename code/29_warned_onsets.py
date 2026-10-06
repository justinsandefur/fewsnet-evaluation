"""Are crises FEWS NET warned about early more often held back by aid?

Take every area that newly enters Crisis (Phase 3+, from Phase 1-2) or
Emergency (Phase 4+, from Phase 1-3) on a FEWS NET current-situation map.
Classify each onset by FEWS NET's earlier forecasts for that area:
  early warning  a forecast issued 4-8 months before reached the onset phase
  late warning   only forecasts issued 1-3 months before did
  no warning     no forecast issued 1-8 months before did
Outcome: FEWS NET's own judgment that humanitarian assistance is keeping the
area at least one phase better than it would otherwise be (the "!" flag), on
the onset map, and on the next map (2-6 months later), plus the phase on the
next map.

  flag = a early + b late + FE(country x map month x onset phase) + e

clustered by country. Uses FEWS NET's judgment at face value; both the
forecast and the flag come from the same analysts. Onsets that aid fully
prevented never appear, so this compares crises that happened.

Outputs: output/tables/warned_onsets*.csv, output/figures/warned_onsets.pdf
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


def events(cs, level):
    c = cs.sort_values(["fnid", "month"]).copy()
    g = c.groupby("fnid")
    c["prev_phase"], c["prev_month"] = g.phase.shift(), g.month.shift()
    c["next_phase"], c["next_month"], c["next_flag"] = g.phase.shift(-1), g.month.shift(-1), g.assist_flag.shift(-1)
    gap = (c.month - c.prev_month).apply(lambda x: x.n if pd.notna(x) else np.nan)
    ngap = (c.next_month - c.month).apply(lambda x: x.n if pd.notna(x) else np.nan)
    e = c[(gap > 0) & (gap <= 6) & (c.prev_phase < level) & (c.phase >= level)].copy()
    e.loc[~((ngap > 0) & (ngap <= 6)), ["next_phase", "next_flag"]] = np.nan
    e["level"] = level
    return e


def warnings_for(e, proj, level):
    """Most severe forecast for the onset month (or the 3 months before) by issue lag."""
    ev = e[["fnid", "month"]].drop_duplicates().rename(columns={"month": "t0"})
    p = proj[["fnid", "month", "report_month", "phase"]].merge(ev, on="fnid")
    lag = (p.t0 - p.report_month).apply(lambda x: x.n)
    to = (p.t0 - p.month).apply(lambda x: x.n)
    p = p[(lag >= 1) & (lag <= 8) & (to >= 0) & (to <= 3)].assign(lag=lag)
    w = p.groupby(["fnid", "t0"]).apply(lambda g: pd.Series({
        "early": float((g[g.lag >= 4].phase >= level).any()),
        "late": float((g[g.lag <= 3].phase >= level).any()),
        "any_fc": float(len(g) > 0),
        "early_fc": float((g.lag >= 4).any())})).reset_index().rename(columns={"t0": "month"})
    return e.merge(w, on=["fnid", "month"], how="left")


def main():
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    cs["assist_flag"] = cs.assist_flag.astype(float)
    out = []
    for level, name in [(3, "Crisis"), (4, "Emergency")]:
        e = warnings_for(events(cs, level), proj, level)
        e = e[e.early_fc == 1]                          # an early forecast existed, so "no early warning" is a real miss
        e["late"] = e.late * (1 - e.early)
        e["group"] = np.select([e.early == 1, e.late == 1], GROUPS[:0:-1], GROUPS[0])
        e["onset"] = name
        out.append(e)
    E = pd.concat(out, ignore_index=True)
    E = E[E.month.dt.year <= 2024]                  # before the 2025 shutdown
    E["flag_now"] = E.assist_flag
    E["flag_next"] = E.next_flag
    E["flag_either"] = E[["flag_now", "flag_next"]].max(axis=1, skipna=True)
    E["next_worse"] = (E.next_phase > E.phase).astype(float).where(E.next_phase.notna())
    E["next_below"] = (E.next_phase < E.level).astype(float).where(E.next_phase.notna())
    E["cell"] = E.country_code + "_" + E.month.astype(str) + "_" + E.phase.astype(str)
    E["iso3"] = E.country_code
    E.to_parquet(INP / "panel" / "warned_onsets.parquet", index=False)

    raw = E.groupby(["onset", "group"]).agg(n=("flag_now", "size"), flag_now=("flag_now", "mean"),
                                            flag_next=("flag_next", "mean"), flag_either=("flag_either", "mean"),
                                            next_worse=("next_worse", "mean"), next_below=("next_below", "mean"),
                                            countries=("country_code", "nunique"))
    raw = raw.reindex(pd.MultiIndex.from_product([["Crisis", "Emergency"], GROUPS], names=["onset", "group"]))
    raw.to_csv(TAB / "warned_onsets_raw.csv")
    pd.set_option("display.width", 220)
    print(raw.round(3).to_string())

    rows = []
    for onset in ["Crisis", "Emergency"]:
        d = E[E.onset == onset]
        for y in ["flag_now", "flag_next", "flag_either", "next_worse", "next_below"]:
            r, n, G = DID.fe_ols(d, y, ["early", "late"], ["cell"])
            for t in ["early", "late"]:
                rows.append({"onset": onset, "outcome": y, "term": t, "coef": r.coef[t], "se": r.se[t], "n": n,
                             "countries": G, "mean_no_warning": d[d.group == GROUPS[0]][y].mean()})
    R = pd.DataFrame(rows)
    R["t"] = R.coef / R.se
    R.to_csv(TAB / "warned_onsets.csv", index=False)
    print(R.round(3).to_string())
    # by year, Crisis onsets: early-warning gap in flag_either
    yr = []
    for y_, d in E[E.onset == "Crisis"].groupby(E.month.dt.year):
        if d.early.sum() >= 10 and (d.early == 0).sum() >= 10:
            r, n, G = DID.fe_ols(d, "flag_either", ["early", "late"], ["cell"])
            yr.append({"year": y_, "coef": r.coef["early"], "se": r.se["early"], "n": n})
    yr = pd.DataFrame(yr)
    yr.to_csv(TAB / "warned_onsets_by_year.csv", index=False)
    print(yr.round(3).to_string())
    figure(raw, R, E)


def figure(raw, R, E):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
    cols = {"no warning": "#bdbdbd", "late warning (1-3 months)": "#6baed6", "early warning (4-8 months)": "#1f4e79"}
    for a, onset in zip(ax, ["Crisis", "Emergency"]):
        r = raw.loc[onset]
        x = np.arange(3)
        for i, (y, lab) in enumerate([("flag_now", "on the onset map"), ("flag_next", "on the next map (2-6 months on)"),
                                      ("flag_either", "on either")]):
            for j, g in enumerate(GROUPS):
                v = r.loc[g, y]
                n = E[(E.onset == onset) & (E.group == g)][y].notna().sum()
                se = np.sqrt(v * (1 - v) / max(n, 1))
                a.bar(i + (j - 1) * 0.27, 100 * v, 0.27, color=cols[g], yerr=196 * se, capsize=2,
                      label=f"{g} (n={int(r.loc[g, 'n'])})" if i == 0 else None)
        a.set_xticks(x, ["Flagged on the\nonset map", "Flagged on the\nnext map", "Flagged on\neither"])
        a.set_ylabel("Share of new crises FEWS NET says aid is holding\nat least one phase better (%)")
        lvl = "Crisis or worse (Phase 3+)" if onset == "Crisis" else "Emergency or worse (Phase 4+)"
        a.set_title(f"{'A' if onset == 'Crisis' else 'B'}. Areas newly in {lvl}", loc="left", fontweight="bold",
                    fontsize=10.5)
        a.legend(fontsize=8, frameon=False, loc="upper left")
        c = R[(R.onset == onset) & (R.outcome == "flag_either") & (R.term == "early")].iloc[0]
        a.text(0.99, 0.97, f"Early vs no warning, same country\nand map round: {100 * c.coef:+.1f} pp (s.e. {100 * c.se:.1f})",
               transform=a.transAxes, ha="right", va="top", fontsize=8.5)
    fig.suptitle("Are crises FEWS NET warned about early more often held back by aid, by FEWS NET's own judgment?",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.text(0.01, 0.01, textwrap.fill(
        "FEWS NET current-situation maps, 2011-2024. A new crisis is an area at the phase shown whose previous map "
        "(within 6 months) was below it. Early warning: a forecast issued 4-8 months before reached that phase; late: "
        "only forecasts issued 1-3 months before did; no warning: none did (onsets with no forecast issued 4-8 months "
        "before are excluded). Flag: FEWS NET marks the area '!' when humanitarian assistance keeps it at least one "
        "phase better than it would otherwise be. 95% intervals for raw shares; the regression estimate compares "
        "onsets in the same country, map round and phase, clustered by country.", 200), fontsize=7.5, color="#555")
    fig.savefig(FIG / "warned_onsets.pdf")
    fig.savefig(FIG / "warned_onsets.png", dpi=150)


if __name__ == "__main__":
    main()
