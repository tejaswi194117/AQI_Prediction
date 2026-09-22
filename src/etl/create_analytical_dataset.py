import pandas as pd


def create_analytical_dataset():

    input_file = "data/cleaned/pollution_weather_joined.csv"

    print(f"Reading: {input_file}")

    df = pd.read_csv(input_file)

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["hour"] = pd.to_datetime(
        df["hour"],
        errors="coerce"
    )

    # Create analysis date
    df["date"] = df["hour"].dt.date

    # --------------------------------------------------
    # 1. DAILY POLLUTION SUMMARY
    # --------------------------------------------------

    daily_pollution = (
        df.groupby(
            ["location_id", "date", "parameter", "unit"],
            as_index=False
        )
        .agg(
            average_value=("value", "mean"),
            minimum_value=("value", "min"),
            maximum_value=("value", "max"),
            measurement_count=("value", "count")
        )
    )

    # --------------------------------------------------
    # 2. DAILY WEATHER SUMMARY
    # --------------------------------------------------

    daily_weather = (
        df.groupby(
            ["date"],
            as_index=False
        )
        .agg(
            average_temperature=("temperature", "mean"),
            average_humidity=("humidity", "mean"),
            average_wind_speed=("wind_speed", "mean"),
            total_precipitation=("precipitation", "sum")
        )
    )

    # --------------------------------------------------
    # 3. CREATE POLLUTANT PIVOT
    # --------------------------------------------------

    pollution_pivot = daily_pollution.pivot_table(
        index=["location_id", "date"],
        columns="parameter",
        values="average_value",
        aggfunc="mean"
    ).reset_index()

    pollution_pivot.columns.name = None

    # Rename pollutants for clarity
    pollution_pivot = pollution_pivot.rename(
        columns={
            "pm25": "pm25",
            "pm10": "pm10",
            "o3": "o3",
            "no2": "no2",
            "so2": "so2",
            "co": "co"
        }
    )

    # Make sure expected pollutant columns exist
    expected_pollutants = [
        "pm25",
        "pm10",
        "o3",
        "no2",
        "so2",
        "co"
    ]

    for pollutant in expected_pollutants:
        if pollutant not in pollution_pivot.columns:
            pollution_pivot[pollutant] = None

    # --------------------------------------------------
    # 4. JOIN DAILY POLLUTION + WEATHER
    # --------------------------------------------------

    analytical = pollution_pivot.merge(
        daily_weather,
        on="date",
        how="left"
    )

    # --------------------------------------------------
    # 5. PM2.5 AQI CATEGORY
    # --------------------------------------------------

    def pm25_category(value):

        if pd.isna(value):
            return "Unknown"

        if value <= 30:
            return "Good"
        elif value <= 60:
            return "Satisfactory"
        elif value <= 90:
            return "Moderate"
        elif value <= 120:
            return "Poor"
        elif value <= 250:
            return "Very Poor"
        else:
            return "Severe"

    analytical["pm25_category"] = analytical["pm25"].apply(
        pm25_category
    )

    # --------------------------------------------------
    # 6. SORT DATA
    # --------------------------------------------------

    analytical = analytical.sort_values(
        ["date", "location_id"]
    )

    # --------------------------------------------------
    # 7. SAVE GOLD DATASET
    # --------------------------------------------------

    output_file = "data/gold/delhi_daily_air_quality.csv"

    analytical.to_csv(
        output_file,
        index=False
    )

    print("\nAnalytical dataset created successfully!")

    print("Records:", len(analytical))

    print("Saved to:")
    print(output_file)

    print("\nColumns:")
    print(list(analytical.columns))

    print("\nPreview:")
    print(analytical.head(10).to_string(index=False))

    print("\nAQI categories:")
    print(
        analytical["pm25_category"]
        .value_counts()
    )


if __name__ == "__main__":
    create_analytical_dataset()