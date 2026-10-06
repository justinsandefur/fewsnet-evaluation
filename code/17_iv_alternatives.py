"""Alternative instruments for humanitarian aid, from the aid literature.

Each is tested for first-stage strength on log humanitarian commitments to
FEWS NET countries (UN Financial Tracking Service), with country and time
fixed effects and standard errors clustered by country.

  A. Donor budget shocks (leave-out shift-share). z[c,y] = sum_d w[d,c] *
     log(donor d's humanitarian commitments to all countries outside c's
     region in year y). Shares w from 2005-2010. Captures donor-side budget
     changes from any source (e.g. UK 2021 cut, Gulf surges).
  B. US fiscal calendar / continuing resolutions. US humanitarian obligations
     bunch at the end of the US fiscal year (July-September) and are delayed
     by continuing resolutions and shutdowns. z[c,q] = US share of c's
     funding x (US commitments to the rest of the world in quarter q,
     relative to the US fiscal-year average).
  C. UN Security Council membership (Kuziemko and Werker 2006): elected
     membership raises US and UN aid. Tested as a direct shifter.
  D. 2025 US cut x pre-period US share (see 16_crowdout_diagnostics.py), and
     its reduced form on IPC food insecurity in 2025-26.

Outputs: output/tables/iv_alternatives.csv, iv_us_cut_reduced_form.csv,
         additions to iv_key_numbers.json
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("iv", ROOT / "code" / "15_instrument.py")
IV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IV)
INP, TAB = IV.INP, IV.TAB
KEY = json.loads((TAB / "iv_key_numbers.json").read_text())

# Elected UN Security Council members by year, parsed from the Wikipedia list
# (input/iv/unsc_wikipedia_raw.txt -> unsc_members.json): two-year terms by start year.
UNSC_NAMES = json.loads((INP / "iv" / "unsc_members.json").read_text())
NAME_FIX = {"Ivory Coast": "CIV", "South Korea": "KOR", "Republic of the Congo": "COG", "Vietnam": "VNM",
            "Democratic Republic of the Congo": "COD", "Bolivia": "BOL", "Venezuela": "VEN", "Syria": "SYR"}


def cluster_fit(fml, d, group="iso3"):
    import re as _re
    used = [c for c in d.columns if _re.search(r"\b" + _re.escape(c) + r"\b", fml)] + [group]
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=used)
    return smf.ols(fml, data=d).fit(cov_type="cluster", cov_kwds={"groups": d[group].astype("category").cat.codes})


def setup():
    codes, emdat, f, region = IV.load()
    panel = pd.read_parquet(INP / "iv" / "panel.parquet")
    fews = sorted(panel[panel.fews].iso3.unique())
    f["year"] = f.month.dt.year
    f["q"] = f.month.dt.asfreq("Q")
    top = f.groupby("donor").amount_usd.sum().nlargest(40).index
    f["d"] = np.where(f.donor.isin(top), f.donor, "Other")
    pre = f[f.year.between(2005, 2010)]
    w = pre.groupby(["iso3", "d"]).amount_usd.sum()
    w = (w / w.groupby(level=0).transform("sum")).rename("w").reset_index()
    return codes, f, region, fews, w


def donor_budget(f, region, fews, w):
    regions = sorted(set(region.values()))
    by = f.groupby(["d", "region", "year"]).amount_usd.sum()
    tot = f.groupby(["d", "year"]).amount_usd.sum()
    rows = []
    for d in w.d.unique():
        for r in regions:
            for y in range(2005, 2026):
                rows.append((d, r, y, np.log1p((tot.get((d, y), 0) - by.get((d, r, y), 0)) / 1e6)))
    B = pd.DataFrame(rows, columns=["d", "region", "year", "lnB"])
    sample = sorted(set(fews) & set(w.iso3))
    P = pd.MultiIndex.from_product([sample, range(2011, 2025)], names=["iso3", "year"]).to_frame(index=False)
    P["region"] = P.iso3.map(region)
    m = w[w.iso3.isin(sample)].merge(P, on="iso3").merge(B, on=["d", "region", "year"])
    m = m[m.d != "Other"]
    m["x"] = m.w * m.lnB
    Z = m.groupby(["iso3", "year"]).x.sum().rename("z_budget")
    y = f.groupby(["iso3", "year"]).amount_usd.sum()
    yfood = f[f.cluster.fillna("").str.contains("Food Security|Nutrition")].groupby(["iso3", "year"]).amount_usd.sum()
    P = P.merge(Z.reset_index(), on=["iso3", "year"], how="left")
    idx = P.set_index(["iso3", "year"]).index
    P["y"] = np.log1p(idx.map(y).fillna(0).astype(float) / 1e6)
    P["yfood"] = np.log1p(idx.map(yfood).fillna(0).astype(float) / 1e6)
    P["z"] = (P.z_budget - P.z_budget.mean()) / P.z_budget.std()
    rows = []
    for yv, lab in [("y", "all sectors"), ("yfood", "food and nutrition")]:
        for samp, sel in [("2011-2024", P.year <= 2024), ("2011-2019 (before COVID)", P.year <= 2019)]:
            d = P[sel]
            mm = cluster_fit(f"{yv} ~ z + C(iso3) + C(year)", d)
            rows.append({"instrument": "A. donor budget shocks (leave-out)", "outcome": lab, "sample": samp,
                         "coef_per_sd": mm.params["z"], "se": mm.bse["z"], "F": (mm.params["z"] / mm.bse["z"]) ** 2,
                         "n": int(mm.nobs), "countries": d.iso3.nunique(), "frequency": "annual"})
    return rows, P


def us_calendar(f, fews):
    us = f.donor.str.startswith("United States")
    pre = f[f.year.between(2005, 2010)]
    share = (pre[pre.donor.str.startswith("United States")].groupby("iso3").amount_usd.sum()
             / pre.groupby("iso3").amount_usd.sum()).rename("us_share")
    rest = f[us].groupby(["q", "iso3"]).amount_usd.sum()
    qs = pd.period_range("2011Q1", "2024Q4", freq="Q")
    sample = sorted(set(fews) & set(share.index))
    P = pd.MultiIndex.from_product([sample, qs], names=["iso3", "q"]).to_frame(index=False)
    world = f[us].groupby("q").amount_usd.sum()
    # US commitments to everyone except c, relative to the US fiscal-year mean (FY runs Oct-Sep)
    P["fy"] = (P.q.dt.year + (P.q.dt.quarter == 4).astype(int))
    own = rest.reindex(pd.MultiIndex.from_frame(P[["q", "iso3"]]), fill_value=0).values
    P["usrest"] = np.log1p((P.q.map(world).fillna(0).values - own) / 1e6)
    P["usrest_dev"] = P.usrest - P.groupby(["iso3", "fy"]).usrest.transform("mean")
    P = P.merge(share, on="iso3")
    P["z"] = P.us_share * P.usrest_dev
    P["z"] = (P.z - P.z.mean()) / P.z.std()
    y = f.groupby(["iso3", "q"]).amount_usd.sum()
    P["y"] = np.log1p(P.set_index(["iso3", "q"]).index.map(y).fillna(0).astype(float) / 1e6)
    P["t"] = P.q.astype(str)
    mm = cluster_fit("y ~ z + C(iso3) + C(t)", P)
    return [{"instrument": "B. US fiscal calendar (US share x US spending timing)", "outcome": "all sectors",
             "sample": "2011-2024", "coef_per_sd": mm.params["z"], "se": mm.bse["z"],
             "F": (mm.params["z"] / mm.bse["z"]) ** 2, "n": int(mm.nobs), "countries": P.iso3.nunique(),
             "frequency": "quarterly"}]


def unsc(P, codes):
    name2iso = {**dict(zip(codes.preferred_name, codes.iso3166a3)), **dict(zip(codes.iso_en_name, codes.iso3166a3)),
                **NAME_FIX}
    UNSC = {name2iso.get(k): v for k, v in UNSC_NAMES.items() if name2iso.get(k)}
    P = P.copy()
    P["unsc"] = [int(y in UNSC.get(i, [])) for i, y in zip(P.iso3, P.year)]
    mm = cluster_fit("y ~ unsc + C(iso3) + C(year)", P)
    KEY["unsc_country_years"] = int(P.unsc.sum())
    return [{"instrument": "C. UN Security Council elected membership", "outcome": "all sectors",
             "sample": "2011-2024", "coef_per_sd": mm.params["unsc"], "se": mm.bse["unsc"],
             "F": (mm.params["unsc"] / mm.bse["unsc"]) ** 2, "n": int(mm.nobs), "countries": P.iso3.nunique(),
             "frequency": "annual (coefficient is for membership, not per SD)"}]


def us_cut_reduced_form(f, codes, fews):
    """Reduced form of the 2025 US cut on IPC food insecurity (multi-agency,
    independent of FEWS NET): change in the share of the analysed population
    in Phase 3+ between the latest 2024 analysis and the latest 2025-26
    analysis, on the 2021-2023 US share of humanitarian funding."""
    pre = f[f.year.between(2021, 2023)]
    us = (pre[pre.donor.str.startswith("United States")].groupby("iso3").amount_usd.sum()
          / pre.groupby("iso3").amount_usd.sum()).rename("us_share")
    ipc = pd.read_csv(INP / "ipc" / "ipc_global_national_long.csv", low_memory=False)
    ipc = ipc[(ipc["Validity period"] == "current") & (ipc.Phase == "3+")].copy()
    ipc["from"] = pd.to_datetime(ipc.From)
    ipc["yr"] = ipc["from"].dt.year
    last = lambda g: g.sort_values("from").iloc[-1]
    a = ipc[ipc.yr == 2024].groupby("Country").apply(last)[["Percentage", "Number"]].rename(
        columns={"Percentage": "p24", "Number": "n24"})
    b = ipc[ipc.yr.isin([2025, 2026])].groupby("Country").apply(last)[["Percentage", "Number"]].rename(
        columns={"Percentage": "p25", "Number": "n25"})
    d = a.join(b, how="inner").join(us, how="inner")
    d["dshare"] = d.p25 - d.p24
    d["fews"] = d.index.isin(fews)
    rows = []
    for lab, s in [("All IPC countries", d), ("FEWS NET countries", d[d.fews])]:
        m = smf.ols("dshare ~ us_share", data=s).fit(cov_type="HC1")
        rows.append({"sample": lab, "coef_us_share": m.params["us_share"], "se": m.bse["us_share"],
                     "n": len(s), "mean_change_pp": s.dshare.mean() * 100})
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "iv_us_cut_reduced_form.csv", index=False)
    d.to_csv(TAB / "iv_us_cut_ipc_countries.csv")
    KEY["us_cut_reduced_form_ipc"] = r.round(4).to_dict("records")
    print(r.round(3).to_string())
    return r


def main():
    codes, f, region, fews, w = setup()
    rows, P = donor_budget(f, region, fews, w)
    rows += us_calendar(f, fews)
    rows += unsc(P, codes)
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "iv_alternatives.csv", index=False)
    print(out.round(3).to_string())
    KEY["alternatives"] = out.round(4).to_dict("records")
    us_cut_reduced_form(f, codes, fews)
    (TAB / "iv_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))


if __name__ == "__main__":
    main()


GULF = ("Saudi Arabia", "United Arab Emirates", "Kuwait", "Qatar")


def oil_gulf(f, fews):
    """Werker, Ahmed and Cohen (2009): oil prices x reliance on Gulf donors.
    z[c,y] = (2005-2010 Gulf share of c's humanitarian funding) x log Brent price."""
    oil = pd.read_csv(INP / "fx" / "DCOILBRENTEU.csv")
    oil.columns = ["date", "p"]
    oil["year"] = pd.to_datetime(oil.date).dt.year
    oil = oil.set_index("year").p.astype(float)
    pre = f[f.year.between(2005, 2010)]
    gulf = pre.donor.str.startswith(GULF)
    share = (pre[gulf].groupby("iso3").amount_usd.sum() / pre.groupby("iso3").amount_usd.sum()).fillna(0)
    sample = sorted(set(fews) & set(pre.iso3))
    P = pd.MultiIndex.from_product([sample, range(2011, 2025)], names=["iso3", "year"]).to_frame(index=False)
    P["gulf_share"] = P.iso3.map(share).fillna(0)
    P["z"] = P.gulf_share * np.log(P.year.map(oil))
    P["z"] = (P.z - P.z.mean()) / P.z.std()
    y = f.groupby(["iso3", "year"]).amount_usd.sum()
    yg = f[f.donor.str.startswith(GULF)].groupby(["iso3", "year"]).amount_usd.sum()
    idx = P.set_index(["iso3", "year"]).index
    P["y"] = np.log1p(idx.map(y).fillna(0).astype(float) / 1e6)
    P["yg"] = np.log1p(idx.map(yg).fillna(0).astype(float) / 1e6)
    rows = []
    for yv, lab in [("y", "all donors"), ("yg", "Gulf donors only")]:
        mm = cluster_fit(f"{yv} ~ z + C(iso3) + C(year)", P)
        rows.append({"instrument": "E. oil price x Gulf donor share (Werker et al. 2009)", "outcome": lab,
                     "sample": "2011-2024", "coef_per_sd": mm.params["z"], "se": mm.bse["z"],
                     "F": (mm.params["z"] / mm.bse["z"]) ** 2, "n": int(mm.nobs), "countries": P.iso3.nunique(),
                     "frequency": "annual"})
    KEY["gulf_share_pre"] = share[share.index.isin(fews)].sort_values(ascending=False).head(8).round(3).to_dict()
    return rows


if __name__ == "__main__":
    codes, f, region, fews, w = setup()
    r = oil_gulf(f, fews)
    out = pd.concat([pd.read_csv(TAB / "iv_alternatives.csv"), pd.DataFrame(r)], ignore_index=True)
    out = out.drop_duplicates(subset=["instrument", "outcome", "sample"], keep="last")
    out.to_csv(TAB / "iv_alternatives.csv", index=False)
    KEY["alternatives"] = out.round(4).to_dict("records")
    print(pd.DataFrame(r).round(3).to_string())
    print(KEY["gulf_share_pre"])
    (TAB / "iv_key_numbers.json").write_text(json.dumps(KEY, indent=1, default=str))
