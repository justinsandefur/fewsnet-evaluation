"""Data for the Stata replication of the Lancet Global Health paper (us_cut_memo/lgh_replication/).

Data assembly only: this script copies the analysis files built upstream (56, 62, 68, 69, 70, 75, via
81_export_stata.py) and reads donor names out of free text (Nutrition Cluster site reports, OCHA 3W).
It estimates nothing; every number in the paper comes from the Stata run in lgh_replication/.
Run after code/56-81. Writes lgh_replication/data/:

  panel.csv            survey domain x round: outcomes, controls (2015 - Gu 2026)
  domain_weights.csv   survey domain -> district population weights
  districts.csv        district: population, aid-dependence components, partners Apr-Oct 2024/2025,
                       food & cash reached and SAM treatment sites (monthly average, Jan-Jun 2024/25/26)
  units2024.csv        2024 partner units (organisation x sector x district) and their US-funded share u
  fts.csv              humanitarian funding to Somalia by year, US vs other donors (US$ m)
  usaid_sites.csv      district x month: nutrition site-months naming USAID/BHA as a funder, 2023-26
  partners.csv         district x month: humanitarian partners present (organisation x sector), 2024-26
  national.csv         national food & cash reached and SAM treatment sites per month, Jan-Jun 2024/25/26
  children.csv         children 6-59 months, Somalia (IPC acute malnutrition analysis 2025/26)

(lgh_replication/data/doc_numbers.csv, the numbers as printed in the manuscript, is kept by hand.)
"""
import importlib.util
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB, ST = ROOT / "input", ROOT / "output" / "tables", ROOT / "stata" / "data"
OUT = ROOT / "lgh_replication" / "data"
OUT.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("m68", ROOT / "code" / "68_somalia_us_cut.py")
M68 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M68)

# straight copies of the Stata export (81)
pd.read_csv(ST / "som_panel.csv")[["domain", "ptype", "season_id", "season_type", "year", "post", "region",
                                   "population_group", "gam", "sam", "muac_gam", "cdr", "u5dr", "rain_z",
                                   "rain12_z", "log_fat", "lp_cereal", "lp_goat"]].to_csv(OUT / "panel.csv", index=False)
for src, dst in [("som_domain_weights.csv", "domain_weights.csv"),
                 ("som_units2024.csv", "units2024.csv"), ("som_fts.csv", "fts.csv"),
                 ("som_delivery_national.csv", "national.csv")]:
    shutil.copy(ST / src, OUT / dst)
d = pd.read_csv(ST / "som_districts.csv")
d[["dist", "pop", "usd_pc", "reach_pc", "partners_pc", "partners24", "partners25",
   "fsc24", "fsc25", "fsc26", "otp24", "otp25", "otp26"]].to_csv(OUT / "districts.csv", index=False)
s = pd.read_csv(ST / "scale_inputs.csv")
s[s.item == "somalia_children_6_59m"].to_csv(OUT / "children.csv", index=False)

# nutrition sites naming USAID/BHA as a funder (free-text donor fields)
n = pd.read_csv(INP / "subnational_aid" / "firststage" / "nutrition_cluster_ona" /
                "som_nutrition_ona_site_month_2018-2026.csv.gz", low_memory=False,
                usecols=["Reporting Period", "District Pcode", "Add other source of funds:",
                         "Partner current source of funds: cash and supplies"])
v = (n["Add other source of funds:"].astype(str) + " " +
     n["Partner current source of funds: cash and supplies"].astype(str)).str.lower()
n["usaid"] = v.str.contains(r"usaid|\bbha\b|ofda|\bffp\b|united states|\busg\b").astype(int)
mon = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                    "september", "october", "november", "december"], 1)}
rp = n["Reporting Period"].astype(str)
n["year"], n["month"] = pd.to_numeric(rp.str[:4], errors="coerce"), rp.str[5:].str.lower().map(mon)
n["dist"] = n["District Pcode"].astype(str).map(M68.dist_key)
n = n.dropna(subset=["year", "month", "dist"])
n = n[(n.year >= 2023) & ((n.year < 2026) | (n.month <= 6))]
n.groupby(["dist", "year", "month"]).usaid.sum().reset_index().astype({"year": int, "month": int}) \
    .to_csv(OUT / "usaid_sites.csv", index=False)

# humanitarian partners present per district and month (OCHA 3W)
o = pd.read_parquet(INP / "subnational_aid" / "tidy" / "org_presence_som.parquet")
o = o[(o.period_type == "month") & o.cluster.isin(M68.SECTORS) & (o.period_start >= "2024-01-01")].copy()
o["dist"] = o.admin2_pcode.map(M68.dist_key)
o["year"], o["month"] = o.period_start.dt.year, o.period_start.dt.month
o.drop_duplicates(["dist", "org", "cluster", "year", "month"]).groupby(["dist", "year", "month"]).size() \
    .rename("partners").reset_index().to_csv(OUT / "partners.csv", index=False)

for f in sorted(OUT.glob("*.csv")):
    if f.name == "doc_numbers.csv":
        continue
    print(f.name, len(pd.read_csv(f)))
