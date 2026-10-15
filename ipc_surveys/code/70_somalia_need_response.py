"""Somalia, 2024-2026: how big was the response, and how much suffering, for a given level of need,
before and after the 2025 US aid withdrawal?

Need (district unless noted)
  p3        people in IPC Phase 3+ (official IPC acute food insecurity, area classifications summed
            to districts; rounds Feb/Aug 2018-2025 and Jan 2026)
  pin       people in need from the humanitarian needs overview (HNO 2024; JIAF 2025, 2026)
  pred_gam  wasting predicted from rainfall, conflict and prices (survey domains; model fitted on
            pre-2025 years other than the one predicted, as in 69)
Response
  FTS humanitarian funding (national, by year; US vs other donors)
  cash      cash and voucher transfers by district from the Cash Working Group 4W (2024: Jan-Dec,
            2025: Jan-Jun; district tables are period totals, so districts are compared as shares
            of the national total; national figures use the monthly tables, Jan-Jun both years).
            Social safety nets (Baxnaano) are excluded.
  partners  organisation x sector units reporting in nutrition, health, food security and WASH,
            Apr-Jun 2024, 2025 and 2026 (OCHA 3W)
  reach     people reached per month in those sectors: 3W Jan-Sep 2024 vs HNRP monitoring Jan-Mar
            2026 (different systems: districts compared as shares of the national total)
Suffering
  FSNAU survey outcomes by domain-season (GAM, SAM, MUAC GAM, CDR, U5DR), and IPC Phase 3+ itself.

Outputs: output/tables/som_need_*.csv, som_need_key.json, output/figures/som_need_*.pdf,
         output/us_cut_memo/numbers_need.tex
"""
import importlib.util
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

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
AID = INP / "subnational_aid"
RESP = AID / "hdx_response" / "som"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M68 = load("m68", "68_somalia_us_cut.py")
M69 = load("m69", "69_somalia_aid_dependence.py")
dist_key, SECTORS = M68.dist_key, M68.SECTORS
KEY = {}
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"
YCOL = {2024: BLUE, 2025: ORANGE, 2026: GREEN}


# ------------------------------------------------------------------ names -> P-codes
def nrm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


NAMES = pd.read_csv(AID / "tidy" / "admin2_names_som.csv").dropna(subset=["admin2_pcode"])
N2P = {}
for a, b, c in zip(NAMES.admin2_raw, NAMES.admin2, NAMES.admin2_pcode):
    for k in (a, b):
        if isinstance(k, str):
            N2P.setdefault(nrm(k), dist_key(c))
N2P.update({nrm(k): v for k, v in {
    "Banadir": "SO22", "Mogadishu": "SO22", "Hargeisa": "SO1201", "Burao": "SO1301", "Bosaso": "SO1601",
    "Garowe": "SO1701", "Galkacyo": "SO1801", "Galkayo": "SO1801", "Dhusamareb": "SO1901", "Beletweyne": "SO2001",
    "Belet Weyne": "SO2001", "Baidoa": "SO2401", "Kismayo": "SO2801", "Afgoye": "SO2302", "Marka": "SO2301",
    "Merka": "SO2301", "Bulo Burto": "SO2002", "Bulo Burti": "SO2002", "Laasqoray": "SO1503", "Lasqoray": "SO1503",
    "Badhan": "SO1503", "Ceel Afweyn": "SO1502", "Erigabo": "SO1501", "Las Anod": "SO1401", "Owdweyne": "SO1303",
    "Odweyne": "SO1303", "Qansax Dheere": "SO2404", "Qansaxdheere": "SO2404", "Rab Dhuure": "SO2505",
    "Rabdhure": "SO2505", "Tayeeglow": "SO2503", "Tiyeeglow": "SO2503", "Waajid": "SO2504", "Wajid": "SO2504",
    "Xudur": "SO2501", "Hudur": "SO2501", "Garbahaarey": "SO2601", "Garbaharey": "SO2601", "Baardheere": "SO2602",
    "Bardhere": "SO2602", "Belet Xaawo": "SO2603", "Beled Hawo": "SO2603", "Doolow": "SO2605", "Dolow": "SO2605",
    "Bu'aale": "SO2701", "Buaale": "SO2701", "Saakow": "SO2703", "Sakow": "SO2703", "Kismaayo": "SO2801",
    "Afmadow": "SO2802", "Badhaadhe": "SO2803", "Jamaame": "SO2804", "Jamame": "SO2804", "Sablaale": "SO2306",
    "Kurtunwaarey": "SO2304", "Wanla Weyn": "SO2307", "Wanlaweyn": "SO2307", "Qoryooley": "SO2305",
    "Baraawe": "SO2303", "Brava": "SO2303", "Balcad": "SO2103", "Balad": "SO2103", "Cadale": "SO2104",
    "Adan Yabaal": "SO2102", "Jalalaqsi": "SO2003", "Cabudwaaq": "SO1902", "Cadaado": "SO1903",
    "Ceel Buur": "SO1904", "Ceel Dheer": "SO1905", "Galdogob": "SO1802", "Hobyo": "SO1803", "Jariiban": "SO1804",
    "Xarardheere": "SO1805", "Harardhere": "SO1805", "Burtinle": "SO1702", "Eyl": "SO1703", "Bandarbeyla": "SO1602",
    "Caluula": "SO1603", "Iskushuban": "SO1604", "Qandala": "SO1605", "Qardho": "SO1606", "Caynabo": "SO1402",
    "Taleex": "SO1403", "Xudun": "SO1404", "Buuhoodle": "SO1302", "Sheikh": "SO1304", "Gebiley": "SO1203",
    "Berbera": "SO1202", "Zeylac": "SO1104", "Lughaye": "SO1103", "Baki": "SO1102", "Borama": "SO1101",
    "Diinsoor": "SO2403", "Dinsor": "SO2403", "Buur Hakaba": "SO2402", "Burhakaba": "SO2402", "Baydhaba": "SO2401",
    "Ceel Barde": "SO2502", "Ceel Waaq": "SO2604", "Luuq": "SO2606", "Jilib": "SO2702", "Jowhar": "SO2101",
    "Dhuusamarreeb": "SO1901", "Gaalkacyo": "SO1801", "Garoowe": "SO1701", "Bossaso": "SO1601", "Burco": "SO1301",
    "Hargeysa": "SO1201", "Laas Caanood": "SO1401", "Ceerigaabo": "SO1501", "Belet Weyne ": "SO2001",
    "Baydoa": "SO2401", "Beletweyn": "SO2001", "Buhoodle": "SO1302", "Laas Canod": "SO1401", "Laas Canood": "SO1401",
    "Dhobley": "SO2802", "Banadir Peri-Urban": "SO22", "Banadir peri": "SO22",
}.items()})


def to_pcode(name):
    if not isinstance(name, str):
        return None
    base = re.sub(r"\s*\(\d+\)\s*$", "", name)
    base = re.sub(r"(?i)[\s-]+(idps?|urban|rural|town|peri-urban|peri).*$", "", base).strip()
    return N2P.get(nrm(base)) or N2P.get(nrm(name))


# ------------------------------------------------------------------ need
def ipc_rounds():
    o = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    s = o[(o.iso3 == "SOM") & (o.source == "IPC")].copy()
    s["dist"] = s.area_name.map(to_pcode)
    KEY["ipc_area_match"] = float(s.dist.notna().mean())
    KEY["ipc_unmatched"] = sorted(set(s[s.dist.isna()].area_name))[:20]
    s = s.dropna(subset=["dist", "population"])
    s["p3"], s["p4"] = s.share3 * s.population, s.share4 * s.population
    R = s.groupby(["month", "dist"])[["population", "p3", "p4"]].sum().reset_index()
    R["share3"] = R.p3 / R.population
    R["month"] = R.month.astype(str)
    return R


def pin_by_district():
    out = []
    # 2024: HNRP planning figures (district 'Overall PiN')
    h = pd.read_excel(RESP / "somalia-humanitarian-needs" / "hnrp_key-figures-2024.xlsx", header=None)
    hr = next(i for i in range(6) if (h.iloc[i] == "Overall PiN").any())
    h.columns = [str(c).strip() for c in h.iloc[hr]]
    h = h.iloc[hr + 1:]
    h = h[h.PCODE.astype(str).str.startswith("SO")]
    h["dist"], h["pin"] = h.PCODE.astype(str).map(dist_key), pd.to_numeric(h["Overall PiN"], errors="coerce")
    out.append(h.groupby("dist").pin.sum().to_frame().assign(year=2024))
    for y, sh in [(2025, "PiN"), (2026, "Pin")]:
        v = pd.read_excel(RESP / "som-jiaf-humanitarian-needs-pin-and-severity" / f"jiaf_somalia_{y}.xlsx",
                          sheet_name=sh, header=None)
        hdr = next(i for i in range(6) if v.iloc[i].astype(str).str.contains("P-Code|Pcode|P-code", case=False).any())
        cols = [re.sub(r"\s+", " ", str(c)).strip().lower() for c in v.iloc[hdr]]
        v = v.iloc[hdr + 1:].copy()
        v.columns = cols
        pc = next(c for c in cols if ("p-code" in c or "pcode" in c) and "2" in c)
        fin = [c for c in cols if "final pin" in c or c == "final"]
        fin = fin[-1] if fin else [c for c in cols if "pin" in c][-1]
        v = v[v[pc].astype(str).str.startswith("SO")]
        v["dist"] = v[pc].astype(str).map(dist_key)
        v["pin"] = pd.to_numeric(v[fin], errors="coerce")
        out.append(v.groupby("dist").pin.sum().to_frame().assign(year=y))
    P = pd.concat(out).reset_index()
    KEY["pin_national"] = P.groupby("year").pin.sum().round(-3).to_dict()
    return P


# ------------------------------------------------------------------ response
def cash():
    rows, nat = [], {}
    for y in [2024, 2025]:
        v = pd.read_excel(RESP / "cwg_4w" / f"cwg_4w_{y}.xlsx", sheet_name="All CVA Tracker", header=None)
        # national monthly people reached (top-left table)
        r0 = next(i for i in range(10) if (v.iloc[i, :10] == "Row Labels").any())
        c0 = list(v.iloc[r0, :10]).index("Row Labels")
        mon = v.iloc[r0, c0 + 1:c0 + 14]
        t = v.iloc[r0 + 1:r0 + 20, c0:c0 + 14]
        t.columns = ["cluster"] + list(mon.astype(str))
        t = t.loc[:, ~t.columns.duplicated()]
        t = t[[c for c in t.columns if c == "cluster" or c != "nan"]]
        t = t[t.cluster.notna()]
        h1 = [m for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun"] if m in t.columns]
        tt = t[~t.cluster.astype(str).str.contains("Overall|Grand Total|Safety", case=False)]
        nat[y] = {"reached_h1_monthly": float(tt[h1].apply(pd.to_numeric, errors="coerce").sum().mean()),
                  "fs_reached_h1_monthly": float(pd.to_numeric(tt[tt.cluster.str.contains("Food", case=False)][h1].iloc[0],
                                                               errors="coerce").mean()),
                  "months": len([m for m in t.columns[1:] if pd.to_numeric(t[m], errors="coerce").sum() > 0])}
        # district blocks: transfers and people reached, by organisation, region and district
        for lab, measure in [("CVA - Monthly Transfer by organization, region and district", "usd"),
                             ("CVA - Monthly people reached by organization, region and district", "reached")]:
            c = [j for j in range(v.shape[1]) if str(v.iloc[0, j]).strip() == lab][0]
            hr = next(i for i in range(10) if str(v.iloc[i, c]) == "Row Labels")
            b = v.iloc[hr + 1:, c:c + 5].copy()
            b.columns = ["region", "district", "org", "cluster", "value"]
            b = b[b.region.notna() & ~b.region.astype(str).str.contains("Grand Total")]
            b = b[~b.cluster.astype(str).str.contains("Safety", case=False)]
            b["value"] = pd.to_numeric(b.value, errors="coerce")
            b["dist"] = b.district.map(to_pcode)
            b["year"], b["measure"] = y, measure
            rows.append(b)
    C = pd.concat(rows)
    KEY["cash_match"] = float(C.dist.notna().mean())
    KEY["cash_unmatched"] = sorted(set(C[C.dist.isna()].district.astype(str)))[:15]
    KEY["cash_national"] = nat
    KEY["cash_totals"] = C.groupby(["year", "measure"]).value.sum().round(-3).unstack().to_dict()
    D = C.dropna(subset=["dist"]).groupby(["year", "measure", "dist"]).value.sum().unstack("measure").reset_index()
    return D, nat


def partners():
    o = pd.read_parquet(AID / "tidy" / "org_presence_som.parquet")
    o = o[(o.period_type == "month") & o.cluster.isin(SECTORS) & o.period_start.dt.month.between(4, 6) &
          o.period_start.dt.year.isin([2024, 2025, 2026])].copy()
    o["dist"], o["year"] = o.admin2_pcode.map(dist_key), o.period_start.dt.year
    m = o.groupby(["year", "dist", "period_start"]).apply(lambda s: s[["org", "cluster"]].drop_duplicates().shape[0])
    return m.groupby(["year", "dist"]).mean().rename("partners").reset_index()


def reach():
    r = pd.read_parquet(AID / "tidy" / "reach_som.parquet")
    r = r[(r.measure == "reached") & ~r.cumulative & (r.period_type == "month") & r.cluster.isin(SECTORS)]
    r = r[((r.series == "som_3w") & (r.period_start.dt.year == 2024)) | (r.series == "som_hnrp2026")].copy()
    r["dist"], r["year"] = r.admin2_pcode.map(dist_key), r.period_start.dt.year
    months = r.groupby("year").period_start.nunique()
    out = r.groupby(["year", "dist"]).value.sum().rename("reach").reset_index()
    out["reach"] = out.reach / out.year.map(months)
    return out


def fts_national():
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet")
    f = f[f.dest_country.fillna("").str.contains("Somalia") & f.status.isin(["paid", "commitment"]) &
          ((f.boundary == "incoming") | f.boundary.isna()) & (f.amount_usd > 0)].copy()
    f["year"] = pd.to_datetime(f.decision_date, errors="coerce").dt.year
    f["us"] = f.donor.fillna("").str.startswith("United States")
    t = f[f.year.between(2017, 2026)].groupby(["year", "us"]).amount_usd.sum().unstack().fillna(0) / 1e6
    t.columns = ["other", "us"]
    t["total"] = t.other + t.us
    return t


# ------------------------------------------------------------------ analysis
def targeting(panel, resp, need, years):
    """Districts: log response share on log need share, by year. Returns slope and the ratio
    of response per person in need, top need tercile vs bottom (by need per capita)."""
    out = []
    for y in years:
        d = panel[(panel.year == y)].dropna(subset=[resp, need, "pop"])
        d = d[(d[need] > 0)]
        rs = d[resp] / d[resp].sum()
        ns = d[need] / d[need].sum()
        ok = rs > 0
        b = np.polyfit(np.log(ns[ok]), np.log(rs[ok]), 1)[0] if ok.sum() > 5 else np.nan
        intensity = d[need] / d["pop"]
        terc = pd.qcut(intensity.rank(method="first"), 3, labels=["low", "mid", "high"])
        per = (d[resp].groupby(terc).sum() / d[need].groupby(terc).sum())
        rel = per / (d[resp].sum() / d[need].sum())
        out.append(dict(response=resp, need=need, year=y, districts=len(d), zero_share=float((~ok).mean()),
                        elasticity=b, rel_low=rel["low"], rel_mid=rel["mid"], rel_high=rel["high"],
                        per_need_low=per["low"], per_need_mid=per["mid"], per_need_high=per["high"]))
    return out


def suffering(p, need):
    """Survey outcome on need, before (2019-2024) and after (2025): slope and level change."""
    rows = []
    for y in ["gam", "sam", "muac_gam", "cdr", "u5dr"]:
        d = p[p.year >= 2019].dropna(subset=[y, need]).copy()
        X = pd.DataFrame({"const": 1.0, "need": d[need], "post": d.post, "need_post": d[need] * d.post}, index=d.index)
        X = X.join(pd.get_dummies(d.season_type, prefix="s", drop_first=True, dtype=float))
        X = X.join(pd.get_dummies(d.ptype, prefix="t", drop_first=True, dtype=float))
        b, se, _ = M68.ols_cl(X, d[y].values, d.region.values)
        cols = list(X.columns)
        g = lambda c: (b[cols.index(c)], se[cols.index(c)])
        rows.append(dict(outcome=y, need=need, n=len(d), post_n=int(d.post.sum()),
                         slope_pre=g("need")[0], slope_pre_se=g("need")[1],
                         slope_change=g("need_post")[0], slope_change_se=g("need_post")[1],
                         level_post=g("post")[0], level_post_se=g("post")[1],
                         p_slope_change=M68.wild_p(X, d[y].values, d.region.values, "need_post")))
    return rows


def slope_by_year(p):
    """Within each year: outcome on Phase 3+ share (prior IPC round), controlling for population type
    and season. All surveys, and Gu surveys only (matched to the February round, which precedes them
    and does not use them)."""
    rows = []
    for lab, sub in [("all", p), ("gu", p[p.season_type == "Gu"])]:
        for y in range(2018, 2027):
            for out in ["gam", "sam", "cdr"]:
                d = sub[sub.year == y].dropna(subset=["need_p3", out])
                if len(d) < 15:
                    continue
                X = pd.DataFrame({"const": 1.0, "need": d.need_p3}, index=d.index)
                X = X.join(pd.get_dummies(d.ptype, prefix="t", drop_first=True, dtype=float))
                if d.season_type.nunique() > 1:
                    X = X.join(pd.get_dummies(d.season_type, prefix="s", drop_first=True, dtype=float))
                b, se, _ = M68.ols_cl(X, d[out].values, d.region.values)
                rows.append(dict(sample=lab, year=y, outcome=out, n=len(d), b10=b[1] / 10, se10=se[1] / 10,
                                 mean_p3=d.need_p3.mean()))
    return pd.DataFrame(rows)


def main():
    pop = M69.district_pop()
    ipc = ipc_rounds()
    pin = pin_by_district()
    C, cash_nat = cash()
    Pt, Re = partners(), reach()
    fts = fts_national()

    # ---- national scale of need and response
    nat_ipc = ipc.groupby("month")[["p3", "p4", "population"]].sum()
    nat_ipc["year"] = nat_ipc.index.str[:4].astype(int)
    p3y = nat_ipc.groupby("year").p3.mean() / 1e6
    N = fts.join(p3y.rename("p3_m"), how="outer")
    N["pin_m"] = pd.Series(KEY["pin_national"]) / 1e6
    N["usd_per_p3"] = N.total / N.p3_m
    N["usd_per_pin"] = N.total / N.pin_m
    N.to_csv(TAB / "som_need_national.csv")
    KEY["national"] = N.round(2).reset_index().to_dict("records")
    cash_pc = {y: cash_nat[y]["reached_h1_monthly"] for y in cash_nat}
    KEY["cash_reached_change_h1"] = cash_pc[2025] / cash_pc[2024] - 1

    # ---- district panel by year
    rnd = {2024: "2024-02", 2025: "2025-02", 2026: "2026-01"}       # latest IPC round before each response window
    rows = []
    for y, m in rnd.items():
        d = ipc[ipc.month == m].set_index("dist")[["p3", "p4", "share3"]]
        d = d.join(pop.rename("pop"), how="outer")
        d["pin"] = pin[pin.year == y].set_index("dist").pin
        d["cash_usd"] = C[C.year == y].set_index("dist").usd if y in (2024, 2025) else np.nan
        d["cash_reached"] = C[C.year == y].set_index("dist").reached if y in (2024, 2025) else np.nan
        d["partners"] = Pt[Pt.year == y].set_index("dist").partners
        d["reach"] = Re[Re.year == y].set_index("dist").reach if y in (2024, 2026) else np.nan
        for c in ["cash_usd", "cash_reached", "partners", "reach"]:
            if d[c].notna().any():
                d[c] = d[c].fillna(0)
        rows.append(d.assign(year=y).reset_index().rename(columns={"index": "dist"}))
    DP = pd.concat(rows)
    DP = DP[DP.dist.notna() & (DP["pop"] > 0)]
    DP.to_csv(TAB / "som_need_district_panel.csv", index=False)
    KEY["districts"] = int(DP.dist.nunique())

    T = []
    for resp, yrs in [("cash_usd", [2024, 2025]), ("cash_reached", [2024, 2025]), ("partners", [2024, 2025, 2026]),
                      ("reach", [2024, 2026])]:
        for need in ["p3", "pin"]:
            T += targeting(DP, resp, need, yrs)
    T = pd.DataFrame(T)
    T.to_csv(TAB / "som_need_targeting.csv", index=False)

    # absolute cash per person in Phase 3+, Jan-Jun, by need tercile (2024 district totals scaled to Jan-Jun)
    h1_scale = {2024: cash_nat[2024]["reached_h1_monthly"] * 6 / C[(C.year == 2024)].reached.sum(), 2025: 1.0}
    KEY["cash_h1_scale_2024"] = h1_scale[2024]

    # ---- change in response by district (actual exposure) and its correlates
    w = DP.pivot_table(index="dist", columns="year", values=["cash_usd", "partners", "reach", "p3", "pin", "pop"])
    E = pd.DataFrame(index=w.index)
    sh = lambda c, y: w[(c, y)] / w[(c, y)].sum()
    E["cash_loss"] = -(np.log(sh("cash_usd", 2025) + 1e-4) - np.log(sh("cash_usd", 2024) + 1e-4))
    E["partner_loss_q2"] = 1 - w[("partners", 2025)] / w[("partners", 2024)]
    E["reach_loss_26"] = -(np.log(sh("reach", 2026) + 1e-4) - np.log(sh("reach", 2024) + 1e-4))
    E["need24"] = w[("p3", 2024)] / w[("pop", 2024)]
    E["need_change"] = w[("p3", 2025)] / w[("pop", 2025)] - E.need24
    E = E.replace([np.inf, -np.inf], np.nan)
    dep = pd.read_csv(TAB / "som_aiddep_districts.csv", index_col=0)[["index"]]
    us = pd.read_csv(TAB / "som_uscut_districts.csv", index_col=0)[["E_pred", "E_loss"]]
    E = E.join(dep).join(us)
    E.to_csv(TAB / "som_need_district_change.csv")
    KEY["change_corr"] = E.corr().round(2).to_dict()
    KEY["cash_loss_vs_need24"] = float(E.cash_loss.corr(E.need24))

    # ---- survey domains: need measures and actual-response exposures
    p = pd.read_parquet(INP / "panel" / "som_aiddep_panel.parquet")
    q = M68.survey_panel()
    p = p.merge(q[["domain", "season_id", "dists"]], on=["domain", "season_id"], how="left")
    # need: share of population in Phase 3+ in the domain's districts at the latest IPC round
    # before fieldwork (Feb round for Gu surveys, Aug round of the same year for Deyr surveys)
    ipc_m = ipc.copy()
    ipc_m["t"] = pd.PeriodIndex(ipc_m.month, freq="M")
    rounds = sorted(ipc_m.t.unique())
    vals = []
    for r in p.itertuples():
        prior = [t for t in rounds if t <= r.month - 1]
        if not prior:
            vals.append(np.nan)
            continue
        t = prior[-1]
        if (r.month - t).n > 9:
            vals.append(np.nan)
            continue
        x = ipc_m[ipc_m.t == t].set_index("dist")
        wts = {k: v for k, v in json.loads(r.dists).items() if k not in (None, "null") and k in x.index}
        if not wts:
            vals.append(np.nan)
            continue
        pp = sum(x.loc[k, "p3"] * v for k, v in wts.items())
        po = sum(x.loc[k, "population"] * v for k, v in wts.items())
        vals.append(pp / po if po else np.nan)
    p["need_p3"] = vals
    KEY["need_p3_coverage"] = float(p.need_p3.notna().mean())
    # need: wasting predicted from rainfall, conflict and prices (leave-one-year-out, pre-2025 fits)
    _, _, err = M69.prediction_gaps(p, "gam")
    err = err.merge(p[["domain", "season_id", "gam"]], on=["domain", "season_id"])
    err["pred_gam"] = err.gam - err.err
    p = p.merge(err[["domain", "season_id", "pred_gam"]], on=["domain", "season_id"], how="left")
    SY = slope_by_year(p)
    SY.to_csv(TAB / "som_need_slope_year.csv", index=False)
    KEY["slope_year"] = SY.round(3).to_dict("records")
    S = pd.DataFrame(suffering(p, "need_p3") + suffering(p, "pred_gam"))
    S.to_csv(TAB / "som_need_suffering.csv", index=False)

    # actual-response exposures at domain level
    ex = []
    for r in p.drop_duplicates("domain").itertuples():
        wts = pd.Series({k: v for k, v in json.loads(r.dists).items() if k not in (None, "null")})
        rec = {"domain": r.domain}
        for c in ["cash_loss", "partner_loss_q2", "reach_loss_26"]:
            v = E[c].reindex(wts.index)
            ok = v.notna()
            rec[c] = float((v[ok] * wts[ok]).sum() / wts[ok].sum()) if ok.any() else np.nan
        ex.append(rec)
    ex = pd.DataFrame(ex)
    for c in ["cash_loss", "partner_loss_q2", "reach_loss_26"]:
        ex["z_" + c] = (ex[c] - ex[c].mean()) / ex[c].std()
    p = p.merge(ex, on="domain")
    D = []
    for exp in ["z_cash_loss", "z_partner_loss_q2", "z_reach_loss_26"]:
        for y in ["gam", "sam", "muac_gam", "cdr", "u5dr"]:
            D.append(dict(exposure=exp, outcome=y, **M69.did(p, exp, y, typed=False)))
    D = pd.DataFrame(D)
    D.to_csv(TAB / "som_need_did_actual.csv", index=False)
    G = {}
    for exp in ["z_cash_loss", "z_partner_loss_q2"]:
        for y in ["gam", "cdr"]:
            S_, k, _ = M69.prediction_gaps(p, y, exp=exp)
            G[f"{exp}|{y}"] = k
    KEY["gaps_actual"] = G
    p.drop(columns=["dists"]).to_parquet(INP / "panel" / "som_need_panel.parquet", index=False)

    figures(N, T, DP, p, h1_scale, SY)
    (TAB / "som_need_key.json").write_text(json.dumps(KEY, indent=1, default=float))
    write_numbers(N, T, S, D, G, cash_nat, E)
    pd.set_option("display.width", 230, "display.max_rows", 200, "display.max_columns", 30)
    print(json.dumps({k: v for k, v in KEY.items() if k not in ("national", "change_corr")}, indent=1, default=float))
    print(N.round(2).to_string())
    print(T.round(2).to_string())
    print(S.round(3).to_string())
    print(D.round(3).to_string())
    print(E.corr().round(2).to_string())


def figures(N, T, DP, p, h1_scale, SY):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    # 1. national: funding and need
    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))
    n = N.loc[2018:2025]
    ax[0].bar(n.index, n.us, color=ORANGE, label="US", width=0.7)
    ax[0].bar(n.index, n.other, bottom=n.us, color=BLUE, label="Other donors", width=0.7)
    ax[0].set_title("Humanitarian funding to Somalia ($M)", fontsize=9.5)
    ax[0].legend(frameon=False, fontsize=8.5)
    ax[1].plot(n.index, n.usd_per_p3, color=GREY, marker="o", ms=4)
    ax[1].set_title("Funding per person in IPC Phase 3+ ($)", fontsize=9.5)
    for a in ax:
        a.set_xticks(range(2018, 2026, 2))
    fig.tight_layout()
    fig.savefig(FIG / "som_need_national.pdf")
    plt.close(fig)
    # 2. response relative to need, by need tercile
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.0), sharey=True)
    for ax, (resp, lab) in zip(axes, [("cash_usd", "Cash transfers"), ("partners", "Partners present"),
                                      ("reach", "People reached")]):
        t = T[(T.response == resp) & (T.need == "p3")]
        x = np.arange(3)
        wdt = 0.8 / len(t)
        for i, r in enumerate(t.itertuples()):
            ax.bar(x + (i - (len(t) - 1) / 2) * wdt, [r.rel_low, r.rel_mid, r.rel_high], width=wdt,
                   color=YCOL[r.year], label=str(r.year))
        ax.axhline(1, color=GREY, lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(["Low", "Mid", "High"])
        ax.set_title(lab, fontsize=9.5)
        ax.set_xlabel("Need (Phase 3+ share)", fontsize=8.5)
        ax.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("Response per person in need\n(relative to national)")
    fig.tight_layout()
    fig.savefig(FIG / "som_need_targeting.pdf")
    plt.close(fig)
    # 3. suffering conditional on need: GAM vs Phase 3+ share and vs predicted GAM, pre vs post
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    for ax, (need, lab) in zip(axes, [("need_p3", "Share in IPC Phase 3+ (prior round)"),
                                      ("pred_gam", "Wasting predicted from rain, conflict, prices")]):
        d = p[p.year >= 2019].dropna(subset=[need, "gam"])
        bins = np.unique(np.quantile(d[need], np.linspace(0, 1, 7)))
        for post, col, lb in [(0, BLUE, "2019-2024"), (1, ORANGE, "2025")]:
            s = d[d.post == post]
            g = s.groupby(pd.cut(s[need], bins, include_lowest=True))
            ax.plot(g[need].mean(), g.gam.mean(), color=col, marker="o", ms=4, label=lb)
        ax.set_xlabel(lab, fontsize=8.5)
        ax.legend(frameon=False, fontsize=8.5)
    axes[0].set_ylabel("Measured wasting (GAM, %)")
    fig.tight_layout()
    fig.savefig(FIG / "som_need_suffering.pdf")
    plt.close(fig)
    # 4. year-by-year slope of wasting on Phase 3+ share
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    for lab, col, off, nm in [("all", BLUE, -0.1, "All surveys"), ("gu", ORANGE, 0.1, "Gu surveys only")]:
        s = SY[(SY["sample"] == lab) & (SY.outcome == "gam")]
        ax.errorbar(s.year + off, s.b10, yerr=1.96 * s.se10, fmt="o", color=col, ms=4, lw=1.2, label=nm)
    ax.axhline(0, color=GREY, lw=0.8)
    ax.axvline(2024.5, color=GREY, ls=":", lw=0.8)
    ax.set_ylabel("Wasting points per 10pp\nmore people in Phase 3+")
    ax.legend(frameon=False, fontsize=8.5)
    ax.set_xticks(range(2018, 2027))
    fig.tight_layout()
    fig.savefig(FIG / "som_need_slope_year.pdf")
    plt.close(fig)


def write_numbers(N, T, S, D, G, cash_nat, E):
    M = {}
    f0 = lambda x: f"{x:,.0f}"
    f1 = lambda x: f"{x:.1f}"
    f2 = lambda x: f"{x:.2f}"
    pc = lambda x: f"{100 * x:.0f}"
    for y in [2022, 2023, 2024, 2025]:
        r = N.loc[y]
        tag = {2022: "Ttwo", 2023: "Tthree", 2024: "Tfour", 2025: "Tfive"}[y]
        M[f"Fund{tag}"], M[f"PthreeM{tag}"], M[f"PerP{tag}"] = f0(r.total), f1(r.p3_m), f0(r.usd_per_p3)
        if not np.isnan(r.pin_m):
            M[f"PinM{tag}"], M[f"PerPin{tag}"] = f1(r.pin_m), f0(r.usd_per_pin)
    M["PinMTsix"] = f1(N.loc[2026, "pin_m"]) if 2026 in N.index else "--"
    M["FundDrop"] = pc(1 - N.loc[2025, "total"] / N.loc[2024, "total"])
    M["PthreeChange"] = pc(N.loc[2025, "p3_m"] / N.loc[2024, "p3_m"] - 1)
    M["PerPDrop"] = pc(1 - N.loc[2025, "usd_per_p3"] / N.loc[2024, "usd_per_p3"])
    M["CashReachTfour"] = f1(cash_nat[2024]["reached_h1_monthly"] / 1e6)
    M["CashReachTfive"] = f1(cash_nat[2025]["reached_h1_monthly"] / 1e6)
    M["CashReachDrop"] = pc(1 - cash_nat[2025]["reached_h1_monthly"] / cash_nat[2024]["reached_h1_monthly"])
    M["CashUsdTfour"] = f0(KEY["cash_totals"]["usd"][2024] / 1e6)
    M["CashUsdTfive"] = f0(KEY["cash_totals"]["usd"][2025] / 1e6)
    M["NeedDistricts"] = KEY["districts"]
    rn = {"cash_usd": "Cash", "cash_reached": "CashR", "partners": "Part", "reach": "Reach"}
    for r in T.itertuples():
        t = rn[r.response] + ("Pthree" if r.need == "p3" else "Pin") + str(r.year)[-1:].replace("4", "Four").replace(
            "5", "Five").replace("6", "Six")
        M[f"el{t}"], M[f"hi{t}"], M[f"lo{t}"] = f2(r.elasticity), f2(r.rel_high), f2(r.rel_low)
    on = {"gam": "Gam", "sam": "Sam", "muac_gam": "Muac", "cdr": "Cdr", "u5dr": "Ufive"}
    nn = {"need_p3": "Ipc", "pred_gam": "Pred"}
    for r in S.itertuples():
        t = nn[r.need] + on[r.outcome]
        sc = 10 if r.need == "need_p3" and r.outcome in ("gam", "sam", "muac_gam") else 1
        M[f"sp{t}"], M[f"spse{t}"] = f2(r.slope_pre / (10 if r.need == "need_p3" else 1)), \
            f2(r.slope_pre_se / (10 if r.need == "need_p3" else 1))
        M[f"sc{t}"], M[f"scse{t}"], M[f"scp{t}"] = f2(r.slope_change / (10 if r.need == "need_p3" else 1)), \
            f2(r.slope_change_se / (10 if r.need == "need_p3" else 1)), f"{r.p_slope_change:.3f}"
        M[f"lv{t}"], M[f"lvse{t}"] = f2(r.level_post), f2(r.level_post_se)
    en = {"z_cash_loss": "Cash", "z_partner_loss_q2": "Part", "z_reach_loss_26": "Reach"}
    for r in D.itertuples():
        t = en[r.exposure] + on[r.outcome]
        M[f"da{t}"], M[f"dase{t}"], M[f"dap{t}"] = f2(r.b), f2(r.se), f2(r.p_wild)
    for k, v in G.items():
        e, y = k.split("|")
        t = en[e] + on[y]
        M[f"gr{t}"], M[f"gg{t}"] = v["gap_rank"], f2(v["gap25"])
    c = KEY["change_corr"]
    M["CorrCashNeed"] = f2(KEY["cash_loss_vs_need24"])
    M["CorrCashDep"] = f2(c["cash_loss"]["index"])
    M["CorrCashUs"] = f2(c["cash_loss"]["E_pred"])
    M["CorrCashPart"] = f2(c["cash_loss"]["E_loss"])
    M["CorrReachCash"] = f2(c["reach_loss_26"]["cash_loss"])
    # cash per person in Phase 3+, January-June, by need tercile (2024 annual district totals scaled to Jan-Jun)
    t = T[(T.response == "cash_usd") & (T.need == "p3")].set_index("year")
    sc = {2024: KEY["cash_h1_scale_2024"], 2025: 1.0}
    for y, tg in [(2024, "Tfour"), (2025, "Tfive")]:
        for lv in ["low", "mid", "high"]:
            M[f"CashPer{lv.capitalize()}{tg}"] = f0(t.loc[y, f"per_need_{lv}"] * sc[y])
    for lv in ["low", "mid", "high"]:
        M[f"CashPerDrop{lv.capitalize()}"] = pc(1 - t.loc[2025, f"per_need_{lv}"] / (t.loc[2024, f"per_need_{lv}"] * sc[2024]))
    SY = pd.DataFrame(KEY["slope_year"])
    for r in SY.itertuples():
        t = ("All" if r.sample == "all" else "Gu") + on[r.outcome] + str(r.year)[-2:].replace("0", "o").replace("1", "i").replace("2", "t").replace("3", "h").replace("4", "f").replace("5", "v").replace("6", "s").replace("7", "e").replace("8", "g").replace("9", "n")
        M[f"sy{t}"], M[f"syse{t}"] = f2(r.b10), f2(r.se10)
    for lab in ["all", "gu"]:
        g = SY[(SY["sample"] == lab) & (SY.outcome == "gam") & (SY.year < 2025)]
        M[("All" if lab == "all" else "Gu") + "SlopeMaxPre"] = f2(g.b10.max())
        M[("All" if lab == "all" else "Gu") + "SlopePreFirst"] = f2(g[g.year < 2024].b10.mean())
    (ROOT / "output" / "us_cut_memo" / "numbers_need.tex").write_text(
        "% generated by code/70_somalia_need_response.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))


if __name__ == "__main__":
    main()
