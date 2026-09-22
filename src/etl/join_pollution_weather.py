import pandas as pd


def join_pollution_weather():

    print("Reading pollution data...")
    pollution = pd.read_csv(
        "data/staging/openaq_measurements.csv"
    )

    print("Reading weather data...")
    weather = pd.read_csv(
        "data/staging/weather_delhi.csv"
    )

    # Convert timestamps
    pollution["timestamp"] = pd.to_datetime(
        pollution["timestamp"],
        errors="coerce",
        utc=True
    )

    # Pollution timestamps are UTC.
    # Convert them to Indian Standard Time.
    pollution["timestamp"] = (
        pollution["timestamp"]
        .dt.tz_convert("Asia/Kolkata")
        .dt.tz_localize(None)
    )

    weather["timestamp"] = pd.to_datetime(
        weather["timestamp"],
        errors="coerce"
    )

    # Keep only the common analysis period
    start_date = pd.Timestamp("2025-02-18 00:00:00")
    end_date = pd.Timestamp("2025-02-21 23:00:00")

    pollution = pollution[
        (pollution["timestamp"] >= start_date) &
        (pollution["timestamp"] <= end_date)
    ].copy()

    # Round pollution measurements to the hour
    pollution["hour"] = pollution["timestamp"].dt.floor("h")

    weather["hour"] = weather["timestamp"].dt.floor("h")

    # Join pollution measurements with weather
    joined = pollution.merge(
        weather[
            [
                "hour",
                "temperature",
                "humidity",
                "wind_speed",
                "precipitation"
            ]
        ],
        on="hour",
        how="left"
    )

    # Remove rows where weather could not be matched
    matched = joined["temperature"].notna().sum()
    unmatched = joined["temperature"].isna().sum()

    print("\nJoin results:")
    print("Pollution records in analysis period:", len(pollution))
    print("Matched records:", matched)
    print("Unmatched records:", unmatched)

    # Save joined dataset
    output_file = "data/cleaned/pollution_weather_joined.csv"

    joined.to_csv(
        output_file,
        index=False
    )

    print(f"\nJoined dataset saved to: {output_file}")
    print("Total joined records:", len(joined))

    print("\nPreview:")
    print(joined.head())


if __name__ == "__main__":
    join_pollution_weather()