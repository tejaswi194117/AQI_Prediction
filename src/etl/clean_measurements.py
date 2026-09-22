import pandas as pd
import json
import glob
import os


def get_latest_file():
    files = glob.glob("data/raw/openaq_measurements_*.json")

    if not files:
        raise FileNotFoundError("No OpenAQ measurement files found.")

    return max(files, key=os.path.getmtime)


def clean_measurements():

    input_file = get_latest_file()

    print(f"Reading: {input_file}")

    with open(input_file, "r") as f:
        data = json.load(f)

    print(f"Raw measurements: {len(data)}")

    records = []

    for item in data:

        parameter = item.get("parameter", {})
        period = item.get("period", {})
        datetime_from = period.get("datetimeFrom", {})

        records.append({
            "location_id": item.get("location_id"),
            "sensor_id": item.get("sensor_id"),
            "parameter": parameter.get("name"),
            "value": item.get("value"),
            "unit": parameter.get("units"),
            "timestamp": datetime_from.get("utc")
        })

    df = pd.DataFrame(records)

    # Convert numeric columns
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True
    )

    # Remove records missing essential information
    df = df.dropna(
        subset=[
            "location_id",
            "sensor_id",
            "parameter",
            "value",
            "timestamp"
        ]
    )

    # Remove invalid pollutant values
    df = df[df["value"] >= 0]

    # Remove duplicate measurements
    df = df.drop_duplicates(
        subset=[
            "sensor_id",
            "timestamp"
        ]
    )

    # Sort
    df = df.sort_values(
        ["location_id", "sensor_id", "timestamp"]
    )

    # Save cleaned data
    output_file = "data/staging/openaq_measurements.csv"

    df.to_csv(output_file, index=False)

    print(f"Cleaned measurements: {len(df)}")
    print(f"Saved to: {output_file}")

    print("\nPollutants:")
    print(df["parameter"].value_counts())

    print("\nTimestamp range:")
    print("From:", df["timestamp"].min())
    print("To:", df["timestamp"].max())


if __name__ == "__main__":
    clean_measurements()