"""Does humanitarian funding follow FEWS NET's classifications, current or forecast?

Country panel at each FEWS NET full map round (Feb/Jun/Oct; quarterly before
2016), 2011-2024. For country c and map round t:
  current   share of the country's FEWS NET areas in Crisis+ (Phase 3+) or
            Emergency+ (Phase 4+) on the current-situation map
  forecast  same shares in the near-term (ML1, next ~4 months) and medium-term
            (ML2, ~4-8 months) projections issued in the same report
  funding   humanitarian funding committed to the country (FTS, all sectors and
            food security / nutrition), months t+1..t+6, log(1 + US$)

  log F(t+1..t+6) = a current + b forecast + g log F(t-6..t-1) + country FE
                    + map-round FE + e, clustered by country

Also a first-difference version (change in shares between rounds on change in
log funding), and the forecast's surprise relative to the current map
(forecast share minus current share). Area shares are unweighted counts of
FEWS NET areas (FEWS NET does not publish area populations).

Outputs: output/tables/aid_response*.csv, output/figures/aid_response.pdf
"""
import importlib.util
import json
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


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


DID = load("did", "25_slope_did.py")
ERR = load("err", "12_errors.py")


def panel():
    c = pd.read_parquet(INP / "fewsnet" / "classifications.parquet")
    n = c[c.scenario == "CS"].groupby("report_month").size()
    rounds = n[n > 1000].index
    c = c[c.report_month.isin(rounds) & (c.report_month.dt.year <= 2024)]
    u = c.groupby(["country_code", "report_month", "scenario", "fnid"]).phase.max().reset_index()
    s = u.groupby(["country_code", "report_month", "scenario"]).phase.agg(
        s3=lambda x: (x >= 3).mean(), s4=lambda x: (x >= 4).mean(), n="size").unstack("scenario")
    s.columns = [f"{a}_{b}" for a, b in s.columns]
    s = s.dropna(subset=["s3_CS"]).reset_index()
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    F = ERR.fts_monthly(codes)
    def window(cc, t, a, b, col):
        idx = pd.MultiIndex.from_product([[cc], pd.period_range(t + a, t + b, freq="M")])
        return F[col].reindex(idx, fill_value=0).sum()
    for col in ["all", "food"]:
        s[f"f_{col}"] = np.log1p([window(cc, t, 1, 6, col) for cc, t in zip(s.country_code, s.report_month)])
        s[f"f_{col}_lag"] = np.log1p([window(cc, t, -6, -1, col) for cc, t in zip(s.country_code, s.report_month)])
    s["iso3"] = s.country_code
    s["round"] = s.report_month.astype(str)
    for k in ["3", "4"]:
        s[f"surp{k}"] = s[f"s{k}_ML2"] - s[f"s{k}_CS"]
    s = s.sort_values(["country_code", "report_month"])
    g = s.groupby("country_code")
    for v in ["s3_CS", "s4_CS", "s3_ML2", "s4_ML2", "f_all", "f_food"]:
        s[f"d_{v}"] = s[v] - g[v].shift()
    return s


def main():
    s = panel()
    s.to_csv(TAB / "aid_response_panel.csv", index=False)
    print(len(s), "country-rounds,", s.country_code.nunique(), "countries")
    rows = []
    for col in ["all", "food"]:
        y, lag = f"f_{col}", f"f_{col}_lag"
        for k in ["3", "4"]:
            specs = {
                "current only": [f"s{k}_CS"],
                "near-term forecast only": [f"s{k}_ML1"],
                "medium-term forecast only": [f"s{k}_ML2"],
                "current + medium-term forecast": [f"s{k}_CS", f"s{k}_ML2"],
                "current + forecast surprise": [f"s{k}_CS", f"surp{k}"],
            }
            for lab, xs in specs.items():
                for fes, felab in [(["iso3", "round"], "country + round FE"), (["round"], "round FE only")]:
                    r, n, G = DID.fe_ols(s, y, xs + [lag], fes)
                    for x in xs:
                        rows.append({"funding": col, "phase": f"{k}+", "spec": lab, "fe": felab, "term": x,
                                     "coef": r.coef[x], "se": r.se[x], "n": n, "countries": G})
            # first differences
            r, n, G = DID.fe_ols(s, f"d_f_{col}", [f"d_s{k}_CS", f"d_s{k}_ML2"], ["round"])
            for x in [f"d_s{k}_CS", f"d_s{k}_ML2"]:
                rows.append({"funding": col, "phase": f"{k}+", "spec": "first differences", "fe": "round FE",
                             "term": x, "coef": r.coef[x], "se": r.se[x], "n": n, "countries": G})
    R = pd.DataFrame(rows)
    R["t"] = R.coef / R.se
    # interpret: effect of a 10 percentage point rise in the share of areas, in % funding
    R["pct_per_10pp"] = 100 * (np.exp(0.1 * R.coef) - 1)
    R.to_csv(TAB / "aid_response.csv", index=False)
    pd.set_option("display.width", 230)
    print(R[R.fe != "round FE only"].round(3).to_string())
    print(R[(R.fe == "round FE only")].round(3).to_string())
    figure(R)
    P = pooled(s)
    figure_pooled(P)


SPECS = [("pooled, no controls", ["one"], False), ("+ time FE (map date)", ["round"], False),
         ("+ prior 6-month funding", ["round"], True), ("+ country FE (within-country)", ["iso3", "round"], True)]


def pooled(s):
    """Same regressions, adding controls step by step from a pooled cross-country regression."""
    s = s.assign(one="x")
    rows = []
    for col in ["all", "food"]:
        for k in ["3", "4"]:
            for vars_, xs in [("alone", [f"s{k}_CS"]), ("alone", [f"s{k}_ML2"]), ("together", [f"s{k}_CS", f"s{k}_ML2"])]:
                for lab, fes, lag in SPECS:
                    r, n, G = DID.fe_ols(s, f"f_{col}", xs + ([f"f_{col}_lag"] if lag else []), fes)
                    for t in xs:
                        b, se = r.coef[t], r.se[t]
                        rows.append({"funding": col, "phase": f"{k}+", "vars": vars_,
                                     "term": "forecast" if "ML2" in t else "current", "spec": lab, "coef": b, "se": se,
                                     "pct": 100 * (np.exp(0.1 * b) - 1), "lo": 100 * (np.exp(0.1 * (b - 1.96 * se)) - 1),
                                     "hi": 100 * (np.exp(0.1 * (b + 1.96 * se)) - 1), "n": n, "countries": G})
    P = pd.DataFrame(rows)
    P.to_csv(TAB / "aid_response_pooled.csv", index=False)
    return P


def figure_pooled(P):
    cols = ["#9ecae1", "#4292c6", "#2171b5", "#08306b"]
    rows = [("3+", "alone", "current", "Crisis+ on the current map"),
            ("3+", "alone", "forecast", "Crisis+ in the forecast"),
            ("4+", "alone", "current", "Emergency+ on the current map"),
            ("4+", "alone", "forecast", "Emergency+ in the forecast"),
            ("3+", "together", "current", "Crisis+: current map"),
            ("3+", "together", "forecast", "Crisis+: forecast"),
            ("4+", "together", "current", "Emergency+: current map"),
            ("4+", "together", "forecast", "Emergency+: forecast")]
    fig, ax = plt.subplots(1, 2, figsize=(14, 7), sharey=True)
    for a, col, title in [(ax[0], "all", "A. All humanitarian funding"),
                          (ax[1], "food", "B. Food security and nutrition funding")]:
        ypos = []
        for i, (ph, v, t, lab) in enumerate(rows):
            y0 = len(rows) - i + (0 if i < 4 else -0.6)
            ypos.append((y0, lab))
            for j, (spec, _, _) in enumerate(SPECS):
                r = P[(P.funding == col) & (P.phase == ph) & (P.vars == v) & (P.term == t) & (P.spec == spec)].iloc[0]
                yy = y0 + 0.27 - 0.18 * j
                a.errorbar(1 + r.pct / 100, yy, xerr=[[(r.pct - r.lo) / 100], [(r.hi - r.pct) / 100]], fmt="o",
                           color=cols[j], ms=4, capsize=2, lw=1.2, label=spec if i == 0 else None)
        a.set_xscale("log")
        ticks = [0.8, 1, 1.25, 1.5, 2, 3, 4]
        a.set_xticks(ticks, [f"{100 * (t - 1):+.0f}%" if t != 1 else "0" for t in ticks])
        a.minorticks_off()
        a.axvline(1, color="#999", lw=0.8)
        a.axhline(len(rows) - 3.8, color="#ccc", lw=0.8)
        a.set_yticks([p for p, _ in ypos], [l for _, l in ypos])
        a.text(0.99, (len(rows) - 0.2 - 0.5) / (len(rows) + 0.6), "", transform=a.transAxes)
        a.set_xlabel("Change in funding committed over the next 6 months\nper 10-point rise in the share of the country's areas at that phase (log scale)")
        a.set_title(title, loc="left", fontweight="bold", fontsize=10.5)
    ax[0].text(-0.02, (len(rows) + 0.5), "Each measure alone", fontweight="bold", fontsize=9, ha="right",
               transform=ax[0].get_yaxis_transform())
    ax[0].text(-0.02, (len(rows) - 3.6), "Current map and forecast together", fontweight="bold", fontsize=9,
               ha="right", transform=ax[0].get_yaxis_transform())
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=8.5, frameon=False, bbox_to_anchor=(0.55, 0.065),
               title="Controls, added cumulatively (top to bottom within each cluster)", title_fontsize=8.5)
    fig.suptitle("Humanitarian funding follows FEWS NET's maps across countries, and its forecasts within them",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0.14, 1, 0.95))
    fig.text(0.01, 0.01, textwrap.fill(
        "Country x FEWS NET map round panel, 37 countries, 2011-2024. Funding: humanitarian commitments in OCHA's "
        "Financial Tracking Service in the 6 months after the map (log). Shares: unweighted share of the country's "
        "FEWS NET areas at the phase on the current-situation map, or in the medium-term (4-8 month) forecast issued "
        "with it. Controls added top to bottom in each cluster: none; time fixed effects, one per map date shared by all countries (global funding swings); "
        "funding in the 6 months before the map; country fixed effects (each country's usual aid level). 95% "
        "intervals clustered by country.", 220), fontsize=7.5, color="#555")
    fig.savefig(FIG / "aid_response_pooled.pdf")
    fig.savefig(FIG / "aid_response_pooled.png", dpi=150)


def figure(R):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for a, col, title in [(ax[0], "all", "A. All humanitarian funding"),
                          (ax[1], "food", "B. Food security and nutrition funding")]:
        rows = []
        for k in ["3", "4"]:
            for spec, term, lab in [("current only", f"s{k}_CS", "Current map, alone"),
                                    ("medium-term forecast only", f"s{k}_ML2", "Forecast (4-8 months), alone"),
                                    ("current + medium-term forecast", f"s{k}_CS", "Current map, with forecast"),
                                    ("current + medium-term forecast", f"s{k}_ML2", "Forecast, with current map")]:
                r = R[(R.funding == col) & (R.phase == f"{k}+") & (R.spec == spec) & (R.term == term)
                      & (R.fe == "country + round FE")].iloc[0]
                rows.append((f"Phase {k}+: {lab}", r.pct_per_10pp, 100 * 0.1 * 1.96 * r.se))
        y = np.arange(len(rows))[::-1]
        for yy, (lab, v, ci) in zip(y, rows):
            c = "#1f4e79" if "Phase 3" in lab else "#c0392b"
            a.errorbar(v, yy, xerr=ci, fmt="o", color=c, capsize=3)
        a.set_yticks(y, [r[0] for r in rows], fontsize=8.5)
        a.axvline(0, color="#999", lw=0.8)
        a.set_xlabel("% change in funding committed over the next 6 months\nper 10-point rise in the share of the country's areas at that phase")
        a.set_title(title, loc="left", fontweight="bold", fontsize=10.5)
    fig.suptitle("Does humanitarian funding follow FEWS NET's maps? Within-country, 2011-2024", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.text(0.01, 0.01, textwrap.fill(
        "Country x FEWS NET map round panel. Funding: humanitarian commitments recorded by OCHA's Financial Tracking "
        "Service in the 6 months after the map, log. Controls: funding in the 6 months before, country and map-round "
        "fixed effects (each country's usual aid level and global funding swings). Shares are unweighted counts of "
        "FEWS NET areas. 95% intervals (approximate, linearised) clustered by country.", 210), fontsize=7.5, color="#555")
    fig.savefig(FIG / "aid_response.pdf")
    fig.savefig(FIG / "aid_response.png", dpi=150)


if __name__ == "__main__":
    main()
