"""Competing-disasters instrument for humanitarian aid: construction and first stage.

Logic: humanitarian budgets and attention are close to fixed in the short run,
so a large sudden-onset disaster on another continent should pull money away
from countries that depend on the same donors.

Two versions of the instrument, both shift-share designs with exposure shares
fixed in 2005-2010 and outcomes measured 2011-2024:

  Z_fund[c,t] = sum_d w[d,c] * log(1 + G[d, t-2..t, outside region of c])
      w[d,c]  donor d's share of country c's humanitarian funding, 2005-2010
      G       donor d's commitments to sudden-onset emergencies on other
              continents in the past three months. A flow counts as going to a
              sudden-onset emergency if its FTS emergency tag names a natural
              disaster, or if it went to a country within six months after a
              large EM-DAT sudden-onset event there (>= 1,000 deaths or
              >= 1 million affected). COVID-19 is excluded (it struck everywhere
              at once). Variant: add the onset of major wars.

  Z_dis[c,t] = R[c] * log(1 + D[t-2..t, outside region of c])
      D       deaths in EM-DAT sudden-onset disasters on other continents
      R[c]    exposure: how much c's 2005-2010 donors directed to sudden-onset
              emergencies, i.e. sum_d w[d,c] * (share of d's 2005-2010 funding
              that went to sudden-onset emergencies)
  Shifts come from nature rather than from donor decisions.

First stage: log(1 + humanitarian commitments to c in t-2..t), on Z, with
country and month fixed effects (so only differential exposure identifies),
standard errors clustered by country.

Outputs: output/tables/iv_first_stage.csv, iv_key_numbers.json,
         output/figures/iv_*.pdf, input/iv/panel.parquet
"""
import json
import re
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
(INP / "iv").mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 11, "axes.titleweight": "bold",
                     "axes.titlelocation": "left"})
ORANGE, BLUE, GREY = "#c55a11", "#1f4e79", "#8c8c8c"
KEY = {}

SUDDEN_TYPES = {"Earthquake", "Storm", "Flood", "Volcanic activity", "Mass movement (wet)",
                "Mass movement (dry)", "Epidemic"}
TAG_RX = re.compile(r"earthquake|tsunami|cyclone|typhoon|hurricane|flood|storm|nargis|haiyan|idai|"
                    r"ebola|cholera|volcan|landslide|mudslide|tropical", re.I)
WAR_RX = re.compile(r"Ukraine Crisis 2022|oPt Complex Emergency 2023|Lebanon (Crisis July 2006|Complex Emergency 2024)|"
                    r"Libya Unrest|Sudan Complex Emergency 2023", re.I)
FIX_ISO = {"Côte d'Ivoire": "CIV", "Venezuela, Bolivarian Republic of": "VEN", "Syrian Arab Republic": "SYR",
           "Democratic Republic of the Congo": "COD", "Congo, The Democratic Republic of the": "COD",
           "occupied Palestinian territory": "PSE", "Türkiye": "TUR", "Turkey": "TUR",
           "Iran, Islamic Republic of": "IRN", "Tanzania, United Republic of": "TZA", "Viet Nam": "VNM",
           "Lao People's Democratic Republic": "LAO", "Korea, Democratic People's Republic of": "PRK",
           "Moldova, Republic of": "MDA", "Bolivia, Plurinational State of": "BOL", "Micronesia, Federated States of": "FSM"}


def wrap_note(fig, text, width=160):
    fig.text(0.01, 0.01, textwrap.fill(text, width), fontsize=8, color="#555", va="bottom")


def load():
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    emdat = pd.read_excel(INP / "em-dat" / "public_emdat_2026-09-21.xlsx")
    f = pd.read_parquet(INP / "fts" / "fts_flows.parquet")
    f = f[((f.boundary == "incoming") | f.boundary.isna()) & f.status.isin(["paid", "commitment"])]
    f = f[f.amount_usd > 0].copy()
    f["month"] = pd.to_datetime(f.decision_date, errors="coerce").dt.to_period("M")
    f = f.dropna(subset=["month"])
    name2iso = {**dict(zip(codes.preferred_name, codes.iso3166a3)), **dict(zip(codes.iso_en_name, codes.iso3166a3)),
                **dict(zip(emdat.Country, emdat.ISO)), **FIX_ISO}
    f["iso3"] = f.dest_country.map(name2iso)             # multi-country flows drop out
    f = f.dropna(subset=["iso3"])
    f["donor"] = f.donor.fillna("Unknown").str.split("; ").str[0]
    region = {**dict(zip(emdat.ISO, emdat.Region))}
    f["region"] = f.iso3.map(region)
    return codes, emdat, f, region


def classify_sudden(f, emdat):
    """Flag flows that went to sudden-onset emergencies."""
    e = emdat[emdat["Disaster Type"].isin(SUDDEN_TYPES)].copy()
    e = e[~e["Event Name"].fillna("").str.contains("COVID", case=False)]
    e = e[e["Disaster Subtype"].fillna("") != "Viral disease"] if False else e
    e = e.dropna(subset=["Start Year"])
    e["start"] = pd.PeriodIndex([f"{int(y)}-{int(m) if pd.notna(m) else 1:02d}" for y, m in
                                 zip(e["Start Year"], e["Start Month"])], freq="M")
    big = e[(e["Total Deaths"].fillna(0) >= 1000) | (e["Total Affected"].fillna(0) >= 1e6)]
    # covid epidemics coded in EM-DAT are excluded above by name; also drop global epidemics
    big = big[~((big["Disaster Type"] == "Epidemic") & (big["Start Year"] == 2020))]
    win = set()
    for r in big.itertuples():
        for k in range(0, 7):
            win.add((r.ISO, r.start + k))
    tag = f.emergency.fillna("")
    f["sudden_tag"] = tag.str.contains(TAG_RX) & ~tag.str.contains("COVID", case=False)
    f["sudden_emdat"] = [(i, m) in win for i, m in zip(f.iso3, f.month)]
    f["sudden"] = f.sudden_tag | f.sudden_emdat
    f["war"] = tag.str.contains(WAR_RX)
    KEY["sudden_share_of_dollars"] = round(float(f.loc[f.sudden, "amount_usd"].sum() / f.amount_usd.sum()), 3)
    KEY["big_sudden_events"] = int(len(big))
    return f, big


def build(f, big, codes, region, sample_iso):
    months = pd.period_range("2006-01", "2024-12", freq="M")
    pre = f[(f.month >= pd.Period("2005-01", "M")) & (f.month <= pd.Period("2010-12", "M"))]
    # donor shares of each recipient's funding, pre-period; small donors pooled
    top = f.groupby("donor").amount_usd.sum().nlargest(40).index
    f["d"] = np.where(f.donor.isin(top), f.donor, "Other")
    pre = f[(f.month >= pd.Period("2005-01", "M")) & (f.month <= pd.Period("2010-12", "M"))]
    w = pre.groupby(["iso3", "d"]).amount_usd.sum()
    w = (w / w.groupby(level=0).transform("sum")).rename("w").reset_index()
    # donor propensity to fund sudden-onset emergencies, pre-period
    prop = (pre[pre.sudden].groupby("d").amount_usd.sum() / pre.groupby("d").amount_usd.sum()).fillna(0)

    regions = sorted(set(region.values()))
    # G[d, region-excluded, month]: donor commitments to sudden-onset emergencies outside region
    s = f[f.sudden]
    sw = f[f.sudden | f.war]
    def shift(src):
        g = src.groupby(["d", "region", "month"]).amount_usd.sum().reset_index()
        out = []
        for r in regions:
            x = g[g.region != r].groupby(["d", "month"]).amount_usd.sum()
            x = x.unstack(fill_value=0).reindex(columns=pd.period_range("2004-10", "2024-12", freq="M"), fill_value=0)
            x3 = x.T.rolling(3, min_periods=1).sum().T
            x3 = x3.stack().rename("G").reset_index().rename(columns={"level_1": "month"})
            x3["region"] = r
            out.append(x3)
        return pd.concat(out)
    G = shift(s)
    Gw = shift(sw)

    # EM-DAT deaths outside region, 3-month window
    e = big.copy()
    D = []
    for r in regions:
        x = e[e.Region != r].groupby("start")["Total Deaths"].sum()
        x = x.reindex(pd.period_range("2004-10", "2024-12", freq="M"), fill_value=0).rolling(3, min_periods=1).sum()
        D.append(pd.DataFrame({"month": x.index, "D": x.values, "region": r}))
    D = pd.concat(D)

    # outcome: commitments by recipient-month
    y = f.groupby(["iso3", "month"]).amount_usd.sum()
    yfood = f[f.cluster.fillna("").str.contains("Food Security|Nutrition")].groupby(["iso3", "month"]).amount_usd.sum()
    panel = pd.MultiIndex.from_product([sample_iso, months], names=["iso3", "month"]).to_frame(index=False)
    panel["region"] = panel.iso3.map(region)
    panel = panel.dropna(subset=["region"])
    a = y.unstack(fill_value=0).reindex(index=sample_iso, columns=pd.period_range("2004-10", "2024-12", freq="M"), fill_value=0)
    a3 = a.T.rolling(3, min_periods=1).sum().T.stack().rename("aid3").reset_index()
    a3.columns = ["iso3", "month", "aid3"]
    af = yfood.unstack(fill_value=0).reindex(index=sample_iso, columns=pd.period_range("2004-10", "2024-12", freq="M"), fill_value=0)
    af3 = af.T.rolling(3, min_periods=1).sum().T.stack().rename("food3").reset_index()
    af3.columns = ["iso3", "month", "food3"]
    panel = panel.merge(a3, on=["iso3", "month"], how="left").merge(af3, on=["iso3", "month"], how="left")

    def zfund(Gx, name):
        m = w.merge(Gx, on="d")
        m = m.merge(panel[["iso3", "region"]].drop_duplicates(), on=["iso3", "region"])
        m[name] = m.w * np.log1p(m.G / 1e6)
        return m.groupby(["iso3", "month"])[name].sum().reset_index()
    panel = panel.merge(zfund(G, "z_fund"), on=["iso3", "month"], how="left")
    panel = panel.merge(zfund(Gw, "z_fund_war"), on=["iso3", "month"], how="left")
    R = w.assign(p=w.d.map(prop).fillna(0)).assign(rp=lambda x: x.w * x.p).groupby("iso3").rp.sum().rename("R")
    panel = panel.merge(R, on="iso3", how="left").merge(D, on=["month", "region"], how="left")
    panel["z_dis"] = panel.R * np.log1p(panel.D)
    for c in ["z_fund", "z_fund_war", "z_dis", "R"]:
        panel[c] = panel[c].fillna(0)
    panel["ln_aid3"] = np.log1p(panel.aid3 / 1e6)
    panel["ln_food3"] = np.log1p(panel.food3 / 1e6)
    panel["year"] = panel.month.dt.year
    panel["moy"] = panel.month.dt.month
    panel["t"] = panel.month.astype(str)
    panel["has_shares"] = panel.iso3.isin(w.iso3)
    return panel, w, prop


def first_stage(panel, z, y="ln_aid3", extra="", label="", sample=None):
    d = panel if sample is None else panel[sample]
    d = d[d.has_shares & d.year.between(2011, 2024)].copy()
    for v in [z, y]:
        d[v + "_s"] = (d[v] - d[v].mean()) / d[v].std() if v == z else d[v]
    fml = f"{y} ~ {z}_s + C(iso3) + C(t){extra}"
    m = smf.ols(fml, data=d).fit(cov_type="cluster", cov_kwds={"groups": d.iso3.astype("category").cat.codes})
    b, se = m.params[f"{z}_s"], m.bse[f"{z}_s"]
    return {"spec": label, "instrument": z, "outcome": y, "coef_per_sd": b, "se": se, "t": b / se,
            "F": (b / se) ** 2, "n": int(m.nobs), "countries": d.iso3.nunique()}


def main():
    codes, emdat, f, region = load()
    f, big = classify_sudden(f, emdat)
    cs = pd.read_parquet(INP / "fewsnet" / "cs_monthly.parquet", columns=["country_code"])
    iso2to3 = dict(zip(codes.iso3166a2, codes.iso3166a3))
    fews = sorted({iso2to3[c] for c in cs.country_code.unique() if c in iso2to3})
    # all recipients with meaningful funding in the pre-period, for a larger sample
    pre_tot = f[(f.month >= pd.Period("2005-01", "M")) & (f.month <= pd.Period("2010-12", "M"))] \
        .groupby("iso3").amount_usd.sum()
    allc = sorted(pre_tot[pre_tot > 10e6].index)
    panel, w, prop = build(f, big, codes, region, sorted(set(allc) | set(fews)))
    panel["fews"] = panel.iso3.isin(fews)
    panel.to_parquet(INP / "iv" / "panel.parquet", index=False)

    rows = []
    for samp, sel in [("FEWS NET countries", panel.fews), ("All recipients", None)]:
        for z in ["z_fund", "z_dis", "z_fund_war"]:
            rows.append(first_stage(panel, z, label=f"{samp}", sample=sel))
        rows.append(first_stage(panel, "z_fund", y="ln_food3", label=f"{samp}, food and nutrition", sample=sel))
        rows.append(first_stage(panel, "z_fund", extra=" + C(iso3):C(moy)", label=f"{samp}, + country x calendar month FE",
                                sample=sel))
    fs = pd.DataFrame(rows)
    fs.to_csv(TAB / "iv_first_stage.csv", index=False)
    print(fs.round(3).to_string())
    KEY["first_stage"] = fs.round(4).to_dict("records")
    KEY["n_fews_countries_with_shares"] = int(panel[panel.fews & panel.has_shares].iso3.nunique())
    KEY["donor_propensity_top"] = prop.sort_values(ascending=False).head(10).round(3).to_dict()
    (TAB / "iv_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))


if __name__ == "__main__":
    main()
