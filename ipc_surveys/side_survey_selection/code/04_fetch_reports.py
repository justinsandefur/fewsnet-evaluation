"""Download DHS and MICS final reports for the survey-exclusion coding.

Sample: every DHS/MICS since 2000 in a country with 25+ battle deaths in the
fieldwork year or the two years before ("conflict set"), plus a random
comparison set of 30 DHS + 30 MICS from calm low/lower-middle income countries.

PDFs are large (10-30 MB), so they go outside Dropbox (PDF_DIR, override with
env var REPORT_PDF_DIR). Only extracted text is kept in the project.
"""
import json, os, re, subprocess, time
from pathlib import Path
from urllib.parse import urlencode, quote
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PDF_DIR = Path(os.environ.get("REPORT_PDF_DIR", Path.home() / "Library/Caches/survey_reports"))
PDF_DIR.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (research script; survey-selection side project)"


def curl_json(url, params=None):
    if params:
        url += "?" + urlencode(params)
    for i in range(3):
        r = subprocess.run(["curl", "-sfL", "--max-time", "120", "-A", UA, url], capture_output=True)
        if r.returncode == 0:
            return json.loads(r.stdout)
        time.sleep(3)
    return None


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 50_000:
        return True
    url = quote(url, safe=":/?=&%")
    r = subprocess.run(["curl", "-sfL", "--max-time", "600", "-A", UA, "-o", str(dest), url])
    ok = r.returncode == 0 and dest.exists() and dest.stat().st_size > 50_000
    if not ok and dest.exists():
        dest.unlink()
    return ok


# --- Sample ----------------------------------------------------------------
p = pd.read_csv(ROOT / "data" / "panel.csv").sort_values(["iso3", "year"])
p["conf3"] = p.groupby("iso3").conflict.transform(lambda s: s.rolling(3, min_periods=1).max())
p["bd3"] = p.groupby("iso3").battle_deaths.transform(lambda s: s.rolling(3, min_periods=1).sum())
s = pd.read_csv(ROOT / "data" / "surveys_long.csv")
s = s[(s.program != "LSMS") & (s.year >= 2000)]
s = s.merge(p[["iso3", "year", "name", "conf3", "bd3", "income"]], on=["iso3", "year"], how="left")
s = s.dropna(subset=["conf3"])
conf = s[s.conf3 == 1].assign(set="conflict")
calm = s[(s.conf3 == 0) & s.income.isin(["Low income", "Lower middle income"])]
comp = pd.concat([calm[calm.program == g].sample(30, random_state=7) for g in ["DHS", "MICS"]]).assign(set="comparison")
sample = pd.concat([conf, comp]).reset_index(drop=True)

# --- DHS: publications API ---------------------------------------------------
dhs_ids = sample.loc[sample.program == "DHS", "id"].tolist()
urls = {}
for sid in dhs_ids:
    js = curl_json("https://api.dhsprogram.com/rest/dhs/publications", {"f": "json", "surveyIds": sid, "perpage": 100})
    pubs = (js or {}).get("Data", [])
    fr = [x for x in pubs if x["PublicationTitle"].strip().lower() == "final report"] or \
         [x for x in pubs if "final report" in x["PublicationTitle"].lower()] or \
         [x for x in pubs if "key indicators" in x["PublicationTitle"].lower()]
    urls[sid] = fr[0]["PublicationURL"] if fr else None

# --- MICS: report links from the IHSN and World Bank catalogs -----------------
mcat = pd.read_csv(RAW / "mics_catalog.csv")
mcat["iso3"] = mcat.idno.str[:3]
mcat["year"] = pd.to_numeric(mcat.year_start, errors="coerce")
BAD = ["snapshot", "table", "quality", "sampling error", "questionnaire", "manual", "indicator", "key findings",
       "summary", "state", "province", "region", "tools", "data entry", "syntax", "weights", "programs"]


def mics_score(title, lang):
    """Lower is better; None if not a main report."""
    t = re.sub(r"multiple indicator cluster survey|enqu[êe]te (?:par grappes )?[àa] indicateurs multiples|"
               r"encuesta de indicadores m[úu]ltiples(?: por conglomerados)?", "", title.lower())
    if "report" not in t and "rapport" not in t and "informe" not in t and "relatório" not in t:
        return None
    if any(w in t for w in BAD):
        return None
    return (0 if ("final" in t or "finding" in t) else 1) + (0 if ("english" in t or lang == "English") else 0.5)


for sid in sample.loc[sample.program == "MICS", "id"]:
    iso, yr = sid.split("_")
    cands = []
    for _, r in mcat[(mcat.iso3 == iso) & (mcat.year == int(yr))].iterrows():
        base = "https://catalog.ihsn.org" if r.src == "ihsn" else "https://microdata.worldbank.org"
        js = curl_json(f"{base}/index.php/api/catalog/{r.idno}/resources") or {}
        for res in js.get("resources", []):
            f = res.get("filename") or ""
            sc = mics_score(res.get("title") or "", res.get("language"))
            if sc is None or not f.lower().endswith(".pdf"):
                continue
            url = f if f.startswith("http") else f"{base}/index.php/catalog/{res['survey_id']}/download/{res['resource_id']}"
            cands.append((sc, url))
    urls[sid] = [u for _, u in sorted(cands)] or None


def fetch_any(urls_, dest):
    if not urls_:
        return False
    if isinstance(urls_, str):
        urls_ = [urls_]
    for u in urls_:
        if download(u, dest):
            return True
        if "childinfo.org" in u and download(f"https://web.archive.org/web/2016id_/{u}", dest):
            return True
    return False


sample["report_url"] = sample.id.map(urls)
ok = []
for _, r in sample.iterrows():
    dest = PDF_DIR / f"{r.id}.pdf"
    ok.append(fetch_any(r.report_url, dest))
    print(r.id, "ok" if ok[-1] else "MISSING", flush=True)
sample["have_pdf"] = ok
sample.to_csv(ROOT / "data" / "report_sample.csv", index=False)
print(sample.groupby(["set", "program"]).have_pdf.agg(["sum", "size"]))
