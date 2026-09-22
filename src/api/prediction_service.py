"""Model-independent utilities used by the AQI prediction API."""

import math

import pandas as pd


def pm25_category(value):
    if value is None or math.isnan(value):
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


def prediction_from_features(model_artifact, features):
    """Return a prediction using exactly the columns saved with the model."""
    feature_columns = model_artifact["feature_columns"]
    feature_row = pd.DataFrame(
        [{column: features.get(column) for column in feature_columns}]
    )
    value = max(0.0, float(model_artifact["model"].predict(feature_row)[0]))
    return {
        "model_name": model_artifact["model_name"],
        "predicted_pm25_next_day": round(value, 2),
        "predicted_aqi_category": pm25_category(value),
        "missing_features": [
            column for column in feature_columns if features.get(column) is None
        ],
    }
