import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")
MAX_STATIONS = int(os.getenv("OPENAQ_MAX_STATIONS", "20"))

BASE_URL = "https://api.openaq.org/v3/locations"


def fetch_sensors():

    if not API_KEY:
        print("ERROR: OPENAQ_API_KEY not found in .env")
        return

    print("Starting OpenAQ sensor ingestion...")

    headers = {
        "X-API-Key": API_KEY
    }

    # Stations have already been geographically filtered in clean_openaq.py.
    import pandas as pd

    locations_file = Path("data/staging/openaq_stations.csv")

    locations = pd.read_csv(locations_file)

    location_ids = (
        locations["station_id"].dropna().astype(int).head(MAX_STATIONS).tolist()
    )

    all_sensors = []

    for location_id in location_ids:

        url = f"{BASE_URL}/{location_id}/sensors"

        try:

            response = requests.get(
                url,
                headers=headers,
                params={
                    "limit": 100
                },
                timeout=30
            )

            print(
                f"Location {location_id}: HTTP {response.status_code}"
            )

            response.raise_for_status()

            data = response.json()

            sensors = data.get("results", [])

            for sensor in sensors:

                sensor["location_id"] = location_id

                all_sensors.append(sensor)

        except requests.exceptions.RequestException as error:

            print(
                f"Location {location_id} failed:",
                error
            )

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = raw_dir / f"openaq_sensors_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as file:

        json.dump(
            all_sensors,
            file,
            indent=2
        )

    print()
    print("Raw sensor data saved to:", output_file)
    print("Total sensors collected:", len(all_sensors))


if __name__ == "__main__":
    fetch_sensors()
