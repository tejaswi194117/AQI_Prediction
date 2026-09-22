import json
import os
import pandas as pd
from pathlib import Path


RAW_DIR = Path("data/raw")
STAGING_DIR = Path("data/staging")

STAGING_DIR.mkdir(parents=True, exist_ok=True)

# Delhi is the project's analysis area. These settings can be overridden in
# `.env` or the Airflow environment for a different city/backfill strategy.
CITY_NAME = os.getenv("AQI_CITY", "Delhi")
CITY_LATITUDE = float(os.getenv("AQI_LATITUDE", "28.6139"))
CITY_LONGITUDE = float(os.getenv("AQI_LONGITUDE", "77.2090"))
RADIUS_DEGREES = float(os.getenv("AQI_RADIUS_DEGREES", "0.50"))


def find_latest_openaq_file():
    # Only select the main OpenAQ locations files.
    # This excludes:
    # openaq_sensors_*.json
    # openaq_measurements_*.json
    files = sorted(RAW_DIR.glob("openaq_20*.json"))

    if not files:
        raise FileNotFoundError(
            "No OpenAQ location raw files found."
        )

    return files[-1]


def load_openaq_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "results" not in data:
        raise ValueError(
            f"Invalid OpenAQ locations file: {file_path}"
        )

    return data["results"]


def transform_data(records):
    rows = []

    for record in records:
        coordinates = record.get("coordinates") or {}

        rows.append({
            "station_name": record.get("name"),
            "city": record.get("locality"),
            "country": record.get("country", {}).get("code"),
            "latitude": coordinates.get("latitude"),
            "longitude": coordinates.get("longitude"),
            "station_id": record.get("id"),
            "source": "OpenAQ"
        })

    df = pd.DataFrame(rows)

    return df


def clean_data(df):
    print("Initial records:", len(df))

    # Remove duplicate stations
    df = df.drop_duplicates(
        subset=["station_id"]
    )

    # Remove records without coordinates
    df = df.dropna(
        subset=["latitude", "longitude"]
    )

    # Validate latitude
    df = df[
        df["latitude"].between(-90, 90)
    ]

    # Validate longitude
    df = df[
        df["longitude"].between(-180, 180)
    ]

    # OpenAQ's locality field is not consistently populated. Use a bounding
    # box around the configured city so stations really match the weather data.
    df = df[
        df["latitude"].between(
            CITY_LATITUDE - RADIUS_DEGREES,
            CITY_LATITUDE + RADIUS_DEGREES,
        )
        & df["longitude"].between(
            CITY_LONGITUDE - RADIUS_DEGREES,
            CITY_LONGITUDE + RADIUS_DEGREES,
        )
    ].copy()

    df["city"] = CITY_NAME

    print("Clean records:", len(df))

    return df


def main():

    # Find latest OpenAQ locations raw file
    raw_file = find_latest_openaq_file()

    print("Reading:", raw_file)

    # Load raw data
    records = load_openaq_data(raw_file)

    print("Records loaded:", len(records))

    # Transform data
    df = transform_data(records)

    # Clean data
    df = clean_data(df)

    # Save staging data
    output_file = STAGING_DIR / "openaq_stations.csv"

    df.to_csv(
        output_file,
        index=False
    )

    print("Staging data saved to:", output_file)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 records:")
    print(df.head())


if __name__ == "__main__":
    main()
