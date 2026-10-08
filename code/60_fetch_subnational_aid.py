"""Sub-national humanitarian aid: feasibility probe and first download.

Re-downloads everything used in references/subnational_aid.md into
input/subnational_aid/<source>/ and writes small coverage tables there.

Usage:  .venv/bin/python code/60_fetch_subnational_aid.py [step ...]
Steps (default: all except 'aims_som'):
  cbpf          OCHA Country-Based Pooled Funds API (project x admin1/admin2 x cluster budgets)
  cerf          CERF project list (no location fields; kept for completeness)
  hdx_3w        OCHA 3W/4W operational-presence files on HDX (priority countries; --all for 8)
  hdx_response  HDX response-monitoring / people-reached / nutrition admissions datasets
  hpc_projects  HPC (response-plan) projects with planned locations (admin1-3 pcodes), 2011+
  fts_projects  Share of FTS funding linked to an HPC project (uses cached input/fts/raw)
  iati          d-portal SQL: IATI humanitarian spend and the share with sub-national locations
  aiddata       AidData geocoded releases (Somalia AIMS, Nigeria AIMS, World Bank)
  aims_som      Somalia AIMS public API (aims.mop.gov.so): projects, member-state locations (slow, ~1 hr)
  summary       Coverage tables from the cached files

Everything is anonymous; nothing needs a key. The IATI Datastore API needs a
subscription key and is not used (d-portal is used instead).
"""
import glob
import json
import os
import re
import sys
import time

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "input", "subnational_aid")
H = {"User-Agent": "research-probe (FEWS NET evaluation; sequential requests)"}
PRIORITY = ["som", "eth", "sdn", "nga"]
ALL8 = PRIORITY + ["ssd", "yem", "afg", "cod"]
CBPF_FUNDS = {"SOM21": "SOM", "ETH53": "ETH", "SUD15": "SDN", "NGA75": "NGA",
              "SSD19": "SSD", "YEM64": "YEM", "AFG23": "AFG", "DRC24": "COD"}
CBPF_PFID = {21: "SOM", 53: "ETH", 15: "SDN", 75: "NGA", 19: "SSD", 64: "YEM", 23: "AFG", 24: "COD"}
ISO2 = {"SOM": "SO", "ETH": "ET", "SDN": "SD", "NGA": "NG"}
CNAME = {"SOM": "SOMALIA", "ETH": "ETHIOPIA", "SDN": "SUDAN", "NGA": "NIGERIA"}


def get(url, sleep=1.0, **kw):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=H, timeout=kw.pop("timeout", 600), **kw)
            time.sleep(sleep)
            return r
        except requests.RequestException as e:
            print("  retry", attempt, url[:90], e)
            time.sleep(5)
    return None


def save(url, path, sleep=1.0, overwrite=False, **kw):
    if os.path.exists(path) and not overwrite:
        return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = get(url, sleep=sleep, **kw)
    ok = r is not None and r.status_code == 200 and not r.content[:200].lstrip().lower().startswith(b"<!doctype html")
    print(f"  {'ok ' if ok else 'ERR'} {r.status_code if r is not None else '-'} {len(r.content) if r is not None else 0:>10} {os.path.relpath(path, OUT)}")
    if ok:
        open(path, "wb").write(r.content)
    return ok


def safe(name, n=90):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:n]


# ---------------------------------------------------------------- CBPF
def cbpf():
    d = os.path.join(OUT, "cbpf")
    base = "https://cbpfapi.unocha.org/vo2/odata/"
    save(base + "Poolfund?$format=csv", f"{d}/poolfund.csv")
    # all funds in one call (poolfundAbbrv filter is ignored by these endpoints)
    for e in ["ProjectSummaryAggV2", "ProjectSummaryV2", "ProjectSummaryBeneficiaryDetail",
              "MstPFAdminLocationType", "MstClusters"]:
        save(base + e + "?$format=csv", f"{d}/{e}.csv", sleep=2)
    # older flat table: admin1 budget shares + 'Region -> District' text for 2014-2018
    for f in CBPF_FUNDS:
        save(base + f"ProjectSummary?poolfundAbbrv={f}&$format=csv", f"{d}/projectsummary_{f}.csv", sleep=2)


def num(x):
    return sum(float(t) for t in re.split(r"\|\|\||##", str(x)) if t not in ("", "nan"))


def cbpf_summary():
    d = os.path.join(OUT, "cbpf")
    a = pd.read_csv(f"{d}/ProjectSummaryAggV2.csv", low_memory=False)
    v = pd.read_csv(f"{d}/ProjectSummaryV2.csv", low_memory=False)
    a = a[a.PFId.isin(CBPF_PFID)].copy()
    a["country"] = a.PFId.map(CBPF_PFID)
    a["bdg2"] = a.AdmLocClustBdg2.apply(num)
    g = a.groupby(["country", "PrjCode"]).agg(year=("AYr", "first"), has_adm2=("AdmLoc2", lambda s: s.notna().any()),
                                              has_adm3=("AdmLoc3", lambda s: s.notna().any()),
                                              n_loc=("AdmLoc1", "size"), bdg2=("bdg2", "sum")).reset_index()
    g = g.merge(v[["PrjCode", "PrgBdg"]], on="PrjCode", how="left")
    g["adm2_budget_matches"] = (g.bdg2 / g.PrgBdg).between(0.95, 1.05)
    t = g.groupby(["country", "year"]).agg(projects=("PrjCode", "size"), usd_m=("PrgBdg", lambda s: s.sum() / 1e6),
                                           share_adm2=("has_adm2", "mean"), share_adm3=("has_adm3", "mean"),
                                           share_adm2_budget_ok=("adm2_budget_matches", "mean")).round(3).reset_index()
    t.to_csv(f"{OUT}/coverage_cbpf.csv", index=False)
    print(t[t.country.isin(["SOM", "ETH", "SDN", "NGA"])].to_string(index=False))


# ---------------------------------------------------------------- CERF
def cerf():
    save("https://cerfgms-webapi.unocha.org/v1/project/All.json", f"{OUT}/cerf/project_All.json", timeout=900)


# ---------------------------------------------------------------- HDX
def hdx_search(**params):
    r = get("https://data.humdata.org/api/3/action/package_search", params={"rows": 200, **params}, timeout=120)
    return r.json()["result"]["results"]


def hdx_download(pkg, folder, n=40):
    for res in pkg["resources"]:
        fmt = (res.get("format") or "").lower()
        if fmt in ("web app", "", "pdf", "png", "jpeg", "geojson"):
            continue
        fn = safe(res["name"])
        if not fn.lower().endswith("." + fmt):
            fn += "." + fmt
        save(res["url"], os.path.join(folder, safe(pkg["name"], n), fn), timeout=300)


def hdx_3w():
    d = os.path.join(OUT, "hdx_3w")
    countries = ALL8 if "--all" in sys.argv else PRIORITY
    meta = {}
    for iso in ALL8:
        meta[iso] = hdx_search(fq=f'groups:{iso} AND vocab_Topics:"operational presence"')
        print(iso, len(meta[iso]), "operational-presence datasets")
    json.dump(meta, open(f"{d}/package_search.json", "w"))
    for iso in countries:
        for p in meta[iso]:
            if p["organization"]["name"] in ("hdx-hapi", "hdx"):
                continue
            hdx_download(p, os.path.join(d, iso), n=50 if "response" in d else 40)


HDX_RESPONSE = {
    "som": ["srf-2014", "total-number-of-people-targeted-and-reached-per-region-and-per-cluster",
            "somalia-sam-admissions-in-2015", "somalia-pin-targeted-reached-by-location-and-cluster",
            "somalia-2026-hnrp-cluster-response-monitoring-dataset-january-to-march-2026",
            "cash-based-programming-in-somalia", "somalia-acute-malnutrition-burden-and-prevalence"],
    "eth": ["ethiopia-pin-targeted-reached-by-location-and-cluster", "ethiopia-weekly-emergency-response",
            "number-of-people-reached-with-food-assistance-in-emergency-settings", "ethiopia-malnutrition-prevalence"],
    "sdn": ["sudan-2018-hrp-response-monitoring-4ws", "sudan-2020-hrp-response-monitoring-4ws-quarter-1",
            "sudan-2021-hrp-response-monitoring-4ws", "sudan-2022-hrp-response-monitoring-4ws",
            "sudan-people-reached-by-locality-jan-dec-2019_hrp"],
    "nga": ["north-east-nigeria-food-assistance-coverage-and-gap-analysis-april-2019",
            "north-east-nigeria-food-security-and-agricultural-livelihoods-response-monitoring-january-april-2019",
            "nigeria-north-east-nigeria-progress-monitoring-on-nutrition-indicators-as-of-july-2018",
            "nigeria-acute-malnutrition-data"],
}


def hdx_response():
    d = os.path.join(OUT, "hdx_response")
    meta = {}
    for iso, names in HDX_RESPONSE.items():
        for n in names:
            r = get("https://data.humdata.org/api/3/action/package_show", params={"id": n}, timeout=120)
            if r is None or not r.ok:
                print("  missing", n)
                continue
            p = r.json()["result"]
            meta[n] = p
            hdx_download(p, os.path.join(d, iso), n=50 if "response" in d else 40)
    json.dump(meta, open(f"{d}/package_meta.json", "w"))


# ---------------------------------------------------------------- HPC projects
def hpc_projects():
    d = os.path.join(OUT, "hpc_projects")
    os.makedirs(d, exist_ok=True)
    rows = []
    for iso in ["SOM", "ETH", "SDN", "NGA"]:
        plans = get(f"https://api.hpc.tools/v1/public/plan/country/{iso}", timeout=120).json()["data"]
        for p in plans:
            code = p["planVersion"]["code"]
            years = [int(y["year"]) for y in p.get("years", [])]
            if not years or max(years) < 2011:
                continue
            # country plans only (HRP/CAP/flash appeals), not regional or global
            if not re.match(r"^[CHF]" + {"SDN": "(SDN|SUD)"}.get(iso, iso), code):
                continue
            path = f"{d}/{code}.json"
            if not os.path.exists(path):
                res, page = [], 1
                while True:
                    r = get("https://api.hpc.tools/v2/public/project/search",
                            params={"planCodes": code, "excludeFields": "governingEntities,targets",
                                    "limit": 100, "page": page}, timeout=300)
                    j = r.json()["data"]
                    res += j["results"]
                    if page >= j["pagination"]["pages"]:
                        break
                    page += 1
                json.dump(res, open(path, "w"))
                print(f"  {code}: {len(res)} projects")
            res = json.load(open(path))
            for x in res:
                lv = [l.get("adminLevel") for l in (x.get("locations") or [])]
                rows.append({"country": iso, "plan": code, "year": max(years), "project": x["id"],
                             "requested_usd": float(x.get("currentRequestedFunds") or 0),
                             "max_admin_level": max([l for l in lv if l is not None], default=None),
                             "n_locations": len(lv)})
    t = pd.DataFrame(rows)
    t.to_csv(f"{d}/projects_locations.csv", index=False)
    t["adm1plus"] = t.max_admin_level >= 1
    t["adm2plus"] = t.max_admin_level >= 2
    s = t.groupby(["country", "year"]).agg(projects=("project", "size"),
                                           requested_usd_m=("requested_usd", lambda s: s.sum() / 1e6),
                                           share_adm1=("adm1plus", "mean"), share_adm2=("adm2plus", "mean")).round(3)
    s.reset_index().to_csv(f"{OUT}/coverage_hpc_projects.csv", index=False)
    print(s.to_string())


# ---------------------------------------------------------------- FTS -> projects
def fts_projects():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "input", "fts", "raw", "flows_*.json"))):
        d = json.load(open(f))
        fl = d if isinstance(d, list) else d.get("flows") or d["data"]["flows"]
        for x in fl:
            dest = x.get("destinationObjects", [])
            locs = [o["name"] for o in dest if o["type"] == "Location"]
            if len(locs) != 1:
                continue
            c = {"Somalia": "SOM", "Ethiopia": "ETH", "Sudan": "SDN", "Nigeria": "NGA"}.get(locs[0])
            if c is None:
                continue
            yrs = [o["name"] for o in dest if o["type"] == "UsageYear"]
            rows.append({"country": c, "year": yrs[0] if yrs else x.get("budgetYear"),
                         "usd": x.get("amountUSD") or 0, "status": x.get("status"),
                         "has_project": any(o["type"] == "Project" for o in dest)})
    t = pd.DataFrame(rows)
    t = t[t.status.isin(["paid", "commitment"])]
    t["usd_project"] = t.usd.where(t.has_project, 0)
    s = t.groupby(["country", "year"])[["usd", "usd_project"]].sum()
    s["share_usd_linked_to_project"] = (s.usd_project / s.usd).round(3)
    s = s.reset_index()
    s = s[pd.to_numeric(s.year, errors="coerce").between(2011, 2026)]
    s.to_csv(f"{OUT}/coverage_fts_project_link.csv", index=False)
    print(s.pivot(index="year", columns="country", values="share_usd_linked_to_project").to_string())


# ---------------------------------------------------------------- IATI via d-portal
IATI_SQL = """
with h as (select distinct aid from sector where sector_group in ('720','730','740')),
c as (select aid, country_percent from country where country_code='{iso2}'),
l as (select aid, count(*) nloc from location
      where upper(location_name) not in ('{name}') and location_name is not null group by aid)
select floor(t.trans_day/365.25)+1970 as yr, {grp}
 sum(t.trans_usd*coalesce(c.country_percent,100)/100) usd,
 sum(case when l.nloc>0 then t.trans_usd*coalesce(c.country_percent,100)/100 else 0 end) usd_subnat,
 count(distinct t.aid) nact, count(distinct case when l.nloc>0 then t.aid end) nact_subnat
from trans t join h on h.aid=t.aid join c on c.aid=t.aid left join l on l.aid=t.aid
{join_act} where t.trans_code in ('D','E') group by 1 {grp2} order by 1
"""


def iati():
    d = os.path.join(OUT, "iati")
    os.makedirs(d, exist_ok=True)
    for c, iso2 in ISO2.items():
        for kind in ["year", "publisher"]:
            path = f"{d}/dportal_{c}_{kind}.csv"
            if os.path.exists(path):
                continue
            if kind == "year":
                sql = IATI_SQL.format(iso2=iso2, name=CNAME[c], grp="", grp2="", join_act="")
            else:
                sql = IATI_SQL.format(iso2=iso2, name=CNAME[c], grp="a.reporting,", grp2=",2",
                                      join_act="join act a on a.aid=t.aid")
            r = get("https://d-portal.org/dquery", params={"sql": sql}, sleep=3, timeout=900)
            j = r.json()
            if j.get("error"):
                print("  d-portal error", c, kind, j["error"])
                continue
            pd.DataFrame(j["rows"]).to_csv(path, index=False)
            print(f"  {c} {kind}: {len(j['rows'])} rows")


def iati_summary():
    out = []
    for c in ISO2:
        f = f"{OUT}/iati/dportal_{c}_year.csv"
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f)
        t["country"] = c
        out.append(t)
    t = pd.concat(out)
    t = t[t.yr.between(2011, 2026)]
    t["share_subnat"] = (t.usd_subnat / t.usd).round(3)
    t.to_csv(f"{OUT}/coverage_iati.csv", index=False)
    print(t.pivot(index="yr", columns="country", values="share_subnat").to_string())


# ---------------------------------------------------------------- AidData
def aiddata():
    d = os.path.join(OUT, "aiddata")
    base = "https://github.com/AidData-WM/public_datasets/raw/master/geocoded/"
    for f in ["SomaliaAIMS_GeocodedResearchRelease_Level1_v1.1.1.zip",
              "NigeriaAIMS_GeocodedResearchRelease_Level1_v1.3.2.zip",
              "WorldBank_GeocodedResearchRelease_Level1_v1.4.2.zip"]:
        if save(base + f, f"{d}/{f}"):
            import zipfile
            zipfile.ZipFile(f"{d}/{f}").extractall(f"{d}/{f[:-4]}")


# ---------------------------------------------------------------- Somalia AIMS
def aims_som():
    d = os.path.join(OUT, "aims_som")
    os.makedirs(d, exist_ok=True)
    api = "https://aimsapis.mop.gov.so/api/"
    save(api + "Project/GetProjectTitles", f"{d}/titles.json")
    titles = json.load(open(f"{d}/titles.json"))
    for t in titles:
        for e in ["GetLocations", "GetSectors", "GetDisbursements"]:
            save(f"{api}Project/{e}/{t['id']}", f"{d}/{e}/{t['id']}.json", sleep=0.5, timeout=60)


STEPS = {"cbpf": cbpf, "cerf": cerf, "hdx_3w": hdx_3w, "hdx_response": hdx_response,
         "hpc_projects": hpc_projects, "fts_projects": fts_projects, "iati": iati,
         "aiddata": aiddata, "aims_som": aims_som}

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("--")] or \
        [s for s in STEPS if s != "aims_som"] + ["summary"]
    for s in want:
        print("==", s)
        if s == "summary":
            cbpf_summary()
            iati_summary()
        else:
            STEPS[s]()
