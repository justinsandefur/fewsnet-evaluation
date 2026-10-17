"""Numbers, figures and tables for the CGD working paper (output/cgd_paper/).

Everything quoted in the paper is written to output/cgd_paper/numbers.tex as
LaTeX macros, so the text cannot drift from the code. Inputs are the outputs of
scripts 08, 12, 27, 28, 30-34; this script recomputes the Type I and Type II
statistics for 2011-2024 (before the 2025 shutdown).
"""
import importlib.util
import json
import textwrap
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
OUT = ROOT / "output" / "cgd_paper"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)
STYLE = {"font.family": "sans-serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 9.5, "axes.titleweight": "bold",
                     "axes.titlelocation": "left", "legend.frameon": False, "savefig.bbox": "tight"}
plt.rcParams.update(STYLE)
BLUE, LBLUE, GREY, RED, ORANGE = "#1f4e79", "#9ecae1", "#9e9e9e", "#c0392b", "#e6862e"
N = {}
RAW = {}          # unrounded shares, for numbers derived from other numbers


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    plt.rcParams.update(STYLE)        # some project modules set their own style on import
    return m


def pct(x, d=0):
    return f"{100 * x:.{d}f}"


def sg(v, d=0):
    """Number for running text: no plus sign, typographic minus."""
    t = f"{abs(v):.{d}f}"
    return ("\\textminus{}" + t) if v < 0 and float(t) != 0 else t


def ci(lo, hi, d=0):
    return f"{sg(lo, d)} to {sg(hi, d)}"


# ------------------------------------------------------------------ 1. coverage
def coverage():
    g = pd.read_csv(TAB / "grfc_country_years.csv")
    g = g[g.year <= 2024]
    t3, t4 = g.p3.sum(), g.p4plus.sum()
    N["covPthree"] = pct(g.loc[g.fews, "p3"].sum() / t3)
    N["covPfour"] = pct(g.loc[g.fews, "p4plus"].sum() / t4)
    N["covCountries"] = str(g.iso3.nunique())
    src = g.source.astype(str).str.upper()
    N["grfcFewsSourcePthree"] = pct(g.loc[src.str.contains("FEWS"), "p3"].sum() / t3)
    c = g.groupby(["name", "fews"]).agg(p4=("p4plus", "sum"), p3=("p3", "sum")).reset_index()
    c = c.groupby("name").agg(p4=("p4", "sum"), p3=("p3", "sum"), fews=("fews", "max")).sort_values("p3", ascending=False)
    top = c.head(16)[::-1]
    names = {"Democratic Republic of the Congo": "DR Congo", "Syrian Arab Republic": "Syria",
             "Palestine - Gaza Strip": "Gaza Strip", "Central African Republic": "Central African Rep."}
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    y = np.arange(len(top))
    ax.barh(y, top.p3 / 1e6, color=[BLUE if f else GREY for f in top.fews])
    ax.set_yticks(y, [names.get(n, n) for n in top.index], fontsize=8)
    ax.set_xlabel("Person-years in Crisis or worse (IPC Phase 3+), 2016-2024, millions")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="FEWS NET monitored the country"),
                       Patch(color=GREY, label="FEWS NET did not")], loc="lower right", fontsize=8)
    fig.savefig(FIG / "fig1_coverage.pdf")
    plt.close(fig)
    p = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet")
    N["shareWithIndependent"] = pct(p.ipc_last3.notna().mean())
    N["panelAreas"] = f"{p.fnid.nunique():,}"
    N["panelCountries"] = str(p.country_code.nunique())
    N["panelAreaRounds"] = f"{len(p):,}"
    k = json.loads((TAB / "key_numbers.json").read_text())["outage"]
    N["outBefore"], N["outAug"], N["outOct"] = str(k["countries_before"]), str(k["n_restart_aug25"]), str(k["n_oct25"])
    fts = pd.read_csv(TAB / "funding_by_year.csv")
    fts = fts[(fts.year >= 2011) & (fts.year <= 2024)]
    N["ftsShareFews"] = pct(fts.share_to_fews_countries.mean())
    N["ftsUsFoodShare"] = pct(fts.us_share_of_food_to_fews.mean())


# ------------------------------------------------------------------ 2. Type II
def type2():
    E = load("e", "12_errors.py")
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    cs, proj = cs[cs.month.dt.year <= 2024], proj[proj.report_month.dt.year <= 2024]
    N["csAreaMonths"] = f"{len(cs):,}"
    N["csAreas"] = f"{cs.fnid.nunique():,}"
    N["csCountries"] = str(cs.country_code.nunique())
    ev = E.onsets(cs)
    on, non = ev[ev.onset], ev[~ev.onset]
    fc = E.forecasts_by_lead(ev, proj)
    m = ev[["country_code", "fnid", "month", "onset", "prev_phase", "phase"]].merge(fc, on=["fnid", "month"])
    curve = m.groupby(["onset", "lead"]).fc.agg(n="size", fc4=lambda x: (x >= 4).mean(),
                                                fc3=lambda x: (x >= 3).mean()).reset_index()
    per = m[m.onset].groupby(["fnid", "month"]).fc.agg(any4=lambda x: (x >= 4).any(),
                                                       any3=lambda x: (x >= 3).any()).reset_index()
    early = m[m.onset & (m.lead >= 4)].groupby(["fnid", "month"]).fc.max().clip(upper=4)
    N["tIIonsets"] = f"{len(on):,}"
    N["tIIfromCrisis"] = pct((on.prev_phase == 3).mean())
    N["tIIanyEmergency"] = pct(per.any4.mean())
    N["tIIcrisisOnly"] = pct((per.any3 & ~per.any4).mean())
    N["tIInoWarning"] = pct((~per.any3).mean())
    for k in [1, 4, 8]:
        r = curve[(curve.onset) & (curve.lead == k)].iloc[0]
        N[f"tIIlead{['','one','','','four','','','','eight'][k]}"] = pct(r.fc4)
    N["tIIleadfourCrisis"] = pct(curve[(curve.onset) & (curve.lead == 4)].fc3.iloc[0])
    N["tIIcontrolEmergency"] = pct(curve[~curve.onset].fc4.mean(), 1)
    ed = early.value_counts(normalize=True)
    N["tIIearlyEmergency"], N["tIIearlyCrisis"] = pct(ed.get(4, 0)), pct(ed.get(3, 0))
    RAW["early4"], RAW["early3"] = ed.get(4, 0), ed.get(3, 0)
    N["tIIearlyStressed"] = pct(ed.get(2, 0) + ed.get(1, 0))
    # One panel, with the texture behind the averages: each faint dot is all the areas in one
    # country whose Emergency began in the same month, at one lead (size = number of areas)
    N["tIIepisodes"] = f"{m[m.onset].groupby(['country_code', 'month']).ngroups:,}"
    OR, OR_L, CMP = "#eb6834", "#f5b48f", "#2a78d6"
    fig, a = plt.subplots(figsize=(6.6, 4.3))
    rng = np.random.default_rng(3)
    d = m[m.onset].groupby(["country_code", "month", "lead"]).fc.agg(
        share=lambda x: (x >= 4).mean(), n="size").reset_index()
    N["tIIdotsExtreme"] = pct(d[d.n >= 2].share.isin([0, 1]).mean())
    a.scatter(d.lead + rng.uniform(-0.28, 0.28, len(d)), 100 * d.share, s=4 + 6 * np.sqrt(d.n),
              color=OR, alpha=0.2, edgecolor="none", zorder=2)
    g = curve[curve.onset].sort_values("lead")
    h = curve[~curve.onset].sort_values("lead")
    a.plot(g.lead, 100 * g.fc3, "--", color=OR, lw=1.2, zorder=4)
    a.plot(g.lead, 100 * g.fc4, "o-", color=OR, lw=2.2, ms=5, zorder=5)
    a.plot(h.lead, 100 * h.fc4, "o-", color=CMP, lw=1.6, ms=3.5, zorder=5)
    for k, v in zip(g.lead, g.fc4):
        a.annotate(f"{100 * v:.0f}%", (k, 100 * v), xytext=(0, 8), textcoords="offset points",
                   ha="center", fontsize=7.5, color="#333", fontweight="bold", zorder=6)
    a.text(8.35, 100 * g.fc3.iloc[-1] + 3, "Forecast Crisis or worse", color="#333", fontsize=7.5, ha="left")
    box = dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1)
    a.text(4.75, 100 * g.fc4.iloc[4] - 13, "Forecast Emergency or worse", color="#333", fontsize=7.5,
           ha="left", fontweight="bold", bbox=box)
    a.text(8.35, 100 * h.fc4.iloc[-1] + 6, "Comparison: areas that did not tip into Emergency,\nforecast Emergency",
           color="#333", fontsize=7.5, ha="left", va="bottom", bbox=box)
    a.set_xticks(range(1, 9), [f"{k}" for k in range(1, 9)])
    a.set_xlim(8.5, 0.6)
    a.set_ylim(-4, 104)
    a.set_xlabel("Months between the forecast and the month the Emergency began")
    a.set_ylabel("Share of new Emergencies forecast (%)")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_type2.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ 3. Type I
def type1():
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    cs, proj = cs[cs.month.dt.year <= 2024], proj[proj.report_month.dt.year <= 2024]
    cs = cs.sort_values(["fnid", "month"])
    cs["prev_phase"], cs["prev_flag"] = cs.groupby("fnid").phase.shift(), cs.groupby("fnid").assist_flag.shift()
    fc = proj[(proj.lead >= 4) & (proj.lead <= 8)].sort_values("report_month") \
        .drop_duplicates(["fnid", "month"], keep="last")[["fnid", "month", "phase"]].rename(columns={"phase": "fc"})
    m = cs.merge(fc, on=["fnid", "month"])
    w = m[m.fc >= 4]
    cats = {"came": (w.phase >= 4).mean(), "flag3": ((w.phase == 3) & w.assist_flag).mean(),
            "noflag3": ((w.phase == 3) & ~w.assist_flag).mean(), "better": (w.phase <= 2).mean()}
    N["tIwarnings"] = f"{len(w):,}"
    N["tIcame"], N["tIflagged"] = pct(cats["came"]), pct(cats["flag3"])
    N["tIunflagged"], N["tIbetter"] = pct(cats["noflag3"]), pct(cats["better"])
    N["tIfailed"] = pct(1 - cats["came"])
    RAW.update(came=cats["came"], flag3=cats["flag3"], noflag3=cats["noflag3"], better=cats["better"])
    f3 = w[(w.phase == 3)]
    N["tIflagShareOfCrisis"] = pct(f3.assist_flag.mean())
    unw3 = m[(m.fc < 4) & (m.phase == 3)]
    N["tIflagUnwarnedCrisis"] = pct(unw3.assist_flag.mean())
    ff = w[(w.phase == 3) & w.assist_flag]
    N["tIflaggedAlreadyFlagged"] = pct((ff.prev_flag == True).mean())
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    cname = dict(zip(codes.iso3166a2, codes.preferred_name))
    cname.update({"CD": "DR Congo", "CF": "Central African Rep."})
    w = w.assign(o=np.select([w.phase >= 4, (w.phase == 3) & w.assist_flag, w.phase == 3], ["came", "flag3", "noflag3"], "better"))
    byc = pd.crosstab(w.country_code, w.o, normalize="index").reindex(columns=["came", "flag3", "noflag3", "better"], fill_value=0)
    byc["n"] = w.country_code.value_counts()
    byc = byc[byc.n >= 40].sort_values("came")
    N["tIcountries"] = str(len(byc))
    fig, ax = plt.subplots(2, 1, figsize=(6.5, 1.6 + 0.24 * len(byc)), gridspec_kw={"height_ratios": [1.2, len(byc)]})
    parts = [("came", "Emergency happened", BLUE), ("flag3", "Crisis, flagged by FEWS NET as held back by aid", ORANGE),
             ("noflag3", "Crisis, no aid flag", LBLUE), ("better", "Stressed or better", GREY)]
    a = ax[0]
    left = 0
    for k, lab, c in parts:
        v = cats[k]
        a.barh(0, 100 * v, left=left, color=c, height=0.7, label=lab)
        if v > 0.06:
            a.text(left + 50 * v, 0, f"{100 * v:.0f}%", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        left += 100 * v
    a.set_xlim(0, 100)
    a.set_yticks([0], [f"All countries ({len(w):,})"], fontsize=8, fontweight="bold")
    a.set_xticks([])
    a.spines["bottom"].set_visible(False)
    a.set_title("A. All emergency warnings", fontsize=9)
    a = ax[1]
    y = np.arange(len(byc))
    left = np.zeros(len(byc))
    for k, lab, c in parts:
        a.barh(y, 100 * byc[k], left=left, color=c, height=0.75)
        left += 100 * byc[k].values
    a.set_yticks(y, [f"{cname.get(cc, cc)} ({int(n):,})" for cc, n in zip(byc.index, byc.n)], fontsize=7.5)
    a.set_xlim(0, 100)
    a.set_title("B. By country (number of warned area-months)", fontsize=9)
    a.set_xlabel(f"What happened to area-months that FEWS NET forecast, 4-8 months ahead,\nto be in Emergency or worse (% of warnings)")
    fig.legend(handles=[Patch(color=c, label=lab) for _, lab, c in parts], loc="lower center", ncol=2, fontsize=7.5,
               bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG / "fig3_type1.pdf")
    plt.close(fig)
    # accuracy against "nothing changes" (FEWS NET's own next map)
    p = pd.read_parquet(INP / "panel" / "forecast_value_panel.parquet")
    N["accForecast"] = pct((p.fc_phase == p.next_phase).mean())
    N["accNaive"] = pct((p.phase == p.next_phase).mean())
    ch = p[p.next_phase != p.phase]
    N["accChanges"] = pct((ch.fc_phase == ch.next_phase).mean())
    N["shareChanges"] = pct(len(ch) / len(p))
    up = p[p.next_phase > p.phase]
    N["accWorsenings"] = pct((up.fc_phase >= up.next_phase).mean())
    N["fcPredictsWorsening"] = pct((up.fc_phase > up.phase).mean())


# ------------------------------------------------------------------ 4. FEWS NET vs the official projections
def official():
    d = pd.read_parquet(INP / "panel" / "official_projections.parquet")
    d = d[(d.last3 == 0)].dropna(subset=["fews_fc3"])
    N["offN"], N["offNew"] = f"{len(d):,}", f"{int(d.next3.sum()):,}"
    N["offCountries"] = str(d.iso3.nunique())
    N["offYears"] = f"{d.year.min()}--{d.year.max()}"
    new, old = d[d.next3 == 1], d[d.next3 == 0]
    fz = d.fews_fc3 >= 0.5
    N["offHitOfficial"], N["offHitFews"] = pct(new.proj3.mean()), pct((new.fews_fc3 >= 0.5).mean())
    N["offHitEither"] = pct(((new.proj3 == 1) | (new.fews_fc3 >= 0.5)).mean())
    N["offFaOfficial"], N["offFaFews"] = pct(old.proj3.mean()), pct((old.fews_fc3 >= 0.5).mean())
    N["offFaEither"] = pct(((old.proj3 == 1) | (old.fews_fc3 >= 0.5)).mean())
    N["offHitOnlyFews"] = pct(((new.proj3 == 0) & (new.fews_fc3 >= 0.5)).mean())
    OFF, FEW = "#eb6834", "#2a78d6"
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    curves = {}
    for score, c in [("proj_share3", OFF), ("fews_fc3", FEW)]:
        fpr, tpr, _ = roc_curve(d.next3, d[score])
        curves[score] = (100 * fpr, 100 * (1 - tpr))
        ax.plot(*curves[score], color=c, lw=1.6, zorder=2)
    pts = [(old.proj3.mean(), 1 - new.proj3.mean(), OFF, "o"),
           ((old.fews_fc3 >= 0.5).mean(), 1 - (new.fews_fc3 >= 0.5).mean(), FEW, "s"),
           (((old.proj3 == 1) | (old.fews_fc3 >= 0.5)).mean(), 1 - ((new.proj3 == 1) | (new.fews_fc3 >= 0.5)).mean(), "#222", "D")]
    for x, y, c, mk in pts:
        ax.scatter(100 * x, 100 * y, color=c, marker=mk, s=55, zorder=4, edgecolor="white", linewidth=1.2)
    (xo, yo, *_), (xf, yf, *_), (xe, ye, *_) = pts
    kw = dict(fontsize=8, color="#222", textcoords="offset points")
    ax.annotate("Official IPC / Cadre Harmonis\u00e9\nprojection: area in Crisis or worse", (100 * xo, 100 * yo),
                xytext=(10, 6), **kw)
    ax.annotate("FEWS NET forecast: most of\nthe area in Crisis or worse", (100 * xf, 100 * yf),
                xytext=(1.5, 30), textcoords="data", fontsize=8, color="#222",
                arrowprops=dict(arrowstyle="-", color="#888", lw=0.8))
    ax.annotate("Warn if either one warns", (100 * xe, 100 * ye), xytext=(10, -4), **kw)
    # direct labels for the two threshold curves
    ax.text(41, 26, "Official projections,\nevery threshold", color=OFF, fontsize=8, fontweight="bold")
    ax.text(43, 14.5 + 22, "FEWS NET,\nevery threshold", color=FEW, fontsize=8, fontweight="bold")
    ax.text(59, 97, "Lower and further left is better", ha="right", va="top", fontsize=8, color="#555", style="italic")
    ax.set_xlabel("False alarms (Type I error): share of areas that stayed out of Crisis\nthat were warned about (%)")
    ax.set_ylabel("Misses (Type II error): share of new Crises\nthat were not warned about (%)")
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_official.pdf")
    plt.close(fig)
    R = pd.read_csv(TAB / "official_projections.csv")
    R.to_csv(OUT / "table_official.csv", index=False)


# ------------------------------------------------------------------ 5. contribution beyond a world without FEWS NET
def contribution():
    a = pd.read_csv(TAB / "fewsnet_contribution_auc.csv")
    a = a[a["sample"] == "areas not in Crisis at last analysis"]
    get = lambda b, m: a[(a.baseline == b) & (a.model == m)].auc.iloc[0]
    for b, k in [("raw data", "Raw"), ("raw data + latest Cadre Harmonise / IPC", "RawIPC")]:
        N[f"auc{k}"] = f"{get(b, 'baseline'):.2f}"
        RAW[f"auc{k}"], RAW[f"auc{k}Fews"] = get(b, "baseline"), get(b, "baseline + FEWS NET")
        N[f"auc{k}Fews"] = f"{get(b, 'baseline + FEWS NET'):.2f}"
    N["aucEvents"] = f"{int(a.events.iloc[0]):,}"
    N["aucN"] = f"{int(a.n.iloc[0]):,}"
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    for i, (b, lab) in enumerate([("raw data", "Rainfall, conflict and\nfood prices only"),
                                  ("raw data + latest Cadre Harmonise / IPC", "Plus the latest official\nIPC / Cadre Harmonise analysis")]):
        for j, (mdl, c, nm) in enumerate([("baseline", GREY, "What donors could know without FEWS NET"),
                                          ("baseline + FEWS NET", BLUE, "Adding FEWS NET's current map and forecast")]):
            v = get(b, mdl)
            ax.bar(i + (j - 0.5) * 0.36, v, 0.36, color=c, label=nm if i == 0 else None)
            ax.text(i + (j - 0.5) * 0.36, v + 0.006, f"{v:.2f}", ha="center", fontsize=8.5)
        ax.set_xticks([0, 1], ["Rainfall, conflict and\nfood prices only", "Plus the latest official\nIPC / Cadre Harmonise analysis"], fontsize=8)
    ax.set_ylim(0.5, 1.0)
    ax.set_ylabel("Accuracy in ranking which areas tip into Crisis\n(AUC: 0.5 = coin flip, 1 = perfect)")
    ax.legend(fontsize=7.5, loc="upper left")
    fig.savefig(FIG / "fig5_contribution.pdf")
    plt.close(fig)
    R = pd.read_csv(TAB / "fewsnet_contribution.csv")
    acc = R[R.block.str.startswith("accuracy") & (R["sample"] == "areas not in Crisis at last analysis") & (R.spec == "both")]
    for b, k in [("raw data", "Raw"), ("raw data + latest Cadre Harmonise / IPC", "RawIPC")]:
        for t, kk in [("c_cur3", "Cur"), ("c_fc3", "Fc")]:
            r = acc[(acc.baseline == b) & (acc.term == t)].iloc[0]
            N[f"contrib{k}{kk}"], N[f"contrib{k}{kk}Se"] = f"{r.coef:.2f}", f"{r.se:.2f}"
    R.to_csv(OUT / "table_contribution.csv", index=False)


# ------------------------------------------------------------------ 6. money
def money():
    P = pd.read_csv(TAB / "aid_response_pooled.csv")
    P = P[(P.vars == "together")]
    specs = ["pooled, no controls", "+ time FE (map date)", "+ prior 6-month funding", "+ country FE (within-country)"]
    slab = ["No controls", "+ global funding\nswings (time FE)", "+ country's funding\nin prior 6 months", "+ country's usual\naid level (country FE)"]
    for col, k in [("all", "All"), ("food", "Food")]:
        for ph, kk in [("3+", "Three"), ("4+", "Four")]:
            for t, kt in [("forecast", "Fc"), ("current", "Cur")]:
                for s, ks in [(specs[0], "Pool"), (specs[3], "Within")]:
                    r = P[(P.funding == col) & (P.phase == ph) & (P.term == t) & (P.spec == s)].iloc[0]
                    N[f"aid{k}{kk}{kt}{ks}"] = sg(r.pct)
                    N[f"aid{k}{kk}{kt}{ks}Ci"] = ci(r.lo, r.hi)
    C = pd.read_csv(TAB / "fewsnet_contribution.csv")
    C = C[C.block == "funding"]
    pc = lambda b: 100 * (np.exp(0.1 * b) - 1)
    for b, k in [("raw data", "Raw"), ("raw data + latest Cadre Harmonise / IPC", "RawIPC")]:
        for col, kc in [("all", "All"), ("food", "Food")]:
            for t, kt in [("contrib_fc3", "Contrib"), ("base_fc3", "Base")]:
                r = C[(C.baseline == b) & (C["sample"] == f"{col} funding, within country") & (C.spec == "forecast") & (C.term == t)].iloc[0]
                N[f"money{k}{kc}{kt}"] = sg(pc(r.coef))
                N[f"money{k}{kc}{kt}Ci"] = ci(pc(r.coef - 1.96 * r.se), pc(r.coef + 1.96 * r.se))
    fig, ax = plt.subplots(2, 1, figsize=(6.3, 6.4), gridspec_kw={"height_ratios": [1.15, 1]})
    a = ax[0]
    for j, (t, c, nm) in enumerate([("current", GREY, "Share of areas in Crisis+ on the current map"),
                                    ("forecast", BLUE, "Share of areas FEWS NET forecasts in Crisis+ (4-8 months)")]):
        xs, ys, lo, hi = [], [], [], []
        for i, s in enumerate(specs):
            r = P[(P.funding == "food") & (P.phase == "3+") & (P.term == t) & (P.spec == s)].iloc[0]
            xs.append(i + (j - 0.5) * 0.22)
            ys.append(r.pct)
            lo.append(r.pct - r.lo)
            hi.append(r.hi - r.pct)
        a.errorbar(xs, ys, yerr=[lo, hi], fmt="o", color=c, capsize=2, label=nm)
    a.axhline(0, color="#999", lw=0.8)
    a.set_xticks(range(4), slab, fontsize=7.5)
    a.set_ylabel("% change in food and nutrition\nfunding over the next 6 months,\nper 10 percentage points")
    a.set_title("A. Current map and forecast in the same regression, adding controls left to right")
    a.legend(fontsize=7.5, loc="upper right")
    a = ax[1]
    C2 = C[(C.baseline == "raw data") & (C.spec == "forecast") & C["sample"].str.contains("within country")]
    for i, col in enumerate(["all", "food"]):
        for j, (t, c, nm) in enumerate([("base_fc3", GREY, "Predictable from country, season,\nrainfall, conflict and prices"),
                                        ("contrib_fc3", BLUE, "FEWS NET's own contribution")]):
            r = C2[(C2["sample"].str.startswith(col)) & (C2.term == t)].iloc[0]
            v = pc(r.coef)
            a.errorbar(i + (j - 0.5) * 0.3, v, yerr=[[v - pc(r.coef - 1.96 * r.se)], [pc(r.coef + 1.96 * r.se) - v]],
                       fmt="o", color=c, capsize=2, label=nm if i == 0 else None)
    a.axhline(0, color="#999", lw=0.8)
    a.set_xticks([0, 1], ["All humanitarian funding", "Food and nutrition funding"], fontsize=8)
    a.set_ylabel("% change in funding over the\nnext 6 months, per 10 percentage\npoints of areas forecast in Crisis+")
    a.set_title("B. Which part of the forecast moves money? (all controls)")
    a.legend(fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig6_money.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ 7. masking, shutdown, coverage changes (appendix)
def appendix():
    mk = pd.read_csv(TAB / "forecast_value_masking.csv")
    for oc, k in [("mapped", "Mapped"), ("need", "Need")]:
        for f, kf in [("less than usual", "Low"), ("more than usual", "High")]:
            r = mk[(mk.outcome == oc) & (mk.funding == f)].iloc[0]
            N[f"mask{k}{kf}"] = f"{r.coef:.2f}"
    fv = pd.read_csv(TAB / "forecast_value.csv")
    r = fv[(fv.block == "masking") & (fv.outcome == "mapped")].iloc[0]
    N["maskInter"], N["maskInterSe"] = f"{r.coef:.3f}", f"{r.se:.3f}"
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    order = ["less than usual", "about usual", "more than usual"]
    for j, (oc, c, nm) in enumerate([("mapped", RED, "Outcome as mapped"),
                                     ("need", BLUE, "Outcome by need (mapped phase,\nplus one if flagged as held up by aid)")]):
        d = mk[mk.outcome == oc].set_index("funding").reindex(order)
        x = np.arange(3) + (j - 0.5) * 0.15
        ax.errorbar(x, d.coef, yerr=1.96 * d.se, fmt="o-", color=c, capsize=3, label=nm)
    ax.set_xticks(range(3), ["Funding rose less\nthan usual", "About as usual", "More than usual"], fontsize=8)
    ax.set_xlabel("Humanitarian funding to the country in the 6 months after the forecast")
    ax.set_ylabel("Share of FEWS NET's distinctive warnings\nborne out on its next map")
    ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2)
    fig.savefig(FIG / "figA1_masking.pdf")
    plt.close(fig)
    # 2025 shutdown: flagged areas, 12-month comparisons
    fr = pd.read_csv(TAB / "flag_release.csv")
    for v, k in [("A. FEWS NET's own later maps", "Own"), ("B. Cadre Harmonise / IPC", "Ipc")]:
        r = fr[(fr.version == v) & (fr.horizon == "12 months") & (fr.outcome == "dphase") & (fr.spec == "flagged x exposed")].iloc[0]
        N[f"flag{k}"], N[f"flag{k}Se"], N[f"flag{k}P"] = sg(r.coef, 2), f"{r.se:.2f}", f"{r.wild_p:.2f}"
        N[f"flag{k}Placebo"] = f"{r.flag_gap_unexposed:.2f}"
    yf = pd.read_csv(TAB / "flag_release_by_year_fews.csv")
    yi = pd.read_csv(TAB / "flag_release_by_year_ipc_phase.csv")
    fig, ax = plt.subplots(1, 2, figsize=(6.8, 3.0), sharey=True)
    for a, d, t in [(ax[0], yf, "A. FEWS NET's own later maps"), (ax[1], yi, "B. Official IPC / Cadre Harmonise")]:
        d = d[(d.hm == 12) & (d.year >= 2014)]
        for r in d.itertuples():
            c = RED if r.year >= 2025 else BLUE
            a.errorbar(r.year, r.coef, yerr=1.96 * r.se, fmt="o", color=c, capsize=2, ms=4)
        a.axhline(0, color="#999", lw=0.8)
        a.axvline(2024.5, color=RED, ls="--", lw=0.8)
        a.set_title(t)
        a.set_xlabel("Year of the later classification")
    ax[0].set_ylabel("Extra worsening of flagged areas\nover 12 months (phases)")
    for a in ax:
        a.text(2024.4, a.get_ylim()[0] + 0.05, "US aid cut ", color=RED, fontsize=7.5, ha="right", va="bottom")
    fig.tight_layout()
    fig.savefig(FIG / "figA2_shutdown.pdf")
    plt.close(fig)
    # coverage changes x local shocks
    S = pd.read_csv(TAB / "shock_index_results.csv")
    pw = pd.read_csv(TAB / "shock_index_power.csv")
    N["shockRsq"] = pct(pw[(pw.fe == "area + country x month FE") & (pw.outcome == "share3") & (pw.shocks == "all three")].within_r2.iloc[0], 1)
    N["shockRsqRain"] = pct(pw[(pw.fe == "area + country x month FE") & (pw.outcome == "share3") & (pw.shocks == "rainfall")].within_r2.iloc[0], 2)
    for samp, k in [("pre-2025", "Pre"), ("2025-26 (shutdown and restoration)", "Post")]:
        r = S[(S.outcome == "share3") & (S["sample"] == samp) & (S.spec.str.startswith("country-specific")) & (S.term == "index x FEWS NET covering")].iloc[0]
        N[f"cov{k}"], N[f"cov{k}Se"] = sg(r.coef, 3), f"{r.se:.3f}"
    r = S[(S.outcome == "phase3") & (S["sample"] == "pre-2025") & (S.spec.str.startswith("country-specific")) & (S.term == "index x FEWS NET covering")].iloc[0]
    N["covPrePhase"], N["covPrePhaseSe"] = sg(r.coef, 3), f"{r.se:.3f}"
    # need-defined emergencies: how many held back by aid were flag switches in steady Phase 3 areas
    E = pd.read_parquet(INP / "panel" / "need_onsets.parquet")
    E = E[E.onset == "Emergency"]
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet").sort_values(["fnid", "month"])
    cs["prev_phase"] = cs.groupby("fnid").phase.shift()
    E = E.merge(cs[["fnid", "month", "prev_phase"]], on=["fnid", "month"], how="left", suffixes=("", "_cs"))
    held = E[E.averted == 1]
    N["needOnsets"], N["needHeld"] = f"{len(E):,}", pct(E.averted.mean())
    N["needHeldSteady"] = pct((held.prev_phase_cs == 3).mean() if "prev_phase_cs" in held else (held.prev_phase == 3).mean())
    no = pd.read_csv(TAB / "need_onsets.csv")
    r = no[(no.onset == "Emergency") & (no.warning_defn == "forecast need (phase + flag)") & (no.term == "early")].iloc[0]
    N["needEarly"], N["needEarlySe"] = sg(100 * r.coef), f"{100 * r.se:.0f}"


def bootstrap():
    b = OUT / "bootstrap.json"
    if b.exists():
        j = json.loads(b.read_text())
        N["bootOffAllFews"], N["bootOffNewFews"] = f"{j['official_all_fews_fc3']:.3f}", f"{j['official_new_fews_fc3']:.3f}"
        N["bootOffAllProj"], N["bootOffNewProj"] = f"{j['official_all_proj3']:.3f}", f"{j['official_new_proj3']:.3f}"
    R = pd.read_csv(TAB / "official_projections.csv")
    g = lambda samp, sp, t: R[(R["sample"] == samp) & (R.spec == sp) & (R.term == t)].iloc[0]
    for samp, k in [("all areas", "All"), ("not in Crisis at the last analysis", "New")]:
        sp = "both + last official analysis" if samp == "all areas" else "both"
        N[f"offCoef{k}Fews"], N[f"offCoef{k}Proj"] = f"{g(samp, sp, 'fews_fc3').coef:.2f}", f"{g(samp, sp, 'proj3').coef:.2f}"
    N["offNall"] = f"{int(g('all areas', 'both', 'proj3').n):,}"
    N["offCountriesAll"] = str(int(g("all areas", "both", "proj3").countries))
    o = pd.read_json(ROOT / "output" / "tables" / "key_numbers.json", typ="series") if False else None


def r2(v):
    """Two significant figures, with thousands separators."""
    from math import floor, log10
    if v == 0 or pd.isna(v):
        return "n.a."
    d = -int(floor(log10(abs(v)))) + 1
    return f"{round(v, d):,.0f}"


def benefit():
    """Macros for the benefit-cost section (inputs from 36_benefit_cost.py)."""
    k = json.loads((TAB / "benefit_cost_key.json").read_text())
    R = pd.read_csv(TAB / "benefit_cost.csv")
    R = R[R.budget == "central"]
    N["bcBudget"], N["bcBudgetLow"], N["bcBudgetHigh"] = "45", "35", "65"
    N["bcFlaggedRounds"] = f"{k['flagged_area_rounds']:,}"
    N["bcFlaggedAreas"] = f"{k['flagged_areas']:,}"
    N["bcPeople"] = f"{k['avg_people_flagged'] / 1e6:.0f}"
    for m, km in [("low", "Cons"), ("central", "Mid"), ("high", "Up")]:
        N[f"bcGross{km}"] = f"{k['gross_deaths'][m] / 1e3:,.0f}"
    N["bcGrossCrisis"] = f"{k['gross_crisis_py'] / 1e6:.1f}"
    N["bcPhaseTwo"], N["bcPhaseThree"] = pct(k["share_phase"]["2"]), pct(k["share_phase"]["3"])
    N["bcSthreeCrisis"], N["bcSthreeStressed"] = pct(k["s3"]["3"]), pct(k["s3"]["2"])
    N["bcSthreeEmerg"], N["bcSfourEmerg"] = pct(k["s3"]["4"]), pct(k["s4"]["4"])
    names = {"A1": "One", "A2": "Two", "A3": "Three", "A4": "Four", "A5": "Five"}
    for a, ka in names.items():
        d = R[R.attribution == a].set_index("mortality")
        N[f"bcShare{ka}"] = pct(d.loc["central", "mean_share_attributed"], 1 if abs(d.loc["central", "mean_share_attributed"]) < 0.1 else 0).replace("-", "\\textminus{}")
        N[f"bcBeta{ka}"] = f"{d.loc['central', 'beta'] / 10 * 100:.0f}"
        for m, km in [("low", "Cons"), ("central", "Mid"), ("high", "Up")]:
            dd, cc = d.loc[m, "deaths_per_year"], d.loc[m, "cost_per_death"]
            N[f"bcDeaths{ka}{km}"] = ("\\textminus{}" if dd < 0 else "") + f"{abs(round(dd, -2)):,.0f}"
            N[f"bcCost{ka}{km}"] = r2(cc) if pd.notna(cc) else "n.a."
        N[f"bcCrisis{ka}"] = sg(d.loc["central", "crisis_person_years"] / 1e6, 1)
    # ranges over mortality scenarios for the two families of attribution
    pos = R[R.cost_per_death.notna()]
    di, wh = pos[pos.attribution.isin(["A1", "A2", "A3"])], pos[pos.attribution.isin(["A4", "A5"])]
    N["bcDistinctLo"], N["bcDistinctHi"] = r2(di.cost_per_death.min()), r2(di.cost_per_death.max())
    N["bcWholeLo"], N["bcWholeHi"] = r2(wh.cost_per_death.min()), r2(wh.cost_per_death.max())
    O = pd.read_csv(TAB / "benefit_cost_onesided.csv")
    O = O[(O.budget == "central") & O.attribution.isin(["A1", "A2", "A3"])]
    N["bcOneLo"], N["bcOneHi"] = r2(O.cost_per_death.min()), r2(O.cost_per_death.max())
    N["bcOneShareFood"] = sg(100 * O[(O.attribution == "A3") & (O.mortality == "central")].mean_share_attributed.iloc[0], 1)
    for a, ka in [("A4", "Four"), ("A5", "Five")]:
        py = R[(R.attribution == a) & (R.mortality == "central")].crisis_person_years.iloc[0]
        N[f"bcCostCrisis{ka}"] = f"{45e6 / py:,.0f}"
    B = pd.read_csv(TAB / "benefit_cost.csv")
    wb = B[B.attribution.isin(["A4", "A5"])]
    N["bcWholeLoBudgetLo"], N["bcWholeHiBudgetHi"] = r2(wb.cost_per_death.min()), r2(wb.cost_per_death.max())
    w = R[(R.attribution.isin(["A4", "A5"])) & (R.mortality == "low")].child_wasting_years
    N["bcWastingLo"], N["bcWastingHi"] = r2(w.min()), r2(w.max())


def distinct():
    """Headline benefit-cost numbers: FEWS NET credited only with its distinctive information (A1-A3)."""
    R = pd.read_csv(TAB / "benefit_cost.csv")
    R = R[(R.budget == "central") & R.attribution.isin(["A1", "A2", "A3"])]
    c = R[R.mortality == "central"]
    N["dDeathsLo"], N["dDeathsHi"] = r2(R.deaths_per_year.min()), r2(R.deaths_per_year.max())
    N["dEmergLo"], N["dEmergHi"] = r2(c.emergency_person_years.min()), r2(c.emergency_person_years.max())
    ce = c.budget_usd / c.emergency_person_years
    N["dCostEmergLo"], N["dCostEmergHi"] = r2(ce.min()), r2(ce.max())
    N["dCrisisLo"], N["dCrisisHi"] = r2(c.crisis_person_years.min()), r2(c.crisis_person_years.max())
    cc = c.budget_usd / c.crisis_person_years
    N["dCostCrisisLo"], N["dCostCrisisHi"] = r2(cc.min()), r2(cc.max())
    N["dWastLo"], N["dWastHi"] = r2(c.child_wasting_years.min()), r2(c.child_wasting_years.max())
    cw = c.budget_usd / c.child_wasting_years
    N["dCostWastLo"], N["dCostWastHi"] = r2(cw.min()), r2(cw.max())
    aw = R.budget_usd / R.child_wasting_years
    N["dCostWastMin"], N["dCostWastMax"] = r2(aw.min()), r2(aw.max())
    N["dShareLo"], N["dShareHi"] = f"{100 * c.mean_share_attributed.min():.1f}", f"{100 * c.mean_share_attributed.max():.1f}"
    W = pd.read_csv(TAB / "benefit_cost.csv")
    W = W[(W.budget == "central") & W.attribution.isin(["A4", "A5"])]
    N["wholeLo"], N["wholeHi"] = r2(W.cost_per_death.min()), r2(W.cost_per_death.max())
    all_d = pd.read_csv(TAB / "benefit_cost.csv")
    all_d = all_d[all_d.attribution.isin(["A1", "A2", "A3"])]
    N["dCostBudgetLo"], N["dCostBudgetHi"] = r2(all_d.cost_per_death.min()), r2(all_d.cost_per_death.max())


def cases():
    j = json.loads((TAB / "case_maps.json").read_text())
    for k, kk in [("somalia", "So"), ("ethiopia", "Et")]:
        c = j[k]
        N[f"case{kk}Areas"], N[f"case{kk}FcFour"], N[f"case{kk}NextFour"] = str(c["areas"]), str(c["fc4"]), str(c["next4"])
        N[f"case{kk}CurFour"], N[f"case{kk}Flags"], N[f"case{kk}FlagShare"] = str(c["cur4"]), str(c["flags"]), pct(c["flag_share"])
        N[f"case{kk}Rain"] = sg(c["rain_z6"], 1)
        N[f"case{kk}NextThree"], N[f"case{kk}CurThree"] = str(c["next3"]), str(c["cur3"])


def hetero():
    """Does funding follow FEWS NET's distinctive information more where official analyses are scarce?"""
    AID = load("aid", "31_aid_response.py")
    s = AID.panel()
    p = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet")
    c = p.groupby(["country_code", "r"]).agg(contrib=("c_fc3", "mean"), base=("b_fc3", "mean"),
                                             ipc=("ipc_last3", lambda v: v.notna().mean())).reset_index()
    s = s.merge(c, left_on=["country_code", "report_month"], right_on=["country_code", "r"])
    s["hi"] = (s.ipc > 0.5).astype(float)
    N["hetShareHigh"] = pct(s.hi.mean())
    s["cx"], s["bx"] = s.contrib * s.hi, s.base * s.hi
    for col, k in [("all", "All"), ("food", "Food")]:
        r, n, G = AID.DID.fe_ols(s, f"f_{col}", ["base", "contrib", "bx", "cx", f"f_{col}_lag"], ["iso3", "round"])
        lo, hi_ = r.coef["contrib"], r.coef["contrib"] + r.coef["cx"]
        N[f"het{k}Low"], N[f"het{k}High"] = f"{100 * (np.exp(0.1 * lo) - 1):.0f}", f"{100 * (np.exp(0.1 * hi_) - 1):.0f}"
        N[f"het{k}DiffSe"] = f"{r.se['cx']:.2f}"
        N[f"het{k}Diff"] = sg(r.coef["cx"], 2)


def budget_and_cg():
    """FEWS NET's budget from USAspending, and the benefit-cost in Coefficient Giving's units."""
    ob = json.loads((TAB / "fewsnet_obligations.json").read_text())
    fy = {}
    for a, d in ob.items():
        for y, v in d.items():
            fy[int(y)] = fy.get(int(y), 0) + v
    N["obAvgLong"] = f"{np.mean([fy.get(y, 0) for y in range(2017, 2025)]) / 1e6:.0f}"
    N["obAvgCore"] = f"{np.mean([fy.get(y, 0) for y in range(2019, 2024)]) / 1e6:.0f}"
    N["obPeak"] = f"{fy[2023] / 1e6:.0f}"
    N["obMin"] = f"{min(fy.get(y, 0) for y in range(2017, 2025)) / 1e6:.0f}"
    N["obPillarOne"] = f"{sum(ob['7200AA19F00018'].values()) / 1e6:.0f}"
    R = pd.read_csv(TAB / "benefit_cost.csv")
    d = R[(R.budget == "central") & R.attribution.isin(["A1", "A2", "A3"])]
    for dpd, k in [(30, "Thirty"), (40, "Forty"), (55, "Fifty")]:
        x = d.deaths_per_year * dpd * 1e5 / d.budget_usd
        N[f"cg{k}Lo"], N[f"cg{k}Hi"] = r2(x.min()), r2(x.max())
    dd = R[R.attribution.isin(["A1", "A2", "A3"]) & (R.mortality == "central")]
    x = dd.deaths_per_year * 40 * 1e5 / dd.budget_usd
    N["cgBudgetLo"], N["cgBudgetHi"] = r2(x.min()), r2(x.max())
    h = [d.emergency_person_years * np.log(1 + g) * 5e4 / d.budget_usd for g in (0.10, 0.25)]
    N["cgHungerLo"], N["cgHungerHi"] = f"{min(v.min() for v in h):.0f}", f"{max(v.max() for v in h):.0f}"
    W = R[(R.budget == "central") & R.attribution.isin(["A4", "A5"])]
    xw = W.deaths_per_year * 40 * 1e5 / W.budget_usd
    N["cgWholeLo"], N["cgWholeHi"] = r2(xw.min()), r2(xw.max())
    # sensitivity: the IPC reference bands instead of the evidence-based calibration
    I = pd.read_csv(TAB / "benefit_cost_ipcbands.csv")
    di = I[(I.budget == "central") & I.attribution.isin(["A1", "A2", "A3"])]
    N["ipcDistinctLo"], N["ipcDistinctHi"] = r2(di.cost_per_death.min()), r2(di.cost_per_death.max())
    N["ipcDeathsLo"], N["ipcDeathsHi"] = r2(di.deaths_per_year.min()), r2(di.deaths_per_year.max())
    x = di.deaths_per_year * 40 * 1e5 / di.budget_usd
    N["ipcCgLo"], N["ipcCgHi"] = r2(x.min()), r2(x.max())
    ki = json.loads((TAB / "benefit_cost_key_ipcbands.json").read_text())
    for m, km in [("low", "Cons"), ("central", "Mid"), ("high", "Up")]:
        N[f"ipcGross{km}"] = f"{ki['gross_deaths'][m] / 1e3:,.0f}"
    wi = I[(I.budget == "central") & I.attribution.isin(["A4", "A5"])]
    N["ipcWholeLo"], N["ipcWholeHi"] = r2(wi.cost_per_death.min()), r2(wi.cost_per_death.max())
    # the cost-effectiveness bar in cost per death, at 40 DALYs per death
    N["cgBarPerDeath"] = r2(40 * 1e5 / 1000)


def predictable():
    """What the public-data benchmark of FEWS NET's forecast actually captures."""
    p = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet").dropna(subset=["b_fc3"])
    p["cm"] = p.country_code + "_" + p.r.dt.month.astype(str)
    fit = p.groupby("cm").b_fc3.transform("mean")
    N["predCountrySeason"] = pct(1 - ((p.b_fc3 - fit) ** 2).sum() / ((p.b_fc3 - p.b_fc3.mean()) ** 2).sum())
    w = p.b_fc3 - fit
    wf = p.fc3 - p.groupby("cm").fc3.transform("mean")
    N["predShocksWithin"] = pct(np.corrcoef(w, wf)[0, 1] ** 2)
    c = p.groupby(["country_code", "r"])[["b_fc3", "c_fc3"]].mean().reset_index()
    for v, k in [("b_fc3", "Base"), ("c_fc3", "Contrib")]:
        N[f"pred{k}Sd"] = f"{c[v].std():.2f}"
        N[f"pred{k}SdWithin"] = f"{(c[v] - c.groupby('country_code')[v].transform('mean')).std():.2f}"


def write_numbers():
    lines = ["% generated by code/40_paper.py -- do not edit"]
    for k, v in sorted(N.items()):
        assert k.isalpha(), k
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    (OUT / "numbers.tex").write_text("\n".join(lines) + "\n")
    (OUT / "numbers.json").write_text(json.dumps(N, indent=1))
    print(json.dumps(N, indent=1))


LABELS = {"fc4": "FEWS NET forecast: Emergency", "flag": "Aid flag now", "fc_flag": "Aid flag in forecast",
          "t_proj4": "Report: Emergency projected", "t_worst4": "Report: worst case Emergency or Famine",
          "t_det": "Report: deterioration expected", "t_aid_down": "Report: aid expected to fall",
          "t_access": "Report: access constrained", "t_conflict": "Report: conflict or displacement",
          "t_rain": "Report: poor rains or harvest", "t_prices": "Report: high prices or currency",
          "t_uncert": "Report: uncertainty stated", "t_mention": "Area discussed in reports",
          "s_any": "Survey in previous 12 months", "s_gam15": "Survey: acute malnutrition 15\\%+",
          "s_mort": "Survey: death rate above emergency threshold", "g_any": "Report: data gap stated"}


def text_table():
    """Appendix table: escalation from Crisis on map, text and data features."""
    r = pd.read_csv(TAB / "text_value_escalation.csv")
    cols = [("next4", "map"), ("next4", "map+text"), ("next4", "map+text+data"),
            ("need4", "map"), ("need4", "map+text"), ("need4", "map+text+data")]
    lines = ["\\begin{tabular}{l" + "c" * len(cols) + "}", "\\toprule",
             " & \\multicolumn{3}{c}{Emergency+ on next map} & \\multicolumn{3}{c}{Emergency+ by need} \\\\",
             "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}",
             " & " + " & ".join(f"({i + 1})" for i in range(len(cols))) + " \\\\", "\\midrule"]
    for v, lab in LABELS.items():
        cells, ses = [], []
        for y, m in cols:
            x = r[(r.outcome == y) & (r.model == m) & (r["var"] == v)]
            if x.empty:
                cells.append(""); ses.append("")
                continue
            b, se = x.coef.iloc[0], x.se.iloc[0]
            t = abs(b / se) if se > 0 else 0
            star = "***" if t > 2.576 else "**" if t > 1.96 else "*" if t > 1.645 else ""
            cells.append(f"{b:.3f}{star}"); ses.append(f"({se:.3f})")
        lines.append(lab + " & " + " & ".join(cells) + " \\\\")
        lines.append(" & " + " & ".join(ses) + " \\\\")
    n = r.groupby(["outcome", "model"]).n.first()
    lines += ["\\midrule", "Area-rounds & " + " & ".join(f"{n[c]:,}" for c in cols) + " \\\\",
              "\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "text.tex").write_text("\n".join(lines) + "\n")


def boot_gain(df, y, a, b, cluster, reps=500, seed=1):
    """AUC(b) - AUC(a) and a 95 percent interval resampling clusters (country-years)."""
    from sklearn.metrics import roc_auc_score
    df = df.dropna(subset=[a, b])
    point = roc_auc_score(df[y], df[b]) - roc_auc_score(df[y], df[a])
    groups = {k: v.index.values for k, v in df.groupby(cluster)}
    keys = np.array(list(groups))
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(reps):
        idx = np.concatenate([groups[k] for k in rng.choice(keys, len(keys))])
        s = df.loc[idx]
        if s[y].nunique() == 2:
            out.append(roc_auc_score(s[y], s[b]) - roc_auc_score(s[y], s[a]))
    lo, hi = np.percentile(out, [2.5, 97.5])
    return point, lo, hi


def fig_information():
    """What information improves the forecast? AUC gains with bootstrap intervals, and what moves the maps."""
    pv = pd.read_parquet(INP / "panel/price_value_preds.parquet")
    pv["cy"] = pv.country_code + pv.r.str[:4]
    pv = pv.reset_index(drop=True)
    rows = []
    specs = [("Starting from public data\n(country, season, rainfall, conflict)", [
                 ("WFP prices", "raw", "raw +WFP prices"),
                 ("FEWS NET's own prices", "raw", "raw +FEWS NET prices"),
                 ("Both price sources", "raw", "raw +both"),
                 ("FEWS NET's map and forecast", "raw", "raw +FEWS NET map and forecast")]),
             ("Starting from FEWS NET's current maps", [
                 ("Both price sources", "base", "+both"),
                 ("FEWS NET's forecast", "base", "+forecast")])]
    for group, items in specs:
        for lab, a, b in items:
            for task in ["new crisis", "escalation"]:
                d = pv[pv.task == task].reset_index(drop=True)
                g, lo, hi = boot_gain(d, "y", a, b, "cy")
                rows.append(dict(group=group, label=lab, task=task, gain=g, lo=lo, hi=hi))
    tp = pd.read_parquet(INP / "reports/text_value_preds.parquet")
    tp["cy"] = tp.country_code + tp.r.str[:4]
    tp = tp.reset_index(drop=True)
    g, lo, hi = boot_gain(tp, "next4", "next4_map", "next4_text", "cy")
    rows.append(dict(group="Starting from FEWS NET's current maps", label="Report text (pilot: 3 countries)",
                     task="escalation", gain=g, lo=lo, hi=hi))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "information_gains.csv", index=False)
    def gain(label, task):
        return f"{100 * R[(R.label == label) & (R.task == task)].gain.iloc[0]:.0f}"
    N["infoMapNew"], N["infoMapEsc"] = gain("FEWS NET's map and forecast", "new crisis"), gain("FEWS NET's map and forecast", "escalation")
    N["infoFcNew"], N["infoFcEsc"] = gain("FEWS NET's forecast", "new crisis"), gain("FEWS NET's forecast", "escalation")

    ns = pd.read_csv(TAB / "text_value_new_survey.csv")
    ns = ns[ns.controls == "all text"].set_index("outcome")

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.2, 4.4), gridspec_kw={"width_ratios": [1.9, 1], "wspace": 0.55})
    col = {"new crisis": BLUE, "escalation": ORANGE}
    mk = {"new crisis": "o", "escalation": "s"}
    y, ticks, labels, heads = 0, [], [], []
    for group, items in specs + [(None, [])]:
        if group is None:
            break
        heads.append((y, group))
        y -= 0.9
        labs = list(dict.fromkeys([l for l, _, _ in items]))
        if group.startswith("Starting from FEWS"):
            labs.append("Report text (pilot: 3 countries)")
        for lab in labs:
            for task, off in [("new crisis", 0.17), ("escalation", -0.17)]:
                r = R[(R.group == group) & (R.label == lab) & (R.task == task)]
                if r.empty:
                    continue
                r = r.iloc[0]
                ax.errorbar(100 * r.gain, y + off, xerr=[[100 * (r.gain - r.lo)], [100 * (r.hi - r.gain)]],
                            fmt=mk[task], color=col[task], ms=5, lw=1.4, capsize=0,
                            label=None)
            ticks.append(y); labels.append(lab)
            y -= 1
        y -= 0.4
    ax.axvline(0, color=GREY, lw=0.8)
    ax.set_yticks(ticks); ax.set_yticklabels(labels, fontsize=8)
    for yy, g in heads:
        ax.text(-0.75, yy, g.replace("\n", " "), transform=ax.get_yaxis_transform(), ha="left", va="center",
                fontsize=8, fontweight="bold", color="#333333")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_ylim(y + 0.6, 0.6)
    ax.set_xlabel("Gain in AUC (points out of 100)")
    ax.set_title("A. Which information improves the forecast?")
    ax.grid(axis="x", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker="o", color=BLUE, ls="", ms=5, label="New crises"),
                       Line2D([], [], marker="s", color=ORANGE, ls="", ms=5, label="Escalation")],
              loc="upper right", bbox_to_anchor=(1.0, 0.9), fontsize=7.5, handletextpad=0.3)

    items = [("next4", "Crisis area reaches\nEmergency"), ("up", "Next map worse\nthan forecast"),
             ("down", "Next map better\nthan forecast")]
    for i, (k, lab) in enumerate(items):
        r = ns.loc[k]
        bx.errorbar(100 * r.coef, -i, xerr=196 * r.se, fmt="D", color=BLUE, ms=5, lw=1.4)
        bx.text(100 * r.coef, -i - 0.32, f"base rate {100 * r.base:.0f}%", ha="center", va="top", fontsize=7, color="#555555")
    bx.axvline(0, color=GREY, lw=0.8)
    bx.set_yticks([-i for i in range(len(items))]); bx.set_yticklabels([l for _, l in items], fontsize=8)
    bx.tick_params(axis="y", length=0); bx.spines["left"].set_visible(False)
    bx.set_ylim(-len(items) + 0.3, 0.6)
    bx.set_xlabel("Change when a new survey arrives\n(percentage points)")
    bx.set_title("B. What moves FEWS NET's maps?")
    bx.grid(axis="x", color="#e6e6e6", lw=0.6); bx.set_axisbelow(True)
    fig.savefig(FIG / "fig8_information.pdf")
    plt.close(fig)


def fig_fsnau():
    """Somalia's scheduled surveys: measured malnutrition against FEWS NET's forecast and the last survey."""
    d = pd.read_csv(TAB / "fsnau_value_panel.csv")
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.0, 3.2), gridspec_kw={"wspace": 0.35})
    d["ph"] = d.fc.round().clip(2, 4)
    g = d.groupby("ph").gam.agg(["mean", "std", "size"])
    se = g["std"] / np.sqrt(g["size"])
    ax.errorbar(g.index, g["mean"], yerr=1.96 * se, fmt="o", color=BLUE, ms=6, lw=1.4)
    for x, r in g.iterrows():
        ax.text(x + 0.08, r["mean"], f"n={int(r['size'])}", fontsize=7, color="#555555", va="center")
    ax.axhline(15, color=GREY, lw=0.8, ls="--")
    ax.text(1.65, 15.4, "critical (15%)", fontsize=7, color="#555555", ha="left")
    ax.set_xticks([2, 3, 4]); ax.set_xticklabels(["Stressed\nor better", "Crisis", "Emergency\nor worse"], fontsize=8)
    ax.set_xlim(1.6, 4.6); ax.set_ylim(0, 25)
    ax.set_ylabel("Acute malnutrition, children under 5 (%)")
    ax.set_title("A. By FEWS NET's forecast for the zone")
    bx.scatter(d.gam_lag, d.gam, s=9, color=BLUE, alpha=0.45, linewidths=0)
    lim = [0, max(d.gam.max(), d.gam_lag.max()) + 2]
    bx.plot(lim, lim, color=GREY, lw=0.8, ls="--")
    b = np.polyfit(d.gam_lag, d.gam, 1)
    xs = np.linspace(lim[0], lim[1], 50)
    bx.plot(xs, b[1] + b[0] * xs, color=ORANGE, lw=1.6)
    bx.set_xlim(lim); bx.set_ylim(lim)
    bx.set_xlabel("Previous round (%)"); bx.set_ylabel("This round (%)")
    bx.set_title("B. Against the zone's previous survey")
    for a_ in (ax, bx):
        a_.grid(axis="y", color="#e6e6e6", lw=0.6); a_.set_axisbelow(True)
    fig.savefig(FIG / "fig9_fsnau.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ what a phase means (57, 58)
def phase_outcomes():
    """Measured malnutrition and mortality by phase: Somalia within zones, and other countries."""
    W = pd.read_csv(TAB / "fsnau_value_within.csv").set_index(["outcome", "phase", "fe"])
    for y, yt in [("gam", "Gam"), ("cdr", "Cdr"), ("u5dr", "Ufive")]:
        for fe, ft in [("key", "Zone"), ("key+t", "ZoneSeason")]:
            r = W.loc[(y, "fc", fe)]
            d = 1 if y == "gam" else 2
            N[f"wz{yt}{ft}"], N[f"wz{yt}{ft}Se"] = f"{r.coef:.{d}f}", f"{r.se:.{d}f}"
            r = W.loc[(y, "after", fe)]
            N[f"wz{yt}{ft}Map"], N[f"wz{yt}{ft}MapSe"] = f"{r.coef:.{d}f}", f"{r.se:.{d}f}"
    k = json.loads((TAB / "phase_outcomes_key.json").read_text())
    P = pd.read_csv(TAB / "phase_outcomes.csv")
    sp = P[(P.source == "SMART+ all") & (P.measure == "fews_cur")].set_index("phase")
    for ph, tag in [("1", "One"), ("2", "Two"), ("3", "Three"), ("4+", "Four")]:
        N[f"spGam{tag}"] = f"{sp.loc[ph, 'gam_mean']:.0f}"
        N[f"spCdr{tag}"] = f"{sp.loc[ph, 'cdr_mean']:.2f}"
    m = k["match"]
    N["spN"], N["spNfews"] = str(m["SMART+ all"]["n"]), str(m["SMART+ all"]["fews_cur"])
    N["spNround"] = str(m["SMART+ Nigeria rounds"]["n"])
    N["fdwN"], N["fdwNfews"] = str(m["FDW (BF, MR)"]["n"]), str(m["FDW (BF, MR)"]["fews_cur"])
    c = k["corr"]
    N["spCorr"] = f"{c['SMART+ all']['fews_cur']['gam']:.2f}"
    N["fdwCorr"] = f"{c['FDW (BF, MR)']['fews_cur']['gam']:.2f}"
    o = k["ols"]
    g = o["SMART+ all"]["fews_cur"]["gam_country_year_fe"]
    N["spSlope"], N["spSlopeSe"] = f"{g['coef']:.1f}", f"{g['se']:.1f}"
    g = o["SMART+ all"]["fews_cur"]["cdr_country_year_fe"]
    N["spCdrSlope"], N["spCdrSlopeSe"] = sg(g["coef"], 2), f"{g['se']:.2f}"
    g = o["SMART+ all"]["ipc_ch"]["cdr_country_year_fe"]
    N["spCdrSlopeIpc"], N["spCdrSlopeIpcSe"] = f"{g['coef']:.2f}", f"{g['se']:.2f}"
    g = o["SMART+ Nigeria rounds"]["ipc_ch"]["gam_country_year_fe"]
    N["ngSlope"], N["ngSlopeSe"] = f"{g['coef']:.1f}", f"{g['se']:.1f}"
    g = o["FDW (BF, MR)"]["fews_cur"]["gam_country_year_fe"]
    N["fdwSlope"], N["fdwSlopeSe"] = f"{g['coef']:.1f}", f"{g['se']:.1f}"
    a = k["amn"]
    N["amnExpN"], N["amnExpCorr"] = str(a["AMN explicit"]["n"]), f"{a['AMN explicit']['corr']:.2f}"
    N["amnExpAgree"] = pct(a["AMN explicit"]["exact_agree"])
    dk = [x for x in a if x.lower().startswith("amn derived")][0]
    N["amnDerN"], N["amnDerCorr"] = str(a[dk]["n"]), f"{a[dk]['corr']:.2f}"
    N["amnDerCountries"] = str(len(a[dk].get("countries", [])))
    # would paying for surveys pay off? (59_survey_value.py)
    v = json.loads((TAB / "survey_value_key.json").read_text())
    for k_, t in [("share_reached_survey", "Survey"), ("share_reached_forecast", "Fc"), ("share_reached_random", "Rand"),
                  ("share_reached_oracle", "Oracle"), ("rate_rule_share_survey", "RateSurvey"),
                  ("rate_rule_share_forecast", "RateFc")]:
        N[f"svv{t}"] = pct(v[k_])
    N["svvZones"] = f"{v['zones_per_season']:.0f}"
    N["svvRound"] = r2(v["cost_round_central"])
    N["svvDeaths"] = f"{v['deaths_central']:.0f}"
    N["svvCostMid"], N["svvCostLo"], N["svvCostHi"] = (r2(v[f"cost_per_death_{x}"]) for x in ["central", "high", "low"])
    N["svvRateMid"], N["svvRateLo"], N["svvRateHi"] = (r2(v[f"rate_rule_cost_per_death_{x}"]) for x in ["central", "high", "low"])
    fk = json.loads((TAB / "fsnau_value_key.json").read_text())
    N["fsFcOnLag"], N["fsFcOnLagSe"] = f"{10 * fk['fc_on_lag']:.2f}", f"{10 * fk['fc_on_lag_se']:.2f}"
    # the calibration used in the benefit-cost section (36_benefit_cost.py)
    ke = json.loads((TAB / "benefit_cost_key.json").read_text())
    for lvl, t in [("low", "Lo"), ("central", "Mid"), ("high", "Hi")]:
        cd, gm = ke["cdr"][lvl], ke["gam"][lvl]
        N[f"calCdr{t}"] = f"{cd['2'] - cd['1']:.2f}"
        N[f"calFam{t}"] = f"{cd['5'] - cd['4']:.1f}"
        N[f"calGam{t}"] = f"{100 * (gm['2'] - gm['1']):.1f}"


# ------------------------------------------------------------------ within countries (61-63)
def subnational():
    """Does aid follow FEWS NET within Somalia and Sudan, and do its aid flags mark where aid went?"""
    R = pd.read_csv(TAB / "subnational_models.csv")
    K = json.loads((TAB / "subnational_key.json").read_text())
    def g(iso, block, spec, y, v):
        x = R[(R.iso == iso) & (R.block == block) & (R.spec == spec) & (R.outcome == y) & (R["var"] == v)].iloc[0]
        return x
    def star(c, se):
        t = abs(c / se) if se > 0 else 0
        return "***" if t > 2.576 else "**" if t > 1.96 else "*" if t > 1.645 else ""
    rows = [("Pooled-fund aid (asinh US\\$)", "A", "static", "aid", "fc3", "Forecast share in Crisis+"),
            ("", "A", "dynamic", "aid", "fc3", "\\quad with lagged aid"),
            ("", "A", "Anderson-Hsiao", "d_aid", "d_fc3", "\\quad first differences, lag instrumented"),
            ("", "A", "distinctive", "aid", "b_fc3", "Predictable part of forecast"),
            ("", "A", "distinctive", "aid", "c_fc3", "FEWS NET's distinctive information"),
            ("", "A", "placebo: next round's forecast", "aid", "fc3_f1", "Placebo: next round's forecast"),
            ("Any pooled-fund aid", "A", "static", "aid_any", "fc3", "Forecast share in Crisis+"),
            ("Food and nutrition partners present", "A", "static", "pres", "fc3", "Forecast share in Crisis+"),
            ("People reached (asinh, annual)", "A2", "district and year effects", "reach", "fc3", "Forecast share in Crisis+"),
            ("Aid flag share", "B", "contemporaneous", "flag", "aid", "Pooled-fund aid (asinh)"),
            ("", "B", "contemporaneous", "flag (3W presence)", "pres", "Partners present"),
            ("", "B2", "district and year effects", "flag", "reach", "People reached (asinh, annual)"),
            ("", "B", "lags and lead", "flag", "aid_f1", "Placebo: next period's aid")]
    lines = ["\\begin{tabular}{llcc}", "\\toprule", "Outcome & Regressor & Somalia & Sudan \\\\", "\\midrule"]
    for out_lab, block, spec, y, v, lab in rows:
        cells, ses = [], []
        for iso in ["SOM", "SDN"]:
            try:
                x = g(iso, block, spec, y, v)
                cells.append(f"{x.coef:.3f}{star(x.coef, x.se)}"); ses.append(f"({x.se:.3f})")
            except IndexError:
                cells.append("--"); ses.append("")
        lines.append(f"{out_lab} & {lab} & " + " & ".join(cells) + " \\\\")
        lines.append(" & & " + " & ".join(ses) + " \\\\")
    lines += ["\\midrule", f"Districts & & {K['SOM']['districts']} & {K['SDN']['districts']} \\\\",
              f"FEWS NET periods & & {K['SOM']['periods']} & {K['SDN']['periods']} \\\\", "\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "subnational.tex").write_text("\n".join(lines) + "\n")
    for iso, t in [("SOM", "So"), ("SDN", "Sd")]:
        k = K[iso]
        N[f"sub{t}Districts"], N[f"sub{t}Periods"] = str(k["districts"]), str(k["periods"])
        N[f"sub{t}AidShare"] = pct(k["share_with_aid"])
        for nm, (b, sp, y, v) in {"Fc": ("A", "static", "aid", "fc3"), "Any": ("A", "static", "aid_any", "fc3"),
                                  "Base": ("A", "distinctive", "aid", "b_fc3"), "Contrib": ("A", "distinctive", "aid", "c_fc3"),
                                  "Plac": ("A", "placebo: next round's forecast", "aid", "fc3_f1"),
                                  "Pres": ("A", "static", "pres", "fc3"), "Reach": ("A2", "district and year effects", "reach", "fc3"),
                                  "FlagPres": ("B", "contemporaneous", "flag (3W presence)", "pres"),
                                  "FlagAid": ("B", "contemporaneous", "flag", "aid"),
                                  "FlagReach": ("B2", "district and year effects", "flag", "reach"),
                                  "FlagReachPc": ("B2", "district and year effects", "flag", "reach_pc"),
                                  "FlagPersist": ("B", "next round", "flag_next", "flag")}.items():
            x = g(iso, b, sp, y, v)
            d = 3 if nm.startswith("Flag") and nm != "FlagPersist" else 2
            N[f"sub{t}{nm}"], N[f"sub{t}{nm}Se"] = sg(x.coef, d), f"{x.se:.{d}f}"
        N[f"sub{t}AnyPct"] = sg(100 * g(iso, "A", "static", "aid_any", "fc3").coef)
        c = R[(R.iso == iso) & (R.block == "C") & (R.spec == "2SLS") & (R.outcome == "phase_next") & (R["var"] == "aid")].iloc[0]
        N[f"sub{t}IvF"] = f"{c.first_stage_F:.0f}"
    A = pd.read_parquet(INP / "panel/subnational_SOM_annual.parquet")
    pc = ((A.reach_fs + A.reach_nut) / A["pop"].where(A["pop"] > 0))
    pc = pc.clip(upper=pc.quantile(0.99))
    N["subSoFlagReachSd"] = pct(float(g("SOM", "B2", "district and year effects", "flag", "reach_pc").coef) * pc.std())
    N["subSoFlagMean"] = pct(A.flag.mean())


def fig_voi():
    """If treatment followed surveys: extra deaths averted per season by Somalia's survey round."""
    R = pd.read_csv(TAB / "survey_voi.csv")
    R = R[~R.scaled]
    S = R.groupby(["cover", "redeploy", "info"]).deaths.mean().unstack("info")
    S["gain"] = S.survey - S.forecast
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    cols = {0.0: BLUE, 0.5: LBLUE, 1.0: ORANGE}
    labs = {0.0: "No redeployment", 0.5: "Half of stranded supplies moved", 1.0: "All stranded supplies moved"}
    for rd, c in cols.items():
        x = S.xs(rd, level="redeploy")
        ax.plot(100 * x.index, x.gain, marker="o", ms=4, lw=1.6, color=c, label=labs[rd])
    ax.axhline(0, color=GREY, lw=0.8)
    ax.axvline(38, color=GREY, lw=0.8, ls="--")
    ax.text(39, ax.get_ylim()[0] + 0.05 * (ax.get_ylim()[1] - ax.get_ylim()[0]), "38% = average coverage of\ntreatment programmes",
            fontsize=7, color="#555555", va="bottom")
    ax.set_xlabel("Treatment places available, as a share of all acutely\nmalnourished children in the surveyed zones (%)")
    ax.set_ylabel("Extra deaths averted per season\n(survey-based vs forecast-based planning)")
    ax.legend(fontsize=7.5, loc="upper left")
    ax.grid(axis="y", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
    fig.savefig(FIG / "fig10_voi.pdf")
    plt.close(fig)
    k = json.loads((TAB / "survey_voi_key.json").read_text())["table"]
    for rd, t in [("0.0", "Zero"), ("0.5", "Half"), ("1.0", "Full")]:
        x = k[f"0.38_fixed_{rd}"]
        N[f"voiGain{t}"] = f"{x['survey_vs_forecast']:.0f}"
        N[f"voiCost{t}"] = r2(x["cost_per_death_central"])
        N[f"voiCostLo{t}"], N[f"voiCostHi{t}"] = r2(x["cost_per_death_low"]), r2(x["cost_per_death_high"])
        N[f"voiOracle{t}"] = pct(x["survey_share_of_oracle_gain"])
    x = k["0.38_fixed_0.0"]
    N["voiBase"] = f"{x['forecast']:,.0f}"
    N["voiPop"] = f"{x['population']:,.0f}"
    N["voiOracleDeaths"] = f"{x['oracle']:,.0f}"
    kk = json.loads((TAB / "survey_voi_key.json").read_text())
    N["voiZones"], N["voiSeasons"] = f"{kk['zones_per_season']:.0f}", str(kk["seasons"])
    N["voiSamShare"] = pct(kk["sam_share"])
    # range over realistic budgets (20-50 percent) and redeployment assumptions
    g = [v for kx, v in k.items() if kx.split("_")[0] in ("0.2", "0.3", "0.38", "0.5") and "fixed" in kx]
    cpd = [v["cost_per_death_central"] for v in g if v["cost_per_death_central"]]
    N["voiRangeLo"], N["voiRangeHi"] = r2(min(cpd)), r2(max(cpd))


# ------------------------------------------------------------------ what a phase means: single-panel figures
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"      # validated categorical slots 1-3 (dataviz reference palette)
IPC_GAM = {1: (0, 5), 2: (5, 10), 3: (10, 15), 4: (15, 30), 5: (30, 45)}
IPC_CDR = {1: (0, 0.5), 2: (0, 0.5), 3: (0.5, 1.0), 4: (1.0, 2.0), 5: (2.0, 3.0)}


def _survey_points():
    """Survey results with FEWS NET's map phase for the area at the time of the survey."""
    a = pd.read_csv(TAB / "fsnau_value_panel.csv")
    a = a.assign(phase=a.after.fillna(a.cur), group="Somalia, scheduled rounds (FSNAU)")[["phase", "gam", "cdr", "group"]]
    b = pd.read_csv(TAB / "phase_outcomes_surveys.csv").dropna(subset=["cur"])
    b["group"] = np.where(b.recurring, "Other recurring rounds (Nigeria, Burkina Faso, Mauritania)", "Ad hoc surveys (SMART+)")
    b = b.rename(columns={"cur": "phase"})[["phase", "gam", "cdr", "group"]]
    return pd.concat([a, b], ignore_index=True)


def _bands(ax, bands, xmax=5.45):
    for ph, (lo, hi) in bands.items():
        ax.add_patch(plt.Rectangle((ph - 0.45, lo), 0.9, hi - lo, color="#ececec", lw=0, zorder=0))
    ax.add_patch(plt.Rectangle((0, 0), 0, 0, color="#ececec", lw=0, label="IPC reference band for the phase"))


def _strip(ax, d, y, bands, ylabel, ylim):
    groups = ["Somalia, scheduled rounds (FSNAU)", "Other recurring rounds (Nigeria, Burkina Faso, Mauritania)",
              "Ad hoc surveys (SMART+)"]
    cols, mks = dict(zip(groups, [C1, C2, C3])), dict(zip(groups, ["o", "s", "^"]))
    rng = np.random.default_rng(3)
    _bands(ax, bands)
    d = d.dropna(subset=[y, "phase"])
    for i, g in enumerate(groups):
        x = d[d.group == g]
        off = (i - 1) * 0.22
        ax.scatter(x.phase.round().clip(1, 5) + off + rng.uniform(-0.08, 0.08, len(x)), x[y], s=10, alpha=0.55,
                   color=cols[g], marker=mks[g], linewidths=0, label=f"{g} (n={len(x)})", zorder=2)
    m = d.assign(ph=d.phase.round().clip(1, 5)).groupby("ph")[y].agg(["mean", "std", "size"])
    m = m[m["size"] >= 5]
    ax.errorbar(m.index, m["mean"], yerr=1.96 * m["std"] / np.sqrt(m["size"]), fmt="D", color="#222222", ms=6,
                lw=1.4, zorder=4, label="Mean, all surveys (95% interval)")
    ax.set_xticks(range(1, 6))
    ax.set_xticklabels(["1\nMinimal", "2\nStressed", "3\nCrisis", "4\nEmergency", "5\nFamine"], fontsize=8)
    ax.set_xlim(0.5, 5.5); ax.set_ylim(*ylim)
    ax.set_xlabel("FEWS NET's phase for the area at the time of the survey")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
    ax.legend(fontsize=7, loc="upper left", frameon=False)


def fig_phase_singles():
    d = _survey_points()
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    _strip(ax, d, "gam", IPC_GAM, "Acute malnutrition, children under five (%)", (0, 45))
    fig.savefig(FIG / "fig9a_phase_gam.pdf"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    _strip(ax, d, "cdr", IPC_CDR, "Crude death rate (deaths per 10,000 people per day)", (0, 3))
    fig.savefig(FIG / "fig9b_phase_cdr.pdf"); plt.close(fig)
    # within zones (Somalia): residual phase vs residual malnutrition, binned
    a = pd.read_csv(TAB / "fsnau_value_panel.csv").dropna(subset=["fc", "gam"])
    w = a[["gam", "fc"]].copy()
    for _ in range(50):
        for f in ["key", "t"]:
            w = w - w.groupby(a[f]).transform("mean")
    w["bin"] = pd.qcut(w.fc.rank(method="first"), 15, labels=False)
    b = w.groupby("bin").agg(x=("fc", "mean"), y=("gam", "mean"), n=("gam", "size"))
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.scatter(w.fc, w.gam, s=7, color=C1, alpha=0.18, linewidths=0, label="Zone-seasons")
    ax.scatter(b.x, b.y, s=34, color=C1, zorder=3, label="Averages within 15 bins")
    slope = (w.fc @ w.gam) / (w.fc @ w.fc)
    xs = np.linspace(w.fc.quantile(0.01), w.fc.quantile(0.99), 20)
    ax.plot(xs, slope * xs, color=C1, lw=2, label=f"Fitted: {slope:.1f} points per phase")
    ax.plot(xs, 7.5 * xs, color=C2, lw=2, ls="--", label="IPC bands: about 7.5 points per phase")
    ax.axhline(0, color=GREY, lw=0.7); ax.axvline(0, color=GREY, lw=0.7)
    ax.set_xlabel("FEWS NET's forecast phase, relative to the zone's usual level and the season")
    ax.set_ylabel("Acute malnutrition, relative to the zone's\nusual level and the season (points)")
    ax.set_ylim(-12, 14)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    ax.grid(axis="y", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
    fig.savefig(FIG / "fig9c_within_zone.pdf"); plt.close(fig)
    N["wzSlopeFig"] = f"{slope:.1f}"
    # persistence: this round vs the previous round (Somalia)
    fig, ax = plt.subplots(figsize=(5.0, 4.4))
    ax.scatter(a.gam_lag, a.gam, s=11, color=C1, alpha=0.5, linewidths=0)
    lim = [0, max(a.gam.max(), a.gam_lag.max()) + 2]
    ax.plot(lim, lim, color=GREY, lw=0.8, ls="--")
    bb = np.polyfit(a.gam_lag, a.gam, 1)
    ax.plot(lim, np.polyval(bb, lim), color=C1, lw=1.8)
    ax.text(lim[1] * 0.97, np.polyval(bb, lim[1] * 0.97) - 2.5, f"fit: slope {bb[0]:.2f}", ha="right", fontsize=7.5, color="#333333")
    ax.text(lim[1] * 0.97, lim[1] * 0.97 + 0.8, "equal", ha="right", fontsize=7.5, color="#666666")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Acute malnutrition in the previous round, six months earlier (%)")
    ax.set_ylabel("Acute malnutrition this round (%)")
    ax.grid(color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
    fig.savefig(FIG / "fig9d_persistence.pdf"); plt.close(fig)
    # the IPC's two scales for the same areas
    c = pd.read_csv(TAB / "phase_outcomes_amn.csv")
    c = c[(c.comparison == "AMN any") & (c.row == "crosstab")]
    order = ["1", "2", "3", "4+"]
    M = c.pivot_table(index="afi_bin", columns="amn_bin", values="n", aggfunc="sum").reindex(index=order, columns=order).fillna(0)
    Sh = M.div(M.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    im = ax.imshow(Sh.values, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#f4f8fd", "#1c5cab"]),
                   vmin=0, vmax=1, origin="lower")
    for i in range(len(order)):
        for j in range(len(order)):
            v, n = Sh.values[i, j], int(M.values[i, j])
            if M.values[i].sum() == 0:
                continue
            ax.text(j, i, f"{100 * v:.0f}%\n({n})", ha="center", va="center", fontsize=7.5,
                    color="white" if v > 0.5 else "#222222")
    for k in range(len(order)):
        ax.add_patch(plt.Rectangle((k - 0.5, k - 0.5), 1, 1, fill=False, ec="#222222", lw=1.4))
    ax.set_xticks(range(4), ["1", "2", "3", "4 or 5"]); ax.set_yticks(range(4), ["1", "2", "3", "4 or 5"])
    ax.set_xlabel("IPC acute malnutrition phase")
    ax.set_ylabel("IPC acute food insecurity phase")
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Share of areas in the row", fontsize=8)
    fig.savefig(FIG / "fig9e_afi_amn.pdf"); plt.close(fig)
    N["amnAnyN"] = f"{int(M.values.sum()):,}"
    N["amnAnyDiag"] = pct(np.trace(M.values) / M.values.sum())
    # excess deaths in documented crises vs the IPC bands
    e = pd.read_csv(ROOT / "references" / "excess_deaths.csv")
    days = e.months * 30.4
    e["lo"], e["hi"] = e.deaths_lo / (e.p3_hi * days) * 1e4, e.deaths_hi / (e.p3_lo * days) * 1e4
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ax.axvspan(0.2, 0.8, color="#ececec", lw=0, zorder=0)
    ax.text(0.5, len(e) - 0.35, "IPC Crisis band,\nless a normal baseline", ha="center", fontsize=7, color="#555555", va="bottom")
    for i, r in enumerate(e.itertuples()):
        ax.plot([r.lo, r.hi], [i, i], color=C1, lw=3, solid_capstyle="round")
        ax.scatter([(r.lo + r.hi) / 2], [i], color=C1, s=30, zorder=3)
    ax.set_yticks(range(len(e)), e.label, fontsize=8)
    ax.set_ylim(-0.6, len(e) + 0.3)
    ax.set_xlabel("Excess deaths per 10,000 people in Crisis or worse, per day")
    ax.grid(axis="x", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    fig.savefig(FIG / "fig9f_excess_deaths.pdf"); plt.close(fig)


def _foodsec():
    """Independent WFP food security indicators matched to FEWS NET's map phase (66_foodsec_surveys.py).
    Survey rounds (WFP's compilation; mVAM files where the compilation has no value for the area-month) and
    WFP's monthly phone monitoring, averaged to area-years so that repeated months do not dominate."""
    m = pd.read_parquet(INP / "foodsec_surveys/matched.parquet")
    m = m[m.independent_of_ipc & m.indicator.isin(["fcs_poor_borderline", "rcsi_19plus"]) & m.fews_cs.notna()].copy()
    m["key"] = m.area_id.astype(str) + "|" + m.month.astype(str) + "|" + m.indicator
    lit = set(m[m.source == "wfp_lit"].key)
    m = m[~((m.source == "mvam_hdx") & m.key.isin(lit))]
    rounds = m[m.source.isin(["wfp_lit", "mvam_hdx"])].assign(group="WFP survey rounds")
    rt = m[m.source == "wfp_rt"].groupby(["area_id", "iso3", "year", "indicator"]).agg(
        value=("value", "mean"), fews_cs=("fews_cs", "mean")).reset_index().assign(group="WFP phone monitoring (area-years)")
    d = pd.concat([rounds[["area_id", "iso3", "indicator", "value", "fews_cs", "group"]],
                   rt[["area_id", "iso3", "indicator", "value", "fews_cs", "group"]]], ignore_index=True)
    d["phase"] = d.fews_cs
    if d.value.max() <= 1.5:
        d["value"] = 100 * d.value
    return d, m


def fig_foodsec():
    d, m = _foodsec()
    groups = ["WFP survey rounds", "WFP phone monitoring (area-years)"]
    cols, mks = dict(zip(groups, [C1, C2])), dict(zip(groups, ["o", "s"]))
    for ind, fname, ylab in [("fcs_poor_borderline", "fig9g_phase_fcs.pdf", "Households with poor or borderline\nfood consumption (%)"),
                             ("rcsi_19plus", "fig9h_phase_rcsi.pdf", "Households using severe\ncoping strategies (%)")]:
        x0 = d[d.indicator == ind].dropna(subset=["value", "phase"])
        fig, ax = plt.subplots(figsize=(6.6, 4.2))
        rng = np.random.default_rng(5)
        for i, g in enumerate(groups):
            x = x0[x0.group == g]
            ax.scatter(x.phase.round().clip(1, 4) + (i - 0.5) * 0.24 + rng.uniform(-0.09, 0.09, len(x)), x.value,
                       s=7, alpha=0.35, color=cols[g], marker=mks[g], linewidths=0, label=f"{g} (n={len(x):,})", zorder=2)
        mm = x0.assign(ph=x0.phase.round().clip(1, 4)).groupby("ph").value.agg(["mean", "std", "size"])
        ax.errorbar(mm.index, mm["mean"], yerr=1.96 * mm["std"] / np.sqrt(mm["size"]), fmt="D", color="#222222", ms=6,
                    lw=1.4, zorder=4, label="Mean, all (95% interval)")
        # IPC 20% rule: an area is in Phase 3 or worse when at least 20% of households are; these indicators
        # mark households in Phase 3 or worse, so Phases 1-2 imply < 20% and Phases 3+ imply >= 20%
        for ph, (lo, hi) in {1: (0, 20), 2: (0, 20), 3: (20, 100), 4: (20, 100)}.items():
            ax.add_patch(plt.Rectangle((ph - 0.45, lo), 0.9, hi - lo, color="#ececec", lw=0, zorder=0))
        ax.add_patch(plt.Rectangle((0, 0), 0, 0, color="#ececec", lw=0,
                                   label="Range consistent with the phase under the IPC's 20% rule"))
        ax.set_xticks(range(1, 5))
        ax.set_xticklabels(["1\nMinimal", "2\nStressed", "3\nCrisis", "4 or 5\nEmergency+"], fontsize=8)
        ax.set_xlim(0.5, 4.5); ax.set_ylim(0, 100)
        ax.set_xlabel("FEWS NET's phase for the area at the time of the survey")
        ax.set_ylabel(ylab)
        ax.grid(axis="y", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
        ax.legend(fontsize=7, loc="upper left", frameon=False)
        fig.savefig(FIG / fname); plt.close(fig)
        t = "Fcs" if ind.startswith("fcs") else "Rcsi"
        for ph, tag in [(1, "One"), (2, "Two"), (3, "Three"), (4, "Four")]:
            N[f"fs{t}{tag}"] = f"{mm.loc[ph, 'mean']:.0f}" if ph in mm.index else "--"
        N[f"fs{t}N"] = f"{len(x0):,}"
        N[f"fs{t}Corr"] = f"{x0.value.corr(x0.phase):.2f}"
        wc = x0.assign(v=x0.value - x0.groupby("iso3").value.transform("mean"), p=x0.phase - x0.groupby("iso3").phase.transform("mean"))
        N[f"fs{t}CorrCty"] = f"{wc.v.corr(wc.p):.2f}"
        wa = x0.assign(v=x0.value - x0.groupby("area_id").value.transform("mean"), p=x0.phase - x0.groupby("area_id").phase.transform("mean"))
        N[f"fs{t}CorrArea"] = f"{wa.v.corr(wa.p):.2f}"
        N[f"fs{t}SdOne"] = f"{x0[x0.phase.round().clip(1, 4) == 1].value.std():.0f}"
        ph = x0.phase.round().clip(1, 4)
        N[f"fs{t}LowOver"] = pct((x0.value[ph <= 2] >= 20).mean())      # Phase 1-2 areas above the 20% line
        N[f"fs{t}HighUnder"] = pct((x0.value[ph >= 3] < 20).mean())     # Phase 3+ areas below it
    N["fsFoodCountries"] = str(d.iso3.nunique())
    N["fsFoodAreas"] = f"{d.area_id.nunique():,}"
    # the Cadre Harmonise's own input indicators against its own phase (not independent)
    k = json.loads((TAB / "foodsec_phase_key.json").read_text())["ch_hdx (IPC input)"]
    for ind, t in [("fcs_poor_borderline", "Fcs"), ("hhs_3plus", "Hhs"), ("rcsi_19plus", "Rcsi"), ("lcs_crisis_plus", "Lcs")]:
        N[f"ch{t}Corr"] = f"{k[ind]['IPC/CH phase']['corr']:.2f}"
    N["chN"] = f"{k['fcs_poor_borderline']['IPC/CH phase']['n']:,}"
    N["chCountries"] = str(k["fcs_poor_borderline"]["IPC/CH phase"]["countries"])


# ------------------------------------------------------------------ two margins of value (81, 82)
def value_margins():
    v = json.loads((TAB / "value_margins.json").read_text())
    A = json.loads((TAB / "allocation_value_key.json").read_text())
    N["vmAreas"], N["vmCountries"] = f"{A['areas']:,}", str(A["countries"])
    N["vmYears"] = f"{A['year_range'][0]}--{A['year_range'][1]}"
    N["vmFewsCountries"] = str(v["fews_countries"])
    N["vmCover"] = pct(A["implied_coverage"]["central"])
    N["vmCoverLo"], N["vmCoverHi"] = pct(A["implied_coverage"]["high"]), pct(A["implied_coverage"]["low"])
    N["vmFoodAll"] = f"{v['food_per_year_all'] / 1e9:.1f}"
    N["vmFoodSample"] = f"{v['food_per_year_sample'] / 1e9:.1f}"
    N["vmScale"] = f"{v['scale_to_all']:.1f}"
    N["vmNeed"] = f"{v['need_pm_year_sample'] / 1e6:,.0f}"
    for t, tag in [("random", "Rand"), ("half", "Half"), ("perfect", "Perf")]:
        x = v[f"realloc_{t}"]
        N[f"vm{tag}Gain"] = f"{x['gain_pm'] / 1e6:.1f}"
        N[f"vm{tag}GainAll"] = f"{x['gain_pm_all'] / 1e6:.1f}"
        N[f"vm{tag}ShareNeed"] = f"{100 * x['share_of_need']:.1f}"
        N[f"vm{tag}PctMore"] = f"{x['pct_more_reached']:.0f}"
        N[f"vm{tag}Pub"], N[f"vm{tag}Fews"], N[f"vm{tag}Oracle"] = (pct(x[k]) for k in ["public_share", "fews_share", "oracle_share"])
        N[f"vm{tag}OracleGain"] = pct(x["share_of_oracle_gain"])
        N[f"vm{tag}Aid"] = f"{x['aid_equiv'] / 1e6:.0f}"
        N[f"vm{tag}AidAll"] = f"{x['aid_equiv_all'] / 1e6:.0f}"
        N[f"vm{tag}Ratio"] = f"{x['ratio']:.1f}"
        N[f"vm{tag}RatioAll"], N[f"vm{tag}RatioAllLo"], N[f"vm{tag}RatioAllHi"] = (f"{x[k]:.1f}" for k in ["ratio_all", "ratio_all_lo", "ratio_all_hi"])
        N[f"vm{tag}CostPm"] = f"{x['cost_per_pm']:.0f}"
    e = v["envelope_share"]
    N["envShareRaw"], N["envShareIpc"] = pct(e["raw data|symmetric"]), pct(e["raw data + latest Cadre Harmonise / IPC|symmetric"])
    N["envSharePosRaw"] = pct(e["raw data|one-sided-positive"])
    N["envBeta"] = f"{100 * v['beta_food']['raw data'] / 10:.0f}"      # percent per 10 points (log points x 10)
    er, eh = v["envelope_random"], v["envelope_half"]
    N["envUsdLo"] = f"{er['raw data + latest Cadre Harmonise / IPC|symmetric']['usd'] / 1e6:,.0f}"
    N["envUsdHi"] = f"{er['raw data|symmetric']['usd'] / 1e6:,.0f}"
    N["envPmLo"] = f"{er['raw data + latest Cadre Harmonise / IPC|symmetric']['pm'] / 1e6:.1f}"
    N["envPmHi"] = f"{eh['raw data|symmetric']['pm'] / 1e6:.1f}"


def fig_allocation():
    """Share of a fixed food-aid budget that reaches people in Crisis, by what the planner knows."""
    v = json.loads((TAB / "value_margins.json").read_text())
    A = json.loads((TAB / "allocation_value_key.json").read_text())["table"]
    infos = [("population", "Population only"), ("persist", "Latest official analysis only"),
             ("public", "Public information"), ("fews", "Public information + FEWS NET"), ("oracle", "Perfect foresight")]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for j, (t, lab, col, mk) in enumerate([("random", "Random targeting within areas", C1, "o"),
                                          ("half", "Halfway to perfect targeting", C2, "s")]):
        x = A[f"0.3_{t}"]
        vals = [100 * x[f"{i}_share"] for i, _ in infos]
        ys = np.arange(len(infos)) + (0.12 if j == 0 else -0.12)
        ax.scatter(vals, ys, color=col, marker=mk, s=40, zorder=3, label=lab)
        for vv, yy, (i, _) in zip(vals, ys, infos):
            if i in ("public", "fews"):
                ax.text(vv + 0.8, yy, f"{vv:.1f}%", fontsize=7, va="center", color="#333333")
    ax.set_yticks(range(len(infos)), [l for _, l in infos], fontsize=8)
    ax.set_xlabel("Share of food aid reaching people who would otherwise be in Crisis or worse (%)")
    ax.set_xlim(0, 80)
    ax.grid(axis="x", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    fig.savefig(FIG / "fig11_allocation.pdf"); plt.close(fig)


# ------------------------------------------------------------------ famine (Phase 5) forecasts
def famine_errors():
    """Type I and Type II errors at the famine threshold, 4-8 months ahead, by episode."""
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    cs, proj = cs[cs.month.dt.year <= 2024], proj[proj.report_month.dt.year <= 2024]
    fc = proj[(proj.lead >= 4) & (proj.lead <= 8)]
    latest = fc.sort_values("report_month").drop_duplicates(["fnid", "month"], keep="last")[["fnid", "month", "phase"]] \
        .rename(columns={"phase": "fc"})
    # Type I: famine forecasts and what followed
    w = cs.merge(latest, on=["fnid", "month"])
    w = w[w.fc >= 5]
    o = np.select([w.phase >= 5, (w.phase == 4) & w.assist_flag, w.phase == 4], ["came", "flag4", "noflag4"], "lower")
    w = w.assign(o=o, year=w.month.dt.year)
    N["famWarn"], N["famWarnUnits"] = f"{len(w):,}", str(w.fnid.nunique())
    sh = pd.Series(o).value_counts(normalize=True)
    N["famCame"], N["famFlag"], N["famNoFlag"], N["famLower"] = (pct(sh.get(k, 0)) for k in ["came", "flag4", "noflag4", "lower"])
    # Type II: area-months mapped in famine, and what was forecast 4-8 months earlier (most severe)
    f5 = cs[cs.phase >= 5][["country_code", "fnid", "month"]]
    mx = f5.merge(fc.groupby(["fnid", "month"]).phase.max().rename("fcmax").reset_index(), on=["fnid", "month"], how="left")
    N["famMapped"], N["famMappedUnits"] = f"{len(f5):,}", str(f5.fnid.nunique())
    N["famForecastFive"] = pct((mx.fcmax >= 5).mean())
    N["famForecastFour"] = pct((mx.fcmax >= 4).mean())
    N["famMissed"] = pct(1 - (mx.fcmax >= 5).mean())
    # episodes: country x year, units mapped in famine, units forecast in famine and what happened
    ep = w.groupby(["country_code", "year"]).agg(units_fc=("fnid", "nunique"),
                                                 came=("o", lambda x: (x == "came").mean()),
                                                 flag=("o", lambda x: (x == "flag4").mean())).reset_index()
    mp = f5.assign(year=f5.month.dt.year).groupby(["country_code", "year"]).fnid.nunique().rename("units_mapped").reset_index()
    E = ep.merge(mp, on=["country_code", "year"], how="outer").fillna(0).sort_values(["year", "country_code"])
    E.to_csv(TAB / "famine_episodes.csv", index=False)
    names = {"SO": "Somalia", "SS": "South Sudan", "SD": "Sudan", "YE": "Yemen", "ET": "Ethiopia", "NG": "Nigeria"}
    lines = ["\\begin{tabular}{llrrrr}", "\\toprule",
             "Country & Year & Units forecast in Famine & Came true & Held back by aid & Units mapped in Famine \\\\", "\\midrule"]
    for r in E.itertuples():
        lines.append(f"{names.get(r.country_code, r.country_code)} & {int(r.year)} & {int(r.units_fc)} & "
                     + (f"{100 * r.came:.0f}\\% & {100 * r.flag:.0f}\\%" if r.units_fc else "-- & --")
                     + f" & {int(r.units_mapped)} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "famine.tex").write_text("\n".join(lines) + "\n")
    N["famEpisodes"] = str(len(E))
    # famine risk raised in FEWS NET's reports before famine was mapped (pilot countries, 52_text_features.py)
    rep = pd.read_parquet(INP / "reports/reports.parquet")
    rep["m"] = pd.PeriodIndex(rep.month, freq="M")
    for cc, onset, tag in [("SO", "2011-07", "So"), ("SD", "2024-06", "Sd")]:
        on = pd.Period(onset, "M")
        x = rep[(rep.cc == cc) & (rep.m < on) & (rep.m >= on - 12) & rep.nat_famine_risk_mentioned.fillna(False).astype(bool)]
        first = x.m.min()
        N[f"famRisk{tag}"] = first.strftime("%B %Y")
        N[f"famRiskLead{tag}"] = str((on - first).n)
    # precise emergency statements for the introduction
    # from unrounded shares (dividing the printed percentages gave 56 instead of 57)
    N["tIfailFlagShare"] = pct(RAW["flag3"] / (1 - RAW["came"])) if RAW["came"] < 1 else "0"
    N["tIIearlyMiss"] = pct(1 - RAW["early4"])
    N["aucRawPct"], N["aucRawFewsPct"] = f"{100 * RAW['aucRaw']:.0f}", f"{100 * RAW['aucRawFews']:.0f}"
    N["tIIearlyCrisisPlus"] = pct(RAW["early4"] + RAW["early3"])
    N["tIgenuine"] = pct(RAW["noflag3"] + RAW["better"])


# ------------------------------------------------------------------ which pieces are worth paying for
def pieces():
    """Pilot on FEWS NET's reports (53_text_value.py) and the value of price data (55_price_value.py)."""
    k = json.loads((TAB / "text_value_key.json").read_text())
    rep = pd.read_parquet(INP / "reports/reports.parquet")
    rep = rep[rep.cc.isin(["SO", "ET", "SD"])]
    N["txtReports"] = f"{len(rep):,}"
    N["txtOutlooks"] = str((rep.type == "food-security-outlook").sum())
    N["txtMatch"] = pct(k["extract_match"])
    N["txtMatchN"] = str(k["extract_match_n"])
    N["txtEscN"], N["txtEscEvents"] = f"{k['esc_n']:,}", f"{k['esc_events']:,}"
    N["txtEscFcFour"] = pct(k["esc_fc4_share"])
    for y, tag in [("next4", "Map"), ("need4", "Need")]:
        N[f"txtAuc{tag}"] = f"{k[f'auc_{y}_map']:.2f}"
        N[f"txtAuc{tag}Text"] = f"{k[f'auc_{y}_text']:.2f}"
    # surveys quoted in the reports
    N["svTotal"] = str(k["surveys_total"])
    N["svSO"], N["svET"], N["svSD"] = (str(k["surveys_by_country"].get(c, 0)) for c in ["SO", "ET", "SD"])
    bp = pd.read_csv(TAB / "text_value_surveys_by_phase.csv").set_index("phase")
    for ph, tag in [(2, "Two"), (3, "Three"), (4, "Four"), (5, "Five")]:
        N[f"svGam{tag}"] = f"{bp.loc[ph, 'gam_mean']:.0f}"
    N["svCritShare"] = pct(k["survey_crit"] / k["survey_n"])
    cov = pd.read_csv(TAB / "text_value_survey_coverage.csv").set_index("country_code")
    for c in ["ET", "SO", "SD"]:
        N[f"svEmerg{c}"] = pct(cov.loc[c, "emergency_share_with_survey"])
        N[f"svPop{c}"] = pct(cov.loc[c, "pop_share_with_survey_12m"])
    ns = pd.read_csv(TAB / "text_value_new_survey.csv").set_index(["outcome", "controls"])
    r = ns.loc[("up", "all text")]
    N["nsUp"], N["nsUpSe"], N["nsUpBase"] = pct(r.coef, 1), pct(r.se, 1), pct(r.base)
    N["nsShare"] = pct(r.share_new, 1)
    r = ns.loc[("down", "all text")]
    N["nsDown"], N["nsDownSe"] = sg(100 * r.coef, 1), pct(r.se, 1)
    r = ns.loc[("next4", "all text")]
    N["nsEsc"], N["nsEscSe"], N["nsEscBase"] = pct(r.coef, 1), pct(r.se, 1), pct(r.base, 1)
    for key_, tag in [("mech:fc<=2:new_s", "Stress"), ("mech:content:new_crit", "Crit"), ("mech:content:new_ok", "Ok")]:
        for y, yt in [("up", "Up"), ("down", "Down")]:
            r = ns.loc[(y, key_)]
            N[f"ns{tag}{yt}"], N[f"ns{tag}{yt}Se"] = sg(100 * r.coef, 1), pct(r.se, 1)
        N[f"ns{tag}N"] = f"{round(r.share_new * r.n):,}"
    N["nsStressBase"] = pct(ns.loc[("up", "mech:fc<=2:new_s")].base)
    g = k["new_survey_groups"]
    N["nsUnforecast"] = pct(g["escalated_unforecast"]["share_new_survey"])
    N["nsForecast"] = pct(g["escalated_forecast"]["share_new_survey"])
    N["nsNone"] = pct(g["no_escalation"]["share_new_survey"])
    text_table()
    # scheduled surveys in Somalia (57_fsnau_value.py)
    fk = json.loads((TAB / "fsnau_value_key.json").read_text())
    fv = pd.read_csv(TAB / "fsnau_value.csv").set_index("model")
    fc_ = pd.read_csv(TAB / "fsnau_value_changes.csv").set_index("model")
    fpan = pd.read_csv(TAB / "fsnau_value_panel.csv")
    fb = fpan.assign(fc_round=fpan.fc.round().clip(2, 4)).groupby("fc_round").agg(gam=("gam", "mean"))   # as in Figure 9
    sv = pd.read_csv(INP / "fsnau/surveys.csv")
    N["fsAll"] = f"{len(sv):,}"
    N["fsN"], N["fsZones"], N["fsSeasons"] = str(fk["n"]), str(fk["n_zones"]), str(fk["n_seasons"])
    N["fsGam"], N["fsCrit"] = f"{fk['gam_mean']:.0f}", pct(fk["crit_share"])
    N["fsLead"] = f"{fk['median_lead']:.0f}"
    N["fsCorrFc"], N["fsCorrLag"], N["fsCorrAfter"] = (f"{fk[k]:.2f}" for k in ["corr_gam_forecast", "corr_gam_lag", "corr_gam_after_map"])
    N["fsRtwoFc"], N["fsRtwoLag"], N["fsRtwoBoth"] = (sg(fv.loc[m, "r2"], 2) for m in ["FEWS NET forecast", "last survey", "forecast + last survey"])
    N["fsAucFc"], N["fsAucLag"] = f"{fv.loc['FEWS NET forecast', 'auc']:.2f}", f"{fv.loc['last survey', 'auc']:.2f}"
    N["fsChRtwoLag"], N["fsChRtwoFc"] = sg(fc_.loc["last survey", "r2"], 2), sg(fc_.loc["forecast level and change", "r2"], 2)
    N["fsDfc"], N["fsDfcSe"] = f"{fk['dgam_on_dfc']:.1f}", f"{fk['dgam_on_dfc_se']:.1f}"
    for ph, tag in [(2, "Two"), (3, "Three"), (4, "Four")]:
        N[f"fsGam{tag}"] = f"{fb.loc[ph, 'gam']:.0f}"
    N["fsMortN"] = str(fk["mort_n"])
    N["fsMortFc"], N["fsMortLag"] = sg(fk["mort_r2_forecast"], 2), sg(fk["mort_r2_lag"], 2)
    er = pd.read_csv(TAB / "text_value_escalation.csv")
    er = er[(er.outcome == "next4") & (er.model == "map+text")].set_index("var")
    N["txtAidDown"], N["txtAccess"] = pct(er.loc["t_aid_down", "coef"]), pct(er.loc["t_access", "coef"])
    # prices
    pc = pd.read_csv(TAB / "price_value_coverage.csv", index_col=0)
    a = pc.loc["All"]
    N["prBoth"], N["prWfpOnly"], N["prFewsOnly"], N["prNone"] = (pct(a[c]) for c in ["both", "WFP only", "FEWS only", "none"])
    fp = pd.read_parquet(INP / "prices_fdw/prices.parquet", columns=["source_organization", "market_id"])
    own = ~fp.source_organization.str.contains("WFP", case=False, na=False)
    N["prMarketsFews"] = f"{fp[own].market_id.nunique():,}"
    N["prShareNonWfp"] = pct(own.mean())
    pv = pd.read_csv(TAB / "price_value.csv")
    pv = pv[pv["sample"] == "all"].set_index(["task", "model"]).auc
    for task, tag in [("new crisis", "New"), ("escalation", "Esc")]:
        for model, mt in [("base", "Base"), ("+WFP prices", "Wfp"), ("+FEWS NET prices", "Fews"), ("+both", "Both"),
                          ("+forecast", "Fc"), ("raw", "Raw"), ("raw +both", "RawBoth"),
                          ("raw +FEWS NET map and forecast", "RawMap")]:
            if (task, model) in pv.index:
                N[f"pv{tag}{mt}"] = f"{pv.loc[(task, model)]:.3f}"


# ------------------------------------------------------------------ displacement (Somalia, 83_displacement.py)
def displacement():
    k = json.loads((TAB / "displacement_key.json").read_text())
    R = pd.read_csv(TAB / "displacement_forecast.csv")
    O = pd.read_csv(TAB / "displacement_oos.csv").set_index(["outcome", "model"]).r2
    E = pd.read_csv(TAB / "displacement_onsets.csv")
    eff = lambda b: sg(100 * (np.exp(0.1 * b) - 1))
    N["dispDistricts"], N["dispRounds"], N["dispN"] = str(k["districts"]), str(k["rounds"]), f"{k['district_rounds']:,}"
    N["dispTotal"] = f"{k['departures_total'] / 1e6:.1f}"
    N["dispDroughtShare"] = pct(k["drought_share"])
    N["dispMedShare"], N["dispPninety"] = pct(k["dep_per_year_median_share"], 1), pct(k["dep_per_year_p90_share"])
    for y, Y in [("dep", "All"), ("dep_drought", "Drought"), ("dep_conflict", "Conflict")]:
        g = R[R.outcome == y].set_index(["spec", "term"])
        for spec, t, nm in [("map and forecast", "cur3", "Cur"), ("map and forecast", "fc3", "Fc"),
                            ("forecast split", "b_fc3", "Base"), ("forecast split", "c_fc3", "Contrib"),
                            ("forecast split, + IPC", "ci_fc3", "ContribIpc")]:
            r = g.loc[(spec, t)]
            N[f"disp{Y}{nm}"] = eff(r.coef)
            N[f"disp{Y}{nm}Ci"] = f"{eff(r.coef - 1.96 * r.se)} to {eff(r.coef + 1.96 * r.se)}"
    for y, Y in [("dep", "All"), ("dep_drought", "Drought")]:
        N[f"disp{Y}RtwoPub"], N[f"disp{Y}RtwoFews"] = f"{O[(y, 'public')]:.2f}", f"{O[(y, 'public + FEWS NET')]:.2f}"
    for lvl, L in [("Emergency", "Em"), ("Crisis", "Cr")]:
        N[f"dispOn{L}"], N[f"dispOn{L}Early"] = str(k[f"onsets_{lvl}"]), str(k[f"onsets_{lvl}_early"])
        N[f"dispOn{L}Averted"] = str(k[f"onsets_{lvl}_averted"])
        e = E[(E.onset == lvl) & (E.outcome == "dep")].set_index(["window", "term"])
        for w, W in [("post6", "Six"), ("post12", "Twelve")]:
            for t, T in [("early", "Early"), ("averted", "Averted")]:
                r = e.loc[(w, t)]
                N[f"dispOn{L}{T}{W}"] = sg(100 * (np.exp(r.coef) - 1))
                N[f"dispOn{L}{T}{W}Se"] = f"{r.se:.2f}"
                N[f"dispOn{L}{T}{W}Coef"] = f"{r.coef:.2f}"


if __name__ == "__main__":
    coverage()
    type2()
    type1()
    official()
    contribution()
    money()
    appendix()
    bootstrap()
    benefit()
    predictable()
    distinct()
    cases()
    hetero()
    budget_and_cg()
    pieces()
    subnational()
    phase_outcomes()
    fig_information()
    fig_fsnau()
    fig_voi()
    fig_phase_singles()
    fig_foodsec()
    value_margins()
    fig_allocation()
    famine_errors()
    displacement()
    write_numbers()
