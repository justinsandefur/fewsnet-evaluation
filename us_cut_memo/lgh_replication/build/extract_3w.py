"""Read the raw OCHA Somalia 3W spreadsheets and write them as three tidy CSVs (no analysis).

The 3W ("who does what where") is OCHA's list of humanitarian partners by sector and district.

Reads (raw/3w/, downloaded from HDX; see raw/SOURCES.md)
  3W_Operational_Presence_Dataset_Jan-Nov_2024.xlsx              partners present, 2024
  3W_Operational_Presence_Dataset_January_-_December_2025.xlsx   partners present, 2025
  3W_Operational_Presence_Dataset_January_-_June_2026.xlsx       partners present, 2026
  Operational_Partners_Presence_Jan-Sep_2024.xlsx                activity rows, 2024: people reached,
                                                                 US$ transferred, donor
  3ws-2023-consolidated.xlsx                                     activity rows, 2023: donor
Writes (source/)
  presence_3w.csv    organisation x sector x district x month, 2024-2026 (health, nutrition,
                     food security and WASH only)
  reach_3w_2024.csv  people reached and US$ transferred by district x month x sector, 2024
  donors_3w.csv      the donor named on each 2023 and 2024 activity row, classified as US,
                     a UN agency, or another donor

Python only reads the files, cleans names and classifies the free-text donor field. Counting
partners, averaging donor shares and everything else is done in Stata.
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW, OUT = HERE / "raw" / "3w", HERE / "source"

SECTORS = ["nutrition", "health", "food_security", "wash"]
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

# OCHA posts a new presence file every few months, each repeating all earlier months of the
# year. For any month we use the latest file that covers it, so one file per year:
#   2024: Jan-Nov 2024 file (it has data for January-October); it replaces the Q1 2024 file and
#         the Jan-Sep 2024 file for those months
#   2025: Jan-Dec 2025 file; it replaces the Jan-Mar, Jan-Apr, Jan-Aug, Jan-Sep, Jan-Oct files
#   2026: Jan-Jun 2026 file (the latest posted)
PRESENCE_FILES = [
    ("3W_Operational_Presence_Dataset_Jan-Nov_2024.xlsx", "3W_dataset", 2024),
    ("3W_Operational_Presence_Dataset_January_-_December_2025.xlsx", "3W_Dataset_Jan - Dec 2025", 2025),
    ("3W_Operational_Presence_Dataset_January_-_June_2026.xlsx", "3W_Dataset_Jan-June 2026", 2026),
]

# District P-codes that are wrong in the 2025-26 files. Four Banadir (Mogadishu) districts carry
# each other's codes, and a few cells hold an Excel error (#REF!). We trust the district name
# and use the code the official boundaries (OCHA COD-AB) give that name.
PCODE_FIX = {
    ("Bondhere", "SO2202"): "SO2201", ("Cabdulasis", "SO2201"): "SO2202",
    ("Heliwa", "SO2209"): "SO2208", ("Hodan", "SO2208"): "SO2209",
    ("Daynile", "#REF!"): "SO2203", ("Wadajir (Medina)", "#REF!"): "SO2215",
    ("Yaaqshid", "#REF!"): "SO2217", ("Bu'aale", "#REF!"): "SO2701",
}


def read_sheet(file, sheet, header=0):
    """One sheet as text: spaces trimmed, and blank / '(blank)' / 'N/A' cells set to missing."""
    d = pd.read_excel(RAW / file, sheet_name=sheet, header=header, keep_default_na=False)
    for c in d.columns:
        d[c] = d[c].map(lambda v: v.replace("\xa0", " ").strip() if isinstance(v, str) else v)
        d[c] = d[c].replace(["", "(blank)", "N/A", "n/a", "#N/A"], None)
    return d


def clean_org(name):
    """Organisation name in plain lower-case letters, so spellings match across files:
    accents and anything in brackets (usually the acronym) removed, punctuation made a space."""
    if not isinstance(name, str):
        return None
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.replace("'", "").replace("`", ""))
    return re.sub(r"\s+", " ", s).strip() or None


# Sector labels differ between files ('Nutrition', 'Food Security', 'WASH', 'CCCM', ...).
# The first rule that matches wins; anything else is 'other'.
CLUSTER_RULES = [
    ("shelter_nfi", r"shelter|non-? ?food|\bnfi|s ?& ?nfi|snfi|es/?nfi|es nfi|^es\b"),
    ("food_security", r"food|\bfs[lc]\b|livelihood|agricult|cash for food|\bfsl\b|^fsc"),
    ("nutrition", r"nutri|nutrt|\bnut\b"),
    ("health", r"health|covid|\bhea\b"),
    ("wash", r"wash|water|sanitation|hygiene"),
    ("protection", r"protect|gbv|gender|\bcp\b|hlp|housing|mine|explosive|\beh\b|\bma\b|child"),
    ("education", r"educ|\bedu\b"),
]


def map_cluster(label):
    if not isinstance(label, str) or label.strip().lower() in ("", "nan", "none", "(blank)"):
        return None
    s = label.strip().lower()
    if "health" in s and "nutr" in s:      # e.g. 'Health and Nutrition': counted as health
        return "health"
    for name, pattern in CLUSTER_RULES:
        if re.search(pattern, s):
            return name
    return "other"


def district_code(name, code):
    code = str(code).strip().upper()
    return PCODE_FIX.get((name, code), code)


def presence():
    """Which organisation worked in which sector, district and month."""
    parts = []
    for file, sheet, year in PRESENCE_FILES:
        d = read_sheet(file, sheet)
        d = d.dropna(subset=["Month", "Cluster", "District", "DistrictPcode", "Organization_Name"])
        parts.append(pd.DataFrame({
            "org": d.Organization_Name.map(clean_org),
            "cluster": d.Cluster.map(map_cluster),
            "admin2_pcode": [district_code(n, c) for n, c in zip(d.District, d.DistrictPcode)],
            "year": year,
            "month": d.Month.str[:3].str.lower().map(MONTHS),
        }))
    p = pd.concat(parts)
    p = p[p.cluster.isin(SECTORS)].drop_duplicates()
    return p.sort_values(["year", "month", "admin2_pcode", "cluster", "org"])


def to_number(v):
    """A number, or missing. Text like '1,200' or '$500' is read; dates (Excel turned some
    counts into dates) and other text are missing."""
    if isinstance(v, bool) or isinstance(v, pd.Timestamp) or hasattr(v, "year"):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("$", "")
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def reach_2024():
    """People reached and US$ transferred, 2024. Only the Jan-Sep 2024 activity file has these;
    the later presence-only files do not. Rows are summed to district x month x sector."""
    d = read_sheet("Operational_Partners_Presence_Jan-Sep_2024.xlsx", "Data")
    d = d[~d["Cluster/AoR"].astype(str).str.startswith("#")]          # HXL tag row under the header
    d = d[~d.Status.astype(str).str.lower().str.contains("plan")]     # planned, not yet delivered
    parts = []
    for measure, col in [("reached", "Total Individulals reached"), ("usd", "Total USD transferred")]:
        parts.append(pd.DataFrame({
            "admin2_pcode": d.DistrictCode.map(lambda c: str(c).strip().upper()),
            "period_start": "2024-" + d["Reporting \nMonth"].str[:3].str.lower().map(MONTHS).map("{:02d}".format) + "-01",
            "cluster": d["Cluster/AoR"].map(map_cluster),
            "measure": measure,
            "value": d[col].map(to_number),
        }))
    r = pd.concat(parts).dropna(subset=["value"])
    return r.groupby(["admin2_pcode", "period_start", "cluster", "measure"], as_index=False).value.sum()


# Donor field: free text such as 'BHA', 'ECHO, SHF', 'UNICEF/WFP'. It is split into names and
# each name is classified: 'us' (a US government donor), a UN agency (whose US share is taken
# from FTS in Stata), or 'nonus'. Names matching none of these say nothing and are dropped.
US_RX = re.compile(r"usaid|\bbha\b|\bofda\b|\bffp\b|\bprm\b|united states|\bus ?gov|\busg\b|state department|"
                   r"\bu\.s\.?\b|\bus\b|american people|creative associate|pepfar|\bcdc\b|feed the future", re.I)
AGENCY_RX = {"unicef": r"unicef|children'?s fund", "wfp": r"\bwfp\b|world food", "unhcr": r"unhcr|refugee agency",
             "iom": r"\biom\b|organi[sz]ation for migration", "fao": r"\bfao\b|food and agriculture",
             "unfpa": r"unfpa|population fund", "who": r"\bwho\b|world health"}
NONUS_RX = re.compile(
    r"echo|\beu\b|european|fcdo|dfid|\buk\b|united kingdom|\bshf\b|humanitarian fund|cerf|central emergency|"
    r"world ?bank|\bwb\b|ida\b|sida|\bsdc\b|swiss|danida|denmark|nmfa|norad|norw|gffo|german|giz|kfw|bmz|"
    r"auswärtiges|irish|ireland|\bgac\b|canada|japan|jica|korea|koica|qatar|ksrelief|saudi|\buae\b|emirat|kuwait|"
    r"turk|tika|\becw\b|education cannot|\bgpe\b|global partnership|global fund|gavi|dutch|netherland|\bmfa\b|"
    r"ital|aics|france|afd\b|own fund|internal|self|volunteer|private|misereor|mieser|caritas|secours|"
    r"kindermission|\bdkh\b|forum ?civ|start fund|islamic relief|gates|ocha|\bsrcs\b|ifrc|\bicrc\b|"
    r"finland|sweden|swedish|austria|belgi|luxem|spain|aecid|australia|dfat|china|islamic development|"
    r"diakonie|bread for|tearfund|christian aid|cafod|trocaire|oxfam|government of somalia|\bfgs\b|"
    r"ministry|unocha|\bpbf\b|peacebuilding|unmptf|joint programme|mptf", re.I)


def donor_classes(text):
    """Classes of the donor names in one donor field (an empty list if none is informative)."""
    if not isinstance(text, str):
        return []
    t = text.strip()
    if t in ("", "0", "nan", "-") or re.fullmatch(r"(?i)other|not in the list|n/?a|none|\(blank\)|ingo|nngo|un", t):
        return []
    out = []
    for name in [x.strip() for x in re.split(r"[,/|;&+]| and |\n", t) if x.strip()]:
        agency = [k for k, p in AGENCY_RX.items() if re.search(p, name, re.I)]
        if US_RX.search(name):          # US checked first: 'USAID via UNICEF' counts as US
            out.append("us")
        elif agency:
            out.append(agency[0])
        elif NONUS_RX.search(name):
            out.append("nonus")
    return out


def donors():
    """One row per (activity row, informative donor name). A row whose donor field says nothing
    useful is kept once with an empty donor_class, so Stata still sees the row."""
    files = [(2023, "3ws-2023-consolidated.xlsx", "DATA", 2,
              "Organization Name", "Organization Type", "Cluster", "Donor", "District_Pcode"),
             (2024, "Operational_Partners_Presence_Jan-Sep_2024.xlsx", "Data", 0,
              "The name of your organisation with acronym", "The type of your organisation",
              "Cluster/AoR", "The donor for the acitvity", "DistrictCode")]
    rows = []
    for year, file, sheet, header, org, org_type, cluster, donor, district in files:
        d = pd.read_excel(RAW / file, sheet_name=sheet, header=header)
        d = d[~d[org].astype(str).str.startswith("#")]                # HXL tag row (2024 file)
        for i, r in d.iterrows():
            dist = str(r[district]).strip() if pd.notna(r[district]) else None
            if dist and dist.startswith("SO22"):                      # Banadir districts as one
                dist = "SO22"
            if clean_org(r[org]) is None or dist is None:
                continue
            base = dict(file_year=year, row_id=i, org=clean_org(r[org]), org_type=r[org_type],
                        cluster=map_cluster(r[cluster]), dist=dist)
            for c in donor_classes(r[donor]) or [None]:
                rows.append(dict(base, donor_class=c))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, df in [("presence_3w", presence()), ("reach_3w_2024", reach_2024()), ("donors_3w", donors())]:
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name}.csv: {len(df):,} rows")
