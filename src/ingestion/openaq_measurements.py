import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

BASE_URL = "https://api.openaq.org/v3/sensors"


def fetch_measurements():

    if not API_KEY:
        print("ERROR: OPENAQ_API_KEY not found in .env")
        return

    # Find latest sensor file
    raw_dir = Path("data/raw")

    sensor_files = sorted(
        raw_dir.glob("openaq_sensors_*.json")
    )

    if not sensor_files:
        print("ERROR: No sensor file found.")
        return

    sensor_file = sensor_files[-1]

    print("Reading sensors from:", sensor_file)

    with open(sensor_file, "r", encoding="utf-8") as file:
        sensors = json.load(file)

    print("Total sensors:", len(sensors))

    headers = {
        "X-API-Key": API_KEY
    }

    all_measurements = []

    # We will initially collect a small amount of data
    # to verify the pipeline.
    for sensor in sensors:

        sensor_id = sensor.get("id")

        if not sensor_id:
            continue

        url = f"{BASE_URL}/{sensor_id}/measurements"

        try:

            response = requests.get(
                url,
                headers=headers,
                params={
                    "limit": 100
                },
                timeout=30
            )

            if response.status_code != 200:
                print(
                    f"Sensor {sensor_id}: HTTP "
                    f"{response.status_code}"
                )
                continue

            data = response.json()

            measurements = data.get("results", [])

            # Add sensor metadata to every measurement
            for measurement in measurements:

                measurement["sensor_id"] = sensor_id
                measurement["parameter_name"] = (
                    sensor.get("parameter", {}).get("name")
                )
                measurement["parameter_units"] = (
                    sensor.get("parameter", {}).get("units")
                )
                measurement["location_id"] = (
                    sensor.get("location_id")
                )

                all_measurements.append(measurement)

            print(
                f"Sensor {sensor_id}: "
                f"{len(measurements)} measurements"
            )

        except requests.exceptions.RequestException as error:

            print(
                f"Sensor {sensor_id} failed:",
                error
            )

    # Save raw measurements
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_file = (
        raw_dir /
        f"openaq_measurements_{timestamp}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_measurements,
            file,
            indent=2
        )

    print()
    print(
        "Raw measurement data saved to:",
        output_file
    )

    print(
        "Total measurements collected:",
        len(all_measurements)
    )


if __name__ == "__main__":
    fetch_measurements()