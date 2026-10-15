"""Ethiopia: first stage and food-insecurity outcomes for the 2025 US aid cut (zone level).

Data assembled by code/77_ethiopia_assemble.py (input/ethiopia/tidy/; references/ethiopia_sources.md).
Exposure (zone, 2024): share of OCHA 4W activity rows with a US donor (USAID/BHA/State; all sectors and
nutrition only); share of the zone's food-assistance woredas served by JEOP (the USAID-funded
Catholic Relief Services consortium) in 2024.
First stage: change in 4W activity rows and partners, 2025 vs 2024 (all, food, nutrition, health).
Outcome: FEWS NET woreda current-situation classifications (fnid ET2023C1xxxxxx = OCHA woreda code),
summarised by zone: share of woredas in Phase 3+ and mean phase. Rounds Feb/Jun/Oct 2024 (pre),
Oct 2025, Feb and Jun 2026 (post; FEWS NET published nothing on Ethiopia Feb-May 2025). Same-season
comparison: Oct 2025 vs Oct 2024. Region-clustered errors (11 regions).
Caveats: classifications are sticky and partly reflect assistance; nutrition outcomes are not available
publicly on both sides of the cut (SMART surveys in 2025-26 cover few, different zones).

Outputs: output/tables/eth_*.csv, output/figures/eth_results.pdf, output/us_cut_memo/numbers_eth.tex
"""
import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
ET = INP / "ethiopia" / "tidy"
M, KEY = {}, {}
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M71 = load("m71", "71_somalia_first_stage.py")
M73 = load("m73", "73_somalia_markets_displacement.py")


def exposure():
    e = pd.read_csv(ET / "exposure_4w_zone_2024.csv")
    e["us_share"] = e.us_share_rows_2024
    e["us_nut"] = e.n_rows_nutrition_us_2024 / e.n_rows_nutrition_2024.replace(0, np.nan)
    e["us_food"] = e.n_rows_food_us_2024 / e.n_rows_food_2024.replace(0, np.nan)
    for s in ["", "_food", "_nutrition", "_health"]:
        a, b = e.get(f"n_rows{s}_2024"), e.get(f"n_rows{s}_2025")
        if a is not None and b is not None:
            e[f"dlog{s or '_all'}"] = np.log(b + 1) - np.log(a + 1)
    e["dlog_partners"] = e.dlog_partners_2025_vs_2024
    f = pd.read_csv(ET / "exposure_food_operator_zone_year.csv")
    j = f[f.year == 2024].set_index("zone_pcode").jeop_share_woredas.rename("jeop24")
    e = e.set_index("zone_pcode").join(j)
    e["jeop24"] = e.jeop24.fillna(0)
    e["region"] = e.index.str[:4]
    KEY["zones"] = int(len(e))
    KEY["us_share_desc"] = e.us_share.describe().round(3).to_dict()
    KEY["jeop_zones"] = int((e.jeop24 > 0).sum())
    return e


def first_stage(e):
    rows = []
    for x in ["dlog_all", "dlog_food", "dlog_nutrition", "dlog_health", "dlog_partners"]:
        for z in ["us_share", "us_nut", "jeop24"]:
            d = e.dropna(subset=[x, z])
            d = d[np.isfinite(d[x])]
            A = np.column_stack([np.ones(len(d)), d[z]])
            b, V = M71.cl_ols(d[x].values, A, d.region.values)
            rows.append(dict(x=x, z=z, b=b[1], se=np.sqrt(V[1, 1]), F=b[1] ** 2 / V[1, 1], n=len(d),
                             b_sd=b[1] * d[z].std(), x_mean=d[x].mean()))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "eth_firststage.csv", index=False)
    return R


def outcomes(e):
    c = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    c = c[(c.country_code == "ET") & c.fnid.str.startswith("ET2023")].copy()
    c["month"] = c.month.astype(str)
    cov = c.groupby("month").fnid.nunique()
    c = c[c.month.isin(cov[cov > 1000].index)]
    c["zone"] = "ET" + c.fnid.str[8:12]
    pop = pd.read_parquet(INP / "panel" / "fnid_population.parquet").set_index("fnid")["pop"]
    c["w"] = c.fnid.map(pop).fillna(1.0)
    c["p3"] = (c.phase >= 3).astype(float)
    c["flag"] = c.assist_flag.astype(float)
    Z = c.groupby(["zone", "month"]).apply(lambda s: pd.Series({
        "share3": 100 * np.average(s.p3, weights=s.w), "phase": np.average(s.phase, weights=s.w),
        "flag": 100 * np.average(s.flag, weights=s.w)})).reset_index()
    KEY["rounds"] = sorted(Z.month.unique())
    KEY["zone_match"] = float(Z.zone.isin(e.index).mean())
    M["etZoneMatch"] = f"{100 * KEY['zone_match']:.0f}"
    Z = Z.merge(e[["us_share", "us_nut", "jeop24", "region", "dlog_all", "dlog_partners"]], left_on="zone", right_index=True)
    Z["post"] = (Z.month >= "2025-01").astype(float)
    Z["dist"] = Z.zone
    nat = c.groupby("month").apply(lambda s: pd.Series({"share3": 100 * np.average(s.p3, weights=s.w),
                                                        "flag": 100 * np.average(s.flag, weights=s.w)}))
    nat.to_csv(TAB / "eth_national.csv")
    KEY["national"] = nat.round(1).to_dict()
    return Z


def main():
    e = exposure()
    FS = first_stage(e)
    Z = outcomes(e)
    sd = {z: Z.drop_duplicates("zone")[z].std() for z in ["us_share", "us_nut", "jeop24", "dlog_all"]}
    rows, ev = [], []
    for y in ["share3", "phase", "flag"]:
        for z in ["us_share", "us_nut", "jeop24"]:
            for lab, sub in [("all post rounds", Z), ("Oct 2025 vs 2024 rounds", Z[Z.month.isin(
                    [m for m in Z.month.unique() if m < "2025"] + ["2025-10"])])]:
                r = M73.dd(sub, y, z, ["zone", "month"], scale=sd[z])
                rows.append(dict(outcome=y, exposure=z, sample=lab, **r))
            # same-season comparisons: zone x season-of-year fixed effects (Feb/Jun/Oct maps differ by season)
            Zs = Z.assign(zs=Z.zone + "|" + Z.month.str[5:7])
            r = M73.dd(Zs, y, z, ["zs", "month"], scale=sd[z])
            rows.append(dict(outcome=y, exposure=z, sample="same-season", **r))
        # actual activity loss (minus log change in 4W rows), per s.d.
        Zl = Z.assign(loss=-Z.dlog_all)
        r = M73.dd(Zl, y, "loss", ["zone", "month"], scale=Zl.drop_duplicates("zone").loss.std())
        rows.append(dict(outcome=y, exposure="activity loss", sample="all post rounds", **r))
        for z in ["us_share", "jeop24"]:
            v = M73.event(Z.assign(t=Z.month), y, z, ["zone", "month"], "t", "2024-10", sd[z])
            v["outcome"], v["exposure"] = y, z
            ev.append(v)
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "eth_did.csv", index=False)
    EV = pd.concat(ev)
    EV.to_csv(TAB / "eth_event.csv", index=False)
    figure(e, EV)
    write(FS, R, EV)
    pd.set_option("display.width", 230, "display.max_rows", 200)
    print(KEY)
    print(FS.round(3).to_string())
    print(R.round(3).to_string())
    print(EV.round(2).to_string())


def figure(e, EV):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))
    ax = axes[0]
    d = e.dropna(subset=["us_share", "dlog_all"])
    ax.scatter(100 * d.us_share, d.dlog_all, s=12, color=BLUE, alpha=0.6, lw=0)
    b = np.polyfit(100 * d.us_share, d.dlog_all, 1)
    xs = np.linspace(0, 100 * d.us_share.max(), 10)
    ax.plot(xs, b[0] * xs + b[1], color=ORANGE)
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xlabel("US-donor share of 2024 activities (%)", fontsize=9)
    ax.set_ylabel("Log change in activities, 2025 vs 2024", fontsize=9)
    ax = axes[1]
    for z, col in [("us_share", ORANGE), ("jeop24", BLUE)]:
        v = EV[(EV.outcome == "share3") & (EV.exposure == z)].sort_values("t")
        x = np.arange(len(v)) + (0.12 if z == "jeop24" else -0.12)
        ax.errorbar(x, v.b, yerr=1.96 * v.se, fmt="o", ms=3.5, color=col, lw=1,
                    label={"us_share": "US-donor share", "jeop24": "JEOP food share"}[z])
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xticks(range(len(v)))
    ax.set_xticklabels([t[2:] for t in v.t], fontsize=7, rotation=90)
    ax.set_title("Woredas in Phase 3+ (pp, FEWS NET)\nper s.d. of exposure, vs Oct 2024", fontsize=9)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "eth_results.pdf")
    plt.close(fig)


def write(FS, R, EV):
    f2 = lambda v: f"{v:.2f}"
    xn = {"dlog_all": "All", "dlog_food": "Food", "dlog_nutrition": "Nut", "dlog_health": "Hea", "dlog_partners": "Part"}
    zn = {"us_share": "Us", "us_nut": "UsNut", "jeop24": "Jeop"}
    for r in FS.itertuples():
        t = xn[r.x] + zn[r.z]
        M[f"etF{t}"], M[f"etB{t}"], M[f"etBsd{t}"], M[f"etXm{t}"] = f"{r.F:.1f}", f2(r.b), f2(r.b_sd), f2(r.x_mean)
    yn = {"share3": "Pthree", "phase": "Phase", "flag": "Flag"}
    zn2 = {"us_share": "Us", "us_nut": "UsNut", "jeop24": "Jeop", "activity loss": "Loss"}
    sn = {"all post rounds": "", "Oct 2025 vs 2024 rounds": "Oct", "same-season": "Ss"}
    for r in R.itertuples():
        t = yn[r.outcome] + zn2[r.exposure] + sn[r.sample]
        M[f"etD{t}"], M[f"etDse{t}"], M[f"etDp{t}"] = f2(r.b), f2(r.se), f2(r.p)
    nat = KEY["national"]["share3"]
    M["etNatOctTf"], M["etNatOctTv"] = f"{nat['2024-10']:.0f}", f"{nat['2025-10']:.0f}"
    M["etNatJunTs"] = f"{nat.get('2026-06', np.nan):.0f}"
    M["etZones"] = KEY["zones"]
    M["etJeopZones"] = KEY["jeop_zones"]
    M["etUsMean"] = f"{100 * KEY['us_share_desc']['mean']:.0f}"
    (ROOT / "output" / "us_cut_memo" / "numbers_eth.tex").write_text(
        "% generated by code/76_ethiopia_us_cut.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))


if __name__ == "__main__":
    main()
