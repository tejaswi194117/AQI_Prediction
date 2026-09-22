import pandas as pd
import json
import glob
import os


CITY_NAME = os.getenv("AQI_CITY", "Delhi")
CITY_LATITUDE = float(os.getenv("AQI_LATITUDE", "28.6139"))
CITY_LONGITUDE = float(os.getenv("AQI_LONGITUDE", "77.2090"))


def get_latest_file():
    files = glob.glob("data/raw/weather_delhi_*.json")

    if not files:
        raise FileNotFoundError("No Delhi weather files found.")

    return max(files, key=os.path.getmtime)


def clean_weather():

    input_file = get_latest_file()

    print(f"Reading: {input_file}")

    with open(input_file, "r") as f:
        data = json.load(f)

    hourly = data["hourly"]

    df = pd.DataFrame({
        "timestamp": hourly["time"],
        "temperature": hourly["temperature_2m"],
        "humidity": hourly["relative_humidity_2m"],
        "wind_speed": hourly["wind_speed_10m"],
        "precipitation": hourly["precipitation"]
    })

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # Numeric conversion
    numeric_columns = [
        "temperature",
        "humidity",
        "wind_speed",
        "precipitation"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Add location information
    df["city"] = CITY_NAME
    df["latitude"] = CITY_LATITUDE
    df["longitude"] = CITY_LONGITUDE
    df["source"] = "Open-Meteo"

    # Remove invalid records
    df = df.dropna(
        subset=[
            "timestamp",
            "temperature",
            "humidity",
            "wind_speed",
            "precipitation"
        ]
    )

    # Data-quality validation
    df = df[
        (df["humidity"] >= 0) &
        (df["humidity"] <= 100) &
        (df["wind_speed"] >= 0) &
        (df["precipitation"] >= 0)
    ]

    # Remove duplicates
    df = df.drop_duplicates(
        subset=["timestamp"]
    )

    # Sort
    df = df.sort_values("timestamp")

    # Reorder columns
    df = df[
        [
            "city",
            "latitude",
            "longitude",
            "timestamp",
            "temperature",
            "humidity",
            "wind_speed",
            "precipitation",
            "source"
        ]
    ]

    output_file = "data/staging/weather_delhi.csv"

    df.to_csv(
        output_file,
        index=False
    )

    print(f"\nCleaned weather records: {len(df)}")
    print(f"Saved to: {output_file}")

    print("\nWeather data preview:")
    print(df.head())

    print("\nTimestamp range:")
    print("From:", df["timestamp"].min())
    print("To:", df["timestamp"].max())


if __name__ == "__main__":
    clean_weather()
