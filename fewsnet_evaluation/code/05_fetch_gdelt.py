"""Monthly news coverage of hunger in FEWS NET countries, from the GDELT
DOC 2.0 API (online news, January 2017 onward).

For each country we count articles that mention the country name together
with a hunger term, separately for all sources and for US-based sources.
The API also returns the total number of articles GDELT monitored that day
("norm"), so coverage can be expressed as a share of all news.

GDELT asks for at most one request every five seconds. Coverage before 2017
would need another source (for example the New York Times Article Search API
or the Vanderbilt Television News Archive used by Eisensee and Stromberg 2007).

Output: input/news/gdelt_monthly.csv
"""
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "input" / "news"
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)
API = "https://api.gdeltproject.org/api/v2/doc/doc"

COUNTRIES = {
    "AF": "Afghanistan", "AO": "Angola", "BF": "Burkina Faso", "BI": "Burundi",
    "CD": "Congo", "CF": "Central African Republic", "CM": "Cameroon", "DJ": "Djibouti",
    "ET": "Ethiopia", "GT": "Guatemala", "HN": "Honduras", "HT": "Haiti", "KE": "Kenya",
    "LS": "Lesotho", "MG": "Madagascar", "ML": "Mali", "MR": "Mauritania",
    "MW": "Malawi", "MZ": "Mozambique", "NE": "Niger", "NG": "Nigeria",
    "NI": "Nicaragua", "RW": "Rwanda", "SD": "Sudan", "SN": "Senegal", "SO": "Somalia",
    "SS": "South Sudan", "SV": "El Salvador", "TD": "Chad", "TZ": "Tanzania",
    "UG": "Uganda", "YE": "Yemen", "ZM": "Zambia", "ZW": "Zimbabwe",
    "PS": "Gaza", "MM": "Myanmar", "SY": "Syria", "UA": "Ukraine", "VE": "Venezuela",
}
TERMS = '(famine OR hunger OR starvation OR "food crisis" OR "food insecurity" OR drought)'


def query(q: str, tag: str) -> pd.DataFrame:
    path = RAW / f"{tag}.csv"
    if path.exists():
        return pd.read_csv(path)
    params = {"query": q, "mode": "timelinevolraw", "format": "json",
              "startdatetime": "20170101000000",
              "enddatetime": pd.Timestamp.today().strftime("%Y%m%d000000")}
    # GDELT throttles by IP well beyond its stated one-per-5-seconds rule once
    # it sees long-range queries, so pace generously and back off hard.
    for attempt in range(4):
        try:
            r = requests.get(API, params=params, timeout=180)
        except requests.RequestException as e:
            print(f"  network error for {tag}: {type(e).__name__}")
            time.sleep(60 * 2 ** min(attempt, 3))
            continue
        time.sleep(15)
        if r.status_code == 200 and r.text.startswith("{"):
            data = r.json()["timeline"][0]["data"]
            df = pd.DataFrame(data)
            df.to_csv(path, index=False)
            return df
        time.sleep(60 * 2 ** min(attempt, 3))
    print(f"  giving up on {tag} for now; re-run later to fill it")
    return None


def main():
    frames = []
    for iso2, name in COUNTRIES.items():
        for scope, extra in [("all", ""), ("us", " sourcecountry:US")]:
            df = query(f'"{name}" {TERMS}{extra}', f"{iso2}_{scope}")
            if df is None:
                continue
            df["iso2"], df["scope"] = iso2, scope
            frames.append(df)
            print(iso2, scope, int(df["value"].sum()))
    d = pd.concat(frames)
    d["month"] = pd.to_datetime(d["date"].str[:8]).dt.to_period("M").astype(str)
    m = d.groupby(["iso2", "scope", "month"]).agg(articles=("value", "sum"),
                                                  all_articles=("norm", "sum")).reset_index()
    m.to_csv(OUT / "gdelt_monthly.csv", index=False)


if __name__ == "__main__":
    main()
