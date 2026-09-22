import pandas as pd
import os


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

    # Join only the time period covered by both inputs. Optional environment
    # dates support reproducible historical backfills without source edits.
    start_date = max(pollution["timestamp"].min(), weather["timestamp"].min())
    end_date = min(pollution["timestamp"].max(), weather["timestamp"].max())

    configured_start = os.getenv("ANALYSIS_START_DATE")
    configured_end = os.getenv("ANALYSIS_END_DATE")
    if configured_start:
        start_date = max(start_date, pd.Timestamp(configured_start))
    if configured_end:
        end_date = min(end_date, pd.Timestamp(configured_end))

    if start_date > end_date:
        raise ValueError(
            "Pollution and weather files have no overlapping timestamps. "
            "Run the ingestions for the same date range."
        )

    print(f"Common analysis period: {start_date} to {end_date}")

    pollution = pollution[
        (pollution["timestamp"] >= start_date) &
        (pollution["timestamp"] <= end_date)
    ].copy()

    aggregation = pollution.get("aggregation", pd.Series("hours", index=pollution.index))
    if aggregation.eq("days").all():
        # A daily OpenAQ value should receive a complete daily weather
        # summary, rather than only the weather at midnight.
        pollution["hour"] = pollution["timestamp"].dt.normalize()
        weather["date"] = weather["timestamp"].dt.normalize()
        daily_weather = (
            weather.groupby("date", as_index=False)
            .agg(
                temperature=("temperature", "mean"),
                humidity=("humidity", "mean"),
                wind_speed=("wind_speed", "mean"),
                precipitation=("precipitation", "sum"),
            )
            .rename(columns={"date": "hour"})
        )
        joined = pollution.merge(daily_weather, on="hour", how="left")
    elif aggregation.eq("hours").all():
        pollution["hour"] = pollution["timestamp"].dt.floor("h")
        weather["hour"] = weather["timestamp"].dt.floor("h")
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
    else:
        raise ValueError(
            "Cannot join mixed OpenAQ aggregation granularities in one run."
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
