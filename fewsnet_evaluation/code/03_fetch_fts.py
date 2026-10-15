"""Download all humanitarian funding flows from OCHA's Financial Tracking
Service (FTS) public API, one year at a time, and flatten them to a table.

Each flow records donor, recipient organisation, destination country (and
sometimes sub-national location), sector ("global cluster"), amount in USD,
and decision / reporting dates. Decision dates let us ask whether money was
committed before or after a warning.

Outputs: input/fts/raw/flows_YYYY.json, input/fts/fts_flows.parquet
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "input" / "fts" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
URL = "https://api.hpc.tools/v1/public/fts/flow"


def fetch_year(year: int) -> list:
    out = RAW / f"flows_{year}.json"
    if out.exists():
        return json.loads(out.read_text())
    flows, url, params = [], URL, {"year": year, "limit": 1000}
    while url:
        r = requests.get(url, params=params, timeout=300)
        r.raise_for_status()
        j = r.json()
        flows += j["data"]["flows"]
        url, params = j["meta"].get("nextLink"), None
        time.sleep(0.5)
    out.write_text(json.dumps(flows))
    return flows


def objs(lst, kind, side):
    """Pull names of a given object type from source/destination objects."""
    return "; ".join(o["name"] for o in lst if o["type"] == kind) or None


def flatten(f: dict) -> dict:
    src, dst = f.get("sourceObjects", []), f.get("destinationObjects", [])
    donor_types = [t for o in src if o["type"] == "Organization"
                   for t in o.get("organizationTypes", [])]
    return {
        "id": f["id"], "amount_usd": f.get("amountUSD"), "status": f.get("status"),
        "flow_type": f.get("flowType"), "boundary": f.get("boundary"),
        "date": f.get("date"), "decision_date": f.get("decisionDate"),
        "first_reported": f.get("firstReportedDate"), "budget_year": f.get("budgetYear"),
        "donor": objs(src, "Organization", "src"),
        "donor_type": "; ".join(sorted(set(donor_types))) or None,
        "donor_country": objs(src, "Location", "src"),
        "recipient": objs(dst, "Organization", "dst"),
        "dest_country": objs(dst, "Location", "dst"),
        "cluster": objs(dst, "GlobalCluster", "dst"),
        "emergency": objs(dst, "Emergency", "dst"),
        "plan": objs(dst, "Plan", "dst"),
        "usage_year": objs(dst, "UsageYear", "dst"),
        "parent_flow": f.get("parentFlowId"),
        "description": (f.get("description") or "")[:300],
    }


def main():
    rows = []
    for year in range(2005, pd.Timestamp.today().year + 1):
        fl = fetch_year(year)
        print(f"{year}: {len(fl):,} flows")
        rows += [flatten(f) for f in fl]
    df = pd.DataFrame(rows).drop_duplicates("id")
    df.to_parquet(ROOT / "input" / "fts" / "fts_flows.parquet", index=False)
    print(f"{len(df):,} unique flows, ${df.amount_usd.sum() / 1e9:,.0f}bn")


if __name__ == "__main__":
    main()
