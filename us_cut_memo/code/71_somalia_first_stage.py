"""Somalia: first stage, 2SLS and robustness for the 2025 aid cut (responds to an external review).

The question is framed as instrumental variables. Pre-cut exposure Z (aid dependence index, 2024;
US-funded share of partners, 2024) should predict a fall in aid actually delivered X, and X should
predict outcomes Y. Only then does a zero reduced form say something about the effect of losing aid.

X (district, then population-weighted to survey domains):
  cash_abs    cash and voucher transfers lost, US$ per resident, Jan-Jun 2025 vs Jan-Jun 2024
              (Cash Working Group 4W; 2024 district totals scaled to Jan-Jun with the national monthly
              series). Positive = loss. Jan-Jun 2025 is the window just before the Gu 2025 surveys.
  cash_log    minus the log change in cash per resident (proportional loss)
  reach_abs   cash recipients lost per 100 residents per month, same windows
Y: FSNAU survey outcomes (GAM primary). IV sample: 2015-2024 plus Gu 2025 (Deyr 2025 is excluded
because cash data end in June 2025). Model: y = domain FE + population-type x season FE + rain +
conflict + beta * X x Gu2025, instrumented by Z x Gu2025. Prices are left out of the IV controls
because the cut may itself move local prices.
Inference: cluster-robust by region (15 clusters); weak-instrument-robust Anderson-Rubin intervals
(critical values from F(l, G-1)).

Review checks: Gu and Deyr 2025 separately; exposure x 2024 food insecurity interaction; which
domains drop out after the cut; Section 4 without price controls; sensitivity to pre-trends
(linear exposure-specific trends, and a relative-magnitudes bound on the event study);
equivalence-style statement against a 1-point wasting target.

Outputs: output/tables/som_fs_*.csv, som_fs_key.json, output/figures/som_fs_*.pdf,
         output/us_cut_memo/numbers_fs.tex
"""
import importlib.util
import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
KEY = {}
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M68 = load("m68", "68_somalia_us_cut.py")
M69 = load("m69", "69_somalia_aid_dependence.py")


# ------------------------------------------------------------------ X by district
def district_x():
    D = pd.read_csv(TAB / "som_need_district_panel.csv")
    sc = json.loads((TAB / "som_need_key.json").read_text())["cash_h1_scale_2024"]
    w = D.pivot_table(index="dist", columns="year", values=["cash_usd", "cash_reached", "pop", "p3"])
    X = pd.DataFrame(index=w.index)
    X["pop"] = w[("pop", 2024)]
    X["cash24"] = w[("cash_usd", 2024)] * sc / X["pop"]
    X["cash25"] = w[("cash_usd", 2025)] / X["pop"]
    X["cash_abs"] = X.cash24 - X.cash25
    X["cash_log"] = -(np.log(X.cash25 + 0.05) - np.log(X.cash24 + 0.05))
    X["reach_abs"] = (w[("cash_reached", 2024)] * sc - w[("cash_reached", 2025)]) / X["pop"] / 6 * 100
    X["p3share24"] = w[("p3", 2024)] / X["pop"]
    us = pd.read_csv(TAB / "som_uscut_districts.csv", index_col=0)[["E_pred", "E_loss"]]
    dep = pd.read_csv(TAB / "som_aiddep_districts.csv", index_col=0)[["index"]]
    X = X.join(us).join(dep)
    X["region"] = X.index.str[:4]
    X.to_csv(TAB / "som_fs_districts.csv")
    return X


def cl_ols(y, X, g):
    """OLS with CR1 cluster-robust covariance. X: 2-D array incl. constant."""
    XtX = np.linalg.pinv(X.T @ X)
    b = XtX @ X.T @ y
    e = y - X @ b
    G = np.unique(g)
    n, k = X.shape
    meat = sum(np.outer(X[g == q].T @ e[g == q], X[g == q].T @ e[g == q]) for q in G)
    V = XtX @ meat @ XtX * len(G) / (len(G) - 1) * (n - 1) / (n - k)
    return b, V


def district_first_stage(X):
    rows = []
    for xv in ["cash_abs", "cash_log", "reach_abs"]:
        for z in ["index", "E_pred"]:
            for wt in [False, True]:
                d = X.dropna(subset=[xv, z])
                A = np.column_stack([np.ones(len(d)), d[z]])
                if wt:
                    s = np.sqrt(d["pop"].values / d["pop"].mean())
                    b, V = cl_ols(d[xv].values * s, A * s[:, None], d.region.values)
                else:
                    b, V = cl_ols(d[xv].values, A, d.region.values)
                rows.append(dict(x=xv, z=z, weighted=wt, b=b[1], se=np.sqrt(V[1, 1]), F=b[1] ** 2 / V[1, 1], n=len(d),
                                 z_sd=d[z].std(), x_mean=d[xv].mean()))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "som_fs_district_firststage.csv", index=False)
    return R


# ------------------------------------------------------------------ domain panel
def domain_panel(X):
    p = pd.read_parquet(INP / "panel" / "som_need_panel.parquet")
    q = M68.survey_panel()
    p = p.merge(q[["domain", "season_id", "dists"]], on=["domain", "season_id"], how="left")
    rows = []
    for r in p.drop_duplicates("domain").itertuples():
        w = pd.Series({k: v for k, v in json.loads(r.dists).items() if k not in (None, "null")})
        rec = {"domain": r.domain}
        for c in ["cash_abs", "cash_log", "reach_abs", "p3share24", "index", "E_pred"]:
            v = X[c].reindex(w.index)
            ok = v.notna()
            rec["x_" + c] = float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan
        rows.append(rec)
    p = p.merge(pd.DataFrame(rows), on="domain")
    p["gu25"] = ((p.year == 2025) & (p.season_type == "Gu")).astype(float)
    p["deyr25"] = ((p.year == 2025) & (p.season_type == "Deyr")).astype(float)
    p["gu26"] = ((p.year == 2026) & (p.season_type == "Gu")).astype(float)
    return p


def fe_matrix(d, controls):
    A = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
    A = A.join(pd.get_dummies(d.ptype + ":" + d.season_id, prefix="t", drop_first=True, dtype=float))
    for c in controls:
        A[c] = d[c]
    A.insert(0, "const", 1.0)
    return A.loc[:, A.std() > 0].assign(const=1.0).values


def partial(v, A):
    return v - A @ np.linalg.lstsq(A, v, rcond=None)[0]


def iv(d, y, x, zs, controls=("rain_z", "rain12_z", "log_fat"), post="gu25"):
    """2SLS of y on x*post instrumented by z*post, after partialling out FE and controls."""
    d = d.dropna(subset=[y, x] + list(zs) + list(controls)).copy()
    A = fe_matrix(d, controls)
    g = d.region.values
    yt = partial(d[y].values, A)
    xt = partial((d[x] * d[post]).values, A)
    Zt = np.column_stack([partial((d[z] * d[post]).values, A) for z in zs])
    n, G, l = len(d), len(np.unique(g)), len(zs)
    dof = A.shape[1] + 1
    # first stage
    pi = np.linalg.lstsq(Zt, xt, rcond=None)[0]
    ex = xt - Zt @ pi
    ZtZ = np.linalg.pinv(Zt.T @ Zt)
    meat = sum(np.outer(Zt[g == q].T @ ex[g == q], Zt[g == q].T @ ex[g == q]) for q in np.unique(g))
    Vpi = ZtZ @ meat @ ZtZ * G / (G - 1) * (n - 1) / (n - dof - l)
    F = float(pi @ np.linalg.pinv(Vpi) @ pi / l)
    # reduced form
    rho = np.linalg.lstsq(Zt, yt, rcond=None)[0]
    er = yt - Zt @ rho
    meat = sum(np.outer(Zt[g == q].T @ er[g == q], Zt[g == q].T @ er[g == q]) for q in np.unique(g))
    Vrho = ZtZ @ meat @ ZtZ * G / (G - 1) * (n - 1) / (n - dof - l)
    # 2SLS
    xh = Zt @ pi
    beta = float(xh @ yt / (xh @ xt))
    e = yt - beta * xt
    s = sum((xh[g == q] @ e[g == q]) ** 2 for q in np.unique(g))
    se = float(np.sqrt(s / (xh @ xt) ** 2 * G / (G - 1) * (n - 1) / (n - dof - 1)))
    # OLS of y on x*post (same partialling)
    bo = float(xt @ yt / (xt @ xt))
    eo = yt - bo * xt
    so = sum((xt[g == q] @ eo[g == q]) ** 2 for q in np.unique(g))
    seo = float(np.sqrt(so / (xt @ xt) ** 2 * G / (G - 1) * (n - 1) / (n - dof - 1)))
    # Anderson-Rubin set on a grid
    crit = stats.f.ppf(0.95, l, G - 1)

    def ar_stat(b0):
        u = yt - b0 * xt
        c = np.linalg.lstsq(Zt, u, rcond=None)[0]
        eu = u - Zt @ c
        mt = sum(np.outer(Zt[g == q].T @ eu[g == q], Zt[g == q].T @ eu[g == q]) for q in np.unique(g))
        Vc = ZtZ @ mt @ ZtZ * G / (G - 1) * (n - 1) / (n - dof - l)
        return float(c @ np.linalg.pinv(Vc) @ c / l)
    span = max(40 * abs(se), 4 * abs(beta), 2.0)
    grid = np.linspace(beta - span, beta + span, 2001)
    acc = [b0 for b0 in grid if ar_stat(b0) < crit]
    ar_lo, ar_hi = (min(acc), max(acc)) if acc else (np.nan, np.nan)
    bounded = bool(acc) and acc[0] > grid[0] and acc[-1] < grid[-1]
    # 90% AR interval for equivalence statements
    crit90 = stats.f.ppf(0.90, l, G - 1)
    acc90 = [b0 for b0 in grid if ar_stat(b0) < crit90]
    return dict(y=y, x=x, z="+".join(zs), n=n, post_n=int(d[post].sum()), clusters=G, F=F,
                pi=[float(v) for v in pi], rho=[float(v) for v in rho], rho_se=[float(np.sqrt(Vrho[i, i])) for i in range(l)],
                beta=beta, se=se, ols=bo, ols_se=seo, ar_lo=ar_lo, ar_hi=ar_hi, ar_bounded=bounded,
                ar90_lo=min(acc90) if acc90 else np.nan, ar90_hi=max(acc90) if acc90 else np.nan,
                x_mean_post=float(d.loc[d[post] == 1, x].mean()), x_sd_post=float(d.loc[d[post] == 1, x].std()))


# ------------------------------------------------------------------ review checks
def seasons_split(p):
    """Reduced form with separate Gu 2025 and Deyr 2025 terms."""
    rows = []
    for z in ["E_pred", "E_loss", "z_index", "x_cash_abs"]:
        for y in ["gam", "sam", "cdr"]:
            d = p.dropna(subset=[y, z]).copy()
            A = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
            A = A.join(pd.get_dummies(d.ptype + ":" + d.season_id, prefix="t", drop_first=True, dtype=float))
            A["gu"], A["deyr"], A["gu26"] = d[z] * d.gu25, d[z] * d.deyr25, d[z] * d.gu26
            for c in ["rain_z", "rain12_z", "log_fat"]:
                A[c] = d[c]
            A.insert(0, "const", 1.0)
            A = A.loc[:, A.std() > 0].assign(const=1.0)
            b, se, _ = M68.ols_cl(A, d[y].values, d.region.values)
            cols = list(A.columns)
            sd = d.drop_duplicates("domain")[z].std()
            for s in ["gu", "deyr", "gu26"]:
                if s not in cols:
                    continue
                j = cols.index(s)
                rows.append(dict(z=z, y=y, season=s, b=b[j], se=se[j], b_sd=b[j] * sd, se_sd=se[j] * sd,
                                 p_wild=M68.wild_p(A, d[y].values, d.region.values, s),
                                 n_post=int({"gu": d.gu25, "deyr": d.deyr25, "gu26": d.gu26}[s].sum())))
    return pd.DataFrame(rows)


def stress_interaction(p):
    """Exposure x post x 2024 food insecurity (standardised across domains)."""
    rows = []
    dom = p.drop_duplicates("domain")
    s = (p.x_p3share24 - dom.x_p3share24.mean()) / dom.x_p3share24.std()
    p = p.assign(stress=s)
    for z in ["E_pred", "z_index", "x_cash_abs"]:
        zz = (p[z] - dom[z].mean()) / dom[z].std()
        for y in ["gam", "sam"]:
            d = p.assign(zs=zz).dropna(subset=[y, "zs", "stress"]).copy()
            A = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
            A = A.join(pd.get_dummies(d.ptype + ":" + d.season_id, prefix="t", drop_first=True, dtype=float))
            A["z_post"], A["s_post"], A["zs_post"] = d.zs * d.post, d.stress * d.post, d.zs * d.stress * d.post
            for c in ["rain_z", "rain12_z", "log_fat"]:
                A[c] = d[c]
            A.insert(0, "const", 1.0)
            A = A.loc[:, A.std() > 0].assign(const=1.0)
            b, se, _ = M68.ols_cl(A, d[y].values, d.region.values)
            cols = list(A.columns)
            for c in ["z_post", "s_post", "zs_post"]:
                j = cols.index(c)
                rows.append(dict(z=z, y=y, term=c, b=b[j], se=se[j],
                                 p_wild=M68.wild_p(A, d[y].values, d.region.values, c) if c == "zs_post" else np.nan))
    return pd.DataFrame(rows)


def attrition(p):
    """Domains surveyed in 2024 but not in 2025: do they differ by exposure or prior trend?"""
    d24 = p[p.year == 2024].groupby("domain").gam.mean()
    d23 = p[p.year == 2023].groupby("domain").gam.mean()
    d25 = set(p[p.year == 2025].domain)
    dom = p.drop_duplicates("domain").set_index("domain")
    A = dom.loc[d24.index, ["E_pred", "E_loss", "z_index", "x_cash_abs", "ptype"]].copy()
    A["observed25"] = A.index.isin(d25)
    A["gam24"] = d24
    A["dgam_23_24"] = d24 - d23.reindex(d24.index)
    out = {"domains_2024": int(len(A)), "observed_2025": int(A.observed25.sum()),
           "missing_by_type": A[~A.observed25].ptype.value_counts().to_dict()}
    for c in ["E_pred", "E_loss", "z_index", "x_cash_abs", "gam24", "dgam_23_24"]:
        a, b = A[A.observed25][c].dropna(), A[~A.observed25][c].dropna()
        t = stats.ttest_ind(a, b, equal_var=False) if len(b) > 1 else None
        out[c] = dict(observed=float(a.mean()), missing=float(b.mean()) if len(b) else np.nan,
                      p=float(t.pvalue) if t is not None else np.nan)
    d26 = set(p[p.year == 2026].domain)
    A["observed26"] = A.index.isin(d26)
    out["observed_2026"] = int(A.observed26.sum())
    for c in ["E_pred", "z_index", "gam24", "dgam_23_24"]:
        out[c + "_26"] = dict(observed=float(A[A.observed26][c].mean()), missing=float(A[~A.observed26][c].mean()),
                              p=float(stats.ttest_ind(A[A.observed26][c].dropna(), A[~A.observed26][c].dropna(),
                                                      equal_var=False).pvalue))
    A.to_csv(TAB / "som_fs_attrition.csv")
    # balanced: domains with surveys in both 2024 and 2025
    bal = set(A[A.observed25].index)
    return out, bal


def did_simple(d, z, y, controls, trend=False):
    d = d.dropna(subset=[y, z]).copy()
    A = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
    A = A.join(pd.get_dummies(d.ptype + ":" + d.season_id, prefix="t", drop_first=True, dtype=float))
    A["treat"] = d[z] * d.post
    if trend:
        A["ztrend"] = d[z] * (d.year - 2024)
    for c in controls:
        A[c] = d[c]
    A.insert(0, "const", 1.0)
    A = A.loc[:, A.std() > 0].assign(const=1.0)
    b, se, _ = M68.ols_cl(A, d[y].values, d.region.values)
    j = list(A.columns).index("treat")
    return dict(b=b[j], se=se[j], p_wild=M68.wild_p(A, d[y].values, d.region.values, "treat"), n=len(d))


def event_rm(p, z, y="gam"):
    """Relative-magnitudes bound (Rambachan-Roth style, approximate): post effect allowed to deviate
    from parallel trends by up to Mbar times the largest change between consecutive pre-period event
    coefficients. Returns the 2025 coefficient, its s.e., the max pre-period change, and the
    breakdown Mbar at which the 95% interval would include zero (or, if it already does, would
    include a 1-point-per-s.d. effect)."""
    d = p.dropna(subset=[y, z]).copy()
    A = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
    A = A.join(pd.get_dummies(d.ptype + ":" + d.season_id, prefix="t", drop_first=True, dtype=float))
    yrs = [yy for yy in sorted(d.year.unique()) if yy != 2024]
    for yy in yrs:
        A[f"ev{yy}"] = d[z] * (d.year == yy)
    for c in ["rain_z", "rain12_z", "log_fat"]:
        A[c] = d[c]
    A.insert(0, "const", 1.0)
    A = A.loc[:, A.std() > 0].assign(const=1.0)
    b, se, _ = M68.ols_cl(A, d[y].values, d.region.values)
    cols = list(A.columns)
    ev = pd.Series({yy: b[cols.index(f"ev{yy}")] for yy in yrs if f"ev{yy}" in cols})
    ev[2024] = 0.0
    ev = ev.sort_index()
    pre = ev[ev.index <= 2024]
    maxd = float(pre.diff().abs().max())
    b25, s25 = ev[2025], se[cols.index("ev2025")]
    sd = d.drop_duplicates("domain")[z].std()
    out = dict(z=z, b25_sd=b25 * sd, se25_sd=s25 * sd, maxdiff_sd=maxd * sd)
    for M in [0.5, 1.0]:
        out[f"lo_M{M}"] = (b25 - 1.96 * s25 - M * maxd) * sd
        out[f"hi_M{M}"] = (b25 + 1.96 * s25 + M * maxd) * sd
    return out


def main():
    X = district_x()
    FS = district_first_stage(X)
    p = domain_panel(X)
    KEY["x_district"] = X[["cash24", "cash25", "cash_abs", "cash_log", "reach_abs"]].describe().round(2).to_dict()

    # 2SLS, Gu 2025
    pp = p[(p.deyr25 == 0) & (p.year <= 2025)]
    R = []
    for x in ["x_cash_abs", "x_reach_abs", "x_cash_log"]:
        for zs in [["x_index"], ["x_E_pred"], ["x_index", "x_E_pred"]]:
            for y in ["gam", "sam", "muac_gam", "cdr", "u5dr"]:
                R.append(iv(pp, y, x, zs))
    R = pd.DataFrame(R)
    R.to_csv(TAB / "som_fs_iv.csv", index=False)

    S = seasons_split(p)
    S.to_csv(TAB / "som_fs_seasons.csv", index=False)
    SI = stress_interaction(p)
    SI.to_csv(TAB / "som_fs_stress.csv", index=False)
    att, bal = attrition(p)
    KEY["attrition"] = att
    # balanced panel and no-price checks
    rows = []
    for z in ["E_pred", "E_loss", "z_index"]:
        rows.append(dict(z=z, spec="main (rain, conflict)", **did_simple(p, z, "gam", ["rain_z", "rain12_z", "log_fat"])))
        rows.append(dict(z=z, spec="with prices", **did_simple(p, z, "gam", M69.CTRL)))
        rows.append(dict(z=z, spec="balanced 2024-25 domains",
                         **did_simple(p[p.domain.isin(bal)], z, "gam", ["rain_z", "rain12_z", "log_fat"])))
        rows.append(dict(z=z, spec="exposure-specific linear trend",
                         **did_simple(p, z, "gam", ["rain_z", "rain12_z", "log_fat"], trend=True)))
    RB = pd.DataFrame(rows)
    sd = {z: p.drop_duplicates("domain")[z].std() for z in ["E_pred", "E_loss", "z_index"]}
    RB["b_sd"], RB["se_sd"] = RB.b * RB.z.map(sd), RB.se * RB.z.map(sd)
    RB.to_csv(TAB / "som_fs_robust.csv", index=False)
    RM = pd.DataFrame([event_rm(p, z) for z in ["E_pred", "E_loss", "z_index"]])
    RM.to_csv(TAB / "som_fs_relmag.csv", index=False)

    figures(X, R)
    (TAB / "som_fs_key.json").write_text(json.dumps(KEY, indent=1, default=float))
    write_numbers(FS, R, S, SI, RB, RM, X)
    pd.set_option("display.width", 240, "display.max_rows", 200, "display.max_columns", 30)
    print(FS.round(3).to_string())
    print(R[["y", "x", "z", "n", "post_n", "F", "rho", "beta", "se", "ols", "ar_lo", "ar_hi", "ar_bounded",
             "ar90_lo", "ar90_hi", "x_mean_post"]].round(3).to_string())
    print(S.round(3).to_string())
    print(SI.round(3).to_string())
    print(json.dumps(att, indent=1, default=float))
    print(RB.round(3).to_string())
    print(RM.round(3).to_string())


def figures(X, R):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    d = X.dropna(subset=["index", "cash_abs", "E_pred", "cash_log"])
    for ax, (z, x, zl, xl) in zip(axes, [("index", "cash_abs", "Aid dependence index, 2024", "Cash lost, $ per resident (Jan-Jun)"),
                                         ("E_pred", "cash_log", "US-funded share of partners, 2024",
                                          "Proportional cash loss (minus log change)")]):
        ax.scatter(d[z], d[x], s=np.clip(d["pop"] / 2e4, 6, 120), color=BLUE, alpha=0.5, lw=0)
        b = np.polyfit(d[z], d[x], 1)
        xs = np.linspace(d[z].min(), d[z].max(), 10)
        ax.plot(xs, b[0] * xs + b[1], color=ORANGE, lw=1.5)
        ax.axhline(0, color=GREY, lw=0.8)
        ax.set_xlabel(zl, fontsize=9)
        ax.set_ylabel(xl, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "som_fs_firststage.pdf")
    plt.close(fig)


def write_numbers(FS, R, S, SI, RB, RM, X):
    M = {}
    f1 = lambda v: f"{v:.1f}"
    f2 = lambda v: f"{v:.2f}"
    f0 = lambda v: f"{v:,.0f}"
    pc = lambda v: f"{100 * v:.0f}"
    M["fsCashTfour"], M["fsCashTfive"] = f1(X.cash24.mean()), f1(X.cash25.mean())
    M["fsCashAbsMed"], M["fsCashAbsMean"] = f1(X.cash_abs.median()), f1(X.cash_abs.mean())
    M["fsCashPopTfour"] = f1((X.cash24 * X["pop"]).sum() / X["pop"].sum())
    M["fsCashPopTfive"] = f1((X.cash25 * X["pop"]).sum() / X["pop"].sum())
    zn = {"index": "Idx", "E_pred": "Us"}
    xn = {"cash_abs": "Abs", "cash_log": "Log", "reach_abs": "Reach"}
    for r in FS.itertuples():
        t = xn[r.x] + zn[r.z] + ("W" if r.weighted else "")
        M[f"fsF{t}"], M[f"fsB{t}"], M[f"fsBsd{t}"] = f1(r.F), f2(r.b), f2(r.b * r.z_sd)
    xn2 = {"x_cash_abs": "Abs", "x_reach_abs": "Reach", "x_cash_log": "Log"}
    zn2 = {"x_index": "Idx", "x_E_pred": "Us", "x_index+x_E_pred": "Both"}
    yn = {"gam": "Gam", "sam": "Sam", "muac_gam": "Muac", "cdr": "Cdr", "u5dr": "Ufive"}
    for r in R.itertuples():
        t = xn2[r.x] + zn2[r.z] + yn[r.y]
        sc = 10 if r.x == "x_cash_abs" else 1        # per $10 per resident
        M[f"ivF{t}"] = f1(r.F)
        M[f"ivB{t}"], M[f"ivSe{t}"] = f2(r.beta * sc), f2(r.se * sc)
        M[f"ivOls{t}"] = f2(r.ols * sc)
        M[f"ivLo{t}"] = f2(r.ar_lo * sc) if r.ar_bounded else "$-\\infty$"
        M[f"ivHi{t}"] = f2(r.ar_hi * sc) if r.ar_bounded else "$\\infty$"
        M[f"ivLoNinety{t}"], M[f"ivHiNinety{t}"] = f2(r.ar90_lo * sc), f2(r.ar90_hi * sc)
        M[f"ivRho{t}"] = f2(r.rho[0])
        M[f"ivN{t}"], M[f"ivPost{t}"] = f0(r.n), f0(r.post_n)
        M[f"ivXmean{t}"] = f1(r.x_mean_post) if r.x != "x_cash_log" else pc(1 - np.exp(-r.x_mean_post))
        # implied effect at the average loss in the post sample, with the AR interval
        M[f"ivAtMean{t}"] = f1(r.beta * r.x_mean_post)
        M[f"ivAtMeanLo{t}"] = f1(r.ar_lo * r.x_mean_post) if r.ar_bounded else "$-\\infty$"
        M[f"ivAtMeanHi{t}"] = f1(r.ar_hi * r.x_mean_post) if r.ar_bounded else "$\\infty$"
    sn = {"E_pred": "Us", "E_loss": "Loss", "z_index": "Idx", "x_cash_abs": "Cash"}
    for r in S.itertuples():
        t = sn[r.z] + yn[r.y] + {"gu": "Gu", "deyr": "Deyr", "gu26": "GuTs"}[r.season]
        M[f"ssB{t}"], M[f"ssSe{t}"], M[f"ssP{t}"] = f2(r.b_sd), f2(r.se_sd), f2(r.p_wild)
    for r in SI.itertuples():
        t = sn[r.z] + yn[r.y] + {"z_post": "Z", "s_post": "S", "zs_post": "ZS"}[r.term]
        M[f"siB{t}"], M[f"siSe{t}"] = f2(r.b), f2(r.se)
        if r.term == "zs_post":
            M[f"siP{t}"] = f2(r.p_wild)
    spn = {"main (rain, conflict)": "Main", "with prices": "Prices", "balanced 2024-25 domains": "Bal",
           "exposure-specific linear trend": "Trend"}
    for r in RB.itertuples():
        t = sn[r.z] + spn[r.spec]
        M[f"rbB{t}"], M[f"rbSe{t}"], M[f"rbP{t}"] = f2(r.b_sd), f2(r.se_sd), f2(r.p_wild)
    for r in RM.itertuples():
        t = sn[r.z]
        M[f"rmB{t}"], M[f"rmSe{t}"], M[f"rmMax{t}"] = f2(r.b25_sd), f2(r.se25_sd), f2(r.maxdiff_sd)
        M[f"rmLoHalf{t}"], M[f"rmHiHalf{t}"] = f2(r._5), f2(r._6)
        M[f"rmLoOne{t}"], M[f"rmHiOne{t}"] = f2(r._7), f2(r._8)
    a = KEY["attrition"]
    M["atTfour"], M["atObs"] = a["domains_2024"], a["observed_2025"]
    M["atMiss"] = a["domains_2024"] - a["observed_2025"]
    M["atObsTs"] = a.get("observed_2026", 0)
    for c, t in [("E_pred", "Us"), ("z_index", "Idx"), ("gam24", "Gam"), ("dgam_23_24", "Dgam")]:
        if c + "_26" in a:
            M[f"atObsTs{t}"], M[f"atMisTs{t}"], M[f"atPTs{t}"] = f2(a[c + "_26"]["observed"]), f2(a[c + "_26"]["missing"]), f2(a[c + "_26"]["p"])
    for c, t in [("E_pred", "Us"), ("z_index", "Idx"), ("gam24", "Gam"), ("dgam_23_24", "Dgam"), ("x_cash_abs", "Cash")]:
        M[f"atObs{t}"], M[f"atMis{t}"], M[f"atP{t}"] = f2(a[c]["observed"]), f2(a[c]["missing"]), f2(a[c]["p"])
    (ROOT / "output" / "us_cut_memo" / "numbers_fs.tex").write_text(
        "% generated by code/71_somalia_first_stage.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))


if __name__ == "__main__":
    main()
