"""Cut two large raw files down to the rows and columns the paper uses (no analysis).

Reads
  raw/fts/flows_YYYY.json        OCHA Financial Tracking Service, every flow, one JSON file per year
                                 (as returned by the FTS public API)
  raw/nutrition/ona.csv.gz       Somalia Nutrition Cluster site reports ("DATA from ONA" sheet), 2018-2026
Writes
  source/fts_somalia.csv         flows with Somalia among the destination locations: id, amount, status,
                                 boundary, decision date, donor and recipient organisations
  source/nutrition_sites.csv     site reports from 2023 on: reporting period, district, whether the site
                                 treats severe acute malnutrition (OTP), and the two free-text funding fields

Everything else (which flows count, US vs other donors, which sites name USAID) is done in Stata.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW, OUT = HERE / "raw", HERE / "source"


def names(objects, kind):
    """Names of one type of object (Organization, Location, ...) on one side of a flow, ';'-separated."""
    return "; ".join(o["name"] for o in objects if o["type"] == kind) or None


def fts():
    rows = []
    for f in sorted((RAW / "fts").glob("flows_*.json")):
        for x in json.loads(f.read_text()):
            src, dst = x.get("sourceObjects", []), x.get("destinationObjects", [])
            rows.append({"id": x["id"], "amount_usd": x.get("amountUSD"), "status": x.get("status"),
                         "boundary": x.get("boundary"), "decision_date": x.get("decisionDate"),
                         "donor": names(src, "Organization"), "recipient": names(dst, "Organization"),
                         "dest_country": names(dst, "Location")})
    d = pd.DataFrame(rows).drop_duplicates("id")      # a flow can appear in more than one year's file
    d = d[d.dest_country.fillna("").str.contains("Somalia")]
    d.to_csv(OUT / "fts_somalia.csv", index=False)
    print(f"FTS: {len(d)} flows to Somalia")


def nutrition():
    cols = {"Reporting Period": "period", "District Pcode": "dist", "site_activity/OTP": "otp",
            "concat_site_activity": "activities", "Partner current source of funds: cash and supplies": "funds",
            "Add other source of funds:": "funds_other"}
    n = pd.read_csv(RAW / "nutrition" / "ona.csv.gz", usecols=list(cols), low_memory=False, dtype=str)
    n = n.rename(columns=cols)[list(cols.values())]
    n = n[n.period.str[:4].isin(["2023", "2024", "2025", "2026"])]
    n.to_csv(OUT / "nutrition_sites.csv", index=False)
    print(f"Nutrition: {len(n)} site reports, 2023-26")


if __name__ == "__main__":
    fts()
    nutrition()
