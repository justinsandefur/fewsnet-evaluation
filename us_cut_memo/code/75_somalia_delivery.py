"""Somalia: a fuller first stage from monthly delivered-aid data, and 2SLS by survey season.

Delivered aid (district x month), both recovered from public dashboards/folders (see
references/firststage_sources.md):
  FSC     Food Security Cluster: people reached with emergency food and cash/voucher assistance,
          Jan 2024 - Aug 2026 (WFP Tableau dashboard; ~85-90% WFP)
  NUT     Nutrition Cluster ONA site-month reports, 2018-2026: sites reporting, sites offering OTP
          (severe malnutrition treatment), OTP and TSFP admissions, children screened, RUTF stockout days
Exposure Z (district, 2024): aid dependence index (69); US-funded share of partners incl. UN pass-through
(68); and BHA/USAID named as donor (share of 2024 4W activity records in nutrition, health, food, WASH;
records recovered from the 2024 4W pivot cache).
Windows aligned to the surveys: Gu (fieldwork ~Jun-Jul) uses Jan-Jun; Deyr (~Nov-Dec) uses Jul-Nov.

Outputs: output/tables/som_dlv_*.csv, som_dlv_key.json, output/figures/som_dlv_*.pdf,
         output/us_cut_memo/numbers_dlv.tex
"""
import importlib.util
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, FIG = ROOT / "input", ROOT / "output" / "tables", ROOT / "output" / "figures"
FS = INP / "subnational_aid" / "firststage"
KEY, M = {}, {}
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                       "september", "october", "november", "december"], 1)}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M68 = load("m68", "68_somalia_us_cut.py")
M69 = load("m69", "69_somalia_aid_dependence.py")
M71 = load("m71", "71_somalia_first_stage.py")
dist_key = M68.dist_key
WIN = {"gu": range(1, 7), "deyr": range(7, 12)}


# ------------------------------------------------------------------ delivered aid, district x month
def fsc():
    rows = []
    for y in [2024, 2025, 2026]:
        d = pd.read_csv(FS / "fsc_tableau" / f"fsc_som_{y}_food_cash_reached_district_month.csv")
        d["reached"] = pd.to_numeric(d.reached.astype(str).str.replace(",", ""), errors="coerce")
        d["m"] = d.month.str.lower().map(MONTHS)
        d["dist"] = d.admin2_pcode.map(dist_key)
        g = d.groupby(["dist", "m"]).reached.sum().unstack(fill_value=0)       # zero where not on the map
        months = sorted(d.m.unique())
        g = g.reindex(columns=months, fill_value=0).stack().rename("fsc").reset_index()
        g["year"] = y
        rows.append(g)
    F = pd.concat(rows)
    # districts reached in any year get zeros in months they are absent
    alld = F.dist.unique()
    idx = pd.MultiIndex.from_frame(F[["year", "m"]].drop_duplicates()).to_frame(index=False)
    full = idx.assign(k=1).merge(pd.DataFrame({"dist": alld, "k": 1}), on="k").drop(columns="k")
    F = full.merge(F, on=["year", "m", "dist"], how="left").fillna({"fsc": 0})
    KEY["fsc_total"] = F.groupby("year").fsc.sum().round(-3).to_dict()
    return F


def nutrition():
    n = pd.read_csv(FS / "nutrition_cluster_ona" / "som_nutrition_ona_site_month_2018-2026.csv.gz", low_memory=False)
    rp = n["Reporting Period"].astype(str)
    n["year"] = pd.to_numeric(rp.str[:4], errors="coerce")
    n["m"] = rp.str[5:].str.lower().map(MONTHS)
    n = n.dropna(subset=["year", "m"])
    n["dist"] = n["District Pcode"].astype(str).map(dist_key)
    num = lambda c: pd.to_numeric(n[c], errors="coerce")
    otp = n["site_activity/OTP"].astype(str).eq("True") | n.concat_site_activity.astype(str).str.contains("OTP")
    n["otp_site"] = otp.astype(float)
    n["otp_adm"] = num("Total benenficiaries admitted in OTP using MUAC or W/H").fillna(0) + \
        num("Total benenficiaries admitted in OTP with oedema").fillna(0)
    n["tsfp_adm"] = num("Total benenficiaries admitted in TSFP using MUAC or W/H").fillna(0)
    n["screened"] = num("Total Beneficiaries screened for acute malnutrition")
    n["rutf_out"] = num("How many days did the facility faced RUTF stockout?")
    n["unicef"] = n["Partner current source of funds: cash and supplies"].astype(str).str.contains("UNICEF").astype(float)
    g = n.groupby(["dist", "year", "m"]).agg(sites=("facility_site_id", "nunique"), otp_sites=("otp_site", "sum"),
                                              otp_adm=("otp_adm", "sum"), tsfp_adm=("tsfp_adm", "sum"),
                                              screened=("screened", "sum"), rutf_out=("rutf_out", "mean"),
                                              unicef=("unicef", "mean")).reset_index()
    g["year"], g["m"] = g.year.astype(int), g.m.astype(int)
    KEY["nut_sites_by_year"] = g.groupby("year").sites.sum().to_dict()
    return g


def bha_share():
    d = pd.read_csv(FS / "cwg_4w" / "som_4w_2024_records_from_pivotcache.csv", low_memory=False)
    d["cluster"] = d["Cluster/AoR"].map(M68.T62.map_cluster)
    d = d[d.cluster.isin(M68.SECTORS)]
    d["dist"] = d.DistrictCode.astype(str).map(dist_key)
    don = d["The donor for the acitvity"].astype(str)
    d["us_direct"] = don.str.contains(M68.US_RX).astype(float)
    d["known"] = ~don.isin(["0", "nan", "Other", "Not in the List", "(blank)"])
    k = d[d.known]
    KEY["bha_records"] = int(d.us_direct.sum())
    org = d["The name of your organisation with acronym"].map(M68.T62.clean_org)
    # organisation-level fallback for records without a usable donor
    ou = k.groupby(org[d.known]).us_direct.mean()
    d["u"] = np.where(d.known, d.us_direct, org.map(ou))
    return d.groupby("dist").u.mean().rename("E_bha")


# ------------------------------------------------------------------ first stage
def district_frame():
    pop = M69.district_pop().rename("pop")
    X = pd.read_csv(TAB / "som_fs_districts.csv", index_col=0)[["index", "E_pred", "region"]]
    X = X.join(bha_share()).join(pop)
    return X


def windows(F, N, X):
    out = pd.DataFrame(index=X.index)
    u5 = X["pop"] * 0.19
    for w, ms in WIN.items():
        f = F[F.m.isin(ms)].groupby(["dist", "year"]).fsc.mean().unstack()
        n = N[N.m.isin(ms)].groupby(["dist", "year"])[["sites", "otp_sites", "otp_adm", "rutf_out"]].mean()
        for y in [2024, 2025]:
            out[f"fsc_{w}{y}"] = f.get(y)
            for c in ["sites", "otp_sites", "otp_adm", "rutf_out"]:
                out[f"{c}_{w}{y}"] = n[c].unstack().get(y) if y in n.index.get_level_values(1) else np.nan
        out[f"fsc_loss_{w}"] = (out[f"fsc_{w}2024"].fillna(0) - out[f"fsc_{w}2025"].fillna(0)) / X["pop"] * 100
        out[f"fsc_log_{w}"] = -(np.log(out[f"fsc_{w}2025"].fillna(0) + 100) - np.log(out[f"fsc_{w}2024"].fillna(0) + 100))
        out[f"otp_loss_{w}"] = (out[f"otp_sites_{w}2024"].fillna(0) - out[f"otp_sites_{w}2025"].fillna(0)) / u5 * 1e4
        out[f"otp_log_{w}"] = -(np.log(out[f"otp_sites_{w}2025"].fillna(0) + 1) - np.log(out[f"otp_sites_{w}2024"].fillna(0) + 1))
        out[f"adm_log_{w}"] = -(np.log(out[f"otp_adm_{w}2025"].fillna(0) + 10) - np.log(out[f"otp_adm_{w}2024"].fillna(0) + 10))
        out[f"stock_ch_{w}"] = out[f"rutf_out_{w}2025"] - out[f"rutf_out_{w}2024"]
    return X.join(out)


def first_stage(D):
    rows = []
    for w in WIN:
        for x in ["fsc_loss", "fsc_log", "otp_loss", "otp_log", "adm_log", "stock_ch"]:
            for z in ["index", "E_pred", "E_bha"]:
                d = D.dropna(subset=[f"{x}_{w}", z])
                A = np.column_stack([np.ones(len(d)), d[z]])
                b, V = M71.cl_ols(d[f"{x}_{w}"].values, A, d.region.values)
                rows.append(dict(window=w, x=x, z=z, b=b[1], se=np.sqrt(V[1, 1]), F=b[1] ** 2 / V[1, 1], n=len(d),
                                 z_sd=d[z].std(), x_mean=d[f"{x}_{w}"].mean(), b_sd=b[1] * d[z].std()))
    R = pd.DataFrame(rows)
    R.to_csv(TAB / "som_dlv_firststage.csv", index=False)
    return R


def monthly_event(F, N, X):
    """Monthly coefficients of delivered aid on exposure (district and month FE), relative to 2024."""
    out = []
    P = F.merge(N[["dist", "year", "m", "otp_sites"]], on=["dist", "year", "m"], how="outer")
    P = P[(P.year >= 2024) & (P.year <= 2025)].merge(X[["index", "E_pred", "E_bha", "pop", "region"]], left_on="dist",
                                                      right_index=True)
    P["fsc_pc"] = P.fsc / P["pop"] * 100
    P["otp_pc"] = P.otp_sites.fillna(0) / (P["pop"] * 0.19) * 1e4
    P["t"] = P.year.astype(str) + "-" + P.m.astype(int).astype(str).str.zfill(2)
    for y, z in [("fsc_pc", "index"), ("fsc_pc", "E_pred"), ("otp_pc", "index"), ("otp_pc", "E_pred")]:
        d = P.dropna(subset=[y, z]).copy()
        zs = (d[z] - d.drop_duplicates("dist")[z].mean()) / d.drop_duplicates("dist")[z].std()
        ts = sorted(d.t.unique())
        post = [t for t in ts if t >= "2025-01"]
        # reference: 2024 average
        yt = M71.partial(d[y].values, pd.get_dummies(d.dist, dtype=float).join(pd.get_dummies(d.t, dtype=float)).values)
        Z = np.column_stack([zs * (d.t == t) for t in post])
        A = pd.get_dummies(d.dist, dtype=float).join(pd.get_dummies(d.t, dtype=float)).values
        Zt = np.column_stack([M71.partial(Z[:, j], A) for j in range(Z.shape[1])])
        b, V = M71.cl_ols(yt, Zt, d.region.values)
        out += [dict(y=y, z=z, t=t, b=b[j], se=np.sqrt(V[j, j])) for j, t in enumerate(post)]
    E = pd.DataFrame(out)
    E.to_csv(TAB / "som_dlv_event.csv", index=False)
    return E, P


# ------------------------------------------------------------------ 2SLS by season
def domain_iv(D):
    p = pd.read_parquet(INP / "panel" / "som_need_panel.parquet")
    q = M68.survey_panel()
    p = p.merge(q[["domain", "season_id", "dists"]], on=["domain", "season_id"], how="left")
    cols = ["fsc_loss_gu", "fsc_loss_deyr", "fsc_log_gu", "fsc_log_deyr", "otp_loss_gu", "otp_loss_deyr",
            "otp_log_gu", "otp_log_deyr", "index", "E_pred", "E_bha"]
    rows = []
    for r in p.drop_duplicates("domain").itertuples():
        w = pd.Series({k: v for k, v in json.loads(r.dists).items() if k not in (None, "null")})
        rec = {"domain": r.domain}
        for c in cols:
            v = D[c].reindex(w.index)
            ok = v.notna()
            rec["d_" + c] = float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan
        rows.append(rec)
    p = p.merge(pd.DataFrame(rows), on="domain")
    p["gu25"] = ((p.year == 2025) & (p.season_type == "Gu")).astype(float)
    p["deyr25"] = ((p.year == 2025) & (p.season_type == "Deyr")).astype(float)
    p["post25"] = p.gu25 + p.deyr25
    p = p[p.year <= 2025]      # delivered-aid windows are 2025; Gu 2026 is analysed in 68/69/71
    for x in ["fsc_loss", "fsc_log", "otp_loss", "otp_log"]:
        p[f"x_{x}"] = np.where(p.season_type == "Gu", p[f"d_{x}_gu"], p[f"d_{x}_deyr"])
    R = []
    for x in ["x_fsc_loss", "x_fsc_log", "x_otp_loss", "x_otp_log"]:
        for zs in [["d_index"], ["d_E_pred"], ["d_E_bha"], ["d_index", "d_E_pred"]]:
            for y in ["gam", "sam", "muac_gam", "cdr", "u5dr"]:
                for post, lab in [("post25", "both"), ("gu25", "gu"), ("deyr25", "deyr")]:
                    s = p if post == "post25" else p[p[{"gu25": "deyr25", "deyr25": "gu25"}[post]] == 0]
                    R.append(dict(season=lab, **M71.iv(s, y, x, zs, post=post)))
    R = pd.DataFrame(R)
    R.to_csv(TAB / "som_dlv_iv.csv", index=False)
    return R, p


def figures(E, P):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.2))
    nat = P.groupby("t").agg(fsc=("fsc", "sum"), otp=("otp_sites", "sum"))
    ax = axes[0]
    ax.plot(range(len(nat)), nat.fsc / 1e6, color=BLUE, marker="o", ms=3)
    ax.set_title("Food & cash reached (millions/month)", fontsize=9)
    ax2 = ax.twinx()
    ax2.plot(range(len(nat)), nat.otp, color=ORANGE, marker="o", ms=3)
    ax2.set_ylabel("Sites offering OTP", color=ORANGE, fontsize=8)
    ax.set_xticks(range(0, len(nat), 3))
    ax.set_xticklabels([t[2:] for t in nat.index[::3]], fontsize=7, rotation=90)
    for ax, y, lab in [(axes[1], "fsc_pc", "Food & cash reached per 100 residents"),
                       (axes[2], "otp_pc", "OTP sites per 10,000 children")]:
        for z, col in [("index", ORANGE), ("E_pred", BLUE)]:
            e = E[(E.y == y) & (E.z == z)]
            x = np.arange(len(e)) + (0.15 if z == "E_pred" else -0.15)
            ax.errorbar(x, e.b, yerr=1.96 * e.se, fmt="o", ms=3, color=col, lw=1,
                        label={"index": "Aid dependence", "E_pred": "US reliance"}[z])
        ax.axhline(0, color=GREY, lw=0.8)
        ax.set_xticks(range(0, 12, 2))
        ax.set_xticklabels([f"25-{m:02d}" for m in range(1, 13, 2)], fontsize=7, rotation=90)
        ax.set_title(lab + "\nper s.d. of exposure, vs 2024", fontsize=9)
        ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(FIG / "som_dlv_firststage.pdf")
    plt.close(fig)


def write_numbers(FSR, R, P):
    f1 = lambda v: f"{v:.1f}"
    f2 = lambda v: f"{v:.2f}"
    tot = KEY["fsc_total"]
    M["dvFscTf"], M["dvFscTv"] = f1(tot[2024] / 1e6), f1(tot[2025] / 1e6)
    M["dvFscDrop"] = f"{100 * (1 - tot[2025] / tot[2024]):.0f}"
    nat = P.groupby(["year", "m"]).otp_sites.sum().unstack(0)
    M["dvOtpTf"], M["dvOtpTv"] = f"{nat[2024].mean():.0f}", f"{nat[2025].mean():.0f}"
    xn = {"fsc_loss": "FscL", "fsc_log": "FscG", "otp_loss": "OtpL", "otp_log": "OtpG", "adm_log": "AdmG", "stock_ch": "Stk"}
    zn = {"index": "Idx", "E_pred": "Us", "E_bha": "Bha"}
    for r in FSR.itertuples():
        t = xn[r.x] + zn[r.z] + ("Gu" if r.window == "gu" else "Dy")
        M[f"dvF{t}"], M[f"dvBsd{t}"] = f1(r.F), f2(r.b_sd)
        M[f"dvXm{t}"] = f2(r.x_mean)
    xn2 = {"x_fsc_loss": "FscL", "x_fsc_log": "FscG", "x_otp_loss": "OtpL", "x_otp_log": "OtpG"}
    zn2 = {"d_index": "Idx", "d_E_pred": "Us", "d_E_bha": "Bha", "d_index+d_E_pred": "Both"}
    yn = {"gam": "Gam", "sam": "Sam", "muac_gam": "Muac", "cdr": "Cdr", "u5dr": "Ufive"}
    sn = {"both": "", "gu": "Gu", "deyr": "Dy"}
    for r in R.itertuples():
        t = xn2[r.x] + zn2[r.z] + yn[r.y] + sn[r.season]
        M[f"dvIvF{t}"], M[f"dvIvB{t}"] = f1(r.F), f2(r.beta)
        M[f"dvIvLo{t}"] = f2(r.ar_lo) if r.ar_bounded else "$-\\infty$"
        M[f"dvIvHi{t}"] = f2(r.ar_hi) if r.ar_bounded else "$\\infty$"
        M[f"dvIvXm{t}"] = f2(r.x_mean_post)
        M[f"dvIvAt{t}"] = f1(r.beta * r.x_mean_post)
        M[f"dvIvAtLo{t}"] = f1(r.ar_lo * r.x_mean_post) if r.ar_bounded else "$-\\infty$"
        M[f"dvIvAtHi{t}"] = f1(r.ar_hi * r.x_mean_post) if r.ar_bounded else "$\\infty$"
    (ROOT / "output" / "us_cut_memo" / "numbers_dlv.tex").write_text(
        "% generated by code/75_somalia_delivery.py -- do not edit\n" +
        "".join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in M.items()))


def main():
    F, N, X = fsc(), nutrition(), district_frame()
    D = windows(F, N, X)
    D.to_csv(TAB / "som_dlv_districts.csv")
    FSR = first_stage(D)
    E, P = monthly_event(F, N, X)
    R, p = domain_iv(D)
    figures(E, P)
    write_numbers(FSR, R, P)
    (TAB / "som_dlv_key.json").write_text(json.dumps(KEY, indent=1, default=str))
    pd.set_option("display.width", 240, "display.max_rows", 300, "display.max_columns", 30)
    print(json.dumps(KEY, indent=1, default=str))
    print(D[[c for c in D.columns if c.startswith(("fsc_loss", "fsc_log", "otp_loss", "otp_log", "adm_log", "stock"))]].describe().round(2).to_string())
    print(D[["index", "E_pred", "E_bha"]].corr().round(2))
    print(FSR.round(3).to_string())
    print(R[["season", "y", "x", "z", "n", "post_n", "F", "beta", "se", "ols", "ar_lo", "ar_hi", "ar_bounded",
             "x_mean_post"]].round(3).to_string())


if __name__ == "__main__":
    main()
