"""Did child wasting rise more in parts of Somalia that relied on US-funded partners?

The 2025 US aid withdrawal (stop-work order 24 Jan 2025, terminations Feb-Mar) as a
difference-in-differences across FSNAU survey domains, 2015-2025.

Outcome. FSNAU's seasonal SMART surveys (post-Gu ~Jun-Jul, post-Deyr ~Nov-Dec), one row
per survey domain x season: rural livelihood zones (matched to FEWS NET units with the
rules in 57_fsnau_value.py) and town IDP / urban populations. Primary: GAM (weight-for-
height, %). Secondary: SAM, MUAC-based GAM, crude and under-5 death rates. Ad hoc partner
NGO surveys and MUAC-only rapid assessments are excluded, as in 57.

Exposure (two measures, side by side; districts collapsed so Banadir is one unit).
  A. Predicted reliance: the share of a district's 2024 partner presence in nutrition,
     health, food security and WASH that was US-funded. Built from OCHA's 2024 3W, which
     names the donor of each activity: US donors (USAID, BHA, PRM, State) = 1; pass-through
     UN agencies (UNICEF, WFP, UNHCR, ...) = that agency's 2023-24 US share in Somalia from
     FTS; other donors = 0; activities without a usable donor take the organisation's own
     average (else the average for its organisation type). Fixed before the cut.
  B. Actual partner loss: 1 - (average monthly partners Apr-Oct 2025 / Apr-Oct 2024) in
     the same four sectors, from the organisation-level 3W (62_tidy_3w.py).
  Domains take the population-weighted mean over their districts.

Model. y[i,t] = a[i] + g[type x season] + b * E[i] x Post[t] + controls + e,
Post = Gu 2025 and Deyr 2025/26. Event study: E x year (2024 = reference). Controls:
rainfall anomaly (6-month CHIRPS z-score) and log conflict fatalities (ACLED, 6 months)
for the domain's districts. Standard errors clustered by region (admin-1), p-values from
a restricted wild cluster bootstrap (Webb weights, 1,999 draws).

Outputs: output/tables/som_uscut_*.csv, som_uscut_key.json, output/figures/som_uscut_*.pdf,
         input/panel/som_uscut_panel.parquet
"""
import difflib
import importlib.util
import json
import re
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
RNG = np.random.default_rng(20251013)
KEY = {}


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


F57 = load_module("f57", "57_fsnau_value.py")
T62 = load_module("t62", "62_tidy_3w.py")
SECTORS = {"nutrition", "health", "food_security", "wash"}
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"


def dist_key(p):
    """Collapse Banadir's 17 districts (reported separately from 2025) into SO22."""
    if not isinstance(p, str):
        return None
    return "SO22" if p.startswith("SO22") else p


# ------------------------------------------------------------------ donor shares
def agency_us_shares():
    """2023-24 US share of each UN agency's humanitarian funding in Somalia (FTS)."""
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet")
    f = f[f.dest_country.fillna("").str.contains("Somalia") & f.status.isin(["paid", "commitment"]) &
          ((f.boundary == "incoming") | f.boundary.isna()) & (f.amount_usd > 0)].copy()
    f["y"] = pd.to_datetime(f.decision_date, errors="coerce").dt.year
    f = f[f.y.between(2023, 2024)]
    f["us"] = f.donor.fillna("").str.startswith("United States")
    pats = {"unicef": "Children's Fund", "wfp": "World Food Programme", "unhcr": "High Commissioner for Refugees",
            "iom": "International Organization for Migration", "fao": "Food and Agriculture Organization",
            "unfpa": "Population Fund", "who": "World Health Organization"}
    out = {}
    for k, p in pats.items():
        s = f[f.recipient.fillna("").str.contains(p, regex=False)]
        out[k] = float(s[s.us].amount_usd.sum() / s.amount_usd.sum()) if len(s) else 0.0
    # money FTS reports US-to-Somalia overall, as context
    out["_all_somalia"] = float(f[f.us].amount_usd.sum() / f.amount_usd.sum())
    return out


def fts_change():
    """Humanitarian funding to Somalia by year, US vs other donors (FTS, by decision date)."""
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet")
    f = f[f.dest_country.fillna("").str.contains("Somalia") & f.status.isin(["paid", "commitment"]) &
          ((f.boundary == "incoming") | f.boundary.isna()) & (f.amount_usd > 0)].copy()
    f["y"] = pd.to_datetime(f.decision_date, errors="coerce").dt.year
    f["us"] = f.donor.fillna("").str.startswith("United States")
    t = f[f.y.between(2019, 2025)].groupby(["y", "us"]).amount_usd.sum().unstack().fillna(0) / 1e6
    t.columns = ["other_musd", "us_musd"]
    t.to_csv(TAB / "som_uscut_fts.csv")
    return {int(k): {c: round(float(v[c]), 1) for c in t.columns} for k, v in t.iterrows()}


US_RX = re.compile(r"usaid|\bbha\b|\bofda\b|\bffp\b|\bprm\b|united states|\bus ?gov|\busg\b|state department|"
                   r"\bu\.s\.?\b|\bus\b|american people|creative associate|pepfar|\bcdc\b|feed the future", re.I)
AGENCY_RX = {"unicef": r"unicef|children'?s fund", "wfp": r"\bwfp\b|world food", "unhcr": r"unhcr|refugee agency",
             "iom": r"\biom\b|organi[sz]ation for migration", "fao": r"\bfao\b|food and agriculture",
             "unfpa": r"unfpa|population fund", "who": r"\bwho\b|world health"}
NONUS_RX = re.compile(
    r"echo|\beu\b|european|fcdo|dfid|\buk\b|united kingdom|\bshf\b|humanitarian fund|cerf|central emergency|"
    r"world ?bank|\bwb\b|ida\b|sida|\bsdc\b|swiss|danida|denmark|nmfa|norad|norw|gffo|german|giz|kfw|bmz|"
    r"auswärtiges|irish|ireland|\bgac\b|canada|japan|jica|korea|koica|qatar|ksrelief|saudi|\buae\b|emirat|kuwait|"
    r"turk|tika|\becw\b|education cannot|\bgpe\b|global partnership|global fund|gavi|dutch|netherland|\bmfa\b|"
    r"ital|aics|france|afd\b|own fund|internal|self|volunteer|private|misereor|mieser|caritas|secours|"
    r"kindermission|\bdkh\b|forum ?civ|start fund|islamic relief|gates|ocha|\bsrcs\b|ifrc|\bicrc\b|"
    r"finland|sweden|swedish|austria|belgi|luxem|spain|aecid|australia|dfat|china|islamic development|"
    r"diakonie|bread for|tearfund|christian aid|cafod|trocaire|oxfam|government of somalia|\bfgs\b|"
    r"ministry|unocha|\bpbf\b|peacebuilding|unmptf|joint programme|mptf", re.I)


def classify_donor(text, ag):
    """US-funded share implied by a 3W donor field; None if uninformative."""
    if not isinstance(text, str):
        return None
    t = text.strip()
    if t in ("", "0", "nan", "-") or re.fullmatch(r"(?i)other|not in the list|n/?a|none|\(blank\)|ingo|nngo|un", t):
        return None
    toks = [x.strip() for x in re.split(r"[,/|;&+]| and |\n", t) if x.strip()]
    vals = []
    for x in toks:
        if US_RX.search(x):
            vals.append(1.0)
            continue
        hit = [k for k, p in AGENCY_RX.items() if re.search(p, x, re.I)]
        if hit:
            vals.append(ag[hit[0]])
        elif NONUS_RX.search(x):
            vals.append(0.0)
    if not vals:
        return None
    return float(np.mean(vals))


def read_donor_3w(path, sheet, header):
    d = pd.read_excel(path, sheet_name=sheet, header=header)
    cols = {c: re.sub(r"\s+", " ", str(c)).strip().lower() for c in d.columns}
    d = d.rename(columns=cols)
    pick = lambda *pats: next(c for c in d.columns if any(re.search(p, c) for p in pats))
    out = pd.DataFrame({
        "org": d[pick(r"^the name of your organisation|^organization name$")],
        "org_type": d[pick(r"^the type of your organisation|^organization type$")],
        "cluster_raw": d[pick(r"^cluster")],
        "donor": d[pick(r"donor")],
        "district": d[pick(r"^districtcode$|^district_pcode$")],
    })
    out["org"] = out.org.map(T62.clean_org)
    out["cluster"] = out.cluster_raw.map(T62.map_cluster)
    out["dist"] = out.district.astype(str).str.strip().where(out.district.notna()).map(dist_key)
    return out.dropna(subset=["org", "dist"])


def predicted_exposure(ag):
    base = AID / "hdx_3w" / "som" / "somalia-operational-presence"
    d24 = read_donor_3w(base / "Operational_Partners_Presence_Jan-Sep_2024.xlsx", "Data", 0)
    d23 = read_donor_3w(base / "3ws-2023-consolidated.xlsx", "DATA", 2)
    d24 = d24.iloc[1:] if str(d24.org.iloc[0]).startswith("#") else d24      # HXL tag row
    for d in (d23, d24):
        d["u"] = [classify_donor(x, ag) for x in d.donor]
    both = pd.concat([d23, d24])
    KEY["donor_rows_2024"] = int(len(d24))
    KEY["donor_informative_2024"] = float(d24.u.notna().mean())
    # organisation fallback: own average over 2023-24 rows with a usable donor
    org_u = both.dropna(subset=["u"]).groupby("org").u.mean()
    un_org = {k: ag[k] for k in ag if not k.startswith("_")}
    un_name = {"united nations childrens fund": "unicef", "world food programme": "wfp",
               "united nations high commissioner for refugees": "unhcr", "international organization for migration": "iom",
               "food and agriculture organization": "fao", "united nations population fund": "unfpa",
               "world health organization": "who"}
    typ = d24.groupby("org").org_type.agg(lambda s: s.dropna().astype(str).str.upper().str.strip().mode().iat[0]
                                          if s.notna().any() else "OTHER")
    d = d24[d24.cluster.isin(SECTORS)].copy()
    unit = d.groupby(["dist", "org", "cluster"]).u.mean().rename("u_rows").reset_index()
    unit["u_org"] = unit.org.map(org_u)
    unit["u_un"] = unit.org.map(un_name).map(un_org)
    unit["type"] = unit.org.map(typ).fillna("OTHER")
    unit["u"] = unit.u_rows.fillna(unit.u_org).fillna(unit.u_un)
    type_mean = unit.dropna(subset=["u"]).groupby("type").u.mean()
    unit["imputed"] = unit.u.isna()
    unit["u"] = unit.u.fillna(unit.type.map(type_mean)).fillna(unit.u.mean())
    KEY["units_2024"] = int(len(unit))
    KEY["units_imputed_share"] = float(unit.imputed.mean())
    KEY["unit_u_mean"] = float(unit.u.mean())
    E = unit.groupby("dist").agg(E_pred=("u", "mean"), E_pred_obs=("u", lambda s: np.nan), n_units24=("u", "size"))
    E["E_pred_obs"] = unit[~unit.imputed].groupby("dist").u.mean()     # robustness: no imputation
    E["us_units24"] = unit.groupby("dist").u.sum()
    unit.to_csv(TAB / "som_uscut_units2024.csv", index=False)
    return E, unit


def partner_loss(unit):
    o = pd.read_parquet(AID / "tidy" / "org_presence_som.parquet")
    o = o[(o.period_type == "month") & o.cluster.isin(SECTORS)].copy()
    o["dist"] = o.admin2_pcode.map(dist_key)
    o["y"], o["m"] = o.period_start.dt.year, o.period_start.dt.month
    o = o[o.m.between(4, 10) & o.y.isin([2024, 2025]) & o.dist.notna()]
    mon = o.groupby(["dist", "y", "m"]).apply(lambda s: s[["org", "cluster"]].drop_duplicates().shape[0])
    avg = mon.groupby(["dist", "y"]).mean().unstack()
    L = pd.DataFrame({"partners24": avg[2024], "partners25": avg[2025]})
    L["E_loss"] = 1 - L.partners25.fillna(0) / L.partners24
    L.loc[L.partners24.isna(), "E_loss"] = np.nan
    # do US-funded units disappear more? (unit = org x sector x district, any month Apr-Oct)
    # spelling variants across the 2024 and 2025 files (e.g. 'lable'/'label'): map a 2025 name to the
    # closest 2024 name when very similar
    n24 = sorted(set(o[o.y == 2024].org))
    ren = {}
    for nm in set(o[o.y == 2025].org) - set(n24):
        c = difflib.get_close_matches(nm, n24, n=1, cutoff=0.9)
        if c:
            ren[nm] = c[0]
    o["org"] = o.org.replace(ren)
    KEY["org_renames_2025"] = len(ren)
    p25 = set(map(tuple, o[o.y == 2025][["dist", "org", "cluster"]].drop_duplicates().values))
    p24 = o[o.y == 2024][["dist", "org", "cluster"]].drop_duplicates()
    p24 = p24.merge(unit[["dist", "org", "cluster", "u"]], on=["dist", "org", "cluster"], how="left")
    p24["stay"] = [tuple(r) in p25 for r in p24[["dist", "org", "cluster"]].values]
    p24["grp"] = pd.cut(p24.u, [-0.01, 0.1, 0.5, 1.01], labels=["<10% US", "10-50% US", ">50% US"])
    st = p24.groupby("grp", dropna=False).stay.agg(["mean", "size"])
    st.to_csv(TAB / "som_uscut_unit_survival.csv")
    KEY["unit_survival"] = {str(k): [round(float(v["mean"]), 3), int(v["size"])] for k, v in st.iterrows()}
    return L


# ------------------------------------------------------------------ survey panel
TOWNS = [  # pattern -> district P-code (Banadir collapsed)
    (r"mogadishu|banadir|daynil|dharken|hamar|waberi|madina|wadajir", "SO22"), (r"baidoa|baydhab", "SO2401"),
    (r"bos+a+so", "SO1601"), (r"dh?u+s+a?m+a?r+e+b|guri ?e?l", "SO1901"), (r"dol+o+w|dowlo", "SO2605"),
    (r"galk?a?h?c?a?yo|galcayo|galkahyo", "SO1801"), (r"garowe|nugal|nugaal", "SO1701"),
    (r"kismay|l\. juba", "SO2801"), (r"hargeisa|w\.? ?galbeed|woq|galbeed", "SO1201"), (r"burao|togh?dheer", "SO1301"),
    (r"berbera", "SO1202"), (r"qardho|gardo", "SO1606"), (r"belet ?w|beled ?w|beletyw", "SO2001"),
    (r"dho?bley|dobley", "SO2802"), (r"las ?anod|lasanood|sool", "SO1401"), (r"afgoye", "SO2302"),
    (r"bardera|bardheer", "SO2602"), (r"afmadow", "SO2802"), (r"abudwaq", "SO1902"), (r"buale", "SO2701"),
    (r"jowhar", "SO2101"), (r"wajid", "SO2504"), (r"hudd?ur|xuddur", "SO2501"), (r"elberde", "SO2502"),
    (r"erigavo|sanaag", "SO1501"), (r"bor[ao]ma|awdal|adwal", "SO1101"), (r"\bbari\b", "SO1601"),
    (r"mudug", "SO1801"), (r"galgad", "SO1901"), (r"mataban", "SO2001"), (r"qoryol", "SO2305"),
    (r"sak[o]+w", "SO2703"), (r"togwajale", "SO1203"), (r"luuq", "SO2606"), (r"belet hawa", "SO2603"),
    (r"bulo ?burt|buloburti", "SO2002"), (r"dinsor", "SO2403"), (r"jalaq?l?a?qsi", "SO2003"),
    (r"jamame", "SO2804"), (r"haradhere", "SO1805"), (r"eldhere", "SO1905"), (r"qanshadhere", "SO2404"),
    (r"teiglow", "SO2503"), (r"margaga", "SO2101"),
]


def town_district(name):
    n = name.lower()
    for p, code in TOWNS:
        if re.search(p, n):
            return code
    return None


def town_domain(r):
    code = town_district(r.population_group)
    if code is None:
        return None, None
    t = "IDP" if r.population_type == "IDP" else "urban"     # 'mixed' urban+IDP town surveys count as urban
    return f"{t}|{code}", code


def survey_panel():
    s = pd.read_csv(INP / "fsnau" / "surveys.csv")
    s = s[(s.method == "SMART") & s.gam.notna()].copy()
    s = s[~s.population_group.str.contains(r"\b(ACF|SCI|CARE|INTERSOS|EPHCO|Concern)\b|\(SCI\)|Wordwide", regex=True)]
    s = s[~s.population_group.str.fullmatch(r"(?i)median|mean|average")]
    U = F57.units()
    fx = pd.read_csv(AID / "tidy" / "fews_admin2_som.csv")
    f2d = dict(zip(fx.fnid, fx.admin2_pcode.map(dist_key)))
    pop = pd.read_parquet(INP / "panel" / "fnid_population.parquet").set_index("fnid")["pop"]
    rows = []
    for i, r in s.iterrows():
        if r.population_type == "rural":
            x = F57.rule(r.population_group, r.region)
            if x is None:
                continue
            ids = F57.match(U, *x[:3])
            if not ids:
                continue
            w = pd.Series({f: pop.get(f, np.nan) for f in ids}).fillna(1.0)
            d = pd.Series([f2d.get(f) for f in w.index], index=w.index)
            dw = w.groupby(d.values).sum()
            rows.append(dict(idx=i, domain=f"rural|{x[3]}", dists=json.dumps((dw / dw.sum()).round(4).to_dict()),
                             fnids=";".join(sorted(ids))))
        else:
            dom, code = town_domain(r)
            if dom is None:
                continue
            ids = fx[fx.admin2_pcode.map(dist_key) == code].fnid.tolist()
            rows.append(dict(idx=i, domain=dom, dists=json.dumps({code: 1.0}), fnids=";".join(ids)))
    cw = pd.DataFrame(rows).set_index("idx")
    s = s.join(cw, how="inner")
    s["month"] = [F57.target_month(r) for r in s.itertuples()]
    s["ptype"] = s.domain.str.split("|").str[0]
    s["season_id"] = s.season_type + " " + s.season_year.astype(int).astype(str)
    s["year"] = s.season_year.astype(int)
    s["post"] = (s.year >= 2025).astype(int)
    # several surveys of one domain in one season (e.g. two Mogadishu urban samples): average
    num = ["gam", "sam", "muac_gam", "muac_sam", "cdr", "u5dr", "stunting", "underweight", "morbidity", "measles",
           "vita"]
    keep = ["domain", "ptype", "season_id", "season_type", "year", "post", "dists", "fnids"]
    p = s.groupby(keep, as_index=False).agg({**{c: "mean" for c in num}, "month": "first",
                                             "population_group": "first"})
    return p


def add_controls(p):
    rain = pd.read_parquet(INP / "panel" / "fnid_rain_monthly.parquet")
    rain = rain[rain.index.str.startswith("SO")]
    cols = list(rain.columns)
    ac = pd.read_excel(INP / "acled" / "hdx" / "som.xlsx", sheet_name="Data")
    ac["dist"] = ac["Admin2 Pcode"].map(dist_key)
    mnum = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"], 1)}
    ac["t"] = pd.PeriodIndex([f"{y}-{mnum.get(m, m) if not str(m).isdigit() else int(m):02d}"
                              for y, m in zip(ac.Year, ac.Month)], freq="M")
    acm = ac.groupby(["dist", "t"]).Fatalities.sum()
    rz, fat = [], []
    for r in p.itertuples():
        ids = [f for f in r.fnids.split(";") if f in rain.index]
        end = str(r.month)
        if ids and end in cols:
            j = cols.index(end)
            win = rain.loc[ids, cols[j - 5:j + 1]].sum(axis=1)
            clim = []
            for yy in range(1991, 2021):
                e = f"{yy}-{end[5:]}"
                if e in cols:
                    k = cols.index(e)
                    clim.append(rain.loc[ids, cols[k - 5:k + 1]].sum(axis=1))
            C = pd.concat(clim, axis=1)
            z = ((win - C.mean(axis=1)) / C.std(axis=1).replace(0, np.nan)).mean()
            rz.append(z)
        else:
            rz.append(np.nan)
        dw = json.loads(r.dists)
        tot = 0.0
        for d, w in dw.items():
            if d is None or d == "null":
                continue
            s = acm.get(d)
            if s is not None:
                tot += w * s[(s.index > r.month - 6) & (s.index <= r.month)].sum()
        fat.append(np.log1p(tot))
    p["rain_z"], p["log_fat"] = rz, fat
    p["rain_z"] = p.rain_z.fillna(p.rain_z.mean())
    return p


def domain_exposure(p, E, L):
    out = []
    for r in p.drop_duplicates("domain").itertuples():
        dw = {k: v for k, v in json.loads(r.dists).items() if k not in (None, "null")}
        w = pd.Series(dw)
        rec = {"domain": r.domain}
        for c, src in [("E_pred", E.E_pred), ("E_pred_obs", E.E_pred_obs), ("E_loss", L.E_loss)]:
            v = src.reindex(w.index)
            ok = v.notna()
            rec[c] = float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan
        reg = pd.Series({d[:4]: 0.0 for d in w.index})
        for d, x in w.items():
            reg[d[:4]] += x
        rec["region"] = reg.idxmax()
        out.append(rec)
    return p.merge(pd.DataFrame(out), on="domain")


# ------------------------------------------------------------------ estimation
def design(d, exp, y, controls=True, event=False, extra=None):
    d = d.dropna(subset=[y, exp] + (extra or [])).copy()
    X = pd.get_dummies(d.domain, prefix="d", drop_first=True, dtype=float)
    X = X.join(pd.get_dummies(d.ptype + ":" + d.season_id, prefix="t", drop_first=True, dtype=float))
    names = []
    if event:
        for yr in sorted(d.year.unique()):
            if yr == 2024:
                continue
            X[f"ev{yr}"] = d[exp] * (d.year == yr)
            names.append(f"ev{yr}")
    else:
        X["treat"] = d[exp] * d.post
        names.append("treat")
    if controls:
        X["rain_z"], X["log_fat"] = d.rain_z, d.log_fat
    for c in extra or []:
        X[c] = d[c]
    X.insert(0, "const", 1.0)
    X = X.loc[:, X.std() > 0].assign(const=1.0)
    return d, X, d[y].values, names


def ols_cl(X, y, g):
    Xv = X.values
    XtX = np.linalg.pinv(Xv.T @ Xv)
    b = XtX @ Xv.T @ y
    e = y - Xv @ b
    G = len(np.unique(g))
    n, k = Xv.shape
    meat = np.zeros((k, k))
    for gg in np.unique(g):
        s = Xv[g == gg].T @ e[g == gg]
        meat += np.outer(s, s)
    V = XtX @ meat @ XtX * G / (G - 1) * (n - 1) / (n - k)
    return b, np.sqrt(np.diag(V)), e


def wild_p(X, y, g, col, B=1999):
    """Restricted wild cluster bootstrap p-value (Webb six-point weights)."""
    j = list(X.columns).index(col)
    b, se, _ = ols_cl(X, y, g)
    t0 = b[j] / se[j]
    Xr = X.drop(columns=col)
    br = np.linalg.lstsq(Xr.values, y, rcond=None)[0]
    fit, er = Xr.values @ br, y - Xr.values @ br
    groups = np.unique(g)
    gi = np.searchsorted(groups, g)
    W = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    Xv = X.values
    XtX = np.linalg.pinv(Xv.T @ Xv)
    n, k = Xv.shape
    G = len(groups)
    ts = []
    for _ in range(B):
        w = RNG.choice(W, G)[gi]
        ys = fit + w * er
        bs = XtX @ Xv.T @ ys
        es = ys - Xv @ bs
        sc = np.zeros(k)
        meat = 0.0
        # only the variance of coefficient j is needed
        a = XtX[j]
        for q in range(G):
            m = gi == q
            v = a @ (Xv[m].T @ es[m])
            meat += v * v
        sej = np.sqrt(meat * G / (G - 1) * (n - 1) / (n - k))
        ts.append(bs[j] / sej)
    return float(np.mean(np.abs(ts) >= abs(t0)))


def pretrend_p(d0, exp, y, B=999):
    """Wild cluster bootstrap p-value for the joint null that all pre-2024 event-study terms are zero
    (Wald statistic with cluster-robust variance)."""
    d, X, yy, names = design(d0, exp, y, event=True)
    pre = [n for n in names if int(n[2:]) < 2024 and n in X.columns]
    g = d.region.values
    groups = np.unique(g)
    gi = np.searchsorted(groups, g)
    Xv = X.values
    XtX = np.linalg.pinv(Xv.T @ Xv)
    idx = [list(X.columns).index(n) for n in pre]
    n, k = Xv.shape
    G = len(groups)

    def wald(yv):
        b = XtX @ Xv.T @ yv
        e = yv - Xv @ b
        A = XtX[idx]
        S = np.array([A @ (Xv[gi == q].T @ e[gi == q]) for q in range(G)])
        V = S.T @ S * G / (G - 1) * (n - 1) / (n - k)
        bb = b[idx]
        return float(bb @ np.linalg.pinv(V) @ bb)
    w0 = wald(yy)
    Xr = X.drop(columns=pre).values
    br = np.linalg.lstsq(Xr, yy, rcond=None)[0]
    fitr, er = Xr @ br, yy - Xr @ br
    W = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    ws = [wald(fitr + RNG.choice(W, G)[gi] * er) for _ in range(B)]
    return float(np.mean(np.array(ws) >= w0))


def fit(d0, exp, y, **kw):
    boot = kw.pop("boot", True)
    d, X, yy, names = design(d0, exp, y, **kw)
    g = d.region.values
    b, se, _ = ols_cl(X, yy, g)
    cols = list(X.columns)
    res = {}
    for nm in names:
        if nm in cols:
            j = cols.index(nm)
            res[nm] = dict(b=b[j], se=se[j])
    if boot and "treat" in res:
        res["treat"]["p_wild"] = wild_p(X, yy, g, "treat")
    return res, d


def main():
    ag = agency_us_shares()
    KEY["agency_us_share"] = {k: round(v, 3) for k, v in ag.items()}
    KEY["fts_somalia"] = fts_change()
    E, unit = predicted_exposure(ag)
    L = partner_loss(unit)
    D = E.join(L, how="outer")
    D.to_csv(TAB / "som_uscut_districts.csv")
    KEY["districts"] = int(D.E_pred.notna().sum())
    KEY["E_pred_dist"] = D.E_pred.describe().round(3).to_dict()
    KEY["E_loss_dist"] = D.E_loss.describe().round(3).to_dict()
    KEY["partners_total"] = {"2024": float(L.partners24.sum()), "2025": float(L.partners25.sum())}
    m = D.dropna(subset=["E_pred", "E_loss"])
    KEY["corr_pred_loss_dist"] = float(m.E_pred.corr(m.E_loss))
    # first stage at district level: predicted reliance -> partner loss
    xs = np.column_stack([np.ones(len(m)), m.E_pred])
    bfs = np.linalg.lstsq(xs, m.E_loss.values, rcond=None)[0]
    KEY["first_stage_slope"] = float(bfs[1])

    p = survey_panel()
    p = add_controls(p)
    p = domain_exposure(p, E, L)
    p = p[p.year >= 2015]
    p.drop(columns=["dists"]).to_parquet(INP / "panel" / "som_uscut_panel.parquet", index=False)
    KEY["panel_rows"] = int(len(p))
    KEY["domains"] = int(p.domain.nunique())
    KEY["post_rows"] = int(p.post.sum())
    KEY["post_domains"] = int(p[p.post == 1].domain.nunique())
    KEY["regions"] = int(p.region.nunique())
    KEY["domains_by_type"] = p.drop_duplicates("domain").ptype.value_counts().to_dict()
    dom = p.drop_duplicates("domain")
    KEY["corr_pred_loss_domain"] = float(dom.E_pred.corr(dom.E_loss))
    for c in ["E_pred", "E_loss"]:
        KEY[f"{c}_sd_domain"] = float(dom[c].std())
        KEY[f"{c}_domain"] = dom[c].describe().round(3).to_dict()

    # main results
    rows = []
    outcomes = ["gam", "sam", "muac_gam", "muac_sam", "stunting", "underweight", "morbidity", "cdr", "u5dr",
                "measles", "vita"]
    for exp in ["E_pred", "E_loss"]:
        for y in outcomes:
            r, d = fit(p, exp, y)
            sd = d.drop_duplicates("domain")[exp].std()
            rows.append(dict(exposure=exp, outcome=y, spec="main", b=r["treat"]["b"], se=r["treat"]["se"],
                             p_wild=r["treat"]["p_wild"], n=len(d), domains=d.domain.nunique(),
                             post_n=int(d.post.sum()), sd_exp=sd, ymean_pre=d[d.post == 0][y].mean()))
    # robustness for GAM
    base = p[(p.year.between(2019, 2024))].groupby("domain").gam.mean().rename("gam_base")
    pb = p.join(base, on="domain")
    pb["base_x_post"] = pb.gam_base * pb.post
    for exp in ["E_pred", "E_loss"]:
        specs = [
            ("no controls", p, dict(controls=False)),
            ("baseline GAM x post", pb, dict(extra=["base_x_post"])),
            ("rural only", p[p.ptype == "rural"], {}),
            ("towns only (IDP+urban)", p[p.ptype != "rural"], {}),
            ("drop Banadir", p[~p.domain.str.endswith("SO22")], {}),
            ("since 2019", p[p.year >= 2019], {}),
        ]
        if exp == "E_pred":
            specs.append(("no imputed donors", p.assign(E_pred=p.E_pred_obs), {}))
        for lab, dd, kw in specs:
            r, d = fit(dd, exp, "gam", **kw)
            rows.append(dict(exposure=exp, outcome="gam", spec=lab, b=r["treat"]["b"], se=r["treat"]["se"],
                             p_wild=r["treat"]["p_wild"], n=len(d), domains=d.domain.nunique(),
                             post_n=int(d.post.sum()), sd_exp=d.drop_duplicates("domain")[exp].std(),
                             ymean_pre=d[d.post == 0].gam.mean()))
    R = pd.DataFrame(rows)
    R["b_per10pp"] = R.b * 0.1
    R["b_per_sd"] = R.b * R.sd_exp
    R.to_csv(TAB / "som_uscut_results.csv", index=False)
    KEY["results"] = R.round(4).to_dict("records")

    # event studies
    ev = []
    for exp in ["E_pred", "E_loss"]:
        for y in ["gam", "cdr"]:
            r, d = fit(p, exp, y, event=True, boot=False)
            for k, v in r.items():
                ev.append(dict(exposure=exp, outcome=y, year=int(k[2:]), b=v["b"], se=v["se"]))
            KEY[f"pretrend_p_{exp}_{y}"] = pretrend_p(p, exp, y)
    EV = pd.DataFrame(ev)
    EV.to_csv(TAB / "som_uscut_event.csv", index=False)

    # high vs low exposure raw means (median split of predicted reliance)
    med = dom.E_pred.median()
    p["high"] = p.E_pred > med
    raw = p.groupby(["year", "high"]).gam.mean().unstack()
    raw.to_csv(TAB / "som_uscut_raw_means.csv")
    KEY["median_E_pred"] = float(med)
    KEY["raw_change_24_25"] = {"high": float(raw.loc[2025, True] - raw.loc[2024, True]),
                               "low": float(raw.loc[2025, False] - raw.loc[2024, False])}
    KEY["raw_change_pre_25"] = {
        "high": float(raw.loc[2025, True] - raw.loc[2019:2024, True].mean()),
        "low": float(raw.loc[2025, False] - raw.loc[2019:2024, False].mean())}

    NS = national_shortfall(p)
    print(NS.round(2).to_string())
    figures(p, EV, raw, D, dom)
    (TAB / "som_uscut_key.json").write_text(json.dumps(KEY, indent=1, default=float))
    write_numbers(R)
    pd.set_option("display.width", 220, "display.max_rows", 100)
    print(json.dumps({k: v for k, v in KEY.items() if k != "results"}, indent=1, default=float))
    print(R[["exposure", "outcome", "spec", "b_per10pp", "se", "p_wild", "n", "domains", "post_n", "sd_exp",
             "ymean_pre"]].round(3).to_string())
    print(EV.round(2).to_string())


def national_shortfall(p):
    """Countrywide: is 2025 worse than rainfall and conflict predict? For each year 2017-2025, fit
    GAM ~ domain FE + season-type FE + linear trend + rain + conflict on all OTHER pre-2025 years and
    take the mean prediction error in the held-out year. 2025's error is compared with the
    distribution of errors in 2017-2024 (a placebo-in-time check, descriptive only)."""
    d = p.dropna(subset=["gam"]).copy()
    d["trend"] = d.year - 2015
    d["deyr"] = (d.season_type == "Deyr").astype(float)
    out = []
    for yr in range(2017, 2026):
        tr = d[(d.year != yr) & (d.year < 2025)]
        te = d[(d.year == yr) & d.domain.isin(tr.domain)]
        def X(z):
            m = pd.get_dummies(z.domain, dtype=float).reindex(columns=sorted(tr.domain.unique()), fill_value=0.0)
            return np.column_stack([m.values, z[["deyr", "trend", "rain_z", "log_fat"]].values])
        b = np.linalg.lstsq(X(tr), tr.gam.values, rcond=None)[0]
        err = te.gam.values - X(te) @ b
        out.append(dict(year=yr, err=float(err.mean()), n=len(te)))
    S = pd.DataFrame(out)
    S.to_csv(TAB / "som_uscut_national.csv", index=False)
    pre = S[S.year < 2025].err
    KEY["national_err_2025"] = float(S[S.year == 2025].err.iloc[0])
    KEY["national_err_pre_sd"] = float(pre.std())
    KEY["national_err_pre_maxabs"] = float(pre.abs().max())
    KEY["national_err_rank"] = int((pre.abs() >= abs(KEY["national_err_2025"])).sum())
    return S


def write_numbers(R):
    """LaTeX macros for output/us_cut_memo/us_cut_memo.tex (every number in the memo comes from here)."""
    K, M = KEY, {}
    f0 = lambda x: f"{x:,.0f}"
    f1 = lambda x: f"{x:.1f}"
    f2 = lambda x: f"{x:.2f}"
    pc = lambda x: f"{100 * x:.0f}"
    M["Domains"], M["Rows"], M["PostRows"], M["PostDomains"] = K["domains"], K["panel_rows"], K["post_rows"], K["post_domains"]
    M["Regions"] = K["regions"]
    for t in ["rural", "IDP", "urban"]:
        M[f"Dom{t.capitalize() if t != 'IDP' else 'Idp'}"] = K["domains_by_type"].get(t, 0)
    fts = K["fts_somalia"]
    M["UsTwentyFour"], M["UsTwentyFive"] = f0(fts[2024]["us_musd"]), f0(fts[2025]["us_musd"])
    M["OtherTwentyFour"], M["OtherTwentyFive"] = f0(fts[2024]["other_musd"]), f0(fts[2025]["other_musd"])
    M["UsDrop"] = pc(1 - fts[2025]["us_musd"] / fts[2024]["us_musd"])
    M["OtherDrop"] = pc(1 - fts[2025]["other_musd"] / fts[2024]["other_musd"])
    ag = K["agency_us_share"]
    M["WfpUs"], M["UnicefUs"], M["UnhcrUs"] = pc(ag["wfp"]), pc(ag["unicef"]), pc(ag["unhcr"])
    M["DonorRows"], M["DonorInfo"] = f0(K["donor_rows_2024"]), pc(K["donor_informative_2024"])
    M["Units"], M["UnitsImputed"], M["UnitU"] = f0(K["units_2024"]), pc(K["units_imputed_share"]), pc(K["unit_u_mean"])
    M["Districts"] = K["districts"]
    M["EpredMin"], M["EpredMax"] = pc(K["E_pred_dist"]["min"]), pc(K["E_pred_dist"]["max"])
    M["EpredQone"], M["EpredQthree"] = pc(K["E_pred_domain"]["25%"]), pc(K["E_pred_domain"]["75%"])
    M["EpredSd"], M["ElossSd"] = pc(K["E_pred_sd_domain"]), pc(K["E_loss_sd_domain"])
    M["PartnersTwentyFour"], M["PartnersTwentyFive"] = f0(K["partners_total"]["2024"]), f0(K["partners_total"]["2025"])
    M["PartnersDrop"] = pc(1 - K["partners_total"]["2025"] / K["partners_total"]["2024"])
    M["ElossMed"] = pc(K["E_loss_dist"]["50%"])
    M["SurvHigh"], M["SurvLow"] = pc(K["unit_survival"][">50% US"][0]), pc(K["unit_survival"]["<10% US"][0])
    M["CorrPredLoss"] = f2(K["corr_pred_loss_dist"])
    M["PreP"], M["PrePLoss"] = f2(K["pretrend_p_E_pred_gam"]), f2(K["pretrend_p_E_loss_gam"])
    M["RawHigh"], M["RawLow"] = f1(K["raw_change_24_25"]["high"]), f1(K["raw_change_24_25"]["low"])
    M["NatErr"], M["NatSd"] = f1(K["national_err_2025"]), f1(K["national_err_pre_sd"])
    M["NatMax"], M["NatRank"] = f1(K["national_err_pre_maxabs"]), K["national_err_rank"]
    names = {"main": "", "no controls": "NoCtl", "baseline GAM x post": "Base", "rural only": "Rural",
             "towns only (IDP+urban)": "Towns", "drop Banadir": "NoBan", "since 2019": "Since",
             "no imputed donors": "NoImp"}
    outn = {"gam": "Gam", "sam": "Sam", "muac_gam": "Muac", "muac_sam": "MuacSam", "stunting": "Stunt",
            "underweight": "Uwt", "morbidity": "Morb", "cdr": "Cdr", "u5dr": "Ufive", "measles": "Meas", "vita": "Vita"}
    for r in R.itertuples():
        tag = ("Pred" if r.exposure == "E_pred" else "Loss") + outn[r.outcome] + names[r.spec]
        M[f"b{tag}"], M[f"se{tag}"], M[f"p{tag}"] = f2(r.b_per10pp), f2(r.se * 0.1), f2(r.p_wild)
        if r.spec == "main":
            M[f"n{tag}"], M[f"post{tag}"], M[f"ym{tag}"] = f0(r.n), f0(r.post_n), f1(r.ymean_pre)
        if r.spec == "main" and r.outcome == "gam":
            M[f"lo{tag}"], M[f"hi{tag}"] = f2(r.b_per10pp - 1.96 * r.se * 0.1), f2(r.b_per10pp + 1.96 * r.se * 0.1)
            M[f"mde{tag}"] = f1(2.8 * r.se * 0.1)
            M[f"Ymean{tag}"] = f1(r.ymean_pre)
            iqr = (K["E_pred_domain"]["75%"] - K["E_pred_domain"]["25%"]) if r.exposure == "E_pred" else \
                (K["E_loss_domain"]["75%"] - K["E_loss_domain"]["25%"])
            M[f"iqr{tag}"] = pc(iqr)
            M[f"biqr{tag}"], M[f"hiiqr{tag}"] = f1(r.b * iqr), f1((r.b + 1.96 * r.se) * iqr)
    out = ROOT / "output" / "us_cut_memo"
    out.mkdir(parents=True, exist_ok=True)
    (out / "numbers.tex").write_text("% generated by code/68_somalia_us_cut.py -- do not edit\n" +
                                     "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))


def figures(p, EV, raw, D, dom):
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    # 1. raw means
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    ax.plot(raw.index, raw[True], color=ORANGE, marker="o", ms=4, label="More reliant on US-funded partners")
    ax.plot(raw.index, raw[False], color=BLUE, marker="o", ms=4, label="Less reliant")
    ax.axvspan(2024.5, 2025.5, color=GREY, alpha=0.12, lw=0)
    ax.set_ylabel("Child wasting (GAM, %)")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_xticks(range(2015, 2026, 2))
    fig.tight_layout()
    fig.savefig(FIG / "som_uscut_raw.pdf")
    plt.close(fig)
    # 2. event study, GAM, both exposures (per 10pp)
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2), sharey=True)
    for ax, (exp, lab, col) in zip(axes, [("E_pred", "Predicted reliance (2024 donors)", ORANGE),
                                          ("E_loss", "Actual partner loss (2024 to 2025)", GREEN)]):
        e = EV[(EV.exposure == exp) & (EV.outcome == "gam")].sort_values("year")
        e = pd.concat([e, pd.DataFrame([dict(year=2024, b=0, se=0)])]).sort_values("year")
        ax.axhline(0, color=GREY, lw=0.8)
        ax.errorbar(e.year, e.b * 0.1, yerr=1.96 * e.se * 0.1, fmt="o", color=col, ms=4, capsize=0, lw=1.2)
        ax.axvline(2024.5, color=GREY, ls=":", lw=0.8)
        ax.set_title(lab, fontsize=9.5)
        ax.set_xticks(range(2015, 2026, 2))
    axes[0].set_ylabel("GAM points per 10pp exposure")
    fig.tight_layout()
    fig.savefig(FIG / "som_uscut_event.pdf")
    plt.close(fig)
    # 3. predicted reliance vs actual loss, districts
    m = D.dropna(subset=["E_pred", "E_loss"])
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.scatter(m.E_pred * 100, m.E_loss * 100, s=np.clip(m.n_units24, 5, 120), color=BLUE, alpha=0.55, lw=0)
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xlabel("US-funded share of 2024 partners (%)")
    ax.set_ylabel("Partners lost, 2024 to 2025 (%)")
    fig.tight_layout()
    fig.savefig(FIG / "som_uscut_firststage.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
