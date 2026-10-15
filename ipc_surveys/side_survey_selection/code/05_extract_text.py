"""Pull the sampling-relevant passages out of each report PDF.

For each report keeps (a) every sentence that mentions exclusions, insecurity,
camps, displacement, nomads, or unvisited/replaced clusters, and (b) the first
pages of the sample-design section, so cluster counts in tables come along.
Output: data/report_text/<survey id>.txt, small enough to code by hand.
"""
import os, re
from pathlib import Path
import fitz  # pymupdf
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = Path(os.environ.get("REPORT_PDF_DIR", Path.home() / "Library/Caches/survey_reports"))
OUT = ROOT / "data" / "report_text"
OUT.mkdir(parents=True, exist_ok=True)

# Narrow terms are searched everywhere; broad terms only on methodology pages.
NARROW = re.compile(r"""
    \binsecur(?!ity\ (?:alimentaire|food))(?!e\ alimentaire) | ins[ée]curit[ée](?!\ alimentaire)
  | inseguridad(?!\ alimentaria) | \bsecurity\ (?:reason|situation|concern|problem|issue|condition|threat)
  | raisons?\ de\ s[ée]curit[ée] | \bcamps?\b | campement | refugee | r[ée]fugi[ée] | refugiad
  | displaced | d[ée]plac[ée]s | desplazad | deslocad | \bIDPs?\b | inaccessib | not\ (?:be\ )?visited
  | non\ visit | could\ not\ be\ (?:reached|visited|covered|surveyed|enumerated|accessed)
  | n'ont\ (?:pas\ )?pu\ (?:être\ )?(?:enquêt|visit|couvr) | nomad | boko | shabaab | militan | terroris
""", re.I | re.X)
BROAD = re.compile(r"""
    exclu(?!siv|sif) | excluí | not\ covered | non\ couvert | replac | remplac | conflict | conflit
  | \bwar\b | guerre | armed | arm[ée]e?s | violence | access | security | s[ée]curit[ée] | completed | achev
  | dropped | omitted | omis | institutional | collective | collectif
""", re.I | re.X)
SECTION = re.compile(r"sample design|sampling design|plan de sondage|conception de l'?[ée]chantillon|"
                     r"dise[ñn]o (?:de la )?muestra|desenho da amostra|plano de amostragem|amostragem|sampling frame|"
                     r"base de sondage|sample and survey methodology|[ée]chantillonnage|выборк|تصميم العينة|العينة", re.I)
NOISE = re.compile(r"domestic violence|violence conjugale|violence domestique|spousal|sexual violence|"
                   r"campaign|campagne|accesss? to (?:health|care|water|media|information|contracept)|"
                   r"acc[eè]s aux? (?:soins|services|m[ée]dias|eau)", re.I)

TOC = re.compile(r"\.{6,}")

sample = pd.read_csv(ROOT / "data" / "report_sample.csv")
for _, r in sample[sample.have_pdf].iterrows():
    out = OUT / f"{r.id}.txt"
    if out.exists():
        continue
    try:
        doc = fitz.open(PDF_DIR / f"{r.id}.pdf")
    except Exception as e:
        print(r.id, "unreadable", e); continue
    pages = [re.sub(r"\s+", " ", pg.get_text()) for pg in doc]
    hits = [i for i, t in enumerate(pages) if SECTION.search(t) and not TOC.search(t)]
    method = set()
    for i in hits:
        method.update(range(i, min(i + 6, len(pages))))
    sents = []
    for i, txt in enumerate(pages):
        rx_ok = (lambda x: NARROW.search(x) or BROAD.search(x)) if i in method else NARROW.search
        for snt in re.split(r"(?<=[.;:])\s+(?=[A-Z0-9ÉÀ(▪•])", txt):
            if rx_ok(snt) and not NOISE.search(snt) and not TOC.search(snt) and 30 < len(snt) < 700:
                sents.append(f"[p{i+1}] {snt}")
    section_pages = [(i + 1, pages[i][:3000]) for i in hits[:3]]
    seen, keep = set(), []
    for snt in sents:
        k = snt[snt.index("]") + 2:][:120]
        if k not in seen:
            seen.add(k); keep.append(snt)
    head = f"{r.id} | {r['name']} | {r.program} | fieldwork start {r.year} | set={r['set']} | pages={len(doc)}\n"
    body = "== SENTENCES ==\n" + "\n".join(keep[:90]) + "\n\n== SAMPLE DESIGN PAGES ==\n" + \
           "\n".join(f"[p{pg}] {t}" for pg, t in section_pages)
    out.write_text(head + body[:24000])
    print(r.id, len(keep), "sentences", len(section_pages), "design pages", flush=True)
