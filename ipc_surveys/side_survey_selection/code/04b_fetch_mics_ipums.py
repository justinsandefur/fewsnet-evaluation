"""Second pass for MICS reports missing from the microdata catalogs: IPUMS-MICS
hosts report PDFs at mics.ipums.org/mics/resources/enum_materials_pdf/report_<iso2><year><a|b>_<lang>.pdf.
Also downloads the hand-found URLs in data/mics_manual_urls.csv. Updates have_pdf."""
import os, subprocess
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = Path(os.environ.get("REPORT_PDF_DIR", Path.home() / "Library/Caches/survey_reports"))
cty = pd.read_csv(ROOT / "data" / "raw" / "countries.csv", keep_default_na=False)
iso2 = dict(zip(cty.iso3, cty.iso2.str.lower()))
s = pd.read_csv(ROOT / "data" / "report_sample.csv")


def ok(f):
    return f.exists() and f.stat().st_size > 300_000 and b"%PDF" in f.read_bytes()[:1024]


def get(url, dest):
    subprocess.run(["curl", "-sfL", "--max-time", "600", "-A", "Mozilla/5.0", "-o", str(dest), url])
    if not ok(dest) and dest.exists():
        dest.unlink()
    return ok(dest)


manual = ROOT / "data" / "mics_manual_urls.csv"
if manual.exists():
    for _, r in pd.read_csv(manual).iterrows():
        dest = PDF_DIR / f"{r.id}.pdf"
        if isinstance(r.url, str) and r.url.endswith(".pdf") and not ok(dest):
            get(r.url, dest)

for i, r in s[s.program == "MICS"].iterrows():
    dest = PDF_DIR / f"{r.id}.pdf"
    if not ok(dest):
        iso, yr = r.id.split("_")
        for suf in "ab":
            for lang in ["eng", "fre", "spa", "por", "rus", "ara"]:
                if get(f"https://mics.ipums.org/mics/resources/enum_materials_pdf/report_{iso2.get(iso,'xx')}{yr}{suf}_{lang}.pdf", dest):
                    break
            if ok(dest):
                break
    s.loc[i, "have_pdf"] = ok(dest)
    print(r.id, "ok" if ok(dest) else "MISSING", flush=True)
s.loc[s.program == "DHS", "have_pdf"] = [ok(PDF_DIR / f"{x}.pdf") for x in s.loc[s.program == "DHS", "id"]]
s.to_csv(ROOT / "data" / "report_sample.csv", index=False)
print(s.groupby(["set", "program"]).have_pdf.agg(["sum", "size"]))
