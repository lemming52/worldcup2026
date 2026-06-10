"""Fetch historical daily relative humidity for all WC 2026 capital cities.

Uses the Open-Meteo archive API (free, no auth) to retrieve mean relative
humidity at 2m for June 11–27, 2025 — the same calendar dates as the 2026
tournament, one year prior.

Run from project root:
    python scripts/fetch_humidity.py
"""

import time
import urllib.request
import json
from pathlib import Path
import pandas as pd

_DATA_DIR = Path(__file__).parent.parent / "data"

START_DATE = "2025-06-11"
END_DATE   = "2025-06-27"


def fetch_humidity(lat: float, lon: float) -> dict[str, float]:
    """Return {date_str: humidity} for the given coordinates."""
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={START_DATE}&end_date={END_DATE}"
        "&daily=relative_humidity_2m_mean"
        "&timezone=auto"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "worldcup2026-humidity/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    dates   = data["daily"]["time"]
    values  = data["daily"]["relative_humidity_2m_mean"]
    return dict(zip(dates, values))


def build() -> pd.DataFrame:
    capitals_df = pd.read_csv(_DATA_DIR / "capitals.csv")
    rows = []
    for _, row in capitals_df.iterrows():
        capital = str(row["capital"])
        lat, lon = float(row["latitude"]), float(row["longitude"])
        print(f"  Fetching {capital} ({lat:.2f}, {lon:.2f})...")
        try:
            humidity_by_date = fetch_humidity(lat, lon)
            for date, humidity in humidity_by_date.items():
                rows.append({"capital": capital, "date": date, "humidity": humidity})
        except Exception as e:
            print(f"    WARNING: failed for {capital}: {e}")
        time.sleep(0.1)  # be polite to the API

    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(f"Fetching humidity data for {START_DATE} → {END_DATE} (2025)...")
    df = build()
    out = _DATA_DIR / "humidity_2025.csv"
    df.to_csv(out, index=False)
    n_capitals = df["capital"].nunique()
    n_rows = len(df)
    print(f"Written {n_rows} rows ({n_capitals} capitals) to {out}")
    missing = df[df["humidity"].isna()]
    if not missing.empty:
        print(f"WARNING: {len(missing)} missing values")
