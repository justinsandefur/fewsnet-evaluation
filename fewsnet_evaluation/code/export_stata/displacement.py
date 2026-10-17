"""Exports for stata/13_displacement.do (code/83_displacement.py, Somalia).

  disp_rounds.csv   district x FEWS NET round: departures over the 6 months before and after (all reasons,
                    drought, conflict), FEWS NET's map and forecast and the forecast split, district population
  disp_onsets.csv   need-defined Crisis and Emergency onsets with departures from the area before and after
  disp_totals.csv   total departures matched to districts and the drought share
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import INP, TAB, periods_to_str  # noqa: E402


def export(out):
    import pandas as pd
    D = pd.read_parquet(INP / "panel" / "displacement_district_rounds.parquet")
    keep = ["pcode", "round", "pop", "cur3", "fc3", "b_fc3", "c_fc3", "bi_fc3", "ci_fc3"] + \
        [f"{c}_{w}" for c in ["dep", "dep_drought", "dep_conflict"] for w in ["prev6", "next6"]]
    periods_to_str(D[keep]).to_csv(out / "disp_rounds.csv", index=False)
    E = pd.read_parquet(INP / "panel" / "displacement_onsets.parquet")
    keep = ["fnid", "mcell", "region", "onset", "early", "late", "averted"] + \
        [f"dep_{w}" for w in ["pre6", "post6", "post12"]]
    E[keep].to_csv(out / "disp_onsets.csv", index=False)
    k = json.loads((TAB / "displacement_key.json").read_text())
    pd.DataFrame([{"total": k["departures_total"], "drought_share": k["drought_share"]}]).to_csv(out / "disp_totals.csv", index=False)
