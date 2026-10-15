"""Download survey metadata (DHS, MICS, LSMS) and country-year covariates.

Survey metadata only; no microdata. All sources are public APIs.
  DHS   : DHS Program API (api.dhsprogram.com), fieldwork start dates
  MICS  : IHSN survey catalog (catalog.ihsn.org), entries with "_MICS_" in the id
  LSMS  : World Bank Microdata Library, LSMS collection
  WDI   : GDP per capita, growth, population, battle deaths, under-5 deaths, income groups
  WGI   : political stability / absence of violence
  Maddison Project 2023 : GDP per capita, used to fill gaps in WDI (Somalia, Syria, ...)
  UCDP  : battle-related deaths v25.1 by conflict-year and location
"""
import io, json, zipfile, time
from pathlib import Path
import pandas as pd
import subprocess
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = "research-script (survey-selection side project)"


class _Resp:
    def __init__(self, content):
        self.content = content
    def json(self):
        return json.loads(self.content)


def get(url, params=None):
    """Fetch with curl: python-requests on this machine's LibreSSL hangs on some hosts."""
    if params:
        url = url + "?" + urlencode(params)
    for i in range(4):
        out = subprocess.run(["curl", "-sfL", "--max-time", "300", "-A", UA, url], capture_output=True)
        if out.returncode == 0:
            return _Resp(out.stdout)
        print("  retry", i, url, out.returncode, flush=True)
        time.sleep(3 * (i + 1))
    raise RuntimeError(url)


def catalog(base, **params):
    rows, page = [], 1
    while True:
        p = dict(ps=500, page=page, **params)
        res = get(f"{base}/index.php/api/catalog/search", params=p).json()["result"]
        rows += res["rows"]
        if len(rows) >= int(res["found"]) or not res["rows"]:
            break
        page += 1
    return pd.DataFrame(rows)


# --- DHS, MICS (IHSN + WB catalogs), LSMS (WB) -------------------------------
if not (RAW / "lsms_catalog.csv").exists():
    r = get("https://api.dhsprogram.com/rest/dhs/surveys",
            params={"f": "json", "perpage": 2000, "surveyStatus": "all"})
    dhs = pd.DataFrame(r.json()["Data"])
    dhs.to_csv(RAW / "dhs_surveys_api.csv", index=False)
    print("DHS rows", len(dhs), dhs.SurveyType.value_counts().to_dict())

    mics_ihsn = catalog("https://catalog.ihsn.org", sk="MICS")
    mics_wb = catalog("https://microdata.worldbank.org", collection="mics")
    mics = pd.concat([mics_ihsn.assign(src="ihsn"), mics_wb.assign(src="wb")])
    mics = mics[mics.idno.str.contains("_MICS", case=False, na=False)]
    mics.to_csv(RAW / "mics_catalog.csv", index=False)
    print("MICS catalog rows", len(mics))

    lsms = catalog("https://microdata.worldbank.org", collection="lsms")
    lsms.to_csv(RAW / "lsms_catalog.csv", index=False)
    print("LSMS rows", len(lsms))


# --- WDI / WGI --------------------------------------------------------------
def wb_indicator(code, source=2):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{code}"
    out, page = [], 1
    while True:
        js = get(url, params=dict(format="json", per_page=5000, page=page, source=source,
                                  date="1985:2025")).json()
        out += js[1] or []
        if page >= js[0]["pages"]:
            break
        page += 1
    # WGI (source 3) rows carry only a country name, not a code
    d = pd.DataFrame([{"iso3": x["countryiso3code"], "cname": x["country"]["value"],
                       "year": int(x["date"]), code: x["value"]} for x in out])
    return d


def cached_indicator(code, source=2):
    f = RAW / f"wdi_{code}.csv"
    if not f.exists():
        print("WDI", code, flush=True)
        wb_indicator(code, source).to_csv(f, index=False)
    return pd.read_csv(f, keep_default_na=False, na_values=[""])

WDI = ["NY.GDP.PCAP.PP.KD", "NY.GDP.PCAP.KD", "NY.GDP.PCAP.KD.ZG", "SP.POP.TOTL",
       "VC.BTL.DETH", "SH.DTH.MORT", "SH.DYN.MORT", "SP.POP.0014.TO"]

cty = get("https://api.worldbank.org/v2/country", params=dict(format="json", per_page=400)).json()[1]
cty = pd.DataFrame([{"iso3": c["id"], "iso2": c["iso2Code"], "name": c["name"],
                     "region": c["region"]["value"], "income": c["incomeLevel"]["value"],
                     "lending": c["lendingType"]["value"]} for c in cty])
cty = cty[cty.region != "Aggregates"]
cty.to_csv(RAW / "countries.csv", index=False)

frames = [cached_indicator(c).query("iso3 != ''").drop(columns="cname").set_index(["iso3", "year"])
          for c in WDI]
wgi = cached_indicator("GOV_WGI_PV.EST", source=3)
wgi["iso3"] = wgi.cname.map(dict(zip(cty.name, cty.iso3)))
print("WGI names not matched:", sorted(set(wgi.loc[wgi.iso3.isna(), "cname"]))[:40])
frames.append(wgi.dropna(subset=["iso3"]).drop(columns="cname")
              .rename(columns={"GOV_WGI_PV.EST": "PV.EST"}).set_index(["iso3", "year"]))
wdi = pd.concat(frames, axis=1).reset_index()
wdi.to_csv(RAW / "wdi.csv", index=False)
print("WDI", wdi.shape)

# --- Maddison ---------------------------------------------------------------
r = get("https://dataverse.nl/api/access/datafile/421302")
(RAW / "mpd2023.xlsx").write_bytes(r.content)

# --- UCDP battle-related deaths (conflict-level, by location) ---------------
r = get("https://ucdp.uu.se/downloads/brd/ucdp-brd-conf-251-csv.zip")
z = zipfile.ZipFile(io.BytesIO(r.content))
name = [n for n in z.namelist() if n.endswith(".csv")][0]
(RAW / "ucdp_brd_conf.csv").write_bytes(z.read(name))
print("done")
