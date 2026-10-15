"""Somalia: a more proximate outcome for the cash first stage -- current food insecurity.

Outcome: share of each district's population in IPC Phase 3+ (official IPC acute food insecurity,
current classification; areas summed to districts as in 70), rounds 2019-2026. The Aug 2025 and
Jan 2026 rounds come after six or more months of reduced cash; the Feb 2025 round describes
Jan-Mar 2025, when the cut had barely reached households, and is shown separately.

Same instruments and endogenous variables as 71 (district level, 15+ region clusters):
  Z: aid dependence index (2024), US-funded share of partners (2024)
  X: cash lost per resident; cash recipients lost per 100 residents; proportional cash loss
Model: share3[d,r] = district FE + round FE + beta * X[d] x post[r], instrumented by Z[d] x post[r];
post = Aug 2025 and Jan 2026 (Feb 2025 dropped from the IV sample). Event study by round.

Caveat: IPC classifications are analyst judgments that combine survey evidence with assumptions,
account for assistance received, and are sticky between rounds.

Outputs: output/tables/som_ipc_*.csv, output/figures/som_ipc_event.pdf, output/us_cut_memo/numbers_ipc.tex
"""
import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
TAB, FIG = ROOT / "output" / "tables", ROOT / "output" / "figures"
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M70 = load("m70", "70_somalia_need_response.py")
M71 = load("m71", "71_somalia_first_stage.py")
POST = ["2025-08", "2026-01"]


def panel():
    ipc = M70.ipc_rounds()
    ipc = ipc[(ipc.month >= "2019-01") & (ipc.month <= "2026-01")]
    # keep rounds that cover most districts (2021-08..2022-05 rounds were region aggregates)
    cov = ipc.groupby("month").dist.nunique()
    ipc = ipc[ipc.month.isin(cov[cov >= 60].index)]
    X = pd.read_csv(TAB / "som_fs_districts.csv", index_col=0)
    d = ipc.merge(X[["cash_abs", "cash_log", "reach_abs", "index", "E_pred"]], left_on="dist", right_index=True)
    d["region"] = d.dist.str[:4]
    d["post"] = d.month.isin(POST).astype(float)
    d["share3"] = 100 * d.share3          # percentage points
    d["share4"] = 100 * d.p4 / d.population
    return d


def demean2(v, a, b):
    """Two-way within transformation (district, round) by alternating projections."""
    v = v.astype(float).copy()
    for _ in range(200):
        v0 = v.copy()
        v = v - v.groupby(a).transform("mean")
        v = v - v.groupby(b).transform("mean")
        if np.max(np.abs(v - v0)) < 1e-10:
            break
    return v


def iv2(d, y, x, z):
    d = d.dropna(subset=[y, x, z]).copy()
    a, b, g = d.dist, d.month, d.region.values
    yt = demean2(d[y], a, b).values
    xt = demean2(d[x] * d.post, a, b).values
    zt = demean2(d[z] * d.post, a, b).values
    G, n = len(np.unique(g)), len(d)
    adj = G / (G - 1)

    def ols(u, v):
        bb = (v @ u) / (v @ v)
        e = u - bb * v
        s = sum((v[g == q] @ e[g == q]) ** 2 for q in np.unique(g))
        return bb, np.sqrt(s / (v @ v) ** 2 * adj)
    pi, spi = ols(xt, zt)
    rho, srho = ols(yt, zt)
    beta = rho / pi
    e = yt - beta * xt
    se = np.sqrt(sum((zt[g == q] @ e[g == q]) ** 2 for q in np.unique(g)) / (zt @ xt) ** 2 * adj)
    crit = stats.f.ppf(0.95, 1, G - 1)
    span = max(40 * se, 4 * abs(beta), 2.0)
    grid = np.linspace(beta - span, beta + span, 4001)
    acc = []
    for b0 in grid:
        c, sc = ols(yt - b0 * xt, zt)
        if (c / sc) ** 2 < crit:
            acc.append(b0)
    bounded = bool(acc) and acc[0] > grid[0] and acc[-1] < grid[-1]
    bo, sbo = ols(yt, xt)
    xm = float(d.loc[d.post == 1].drop_duplicates("dist")[x].mean())
    return dict(y=y, x=x, z=z, n=n, districts=d.dist.nunique(), clusters=G, F=(pi / spi) ** 2, pi=pi,
                rho=rho, rho_se=srho, rho_p=2 * stats.t.sf(abs(rho / srho), G - 1), beta=beta, se=se,
                ar_lo=min(acc) if bounded else np.nan, ar_hi=max(acc) if bounded else np.nan, ols=bo, ols_se=sbo,
                x_mean=xm, ymean_pre=float(d.loc[d.post == 0, y].mean()))


def event(d, y, z):
    d = d.dropna(subset=[y, z]).copy()
    rounds = sorted(d.month.unique())
    ref = "2024-08"
    cols = [r for r in rounds if r != ref]
    Z = pd.DataFrame({r: d[z] * (d.month == r) for r in cols}, index=d.index)
    yt = demean2(d[y], d.dist, d.month).values
    Zt = np.column_stack([demean2(Z[r], d.dist, d.month).values for r in cols])
    b, V = M71.cl_ols(yt, Zt, d.region.values)
    sd = d.drop_duplicates("dist")[z].std()
    out = pd.DataFrame({"round": cols, "b_sd": b * sd, "se_sd": np.sqrt(np.diag(V)) * sd})
    out = pd.concat([out, pd.DataFrame([{"round": ref, "b_sd": 0.0, "se_sd": 0.0}])]).sort_values("round")
    out["z"], out["y"] = z, y
    return out


def main():
    d = panel()
    iv_d = d[d.month != "2025-02"]
    R = pd.DataFrame([iv2(iv_d, y, x, z) for y in ["share3", "share4"]
                      for x, z in [("reach_abs", "index"), ("cash_abs", "index"), ("cash_log", "E_pred")]])
    R.to_csv(TAB / "som_ipc_iv.csv", index=False)
    E = pd.concat([event(d, "share3", z) for z in ["index", "E_pred"]])
    E.to_csv(TAB / "som_ipc_event.csv", index=False)
    figure(E)
    write_numbers(R, E, d)
    pd.set_option("display.width", 220)
    print(d.groupby("month").agg(districts=("dist", "nunique"), share3=("share3", "mean")).round(1).T.to_string())
    print(R.round(3).to_string())
    print(E.round(2).to_string())


def figure(E):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2), sharey=True)
    for ax, (z, lab, col) in zip(axes, [("index", "Aid dependence", ORANGE), ("E_pred", "US reliance", BLUE)]):
        e = E[E.z == z]
        x = np.arange(len(e))
        ax.errorbar(x, e.b_sd, yerr=1.96 * e.se_sd, fmt="o", color=col, ms=4, lw=1.2)
        ax.axhline(0, color=GREY, lw=0.8)
        ref = list(e["round"]).index("2025-02") - 0.5
        ax.axvline(ref, color=GREY, ls=":", lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([r[2:4] + ("F" if r[5:] in ("01", "02") else "A") for r in e["round"]], fontsize=7, rotation=90)
        ax.set_title(lab, fontsize=9.5)
    axes[0].set_ylabel("Phase 3+ share (pp) per s.d.\nrelative to Aug 2024")
    fig.tight_layout()
    fig.savefig(FIG / "som_ipc_event.pdf")
    plt.close(fig)


def write_numbers(R, E, d):
    M = {}
    f2 = lambda v: f"{v:.2f}"
    f1 = lambda v: f"{v:.1f}"
    xn = {"reach_abs": "Reach", "cash_abs": "Abs", "cash_log": "Log"}
    yn = {"share3": "Pthree", "share4": "Pfour"}
    for r in R.itertuples():
        t = xn[r.x] + yn[r.y]
        sc = 10 if r.x == "cash_abs" else 1
        M[f"ipF{t}"], M[f"ipRho{t}"], M[f"ipRhoP{t}"] = f1(r.F), f2(r.rho), f2(r.rho_p)
        M[f"ipB{t}"], M[f"ipSe{t}"] = f2(r.beta * sc), f2(r.se * sc)
        M[f"ipLo{t}"] = f2(r.ar_lo * sc) if not np.isnan(r.ar_lo) else "$-\\infty$"
        M[f"ipHi{t}"] = f2(r.ar_hi * sc) if not np.isnan(r.ar_hi) else "$\\infty$"
        M[f"ipAtMean{t}"] = f1(r.beta * r.x_mean)
        M[f"ipAtMeanLo{t}"] = f1(r.ar_lo * r.x_mean) if not np.isnan(r.ar_lo) else "$-\\infty$"
        M[f"ipAtMeanHi{t}"] = f1(r.ar_hi * r.x_mean) if not np.isnan(r.ar_hi) else "$\\infty$"
        M[f"ipOls{t}"] = f2(r.ols * sc)
        M[f"ipYmean{t}"] = f1(r.ymean_pre)
        M[f"ipN{t}"] = r.districts
    for r in E.itertuples():
        t = ("Idx" if r.z == "index" else "Us") + r.round.replace("-", "")[2:].replace("0", "o").replace("1", "i").replace(
            "2", "t").replace("4", "f").replace("5", "v").replace("6", "s").replace("8", "g").replace("9", "n").replace("3", "h").replace("7", "e")
        M[f"ie{t}"], M[f"ieSe{t}"] = f2(r.b_sd), f2(r.se_sd)
    m = d.groupby("month").share3.mean()
    M["ipNatAugTfour"], M["ipNatAugTfive"], M["ipNatJanTsix"] = f1(m["2024-08"]), f1(m["2025-08"]), f1(m["2026-01"])
    (ROOT / "output" / "us_cut_memo" / "numbers_ipc.tex").write_text(
        "% generated by code/72_somalia_ipc_outcome.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))


if __name__ == "__main__":
    main()
