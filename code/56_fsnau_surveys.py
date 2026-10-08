"""FSNAU (Somalia) seasonal nutrition and mortality survey results, 2009-2025.

Two sources, both from fsnau.org (FAO Somalia):

1. The FSNAU "Nutrition Summary Reports" portal (https://fsnau.org/nutrition/?season=YYYY/gu|deyr):
   one HTML table per season, one row per survey (livelihood zone / IDP / urban population),
   point estimates only: GAM and SAM (weight-for-height, WHO), CDR, U5DR, MUAC-GAM/SAM,
   morbidity, measles, stunting, underweight, vitamin A.  No confidence intervals, dates or
   sample sizes.  Older seasons (2009-2011) are entered inconsistently (one survey split
   across rows, values in the wrong columns); see `portal` flags.

2. The seasonal PDF reports (nutrition technical series reports 2010-2016, "Key Nutrition
   Results Summary" tables 2017-2024), which give GAM and SAM with 95% CIs, CDR and U5DR
   with CIs, fieldwork dates and (often) sample sizes.  Downloaded from the fsnau.org
   downloads feed (downloads.xml).  Parsed in `parse_pdfs()`; see table rules there.

Usage:
    python code/56_fsnau_surveys.py fetch   # portal pages + selected PDFs (cached, ~1s apart)
    python code/56_fsnau_surveys.py         # parse -> input/fsnau/surveys.csv (+ coverage table)
"""
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "fsnau"
RAW = OUT / "raw"
HTML = OUT / "html"
UA = {"User-Agent": "Mozilla/5.0 (research; FEWS NET evaluation)"}

# Seasonal reports to fetch: (season, title in downloads.xml).  One or more per season.
DOCS = [
    ("Deyr 2010/11", "FSNAU Technical Series Report Post Deyr 10-11 Nutrition Analysis"),
    ("Gu 2011", "FSNAU Nutrition Technical Series Report, Post Gu 2011 Analysis"),
    ("Deyr 2011/12", "FSNAU Post Deyr 2011/12-Nutrition Technical Report"),
    ("Gu 2012", "FSNAU Technical Series Report Post Gu 2012 Nutrition Analysis"),
    ("Deyr 2012/13", "FSNAU Technical Series Report Post Deyr 2012/13 Nutrition Analysis"),
    ("Gu 2013", "FSNAU Technical Series Report - Post Gu 2013 Nutrition Analysis"),
    ("Deyr 2013/14", "FSNAU Technical Series Report - Post Deyr 2013-14 Nutrition Analysis"),
    ("Gu 2014", "FSNAU Technical Series Report - Post Gu 2014 Nutrition Analysis Report"),
    ("Deyr 2014/15", "FSNAU Nutrition Analysis Technical Series Report Post Deyr 2014/15"),
    ("Gu 2015", "FSNAU Nutrition Analysis Technical Series Report Post Gu 2015"),
    ("Deyr 2015/16", "FSNAU 2015/16 Post - Deyr Nutrition Technical Report, April 2016"),
    ("Gu 2016", "FSNAU 2016 Post - Gu Nutrition Technical Report, December 2016"),
    ("Gu 2016", "Summary of the Nutrition Situation for Somalia Gu 2016"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Northwest"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Northeast and Central"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Central"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Hiran"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Shabelle and Banadir"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Bay and Bakool"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Gedo"),
    ("Deyr 2016/17", "Nutrition Situation Analysis Post Deyr 2016/17, Kismaiyo and Dhobley"),
    ("Gu 2017", "FSNAU-FEWS NET 2017 Post Gu Technical Release Final - 31 Aug 2017"),
    ("Gu 2017", "2017 Post Gu Joint FSNAU FEWS NET Presentation, 5 September 2017"),
    ("Deyr 2017/18", "Nutrition Situation Summary for Somalia - Deyr 2017"),
    ("Gu 2018", "Summary of Nutrition Situation for Somalia Gu, 2018"),
    ("Deyr 2018/19", "2018 Deyr Nutrition Summary Results"),
    ("Gu 2019", "Somalia 2019 Post Gu FSNAU Nutrition Survey Summary Results"),
    ("Deyr 2019/20", "2019 Post Deyr Assessment Key Nutrition Results, February 2020"),
    ("Gu 2020", "Somalia 2020 Post Gu Key Nutrition Results Summary, 30th Sep 2020"),
    ("Deyr 2020/21", "2020 Post Deyr Key Nutrition Results Summary, 4 Feb 2021"),
    ("Gu 2021", "Somalia 2021 Post Gu Nutrition Survey Summary Results"),
    ("Deyr 2021/22", "Somalia 2021 Post Deyr Nutrition Survey Summary Results"),
    ("Gu 2022", "Somalia 2022 Post Gu Nutrition Results Summary - 13 Sep 2022"),
    ("Deyr 2022/23", "Somalia 2022 Post Deyr Nutrition Results Summary, 28 Feb 2023"),
    ("Gu 2023", "Somalia 2023 Post G Nutrition Results Summary, 18 Sep 2023.pdf"),
    ("Deyr 2023/24", "Somalia 2023 Post Deyr Nutrition Results Summary"),
    ("Gu 2024", "Somalia 2024 Post Gu Acute Malnutrition Prevalence by District - 25 Sep 2024"),
    ("Gu 2024", "Somalia 2024 Post Gu IPC communication report"),
    ("Deyr 2024/25", "Somalia 2024 Post Deyr Assessment Key Nutrition Results Summary - Feb 24 2025"),
    # IPC acute malnutrition reports (some carry an annex of GAM with 95% CIs by survey)
    ("Gu 2020", "Somalia IPC Acute Food Insecurity and Acute Malnutrition Analyses report for August - December 2020"),
    ("Deyr 2020/21", "IPC Somalia Acute Food Insecurity Malnutrition Report, January-July 2021"),
    ("Gu 2021", "IPC Somalia Acute Food Insecurity Malnutrition, 2021 July-Dec Report"),
    ("Gu 2022", "IPC Famine Review Report Somalia - December 2022"),
    ("Gu 2023", "Somalia IPC Acute Food Insecurity Malnutrition Report, Aug Dec 2023"),
    ("Deyr 2023/24", "IPC Somalia Acute Food Insecurity Malnutrition, Jan-Jun 2024 Report"),
    ("Deyr 2024/25", "Somalia 2024 Post Deyr IPC Communication Report"),
]


def get(url, path, sleep=1.0):
    if path.exists() and path.stat().st_size > 0:
        return path
    time.sleep(sleep)
    r = requests.get(url, headers=UA, timeout=120, verify=False)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path


def fetch():
    import urllib3
    urllib3.disable_warnings()
    HTML.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    for y in range(2009, 2026):
        for s in ("gu", "deyr"):
            get(f"https://fsnau.org/nutrition/?season={y}/{s}", HTML / f"nutrition_{y}_{s}.html")
    feed = get("https://fsnau.org/downloads.xml", HTML / "downloads.xml.html")
    t = feed.read_text(encoding="utf-8", errors="replace")
    items = {}
    for it in re.findall(r"<item>(.*?)</item>", t, re.S):
        title = re.sub(r"\s+", " ", re.search(r"<title>(.*?)</title>", it, re.S).group(1)).strip()
        title = title.replace("&amp;", "&").replace("&#039;", "'")
        link = re.search(r"<link>(.*?)</link>", it).group(1)
        enc = re.search(r'enclosure url="([^"]*)"', it)
        items.setdefault(title, (link, enc.group(1) if enc else None))
    rows = []
    for season, title in DOCS:
        link, fileurl = items[title]
        if fileurl is None:  # resolve the item page to its file
            page = get(link, HTML / ("item_" + link.rstrip("/").split("/")[-1] + ".html"))
            hrefs = re.findall(r'href="([^"]+\.(?:pdf|xlsx?|zip|pptx?))"', page.read_text(errors="replace"))
            sidebar = re.findall(r'href="([^"]+\.(?:pdf|xlsx?|zip|pptx?))"', (HTML / "home.html").read_text(errors="replace")) \
                if (HTML / "home.html").exists() else []
            hrefs = [h for h in hrefs if h not in sidebar and "2026" not in h]
            fileurl = hrefs[0] if hrefs else None
        if fileurl is None:
            print("no file:", title)
            continue
        fileurl = fileurl.replace(" ", "%20").replace("http://", "https://").replace("www.fsnau.org", "fsnau.org")
        name = requests.utils.unquote(fileurl.split("/")[-1]).replace(" ", "_")
        try:
            get(fileurl, RAW / name)
            ok = True
        except Exception as e:  # noqa
            print("failed", fileurl, e)
            ok = False
        rows.append(dict(season=season, title=title, url=fileurl, file=name, ok=ok))
        print(season, name, ok)
    pd.DataFrame(rows).to_csv(OUT / "documents.csv", index=False)
    # HDX copies of FSNAU tables (the Deyr 2019/20 summary PDF on fsnau.org is an image)
    (RAW / "hdx").mkdir(exist_ok=True)
    for url in HDX:
        get(url, RAW / "hdx" / url.split("/")[-1])
    # text layer of every PDF, with page markers
    import fitz
    (OUT / "text").mkdir(exist_ok=True)
    for f in sorted(RAW.glob("*.pdf")):
        out = OUT / "text" / (f.name + ".txt")
        if not out.exists():
            d = fitz.open(f)
            out.write_text("\n".join(f"=====PAGE {i + 1}\n" + p.get_text() for i, p in enumerate(d)))
    # Checchi et al. (LSHTM) replication files: survey metadata with fieldwork months, 2013-2019.
    # No licence on the repositories; used only for fieldwork months (cited as secondary source).
    for repo, sub, files in [
        ("mortality_small_area_estimation", "mort", ["som_survey_metadata.xlsx"]),
        ("acute_malnutrition_predictive_models", "nut", ["som_survey_metadata_nut.xlsx"]),
    ]:
        (RAW / "checchi" / sub).mkdir(parents=True, exist_ok=True)
        for f in files:
            get(f"https://raw.githubusercontent.com/francescochecchi/{repo}/main/{f}", RAW / "checchi" / sub / f)


HDX = [
    "https://data.humdata.org/dataset/ccee1ec6-75b8-43df-98b0-6a521019e56b/resource/63c0dde6-8a17-4dad-b26a-226c15233eca/download/2019-post-deyr-assessment-key-nutrition-results-february-2020.xlsx",
    "https://data.humdata.org/dataset/6c4c69cf-8ca0-4bfc-8c46-73cdb18812d5/resource/db721063-7eac-4a3c-ab48-b629f7554d84/download/fsnau-survey-results-2017-2020.xlsx",
]




# ----------------------------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------------------------
NUM = r"\d+(?:\.\d+)?"
VALUE_COLS = ["gam", "gam_lo", "gam_hi", "sam", "sam_lo", "sam_hi", "muac_gam", "muac_gam_lo",
              "muac_gam_hi", "muac_sam", "cdr", "cdr_lo", "cdr_hi", "u5dr", "u5dr_lo", "u5dr_hi"]
# first season documented in the PDF technical series (transcribed); later seasons use the portal
TRANSCRIBED_SEASONS_END = (2016, "deyr")


def season_label(year, s):
    return f"Gu {year}" if s == "gu" else f"Deyr {year}/{str(year + 1)[-2:]}"


def season_key(label):
    m = re.match(r"(Gu|Deyr) (\d{4})", label)
    return int(m.group(2)), m.group(1).lower()


def season_order(label):
    y, s = season_key(label)
    return y + (0.5 if s == "deyr" else 0)


SYN = [
    (r"\bagro[\s-]*pastoral(ist)?s?\b", "agropastoral"), (r"\bagro[\s-]*past\.?\b", "agropastoral"),
    (r"\bap\b", "agropastoral"), (r"\bidp'?s\b", "idp"), (r"\bidps\b", "idp"),
    (r"\bnw\b", "northwest"), (r"\bne\b", "northeast"), (r"\bn\.?\b", "north"), (r"\bs\.?\b", "south"),
    (r"\bw\.?\b", "west"), (r"\be\.?\b", "east"), (r"\bl\.?\b", "lower"), (r"\bm\.?\b", "middle"),
    (r"bosas+o", "bossaso"), (r"gal(ca|ka|kac)y?yo", "galkayo"), (r"dol+ow|dowlo", "dolow"),
    (r"kismai?y[ou]", "kismayo"), (r"bele[dt]\s?we[iy]ne?", "beletweyne"), (r"dh?usa?mar[e]+b", "dhusamareb"),
    (r"togh?dh?eer", "togdheer"), (r"nugaa?l", "nugal"), (r"aduun", "addun"), (r"hargey?sa", "hargeisa"),
    (r"baydhab[ao]", "baidoa"), (r"wgolis", "west golis"), (r"egolis", "east golis"), (r"\bhaw?d\b", "hawd"),
    (r"matab[a]+n", "mataban"), (r"dhobl?ey|dobley", "dhobley"), (r"guban", "guban"),
]
STOP = {"lz", "livelihood", "livelihoods", "zone", "zones", "of", "the", "and", "region", "regions",
        "pastoralists", "survey", "combined", "cross", "cutting", "population", "district"}


def norm(name):
    t = str(name).lower().replace("&", " and ")
    t = re.sub(r"[()\[\]/,*:;]", " ", t)
    for a, b in SYN:
        t = re.sub(a, b, t)
    t = re.sub(r"[^a-z ]", " ", t)
    return [w for w in t.split() if w not in STOP]


def similarity(a, b):
    a, b = set(norm(a)), set(norm(b))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def pop_type(name):
    n = " ".join(norm(name))
    idp = "idp" in n
    urb = bool(re.search(r"\burban\b|\btown\b", n))
    if idp and urb:
        return "mixed"
    if idp:
        return "IDP"
    if urb:
        return "urban"
    return "rural"


def region_from_name(name):
    m = re.search(r"\(([^)]*)\)", str(name))
    if not m:
        return ""
    r = m.group(1).strip()
    # parentheses sometimes describe the livelihood ("Riverine& AP"), not a region
    if re.search(r"riverine|agro|urban|idp|pastoral|sorghum|cross|combined", r, re.I):
        return ""
    return r


def tofloat(x):
    if x is None:
        return None
    x = str(x).strip().replace("%", "")
    try:
        return float(x)
    except ValueError:
        return None


def portal():
    """All rows of the FSNAU nutrition portal, one per table row."""
    import html as H
    cols = ["population_group", "gam", "sam", "cdr", "u5dr", "vita", "muac_gam", "muac_sam",
            "morbidity", "measles", "stunting", "underweight"]
    rows = []
    for f in sorted(HTML.glob("nutrition_*_*.html")):
        y, s = re.match(r"nutrition_(\d{4})_(gu|deyr)", f.name).groups()
        t = f.read_text(encoding="utf-8", errors="replace")
        head = [re.sub("<[^>]+>", "", h).strip() for h in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)]
        assert head[:5] == ["Livelihood Zone", "GAM", "SAM", "CDR", "U5DR"], (f, head)
        for tr in re.findall(r"<tr>(.*?)</tr>", t, re.S):
            tds = [H.unescape(re.sub("<[^>]+>", "", x)).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(tds) == len(cols):
                r = dict(zip(cols, tds))
                r["population_group"] = re.sub(r"\s+", " ", r["population_group"])
                r.update(year=int(y), s=s, season=season_label(int(y), s), source_file=f"html/{f.name}",
                         source_url=f"https://fsnau.org/nutrition/?season={y}/{s}")
                rows.append(r)
    df = pd.DataFrame(rows)
    for c in cols[1:]:
        df[c] = df[c].map(tofloat)
    return df


def ipc_annex(fname, page):
    """Annex 1 of the IPC acute malnutrition reports: GAM (95% CI) this season and same season a year earlier."""
    CI = re.compile(rf"^({NUM})\s*(?:percent)?\s*\(\s*({NUM})\s*-\s*({NUM})\s*\)?$")
    REMARK = re.compile(r"^(Likely|Significant|Insignificant|Not [Ss]ignificant|Phase|\(only|change|No [Cc]hange|"
                        r"[Dd]eterioration|[Ii]mprovement)")
    pages = (OUT / "text" / (fname + ".txt")).read_text().split("=====PAGE ")
    txt = [p for p in pages if p.startswith(f"{page}\n")][0]
    lines = [l.strip() for l in txt.split("\n")]
    start = max(i for i, l in enumerate(lines[:40]) if re.search(r"value|Remarks", l)) + 1
    if lines[start].startswith("Remarks"):
        start += 1
    rows, name, vals, buf = [], [], [], ""
    for l in lines[start:]:
        if not l:
            continue
        if buf:
            l, buf = buf + " " + l, ""
        if len(vals) < 2:
            if l in ("N/A", "NA"):
                vals.append((None, None, None))
                continue
            m = CI.match(l)
            if m:
                vals.append(tuple(float(x) for x in m.groups()))
                continue
            if re.match(rf"^{NUM}\s*(percent)?\s*\(\s*{NUM}\s*-?\s*$", l):
                buf = l
                continue
            name.append(l)
            continue
        if re.match(rf"^[-−]?{NUM}$|^_$|^N/A$|^[<>]0[,.]\d+$", l) or REMARK.match(l):
            continue
        rows.append((" ".join(name), vals))
        name, vals = [l], []
    if name and len(vals) == 2:
        rows.append((" ".join(name), vals))
    out = []
    for nm, v in rows:
        nm = re.sub(r"^(Not Significant( - Phase change)?|Significant \w+)\s+", "", nm)
        ok = not re.search(r"\d|>0", nm)  # a stray value in the name means the row layout broke
        out.append(dict(population_group=nm, ok=ok, cur=v[0], prev=v[1], file=fname, page=page))
    return out


IPC_ANNEXES = [  # (file, page, season of 'cur', season of 'prev')
    ("IPC-Somalia-Acute-Food-Insecurity-Malnutrition-Jan-Jun-2024-Report.pdf", 21, "Deyr 2023/24", "Deyr 2022/23"),
    ("Somalia-2024-Post-Gu-IPC-communication-report_0.pdf", 26, "Gu 2024", "Gu 2023"),
    ("IPC_Somalia_Acute_Food_Insecurity_Malnutrition_Jan_Jun2025_Report_0.pdf", 30, "Deyr 2024/25", "Deyr 2023/24"),
]


def ipc_cis():
    rows = []
    for f, p, cur, prev in IPC_ANNEXES:
        for r in ipc_annex(f, p):
            if not r["ok"]:
                continue
            for season, v in ((cur, r["cur"]), (prev, r["prev"])):
                if v[0] is not None:
                    rows.append(dict(season=season, population_group=r["population_group"], gam=v[0],
                                     gam_lo=v[1], gam_hi=v[2], ci_source=f"raw/{f} p{p}",
                                     ci_role="current" if season == cur else "previous-year comparison"))
    return pd.DataFrame(rows)


def summary_pdfs():
    """GAM and SAM (first two values after each name) from the one-page seasonal summaries, 2016-2024."""
    docs = pd.read_csv(OUT / "documents.csv")
    docs = docs[docs.title.str.contains("Summary|Summary Results|Key Nutrition Results", case=False)
                & ~docs.title.str.contains("IPC|Prevalence by District", case=False)]
    rows = []
    for _, d in docs.iterrows():
        tf = OUT / "text" / (d.file + ".txt")
        if not tf.exists():
            continue
        lines = [l.strip() for l in tf.read_text().split("\n")]
        page = 0
        name = None
        nums = []
        for l in lines + ["END"]:
            m = re.match(r"=====PAGE (\d+)", l)
            if m:
                page = int(m.group(1))
                continue
            if re.match(rf"^{NUM}%?$", l):
                if name:
                    nums.append(float(l.rstrip("%")))
                continue
            if name and len(nums) >= 2:
                rows.append(dict(season=d.season, population_group=name, gam=nums[0], sam=nums[1],
                                 file=d.file, page=page))
            name, nums = (l if re.search(r"[A-Za-z]{3}", l) else None), []
    df = pd.DataFrame(rows)
    return df[~df.population_group.str.contains("Median|Population|Acute|Children|Coverage|Rate|MUAC|"
                                                 "Day|Sanitation|Water|Vaccin|Suppl", case=False)]


def match(left, right, key="population_group", gam_left="gam", gam_right="gam", thresh=0.5):
    """One-to-one name matching within season (global greedy on score); an equal GAM adds 0.3."""
    out = []
    for season, L in left.groupby("season"):
        R = right[right.season == season]
        pairs = []
        for i, l in L.iterrows():
            for j, r in R.iterrows():
                sc = similarity(l[key], r[key])
                if pd.notna(l.get(gam_left)) and pd.notna(r.get(gam_right)) and abs(l[gam_left] - r[gam_right]) < 0.05:
                    sc += 0.3
                if sc >= thresh:
                    pairs.append((sc, i, j))
        ui, uj = set(), set()
        for sc, i, j in sorted(pairs, key=lambda x: -x[0]):
            if i not in ui and j not in uj:
                ui.add(i)
                uj.add(j)
                out.append((i, j, round(sc, 2)))
    return out


def hdx_tables():
    """FSNAU GAM/SAM tables republished on HDX (Gu 2017 - Deyr 2020/21; Deyr 2019/20 summary)."""
    rows = []
    f = RAW / "hdx" / "fsnau-survey-results-2017-2020.xlsx"
    if f.exists():
        d = pd.read_excel(f, "Sheet1", header=None)
        for c in range(1, 17, 2):
            lab = str(d.iloc[0, c]).replace("Post ", "").replace("Gu'", "Gu").strip()
            m = re.match(r"(Gu|Deyr) (\d{4})", lab)
            if not m:
                continue
            season = season_label(int(m.group(2)), m.group(1).lower())
            for r in range(2, len(d)):
                nm, g, sm = d.iloc[r, 0], tofloat(d.iloc[r, c]), tofloat(d.iloc[r, c + 1])
                if isinstance(nm, str) and g is not None and not re.search("median", nm, re.I):
                    rows.append(dict(season=season, population_group=nm.strip(), gam=g, sam=sm,
                                     file="hdx/" + f.name, page=f"col {c}"))
    f = RAW / "hdx" / "2019-post-deyr-assessment-key-nutrition-results-february-2020.xlsx"
    if f.exists():
        d = pd.read_excel(f, header=None)
        for r in range(2, len(d)):
            nm, g, sm = d.iloc[r, 0], tofloat(d.iloc[r, 1]), tofloat(d.iloc[r, 2])
            if isinstance(nm, str) and g is not None and not re.search("median", nm, re.I):
                rows.append(dict(season="Deyr 2019/20", population_group=nm.strip(), gam=g, sam=sm,
                                 file="hdx/" + f.name, page=""))
    return pd.DataFrame(rows)


def transcribed():
    """Hand-transcribed technical-report tables, with each number checked against the page text."""
    frames = []
    for f in sorted((OUT / "transcribed").glob("*.csv")):
        d = pd.read_csv(f, dtype=str)
        d["transcription_file"] = f"transcribed/{f.name}"
        frames.append(d)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    texts = {}
    shares = []
    for _, r in df.iterrows():
        fn = str(r.get("file", ""))
        if fn not in texts:
            tf = OUT / "text" / (fn + ".txt")
            texts[fn] = tf.read_text().split("=====PAGE ") if tf.exists() else []
        page_txt = ""
        try:
            pg = int(float(r["page"]))
            # tables often continue onto the next page (death rates, MUAC)
            page_txt = "\n".join(p for p in texts[fn] if p.startswith(f"{pg}\n") or p.startswith(f"{pg + 1}\n"))
        except (ValueError, TypeError):
            pass
        flat = re.sub(r"\s+", " ", page_txt)
        hit = tot = 0
        for c in VALUE_COLS:
            v = r.get(c)
            if pd.isna(v) or str(v).strip() == "":
                continue
            tot += 1
            x = tofloat(v)
            if x is None:
                continue
            forms = {str(v).strip(), f"{x:.1f}", f"{x:.2f}", f"{x:g}", f"{x:.0f}" if x == int(x) else "x"}
            if any(re.search(rf"(?<![\d.]){re.escape(fm)}(?![\d])", flat) for fm in forms):
                hit += 1
        shares.append(hit / tot if tot else None)
    df["verified_share"] = shares
    if "notes" not in df:
        df["notes"] = ""
    for c in VALUE_COLS + ["n_children", "n_clusters"]:
        if c in df:
            raw = df[c].fillna("").astype(str).str.strip()
            bad = (raw != "") & raw.map(tofloat).isna()
            df.loc[bad, "notes"] = df.loc[bad, "notes"].fillna("") + "; " + c + " printed as '" + raw[bad] + "'"
            df[c] = df[c].map(tofloat)
    return df


def checchi_months():
    f = RAW / "checchi" / "mort" / "som_survey_metadata.xlsx"
    if not f.exists():
        return pd.DataFrame()
    m = pd.read_excel(f, "survey_metadata")
    m = m[m.season.isin(["Gu", "Deyr"])].copy()
    # Checchi's 'Deyr' year is the calendar year of fieldwork start
    m["season"] = [season_label(int(y), s.lower()) for y, s in zip(m.year_survey, m.season)]
    m["population_group"] = m.lhz_name.fillna("").astype(str) + " " + m.district.fillna("").astype(str) + " " + \
        m.livelihood_survey_pop.fillna("").astype(str).str.replace("displaced", "IDP").str.replace("agropastoralists", "agropastoral")
    import calendar
    m["fieldwork_checchi"] = [f"{calendar.month_abbr[int(a)]}-{calendar.month_abbr[int(b)]} {int(y)}" if a != b
                              else f"{calendar.month_abbr[int(a)]} {int(y)}"
                              for a, b, y in zip(m.month_start, m.month_end, m.year_survey)]
    m["gam"] = m.report_gam
    return m[["season", "population_group", "survey_id", "fieldwork_checchi", "gam", "notes"]]


def build():
    P = portal()
    P = P[(P.year >= 2010) & ~((P.year == 2010) & (P.s == "gu"))]
    T = transcribed()
    out = []

    # (1) seasons Deyr 2010/11 - Deyr 2016/17: transcribed technical-report tables
    if len(T):
        # the same survey printed in two regional tables/decks: identical numbers within a season
        key = ["season", "gam", "sam", "cdr", "u5dr", "muac_gam"]
        dup = T.duplicated(subset=key, keep="first") & T[["gam", "cdr", "muac_gam"]].notna().any(axis=1)
        T = T[~dup | T[key[1:]].isna().all(axis=1)]
        t = T.copy()
        t["hand_transcribed"] = True
        t["source_file"] = "raw/" + t["file"]
        t["ci_source"] = t["source_file"] + " p" + t["page"].astype(str)
        t["fieldwork_source"] = t["fieldwork"].notna().map({True: "report", False: ""})
        # portal cross-check
        Pt = P[P.season.isin(t.season.unique())]
        for i, j, sc in match(t, Pt):
            t.loc[i, "portal_gam"] = Pt.loc[j, "gam"]
            t.loc[i, "portal_sam"] = Pt.loc[j, "sam"]
            t.loc[i, "portal_name"] = Pt.loc[j, "population_group"]
        out.append(t)
    done = set(T.season) if len(T) else set()

    # (2) other seasons: portal rows with a GAM or CDR value (the old portal splits surveys across rows)
    p = P[~P.season.isin(done)].copy()
    p = p[p[["gam", "cdr", "u5dr", "muac_gam"]].notna().any(axis=1)]  # rows with SAM only are split fragments
    p["hand_transcribed"] = False
    p["method"] = ["MUAC rapid" if pd.isna(g) and pd.notna(m) else "SMART" for g, m in zip(p.gam, p.muac_gam)]
    p["page"] = ""
    p["fieldwork"] = None
    p["fieldwork_source"] = ""
    # GAM confidence intervals from the IPC annexes
    C = ipc_cis()
    C = C.sort_values("ci_role")  # 'current' before 'previous-year comparison'
    for i, j, sc in match(p, C):
        if abs(p.loc[i, "gam"] - C.loc[j, "gam"]) < 0.05:
            p.loc[i, ["gam_lo", "gam_hi"]] = C.loc[j, ["gam_lo", "gam_hi"]].values
            p.loc[i, "ci_source"] = C.loc[j, "ci_source"] + f" ({C.loc[j, 'ci_role']})"
    # summary-PDF cross-check
    S = summary_pdfs()
    H = hdx_tables()
    S = pd.concat([S, H[~H.season.isin(S.season)]], ignore_index=True)  # HDX only where no summary PDF parsed
    for i, j, sc in match(p, S):
        p.loc[i, "pdf_gam"] = S.loc[j, "gam"]
        p.loc[i, "pdf_sam"] = S.loc[j, "sam"]
        p.loc[i, "pdf_source"] = f"raw/{S.loc[j, 'file']} p{S.loc[j, 'page']}"
    # Where GAM agrees (so the row is aligned) but SAM differs, the published table wins: the portal's
    # Gu 2018 SAM column for rural zones holds values from split fragment rows.
    bad = (p.pdf_gam - p.gam).abs().lt(0.05) & (p.pdf_sam - p.sam).abs().ge(0.05)
    p.loc[bad, "notes"] = "portal SAM " + p.loc[bad, "sam"].astype(str) + " replaced by published table value"
    p.loc[bad, "sam"] = p.loc[bad, "pdf_sam"]
    off = (p.pdf_gam - p.gam).abs().ge(0.05)
    p.loc[off, "notes"] = "GAM differs from the matched summary-table row (likely a different table, e.g. MUAC); portal kept"
    out.append(p)

    df = pd.concat(out, ignore_index=True)
    df["season_year"], df["season_type"] = zip(*df.season.map(season_key))
    df["season_type"] = df.season_type.str.capitalize()
    df["population_type"] = [pt if isinstance(pt, str) and pt else pop_type(n)
                             for pt, n in zip(df.get("population_type", pd.Series(index=df.index)), df.population_group)]
    df["region"] = [r if isinstance(r, str) and r else region_from_name(n)
                    for r, n in zip(df.get("region", pd.Series(index=df.index)), df.population_group)]
    df["method"] = df["method"].fillna("SMART")

    # fieldwork months from Checchi et al. metadata where the documents do not give them
    M = checchi_months()
    if len(M):
        for i, j, sc in match(df, M, thresh=0.6):
            if pd.isna(df.loc[i, "fieldwork"]) or df.loc[i, "fieldwork"] == "":
                df.loc[i, "fieldwork"] = M.loc[j, "fieldwork_checchi"]
                df.loc[i, "fieldwork_source"] = "Checchi et al. metadata (" + M.loc[j, "survey_id"] + ")"

    cols = ["season", "season_year", "season_type", "fieldwork", "fieldwork_source", "population_group",
            "region", "population_type", "method", "n_children", "n_clusters"] + VALUE_COLS + \
           ["source_file", "page", "ci_source", "hand_transcribed", "verified_share", "transcription_file",
            "portal_name", "portal_gam", "portal_sam", "pdf_gam", "pdf_sam", "pdf_source", "source_url", "notes"]
    for c in cols:
        if c not in df:
            df[c] = None
    df = df[cols]
    df["order"] = df.season.map(season_order)
    df = df.sort_values(["order", "population_type", "population_group"]).drop(columns="order")
    df.to_csv(OUT / "surveys.csv", index=False)
    return df


def coverage(df):
    seasons = [season_label(y, s) for y in range(2010, 2026) for s in ("gu", "deyr")][1:]
    g = df[df.method != "MUAC rapid"]
    tab = pd.DataFrame(index=seasons)
    tab["surveys"] = df.groupby("season").size()
    tab["with_gam"] = g[g.gam.notna()].groupby("season").size()
    tab["with_gam_ci"] = df[df.gam_lo.notna()].groupby("season").size()
    tab["with_cdr"] = df[df.cdr.notna()].groupby("season").size()
    tab["muac_rapid"] = df[df.method == "MUAC rapid"].groupby("season").size()
    for t in ["rural", "urban", "IDP", "mixed"]:
        tab[t] = df[df.population_type == t].groupby("season").size()
    tab["with_fieldwork"] = df[df.fieldwork.notna() & (df.fieldwork != "")].groupby("season").size()
    tab = tab.fillna(0).astype(int)
    tab.index.name = "season"
    tab.to_csv(OUT / "coverage_by_season.csv")
    return tab


SOUTH_CENTRAL = {  # rural livelihood groups in areas FSNAU reports as insecure at times (regex on normalised name)
    "Juba riverine": r"\bjuba\b.*riverine|riverine.*\bjuba\b",
    "Juba agropastoral": r"\bjuba\b.*agropastoral|agropastoral.*\bjuba\b",
    "Juba pastoral": r"\bjuba\b.*pastoral(?!.*agro)|juba cattle",
    "South Gedo (any rural)": r"south gedo",
    "North Gedo (any rural)": r"north gedo",
    "Bakool pastoral": r"bakool.*pastoral(?<!agropastoral)|elberde|southern inland",
    "Bakool agropastoral": r"bakool agropastoral",
    "Bay agropastoral": r"\bbay\b.*agropastoral|bayagrop",
    "Shabelle riverine": r"shabelle.*riverine",
    "Shabelle agropastoral": r"shabelle.*agropastoral",
    "Hiran rural (incl. Beletweyne district)": r"hiran (agropastoral|riverine|pastoral)|beletweyne (district|rural)|mataban",
    "Cowpea belt (central agropastoral)": r"cowpea",
    "Coastal Deeh central": r"coastal deeh.*(central|galgadud)",
}


def south_central(df):
    seasons = [season_label(y, s) for y in range(2010, 2026) for s in ("gu", "deyr")][1:]
    tab = pd.DataFrame(index=list(SOUTH_CENTRAL), columns=seasons).fillna("")
    for _, r in df.iterrows():
        if r.population_type not in ("rural", "mixed"):
            continue
        n = " ".join(norm(r.population_group))
        for k, rx in SOUTH_CENTRAL.items():
            if re.search(rx, n):
                kind = "SMART" if pd.notna(r.gam) else ("MUAC" if pd.notna(r.muac_gam) or r.method == "MUAC rapid" else "other")
                cur = tab.loc[k, r.season]
                if cur != "SMART":
                    tab.loc[k, r.season] = kind if cur in ("", "other") else cur
    tab.index.name = "group"
    tab.T.to_csv(OUT / "coverage_south_central.csv")
    gaps = []
    for f in sorted((OUT / "transcribed").glob("*_gaps.txt")):
        for line in f.read_text().splitlines():
            if line.strip() and not line.startswith(("Gaps /", "No statements")):
                gaps.append(dict(file=f.name.replace("_gaps.txt", ".pdf"), statement=line.strip()))
    pd.DataFrame(gaps).to_csv(OUT / "gaps_statements.csv", index=False)
    return tab


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch()
    else:
        d = build()
        print(coverage(d).to_string())
        print(south_central(d).to_string())
