"""A crude benefit-cost calculation for FEWS NET.

Chain of assumptions (each a range):
  1. FEWS NET's word: in every area-round it flags "!", humanitarian assistance keeps
     the area one phase better than it would otherwise be (counterfactual = phase + 1).
  2. People: area population (WorldPop 2020, UN-adjusted, 1 km) over the time until
     the next map (capped at 6 months).
  3. What a phase means: IPC reference-table thresholds for the crude death rate
     (deaths/10,000/day) and global acute malnutrition among under-5s, and the
     empirical shares of people in Crisis+ / Emergency+ in areas of each phase in the
     official IPC and Cadre Harmonise data.
  4. FEWS NET's share of that aid: from the funding regressions, the share of
     humanitarian funding in the country-round attributable to FEWS NET, where x is
     FEWS NET's contribution (or its whole forecast) for the country-round and beta the
     funding response: 1 - exp(-beta x) for x >= 0 and -(1 - exp(beta x)) for x < 0
     (symmetric; the one-sided form 1 - exp(-beta x) throughout is a sensitivity check).
     Signed: where FEWS NET was less alarmed than public data, the share is negative.
  5. Cost: FEWS NET's annual budget.

Outputs: output/tables/benefit_cost*.csv, output/cgd_paper/figures/fig7_benefit_cost.pdf,
         numbers appended by 40_paper.py from benefit_cost_key.json
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
import rasterio
from rasterio.mask import mask as rmask

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
FIG = ROOT / "output" / "cgd_paper" / "figures"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FV = load("fv", "32_forecast_value.py")
YEARS = 14                     # 2011-2024
U5 = 0.17                      # share of population under five (sub-Saharan Africa, roughly)

# IPC reference table (area outcomes): crude death rate, deaths per 10,000 per day.
# Phases 1-2: < 0.5; Phase 3: 0.5-1; Phase 4: 1-2; Phase 5: > 2.
CDR = {"low": {1: 0.75, 2: 0.75, 3: 0.75, 4: 1.00, 5: 2.00},     # deaths only above Crisis: no excess
                                                                   # mortality from Crisis itself (the IPC's
                                                                   # description of Phase 3); bottom of each band
       "central": {1: 0.30, 2: 0.30, 3: 0.75, 4: 1.50, 5: 3.00},  # mid-points (Phase 5: 2-4)
       "high": {1: 0.25, 2: 0.25, 3: 1.00, 4: 2.00, 5: 4.00}}     # top of each band
# Global acute malnutrition among under-5s: <5%, 5-10%, 10-15%, 15-30%, >30%.
GAM = {"low": {1: 0.04, 2: 0.05, 3: 0.10, 4: 0.15, 5: 0.30},
       "central": {1: 0.025, 2: 0.075, 3: 0.125, 4: 0.225, 5: 0.35},
       "high": {1: 0.0, 2: 0.10, 3: 0.15, 4: 0.30, 5: 0.40}}

BUDGET = {"low": 27e6, "central": 64e6, "high": 90e6}


def rounds():
    c = pd.read_parquet(INP / "fewsnet" / "classifications.parquet", columns=["scenario", "report_month"])
    n = c[c.scenario == "CS"].groupby("report_month").size()
    return n[n > 1000].index


def flagged_rounds():
    R = rounds()
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet")
    cs = cs[cs.month.isin(R)].sort_values(["fnid", "month"])
    cs["next"] = cs.groupby("fnid").month.shift(-1)
    cs = cs[cs.month.dt.year <= 2024]
    gap = (cs.next - cs.month).apply(lambda x: x.n if pd.notna(x) else np.nan)
    cs["months"] = gap.where(gap <= 6, 4).fillna(4)
    return cs, cs[cs.assist_flag == True].copy()


def populations(fnids):
    f = INP / "panel" / "fnid_population.parquet"
    if f.exists():
        p = pd.read_parquet(f)
        if set(fnids) <= set(p.fnid):
            return p
    units = FV.unit_geoms(fnids)
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    i23 = dict(zip(codes.iso3166a2, codes.iso3166a3))
    units["iso3"] = units.fnid.str[:2].map(i23)
    rows = []
    for iso, g in units.groupby("iso3"):
        tif = INP / "worldpop" / f"{iso}.tif"
        if not tif.exists():
            continue
        with rasterio.open(tif) as src:
            nod = src.nodata
            for fn, geom in zip(g.fnid, g.geometry):
                try:
                    a, _ = rmask(src, [geom], crop=True, all_touched=False)
                    v = a[0].astype(float)
                    v = v[(v > 0) & (v != nod)] if nod is not None else v[v > 0]
                    rows.append((fn, float(v.sum())))
                except Exception:
                    rows.append((fn, np.nan))
        print("population", iso, len(g), flush=True)
    p = pd.DataFrame(rows, columns=["fnid", "pop"])
    p.to_parquet(f, index=False)
    return p


def main():
    allcs, fl = flagged_rounds()
    pop = populations(sorted(fl.fnid.unique()))
    fl = fl.merge(pop, on="fnid", how="left")
    print("flagged area-rounds", len(fl), "with population", round(fl["pop"].notna().mean(), 3),
          "median pop", fl["pop"].median())
    fl["person_days"] = fl["pop"] * fl.months * 30.4
    fl["p"] = fl.phase.clip(1, 4).astype(int)
    fl["cf"] = fl.p + 1
    # empirical shares of people in Crisis+ / Emergency+ by area phase (official IPC / CH)
    o = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    o = o[o.phase.between(1, 5)]
    s3 = o.groupby("phase").share3.mean().to_dict()
    s4 = o.groupby("phase").share4.mean().to_dict()
    s3[5], s4[5] = max(s3.get(5, 0.9), 0.9), max(s4.get(5, 0.6), 0.6)
    fl["d_crisis"] = fl.cf.map(s3) - fl.p.map(s3)          # share of people kept out of Crisis or worse
    fl["d_emerg"] = fl.cf.map(s4) - fl.p.map(s4)           # ... out of Emergency or worse
    for k in CDR:
        fl[f"deaths_{k}"] = fl.person_days * (fl.cf.map(CDR[k]) - fl.p.map(CDR[k])) / 1e4
        fl[f"wasting_{k}"] = fl["pop"] * U5 * fl.months / 12 * (fl.cf.map(GAM[k]) - fl.p.map(GAM[k]))
    fl["crisis_py"] = fl.person_days / 365 * fl.d_crisis
    fl["emerg_py"] = fl.person_days / 365 * fl.d_emerg
    # FEWS NET's share of the aid: country-round contribution / forecast, and funding responses
    P = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet",
                        columns=["fnid", "r", "country_code", "c_fc3", "ci_fc3", "fc3"])
    cr = P.groupby(["country_code", "r"])[["c_fc3", "ci_fc3", "fc3"]].mean().reset_index().rename(columns={"r": "month"})
    fl = fl.merge(cr, on=["country_code", "month"], how="left")
    C = pd.read_csv(TAB / "fewsnet_contribution.csv")
    C = C[(C.block == "funding") & (C.spec == "forecast") & C["sample"].str.contains("within country")]
    gb = lambda b, f: C[(C.baseline == b) & (C["sample"] == f"{f} funding, within country") & (C.term == "contrib_fc3")].coef.iloc[0]
    Pq = pd.read_csv(TAB / "aid_response_pooled.csv")
    gf = lambda f, sp: Pq[(Pq.funding == f) & (Pq.phase == "3+") & (Pq.vars == "together") & (Pq.term == "forecast") & (Pq.spec == sp)].coef.iloc[0]
    ATTR = [
        ("A1", "FEWS NET's distinctive information (beyond rainfall, conflict, prices and official analyses); all humanitarian funding",
         "ci_fc3", gb("raw data + latest Cadre Harmonise / IPC", "all")),
        ("A2", "FEWS NET's distinctive information (beyond rainfall, conflict and prices); all humanitarian funding",
         "c_fc3", gb("raw data", "all")),
        ("A3", "FEWS NET's distinctive information (beyond rainfall, conflict and prices); food and nutrition funding",
         "c_fc3", gb("raw data", "food")),
        ("A4", "FEWS NET's whole forecast; all humanitarian funding (within country)", "fc3",
         gf("all", "+ country FE (within-country)")),
        ("A5", "FEWS NET's whole forecast; food and nutrition funding (within country)", "fc3",
         gf("food", "+ country FE (within-country)")),
    ]
    have = fl.dropna(subset=["pop", "c_fc3"])
    print("flagged area-rounds used:", len(have), "of", len(fl))
    gross = {k: have[f"deaths_{k}"].sum() / YEARS for k in CDR}
    gross_py = have.crisis_py.sum() / YEARS
    def attribute(beta, x, form):
        """Share of the aid in the country-round attributable to FEWS NET.
        one-sided: 1 - exp(-beta x), the exact counterpart of the log-funding regression. For x < 0 it is
                   the extra funding there would have been without FEWS NET, as a share of actual funding,
                   and is unbounded below.
        symmetric: the same for x >= 0; for x < 0, -(1 - exp(beta x)), the funding FEWS NET subtracted
                   as a share of what there would have been without it. Both branches are shares of the
                   larger of actual and counterfactual funding, so over- and under-alarm count equally."""
        bx = beta * x
        if form == "one-sided":
            return 1 - np.exp(-bx)
        return np.where(bx >= 0, 1 - np.exp(-bx), -(1 - np.exp(bx)))

    out = {}
    for form in ["symmetric", "one-sided"]:
        rows = []
        for code, lab, x, beta in ATTR:
            A = attribute(beta, have[x].values, form)
            for k in CDR:
                d = (A * have[f"deaths_{k}"]).sum() / YEARS
                w = (A * have[f"wasting_{k}"]).sum() / YEARS
                for bk, b in BUDGET.items():
                    rows.append({"attribution": code, "attribution_label": lab, "beta": beta, "mortality": k,
                                 "budget": bk, "formula": form,
                                 "mean_share_attributed": float((A * have[f"deaths_central"]).sum() / have["deaths_central"].sum()),
                                 "deaths_per_year": d, "cost_per_death": b / d if d > 0 else np.nan,
                                 "crisis_person_years": (A * have.crisis_py).sum() / YEARS,
                                 "emergency_person_years": (A * have.emerg_py).sum() / YEARS,
                                 "child_wasting_years": w, "budget_usd": b})
        out[form] = pd.DataFrame(rows)
    out["one-sided"].to_csv(TAB / "benefit_cost_onesided.csv", index=False)
    R = out["symmetric"]
    R.to_csv(TAB / "benefit_cost.csv", index=False)
    pd.set_option("display.width", 250)
    show = R[R.budget == "central"].pivot_table(index="attribution", columns="mortality",
                                                 values=["deaths_per_year", "cost_per_death"]).round(0)
    print(show)
    print(R[(R.budget == "central") & (R.mortality == "central")][["attribution", "mean_share_attributed", "crisis_person_years",
                                                                  "emergency_person_years", "child_wasting_years"]].round(3))
    by_phase = have.groupby("p").agg(area_rounds=("fnid", "size"), people_m=("pop", lambda v: v.sum() / 1e6),
                                     deaths_central=("deaths_central", "sum")).assign(deaths_central=lambda d: d.deaths_central / YEARS)
    by_phase.to_csv(TAB / "benefit_cost_by_phase.csv")
    print(by_phase.round(1))
    # population context: average people living in flagged areas at any time
    avg_people = (have["pop"] * have.months / 12).sum() / YEARS
    key = {"flagged_area_rounds": int(len(fl)), "flagged_used": int(len(have)), "flagged_areas": int(have.fnid.nunique()),
           "avg_people_flagged": float(avg_people), "gross_deaths": gross, "gross_crisis_py": float(gross_py),
           "s3": {int(k): float(v) for k, v in s3.items()}, "s4": {int(k): float(v) for k, v in s4.items()},
           "share_phase": have.p.value_counts(normalize=True).sort_index().to_dict(),
           "betas": {a[0]: float(a[3]) for a in ATTR}}
    (TAB / "benefit_cost_key.json").write_text(json.dumps(key, indent=1, default=float))
    print(json.dumps(key, indent=1, default=float))
    figure(R)


def figure(R):
    """Cost per outcome averted, crediting FEWS NET only with its distinctive information."""
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    labs = {"A1": "All aid,\nbeyond data\n+ official", "A2": "All aid,\nbeyond\ndata", "A3": "Food aid,\nbeyond\ndata"}
    d = R[(R.budget == "central") & R.attribution.isin(list(labs))].copy()
    d["cost_emerg"] = d.budget_usd / d.emergency_person_years
    d["cost_crisis"] = d.budget_usd / d.crisis_person_years
    d["cost_wasting"] = d.budget_usd / d.child_wasting_years
    panels = [("cost_per_death", "A. Per death averted", [(3000, 5500, "GiveWell top charities\n(\\$3,000-5,500)")]),
              ("cost_emerg", "B. Per person-year kept out of\nEmergency or worse", []),
              ("cost_wasting", "C. Per child-year of acute\nmalnutrition averted", [])]
    fig, ax = plt.subplots(1, 3, figsize=(7.6, 3.5))
    for a, (col, title, bands) in zip(ax, panels):
        for i, at in enumerate(labs):
            s_ = d[d.attribution == at].set_index("mortality")[col]
            v = s_[s_ > 0]
            a.plot([i, i], [v.min(), v.max()], color="#1f4e79", lw=2.5, solid_capstyle="butt")
            a.scatter([i], [s_["central"]], color="#1f4e79", s=36, zorder=3)
            a.text(i + 0.12, s_["central"], f"\\${float(f'{s_.central:.2g}'):,.0f}", fontsize=7, va="center")
        for lo, hi, lab in bands:
            a.axhspan(lo, hi, color="#e6862e", alpha=0.25, lw=0)
            a.text(2.4, (lo * hi) ** 0.5, lab, fontsize=6.5, ha="right", va="center", color="#a0521a")
        a.set_yscale("log")
        from matplotlib.ticker import FuncFormatter, LogLocator
        a.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
        a.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
        a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"\\${v:,.0f}"))
        a.set_xticks(range(3), list(labs.values()), fontsize=7)
        a.set_xlim(-0.5, 2.6)
        a.set_title(title, fontsize=8.5, loc="left", fontweight="bold")
    ax[0].set_ylabel("FEWS NET budget per outcome averted\n(log scale; budget \\$64 million a year)")
    fig.tight_layout()
    fig.savefig(FIG / "fig7_benefit_cost.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig7_benefit_cost.png", dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    main()
