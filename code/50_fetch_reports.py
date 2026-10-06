"""Download FEWS NET narrative reports (outlooks, updates, key message updates,
remote monitoring reports, alerts) from fews.net and save their main text.

Report URLs come from the site's sitemap (input/reports/sitemap_urls.txt).
Usage: python 50_fetch_reports.py [url_list]   (default: input/reports/pilot_urls.txt)
Output: input/reports/html/<country>__<type>__<month-year>.html and
        input/reports/text/<same>.txt, plus input/reports/index.csv
"""
import html
import re
import sys
import time
from pathlib import Path

import pandas as pd
import fitz  # pymupdf
import requests

ROOT = Path(__file__).resolve().parents[1] / "input" / "reports"
HTML, TEXT, PDF = ROOT / "html", ROOT / "text", ROOT / "pdf"
STUB = "archived report which currently has no summary text"
MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}


def parse(url):
    parts = url.rstrip("/").split("/")
    country, rtype, slug = parts[-3], parts[-2], parts[-1]
    m = re.match(r"([a-z]+)-(\d{4})", slug)
    return country, rtype, slug, int(m.group(2)), MONTHS.get(m.group(1))


def main_text(raw):
    """Strip page chrome: keep the article body, drop scripts, nav and footer."""
    t = re.sub(r"<(script|style|nav|footer|header)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    m = re.search(r"<main\b.*?</main>", t, flags=re.S | re.I)
    if m:
        t = m.group(0)
    t = re.sub(r"<(br|/p|/li|/h\d|/tr|/div)\b[^>]*>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t)
    # The footer lists the site's latest reports; cut it so no later text leaks in.
    t = t.split("Related Analysis Listing")[0]
    return t.strip()


def main():
    urls = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "pilot_urls.txt").read_text().split()
    HTML.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)
    rows = []
    s = requests.Session()
    s.headers["User-Agent"] = "research (FEWS NET evaluation; contact via CGD)"
    for url in urls:
        country, rtype, slug, year, month = parse(url)
        name = f"{country}__{rtype}__{slug}"
        h = HTML / f"{name}.html"
        if not h.exists():
            r = s.get(url, timeout=60)
            if r.status_code != 200:
                print("fail", r.status_code, url)
                continue
            h.write_text(r.text)
            time.sleep(1.0)
        txt = main_text(h.read_text())
        if STUB in txt:
            # archived reports keep their content only in the PDF behind /print
            pdf = PDF / f"{name}.pdf"
            if not pdf.exists():
                r = s.get(url + "/print", timeout=120)
                if r.status_code == 200 and r.content[:4] == b"%PDF":
                    PDF.mkdir(exist_ok=True)
                    pdf.write_bytes(r.content)
                time.sleep(1.0)
            if pdf.exists():
                with fitz.open(pdf) as doc:
                    txt = "\n".join(pg.get_text() for pg in doc).strip()
        (TEXT / f"{name}.txt").write_text(txt)
        rows.append(dict(name=name, url=url, country=country, type=rtype, year=year,
                         month=month, chars=len(txt)))
    idx = pd.DataFrame(rows)
    old = ROOT / "index.csv"
    if old.exists():
        idx = pd.concat([pd.read_csv(old), idx]).drop_duplicates("name", keep="last")
    idx.sort_values(["country", "year", "month", "type"]).to_csv(old, index=False)
    print(idx.groupby(["country", "type"]).chars.describe()[["count", "mean", "max"]])


if __name__ == "__main__":
    main()
