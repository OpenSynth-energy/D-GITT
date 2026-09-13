"""
Fetch physical cross-border flows (ENTSO-E documentType A11) between France
and a set of neighbouring bidding zones, for a fixed list of French local
timestamps.

Output CSV columns match the target format:
    timestamp_fr, datetime_utc, country,
    export_fr_to_country, import_country_to_fr, net_fr_to_country
"""

import time
import os
import pandas as pd
from entsoe import EntsoePandasClient

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_TOKEN = "YOUR-API-KEY"

# entsoe-py Area codes for France's neighbours (display label -> Area code)
COUNTRIES = {
    "BE": "BE",
    "CH": "CH",
    "DE-LU": "DE_LU",
    "ES": "ES",
    "GB": "GB",
    "IT-North": "IT_NORD",
}

FR = "FR"
PARIS_TZ = "Europe/Paris"

TIMESTAMPS = [
    
]

OUTPUT_BASE_DIR = "7K-Challenge/7K-baseline_reconstruction/data/entsoe"
REQUEST_PAUSE_SECONDS = 1  # be gentle with the API between calls
RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 5

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_hourly_value(client, code_from, code_to, hour_start_utc):
    """
    Query physical cross-border flow (A11) for a single hour and return a
    single float. Returns None if nothing was returned (e.g. no flow /
    no data published for that hour).
    """
    hour_end_utc = hour_start_utc + pd.Timedelta(hours=1)
 
    last_err = None
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            series = client.query_crossborder_flows(
                code_from, code_to, start=hour_start_utc, end=hour_end_utc
            )
            if series is None or series.empty:
                return 0.0
            # The series is indexed by (sub-hourly) timestamps within the
            # window; average in case resolution is finer than 1h, and to
            # be robust to an index that doesn't align exactly on the hour.
            return float(series.mean())
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY_SECONDS)
    print(f"  [warning] {code_from}->{code_to} at {hour_start_utc}: {last_err}")
    return None
 
 
def build_output_path(ts_fr):
    """
    data/entsoe/<year>/entsoe_flows_<YYYY-MM-DD>T<HHMM>.csv
    based on the French local timestamp (ts_fr).
    """
    year_dir = os.path.join(OUTPUT_BASE_DIR, str(ts_fr.year))
    os.makedirs(year_dir, exist_ok=True)
    filename = f"entsoe_flows_{ts_fr.strftime('%Y-%m-%d')}T{ts_fr.strftime('%H%M')}.csv"
    return os.path.join(year_dir, filename)
 
 
def main():
    client = EntsoePandasClient(api_key=API_TOKEN)
 
    written_paths = []
    for ts_str in TIMESTAMPS:
        ts_fr = pd.Timestamp(ts_str, tz=PARIS_TZ)
        ts_utc = ts_fr.tz_convert("UTC")
 
        print(f"Timestamp {ts_fr} (FR) / {ts_utc} (UTC)")
 
        rows = []
        for label, area_code in COUNTRIES.items():
            export_val = get_hourly_value(client, FR, area_code, ts_utc)
            time.sleep(REQUEST_PAUSE_SECONDS)
 
            import_val = get_hourly_value(client, area_code, FR, ts_utc)
            time.sleep(REQUEST_PAUSE_SECONDS)
 
            net_val = (
                export_val - import_val
                if export_val is not None and import_val is not None
                else None
            )
 
            rows.append(
                {
                    "timestamp_fr": ts_fr.strftime("%Y-%m-%d %H:%M:%S"),
                    "datetime_utc": ts_utc.strftime("%Y-%m-%d %H:%M:%S"),
                    "country": label,
                    "export_fr_to_country": export_val,
                    "import_country_to_fr": import_val,
                    "net_fr_to_country": net_val,
                }
            )
            print(f"  {label}: export={export_val} import={import_val} net={net_val}")
 
        out_path = build_output_path(ts_fr)
        pd.DataFrame(rows).to_csv(out_path, index=False)
        written_paths.append(out_path)
        print(f"  -> saved {out_path}")
 
    print(f"\nSaved {len(written_paths)} files:")
    for p in written_paths:
        print(f"  - {p}")
 
 
if __name__ == "__main__":
    main()