"""Build leakage-safe daily features for next-day PM2.5 forecasting."""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/gold/delhi_daily_air_quality.csv")
OUTPUT_FILE = Path("data/gold/ml_aqi_features.csv")


def pm25_category(value):
    if pd.isna(value):
        return "Unknown"
    if value <= 30:
        return "Good"
    if value <= 60:
        return "Satisfactory"
    if value <= 90:
        return "Moderate"
    if value <= 120:
        return "Poor"
    if value <= 250:
        return "Very Poor"
    return "Severe"


def build_features(gold_data):
    """Return one ML row per observed location/date.

    Each location is expanded to a daily index before shifts and rolling
    calculations. This prevents a missing day from being incorrectly treated
    as yesterday, and all historical PM2.5 features are shifted first to
    prevent target leakage.
    """
    required_columns = {"location_id", "date", "pm25"}
    missing_columns = required_columns.difference(gold_data.columns)
    if missing_columns:
        raise ValueError(f"Gold dataset is missing columns: {sorted(missing_columns)}")

    df = gold_data.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["location_id", "date"]).sort_values(
        ["location_id", "date"]
    )
    df = df.drop_duplicates(subset=["location_id", "date"], keep="last")

    feature_frames = []
    for location_id, group in df.groupby("location_id", sort=False):
        group = group.set_index("date").sort_index()
        full_dates = pd.date_range(group.index.min(), group.index.max(), freq="D")
        expanded = group.reindex(full_dates)
        observed = expanded["location_id"].notna()
        expanded["location_id"] = location_id

        pm25 = expanded["pm25"]
        expanded["pm25_lag_1d"] = pm25.shift(1)
        expanded["pm25_lag_3d"] = pm25.shift(3)
        expanded["pm25_lag_7d"] = pm25.shift(7)
        expanded["pm25_rolling_mean_3d"] = pm25.shift(1).rolling(3, min_periods=3).mean()
        expanded["pm25_rolling_mean_7d"] = pm25.shift(1).rolling(7, min_periods=7).mean()
        expanded["target_pm25_next_day"] = pm25.shift(-1)

        # Keep only source dates that actually existed in the gold dataset.
        expanded["is_observed_date"] = observed
        feature_frames.append(expanded.reset_index(names="date"))

    features = pd.concat(feature_frames, ignore_index=True)
    features = features[features["is_observed_date"]].drop(columns="is_observed_date")
    features["day_of_week"] = features["date"].dt.dayofweek
    features["month"] = features["date"].dt.month
    features["day_of_year"] = features["date"].dt.dayofyear
    features["target_pm25_category"] = features["target_pm25_next_day"].map(
        pm25_category
    )

    return features.sort_values(["location_id", "date"]).reset_index(drop=True)


def create_training_dataset():
    print(f"Reading gold dataset: {INPUT_FILE}")
    gold_data = pd.read_csv(INPUT_FILE)
    features = build_features(gold_data)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUTPUT_FILE, index=False)

    trainable_rows = features.dropna(
        subset=["pm25_lag_1d", "target_pm25_next_day"]
    )
    print(f"ML feature rows: {len(features)}")
    print(f"Trainable next-day PM2.5 rows: {len(trainable_rows)}")
    print(f"Saved to: {OUTPUT_FILE}")

    if len(trainable_rows) < 100:
        print(
            "WARNING: Fewer than 100 trainable rows. Collect more historical "
            "daily data before training a model."
        )


if __name__ == "__main__":
    create_training_dataset()
