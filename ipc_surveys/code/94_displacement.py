"""Is the IPC measuring displacement instead of malnutrition and death? Somalia, 2016-2023.

Displacement: UNHCR's Protection and Return Monitoring Network (PRMN), weekly records of people displaced, by
district of origin and of arrival and stated reason (input/displacement/prmn/, Jan 2016 - Aug 2023).

A. Districts x survey seasons (the panel of 87_aid_vs_need.py, 2016-2023): the official IPC Phase 3+ share,
   FEWS NET's map and forecast, rainfall and conflict signals, the season's survey outcomes (all survey domains in
   the district), and departures out of the district in the six months before and after the survey month
   (log of 1 + people per 1,000 residents). Correlations within season; out-of-sample R-squared (leave one season
   out) of each information set for each outcome; and what predicts the Phase 3+ share.
B. Somali regions x months (Oct 2020 - May 2023): do household food consumption and coping (WFP's monthly phone
   monitoring), rainfall and previous violence predict departures over the next three months?
C. Reassignment: count people who left a district in the previous 6 or 12 months as part of that district, with
   the outcomes measured in the displaced settlements they reached (stayers: the district's rural and town
   surveys); and, as a stress test, with assumed death rates of 1, 2, 5 and 10 per 10,000 per day.
D. Displaced settlements: are their outcomes related to the Phase 3+ share of the districts their recent
   arrivals came from, to their own district's share, or to the number of arrivals?

Outputs: output/tables/disp_*.csv, output/cgd_paper/numbers_disp.tex, output/cgd_paper/figures/fig17_reassign.pdf
"""
import contextlib
import importlib.util
import io
import json
import re
import unicodedata
import warnings

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, PAPER = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "cgd_paper"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    return m


def norm(s):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower())


def f2(x):
    return f"{x:.2f}".replace("-", "\\textminus{}")


M70 = load("m70", "70_somalia_need_response.py")
M68 = load("m68", "68_somalia_us_cut.py")
M = {}

# ------------------------------------------------------------------ displacement records
x = pd.read_excel(INP / "displacement" / "prmn" / "prmn.xlsx")
x["t"] = pd.PeriodIndex(pd.to_datetime(x["Month End"], dayfirst=True), freq="M")
x["o"] = x["Previous (Departure) District"].map(M70.to_pcode)
x["d"] = x["Current (Arrival) District"].map(M70.to_pcode)
x["n"] = x["Number of Individuals"]
x["why"] = x.Reason.map({"Drought related": "drought", "Conflict/Insecurity": "conflict", "Flood": "flood"}).fillna("other")
M["dpRecords"] = f"{len(x):,}"
M["dpDroughtShare"] = f"{100 * x.loc[x.why == 'drought', 'n'].sum() / x.n.sum():.0f}"
M["dpConflictShare"] = f"{100 * x.loc[x.why == 'conflict', 'n'].sum() / x.n.sum():.0f}"
M["dpPeople"] = f"{x.n.sum() / 1e6:.1f}"
flows = x.dropna(subset=["o"]).groupby(["o", "t", "why"]).n.sum().unstack("why", fill_value=0)

ipc = M70.ipc_rounds()
ipc["tp"] = pd.PeriodIndex(ipc.month, freq="M")
ROUNDS = sorted(ipc.tp.unique())


def p3_at(dist, t):
    prior = [r for r in ROUNDS if r <= t and (t - r).n <= 9]
    if not prior:
        return np.nan
    z = ipc[(ipc.tp == prior[-1]) & (ipc.dist == dist)]
    return z.share3.iloc[0] if len(z) else np.nan


def window(dist, t, lo, hi, col):
    if dist not in flows.index.get_level_values(0):
        return 0.0
    f = flows.loc[dist]
    f = f[(f.index >= t + lo) & (f.index <= t + hi)]
    return float(f[col].sum()) if col in f else 0.0


# ================================================================== A. districts x seasons
D = pd.read_parquet(INP / "panel" / "aidneed_panel.parquet")
D = D[D.country == "Somalia"].copy()
D["tp"] = pd.PeriodIndex(D.t.astype(str), freq="M")
for col in ["drought", "conflict"]:
    D[f"{col}_next"] = [window(r.unit, r.tp, 1, 6, col) for r in D.itertuples()]
    D[f"{col}_prev"] = [window(r.unit, r.tp, -6, -1, col) for r in D.itertuples()]
D = D[(D.tp >= pd.Period("2016-07", "M")) & (D.tp <= pd.Period("2023-02", "M"))]
for col in ["drought", "conflict"]:
    for w in ["next", "prev"]:
        D[f"l_{col}_{w}"] = np.log1p(D[f"{col}_{w}"] / D["pop"] * 1000)
D["l_pop"] = np.log(D["pop"])
A = D.dropna(subset=["need_p3", "gam", "cdr", "u5dr", "rain12_z", "log_fat", "fews_cs"]).copy()
A[["unit", "period", "pop", "l_pop", "need_p3", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat", "gam", "cdr",
   "u5dr", "l_drought_next", "l_drought_prev", "l_conflict_next", "l_conflict_prev"]].to_csv(TAB / "disp_district.csv", index=False)
M["dpAN"], M["dpADistricts"], M["dpASeasons"] = f"{len(A):,}", f"{A.unit.nunique()}", f"{A.period.nunique()}"

Aw = A.copy()
for c in ["need_p3", "gam", "cdr", "u5dr", "l_drought_next", "l_conflict_next", "l_drought_prev"]:
    Aw[c] = Aw[c] - Aw.groupby("period")[c].transform("mean")
OUT = {"gam": "Gam", "cdr": "Cdr", "u5dr": "Ufive", "l_drought_next": "DrNext", "l_conflict_next": "CoNext",
       "l_drought_prev": "DrPrev"}
for c, K in OUT.items():
    M[f"dpCorr{K}"] = f2(Aw[c].corr(Aw.need_p3))


def oos(y, xs):
    d = A.copy()
    for c in [y] + xs:
        d[c] = d[c] - d.groupby("period")[c].transform("mean")
    f = f"{y} ~ l_pop" + "".join(" + " + v for v in xs)
    pred = pd.Series(np.nan, index=d.index)
    for s in d.period.unique():
        tr, te = d.period != s, d.period == s
        pred[te] = smf.ols(f, d[tr]).fit().predict(d[te])
    return 1 - ((d[y] - pred) ** 2).sum() / (d[y] ** 2).sum()


R = []
for y, K in [(k, v) for k, v in OUT.items() if k != "l_drought_prev"]:
    for xs, X in [([], "Pop"), (["need_p3"], "Ipc"), (["fews_cs", "fews_fc"], "Fews"),
                  (["rain_z", "rain12_z", "log_fat"], "Trig")]:
        r = oos(y, xs)
        M[f"dpR{K}{X}"] = f2(r)
        R.append(dict(outcome=y, info=X, r2=r))
pd.DataFrame(R).to_csv(TAB / "disp_oos.csv", index=False)

z = A.copy()
for c in ["l_drought_prev", "l_conflict_prev", "gam", "cdr", "u5dr", "rain12_z", "rain_z", "log_fat"]:
    z[c] = (z[c] - z[c].mean()) / z[c].std()
for fe, F in [("C(period)", "B"), ("C(period) + C(unit)", "W")]:
    m = smf.ols(f"need_p3 ~ l_drought_prev + l_conflict_prev + gam + cdr + u5dr + rain12_z + rain_z + log_fat + l_pop + {fe}",
                z).fit(cov_type="cluster", cov_kwds={"groups": z.unit.astype("category").cat.codes})
    for v, V in [("l_drought_prev", "Dr"), ("l_conflict_prev", "Co"), ("gam", "Gam"), ("cdr", "Cdr"), ("u5dr", "Ufive")]:
        M[f"dpP{F}{V}"] = f"{100 * m.params[v]:.1f}".replace("-", "\\textminus{}")
        M[f"dpP{F}{V}Se"] = f"{100 * m.bse[v]:.1f}"

# ================================================================== B. regions x months: household measures
ac = pd.read_excel(INP / "acled" / "hdx" / "som.xlsx", sheet_name="Data")
RC = {norm(a): p for a, p in zip(ac.Admin1, ac["Admin1 Pcode"])}
for k, v in {"Jubbada Dhexe": "Middle Juba", "Jubbada Hoose": "Lower Juba", "Shabeellaha Dhexe": "Middle Shabelle",
             "Shabeellaha Hoose": "Lower Shabelle", "Galguduud": "Galgaduud", "Hiiraan": "Hiraan",
             "Banaadir": "Banadir"}.items():
    RC[norm(k)] = RC[norm(v)]
x["reg"] = x["Previous (Departure) Region"].map(lambda n: RC.get(norm(n)))
dep = x.groupby(["reg", "t", "why"]).n.sum().unstack(fill_value=0)
dep["all"] = dep.sum(axis=1)
ac["t"] = pd.PeriodIndex(pd.to_datetime(ac.Month + " " + ac.Year.astype(str), format="%B %Y"), freq="M")
fat = ac.groupby(["Admin1 Pcode", "t"]).Fatalities.sum()
fsi = pd.read_parquet(INP / "foodsec_surveys" / "indicators.parquet")
fsi = fsi[(fsi.iso3 == "SOM") & (fsi.source == "wfp_rt")].copy()
fsi["reg"] = fsi.adm1_name.map(lambda n: RC.get(norm(n)))
fs = fsi.pivot_table(index=["reg", "month"], columns="indicator", values="value")
F57 = load("m57", "57_fsnau_value.py")
U = F57.units()
U["reg"] = U.reg.map(lambda n: RC.get(norm(n)))
rain = pd.read_parquet(INP / "panel" / "fnid_rain_monthly.parquet")
rain = rain[rain.index.isin(U.fnid)]
rr = rain.groupby(U.set_index("fnid").reg.reindex(rain.index).values).mean().T
rr.index = pd.PeriodIndex(rr.index, freq="M")


def rz(k):
    s = rr.rolling(k).sum()
    clim = s[(s.index.year >= 1991) & (s.index.year <= 2020)]
    mu, sd = clim.groupby(clim.index.month).mean(), clim.groupby(clim.index.month).std()
    return (s - mu.reindex(s.index.month).values) / sd.reindex(s.index.month).values


R6, R12 = rz(6), rz(12)
sub = pd.read_parquet(INP / "panel" / "subnational_SOM.parquet")
popr = sub.drop_duplicates("key").assign(reg=lambda q: q.key.str[:4]).groupby("reg").pop.sum()
P = []
for (reg, t) in fs.index:
    if not (pd.Period("2020-10", "M") <= t <= pd.Period("2023-05", "M")):
        continue
    g = lambda col, ms: sum(dep.loc[(reg, s), col] if (reg, s) in dep.index else 0 for s in ms)
    P.append(dict(reg=reg, t=str(t), q=f"{t.year}Q{t.quarter}", fcs=fs.loc[(reg, t), "fcs_poor_borderline"],
                  rcsi=fs.loc[(reg, t), "rcsi_19plus"], rain6=R6.loc[t, reg] if reg in R6 else np.nan,
                  rain12=R12.loc[t, reg] if reg in R12 else np.nan,
                  fat3=sum(fat.get((reg, t - k), 0) for k in range(3)), fat12=sum(fat.get((reg, t - k), 0) for k in range(12)),
                  drought=g("drought", [t + 1, t + 2, t + 3]), allmv=g("all", [t + 1, t + 2, t + 3]), pop=popr.get(reg, np.nan)))
P = pd.DataFrame(P).dropna()
for c in ["drought", "allmv"]:
    P["y_" + c] = np.log1p(P[c] / P["pop"] * 1000)
P["lfat3"], P["lfat12"] = np.log1p(P.fat3), np.log1p(P.fat12)
P.to_csv(TAB / "disp_region.csv", index=False)
M["dpBN"], M["dpBRegions"], M["dpBMonths"] = f"{len(P):,}", f"{P.reg.nunique()}", f"{P.t.nunique()}"
M["dpBMean"] = f"{(P.drought / P['pop'] * 1000).mean():.0f}"
SETS = {"Hh": ["fcs", "rcsi"], "Rain": ["rain6", "rain12"], "Viol": ["lfat3", "lfat12"],
        "All": ["fcs", "rcsi", "rain6", "rain12", "lfat3", "lfat12"]}


def oos_b(y, xs, fe):
    f = f"{y} ~ 1" + "".join(" + " + v for v in xs) + (" + C(reg)" if fe else "")
    pred = pd.Series(np.nan, index=P.index)
    for q in P.q.unique():
        tr, te = P.q != q, P.q == q
        pred[te] = smf.ols(f, P[tr]).fit().predict(P[te])
    base = P.groupby("reg")[y].transform("mean") if fe else P[y].mean()
    return 1 - ((P[y] - pred) ** 2).sum() / ((P[y] - base) ** 2).sum()


for y, Y in [("y_drought", "Dr"), ("y_allmv", "All")]:
    for k, xs in SETS.items():
        M[f"dpB{Y}{k}"] = f2(oos_b(y, xs, False))
        M[f"dpB{Y}{k}W"] = f2(oos_b(y, xs, True))
zb = P.copy()
for c in ["fcs", "rcsi", "rain6", "rain12", "lfat3", "lfat12"]:
    zb[c] = (zb[c] - zb[c].mean()) / zb[c].std()
for fe, F in [(" + C(reg)", "W"), (" + C(reg) + C(t)", "WT")]:
    m = smf.ols("y_drought ~ fcs + rcsi + rain6 + rain12 + lfat3 + lfat12" + fe, zb).fit(
        cov_type="cluster", cov_kwds={"groups": zb.reg.astype("category").cat.codes})
    for v, V in [("fcs", "Fcs"), ("rain6", "Rain")]:
        M[f"dpB{F}{V}"] = f"{m.params[v]:.2f}".replace("-", "\\textminus{}")
        M[f"dpB{F}{V}Se"] = f"{m.bse[v]:.2f}"

# ================================================================== C. reassignment
q = M68.survey_panel()
q["tp"] = pd.PeriodIndex(q.month.astype(str), freq="M")
L = pd.DataFrame([dict(dist=dd, season=r.season_id, tp=r.tp, ptype=r.ptype, w=w, gam=r.gam, cdr=r.cdr, u5dr=r.u5dr)
                  for r in q.itertuples() for dd, w in json.loads(r.dists).items() if dd not in (None, "null") and w > 0])


def wmean(g, c):
    ok = g[c].notna()
    return np.average(g.loc[ok, c], weights=g.loc[ok, "w"]) if ok.any() else np.nan


S = L[L.ptype != "IDP"].groupby(["dist", "season"]).apply(
    lambda g: pd.Series({"tp": g.tp.min(), **{c: wmean(g, c) for c in ["gam", "cdr", "u5dr"]}})).reset_index()
for c in ["gam", "cdr", "u5dr"]:
    S[c] = pd.to_numeric(S[c])
idp = L[L.ptype == "IDP"].groupby(["dist", "season"])[["gam", "cdr", "u5dr"]].mean()
sub["dist"] = sub.key.map(M68.dist_key)
pop = sub.groupby("dist").pop.mean()
S = S[(S.tp >= pd.Period("2018-07", "M")) & (S.tp <= pd.Period("2023-08", "M"))].copy()
S["p3"] = [p3_at(r.dist, r.tp) for r in S.itertuples()]
S["pop"] = S.dist.map(pop)
S = S.dropna(subset=["p3", "pop"])
xo = x.dropna(subset=["o", "d"])
xo = xo[xo.o != xo.d]
rows = []
for r in S.itertuples():
    out = {}
    for win in [6, 12]:
        f = xo[(xo.o == r.dist) & (xo.t >= r.tp - win) & (xo.t <= r.tp - 1)].groupby("d").n.sum()
        out[f"left{win}"] = float(f.sum())
        for c in ["gam", "cdr", "u5dr"]:
            ys, ws = [], []
            for dd, n in f.items():
                if (dd, r.season) in idp.index and pd.notna(idp.loc[(dd, r.season), c]):
                    ys.append(idp.loc[(dd, r.season), c]); ws.append(n)
            stay = max(r.pop - f.sum(), 0.5 * r.pop)
            v = getattr(r, c)
            out[f"{c}_star{win}"] = (stay * v + sum(a * b for a, b in zip(ys, ws))) / (stay + sum(ws)) if pd.notna(v) else np.nan
    rows.append(out)
S = pd.concat([S.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
S["season_s"] = S.season
S.drop(columns=["tp"]).to_csv(TAB / "disp_reassign.csv", index=False)
wn = lambda v: v - v.groupby(S.season).transform("mean")
M["dpCN"], M["dpCDistricts"], M["dpCSeasons"] = f"{len(S):,}", f"{S.dist.nunique()}", f"{S.season.nunique()}"
WN = {6: "Six", 12: "Twelve"}
for win in [6, 12]:
    sh = S[f"left{win}"] / S["pop"]
    M[f"dpCLeftMed{WN[win]}"] = f"{100 * sh.median():.1f}"
    M[f"dpCLeftNinety{WN[win]}"] = f"{100 * sh.quantile(.9):.1f}"
for c, K in [("gam", "Gam"), ("cdr", "Cdr"), ("u5dr", "Ufive")]:
    ok = S[c].notna()
    M[f"dpCStay{K}"] = f2(wn(S[c])[ok].corr(wn(S.p3)[ok]))
    for win in [6, 12]:
        okw = ok & S[f"{c}_star{win}"].notna()
        M[f"dpCAll{K}{WN[win]}"] = f2(wn(S[f"{c}_star{win}"])[okw].corr(wn(S.p3)[okw]))
sh12 = S.left12 / S["pop"]
M["dpCLeftCorr"] = f2(wn(sh12).corr(wn(S.p3)))
stress = []
okc = S.cdr.notna()
for X in [None, 1.0, 2.0, 5.0, 10.0]:
    y = S.cdr if X is None else (1 - sh12) * S.cdr + sh12 * X
    rho = wn(y)[okc].corr(wn(S.p3)[okc])
    stress.append(dict(rate=X, corr=rho))
    M[f"dpCStress{'None' if X is None else {1.0: 'One', 2.0: 'Two', 5.0: 'Five', 10.0: 'Ten'}[X]}"] = f2(rho)
pd.DataFrame(stress).to_csv(TAB / "disp_stress.csv", index=False)

# ================================================================== D. displaced settlements
p = pd.read_parquet(INP / "panel" / "som_need_panel.parquet")
p = p[p.ptype == "IDP"].copy()
p["tp"] = pd.PeriodIndex(p.month.astype(str), freq="M")
p["dist"] = p.domain.str.split("|").str[1]
p = p[(p.tp >= pd.Period("2018-07", "M")) & (p.tp <= pd.Period("2023-08", "M"))]
rows = []
for r in p.itertuples():
    a = xo[(xo.d == r.dist) & (xo.t >= r.tp - 6) & (xo.t <= r.tp - 1)]
    ext = a.groupby("o").n.sum()
    po = pd.Series({o: p3_at(o, r.tp) for o in ext.index}).dropna()
    w = ext.reindex(po.index)
    rows.append(dict(domain=r.domain, season=r.season_id, gam=r.gam, cdr=r.cdr, u5dr=r.u5dr, local_p3=p3_at(r.dist, r.tp),
                     origin_p3=(po * w).sum() / w.sum() if w.sum() > 0 else np.nan, arrivals=float(ext.sum())))
E = pd.DataFrame(rows).dropna(subset=["local_p3", "origin_p3"])
E["l_arr"] = np.log1p(E.arrivals)
E.to_csv(TAB / "disp_settlements.csv", index=False)
M["dpDN"], M["dpDSettlements"], M["dpDSeasons"] = f"{len(E):,}", f"{E.domain.nunique()}", f"{E.season.nunique()}"
for c, K in [("gam", "Gam"), ("cdr", "Cdr"), ("u5dr", "Ufive")]:
    M[f"dpDOwn{K}"] = f2(E[c].corr(E.local_p3))
    M[f"dpDOrigin{K}"] = f2(E[c].corr(E.origin_p3))
    M[f"dpDArr{K}"] = f2(E[c].corr(E.l_arr))
    m = smf.ols(f"{c} ~ local_p3 + origin_p3 + l_arr + C(season)", E).fit(
        cov_type="cluster", cov_kwds={"groups": E.domain.astype("category").cat.codes})
    dg = 2 if c == "gam" else 3
    M[f"dpDArrB{K}"] = f"{m.params['l_arr']:.{dg}f}"
    M[f"dpDArrB{K}Se"] = f"{m.bse['l_arr']:.{dg}f}"

# ------------------------------------------------------------------ figure: reassignment and stress test
fig, ax = plt.subplots(figsize=(7.2, 3.9))
lab = ["Stayers\nonly", "Left in past\n6 months", "Left in past\n12 months", "1", "2", "5", "10"]
vals = [wn(S.cdr)[okc].corr(wn(S.p3)[okc]),
        float(M["dpCAllCdrSix"].replace("\\textminus{}", "-")), float(M["dpCAllCdrTwelve"].replace("\\textminus{}", "-"))] + \
       [s_["corr"] for s_ in stress[1:]]
cols = ["#52514e", "#2a78d6", "#2a78d6", "#e34948", "#e34948", "#e34948", "#e34948"]
ax.bar(range(len(vals)), vals, color=cols, width=0.62)
for i, v in enumerate(vals):
    ax.text(i, v + 0.004, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color="#52514e")
ax.set_xticks(range(len(vals)))
ax.set_xticklabels(lab, fontsize=8)
ax.axhline(0, color="#52514e", lw=0.8)
ax.set_ylabel("Correlation of the district's\nPhase 3+ share with its crude death rate")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#52514e", label="People who stayed"),
                   Patch(color="#2a78d6", label="Plus people who left, at the death rate measured where they arrived"),
                   Patch(color="#e34948", label="Plus everyone who left in the past year, at an assumed death rate\n(1, 2, 5 or 10 per 10,000 per day)")],
          frameon=False, fontsize=7.5, loc="upper right")
ax.set_ylim(0, 0.26)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
fig.savefig(PAPER / "figures" / "fig17_reassign.pdf", bbox_inches="tight"); plt.close(fig)

lines = ["% Written by code/94_displacement.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()]
(PAPER / "numbers_disp.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
