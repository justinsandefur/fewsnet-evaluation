"""Northern Nigeria panels: survey outcomes, food-insecurity phases, shocks and humanitarian aid.

Two outputs, both keyed to OCHA COD-AB admin-2 P-codes (LGAs, e.g. NG008016 = Konduga):

  input/panel/nga_domain_panel.parquet   one row per survey domain x survey round
  input/panel/nga_lga_aid_panel.parquet  one row per LGA x survey round (LGAs inside any domain surveyed
                                         that round), with aid in the 6 months after the survey month

Scope: north-east (Adamawa, Borno, Yobe) and north-west (Jigawa, Kaduna, Katsina, Kebbi, Sokoto, Zamfara)
states. SMART+ surveys in Benue and Niger (BENSS, NSS; north-central) are dropped.

SOURCES AND CHOICES
1. Surveys: SMART+ dashboard (input/smartplus/{anthropometry,mortality}.json, as cached by
   58_phase_outcomes.py). Shared surveys only; the 'toto' test entry is dropped. GAM and SAM are
   weight-for-height (WHZ) prevalences for children 6-59 months, in percent; cdr and u5dr are crude and
   under-five death rates per 10,000 per day (mortality.json, same survey id). The dashboard API has no
   morbidity values (the 'indicators' list names morbidity modules, but keystats carry none), so
   `morbidity` is NaN throughout. Month = the dashboard's surveyYear/surveyMonth (one survey,
   'FHI 360_12_2024_Bama', is filed as 2024-08 although its name says 12_2024; the field is kept).
2. Survey domain -> LGAs: input/smartplus/nga_domain_lga.csv (written by this script if absent, then
   treated as a hand-editable input; delete it or pass --rebuild-crosswalk to regenerate). Rules:
   a. Programme surveys (NFSS by NBS/UNICEF in the north-east; SOKAZA in Sokoto/Katsina/Zamfara and,
      from 2025, Jigawa and Kebbi) report zones such as 'Northern Yobe' or 'Central Katsina 1'. Their
      LGA lists come from the IPC acute malnutrition (AMN) caseload tables that UNICEF/the Nutrition
      Sector post on HDX for the same NFSS/SOKAZA domains (Domain x LGA x under-five population):
      input/subnational_aid/hdx_response/nga/nigeria-acute-malnutrition-data/ (2024, 2025 and
      2026 tables). Tables are read oldest to newest and the newest assignment of an LGA wins (the 2025-26
      tables list complete zones; the 2024 Katsina table omitted some LGAs). Page-break artefacts are
      merged ('East Borno' + 'Eastern Borno'; 'Southern Adama-wa'; a lone 'Central Katsina' (Batsari)
      and 'Northern Katsina' (Baure) row go to zone 1 of that name). LGAs starred as inaccessible
      ('*Inaccessible areas, no data') in the newest table listing them (Abadam, Guzamala, Kukawa) are
      kept in the CSV with inaccessible=1 and get weight 0: the survey could not sample them.
   b. Kaduna (NFSS round 1, Aug 2026) has no domain table on disk. 'Kaduna Central' and 'Kaduna North'
      are taken to be the senatorial districts in COD-AB (sendist_en). This is an assumption.
   c. Single-LGA surveys (ACF, FHI 360, PUI, IMC) are matched to the LGA named in surveyName within the
      survey's state ('<LGA> LGA' domains).
   Weights: CH population of each LGA (sum of resident and IDP rows) from the CH analysis used for that
   survey (rule 3), normalised to 1 within the domain. The CSV also records the AMN-table under-five
   count for reference.
3. Phases, Cadre Harmonise (input/ipc/cadre_harmonise_caf_ipc_mars26.xlsx), CURRENT analyses only.
   Release month: March for the Jan-May exercise, November for the Sep-Dec exercise. For each survey,
   the latest current analysis released strictly before the survey month; LGAs absent from that
   exercise (e.g. the partial March 2026 file covers part of Borno only; Marte is dropped from CH after
   2023) fall back to the most recent earlier current analysis that has them (ch_age_m = months from
   release to survey; in the domain panel the maximum over its LGAs, ch_release the newest release used). need_p3 = sum(phase35) / sum(population) over the domain's LGAs (population-weighted CH
   Phase 3+ share); p3 = people in Phase 3-5.
4. FEWS NET (input/fewsnet/cs_monthly.parquet, proj_monthly.parquet). There is no tidy Nigeria
   fnid->LGA table, so one is built here by overlaying the FEWS NET units in use since 2021
   (admin-2 x livelihood-zone polygons, input/fewsnet/units.gpkg) on COD-AB LGAs (equal-area
   projection); an LGA's value is the area-weighted mean over the unit pieces inside it.
   fews_cs: phase of the latest current-situation map in the survey month or the 3 months before
   (as in 58_phase_outcomes.py); FEWS NET maps Nigeria in Feb, Jun and Oct, so this is the June map
   for Jun-Sep surveys. The 2025 shutdown left no Feb or Jun 2025 map, so Aug-Sep 2025 surveys are NaN.
   fews_fc: projection for the survey month from the latest report issued 3-8 months earlier (lead
   3-8). Domain values are CH-population-weighted means over LGAs.
5. Shocks, windows ending in the survey month m (input/panel/shock_panel.parquet only holds CH
   analysis months, March and November, so values are recomputed with the same code):
   rain_z, rain12_z: 6- and 12-month CHIRPS rainfall z-scores against the previous 20 years
     (24_area_rainfall.shocks on input/panel/area_rain_monthly.parquet, CH LGA polygons), windows
     ending in m.
   log_fat: log(1 + ACLED fatalities in months m-5..m) from input/acled/hdx/nga.xlsx, matched by
     ACLED's own admin-2 P-code (LGA panel: per LGA; domain panel: log1p of the domain's summed
     fatalities). Rain and price values reproduce shock_panel.parquet exactly at its months; fatalities
     differ for a few LGAs (Abadam, Maiduguri, Wamako, Gulani) where 27's name match falls back to the
     state total, which the P-code match avoids.
   dp3, dp12: mean 3- and 12-month log change in WFP retail cereal/tuber prices over months m-2..m,
     markets in the LGA, else in the state (27_shock_index.wfp_prices / price_shocks).
   Domain values for rain and prices are CH-population-weighted means over LGAs.
6. Aid (LGA panel), windows defined on the survey month m:
   cbpf_usd: OCHA Nigeria Humanitarian Fund (CBPF fund 75) budgets for projects starting in months
     m+1..m+6, all clusters, split by LGA with the location x cluster budget table
     (ProjectSummaryAggV2 AdmLocClustBdg2; start date AStrDt, else approval date; as in
     61_subnational_panel.cbpf_side). LGA names matched to COD-AB with 62_tidy_3w.Gazetteer. LGAs the fund
     never allocated to get 0 (the fund covers the north-east, and a few north-west projects). NaN if the
     window runs past the data vintage (CBPF cached 8 Oct 2026, so windows must end by Sep 2026).
     cbpf_usd_prev6: same for months m-6..m-1. Note the April 2026 'NSFT' allocation (about $121M,
     mostly WFP/UNICEF), several times a normal year, sits in the prev6 window of Aug 2026 surveys.
   partners: distinct organisations (acronym, else name) reporting any activity in the LGA in any month
     m+1..m+6 in OCHA's north-east 3W (input/subnational_aid/hdx_3w/nga; header detection from
     62_tidy_3w / 64_wfp_subnational). Rows with status planned, cancelled or suspended are excluded.
     When several files report the same month, the file with the most rows for that month is used (the
     Jan-Dec 2023 'Updated' release supersedes the 2023 quarterlies). The Jul-Sep 2025 file is a copy
     of Apr-Jun 2025 with the months relabelled (over 99% of rows identical) and is dropped, so 3W coverage
     is Jan 2023-Jun 2025 and Apr-Jun 2026. NaN if no 3W month falls in the window, and for LGAs outside
     Adamawa, Borno and Yobe (the 3W covers only those states); 0 for covered LGAs with no rows.
     partners_months = number of window months with 3W data.
   reach: NaN. The 2023-2026 Nigeria 3W files carry no people-reached column (only Nov 2019-2020 do),
     and no other LGA-level reach series exists for these years (references/subnational_aid.md).
7. LGA outcomes: gam, sam, cdr, u5dr from the domain(s) covering the LGA that round; if several, mean
   weighted by the LGA's weight in each domain (so a single-LGA survey outweighs a zone survey).
8. Lags: L_gam, L_cdr, L_u5dr = the same domain's previous survey (any round), NaN if none.

Usage: .venv/bin/python code/88_nigeria_panels.py [--rebuild-crosswalk]
"""
import importlib.util
import json
import re
import sys
import unicodedata
import warnings
import zipfile
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "input"
SA = INP / "subnational_aid"
XW = INP / "smartplus" / "nga_domain_lga.csv"
VINTAGE_CBPF = pd.Period("2026-09", "M")       # last complete month in the cached CBPF tables
STATES = ["Adamawa", "Borno", "Yobe", "Jigawa", "Kaduna", "Katsina", "Kebbi", "Sokoto", "Zamfara"]
THREEW_STATES = {"Adamawa", "Borno", "Yobe"}
DIRS = {"north": "Northern", "northern": "Northern", "south": "Southern", "southern": "Southern",
        "east": "Eastern", "eastern": "Eastern", "west": "Western", "western": "Western",
        "central": "Central", "centarl": "Central"}
AMN_DIR = SA / "hdx_response/nga/nigeria-acute-malnutrition-data"
AMN_FILES = ["Nigerian_Acute_Malnutrition_2024.xlsx", "Nigerian_Acute_Malnutrition_2025.xlsx",
             "nigerian-acute-malnutrition-2026-april-may-september.xlsx"]
LGA_ALIAS = {"dageshuni": "Dange-Shuni", "dangeshuni": "Dange-Shuni", "wammako": "Wamako", "wamakko": "Wamako",
             "teungo": "Toungo", "gumi": "Gummi", "maiadwa": "Mai'adua", "jere": "Jere", "kauranamoda": "Kaura Namoda",
             "birninkudu": "Birni Kudu", "suletankakar": "Sule-Tankarkar", "malammaduri": "Malam Madori",
             "kirikasama": "Kiri Kasamma", "wasagudanko": "Wasagu/Danko", "makarfi": "Markafi",
             "sabongari": "Sabon-Gari", "dutsinma": "Dutsin-Ma", "askirauba": "Askira/Uba"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


W64 = load("w64", "64_wfp_subnational.py")        # 3W header helpers (imports 62 as W64.t62)
T62 = W64.t62
RAIN = load("rain24", "24_area_rainfall.py")
SHK = load("shock27", "27_shock_index.py")


def nm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


# ------------------------------------------------------------------ geography
def cod():
    g = gpd.read_file(zipfile.ZipFile(INP / "areas/codab/nga.geojson.zip").open("nga_admin2.geojson"))
    return g[["adm2_pcode", "adm2_name", "adm1_pcode", "adm1_name", "sendist_en", "geometry"]]


class Names:
    """LGA names -> COD-AB P-codes (62_tidy_3w.Gazetteer, plus aliases for spellings it misses)."""

    def __init__(self, G):
        self.gz = T62.Gazetteer("NGA")
        self.G = G
        self.a1 = dict(zip(G.adm1_name, G.adm1_pcode))
        self.byname = {(r.adm1_name, nm(r.adm2_name)): r.adm2_pcode for r in G.itertuples()}

    def lga(self, state, name, code=None):
        a1 = self.a1.get(state)
        n = nm(re.sub(r"\*", "", str(name)))
        if n in LGA_ALIAS and (state, nm(LGA_ALIAS[n])) in self.byname:
            return self.byname[(state, nm(LGA_ALIAS[n]))]
        if (state, n) in self.byname:
            return self.byname[(state, n)]
        p, _, _ = self.gz.match_adm2(str(name).replace("*", "").strip(), a1, code)
        return p


def ch_to_cod(c):
    return f"NG0{c[2:4]}0{c[4:6]}" if isinstance(c, str) and len(c) == 6 else None


def cod_to_ch(p):
    return f"NG{p[3:5]}{p[6:8]}"


# ------------------------------------------------------------------ crosswalk
def canon_domain(text, state_hint=None):
    """'NFSS_R13_..._Northern Yobe' / 'Central\\nKatsina 1' / 'KEBBI CENTRAL 1' -> 'Central Kebbi 1'."""
    toks = re.findall(r"[a-z]+|\d+", str(text).lower())
    if "mmc" in toks:
        return "MMC/Jere", "Borno"
    st = next((s for s in STATES + ["Benue", "Niger"] if s.lower() in toks), None)
    if st is None:   # 'Southern Adama-wa', 'Adama wa'
        j = "".join(toks)
        st = next((s for s in STATES if s.lower() in j), state_hint)
    d = next((DIRS[t] for t in toks if t in DIRS), None)
    num = toks[-1] if toks and re.fullmatch(r"[1-9]", toks[-1]) else None
    if d is None or st is None:
        return None, st
    return f"{d} {st}" + (f" {num}" if num else ""), st


def amn_tables(N):
    rows = []
    for f in AMN_FILES:
        book = pd.read_excel(AMN_DIR / f, sheet_name=None, header=None)
        for sh, v in book.items():
            hit = [i for i, r in v.iterrows() if any(isinstance(c, str) and c.startswith("Local") for c in r)]
            if not hit:
                continue
            v = v.iloc[hit[0] + 1:, :3].copy()
            v.columns = ["dom", "lga", "u5"]
            v["dom"] = v.dom.ffill()
            v = v.dropna(subset=["lga"])
            for r in v.itertuples():
                if str(r.dom).strip().lower().startswith(("total", "*")) or str(r.lga).strip().lower() == "total":
                    continue
                d, st = canon_domain(r.dom)
                if d is None or st not in STATES:
                    continue
                for lg in re.split(r",\s*", str(r.lga)):
                    rows.append(dict(table=f, sheet=sh, domain=d, state=st, lga_raw=lg.strip(),
                                     inaccessible=int("*" in lg or "*" in str(r.dom)),
                                     u5=pd.to_numeric(str(r.u5).replace(",", ""), errors="coerce")))
    a = pd.DataFrame(rows)
    a["lga_raw"] = a.lga_raw.str.replace(r"\s+", " ", regex=True).str.replace(r"^J ere$", "Jere", regex=True)
    a["lga"] = [N.lga(s, x) for s, x in zip(a.state, a.lga_raw)]
    bad = a[a.lga.isna()]
    if len(bad):
        print("  AMN-table LGAs not matched to COD-AB:", bad[["state", "lga_raw"]].drop_duplicates().values.tolist())
    # page-break artefacts: a domain without a number whose numbered siblings exist -> zone 1
    doms = set(a.domain)
    a["domain"] = [f"{d} 1" if (not d[-1].isdigit() and f"{d} 1" in doms) else d for d in a.domain]
    a["order"] = a.table.map({f: i for i, f in enumerate(AMN_FILES)})
    a = a.dropna(subset=["lga"]).sort_values("order")
    last = a.groupby("lga").tail(1)                    # newest table wins
    return last


def build_crosswalk(N, G, surveys):
    a = amn_tables(N)
    out = []
    for r in a.itertuples():
        src = f"IPC AMN caseload table (HDX nigeria-acute-malnutrition-data), {r.table} [{r.sheet}]"
        why = "LGA listed under this NFSS/SOKAZA domain in the newest table that lists it"
        if r.inaccessible:
            why += "; starred inaccessible (not sampled) -> weight 0"
        out.append(dict(domain=r.domain, state=r.state, lga_pcode=r.lga, lga_name=None, inaccessible=r.inaccessible,
                        u5_amn_table=r.u5, source_rationale=f"{src}: {why}"))
    for sd in ["Kaduna Central", "Kaduna North"]:
        d = ("Central" if "Central" in sd else "Northern") + " Kaduna"
        for p in G.loc[G.sendist_en == sd, "adm2_pcode"]:
            out.append(dict(domain=d, state="Kaduna", lga_pcode=p, lga_name=None, inaccessible=0, u5_amn_table=np.nan,
                            source_rationale=f"No NFSS Kaduna domain table on disk; ASSUMED domain = {sd} senatorial "
                                             "district (COD-AB sendist_en)"))
    for d, st, p in surveys.loc[surveys.single_lga, ["domain", "state", "lga1"]].drop_duplicates().values:
        out.append(dict(domain=d, state=st, lga_pcode=p, lga_name=None, inaccessible=0, u5_amn_table=np.nan,
                        source_rationale="Single-LGA survey: LGA named in the SMART+ surveyName"))
    X = pd.DataFrame(out)
    X["lga_name"] = X.lga_pcode.map(dict(zip(G.adm2_pcode, G.adm2_name)))
    X = X.sort_values(["state", "domain", "lga_name"]).reset_index(drop=True)
    XW.parent.mkdir(parents=True, exist_ok=True)
    X.to_csv(XW, index=False)
    print(f"  wrote {XW.relative_to(ROOT)} ({len(X)} rows, {X.domain.nunique()} domains)")
    return X


# ------------------------------------------------------------------ surveys
PROG = re.compile(r"^(NFSS|SOKAZA|NSS|BENSS)_R(\d+)_", re.I)


def surveys(N, G):
    a = json.loads((INP / "smartplus/anthropometry.json").read_text())["surveys"]
    mo = {s["id"]: s["keystats"] for s in json.loads((INP / "smartplus/mortality.json").read_text())["surveys"]}
    g = _g
    rows = []
    for s in a:
        if s["countryCode"] != "NG" or not s["share"] or re.match(r"(?i)^(toto|test)\b", s["surveyName"].strip()):
            continue
        k, mk = s["keystats"], mo.get(s["id"], {})
        name = s["surveyName"].strip()
        m = PROG.match(name)
        month = pd.Period(f"{s['surveyYear']}-{s['surveyMonth']:02d}", "M")
        rec = dict(sid=s["id"], survey=name, month=month, adm1=s["administrative_area_level_1"],
                   gam=100 * g(k, "gam", "whz", "all", "prop"), sam=100 * g(k, "sam", "whz", "all", "prop"),
                   cdr=g(mk, "crudeMortalityRate", "all", "stat"), u5dr=g(mk, "under5MortalityRate", "stat"),
                   morbidity=np.nan, single_lga=False, lga1=None)
        if m:
            d, st = canon_domain(name[m.end():], s["administrative_area_level_1"])
            rec.update(domain=d, state=st, round_id=f"{m.group(1).upper()}_R{int(m.group(2))}")
        else:
            st = s["administrative_area_level_1"]
            x = nm(name)
            pool = G[G.adm1_name == st]
            hits = [(len(nm(r.adm2_name)), r.adm2_pcode, r.adm2_name) for r in pool.itertuples()
                    if nm(r.adm2_name) in x]
            if not hits:
                print("  no LGA found in survey name:", name)
                continue
            _, p, lname = max(hits)
            org = re.split(r"[_,]", name)[0].strip()
            rec.update(domain=f"{lname} LGA", state=st, round_id=f"{org}_{month}", single_lga=True, lga1=p)
        rows.append(rec)
    S = pd.DataFrame(rows)
    drop = S[~S.state.isin(STATES) | S.domain.isna()]
    print(f"  SMART+ Nigeria: {len(S)} shared surveys; dropped {len(drop)} outside NE/NW or without a domain:",
          sorted(set(drop.survey.str[:40])))
    S = S[S.state.isin(STATES) & S.domain.notna()].copy()
    dup = S[S.duplicated(["domain", "round_id"], keep=False)]
    if len(dup):
        print("  duplicate domain x round (kept first):", dup[["domain", "round_id", "survey"]].values.tolist())
        S = S.drop_duplicates(["domain", "round_id"])
    return S


def _g(d, *ks):
    for k in ks:
        if not isinstance(d, dict):
            return np.nan
        d = d.get(k)
    return d if d is not None else np.nan


# ------------------------------------------------------------------ Cadre Harmonise
def cadre():
    x = pd.read_excel(INP / "ipc/cadre_harmonise_caf_ipc_mars26.xlsx")
    x = x[(x.adm0_name == "Nigeria") & (x.chtype == "current") & x.adm2_pcod2.notna()]
    x = x[x.exercise_label.isin(["Jan-May", "Sep-Dec"])]
    x["release"] = [pd.Period(f"{y}-{'03' if l == 'Jan-May' else '11'}", "M") for y, l in zip(x.exercise_year, x.exercise_label)]
    x["lga"] = x.adm2_pcod2.map(ch_to_cod)
    c = x.groupby(["lga", "release"]).agg(pop=("population", lambda v: v.sum(min_count=1)),
                                          p3=("phase35", lambda v: v.sum(min_count=1))).reset_index()
    return c.dropna(subset=["pop"])


def ch_for(C, lgas, month):
    """Per LGA: latest current CH released strictly before `month` (fallback: older)."""
    c = C[C.lga.isin(lgas) & (C.release < month)].sort_values("release").groupby("lga").tail(1).set_index("lga")
    c["ch_age_m"] = [(month - r).n for r in c.release]
    return c


# ------------------------------------------------------------------ FEWS NET
def fews_weights(G):
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet")
    cs = cs[(cs.country_code == "NG") & (cs.month >= "2022-01")]
    U = gpd.read_file(INP / "fewsnet/units.gpkg")
    U = U[U.fnid.isin(cs.fnid.unique())].drop_duplicates("fnid")[["fnid", "geometry"]]
    U = U[U.geom_type.isin(["Polygon", "MultiPolygon"])]
    L = G[G.adm1_name.isin(STATES)][["adm2_pcode", "geometry"]]
    ea = "EPSG:6933"
    o = gpd.overlay(U.to_crs(ea), L.to_crs(ea), how="intersection", keep_geom_type=True)
    o["a"] = o.area
    o = o[o.a > 0]
    o["w"] = o.a / o.groupby("adm2_pcode").a.transform("sum")
    o = o[o.w > 0.005]
    o["w"] = o.w / o.groupby("adm2_pcode").w.transform("sum")
    print(f"  FEWS NET: {U.fnid.nunique()} units overlaid on {o.adm2_pcode.nunique()} of {len(L)} NE/NW LGAs")
    return o[["fnid", "adm2_pcode", "w"]].rename(columns={"adm2_pcode": "lga"})


def fews_values(FW, months):
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet")
    cs = cs[(cs.country_code == "NG") & cs.fnid.isin(FW.fnid)]
    pr = pd.read_parquet(INP / "fewsnet/proj_monthly.parquet")
    pr = pr[(pr.country_code == "NG") & pr.fnid.isin(FW.fnid) & pr.lead.between(3, 8)]
    out = []
    for m in months:
        c = cs[cs.month.between(m - 3, m)].sort_values("month").groupby("fnid").tail(1)[["fnid", "phase"]]
        p = pr[pr.month == m]
        p = p[p.report_month == p.groupby("fnid").report_month.transform("max")].groupby("fnid").phase.max()
        u = FW.merge(c.rename(columns={"phase": "cs"}), on="fnid", how="left")
        u["fc"] = u.fnid.map(p)
        for v in ["cs", "fc"]:
            ok = u[v].notna()
            agg = (u[v] * u.w).where(ok).groupby(u.lga).sum(min_count=1) / u.w.where(ok).groupby(u.lga).sum()
            u[f"{v}_l"] = u.lga.map(agg)
        r = u.drop_duplicates("lga")[["lga", "cs_l", "fc_l"]].rename(columns={"cs_l": "fews_cs", "fc_l": "fews_fc"})
        r["month"] = m
        out.append(r)
    return pd.concat(out, ignore_index=True)


# ------------------------------------------------------------------ shocks
def shocks(pairs, G):
    """pairs: DataFrame lga, month (survey month). Windows end in the survey month."""
    p = pairs.drop_duplicates().copy()
    p["key"] = p.lga.map(cod_to_ch)
    p["t"] = p.month + 1                        # 24/27 windows end at t-1
    R = pd.read_parquet(INP / "panel/area_rain_monthly.parquet")
    R.columns = pd.PeriodIndex(R.columns, freq="M")
    r = RAIN.shocks(R, p[["key", "t"]].rename(columns={"t": "month"}))
    r = r.rename(columns={"month": "t", "rain_z6": "rain_z", "rain_z12": "rain12_z"})
    p = p.merge(r[["key", "t", "rain_z", "rain12_z"]], on=["key", "t"], how="left")
    # ACLED fatalities m-5..m by ACLED's admin-2 P-code
    a = pd.read_excel(INP / "acled/hdx/nga.xlsx", sheet_name="Data")
    a["month"] = pd.PeriodIndex([f"{y}-{SHK.MONTHS[mm]:02d}" for y, mm in zip(a.Year, a.Month)], freq="M")
    f = a.groupby(["Admin2 Pcode", "month"]).Fatalities.sum()
    last = a.month.max()
    p["fat6"] = [sum(f.get((l, m - k), 0) for k in range(6)) if m <= last else np.nan for l, m in zip(p.lga, p.month)]
    # prices (27_shock_index): months t-3..t-1 = m-2..m
    geo = gpd.read_file(INP / "areas/ch_current_2023.geojson")
    geo = geo[geo.adm0_pcod3 == "NGA"].dropna(subset=["adm2_pcod2"]).drop_duplicates("adm2_pcod2")
    geo = geo.rename(columns={"adm2_pcod2": "key"})[["key", "geometry"]]
    mk = SHK.wfp_prices()
    mk = mk[mk.iso3 == "NGA"]
    pp = p[["key", "t", "lga"]].rename(columns={"t": "month"})
    pp["iso3"] = "NGA"
    pp["adm1_name"] = pp.lga.map(dict(zip(G.adm2_pcode, G.adm1_name)))
    ps = SHK.price_shocks(pp, mk, geo).sort_values("price_level").drop_duplicates(["key", "month"])
    p = p.merge(ps.rename(columns={"month": "t"})[["key", "t", "dp3", "dp12", "price_level"]], on=["key", "t"], how="left")
    return p.drop(columns=["key", "t"])


# ------------------------------------------------------------------ CBPF
def cbpf(N):
    a = pd.read_csv(SA / "cbpf/ProjectSummaryAggV2.csv", low_memory=False)
    a = a[a.PFId == 75]
    p = pd.read_csv(SA / "cbpf/ProjectSummaryV2.csv", low_memory=False)[["PrjCode", "AStrDt", "ApprDt"]]
    a = a.merge(p.drop_duplicates("PrjCode"), on="PrjCode", how="left")
    a["start"] = pd.to_datetime(a.AStrDt, format="mixed", errors="coerce").fillna(
        pd.to_datetime(a.ApprDt, format="mixed", errors="coerce"))
    a = a.dropna(subset=["start", "AdmLoc2"])
    a["usd"] = [sum(float(b) for b in str(x).split("|||") if re.fullmatch(r"-?[\d.]+", b.strip()))
                for x in a.AdmLocClustBdg2]
    a["lga"] = [N.lga(s, l) for s, l in zip(a.AdmLoc1, a.AdmLoc2)]
    a["m"] = a.start.dt.to_period("M")
    print(f"  CBPF NGA75: {len(a)} project-locations, {a.lga.notna().mean():.3f} of rows and "
          f"{a.loc[a.lga.notna(), 'usd'].sum() / a.usd.sum():.3f} of US$ matched to LGAs; starts {a.m.min()}..{a.m.max()}")
    return a.dropna(subset=["lga"]).groupby(["lga", "m"]).usd.sum()


def window_sum(s, lga, a, b):
    if lga is None:
        return np.nan
    try:
        x = s.loc[lga]
    except KeyError:
        return 0.0
    return float(x[(x.index >= a) & (x.index <= b)].sum())


# ------------------------------------------------------------------ 3W presence
SKIP_STATUS = re.compile(r"plan|cancel|suspend", re.I)


def presence(N):
    base = SA / "hdx_3w/nga"
    files, seen = [], {}
    for p in sorted(base.rglob("*")):
        if not p.is_file() or not re.search(r"\.(xlsx|csv)$", p.name, re.I):
            continue
        win = W64.file_window(p.name)
        if win is None or win[1] < pd.Timestamp("2022-07-01"):
            continue
        book = T62.read_book(p)
        pk = T62.pick_sheet(book, need=("org",))
        if pk is None:
            print("  3W skip (no organisation column):", p.name)
            continue
        name, start, roles, rows, hi = pk
        roles = W64.augment(roles, rows[hi], "nga")
        H = [str(h).strip().lower() if h is not None else "" for h in rows[hi]]
        roles.setdefault("status", next((j for j, h in enumerate(H) if h.startswith("status")), None))
        tcols = [j for j, h in enumerate(H) if h not in ("month", "year", "date check")]
        sig = {tuple(str(r[j]) if j < len(r) else "" for j in tcols) for r in rows[start:] if r}
        files.append((p, win, roles, rows, start, sig))
    # relabelled duplicates: >98% of a file's rows (ignoring month/year) found in a file for an earlier,
    # non-overlapping window (overlapping releases, e.g. 2023 quarterlies vs Jan-Dec 2023, are resolved per month below)
    keep = []
    for i, (p, win, roles, rows, start, sig) in enumerate(files):
        dup = [q for q, w2, *_r, s2 in files[:i] if w2[1] < win[0] and len(sig & s2) > 0.98 * len(sig)]
        if dup:
            print(f"  3W drop {p.name}: same rows as {dup[0].name} with months relabelled")
            continue
        keep.append((p, win, roles, rows, start))
    recs = []
    for p, win, roles, rows, start in keep:
        for rec in T62.rows_to_records(rows, start, roles):
            org = rec.get("org_acr") or rec.get("org")
            if not org or (rec.get("status") and SKIP_STATUS.search(str(rec["status"]))):
                continue
            per = None
            if rec.get("month") is not None:
                yr = int(T62.num(rec["year"])) if T62.num(rec.get("year")) == T62.num(rec.get("year")) else win[0].year
                per = T62.parse_month(rec["month"], yr)
            if per is None or per[0] != per[1] or not (win[0] <= per[0] <= win[1]):
                continue
            recs.append((p.name, T62.clean_org(org), rec.get("adm1"), rec.get("adm2"), rec.get("adm2_code"),
                         pd.Period(per[0], "M")))
    D = pd.DataFrame(recs, columns=["file", "org", "adm1", "adm2", "code", "m"])
    keys = D[["adm1", "adm2", "code"]].drop_duplicates()
    keys["lga"] = [N.gz.match_adm2(str(b) if b else None, N.gz.match_adm1(str(a) if a else None)[0], c)[0]
                   for a, b, c in keys.itertuples(index=False)]
    D = D.merge(keys, on=["adm1", "adm2", "code"], how="left")
    # one file per month: the one with most rows that month
    n = D.groupby(["m", "file"]).size().rename("n").reset_index().sort_values("n").groupby("m").tail(1)
    D = D.merge(n[["m", "file"]], on=["m", "file"])
    print(f"  3W: {len(D):,} activity rows, {D.lga.notna().mean():.3f} matched to LGAs; months covered: "
          f"{D.m.min()}..{D.m.max()} ({D.m.nunique()} months); files used: {sorted(D.file.unique())}")
    return D.dropna(subset=["lga"]), set(D.m)


# ------------------------------------------------------------------ main
def main(rebuild):
    G = cod()
    N = Names(G)
    S = surveys(N, G)
    X = build_crosswalk(N, G, S) if (rebuild or not XW.exists()) else pd.read_csv(XW)
    miss = sorted(set(S.domain) - set(X.domain))
    if miss:
        print("  domains without LGAs in the crosswalk (dropped):", miss)
        S = S[~S.domain.isin(miss)]
    Xa = X[X.inaccessible == 0]
    dl = Xa.groupby("domain").lga_pcode.apply(list).to_dict()
    C = cadre()
    states = dict(zip(G.adm2_pcode, G.adm1_name))

    # LGA-level inputs for every (lga, survey month)
    pairs = pd.DataFrame([(l, m) for d, m in zip(S.domain, S.month) for l in dl[d]], columns=["lga", "month"]).drop_duplicates()
    FW = fews_weights(G)
    FV = fews_values(FW, sorted(pairs.month.unique()))
    SH = shocks(pairs, G)
    LV = pairs.merge(FV, on=["lga", "month"], how="left").merge(SH, on=["lga", "month"], how="left")
    LV = LV.set_index(["lga", "month"])

    dom_rows, lga_rows = [], []
    for s in S.itertuples():
        lgas = dl[s.domain]
        ch = ch_for(C, lgas, s.month)
        pops = pd.Series({l: ch["pop"].get(l, np.nan) for l in lgas})
        w = (pops / pops.sum()).fillna(0.0)
        lv = LV.loc[[(l, s.month) for l in lgas]].droplevel(1)

        def wmean(v):
            ok = lv[v].notna() & (w > 0)
            return float((lv.loc[ok, v] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan
        dom_rows.append(dict(
            domain=s.domain, round_id=s.round_id, month=str(s.month), state=s.state, survey=s.survey, sid=s.sid,
            lgas=json.dumps({l: round(float(w[l]), 4) for l in lgas}), n_lgas=len(lgas),
            gam=s.gam, sam=s.sam, cdr=s.cdr, u5dr=s.u5dr, morbidity=s.morbidity,
            need_p3=ch.p3.sum() / ch["pop"].sum() if len(ch) and ch.p3.notna().any() else np.nan,
            ch_release=str(ch.release.max()) if len(ch) else None, ch_age_m=ch.ch_age_m.max() if len(ch) else np.nan,
            fews_cs=wmean("fews_cs"), fews_fc=wmean("fews_fc"), rain_z=wmean("rain_z"), rain12_z=wmean("rain12_z"),
            log_fat=np.log1p(lv.fat6.sum()) if lv.fat6.notna().any() else np.nan,
            dp3=wmean("dp3"), dp12=wmean("dp12"), pop=pops.sum(min_count=1)))
        for l in lgas:
            lga_rows.append(dict(lga=l, round_id=s.round_id, domain=s.domain, month=s.month, w=w[l],
                                 gam=s.gam, sam=s.sam, cdr=s.cdr, u5dr=s.u5dr))
    D = pd.DataFrame(dom_rows)
    D["_m"] = pd.PeriodIndex(D.month, freq="M")
    D = D.sort_values(["domain", "_m"])
    for v in ["gam", "cdr", "u5dr"]:
        D[f"L_{v}"] = D.groupby("domain")[v].shift(1)
    D["L_month"] = D.groupby("domain").month.shift(1)
    D = D.drop(columns="_m").reset_index(drop=True)

    # ---- LGA x round panel
    L = pd.DataFrame(lga_rows)
    L["ww"] = L.w.where(L.w > 0, 1e-6)
    agg = []
    for (l, r), g in L.groupby(["lga", "round_id"]):
        rec = dict(lga=l, round_id=r, month=g.month.min(), domains="|".join(g.domain), lga_name=None)
        for v in ["gam", "sam", "cdr", "u5dr"]:
            ok = g[v].notna()
            rec[v] = float((g.loc[ok, v] * g.ww[ok]).sum() / g.ww[ok].sum()) if ok.any() else np.nan
        agg.append(rec)
    A = pd.DataFrame(agg)
    A["lga_name"] = A.lga.map(dict(zip(G.adm2_pcode, G.adm2_name)))
    A["state"] = A.lga.map(states)
    chrows = []
    for r in A.itertuples():
        ch = ch_for(C, [r.lga], r.month)
        chrows.append((ch["pop"].iloc[0], ch.p3.iloc[0], str(ch.release.iloc[0]), ch.ch_age_m.iloc[0]) if len(ch)
                      else (np.nan, np.nan, None, np.nan))
    A[["pop", "p3", "ch_release", "ch_age_m"]] = pd.DataFrame(chrows, index=A.index)
    A["need_p3"] = A.p3 / A["pop"]
    A = A.merge(LV.reset_index(), on=["lga", "month"], how="left")
    A["log_fat"] = np.log1p(A.fat6)

    # aid
    CB = cbpf(N)
    P, pmonths = presence(N)
    po = P.groupby(["lga", "m"]).org.apply(set)
    cb, cbp, part, pmon = [], [], [], []
    for r in A.itertuples():
        a, b = r.month + 1, r.month + 6
        cb.append(window_sum(CB, r.lga, a, b) if b <= VINTAGE_CBPF else np.nan)
        cbp.append(window_sum(CB, r.lga, r.month - 6, r.month - 1))
        cov = [m for m in pd.period_range(a, b, freq="M") if m in pmonths]
        pmon.append(len(cov))
        if not cov or r.state not in THREEW_STATES:
            part.append(np.nan)
            continue
        orgs = set()
        for m in cov:
            orgs |= po.get((r.lga, m), set())
        part.append(float(len(orgs)))
    A["cbpf_usd"], A["cbpf_usd_prev6"], A["partners"], A["partners_months"] = cb, cbp, part, pmon
    A["reach"] = np.nan
    A["month"] = A.month.astype(str)
    cols = ["lga", "lga_name", "state", "round_id", "month", "domains", "pop", "need_p3", "p3", "ch_release", "ch_age_m",
            "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat", "dp3", "dp12", "price_level",
            "gam", "sam", "cdr", "u5dr", "cbpf_usd", "cbpf_usd_prev6", "partners", "partners_months", "reach"]
    A = A[cols].sort_values(["round_id", "lga"]).reset_index(drop=True)

    dcols = ["domain", "round_id", "month", "state", "survey", "sid", "lgas", "n_lgas", "gam", "sam", "cdr", "u5dr",
             "morbidity", "need_p3", "ch_release", "ch_age_m", "fews_cs", "fews_fc", "rain_z", "rain12_z", "log_fat",
             "dp3", "dp12", "pop", "L_gam", "L_cdr", "L_u5dr", "L_month"]
    D = D[dcols]
    D.to_parquet(INP / "panel/nga_domain_panel.parquet", index=False)
    A.to_parquet(INP / "panel/nga_lga_aid_panel.parquet", index=False)
    report(D, A)


def report(D, A):
    pd.set_option("display.width", 200)
    print("\n================ COVERAGE ================")
    for name, T, key, unit in [("nga_domain_panel", D, ["domain", "round_id"], "domain"),
                               ("nga_lga_aid_panel", A, ["lga", "round_id"], "lga")]:
        assert not T.duplicated(key).any(), f"{name}: duplicate keys"
        print(f"\n{name}: {len(T)} rows, {T.round_id.nunique()} rounds, {T[unit].nunique()} {unit}s, "
              f"months {T.month.min()}..{T.month.max()}, states {sorted(T.state.unique())}")
        num = [c for c in T.columns if c not in key + ["month", "state", "survey", "lgas", "domains", "lga_name", "sid"]]
        print("  share non-missing: " + ", ".join(f"{c}={T[c].notna().mean():.2f}" for c in num))
    print("\nrounds (domain panel):")
    print(D.groupby("round_id").agg(month=("month", "min"), domains=("domain", "size"), gam=("gam", lambda x: x.notna().sum()),
                                    cdr=("cdr", lambda x: x.notna().sum()), fews_cs=("fews_cs", lambda x: x.notna().sum()),
                                    need_p3=("need_p3", lambda x: x.notna().sum())).sort_values("month").to_string())
    print("\naid coverage by round (LGA panel):")
    g = A.groupby("round_id").agg(month=("month", "min"), lgas=("lga", "size"),
                                  cbpf_nonmiss=("cbpf_usd", lambda x: x.notna().mean()),
                                  cbpf_pos=("cbpf_usd", lambda x: (x > 0).mean()),
                                  cbpf_musd=("cbpf_usd", lambda x: x.sum() / 1e6),
                                  partners=("partners", lambda x: x.notna().mean()),
                                  partners_mean=("partners", "mean"))
    print(g.sort_values("month").round(2).to_string())


if __name__ == "__main__":
    main("--rebuild-crosswalk" in sys.argv)
