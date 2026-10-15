"""Export analysis-ready CSVs for the Stata replication of the US-cut memo (stata/).

Python keeps the jobs Stata is bad at: parsing survey PDFs, scraping dashboards, fuzzy-matching
organisation and place names, and rainfall windows. This script writes the
results of that work as plain tables. The Stata do-files then build the exposures from their
components and re-estimate every headline number in the memo.

Run after code/56-80. Writes stata/data/*.csv:
  som_panel.csv            survey domain x round: outcomes, controls, ids (FSNAU SMART, 2015 - Gu 2026)
  som_domain_weights.csv   survey domain -> district population weights (sum to 1 within domain)
  som_districts.csv        district: population, aid-dependence components, partners 2024/25,
                           2024 Phase 3+ share, delivered aid (food & cash, treatment sites, cash transfers) by window
  som_units2024.csv        2024 partner presence, organisation x sector x district, with the US-funded
                           share u of each unit (donor field of the 3W, UN agencies at their FTS US share)
  som_fts.csv              humanitarian funding to Somalia by year, US vs other donors (US$ m)
  us_funding_2024.csv      US humanitarian funding by recipient country, 2024 (FTS)
  nga_zones.csv            Nigeria surveillance zone x year: outcomes and zone exposures
  nga_lgas.csv             Nigeria north-east LGA: US share of 2024 partners and partner loss
  eth_zones.csv            Ethiopia zone: US-donor share, JEOP share, change in 4W activity
  eth_zone_rounds.csv      Ethiopia zone x FEWS NET round: share of woredas in Phase 3+
  scale_inputs.csv         child populations used to turn percentage points into children
  python_numbers.csv       every \\newcommand in output/us_cut_memo/numbers_*.tex (for 08_compare.do)
"""
import importlib.util
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INP, TAB = ROOT / "input", ROOT / "output" / "tables"
OUT = ROOT / "stata" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M68 = load("m68", "68_somalia_us_cut.py")
M75 = load("m75", "75_somalia_delivery.py")
M76 = load("m76", "76_ethiopia_us_cut.py")


def somalia():
    # survey panel (identical rows to som_uscut_panel; adds rain12_z and price controls)
    p = pd.read_parquet(INP / "panel" / "som_need_panel.parquet")
    keep = ["domain", "ptype", "season_id", "season_type", "year", "post", "region", "population_group",
            "gam", "sam", "muac_gam", "muac_sam", "stunting", "underweight", "morbidity", "cdr", "u5dr",
            "measles", "vita", "rain_z", "rain12_z", "log_fat", "lp_cereal", "lp_goat"]
    p[keep].to_csv(OUT / "som_panel.csv", index=False)

    # domain -> district weights
    q = M68.survey_panel().drop_duplicates("domain")
    w = [(r.domain, d, v) for r in q.itertuples() for d, v in json.loads(r.dists).items() if d not in (None, "null")]
    pd.DataFrame(w, columns=["domain", "dist", "w"]).to_csv(OUT / "som_domain_weights.csv", index=False)

    # districts
    D = pd.read_csv(TAB / "som_aiddep_districts.csv", index_col=0)[["pop", "usd_pc", "reach_pc", "partners_pc"]]
    D = D.join(pd.read_csv(TAB / "som_uscut_districts.csv", index_col=0)[["partners24", "partners25"]])
    # share of the population in IPC Phase 3+ in 2024 (food insecurity before the cut)
    D = D.join(pd.read_csv(TAB / "som_fs_districts.csv", index_col=0)[["p3share24"]])
    # cash transfers (Cash Working Group 4W): 2024 annual totals scaled to Jan-Jun by the national monthly series
    C = pd.read_csv(TAB / "som_need_district_panel.csv").pivot_table(index="dist", columns="year",
                                                                       values=["cash_usd", "cash_reached"])
    sc = json.loads((TAB / "som_need_key.json").read_text())["cash_h1_scale_2024"]
    D["cash24"] = C[("cash_usd", 2024)] * sc / D["pop"]
    D["cash25"] = C[("cash_usd", 2025)] / D["pop"]
    D["cashreach24"] = C[("cash_reached", 2024)] * sc / D["pop"] / 6 * 100
    D["cashreach25"] = C[("cash_reached", 2025)] / D["pop"] / 6 * 100
    # food & cash reached (FSC) and sites offering severe-malnutrition treatment (Nutrition Cluster):
    # monthly average by district, January-June of each year
    F, N = M75.fsc(), M75.nutrition()
    fh = F[F.m.between(1, 6)].groupby(["dist", "year"]).fsc.mean().unstack()
    nh = N[N.m.between(1, 6)].groupby(["dist", "year"]).otp_sites.mean().unstack()
    for y in [2024, 2025, 2026]:
        D[f"fsc{y % 100}"] = fh.get(y)
        D[f"otp{y % 100}"] = nh.get(y)
    D.index.name = "dist"
    D.reset_index().to_csv(OUT / "som_districts.csv", index=False)
    # national monthly averages, Jan-Jun (the memo's national numbers)
    nat = pd.DataFrame({"year": [2024, 2025, 2026],
                        "fsc_nat": [F[F.m.between(1, 6) & (F.year == y)].fsc.sum() / 6 for y in [2024, 2025, 2026]],
                        "otp_nat": [N[N.m.between(1, 6) & (N.year == y)].otp_sites.sum() /
                                    N[N.m.between(1, 6) & (N.year == y)].m.nunique() for y in [2024, 2025, 2026]]})
    nat.to_csv(OUT / "som_delivery_national.csv", index=False)

    u = pd.read_csv(TAB / "som_uscut_units2024.csv")[["dist", "org", "cluster", "type", "u", "imputed"]]
    u.to_csv(OUT / "som_units2024.csv", index=False)
    pd.read_csv(TAB / "som_uscut_fts.csv").rename(columns={"y": "year"}).to_csv(OUT / "som_fts.csv", index=False)
    pd.read_csv(TAB / "us_hum_funding_2024.csv").to_csv(OUT / "us_funding_2024.csv", index=False)


def nigeria():
    pd.read_csv(TAB / "nga_zone_panel.csv").drop(columns=["surveyName"]).to_csv(OUT / "nga_zones.csv", index=False)
    L = pd.read_csv(TAB / "nga_lga_exposure.csv")
    L[["lga_key", "zone", "region", "u5", "us_share", "loss25"]].to_csv(OUT / "nga_lgas.csv", index=False)


def ethiopia():
    e = M76.exposure()
    e.index.name = "zone"
    e[["region", "us_share", "us_nut", "us_food", "jeop24", "dlog_all", "dlog_food", "dlog_nutrition",
       "dlog_health", "dlog_partners"]].reset_index().to_csv(OUT / "eth_zones.csv", index=False)
    Z = M76.outcomes(e)
    Z[["zone", "month", "share3", "phase", "region"]].to_csv(OUT / "eth_zone_rounds.csv", index=False)
    pd.read_csv(TAB / "eth_national.csv").to_csv(OUT / "eth_national.csv", index=False)


def scale_inputs():
    amn = pd.read_excel(INP / "ipc_amn" / "somalia-acute-malnutrition-analysis" /
                        "acute-malnutrition-between-july-2025-and-june-2026.xlsx", header=None)
    som = float(amn[amn[0].astype(str).str.strip() == "Total"].iloc[0][1])
    B = INP / "subnational_aid" / "hdx_response" / "nga" / "nigeria-acute-malnutrition-data"
    v = pd.read_excel(B / "Nigerian_Acute_Malnutrition_2025.xlsx", sheet_name="NORTH-EAST NIGERIA", header=None)
    hr = next(i for i in range(6) if str(v.iloc[i, 0]).strip() in ("Zone", "Domain"))
    nga = float(pd.to_numeric(v.iloc[hr + 1:, 2], errors="coerce").sum())
    pd.DataFrame([dict(item="somalia_children_6_59m", value=som,
                       source="IPC acute malnutrition analysis Jul 2025-Jun 2026, Total row"),
                  dict(item="nigeria_ne_children_u5", value=nga,
                       source="IPC acute malnutrition 2025, North-East Nigeria sheet")]).to_csv(OUT / "scale_inputs.csv", index=False)


def python_numbers():
    rows = []
    for f in sorted((ROOT / "output" / "us_cut_memo").glob("numbers*.tex")):
        for line in f.read_text().splitlines():
            m = re.match(r"\\newcommand\{\\n([A-Za-z]+)\}\{(.*)\}$", line)
            if m:
                rows.append(dict(name=m.group(1), value=m.group(2), file=f.name))
    # Fig 3 event-study coefficients (wasting by survey round, per s.d. of exposure)
    zn = {"z_index": "Dep", "E_pred": "Us", "E_loss": "Loss"}
    for r in pd.read_csv(TAB / "fig3_round_event.csv").itertuples():
        s, y = r.round.split()
        if y not in ("2024",):
            rows.append(dict(name=f"evt{zn[r.exposure]}{s}{y}", value=f"{r.b:.2f}", file="fig3_round_event.csv"))
    pd.DataFrame(rows).to_csv(OUT / "python_numbers.csv", index=False)
    # domain exposures as Python built them (01_somalia_build.do checks its own against these)
    p = pd.read_parquet(INP / "panel" / "som_need_panel.parquet").drop_duplicates("domain")
    p[["domain", "E_pred", "E_loss", "z_index"]].to_csv(OUT / "python_domain_exposures.csv", index=False)


if __name__ == "__main__":
    somalia()
    nigeria()
    ethiopia()
    scale_inputs()
    python_numbers()
    for f in sorted(OUT.glob("*.csv")):
        print(f.name, len(pd.read_csv(f)))
