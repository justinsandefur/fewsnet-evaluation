"""FEWS NET market prices from the FEWS NET Data Warehouse (FDW), and coverage vs. WFP prices.

Access: the FDW REST API with format=csv and NO page_size returns the whole filtered result in one
response (~1,000 rows/s). The paginated JSON route is unusable for bulk download: page_size >= 1000
and offset > 1000 both return 403 Forbidden, so a JSON query can reach at most ~1,500 records.
  /api/marketpricefacts/?format=csv&country_code=XX&price_type=Retail&start_date=..&end_date=..
                         &product=<cpcv2>&product=<cpcv2>...   (product is repeatable and OR'd)
  /api/marketproduct/?format=csv   catalogue of every market x product series (21k rows)
  /api/market/?format=csv          every market with fnid, admin names, coordinates (2.3k rows)
Filters: retail prices only, period starting 2008-01 to 2024-12, product codes (cpcv2) of staple
cereals, tubers and pulses chosen from the catalogue by product name (PRODUCT_KEEP / PRODUCT_DROP below;
the list kept is written to input/prices_fdw/products.csv). One request per country (split by period if
it fails), cached as input/prices_fdw/raw/*.csv so the script resumes; sequential, 0.5 s apart.

Outputs
  input/prices_fdw/catalog.parquet   every market x product series in FDW (catalogue)
  input/prices_fdw/products.csv      product codes kept by the staple filter
  input/prices_fdw/prices.parquet    market x product x month, retail, staples, 2008-2024
  input/prices_fdw/markets.parquet   one row per market with coordinates (/api/market/)
  output/tables/price_coverage.csv   country x year: markets reporting (FDW, WFP) and share of FEWS NET
                                     areas with a reporting market within 150 km (FDW, WFP, union)

Usage: python 54_fetch_fdw_prices.py [fetch|build|coverage]   (default: all three)
"""
import re
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "input"
OUT = INP / "prices_fdw"
RAW = OUT / "raw"
TAB = ROOT / "output" / "tables"
RAW.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

API = "https://fdw.fews.net/api/"
START, END = "2008-01-01", "2024-12-31"
PRIORITY = ["SO", "ET", "SD", "SS", "KE", "NG", "NE", "ML", "BF", "TD", "YE", "AF", "HT"]
RADIUS_M = 150_000

# staple filter on FDW product names (case-insensitive regex)
PRODUCT_KEEP = r"maize|corn|sorghum|millet|wheat|rice|teff|cassava|\bgari\b|beans?\b|cowpea|niebe|niébé"
PRODUCT_DROP = (r"bran\b|seed|\boil|green bean|soy|coffee|cocoa|cake|bread|biscuit|pasta|macaroni|spaghetti|noodle|"
                r"feed|fodder|stover|straw|husks|popcorn|sweet corn|corn ?flakes|starch|beer|tortilla|buckwheat|"
                r"vanilla|baked|cooked|prepared|milling")
# not kept: potatoes, sweet potatoes, yams, taro, lentils, peas, chickpeas, barley, unspecified pulses;
# cpcv2 R0124* ("flat bean") is a fresh vegetable and is dropped too

S = requests.Session()
S.headers["User-Agent"] = "fewsnet-evaluation research script (sequential, cached)"


def read_fdw_csv(f):
    """FDW CSVs carry a byte-order mark at the start of every row, not just the file: strip it."""
    d = pd.read_csv(f, low_memory=False, encoding="utf-8-sig")
    c0 = d.columns[0]
    if d[c0].dtype == object:
        d[c0] = d[c0].str.lstrip("\ufeff")
        if c0 == "id":
            d[c0] = pd.to_numeric(d[c0])
    return d


def get_csv(endpoint, params, cache):
    """Unpaginated CSV for an endpoint, cached to raw/<cache>.csv; retries with backoff."""
    f = RAW / f"{cache}.csv"
    if f.exists():
        return read_fdw_csv(f)
    for k in range(4):
        try:
            r = S.get(API + endpoint + "/", params={**params, "format": "csv"}, timeout=1800)
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                tmp = f.with_suffix(".part")
                tmp.write_bytes(r.content)
                tmp.rename(f)
                time.sleep(0.5)
                return read_fdw_csv(f)
            print(f"    HTTP {r.status_code}: {r.text[:80]!r}; retry", flush=True)
        except requests.RequestException as e:
            print(f"    {type(e).__name__}; retry", flush=True)
        time.sleep(10 * 2 ** k)
    raise RuntimeError(f"failed: {endpoint} {params}")


def countries():
    return sorted(pd.read_parquet(INP / "fewsnet" / "ipcphase.parquet", columns=["country_code"])
                  .country_code.dropna().unique())


def staple_products(cat):
    """Product codes (cpcv2) of staple cereals, tubers and pulses, from the catalogue."""
    p = cat.groupby(["cpcv2", "product_name"]).datapoint_count.sum().reset_index()
    nm = p.product_name.str.lower()
    keep = nm.str.contains(PRODUCT_KEEP) & ~nm.str.contains(PRODUCT_DROP) & ~p.cpcv2.str.startswith("R0124")
    p["keep"] = keep
    p.sort_values("datapoint_count", ascending=False).to_csv(OUT / "products_all.csv", index=False)
    k = p[keep].copy()
    k.to_csv(OUT / "products.csv", index=False)
    return sorted(k.cpcv2.unique())


def fetch():
    cc = countries()
    print("FEWS NET countries:", " ".join(cc), flush=True)
    cat = get_csv("marketproduct", {}, "catalog")
    cat.to_parquet(OUT / "catalog.parquet")
    mk = get_csv("market", {}, "market")
    mk.to_parquet(OUT / "market_endpoint.parquet")
    print(f"  catalogue: {len(cat):,} series; markets: {len(mk):,}", flush=True)
    codes = staple_products(cat)
    print(f"  staple product codes kept: {len(codes)}", flush=True)
    c = cat[cat.cpcv2.isin(codes) & (cat.price_type == "Retail")].copy()
    c["cc"] = c.fnid.str[:2]
    c = c[c.cc.isin(cc) & (c.last_period_date >= START) & (c.first_period_date <= END)]
    est = c.groupby("cc").datapoint_count.sum().sort_values(ascending=False)
    print(f"  catalogue datapoints in these series (all years): {est.sum():,}\n" + est.to_string(), flush=True)
    order = [x for x in PRIORITY if x in cc] + [x for x in cc if x not in PRIORITY]
    t0 = time.time()
    for x in order:
        mine = sorted(c[c.cc == x].cpcv2.unique())
        if not mine:
            print(f"  {x}: no staple retail series in catalogue", flush=True)
            continue
        q = {"country_code": x, "price_type": "Retail", "product": mine}
        try:
            n = len(get_csv("marketpricefacts", {**q, "start_date": START, "end_date": END}, f"price_{x}"))
        except RuntimeError:
            n = 0
            for a_, b_ in [("2008-01-01", "2012-12-31"), ("2013-01-01", "2018-12-31"), ("2019-01-01", END)]:
                n += len(get_csv("marketpricefacts", {**q, "start_date": a_, "end_date": b_},
                                 f"price_{x}_{a_[:4]}"))
        print(f"  {x}: {n:,} records ({len(mine)} products; {time.time() - t0:.0f} s elapsed)", flush=True)


KEEP_COLS = ["country_code", "country", "admin_1", "admin_2", "fnid", "market", "market_id", "cpcv2", "product",
             "product_source", "price_type", "unit", "currency", "period_date", "start_date", "value",
             "common_unit", "common_unit_price", "common_currency_price", "status", "collection_status",
             "latitude", "longitude", "dataseries", "source_organization"]


def build():
    files = sorted(RAW.glob("price_*.csv"))
    d = pd.concat([read_fdw_csv(f) for f in files], ignore_index=True)
    print(f"raw price records: {len(d):,} from {len(files)} files", flush=True)
    d = d[[c for c in KEEP_COLS if c in d.columns]].drop_duplicates()
    d["month"] = pd.to_datetime(d.start_date).dt.to_period("M")
    d = d[d.value.notna() & (d.value > 0)]
    d = d[(d.month >= pd.Period(START[:7], "M")) & (d.month <= pd.Period(END[:7], "M"))]
    # one row per market x product series x month (series = market, product, unit, currency, source)
    key = ["fnid", "cpcv2", "product_source", "unit", "currency", "month"]
    first = ["country_code", "country", "admin_1", "admin_2", "market", "market_id", "product", "price_type",
             "common_unit", "latitude", "longitude", "source_organization"]
    p = (d.groupby(key, dropna=False)
         .agg(**{c: (c, "first") for c in first},
              price=("value", "mean"), price_common_unit=("common_unit_price", "mean"),
              price_usd=("common_currency_price", "mean"), n_obs=("value", "size"))
         .reset_index())
    mk = get_csv("market", {}, "market")
    mk = mk.rename(columns={"id": "market_id", "latitude": "lat_m", "longitude": "lon_m", "name": "market_name"})
    p = p.merge(mk[["market_id", "lat_m", "lon_m"]], on="market_id", how="left")
    p["latitude"] = p.latitude.fillna(p.lat_m)
    p["longitude"] = p.longitude.fillna(p.lon_m)
    p = p.drop(columns=["lat_m", "lon_m"])
    p["month"] = p.month.astype(str)
    p.to_parquet(OUT / "prices.parquet")
    print(f"prices.parquet: {len(p):,} market x product x month rows, {p.fnid.nunique():,} markets, "
          f"{p.country_code.nunique()} countries", flush=True)
    # markets: from the market endpoint, restricted to markets with any price series in FDW, plus
    # summary of staple-price reporting in 2008-2024
    s = p.groupby("market_id").agg(n_months=("month", "nunique"), n_products=("cpcv2", "nunique"),
                                   first_month=("month", "min"), last_month=("month", "max")).reset_index()
    m = mk[["market_id", "fnid", "market_name", "country_code", "country", "admin_1", "admin_2", "urban_rural",
            "lat_m", "lon_m"]].rename(columns={"lat_m": "latitude", "lon_m": "longitude"})
    m = m.merge(s, on="market_id", how="left")
    m["has_staple_prices"] = m.n_months.notna()
    m.to_parquet(OUT / "markets.parquet")
    print(f"markets.parquet: {len(m):,} markets ({m.has_staple_prices.sum():,} with staple retail prices "
          f"2008-2024; {m.latitude.notna().mean():.1%} with coordinates)", flush=True)


ISO2_3 = {"AF": "AFG", "AO": "AGO", "BF": "BFA", "BI": "BDI", "CD": "COD", "CF": "CAF", "CI": "CIV", "CM": "CMR",
          "CO": "COL", "DJ": "DJI", "ET": "ETH", "GT": "GTM", "HN": "HND", "HT": "HTI", "KE": "KEN", "LB": "LBN",
          "LK": "LKA", "LR": "LBR", "LS": "LSO", "MG": "MDG", "ML": "MLI", "MR": "MRT", "MW": "MWI", "MZ": "MOZ",
          "NE": "NER", "NG": "NGA", "NI": "NIC", "NP": "NPL", "PK": "PAK", "RW": "RWA", "SD": "SDN", "SL": "SLE",
          "SO": "SOM", "SS": "SSD", "SV": "SLV", "SY": "SYR", "TD": "TCD", "TG": "TGO", "UA": "UKR", "UG": "UGA",
          "VE": "VEN", "YE": "YEM", "ZM": "ZMB", "ZW": "ZWE", "MX": "MEX", "TZ": "TZA", "NA": "NAM", "ZA": "ZAF"}
WFP_KEEP = r"maize|sorghum|millet|wheat|rice|teff|cassava|gari|beans|cowpea|niebe"
WFP_DROP = r"bran|seed|oil|green|soy|bread|pasta|macaroni|spaghetti|noodle|starch|biscuit"


def wfp_markets():
    """WFP retail staple prices: market x year with coordinates (same product filter as FDW)."""
    rows = []
    for f in sorted((INP / "prices").glob("*.csv")):
        d = pd.read_csv(f, skiprows=[1], low_memory=False)
        d["iso3"] = f.stem.upper()
        rows.append(d)
    w = pd.concat(rows, ignore_index=True)
    c = w.commodity.str.lower()
    w = w[(w.pricetype.str.lower() == "retail") & c.str.contains(WFP_KEEP) & ~c.str.contains(WFP_DROP)
          & w.category.str.lower().isin(["cereals and tubers", "pulses and nuts"])]
    w["year"] = pd.to_datetime(w.date, errors="coerce").dt.year
    w = w.dropna(subset=["year", "price", "latitude", "longitude"])
    w = w[w.price > 0]
    w["mk"] = w.iso3 + "|" + w.market_id.astype(str)
    return w.groupby(["iso3", "mk", "year"]).agg(lat=("latitude", "first"), lon=("longitude", "first")).reset_index()


def coverage():
    p = pd.read_parquet(OUT / "prices.parquet")
    p["year"] = p.month.str[:4].astype(int)
    f = (p.dropna(subset=["latitude", "longitude"])
         .groupby(["country_code", "fnid", "year"]).agg(lat=("latitude", "first"), lon=("longitude", "first"))
         .reset_index())
    f["iso3"] = f.country_code.map(ISO2_3)
    f["mk"] = "FDW|" + f.fnid
    w = wfp_markets()
    w = w[(w.year >= 2008) & (w.year <= 2024)]
    # FEWS NET mapping areas classified in each year (current situation or forecast), centroids
    ip = pd.read_parquet(INP / "fewsnet" / "ipcphase.parquet", columns=["country_code", "fnid", "reporting_date"])
    ip["year"] = pd.to_datetime(ip.reporting_date).dt.year
    ay = ip.dropna(subset=["fnid", "year"]).drop_duplicates(["country_code", "fnid", "year"])
    u = gpd.read_file(INP / "fewsnet" / "units.gpkg")[["fnid", "geometry"]].drop_duplicates("fnid")
    u = u[u.geometry.notna()].to_crs(6933)
    u["geometry"] = u.geometry.centroid
    ay = ay[ay.fnid.isin(u.fnid)]
    print(f"area-years: {len(ay):,} ({ay.fnid.nunique():,} areas with geometry)", flush=True)
    xy = u.set_index("fnid").geometry

    def near(pts, year):
        """fnids (any country) with a market of `pts` (reporting in `year`) within 150 km."""
        q = pts[pts.year == year]
        a = ay[ay.year == year]
        if q.empty or a.empty:
            return set()
        g = gpd.GeoDataFrame(q, geometry=gpd.points_from_xy(q.lon, q.lat), crs=4326).to_crs(6933)
        c = gpd.GeoDataFrame(a[["fnid"]], geometry=xy.loc[a.fnid].values, crs=6933)
        j = gpd.sjoin_nearest(c, g[["mk", "geometry"]], max_distance=RADIUS_M)
        return set(j.fnid)

    out = []
    for y in range(2008, 2025):
        nf, nw = near(f, y), near(w, y)
        a = ay[ay.year == y]
        for cc, g in a.groupby("country_code"):
            s = set(g.fnid)
            i3 = ISO2_3.get(cc)
            out.append({"country_code": cc, "iso3": i3, "year": y, "n_areas": len(s),
                        "fdw_markets": f[(f.country_code == cc) & (f.year == y)].mk.nunique(),
                        "wfp_markets": w[(w.iso3 == i3) & (w.year == y)].mk.nunique(),
                        "share_fdw_150km": len(s & nf) / len(s), "share_wfp_150km": len(s & nw) / len(s),
                        "share_union_150km": len(s & (nf | nw)) / len(s)})
    t = pd.DataFrame(out).sort_values(["country_code", "year"])
    # countries with FDW or WFP markets but no classified areas that year are omitted (no denominator)
    t.round(4).to_csv(TAB / "price_coverage.csv", index=False)
    print(f"price_coverage.csv: {len(t)} country-years", flush=True)
    # pooled 2011-2024, area-year weighted
    q = t[(t.year >= 2011)].copy()
    for k in ["fdw", "wfp", "union"]:
        q[k] = q[f"share_{k}_150km"] * q.n_areas
    g = q.groupby("country_code").agg(area_years=("n_areas", "sum"), fdw=("fdw", "sum"), wfp=("wfp", "sum"),
                                      union=("union", "sum"), fdw_mk=("fdw_markets", "mean"),
                                      wfp_mk=("wfp_markets", "mean"))
    for k in ["fdw", "wfp", "union"]:
        g[k] = (g[k] / g.area_years).round(3)
    tot = q[["n_areas", "fdw", "wfp", "union"]].sum()
    g.loc["ALL"] = [tot.n_areas, round(tot.fdw / tot.n_areas, 3), round(tot.wfp / tot.n_areas, 3),
                    round(tot.union / tot.n_areas, 3), np.nan, np.nan]
    g = g.round({"fdw_mk": 1, "wfp_mk": 1})
    g.to_csv(TAB / "price_coverage_pooled.csv")
    print("\nPooled 2011-2024 (share of FEWS NET area-years with a reporting market within 150 km; "
          "mean markets reporting per year):\n" + g.sort_values("area_years", ascending=False).to_string())


if __name__ == "__main__":
    steps = sys.argv[1:] or ["fetch", "build", "coverage"]
    for s in steps:
        {"fetch": fetch, "build": build, "coverage": coverage}[s]()
