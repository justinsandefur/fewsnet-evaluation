"""Inventory of non-DHS household surveys that could supply child
anthropometry: UNICEF's Multiple Indicator Cluster Surveys (MICS), the World
Bank's Core Welfare Indicators Questionnaire (CWIQ), the Living Standards
Measurement Study (LSMS) and the World Bank's Fragility, Conflict and
Violence (FCV) collection.

Source: World Bank Microdata Library API, which lists each survey and its
variable labels. A survey is flagged as having anthropometry if its variable
labels include child weight and height/length (or weight-for-height /
height-for-age z-scores), and as having GPS if any label mentions latitude,
longitude or GPS. Labels are a good but imperfect guide: MICS cluster
coordinates, where collected, are usually withheld from public files, so the
GPS flag is checked separately against documentation.

Output: input/surveys/survey_inventory.csv
"""
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "surveys"
RAW = OUT / "raw_vars"
RAW.mkdir(parents=True, exist_ok=True)
API = "https://microdata.worldbank.org/index.php/api/catalog"

WEIGHT = re.compile(r"\bweight\b.*\b(kg|kilo)|\bweight of (child|the child)|child'?s weight|^weight$|"
                    r"weight-for-height|weight for height|wasting|\b(whz|waz)\d*\b|"
                    r"poids de l'enfant|poids pour (hauteur|taille)|\(kilogrammes\)|"
                    r"peso del? (la )?niñ|peso para (la )?talla", re.I)
HEIGHT = re.compile(r"\b(height|length)\b.*\b(cm|centimet)|child'?s (height|length)|^(height|length)$|"
                    r"height-for-age|height for age|length/height|stunting|\bhaz\d*\b|"
                    r"taille de l'enfant|hauteur pour (l')?[aâ]ge|taille pour (l')?[aâ]ge|"
                    r"talla del? (la )?niñ|talla para (la )?edad", re.I)
MUAC = re.compile(r"\bmuac\b|mid-upper arm|middle upper arm|arm circumference|p[ée]rim[eè]tre brachial|"
                  r"circunferencia (del )?brazo", re.I)
GPS = re.compile(r"latitude|longitude|\bgps\b|\blat\b|\blon\b|coordinates", re.I)
DATE = re.compile(r"(date|month|day|year) of interview|interview (date|month|day|year)", re.I)


def search(**params):
    rows, page = [], 0
    while True:
        r = requests.get(f"{API}/search", params={"ps": 100, "page": page + 1, **params}, timeout=120)
        r.raise_for_status()
        res = r.json()["result"]
        rows += res["rows"]
        if len(rows) >= int(res["found"]) or not res["rows"]:
            return rows
        page += 1


def variables(idno: str) -> list:
    path = RAW / f"{idno}.json"
    if path.exists():
        return json.loads(path.read_text())
    try:
        r = requests.get(f"{API}/{idno}/variables", timeout=120)
        v = r.json().get("variables", []) if r.ok else []
    except (requests.RequestException, ValueError):
        v = []
    path.write_text(json.dumps(v))
    time.sleep(0.3)
    return v


def flags(vs: list) -> dict:
    labels = [f"{v.get('name', '')} {v.get('labl', '')}" for v in vs]
    has = lambda rx: any(rx.search(l) for l in labels)
    return {"n_vars": len(vs), "weight": has(WEIGHT), "height": has(HEIGHT), "muac": has(MUAC),
            "gps_var": has(GPS), "interview_date": has(DATE)}


def main():
    studies = []
    for coll in ["MICS", "lsms", "FCV"]:
        for s in search(collection=coll):
            studies.append({**s, "source": coll})
    # Free-text search matches thousands of surveys on these common words, so
    # keep only those whose title names the CWIQ.
    for sk in ["CWIQ", "Core Welfare Indicators Questionnaire"]:
        for s in search(sk=sk):
            if re.search(r"Core Welfare Indicator|CWIQ", s["title"], re.I):
                studies.append({**s, "source": "CWIQ"})
    df = pd.DataFrame(studies).drop_duplicates("idno")
    # Studies listed in MICS/LSMS collections but titled CWIQ are CWIQ
    df.loc[df.title.str.contains("Core Welfare|CWIQ", case=False), "source"] = "CWIQ"
    rows = []
    for s in df.itertuples():
        f = flags(variables(s.idno))
        rows.append({"source": s.source, "idno": s.idno, "country": s.nation,
                     "year_start": s.year_start, "year_end": s.year_end, "title": s.title,
                     "url": s.url, **f})
    out = pd.DataFrame(rows)
    out["anthro"] = (out.weight & out.height) | out.muac
    out.to_csv(OUT / "survey_inventory.csv", index=False)
    print(out.groupby("source").agg(surveys=("idno", "size"), with_vars=("n_vars", lambda x: (x > 0).sum()),
                                    anthro=("anthro", "sum"), gps=("gps_var", "sum")))


if __name__ == "__main__":
    main()
