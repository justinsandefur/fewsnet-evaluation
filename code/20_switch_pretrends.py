"""Are FEWS NET's entries and exits exogenous? Event studies around the real
coverage switches before 2025 (18_coverage_history.py).

Stacked difference-in-differences: for each switch (country c, year Y), take
c's years Y-4..Y+3 and the same calendar years for countries whose coverage
never changed, with event-specific country and year fixed effects. Estimated
separately for entries and exits; year Y-1 omitted; errors clustered by country.

Outcomes, all measured independently of FEWS NET:
  log humanitarian funding (UN Financial Tracking Service)
  log(1 + conflict events) (ACLED, country-year)
  log(1 + people affected by natural disasters) (EM-DAT)
  share of population in Crisis or worse (Global Report on Food Crises, 2016 on)

Outputs: output/tables/switch_eventstudy.csv, output/figures/switch_eventstudy.pdf
"""
import importlib.util
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
spec = importlib.util.spec_from_file_location("iv", ROOT / "code" / "15_instrument.py")
IV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IV)
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 10.5, "axes.titleweight": "bold",
                     "axes.titlelocation": "left"})
WIN = range(-4, 4)


def outcomes():
    codes, emdat, f, region = IV.load()
    f["year"] = f.month.dt.year
    aid = np.log1p(f.groupby(["iso3", "year"]).amount_usd.sum() / 1e6).rename("ln_aid")
    a = pd.read_excel(INP / "acled" / "number_of_political_violence_events_by_country-year_as-of-25Sep2026.xlsx")
    name2iso = {**dict(zip(codes.preferred_name, codes.iso3166a3)), **dict(zip(codes.iso_en_name, codes.iso3166a3)),
                **dict(zip(emdat.Country, emdat.ISO)), **IV.FIX_ISO, "Ivory Coast": "CIV",
                "Democratic Republic of Congo": "COD", "Republic of Congo": "COG", "eSwatini": "SWZ"}
    a["iso3"] = a.COUNTRY.map(name2iso)
    first = a.groupby("iso3").YEAR.min()
    conf = np.log1p(a.groupby(["iso3", "YEAR"]).EVENTS.sum()).rename("ln_conflict")
    conf.index.names = ["iso3", "year"]
    e = emdat[emdat["Disaster Group"] == "Natural"]
    dis = np.log1p(e.groupby(["ISO", "Start Year"])["Total Affected"].sum()).rename("ln_affected")
    dis.index.names = ["iso3", "year"]
    g = pd.read_csv(TAB / "grfc_country_years.csv")
    gr = pd.read_excel(INP / "ipc" / "grfc_afi_database_2016-2025_september_update.xlsx")
    gr.columns = [c.strip() for c in gr.columns]
    pop = gr.groupby(["ISO Code 3", "Year of reference"])["Total country population"].max()
    g["pop"] = [pop.get((i, y), np.nan) for i, y in zip(g.iso3, g.year)]
    p3 = (g.set_index(["iso3", "year"]).p3 / g.set_index(["iso3", "year"])["pop"]).rename("p3_share")
    return aid, conf, first, dis, p3


def stack(R, H, y, years, never, first_obs=None):
    rows = []
    for k, ev in enumerate(R.itertuples()):
        yrs = [ev.year + r for r in WIN]
        for c in [ev.iso3] + never:
            for yy in yrs:
                if yy not in years:
                    continue
                v = y.get((c, yy), np.nan)
                if first_obs is not None and yy < first_obs.get(c, 9999):
                    v = np.nan
                rows.append({"ev": k, "iso3": c, "year": yy, "y": v, "treated": int(c == ev.iso3),
                             "rel": yy - ev.year if c == ev.iso3 else -99})
    d = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan).dropna(subset=["y"])
    d["ec"] = d.ev.astype(str) + "_" + d.iso3
    d["ey"] = d.ev.astype(str) + "_" + d.year.astype(str)
    for r in WIN:
        if r != -1:
            d[f"r{r + 10}"] = ((d.rel == r) & (d.treated == 1)).astype(int)
    terms = [f"r{r + 10}" for r in WIN if r != -1]
    terms = [t for t in terms if d[t].sum() > 0]
    # two-way within transformation (event-country and event-year effects)
    cols = ["y"] + terms
    w = d[cols].astype(float).copy()
    for _ in range(200):
        old = w.values.copy()
        for fe in ["ec", "ey"]:
            w = w - w.groupby(d[fe]).transform("mean")
        if np.max(np.abs(w.values - old)) < 1e-10:
            break
    X, Y = w[terms].values, w["y"].values
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ Y
    u = Y - X @ b
    meat = np.zeros((len(terms), len(terms)))
    for _, idx in d.reset_index(drop=True).groupby("iso3").indices.items():
        sc = X[idx].T @ u[idx]
        meat += np.outer(sc, sc)
    G = d.iso3.nunique()
    se = np.sqrt(np.diag(XtXi @ meat @ XtXi) * G / (G - 1))
    out = [{"rel": int(t[1:]) - 10, "coef": bb, "se": ss} for t, bb, ss in zip(terms, b, se)]
    out.append({"rel": -1, "coef": 0.0, "se": 0.0})
    return pd.DataFrame(out).sort_values("rel"), d.loc[d.treated == 1].ev.nunique()


def main():
    R = pd.read_csv(TAB / "coverage_switches_maps.csv")
    R = R[(R.year >= 2010) & (R.year <= 2024) & (R.iso3 != "-99")]
    H = pd.read_csv(TAB / "coverage_history.csv")
    switchers = set(R.iso3)
    covered_ever = set(H[H.covered].iso3)
    aid, conf, first, dis, p3 = outcomes()
    # never-switching comparison group: countries never covered, plus countries
    # covered throughout 2009-2024
    always = set(H[(H.year.between(2009, 2024))].groupby("iso3").covered.all().loc[lambda s: s].index)
    pool = sorted((set(aid.index.get_level_values(0)) - covered_ever) | always)
    pool = [c for c in pool if c not in switchers]
    res = []
    specs = [("ln_aid", aid, range(2006, 2025), None, "Log humanitarian funding"),
             ("ln_conflict", conf, range(2006, 2025), first, "Log(1 + conflict events)"),
             ("ln_affected", dis, range(2006, 2025), None, "Log(1 + people affected by disasters)"),
             ("p3_share", p3, range(2016, 2026), None, "Share of population in Crisis or worse")]
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.2), sharex=True)
    for j, (name, y, yrs, fo, lab) in enumerate(specs):
        for i, (direction, col) in enumerate([("on", "#1f4e79"), ("off", "#c55a11")]):
            ev = R[R.direction == direction]
            es, n = stack(ev, H, y, set(yrs), pool, fo)
            es["outcome"], es["direction"], es["events"] = name, direction, n
            res.append(es)
            ax = axes[i, j]
            ax.errorbar(es.rel, es.coef, yerr=1.96 * es.se, fmt="o-", color=col, capsize=2, ms=4)
            ax.axhline(0, color="#999", lw=0.8)
            ax.axvline(-0.5, color="#999", lw=0.8, ls="--")
            ax.set_title(f"{lab}\n{'FEWS NET enters' if direction == 'on' else 'FEWS NET leaves'} ({n} events)",
                         fontsize=9)
            if i == 1:
                ax.set_xlabel("Years relative to the switch")
    fig.suptitle("Did anything else change when FEWS NET entered or left a country?", fontweight="bold",
                 x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.text(0.01, 0.01, textwrap.fill(
        "Stacked difference-in-differences around each real FEWS NET coverage switch, 2010-2024 (entries, top; exits, "
        "bottom), relative to countries whose coverage never changed. Year before the switch = 0. Bars: 95% intervals, "
        "clustered by country. Outcomes come from sources independent of FEWS NET: UN Financial Tracking Service, "
        "ACLED, EM-DAT, Global Report on Food Crises (2016 on).", 200), fontsize=8, color="#555")
    fig.savefig(FIG / "switch_eventstudy.pdf")
    out = pd.concat(res)
    out.to_csv(TAB / "switch_eventstudy.csv", index=False)
    pre = out[out.rel < -1].groupby(["outcome", "direction"]).apply(
        lambda g: pd.Series({"mean_pre": g.coef.mean(), "max_abs_t": (g.coef / g.se).abs().max()}))
    print(pre.round(3).to_string())
    post = out[out.rel >= 0].groupby(["outcome", "direction"]).coef.mean().round(3)
    print(post.to_string())
    print("comparison countries:", len(pool))


if __name__ == "__main__":
    main()
