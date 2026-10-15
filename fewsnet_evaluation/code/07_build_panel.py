"""Build a clean FEWS NET unit x month panel from the raw API pulls.

Each raw row is one classification of one unit in one report:
  CS  = current situation, one month (the reporting month)
  ML1 = near-term projection, usually the next four months
  ML2 = medium-term projection, the four months after that
The value is the phase (1 Minimal, 2 Stressed, 3 Crisis, 4 Emergency,
5 Famine). "is_allowing_for_assistance" is FEWS NET's "!" marker: the unit
would likely be at least one phase worse without humanitarian assistance.
In the API it is a single series per unit x report x scenario (checked), so it
is carried as a flag. The API has no classifications before January 2011;
earlier FEWS NET maps used a pre-IPC scale and are only in the shapefiles.

Outputs (input/fewsnet/):
  classifications.parquet  one row per unit x report x scenario (cleaned)
  cs_monthly.parquet       current situation by unit x month
  proj_monthly.parquet     projections expanded to unit x target month, with
                           the lead time (months between report and target)
"""
import glob
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEW = ROOT / "input" / "fewsnet"

COLS = ["id", "country", "country_code", "fnid", "geographic_unit_name", "classification_scale",
        "scenario", "is_allowing_for_assistance", "projection_start", "projection_end",
        "reporting_date", "value", "status", "source_document"]


def load_raw() -> pd.DataFrame:
    frames = [pd.read_csv(f, encoding="utf-8-sig", usecols=lambda c: c in COLS, low_memory=False)
              for f in sorted(glob.glob(str(FEW / "raw" / "ipcphase_*.csv")))]
    d = pd.concat([f for f in frames if len(f)], ignore_index=True).drop_duplicates("id")
    for c in ["projection_start", "projection_end", "reporting_date"]:
        d[c] = pd.to_datetime(d[c], errors="coerce")
    return d


def main():
    d = load_raw()
    n0 = len(d)
    d = d[(d.status == "Collected") & d.value.between(1, 5)].copy()
    d["phase"] = d.value.round().astype(int)
    d["report_month"] = d.reporting_date.dt.to_period("M")
    print(f"{n0:,} raw rows, {len(d):,} usable classifications")

    d["assist"] = d.is_allowing_for_assistance.astype("boolean").fillna(False).astype(bool)
    d = d.sort_values("assist").drop_duplicates(
        ["fnid", "report_month", "scenario", "assist"], keep="last")
    d.drop(columns=["value", "status"]).to_parquet(FEW / "classifications.parquet", index=False)

    head = d.sort_values("assist").drop_duplicates(["fnid", "report_month", "scenario"], keep="last")
    head = head.merge(
        d.groupby(["fnid", "report_month", "scenario"]).assist.any().rename("assist_flag"),
        left_on=["fnid", "report_month", "scenario"], right_index=True)

    cs = head[head.scenario == "CS"].copy()
    cs["month"] = cs.projection_start.dt.to_period("M")
    cs = (cs.sort_values("reporting_date")
            .drop_duplicates(["fnid", "month"], keep="last")
            [["country_code", "fnid", "month", "phase", "assist_flag", "classification_scale"]])
    cs.to_parquet(FEW / "cs_monthly.parquet", index=False)

    pr = head[head.scenario.isin(["ML1", "ML2"])].dropna(subset=["projection_start", "projection_end"])
    rows = []
    for r in pr.itertuples(index=False):
        for m in pd.period_range(r.projection_start, r.projection_end, freq="M"):
            rows.append((r.country_code, r.fnid, r.scenario, r.report_month, m, r.phase, r.assist_flag))
    proj = pd.DataFrame(rows, columns=["country_code", "fnid", "scenario", "report_month",
                                       "month", "phase", "assist_flag"])
    proj["lead"] = (proj.month - proj.report_month).apply(lambda x: x.n)
    proj.to_parquet(FEW / "proj_monthly.parquet", index=False)

    print(f"current situation: {len(cs):,} unit-months, {cs.fnid.nunique():,} units, "
          f"{cs.country_code.nunique()} countries, {cs.month.min()} to {cs.month.max()}")
    print(f"projections: {len(proj):,} unit x target-month rows")
    print(cs.groupby(cs.month.dt.year).agg(countries=("country_code", "nunique"),
                                            units=("fnid", "nunique")))


if __name__ == "__main__":
    main()
