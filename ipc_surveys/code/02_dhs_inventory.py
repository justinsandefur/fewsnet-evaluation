"""Inventory DHS surveys usable as an outcome source.

Uses the public DHS Program API (no key needed for metadata) to list every
survey with fieldwork dates, whether it collected anthropometry, whether a GPS
dataset exists, and the unweighted number of children measured for wasting and
stunting. The microdata and GPS files themselves require a registered request
per survey at https://dhsprogram.com/data/new-user-registration.cfm .

Outputs: input/dhs/dhs_surveys.csv (all surveys, all countries)
"""
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "dhs"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.dhsprogram.com/rest/dhs"

ANTHRO_ID, GPS_ID = "10", "26"  # DHS survey characteristic ids
INDICATORS = {"CN_NUTS_C_WH2": "wasted", "CN_NUTS_C_HA2": "stunted"}


def get_all(endpoint, **params):
    rows, page = [], 1
    while True:
        r = requests.get(f"{API}/{endpoint}", params={"f": "json", "perpage": 1000,
                                                      "page": page, **params}, timeout=120)
        r.raise_for_status()
        j = r.json()
        rows += j["Data"]
        if page >= j["TotalPages"]:
            return pd.DataFrame(rows)
        page += 1


def main():
    s = get_all("surveys")
    chars = s["SurveyCharacteristicIds"].fillna("").str.split(r",\s*")
    s["has_anthro"] = chars.apply(lambda c: ANTHRO_ID in c)
    s["gps_flag"] = chars.apply(lambda c: GPS_ID in c)

    ge = get_all("datasets", fileType="GE")
    s["gps_file"] = s["SurveyId"].isin(ge["SurveyId"])

    for ind, name in INDICATORS.items():
        d = get_all("data", indicatorIds=ind, breakdown="national")
        d = d[d["IsTotal"] == 1].groupby("SurveyId").agg(
            **{f"pct_{name}": ("Value", "first"), f"n_{name}": ("DenominatorUnweighted", "first")})
        s = s.merge(d, left_on="SurveyId", right_index=True, how="left")

    keep = ["SurveyId", "CountryName", "DHS_CountryCode", "SurveyYear", "SurveyType",
            "SurveyStatus", "FieldworkStart", "FieldworkEnd", "NumberOfSamplePoints",
            "NumberofHouseholds", "has_anthro", "gps_flag", "gps_file",
            "pct_wasted", "n_wasted", "pct_stunted", "n_stunted", "ReleaseDate"]
    s = s[keep].sort_values(["CountryName", "SurveyYear"])
    s.to_csv(OUT / "dhs_surveys.csv", index=False)
    print(s.groupby("SurveyType").size())
    print(f"{len(s)} surveys written")


if __name__ == "__main__":
    main()
