"""Scale of the estimated effects, and why Somalia, Nigeria and Ethiopia.

1. Somalia. Translate the agency-loss estimate (the exposure with a natural zero: a place that lost no
   agencies is untreated) into percentage points of wasting and numbers of children:
      effect (pp) = b (pp per unit of agency loss) x child-weighted mean agency loss
      children    = effect / 100 x children aged 6-59 months (IPC acute malnutrition analysis, 2025/26)
   for Gu 2026 (mid-2026) and for the pooled post-cut period, with 95% intervals from the s.e. Cross-check
   with US reliance measured from the least-exposed tenth of districts. Compare with the national change:
   how far 2025 and 2026 wasting ran above the rainfall-conflict-price prediction (69), which caps the
   average effect unless other forces were improving nutrition.
2. Nigeria (north-east). Same calculation with the zone-level agency-loss estimate and children under five
   in the north-east surveillance zones (IPC acute malnutrition tables, 2025).
3. Why these countries: US humanitarian funding in 2024 by recipient (FTS), rank and US share.

Writes output/us_cut_memo/numbers_scale.tex and output/tables/us_cut_scale.csv.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
M = {}
f0 = lambda v: f"{v:,.0f}"
f1 = lambda v: f"{v:.1f}"
k = lambda v: f"{round(v, -3):,.0f}"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def somalia():
    amn = pd.read_excel(INP / "ipc_amn" / "somalia-acute-malnutrition-analysis" /
                        "acute-malnutrition-between-july-2025-and-june-2026.xlsx", header=None)
    tot = amn[amn[0].astype(str).str.strip() == "Total"].iloc[0]
    kids = float(tot[1])
    M["scSomKids"] = f1(kids / 1e6)
    M["scSomGamCaseload"] = f1(float(tot[4]) / 1e6)
    M69 = load("m69", "69_somalia_aid_dependence.py")
    pop = M69.district_pop()
    D = pd.read_csv(TAB / "som_uscut_districts.csv", index_col=0)[["E_pred", "E_loss"]].join(pop.rename("pop"))
    d = D.dropna()
    loss = float(np.average(d.E_loss, weights=d["pop"]))
    us_mean = float(np.average(d.E_pred, weights=d["pop"]))
    us_p10 = float(d.E_pred.quantile(0.10))
    M["scSomLoss"] = f"{100 * loss:.0f}"
    S = pd.read_csv(TAB / "som_fs_seasons.csv")
    RB = pd.read_csv(TAB / "som_fs_robust.csv")
    rows = []

    def add(label, b, se, x, outcome):
        e, lo, hi = b * x, (b - 1.96 * se) * x, (b + 1.96 * se) * x
        rows.append(dict(country="Somalia", estimate=label, outcome=outcome, pp=e, pp_lo=lo, pp_hi=hi,
                         children=e / 100 * kids, children_lo=lo / 100 * kids, children_hi=hi / 100 * kids))
    g = S[(S.z == "E_loss") & (S.season == "gu26")].set_index("y")
    add("agency loss, Gu 2026", g.loc["gam", "b"], g.loc["gam", "se"], loss, "gam")
    add("agency loss, Gu 2026", g.loc["sam", "b"], g.loc["sam", "se"], loss, "sam")
    r = RB[(RB.z == "E_loss") & RB.spec.str.startswith("main")].iloc[0]
    add("agency loss, pooled 2025-26", r.b, r.se, loss, "gam")
    u = S[(S.z == "E_pred") & (S.season == "gu26")].set_index("y")
    add("US reliance vs least-exposed tenth, Gu 2026", u.loc["gam", "b"], u.loc["gam", "se"], us_mean - us_p10, "gam")
    # national change relative to prediction (69)
    key = json.loads((TAB / "som_aiddep_key.json").read_text())["gaps"]["gam"]
    for y, kk in [(2025, "mean25"), (2026, "mean26")]:
        rows.append(dict(country="Somalia", estimate=f"national, above prediction {y}", outcome="gam",
                         pp=key[kk], children=key[kk] / 100 * kids))
    R = pd.DataFrame(rows)
    t = {"agency loss, Gu 2026": "LossTs", "agency loss, pooled 2025-26": "LossPool",
         "US reliance vs least-exposed tenth, Gu 2026": "UsTs", "national, above prediction 2025": "NatTv",
         "national, above prediction 2026": "NatTs"}
    for r in R.itertuples():
        tag = t[r.estimate] + ("Sam" if r.outcome == "sam" else "")
        M[f"scSomPp{tag}"] = f1(r.pp)
        M[f"scSomKids{tag}"] = k(r.children)
        if not pd.isna(getattr(r, "pp_lo", np.nan)):
            M[f"scSomPpLo{tag}"], M[f"scSomPpHi{tag}"] = f1(r.pp_lo), f1(r.pp_hi)
            M[f"scSomKidsLo{tag}"], M[f"scSomKidsHi{tag}"] = k(r.children_lo), k(r.children_hi)
    base = 13.0 / 100 * kids
    M["scSomBaseWasted"] = k(base)
    M["scSomPctIncLossTs"] = f"{100 * R[(R.estimate == 'agency loss, Gu 2026') & (R.outcome == 'gam')].children.iloc[0] / base:.0f}"
    return R


def nigeria():
    B = INP / "subnational_aid" / "hdx_response" / "nga" / "nigeria-acute-malnutrition-data"
    v = pd.read_excel(B / "Nigerian_Acute_Malnutrition_2025.xlsx", sheet_name="NORTH-EAST NIGERIA", header=None)
    hr = next(i for i in range(6) if str(v.iloc[i, 0]).strip() in ("Zone", "Domain"))
    u5 = pd.to_numeric(v.iloc[hr + 1:, 2], errors="coerce").sum()
    M["scNgaKids"] = f1(u5 / 1e6)
    Z = pd.read_csv(TAB / "nga_zone_panel.csv")
    z = Z[(Z.region == "NE")].drop_duplicates("zone")
    N = pd.read_csv(TAB / "nga_did.csv")
    sd = z.loss25.std()
    loss = float(z.loss25.mean())
    M["scNgaLoss"] = f"{100 * loss:.0f}"
    rows = []
    for sample, tag in [("NE zones", "Pool"), ("NE zones, 2025 only", "Tv")]:
        for y in ["gam", "sam"]:
            r = N[(N.exposure == "z_loss25") & (N["sample"] == sample) & (N.outcome == y)].iloc[0]
            b, se = r.b / sd, r.se / sd
            e, lo, hi = b * loss, (b - 1.96 * se) * loss, (b + 1.96 * se) * loss
            rows.append(dict(country="Nigeria NE", estimate=sample, outcome=y, pp=e, pp_lo=lo, pp_hi=hi,
                             children=e / 100 * u5, children_lo=lo / 100 * u5, children_hi=hi / 100 * u5))
            t = tag + ("Sam" if y == "sam" else "")
            M[f"scNgaPp{t}"], M[f"scNgaPpLo{t}"], M[f"scNgaPpHi{t}"] = f1(e), f1(lo), f1(hi)
            M[f"scNgaKids{t}"], M[f"scNgaKidsLo{t}"], M[f"scNgaKidsHi{t}"] = k(e / 100 * u5), k(lo / 100 * u5), k(hi / 100 * u5)
    return pd.DataFrame(rows)


def why_countries():
    M15 = load("m15", "15_instrument.py")
    codes, emdat, f, region = M15.load()
    f["year"] = f.month.dt.year
    f["us"] = f.donor.str.startswith("United States")
    g = f[f.year == 2024].groupby("iso3").apply(lambda s: pd.Series({
        "us": s[s.us].amount_usd.sum() / 1e6, "total": s.amount_usd.sum() / 1e6}))
    g["share"] = g.us / g.total
    g = g.sort_values("us", ascending=False)
    g["rank"] = np.arange(1, len(g) + 1)
    g.to_csv(TAB / "us_hum_funding_2024.csv")
    for iso, t in [("SOM", "Som"), ("NGA", "Nga"), ("ETH", "Eth")]:
        M[f"scRank{t}"], M[f"scUs{t}"], M[f"scShare{t}"] = int(g.loc[iso, "rank"]), f0(g.loc[iso, "us"]), f"{100 * g.loc[iso, 'share']:.0f}"
    top = g.head(12)
    M["scTopList"] = ", ".join(top.index)
    return g


def main():
    R = pd.concat([somalia(), nigeria()])
    R.to_csv(TAB / "us_cut_scale.csv", index=False)
    G = why_countries()
    (ROOT / "output" / "us_cut_memo" / "numbers_scale.tex").write_text(
        "% generated by code/80_us_cut_scale.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k_}}}{{{v}}}\n" for k_, v in M.items()))
    pd.set_option("display.width", 200)
    print(R.round(2).to_string())
    print(G.head(15).round(2))
    print(M)


if __name__ == "__main__":
    main()
