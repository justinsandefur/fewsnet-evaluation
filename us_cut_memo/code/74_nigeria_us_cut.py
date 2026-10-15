"""Nigeria: did outcomes worsen more where aid partners relied on US money, or where partners left?

Outcomes (zone x year). UNICEF/National Bureau of Statistics nutrition surveillance, fielded every
August-September on fixed zones (SMART+ platform, input/smartplus): NFSS in the north-east
(10 zones of Borno, Yobe, Adamawa; rounds 2023-2026) and SOKAZA in the north-west (Sokoto,
Katsina, Zamfara; 2024-2026). GAM, SAM, MUAC GAM, stunting, underweight; CDR and U5DR from the
mortality module. Post = 2025 and 2026 (surveys 7-8 and 19-20 months after the cut).
Zones are defined as LGA lists in the IPC acute malnutrition tables (HDX, 2024-2026 files).

Exposure (north-east only; the OCHA 3W covers the humanitarian-response states):
  us_share   US-funded share of 2024 partner presence (nutrition, health, food security, WASH),
             April-June 2024. Organisations are US-funded if they held a USAID/State award with
             place of performance Nigeria active in FY2023-25 (USAspending; recipients are named in
             Nigeria, unlike Somalia); UN agencies take their 2023-24 FTS US share in Nigeria.
  loss       partner loss, April-June 2025 vs April-June 2024 (the Jul-Sep 2025 3W file repeats
             Apr-Jun with relabelled months, so only Apr-Jun is used)
  density    2024 partners per 100,000 children under five
Zone values: weighted by children under five across the zone's LGAs.
North-east vs north-west is a second, coarser contrast in aid dependence.

Food insecurity (LGA x round): Cadre Harmonise Phase 3+ share, March and November rounds
2019-2025 (Nov 2025 is the first round fully after the cut). Same exposures, LGA level.

Inference: few clusters (10 north-east zones; ~65 LGAs). Zone-level: wild cluster bootstrap by
zone. LGA level: clustered by LGA. First stage: LGA level.

Outputs: output/tables/nga_*.csv, nga_key.json, output/figures/nga_*.pdf,
         output/us_cut_memo/numbers_nga.tex
"""
import difflib
import importlib.util
import json
import re
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
W3 = INP / "subnational_aid" / "hdx_3w" / "nga" / "nigeria-3w"
AMN = INP / "subnational_aid" / "hdx_response" / "nga" / "nigeria-acute-malnutrition-data"
KEY, M = {}, {}
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"
RNG = np.random.default_rng(7)
SECT = {"nutrition": r"^nut", "health": r"^hea", "food_security": r"^(fsc|food)", "wash": r"^(wash|water)"}


def nrm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def zone_key(s):
    """'Southern\\nAdamawa', 'NFSS_..._South_Borno', 'Centarl Yobe', 'KEBBI CENTRAL 1' -> 'south|adamawa|'."""
    t = str(s).lower().replace("\n", " ").replace("_", " ").replace("-", " ")
    t = t.replace("centarl", "central").replace("mmc & jere", "mmc jere").replace("mmc and jere", "mmc jere")
    state = next((x for x in ["borno", "yobe", "adamawa", "sokoto", "katsina", "zamfara", "jigawa", "kebbi", "kaduna",
                              "benue", "niger"] if x in t), "")
    if "mmc" in t or "jere" in t and "kebbi" not in t:
        return "mmc|borno|"
    d = next((v for k, v in [("north", "north"), ("south", "south"), ("east", "east"), ("west", "west"),
                             ("central", "central")] if re.search(rf"\b{k}", t)), "")
    num = re.findall(r"\b([1-3])\b", t)
    return f"{d}|{state}|{num[-1] if num else ''}"


# ------------------------------------------------------------------ zones and LGAs
def zones():
    rows = []
    for f, sheets in [("Nigerian_Acute_Malnutrition_2024.xlsx", ["North West Nigeria", "North East Nigeria"]),
                      ("Nigerian_Acute_Malnutrition_2025.xlsx", ["NORTH-WEST NIGERIA", "NORTH-EAST NIGERIA"])]:
        for sh in sheets:
            v = pd.read_excel(AMN / f, sheet_name=sh, header=None)
            hr = next(i for i in range(6) if str(v.iloc[i, 0]).strip() in ("Zone", "Domain"))
            for r in v.iloc[hr + 1:].itertuples(index=False):
                z, lga, u5 = r[0], r[1], r[2]
                if not isinstance(z, str) or z.startswith("#") or not isinstance(lga, str):
                    continue
                if re.search(r"total", z, re.I):
                    continue
                rows.append(dict(src=f[-9:-5], region="NE" if "EAST" in sh.upper() else "NW", zone_raw=z.strip(),
                                 lga=re.sub(r"[*\n]", "", lga).strip(), u5=pd.to_numeric(u5, errors="coerce")))
    Z = pd.DataFrame(rows)
    Z["state"] = Z.zone_raw.map(lambda s: zone_key(s).split("|")[1])
    Z["zone"] = Z.zone_raw.map(zone_key)
    # zone keys whose state is missing (e.g. 'Northern Borno' always has it) -- keep
    Z["lga_key"] = Z.state + "|" + Z.lga.map(nrm)
    Z = Z.sort_values("src").drop_duplicates("lga_key", keep="last")   # 2025 definition wins
    return Z


# ------------------------------------------------------------------ outcomes
def surveys():
    A = pd.DataFrame(json.loads((INP / "smartplus" / "anthropometry.json").read_text())["surveys"])
    Mo = pd.DataFrame(json.loads((INP / "smartplus" / "mortality.json").read_text())["surveys"])
    A = A[(A.countryCode == "NG") & A.surveyName.str.contains(r"NFSS|SOKAZA", case=False, na=False)].copy()

    def g(k, *path):
        try:
            for p in path:
                k = k[p]
            return 100 * float(k)
        except (KeyError, TypeError):
            return np.nan
    A["gam"] = A.keystats.map(lambda k: g(k, "gam", "whz", "all", "prop"))
    A["sam"] = A.keystats.map(lambda k: g(k, "sam", "whz", "all", "prop"))
    A["muac_gam"] = A.keystats.map(lambda k: g(k, "gam", "muac", "all", "prop"))
    A["stunting"] = A.keystats.map(lambda k: g(k, "stunting", "global", "all", "prop"))
    A["underweight"] = A.keystats.map(lambda k: g(k, "underweight", "global", "all", "prop"))
    mo = Mo.set_index("id").keystats
    A["cdr"] = A.id.map(lambda i: mo.get(i, {}).get("crudeMortalityRate", {}).get("all", {}).get("stat") if i in mo.index else np.nan)
    A["u5dr"] = A.id.map(lambda i: mo.get(i, {}).get("under5MortalityRate", {}).get("stat") if i in mo.index else np.nan)
    name = A.surveyName.str.replace(r"^.*?20\d\d[_ ]+", "", regex=True)
    A["zone"] = [zone_key(n + " " + (s or "")) if zone_key(n).split("|")[1] == "" else zone_key(n)
                 for n, s in zip(name, A.administrative_area_level_1)]
    A["year"] = A.surveyYear.astype(int)
    A["region"] = np.where(A.surveyName.str.contains("NFSS"), "NE", "NW")
    A.loc[A.zone.str.contains("kebbi|jigawa|kaduna|niger|benue"), "region"] = "NW"
    keep = ["zone", "year", "region", "gam", "sam", "muac_gam", "stunting", "underweight", "cdr", "u5dr", "surveyName"]
    S = A[keep].groupby(["zone", "year", "region"], as_index=False).agg(
        {**{c: "mean" for c in keep[3:-1]}, "surveyName": "first"})
    return S


# ------------------------------------------------------------------ exposure
def us_orgs():
    """US-funded organisations in Nigeria: USAID/State awards FY2023-25 (USAspending) and UN agencies' FTS US share."""
    u = pd.read_csv(INP / "usaspending" / "nga_awards_fy22_25.csv")
    u = u[u["Awarding Agency"].isin(["Agency for International Development", "Department of State"])]
    u = u[pd.to_datetime(u["End Date"], errors="coerce") >= "2023-10-01"]
    names = set(u["Recipient Name"].dropna().map(nrm))
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet")
    f = f[f.dest_country.fillna("").str.contains("Nigeria") & f.status.isin(["paid", "commitment"]) &
          ((f.boundary == "incoming") | f.boundary.isna()) & (f.amount_usd > 0)].copy()
    f["y"] = pd.to_datetime(f.decision_date, errors="coerce").dt.year
    f = f[f.y.between(2023, 2024)]
    f["us"] = f.donor.fillna("").str.startswith("United States")
    un = {}
    for k, pat in {"wfp": "World Food Programme", "unicef": "Children's Fund", "iom": "Organization for Migration",
                   "unhcr": "High Commissioner for Refugees", "fao": "Food and Agriculture", "who": "World Health Organization",
                   "unfpa": "Population Fund"}.items():
        s = f[f.recipient.fillna("").str.contains(pat, regex=False)]
        un[k] = float(s[s.us].amount_usd.sum() / s.amount_usd.sum()) if len(s) else 0.0
    KEY["un_us_share"] = {k: round(v, 3) for k, v in un.items()}
    KEY["fts_nga"] = {int(y): {"us": round(float(g[g.us].amount_usd.sum() / 1e6), 1),
                               "other": round(float(g[~g.us].amount_usd.sum() / 1e6), 1)}
                      for y, g in pd.read_parquet(INP / "fts" / "fts_flows.parquet").pipe(
                          lambda x: x[x.dest_country.fillna("").str.contains("Nigeria") & x.status.isin(["paid", "commitment"]) &
                                      ((x.boundary == "incoming") | x.boundary.isna()) & (x.amount_usd > 0)]).assign(
                          y=lambda x: pd.to_datetime(x.decision_date, errors="coerce").dt.year,
                          us=lambda x: x.donor.fillna("").str.startswith("United States")).groupby("y") if 2019 <= y <= 2025}
    return names, un


ALIAS = {  # 3W organisation (normalised) -> USAspending recipient (normalised) where names differ
    "actionagainsthunger": "actioncontrelafaim", "familyhealthinternationalfhi": "familyhealthinternational",
    "fhi": "familyhealthinternational", "danishrefugeecouncil": "danskflygtningehjaelp",
    "savethechildreninternational": "savethechildrenfederationinc", "savethechildren": "savethechildrenfederationinc",
    "internationalrescuecommittee": "internationalrescuecommitteeinc", "premiereurgenceinternationale": "premiereurgenceinternationale",
    "norwegianrefugeecouncil": "norwegianrefugeecouncilnrcstiftelsenflyktninghjelpen", "catholicreliefservices":
        "catholicreliefservicesunitedstatesconferenceofcatholicbishops", "internationalmedicalcorps": "internationalmedicalcorps",
}


def org_u(org, acr, names, un):
    n, a = nrm(org), nrm(acr)
    for k, pat in {"wfp": "worldfoodprogram", "unicef": "childrensfund|unicef", "iom": "migration", "unhcr": "refugees|unhcr",
                   "fao": "foodandagriculture", "who": "worldhealthorganization", "unfpa": "populationfund"}.items():
        if re.search(pat, n) or a == k:
            return un[k]
    if n in ALIAS:
        n = ALIAS[n]
    if n in names or any(n and (n in x or x in n) and min(len(n), len(x)) > 10 for x in names):
        return 1.0
    if difflib.get_close_matches(n, list(names), n=1, cutoff=0.9):
        return 1.0
    return 0.0


def read_3w(f):
    d = pd.read_csv(W3 / f, encoding="latin1") if f.endswith("csv") else pd.read_excel(W3 / f)
    d.columns = [c.strip().lower().replace(" ", "_").replace(".", "") for c in d.columns]
    d = d.rename(columns={"organisation": "org", "org_acronym": "acr", "project_sector": "sector", "states": "state",
                          "lga_pcode": "lga_pcode", "lga": "lga"})
    d = d[~d.org.astype(str).str.startswith("#")]
    d["sec"] = None
    for k, pat in SECT.items():
        d.loc[d.sector.astype(str).str.lower().str.match(pat), "sec"] = k
    d["lga_key"] = d.state.astype(str).str.lower().str.strip() + "|" + d.lga.map(nrm)
    return d[["org", "acr", "sec", "state", "lga", "lga_pcode", "lga_key"]]


def exposure(Z):
    names, un = us_orgs()
    files = {2024: "who-is-doing-what-and-where_nga_3w_apr_jun_2024.csv",
             2025: "who-is-doing-what-and-where_nga_3w_apr_jun_2025.xlsx",
             2026: "who-is-doing-what-and-where_nga_3w_apr_jun_2026.xlsx"}
    P = {y: read_3w(f) for y, f in files.items()}
    # one identifier per organisation across years: same normalised name OR same acronym
    allo = pd.concat(P.values())[["org", "acr"]].drop_duplicates()
    allo["n"], allo["a"] = allo.org.map(nrm), allo.acr.map(nrm)
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x
    for n, a_ in zip(allo.n, allo.a):
        if n:
            find("n:" + n)
        if a_ and len(a_) >= 2 and n:
            parent[find("a:" + a_)] = find("n:" + n)
    oid = {o: find("n:" + nrm(o)) for o in allo.org}
    for y in P:
        P[y]["oid"] = P[y].org.map(oid)
    d24 = P[2024][P[2024].sec.notna()].copy()
    orgs = d24.drop_duplicates("org")[["org", "acr"]]
    orgs["u"] = [org_u(o, a, names, un) for o, a in zip(orgs.org, orgs.acr)]
    KEY["orgs_2024"], KEY["orgs_us"] = int(len(orgs)), int((orgs.u >= 0.99).sum())
    KEY["orgs_us_list"] = sorted(orgs[orgs.u >= 0.99].org.tolist())[:60]
    d24 = d24.merge(orgs[["org", "u"]], on="org")
    units = {y: P[y][P[y].sec.notna()].drop_duplicates(["lga_key", "oid", "sec"]) for y in P}
    L = pd.DataFrame({f"units{y}": units[y].groupby("lga_key").size() for y in P})
    L["us_share"] = d24.drop_duplicates(["lga_key", "oid", "sec"]).groupby("lga_key").u.mean()
    L["us_units24"] = d24.drop_duplicates(["lga_key", "oid", "sec"]).groupby("lga_key").u.sum()
    L = L[L.units2024.notna()]
    L["loss25"] = 1 - L.units2025.fillna(0) / L.units2024
    L["loss26"] = 1 - L.units2026.fillna(0) / L.units2024
    # survival of US-funded vs other units
    s25 = set(map(tuple, units[2025][["lga_key", "oid", "sec"]].values))
    t = d24.drop_duplicates(["lga_key", "oid", "sec"]).copy()
    t["stay"] = [tuple(r) in s25 for r in t[["lga_key", "oid", "sec"]].values]
    s25o = set(units[2025].oid)
    KEY["org_survival"] = {"us": float(t[t.u >= 0.5].drop_duplicates("oid").oid.isin(s25o).mean()),
                           "nonus": float(t[t.u < 0.5].drop_duplicates("oid").oid.isin(s25o).mean())}
    KEY["survival"] = {"us": float(t[t.u >= 0.5].stay.mean()), "nonus": float(t[t.u < 0.5].stay.mean()),
                       "n_us": int((t.u >= 0.5).sum()), "n_nonus": int((t.u < 0.5).sum())}
    # WFP food assistance present in the LGA in 2024 (WFP was ~half US-funded and suspended food aid to
    # about 1.3 million people in the north-east in mid-2025, just before the 2025 survey round)
    w = pd.read_parquet(INP / "subnational_aid" / "tidy" / "wfp_nga.parquet")
    w = w[(w.period_start.dt.year == 2024) & (w.cluster == "food_security")]
    wl = set((w.admin1.str.lower().str.strip() + "|" + w.admin2.map(nrm)))
    L["wfp24"] = [1.0 if k in wl else 0.0 for k in L.index]
    KEY["wfp_lgas_2024"] = int(L.wfp24.sum())
    L = L.join(Z.set_index("lga_key")[["u5", "zone", "region"]], how="left")
    L["density"] = L.units2024 / L.u5 * 1e5
    KEY["lga_match"] = float(L.zone.notna().mean())
    KEY["lga_unmatched"] = sorted(L[L.zone.isna()].index)[:20]
    L.to_csv(TAB / "nga_lga_exposure.csv")
    return L


def zone_exposure(L, Z):
    zz = Z.set_index("lga_key")
    rows = []
    for z, g in Z.groupby("zone"):
        rec = {"zone": z}
        l = L.reindex(g.lga_key)
        w = g.set_index("lga_key").u5.reindex(l.index).fillna(1)
        for c in ["us_share", "loss25", "density", "wfp24"]:
            ok = l[c].notna()
            rec[c] = float((l[c][ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan
        rec["lgas"], rec["lgas_3w"] = len(g), int(l.units2024.notna().sum())
        rows.append(rec)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ estimation helpers
def demean(v, groups, iters=300):
    v = v.astype(float).copy()
    for _ in range(iters):
        v0 = v.copy()
        for gg in groups:
            v = v - v.groupby(gg).transform("mean")
        if np.max(np.abs(v - v0)) < 1e-10:
            break
    return v


def did(d, y, e, unit, time, cl, post="post", B=9999):
    """Two-way FE DiD of y on e x post. Cluster-robust s.e. with the usual small-sample factor
    G/(G-1) x (n-1)/(n-k), k counting both sets of fixed effects (as Stata's regress does), and a
    restricted wild cluster bootstrap p-value (Webb weights). Each bootstrap sample is re-demeaned by
    unit and time before re-estimating: multiplying residuals by cluster weights reintroduces time
    means, and leaving them in inflates the bootstrap s.e. and understates p-values."""
    d = d.dropna(subset=[y, e]).copy()
    fe = [d[unit], d[time]]
    yt = demean(d[y], fe).values
    xt = demean(d[e] * d[post], fe).values
    g = d[cl].values
    groups = np.unique(g)
    G, n = len(groups), len(d)
    k = d[unit].nunique() + d[time].nunique()          # unit FE + time FE - 1 + the treatment term
    adj = G / (G - 1) * (n - 1) / (n - k)

    def t_stat(yv):
        b = (xt @ yv) / (xt @ xt)
        r = yv - b * xt
        return b, np.sqrt(sum((xt[g == q] @ r[g == q]) ** 2 for q in groups) / (xt @ xt) ** 2 * adj)
    b, se = t_stat(yt)
    # restricted wild cluster bootstrap: under H0 (b = 0) the restricted residual is yt itself
    gi = np.searchsorted(groups, g)
    W = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    D = np.column_stack([pd.get_dummies(f, dtype=float).values for f in fe])
    Mfe = np.eye(n) - D @ np.linalg.pinv(D)          # residual maker for the two sets of FE
    ts = []
    for _ in range(B):
        ys = Mfe @ (RNG.choice(W, G)[gi] * yt)
        bs, ses = t_stat(ys)
        ts.append(bs / ses)
    p = float(np.mean(np.abs(ts) >= abs(b / se)))
    return dict(b=b, se=se, p_wild=p, n=n, units=d[unit].nunique(), clusters=G)


def first_stage(L):
    d = L.dropna(subset=["us_share", "loss25"])
    d = d[d.zone.notna() | True]
    X = np.column_stack([np.ones(len(d)), d.us_share])
    b = np.linalg.lstsq(X, d.loss25.values, rcond=None)[0]
    e = d.loss25.values - X @ b
    V = np.linalg.pinv(X.T @ X) @ (X.T * e ** 2) @ X @ np.linalg.pinv(X.T @ X) * len(d) / (len(d) - 2)
    KEY["fs_lga"] = dict(b=float(b[1]), se=float(np.sqrt(V[1, 1])), F=float(b[1] ** 2 / V[1, 1]), n=len(d),
                         corr=float(d.us_share.corr(d.loss25)))
    d2 = L.dropna(subset=["density", "loss25"])
    KEY["fs_lga_density_corr"] = float(np.log(d2.density + 1).corr(d2.loss25))


# ------------------------------------------------------------------ Cadre Harmonise
def ch_panel(L, Z):
    o = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    c = o[(o.iso3 == "NGA") & (o.source == "CH")].copy()
    c["month"] = c.month.astype(str)
    c = c[(c.month >= "2019-01") & c.month.str[5:].isin(["03", "11"]) & (c.month <= "2025-12")]
    c["lga_key"] = c.adm1_name.astype(str).str.lower().str.strip() + "|" + c.area_name.map(nrm)
    c["share3"] = 100 * c.share3
    c = c.join(L[["us_share", "loss25", "density"]], on="lga_key")
    c["ne"] = c.adm1_name.str.lower().isin(["borno", "yobe", "adamawa"]).astype(float)
    c["nw_ne"] = c.adm1_name.str.lower().isin(["borno", "yobe", "adamawa", "sokoto", "katsina", "zamfara", "jigawa", "kebbi"])
    c["post"] = (c.month == "2025-11").astype(float)
    c = c[c.month != "2025-03"]      # March 2025 round: transition
    KEY["ch_rounds"] = sorted(c.month.unique())
    KEY["ch_lgas_matched"] = int(c[c.us_share.notna()].lga_key.nunique())
    return c


def main():
    Z = zones()
    S = surveys()
    L = exposure(Z)
    first_stage(L)
    ZE = zone_exposure(L, Z)
    S = S.merge(ZE, on="zone", how="left")
    S["post"] = (S.year >= 2025).astype(float)
    S.to_csv(TAB / "nga_zone_panel.csv", index=False)
    KEY["zones"] = S.groupby("region").zone.nunique().to_dict()
    KEY["zone_years"] = S.groupby(["region", "year"]).size().unstack().fillna(0).astype(int).to_dict()
    KEY["zones_unmatched_exposure"] = sorted(S[(S.region == "NE") & S.us_share.isna()].zone.unique())
    ne = S[(S.region == "NE") & S.us_share.notna()].copy()
    for c in ["us_share", "loss25", "density", "wfp24"]:
        ne["z_" + c] = (ne[c] - ne.drop_duplicates("zone")[c].mean()) / ne.drop_duplicates("zone")[c].std()
    R = []
    outs = ["gam", "sam", "muac_gam", "stunting", "underweight", "cdr", "u5dr"]
    for e in ["z_us_share", "z_loss25", "z_density", "z_wfp24"]:
        for y in outs:
            R.append(dict(sample="NE zones", exposure=e, outcome=y, **did(ne, y, e, "zone", "year", "zone")))
            R.append(dict(sample="NE zones, 2025 only", exposure=e, outcome=y,
                          **did(ne[ne.year != 2026], y, e, "zone", "year", "zone")))
    # north-east vs north-west (zones observed in 2024 and later)
    both = S[S.zone.isin(S[S.year == 2024].zone) & (S.year >= 2024)].copy()
    both["ne"] = (both.region == "NE").astype(float)
    for y in outs:
        R.append(dict(sample="NE vs NW zones", exposure="ne", outcome=y, **did(both, y, "ne", "zone", "year", "zone")))
    R = pd.DataFrame(R)
    R.to_csv(TAB / "nga_did.csv", index=False)

    C = ch_panel(L, Z)
    CR = []
    cne = C[C["ne"] == 1].copy()
    for c in ["us_share", "loss25", "density"]:
        sd = cne.drop_duplicates("lga_key")[c].std()
        cne["z_" + c] = (cne[c] - cne.drop_duplicates("lga_key")[c].mean()) / sd
        CR.append(dict(sample="NE LGAs", exposure="z_" + c, **did(cne, "share3", "z_" + c, "lga_key", "month", "lga_key")))
    cnw = C[C.nw_ne].copy()
    CR.append(dict(sample="NE vs NW LGAs", exposure="ne", **did(cnw, "share3", "ne", "lga_key", "month", "lga_key")))
    CR = pd.DataFrame(CR)
    CR.to_csv(TAB / "nga_ch_did.csv", index=False)
    # event study, CH, NE LGAs by US share
    ev = []
    for e in ["z_us_share", "z_loss25"]:
        d = cne.dropna(subset=[e, "share3"])
        for m in sorted(d.month.unique()):
            if m == "2024-11":
                continue
            d["x"] = d[e] * (d.month == m)
        rounds = [m for m in sorted(d.month.unique()) if m != "2024-11"]
        yt = demean(d.share3, [d.lga_key, d.month]).values
        Xm = np.column_stack([demean(d[e] * (d.month == m), [d.lga_key, d.month]).values for m in rounds])
        b = np.linalg.lstsq(Xm, yt, rcond=None)[0]
        res = yt - Xm @ b
        g = d.lga_key.values
        XtX = np.linalg.pinv(Xm.T @ Xm)
        meat = sum(np.outer(Xm[g == q].T @ res[g == q], Xm[g == q].T @ res[g == q]) for q in np.unique(g))
        V = XtX @ meat @ XtX
        ev += [dict(exposure=e, round=m, b=b[i], se=np.sqrt(V[i, i])) for i, m in enumerate(rounds)]
        ev.append(dict(exposure=e, round="2024-11", b=0.0, se=0.0))
    EV = pd.DataFrame(ev).sort_values(["exposure", "round"])
    EV.to_csv(TAB / "nga_ch_event.csv", index=False)
    figures(S, EV)
    write_numbers(R, CR, S)
    (TAB / "nga_key.json").write_text(json.dumps(KEY, indent=1, default=str))
    pd.set_option("display.width", 230, "display.max_rows", 200)
    print(json.dumps({k: v for k, v in KEY.items() if k != "orgs_us_list"}, indent=1, default=str))
    print(S.round(2).to_string())
    print(R.round(3).to_string())
    print(CR.round(3).to_string())
    print(EV.round(2).to_string())


def figures(S, EV):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.3))
    ax = axes[0]
    ne = S[S.region == "NE"].dropna(subset=["us_share"])
    hi = ne.us_share > ne.drop_duplicates("zone").us_share.median()
    for lab, sub, col in [("NE, more US-reliant", ne[hi], ORANGE), ("NE, less US-reliant", ne[~hi], BLUE),
                          ("North-west", S[(S.region == "NW") & S.zone.isin(S[S.year == 2024].zone)], GREEN)]:
        m = sub.groupby("year").gam.mean()
        ax.plot(m.index, m.values, marker="o", ms=4, color=col, label=lab)
    ax.axvline(2024.5, color=GREY, ls=":", lw=0.8)
    ax.set_ylabel("Wasting (GAM, %)")
    ax.set_xticks([2023, 2024, 2025, 2026])
    ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    e = EV[EV.exposure == "z_us_share"]
    x = np.arange(len(e))
    ax.errorbar(x, e.b, yerr=1.96 * e.se, fmt="o", color=ORANGE, ms=4, lw=1.2)
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([r[2:4] + ("M" if r[5:] == "03" else "N") for r in e["round"]], fontsize=8)
    ax.set_title("Phase 3+ share (pp) per s.d. of US reliance,\nNE LGAs, relative to Nov 2024", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "nga_results.pdf")
    plt.close(fig)


def write_numbers(R, CR, S):
    f2 = lambda v: f"{v:.2f}"
    en = {"z_us_share": "Us", "z_loss25": "Loss", "z_density": "Dens", "ne": "Ne", "z_wfp24": "Wfp"}
    on = {"gam": "Gam", "sam": "Sam", "muac_gam": "Muac", "stunting": "Stunt", "underweight": "Uwt", "cdr": "Cdr", "u5dr": "Ufive"}
    sn = {"NE zones": "", "NE zones, 2025 only": "Tf", "NE vs NW zones": ""}
    for r in R.itertuples():
        t = en[r.exposure] + on[r.outcome] + sn[r.sample]
        M[f"ngB{t}"], M[f"ngSe{t}"], M[f"ngP{t}"] = f2(r.b), f2(r.se), f2(r.p_wild)
    for r in CR.itertuples():
        t = en[r.exposure]
        M[f"chB{t}"], M[f"chSe{t}"], M[f"chP{t}"] = f2(r.b), f2(r.se), f2(r.p_wild)
        M[f"chN{t}"] = r.units
    fs = KEY["fs_lga"]
    M["ngFsB"], M["ngFsSe"], M["ngFsF"], M["ngFsN"], M["ngFsCorr"] = f2(fs["b"]), f2(fs["se"]), f"{fs['F']:.1f}", fs["n"], f2(fs["corr"])
    sv = KEY["survival"]
    M["ngSurvUs"], M["ngSurvNon"] = f"{100 * sv['us']:.0f}", f"{100 * sv['nonus']:.0f}"
    M["ngOrgSurvUs"] = f"{100 * KEY['org_survival']['us']:.0f}"
    M["ngOrgSurvNon"] = f"{100 * KEY['org_survival']['nonus']:.0f}"
    M["ngOrgs"], M["ngOrgsUs"] = KEY["orgs_2024"], KEY["orgs_us"]
    fts = KEY["fts_nga"]
    M["ngUsTf"], M["ngUsTv"] = f"{fts[2024]['us']:.0f}", f"{fts[2025]['us']:.0f}"
    M["ngOtTf"], M["ngOtTv"] = f"{fts[2024]['other']:.0f}", f"{fts[2025]['other']:.0f}"
    M["ngZonesNe"], M["ngZonesNw"] = KEY["zones"].get("NE", 0), KEY["zones"].get("NW", 0)
    ne = S[S.region == "NE"].groupby("year").gam.mean()
    nw = S[(S.region == "NW") & S.zone.isin(S[S.year == 2024].zone)].groupby("year").gam.mean()
    for y in [2023, 2024, 2025, 2026]:
        if y in ne.index:
            M[f"ngNeGam{y}"] = f"{ne[y]:.1f}"
        if y in nw.index:
            M[f"ngNwGam{y}"] = f"{nw[y]:.1f}"
    (ROOT / "output" / "us_cut_memo" / "numbers_nga.tex").write_text(
        "% generated by code/74_nigeria_us_cut.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{re.sub(r'[0-9]', lambda m: 'ABCDEFGHIJ'[int(m.group())], k)}}}{{{v}}}\n"
                for k, v in M.items()))


if __name__ == "__main__":
    main()
