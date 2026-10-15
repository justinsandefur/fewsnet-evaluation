"""Data for 06_money.do, 07_shocks.do, 08_flags.do and 09_subnational.do.

Python keeps the panel building (FTS windows, polygon overlays, ACLED/WFP matching, the
cross-fitted baseline predictions); Stata re-estimates everything from these files.

  aid_panel.csv              country x FEWS NET map round: shares of areas in Phase 3+/4+ on the
                             current map (CS) and medium-term forecast (ML2); log funding (FTS, all and
                             food) in the 6 months after and before the map (31_aid_response.panel)
  contrib_areas.csv          FEWS NET area x round: predictable part (b_, bi_) and FEWS NET's
                             contribution (c_, ci_) of the Phase 3+ forecast, latest IPC (for coverage)
                             (fewsnet_contribution_panel; i = baseline includes the latest CH/IPC)
  shock_panel.csv            CH/IPC area x analysis month: outcomes, shock features, FEWS NET coverage
                             (input/panel/shock_panel.parquet, 27_shock_index.py)
  flag_pairs.csv             same-season pairs for the 2025 aid-cut test (28_flag_release.py):
                             version A (FEWS NET maps) and B (CH/IPC with overlaid flags)
  sub_<ISO>.csv, sub_<ISO>_annual.csv
                             Somalia / Sudan district x FEWS NET period and district x year panels
                             (63_subnational_models.py inputs)
Reference values for Table A1 (money.tex) and the subnational table go to python_tables_money.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import INP, TAB, load, periods_to_str, table_refs  # noqa: E402


def money(out):
    AID = load("aid", "31_aid_response.py")
    s = AID.panel()
    keep = ["country_code", "report_month", "s3_CS", "s4_CS", "s3_ML2", "s4_ML2",
            "f_all", "f_food", "f_all_lag", "f_food_lag"]
    periods_to_str(s[keep]).to_csv(out / "aid_panel.csv", index=False)
    p = pd.read_parquet(INP / "panel" / "fewsnet_contribution_panel.parquet",
                        columns=["country_code", "r", "b_fc3", "c_fc3", "bi_fc3", "ci_fc3", "ipc_last3"])
    periods_to_str(p).to_csv(out / "contrib_areas.csv", index=False)


def shocks(out):
    cols = ["iso3", "key", "month", "share3", "phase3", "covd", "dry6", "dry12", "drought", "ln_ev6", "ln_fat6",
            "d_ln_ev6", "dp12", "dp3", "miss_conf", "miss_price"]
    p = pd.read_parquet(INP / "panel" / "shock_panel.parquet", columns=cols)
    periods_to_str(p).to_csv(out / "shock_panel.csv", index=False)


def flags(out):
    FR = load("fr", "28_flag_release.py")
    cs = FR.fews_maps()
    A = FR.pairs_fews(cs).assign(version="A")
    outcomes = pd.read_parquet(INP / "panel" / "outcomes.parquet")
    geo, o = FR.RAIN.area_geometries(outcomes)
    B = FR.pairs_ipc(o, FR.overlay_flags(cs, geo, o)).assign(version="B")
    cols = ["version", "hm", "iso3", "cell", "flag", "exposed", "dphase"]
    pd.concat([A[cols], B[cols]]).to_csv(out / "flag_pairs.csv", index=False)


def subnational(out):
    for iso in ["SOM", "SDN"]:
        periods_to_str(pd.read_parquet(INP / f"panel/subnational_{iso}.parquet")).to_csv(out / f"sub_{iso}.csv", index=False)
        pd.read_parquet(INP / f"panel/subnational_{iso}_annual.parquet").to_csv(out / f"sub_{iso}_annual.csv", index=False)


def refs():
    """Table cells as printed: Table A1 (coef x 10, 1 decimal) and the subnational table (3 decimals)."""
    rows = []
    P = pd.read_csv(TAB / "aid_response_pooled.csv")
    P = P[(P.vars == "together") & (P.spec == "+ country FE (within-country)") & (P.phase == "3+")]
    for col in ["all", "food"]:
        for t, rk in [("current", "cur"), ("forecast", "fc")]:
            r = P[(P.funding == col) & (P.term == t)].iloc[0]
            rows += [(f"tab_money_{rk}_{col}", f"{10 * r.coef:.1f}"), (f"tab_money_{rk}_{col}_se", f"{10 * r.se:.1f}")]
        rows += [(f"tab_money_n_{col}", str(int(r.n))), (f"tab_money_countries_{col}", str(int(r.countries)))]
    C = pd.read_csv(TAB / "fewsnet_contribution.csv")
    C = C[(C.block == "funding") & (C.spec == "forecast") & C["sample"].str.contains("within country")]
    for bl, bk in [("raw data", "raw"), ("raw data + latest Cadre Harmonise / IPC", "rawipc")]:
        for col in ["all", "food"]:
            for t, rk in [("base_fc3", "base"), ("contrib_fc3", "contrib")]:
                r = C[(C.baseline == bl) & (C.term == t) & (C["sample"] == f"{col} funding, within country")].iloc[0]
                rows += [(f"tab_money_{rk}_{bk}_{col}", f"{10 * r.coef:.1f}"),
                         (f"tab_money_{rk}_{bk}_{col}_se", f"{10 * r.se:.1f}")]
            rows += [(f"tab_money_n_{bk}_{col}", str(int(r.n))), (f"tab_money_countries_{bk}_{col}", str(int(r.countries)))]
    # subnational table: rows as in 40_paper.subnational(), numbered 1-13
    R = pd.read_csv(TAB / "subnational_models.csv")
    K = json.loads((TAB / "subnational_key.json").read_text())
    spec = [("A", "static", "aid", "fc3"), ("A", "dynamic", "aid", "fc3"), ("A", "Anderson-Hsiao", "d_aid", "d_fc3"),
            ("A", "distinctive", "aid", "b_fc3"), ("A", "distinctive", "aid", "c_fc3"),
            ("A", "placebo: next round's forecast", "aid", "fc3_f1"), ("A", "static", "aid_any", "fc3"),
            ("A", "static", "pres", "fc3"), ("A2", "district and year effects", "reach", "fc3"),
            ("B", "contemporaneous", "flag", "aid"), ("B", "contemporaneous", "flag (3W presence)", "pres"),
            ("B2", "district and year effects", "flag", "reach"), ("B", "lags and lead", "flag", "aid_f1")]
    for i, (b, sp, y, v) in enumerate(spec, 1):
        for iso, ik in [("SOM", "so"), ("SDN", "sd")]:
            x = R[(R.iso == iso) & (R.block == b) & (R.spec == sp) & (R.outcome == y) & (R["var"] == v)]
            if len(x):
                rows += [(f"tab_subnat_{i}_{ik}", f"{x.coef.iloc[0]:.3f}"), (f"tab_subnat_{i}_{ik}_se", f"{x.se.iloc[0]:.3f}")]
    for iso, ik in [("SOM", "so"), ("SDN", "sd")]:
        rows += [(f"tab_subnat_districts_{ik}", str(K[iso]["districts"])), (f"tab_subnat_periods_{ik}", str(K[iso]["periods"]))]
    return rows


def export(out):
    money(out)
    shocks(out)
    flags(out)
    subnational(out)
    table_refs(out, "money", refs())
