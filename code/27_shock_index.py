"""Combined local shock index (rainfall, conflict, food prices) and the test of
whether its effect on food insecurity classifications changes with FEWS NET
coverage, including the 2025 shutdown.

Shocks for an analysis of area a in month t (all measured before t):
  rainfall  dryness = minus the 6- and 12-month rainfall z-scores (rolling
            20-year normal), and a drought flag (24_area_rainfall.py)
  conflict  log(1 + ACLED political violence events) and log(1 + fatalities)
            in months t-6..t-1, and the change against the same window a year
            earlier. Matched to areas by district name, else by region.
  prices    mean 12-month and 3-month log change in retail cereal and tuber
            prices across WFP markets in the area (markets placed by
            coordinates; else markets in the same region), months t-3..t-1.
  Missing conflict or price data are set to zero with a missing indicator.

Index: y = X b, with b estimated within area and country x month fixed effects
on all countries except the area's own (leave-one-country-out), so the index
for a country never uses that country's outcomes.

Test: y = beta*index + delta*index*covered + area FE + country x month FE,
with and without country-specific index slopes. Coverage: cleaned annual
history before 2025; FEWS NET reports in the month or the month before,
from 2025 (captures the shutdown and staggered restoration).

Outputs: input/panel/shock_panel.parquet, output/tables/shock_index_*.csv,
         output/figures/shock_index_*.pdf
"""
import importlib.util
import json
import re
import textwrap
import unicodedata
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
spec = importlib.util.spec_from_file_location("did", ROOT / "code" / "25_slope_did.py")
DID = importlib.util.module_from_spec(spec)
spec.loader.exec_module(DID)
spec2 = importlib.util.spec_from_file_location("rain", ROOT / "code" / "24_area_rainfall.py")
RAIN = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(RAIN)
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"], 1)}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


# ------------------------------------------------------------------ conflict
def acled():
    rows = []
    for f in sorted((INP / "acled" / "hdx").glob("*.xlsx")):
        x = pd.ExcelFile(f)
        d = x.parse(x.sheet_names[-1])
        d["iso3"] = f.stem.upper()
        rows.append(d)
    a = pd.concat(rows, ignore_index=True)
    a["month"] = pd.PeriodIndex([f"{y}-{MONTHS[m]:02d}" for y, m in zip(a.Year, a.Month)], freq="M")
    a["a2"] = a.iso3 + "|" + a.Admin2.map(norm)
    a["a1"] = a.iso3 + "|" + a.Admin1.map(norm)
    return a


def conflict_shocks(p, a):
    """Events and fatalities in t-6..t-1 for each analysis, by district then region."""
    def window_sum(g, unit):
        s = g.groupby([unit, "month"])[["Events", "Fatalities"]].sum()
        out = {}
        for u, x in s.groupby(level=0):
            x = x.droplevel(0).sort_index()
            idx = pd.period_range(x.index.min(), pd.Period("2026-09", "M"), freq="M")
            x = x.reindex(idx, fill_value=0)
            r6 = x.rolling(6, min_periods=1).sum().shift(1)          # t-6..t-1
            out[u] = r6
        return out
    d2 = window_sum(a, "a2")
    d1 = window_sum(a, "a1")
    rows = []
    for r in p[["key", "iso3", "area_name", "adm1_name", "month"]].drop_duplicates().itertuples(index=False):
        k2 = r.iso3 + "|" + norm(r.area_name)
        k1 = r.iso3 + "|" + norm(r.adm1_name) if pd.notna(r.adm1_name) else None
        src, lvl = (d2, "district") if k2 in d2 else ((d1, "region") if k1 in d1 else ((d1, "region") if (r.iso3 + "|" + norm(r.area_name)) in d1 else (None, None)))
        key = k2 if lvl == "district" else (k1 if (k1 in d1) else r.iso3 + "|" + norm(r.area_name))
        rec = {"key": r.key, "month": r.month, "conf_level": lvl}
        if src is not None and r.month in src[key].index:
            x = src[key]
            rec["ev6"], rec["fat6"] = x.loc[r.month, "Events"], x.loc[r.month, "Fatalities"]
            prev = r.month - 12
            if prev in x.index:
                rec["ev6_prev"] = x.loc[prev, "Events"]
        rows.append(rec)
    c = pd.DataFrame(rows)
    c["ln_ev6"] = np.log1p(c.ev6)
    c["ln_fat6"] = np.log1p(c.fat6)
    c["d_ln_ev6"] = c.ln_ev6 - np.log1p(c.ev6_prev)
    return c


# ------------------------------------------------------------------ prices
def wfp_prices():
    rows = []
    for f in sorted((INP / "prices").glob("*.csv")):
        try:
            d = pd.read_csv(f, skiprows=[1], low_memory=False)
        except Exception:
            continue
        d["iso3"] = f.stem.upper()
        rows.append(d)
    w = pd.concat(rows, ignore_index=True)
    w = w[(w.category.str.lower() == "cereals and tubers") & (w.pricetype.str.lower() == "retail")]
    w["month"] = pd.to_datetime(w.date, errors="coerce").dt.to_period("M")
    w = w.dropna(subset=["month", "price", "latitude", "longitude"])
    w = w[w.price > 0]
    w["series"] = w.iso3 + "|" + w.market.astype(str) + "|" + w.commodity + "|" + w.unit.astype(str)
    s = w.groupby(["series", "month"]).agg(lp=("price", lambda x: np.log(x).mean()), iso3=("iso3", "first"),
                                           market=("market", "first"), admin1=("admin1", "first"),
                                           lat=("latitude", "first"), lon=("longitude", "first")).reset_index()
    s = s.sort_values(["series", "month"])
    s["mi"] = s.month.astype("int64")
    for k in [3, 12]:
        prev = s[["series", "mi", "lp"]].copy()
        prev["mi"] = prev.mi + k
        s = s.merge(prev.rename(columns={"lp": f"lp_{k}"}), on=["series", "mi"], how="left")
        s[f"dp{k}"] = s.lp - s[f"lp_{k}"]
    m = s.groupby(["iso3", "market", "month"]).agg(dp12=("dp12", "mean"), dp3=("dp3", "mean"), lat=("lat", "first"),
                                                   lon=("lon", "first"), admin1=("admin1", "first")).reset_index()
    return m


def price_shocks(p, m, geo):
    mk = m.drop_duplicates(["iso3", "market"])[["iso3", "market", "lat", "lon", "admin1"]]
    pts = gpd.GeoDataFrame(mk, geometry=gpd.points_from_xy(mk.lon, mk.lat), crs=4326)
    keys = set(p.key)
    g = geo[geo.key.isin(keys)]
    j = gpd.sjoin(pts, g[["key", "geometry"]], how="left", predicate="within")
    market_area = j.dropna(subset=["key"])[["iso3", "market", "key"]]
    m2 = m.merge(market_area, on=["iso3", "market"], how="left")
    m2["a1"] = m2.iso3 + "|" + m2.admin1.map(norm)
    # average over months t-3..t-1 for each area (spatial), and each region (by name)
    def lagged(df, unit):
        x = df.dropna(subset=[unit]).groupby([unit, "month"])[["dp12", "dp3"]].mean()
        out = {}
        for u, y in x.groupby(level=0):
            y = y.droplevel(0).sort_index()
            idx = pd.period_range(y.index.min(), pd.Period("2026-09", "M"), freq="M")
            out[u] = y.reindex(idx).rolling(3, min_periods=1).mean().shift(1)
        return out
    by_area = lagged(m2, "key")
    by_reg = lagged(m2, "a1")
    rows = []
    for r in p[["key", "iso3", "adm1_name", "month"]].drop_duplicates().itertuples(index=False):
        rec = {"key": r.key, "month": r.month, "price_level": None}
        k1 = r.iso3 + "|" + norm(r.adm1_name) if pd.notna(r.adm1_name) else None
        for src, k, lvl in [(by_area, r.key, "area"), (by_reg, k1, "region")]:
            if k in src and r.month in src[k].index and pd.notna(src[k].loc[r.month, "dp12"]):
                rec["dp12"], rec["dp3"] = src[k].loc[r.month, "dp12"], src[k].loc[r.month, "dp3"]
                rec["price_level"] = lvl
                break
        rows.append(rec)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ coverage
def coverage(p):
    H = pd.read_csv(TAB / "coverage_history.csv")
    H = H[H.year <= 2024].sort_values(["iso3", "year"])
    # gaps of one or two years between covered years (e.g. Burkina Faso 2018-19, Mauritania 2019)
    # are holes in the archive, not exits: FEWS NET kept reporting on these countries
    for c, g in H.groupby("iso3"):
        v = g.covered.astype(bool).values
        for i in range(len(v)):
            if not v[i] and v[:i].any() and v[i + 1:i + 3].any():
                H.loc[g.index[i], "covered"] = True
    H = H.set_index(["iso3", "year"]).covered
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    iso2to3 = dict(zip(codes.iso3166a2, codes.iso3166a3))
    cls = pd.read_parquet(INP / "fewsnet" / "classifications.parquet", columns=["country_code", "report_month"])
    api = set(zip(cls.country_code.map(iso2to3), cls.report_month))
    out = []
    for i, m in zip(p.iso3, p.month):
        if m.year <= 2024:
            out.append(float(H.get((i, m.year), False)))
        else:
            out.append(float(any((i, m - k) in api for k in range(0, 2))))
    return np.array(out)


# ------------------------------------------------------------------ index
FEATURES = ["dry6", "dry12", "drought", "ln_ev6", "ln_fat6", "d_ln_ev6", "dp12", "dp3",
            "miss_conf", "miss_price"]


def build_index(p, y):
    d = p.dropna(subset=[y]).copy()
    for fe in ["key", "cm"]:
        d = d[d.groupby(fe)[y].transform("size") > 1]
    w = DID.within(d, [y] + FEATURES, ["key", "cm"])
    idx = pd.Series(np.nan, index=d.index)
    coefs = {}
    for c in d.iso3.unique():
        tr = d.iso3 != c
        X, Y = w.loc[tr, FEATURES].values, w.loc[tr, y].values
        b = np.linalg.lstsq(X, Y, rcond=None)[0]
        coefs[c] = b
        idx[~tr] = d.loc[~tr, FEATURES].values @ b
    full = np.linalg.lstsq(w[FEATURES].values, w[y].values, rcond=None)[0]
    return idx, pd.Series(full, index=FEATURES), pd.DataFrame(coefs, index=FEATURES).T


def main():
    p = pd.read_parquet(INP / "panel" / "analysis_panel.parquet")
    outcomes = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    geo, _ = RAIN.area_geometries(outcomes)
    a = acled()
    c = conflict_shocks(p, a)
    m = wfp_prices()
    pr = price_shocks(p, m, geo)
    c = c.sort_values("conf_level").drop_duplicates(["key", "month"])     # district match preferred
    pr = pr.sort_values("price_level").drop_duplicates(["key", "month"])  # area match preferred
    p = p.merge(c, on=["key", "month"], how="left").merge(pr, on=["key", "month"], how="left")
    p["dry6"], p["dry12"] = -p.rain_z6.clip(-4, 4), -p.rain_z12.clip(-4, 4)
    p["miss_conf"] = p.ln_ev6.isna().astype(float)
    p["miss_price"] = p.dp12.isna().astype(float)
    for v in ["ln_ev6", "ln_fat6", "d_ln_ev6", "dp12", "dp3"]:
        p[v] = p[v].fillna(0).clip(-3, 12)
    p["dp12"], p["dp3"] = p.dp12.clip(-1.5, 1.5), p.dp3.clip(-1, 1)
    p = p.dropna(subset=["dry6", "dry12", "drought"])
    assert np.isfinite(p[FEATURES].values).all()
    p["covd"] = coverage(p)
    p["phase3"] = (p.phase >= 3).astype(float)
    p["cm"] = p.iso3 + "_" + p.month.astype(str)
    p.to_parquet(INP / "panel" / "shock_panel.parquet", index=False)
    cov = p.groupby("source")[["miss_conf", "miss_price"]].mean().round(3)
    print("share missing conflict / price data by source:\n", cov)

    results, weights = [], {}
    for y in ["share3", "phase3"]:
        idx, full, loo = build_index(p, y)
        p[f"index_{y}"] = idx
        weights[y] = full
        loo.to_csv(TAB / f"shock_index_loo_weights_{y}.csv")
        # predictive power of each component and of the index (within area and country-month)
        d = p.dropna(subset=[f"index_{y}"]).copy()
        d["ix"] = (d[f"index_{y}"] - d[f"index_{y}"].mean()) / d[f"index_{y}"].std()
        r, n, G = DID.fe_ols(d, y, ["ix"], ["key", "cm"])
        results.append({"outcome": y, "spec": "index alone (predictive power)", "sample": "all",
                        "term": "index (per SD)", "coef": r.coef["ix"], "se": r.se["ix"], "n": n, "countries": G})
        for lab, sel in [("pre-2025", d.month <= pd.Period("2024-12", "M")),
                         ("2025-26 (shutdown and restoration)", d.month >= pd.Period("2025-01", "M")),
                         ("all", d.month > pd.Period("2000-01", "M"))]:
            dd = d[sel].copy()
            dd["ix_cov"] = dd.ix * dd.covd
            r, n, G = DID.fe_ols(dd, y, ["ix", "ix_cov"], ["key", "cm"])
            for t in ["ix", "ix_cov"]:
                results.append({"outcome": y, "spec": "common slope", "sample": lab,
                                "term": {"ix": "index (per SD)", "ix_cov": "index x FEWS NET covering"}[t],
                                "coef": r.coef[t], "se": r.se[t], "n": n, "countries": G})
            cs = []
            for cc in dd.iso3.unique():
                dd[f"s_{cc}"] = dd.ix * (dd.iso3 == cc)
                cs.append(f"s_{cc}")
            r, n, G = DID.fe_ols(dd, y, ["ix_cov"] + cs, ["key", "cm"])
            nsw = int(dd.groupby("iso3").covd.agg(lambda v: 0 < v.mean() < 1).sum())
            results.append({"outcome": y, "spec": f"country-specific slopes ({nsw} switching countries)", "sample": lab,
                            "term": "index x FEWS NET covering", "coef": r.coef["ix_cov"], "se": r.se["ix_cov"],
                            "n": n, "countries": G})
    # leave-one-switching-country-out, pre-2025, country-specific slopes (Phase 3+ indicator)
    d = p[(p.month <= pd.Period("2024-12", "M"))].dropna(subset=["index_phase3"]).copy()
    d["ix"] = (d.index_phase3 - p.index_phase3.mean()) / p.index_phase3.std()
    d["ix_cov"] = d.ix * d.covd
    sw = sorted(d.groupby("iso3").covd.agg(lambda v: 0 < v.mean() < 1).loc[lambda x: x].index)
    def slopes(q):
        q = q.copy(); xs = ["ix_cov"]
        for cc in q.iso3.unique():
            q[f"s_{cc}"] = q.ix * (q.iso3 == cc); xs.append(f"s_{cc}")
        r, n, G = DID.fe_ols(q, "phase3", xs, ["key", "cm"])
        return r.loc["ix_cov"]
    lo = []
    for cc in sw:
        for spec_, fn in [("common slope", lambda q: DID.fe_ols(q.assign(), "phase3", ["ix", "ix_cov"], ["key", "cm"])[0].loc["ix_cov"]),
                          ("country-specific slopes", slopes)]:
            r = fn(d[d.iso3 != cc])
            lo.append({"dropped": cc, "spec": spec_, "coef": r.coef, "se": r.se})
    pd.DataFrame(lo).to_csv(TAB / "shock_index_leaveout.csv", index=False)
    # predictive power: within R-squared of each component group and of the full set
    groups = {"rainfall": ["dry6", "dry12", "drought"], "conflict": ["ln_ev6", "ln_fat6", "d_ln_ev6", "miss_conf"],
              "food prices": ["dp12", "dp3", "miss_price"], "all three": FEATURES}
    pw = []
    for fes, lab in [(["key", "cm"], "area + country x month FE"), (["key", "mo"], "area + month FE")]:
        q = p.assign(mo=p.month.astype(str))
        for fe in fes:
            q = q[q.groupby(fe).phase3.transform("size") > 1]
        for y in ["share3", "phase3"]:
            w = DID.within(q, [y] + FEATURES, fes)
            for g, xs in groups.items():
                X, Y = w[xs].values, w[y].values
                b = np.linalg.lstsq(X, Y, rcond=None)[0]
                pw.append({"fe": lab, "outcome": y, "shocks": g, "within_r2": 1 - ((Y - X @ b) ** 2).sum() / (Y ** 2).sum()})
    pw = pd.DataFrame(pw)
    pw.to_csv(TAB / "shock_index_power.csv", index=False)
    print(pw.pivot_table(index=["fe", "outcome"], columns="shocks", values="within_r2").round(4))
    R = pd.DataFrame(results)
    R["t"] = R.coef / R.se
    R.to_csv(TAB / "shock_index_results.csv", index=False)
    pd.DataFrame(weights).to_csv(TAB / "shock_index_weights.csv")
    pd.set_option("display.width", 220)
    print(pd.DataFrame(weights).round(4))
    print(R.round(4).to_string())
    figure(R, pw, pd.DataFrame(lo))


def figure(R, pw, lo):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw={"width_ratios": [1, 1.25]})
    a = ax[0]
    q = pw[pw.outcome == "share3"].pivot(index="shocks", columns="fe", values="within_r2")
    q = q.loc[["rainfall", "food prices", "conflict", "all three"]] * 100
    y = np.arange(len(q))
    a.barh(y + 0.2, q["area + month FE"], 0.4, color="#9ecae1", label="Within area and month\n(national shocks count)")
    a.barh(y - 0.2, q["area + country x month FE"], 0.4, color="#1f4e79",
           label="Within area and country-month\n(local shocks only: the test)")
    a.set_yticks(y, q.index)
    a.set_xlabel("Share of variation in the population share in Crisis or worse\nexplained by the shocks (%)")
    a.set_title("A. The shocks barely predict the classifications", loc="left", fontweight="bold", fontsize=10.5)
    a.legend(fontsize=8, loc="lower right", frameon=False)
    a = ax[1]
    rows = R[(R.outcome == "phase3") & (R.term == "index x FEWS NET covering")].reset_index(drop=True)
    labs = [f"{r.sample}\n{r.spec}" for r in rows.itertuples()]
    yy = np.arange(len(rows))[::-1]
    a.errorbar(rows.coef, yy, xerr=1.96 * rows.se, fmt="o", color="#1f4e79", capsize=3, zorder=3)
    for i, r in enumerate(rows.itertuples()):
        if r.sample == "pre-2025":
            sp = "country-specific slopes" if "country" in r.spec else "common slope"
            z = lo[lo.spec == sp]
            a.scatter(z.coef, np.full(len(z), yy[i]) - 0.22, s=14, color="#e6550d", zorder=4,
                      label="Dropping one switching country at a time" if i == 0 else None)
            for t in z.itertuples():
                if t.dropped == "CMR":
                    a.annotate("without\nCameroon", (t.coef, yy[i] - 0.22), xytext=(0, -20), textcoords="offset points",
                               fontsize=7, color="#e6550d", ha="center")
    a.axvline(0, color="#999", lw=0.8)
    a.set_yticks(yy, labs, fontsize=8)
    a.set_xlabel("Extra effect of a 1 SD shock on the chance an area is in Crisis or worse\nwith FEWS NET covering the country\n(negative = warnings soften the blow)")
    a.set_title("B. Does FEWS NET coverage change what shocks do?", loc="left", fontweight="bold", fontsize=10.5)
    a.legend(fontsize=8, loc="center right", frameon=False)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.text(0.01, 0.01, textwrap.fill(
        "Outcome: Cadre Harmonise (West Africa, 2014-26) and IPC (2017-26) area classifications, independent of FEWS NET's "
        "own maps. Shock index: rainfall deficits (CHIRPS), political violence events and deaths (ACLED, sub-national for "
        "19 countries) and cereal price changes (WFP markets), all measured before the analysis month, weighted to predict "
        "classifications in other countries (leave-one-country-out). Coverage: annual FEWS NET reporting before 2025 "
        "(one- and two-year archive gaps filled); monthly reports from 2025 (shutdown January-July 2025, staggered restoration). "
        "All regressions: area and country x month fixed effects; 95% intervals clustered by country.", 215),
        fontsize=7.5, color="#555")
    fig.savefig(FIG / "shock_index.pdf")
    fig.savefig(FIG / "shock_index.png", dpi=150)


if __name__ == "__main__":
    main()
