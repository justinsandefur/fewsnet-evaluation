"""Match each FSNAU nutrition survey to the places it covers (name matching only; no analysis).

Reads
  raw/fsnau/surveys.csv          FSNAU survey results, one row per survey, transcribed from FSNAU's
                                 seasonal reports (see raw/SOURCES.md)
  raw/fewsnet/ipcphase_so.csv    FEWS NET classifications for Somalia, used only for the names of Somalia's
                                 livelihood-zone units ("<zone>, <district>, <region>")
Writes
  source/surveys.csv             the survey rows, plus three columns added here:
    domain   survey domain: "rural|<zone key>", "IDP|<district>" or "urban|<district>"; blank if the
             name could not be matched
    fnids    rural surveys: the FEWS NET units of that livelihood zone (";"-separated)
    dist     town surveys: the district P-code of the town
    month    target month of fieldwork (YYYY-MM): the last month named in the fieldwork dates,
             else July (Gu) or November (Deyr) of the survey year

Everything else (which surveys to keep, weights, averaging) is done in Stata (../00_data.do).
The rules are those of code/57_fsnau_value.py (rural) and code/68_somalia_us_cut.py (towns).
"""
import re
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", "This pattern")   # zone patterns use groups; harmless

HERE = Path(__file__).resolve().parent
RAW, OUT = HERE / "raw", HERE / "source"

# ------------------------------------------------------------------ rural surveys -> livelihood units
NW = {"Awdal", "Woqooyi Galbeed", "Togdheer", "Sool", "Sanaag"}
NE = {"Bari", "Nugaal", "Mudug", "Sool", "Sanaag"}
CENTRAL = {"Mudug", "Galgaduud"}
SHABELLE = {"Middle Shabelle", "Lower Shabelle"}
JUBA = {"Middle Juba", "Lower Juba"}
NORTH_GEDO = {"Belet Xaawo", "Doolow", "Luuq"}
REGIONS = ["Awdal", "Bakool", "Banaadir", "Bari", "Bay", "Galgaduud", "Gedo", "Hiiraan", "Lower Juba",
           "Lower Shabelle", "Middle Juba", "Middle Shabelle", "Mudug", "Nugaal", "Sanaag", "Sool",
           "Togdheer", "Woqooyi Galbeed"]
RIVERINE = r"riverine|pump|gravity|irrigat"
AGRO = r"agro"


def units():
    """Somalia's FEWS NET livelihood units (not towns or camps), with zone, district and region names."""
    u = pd.read_csv(RAW / "fewsnet" / "ipcphase_so.csv", encoding="utf-8-sig", low_memory=False,
                    usecols=["country_code", "fnid", "geographic_unit_full_name"])
    u = u[u.country_code == "SO"].drop_duplicates("fnid").dropna()
    p = u.geographic_unit_full_name.str.rsplit(",", n=3, expand=True)
    u["lz"], u["dist"], u["reg"] = p[0].str.strip(), p[1].str.strip(), p[2].str.strip()
    u = u.dropna(subset=["reg"])
    u = u[~u.lz.str.contains("Urban|IDP", case=False)]
    u["lzl"] = u.lz.str.lower()
    return u


def rule(name, region):
    """Survey name -> (livelihood-zone pattern, regions, districts, key); None if not a known zone."""
    n = name.lower().replace("-", " ").replace("shabeele", "shabelle").replace("adduun", "addun")
    n = re.sub(r"\s+", " ", n)
    regs, dists, lz = None, None, None
    # "of northwest" etc. narrows a zone that spans the north to one side
    qual = (NW if re.search(r"\bnw\b|north ?west|of northwest", n) else
            NE if re.search(r"\bne\b|north ?east|of northeast", n) else
            CENTRAL if re.search(r"central", n) else None)
    if "addun" in n: lz = "addun"
    elif "hawd" in n: lz = "hawd"
    elif "guban" in n and "golis" not in n: lz = "guban"
    elif "west golis" in n: lz = "west golis"
    elif "east golis" in n: lz = "east golis"
    elif "golis" in n: lz = "golis"
    elif "coastal deeh" in n: lz = "coastal deeh"
    elif "nugal valley" in n: lz = "nugal valley"
    elif "sool plateau" in n or "sool sanag" in n: lz = "sool.?sanag plateau|sool plateau"
    elif "northern inland" in n: lz = "northern inland"
    elif re.search(r"north ?west(ern)? agro|nw agro", n): lz = "north.?west(ern)? ?agro|north-west agro"
    elif "togdheer agro" in n: lz = "togdheer agro"
    elif "cowpea" in n: lz = "cowpea|central regions agro"
    elif "dawo" in n: lz = "dawo"
    elif re.search(r"bay agro|sorghum high", n) or (n.startswith("bay") and "agro" in n):
        lz, regs = r"bay|sorghum high", {"Bay"}
    elif "bakool" in n:
        lz, regs = (AGRO if "agro" in n else "pastoral"), {"Bakool"}
    elif "gedo" in n:
        regs = {"Gedo"}
        dists = NORTH_GEDO if "north" in n else (None if "south" not in n else "SOUTH")
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else "pastoral" if "pastoral" in n else None
    elif "shabelle" in n:
        regs = ({"Lower Shabelle"} if "lower" in n else {"Middle Shabelle"} if "middle" in n else SHABELLE)
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else None
    elif "juba" in n:
        regs = ({"Lower Juba"} if "lower" in n else {"Middle Juba"} if "middle" in n else JUBA)
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else "pastoral" if "pastoral" in n else None
    elif re.search(r"belet ?w|beled ?w", n) or "mataban" in n:
        # Mataban district was carved out of Beledweyn; FEWS NET units still use Beledweyn
        regs, dists = {"Hiiraan"}, {"Beledweyn"}
    elif re.search(r"hiran|hiraan|hiiraan", n):
        regs = {"Hiiraan"}
        lz = RIVERINE if "riverine" in n else AGRO if "agro" in n else None
    else:
        return None
    if regs is None and qual is not None:
        regs = qual
    if regs is None and isinstance(region, str):          # fall back on the region FSNAU reports
        regs = {r for r in REGIONS if r.lower() in region.lower()} or None
    key = f"{lz}|{','.join(sorted(regs)) if regs else ''}|{dists if isinstance(dists, str) else ','.join(sorted(dists or []))}"
    return lz, regs, dists, key


def match(U, lz, regs, dists):
    """FEWS NET units in the given regions/districts whose zone name matches the pattern."""
    s = U
    if regs:
        s = s[s.reg.isin(regs)]
    if dists == "SOUTH":
        s = s[~s.dist.isin(NORTH_GEDO)]
    elif dists:
        s = s[s.dist.isin(dists)]
    if lz:
        s = s[s.lzl.str.contains(lz, regex=True)]
    return set(s.fnid)


# ------------------------------------------------------------------ town surveys -> district
TOWNS = [  # name pattern -> district P-code (Banadir as one district, SO22)
    (r"mogadishu|banadir|daynil|dharken|hamar|waberi|madina|wadajir", "SO22"), (r"baidoa|baydhab", "SO2401"),
    (r"bos+a+so", "SO1601"), (r"dh?u+s+a?m+a?r+e+b|guri ?e?l", "SO1901"), (r"dol+o+w|dowlo", "SO2605"),
    (r"galk?a?h?c?a?yo|galcayo|galkahyo", "SO1801"), (r"garowe|nugal|nugaal", "SO1701"),
    (r"kismay|l\. juba", "SO2801"), (r"hargeisa|w\.? ?galbeed|woq|galbeed", "SO1201"), (r"burao|togh?dheer", "SO1301"),
    (r"berbera", "SO1202"), (r"qardho|gardo", "SO1606"), (r"belet ?w|beled ?w|beletyw", "SO2001"),
    (r"dho?bley|dobley", "SO2802"), (r"las ?anod|lasanood|sool", "SO1401"), (r"afgoye", "SO2302"),
    (r"bardera|bardheer", "SO2602"), (r"afmadow", "SO2802"), (r"abudwaq", "SO1902"), (r"buale", "SO2701"),
    (r"jowhar", "SO2101"), (r"wajid", "SO2504"), (r"hudd?ur|xuddur", "SO2501"), (r"elberde", "SO2502"),
    (r"erigavo|sanaag", "SO1501"), (r"bor[ao]ma|awdal|adwal", "SO1101"), (r"\bbari\b", "SO1601"),
    (r"mudug", "SO1801"), (r"galgad", "SO1901"), (r"mataban", "SO2001"), (r"qoryol", "SO2305"),
    (r"sak[o]+w", "SO2703"), (r"togwajale", "SO1203"), (r"luuq", "SO2606"), (r"belet hawa", "SO2603"),
    (r"bulo ?burt|buloburti", "SO2002"), (r"dinsor", "SO2403"), (r"jalaq?l?a?qsi", "SO2003"),
    (r"jamame", "SO2804"), (r"haradhere", "SO1805"), (r"eldhere", "SO1905"), (r"qanshadhere", "SO2404"),
    (r"teiglow", "SO2503"), (r"margaga", "SO2101"),
]


def town_district(name):
    """First town pattern that matches the survey name (order matters)."""
    for pat, code in TOWNS:
        if re.search(pat, name.lower()):
            return code
    return None


# ------------------------------------------------------------------ fieldwork month
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()


def target_month(fieldwork, season_type, season_year):
    """Last month and year named in the fieldwork dates; else July (Gu) or November (Deyr)."""
    if isinstance(fieldwork, str):
        m = re.findall(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? ?(20\d\d)?", fieldwork.lower())
        y = re.findall(r"20\d\d", fieldwork)
        if m and y:
            return f"{y[-1]}-{MONTHS.index(m[-1][0]) + 1:02d}"
    return f"{int(season_year)}-{'07' if season_type == 'Gu' else '11'}"


def main():
    s = pd.read_csv(RAW / "fsnau" / "surveys.csv")
    U = units()
    s["domain"], s["fnids"], s["dist"] = "", "", ""
    for i, r in s.iterrows():
        if r.population_type == "rural":
            x = rule(r.population_group, r.region)
            ids = match(U, *x[:3]) if x else set()
            if ids:
                s.loc[i, ["domain", "fnids"]] = f"rural|{x[3]}", ";".join(sorted(ids))
        else:
            code = town_district(r.population_group)
            if code:
                # "mixed" (urban and IDP) town surveys count as urban
                s.loc[i, ["domain", "dist"]] = f"{'IDP' if r.population_type == 'IDP' else 'urban'}|{code}", code
    s["month"] = [target_month(f, t, y) for f, t, y in zip(s.fieldwork, s.season_type, s.season_year)]
    s.insert(0, "row", range(1, len(s) + 1))
    keep = ["row", "season_type", "season_year", "population_group", "region", "population_type", "method",
            "gam", "sam", "muac_gam", "cdr", "u5dr", "domain", "fnids", "dist", "month"]
    s[keep].to_csv(OUT / "surveys.csv", index=False)
    print(f"{len(s)} surveys, {(s.domain != '').sum()} matched to a domain")


if __name__ == "__main__":
    main()
