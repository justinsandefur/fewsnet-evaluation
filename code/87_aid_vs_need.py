"""Where does humanitarian aid go: where the phases are, or where children are malnourished and dying?

Somalia (district x FSNAU survey season, 2015-2026) and Nigeria (LGA x survey round, 2023-2026,
from code/88_nigeria_panels.py). Parallel to code/84_triggers_vs_phases.py, which asks which
information predicts malnutrition and death; this asks which information predicts aid.

Aid, all sectors, in the six months after the survey month (so every predictor is known first):
  usd       OCHA pooled-fund (CBPF) budgets for projects starting in the window, split by district
  partners  distinct organisations present (OCHA 3W), averaged over the window's reports
  reach     people reached per month (Somalia: Cash Working Group 2018-23, 3W 2024, HNRP 2026;
            series differ by year, so everything is compared within a season)
Information at the time of the survey, by district:
  phases    IPC/CH share in Phase 3+ (latest analysis before the survey), FEWS NET current map
            (share Crisis+) and forecast (share forecast Crisis+)
  triggers  rainfall anomaly (6 and 12 months), log conflict fatalities (6 months), prices
  survey    the season's measured GAM, SAM, crude and under-five death rates (and morbidity)
Two analyses.
  1. Prediction. Out-of-sample R-squared (leave one season out) for each information set,
     predicting log aid per capita relative to the season's mean (which districts get more this
     season), with log population in every model.
  2. Allocation benchmark. Within each season, districts' shares of aid against their shares of
     (a) people in Phase 3+, (b) expected deaths (crude death rate x population), (c) expected
     under-five deaths, (d) acutely malnourished children. Dissimilarity index: the share of aid that
     would have to move between districts for aid to be distributed like each need measure.

Outputs: output/tables/aidneed_*.csv, output/cgd_paper/numbers_aidneed.tex,
         output/cgd_paper/figures/fig14_aid_r2.pdf, fig15_allocation.pdf
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
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, PAPER = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "cgd_paper"
AID = INP / "subnational_aid"
U5_SHARE = 0.19          # children under five as a share of population (Somalia/NE Nigeria, approx.)
HALF_YEAR = 182.5


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ================================================================== Somalia
def somalia():
    M68 = load("m68", "68_somalia_us_cut.py")
    M70 = load("m70", "70_somalia_need_response.py")
    dk = M68.dist_key
    q = M68.survey_panel()                                   # domain x season with district weights
    trig = pd.read_parquet(INP / "panel" / "som_need_panel.parquet")[
        ["domain", "season_id", "rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat"]]
    q = q.merge(trig, on=["domain", "season_id"], how="left")
    q["t"] = pd.PeriodIndex(q.month.astype(str), freq="M")

    # long: domain x district link, weight = domain's share in the district
    L = []
    for r in q.itertuples():
        for d, w in json.loads(r.dists).items():
            if d not in (None, "null"):
                L.append(dict(dist=d, season_id=r.season_id, t=r.t, w=w, **{c: getattr(r, c) for c in
                         ["gam", "sam", "cdr", "u5dr", "morbidity", "rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat"]}))
    L = pd.DataFrame(L)
    num = ["gam", "sam", "cdr", "u5dr", "morbidity", "rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat"]

    def wmean(g):
        out = {}
        for c in num:
            ok = g[c].notna() & (g.w > 0)
            out[c] = np.average(g.loc[ok, c], weights=g.loc[ok, "w"]) if ok.any() else np.nan
        out["t"] = g.t.min()
        return pd.Series(out)
    D = L.groupby(["dist", "season_id"]).apply(wmean).reset_index()
    D[num] = D[num].apply(pd.to_numeric, errors="coerce")

    # phases: IPC Phase 3+ share (latest round before survey, within 9 months); FEWS NET map/forecast
    ipc = M70.ipc_rounds()
    ipc["t"] = pd.PeriodIndex(ipc.month, freq="M")
    rounds = sorted(ipc.t.unique())
    sub = pd.read_parquet(INP / "panel" / "subnational_SOM.parquet")
    sub["dist"] = sub.key.map(dk)
    sub["tp"] = pd.PeriodIndex(sub.t, freq="M")
    pop = sub.groupby("dist").pop.mean()
    need_p3, cs3, fc3 = [], [], []
    for r in D.itertuples():
        prior = [x for x in rounds if x <= r.t - 1 and (r.t - x).n <= 9]
        if prior:
            x = ipc[(ipc.t == prior[-1]) & (ipc.dist == r.dist)]
            need_p3.append(x.share3.iloc[0] if len(x) else np.nan)
        else:
            need_p3.append(np.nan)
        s = sub[(sub.dist == r.dist) & (sub.tp <= r.t)].sort_values("tp")
        cs3.append(s.cs3.iloc[-1] if len(s) else np.nan)
        fc3.append(s.fc3.iloc[-1] if len(s) else np.nan)
    D["need_p3"], D["fews_cs"], D["fews_fc"] = need_p3, cs3, fc3
    D["pop"] = D.dist.map(pop)

    # aid in the six months after the survey month
    cb = sub[["dist", "tp", "cbpf_all"]]
    org = pd.read_parquet(AID / "tidy" / "org_presence_som.parquet")
    org["dist"] = org.admin2_pcode.map(dk)
    org["tp"] = pd.PeriodIndex(org.period_start, freq="M")
    rch = pd.read_parquet(AID / "tidy" / "reach_som.parquet")
    rch = rch[(rch.measure == "reached") & ~rch.cumulative & (rch.period_type == "month")].copy()
    rch["dist"] = rch.admin2_pcode.map(dk)
    rch["tp"] = pd.PeriodIndex(rch.period_start, freq="M")
    rch = rch.dropna(subset=["dist"])
    usd, prt, rea = [], [], []
    for r in D.itertuples():
        lo, hi = r.t + 1, r.t + 6
        c = cb[(cb.dist == r.dist) & (cb.tp >= lo) & (cb.tp <= hi)]
        usd.append(c.cbpf_all.sum())
        o = org[(org.tp >= lo) & (org.tp <= hi)]
        if len(o):
            od = o[o.dist == r.dist]
            prt.append(od.groupby("tp").org.nunique().reindex(o.tp.unique(), fill_value=0).mean())
        else:
            prt.append(np.nan)
        x = rch[(rch.tp >= lo) & (rch.tp <= hi)]
        if len(x):
            xd = x[x.dist == r.dist]
            rea.append(xd.groupby("tp").value.sum().reindex(x.tp.unique(), fill_value=0).mean())
        else:
            rea.append(np.nan)
    D["usd"], D["partners"], D["reach"] = usd, prt, rea
    D["country"] = "Somalia"
    D = D.rename(columns={"dist": "unit", "season_id": "period"})
    D["t"] = D.t.astype(str)
    return D


# ================================================================== Nigeria
def nigeria():
    f = INP / "panel" / "nga_lga_aid_panel.parquet"
    if not f.exists():
        return None
    n = pd.read_parquet(f).rename(columns={"lga": "unit", "round_id": "period", "cbpf_usd": "usd", "month": "t"})
    n["country"] = "Nigeria"
    n["lp_cereal"] = n.dp12.fillna(0)               # 12-month price change; missing for most LGAs, set to 0
    n["lp_goat"] = np.nan
    for c in ["fews_cs", "fews_fc"]:                # FEWS NET covers two-thirds of LGA-rounds: fill with round mean
        n[c] = n[c].fillna(n.groupby("period")[c].transform("mean")).fillna(n[c].mean())
    n["reach"] = np.nan
    return n


# ================================================================== analysis
SETS = {
    "Base (population)": [],
    "Phases (IPC/CH share 3+, FEWS NET map and forecast)": ["need_p3", "fews_cs", "fews_fc"],
    "Triggers (rain, conflict, prices)": ["rain_z", "rain12_z", "log_fat", "lp_cereal"],
    "Phases + triggers": ["need_p3", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat", "lp_cereal"],
    "Survey outcomes (malnutrition, deaths)": ["gam", "sam", "cdr", "u5dr"],
    "Survey outcomes + triggers": ["gam", "sam", "cdr", "u5dr", "rain_z", "rain12_z", "log_fat", "lp_cereal"],
}
AIDS = {"usd": "Pooled-fund dollars", "partners": "Partners present", "reach": "People reached"}


def prep(D, aid):
    d = D.copy()
    d["y"] = np.log1p(d[aid] / d["pop"] * (1e3 if aid != "usd" else 1))
    d["y"] = d.y - d.groupby("period").y.transform("mean")      # which districts get more this season
    d["lpop"] = np.log(d["pop"])
    for c in ["need_p3", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat", "lp_cereal", "gam", "sam", "cdr", "u5dr"]:
        d[c] = d[c] - d.groupby("period")[c].transform("mean")    # within-season variation only
    return d


def oos(d, xs):
    f = "y ~ lpop" + "".join(f" + {x}" for x in xs)
    pred = pd.Series(np.nan, index=d.index)
    for s in d.period.unique():
        tr, te = d[d.period != s], d[d.period == s]
        pred.loc[te.index] = smf.ols(f, tr).fit().predict(te)
    return 1 - ((d.y - pred) ** 2).sum() / (d.y ** 2).sum()


def dissimilarity(D, aid):
    rows = []
    for (cty, per), g in D.dropna(subset=[aid, "pop"]).groupby(["country", "period"]):
        g = g.copy()
        if g[aid].sum() <= 0 or len(g) < 4:
            continue
        g["deaths"] = g.cdr * g["pop"] * HALF_YEAR / 1e4
        g["u5deaths"] = g.u5dr * g["pop"] * U5_SHARE * HALF_YEAR / 1e4
        g["malnourished"] = g.gam / 100 * g["pop"] * U5_SHARE
        g["p3"] = g.need_p3 * g["pop"]
        s_aid = g[aid] / g[aid].sum()
        out = dict(country=cty, period=per, aid=aid, n=len(g), total=g[aid].sum())
        for need in ["p3", "deaths", "u5deaths", "malnourished", "pop"]:
            ok = g[need].notna()
            if ok.sum() < 4 or g.loc[ok, need].sum() <= 0:
                out[need] = np.nan
                continue
            sa = g.loc[ok, aid] / g.loc[ok, aid].sum()
            sn = g.loc[ok, need] / g.loc[ok, need].sum()
            out[need] = 0.5 * (sa - sn).abs().sum()
            out[f"corr_{need}"] = np.corrcoef(sa, sn)[0, 1]
        rows.append(out)
    return pd.DataFrame(rows)


def main():
    S = somalia()
    N = nigeria()
    D = pd.concat([S, N]) if N is not None else S
    numc = ["gam", "sam", "cdr", "u5dr", "morbidity", "rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat",
            "need_p3", "fews_cs", "fews_fc", "pop", "usd", "partners", "reach"]
    D[numc] = D[numc].apply(pd.to_numeric, errors="coerce")
    D.to_parquet(INP / "panel" / "aidneed_panel.parquet")

    rows = []
    for cty, g in D.groupby("country"):
        for aid in AIDS:
            base = g.dropna(subset=[aid, "pop", "need_p3", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat",
                                    "gam", "cdr", "u5dr"]).copy()
            base = base[base["pop"] > 0]
            if "lp_cereal" in base and base.lp_cereal.notna().mean() > 0.5:
                base["lp_cereal"] = base.lp_cereal.fillna(base.lp_cereal.mean())
            else:
                base["lp_cereal"] = 0.0
            base["sam"] = base.sam.fillna(base.sam.mean())
            if base.period.nunique() < 3 or len(base) < 30:
                continue
            d = prep(base, aid)
            for lab, xs in SETS.items():
                rows.append(dict(country=cty, aid=aid, info=lab, r2=oos(d, xs), n=len(d), periods=d.period.nunique(),
                                 units=d.unit.nunique()))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "aidneed_oos_r2.csv", index=False)

    DS = pd.concat([dissimilarity(D, a) for a in AIDS])
    DS.to_csv(TAB / "aidneed_dissimilarity.csv", index=False)

    # in-sample standardized horse race (within season), for reference
    hr = []
    for cty, g in D.groupby("country"):
        for aid in AIDS:
            d = g.dropna(subset=[aid, "pop", "need_p3", "gam", "cdr", "u5dr"]).copy()
            d = d[d["pop"] > 0]
            if len(d) < 30:
                continue
            d = prep(d, aid)
            for c in ["need_p3", "gam", "cdr", "u5dr"]:
                d[c] = d[c] / d[c].std()
            m = smf.ols("y ~ lpop + need_p3 + gam + cdr + u5dr", d).fit(
                cov_type="cluster", cov_kwds={"groups": d.unit.astype("category").cat.codes})
            for c in ["need_p3", "gam", "cdr", "u5dr"]:
                hr.append(dict(country=cty, aid=aid, var=c, b=m.params[c], se=m.bse[c], p=m.pvalues[c], n=int(m.nobs)))
    HR = pd.DataFrame(hr)
    HR.to_csv(TAB / "aidneed_horserace.csv", index=False)
    figures(R, DS)
    numbers(R, DS, HR, D)

    pd.set_option("display.width", 220)
    print(R.pivot_table(index="info", columns=["country", "aid"], values="r2").round(3))
    print(R.groupby(["country", "aid"])[["n", "periods", "units"]].first())
    print(DS.groupby(["country", "aid"])[["p3", "deaths", "u5deaths", "malnourished", "pop"]].mean().round(3))
    print(HR.round(3).to_string(index=False))


COLS = ["#c3c2b7", "#e34948", "#2a78d6", "#4a3aa7", "#1baf7a", "#008300"]


def figures(R, DS):
    groups = [(c, a) for c in ["Somalia", "Nigeria"] for a in AIDS if ((R.country == c) & (R.aid == a)).any()]
    fig, ax = plt.subplots(figsize=(8.5, 4))
    k = len(SETS)
    w = 0.8 / k
    for j, (lab, col) in enumerate(zip(SETS, COLS)):
        vals = [R[(R.country == c) & (R.aid == a) & (R["info"] == lab)].r2.iloc[0] for c, a in groups]
        ax.bar(np.arange(len(groups)) + (j - (k - 1) / 2) * w, np.maximum(vals, -0.05), w * 0.92, color=col, label=lab)
    ax.axhline(0, color="#52514e", lw=0.8)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f"{AIDS[a]}\n({c})" for c, a in groups], fontsize=9)
    ax.set_ylabel("Out-of-sample $R^2$ (leave one season out)")
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    ax.set_ylim(-0.06, max(0.5, R.r2.max() + 0.15))
    fig.savefig(PAPER / "figures" / "fig14_aid_r2.pdf", bbox_inches="tight"); plt.close(fig)

    # allocation: share of aid that would move to match each need measure
    M = DS.groupby(["country", "aid"])[["p3", "deaths", "u5deaths", "malnourished"]].mean()
    labs = {"p3": "People in Phase 3+", "deaths": "Expected deaths", "u5deaths": "Expected under-five deaths",
            "malnourished": "Acutely malnourished children"}
    cols = ["#e34948", "#2a78d6", "#4a3aa7", "#1baf7a"]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    k = 4
    w = 0.8 / k
    for j, (need, col) in enumerate(zip(labs, cols)):
        vals = [M.loc[g, need] if g in M.index else np.nan for g in groups]
        ax.bar(np.arange(len(groups)) + (j - (k - 1) / 2) * w, 100 * np.array(vals), w * 0.92, color=col, label=labs[need])
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f"{AIDS[a]}\n({c})" for c, a in groups], fontsize=9)
    ax.set_ylabel("Share of aid that would have to move (%)")
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    fig.savefig(PAPER / "figures" / "fig15_allocation.pdf", bbox_inches="tight"); plt.close(fig)


def numbers(R, DS, HR, D):
    def f2(x):
        return f"{x:.2f}".replace("-", "\\textminus{}")
    m = {}
    C = {"Somalia": "Som", "Nigeria": "Nga"}
    A = {"usd": "Usd", "partners": "Prt", "reach": "Rch"}
    I = {"Base (population)": "Base", "Phases (IPC/CH share 3+, FEWS NET map and forecast)": "Phase",
         "Triggers (rain, conflict, prices)": "Trig", "Phases + triggers": "PhaseTrig",
         "Survey outcomes (malnutrition, deaths)": "Surv", "Survey outcomes + triggers": "SurvTrig"}
    for r in R.itertuples():
        m[f"ar{C[r.country]}{A[r.aid]}{I[r.info]}"] = f2(r.r2)
    for (c, a), g in R.groupby(["country", "aid"]):
        m[f"ar{C[c]}{A[a]}N"] = f"{int(g.n.iloc[0]):,}"
        m[f"ar{C[c]}{A[a]}Periods"] = f"{int(g.periods.iloc[0])}"
        m[f"ar{C[c]}{A[a]}Units"] = f"{int(g.units.iloc[0])}"
    M = DS.groupby(["country", "aid"])[["p3", "deaths", "u5deaths", "malnourished", "pop"]].mean()
    for (c, a), r in M.iterrows():
        for need, nm in [("p3", "Pthree"), ("deaths", "Deaths"), ("u5deaths", "Ufive"), ("malnourished", "Maln"),
                         ("pop", "Pop")]:
            if pd.notna(r[need]):
                m[f"dis{C[c]}{A[a]}{nm}"] = f"{100 * r[need]:.0f}"
    for r in HR.itertuples():
        m[f"hr{C[r.country]}{A[r.aid]}{ {'need_p3': 'Pthree', 'gam': 'Gam', 'cdr': 'Cdr', 'u5dr': 'Ufive'}[r.var] }"] = f2(r.b)
    lines = ["% Written by code/87_aid_vs_need.py -- do not edit by hand"]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    (PAPER / "numbers_aidneed.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
