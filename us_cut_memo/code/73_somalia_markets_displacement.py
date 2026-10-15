"""Somalia: outcomes closer to cash than wasting -- local prices and displacement.

Prices. If cash transfers fell more in some districts, local demand should fall more there:
prices of locally traded goods (sorghum, maize, cowpeas, camel milk, goat meat) and possibly
livestock should fall relative to elsewhere. Imported goods (rice, wheat flour, pasta, sugar,
oil), priced off world markets and transport, are a partial placebo. WFP market prices (HDX),
~41 markets, monthly Jan 2023 - Aug 2026, US$ prices.
  log price[m,c,t] = market x commodity FE + commodity x month FE + b * E[d(m)] x post[t]
post = Jan 2025 onwards; event study by quarter relative to 2024Q4. E = cash lost per resident
(X), aid dependence and US reliance (Z), from 71; reduced forms and 2SLS. Region clusters.

Displacement. IOM DTM Emergency Trends Tracking (ETT), Somalia, Oct 2023 - 2026: newly displaced
people recorded by district of arrival and by reason. Outcome: new arrivals per 1,000 residents
per month, all reasons and reasons other than conflict and floods/rain (drought, lack of food,
livelihoods, assistance). Same design at district x month level.

Outputs: output/tables/som_mkt_*.csv, som_disp_*.csv, output/figures/som_mkt_event.pdf,
         som_disp_event.pdf, output/us_cut_memo/numbers_mkt.tex
"""
import importlib.util
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"
M = {}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M70 = load("m70", "70_somalia_need_response.py")
M71 = load("m71", "71_somalia_first_stage.py")
GROUPS = {
    "local food": ["Sorghum (red)", "Sorghum (white)", "Maize (white)", "Cowpeas", "Milk (camel)", "Meat (goat)"],
    "imported food": ["Rice (imported)", "Wheat flour (imported)", "Pasta", "Sugar (white)", "Oil (vegetable, imported)"],
    "livestock (goat)": ["Livestock (Goat)"],
}
EXPO = [("cash_abs", "Cash lost per resident ($10)", 10), ("index", "Aid dependence (per s.d.)", None),
        ("E_pred", "US reliance (per s.d.)", None)]


def exposures():
    X = pd.read_csv(TAB / "som_fs_districts.csv", index_col=0)
    return X[["cash_abs", "reach_abs", "cash_log", "index", "E_pred", "pop"]]


def demean(v, groups, iters=300):
    v = v.astype(float).copy()
    for _ in range(iters):
        v0 = v.copy()
        for g in groups:
            v = v - v.groupby(g).transform("mean")
        if np.max(np.abs(v - v0)) < 1e-9:
            break
    return v


def cl(u, v, g):
    b = (v @ u) / (v @ v)
    e = u - b * v
    G = np.unique(g)
    s = sum((v[g == q] @ e[g == q]) ** 2 for q in G)
    return b, np.sqrt(s / (v @ v) ** 2 * len(G) / (len(G) - 1))


def dd(d, y, e, fe, post="post", scale=1.0):
    """Reduced-form DiD coefficient of y on e x post after demeaning by fe; region clusters."""
    d = d.dropna(subset=[y, e])
    yt = demean(d[y], [d[f] for f in fe]).values
    xt = demean(d[e] * d[post], [d[f] for f in fe]).values
    b, se = cl(yt, xt, d.region.values)
    # small-sample factor (n-1)/(n-k), k counting the fixed effects (as Stata's regress does)
    n, k = len(d), sum(d[f].nunique() for f in fe) - (len(fe) - 1) + 1
    se = se * np.sqrt((n - 1) / (n - k))
    G = d.region.nunique()
    return dict(b=b * scale, se=se * scale, p=2 * stats.t.sf(abs(b / se), G - 1), n=len(d), clusters=G,
                units=d.dist.nunique())


def iv(d, y, x, z, fe, post="post"):
    d = d.dropna(subset=[y, x, z])
    g = d.region.values
    yt = demean(d[y], [d[f] for f in fe]).values
    xt = demean(d[x] * d[post], [d[f] for f in fe]).values
    zt = demean(d[z] * d[post], [d[f] for f in fe]).values
    pi, spi = cl(xt, zt, g)
    rho, srho = cl(yt, zt, g)
    beta = rho / pi
    G = len(np.unique(g))
    crit = stats.f.ppf(0.95, 1, G - 1)
    span = max(40 * abs(srho / pi), 4 * abs(beta), 0.05)
    acc = [b0 for b0 in np.linspace(beta - span, beta + span, 4001) if (lambda c: (c[0] / c[1]) ** 2)(cl(yt - b0 * xt, zt, g)) < crit]
    bounded = bool(acc) and acc[0] > beta - span and acc[-1] < beta + span
    return dict(F=(pi / spi) ** 2, beta=beta, ar_lo=min(acc) if bounded else np.nan, ar_hi=max(acc) if bounded else np.nan)


def event(d, y, e, fe, tcol, ref, scale):
    d = d.dropna(subset=[y, e]).copy()
    periods = [t for t in sorted(d[tcol].unique()) if t != ref]
    yt = demean(d[y], [d[f] for f in fe]).values
    Z = np.column_stack([demean(d[e] * (d[tcol] == t), [d[f] for f in fe]).values for t in periods])
    b, V = M71.cl_ols(yt, Z, d.region.values)
    out = pd.DataFrame({"t": periods, "b": b * scale, "se": np.sqrt(np.diag(V)) * scale})
    return pd.concat([out, pd.DataFrame([{"t": ref, "b": 0.0, "se": 0.0}])]).sort_values("t")


# ------------------------------------------------------------------ prices
def prices():
    p = pd.read_csv(INP / "prices" / "som.csv", low_memory=False)
    p = p[~p.date.astype(str).str.startswith("#")]
    p["usdprice"] = pd.to_numeric(p.usdprice, errors="coerce")
    p = p[(p.pricetype == "Retail") & (p.usdprice > 0) & (p.date >= "2023-01-01")]
    p["dist"] = p.admin2.map(M70.to_pcode)
    M["mkUnmatched"] = int(p[p.dist.isna()].market.nunique())
    p = p.dropna(subset=["dist"])
    p["t"] = p.date.str[:7]
    p["q"] = pd.PeriodIndex(pd.to_datetime(p.date), freq="Q").astype(str)
    p["lp"] = 100 * np.log(p.usdprice)
    p["mc"] = p.market + "|" + p.commodity
    p["ct"] = p.commodity + "|" + p.t
    p["post"] = (p.date >= "2025-01-01").astype(float)
    X = exposures()
    p = p.merge(X, left_on="dist", right_index=True, how="left")
    p["region"] = p.dist.str[:4]
    return p


def run_prices():
    p = prices()
    sd = {e: p.drop_duplicates("dist")[e].std() for e in ["index", "E_pred"]}
    rows, ev = [], []
    for grp, comms in GROUPS.items():
        d = p[p.commodity.isin(comms)]
        for e, lab, sc in EXPO:
            s = sc if sc else sd[e]
            r = dd(d, "lp", e, ["mc", "ct"], scale=s)
            rows.append(dict(group=grp, exposure=e, **r, markets=d.market.nunique()))
        for x, z in [("cash_abs", "index"), ("reach_abs", "index"), ("cash_log", "E_pred")]:
            r = iv(d, "lp", x, z, ["mc", "ct"])
            rows.append(dict(group=grp, exposure=f"IV:{x}|{z}", b=r["beta"] * (10 if x == "cash_abs" else 1),
                             F=r["F"], ar_lo=r["ar_lo"] * (10 if x == "cash_abs" else 1),
                             ar_hi=r["ar_hi"] * (10 if x == "cash_abs" else 1)))
        e = event(d, "lp", "cash_abs", ["mc", "ct"], "q", "2024Q4", 10)
        e["group"] = grp
        ev.append(e)
    # within market x month: local food relative to imported food (removes currency, transport and
    # other market-wide shocks; the cleanest test of a local demand effect)
    d = p[p.commodity.isin(GROUPS["local food"] + GROUPS["imported food"])].copy()
    d["local"] = d.commodity.isin(GROUPS["local food"]).astype(float)
    d["mt"] = d.market + "|" + d.t
    d["post_local"] = d.post * d.local
    for e, lab, sc in EXPO:
        s_ = sc if sc else sd[e]
        r = dd(d, "lp", e, ["mc", "ct", "mt"], post="post_local", scale=s_)
        rows.append(dict(group="local minus imported", exposure=e, **r, markets=d.market.nunique()))
    for x, z in [("cash_abs", "index"), ("reach_abs", "index"), ("cash_log", "E_pred")]:
        r = iv(d, "lp", x, z, ["mc", "ct", "mt"], post="post_local")
        rows.append(dict(group="local minus imported", exposure=f"IV:{x}|{z}", b=r["beta"] * (10 if x == "cash_abs" else 1),
                         F=r["F"], ar_lo=r["ar_lo"] * (10 if x == "cash_abs" else 1),
                         ar_hi=r["ar_hi"] * (10 if x == "cash_abs" else 1)))
    d["qlocal"] = np.where(d.local == 1, d.q, "imported")
    e3 = []
    dd_ = d.dropna(subset=["cash_abs"]).copy()
    yt = demean(dd_["lp"], [dd_["mc"], dd_["ct"], dd_["mt"]]).values
    qs = [q for q in sorted(dd_.q.unique()) if q != "2024Q4"]
    Zq = np.column_stack([demean(dd_["cash_abs"] * dd_.local * (dd_.q == q), [dd_["mc"], dd_["ct"], dd_["mt"]]).values
                          for q in qs])
    bq, Vq = M71.cl_ols(yt, Zq, dd_.region.values)
    e3 = pd.DataFrame({"t": qs, "b": bq * 10, "se": np.sqrt(np.diag(Vq)) * 10})
    e3 = pd.concat([e3, pd.DataFrame([{"t": "2024Q4", "b": 0.0, "se": 0.0}])]).sort_values("t")
    e3["group"] = "local minus imported"
    ev.append(e3)
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "som_mkt_did.csv", index=False)
    EV = pd.concat(ev)
    EV.to_csv(TAB / "som_mkt_event.csv", index=False)
    M["mkMarkets"], M["mkDistricts"] = p.market.nunique(), p.dist.nunique()
    gn = {"local food": "Local", "imported food": "Imp", "livestock (goat)": "Goat", "local minus imported": "Rel"}
    en = {"cash_abs": "Cash", "index": "Idx", "E_pred": "Us"}
    for r in R.itertuples():
        if r.exposure in en:
            t = gn[r.group] + en[r.exposure]
            M[f"mkB{t}"], M[f"mkSe{t}"], M[f"mkP{t}"] = f"{r.b:.2f}", f"{r.se:.2f}", f"{r.p:.2f}"
        elif r.exposure == "IV:cash_abs|index":
            t = gn[r.group]
            M[f"mkIvF{t}"], M[f"mkIv{t}"] = f"{r.F:.1f}", f"{r.b:.2f}"
            M[f"mkIvLo{t}"] = f"{r.ar_lo:.2f}" if not np.isnan(r.ar_lo) else "$-\\infty$"
            M[f"mkIvHi{t}"] = f"{r.ar_hi:.2f}" if not np.isnan(r.ar_hi) else "$\\infty$"
    # national price path: local vs imported, index Jan 2024 = 100
    nat = p[p.commodity.isin(GROUPS["local food"] + GROUPS["imported food"])].copy()
    nat["grp"] = np.where(nat.commodity.isin(GROUPS["local food"]), "local", "imported")
    base = nat[nat.t.between("2024-01", "2024-12")].groupby("mc").lp.mean()
    nat["rel"] = nat.lp - nat.mc.map(base)
    NP = nat.groupby(["grp", "t"]).rel.mean().unstack(0)
    NP.to_csv(TAB / "som_mkt_national.csv")
    for g in ["local", "imported"]:
        M[f"mkNat{g.capitalize()}Tfive"] = f"{NP.loc['2025-01':'2025-12', g].mean():.0f}"
    plot_event(EV, "group", "som_mkt_event.pdf", "Price change (%) per $10\ncash lost per resident",
               [("local minus imported", ORANGE), ("livestock (goat)", GREEN)])
    print(R.round(3).to_string())
    print(EV.round(2).to_string())


def plot_event(EV, key, fname, ylab, series):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ts = sorted(EV.t.unique())
    for i, (k, col) in enumerate(series):
        e = EV[EV[key] == k].set_index("t").reindex(ts)
        x = np.arange(len(ts)) + (i - (len(series) - 1) / 2) * 0.18
        ax.errorbar(x, e.b, yerr=1.96 * e.se, fmt="o", color=col, ms=3.5, lw=1.1, label=k)
    ax.axhline(0, color=GREY, lw=0.8)
    cut = [j for j, t in enumerate(ts) if str(t) >= "2025"][0] - 0.5
    ax.axvline(cut, color=GREY, ls=":", lw=0.8)
    ax.set_xticks(np.arange(len(ts)))
    ax.set_xticklabels([str(t)[2:] for t in ts], fontsize=7, rotation=90)
    ax.set_ylabel(ylab, fontsize=9)
    ax.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(FIG / fname)
    plt.close(fig)


# ------------------------------------------------------------------ displacement
def ett():
    files = ["ett_oct2023_feb2024", "ett_apr2024_dec2024", "ett_feb2025_may2026", "ett_jun2026"]
    rows = []
    for f in files:
        d = pd.read_excel(INP / "displacement" / "dtm_ett" / f"{f}.xlsx", sheet_name=0)
        d = d[~d.iloc[:, 0].astype(str).str.startswith("#")]
        c = {k: next((col for col in d.columns if col.startswith(k)), None) for k in [
            "Date of Assessment", "OCHA District Pcode", "Total new arrivals since last week",
            "Reason for the new arrivals", "Somalia District of Origin", "Somalia Region of Origin",
            "Response - General food distribution", "Response - Nutrition Services", "Reason of Displacement",
            "Main Cause of Displacement", "Settlement ID", "Location ID"]}
        sid = c["Settlement ID"] or c["Location ID"]
        x = pd.DataFrame({
            "date": pd.to_datetime(d[c["Date of Assessment"]], errors="coerce"),
            "dist": d[c["OCHA District Pcode"]].astype(str).map(M70.dist_key),
            "arr": pd.to_numeric(d[c["Total new arrivals since last week"]], errors="coerce").fillna(0),
            "why_come": d[c["Reason for the new arrivals"]].astype(str),
            "orig": d[c["Somalia District of Origin"]].astype(str),
            "food": d[c["Response - General food distribution"]].astype(str).str.lower().str.startswith("y"),
            "nut": d[c["Response - Nutrition Services"]].astype(str).str.lower().str.startswith("y"),
            "reason": d[c["Reason of Displacement"]].astype(str),
            "site": d[sid].astype(str), "file": f})
        rows.append(x)
    E = pd.concat(rows, ignore_index=True).dropna(subset=["date"])
    E = E[E.date >= "2023-10-01"]
    E["t"] = E.date.dt.to_period("M").astype(str)
    E["odist"] = E.orig.map(M70.to_pcode)
    E["slow"] = ~E.reason.str.contains("Conflict|Flood|Insecurity|Evict", case=False)
    E["aid_seek"] = E.why_come.str.contains("assistance|aid", case=False)
    M["dpRows"], M["dpOrigMatch"] = f"{len(E):,}", f"{100 * E[E.arr > 0].odist.notna().mean():.0f}"
    return E


def displacement():
    E = ett()
    X = exposures()
    pop = X["pop"]
    months = sorted(E.t.unique())
    dists = sorted(set(X.index))
    grid = pd.MultiIndex.from_product([dists, months], names=["dist", "t"]).to_frame(index=False)
    a = E[E.arr > 0].copy()
    a["arr_aid"] = a.arr * a.aid_seek
    dest = a.groupby(["dist", "t"]).agg(arr=("arr", "sum"), arr_aid=("arr_aid", "sum")).reset_index()
    orig = a[a.slow].groupby(["odist", "t"]).arr.sum().rename("out_slow").reset_index().rename(columns={"odist": "dist"})
    resp = a.groupby(["dist", "t"]).agg(food_resp=("food", "mean"), nut_resp=("nut", "mean"),
                                        assessments=("site", "size")).reset_index()
    cov = E.groupby(["dist", "t"]).site.nunique().rename("sites_assessed").reset_index()
    P = grid.merge(dest, how="left").merge(orig, how="left").merge(resp, how="left").merge(cov, how="left")
    for c in ["arr", "arr_aid", "out_slow"]:
        P[c] = P[c].fillna(0)
    P = P.merge(X, left_on="dist", right_index=True)
    P["arr_pk"] = P.arr / P["pop"] * 1000
    P["out_pk"] = P.out_slow / P["pop"] * 1000
    P["aid_share"] = P.arr_aid / P.arr.replace(0, np.nan)
    P["post"] = (P.t >= "2025-02").astype(float)
    P["region"] = P.dist.str[:4]
    P["q"] = pd.PeriodIndex(P.t, freq="M").asfreq("Q").astype(str)
    # districts monitored before and after the cut only
    keep = P[(P.sites_assessed > 0)].groupby("dist").post.agg(["min", "max"])
    P = P[P.dist.isin(keep[(keep["min"] == 0) & (keep["max"] == 1)].index)]
    sd = {e: P.drop_duplicates("dist")[e].std() for e in ["index", "E_pred"]}
    rows, ev = [], []
    for y in ["arr_pk", "out_pk", "aid_share", "food_resp", "nut_resp"]:
        for e, lab, sc in EXPO:
            s_ = sc if sc else sd[e]
            r = dd(P, y, e, ["dist", "t"], scale=s_)
            rows.append(dict(outcome=y, exposure=e, **r))
        for e in ["index", "E_pred"]:
            v = event(P, y, e, ["dist", "t"], "q", "2024Q4", sd[e])
            v["outcome"], v["exposure"] = y, e
            ev.append(v)
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "som_disp_did.csv", index=False)
    EV = pd.concat(ev)
    EV.to_csv(TAB / "som_disp_event.csv", index=False)
    nat = P.groupby("t").agg(arr=("arr", "sum"), out=("out_slow", "sum"), food=("food_resp", "mean"),
                             sites=("sites_assessed", "sum"))
    nat.to_csv(TAB / "som_disp_national.csv")
    yn = {"arr_pk": "Arr", "out_pk": "Out", "aid_share": "Aid", "food_resp": "Food", "nut_resp": "Nut"}
    en = {"cash_abs": "Cash", "index": "Idx", "E_pred": "Us"}
    for r in R.itertuples():
        t = yn[r.outcome] + en[r.exposure]
        M[f"dpB{t}"], M[f"dpSe{t}"], M[f"dpP{t}"] = f"{r.b:.2f}", f"{r.se:.2f}", f"{r.p:.2f}"
    M["dpDistricts"] = P.dist.nunique()
    pre, post = nat.loc[:"2024-12"], nat.loc["2025-02":"2025-12"]
    M["dpFoodPre"], M["dpFoodPost"] = f"{100 * pre.food.mean():.0f}", f"{100 * post.food.mean():.0f}"
    M["dpFoodLate"] = f"{100 * nat.loc['2025-11':'2025-12'].food.mean():.0f}"
    M["dpFoodTsix"] = f"{100 * nat.loc['2026-01':].food.mean():.0f}"
    M["dpArrPre"], M["dpArrPost"] = f"{pre.arr.mean() / 1e3:.0f}", f"{post.arr.mean() / 1e3:.0f}"
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))
    ax = axes[0]
    ax.plot(range(len(nat)), 100 * nat.food, color=ORANGE, marker="o", ms=3, label="New arrivals got food distribution (%)")
    ax.set_xticks(range(0, len(nat), 3))
    ax.set_xticklabels([t[2:] for t in nat.index[::3]], fontsize=7, rotation=90)
    ax.legend(frameon=False, fontsize=8)
    ax2 = ax.twinx()
    ax2.bar(range(len(nat)), nat.arr / 1e3, color=BLUE, alpha=0.3)
    ax2.set_ylabel("New arrivals (thousands/month)", fontsize=8, color=BLUE)
    ax = axes[1]
    for e, col in [("index", ORANGE), ("E_pred", BLUE)]:
        v = EV[(EV.outcome == "food_resp") & (EV.exposure == e)].sort_values("t")
        x = np.arange(len(v)) + (0.12 if e == "E_pred" else -0.12)
        ax.errorbar(x, 100 * v.b, yerr=196 * v.se, fmt="o", ms=3, color=col, lw=1,
                    label={"index": "Aid dependence", "E_pred": "US reliance"}[e])
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xticks(range(len(v)))
    ax.set_xticklabels([t[2:] for t in v.t], fontsize=7, rotation=90)
    ax.set_title("Food distribution to new arrivals (pp)\nper s.d. of exposure, vs 2024Q4", fontsize=9)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "som_disp_event.pdf")
    plt.close(fig)
    print(R.round(3).to_string())
    print(nat.round(2).to_string())


def write():
    """Update the macros this run produced, keeping the others (prices and displacement can run separately)."""
    f = ROOT / "output" / "us_cut_memo" / "numbers_mkt.tex"
    old = {}
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.match(r"\\newcommand\{\\n(\w+)\}\{(.*)\}$", line)
            if m:
                old[m.group(1)] = m.group(2)
    old.update({k: str(v) for k, v in M.items()})
    f.write_text("% generated by code/73_somalia_markets_displacement.py -- do not edit\n" +
                 "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in old.items()))


if __name__ == "__main__":
    import sys
    if "noprices" not in sys.argv:
        run_prices()
    displacement()
    write()
