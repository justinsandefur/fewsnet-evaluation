"""Harmonised long tables from the cached OCHA 3W/4W/5W and response-monitoring files.

Reads the raw files that 60_fetch_subnational_aid.py cached under
input/subnational_aid/hdx_3w/<iso>/ and hdx_response/<iso>/ and writes, per country,
to input/subnational_aid/tidy/:

  presence_<iso3>.parquet   admin1 x admin2 x period x cluster: n_partners (distinct
                            reporting organisations), n_activities (rows), source file
  reach_<iso3>.parquet      people reached / targeted / US$ transferred by admin unit x
                            period x cluster x indicator
  admin2_names_<iso3>.csv   every admin1/admin2 name (and P-code) seen in the 3W, response
                            and CBPF files, with the canonical OCHA COD-AB P-code and name
  fews_admin2_<iso3>.csv    FEWS NET fnid (all vintages) -> canonical admin1/admin2
  log_<iso3>.txt            every file used or skipped and why; de-duplication decisions;
                            cluster mapping; match rates

Canonical units are the OCHA COD-AB admin-2 boundaries cached in input/areas/codab/
(Somalia v03: 91 districts incl. the 17 Banadir districts; Sudan v03 2020: 189 localities).
Older Somalia files report Banadir as one district; those rows get the pseudo P-code SO22
("Banadir (all districts)"), and so does the FEWS NET Banadir unit.

Periods: period_start / period_end are the first day of the first and last calendar month
covered (inclusive). period_type is one of
  month      rows refer to one reporting month (a month column in the file, or a monthly file)
  quarter    quarterly file (Somalia 3W 2016 Q1, 2019 Q1-Q4)
  annual     one row per organisation x locality for the year (Sudan 2014-2019)
  snapshot   presence "as of" a date (Sudan 2020-2022 3W); start = end = that month
  range      a multi-month window reported as one figure (e.g. Sudan "April-June 2023",
             HRP "Jan-Sep" cumulative reach)
Monthly values are never invented from quarterly/annual/cumulative figures.

De-duplication rules (documented in each log):
  1. Exact duplicate files (same bytes, or a re-posted copy in another HDX dataset) are skipped.
  2. Within a series, for every period window (period_start, period_end) the rows come from
     ONE file: the highest-ranked file reporting that window. Rank = the file's release order
     (later releases supersede earlier ones, e.g. Somalia 3W Jan-Dec 2025 supersedes
     Jan-Oct 2025 for January-October); ties broken by disaggregation (admin-2 > admin-1).
  3. Reach: within a series the same rule applies to (window, measure). Windows that differ
     (e.g. Sudan HRP Jan-Mar, Jan-Jun, Jan-Dec 2020 cumulative) are all kept; the column
     latest_window marks, for each series x year x period_start, the longest cumulative window,
     so that cumulative paths are not summed by mistake.
  4. Different series (e.g. Somalia 3W US$ vs Cash Working Group US$ in 2023) are NOT merged
     or netted against each other: they overlap in content. Always filter on `series`.

Columns latest_window (presence and reach) flag the longest of nested windows that share a start
month; filter on it (or on period_type == "month") before summing over time.

Ethiopia and Nigeria are not yet covered (their files are cached; add manifests in MANIFEST).

Usage: .venv/bin/python code/62_tidy_3w.py [som] [sdn]     (default: som sdn; ~3 min)
"""
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import unicodedata
import warnings
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
AID = ROOT / "input" / "subnational_aid"
OUT = AID / "tidy"
CODAB = ROOT / "input" / "areas" / "codab"
FEWS = ROOT / "input" / "fewsnet" / "ipcphase.parquet"

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
MON3 = {k[:3]: v for k, v in MONTHS.items()}
MON3["sept"] = 9


# --------------------------------------------------------------------------- logging
class Log:
    def __init__(self, iso):
        self.iso = iso
        self.lines = []

    def __call__(self, *a):
        self.lines.append(" ".join(str(x) for x in a))

    def write(self):
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"log_{self.iso}.txt").write_text("\n".join(self.lines) + "\n")


# --------------------------------------------------------------------------- readers
def sniff(path):
    b = path.read_bytes()[:8]
    if b.startswith(b"PK"):
        return "xlsx"
    if b.startswith(b"\xd0\xcf\x11\xe0"):
        return "xls"
    head = path.read_bytes()[:400].lower()
    if b"<!doctype html" in head or b"<html" in head:
        return "html"
    return "csv"


def _cell(v):
    if isinstance(v, str):
        v = v.replace("\xa0", " ").strip()
        return v if v not in ("", "(blank)", "N/A", "n/a", "#N/A") else None
    return v


def read_book(path):
    """Return {sheet_name: list of row lists}. Values keep their Python types."""
    kind = sniff(path)
    if kind == "html":
        raise ValueError("file is an HTML page (dead link / Google login), not data")
    if kind == "xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        out = {}
        for ws in wb.worksheets:
            rows, empty = [], 0
            for r in ws.iter_rows(values_only=True):
                r = [_cell(v) for v in r]
                if any(v is not None for v in r):
                    empty = 0
                else:
                    empty += 1
                    if empty > 500:      # sheets that claim 1,048,576 rows
                        break
                rows.append(r)
            while rows and not any(v is not None for v in rows[-1]):
                rows.pop()
            out[ws.title] = rows
        wb.close()
        return out
    if kind == "xls":
        import xlrd
        wb = xlrd.open_workbook(path)
        out = {}
        for sh in wb.sheets():
            rows = []
            for i in range(sh.nrows):
                r = []
                for j, c in enumerate(sh.row(i)):
                    v = c.value
                    if c.ctype == xlrd.XL_CELL_DATE:
                        v = xlrd.xldate.xldate_as_datetime(v, wb.datemode)
                    elif c.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                        v = None
                    r.append(_cell(v))
                rows.append(r)
            out[sh.name] = rows
        return out
    raw = path.read_bytes().replace(b"\x00", b"")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rows = [[_cell(v) for v in r] for r in csv.reader(io.StringIO(txt))]
    return {"csv": rows}


def num(v):
    """Numeric value or NaN. Dates (Excel-corrupted counts) and text are NaN."""
    if v is None or isinstance(v, (dt.datetime, dt.date, dt.time)):
        return np.nan
    if isinstance(v, bool):
        return np.nan
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("$", "")
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return float(s)
    return np.nan


def is_date_like(v):
    return isinstance(v, (dt.datetime, dt.date)) or (
        isinstance(v, str) and re.fullmatch(r"\d{1,2}/\d{1,2}/1900", v.strip()))


# --------------------------------------------------------------------------- columns
def hxl_parse(tag):
    t = str(tag).strip().lower().replace(" ", "").replace("\t", "")
    if not t.startswith("#"):
        return None
    parts = t[1:].split("+")
    return parts[0], set(p for p in parts[1:] if p)


def find_header(rows, maxscan=15):
    """Locate the header row (best keyword score) and an HXL row if any."""
    kw = re.compile(r"cluster|sector|organi[sz]ation|org\b|org\.|partner|region|state|district|"
                    r"locality|month|individual|reached|benef|admin|year|pcode|p_cod|activity",
                    re.I)
    best, best_i, hxl_i = -1, None, None
    for i, r in enumerate(rows[:maxscan]):
        vals = [v for v in r if v is not None]
        if not vals:
            continue
        nh = sum(1 for v in vals if isinstance(v, str) and v.startswith("#"))
        if nh >= max(2, 0.5 * len(vals)):
            hxl_i = i
            continue
        sc = sum(1 for v in vals if isinstance(v, str) and kw.search(v) and len(v) < 120)
        if sc > best:
            best, best_i = sc, i
    return best_i, hxl_i, best


ROLE_ORDER = ["cluster", "org", "org_acr", "org_impl", "adm1", "adm1_code", "adm2",
              "adm2_code", "month", "year", "status", "reached", "usd"]


def assign_roles(header, hxl, overrides=None):
    """Map roles -> column index using HXL tags first, then header text."""
    n = max(len(header or []), len(hxl or []))
    header = list(header or []) + [None] * (n - len(header or []))
    hxl = list(hxl or []) + [None] * (n - len(hxl or []))
    roles = {}

    def put(role, j):
        if role not in roles:
            roles[role] = j

    # HXL
    for j, t in enumerate(hxl):
        p = hxl_parse(t) if t else None
        if not p:
            continue
        base, at = p
        if base in ("sector", "cluster"):
            put("cluster", j)
        elif base == "org":
            if "type" in at or "funder" in at:
                continue
            if "acronym" in at or "acr" in at:
                put("org_acr", j)
            elif "impl" in at:
                put("org_impl", j)
            else:
                put("org", j)
        elif base in ("adm1", "admin1"):
            put("adm1_code" if "code" in at else "adm1", j)
        elif base in ("adm2", "admin2"):
            put("adm2_code" if "code" in at else "adm2", j)
        elif base == "date":
            if "year" in at:
                put("year", j)
            elif "start" in at or "end" in at:
                continue
            else:
                put("month", j)
        elif base == "status":
            put("status", j)
        elif base in ("reached", "beneficiary", "benefeciary") and not (at & {"hh", "f", "m", "children", "adult"}):
            put("reached", j)
        elif base == "value" and "total" in at:
            put("usd", j)
    # header text (Somalia: admin-1 is the region, 'State' is the federal member state)
    region_cols, state_cols = [], []
    for j, h in enumerate(header):
        if not isinstance(h, str):
            continue
        s = re.sub(r"\s+", " ", h.lower()).strip()
        if re.search(r"^(cluster|sector)\b|cluster/aor|^cluster name|sector/ ?intervention|sector_cluster|"
                     r"sector/cluster", s) and not re.search(r"\bid\b|sub sector|clusters\+", s):
            put("cluster", j)
        elif re.search(r"acronym|^org\.? acr", s):
            put("org_acr", j)
        elif re.search(r"implementing partner|imple\.|implementing organi[sz]ation name", s) and "type" not in s:
            if re.search(r"implementing organi[sz]ation name|org\. implementing", s):
                put("org", j)
            else:
                put("org_impl", j)
        elif re.search(r"^organi[sz]ation|^orgnization|^org\.? name|^org name|partner name|name of your organi|"
                       r"org\. implementing|^organisation_name|^organization_name|^organisation$", s) \
                and not re.search(r"type|not on list|if not", s):
            put("org", j)
        elif re.search(r"^(region|state)\s*(p_?cod|pcode|_pcode|code)|regionpcode|regioncode|^r_code|"
                       r"p-code admin1|admin1pcode", s):
            put("adm1_code", j)
        elif re.search(r"(district|admin2|locality)[ _]*(p_?code|pcode|_cod|code)|pcode admin2", s):
            put("adm2_code", j)
        elif re.search(r"^region\b|^select region|^admin1name", s):
            region_cols.append(j)
        elif re.search(r"^state\b", s):
            state_cols.append(j)
        elif re.search(r"^district\b|^select district|^locality\b|^admin2name|^admin2 name", s):
            put("adm2", j)
        elif re.search(r"^(for )?(reporting\s*)?month$|^cash delivery month$", s):
            put("month", j)
        elif re.search(r"^year$|cash delivery\s+year", s):
            put("year", j)
        elif re.search(r"^status", s):
            put("status", j)
        elif re.search(r"total # of \*?individuals|^individuals$|total individu|^# of individuals|"
                       r"total of beneficiaries reached|total beneficiary reached|total beneficiaries reached", s):
            put("reached", j)
        elif re.search(r"total usd transferred|total transfers usd", s):
            put("usd", j)
    if "adm1" not in roles and (region_cols or state_cols):
        roles["adm1"] = (region_cols or state_cols)[0]
    if overrides:
        for k, v in overrides.items():
            idx = [j for j, h in enumerate(header) if isinstance(h, str) and h.strip().lower() == v.lower()]
            if idx:
                roles[k] = idx[0]
    if "org" not in roles and "org_acr" in roles:
        roles["org"] = roles["org_acr"]
    if "org" not in roles and "org_impl" in roles:
        roles["org"] = roles.pop("org_impl")
    return roles


SKIP_SHEETS = re.compile(r"pivot|summary|analysis|map|dropdown|admin ?names?|org list|definition|"
                         r"read ?me|icons|^sheet[0-9]|type_of_org|sector_by|by_state|unique partner|"
                         r"regionstate|^districts$|rounding|method|first page|2nd page|sectors$|karthoum|"
                         r"org by state", re.I)


def pick_sheet(book, need=("cluster", "adm2"), sheet=None, overrides=None):
    """Choose the data sheet; return (sheet name, header idx, roles, rows) or None."""
    cands = []
    for name, rows in book.items():
        if sheet and name != sheet:
            continue
        if not sheet and SKIP_SHEETS.search(name) and len(book) > 1:
            continue
        hi, xi, sc = find_header(rows)
        if hi is None:
            continue
        roles = assign_roles(rows[hi], rows[xi] if xi is not None else None, overrides)
        if not all(r in roles for r in need):
            continue
        pref = 1 if re.search(r"data|presence|combined|compiled|master|hdx|3w|locality|jan|response", name, re.I) else 0
        cands.append((pref, len(rows), name, hi, xi, roles, rows))
    if not cands:
        return None
    cands.sort(key=lambda c: (-c[0], -c[1]))
    pref, n, name, hi, xi, roles, rows = cands[0]
    start = max(hi, xi if xi is not None else -1) + 1
    return name, start, roles, rows, hi


# --------------------------------------------------------------------------- clusters
CLUSTER_RULES = [
    ("shelter_nfi", r"shelter|non-? ?food|\bnfi|s ?& ?nfi|snfi|es/?nfi|es nfi|^es\b"),
    ("food_security", r"food|\bfs[lc]\b|livelihood|agricult|cash for food|\bfsl\b|^fsc"),
    ("nutrition", r"nutri|nutrt|\bnut\b"),
    ("health", r"health|covid|\bhea\b"),
    ("wash", r"wash|water|sanitation|hygiene"),
    ("protection", r"protect|gbv|gender|\bcp\b|hlp|housing|mine|explosive|\beh\b|\bma\b|child"),
    ("education", r"educ|\bedu\b"),
]


def map_cluster(raw):
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    s = str(raw).strip().lower()
    if s in ("", "nan", "none", "(blank)"):
        return None
    # 'RCF - Health and Nutrition' etc.: health first if both
    if "health" in s and "nutr" in s:
        return "health"
    for name, pat in CLUSTER_RULES:
        if re.search(pat, s):
            return name
    return "other"


# --------------------------------------------------------------------------- names
ARTICLES = {"al", "el", "ad", "ed", "ag", "aj", "as", "at", "ar", "an", "ash", "es", "um", "umm", "um."}
DROP_WORDS = {"locality", "district", "town", "pca", "area", "box", "rural", "reifi", "madeinat",
              "city", "state", "region", "camp", "camps"}


def ascii_(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()


def norm(s):
    s = ascii_(s).lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.replace("'", "").replace("`", ""))
    return re.sub(r"\s+", " ", s).strip()


def skel(s):
    """Spelling skeleton for Somali / Arabic transliterations."""
    toks = [t for t in norm(s).split() if t not in ARTICLES and t not in DROP_WORDS]
    out = []
    for t in toks:
        t = re.sub(r"^c(?=[aeiou])", "", t)       # Somali 'c' (ayn) at word start
        t = t.replace("x", "h").replace("q", "k").replace("dh", "d").replace("kh", "k") \
             .replace("sh", "s").replace("ou", "u").replace("y", "i").replace("ei", "i") \
             .replace("e", "i").replace("o", "u").replace("w", "u")
        t = re.sub(r"(.)\1+", r"\1", t)
        t = re.sub(r"(?<=.)[aiu]+$", "", t) if len(t) > 4 else t
        out.append(t)
    return "".join(out)


ADM1_ALIAS = {
    "SOM": {"hiiraan": "Hiraan", "hiran": "Hiraan", "waqooyi galbeed": "Woqooyi Galbeed",
            "woqooyi galbeed": "Woqooyi Galbeed", "w galbeed": "Woqooyi Galbeed",
            "galguduud": "Galgaduud", "shabelle dhexe": "Middle Shabelle",
            "shabelle hoose": "Lower Shabelle", "jubbada dhexe": "Middle Juba",
            "jubbada hoose": "Lower Juba", "mogadishu": "Banadir", "benadir": "Banadir",
            "togdher": "Togdheer", "nugal": "Nugaal", "sanag": "Sanaag", "bakol": "Bakool"},
    "SDN": {"al gezira": "Aj Jazirah", "gezira": "Aj Jazirah", "el gezira": "Aj Jazirah",
            "jazirah": "Aj Jazirah", "al jazirah": "Aj Jazirah", "aj jazirah": "Aj Jazirah",
            "al jazeera": "Aj Jazirah", "gedarif": "Gedaref", "gadaref": "Gedaref",
            "al gedaref": "Gedaref", "al qadarif": "Gedaref", "abyei pca box": "Abyei PCA",
            "abyei": "Abyei PCA", "abyei pca area": "Abyei PCA", "abyei area": "Abyei PCA",
            "sinnar": "Sennar", "qadarif": "Gedaref", "al qadarif": "Gedaref", "sennar": "Sennar", "nile": "River Nile", "river nile": "River Nile",
            "northern": "Northern", "white nile": "White Nile", "blue nile": "Blue Nile",
            "red sea": "Red Sea", "khartoum": "Khartoum", "kassala": "Kassala",
            "south kordofan": "South Kordofan", "north kordofan": "North Kordofan",
            "west kordofan": "West Kordofan", "north darfur": "North Darfur",
            "south darfur": "South Darfur", "west darfur": "West Darfur", "east darfur": "East Darfur",
            "central darfur": "Central Darfur", "southern kordofan": "South Kordofan",
            "northern kordofan": "North Kordofan", "western kordofan": "West Kordofan",
            "northern darfur": "North Darfur", "southern darfur": "South Darfur",
            "western darfur": "West Darfur", "eastern darfur": "East Darfur"},
}

# district aliases: normalised variant -> COD name (only where skeleton matching fails)
ADM2_ALIAS = {
    "SOM": {"baidoa": "Baydhaba", "baidao": "Baydhaba", "bardera": "Baardheere", "bardhere": "Baardheere",
            "galkayo": "Gaalkacyo", "galkacyo": "Gaalkacyo", "gaalkacayo": "Gaalkacyo",
            "erigavo": "Ceerigaabo", "erigabo": "Ceerigaabo",
            "las anod": "Laas Caanood", "lasanod": "Laas Caanood", "laascaanood": "Laas Caanood",
            "burao": "Burco", "burco": "Burco", "brava": "Baraawe", "barawe": "Baraawe", "merka": "Marka",
            "merca": "Marka", "zeila": "Zeylac", "zaila": "Zeylac", "alula": "Caluula", "abudwak": "Cabudwaaq",
            "abudwaq": "Cabudwaaq", "dhusamareb": "Dhuusamarreeb", "dhusamarreb": "Dhuusamarreeb",
            "dusamareb": "Dhuusamarreeb", "bosaso": "Bossaso", "bosasso": "Bossaso", "kismayo": "Kismaayo",
            "kismayu": "Kismaayo", "balad": "Balcad", "adale": "Cadale", "wanlaweyn": "Wanla Weyn",
            "wanla weyne": "Wanla Weyn", "elwak": "Ceel Waaq", "el wak": "Ceel Waaq", "dolo": "Doolow",
            "dollow": "Doolow", "tieglow": "Tayeeglow", "tiyeglow": "Tayeeglow", "rabdure": "Rab Dhuure",
            "rab dhure": "Rab Dhuure", "rabdhure": "Rab Dhuure", "haradhere": "Xarardheere",
            "harardhere": "Xarardheere", "buhodle": "Buuhoodle", "buuhodle": "Buuhoodle",
            "ainabo": "Caynabo", "aynabo": "Caynabo", "hudun": "Xudun", "hudur": "Xudur",
            "hargeisa": "Hargeysa", "hargeisa town": "Hargeysa", "garowe": "Garoowe",
            "beletweyne": "Belet Weyne", "beledweyne": "Belet Weyne", "beledweyn": "Belet Weyne",
            "belet weyn": "Belet Weyne", "bulo burte": "Bulo Burto", "bulo burti": "Bulo Burto",
            "buloburte": "Bulo Burto", "belet hawa": "Belet Xaawo", "beled hawo": "Belet Xaawo",
            "beled hawa": "Belet Xaawo", "garbaharey": "Garbahaarey", "garbaharrey": "Garbahaarey",
            "el barde": "Ceel Barde", "elbarde": "Ceel Barde", "el bur": "Ceel Buur",
            "elbur": "Ceel Buur", "el dher": "Ceel Dheer", "eldher": "Ceel Dheer", "adado": "Cadaado",
            "el afweyn": "Ceel Afweyn", "elafweyn": "Ceel Afweyn", "taleh": "Taleex",
            "odweyne": "Owdweyne", "oodweyne": "Owdweyne", "jamame": "Jamaame", "jamaame": "Jamaame",
            "badhadhe": "Badhaadhe", "sakow": "Saakow", "buale": "Bu'aale", "bualle": "Bu'aale",
            "qansah dhere": "Qansax Dheere", "qansax dhere": "Qansax Dheere", "burhakaba": "Buur Hakaba",
            "bur hakaba": "Buur Hakaba", "dinsor": "Diinsoor", "dinsoor": "Diinsoor",
            "kurtunwarey": "Kurtunwaarey", "qoryoley": "Qoryooley", "sablale": "Sablaale",
            "afgoye": "Afgooye", "lasqoray": "Laasqoray", "las qoray": "Laasqoray",
            "jariban": "Jariiban", "galdogob": "Galdogob", "bandar beyla": "Bandarbeyla",
            "iskushuban": "Iskushuban", "qardo": "Qardho", "gardo": "Qardho", "burtinle": "Burtinle",
            "luq": "Luuq", "lugh": "Luuq", "wajid": "Waajid", "waajid": "Waajid", "el waq": "Ceel Waaq",
            "gabiley": "Gebiley", "laas caaunrestrictedod": "Laas Caanood", "baderbeyla": "Bandarbeyla",
            "goldogob": "Galdogob", "abdulaziz": "Cabdulasis", "mogadishu cabdulcasiis": "Cabdulasis",
            "cabdulcasiis": "Cabdulasis", "shingani": "Shangaani", "laasanood": "Laas Caanood",
            "qarhdo": "Qardho", "kaaraan": "Karaan", "hawlwadaag": "Hawl Wadaag", "hodon": "Hodan",
            "mogadishu": "Banadir", "banadir": "Banadir", "benadir": "Banadir",
            "mogadishu banadir": "Banadir", "banaadir": "Banadir", "xamar": "Banadir"},
    "SDN": {"madani el kobra greater wad m": "Medani Al Kubra", "medani": "Medani Al Kubra",
            "wad medani": "Medani Al Kubra", "madani": "Medani Al Kubra",
            "el geneina": "Ag Geneina", "geneina": "Ag Geneina", "al geneina": "Ag Geneina",
            "el roseires": "Ar Rusayris", "roseires": "Ar Rusayris", "al roseires": "Ar Rusayris",
            "el kurmuk": "Al Kurmuk", "kurmuk": "Al Kurmuk", "geissan": "Geisan", "giessan": "Geisan",
            "zalingei": "Zalingi", "zalingi": "Zalingi", "el fasher": "Al Fasher", "fasher": "Al Fasher",
            "nyala north": "Nyala Shimal", "nyala south": "Nyala Janoub", "north nyala": "Nyala Shimal",
            "south nyala": "Nyala Janoub", "port sudan": "Port Sudan", "el jabaleen": "Aj Jabalain",
            "al jabalain": "Aj Jabalain", "jebelien": "Aj Jabalain", "kosti": "Kosti",
            "el salam wn": "As Salam / Ar Rawat", "al salam wn": "As Salam / Ar Rawat",
            "el salam": None, "um durman": "Um Durman", "omdurman": "Um Durman",
            "jebel awlia": "Jebel Awlia", "jabal awliya": "Jebel Awlia", "sharg el nile": "Sharg An Neel",
            "sharq an nil": "Sharg An Neel", "east nile": "Sharg An Neel", "karari": "Karrari",
            "abyei pca": "Abyei PCA area", "abyei pca area": "Abyei PCA area",
            "kadugli": "Kadugli", "el buram": "Al Buram", "al sunut": "As Sunut", "el sunut": "As Sunut",
            "kas": "Kas", "kass": "Kas", "tawila": "Tawila", "kutum": "Kutum", "kebkabiya": "Kebkabiya",
            "mellit": "Melit", "um kadada": "Um Kadadah", "saraf omra": "Saraf Omra",
            "el lait": "Al Lait", "el tina": "At Tina", "tina": "At Tina", "kernoi": "Kernoi",
            "um baru": "Um Baru", "el malha": "Al Malha", "el koma": "Al Koma", "el serif": "As Serief",
            "el sireaf": "As Serief", "dar el salam": "Dar As Salam", "dar al salam": "Dar As Salam",
            "el daein": "Ad Du'ayn", "ed daein": "Ad Du'ayn", "ed daien": "Ad Du'ayn", "ad duayn": "Ad Du'ayn",
            "el ferdous": "Al Firdous", "el firdous": "Al Firdous", "bahr el arab": "Bahr Al Arab",
            "abu karinka": "Abu Karinka", "yassin": "Yassin", "shearia": "Shia'ria", "shiaria": "Shia'ria",
            "adila": "Adila", "assalaya": "Assalaya", "abu jabra": "Abu Jabrah",
            "el radoum": "Al Radoum", "rehaid el birdi": "Rehaid Albirdi", "rehed el berdi": "Rehaid Albirdi",
            "ed el fursan": "Ed Al Fursan", "edd al fursan": "Ed Al Fursan", "kateila": "Kateila",
            "katila": "Kateila", "el wihda": "Al Wihda", "um dafug": "Um Dafoug", "um dafoug": "Um Dafoug",
            "sharg al jabal": "Sharg Aj Jabal", "east jebel marra": "Sharg Aj Jabal",
            "sharq aj jabal": "Sharg Aj Jabal", "beleil": "Beliel", "bielel": "Beliel",
            "el salam sd": "As Salam - SD", "as salam sd": "As Salam - SD", "el sunta": "As Sunta",
            "al sunta": "As Sunta", "mershing": "Mershing", "nitega": "Nitega", "tullus": "Tulus",
            "gereida": "Gereida", "shattaya": "Shattaya", "kubum": "Kubum", "buram": "Buram",
            "damso": "Damso", "beida": "Beida", "habila wd": "Habila - WD", "habila sk": "Habila - SK",
            "foro baranga": "Foro Baranga", "jebel moon": "Jebel Moon", "kereneik": "Kereneik",
            "krenik": "Kereneik", "kulbus": "Kulbus", "sirba": "Sirba", "azum": "Azum", "bindisi": "Bendasi",
            "mukjar": "Mukjar", "west jebel marra": "Gharb Jabal Marrah", "gharb jabal marrah": "Gharb Jabal Marrah",
            "north jebel marra": "Shamal Jabal Marrah", "central jebel marra": "Wasat Jabal Marrah",
            "um dukhun": "Um Dukhun", "wadi salih": "Wadi Salih", "rashad": "Ar Rashad",
            "el rashad": "Ar Rashad", "el quoz": "Al Quoz", "dilling": "Dilling", "dalami": "Delami",
            "heiban": "Heiban", "talodi": "Talawdi", "abu jubaiha": "Abu Jubayhah", "abu jubeiha": "Abu Jubayhah",
            "abassiya": "Abassiya", "um durein": "Um Durein", "reif shargi": "Ar Reif Ash Shargi",
            "el reif el shargi": "Ar Reif Ash Shargi", "abu kershola": "Abu Kershola", "el leri": "Al Leri",
            "el tadamon sk": "At Tadamon - SK", "ghadeer": "Ghadeer", "el tadamon bn": "At Tadamon - BN",
            "baw": "Baw", "ed damazine": "Ed Damazine", "damazine": "Ed Damazine", "wad el mahi": "Wad Al Mahi",
            "el dwaim": "Ad Diwaim", "ed dueim": "Ad Diwaim", "um remta": "Um Rimta", "rabak": "Rabak",
            "tendalti": "Tendalti", "el gitaina": "Al Gitaina", "guli": "Guli",
            "halfa el gadida": "Halfa Aj Jadeedah", "new halfa": "Halfa Aj Jadeedah", "kassala": "Madeinat Kassala",
            "el fau": "Al Fao", "el fao": "Al Fao", "el fashaga": "Al Fashaga", "el qureisha": "Al Qureisha",
            "el butana": "Al Butanah", "basunda": "Basundah", "gedaref": "Madeinat Al Gedaref",
            "gedaref town": "Madeinat Al Gedaref", "el mafaza": "Al Mafaza", "el rahad": None,
            "galabat": None, "um rawaba": "Um Rawaba", "sheikan": "Sheikan", "el obeid": "Sheikan",
            "soudari": "Soudari", "sodari": "Soudari", "bara": "Bara", "gebrat el sheikh": "Gebrat Al Sheikh",
            "um dam haj ahmed": "Um Dam Haj Ahmed", "west bara": "Gharb Bara", "abu zabad": "Abu Zabad",
            "en nahud": "An Nuhud", "el nuhud": "An Nuhud", "an nahud": "An Nuhud", "ghubeish": "Ghubaish",
            "wad banda": "Wad Bandah", "keilak": "Keilak", "babanusa": "Babanusa", "el lagowa": "Al Lagowa",
            "lagawa": "Al Lagowa", "el dibab": "Al Dibab", "el idia": "Al Idia", "el khiwai": "Al Khiwai",
            "el meiram": "Al Meiram", "el salam wk": "As Salam - WK", "sennar": "Sennar", "sinja": "Sinja",
            "singa": "Sinja", "abu hujar": "Abu Hujar", "ed dali": "Ad Dali", "dinder": "Ad Dinder",
            "el dinder": "Ad Dinder", "el suki": "As Suki", "east sennar": "Sharg Sennar",
            "el hasahisa": "Al Hasahisa", "hasahisa": "Al Hasahisa", "el kamlin": "Al Kamlin",
            "el managil": "Al Manaqil", "managil": "Al Manaqil", "el qurashi": "Al Qurashi",
            "south gezira": "Janub Al Jazirah", "east gezira": "Sharg Al Jazirah",
            "eastern el gezira": "Sharg Al Jazirah", "um el gura": "Um Algura", "um al qura": "Um Algura",
            "atbara": "Atbara", "ed damer": "Ad Damar", "el damer": "Ad Damar", "shendi": "Shendi",
            "berber": "Barbar", "abu hamad": "Abu Hamad", "el matama": "Al Matama", "el buhaira": "Al Buhaira",
            "dongola": "Dongola", "merowe": "Merwoe", "ed debba": "Ad Dabbah", "el dabba": "Ad Dabbah",
            "el golid": "Al Golid", "el burgaig": "Al Burgaig", "wadi halfa": "Halfa", "halfa": "Halfa",
            "delgo": "Delgo", "tokar": "Tawkar", "sinkat": "Sinkat", "haya": "Haya", "suakin": "Sawakin",
            "halaib": "Hala'ib", "jubayt elmaadin": "Jubayt Elma'aadin", "agig": "Agig", "dordieb": "Dordieb",
            "el ganab": "Al Ganab", "bahri": "Bahri", "khartoum north": "Bahri", "khartoum": "Khartoum",
            "um bada": "Um Bada",
            # added after inspecting unmatched names (log_sdn.txt)
            "jabal aulia": "Jebel Awlia", "ombadda": "Um Bada", "ombbada": "Um Bada", "oumbada": "Um Bada",
            "sharq el nile": "Sharg An Neel", "ailliet": "Al Lait", "kabkabiya": "Kebkabiya",
            "kalimendo": "Kelemando", "kalmando": "Kelemando", "kornoi": "Kernoi", "umkadada": "Um Kadadah",
            "umm keddada": "Um Kadadah", "um keddada": "Um Kadadah", "um buru": "Um Baru", "dimsu": "Damso",
            "e jebel marra": "Sharg Aj Jabal", "east jabal marra": "Sharg Aj Jabal",
            "sharg jabel marra": "Sharg Aj Jabal", "marshang": "Mershing", "rahad el berdi": "Rehaid Albirdi",
            "sharia": "Shia'ria", "sheiria": "Shia'ria", "elfardos": "Al Firdous",
            "central jabal marra": "Wasat Jabal Marrah", "central jabal marrah": "Wasat Jabal Marrah",
            "golo": "Wasat Jabal Marrah", "nertiti": "Gharb Jabal Marrah", "nertiti wjm": "Gharb Jabal Marrah",
            "rokoro": "Shamal Jabal Marrah", "abu gubeiha": "Abu Jubayhah", "abu kashola": "Abu Kershola",
            "algoz": "Al Quoz", "alleri": "Al Leri", "gedeer": "Ghadeer", "gedir": "Ghadeer",
            "eltadamoun": "At Tadamon - SK", "reif asharqi": "Ar Reif Ash Shargi", "abyei area": "Abyei PCA area",
            "qessan": "Geisan", "wad almahi": "Wad Al Mahi", "el qeteena": "Al Gitaina", "el gutaina": "Al Gitaina",
            "el douiem": "Ad Diwaim", "al dweim": "Ad Diwaim", "um ramtta": "Um Rimta", "umm ramtta": "Um Rimta",
            "um ramta": "Um Rimta", "el qaneb": "Al Ganab", "algunab": "Al Ganab",
            "jabiet al maadin": "Jubayt Elma'aadin", "toker": "Tawkar", "algerba": "Reifi Khashm Elgirba",
            "khashm ghirba": "Reifi Khashm Elgirba", "atbara river": "Reifi Nahr Atbara",
            "halfa eedeeda": "Halfa Aj Jadeedah", "hamshkorep": "Reifi Hamashkureib",
            "north dalta": "Reifi Shamal Ad Delta", "north delta": "Reifi Shamal Ad Delta",
            "talkok": "Reifi Telkok", "albutana": "Al Butanah", "alfshaga": "Al Fashaga",
            "e el qalabat": "Galabat Ash-Shargiah", "eastern el galabat": "Galabat Ash-Shargiah",
            "sharg el galabat": "Galabat Ash-Shargiah", "w el qalabat": "Al Galabat Al Gharbyah - Kassab",
            "west gallabat": "Al Galabat Al Gharbyah - Kassab",
            "western el galabat": "Al Galabat Al Gharbyah - Kassab",
            "gharb el galabat": "Al Galabat Al Gharbyah - Kassab", "el hehoud": "An Nuhud",
            "el nehoud": "An Nuhud", "elhould": "An Nuhud", "el obied": "Sheikan",
            "jabrat elshiekh": "Gebrat Al Sheikh", "jebrt el sheekh": "Gebrat Al Sheikh", "qebaesh": "Ghubaish",
            "um dam": "Um Dam Haj Ahmed", "wa banda": "Wad Bandah", "sharq al jeezira": "Sharg Al Jazirah",
            "e el jazeera": "Sharg Al Jazirah", "sharg el gezira": "Sharg Al Jazirah", "wad madani": "Medani Al Kubra",
            "gre wad madani": "Medani Al Kubra", "greater wad madani": "Medani Al Kubra",
            "24 al gurashi": "Al Qurashi", "gorrashi": "Al Qurashi", "janub el gezira": "Janub Al Jazirah",
            "s el jazeera": "Janub Al Jazirah", "southern el gezira": "Janub Al Jazirah", "alborgag": "Al Burgaig",
            "aldaba": "Ad Dabbah", "dalgo": "Delgo", "marawi": "Merwoe", "al khowey": "Al Khiwai",
            "alkhowai": "Al Khiwai", "almairam": "Al Meiram", "alodaiya": "Al Idia", "el odaya": "Al Idia",
            "al dalanj": "Dilling", "zamzam": "Al Fasher", "kalma": "Beliel"},
}


class Gazetteer:
    """COD-AB admin-1/admin-2 with name matching."""

    def __init__(self, iso):
        self.iso = iso
        z = zipfile.ZipFile(CODAB / f"{iso.lower()}.geojson.zip")
        d = json.loads(z.read(f"{iso.lower()}_admin2.geojson"))
        rows = []
        for f in d["features"]:
            p = f["properties"]
            if p["adm2_pcode"] == "Unspecified":
                continue
            rows.append((p["adm1_pcode"], p["adm1_name"], p["adm2_pcode"], p["adm2_name"]))
        self.adm2 = pd.DataFrame(rows, columns=["admin1_pcode", "admin1", "admin2_pcode", "admin2"])
        if iso == "SOM":   # pseudo unit for 'Banadir' reported as a single district
            self.adm2.loc[len(self.adm2)] = ["SO22", "Banadir", "SO22", "Banadir"]
        self.adm1 = self.adm2.drop_duplicates("admin1_pcode")[["admin1_pcode", "admin1"]]
        self.a1_by_code = dict(zip(self.adm1.admin1_pcode, self.adm1.admin1))
        self.a2_by_code = {r.admin2_pcode: r for r in self.adm2.itertuples()}
        self.a1_alias = {norm(k): v for k, v in ADM1_ALIAS.get(iso, {}).items()}
        self.a2_alias = {norm(k): v for k, v in ADM2_ALIAS.get(iso, {}).items()}

    def match_adm1(self, name, code=None):
        from rapidfuzz import fuzz, process
        if code and str(code).strip().upper() in self.a1_by_code:
            c = str(code).strip().upper()
            if name is None or fuzz.token_sort_ratio(skel(name), skel(self.a1_by_code[c])) >= 60 \
                    or norm(name) in self.a1_alias:
                return c, "pcode", 100
        if name is None:
            return None, None, 0
        n = norm(name)
        if n in self.a1_alias:
            nm = self.a1_alias[n]
            c = self.adm1.loc[self.adm1.admin1 == nm, "admin1_pcode"]
            if len(c):
                return c.iloc[0], "alias", 100
        names = {r.admin1_pcode: skel(r.admin1) for r in self.adm1.itertuples()}
        res = process.extractOne(skel(name), names, scorer=fuzz.ratio)
        if res and res[1] >= 85:
            return res[2], "fuzzy", res[1]
        return None, None, res[1] if res else 0

    def match_adm2(self, name, a1code=None, code=None):
        """Return (admin2_pcode, method, score)."""
        from rapidfuzz import fuzz, process
        if code is not None:
            c = str(code).strip().upper()
            if self.iso == "SDN" and re.fullmatch(r"SD\d{5}", c) is None and re.fullmatch(r"\d{1,3}", c):
                c = None      # bare locality IDs (LID) use an older numbering
            if c and c in self.a2_by_code:
                r = self.a2_by_code[c]
                if name is None or fuzz.ratio(skel(name), skel(r.admin2)) >= 70 \
                        or self.a2_alias.get(norm(name)) == r.admin2:
                    return c, "pcode", 100
        if name is None:
            return None, None, 0
        n = norm(name)
        if self.iso == "SOM" and (a1code == "SO22" or a1code is None) and \
                self.a2_alias.get(n) == "Banadir":
            return "SO22", "alias", 100
        pool = self.adm2 if a1code is None else self.adm2[self.adm2.admin1_pcode == a1code]
        if self.iso == "SOM" and a1code != "SO22":
            pool = pool[pool.admin2_pcode != "SO22"]
        if n in self.a2_alias and self.a2_alias[n]:
            hit = pool[pool.admin2 == self.a2_alias[n]]
            if len(hit) == 1:
                return hit.admin2_pcode.iloc[0], "alias", 100
            hit = self.adm2[self.adm2.admin2 == self.a2_alias[n]]
            if len(hit) == 1:
                return hit.admin2_pcode.iloc[0], "alias_other_admin1", 95
        sk = skel(name)
        if not sk:
            return None, None, 0
        if len(pool):
            choices = {r.admin2_pcode: skel(r.admin2) for r in pool.itertuples()}
            res = process.extract(sk, choices, scorer=fuzz.ratio, limit=2)
            if res and res[0][1] >= 85 and (len(res) == 1 or res[0][1] - res[1][1] >= 5 or res[0][1] == 100):
                return res[0][2], "fuzzy", res[0][1]
            res2 = process.extract(sk, choices, scorer=fuzz.partial_ratio, limit=2)
            if res2 and len(sk) >= 5 and res2[0][1] >= 95 and (len(res2) == 1 or res2[0][1] - res2[1][1] >= 10):
                return res2[0][2], "fuzzy_partial", res2[0][1]
        # outside the reported admin-1 (boundary changes, e.g. Sudan West Kordofan 2013)
        choices = {r.admin2_pcode: skel(r.admin2) for r in self.adm2.itertuples()}
        res = process.extract(sk, choices, scorer=fuzz.ratio, limit=2)
        if res and res[0][1] >= 92 and (len(res) == 1 or res[0][1] - res[1][1] >= 8):
            return res[0][2], "fuzzy_other_admin1", res[0][1]
        return None, None, (res[0][1] if res else 0)


# --------------------------------------------------------------------------- periods
def ym(y, m):
    return pd.Timestamp(year=int(y), month=int(m), day=1)


def parse_month(v, year):
    """Month value -> (start, end) Timestamps, or None."""
    if v is None:
        return None
    if isinstance(v, (dt.datetime, dt.date)):
        return ym(v.year, v.month), ym(v.year, v.month)
    if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)):
        if 1 <= int(v) <= 12 and year:
            return ym(year, int(v)), ym(year, int(v))
        return None
    s = str(v).strip().lower()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})(-\d{1,2})?( 00:00:00)?", s)
    if m:
        return ym(m.group(1), m.group(2)), ym(m.group(1), m.group(2))
    m = re.fullmatch(r"(\d{1,2})\s+([a-z]+)", s)        # '02 February'
    if m and m.group(2) in MONTHS and year:
        return ym(year, MONTHS[m.group(2)]), ym(year, MONTHS[m.group(2)])
    toks = re.findall(r"[a-z]+", s)
    ms = [MONTHS.get(t, MON3.get(t[:4] if t.startswith("sept") else t[:3])) for t in toks]
    ms = [x for x in ms if x]
    yr = re.search(r"(20\d\d)", s)
    y = int(yr.group(1)) if yr else year
    if not ms or not y:
        return None
    return ym(y, ms[0]), ym(y, ms[-1])


def months_between(a, b):
    return (b.year - a.year) * 12 + b.month - a.month + 1


# --------------------------------------------------------------------------- manifests
# kind: presence / reach_3w (presence + reach from the same 3W rows) / cwg / matrix / srf2014 /
#       hrp_wide / hrp_state2018 / hrp2019 / drought2023 / hnrp2026 / skip
# period: (start, end) 'YYYY-MM' used when rows carry no month; ptype; year for month columns;
# rank: release order within the series (higher wins).
S3 = "hdx_3w/som/somalia-operational-presence/"
SR = "hdx_response/som/"
MANIFEST = {"som": [
    dict(f="hdx_3w/som/somalia-who-is-doing-what-and-where-3w-2/160525_3W_Master_Q1_2016_Public.xlsx",
         kind="reach_3w", series="som_3w", period=("2016-01", "2016-03"), ptype="quarter", rank=201601),
    dict(f="hdx_3w/som/somalia-who-is-doing-what-and-where-3w-2/160525_3W_Master_Q1_2016_dashboard.csv",
         kind="skip", why="same Q1 2016 records as the _Public.xlsx (dashboard extract, fewer columns)"),
    dict(f=S3 + "3W_All_Clusters_Quarter_I_Jan_-_March__2019.xlsx", kind="reach_3w", series="som_3w",
         period=("2019-01", "2019-03"), ptype="quarter", rank=201903),
    dict(f=S3 + "3W_All_Cluster_Quarter_II_Apr_-_Jun__2019.xlsx", kind="reach_3w", series="som_3w",
         period=("2019-04", "2019-06"), ptype="quarter", rank=201906),
    dict(f=S3 + "3W_All_Cluster_Quarter_III_Jul_-_Sep__2019.xlsx", kind="reach_3w", series="som_3w",
         period=("2019-07", "2019-09"), ptype="quarter", rank=201909),
    dict(f=S3 + "3w_all_cluster_Quarter_IV_Oct_-_Dec__2019.xlsx", kind="reach_3w", series="som_3w",
         period=("2019-10", "2019-12"), ptype="quarter", rank=201912),
    dict(f=S3 + "3W_All_Clusters_January_2020.csv", kind="reach_3w", series="som_3w",
         period=("2020-01", "2020-01"), ptype="month", rank=202001),
    dict(f=S3 + "3W_All_Clusters_February_2020.csv", kind="reach_3w", series="som_3w",
         period=("2020-02", "2020-02"), ptype="month", rank=202002),
    dict(f=S3 + "3W_All_Clusters_March_2020.csv", kind="reach_3w", series="som_3w",
         period=("2020-03", "2020-03"), ptype="month", rank=202003),
] + [
    dict(f=S3 + fn, kind="presence", series="som_3w", period=(p, p), ptype="month", rank=int(p.replace("-", "")),
         note="reach columns not used: '# OF BENEFICIARIES' / 'Individuals' / 'Households' are misaligned "
              "between rows (individuals sometimes under '# OF BENEFICIARIES', households under 'Individuals')")
    for fn, p in [("3W__All_Clusters__April_2020.xlsx", "2020-04"), ("3W_All_Clusters_May_2020.xlsx", "2020-05"),
                  ("3W_All_Clusters_June_2020.xlsx", "2020-06"), ("3W_All_Clusters_July_2020.xlsx", "2020-07"),
                  ("3W_All_Clusters_August_2020.xlsx", "2020-08")]
] + [
    dict(f=S3 + f"3W_All_Clusters_{m}_2020.xlsx", kind="skip",
         why="HTML page saved from the defunct humanitarianresponse.info link, not data")
    for m in ["September", "October", "November", "December"]
] + [
    dict(f=S3 + "3W_All_Clusters_March_2021.xlsx", kind="reach_3w", series="som_3w",
         period=("2021-03", "2021-03"), ptype="month", rank=202103),
    dict(f=S3 + "3W_All_Clusters_September_2021.xlsx", kind="presence", series="som_3w",
         period=("2021-09", "2021-09"), ptype="month", rank=202109),
    dict(f=S3 + "3W_All_Clusters_January_2022.xlsx", kind="presence", series="som_3w",
         period=("2022-01", "2022-01"), ptype="month", rank=202201),
    dict(f=S3 + "3W_All_Clusters_February_2022.xlsx", kind="presence", series="som_3w",
         period=("2022-02", "2022-02"), ptype="month", rank=202202),
    dict(f=S3 + "3W_All_Clusters_March_2022.xlsx", kind="presence", series="som_3w",
         period=("2022-03", "2022-03"), ptype="month", rank=202203),
    dict(f="hdx_3w/som/ocha-somalia-operational-presence-2022/OCHA_SOM_Drought_Partner_Presence_2022.xlsx",
         kind="presence", series="som_3w", year=2022, ptype="month", rank=202200,
         note="drought partner presence; ranked below the all-cluster monthly 3W where months overlap"),
    dict(f="hdx_3w/som/ocha-somalia-operational-presence-2022/SOM_Drought_Partner_Presence_2022_Nov.xlsx",
         kind="presence", series="som_3w", year=2022, ptype="month", rank=202200.5,
         note="drought partner presence (Nov release); ranked below the all-cluster monthly 3W"),
    dict(f=S3 + "ocha_som_operational_presence_3w_data_oct2022.xlsx", kind="presence", series="som_3w",
         period=("2022-10", "2022-10"), ptype="month", rank=202210),
    dict(f="hdx_3w/som/somalia-who-is-doing-what-and-where-3w/OCHA_SOM_Operational_Presence_3W_data_Oct2022.xlsx",
         kind="skip", why="duplicate of somalia-operational-presence/ocha_som_operational_presence_3w_data_oct2022.xlsx"),
    dict(f=S3 + "3ws-05-july_2023.xlsx", kind="presence", series="som_3w", year=2023, ptype="month", rank=202307,
         ytd=("2023-01", "2023-07"), note="Month = 7 (July 2023) or 'YTD' (read as January-July 2023, range)"),
    dict(f="hdx_3w/som/somalia-who-is-doing-what-and-where-3w/3Ws_05-July_2023.xlsx", kind="skip",
         why="duplicate of somalia-operational-presence/3ws-05-july_2023.xlsx"),
    dict(f=S3 + "3w_-operational-presence_jan_nov-2023.xlsx", kind="skip",
         why="no cluster/sector column (org x district list only) and the month is filled for ~1% of rows"),
    dict(f="hdx_3w/som/somalia-who-is-doing-what-and-where-3w/3w_-operational-presence_Jan_Nov-2023.xlsx",
         kind="skip", why="duplicate of somalia-operational-presence/3w_-operational-presence_jan_nov-2023.xlsx"),
    dict(f=S3 + "3ws-2023-consolidated.xlsx", kind="reach_3w", series="som_3w", year=2023, ptype="month",
         rank=202312, sheet="DATA", overrides={"month": "Month"},
         note="activity rows; Month takes values 1-3 only (Q1 2023); 'Total USD transferred' used as US$; "
              "no individuals-reached column"),
    dict(f="hdx_3w/som/somalia-who-is-doing-what-and-where-3w/3Ws_2023_Consolidated.xlsx", kind="skip",
         why="duplicate of somalia-operational-presence/3ws-2023-consolidated.xlsx"),
    dict(f=S3 + "3Ws_All_Clusters_1st_Qtr_2024.xlsx", kind="presence", series="som_3w", year=2024,
         ptype="month", rank=202403),
    dict(f=S3 + "Operational_Partners_Presence_Jan-Sep_2024.xlsx", kind="reach_3w", series="som_3w", year=2024,
         ptype="month", rank=202409, overrides={"month": "Reporting \nMonth", "reached": "Total Individulals reached",
                                                  "usd": "Total USD transferred"},
         note="reach by reporting month, labelled cumulative=False; but in ~1/3 of activity series reported for 3+ "
              "months the figure rises every month, so some partners report cumulative-to-date figures"),
    dict(f=S3 + "3W_Operational_Presence_Dataset_Jan-Nov_2024.xlsx", kind="presence", series="som_3w",
         year=2024, ptype="month", rank=202411),
    dict(f=S3 + "3W_Operational_Presence_Dataset_January_-_March_2025.xlsx", kind="presence", series="som_3w",
         year=2025, ptype="month", rank=202503),
    dict(f=S3 + "3W_Operational_Presence_Dataset_January_-_April_2025.xlsx", kind="presence", series="som_3w",
         year=2025, ptype="month", rank=202504),
    dict(f=S3 + "3W_Operational_Presence_Dataset_January_-_August.xlsx", kind="presence", series="som_3w",
         year=2025, ptype="month", rank=202508),
    dict(f=S3 + "3w-operational-presence-dataset_january-september.xlsx", kind="presence", series="som_3w",
         year=2025, ptype="month", rank=202509),
    dict(f=S3 + "3W_Operational_Presence_Dataset_January_-_October.xlsx", kind="presence", series="som_3w",
         year=2025, ptype="month", rank=202510),
    dict(f=S3 + "3W_Operational_Presence_Dataset_January_-_December_2025.xlsx", kind="presence",
         series="som_3w", year=2025, ptype="month", rank=202512),
    dict(f=S3 + "3W_Operational_Presence_Dataset_January_-_June_2026.xlsx", kind="presence", series="som_3w",
         year=2026, ptype="month", rank=202606),
    # ---- response monitoring
    dict(f=SR + "srf-2014/Response_Data_2014.csv", kind="srf2014", series="som_srf2014", rank=2014),
    dict(f=SR + "srf-2014/Response_Data_2014.xlsx", kind="skip",
         why="same 2014 data as Response_Data_2014.csv (wide monthly sheets); the CSV is already long"),
    dict(f=SR + "srf-2014/Overall_SRF_2015.xlsx.csv", kind="skip",
         why="2015 monthly sheets with merged indicator headers whose sub-columns change from sheet to sheet "
             "(target / reached / reached-this-month); not parsed reliably"),
    dict(f=SR + "total-number-of-people-targeted-and-reached-per-re/Somalia_Monitoring_Matrix_-_as_of_November_2017.xlsx",
         kind="matrix", series="som_matrix", year=2017, rank=2017),
    dict(f=SR + "total-number-of-people-targeted-and-reached-per-re/Somalia_Monitoring_Matrix_-_as_of_September_2018.xlsx",
         kind="matrix", series="som_matrix", year=2018, rank=2018),
    dict(f=SR + "total-number-of-people-targeted-and-reached-per-re/Somalia_Monitoring_Matrix_-_as_of_October_2019.xlsx",
         kind="matrix", series="som_matrix", year=2019, rank=2019),
    dict(f=SR + "total-number-of-people-targeted-and-reached-per-re/Somalia_Monitoring_Matrix_-_as_of_October_2019.google sheet",
         kind="skip", why="HTML (Google Sheets login page), not data"),
    dict(f=SR + "total-number-of-people-targeted-and-reached-per-re/Somalia_OCHA_-_Monitoring_Matrix_2017.google sheet",
         kind="skip", why="HTML (Google Sheets login page), not data"),
    dict(f=SR + "somalia-pin-targeted-reached-by-location-and-clust/somalia-drought-affected-targeted-reached-by-location.csv",
         kind="drought2023", series="som_drought2023", rank=202307),
    dict(f=SR + "somalia-2026-hnrp-cluster-response-monitoring-data/Somalia_2026_HNRP_Cluster_Response_Monitoring_Dataset_January_to_March_2026_updated.xlsx",
         kind="hnrp2026", series="som_hnrp2026", rank=202603),
    dict(f=SR + "somalia-sam-admissions-in-2015/SAM_Admissions_2015.xlsx", kind="skip",
         why="SAM admissions (nutrition caseload treated), not people reached/targeted/US$; out of scope here"),
] + [dict(f=SR + "somalia-acute-malnutrition-burden-and-prevalence/" + fn, kind="skip",
          why="malnutrition burden/prevalence (need), not response")
     for fn in ["2021_Post_Gu_AMN_Burden_and_Prevalence_-_9_Sep_2021.xlsx",
                "FSNAU_Nutrition_Surveys_data-Gu_and_Deyr_2020.xlsx", "FSNAU_Survey_Results-_2017-2020.xlsx",
                "somalia-2023-post-gu-acute-malnutrition-burden-and-prevalence-by-district-21-sep-2023.xlsx",
                "Somalia_2022_Post_Gu_Total_Acute_Malnutrition_Burden_and_Prevalence_for_Aug_2022_to_Jul_20.xlsx"]],
    "sdn": []}

# Somalia Cash Working Group files (monthly, region-level 2018-21, district-level 2022-23)
for p in sorted((AID / SR / "cash-based-programming-in-somalia").glob("*")):
    rel = str(p.relative_to(AID))
    n = p.name.lower()
    if "2024" in n or "2025" in n:
        MANIFEST["som"].append(dict(f=rel, kind="skip", why="HTML (Google Drive page), not data"))
        continue
    if n == "somalia_cash_august_2019.xlsx":
        MANIFEST["som"].append(dict(f=rel, kind="skip",
                                    why="value column is '# of HOUSEHOLDS' (not individuals); not converted"))
        continue
    m = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)"
                  r"[_ -]*(?:to[_ -]*(january|february|march|april|may|june|july|august|september|october|"
                  r"november|december)[_ -]*)?(20\d\d)", n)
    if "raw_dataset_2023" in n:
        y, a, b = 2023, 1, 12
    else:
        y = int(m.group(3))
        a, b = MONTHS[m.group(1)], MONTHS[m.group(2) or m.group(1)]
    MANIFEST["som"].append(dict(f=rel, kind="cwg", series="som_cwg", year=y,
                                period=(f"{y}-{a:02d}", f"{y}-{b:02d}"), ptype="month",
                                rank=y * 100 + b, multi_sheet=(a != b and "2021" in n and "january_to_march" in n)))

D3 = "hdx_3w/sdn/sudan-operational-presence/"
DR = "hdx_response/sdn/"
MANIFEST["sdn"] = [
    dict(f=D3 + "Sudan_3ws_Combined_2014-2019_.xlsx", kind="presence", series="sdn_3w", ptype="annual",
         rank=201912.5, sheet="Combined", overrides={"adm2": "admin2Name", "adm2_code": "Locality_Code"},
         note="one file for 2014-2019; rows carry Year -> annual windows"),
] + [dict(f=D3 + f"Sudan_3w_{y}.xlsx", kind="skip",
          why="superseded by Sudan_3ws_Combined_2014-2019_.xlsx (compiled later, adds locality P-codes). Row counts "
              "match within 1 except 2015 (year file 2,476 rows vs 2,364 in Combined) and 2018 (3,065 vs 3,240)")
     for y in range(2014, 2020)] + [
    dict(f=D3 + "Sudan_3w_2020.xlsx", kind="presence", series="sdn_3w", period=("2020-08", "2020-08"),
         ptype="snapshot", rank=202008, note="compiled August 2020 (HDX description)"),
    dict(f="hdx_3w/sdn/who-is-doing-what-and-where-in-sudan-nov/cleaned_compiled_Nov_3ws.xlsx", kind="presence",
         series="sdn_3w", period=("2020-11", "2020-11"), ptype="snapshot", rank=202011),
    dict(f="hdx_3w/sdn/sudan-who-does-what-where-november-2020/cleaned_compiled_Nov_3ws.xlsx", kind="skip",
         why="earlier copy of the November 2020 3W (re-posted in who-is-doing-what-and-where-in-sudan-nov)"),
    dict(f=D3 + "Sudan_3w_2021.xlsx", kind="presence", series="sdn_3w", period=("2021-03", "2021-03"),
         ptype="snapshot", rank=202103, note="'as of March 2021' (HDX description; sheet is named '2020 3Ws compiled')"),
    dict(f=D3 + "Sudan_3w_31122021.xlsx", kind="presence", series="sdn_3w", period=("2021-12", "2021-12"),
         ptype="snapshot", rank=202112),
    dict(f=D3 + "Sudan_3w_01072022.xlsx", kind="presence", series="sdn_3w", period=("2022-07", "2022-07"),
         ptype="snapshot", rank=202207, sheet="3Ws_by_Locality"),
    dict(f="hdx_3w/sdn/sudan-who-is-doing-what-and-where-3ws/SDN_2022_3Ws-Jul-2022.xlsx", kind="skip",
         why="byte-identical copy of Sudan_3w_01072022.xlsx"),
    dict(f=D3 + "Sudan_3w_18062023.xlsx", kind="presence", series="sdn_3w", year=2023, ptype="range",
         rank=202306, sheet="3W Master Data"),
    dict(f=D3 + "2023_Consolidated_3W_data_April_to_31_July.xlsx", kind="presence", series="sdn_3w", year=2023,
         ptype="range", rank=202307),
    dict(f=D3 + "2023_Consolidated_3W_data_April_to_31_Aug_hxl.xlsx", kind="presence", series="sdn_3w",
         year=2023, ptype="range", rank=202308, period=("2023-04", "2023-08")),
    dict(f=D3 + "2023_Consolidated_3W_data_April_to_31_Oct_hxl.xlsx", kind="presence", series="sdn_3w",
         year=2023, ptype="range", rank=202310, period=("2023-04", "2023-10")),
    dict(f=D3 + "2023_Consolidated_3W_data_April_to_31_Dec_hxl.xlsx", kind="presence", series="sdn_3w",
         year=2023, ptype="range", rank=202312, period=("2023-04", "2023-12")),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-31-march.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202403, sheet="3W_master_data"),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-31-march.xlsx", kind="presence", series="sdn_3w", year=2023,
         ptype="range", rank=202312.5, sheet="3Ws data Dec 23", tag="Dec23 sheet",
         note="second sheet: April-December 2023 cumulative list"),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-31-may.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202405),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-30-june.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202406),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-30-july.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202407),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-30-aug.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202408),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-oct.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202410),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-nov.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202411),
    dict(f=D3 + "2024-consolidated-3w-data-jan-to-dec.xlsx", kind="presence", series="sdn_3w", year=2024,
         ptype="month", rank=202412),
] + [dict(f=D3 + fn, kind="presence", series="sdn_3w", year=2025, ptype="month", rank=202500 + r)
     for fn, r in [("2025-consolidated-3w-data-jan.xlsx", 1), ("2025-consolidated-3w-data-jan-to-feb.xlsx", 2),
                   ("2025-consolidated-3w-data-january-to-march.xlsx", 3),
                   ("2025-consolidated-3w-data-january-to-april.xlsx", 4),
                   ("2025-consolidated-3w-data-january-to-may.xlsx", 5),
                   ("2025-consolidated-3w-data-january-to-june.xlsx", 6),
                   ("2025-consolidated-3w-data-january-to-july.xlsx", 7),
                   ("2025-consolidated-3w-data-january-to-august.xlsx", 8),
                   ("2025-consolidated-3w-data-january-to-september.xlsx", 9),
                   ("2025-consolidated-3w-data-january-to-october.xlsx", 10),
                   ("2025-consolidated-3w-data-january-to-november.xlsx", 11),
                   ("2025-consolidated-3w-data-january-to-december.xlsx", 12)]] + \
    [dict(f=D3 + fn, kind="presence", series="sdn_3w", year=2026, ptype="month", rank=202600 + r)
     for fn, r in [("2026-consolidated-3w-data-january.xlsx", 1),
                   ("2026-consolidated-3w-data-january-to-february.xlsx", 2),
                   ("2026-consolidated-3w-data-January-to-March.xlsx", 3),
                   ("2026-consolidated-3w-data-January-to-April.xlsx", 4),
                   ("2026-consolidated-3w-data-january-to-may.xlsx", 5),
                   ("2026-consolidated-3w-data-january-to-June.xlsx", 6),
                   ("2026-consolidated-3w-data-january-to-july.xlsx", 7)]] + [
    # reach from the post-April-2023 5W raw sheet
    dict(f=D3 + "Sudan_3w_18062023.xlsx", kind="reach_rows", series="sdn_3w_reach", year=2023, ptype="range",
         rank=202306, sheet="All clusters_RawData", tag="RawData",
         note="activity rows with 'Total Beneficiary Reached' (April-June 2023)"),
    # HRP response monitoring
    dict(f=DR + "sudan-2018-hrp-response-monitoring-4ws/sudan-people-reached-by-state-jan-dec-2018_hrp.xlsx",
         kind="hrp_state2018", series="sdn_hrp", period=("2018-01", "2018-12"), rank=201812),
    dict(f=DR + "sudan-people-reached-by-locality-jan-dec-2019_hrp/sudan-people-reached-by-locality-jan-dec-2019_hrp.xlsx",
         kind="hrp2019", series="sdn_hrp", period=("2019-01", "2019-12"), rank=201912),
    dict(f=DR + "sudan-2020-hrp-response-monitoring-4ws-quarter-1/2020-hrp-sectors-response-jan-mar-v1-hxl.xlsx",
         kind="hrp_wide", series="sdn_hrp", period=("2020-01", "2020-03"), rank=202003,
         sheet="HXL LocalityQ1PiNTargetReached"),
    dict(f=DR + "sudan-2020-hrp-response-monitoring-4ws-quarter-1/2020-HRP-Sectors-Response-Jan-Jun-HXLV1.xlsx",
         kind="hrp_wide", series="sdn_hrp", period=("2020-01", "2020-06"), rank=202006,
         sheet="Jan-Jun 2020 Response-Locality"),
    dict(f=DR + "sudan-2020-hrp-response-monitoring-4ws-quarter-1/2020-HRP-Sectors-Response-Jan-Dec-HXLV2.xlsx",
         kind="hrp_wide", series="sdn_hrp", period=("2020-01", "2020-12"), rank=202012,
         sheet="Jan-Dec 2020 Response-Locality"),
    dict(f=DR + "sudan-2021-hrp-response-monitoring-4ws/2021-HRP-Sectors-Response-Jan-Mar.xlsx", kind="hrp_wide",
         series="sdn_hrp", period=("2021-01", "2021-03"), rank=202103),
    dict(f=DR + "sudan-2021-hrp-response-monitoring-4ws/2021-HRP-Sectors-Response-Jan-Sept.xlsx", kind="hrp_wide",
         series="sdn_hrp", period=("2021-01", "2021-09"), rank=202109),
    dict(f=DR + "sudan-2021-hrp-response-monitoring-4ws/2021-HRP-Sectors-Response-Jan-Dec.xlsx", kind="hrp_wide",
         series="sdn_hrp", period=("2021-01", "2021-12"), rank=202112),
    dict(f=DR + "sudan-2022-hrp-response-monitoring-4ws/2022-HRP-Sectors-Response-Jan-Jun.xlsx", kind="hrp_wide",
         series="sdn_hrp", period=("2022-01", "2022-06"), rank=202206),
]


# --------------------------------------------------------------------------- record builders
def file_md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def rows_to_records(rows, start, roles):
    """Yield dicts of role -> raw value for data rows."""
    for r in rows[start:]:
        if r is None:
            continue
        rec = {k: (r[j] if j < len(r) else None) for k, j in roles.items()}
        if all(v is None for v in rec.values()):
            continue
        yield rec


def clean_org(v):
    if v is None:
        return None
    s = norm(v)
    return s or None


def is_total_label(v):
    return v is not None and re.fullmatch(r"(grand )?totals?|sub ?totals?|overall|all|total no of .*|no of .*",
                                          norm(v) or "") is not None


def file_period(m):
    if m.get("period"):
        a, b = m["period"]
        return pd.Timestamp(a + "-01"), pd.Timestamp(b + "-01")
    return None


def parse_3w(path, m, log):
    """Presence (and reach where the file has it) records from a 3W-type file."""
    book = read_book(path)
    need = ("cluster",)
    pick = pick_sheet(book, need=need, sheet=m.get("sheet"), overrides=m.get("overrides"))
    if pick is None:
        raise ValueError("no sheet with cluster and admin columns found; sheets: " + ", ".join(book))
    name, start, roles, rows, hi = pick
    if "adm2" not in roles and "adm2_code" not in roles:
        raise ValueError(f"sheet '{name}' has no admin-2 column (roles found: {sorted(roles)})")
    fp = file_period(m)
    out, bad_month, n_dates_in_reach = [], Counter(), 0
    for rec in rows_to_records(rows, start, roles):
        if rec.get("cluster") is None and rec.get("org") is None:
            continue
        if is_total_label(rec.get("adm1")) or is_total_label(rec.get("cluster")):
            continue
        cl = str(rec.get("cluster") or "")
        if cl.startswith("#") or norm(cl) in ("cluster", "sector", "cluster aor"):
            continue          # a second header row or an HXL row inside the data
        per = None
        ptype = m.get("ptype", "month")
        if m.get("ytd") and str(rec.get("month")).strip().upper() == "YTD":
            rec["month"] = None
            per = tuple(pd.Timestamp(x + "-01") for x in m["ytd"])
            ptype = "range"
        elif "month" in roles and rec.get("month") is not None:
            year = m.get("year")
            if "year" in roles and num(rec.get("year")) == num(rec.get("year")):
                year = int(num(rec["year"]))
            per = parse_month(rec["month"], year)
            if per is None:
                bad_month[str(rec["month"])[:30]] += 1
            elif per[0] != per[1]:
                ptype = "range"
            elif m.get("ptype") in ("range",):
                ptype = "month"
        elif "year" in roles and num(rec.get("year")) == num(rec.get("year")) and not fp:
            y = int(num(rec["year"]))
            per = (ym(y, 1), ym(y, 12))
        if per is None and rec.get("month") is not None and "month" in roles:
            continue          # unparseable month value: counted above, row dropped
        if per is None:
            if fp is None:
                bad_month["<no period>"] += 1
                continue
            per = fp
            if m.get("ptype") == "range" and per[0] == per[1]:
                ptype = "month"
        reached = num(rec.get("reached")) if "reached" in roles else np.nan
        if "reached" in roles and is_date_like(rec.get("reached")):
            n_dates_in_reach += 1
        usd = num(rec.get("usd")) if "usd" in roles else np.nan
        out.append(dict(cluster_raw=rec.get("cluster"), org=clean_org(rec.get("org")),
                        adm1_raw=rec.get("adm1"), adm1_code_raw=rec.get("adm1_code"),
                        adm2_raw=rec.get("adm2"), adm2_code_raw=rec.get("adm2_code"),
                        period_start=per[0], period_end=per[1], period_type=ptype,
                        status=rec.get("status"), reached=reached, usd=usd))
    df = pd.DataFrame(out)
    log(f"    sheet '{name}', data from row {start + 1}, columns: " +
        ", ".join(f"{k}='{str(rows[hi][j] if j < len(rows[hi]) else '')[:25].strip()}'"
                  for k, j in sorted(roles.items(), key=lambda kv: kv[1])))
    if bad_month:
        log(f"    rows without a parseable period (dropped): {dict(bad_month.most_common(5))}")
    if n_dates_in_reach:
        log(f"    {n_dates_in_reach} reached values were Excel dates (corrupted), set to missing")
    return df


def parse_cwg(path, m, log):
    """Somalia Cash Working Group: individuals and US$ by region/district x cluster x month."""
    book = read_book(path)
    frames = []
    y = m["year"]
    for name, rows in book.items():
        hi, xi, sc = find_header(rows)
        if hi is None:
            continue
        ov = {"cluster": "Cash Modality", "reached": "Total Individuals Assisted",
              "usd": "Total USD Transferred", "month": "Cash Delivery Month"} if "raw_dataset_2023" in path.name.lower() else None
        roles = assign_roles(rows[hi], rows[xi] if xi is not None else None, ov)
        if "cluster" not in roles or ("adm1" not in roles and "adm2" not in roles):
            continue
        if "reached" not in roles:
            # first column whose header mentions individuals
            for j, h in enumerate(rows[hi]):
                if isinstance(h, str) and re.search(r"individual", h, re.I):
                    roles["reached"] = j
                    break
        start = max(hi, xi if xi is not None else -1) + 1
        # month: column, else sheet name, else file
        sheet_per = parse_month(name, y) if re.search(r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec",
                                                       name, re.I) else None
        fp = file_period(m)
        recs = []
        for rec in rows_to_records(rows, start, roles):
            if is_total_label(rec.get("adm1")) or rec.get("cluster") is None:
                continue
            if str(rec.get("cluster")).startswith("#") or norm(rec.get("cluster")) in ("cluster", "sector"):
                continue
            per = parse_month(rec.get("month"), y) if rec.get("month") is not None else None
            if per is None:
                per = sheet_per if (sheet_per and sheet_per[0] == sheet_per[1] and fp[0] != fp[1]) else fp
            if per[0] != per[1]:
                continue
            if rec.get("status") is not None and "plan" in str(rec["status"]).lower():
                continue
            recs.append(dict(cluster_raw=rec.get("cluster"), adm1_raw=rec.get("adm1"), adm1_code_raw=None,
                             adm2_raw=rec.get("adm2"), adm2_code_raw=None, period_start=per[0],
                             period_end=per[1], reached=num(rec.get("reached")), usd=num(rec.get("usd"))))
        if recs:
            log(f"    sheet '{name}': {len(recs)} rows; columns " +
                ", ".join(f"{k}='{str(rows[hi][j])[:25]}'" for k, j in sorted(roles.items(), key=lambda kv: kv[1])))
            frames.append(pd.DataFrame(recs))
        if not m.get("multi_sheet"):
            break
    if not frames:
        raise ValueError("no sheet with region/district, cluster and individuals columns")
    return pd.concat(frames, ignore_index=True)


def parse_matrix(path, m, log):
    """Somalia monitoring matrix: region x indicator; end-year target and cumulative reached by month."""
    book = read_book(path)
    rows = book.get("Monitoring Matrix by region")
    if rows is None:
        raise ValueError("no 'Monitoring Matrix by region' sheet")
    y = m["year"]
    title, sub = rows[0], rows[1]
    ncol = max(len(title), len(sub))
    titles, cur = [], None
    for j in range(ncol):
        t = title[j] if j < len(title) else None
        if t is not None:
            cur = str(t)
        titles.append(cur)
    out, skipped = [], Counter()
    for r in rows[2:]:
        if not r or r[0] is None or is_total_label(r[0]) or norm(r[0]) == "region":
            continue
        reg = r[0]
        for j in range(1, ncol):
            t, s = titles[j], (sub[j] if j < len(sub) else None)
            if t is None or ":" not in t or s is None:
                continue
            v = num(r[j] if j < len(r) else None)
            if v != v:
                if j < len(r) and r[j] not in (None, "", ".") and str(r[j]).startswith("#"):
                    skipped["#REF!"] += 1
                continue
            cl, ind = t.split(":", 1)
            ss = str(s).strip().lower()
            if "target" in ss:
                out.append(dict(adm1_raw=reg, cluster_raw=cl.strip(), indicator=re.sub(r"\s+", " ", ind).strip(),
                                measure="targeted", value=v, period_start=ym(y, 1), period_end=ym(y, 12),
                                cumulative=True))
            elif ss in MONTHS:
                out.append(dict(adm1_raw=reg, cluster_raw=cl.strip(), indicator=re.sub(r"\s+", " ", ind).strip(),
                                measure="reached", value=v, period_start=ym(y, 1), period_end=ym(y, MONTHS[ss]),
                                cumulative=True))
    if skipped:
        log(f"    cells with spreadsheet errors skipped: {dict(skipped)}")
    df = pd.DataFrame(out)
    log(f"    sheet 'Monitoring Matrix by region': {df.indicator.nunique()} indicators x "
        f"{df.adm1_raw.nunique()} regions")
    return df


def parse_srf2014(path, m, log):
    d = pd.read_csv(path)
    d = d[d.Region.notna() & ~d.Region.astype(str).str.lower().isin(["total", "somalia"])]
    out = []
    for r in d.itertuples(index=False):
        mo = int(r[2])
        reached, target = num(r[8]), num(r[6])
        base = dict(adm1_raw=r[0], cluster_raw=r[4], indicator=str(r[5]).strip(), cumulative=True)
        if reached == reached:
            out.append({**base, "measure": "reached", "value": reached, "period_start": ym(2014, 1),
                        "period_end": ym(2014, mo)})
        if target == target and mo == 12:
            out.append({**base, "measure": "targeted", "value": target, "period_start": ym(2014, 1),
                        "period_end": ym(2014, 12)})
    log("    columns: Region, Month Num, Category, Metric, End-year target (December rows), "
        "Cumulative Reached (to-date)")
    return pd.DataFrame(out)


def parse_drought2023(path, m, log):
    rows = read_book(path)["csv"]
    out = []
    for r in rows[3:]:
        if not r or r[2] is None:
            continue
        for j, meas in [(6, "targeted"), (7, "reached")]:
            v = num(r[j])
            if v == v:
                out.append(dict(adm1_raw=r[0], adm1_code_raw=r[1], adm2_raw=r[2], adm2_code_raw=r[3],
                                cluster_raw="all clusters", indicator="people (all clusters, drought response)",
                                measure=meas, value=v, period_start=ym(2023, 7), period_end=ym(2023, 7),
                                cumulative=True))
    log("    columns: Region, admin1Pcode, District, admin2Pcode, Target, Reached (single July 2023 snapshot)")
    return pd.DataFrame(out)


def parse_hnrp2026(path, m, log):
    book = read_book(path)
    rows = book["Cluster response Jan-mar_v2"]
    hdr = [str(h).strip() if h is not None else None for h in rows[0]]
    ix = {h: j for j, h in enumerate(hdr) if h}
    out = []
    for r in rows[1:]:
        cl = r[ix["Cluster"]]
        if cl is None or str(cl).startswith("IC-"):
            continue
        base = dict(adm1_raw=r[ix["Region"]], adm1_code_raw=r[ix["R_code"]], adm2_raw=r[ix["Districts"]],
                    adm2_code_raw=r[ix["District Pcode"]], cluster_raw=cl,
                    indicator="people reached (cluster: max across indicators)")
        for mo, col in [(1, "Jan"), (2, "Feb"), (3, "Mar")]:
            v = num(r[ix[col]])
            if v == v:
                out.append({**base, "measure": "reached", "value": v, "period_start": ym(2026, mo),
                            "period_end": ym(2026, mo), "cumulative": False})
        v = num(r[ix["Mar_Cum"]])
        if v == v:
            out.append({**base, "measure": "reached", "value": v, "period_start": ym(2026, 1),
                        "period_end": ym(2026, 3), "cumulative": True})
        v = num(r[ix["TARGET"]])
        if v == v:
            out.append({**base, "indicator": "people targeted (2026 HNRP)", "measure": "targeted", "value": v,
                        "period_start": ym(2026, 1), "period_end": ym(2026, 12), "cumulative": True})
    log("    sheet 'Cluster response Jan-mar_v2': monthly Jan-Mar reach (Jan, Feb, Mar), Mar_Cum, TARGET; "
        "inter-cluster rows (IC-*) dropped")
    return pd.DataFrame(out)


HRP_SECTOR = {"nutrition": "Nutrition", "nfi": "ES/NFI", "wash": "WASH", "education": "Education",
              "childprotection": "Child protection", "fsl": "FSL", "health": "Health", "gbv": "GBV",
              "protection": "Protection", "mine_action": "Mine action", "refugees": "Refugees (RCF)",
              "rcf": "Refugees (RCF)", "total": None, "all": None}


def parse_hrp_wide(path, m, log):
    """Sudan HRP response monitoring: locality x sector, PIN / target / reached (HXL tagged)."""
    book = read_book(path)
    rows = book[m["sheet"]] if m.get("sheet") else list(book.values())[0]
    hi, xi, sc = find_header(rows)
    if xi is None:
        raise ValueError("no HXL row")
    hdr, hxl = rows[hi], rows[xi]
    roles = assign_roles(hdr, hxl)
    fp = file_period(m)
    y = fp[0].year
    cols = []
    for j, t in enumerate(hxl):
        p = hxl_parse(t) if t else None
        if not p or p[0] not in ("reached", "targeted"):
            continue
        at = [a for a in str(t).lower().replace(" ", "").split("+")[1:]]
        sec = at[0] if at else None
        if sec not in HRP_SECTOR:
            continue
        if HRP_SECTOR[sec] is None:
            continue
        extra = at[1:]
        h = str(hdr[j]) if j < len(hdr) and hdr[j] is not None else ""
        if p[0] == "targeted":
            per, cum, ind = (ym(y, 1), ym(y, 12)), True, f"people targeted ({HRP_SECTOR[sec]})"
        else:
            q = [e for e in extra if re.fullmatch(r"q\d", e)]
            tail = [e for e in extra if not re.fullmatch(r"q\d|\d", e)]
            if q and len(extra) == 1:          # single quarter, e.g. +Q2
                k = int(q[0][1])
                per, cum = (ym(y, 3 * k - 2), ym(y, 3 * k)), False
            else:
                per, cum = fp, True
                mh = re.search(r"jan\s*-\s*([a-z]+)", h.lower())
                if mh and MON3.get(mh.group(1)[:3]):   # header says e.g. 'Nutrition Jan-Jun'
                    per = (fp[0], ym(y, MON3[mh.group(1)[:3]]))
            ind = f"people reached ({HRP_SECTOR[sec]}{' ' + ' '.join(tail) if tail else ''})"
            if per[0] == fp[0] and per[1] == fp[1] and len(extra) and q:
                ind = ind
        cols.append((j, sec, p[0], per, cum, ind))
    out = []
    start = max(hi, xi) + 1
    for r in rows[start:]:
        if not r:
            continue
        a2 = r[roles["adm2"]] if "adm2" in roles and roles["adm2"] < len(r) else None
        a1 = r[roles["adm1"]] if "adm1" in roles and roles["adm1"] < len(r) else None
        if a2 is None or is_total_label(a2) or is_total_label(a1):
            continue
        for j, sec, meas, per, cum, ind in cols:
            v = num(r[j] if j < len(r) else None)
            if v != v:
                continue
            out.append(dict(adm1_raw=a1, adm1_code_raw=r[roles["adm1_code"]] if "adm1_code" in roles else None,
                            adm2_raw=a2, adm2_code_raw=r[roles["adm2_code"]] if "adm2_code" in roles else None,
                            cluster_raw=HRP_SECTOR[sec], indicator=ind, measure=meas, value=v,
                            period_start=per[0], period_end=per[1], cumulative=cum))
    df = pd.DataFrame(out)
    odd = [(str(hdr[j])[:30], p[0].strftime("%b"), p[1].strftime("%b")) for j, s, me, p, c, i in cols
           if me == "reached" and (p[0], p[1]) != fp]
    log(f"    sheet '{m.get('sheet') or list(book)[0]}': {len(cols)} reached/targeted columns; "
        f"PIN columns ignored" + (f"; columns with their own window: {odd}" if odd else ""))
    return df


def parse_hrp2019(path, m, log):
    rows = read_book(path)["Jan-Dec 2019 Response-Locality"]
    hdr = rows[0]
    out = []
    for r in rows[2:]:
        if not r or r[2] is None or is_total_label(r[2]):
            continue
        for j in range(3, len(hdr)):
            if hdr[j] is None:
                continue
            v = num(r[j] if j < len(r) else None)
            if v == v:
                out.append(dict(adm1_raw=r[1], adm2_raw=r[2], cluster_raw=str(hdr[j]),
                                indicator=f"people reached ({hdr[j]})", measure="reached", value=v,
                                period_start=ym(2019, 1), period_end=ym(2019, 12), cumulative=True))
    log("    sheet 'Jan-Dec 2019 Response-Locality': sector columns read from the header row "
        "(the HXL tags in this file are wrong, e.g. FSL tagged #inneed)")
    return pd.DataFrame(out)


def parse_hrp_state2018(path, m, log):
    rows = read_book(path)["HXL sheet"]
    out = []
    for r in rows[2:]:
        if not r or r[0] is None:
            continue
        v = num(r[2] if len(r) > 2 else None)
        if v == v:
            out.append(dict(adm1_raw=r[0], cluster_raw=r[1], indicator=f"people reached ({r[1]})",
                            measure="reached", value=v, period_start=ym(2018, 1), period_end=ym(2018, 12),
                            cumulative=True))
    log("    sheet 'HXL sheet': State x Sector x Reached (state level only)")
    return pd.DataFrame(out)


# --------------------------------------------------------------------------- main per country
def resolve_units(df, gz, names_seen, source):
    """Add admin1/admin2 P-codes and canonical names; record raw names in names_seen."""
    for c in ["adm1_raw", "adm1_code_raw", "adm2_raw", "adm2_code_raw"]:
        if c not in df:
            df[c] = None
        df[c] = [None if (x is None or (isinstance(x, float) and np.isnan(x))
                          or norm(x) in ("", "0", "unspecified", "different areas", "na", "none"))
                 else str(x).strip() for x in df[c]]
    hdr = df.adm1_raw.map(lambda x: x is not None and (x.startswith("#") or norm(x) in ("region", "state")))
    df.drop(df.index[hdr.values], inplace=True)
    key = df[["adm1_raw", "adm1_code_raw", "adm2_raw", "adm2_code_raw"]].astype(object).where(
        df[["adm1_raw", "adm1_code_raw", "adm2_raw", "adm2_code_raw"]].notna(), None)
    keys = key.drop_duplicates()
    res = {}
    for k in keys.itertuples(index=False):
        a1, a1c, a2, a2c = [None if (x is None or (isinstance(x, float) and np.isnan(x))) else x for x in k]
        a1s = str(a1).strip() if a1 is not None else None
        a2s = str(a2).strip() if a2 is not None else None
        if a2s is None and a2c is not None and str(a2c).strip().upper() in gz.a1_by_code \
                and str(a2c).strip().upper() not in gz.a2_by_code:
            a1c, a2c = (a1c or a2c), None      # an admin-1 P-code in the district P-code column
        p1, m1, s1 = gz.match_adm1(a1s, a1c)
        p2, m2, s2 = gz.match_adm2(a2s, p1, a2c) if (a2s or a2c) else (None, None, 0)
        if p2 and not p1:
            p1 = gz.a2_by_code[p2].admin1_pcode
            m1 = "from_admin2"
        if p2 and p1 and gz.a2_by_code[p2].admin1_pcode != p1:
            p1 = gz.a2_by_code[p2].admin1_pcode
            m1 = (m1 or "") + "+reassigned_by_admin2"
        res[tuple(k)] = (p1, m1, p2, m2, s2)
        nk = (a1s, str(a1c) if a1c is not None else None, a2s, str(a2c) if a2c is not None else None)
        names_seen[nk]["sources"].add(source)
        names_seen[nk]["res"] = (p1, m1, p2, m2, s2)
    t = [res[tuple(None if (x is None or (isinstance(x, float) and np.isnan(x))) else x for x in k)]
         for k in key.itertuples(index=False)]
    df["admin1_pcode"] = [x[0] for x in t]
    df["admin2_pcode"] = [x[2] for x in t]
    df["admin1"] = df.admin1_pcode.map(gz.a1_by_code)
    df["admin2"] = df.admin2_pcode.map(lambda c: gz.a2_by_code[c].admin2 if c in gz.a2_by_code else None)
    # keep raw names where unmatched so nothing is lost
    df["admin1"] = df.admin1.where(df.admin1.notna(), df.adm1_raw.astype(object))
    df["admin2"] = df.admin2.where(df.admin2.notna() | df.adm2_raw.isna(), df.adm2_raw.astype(object))
    return df


def run(iso):
    ISO3 = {"som": "SOM", "sdn": "SDN"}[iso]
    log = Log(iso)
    gz = Gazetteer(ISO3)
    log(f"62_tidy_3w.py  {ISO3}  run {dt.datetime.now():%Y-%m-%d %H:%M}")
    log(f"Canonical units: COD-AB {len(gz.adm2)} admin-2 units in {len(gz.adm1)} admin-1 "
        f"(input/areas/codab/{iso}.geojson.zip)\n")
    names_seen = defaultdict(lambda: {"sources": set(), "res": None})
    pres_parts, reach_parts, cluster_map = [], [], Counter()
    listed = set()
    hashes = {}
    log("=" * 100)
    log("FILES")
    log("=" * 100)
    for m in MANIFEST[iso]:
        p = AID / m["f"]
        listed.add(p.resolve())
        label = m["f"] + (f" [{m['tag']}]" if m.get("tag") else "")
        if m["kind"] == "skip":
            log(f"SKIP  {label}\n    {m['why']}")
            continue
        if not p.exists():
            log(f"SKIP  {label}\n    file missing")
            continue
        h = file_md5(p)
        if h in hashes and not m.get("tag") and hashes[h] != m["f"]:
            log(f"SKIP  {label}\n    byte-identical to {hashes[h]}")
            continue
        hashes.setdefault(h, m["f"])
        mark = len(log.lines)
        try:
            if m["kind"] in ("presence", "reach_3w", "reach_rows"):
                d = parse_3w(p, m, log)
            elif m["kind"] == "cwg":
                d = parse_cwg(p, m, log)
            else:
                d = {"matrix": parse_matrix, "srf2014": parse_srf2014, "drought2023": parse_drought2023,
                     "hnrp2026": parse_hnrp2026, "hrp_wide": parse_hrp_wide, "hrp2019": parse_hrp2019,
                     "hrp_state2018": parse_hrp_state2018}[m["kind"]](p, m, log)
        except Exception as e:  # noqa
            del log.lines[mark:]
            log(f"SKIP  {label}\n    could not parse: {e}")
            continue
        details = log.lines[mark:]
        del log.lines[mark:]
        if d is None or len(d) == 0:
            log(f"SKIP  {label}\n    no usable rows")
            continue
        d["source_file"] = m["f"] + (f"#{m['sheet']}" if m.get("sheet") and m.get("tag") else "")
        d["series"] = m["series"]
        d["rank"] = m["rank"]
        d = resolve_units(d, gz, names_seen, m["f"])
        d["cluster"] = d.cluster_raw.map(map_cluster)
        for raw, cl in d[["cluster_raw", "cluster"]].astype(str).value_counts().index:
            cluster_map[(str(raw).strip()[:60], cl)] += 1
        msg = []
        if m["kind"] in ("presence", "reach_3w", "reach_rows"):
            if m["kind"] != "reach_rows":
                dd = d[d.cluster.notna()].copy()
                dd["admin_level"] = 2
                pres_parts.append(dd)
                msg.append(f"presence rows {len(dd):,}")
            if m["kind"] in ("reach_3w", "reach_rows"):
                r = d.copy()
                planned = r.status.astype(str).str.lower().str.contains("plan", na=False)
                rr = []
                for meas, col, ind in [("reached", "reached", "individuals reached (sum over activity rows)"),
                                       ("usd", "usd", "US$ transferred (sum over activity rows)")]:
                    x = r[(~planned) & r[col].notna()].copy()
                    if len(x) == 0:
                        continue
                    x["measure"], x["value"], x["indicator"] = meas, x[col], ind
                    # 3W activity figures run over the activity's duration, not the month: cumulative
                    # unless the file reports by reporting month (2023+, Sudan RawData is a window)
                    x["cumulative"] = not (m.get("year") and m["kind"] == "reach_3w" and m["rank"] >= 202301)
                    rr.append(x)
                    msg.append(f"{meas} filled {len(x) / max(1, (~planned).sum()):.0%} of non-planned rows")
                if planned.any():
                    msg.append(f"{planned.sum():,} 'planned' rows excluded from reach")
                if rr:
                    reach_parts.append(pd.concat(rr, ignore_index=True))
        elif m["kind"] == "cwg":
            for meas, col in [("reached", "reached"), ("usd", "usd")]:
                x = d[d[col].notna()].copy()
                if len(x):
                    x["measure"], x["value"] = meas, x[col]
                    x["indicator"] = "individuals reached with cash (CWG)" if meas == "reached" else \
                        "US$ transferred (CWG)"
                    x["cumulative"] = False
                    reach_parts.append(x)
                    msg.append(f"{meas} rows {len(x):,}")
        else:
            reach_parts.append(d)
            msg.append(f"reach rows {len(d):,}")
        lvl = "admin-2" if d.adm2_raw.notna().any() else "admin-1"
        ps, pe = d.period_start.min(), d.period_end.max()
        log(f"USE   {label}\n    {m['series']}; {lvl}; {ps:%Y-%m} to {pe:%Y-%m}; " + "; ".join(msg) +
            (f"\n    note: {m['note']}" if m.get("note") else ""))
        log.lines.extend(details)
    # files present on disk but not in the manifest
    for sub in ["hdx_3w", "hdx_response"]:
        for p in sorted((AID / sub / iso).rglob("*")):
            if p.is_file() and p.resolve() not in listed:
                log(f"SKIP  {p.relative_to(AID)}\n    not in the manifest (not inspected)")
    dirs = [d for d in (AID / "hdx_3w" / iso).iterdir() if d.is_dir() and not any(d.iterdir())]
    for d in dirs:
        log(f"SKIP  {d.relative_to(AID)}/\n    empty directory (download failed, e.g. 401)")

    # ------------------------------------------------------------- presence
    log("\n" + "=" * 100)
    log("PRESENCE: de-duplication (rule 2: one file per series x period window; highest rank wins)")
    log("=" * 100)
    P = pd.concat(pres_parts, ignore_index=True)
    win = P.groupby(["series", "period_start", "period_end", "source_file"]).agg(rank=("rank", "max"),
                                                                                 n=("org", "size")).reset_index()
    win = win.sort_values(["series", "period_start", "period_end", "rank"])
    keep = win.groupby(["series", "period_start", "period_end"]).tail(1)
    dropped = win.merge(keep[["series", "period_start", "period_end", "source_file"]], how="left",
                        on=["series", "period_start", "period_end", "source_file"], indicator=True)
    dropped = dropped[dropped._merge == "left_only"]
    for r in dropped.itertuples():
        w = keep[(keep.series == r.series) & (keep.period_start == r.period_start) & (keep.period_end == r.period_end)]
        log(f"  {r.period_start:%Y-%m}..{r.period_end:%Y-%m}: dropped {r.source_file} ({r.n:,} rows), "
            f"kept {w.source_file.iloc[0]}")
    P = P.merge(keep[["series", "period_start", "period_end", "source_file"]],
                on=["series", "period_start", "period_end", "source_file"])
    P["unit_key"] = P.admin2_pcode.fillna("raw:" + P.admin1.astype(str) + "|" + P.admin2.astype(str))
    grp = ["series", "admin1", "admin1_pcode", "admin2", "admin2_pcode", "unit_key", "period_start",
           "period_end", "period_type", "cluster", "source_file"]
    P[["admin1_pcode", "admin2_pcode"]] = P[["admin1_pcode", "admin2_pcode"]].fillna("")
    pres = (P.groupby(grp, dropna=False)
            .agg(n_partners=("org", "nunique"), n_activities=("org", "size")).reset_index())
    pres[["admin1_pcode", "admin2_pcode"]] = pres[["admin1_pcode", "admin2_pcode"]].replace("", None)
    pres.insert(0, "iso3", ISO3)
    pres = pres.drop(columns="unit_key")
    pres["period_months"] = [months_between(a, b) for a, b in zip(pres.period_start, pres.period_end)]
    # nested cumulative windows with the same start (e.g. Sudan April-June ... April-December 2023):
    # latest_window marks the longest one so that they are not stacked by mistake
    mx = pres.groupby(["series", "period_start"]).period_end.transform("max")
    pres["latest_window"] = (pres.period_end == mx) | (pres.period_type == "month")
    pres = pres.sort_values(["period_start", "period_end", "admin1", "admin2", "cluster"]).reset_index(drop=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pres.to_parquet(OUT / f"presence_{iso}.parquet", index=False)

    # ------------------------------------------------------------- reach
    log("\n" + "=" * 100)
    log("REACH: de-duplication (rule 3: one file per series x window x measure; highest rank wins)")
    log("=" * 100)
    R = pd.concat(reach_parts, ignore_index=True)
    R["admin_level"] = np.where(R.adm2_raw.notna() | R.adm2_code_raw.notna(), 2, 1)
    win = R.groupby(["series", "period_start", "period_end", "measure", "source_file"]).agg(
        rank=("rank", "max"), lvl=("admin_level", "max"), n=("value", "size")).reset_index()
    win = win.sort_values(["series", "period_start", "period_end", "measure", "lvl", "rank"])
    keep = win.groupby(["series", "period_start", "period_end", "measure"]).tail(1)
    dropped = win.merge(keep[["series", "period_start", "period_end", "measure", "source_file"]], how="left",
                        indicator=True)
    dropped = dropped[dropped._merge == "left_only"]
    for r in dropped.itertuples():
        w = keep[(keep.series == r.series) & (keep.period_start == r.period_start) &
                 (keep.period_end == r.period_end) & (keep.measure == r.measure)]
        log(f"  {r.series} {r.measure} {r.period_start:%Y-%m}..{r.period_end:%Y-%m}: dropped {r.source_file} "
            f"({r.n:,} rows), kept {w.source_file.iloc[0]}")
    if not len(dropped):
        log("  no overlapping windows within a series")
    R = R.merge(keep[["series", "period_start", "period_end", "measure", "source_file"]])
    R[["admin1_pcode", "admin2_pcode"]] = R[["admin1_pcode", "admin2_pcode"]].fillna("")
    R["admin2"] = R.admin2.where(R.admin_level == 2, None)
    R["admin2_pcode"] = R.admin2_pcode.where(R.admin_level == 2, "")
    R["cumulative"] = R.cumulative.astype(bool)
    R["indicator"] = R.indicator.astype(str)
    grp = ["series", "admin_level", "admin1", "admin1_pcode", "admin2", "admin2_pcode", "period_start",
           "period_end", "cumulative", "cluster", "indicator", "measure", "source_file"]
    reach = R.groupby(grp, dropna=False).agg(value=("value", "sum"), n_rows=("value", "size")).reset_index()
    reach[["admin1_pcode", "admin2_pcode"]] = reach[["admin1_pcode", "admin2_pcode"]].replace("", None)
    reach["period_type"] = np.where(reach.period_start == reach.period_end, "month", "range")
    # longest cumulative window per series x year x start (do not sum nested cumulative windows)
    reach["year"] = reach.period_start.dt.year
    mx = reach.groupby(["series", "year", "period_start", "measure", "indicator"]).period_end.transform("max")
    reach["latest_window"] = (reach.period_end == mx) | (~reach.cumulative)
    reach = reach.drop(columns="year")
    reach.insert(0, "iso3", ISO3)
    reach = reach.sort_values(["series", "period_start", "period_end", "admin1", "admin2", "cluster",
                               "measure"]).reset_index(drop=True)
    reach.to_parquet(OUT / f"reach_{iso}.parquet", index=False)

    # ------------------------------------------------------------- cluster mapping
    log("\n" + "=" * 100)
    log("CLUSTER MAPPING (raw label -> standard; rows)")
    log("=" * 100)
    agg = defaultdict(int)
    for (raw, cl), n in cluster_map.items():
        agg[(cl, raw)] += n
    for (cl, raw), n in sorted(agg.items()):
        log(f"  {cl:<14} <- {raw}  ({n:,} distinct-label occurrences)")

    # ------------------------------------------------------------- names table (+ CBPF)
    pf = pd.read_csv(AID / "cbpf" / "poolfund.csv")
    cc = {"SOM": "SO", "SDN": "SD"}[ISO3]
    ids = pf[(pf.CountryCode == cc) & pf.ParentPooledFundId.isna()].Id.tolist()
    cb = pd.read_csv(AID / "cbpf" / "ProjectSummaryAggV2.csv", usecols=["PFId", "AdmLoc1", "AdmLoc2", "AYr"])
    cb = cb[cb.PFId.isin(ids)].dropna(subset=["AdmLoc1"]).drop_duplicates(["AdmLoc1", "AdmLoc2"])
    cbd = cb.rename(columns={"AdmLoc1": "adm1_raw", "AdmLoc2": "adm2_raw"})[["adm1_raw", "adm2_raw"]].copy()
    resolve_units(cbd, gz, names_seen, f"cbpf/ProjectSummaryAggV2.csv (PFId {','.join(map(str, ids))})")
    rows = []
    for (a1, a1c, a2, a2c), v in names_seen.items():
        p1, m1, p2, m2, s2 = v["res"]
        rows.append(dict(admin1_raw=a1, admin1_pcode_raw=a1c, admin2_raw=a2, admin2_pcode_raw=a2c,
                         admin1_pcode=p1, admin1=gz.a1_by_code.get(p1),
                         admin2_pcode=p2, admin2=gz.a2_by_code[p2].admin2 if p2 in gz.a2_by_code else None,
                         match_method=m2, match_score=s2, n_sources=len(v["sources"]),
                         sources=" | ".join(sorted(v["sources"]))))
    names = pd.DataFrame(rows).sort_values(["admin1_pcode", "admin2_pcode", "admin1_raw", "admin2_raw"],
                                           na_position="last")
    names.to_csv(OUT / f"admin2_names_{iso}.csv", index=False)
    log("\n" + "=" * 100)
    log("ADMIN NAMES")
    log("=" * 100)
    with2 = names[names.admin2_raw.notna() | names.admin2_pcode_raw.notna()]
    log(f"  distinct raw admin1/admin2 combinations: {len(names):,} ({len(with2):,} with an admin-2 name/code)")
    log(f"  matched to a COD admin-2: {with2.admin2_pcode.notna().mean():.1%}; methods: "
        f"{with2.match_method.value_counts().to_dict()}")
    un = with2[with2.admin2_pcode.isna()]
    if len(un):
        log("  unmatched admin-2 names (raw admin1 / admin2 / sources):")
        for r in un.itertuples():
            log(f"    {r.admin1_raw} / {r.admin2_raw} / {r.admin2_pcode_raw}  [{r.sources[:110]}]")
    # unmatched share of presence rows
    log(f"  presence rows without admin-2 P-code: {pres.admin2_pcode.isna().mean():.1%}; "
        f"reach (admin-2) rows without P-code: "
        f"{reach[reach.admin_level == 2].admin2_pcode.isna().mean():.1%}")

    # ------------------------------------------------------------- FEWS NET crosswalk
    fews_crosswalk(iso, ISO3, gz, log)

    # ------------------------------------------------------------- coverage summary
    log("\n" + "=" * 100)
    log("COVERAGE")
    log("=" * 100)
    for s, g in pres.groupby("series"):
        mo = g[g.period_type == "month"]
        log(f"  presence {s}: {len(g):,} rows; windows {g.groupby(['period_start', 'period_end']).ngroups}; "
            f"{g.period_start.min():%Y-%m}..{g.period_end.max():%Y-%m}; distinct admin-2 "
            f"{g.admin2_pcode.nunique()}; monthly windows {mo.period_start.nunique()} months x "
            f"{mo.admin2_pcode.nunique()} admin-2 = {mo.groupby(['period_start', 'admin2_pcode']).ngroups:,} "
            f"admin-2-months with any partner; by period_type {g.period_type.value_counts().to_dict()}")
    for (s, me), g in reach.groupby(["series", "measure"]):
        lvl = g.admin_level.max()
        u = "admin2_pcode" if lvl == 2 else "admin1_pcode"
        log(f"  reach {s} {me}: {len(g):,} rows; admin-{lvl}; {g.period_start.min():%Y-%m}..{g.period_end.max():%Y-%m}; "
            f"windows {g.groupby(['period_start', 'period_end']).ngroups}; units {g[u].nunique()}; "
            f"unit-windows {g.groupby(['period_start', 'period_end', u]).ngroups:,}; "
            f"cumulative {g.cumulative.mean():.0%}")
    log.write()
    return pres, reach


def fews_crosswalk(iso, ISO3, gz, log):
    from rapidfuzz import fuzz
    cc = {"SOM": "SO", "SDN": "SD"}[ISO3]
    f = pd.read_parquet(FEWS, columns=["fnid", "country_code", "geographic_unit_name",
                                       "geographic_unit_full_name"])
    f = f[f.country_code == cc].drop_duplicates("fnid")
    rows = []
    for r in f.itertuples(index=False):
        full = str(r.geographic_unit_full_name).strip()
        parts = [p.strip() for p in full.split(",")]
        if parts and norm(parts[-1]) in ("somalia", "sudan"):
            parts = parts[:-1]
        unit = str(r.geographic_unit_name).strip()
        # geographic_unit_name may itself contain commas; strip it from the front
        rest = full[len(unit):].strip(" ,") if full.startswith(unit) else ", ".join(parts[1:])
        rp = [p.strip() for p in rest.split(",") if p.strip()]
        if rp and norm(rp[-1]) in ("somalia", "sudan"):
            rp = rp[:-1]
        a1 = rp[-1] if len(rp) >= 1 else None
        if a1 is not None and norm(a1) == norm(unit):
            a1 = None
        a2 = rp[-2] if len(rp) >= 2 else None
        vint = re.match(r"[A-Z]{2}(\d{4}[A-Z]\d)?", r.fnid)
        p1, m1, s1 = gz.match_adm1(a1)
        p2, m2, s2 = gz.match_adm2(a2, p1) if a2 else (None, None, 0)
        if a2 is None and a1 is None and unit and "IDP" in r.fnid:
            # IDP settlement units are named after their town: match the name as a district
            p2, m2, s2 = gz.match_adm2(re.sub(r"(?i)\bcamps?\b.*$", "", unit).strip() or unit, None)
            m2 = ("idp_" + m2) if m2 else None
            a2 = unit
        elif a2 is None and p1 is None and unit:
            # admin-1-level units (e.g. 'Banadir, Somalia')
            p1, m1, s1 = gz.match_adm1(unit)
        if ISO3 == "SOM" and p1 == "SO22" and not p2:
            p2, m2, s2 = "SO22", "banadir_region", 100
        # P-code embedded in the fnid (Somalia C3 units: SOyyyyC3 RR DD zz; Sudan C3: SDyyyyC3 SS LLL zz)
        code = None
        mm = re.fullmatch(r"SO\d{4}C3(\d{2})(\d{2})\d{2}", r.fnid)
        if mm:
            code = f"SO{mm.group(1)}{mm.group(2)}"
        mm = re.fullmatch(r"SD\d{4}C3(\d{2})(\d{3})\d{2}", r.fnid)
        if mm:
            code = f"SD{mm.group(1)}{mm.group(2)}"
        if ISO3 == "SOM" and code and code.startswith("SO22"):
            code = "SO22"
        code_ok = code in gz.a2_by_code if code else None
        if p2 is None and code_ok:
            nm = gz.a2_by_code[code].admin2
            sc = fuzz.ratio(skel(a2 or ""), skel(nm))
            p2, m2, s2 = code, "fnid_code", sc
        if p2 and (p1 is None or gz.a2_by_code[p2].admin1_pcode != p1):
            p1 = gz.a2_by_code[p2].admin1_pcode
        rows.append(dict(fnid=r.fnid, vintage=vint.group(1) if vint and vint.group(1) else r.fnid[:2] + "-other",
                         unit_name=unit, admin2_raw=a2, admin1_raw=a1,
                         admin1_pcode=p1, admin1=gz.a1_by_code.get(p1),
                         admin2_pcode=p2, admin2=gz.a2_by_code[p2].admin2 if p2 in gz.a2_by_code else None,
                         match_method=m2, match_score=s2, fnid_pcode=code,
                         fnid_pcode_agrees=(None if not code_ok else (code == p2)),
                         geographic_unit_full_name=full))
    x = pd.DataFrame(rows).sort_values("fnid")
    x.to_csv(OUT / f"fews_admin2_{iso}.csv", index=False)
    log("\n" + "=" * 100)
    log("FEWS NET CROSSWALK (fnid -> canonical admin-2)")
    log("=" * 100)
    log(f"  units: {len(x):,}; matched to admin-2: {x.admin2_pcode.notna().mean():.1%}; "
        f"methods {x.match_method.value_counts(dropna=False).to_dict()}")
    for v, g in x.groupby("vintage"):
        log(f"    {v}: {len(g):4d} units, matched {g.admin2_pcode.notna().mean():6.1%}, "
            f"name-matched {g.match_method.isin(['pcode', 'alias', 'fuzzy', 'fuzzy_partial', 'alias_other_admin1', 'fuzzy_other_admin1', 'banadir_region']).mean():6.1%}")
    chk = x[x.fnid_pcode_agrees.notna() & x.match_method.ne("fnid_code")]
    if len(chk):
        log(f"  check against the P-code embedded in C3 fnids: name match agrees for "
            f"{chk.fnid_pcode_agrees.astype(bool).mean():.1%} of {len(chk):,} units")
        dis = chk[~chk.fnid_pcode_agrees.astype(bool)].drop_duplicates(["admin2_raw", "admin1_raw"])
        for r in dis.head(40).itertuples():
            log(f"    disagree: {r.admin2_raw}, {r.admin1_raw}: name -> {r.admin2_pcode} {r.admin2}; "
                f"fnid code {r.fnid_pcode} {gz.a2_by_code[r.fnid_pcode].admin2}")
    un = x[x.admin2_pcode.isna()].drop_duplicates(["admin2_raw", "admin1_raw"])
    if len(un):
        log(f"  unmatched names ({len(un)} distinct admin2/admin1 pairs, "
            f"{x.admin2_pcode.isna().sum()} units):")
        for r in un.itertuples():
            log(f"    [{r.vintage}] {r.geographic_unit_full_name}")


if __name__ == "__main__":
    isos = [a for a in sys.argv[1:] if a in ("som", "sdn")] or ["som", "sdn"]
    for iso in isos:
        run(iso)
