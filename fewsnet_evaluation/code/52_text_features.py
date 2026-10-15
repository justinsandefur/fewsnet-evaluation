"""Turn extracted report JSON (input/reports/extracted/*.json) into tables, and
match each area mention to FEWS NET mapping units (fnids).

Outputs (input/reports/):
  reports.parquet   one row per report: national fields, counts
  mentions.parquet  one row per area mention, with matched fnids (exploded)
  surveys.parquet   one row per survey result, with matched fnids where possible
  gaps.parquet      one row per stated data gap
"""
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "input" / "reports"
MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october november december".split(), 1)}
CODES = {"somalia": "SO", "ethiopia": "ET", "sudan": "SD", "south-sudan": "SS", "kenya": "KE",
         "nigeria": "NG", "niger": "NE", "mali": "ML", "burkina-faso": "BF", "chad": "TD",
         "yemen": "YE", "afghanistan": "AF", "haiti": "HT", "uganda": "UG", "mozambique": "MZ",
         "zimbabwe": "ZW", "malawi": "MW", "madagascar": "MG", "democratic-republic-congo": "CD",
         "guatemala": "GT", "honduras": "HN", "el-salvador": "SV", "nicaragua": "NI",
         "mauritania": "MR", "central-african-republic": "CF", "cameroon": "CM", "burundi": "BI",
         "rwanda": "RW", "tanzania": "TZ", "lesotho": "LS", "zambia": "ZM", "djibouti": "DJ"}
STOP = {"region", "regions", "zone", "zones", "state", "states", "district", "districts", "woreda",
        "woredas", "locality", "localities", "livelihood", "areas", "area", "the", "of", "and",
        "in", "parts", "northern", "southern", "eastern", "western", "central", "north", "south",
        "east", "west", "lowlands", "highlands", "lz", "pastoral", "agropastoral", "agro-pastoral",
        "riverine", "town", "towns", "idps", "idp", "camps", "camp", "periphery", "its", "and",
        "most", "some", "pockets", "admin", "rural", "urban"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s.replace("-", " "))
    return re.sub(r"\s+", " ", s).strip()


def core(s):
    return " ".join(w for w in norm(s).split() if w not in STOP)


def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()


def units():
    df = pd.read_parquet(ROOT / "input/fewsnet/ipcphase.parquet",
                         columns=["country_code", "fnid", "geographic_unit_full_name"])
    df = df.drop_duplicates("fnid").dropna()
    parts = df.geographic_unit_full_name.str.rsplit(",", n=3, expand=True)
    df["unit"], df["adm2"], df["adm1"] = parts[0], parts[1], parts[2]
    for c in ["unit", "adm2", "adm1"]:
        df[c + "_n"] = df[c].map(core)
    return df


def best(name, options, cut=0.84):
    """Options whose core name matches `name` (exact, contained word-wise, or fuzzy)."""
    n = core(name)
    if not n:
        return set()
    out = set()
    for o in options:
        if not o:
            continue
        if n == o or (len(n) > 3 and re.search(rf"\b{re.escape(n)}\b", o)) or \
           (len(o) > 3 and re.search(rf"\b{re.escape(o)}\b", n)) or sim(n, o) >= cut:
            out.add(o)
    return out


def match(m, U):
    """Return (fnids, level) for one mention against country units U."""
    a1 = [x for x in re.split(r"[;/]| and ", m.get("admin1") or "") if x.strip()]
    a2 = [x for x in re.split(r"[;/]| and ", m.get("admin2") or "") if x.strip()]
    lz = m.get("livelihood_zone")
    pool = U
    if a1:
        hits = set().union(*[best(x, U.adm1_n.unique()) for x in a1])
        if hits:
            pool = U[U.adm1_n.isin(hits)]
    # a named unit in the location text ('Bare Woreda', 'Dessie Zuria Woreda, South Wollo')
    head = (m.get("location") or "").split(",")[0].split("(")[0]
    head = re.sub(r"\b(woreda|locality|district|town|IDPs?|camps?)\b", "", head, flags=re.I)
    if core(head) and len(core(head)) > 3:
        n = core(head)
        ok = pool.unit_n.map(lambda o: o == n or sim(n, o) >= 0.88)
        if ok.any():
            return set(pool[ok].fnid), "unit"
    within = len(pool) < len(U)
    cut2 = 0.72 if within else 0.84
    hits2 = set()
    for x in a2:
        hits2 |= best(x, pool.adm2_n.unique(), cut2) | best(x, pool.unit_n.unique(), cut2)
    if hits2:
        sel = pool[pool.adm2_n.isin(hits2) | pool.unit_n.isin(hits2)]
        return set(sel.fnid), "admin2"
    if lz:
        # livelihood-zone names keep words like 'agropastoral', so compare full normalized names
        n = norm(lz).replace(" livelihood zone", "")
        names = pool.unit.map(norm)
        k = len(n.split())
        ok = names.map(lambda o: n in o or sim(n, " ".join(o.split()[:k])) >= 0.8)
        if ok.any():
            return set(pool[ok].fnid), "zone"
    if a1 and len(pool) < len(U):
        return set(pool.fnid), "admin1"
    # fall back to the free-text location: admin1, then admin2/unit names
    loc = m.get("location") or ""
    for col, lev in [("adm1_n", "admin1"), ("adm2_n", "admin2"), ("unit_n", "zone")]:
        hits = best(loc, U[col].unique(), cut=0.9)
        if hits and len(hits) <= 3:
            return set(U[U[col].isin(hits)].fnid), lev
    return set(), "none"


def main():
    U_all = units()
    reports, mentions, surveys, gaps = [], [], [], []
    for f in sorted((REP / "extracted").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except json.JSONDecodeError:
            print("bad json", f.name)
            continue
        country, rtype, slug = f.stem.split("__")
        mo = re.match(r"([a-z]+)-(\d{4})", slug)
        month = pd.Period(f"{mo.group(2)}-{MONTHS[mo.group(1)]:02d}", "M")
        cc = CODES.get(country)
        U = U_all[U_all.country_code == cc]
        nat = d.get("national") or {}
        reports.append(dict(name=f.stem, country=country, cc=cc, type=rtype, month=month,
                            remote=d.get("remote_monitoring"), n_areas=len(d.get("areas") or []),
                            n_surveys=len(d.get("surveys") or []), n_gaps=len(d.get("data_gaps") or []),
                            sources=";".join(d.get("data_sources_cited") or []),
                            **{f"nat_{k}": v for k, v in nat.items()}))
        for i, m in enumerate(d.get("areas") or []):
            ids, lev = match(m, U)
            row = dict(name=f.stem, cc=cc, type=rtype, month=month, i=i, level=lev, n_fnids=len(ids),
                       **{k: (";".join(v) if isinstance(v, list) else v) for k, v in m.items()})
            mentions += [dict(row, fnid=x) for x in ids] or [dict(row, fnid=None)]
        for i, s in enumerate(d.get("surveys") or []):
            ids, lev = match(s, U)
            row = dict(name=f.stem, cc=cc, type=rtype, month=month, i=i, level=lev, n_fnids=len(ids), **s)
            surveys += [dict(row, fnid=x) for x in ids] or [dict(row, fnid=None)]
        for i, g in enumerate(d.get("data_gaps") or []):
            ids, lev = match(g, U)
            gaps.append(dict(name=f.stem, cc=cc, type=rtype, month=month, i=i, level=lev,
                             n_fnids=len(ids), fnids=";".join(sorted(ids)), **g))
    for nm, rows in [("reports", reports), ("mentions", mentions), ("surveys", surveys), ("gaps", gaps)]:
        df = pd.DataFrame(rows)
        if "month" in df:
            df["month"] = df.month.astype(str)
        df.to_parquet(REP / f"{nm}.parquet", index=False)
        print(nm, len(df))
    m = pd.DataFrame(mentions).drop_duplicates(["name", "i"])
    print("mention match levels:\n", m.groupby("cc")["level"].value_counts(normalize=True).round(2))


if __name__ == "__main__":
    main()
