"""Detailed figures for missed emergencies (Type II) and false alarms (Type I).

Builds on 12_errors.py (same definitions):
  onset    an area newly in Emergency or worse (Phase 4+) on a current-situation
           map, when its previous map (within six months) showed Crisis or better
  warning  a forecast of Emergency issued 4-8 months before a month for which a
           current-situation map exists

Figures (output/figures/):
  t2_lines_with_points.pdf   share of onsets forecast as Emergency by lead, with
                             one dot per country-month of onsets
  t2_every_onset.pdf         one row per onset: the phase FEWS NET was forecasting
                             in each of the eight months before it hit
  t1_by_country.pdf          what happened to each country's Emergency warnings
  t1_funding_onsets.pdf      funding around the month emergencies hit, by how
                             early they were foretold
  t1_funding_warnings.pdf    funding around the month emergencies were predicted
                             to hit, for predictions that came true and did not
"""
import importlib.util
import textwrap
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e", ROOT / "code" / "12_errors.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
INP, TAB, FIG = E.INP, E.TAB, E.FIG
NAMES = {**E.NAMES, "BI": "Burundi", "CM": "Cameroon", "HN": "Honduras", "LS": "Lesotho",
         "AO": "Angola", "MR": "Mauritania", "ZM": "Zambia", "NI": "Nicaragua", "SV": "El Salvador",
         "VE": "Venezuela", "LB": "Lebanon", "TG": "Togo", "DJ": "Djibouti", "RW": "Rwanda"}
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 11, "axes.titleweight": "bold",
                     "axes.titlelocation": "left"})
ORANGE, BLUE, GREY = "#c55a11", "#1f4e79", "#8c8c8c"
# IPC's own phase colours
PHASE_COL = {0: "#f2f2f2", 1: "#cdfacd", 2: "#fae61e", 3: "#e67800", 4: "#c80000", 5: "#640000"}
KEY = {}


def footnote(fig, text, width=150, size=8):
    """Wrapped source note along the bottom of the figure."""
    fig.text(0.01, 0.01, "\n".join(textwrap.fill(t, width) for t in text.split("\n")),
             fontsize=size, color="#555", va="bottom", ha="left")


def load():
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    return cs, proj, codes


# ---------------------------------------------------------------- Type II
def onset_forecasts(cs, proj):
    ev = E.onsets(cs)
    on = ev[ev.onset]
    ctrl = ev[~ev.onset].sample(min(30000, (~ev.onset).sum()), random_state=1)
    fc = E.forecasts_by_lead(pd.concat([on, ctrl]), proj)
    m = pd.concat([on, ctrl])[["country_code", "fnid", "month", "onset", "prev_phase"]].merge(
        fc, on=["fnid", "month"])
    return on, m


def fig_lines_with_points(m):
    fig, ax = plt.subplots(figsize=(10, 6.2))
    rng = np.random.default_rng(3)
    for onset, col, lab in [(True, ORANGE, "Areas where an Emergency began"),
                            (False, BLUE, "Areas that stayed below Emergency (comparison)")]:
        d = m[m.onset == onset]
        # one dot per country x outcome-month x lead: the share of that batch of areas warned
        g = d.groupby(["country_code", "month", "lead"]).agg(
            share=("fc", lambda x: (x >= 4).mean()), n=("fc", "size")).reset_index()
        if onset:
            g = g[g.n >= 1]
        else:
            g = g[g.n >= 5]
        if onset:
            x = g.lead + rng.uniform(-0.28, 0.28, len(g))
            ax.scatter(x, g.share, s=8 + 12 * np.sqrt(g.n), color=col, alpha=0.22, edgecolor="none")
        line = d.groupby("lead").fc.apply(lambda x: (x >= 4).mean())
        ax.plot(line.index, line.values, color=col, lw=3, marker="o", ms=7, label=lab, zorder=5)
        for k, v in line.items():
            if onset:
                ax.annotate(f"{v:.0%}", (k, v), xytext=(0, 10), textcoords="offset points",
                            ha="center", fontsize=9, color=col, fontweight="bold")
    ax.set_xticks(range(1, 9))
    ax.set_xticklabels([f"{k} month{'s' if k > 1 else ''}\nbefore" for k in range(1, 9)])
    ax.invert_xaxis()
    ax.set_ylim(-0.04, 1.04)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_yticklabels([f"{v:.0%}" for v in np.linspace(0, 1, 6)])
    ax.set_xlabel("When the forecast was issued, relative to the month the Emergency began "
                  "(or the comparison month)")
    ax.set_ylabel("Share of areas that FEWS NET forecast to be in Emergency (Phase 4+)\n"
                  "for that month or any of the three months before it")
    ax.set_title("Were emergencies forecast before they began?", pad=30)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=10)

    n_on, n_ep = m[m.onset].groupby(["fnid", "month"]).ngroups, m[m.onset].groupby(["country_code", "month"]).ngroups
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    footnote(fig, "Lines: share of all areas. Each faint dot: all the areas in one country whose Emergency began in the same "
             "month (dot size = number of areas; dots are spread sideways slightly so they do not overlap). "
             f"{n_on:,} areas in which an Emergency began, in {n_ep} country-months, 2011-2026. Comparison: a random 30,000 "
             "area-months that were below Emergency and stayed below. Source: FEWS NET classifications and forecasts (IPC scale).")
    fig.savefig(FIG / "t2_lines_with_points.pdf")
    plt.close(fig)


def fig_every_onset(m):
    d = m[m.onset].pivot_table(index=["country_code", "fnid", "month"], columns="lead", values="fc",
                               aggfunc="max").reindex(columns=range(1, 9))
    d = d.fillna(0).astype(int)
    # earliest Emergency warning, for sorting within country
    first4 = d.apply(lambda r: max([k for k in range(1, 9) if r[k] >= 4], default=0), axis=1)
    n4 = (d >= 4).sum(axis=1)
    n3 = (d >= 3).sum(axis=1)
    d = d.assign(first4=first4, n4=n4, n3=n3).reset_index()
    counts = d.country_code.value_counts()
    keep = counts[counts >= 20].index
    d = d[d.country_code.isin(keep)]
    order = d.groupby("country_code").first4.apply(lambda x: (x > 0).mean()).sort_values(ascending=False).index
    d["c_rank"] = d.country_code.map({c: i for i, c in enumerate(order)})
    d = d.sort_values(["c_rank", "first4", "n4", "n3"], ascending=[True, False, False, False])
    mat = d[list(range(8, 0, -1))].values          # columns: 8 months before ... 1 month before
    mat = np.c_[mat, np.full(len(mat), 4)]          # the onset itself (Emergency)
    cmap = ListedColormap([PHASE_COL[k] for k in range(6)])
    norm = BoundaryNorm(np.arange(-0.5, 6.5, 1), cmap.N)
    fig, ax = plt.subplots(figsize=(10, 13))
    ax.imshow(mat, aspect="auto", cmap=cmap, norm=norm, interpolation="none")
    # country separators and labels
    pos = 0
    for c in order:
        n = (d.country_code == c).sum()
        ax.axhline(pos - 0.5, color="white", lw=4)
        warned = (d[d.country_code == c].first4 > 0).mean()
        ax.text(-0.7, pos + n / 2, f"{NAMES.get(c, c)}\n{n} areas; {warned:.0%} forecast\nas Emergency beforehand",
                ha="right", va="center", fontsize=8.5)
        pos += n
    ax.axvline(7.5, color="black", lw=1.5)
    ax.set_xticks(range(9))
    ax.set_xticklabels([f"{k} mo.\nbefore" for k in range(8, 0, -1)] + ["Month\nEmergency\nbegan"], fontsize=8.5)
    ax.xaxis.tick_top()
    ax.set_yticks([])
    ax.spines[:].set_visible(False)
    ax.set_title("Every Emergency that began, and what FEWS NET had forecast for it\n", pad=40)
    handles = [Patch(color=PHASE_COL[k], label=l) for k, l in
               [(0, "No forecast available"), (1, "1 Minimal"), (2, "2 Stressed"), (3, "3 Crisis"),
                (4, "4 Emergency"), (5, "5 Famine")]]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.008), ncol=3, frameon=False,
              fontsize=9, title="Phase FEWS NET forecast for the area in a report issued that many months earlier\n"
              "(the most severe phase it forecast for the month the Emergency began or the three months before)",
              title_fontsize=9)
    fig.subplots_adjust(left=0.25, right=0.97, top=0.9, bottom=0.12)
    footnote(fig, "Each row is one map area in which an Emergency (Phase 4+) began, 2011-2026; countries with at least 20 "
             "such areas. Within each country, rows are sorted by how early Emergency was first forecast. Grey cells: that "
             "month's report made no forecast covering the period (forecast periods follow FEWS NET's seasonal calendar). "
             "Source: FEWS NET classifications and forecasts (IPC scale).", width=165)
    fig.savefig(FIG / "t2_every_onset.pdf")
    plt.close(fig)
    KEY["t2_rows"] = int(len(d))


# ---------------------------------------------------------------- Type I
def warnings_table(cs, proj):
    fc = proj[(proj.lead >= 4) & (proj.lead <= 8)].sort_values("report_month") \
        .drop_duplicates(["fnid", "month"], keep="last")[["fnid", "month", "phase", "report_month", "lead"]] \
        .rename(columns={"phase": "fc"})
    m = cs.merge(fc, on=["fnid", "month"])
    return m[m.fc >= 4].copy()


def fig_by_country(w):
    w["result"] = np.select([w.phase >= 4, w.assist_flag], ["came", "flag"], "noflag")
    t = w.groupby(["country_code", "result"]).size().unstack(fill_value=0)
    t = t[t.sum(axis=1) >= 20]
    t["n"] = t.sum(axis=1)
    s = t[["came", "flag", "noflag"]].div(t.n, axis=0).sort_values("came")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    y = np.arange(len(s))
    left = np.zeros(len(s))
    for col, c, lab in [("came", "#c80000", "Came true: the area was in Emergency or worse"),
                        ("flag", "#f4a261", "Did not come true, and FEWS NET says aid is what kept the area out of Emergency"),
                        ("noflag", "#9dc3e6", "Did not come true, with no such statement")]:
        ax.barh(y, s[col], left=left, color=c, label=lab)
        for yi, (l, v) in enumerate(zip(left, s[col])):
            if v >= 0.08:
                ax.text(l + v / 2, yi, f"{v:.0%}", ha="center", va="center", fontsize=8.5,
                        color="white" if col == "came" else "#222")
        left += s[col].values
    ax.set_yticks(y)
    ax.set_yticklabels([f"{NAMES.get(c, c)}  ({int(t.loc[c, 'n']):,})" for c in s.index])
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_xticklabels([f"{v:.0%}" for v in np.linspace(0, 1, 6)])
    ax.set_xlabel("Share of the country's Emergency forecasts")
    ax.set_title("What happened when FEWS NET forecast an Emergency 4-8 months ahead?")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(-0.02, -0.1), fontsize=9.5)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    footnote(fig, "Each forecast is one map area for one month, checked against FEWS NET's later map for that month. Number "
             "of forecasts in brackets; 2011-2026; countries with at least 20. \"Aid is what kept the area out of "
             "Emergency\" is FEWS NET's own flag that the area would be at least one phase worse without humanitarian "
             "assistance. Source: FEWS NET classifications and forecasts (IPC scale).")
    fig.savefig(FIG / "t1_by_country.pdf")
    plt.close(fig)
    KEY["t1_by_country"] = s.round(3).reset_index().to_dict("records")


def funding_index(codes):
    f = E.fts_monthly(codes)
    f = f.reset_index().rename(columns={"level_0": "iso2", "level_1": "month"})
    f.columns = ["iso2", "month", "all", "food"]
    f["year"] = f.month.dt.year
    # complete country x month grid so months without commitments count as zero
    grid = pd.MultiIndex.from_product([f.iso2.unique(), pd.period_range("2010-01", "2024-12", freq="M")],
                                      names=["iso2", "month"])
    f = f.set_index(["iso2", "month"])[["all", "food"]].reindex(grid, fill_value=0).reset_index()
    f["year"] = f.month.dt.year
    for col in ["all", "food"]:
        avg = f.groupby(["iso2", "year"])[col].transform("mean")
        f[col + "_rel"] = np.where(avg > 0, f[col] / avg, np.nan)
    return f.set_index(["iso2", "month"])


def event_paths(events, fund, pre=12, post=6):
    rows = []
    for e in events.itertuples():
        for k in range(-pre, post + 1):
            key = (e.country_code, e.t0 + k)
            if key in fund.index:
                r = fund.loc[key]
                rows.append({"ep": e.Index, "group": e.group, "rel": k, "all_rel": r["all_rel"],
                             "food_rel": r["food_rel"]})
    return pd.DataFrame(rows)


def plot_paths(p, groups, title, xlabel, fname, note, col="all_rel"):
    fig, ax = plt.subplots(figsize=(10, 6))
    rng = np.random.default_rng(0)
    for g, c in groups:
        d = p[p.group == g]
        n_ep = d.ep.nunique()
        # faint: each episode, smoothed over 3 months
        for _, e in d.groupby("ep"):
            s = e.set_index("rel")[col].rolling(3, center=True, min_periods=1).mean()
            ax.plot(s.index, s.values, color=c, alpha=0.06, lw=0.8)
        mean = d.groupby("rel")[col].mean().rolling(3, center=True, min_periods=1).mean()
        # bootstrap band over episodes
        eps = d.ep.unique()
        boots = []
        for _ in range(300):
            pick = rng.choice(eps, len(eps))
            bb = pd.concat([d[d.ep == e] for e in pick]).groupby("rel")[col].mean()
            boots.append(bb.rolling(3, center=True, min_periods=1).mean())
        b = pd.concat(boots, axis=1)
        ax.fill_between(b.index, b.quantile(0.05, axis=1), b.quantile(0.95, axis=1), color=c, alpha=0.15, lw=0)
        ax.plot(mean.index, mean.values, color=c, lw=3, label=f"{g}  ({n_ep} episodes)")
    ax.axvline(0, color="black", lw=1)
    ax.axhline(1, color=GREY, lw=0.8, ls="--")
    ax.text(0.15, 0.02, "1 = the country's average month that year", transform=ax.get_xaxis_transform(),
            fontsize=8.5, color=GREY)
    ax.set_ylim(0, 3.2)
    ax.set_xticks(range(-12, 7, 2))
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Humanitarian funding committed to the country that month\n"
                  "(relative to the country's average month in the same year)")
    ax.set_title(title)
    ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    footnote(fig, note.replace("\n", " "))
    fig.savefig(FIG / fname)
    plt.close(fig)


def fig_funding_onsets(on, m, fund):
    """t = 0: the month an Emergency began in at least one area of the country.
    Groups by how early FEWS NET first forecast Emergency for any of those areas."""
    o = m[m.onset & (m.fc >= 4)].groupby(["country_code", "month"]).lead.max()
    ep = on.groupby(["country_code", "month"]).size().rename("n_areas").reset_index()
    ep["first"] = ep.set_index(["country_code", "month"]).index.map(o)
    ep["group"] = pd.cut(ep["first"].fillna(0), [-1, 0, 4, 8],
                         labels=["Never forecast as Emergency", "First forecast 1-4 months ahead",
                                 "First forecast 5-8 months ahead"]).astype(str)
    ep = ep[ep.month.dt.year <= 2024].rename(columns={"month": "t0"}).reset_index(drop=True)
    p = event_paths(ep, fund)
    groups = [("First forecast 5-8 months ahead", "#7f0000"), ("First forecast 1-4 months ahead", "#f4a261"),
              ("Never forecast as Emergency", GREY)]
    plot_paths(p, groups, "Did money arrive earlier when the emergency was foretold earlier?",
               "Months relative to the month an Emergency began in the country (0)",
               "t1_funding_onsets.pdf",
               "An episode is a country and month in which an Emergency began in at least one map area (2011-2024). "
               "Groups by how early FEWS NET first forecast Emergency for any of those areas.\n"
               "Thick lines: average across episodes (3-month moving average); band: 90% interval from resampling "
               "episodes; faint lines: individual episodes. Source: FEWS NET; UN Financial Tracking Service.")
    KEY["t1_onset_episodes"] = ep.group.value_counts().to_dict()
    pre = p[(p.rel >= -6) & (p.rel <= -1)].groupby("group").all_rel.mean()
    KEY["t1_onset_prewindow_mean"] = pre.round(3).to_dict()


def fig_funding_warnings(w, fund):
    """t = 0: the month for which FEWS NET forecast Emergency (4-8 months ahead)
    in at least one area of the country. Came true if most warned areas were in
    Emergency that month."""
    ep = w.groupby(["country_code", "month"]).agg(n=("fnid", "size"), hit=("phase", lambda x: (x >= 4).mean()),
                                                   flag=("assist_flag", "mean")).reset_index()
    ep["group"] = np.where(ep.hit >= 0.5, "Forecast came true (most warned areas in Emergency)",
                           "Forecast did not come true (most warned areas better than Emergency)")
    ep = ep[ep.month.dt.year <= 2024].rename(columns={"month": "t0"}).reset_index(drop=True)
    p = event_paths(ep, fund)
    groups = [("Forecast came true (most warned areas in Emergency)", "#c80000"),
              ("Forecast did not come true (most warned areas better than Emergency)", BLUE)]
    plot_paths(p, groups, "Did forecasts that failed to come true receive more money beforehand?",
               "Months relative to the month FEWS NET had forecast Emergency for (0); "
               "the forecast was issued 4-8 months before 0",
               "t1_funding_warnings.pdf",
               "An episode is a country and month for which FEWS NET forecast Emergency, 4-8 months ahead, in at "
               "least one map area (2011-2024), checked against its later map.\n"
               "Thick lines: average across episodes (3-month moving average); band: 90% interval from resampling "
               "episodes; faint lines: individual episodes. Source: FEWS NET; UN Financial Tracking Service.")
    plot_paths(p, groups, "Food and nutrition funding only",
               "Months relative to the month FEWS NET had forecast Emergency for (0)",
               "t1_funding_warnings_food.pdf",
               "As in the previous figure, but counting only funding recorded for the food security and "
               "nutrition sectors (often unrecorded before 2017).", col="food_rel")
    KEY["t1_warning_episodes"] = ep.group.value_counts().to_dict()
    pre = p[(p.rel >= -6) & (p.rel <= -1)].groupby("group").all_rel.mean()
    KEY["t1_warning_prewindow_mean"] = pre.round(3).to_dict()


def fig_flag_over_time(cs, w):
    """For each warned area x target month (t=0), the area's most recent
    current-situation map in each month from t-8 to t+6 (maps are carried
    forward up to three months). Lines: share of areas in Emergency or worse,
    and share flagged as held down by aid, for warnings that came true and not."""
    carry = pd.concat([cs.assign(month=cs.month + k) for k in range(4)])
    carry = carry.sort_values("month").drop_duplicates(["fnid", "month"], keep="first") \
        [["fnid", "month", "phase", "assist_flag"]]
    ev = w[["fnid", "month", "phase"]].rename(columns={"month": "t0", "phase": "outcome"})
    ev["group"] = np.where(ev.outcome >= 4, "came", "not")
    rows = []
    for k in range(-8, 7):
        x = ev.assign(month=ev.t0 + k).merge(carry, on=["fnid", "month"], how="inner")
        for g, d in x.groupby("group"):
            rows.append({"rel": k, "group": g, "n": len(d), "p4": (d.phase >= 4).mean(),
                         "flag": d.assist_flag.mean(), "p3flag": (d.assist_flag & (d.phase == 3)).mean()})
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "errors_flag_over_time.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), sharex=True)
    labs = {"came": ("Forecast came true", "#c80000"), "not": ("Forecast did not come true", BLUE)}
    for ax, col, title, ylab in [
            (axes[0], "p4", "A. Share of warned areas in Emergency or worse",
             "Share of warned areas whose current map\nshows Emergency or worse (Phase 4+)"),
            (axes[1], "flag", "B. Share FEWS NET says are held down by aid",
             "Share of warned areas flagged as at least one phase\nbetter than they would be without humanitarian aid")]:
        for g in ["came", "not"]:
            d = r[r.group == g]
            ax.plot(d.rel, d[col], color=labs[g][1], lw=3, marker="o", ms=5,
                    label=f"{labs[g][0]} ({int(ev.group.eq(g).sum()):,} area-months)")
            ax.fill_between(d.rel, d[col] - E.ci(d[col], d.n), d[col] + E.ci(d[col], d.n),
                            color=labs[g][1], alpha=0.15, lw=0)
        ax.axvline(0, color="black", lw=1)
        ax.axvspan(-8, -4, color=GREY, alpha=0.08, lw=0)
        ax.text(-6, 0.97, "forecast\nissued", ha="center", va="top", fontsize=8.5, color="#555",
                transform=ax.get_xaxis_transform())
        ax.text(0.15, 0.97, "month the Emergency\nwas forecast for", ha="left", va="top", fontsize=8.5,
                transform=ax.get_xaxis_transform())
        ax.set_ylim(0, 1)
        ax.set_yticks(np.linspace(0, 1, 6))
        ax.set_yticklabels([f"{v:.0%}" for v in np.linspace(0, 1, 6)])
        ax.set_xticks(range(-8, 7, 2))
        ax.set_xlabel("Months relative to the month FEWS NET had forecast Emergency for")
        ax.set_ylabel(ylab)
        ax.set_title(title)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="upper left", bbox_to_anchor=(0.01, 0.95), ncol=2, fontsize=10)
    fig.suptitle("Areas forecast to be in Emergency: what their maps showed before and after the forecast month",
                 fontweight="bold", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.07, 1, 0.91))
    footnote(fig, "Lines move in steps because current-situation maps are published only three or four times a year. "
             "Each line follows the same map areas month by month: areas that FEWS NET forecast, 4-8 months "
             "ahead, to be in Emergency in month 0 (2011-2026). In each month the area's most recent current-situation "
             "map (up to three months old) is used. \"Held down by aid\" is FEWS NET's own flag that the area would be "
             "at least one phase worse without humanitarian assistance. Bands: 95% intervals, not adjusted for "
             "clustering. Source: FEWS NET classifications and forecasts (IPC scale).", width=190)
    fig.savefig(FIG / "t1_flag_over_time.pdf")
    plt.close(fig)
    KEY["flag_over_time"] = r[r.rel.isin([-8, -4, 0, 4])].round(3).to_dict("records")


def main():
    cs, proj, codes = load()
    on, m = onset_forecasts(cs, proj)
    fig_lines_with_points(m)
    fig_every_onset(m)
    w = warnings_table(cs, proj)
    fig_by_country(w)
    fig_flag_over_time(cs, w)
    fund = funding_index(codes)
    fig_funding_onsets(on, m, fund)
    fig_funding_warnings(w, fund)
    (TAB / "errors_detail_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))
    print(json.dumps(KEY, indent=1, default=str))


if __name__ == "__main__":
    main()
