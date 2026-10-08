"""District x period panel of FEWS NET information and humanitarian aid (Somalia, Sudan).

Periods follow FEWS NET's map rounds: P(r) = the four months starting at round month r
(Feb-May, Jun-Sep, Oct-Jan; before 2016, quarterly rounds are mapped to the period that
contains them). For district d and period t:

  FEWS NET information published at the round that opens t (population-weighted over the
  FEWS NET units in d, using input/subnational_aid/tidy/fews_admin2_<iso3>.csv):
    cs3, cs4     share of population in units mapped Crisis+ / Emergency+ (current map)
    flag         share of population in units carrying the '!' aid flag
    fc3, fc4     share forecast Crisis+ / Emergency+ for period t (near-term projection)
    fc3_next     share forecast Crisis+ for period t+1 (medium-term projection)
    c_fc3, b_fc3 FEWS NET's distinctive forecast (beyond rainfall, conflict, prices, country,
                 season) and its predictable part (32/33_*.py), for the medium-term forecast
  Aid:
    cbpf_fs, cbpf_nut, cbpf_cash, cbpf_all   pooled-fund budget (US$) for projects starting in t,
                 split by district and cluster as in the CBPF location x cluster budget
    pres_fs, pres_nut                        3W partners present (food security, nutrition),
                 where available (62_tidy_3w.py)
  Districts are OCHA admin-2 P-codes (62_tidy_3w.py crosswalks FEWS NET units and source names).
  A second, annual panel (subnational_<iso3>_annual.parquet) adds people reached by food
  security and nutrition partners where the windows allow (Somalia 2022-24, Sudan 2019-22).
  Outcomes: next FEWS NET map (cs3_next, phase_next, flag_next); official IPC/CH Crisis+
  share for the district where available (input/panel/outcomes.parquet).

Output: input/panel/subnational_<iso3>.parquet
"""
import re
import sys
import unicodedata
import warnings
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "input"
SA = INP / "subnational_aid"
FUND = {"SOM": 21, "SDN": 15, "ETH": 53, "NGA": 75}
CC = {"SOM": "SO", "SDN": "SD", "ETH": "ET", "NGA": "NG"}
CLUST = {6: "fs", 9: "nut", 15: "cash"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"^(al|el|ad|as|ar|an)[ -]", "", s)
    return re.sub(r"[^a-z]", "", s)


def period_of(month):
    """Map a monthly Period to the FEWS NET period that contains it: label = its opening round month."""
    m, y = month.month, month.year
    if m == 1:
        return pd.Period(f"{y - 1}-10", "M")
    start = 2 if m < 6 else 6 if m < 10 else 10
    return pd.Period(f"{y}-{start:02d}", "M")


def crosswalk(iso):
    """FEWS NET unit -> district P-code (62_tidy_3w.py). Banadir's older single-district units carry the region code."""
    cw = pd.read_csv(SA / "tidy" / f"fews_admin2_{iso.lower()}.csv")
    cw["key"] = cw.admin2_pcode.fillna(cw.admin1_pcode)
    return cw.dropna(subset=["key"])[["fnid", "key", "admin1", "admin2"]]


def names(iso):
    """Raw (admin1, admin2) names in source files -> district P-code."""
    n = pd.read_csv(SA / "tidy" / f"admin2_names_{iso.lower()}.csv")
    n["key"] = n.admin2_pcode.fillna(n.admin1_pcode)
    n["raw"] = n.admin1_raw.map(norm) + "|" + n.admin2_raw.map(norm)
    return n.dropna(subset=["key"]).drop_duplicates("raw").set_index("raw").key


def unit_population(fnids):
    """WorldPop population for FEWS NET units (cached in fnid_population.parquet; 36_benefit_cost.py computes it).
    The helper rewrites the cache with exactly the units requested, so request the union."""
    f = INP / "panel/fnid_population.parquet"
    have = pd.read_parquet(f)
    need = set(fnids) - set(have.fnid)
    if need:
        import importlib.util
        spec = importlib.util.spec_from_file_location("bc", ROOT / "code" / "36_benefit_cost.py")
        bc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bc)
        bc.populations(sorted(set(have.fnid) | need))
        have = pd.read_parquet(f)
    return have.set_index("fnid")["pop"]


def fews_side(iso, cw):
    cc = CC[iso]
    pop = unit_population(cw.fnid)
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet")
    cs = cs[cs.country_code == cc]
    pr = pd.read_parquet(INP / "fewsnet/proj_monthly.parquet")
    pr = pr[pr.country_code == cc]
    # round months: months with a full current-situation map for the country
    n = cs.groupby("month").fnid.nunique()
    rounds = sorted(n[n >= 0.5 * n.max()].index)
    rows = []
    for r in rounds:
        t = period_of(r)
        c = cs[cs.month == r][["fnid", "phase", "assist_flag"]]
        near = pr[(pr.report_month == r) & pr.lead.between(0, 3)].groupby("fnid").phase.max().rename("fc")
        far = pr[(pr.report_month == r) & pr.lead.between(4, 7)].groupby("fnid").phase.max().rename("fcn")
        u = c.merge(near, on="fnid", how="left").merge(far, on="fnid", how="left").merge(cw[["fnid", "key"]], on="fnid")
        u["w"] = u.fnid.map(pop).fillna(0) + 1e-9
        u["cs3"], u["cs4"] = (u.phase >= 3) * u.w, (u.phase >= 4) * u.w
        u["flag"] = u.assist_flag.astype(float) * u.w
        u["fc3"], u["fc4"] = (u.fc >= 3) * u.w, (u.fc >= 4) * u.w
        u["fc3_next"] = (u.fcn >= 3) * u.w
        u["ph"] = u.phase * u.w
        g = u.groupby("key")[["cs3", "cs4", "flag", "fc3", "fc4", "fc3_next", "ph", "w"]].sum()
        for v in ["cs3", "cs4", "flag", "fc3", "fc4", "fc3_next", "ph"]:
            g[v] = g[v] / g.w
        g = g.rename(columns={"ph": "phase", "w": "pop"}).reset_index()
        g["t"], g["round"] = t, r
        rows.append(g)
    F = pd.concat(rows).drop_duplicates(["key", "t"], keep="last")
    # FEWS NET's distinctive forecast (medium-term, at the round)
    P = pd.read_parquet(INP / "panel/fewsnet_contribution_panel.parquet", columns=["fnid", "r", "country_code", "c_fc3", "b_fc3"])
    P = P[P.country_code == cc].merge(cw[["fnid", "key"]], on="fnid")
    P["r"] = pd.PeriodIndex(P.r.astype(str), freq="M")
    P["w"] = P.fnid.map(pop).fillna(0) + 1e-9
    P["t"] = P.r.map(period_of)
    for v in ["c_fc3", "b_fc3"]:
        P[v] = P[v] * P.w
    Pc = P.groupby(["key", "t"])[["c_fc3", "b_fc3", "w"]].sum()
    Pc["c_fc3"], Pc["b_fc3"] = Pc.c_fc3 / Pc.w, Pc.b_fc3 / Pc.w
    F = F.merge(Pc[["c_fc3", "b_fc3"]].reset_index(), on=["key", "t"], how="left")
    return F


def cbpf_side(iso, keys):
    a = pd.read_csv(SA / "cbpf/ProjectSummaryAggV2.csv", low_memory=False)
    a = a[a.PFId == FUND[iso]]
    p = pd.read_csv(SA / "cbpf/ProjectSummaryV2.csv", low_memory=False)[["PrjCode", "AStrDt", "AllYr", "AllSrc", "ApprDt"]]
    a = a.merge(p, on="PrjCode", how="left")
    a["start"] = pd.to_datetime(a.AStrDt, errors="coerce").fillna(pd.to_datetime(a.ApprDt, errors="coerce"))
    a = a.dropna(subset=["start", "AdmLoc2"])
    rows = []
    for r in a.itertuples():
        cl = str(r.ClstAgg).split("|||")
        bd = str(r.AdmLocClustBdg2).split("|||")
        if len(cl) != len(bd):
            continue
        for c, b in zip(cl, bd):
            try:
                rows.append((r.AdmLoc1, r.AdmLoc2, r.start, int(float(c)), float(b), r.PrjCode))
            except ValueError:
                continue
    x = pd.DataFrame(rows, columns=["adm1", "adm2", "start", "clust", "usd", "prj"])
    x["t"] = x.start.dt.to_period("M").map(period_of)
    x["sector"] = x.clust.map(CLUST).fillna("other")
    # raw names -> district P-codes via the harmonised names table
    x["key"] = (x.adm1.map(norm) + "|" + x.adm2.map(norm)).map(names(iso))
    matched = x.key.isin(keys)
    print(f"  CBPF {iso}: {matched.mean():.2f} of rows, {x.loc[matched, 'usd'].sum() / x.usd.sum():.2f} of US$ matched to FEWS NET districts")
    x = x[matched]
    g = x.pivot_table(index=["key", "t"], columns="sector", values="usd", aggfunc="sum", fill_value=0)
    g.columns = [f"cbpf_{c}" for c in g.columns]
    g["cbpf_all"] = g.sum(axis=1)
    env = x.groupby("t").usd.sum().rename("envelope")       # country fund allocations starting in t
    return g.reset_index(), env


def main(iso):
    cw = crosswalk(iso)
    F = fews_side(iso, cw)
    keys = set(F.key)
    C, env = cbpf_side(iso, keys)
    D = F.merge(C, on=["key", "t"], how="left")
    for c in [c for c in D if c.startswith("cbpf_")]:
        D[c] = D[c].fillna(0.0)
    D = D.merge(env.reset_index(), on="t", how="left")
    D["envelope"] = D.envelope.fillna(0.0)
    # 3W presence and reach, if built
    D = attach_3w(D, pd.read_parquet(SA / "tidy" / f"presence_{iso.lower()}.parquet"), "presence")
    D = D.sort_values(["key", "t"])
    g = D.groupby("key")
    for v in ["cs3", "phase", "flag"]:
        D[f"{v}_next"] = g[v].shift(-1)
    D["iso3"], D["adm1"] = iso, D.key.str.split("|").str[0]
    annual(iso, D, cw)
    D["t"] = D.t.astype(str)
    D.to_parquet(INP / f"panel/subnational_{iso}.parquet", index=False)
    print(iso, D.shape, "districts", D.key.nunique(), "periods", D.t.nunique(),
          "with CBPF>0", round((D.cbpf_all > 0).mean(), 3))


def attach_3w(D, T, kind):
    """3W presence: partners per district, food security and nutrition, max over windows of at most
    four months assigned to the FEWS NET period containing their midpoint."""
    T = T[T.period_months <= 4].copy()
    T["key"] = T.admin2_pcode.fillna(T.admin1_pcode)
    mid = T.period_start + (T.period_end - T.period_start) / 2
    T["t"] = [period_of(m) for m in mid.dt.to_period("M")]
    T = T[T.cluster.isin(["food_security", "nutrition"])]
    g = T.pivot_table(index=["key", "t"], columns="cluster", values="n_partners", aggfunc="max")
    g = g.rename(columns={"food_security": "pres_fs", "nutrition": "pres_nut"})
    obs = T.groupby("t").key.nunique()
    g = g.reset_index()
    # periods with a 3W file: districts without a row had no food security or nutrition partner
    D = D.merge(g, on=["key", "t"], how="left")
    have = D.t.isin(obs.index)
    for c in ["pres_fs", "pres_nut"]:
        if c not in D:
            D[c] = np.nan
        D.loc[have, c] = D.loc[have, c].fillna(0.0)
    return D


def annual(iso, D, cw):
    """District x year: FEWS NET flags and phases (mean over rounds) and people reached (food security,
    nutrition), from the series with clean windows."""
    R = pd.read_parquet(SA / "tidy" / f"reach_{iso.lower()}.parquet")
    R = R[R.measure == "reached"].copy()
    R["key"] = R.admin2_pcode.fillna(R.admin1_pcode)
    R["year"] = R.period_end.dt.year
    if iso == "SOM":
        # monthly flows: Cash Working Group (districts 2022-23) and 3W individuals reached (2024)
        R = R[((R.series == "som_cwg") & (R.admin_level == 2)) | ((R.series == "som_3w") & ~R.cumulative & (R.year == 2024))]
        R = R.groupby(["key", "year", "cluster"]).value.sum()
    else:
        # cumulative windows within a year: take each locality's latest window
        R = R[(R.series == "sdn_hrp") & (R.admin_level == 2) & R.cumulative]
        R = R.sort_values("period_end").groupby(["key", "year", "cluster"]).value.last()
    R = R.unstack("cluster").reindex(columns=["food_security", "nutrition"]).fillna(0.0)
    R.columns = ["reach_fs", "reach_nut"]
    R = R.reset_index()
    A = D.assign(year=pd.PeriodIndex(D.t.astype(str), freq="M").year).groupby(["key", "year"]).agg(
        flag=("flag", "mean"), cs3=("cs3", "mean"), phase=("phase", "mean"), fc3=("fc3", "mean"),
        pop=("pop", "max"), pres_fs=("pres_fs", "mean") if "pres_fs" in D else ("flag", "size")).reset_index()
    years = set(R.year)
    A = A[A.year.isin(years)].merge(R, on=["key", "year"], how="left")
    A[["reach_fs", "reach_nut"]] = A[["reach_fs", "reach_nut"]].fillna(0.0)
    A["iso3"] = iso
    A.to_parquet(INP / f"panel/subnational_{iso}_annual.parquet", index=False)
    print(iso, "annual", A.shape, "years", sorted(years), "with reach", round((A.reach_fs + A.reach_nut > 0).mean(), 3))


if __name__ == "__main__":
    for iso in (sys.argv[1:] or ["SOM", "SDN"]):
        main(iso)
