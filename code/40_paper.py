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
    N["tIIearlyStressed"] = pct(ed.get(2, 0) + ed.get(1, 0))
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 3.1), gridspec_kw={"width_ratios": [1.5, 1]})
    a = ax[0]
    g = curve[curve.onset].sort_values("lead")
    a.plot(g.lead, 100 * g.fc3, "o-", color=LBLUE, ms=4, label="Forecast Crisis or worse")
    a.plot(g.lead, 100 * g.fc4, "o-", color=BLUE, ms=4, label="Forecast Emergency or worse")
    h = curve[~curve.onset].sort_values("lead")
    a.plot(h.lead, 100 * h.fc4, "o--", color=GREY, ms=3, lw=1,
           label="Comparison: areas that did not tip\ninto Emergency, forecast Emergency")
    a.set_xlabel("Months between the forecast and the new Emergency")
    a.set_ylabel("Share of new Emergencies (%)")
    a.set_xticks(range(1, 9))
    a.set_ylim(0, 100)
    a.invert_xaxis()
    a.legend(fontsize=7.2, loc="center left", bbox_to_anchor=(0, 0.6))
    a.set_title("A. Share forecast, by how far ahead")
    a = ax[1]
    vals = [ed.get(4, 0), ed.get(3, 0), ed.get(2, 0) + ed.get(1, 0)]
    labs = ["Emergency\nor worse", "Crisis", "Stressed\nor better"]
    cols = [BLUE, LBLUE, GREY]
    a.bar(range(3), [100 * v for v in vals], color=cols)
    for i, v in enumerate(vals):
        a.text(i, 100 * v + 1.5, f"{100 * v:.0f}%", ha="center", fontsize=8)
    a.set_xticks(range(3), labs, fontsize=8)
    a.set_ylabel("Share of new Emergencies (%)")
    a.set_ylim(0, 60)
    a.set_title("B. Most severe forecast\n4-8 months ahead")
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
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    for score, lab, c in [("proj_share3", "Official projection (share of population in Crisis+)", RED),
                          ("fews_fc3", "FEWS NET forecast (share of area forecast in Crisis+)", BLUE)]:
        fpr, tpr, _ = roc_curve(d.next3, d[score])
        ax.plot(100 * fpr, 100 * (1 - tpr), color=c, lw=1.3, label=lab)
    pts = [("Official projection classifies\nthe area in Crisis or worse", old.proj3.mean(), 1 - new.proj3.mean(), RED, "o", (10, -12)),
           ("FEWS NET forecasts Crisis or\nworse for most of the area", (old.fews_fc3 >= 0.5).mean(), 1 - (new.fews_fc3 >= 0.5).mean(), BLUE, "s", (6, 6)),
           ("Either one warns", ((old.proj3 == 1) | (old.fews_fc3 >= 0.5)).mean(),
            1 - ((new.proj3 == 1) | (new.fews_fc3 >= 0.5)).mean(), "black", "D", (8, -14))]
    for lab, x, y, c, mk, off in pts:
        ax.scatter(100 * x, 100 * y, color=c, marker=mk, s=45, zorder=3)
        ax.annotate(lab, (100 * x, 100 * y), xytext=off, textcoords="offset points", fontsize=7.5, color=c)
    ax.set_xlabel("False alarms (Type I): share of areas that stayed below Crisis\nthat were warned about (%)")
    ax.set_ylabel("Misses (Type II): share of new Crises\nthat were not warned about (%)")
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=7, loc="upper right", title="Lines: every possible warning threshold", title_fontsize=7)
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
    N["bcBudget"], N["bcBudgetLow"], N["bcBudgetHigh"] = "64", "27", "90"
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
        N[f"bcCostCrisis{ka}"] = f"{64e6 / py:,.0f}"
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
    write_numbers()
