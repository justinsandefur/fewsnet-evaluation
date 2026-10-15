"""Main-text figures and the core table for the US-cut memo, built to show its four lessons directly.

  Fig 1  som_lesson1_delivery.pdf   Aid delivered in Somalia fell and kept falling: food and cash reached,
                                    sites treating severe malnutrition, and the share of displacement-site
                                    assessments where new arrivals got food, each indexed to Jan-Jun 2024 = 100.
  Fig 2  som_lesson2_terciles.pdf   Food and cash fell most where aid dependence was high, not where US
                                    reliance was high: people reached per 100 residents per month, Jan-Jun
                                    2024/2025/2026, by thirds of each exposure (population-weighted).
  Fig 3  som_lesson34_event.pdf     Child wasting by survey round, per s.d. of each exposure, relative to 2024:
                                    aid dependence (no rise), US-funded agency share and agency loss (rise
                                    growing after the cut).
  Fig 4  som_lesson5_displacement.pdf  Non-conflict displacement out of districts, before vs after the cut, by
                                    thirds of cash lost per resident.
  Table  numbers_fig.tex            First stage and outcome estimates by exposure (one column each).

Inputs are panels and tables written by code/68-75 (run those first).
"""
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
BLUE, ORANGE, GREEN, GREY, DARK = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a", "#333333"
M = {}
f1 = lambda v: f"{v:.1f}"
f2 = lambda v: f"{v:.2f}"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 10, "axes.titleweight": "bold"})


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M68 = load("m68", "68_somalia_us_cut.py")
M71 = load("m71", "71_somalia_first_stage.py")
M73 = load("m73", "73_somalia_markets_displacement.py")
M75 = load("m75", "75_somalia_delivery.py")


# ------------------------------------------------------------------ Fig 1
def fig_delivery(F, N, E):
    f = F.groupby(["year", "m"]).fsc.sum()
    f.index = [f"{y}-{m:02d}" for y, m in f.index]
    n = N[N.year >= 2023].groupby(["year", "m"]).otp_sites.sum()
    n.index = [f"{y}-{m:02d}" for y, m in n.index]
    a = E[E.arr > 0].groupby("t").food.mean()
    base = lambda s: s[[i for i in s.index if "2024-01" <= i <= "2024-06"]].mean()
    S = pd.DataFrame({"food and cash reached": 100 * f / base(f), "treatment sites": 100 * n / base(n),
                      "new arrivals fed": 100 * a / base(a)})
    S = S[(S.index >= "2023-07") & (S.index <= "2026-08")]
    # last month of FSC and nutrition reporting is often incomplete
    S.to_csv(TAB / "fig1_delivery_index.csv")
    for c in S:
        s = S[c].dropna()
        M[f"fone{c.split()[0].capitalize()}Last"] = f"{s.iloc[-3:].mean():.0f}"
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = {t: i for i, t in enumerate(S.index)}
    for c, col in [("food and cash reached", BLUE), ("treatment sites", ORANGE), ("new arrivals fed", GREEN)]:
        s = S[c].rolling(3, min_periods=2, center=True).mean().dropna()
        ax.plot([x[t] for t in s.index], s.values, color=col, lw=2)
        ax.text(x[s.index[-1]] + 0.4, s.values[-1], c, color=col, va="center", fontsize=9)
    ax.axhline(100, color=GREY, lw=0.8, ls=":")
    cut = x["2025-01"] if "2025-01" in x else x["2025-02"]
    ax.axvline(cut, color=DARK, lw=0.8)
    ax.text(cut + 0.3, ax.get_ylim()[1] * 0.97, "US stop-work order", fontsize=8, va="top")
    ticks = [t for t in S.index if t.endswith("-01") or t.endswith("-07")]
    ax.set_xticks([x[t] for t in ticks])
    ax.set_xticklabels([t.replace("-01", "\nJan").replace("-07", "\nJul")[:4] + t[-3:].replace("-01", " Jan").replace("-07", " Jul") for t in ticks], fontsize=8)
    ax.set_xticklabels([("Jan " if t.endswith("-01") else "Jul ") + t[:4] for t in ticks], fontsize=8)
    ax.set_ylabel("Index, Jan-Jun 2024 = 100")
    ax.set_xlim(-0.5, len(S) + 8)
    ax.set_ylim(0, max(160, S.max().max() * 1.05))
    fig.tight_layout()
    fig.savefig(FIG / "som_lesson1_delivery.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ Fig 2
def fig_terciles(F, X):
    fh = F[F.m.between(1, 6)].groupby(["dist", "year"]).fsc.mean().unstack()
    D = X.join(fh)
    rows = []
    for z, lab in [("index", "aid dependence"), ("E_pred", "US reliance")]:
        d = D.dropna(subset=[z, 2024]).copy()
        d["t"] = pd.qcut(d[z].rank(method="first"), 3, labels=["lowest third", "middle third", "highest third"])
        for y in [2024, 2025, 2026]:
            g = d.groupby("t", observed=True).apply(lambda s: 100 * s[y].fillna(0).sum() / s["pop"].sum())
            for t, v in g.items():
                rows.append(dict(exposure=lab, tercile=t, year=y, reach=v))
    T = pd.DataFrame(rows)
    T.to_csv(TAB / "fig2_terciles.csv", index=False)
    for e, et in [("aid dependence", "Dep"), ("US reliance", "Us")]:
        for t, tt in [("lowest third", "Lo"), ("highest third", "Hi")]:
            for y in [2024, 2025, 2026]:
                M[f"ftwo{et}{tt}{y % 100}".replace("24", "Tf").replace("25", "Tv").replace("26", "Ts")] = f1(
                    T[(T.exposure == e) & (T.tercile == t) & (T.year == y)].reach.iloc[0])
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), sharey=True)
    cols = {"lowest third": "#9ec5f0", "middle third": BLUE, "highest third": "#123f73"}
    for ax, e in zip(axes, ["aid dependence", "US reliance"]):
        ends = {t: T[(T.exposure == e) & (T.tercile == t) & (T.year == 2026)].reach.iloc[0] for t in cols}
        # spread end labels so they do not overlap
        order = sorted(ends, key=ends.get)
        ypos, last = {}, -1e9
        for t in order:
            ypos[t] = max(ends[t], last + 1.6)
            last = ypos[t]
        for t in ["lowest third", "middle third", "highest third"]:
            s = T[(T.exposure == e) & (T.tercile == t)].sort_values("year")
            ax.plot(s.year, s.reach, color=cols[t], marker="o", lw=2)
            ax.text(2026.08, ypos[t], t, color=cols[t], fontsize=8, va="center")
        ax.set_title(f"Districts by {e} in 2024")
        ax.set_xticks([2024, 2025, 2026])
        ax.set_xlim(2023.85, 2026.75)
    axes[0].set_ylabel("Food & cash reached per 100\nresidents per month (Jan-Jun)")
    fig.tight_layout()
    fig.savefig(FIG / "som_lesson2_terciles.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ Fig 3
def round_event(p, z, y="gam"):
    d = p.dropna(subset=[y, z]).copy()
    d = d[d.year >= 2019]
    sd = d.drop_duplicates("domain")[z].std()
    d["zs"] = (d[z] - d.drop_duplicates("domain")[z].mean()) / sd
    order = sorted(d.season_id.unique(), key=lambda s: int(s.split()[1]) + (0.5 if s.startswith("Deyr") else 0))
    ref = [s for s in order if s.endswith("2024")]
    rounds = [s for s in order if s not in ref]
    A = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
    A = A.join(pd.get_dummies(d.ptype + ":" + d.season_id, prefix="t", drop_first=True, dtype=float))
    for r in rounds:
        A["ev:" + r] = d.zs * (d.season_id == r)
    for c in ["rain_z", "rain12_z", "log_fat"]:
        A[c] = d[c]
    A.insert(0, "const", 1.0)
    A = A.loc[:, A.std() > 0].assign(const=1.0)
    b, se, _ = M68.ols_cl(A, d[y].values, d.region.values)
    cols = list(A.columns)
    out = [dict(round=r, b=b[cols.index("ev:" + r)], se=se[cols.index("ev:" + r)],
                n=int((d.season_id == r).sum())) for r in rounds if "ev:" + r in cols]
    out += [dict(round=r, b=0.0, se=0.0, n=int((d.season_id == r).sum())) for r in ref]
    O = pd.DataFrame(out)
    O["o"] = O["round"].map({s: i for i, s in enumerate(order)})
    return O.sort_values("o")


def fig_event(p):
    ex = [("z_index", "Aid dependence\n(where food & cash fell most)", ORANGE),
          ("E_pred", "US-funded share of agencies", BLUE),
          ("E_loss", "Agencies lost, 2024 to 2025", GREEN)]
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.5), sharey=True)
    allE = []
    for ax, (z, lab, col) in zip(axes, ex):
        O = round_event(p, z)
        O["exposure"] = z
        allE.append(O)
        xs = np.arange(len(O))
        post = O["round"].str.contains("2025|2026").values
        ax.axvspan(np.argmax(post) - 0.5, len(O) - 0.5, color=GREY, alpha=0.12, lw=0)
        ax.axhline(0, color=GREY, lw=0.8)
        ax.errorbar(xs, O.b, yerr=1.96 * O.se, fmt="o", color=col, ms=4, lw=1.2, capsize=0)
        ax.set_xticks(xs)
        ax.set_xticklabels([("Gu " if r.startswith("Gu") else "Deyr ") + r.split()[1][:4] for r in O["round"]],
                           fontsize=7, rotation=90)
        ax.set_title(lab, fontsize=9.5)
    axes[0].set_ylabel("Wasting (pp) per s.d. of exposure,\nrelative to 2024")
    fig.tight_layout()
    fig.savefig(FIG / "som_lesson34_event.pdf")
    plt.close(fig)
    pd.concat(allE).to_csv(TAB / "fig3_round_event.csv", index=False)


# ------------------------------------------------------------------ Table: first stage and outcomes by exposure
def core_table(F, X, p):
    fh = F[F.m.between(1, 6)].groupby(["dist", "year"]).fsc.mean().unstack()
    D = X.join(fh).join(pd.read_csv(TAB / "som_fs_districts.csv", index_col=0)[["E_loss"]])
    for y in [2025, 2026]:
        D[f"loss{y}"] = (D[2024].fillna(0) - D[y].fillna(0)) / D["pop"] * 100
    for z, zt in [("index", "Dep"), ("E_pred", "Us"), ("E_loss", "Loss")]:
        for y in [2025, 2026]:
            d = D.dropna(subset=[z, f"loss{y}"])
            A = np.column_stack([np.ones(len(d)), d[z]])
            b, V = M71.cl_ols(d[f"loss{y}"].values, A, d.region.values)
            t = f"{zt}{'Tv' if y == 2025 else 'Ts'}"
            M[f"ctFs{t}"], M[f"ctFsSe{t}"] = f2(b[1] * d[z].std()), f2(np.sqrt(V[1, 1]) * d[z].std())
            M[f"ctFsF{t}"] = f1(b[1] ** 2 / V[1, 1])
    S = pd.read_csv(TAB / "som_fs_seasons.csv")
    RB = pd.read_csv(TAB / "som_fs_robust.csv")
    zmap = {"z_index": "Dep", "E_pred": "Us", "E_loss": "Loss"}
    for r in S.itertuples():
        if r.z not in zmap or r.y not in ("gam", "sam"):
            continue
        t = zmap[r.z] + {"gam": "Gam", "sam": "Sam"}[r.y] + {"gu": "GuTv", "deyr": "DyTv", "gu26": "GuTs"}[r.season]
        M[f"ct{t}"], M[f"ctSe{t}"], M[f"ctP{t}"] = f2(r.b_sd), f2(r.se_sd), f2(r.p_wild)
        M[f"ctN{t}"] = r.n_post
    for r in RB[RB.spec == "main (rain, conflict)"].itertuples():
        t = zmap[r.z] + "GamPool"
        M[f"ct{t}"], M[f"ctSe{t}"], M[f"ctP{t}"] = f2(r.b_sd), f2(r.se_sd), f2(r.p_wild)
    dom = p.drop_duplicates("domain")
    M["ctCorrDepUs"] = f2(dom.z_index.corr(dom.E_pred))
    M["ctCorrDepLoss"] = f2(dom.z_index.corr(dom.E_loss))
    M["ctCorrUsLoss"] = f2(dom.E_pred.corr(dom.E_loss))


# ------------------------------------------------------------------ Fig 4
def fig_displacement(E, X):
    a = E[(E.arr > 0) & E.slow & E.odist.notna()]
    out = a.groupby(["odist", "t"]).arr.sum().rename("out").reset_index()
    cov = E.groupby(["dist", "t"]).site.nunique().rename("sites").reset_index()
    months = sorted(E.t.unique())
    G = pd.MultiIndex.from_product([X.index, months], names=["odist", "t"]).to_frame(index=False)
    G = G.merge(out, how="left").fillna({"out": 0})
    G = G.merge(X[["cash_abs", "pop"]], left_on="odist", right_index=True)
    # months when the tracker was running at scale (>500 site assessments nationally)
    run = cov.groupby("t").sites.sum()
    G = G[G.t.isin(run[run > 500].index)]
    G["post"] = G.t >= "2025-02"
    G = G.dropna(subset=["cash_abs"])
    G["third"] = pd.qcut(G.cash_abs.rank(method="first"), 3, labels=["least cash lost", "middle", "most cash lost"])
    T = G.groupby(["third", "post"], observed=True).apply(lambda s: s.out.sum() / s["pop"].sum() / s.t.nunique() * 1e4)
    T = T.unstack()
    T.columns = ["before", "after"]
    T.to_csv(TAB / "fig4_displacement.csv")
    for t, tt in [("least cash lost", "Lo"), ("most cash lost", "Hi")]:
        M[f"ffour{tt}Pre"], M[f"ffour{tt}Post"] = f1(T.loc[t, "before"]), f1(T.loc[t, "after"])
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    xs = np.arange(3)
    ax.bar(xs - 0.18, T.before, width=0.36, color="#9ec5f0", label="Oct 2023 - Jan 2025")
    ax.bar(xs + 0.18, T.after, width=0.36, color=BLUE, label="Feb 2025 - 2026")
    ax.set_xticks(xs)
    ax.set_xticklabels([str(i) for i in T.index], fontsize=9)
    ax.set_ylabel("People displaced per 10,000\nresidents per month")
    ax.legend(frameon=False, fontsize=8.5)
    ax.set_title("Displacement out of district (drought, hunger, livelihoods),\nmonths with full tracker coverage", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "som_lesson5_displacement.pdf")
    plt.close(fig)


def main():
    F, N, X0 = M75.fsc(), M75.nutrition(), M75.district_frame()
    X = X0.join(pd.read_csv(TAB / "som_fs_districts.csv", index_col=0)[["cash_abs"]])
    E = M73.ett()
    p = pd.read_parquet(INP / "panel" / "som_need_panel.parquet")
    fig_delivery(F, N, E)
    fig_terciles(F, X)
    fig_event(p)
    core_table(F, X, p)
    fig_displacement(E, X)
    (ROOT / "output" / "us_cut_memo" / "numbers_fig.tex").write_text(
        "% generated by code/79_us_cut_figures.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))
    print(json.dumps(M, indent=0))


if __name__ == "__main__":
    main()
