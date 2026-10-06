"""Does crowd-out exist? Diagnostics behind the competing-disasters instrument.

(1) Donor-level test. Panel of donor d x recipient c x quarter q (FEWS NET
    recipients, top donors). Does a donor give less to c in quarters when it is
    committing heavily to sudden-onset emergencies on other continents?
        y[d,c,q] = g * log(1 + G[d,q,outside c's region]) + FE[c,q] + FE[d,c] + e
    Recipient x quarter fixed effects absorb all need in c, so g compares donors
    in the same recipient-quarter that were more or less busy elsewhere.
    Also: lags of G (crowd-out may arrive later) and the extensive margin.

(2) Timing. Country-level first stage with windows of 3, 6 and 12 months.

(3) Mega-events. Funding to FEWS NET countries by month around the largest
    sudden-onset emergencies, relative to the same calendar months a year
    earlier.

Outputs: output/tables/iv_donor_level.csv, iv_windows.csv,
         output/figures/iv_mega_events.pdf, additions to iv_key_numbers.json
"""
import importlib.util
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("iv", ROOT / "code" / "15_instrument.py")
IV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IV)
INP, TAB, FIG = IV.INP, IV.TAB, IV.FIG
KEY = json.loads((TAB / "iv_key_numbers.json").read_text())


def demean(df, y, x, fes):
    """Within transformation for several fixed effects by alternating projections."""
    d = df[[y] + x + fes].copy()
    cols = [y] + x
    for _ in range(50):
        old = d[cols].copy()
        for fe in fes:
            d[cols] = d[cols] - d.groupby(fe)[cols].transform("mean")
        if np.max(np.abs(d[cols].values - old.values)) < 1e-9:
            break
    return d


def ols_cluster(d, y, x, cluster):
    X = d[x].values
    Y = d[y].values
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ Y
    u = Y - X @ b
    meat = np.zeros((len(x), len(x)))
    for _, idx in d.groupby(cluster).indices.items():
        s = X[idx].T @ u[idx]
        meat += np.outer(s, s)
    G = d[cluster].nunique()
    V = XtX_inv @ meat @ XtX_inv * G / (G - 1)
    return b, np.sqrt(np.diag(V))


def donor_level(f, fews_iso, region):
    f = f.copy()
    f["q"] = f.month.dt.asfreq("Q")
    top = f[f.iso3.isin(fews_iso)].groupby("donor").amount_usd.sum().nlargest(25).index
    f = f[f.donor.isin(top)]
    qs = pd.period_range("2006Q1", "2024Q4", freq="Q")
    # donor commitments to sudden-onset emergencies, by region and quarter
    s = f[f.sudden].groupby(["donor", "region", "q"]).amount_usd.sum()
    tot = f[f.sudden].groupby(["donor", "q"]).amount_usd.sum()
    y = f[f.iso3.isin(fews_iso)].groupby(["donor", "iso3", "q"]).amount_usd.sum()
    idx = pd.MultiIndex.from_product([top, fews_iso, qs], names=["donor", "iso3", "q"])
    p = y.reindex(idx, fill_value=0).rename("y").reset_index()
    p["region"] = p.iso3.map(region)
    tot_r = tot.reindex(pd.MultiIndex.from_product([top, qs]), fill_value=0)
    def outside(dn, rg, q):
        inside = s.get((dn, rg, q), 0.0)
        return tot_r.get((dn, q), 0.0) - inside
    p["G"] = [outside(dn, rg, q) for dn, rg, q in zip(p.donor, p.region, p.q)]
    p = p.sort_values(["donor", "iso3", "q"])
    for k in [1, 2]:
        p[f"G_l{k}"] = p.groupby(["donor", "iso3"]).G.shift(k)
    p["lnG"], p["lnG_l1"], p["lnG_l2"] = [np.log1p(p[c].fillna(0) / 1e6) for c in ["G", "G_l1", "G_l2"]]
    p["lny"] = np.log1p(p.y / 1e6)
    p["any"] = (p.y > 0).astype(float)
    p["cq"] = p.iso3 + "_" + p.q.astype(str)
    p["dc"] = p.donor + "_" + p.iso3
    p["dq_year"] = p.donor + "_" + p.q.dt.year.astype(str)
    p = p[p.q.dt.year.between(2011, 2024)]
    rows = []
    for yv in ["lny", "any"]:
        for xs, lab in [(["lnG"], "same quarter"), (["lnG", "lnG_l1", "lnG_l2"], "with two lags")]:
            for fes, fl in [(["cq", "dc"], "recipient x quarter, donor x recipient"),
                            (["cq", "dc", "dq_year"], "+ donor x year")]:
                d = demean(p, yv, xs, fes)
                d["donor"] = p.donor.values
                sd = d[xs].std()
                if (sd < 1e-8).any():
                    print("no variation left in", list(sd[sd < 1e-8].index), "with", fl)
                    continue
                b, se = ols_cluster(d, yv, xs, "donor")
                for v, bb, ss in zip(xs, b, se):
                    rows.append({"outcome": yv, "regressors": lab, "fixed_effects": fl, "term": v,
                                 "coef": bb, "se": ss, "t": bb / ss, "n": len(d), "donors": p.donor.nunique()})
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "iv_donor_level.csv", index=False)
    print(r.round(4).to_string())
    KEY["donor_level"] = r.round(4).to_dict("records")
    return p


def windows(panel):
    rows = []
    d0 = panel[panel.fews & panel.has_shares].sort_values(["iso3", "month"]).copy()
    for win in [3, 6, 12]:
        d = d0.copy()
        for c in ["aid3"]:
            d["y"] = np.log1p(d.groupby("iso3").aid3.transform(lambda s: s.rolling(max(1, win // 3), min_periods=1).sum()) / 1e6)
        for lag in [0, 3, 6]:
            dd = d.copy()
            dd["z"] = dd.groupby("iso3").z_fund.shift(lag)
            dd = dd[dd.year.between(2011, 2024)].dropna(subset=["z"])
            dd["z"] = (dd.z - dd.z.mean()) / dd.z.std()
            m = smf.ols("y ~ z + C(iso3) + C(t)", data=dd).fit(
                cov_type="cluster", cov_kwds={"groups": dd.iso3.astype("category").cat.codes})
            rows.append({"window_months": win, "instrument_lag_months": lag, "coef_per_sd": m.params["z"],
                         "se": m.bse["z"], "F": (m.params["z"] / m.bse["z"]) ** 2})
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "iv_windows.csv", index=False)
    print(r.round(3).to_string())
    KEY["windows"] = r.round(4).to_dict("records")


def mega_events(f, fews_iso):
    events = [("Haiti earthquake", "2010-01"), ("Pakistan floods", "2010-08"), ("Japan tsunami", "2011-03"),
              ("Typhoon Haiyan", "2013-11"), ("Nepal earthquake", "2015-04"), ("Ukraine invasion", "2022-02"),
              ("Pakistan floods", "2022-08"), ("Türkiye-Syria earthquake", "2023-02")]
    m = f[f.iso3.isin(fews_iso)].groupby("month").amount_usd.sum()
    m = m.reindex(pd.period_range("2005-01", "2025-12", freq="M"), fill_value=0)
    rows = []
    for name, start in events:
        t0 = pd.Period(start, "M")
        for k in range(-6, 13):
            cur = m.get(t0 + k, np.nan)
            base = m.get(t0 + k - 12, np.nan)
            rows.append({"event": name, "start": start, "rel": k,
                         "ratio": np.log(cur / base) if cur > 0 and base > 0 else np.nan})
    r = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for name, g in r.groupby(["event", "start"]):
        s = g.set_index("rel").ratio.rolling(3, center=True, min_periods=1).mean()
        ax.plot(s.index, s.values, color=IV.GREY, alpha=0.6, lw=1)
        ax.text(12.2, s.iloc[-1], f"{name[0]} {name[1][:4]}", fontsize=7, color="#555", va="center")
    avg = r.groupby("rel").ratio.mean().rolling(3, center=True, min_periods=1).mean()
    ax.plot(avg.index, avg.values, color=IV.ORANGE, lw=3, label="Average across events")
    ax.axvline(0, color="black", lw=1)
    ax.axhline(0, color=IV.GREY, lw=0.8, ls="--")
    ax.set_xlabel("Months relative to the start of the competing emergency")
    ax.set_ylabel("Humanitarian funding to FEWS NET countries\n(log ratio to the same month a year earlier)")
    ax.set_title("Funding to famine-prone countries around the largest sudden emergencies elsewhere")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout(rect=(0, 0.06, 0.93, 1))
    IV.wrap_note(fig, "Total humanitarian commitments to the countries FEWS NET covers, by decision month, compared with the "
                 "same month a year earlier (3-month moving average). Grey lines: individual events; orange: average. A "
                 "crowd-out effect would show as a dip after month 0. Source: UN Financial Tracking Service.")
    fig.savefig(FIG / "iv_mega_events.pdf")
    plt.close(fig)
    post = r[r.rel.between(1, 6)].groupby("event").ratio.mean()
    KEY["mega_events_post_1to6"] = post.round(3).to_dict()





def country_quarterly(f, fews_iso, region):
    """Country-level first stage built from the donor-level pattern: lagged,
    within-budget-year shifts. shift[d,q] = log(1 + G[d,q,outside region]) minus
    donor d's mean of that quantity over the calendar year; z[c,q] sums shifts
    weighted by 2005-2010 donor shares, lagged one and two quarters."""
    f = f.copy()
    f["q"] = f.month.dt.asfreq("Q")
    top = f.groupby("donor").amount_usd.sum().nlargest(40).index
    f["d"] = np.where(f.donor.isin(top), f.donor, "Other")
    pre = f[f.q.dt.year.between(2005, 2010)]
    w = pre.groupby(["iso3", "d"]).amount_usd.sum()
    w = (w / w.groupby(level=0).transform("sum")).rename("w").reset_index()
    qs = pd.period_range("2005Q1", "2024Q4", freq="Q")
    regions = sorted(set(region.values()))
    s = f[f.sudden].groupby(["d", "region", "q"]).amount_usd.sum()
    tot = f[f.sudden].groupby(["d", "q"]).amount_usd.sum()
    rows = []
    for r in regions:
        for dn in w.d.unique():
            for q in qs:
                g = tot.get((dn, q), 0.0) - s.get((dn, r, q), 0.0)
                rows.append((dn, r, q, np.log1p(g / 1e6)))
    G = pd.DataFrame(rows, columns=["d", "region", "q", "lnG"])
    G["yr"] = G.q.dt.year
    G["shift"] = G.lnG - G.groupby(["d", "region", "yr"]).lnG.transform("mean")
    G = G.sort_values(["d", "region", "q"])
    for k in [1, 2]:
        G[f"shift_l{k}"] = G.groupby(["d", "region"])["shift"].shift(k)
        G[f"lnG_l{k}"] = G.groupby(["d", "region"]).lnG.shift(k)
    sample = sorted(set(fews_iso) & set(w.iso3))
    P = pd.MultiIndex.from_product([sample, qs], names=["iso3", "q"]).to_frame(index=False)
    P["region"] = P.iso3.map(region)
    m = w[w.iso3.isin(sample)].merge(P, on="iso3").merge(G, on=["d", "region", "q"])
    for c in ["shift", "shift_l1", "shift_l2", "lnG", "lnG_l1", "lnG_l2"]:
        m[c + "_w"] = m.w * m[c]
    Z = m.groupby(["iso3", "q"])[[c + "_w" for c in ["shift", "shift_l1", "shift_l2", "lnG", "lnG_l1", "lnG_l2"]]].sum()
    y = f[f.iso3.isin(sample)].groupby(["iso3", "q"]).amount_usd.sum()
    P = P.merge(Z.reset_index(), on=["iso3", "q"], how="left")
    P["y"] = np.log1p(P.set_index(["iso3", "q"]).index.map(y).fillna(0).astype(float) / 1e6)
    P["t"] = P.q.astype(str)
    P = P[P.q.dt.year.between(2011, 2024)].dropna()
    for c in [c for c in P.columns if c.endswith("_w")]:
        P[c] = (P[c] - P[c].mean()) / P[c].std()
    rows = []
    for xs, lab in [(["lnG_w"], "levels, same quarter"),
                    (["lnG_l1_w", "lnG_l2_w"], "levels, lags 1-2"),
                    (["shift_l1_w", "shift_l2_w"], "within-year shifts, lags 1-2"),
                    (["shift_w", "shift_l1_w", "shift_l2_w"], "within-year shifts, lags 0-2")]:
        mm = smf.ols("y ~ " + " + ".join(xs) + " + C(iso3) + C(t)", data=P).fit(
            cov_type="cluster", cov_kwds={"groups": P.iso3.astype("category").cat.codes})
        lag_terms = [x for x in xs if "_l" in x] or xs
        R = np.zeros((len(lag_terms), len(mm.params)))
        for i, x in enumerate(lag_terms):
            R[i, list(mm.params.index).index(x)] = 1
        F = float(mm.f_test(R).fvalue)
        for x in xs:
            rows.append({"spec": lab, "term": x, "coef_per_sd": mm.params[x], "se": mm.bse[x],
                         "joint_F_excluded_lags": F, "n": int(mm.nobs), "countries": P.iso3.nunique()})
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "iv_country_quarterly.csv", index=False)
    print(r.round(3).to_string())
    KEY["country_quarterly"] = r.round(4).to_dict("records")


if __name__ == "__main__":
    codes, emdat, f, region = IV.load()
    f, big = IV.classify_sudden(f, emdat)
    panel = pd.read_parquet(INP / "iv" / "panel.parquet")
    fews_iso = sorted(panel[panel.fews].iso3.unique())
    donor_level(f, fews_iso, region)
    windows(panel)
    mega_events(f, fews_iso)
    country_quarterly(f, fews_iso, region)
    (TAB / "iv_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))


CURRENCY = {"European Commission": "EUR", "Germany": "EUR", "France": "EUR", "Netherlands": "EUR",
            "Italy": "EUR", "Spain": "EUR", "Ireland": "EUR", "Belgium": "EUR", "Finland": "EUR",
            "Austria": "EUR", "Luxembourg": "EUR", "Portugal": "EUR", "United Kingdom": "GBP",
            "Japan": "JPY", "Canada": "CAD", "Sweden": "SEK", "Norway": "NOK", "Switzerland": "CHF",
            "Denmark": "DKK", "Australia": "AUD"}
FRED = {"EUR": ("DEXUSEU", False), "GBP": ("DEXUSUK", False), "AUD": ("DEXUSAL", False),
        "JPY": ("DEXJPUS", True), "CAD": ("DEXCAUS", True), "SEK": ("DEXSDUS", True),
        "NOK": ("DEXNOUS", True), "CHF": ("DEXSZUS", True), "DKK": ("DEXDNUS", True)}


def fx_instrument(f, fews_iso):
    """Donor-currency shift-share: z[c,q] = sum_d w[d,c] * log(USD value of one
    unit of donor d's currency), with 2005-2010 donor shares. US dollar and
    dollar-pegged donors (US, Gulf states, UN pooled funds) contribute zero."""
    fx = {}
    for cur, (sid, invert) in FRED.items():
        s = pd.read_csv(INP / "fx" / f"{sid}.csv")
        s.columns = ["date", "v"]
        s["v"] = pd.to_numeric(s.v, errors="coerce")
        s["q"] = pd.to_datetime(s.date).dt.to_period("Q")
        v = s.groupby("q").v.mean()
        fx[cur] = np.log(1 / v) if invert else np.log(v)
    fx = pd.DataFrame(fx)
    f = f.copy()
    f["q"] = f.month.dt.asfreq("Q")
    def cur_of(donor):
        for k, c in CURRENCY.items():
            if donor.startswith(k):
                return c
        return None
    f["cur"] = f.donor.map(cur_of)
    pre = f[f.q.dt.year.between(2005, 2010) & f.iso3.isin(fews_iso)]
    w = pre.groupby(["iso3", "cur"], dropna=False).amount_usd.sum()
    w = (w / w.groupby(level=0).transform("sum")).rename("w").reset_index().dropna(subset=["cur"])
    qs = pd.period_range("2011Q1", "2024Q4", freq="Q")
    P = pd.MultiIndex.from_product([sorted(set(fews_iso) & set(pre.iso3)), qs], names=["iso3", "q"]).to_frame(index=False)
    m = w.merge(P, on="iso3")
    m["x"] = m.w * [fx.loc[q, c] - fx[c].loc["2005Q1":"2010Q4"].mean() for q, c in zip(m.q, m.cur)]
    Z = m.groupby(["iso3", "q"]).x.sum().rename("z_fx")
    eur_share = w.groupby("iso3").w.sum().rename("nonusd_share")
    y = f[f.iso3.isin(fews_iso)].groupby(["iso3", "q"]).amount_usd.sum()
    P = P.merge(Z.reset_index(), on=["iso3", "q"], how="left").fillna({"z_fx": 0})
    P["y"] = np.log1p(P.set_index(["iso3", "q"]).index.map(y).fillna(0).astype(float) / 1e6)
    P["t"] = P.q.astype(str)
    P["z"] = (P.z_fx - P.z_fx.mean()) / P.z_fx.std()
    rows = []
    for lag in [0, 1, 2, 4]:
        d = P.sort_values(["iso3", "q"]).copy()
        d["zl"] = d.groupby("iso3").z.shift(lag)
        d = d.dropna(subset=["zl"])
        mm = smf.ols("y ~ zl + C(iso3) + C(t)", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": d.iso3.astype("category").cat.codes})
        rows.append({"lag_quarters": lag, "coef_per_sd": mm.params["zl"], "se": mm.bse["zl"],
                     "F": (mm.params["zl"] / mm.bse["zl"]) ** 2, "n": int(mm.nobs), "countries": d.iso3.nunique()})
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "iv_fx.csv", index=False)
    print(r.round(3).to_string())
    print("non-USD donor share of pre-period funding, FEWS NET countries:", eur_share.describe().round(2).to_dict())
    KEY["fx"] = r.round(4).to_dict("records")
    KEY["fx_nonusd_share"] = eur_share.describe().round(3).to_dict()


if __name__ == "__main__":
    fx_instrument(f, fews_iso)
    (TAB / "iv_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))


def us_cut(f, fews_iso):
    """The 2025 US aid cut as an aid supply shock: change in log humanitarian
    commitments 2024->2025 on the recipient's 2021-2023 US share."""
    f = f.copy()
    f["year"] = f.month.dt.year
    f["us"] = f.donor.str.startswith("United States")
    pre = f[f.year.between(2021, 2023)]
    us = (pre[pre.us].groupby("iso3").amount_usd.sum() / pre.groupby("iso3").amount_usd.sum()).rename("us_share")
    y = f.groupby(["iso3", "year"]).amount_usd.sum().unstack()
    yn = f[~f.us].groupby(["iso3", "year"]).amount_usd.sum().unstack()
    d = pd.DataFrame({"us_share": us}).join(y[[2024, 2025]]).dropna()
    d = d[d[2024] > 20e6]
    d["dlog"] = np.log(d[2025] + 1e5) - np.log(d[2024] + 1e5)
    d["dnon"] = (np.log(yn[2025].reindex(d.index).fillna(0) + 1e5) - np.log(yn[2024].reindex(d.index).fillna(0) + 1e5))
    d["fews"] = d.index.isin(fews_iso)
    rows = []
    for lab, s in [("All recipients", d), ("FEWS NET countries", d[d.fews])]:
        for yv in ["dlog", "dnon"]:
            m = smf.ols(f"{yv} ~ us_share", data=s).fit(cov_type="HC1")
            rows.append({"sample": lab, "outcome": {"dlog": "all donors", "dnon": "non-US donors"}[yv],
                         "coef": m.params["us_share"], "se": m.bse["us_share"],
                         "F": (m.params["us_share"] / m.bse["us_share"]) ** 2, "n": len(s)})
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "iv_us_cut.csv", index=False)
    print(r.round(3).to_string())
    KEY["us_cut"] = r.round(4).to_dict("records")


if __name__ == "__main__":
    us_cut(f, fews_iso)
    (TAB / "iv_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))
