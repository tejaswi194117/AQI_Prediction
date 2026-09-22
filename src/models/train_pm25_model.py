"""Train and evaluate baseline next-day PM2.5 forecasting models."""

import json
import os
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/gold/ml_aqi_features.csv")
MODEL_FILE = Path("models/pm25_next_day_model.joblib")
METRICS_FILE = Path("models/pm25_next_day_metrics.json")
TARGET = "target_pm25_next_day"
MIN_TRAIN_ROWS = int(os.getenv("MIN_TRAIN_ROWS", "100"))


def time_based_split(data, test_fraction=0.2):
    """Split whole dates chronologically; never shuffle future rows into training."""
    df = data.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    dates = df["date"].drop_duplicates().tolist()
    if len(dates) < 2:
        raise ValueError("At least two distinct dates are required for a time split.")

    split_index = max(1, int(len(dates) * (1 - test_fraction)))
    split_index = min(split_index, len(dates) - 1)
    cutoff = dates[split_index]
    return df[df["date"] < cutoff].copy(), df[df["date"] >= cutoff].copy()


def select_feature_columns(data):
    excluded = {"date", TARGET, "target_pm25_category", "pm25_category"}
    return [
        column
        for column in data.select_dtypes(include="number").columns
        if column not in excluded
    ]


def train_models(train_x, train_y, test_x, test_y):
    """Fit a mean baseline, linear regression, and random forest consistently."""
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.pipeline import Pipeline

    models = {
        "mean_baseline": Pipeline(
            [("imputer", SimpleImputer(strategy="median")), ("model", DummyRegressor())]
        ),
        "linear_regression": Pipeline(
            [("imputer", SimpleImputer(strategy="median")), ("model", LinearRegression())]
        ),
        "random_forest": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=300,
                        min_samples_leaf=2,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }
    results = {}
    fitted_models = {}
    for name, model in models.items():
        model.fit(train_x, train_y)
        prediction = model.predict(test_x)
        results[name] = {
            "mae": float(mean_absolute_error(test_y, prediction)),
            "rmse": float(mean_squared_error(test_y, prediction) ** 0.5),
            "r2": float(r2_score(test_y, prediction)),
        }
        fitted_models[name] = model
    return fitted_models, results


def train():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Feature dataset not found: {INPUT_FILE}")

    data = pd.read_csv(INPUT_FILE)
    data = data.dropna(subset=[TARGET])
    if len(data) < MIN_TRAIN_ROWS:
        raise ValueError(
            f"Need at least {MIN_TRAIN_ROWS} rows with a next-day target; found {len(data)}. "
            "Run a larger historical backfill before training."
        )
    feature_columns = select_feature_columns(data)
    if not feature_columns:
        raise ValueError("No numeric training features are available.")

    train_data, test_data = time_based_split(data)
    if len(train_data) < MIN_TRAIN_ROWS:
        raise ValueError(
            f"Need at least {MIN_TRAIN_ROWS} training rows; found {len(train_data)}. "
            "Run a larger historical backfill before training."
        )

    fitted_models, results = train_models(
        train_data[feature_columns],
        train_data[TARGET],
        test_data[feature_columns],
        test_data[TARGET],
    )
    best_name = min(results, key=lambda name: results[name]["mae"])

    from joblib import dump

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    dump(
        {
            "model": fitted_models[best_name],
            "feature_columns": feature_columns,
            "target": TARGET,
            "model_name": best_name,
        },
        MODEL_FILE,
    )
    metadata = {
        "best_model": best_name,
        "metrics": results,
        "train_rows": len(train_data),
        "test_rows": len(test_data),
        "feature_columns": feature_columns,
        "train_end_date": str(train_data["date"].max().date()),
        "test_start_date": str(test_data["date"].min().date()),
    }
    METRICS_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Best model: {best_name}")
    print(f"Test MAE: {results[best_name]['mae']:.2f}")
    print(f"Saved model: {MODEL_FILE}")
    print(f"Saved metrics: {METRICS_FILE}")


if __name__ == "__main__":
    train()
