"""Does aid follow FEWS NET within countries, do its aid flags mark where aid went, and does
aid improve outcomes? District x FEWS NET period panels (61_subnational_panel.py).

Framework. District d, period t (FEWS NET map rounds). Need N is unobserved; FEWS NET
publishes, at the round opening t, its current map (cs3), its forecast for t (fc3) and the
aid flag. Aid A_dt (pooled-fund food security + nutrition + cash US$, asinh; or 3W partner
presence) is allocated during t. The observed phase at the next round is
P_d,t+1 = N_d,t+1 - theta * A_dt.

(A) Allocation:  A_dt = beta fc3_dt + gamma cs3_dt + rho A_d,t-1 + mu_d + lambda_t + e_dt
    - static: rho = 0; dynamic: lagged aid with district effects (Nickell bias O(1/T),
      T ~ 25-30 periods); Anderson-Hsiao: first differences, Delta A_d,t-1 instrumented with
      A_d,t-2 (consistent under no serial correlation in e).
    - distinctive information: fc3 split into its predictable part (b_fc3) and FEWS NET's
      contribution beyond public data (c_fc3), as in the country-level analysis.
    - timing placebo: aid in t should not respond to FEWS NET's forecast published at t+1
      beyond what was known at t.
(B) Flags: flag_dt = delta A_dt (and A_d,t-1, A_d,t+1) + controls + mu_d + lambda_t.
    If the '!' flag records where aid is holding phases down, it should turn on where and
    when aid arrives, not before.
(C) Aid effects (exploratory): shift-share instrument Z_dt = s_d x asinh(E_t), s_d =
    district's share of the fund's food/nutrition allocations in the first two years
    (dropped from the sample), E_t = the country fund's total allocation in t. With district
    and period effects, Z identifies off high-share districts receiving more when the
    envelope is large; controls for s_d x national Crisis+ share absorb the obvious threat
    (envelopes rising in national crises that hit high-share districts hardest).
    Outcomes: next map Crisis+ share, mean phase, aid flag.

Outputs: output/tables/subnational_models.csv, subnational_key.json
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"


def demean(d, cols, fes, iters=100):
    w = d[cols].astype(float).copy()
    for _ in range(iters):
        before = w.values.copy()
        for f in fes:
            w = w - w.groupby(d[f]).transform("mean")
        if np.abs(w.values - before).max() < 1e-10:
            break
    return w


def cluster_vcov(X, u, groups, XtXi):
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g in np.unique(groups):
        i = groups == g
        s = X[i].T @ u[i]
        meat += np.outer(s, s)
    G = len(np.unique(groups))
    return XtXi @ meat @ XtXi * G / (G - 1)


def ols(d, y, xs, fes, cl="key"):
    d = d.dropna(subset=[y] + xs)
    for f in fes:
        d = d[d.groupby(f)[y].transform("size") > 1]
    w = demean(d, [y] + xs, fes)
    X, Y = w[xs].values, w[y].values
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ Y
    V = cluster_vcov(X, Y - X @ b, d[cl].values, XtXi)
    return pd.DataFrame({"coef": b, "se": np.sqrt(np.diag(V))}, index=xs), len(d), d[cl].nunique()


def iv(d, y, endog, inst, exog, fes, cl="key"):
    """2SLS with fixed effects partialled out; returns second stage and first-stage F (cluster-robust Wald)."""
    d = d.dropna(subset=[y, endog] + inst + exog)
    w = demean(d, [y, endog] + inst + exog, fes)
    Z = w[inst + exog].values
    X = w[[endog] + exog].values
    Y = w[y].values
    ZtZi = np.linalg.pinv(Z.T @ Z)
    # first stage
    pi = ZtZi @ Z.T @ w[endog].values
    V1 = cluster_vcov(Z, w[endog].values - Z @ pi, d[cl].values, ZtZi)
    k = len(inst)
    Fst = float(pi[:k] @ np.linalg.pinv(V1[:k, :k]) @ pi[:k] / k)
    Xh = Z @ (ZtZi @ Z.T @ X)
    XhXi = np.linalg.pinv(Xh.T @ Xh)
    b = XhXi @ Xh.T @ Y
    u = Y - X @ b
    V = cluster_vcov(Xh, u, d[cl].values, XhXi)
    return (pd.DataFrame({"coef": b, "se": np.sqrt(np.diag(V))}, index=[endog] + exog), len(d), d[cl].nunique(),
            Fst, float(pi[0]), float(np.sqrt(V1[0, 0])))


def prep(iso):
    D = pd.read_parquet(INP / f"panel/subnational_{iso}.parquet")
    D["t"] = pd.PeriodIndex(D.t, freq="M")
    D = D[(D.t.dt.year >= 2014) & (D.t.dt.year <= 2024)].sort_values(["key", "t"])
    cash = D.cbpf_cash if "cbpf_cash" in D else 0.0
    D["aid_usd"] = D.get("cbpf_fs", 0.0) + D.get("cbpf_nut", 0.0) + cash
    D["aid"] = np.arcsinh(D.aid_usd)
    D["aid_any"] = (D.aid_usd > 0).astype(float)
    D["aid_all"] = np.arcsinh(D.cbpf_all)
    g = D.groupby("key")
    D["aid_l1"], D["aid_l2"], D["aid_f1"] = g.aid.shift(1), g.aid.shift(2), g.aid.shift(-1)
    D["fc3_f1"] = g.fc3.shift(-1)
    D["d_aid"], D["d_aid_l1"] = D.aid - D.aid_l1, D.aid_l1 - D.aid_l2
    D["d_fc3"], D["d_cs3"] = D.fc3 - g.fc3.shift(1), D.cs3 - g.cs3.shift(1)
    D["tt"] = D.t.astype(str)
    # shift-share instrument
    first = sorted(D.t.unique())[:6]
    base = D[D.t.isin(first)].groupby("key").aid_usd.sum()
    D["share"] = D.key.map(base / base.sum()).fillna(0.0)
    D["Z"] = D.share * np.arcsinh(D.envelope)
    nat = D.groupby("t").apply(lambda x: np.average(x.cs3, weights=x["pop"])).rename("nat_cs3")
    D = D.merge(nat.reset_index(), on="t")
    D["share_x_nat"] = D.share * D.nat_cs3
    D["in_base"] = D.t.isin(first)
    if "pres_fs" in D:
        D["pres"] = D[["pres_fs", "pres_nut"]].fillna(0).sum(axis=1).where(D[["pres_fs", "pres_nut"]].notna().any(axis=1))
    return D


def run(iso):
    D = prep(iso)
    out, key = [], {"iso": iso, "districts": int(D.key.nunique()), "periods": int(D.t.nunique()),
                    "share_with_aid": float(D.aid_any.mean()), "mean_aid_usd": float(D.aid_usd.mean())}
    def rec(block, spec, y, r, n, G, **extra):
        for v, x in r.iterrows():
            out.append(dict(iso=iso, block=block, spec=spec, outcome=y, var=v, coef=x.coef, se=x.se, n=n, clusters=G, **extra))
    FE = ["key", "tt"]
    # (A) allocation
    for y in ["aid", "aid_any"]:
        rec("A", "static", y, *ols(D, y, ["fc3", "cs3"], FE))
        rec("A", "dynamic", y, *ols(D, y, ["fc3", "cs3", "aid_l1"], FE))
        rec("A", "distinctive", y, *ols(D, y, ["c_fc3", "b_fc3", "cs3"], FE))
        rec("A", "placebo: next round's forecast", y, *ols(D, y, ["fc3", "cs3", "fc3_f1"], FE))
    r, n, G, F, pi, pse = iv(D, "d_aid", "d_aid_l1", ["aid_l2"], ["d_fc3", "d_cs3"], ["tt"])
    rec("A", "Anderson-Hsiao", "d_aid", r, n, G, first_stage_F=F)
    if "pres" in D and D.pres.notna().sum() > 200:
        P = D[D.pres.notna()]
        rec("A", "static", "pres", *ols(P, "pres", ["fc3", "cs3"], FE))
        rec("A", "distinctive", "pres", *ols(P, "pres", ["c_fc3", "b_fc3", "cs3"], FE))
    # (B) flags
    rec("B", "contemporaneous", "flag", *ols(D, "flag", ["aid", "cs3", "phase"], FE))
    rec("B", "lags and lead", "flag", *ols(D, "flag", ["aid_l1", "aid", "aid_f1", "cs3", "phase"], FE))
    rec("B", "next round", "flag_next", *ols(D, "flag_next", ["aid", "flag", "cs3", "phase"], FE))
    if "pres" in D and D.pres.notna().sum() > 200:
        rec("B", "contemporaneous", "flag (3W presence)", *ols(D[D.pres.notna()], "flag", ["pres", "cs3", "phase"], FE))
    # (B') flags against people reached (annual panel)
    A = pd.read_parquet(INP / f"panel/subnational_{iso}_annual.parquet")
    A["reach"] = np.arcsinh(A.reach_fs + A.reach_nut)
    A["reach_pc"] = (A.reach_fs + A.reach_nut) / A["pop"].where(A["pop"] > 0)
    A["reach_pc"] = A.reach_pc.clip(upper=A.reach_pc.quantile(0.99))
    A["yy"] = A.year.astype(str)
    key.update(annual_n=int(len(A)), annual_years=sorted(int(y) for y in A.year.unique()),
               flag_mean_annual=float(A.flag.mean()), reach_any=float((A.reach_fs + A.reach_nut > 0).mean()))
    rec("B2", "district and year effects", "flag", *ols(A, "flag", ["reach", "cs3", "phase"], ["key", "yy"]))
    rec("B2", "district and year effects", "flag", *ols(A, "flag", ["reach_pc", "cs3", "phase"], ["key", "yy"]))
    rec("B2", "year effects only", "flag", *ols(A, "flag", ["reach", "cs3", "phase"], ["yy"]))
    # does reach go where FEWS NET forecasts Crisis? (annual)
    rec("A2", "district and year effects", "reach", *ols(A, "reach", ["fc3", "cs3"], ["key", "yy"]))
    # (C) aid effects, shift-share IV (base periods dropped)
    S = D[~D.in_base]
    ctrl = ["cs3", "fc3", "share_x_nat"]
    for y in ["cs3_next", "phase_next", "flag_next"]:
        r, n, G, F, pi, pse = iv(S, y, "aid", ["Z"], ctrl, FE)
        rec("C", "2SLS", y, r, n, G, first_stage_F=F, first_stage=pi, first_stage_se=pse)
        rec("C", "OLS", y, *ols(S, y, ["aid"] + ctrl, FE))
    R = pd.DataFrame(out)
    return R, key


def main():
    isos = sys.argv[1:] or ["SOM", "SDN"]
    R, K = [], {}
    for iso in isos:
        r, k = run(iso)
        R.append(r)
        K[iso] = k
    R = pd.concat(R)
    R.to_csv(TAB / "subnational_models.csv", index=False)
    (TAB / "subnational_key.json").write_text(json.dumps(K, indent=1))
    pd.set_option("display.width", 220)
    show = R[~R["var"].isin(["cs3", "phase", "share_x_nat"])]
    print(show[["iso", "block", "spec", "outcome", "var", "coef", "se", "n", "first_stage_F"]].round(3).to_string() if "first_stage_F" in show else show.round(3).to_string())
    print(json.dumps(K, indent=1))


if __name__ == "__main__":
    main()
