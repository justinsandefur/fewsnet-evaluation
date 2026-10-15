"""Across countries: does humanitarian funding follow people in Phase 3+, or deaths?

Country x year, 2016-2024, countries in the Global Report on Food Crises (GRFC).
  funding   OCHA FTS incoming flows (paid + commitments, standard flows, single usage year,
            single destination country), all sectors, US$
  p3        population in IPC/CH Phase 3 or above (GRFC, peak of the year)
  u5deaths  under-five deaths (UN IGME via World Development Indicators; modelled, slow-moving)
  battle    battle-related deaths (UCDP via WDI)
Two descriptions, both deliberately simple (the death series are modelled and not crisis-specific):
  1. Within each year, countries' shares of funding against their shares of each measure;
     dissimilarity index = share of funding that would have to move between countries.
  2. Within-year regression of log funding on log P3 people, log under-five deaths and log battle
     deaths (+1), with log population, and the out-of-sample R-squared of each (leave one year out).
Outputs: output/tables/xc_aid_*.csv, output/cgd_paper/numbers_xc.tex
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, PAPER = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "cgd_paper"
WDI = ROOT / "side_survey_selection" / "data" / "raw" / "wdi.csv"
CTY = ROOT / "side_survey_selection" / "data" / "raw" / "countries.csv"
Y0, Y1 = 2016, 2024

# --- funding
f = pd.read_parquet(INP / "fts" / "fts_flows.parquet",
                    columns=["amount_usd", "status", "flow_type", "boundary", "dest_country", "usage_year"])
f = f[f.status.isin(["paid", "commitment"]) & (f.flow_type == "Standard") & (f.boundary == "incoming")]
f = f[f.usage_year.astype(str).str.fullmatch(r"\d{4}") & f.dest_country.notna() & ~f.dest_country.astype(str).str.contains(";")]
f["year"] = f.usage_year.astype(int)
cty = pd.read_csv(CTY, keep_default_na=False)
name2iso = dict(zip(cty.name, cty.iso3))
FIX = {"Syrian Arab Republic": "SYR", "Democratic Republic of the Congo": "COD", "Congo, The Democratic Republic of the": "COD",
       "occupied Palestinian territory": "PSE", "Palestine, State of": "PSE", "Yemen": "YEM", "Venezuela (Bolivarian Republic of)": "VEN",
       "Iran, Islamic Republic of": "IRN", "Türkiye": "TUR", "Turkey": "TUR", "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV",
       "Lao People's Democratic Republic": "LAO", "United Republic of Tanzania": "TZA", "Tanzania, United Republic of": "TZA",
       "Republic of Moldova": "MDA", "Moldova, Republic of": "MDA", "Egypt": "EGY", "Gambia": "GMB", "Kyrgyzstan": "KGZ",
       "Bolivia (Plurinational State of)": "BOL", "Democratic People's Republic of Korea": "PRK",
       "Korea, Democratic People's Republic of": "PRK", "Congo": "COG", "Myanmar": "MMR", "Central African Republic": "CAF",
       "Viet Nam": "VNM", "Eswatini": "SWZ", "Somalia": "SOM", "South Sudan": "SSD", "Sudan": "SDN", "Ethiopia": "ETH",
       "Afghanistan": "AFG", "Haiti": "HTI", "Niger": "NER", "Mali": "MLI", "Burkina Faso": "BFA", "Chad": "TCD", "Nigeria": "NGA"}
f["iso3"] = f.dest_country.map(lambda n: FIX.get(n, name2iso.get(n)))
F = f[f.year.between(Y0, Y1)].groupby(["iso3", "year"]).amount_usd.sum().rename("funding").reset_index()

# --- people in Phase 3+ (GRFC)
g = pd.read_excel(INP / "ipc" / "grfc_afi_database_2016-2025_september_update.xlsx")
g = g.rename(columns={"ISO Code 3": "iso3", "Year of reference": "year", "Population in Phase 3 or above #": "p3"})
g["p3"] = pd.to_numeric(g.p3, errors="coerce")
G = g.dropna(subset=["p3"]).groupby(["iso3", "year"]).p3.max().reset_index()

# --- deaths and population (WDI)
w = pd.read_csv(WDI).rename(columns={"SH.DTH.MORT": "u5deaths", "VC.BTL.DETH": "battle", "SP.POP.TOTL": "pop"})
W = w[["iso3", "year", "u5deaths", "battle", "pop"]]
W["battle"] = W.battle.fillna(0)
W["u5deaths"] = W.groupby("iso3").u5deaths.transform(lambda s: s.ffill())     # IGME series end a year early

D = G.merge(F, on=["iso3", "year"], how="inner").merge(W, on=["iso3", "year"], how="left")
D = D[D.year.between(Y0, Y1)].dropna(subset=["funding", "p3", "u5deaths", "pop"])
D = D[(D.funding > 0) & (D.p3 > 0)]
D.to_csv(TAB / "xc_aid_panel.csv", index=False)

# --- 1. dissimilarity by year
rows = []
for y, x in D.groupby("year"):
    sf = x.funding / x.funding.sum()
    out = dict(year=y, n=len(x))
    for k in ["p3", "u5deaths", "battle", "pop"]:
        out[k] = 0.5 * (sf - x[k] / x[k].sum()).abs().sum()
    rows.append(out)
DS = pd.DataFrame(rows)
DS.to_csv(TAB / "xc_aid_dissimilarity.csv", index=False)

# --- 2. within-year regressions and leave-one-year-out R2
d = D.copy()
d["y"] = np.log(d.funding)
for k in ["p3", "u5deaths", "pop"]:
    d[f"l_{k}"] = np.log(d[k])
d["l_battle"] = np.log1p(d.battle)
for c in ["y", "l_p3", "l_u5deaths", "l_pop", "l_battle"]:
    d[c] = d[c] - d.groupby("year")[c].transform("mean")


def oos(xs):
    f = "y ~ l_pop" + "".join(f" + {x}" for x in xs)
    pred = pd.Series(np.nan, index=d.index)
    for yr in d.year.unique():
        pred.loc[d.year == yr] = smf.ols(f, d[d.year != yr]).fit().predict(d[d.year == yr])
    return 1 - ((d.y - pred) ** 2).sum() / (d.y ** 2).sum()


R = {k: oos(v) for k, v in {"pop": [], "p3": ["l_p3"], "u5deaths": ["l_u5deaths"], "battle": ["l_battle"],
                            "all": ["l_p3", "l_u5deaths", "l_battle"]}.items()}
m = smf.ols("y ~ l_pop + l_p3 + l_u5deaths + l_battle", d).fit(cov_type="cluster",
                                                                cov_kwds={"groups": d.iso3.astype("category").cat.codes})
pd.DataFrame({"b": m.params, "se": m.bse, "p": m.pvalues}).to_csv(TAB / "xc_aid_regression.csv")

M = {"xcN": f"{len(D):,}", "xcCountries": f"{D.iso3.nunique()}", "xcYearZero": f"{Y0}", "xcYearOne": f"{Y1}",
     "xcDisPthree": f"{100 * DS.p3.mean():.0f}", "xcDisUfive": f"{100 * DS.u5deaths.mean():.0f}",
     "xcDisBattle": f"{100 * DS.battle.mean():.0f}", "xcDisPop": f"{100 * DS['pop'].mean():.0f}",
     "xcElastPthree": f"{m.params['l_p3']:.2f}", "xcElastPthreeSe": f"{m.bse['l_p3']:.2f}",
     "xcElastUfive": f"{m.params['l_u5deaths']:.2f}".replace("-", "\\textminus{}"),
     "xcElastUfiveSe": f"{m.bse['l_u5deaths']:.2f}",
     "xcElastBattle": f"{m.params['l_battle']:.2f}", "xcElastBattleSe": f"{m.bse['l_battle']:.2f}"}
for k, v in R.items():
    M[f"xcRtwo{ {'pop': 'Pop', 'p3': 'Pthree', 'u5deaths': 'Ufive', 'battle': 'Battle', 'all': 'All'}[k] }"] = \
        f"{v:.2f}".replace("-", "\\textminus{}")
lines = ["% Written by code/89_cross_country_aid.py -- do not edit by hand"]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()]
(PAPER / "numbers_xc.tex").write_text("\n".join(lines) + "\n")
print(len(D), D.iso3.nunique()); print(DS.round(3).to_string(index=False)); print({k: round(v, 3) for k, v in R.items()})
print(m.summary().tables[1])
print("\n".join(lines))
