"""How much does each survey family add to coverage of the world's food crises?

Combines the DHS inventory (02) with MICS, LSMS, CWIQ and UNHCR refugee-camp
nutrition surveys (10), keeps surveys since 2011 that measured children's
weight and height, and asks what share of the people in Crisis or worse, and
in Emergency or worse (Global Report on Food Crises, 2016-2025), lived in
countries with at least one such survey. Tiers are cumulative, ordered by
how precisely the survey locates children:
  1. DHS with GPS (cluster coordinates, displaced up to 5km)
  2. + LSMS with GPS (enumeration-area coordinates, also displaced)
  3. + MICS (region only; cluster coordinates not released)
  4. + UNHCR refugee-camp nutrition surveys (camp only)

Outputs: output/tables/survey_tiers.csv, survey_tiers_by_country.csv,
         additions to output/tables/key_numbers.json
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"

# World Bank catalogue country names that differ from the FEWS NET country list
WB_FIX = {"Congo, Dem. Rep.": "COD", "Congo, Rep.": "COG", "Egypt, Arab Rep.": "EGY",
          "West Bank and Gaza": "PSE", "Yemen, Rep.": "YEM", "Gambia, The": "GMB",
          "Kyrgyz Republic": "KGZ", "Lao PDR": "LAO", "Macedonia, FYR": "MKD",
          "North Macedonia": "MKD", "Iran, Islamic Rep.": "IRN", "Syrian Arab Republic": "SYR",
          "Venezuela, RB": "VEN", "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV",
          "Eswatini": "SWZ", "Viet Nam": "VNM", "Turkiye": "TUR", "South Sudan": "SSD",
          "Bosnia-Herzegovina": "BIH", "St. Lucia": "LCA", "São Tomé and Príncipe": "STP",
          "Somalia": "SOM", "Sudan": "SDN", "Tanzania": "TZA", "Kosovo": "XKX",
          "Afghanistan": "AFG", "Gambia": "GMB", "Myanmar": "MMR"}
DHS_FIX = {"Congo Democratic Republic": "COD", "Congo": "COG", "Cote d'Ivoire": "CIV",
           "Kyrgyz Republic": "KGZ", "Tanzania": "TZA", "Eswatini": "SWZ", "Gambia": "GMB",
           "Myanmar": "MMR"}


def iso3(names: pd.Series, fix: dict, codes: pd.DataFrame) -> pd.Series:
    lookup = dict(zip(codes.name, codes.iso3))
    lookup.update({k: v for k, v in zip(codes.name.str.lower(), codes.iso3)})
    return names.map(lambda n: fix.get(n) or lookup.get(n) or lookup.get(str(n).lower()))


def main():
    codes = pd.DataFrame(json.loads((INP / "fewsnet" / "countries.json").read_text()))
    codes = codes.rename(columns={"iso3166a3": "iso3", "preferred_name": "name"})[["iso3", "name"]]

    dhs = pd.read_csv(INP / "dhs" / "dhs_surveys.csv")
    dhs = dhs[(dhs.n_wasted.fillna(0) > 0) & dhs.gps_file & (dhs.FieldworkEnd >= "2011-01-01")]
    dhs = pd.DataFrame({"family": "DHS (GPS)", "iso3": iso3(dhs.CountryName, DHS_FIX, codes),
                        "year": pd.to_datetime(dhs.FieldworkStart).dt.year, "survey": dhs.SurveyId})

    inv = pd.read_csv(INP / "surveys" / "survey_inventory.csv")
    inv = inv[inv.anthro & (inv.year_start >= 2011)].copy()
    inv["iso3"] = iso3(inv.country, WB_FIX, codes)
    title = inv.title.fillna("")
    fam = pd.Series(None, index=inv.index, dtype=object)
    fam[(inv.source == "lsms") & inv.gps_var] = "LSMS (GPS)"
    fam[inv.source == "MICS"] = "MICS (region)"
    fam[title.str.contains("Expanded Nutrition Survey|Refugee Camp", case=False)] = "UNHCR camps"
    fam[inv.source == "CWIQ"] = "CWIQ"
    inv["family"] = fam
    other = inv.dropna(subset=["family"]).rename(columns={"year_start": "year", "idno": "survey"})
    surveys = pd.concat([dhs, other[["family", "iso3", "year", "survey"]]], ignore_index=True)
    surveys.to_csv(TAB / "anthro_surveys_2011on.csv", index=False)

    g = pd.read_csv(TAB / "grfc_country_years.csv")
    order = ["DHS (GPS)", "LSMS (GPS)", "MICS (region)", "UNHCR camps"]
    rows, have, have_year = [], set(), set()
    for fam_name in order:
        s = surveys[surveys.family == fam_name]
        have |= set(s.iso3.dropna())
        have_year |= {(i, y) for i, y in zip(s.iso3, s.year)}
        any_ = g.iso3.isin(have)
        same = pd.Series([(i, y) in have_year or (i, y - 1) in have_year
                          for i, y in zip(g.iso3, g.year)], index=g.index)
        rows.append({"tier": "+ " + fam_name if rows else fam_name,
                     "surveys_in_family": len(s), "countries_in_family": s.iso3.nunique(),
                     "share_p3_any_since_2011": g.loc[any_, "p3"].sum() / g.p3.sum(),
                     "share_p4_any_since_2011": g.loc[any_, "p4plus"].sum() / g.p4plus.sum(),
                     "share_p4_within_a_year": g.loc[same, "p4plus"].sum() / g.p4plus.sum()})
    tiers = pd.DataFrame(rows)
    tiers.to_csv(TAB / "survey_tiers.csv", index=False)
    print(tiers.round(3).to_string())

    # Which big crisis countries does each family reach?
    top = (g.groupby(["iso3", "name"]).p4plus.sum().sort_values(ascending=False).head(15)
             .reset_index())
    for fam_name in order + ["CWIQ"]:
        s = surveys[surveys.family == fam_name].groupby("iso3").year.apply(
            lambda y: ", ".join(str(int(v)) for v in sorted(set(y))))
        top[fam_name] = top.iso3.map(s).fillna("")
    top.to_csv(TAB / "survey_tiers_by_country.csv", index=False)
    print(top.to_string())

    k = json.loads((TAB / "key_numbers.json").read_text())
    k["survey_tiers"] = tiers.round(3).to_dict("records")
    k["survey_family_counts"] = surveys.groupby("family").agg(
        surveys=("survey", "size"), countries=("iso3", "nunique")).reset_index().to_dict("records")
    (TAB / "key_numbers.json").write_text(json.dumps(k, indent=1, default=str))


if __name__ == "__main__":
    main()
