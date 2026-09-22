"""Fetch a bounded, paginated OpenAQ measurement history for staged sensors."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")
BASE_URL = "https://api.openaq.org/v3/sensors"
GRANULARITY = os.getenv("OPENAQ_GRANULARITY", "days").lower()
PAGE_SIZE = min(int(os.getenv("OPENAQ_PAGE_SIZE", "1000")), 1000)


def history_range():
    """Return an inclusive, UTC-bounded range for a reproducible backfill."""
    today = datetime.now(timezone.utc).date()
    history_days = int(os.getenv("AQI_HISTORY_DAYS", "30"))
    start = os.getenv("OPENAQ_HISTORY_START_DATE")
    end = os.getenv("OPENAQ_HISTORY_END_DATE")

    start_date = pd.Timestamp(start).date() if start else today - timedelta(days=history_days)
    end_date = pd.Timestamp(end).date() if end else today - timedelta(days=1)
    if start_date > end_date:
        raise ValueError("OPENAQ history start date must be on or before its end date.")

    return start_date.isoformat(), f"{end_date.isoformat()}T23:59:59Z"


def fetch_sensor_history(sensor, headers, request_get=requests.get):
    """Return every page for one sensor within the configured date range."""
    sensor_id = sensor.get("id")
    if not sensor_id:
        return []
    if GRANULARITY not in {"hours", "days"}:
        raise ValueError("OPENAQ_GRANULARITY must be either 'hours' or 'days'.")

    datetime_from, datetime_to = history_range()
    endpoint = f"{BASE_URL}/{sensor_id}/{GRANULARITY}"
    page = 1
    results = []

    while True:
        response = request_get(
            endpoint,
            headers=headers,
            params={
                "datetime_from": datetime_from,
                "datetime_to": datetime_to,
                "limit": PAGE_SIZE,
                "page": page,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        page_results = payload.get("results", [])

        for measurement in page_results:
            measurement["sensor_id"] = sensor_id
            measurement["location_id"] = sensor.get("location_id")
            measurement["aggregation"] = GRANULARITY
            results.append(measurement)

        metadata = payload.get("meta", {})
        found = metadata.get("found")
        print(f"Sensor {sensor_id}, page {page}: {len(page_results)} records")

        if not page_results or (found is not None and page * PAGE_SIZE >= int(found)):
            break
        if len(page_results) < PAGE_SIZE:
            break
        page += 1

    return results


def fetch_measurements():
    if not API_KEY:
        print("ERROR: OPENAQ_API_KEY not found in .env")
        return

    raw_dir = Path("data/raw")
    sensor_files = sorted(raw_dir.glob("openaq_sensors_*.json"))
    if not sensor_files:
        print("ERROR: No sensor file found.")
        return

    sensor_file = sensor_files[-1]
    print(f"Reading sensors from: {sensor_file}")
    with open(sensor_file, "r", encoding="utf-8") as file:
        sensors = json.load(file)

    datetime_from, datetime_to = history_range()
    print(f"Fetching {GRANULARITY} data from {datetime_from} to {datetime_to}")
    headers = {"X-API-Key": API_KEY}
    all_measurements = []

    for sensor in sensors:
        try:
            all_measurements.extend(fetch_sensor_history(sensor, headers))
        except requests.exceptions.RequestException as error:
            print(f"Sensor {sensor.get('id')} failed: {error}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = raw_dir / f"openaq_measurements_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(all_measurements, file, indent=2)

    print(f"Raw measurement data saved to: {output_file}")
    print(f"Total {GRANULARITY} records collected: {len(all_measurements)}")


if __name__ == "__main__":
    fetch_measurements()
