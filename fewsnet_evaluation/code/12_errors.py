"""Type I and Type II errors in famine warnings, descriptively.

Type II (missed emergencies). An "onset" is an area whose current-situation
map shows Emergency or worse (Phase 4+) after its previous map, within six
months, showed Phase 3 or better. For each onset we look back at the forecasts
FEWS NET had issued for that month 1-8 months earlier, and compare with areas
whose previous map was also below Emergency but which stayed below Emergency.
The gap between the two lines is how well warnings discriminate; the onset
line itself is the share of real emergencies that were warned of. Replicated
on the multi-agency IPC analyses (2021 on), where an area's phase is derived
from its population shares using the IPC 20% rule.

Type I (false alarms). A warning is a medium-term forecast of Phase 4+ (issued
4-8 months ahead) for a month in which a current-situation map exists. A false
alarm is a warning followed by Phase 3 or better. Two descriptive checks of
whether false alarms reflect an aid response:
  (a) within the IPC system: how often the realised map carries FEWS NET's own
      flag that humanitarian assistance is keeping the area at least one phase
      better than it would otherwise be;
  (b) with aid flows: humanitarian funding committed to the country around new
      warnings, for warnings that came true versus those that did not.

Outputs: output/figures/type2_*.pdf, type1_*.pdf; output/tables/errors_*.csv
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False})
C1, C2, C3 = "#1f4e79", "#c55a11", "#8c8c8c"
KEY = {}
NAMES = {"AF": "Afghanistan", "YE": "Yemen", "SS": "South Sudan", "ET": "Ethiopia", "NG": "Nigeria",
         "SO": "Somalia", "KE": "Kenya", "SD": "Sudan", "HT": "Haiti", "CD": "DR Congo", "ML": "Mali",
         "BF": "Burkina Faso", "NE": "Niger", "MZ": "Mozambique", "ZW": "Zimbabwe", "MG": "Madagascar",
         "TD": "Chad", "MW": "Malawi", "CF": "C. African Rep.", "GT": "Guatemala", "UG": "Uganda"}


def ci(p, n):
    se = np.sqrt(p * (1 - p) / np.maximum(n, 1))
    return 1.96 * se


# ------------------------------------------------------------------ events
def onsets(cs):
    """Each current-situation observation with the area's previous one."""
    c = cs.sort_values(["fnid", "month"]).copy()
    c["prev_phase"] = c.groupby("fnid").phase.shift()
    c["prev_month"] = c.groupby("fnid").month.shift()
    gap = (c.month - c.prev_month).apply(lambda x: x.n if pd.notna(x) else np.nan)
    c = c[(gap > 0) & (gap <= 6) & (c.prev_phase <= 3)].copy()
    c["onset"] = c.phase >= 4
    return c


def forecasts_by_lead(ev, proj, max_k=8, window=3):
    """For each event (area, outcome month t0) and each issue lag k = 1..8, the
    most severe phase that a report issued in month t0-k forecast for the area
    for any month in [t0-window, t0]. Forecast windows are pinned to FEWS NET's
    seasonal calendar, so a forecast issued well ahead often covers the run-up
    to the outcome month rather than the month itself."""
    ev = ev[["fnid", "month"]].drop_duplicates().rename(columns={"month": "t0"})
    p = proj[["fnid", "month", "report_month", "phase"]].merge(ev, on="fnid")
    lag = (p.t0 - p.report_month).apply(lambda x: x.n)
    to = (p.t0 - p.month).apply(lambda x: x.n)
    p = p[(lag >= 1) & (lag <= max_k) & (to >= 0) & (to <= window)].assign(lead=lag)
    return (p.groupby(["fnid", "t0", "lead"]).phase.max().rename("fc").reset_index()
             .rename(columns={"t0": "month"}))


def type2(cs, proj):
    ev = onsets(cs)
    # all onsets; a random sample of non-onsets keeps the merge manageable
    ev = pd.concat([ev[ev.onset], ev[~ev.onset].sample(min(30000, (~ev.onset).sum()), random_state=1)])
    fc = forecasts_by_lead(ev, proj)
    m = ev[["country_code", "fnid", "month", "onset", "prev_phase", "phase"]].merge(fc, on=["fnid", "month"])
    rows = []
    for (onset, lead), g in m.groupby(["onset", "lead"]):
        rows.append({"onset": onset, "lead": lead, "n": len(g),
                     "share_fc4": (g.fc >= 4).mean(), "share_fc3": (g.fc >= 3).mean()})
    curve = pd.DataFrame(rows)
    curve.to_csv(TAB / "errors_type2_curve.csv", index=False)

    # Event-level summary: was the onset ever forecast as Emergency 1-8 months ahead?
    per = m[m.onset].groupby(["country_code", "fnid", "month"]).agg(
        any4=("fc", lambda x: (x >= 4).any()), any3=("fc", lambda x: (x >= 3).any()),
        lead4=("fc", lambda x: None)).reset_index()
    first4 = m[m.onset & (m.fc >= 4)].groupby(["fnid", "month"]).lead.max().rename("earliest_lead")
    per = per.merge(first4, on=["fnid", "month"], how="left")
    n_on = int(ev.onset.sum())
    KEY["type2"] = {
        "onsets": n_on, "onsets_with_forecasts": int(len(per)),
        "share_warned_emergency_any_lead": float(per.any4.mean()),
        "share_warned_crisis_only": float((per.any3 & ~per.any4).mean()),
        "share_no_warning_at_all": float((~per.any3).mean()),
        "share_onsets_from_phase3": float((ev[ev.onset].prev_phase == 3).mean()),
        "median_earliest_lead": float(per.earliest_lead.median()),
        "onset_years": ev[ev.onset].month.dt.year.value_counts().sort_index().to_dict(),
    }
    byc = per.groupby("country_code").agg(n=("any4", "size"), warned=("any4", "mean"),
                                          crisis_only=("any3", "mean")).query("n >= 15")
    byc["crisis_only"] = byc.crisis_only - byc.warned
    byc = byc.sort_values("warned")
    byc.to_csv(TAB / "errors_type2_by_country.csv")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    for onset, col, lab in [(True, C2, "Emergencies that happened"),
                            (False, C1, "Areas that stayed below Emergency")]:
        g = curve[curve.onset == onset].sort_values("lead")
        ax.plot(g.lead, g.share_fc4, color=col, marker="o", ms=3, label=lab)
        ax.fill_between(g.lead, g.share_fc4 - ci(g.share_fc4, g.n), g.share_fc4 + ci(g.share_fc4, g.n),
                        color=col, alpha=0.15, lw=0)
        ax.plot(g.lead, g.share_fc3, color=col, ls=":", lw=1)
    ax.set_xlabel("Months before the outcome that the forecast was issued\n(forecast for that month or the three before it)")
    ax.set_ylabel("Share forecast to be in Emergency")
    ax.set_xticks(range(1, 9))
    ax.set_ylim(0, 1)
    ax.plot([], [], color=C3, ls=":", lw=1, label="(dotted: forecast Crisis or worse)")
    ax.legend(frameon=False, fontsize=6.8, loc="center right", bbox_to_anchor=(1.0, 0.62))
    ax.set_title("A. Were real emergencies forecast?", fontsize=9, loc="left")

    ax = axes[1]
    y = np.arange(len(byc))
    ax.barh(y, byc.warned, color=C2, label="Forecast Emergency")
    ax.barh(y, byc.crisis_only, left=byc.warned, color="#f4b183", label="Forecast Crisis only")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{NAMES.get(c, c)} ({n})" for c, n in zip(byc.index, byc.n)], fontsize=6.5)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of onsets warned 1-8 months ahead")
    ax.legend(frameon=False, fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    ax.set_title("B. By country (number of onsets)", fontsize=9, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "type2_warnings_before_emergencies.pdf")
    plt.close(fig)
    return per


# ------------------------------------------------------------------ IPC replication
def ipc_area_phase(df):
    """IPC area phase from population shares: the highest phase p such that at
    least 20% of the population is in phase p or worse."""
    w = df.pivot_table(index=["Country", "Level 1", "Area", "Date of analysis", "Validity period", "From", "To"],
                       columns="Phase", values="Percentage", aggfunc="first")
    phases = [str(p) for p in [1, 2, 3, 4, 5] if str(p) in w.columns]
    w = w[phases].fillna(0)
    out = pd.Series(1, index=w.index)
    for p in [2, 3, 4, 5]:
        cum = w[[str(q) for q in range(p, 6) if str(q) in w.columns]].sum(axis=1)
        out[cum >= 0.2] = p
    return out.rename("phase").reset_index()


def type2_ipc():
    d = pd.read_csv(INP / "ipc" / "ipc_global_area_long.csv", low_memory=False)
    d = d[d.Phase.isin(["1", "2", "3", "4", "5"])]
    a = ipc_area_phase(d)
    a["From"], a["To"] = pd.to_datetime(a.From), pd.to_datetime(a.To)
    a["area"] = a.Country + "|" + a["Level 1"].fillna("") + "|" + a.Area
    cur = a[a["Validity period"] == "current"].sort_values(["area", "From"])
    cur["prev_phase"] = cur.groupby("area").phase.shift()
    cur["prev_from"] = cur.groupby("area").From.shift()
    cur = cur[cur.prev_phase.notna() & ((cur.From - cur.prev_from).dt.days <= 400) & (cur.prev_phase <= 3)]
    cur["onset"] = cur.phase >= 4
    proj = a[a["Validity period"].isin(["first projection", "second projection"])]
    # A projection "covers" a current analysis if its period overlaps it and it
    # was made in an earlier analysis
    m = cur.merge(proj[["area", "From", "To", "phase", "Date of analysis"]], on="area", suffixes=("", "_p"))
    m = m[(m.From_p <= m.To) & (m.To_p >= m.From) & (pd.to_datetime(m["Date of analysis_p"], format="%b %Y")
                                                    < pd.to_datetime(m["Date of analysis"], format="%b %Y"))]
    best = m.groupby(["area", "From", "onset"]).phase_p.max().reset_index()
    res = best.groupby("onset").agg(n=("phase_p", "size"), share_fc4=("phase_p", lambda x: (x >= 4).mean()),
                                    share_fc3=("phase_p", lambda x: (x >= 3).mean()))
    res.to_csv(TAB / "errors_type2_ipc.csv")
    KEY["type2_ipc"] = res.round(3).reset_index().to_dict("records")
    return res


# ------------------------------------------------------------------ type I
def type1_flag(cs, proj):
    fc = proj[(proj.lead >= 4) & (proj.lead <= 8)].sort_values("report_month") \
        .drop_duplicates(["fnid", "month"], keep="last")[["fnid", "month", "phase", "report_month"]] \
        .rename(columns={"phase": "fc"})
    m = cs.merge(fc, on=["fnid", "month"])
    m["warned"] = m.fc >= 4
    cells = []
    for lab, sel in [("Warned, Emergency happened\n(realised Phase 4+)", m.warned & (m.phase >= 4)),
                     ("Warned, did not happen:\nrealised Crisis (3)", m.warned & (m.phase == 3)),
                     ("Not warned,\nrealised Crisis (3)", ~m.warned & (m.phase == 3)),
                     ("Warned, did not happen:\nrealised Stressed or better", m.warned & (m.phase <= 2)),
                     ("Not warned,\nrealised Stressed or better", ~m.warned & (m.phase <= 2))]:
        g = m[sel]
        cells.append({"cell": lab, "n": len(g), "flag": g.assist_flag.mean()})
    cells = pd.DataFrame(cells)
    cells.to_csv(TAB / "errors_type1_flag.csv", index=False)
    n_w = int(m.warned.sum())
    KEY["type1"] = {"warnings": n_w, "false_alarm_share": float((m[m.warned].phase <= 3).mean()),
                    "false_alarms_realised_3": float((m[m.warned].phase == 3).mean()),
                    "flag": cells.assign(cell=cells.cell.str.replace("\n", " ")).round(3).to_dict("records")}

    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    cols = [C3, C2, C1, "#f4b183", "#9dc3e6"]
    y = np.arange(len(cells))[::-1]
    ax.barh(y, cells.flag, color=cols, xerr=ci(cells.flag, cells.n), error_kw={"lw": 0.8, "ecolor": "#555"})
    ax.set_yticks(y)
    ax.set_yticklabels([f"{c}  (n={n:,})" for c, n in zip(cells.cell, cells.n)], fontsize=6.8)
    ax.set_xlabel("Share of areas FEWS NET flags as kept at least one\n"
                  "phase better than otherwise by humanitarian aid")
    fig.tight_layout()
    fig.savefig(FIG / "type1_aid_flag.pdf")
    plt.close(fig)
    return m


def fts_monthly(codes):
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet")
    f = f[((f.boundary == "incoming") | f.boundary.isna()) & f.status.isin(["paid", "commitment"])]
    fix = {"Côte d'Ivoire": "CI", "Venezuela, Bolivarian Republic of": "VE", "Syrian Arab Republic": "SY",
           "Democratic Republic of the Congo": "CD"}
    name2 = {**dict(zip(codes.preferred_name, codes.iso3166a2)), **dict(zip(codes.iso_en_name, codes.iso3166a2)), **fix}
    f["iso2"] = f.dest_country.map(name2)          # multi-country flows drop out here
    f["month"] = pd.to_datetime(f.decision_date, errors="coerce").dt.to_period("M")
    f["food"] = f.cluster.fillna("").str.contains("Food Security|Nutrition", regex=True)
    f = f.dropna(subset=["iso2", "month"])
    allm = f.groupby(["iso2", "month"]).amount_usd.sum().rename("all")
    food = f[f.food].groupby(["iso2", "month"]).amount_usd.sum().rename("food")
    return pd.concat([allm, food], axis=1).fillna(0)


def type1_funding(m, codes, horizon=6):
    """Country-season episodes: every report containing at least one Emergency
    warning that can be checked against a later map. y = share of warned areas
    that did NOT reach Emergency; x = log humanitarian funding committed to the
    country in the months from the report to the end of the forecast window,
    with country and year averages removed."""
    w = m[m.warned].groupby(["country_code", "report_month"]).agg(
        n_warned=("fnid", "nunique"), false_alarm=("phase", lambda x: (x <= 3).mean()),
        flagged=("assist_flag", "mean")).reset_index()
    fund = fts_monthly(codes)
    def window_sum(cc, r, col):
        idx = pd.MultiIndex.from_product([[cc], pd.period_range(r, r + horizon, freq="M")])
        return fund[col].reindex(idx, fill_value=0).sum()
    w["fund_all"] = [window_sum(c, r, "all") for c, r in zip(w.country_code, w.report_month)]
    w["fund_food"] = [window_sum(c, r, "food") for c, r in zip(w.country_code, w.report_month)]
    w["year"] = w.report_month.dt.year
    w = w[w.year <= 2024]                       # funding records for 2025-26 are incomplete
    for col in ["fund_all", "fund_food"]:
        lx = np.log1p(w[col])
        w[col + "_dm"] = lx - lx.groupby(w.country_code).transform("mean") \
            - lx.groupby(w.year).transform("mean") + lx.mean()
    w["fa_dm"] = w.false_alarm - w.false_alarm.groupby(w.country_code).transform("mean") + w.false_alarm.mean()
    w.to_csv(TAB / "errors_type1_episodes.csv", index=False)

    rng = np.random.default_rng(0)
    def slope(d, x):
        X = np.c_[np.ones(len(d)), d[x]]
        return np.linalg.lstsq(X, d.fa_dm, rcond=None)[0][1]
    res = {}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    for ax, col, title in [(axes[0], "fund_all_dm", "A. All humanitarian funding"),
                           (axes[1], "fund_food_dm", "B. Food and nutrition funding")]:
        d = w.dropna(subset=[col])
        b = slope(d, col)
        cc = d.country_code.unique()
        boots = [slope(pd.concat([d[d.country_code == c] for c in rng.choice(cc, len(cc))]), col)
                 for _ in range(500)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        res[col] = {"slope": round(b, 3), "ci": [round(lo, 3), round(hi, 3)], "n": len(d), "countries": len(cc)}
        bins = pd.qcut(d[col], 8, duplicates="drop")
        g = d.groupby(bins).agg(x=(col, "mean"), y=("fa_dm", "mean"), n=("fa_dm", "size"))
        ax.scatter(d[col], d.fa_dm, s=5, color=C3, alpha=0.25, lw=0)
        ax.scatter(g.x, g.y, s=28, color=C2, zorder=3)
        xs = np.linspace(d[col].quantile(0.02), d[col].quantile(0.98), 10)
        ax.plot(xs, d.fa_dm.mean() + b * (xs - d[col].mean()), color=C2, lw=1)
        ax.set_title(title, fontsize=9, loc="left")
        ax.set_xlabel("Funding committed during forecast window\n(log, relative to country and year average)")
        ax.text(0.03, 0.04, f"slope {b:.2f} [{lo:.2f}, {hi:.2f}]\n{len(d)} country-seasons, {len(cc)} countries",
                transform=ax.transAxes, fontsize=6.5, color="#333")
    axes[0].set_ylabel("Share of Emergency warnings\nthat did not come true")
    axes[0].set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(FIG / "type1_funding_around_warnings.pdf")
    plt.close(fig)
    KEY["type1_funding"] = res
    KEY["type1_episode_count"] = int(len(w))
    return w


def main():
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    proj = pd.read_parquet(INP / "fewsnet" / "proj_monthly.parquet")
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    type2(cs, proj)
    type2_ipc()
    m = type1_flag(cs, proj)
    type1_funding(m, codes)
    (TAB / "errors_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))
    print(json.dumps(KEY, indent=1, default=str))


if __name__ == "__main__":
    main()
