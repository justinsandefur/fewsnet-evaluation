"""First-pass test of the missed-warning design: does a local drought raise
food insecurity less when FEWS NET is covering the country?

  y[a,t] = b * shock[a,t] + d * shock[a,t] x covered[c,t] + area FE + country x month FE + e

y is the share of the area's population in Phase 3+ (also Phase 4+ and the
Phase 3+ indicator), from the Cadre Harmonise / IPC (independent of FEWS NET).
Country x month fixed effects absorb everything national, including whether
the country is covered and how much aid it receives. Standard errors are
clustered by country. Variants:
  (2) + country-specific shock slopes: d identified only from countries whose
      coverage changed
  (3) Cadre Harmonise only
  (4) continuous shock (12-month rainfall z-score, sign flipped so that higher
      = drier)
Event study: shock effect by year relative to coverage switches.

Outputs: output/tables/slope_did.csv, output/figures/slope_did_eventstudy.pdf
"""
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"


def within(d, cols, fes, iters=500, tol=1e-10):
    w = d[cols].astype(float).copy()
    for _ in range(iters):
        old = w.values.copy()
        for fe in fes:
            w = w - w.groupby(d[fe].values).transform("mean")
        if np.nanmax(np.abs(w.values - old)) < tol:
            break
    return w


def fe_ols(d, y, xs, fes, cluster="iso3"):
    d = d.dropna(subset=[y] + xs).copy()
    # drop singletons in each fixed effect (they carry no information)
    for fe in fes:
        d = d[d.groupby(fe)[y].transform("size") > 1]
    w = within(d, [y] + xs, fes)
    X, Y = w[xs].values, w[y].values
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ Y
    u = Y - X @ b
    meat = np.zeros((len(xs), len(xs)))
    groups = d[cluster].values
    for g in np.unique(groups):
        i = groups == g
        s = X[i].T @ u[i]
        meat += np.outer(s, s)
    G = len(np.unique(groups))
    V = XtXi @ meat @ XtXi * G / (G - 1)
    return pd.DataFrame({"coef": b, "se": np.sqrt(np.diag(V))}, index=xs), len(d), G


def main():
    p = pd.read_parquet(INP / "panel" / "analysis_panel.parquet")
    p = p.dropna(subset=["rain_z12"])
    p["dry"] = -p.rain_z12                        # higher = drier
    p["covd"] = p.covered.astype(float)
    p["drought_x_cov"] = p.drought * p.covd
    p["dry_x_cov"] = p.dry * p.covd
    p["phase3"] = (p.phase >= 3).astype(float)
    p["cm"] = p.iso3 + "_" + p.month.astype(str)
    sw = p.groupby("iso3").covd.agg(lambda x: x.nunique() > 1)
    p["switcher"] = p.iso3.map(sw)
    rows = []
    def run(label, d, y, shock, inter, extra_fe=None):
        xs = [shock, inter]
        fes = ["key", "cm"]
        if extra_fe:
            # country-specific shock slopes: partial out shock x country dummies
            dd = d.copy()
            for c in dd.iso3.unique():
                dd[f"s_{c}"] = dd[shock] * (dd.iso3 == c)
            cs = [f"s_{c}" for c in dd.iso3.unique()]
            res, n, G = fe_ols(dd, y, [inter] + cs, fes)
            res = res.loc[[inter]]
        else:
            res, n, G = fe_ols(d, y, xs, fes)
        for t, r in res.iterrows():
            rows.append({"spec": label, "outcome": y, "term": t, "coef": r.coef, "se": r.se,
                         "t": r.coef / r.se, "n": n, "countries": G})
    run("(1) all, drought", p, "share3", "drought", "drought_x_cov")
    run("(2) all, drought, country-specific slopes", p, "share3", "drought", "drought_x_cov", extra_fe=True)
    run("(3) Cadre Harmonise only", p[p.source == "CH"], "share3", "drought", "drought_x_cov")
    run("(4) all, continuous dryness", p, "share3", "dry", "dry_x_cov")
    run("(5) all, Phase 3+ indicator", p, "phase3", "drought", "drought_x_cov")
    run("(6) all, share Phase 4+", p, "share4", "drought", "drought_x_cov")
    run("(7) Cadre Harmonise only, country-specific slopes", p[p.source == "CH"], "share3", "drought",
        "drought_x_cov", extra_fe=True)
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "slope_did.csv", index=False)
    print(r.round(4).to_string())
    k = {"n_rows": int(len(p)), "drought_rate": float(p.drought.mean()), "share_covered": float(p.covd.mean()),
         "switch_countries": sorted(sw[sw].index.tolist()), "mean_share3": float(p.share3.mean())}
    (TAB / "slope_did_key.json").write_text(json.dumps(k, indent=1))
    print(k)

    # event study of the drought effect around switches (switching countries only)
    H = pd.read_csv(TAB / "coverage_switches_maps.csv")
    H = H[H.year <= 2026]
    q = p[p.switcher].copy()
    first = H.groupby("iso3").year.min()
    q["rel"] = q.month.dt.year - q.iso3.map(first)
    q["onfirst"] = q.iso3.map(H.sort_values("year").groupby("iso3").direction.first())
    q = q.dropna(subset=["rel"])
    q["rel"] = q.rel.clip(-4, 4).astype(int)
    # sign: exposure = 1 when the switch turned coverage on, -1 when off
    bins = [b for b in range(-4, 5) if b != -1]
    for b in bins:
        q[f"dr_{b + 10}"] = q.drought * (q.rel == b)
    xs = ["drought"] + [f"dr_{b + 10}" for b in bins if q[f"dr_{b + 10}"].abs().sum() > 0]
    res, n, G = fe_ols(q, "share3", xs, ["key", "cm"])
    es = res.drop(index="drought").reset_index().rename(columns={"index": "term"})
    es["rel"] = es.term.str[3:].astype(int) - 10
    es = pd.concat([es, pd.DataFrame({"rel": [-1], "coef": [0.0], "se": [0.0]})]).sort_values("rel")
    es.to_csv(TAB / "slope_did_eventstudy.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.errorbar(es.rel, es.coef, yerr=1.96 * es.se, fmt="o-", color="#1f4e79", capsize=3)
    ax.axhline(0, color="#999", lw=0.8)
    ax.axvline(-0.5, color="#999", lw=0.8, ls="--")
    ax.set_xlabel("Years relative to the country's first FEWS NET coverage switch (endpoints pooled)")
    ax.set_ylabel("Extra effect of a local drought on the\nshare of the population in Crisis or worse")
    ax.set_title("Does the damage a drought does change around FEWS NET coverage switches?", loc="left",
                 fontweight="bold", fontsize=10.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.text(0.01, 0.01, textwrap.fill(
        f"Switching countries only ({G} countries). Drought = 12-month rainfall more than one standard deviation below "
        "the 1981-2010 norm (CHIRPS). Area and country x analysis-month fixed effects; 95% intervals clustered by "
        "country. Relative to the year before the first switch.", 130), fontsize=8, color="#555")
    fig.savefig(FIG / "slope_did_eventstudy.pdf")


if __name__ == "__main__":
    main()
