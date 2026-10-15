"""WFP-only sub-national series for Somalia, Sudan, Ethiopia and Nigeria.

Memo: references/wfp_subnational.md.

WFP's own publications (Annual Country Reports 2018-2025, Standard Project Reports 2015-2019,
country briefs, situation reports, emergency dashboards) carry no machine-readable sub-national
tables: beneficiaries, tonnage and cash are national, and regions appear only in narrative
sentences or map graphics. The one machine-readable WFP-specific sub-national source is WFP's own
reporting to the OCHA 3W/4W/5W operational-presence files already cached by
60_fetch_subnational_aid.py: rows whose reporting organisation is WFP.

Steps
  fetch   download the ACR/SPR PDFs listed in input/subnational_aid/wfp_acr/index.csv (record of
          what was checked; not used by `build`) and write page text to wfp_acr/text/
  build   (default) WFP rows of the 3W files:
            Somalia, Sudan: 62_tidy_3w.py's parsers, manifest, P-code matching and window
              de-duplication, run with every non-WFP row dropped. Presence by district/locality
              x period x cluster; individuals reached and US$ where the 3W carries them
              (Somalia 2016 Q1, 2019 Q1-2020 Q3, Mar 2021, 2023 US$, Jan-Sep 2024).
            Ethiopia, Nigeria: same header detection on every cached 3W/4W file; presence by
              admin-2 (Ethiopia zone, Nigeria LGA) x period x cluster, matched to COD-AB.
          No hand-transcribed rows.

Output: input/subnational_aid/tidy/wfp_<iso3>.parquet, long:
  iso3, admin1, admin1_pcode, admin2, admin2_pcode, period_start, period_end, period_type, cluster,
  measure (activity_rows | reached | usd), value, cumulative, latest_window, source_file, page,
  hand_transcribed
plus wfp_coverage.csv (country x year x measure: periods, admin-2 units, files).

Caveats: 'activity_rows' counts WFP activity rows in a district (presence, not volume). Reach in
the 3W is summed over activity rows and can double count people across activities; cumulative=True
means figures run over an activity's duration rather than the month (62's rule). WFP rows include
activities WFP reports for its cooperating partners.
"""
import hashlib
import importlib.util
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AID = ROOT / "input" / "subnational_aid"
OUT = AID / "tidy"
ACR = AID / "wfp_acr"
WFP = re.compile(r"\bwfp\b|world food prog", re.I)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

spec = importlib.util.spec_from_file_location("t62", ROOT / "code" / "62_tidy_3w.py")
t62 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t62)

COLS = ["iso3", "admin1", "admin1_pcode", "admin2", "admin2_pcode", "period_start", "period_end",
        "period_type", "cluster", "measure", "value", "cumulative", "latest_window", "source_file",
        "page", "hand_transcribed"]


# ------------------------------------------------------------------------------------- fetch
def fetch():
    import fitz
    import requests
    idx = pd.read_csv(ACR / "index.csv")
    (ACR / "text").mkdir(parents=True, exist_ok=True)
    for r in idx.itertuples():
        p = ACR / r.file
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.stat().st_size < 2000:
            b = requests.get(r.url, headers=UA, timeout=120).content
            if not b.startswith(b"%PDF"):
                print("not a PDF:", r.url)
                continue
            p.write_bytes(b)
            time.sleep(2)
        txt = ACR / "text" / f"{p.parent.name}_{p.stem}.txt"
        if not txt.exists():
            d = fitz.open(p)
            txt.write_text("".join(f"\n=====PAGE {i + 1}=====\n" + pg.get_text() for i, pg in enumerate(d)))
        print(r.iso3, r.year, r.doc_type, p.name)


# ------------------------------------------------------------------- Somalia and Sudan (via 62)
def wfp_only(fn):
    def f(path, m, log):
        d = fn(path, m, log)
        if d is None or len(d) == 0 or "org" not in d:
            return d.iloc[0:0] if d is not None else None
        return d[d.org.astype(str).str.contains(WFP)].reset_index(drop=True)
    return f


def empty(*a, **k):
    return pd.DataFrame()


def som_sdn(iso):
    tmp = OUT / "_wfp_tmp"
    t62.OUT = tmp                       # keep 62's own outputs untouched
    t62.parse_3w = wfp_only(t62.parse_3w)
    for name in ["parse_cwg", "parse_matrix", "parse_srf2014", "parse_drought2023", "parse_hnrp2026",
                 "parse_hrp_wide", "parse_hrp2019", "parse_hrp_state2018"]:
        setattr(t62, name, empty)       # aggregates without an organisation column
    pres, reach = t62.run(iso)
    (tmp / f"log_{iso}.txt").replace(OUT / f"wfp_log_{iso}.txt")
    p = pres.assign(measure="activity_rows", value=pres.n_activities.astype(float), cumulative=False)
    r = reach.copy()
    keep = [c for c in COLS if c in p.columns]
    out = pd.concat([p[keep], r[[c for c in COLS if c in r.columns]]], ignore_index=True)
    return out


# ------------------------------------------------------------- Ethiopia and Nigeria (3W files)
SKIP = re.compile(r"child_protection|health|wash|rrm-data", re.I)
MON = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
                                   "oct", "nov", "dec"], 1)}


def file_window(name):
    """Period covered by a 3W file, from its name: (start, end) or None."""
    s = name.lower().replace("sept", "sep")
    years = [int(y) for y in re.findall(r"(20\d\d)", s)]
    ms = [MON[m] for m in re.findall(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*", s)]
    if not years:
        return None
    if len(years) >= 2 and ms:                        # 'nov2019_2020' -> Nov 2019..Dec 2020
        return t62.ym(years[0], ms[0]), t62.ym(years[-1], 12)
    if not ms:
        return t62.ym(years[0], 1), t62.ym(years[0], 12)
    return t62.ym(years[0], ms[0]), t62.ym(years[0], ms[-1])


def augment(roles, header, iso):
    """Fill admin, sector and reach roles that 62's detector misses in these files."""
    H = [str(h).strip().lower() if h is not None else "" for h in header]

    def find(rx):
        return next((j for j, h in enumerate(H) if re.search(rx, h)), None)
    for role, rx in [("cluster", r"^(project )?sector$|^cluster$"), ("adm1", r"^states?$|^region( name)?$"),
                     ("adm1_code", r"^(state|region) ?p-?code$"), ("adm2", r"^lga( name)?$|^zone( name)?$"),
                     ("adm2_code", r"^(lga|zone) ?p-?code$"), ("reached", r"^people reached$")]:
        if role not in roles:
            j = find(rx)
            if j is not None:
                roles[role] = j
    if iso == "eth":                    # COD-AB admin-2 is the zone; keep woredas out of it
        j, jc = find(r"^zone( name)?$"), find(r"^zone ?p-?code$")
        if j is not None:
            roles["adm2"] = j
            if jc is not None:
                roles["adm2_code"] = jc
            else:
                roles.pop("adm2_code", None)
    return roles


def eth_nga(iso):
    ISO3 = iso.upper()
    gz = t62.Gazetteer(ISO3)
    names_seen = __import__("collections").defaultdict(lambda: {"sources": set(), "res": None})
    log, frames, seen = [], [], {}
    for p in sorted((AID / "hdx_3w" / iso).rglob("*")):
        if not p.is_file() or not re.search(r"\.(xlsx|xls|csv)$", p.name, re.I):
            continue
        rel = str(p.relative_to(AID))
        if SKIP.search(p.name):
            log.append(f"SKIP {rel}: single-sector file without WFP activities")
            continue
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen:
            log.append(f"SKIP {rel}: byte-identical to {seen[h]}")
            continue
        seen[h] = rel
        win = file_window(p.name)
        try:
            book = t62.read_book(p)
            pk = t62.pick_sheet(book, need=("org",))
        except Exception as e:  # noqa
            log.append(f"SKIP {rel}: could not read ({e})")
            continue
        if pk is None or win is None:
            log.append(f"SKIP {rel}: no organisation column or no period in file name")
            continue
        name, start, roles, rows, hi = pk
        roles = augment(roles, rows[hi], iso)
        log.append(f"     roles: " + ", ".join(f"{k}='{str(rows[hi][j])[:20]}'" for k, j in sorted(roles.items())
                                                if k in ("adm1", "adm1_code", "adm2", "adm2_code", "cluster", "month")))
        out = []
        for rec in t62.rows_to_records(rows, start, roles):
            if not rec.get("org") or not WFP.search(str(rec["org"])):
                continue
            per = None
            if rec.get("month") is not None:
                yr = int(t62.num(rec["year"])) if t62.num(rec.get("year")) == t62.num(rec.get("year")) \
                    else win[0].year
                per = t62.parse_month(rec["month"], yr)
                if per is not None and not (win[0] <= per[0] <= win[1]):
                    per = t62.parse_month(rec["month"], win[1].year)
                    if per is not None and not (win[0] <= per[0] <= win[1]):
                        per = None
            per = per or win
            out.append(dict(cluster_raw=rec.get("cluster"), org=t62.clean_org(rec.get("org")),
                            adm1_raw=rec.get("adm1"), adm1_code_raw=rec.get("adm1_code"),
                            adm2_raw=rec.get("adm2"), adm2_code_raw=rec.get("adm2_code"),
                            period_start=per[0], period_end=per[1],
                            period_type="month" if per[0] == per[1] else "range"))
        if not out:
            log.append(f"SKIP {rel}: no WFP rows (sheet '{name}')")
            continue
        d = t62.resolve_units(pd.DataFrame(out), gz, names_seen, rel)
        d["cluster"] = d.cluster_raw.map(t62.map_cluster)
        d["source_file"] = rel
        d["file_rows"] = len(rows) - start
        frames.append(d)
        log.append(f"USE  {rel}: sheet '{name}', {len(d):,} WFP rows, "
                   f"{d.admin2_pcode.notna().mean():.0%} matched to COD-AB admin-2, "
                   f"{win[0]:%Y-%m}..{win[1]:%Y-%m}")
    D = pd.concat(frames, ignore_index=True)
    # one file per period window: the largest file wins (re-issues of the same 3W)
    w = D.groupby(["period_start", "period_end", "source_file"]).file_rows.first().reset_index()
    w = w.sort_values("file_rows").groupby(["period_start", "period_end"]).tail(1)
    D = D.merge(w[["period_start", "period_end", "source_file"]])
    # quarterly/annual windows already covered month by month by another file (e.g. Nigeria
    # Nov 2019-2020 combined file vs the 2020 quarterly 3Ws): keep the monthly rows only
    monthly = set(D.loc[D.period_type == "month", "period_start"])
    rng = D.period_type == "range"
    covered = [all(m in monthly for m in pd.date_range(a, b, freq="MS"))
               for a, b in zip(D.period_start[rng], D.period_end[rng])]
    drop = D.index[rng][np.array(covered, dtype=bool)]
    for f in D.loc[drop, "source_file"].unique():
        log.append(f"DROP range rows of {f}: months already covered by monthly rows of another file")
    D = D.drop(drop)
    D[["admin1_pcode", "admin2_pcode"]] = D[["admin1_pcode", "admin2_pcode"]].fillna("")
    g = (D.groupby(["admin1", "admin1_pcode", "admin2", "admin2_pcode", "period_start", "period_end",
                    "period_type", "cluster", "source_file"], dropna=False)
         .size().rename("value").reset_index())
    g[["admin1_pcode", "admin2_pcode"]] = g[["admin1_pcode", "admin2_pcode"]].replace("", None)
    g["iso3"], g["measure"], g["cumulative"] = ISO3, "activity_rows", False
    mx = g.groupby("period_start").period_end.transform("max")
    g["latest_window"] = (g.period_end == mx) | (g.period_type == "month")
    (OUT / f"wfp_log_{iso}.txt").write_text("\n".join(log) + "\n")
    return g


# ------------------------------------------------------------------------------------- build
def build():
    cov = []
    for iso in ["som", "sdn", "eth", "nga"]:
        d = som_sdn(iso) if iso in ("som", "sdn") else eth_nga(iso)
        d["iso3"] = iso.upper()
        d["page"] = np.nan             # spreadsheet rows; no PDF page
        d["hand_transcribed"] = False
        d["value"] = d.value.astype(float)
        d = d[COLS].sort_values(["measure", "period_start", "admin1", "admin2", "cluster"])
        d.to_parquet(OUT / f"wfp_{iso}.parquet", index=False)
        d["year"] = d.period_start.dt.year
        c = (d.groupby(["iso3", "year", "measure"])
             .agg(periods=("period_start", "nunique"), admin2_units=("admin2", "nunique"),
                  admin2_matched=("admin2_pcode", lambda s: s.notna().mean()),
                  files=("source_file", "nunique"), value=("value", "sum")).reset_index())
        cov.append(c)
        print(iso, len(d), "rows;", d.groupby("measure").period_start.agg(["min", "max"]).to_dict())
    pd.concat(cov).to_csv(OUT / "wfp_coverage.csv", index=False)
    tmp = OUT / "_wfp_tmp"
    if tmp.exists():
        for f in tmp.iterdir():
            f.unlink()
        tmp.rmdir()


if __name__ == "__main__":
    if "fetch" in sys.argv[1:]:
        fetch()
    else:
        build()
