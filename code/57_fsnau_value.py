"""Do scheduled survey results improve forecasts of measured malnutrition?
Somalia, FSNAU seasonal assessments (post-Gu and post-Deyr), 2011-2024.

FSNAU surveys rural livelihood zones on a fixed calendar, twice a year, so the
timing of a survey does not depend on alarm. For each rural zone and season t,
the outcome is acute malnutrition among children (GAM, weight-for-height, from
SMART surveys; and GAM of 15 percent or more, 'critical'). Predictors:
  forecast   FEWS NET's projected phase for the zone in the survey month,
             from the latest report issued 3-8 months before (mean over the
             FEWS NET units matched to the zone; and share of units Phase 3+/4+)
  map        FEWS NET's current-situation phase at that report
  last GAM   the zone's own result in the previous scheduled round (season t-1)
Scored out of sample, leaving one season out at a time: R-squared for GAM and
AUC for critical GAM; also OLS with season fixed effects (which zones are worse
this season), clustered by zone.

Survey names are matched to FEWS NET units by livelihood-zone keywords and
region/district qualifiers (CROSSWALK rules below). Urban and IDP surveys are
excluded (FEWS NET has no separate IDP units before 2023). MUAC-only rapid
assessments and partner NGO surveys (fielded ad hoc) are excluded.

Outputs: output/tables/fsnau_value*.csv, fsnau_value_key.json, input/fsnau/crosswalk.csv
"""
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"

NW = {"Awdal", "Woqooyi Galbeed", "Togdheer", "Sool", "Sanaag"}
NE = {"Bari", "Nugaal", "Mudug", "Sool", "Sanaag"}
CENTRAL = {"Mudug", "Galgaduud"}
SHABELLE = {"Middle Shabelle", "Lower Shabelle"}
JUBA = {"Middle Juba", "Lower Juba"}
NORTH_GEDO = {"Belet Xaawo", "Doolow", "Luuq"}
REGIONS = ["Awdal", "Bakool", "Banaadir", "Bari", "Bay", "Galgaduud", "Gedo", "Hiiraan", "Lower Juba",
           "Lower Shabelle", "Middle Juba", "Middle Shabelle", "Mudug", "Nugaal", "Sanaag", "Sool",
           "Togdheer", "Woqooyi Galbeed"]
RIVERINE = r"riverine|pump|gravity|irrigat"
AGRO = r"agro"


def units():
    u = pd.read_parquet(INP / "fewsnet/ipcphase.parquet", columns=["country_code", "fnid", "geographic_unit_full_name"])
    u = u[u.country_code == "SO"].drop_duplicates("fnid").dropna()
    p = u.geographic_unit_full_name.str.rsplit(",", n=3, expand=True)
    u["lz"], u["dist"], u["reg"] = p[0].str.strip(), p[1].str.strip(), p[2].str.strip()
    u = u.dropna(subset=["reg"])
    u = u[~u.lz.str.contains("Urban|IDP", case=False)]
    u["lzl"] = u.lz.str.lower()
    return u[["fnid", "lz", "lzl", "dist", "reg"]]


def rule(name, region):
    """Survey population name -> (livelihood pattern, regions, districts, key). None if unmatched."""
    n = name.lower().replace("-", " ").replace("shabeele", "shabelle").replace("adduun", "addun")
    n = re.sub(r"\s+", " ", n)
    regs, dists, lz = None, None, None
    qual = (NW if re.search(r"\bnw\b|north ?west|of northwest", n) else
            NE if re.search(r"\bne\b|north ?east|of northeast", n) else
            CENTRAL if re.search(r"central", n) else None)
    if "addun" in n: lz = "addun"
    elif "hawd" in n: lz = "hawd"
    elif "guban" in n and "golis" not in n: lz = "guban"
    elif "west golis" in n: lz = "west golis"
    elif "east golis" in n: lz = "east golis"
    elif "golis" in n: lz = "golis"
    elif "coastal deeh" in n: lz = "coastal deeh"
    elif "nugal valley" in n: lz = "nugal valley"
    elif "sool plateau" in n or "sool sanag" in n: lz = "sool.?sanag plateau|sool plateau"
    elif "northern inland" in n: lz = "northern inland"
    elif re.search(r"north ?west(ern)? agro|nw agro", n): lz = "north.?west(ern)? ?agro|north-west agro"
    elif "togdheer agro" in n: lz = "togdheer agro"
    elif "cowpea" in n: lz = "cowpea|central regions agro"
    elif "dawo" in n: lz = "dawo"
    elif re.search(r"bay agro|sorghum high", n) or (n.startswith("bay") and "agro" in n):
        lz, regs = r"bay|sorghum high", {"Bay"}
    elif "bakool" in n:
        lz, regs = (AGRO if "agro" in n else "pastoral"), {"Bakool"}
    elif "gedo" in n:
        regs = {"Gedo"}
        dists = NORTH_GEDO if "north" in n else (None if "south" not in n else "SOUTH")
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else "pastoral" if "pastoral" in n else None
    elif "shabelle" in n:
        regs = ({"Lower Shabelle"} if "lower" in n else {"Middle Shabelle"} if "middle" in n else SHABELLE)
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else None
    elif "juba" in n:
        regs = ({"Lower Juba"} if "lower" in n else {"Middle Juba"} if "middle" in n else JUBA)
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else "pastoral" if "pastoral" in n else None
    elif re.search(r"belet ?w|beled ?w", n):
        regs, dists = {"Hiiraan"}, {"Beledweyn"}
    elif "mataban" in n:
        # Mataban district is carved out of Beledweyn; FEWS NET units still use Beledweyn
        regs, dists = {"Hiiraan"}, {"Beledweyn"}
    elif re.search(r"hiran|hiraan|hiiraan", n):
        regs = {"Hiiraan"}
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else None
    else:
        return None
    if regs is None and qual is not None:
        regs = qual
    if regs is None and isinstance(region, str):
        hit = [r for r in REGIONS if r.lower() in region.lower()]
        regs = set(hit) or None
    key = f"{lz}|{','.join(sorted(regs)) if regs else ''}|{dists if isinstance(dists, str) else ','.join(sorted(dists or []))}"
    return lz, regs, dists, key


def match(U, lz, regs, dists):
    s = U
    if regs:
        s = s[s.reg.isin(regs)]
    if dists == "SOUTH":
        s = s[~s.dist.isin(NORTH_GEDO)]
    elif dists:
        s = s[s.dist.isin(dists)]
    if lz:
        s = s[s.lzl.str.contains(lz, regex=True)]
    return set(s.fnid)


def target_month(row):
    if isinstance(row.fieldwork, str):
        m = re.findall(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? ?(20\d\d)?", row.fieldwork.lower())
        y = re.findall(r"20\d\d", row.fieldwork)
        if m and y:
            mon = "jan feb mar apr may jun jul aug sep oct nov dec".split().index(m[-1][0]) + 1
            return pd.Period(f"{y[-1]}-{mon:02d}", "M")
    yr = int(row.season_year)
    return pd.Period(f"{yr}-07", "M") if row.season_type == "Gu" else pd.Period(f"{yr}-11", "M")


def build():
    s = pd.read_csv(INP / "fsnau/surveys.csv")
    s = s[(s.population_type == "rural") & (s.method == "SMART") & s.gam.notna()].copy()
    # partner NGO surveys (ACF, SCI, CARE, ...) are fielded ad hoc, not on FSNAU's schedule
    s = s[~s.population_group.str.contains(r"\b(ACF|SCI|CARE|INTERSOS|EPHCO)\b|\(SCI\)", regex=True)]
    U = units()
    rows = []
    for i, r in s.iterrows():
        x = rule(r.population_group, r.region)
        if x is None:
            rows.append(dict(idx=i, key=None, n_units=0))
            continue
        lz, regs, dists, key = x
        ids = match(U, lz, regs, dists)
        rows.append(dict(idx=i, key=key if ids else None, n_units=len(ids), fnids=";".join(sorted(ids))))
    cw = pd.DataFrame(rows).set_index("idx")
    s = s.join(cw)
    s[["season", "population_group", "region", "key", "n_units"]].to_csv(INP / "fsnau/crosswalk.csv", index=False)
    s = s[s.key.notna()].copy()
    s["month"] = [target_month(r) for r in s.itertuples()]
    # season order index: Gu 2011 = 2011.0, Deyr 2011/12 = 2011.5
    s["t"] = s.season_year + np.where(s.season_type == "Deyr", 0.5, 0.0)
    # one row per zone key and season (average duplicates, e.g. re-analyses)
    s = s.groupby(["key", "t"]).agg(month=("month", "first"), season=("season", "first"), gam=("gam", "mean"),
                                    cdr=("cdr", "mean"), u5dr=("u5dr", "mean"), fnids=("fnids", "first"),
                                    name=("population_group", "first")).reset_index()
    prev = s[["key", "t", "gam"]].rename(columns={"gam": "gam_lag"})
    prev["t"] = prev.t + 0.5
    s = s.merge(prev, on=["key", "t"], how="left")
    # FEWS NET forecast for the survey month, latest report issued 3-8 months before
    pr = pd.read_parquet(INP / "fewsnet/proj_monthly.parquet")
    pr = pr[(pr.country_code == "SO") & pr.lead.between(3, 8)]
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet")
    cs = cs[cs.country_code == "SO"]
    out = []
    for r in s.itertuples():
        ids = r.fnids.split(";")
        f = pr[pr.fnid.isin(ids) & (pr.month == r.month)]
        if f.empty:
            out.append({})
            continue
        rep = f.report_month.max()
        f = f[f.report_month == rep]
        f = f.loc[f.groupby("fnid").lead.idxmin()]
        c = cs[cs.fnid.isin(ids) & (cs.month <= rep) & (cs.month > rep - 4)]
        c = c[c.month == c.month.max()] if not c.empty else c
        out.append(dict(fc=f.phase.mean(), fc3=(f.phase >= 3).mean(), fc4=(f.phase >= 4).mean(),
                        fc_flag=f.assist_flag.mean(), lead=int(r.month.ordinal - rep.ordinal),
                        cur=c.phase.mean() if len(c) else np.nan, n_fc=len(f)))
    s = pd.concat([s.reset_index(drop=True), pd.DataFrame(out)], axis=1)
    s["crit"] = (s.gam >= 15).astype(float)
    s["crit_lag"] = (s.gam_lag >= 15).astype(float).where(s.gam_lag.notna())
    s = s[(s.t >= 2011) & (s.t < 2025)]
    return s


def loso(d, y, xs, binary=False):
    """Leave-one-season-out OLS predictions; R-squared (continuous) or AUC (binary)."""
    pred = pd.Series(np.nan, index=d.index)
    for t in d.t.unique():
        tr, te = d.t != t, d.t == t
        X = np.column_stack([np.ones(tr.sum())] + [d.loc[tr, x] for x in xs])
        b = np.linalg.lstsq(X, d.loc[tr, y], rcond=None)[0]
        Xt = np.column_stack([np.ones(te.sum())] + [d.loc[te, x] for x in xs])
        pred[te] = Xt @ b
    if binary:
        return roc_auc_score(d[y], pred)
    return 1 - ((d[y] - pred) ** 2).sum() / ((d[y] - d[y].mean()) ** 2).sum()


def fe_ols(d, y, xs):
    """OLS with season fixed effects, clustered by zone."""
    w = d[[y] + xs].sub(d.groupby("t")[[y] + xs].transform("mean"))
    X, Y = w[xs].values, w[y].values
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ Y
    u = Y - X @ b
    meat = np.zeros((len(xs), len(xs)))
    for g in d.key.unique():
        i = (d.key == g).values
        sc = X[i].T @ u[i]
        meat += np.outer(sc, sc)
    G = d.key.nunique()
    V = XtXi @ meat @ XtXi * G / (G - 1)
    return pd.DataFrame({"coef": b, "se": np.sqrt(np.diag(V))}, index=xs)


def fe_slope(d, y, x, fes):
    """Slope of y on x after sweeping out the fixed effects in fes (alternating projections),
    standard error clustered by zone."""
    d = d.dropna(subset=[y, x]).copy()
    for _ in range(50):
        for f in fes:
            for c in [y, x]:
                d[c] = d[c] - d.groupby(f)[c].transform("mean")
    X, Y = d[x].values, d[y].values
    b = (X @ Y) / (X @ X)
    u = Y - b * X
    G = d.key.unique()
    meat = sum((X[(d.key == g).values] @ u[(d.key == g).values]) ** 2 for g in G)
    return b, float(np.sqrt(meat / (X @ X) ** 2 * len(G) / (len(G) - 1))), len(d)


def main():
    s = build()
    key = {"surveys_rural_smart": int(len(s)), "zones": int(s.key.nunique()),
           "with_forecast": int(s.fc.notna().sum()), "with_lag": int(s.gam_lag.notna().sum())}
    d = s.dropna(subset=["fc", "gam_lag", "cur"]).copy()
    key.update(n=int(len(d)), n_zones=int(d.key.nunique()), n_seasons=int(d.t.nunique()),
               crit_share=float(d.crit.mean()), median_lead=float(d.lead.median()),
               gam_mean=float(d.gam.mean()))
    models = {"season pattern only": [],
              "FEWS NET forecast": ["fc", "fc3", "fc4"],
              "FEWS NET forecast + map": ["fc", "fc3", "fc4", "cur"],
              "last survey": ["gam_lag"],
              "forecast + last survey": ["fc", "fc3", "fc4", "gam_lag"],
              "forecast + map + last survey": ["fc", "fc3", "fc4", "cur", "gam_lag"]}
    d["gu"] = (d.t % 1 == 0).astype(float)
    rows = []
    for name, xs in models.items():
        xs2 = xs + ["gu"]
        rows.append(dict(model=name, r2=loso(d, "gam", xs2), auc=loso(d, "crit", xs2, binary=True)))
    res = pd.DataFrame(rows)
    res.to_csv(TAB / "fsnau_value.csv", index=False)
    # within season: which zones are worse this season?
    fe = []
    for name, xs in [("forecast", ["fc"]), ("last survey", ["gam_lag"]), ("both", ["fc", "gam_lag"]),
                     ("both + map", ["fc", "cur", "gam_lag"])]:
        r = fe_ols(d, "gam", xs)
        for v, x in r.iterrows():
            fe.append(dict(model=name, var=v, coef=x.coef, se=x.se))
    fe = pd.DataFrame(fe)
    fe.to_csv(TAB / "fsnau_value_fe.csv", index=False)
    # changes: does the forecast predict which zones deteriorate (GAM up from last round)?
    d["dgam"] = d.gam - d.gam_lag
    d["dfc"] = d.fc - d.cur
    d["worse5"] = (d.dgam >= 5).astype(float)
    ch = []
    for name, xs in [("season pattern only", []), ("forecast change", ["dfc"]),
                     ("forecast level and change", ["fc", "dfc"]), ("last survey", ["gam_lag"]),
                     ("forecast + last survey", ["fc", "dfc", "gam_lag"])]:
        ch.append(dict(model=name, r2=loso(d, "dgam", xs + ["gu"]), auc=loso(d, "worse5", xs + ["gu"], binary=True)))
    ch = pd.DataFrame(ch)
    ch.to_csv(TAB / "fsnau_value_changes.csv", index=False)
    r = fe_ols(d, "dgam", ["dfc", "gam_lag"])
    key["dgam_on_dfc"], key["dgam_on_dfc_se"] = float(r.loc["dfc", "coef"]), float(r.loc["dfc", "se"])
    key["worse5_share"] = float(d.worse5.mean())
    # the map FEWS NET published after the survey (which can use it): does it line up with GAM?
    cs = pd.read_parquet(INP / "fewsnet/cs_monthly.parquet")
    cs = cs[cs.country_code == "SO"]
    after = []
    for r_ in d.itertuples():
        c = cs[cs.fnid.isin(r_.fnids.split(";")) & (cs.month > r_.month) & (cs.month <= r_.month + 5)]
        after.append(c[c.month == c.month.min()].phase.mean() if len(c) else np.nan)
    d["after"] = after
    a_ = d.dropna(subset=["after"])
    key["corr_gam_after_map"] = float(a_.gam.corr(a_.after))
    key["corr_gam_forecast"] = float(d.gam.corr(d.fc))
    key["corr_gam_lag"] = float(d.gam.corr(d.gam_lag))
    r = fe_ols(a_, "gam", ["after"])
    key["gam_on_after"], key["gam_on_after_se"] = float(r.loc["after", "coef"]), float(r.loc["after", "se"])
    # mortality as the outcome
    m = d.dropna(subset=["u5dr"])
    m = m.assign(u5_lag=m.merge(s[["key", "t", "u5dr"]].assign(t=lambda x: x.t + 0.5).rename(columns={"u5dr": "u5l"}),
                                on=["key", "t"], how="left").u5l.values).dropna(subset=["u5_lag"])
    key["mort_n"] = int(len(m))
    key["mort_r2_forecast"] = float(loso(m, "u5dr", ["fc", "fc3", "fc4", "gu"]))
    key["mort_r2_lag"] = float(loso(m, "u5dr", ["u5_lag", "gu"]))
    # does FEWS NET's forecast already use the last survey?
    r = fe_ols(d, "fc", ["gam_lag", "cur"])
    key["fc_on_lag"], key["fc_on_lag_se"] = float(r.loc["gam_lag", "coef"]), float(r.loc["gam_lag", "se"])
    # by phase forecast: mean GAM
    d["fc_round"] = d.fc.round().clip(1, 5)
    bp = d.groupby("fc_round").agg(n=("gam", "size"), gam=("gam", "mean"), crit=("crit", "mean")).reset_index()
    bp.to_csv(TAB / "fsnau_value_by_forecast.csv", index=False)
    # within zone: what does one phase mean for measured outcomes in the same zone?
    rows = []
    for y in ["gam", "cdr", "u5dr"]:
        for x in ["after", "fc"]:
            for fes in [["t"], ["key"], ["key", "t"]]:
                b_, se_, n_ = fe_slope(d, y, x, fes)
                rows.append(dict(outcome=y, phase=x, fe="+".join(fes), coef=b_, se=se_, n=n_))
    W = pd.DataFrame(rows)
    W.to_csv(TAB / "fsnau_value_within.csv", index=False)
    print(W.round(3))
    (TAB / "fsnau_value_key.json").write_text(json.dumps(key, indent=1))
    d.drop(columns=["fnids"]).assign(month=d.month.astype(str)).to_csv(TAB / "fsnau_value_panel.csv", index=False)
    pd.set_option("display.width", 200)
    print(json.dumps(key, indent=1)); print(res.round(3)); print(ch.round(3)); print(fe.round(3)); print(bp.round(2))


if __name__ == "__main__":
    main()
