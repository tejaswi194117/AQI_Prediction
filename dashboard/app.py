"""Streamlit dashboard for observed pollution trends and PM2.5 forecasts."""

import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


sys.path.insert(0, os.path.dirname(__file__))
from api_client import get_json, predict


ROOT = Path(__file__).resolve().parents[1]
GOLD_FILE = ROOT / "data" / "gold" / "delhi_daily_air_quality.csv"
API_BASE_URL = os.getenv("AQI_API_URL", "http://127.0.0.1:8000")
POLLUTANTS = ["pm25", "pm10", "no2", "so2", "o3", "co"]
WEATHER_FIELDS = {
    "average_temperature": "Temperature (°C)",
    "average_humidity": "Humidity (%)",
    "average_wind_speed": "Wind speed (m/s)",
    "total_precipitation": "Precipitation (mm)",
}


st.set_page_config(page_title="Delhi Air Quality", page_icon="🌫️", layout="wide")
st.title("Delhi Air Quality")
st.caption("Historical station observations and next-day PM2.5 estimates.")


@st.cache_data
def load_gold(path, modified):
    data = pd.read_csv(path)
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    return data.dropna(subset=["date"])


if not GOLD_FILE.exists():
    st.error(f"Historical dataset not found: {GOLD_FILE}")
    st.stop()

try:
    gold = load_gold(str(GOLD_FILE), GOLD_FILE.stat().st_mtime)
except (OSError, pd.errors.ParserError, ValueError) as error:
    st.error(f"Could not read the historical dataset: {error}")
    st.stop()

if gold.empty:
    st.warning("The historical dataset has no valid dates yet.")
    st.stop()

minimum_date = gold["date"].min().date()
maximum_date = gold["date"].max().date()
st.caption(
    f"Showing committed or locally generated data from {minimum_date} to {maximum_date}. "
    "Refresh the data pipeline to update these observations."
)

trends_tab, forecast_tab = st.tabs(["Pollution trends", "Next-day prediction"])

with trends_tab:
    station_ids = sorted(gold["location_id"].dropna().unique().tolist())
    selected_stations = st.multiselect(
        "Monitoring stations", station_ids, default=station_ids
    )
    selected_dates = st.date_input(
        "Date range", value=(minimum_date, maximum_date), min_value=minimum_date,
        max_value=maximum_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = selected_dates

    observed = gold[
        gold["location_id"].isin(selected_stations)
        & gold["date"].dt.date.between(start_date, end_date)
    ].copy()
    present_pollutants = [name for name in POLLUTANTS if name in observed.columns]
    available_weather = [name for name in WEATHER_FIELDS if name in observed.columns]

    if observed.empty:
        st.info("No station observations match these filters.")
    else:
        left, right = st.columns(2)
        with left:
            st.metric("Daily station records", f"{len(observed):,}")
        with right:
            st.metric("Stations selected", observed["location_id"].nunique())

        if present_pollutants:
            pollutant = st.selectbox("Pollutant", present_pollutants, index=0)
            st.subheader(f"Daily {pollutant.upper()} by station")
            chart_data = observed[["date", "location_id", pollutant]].dropna(
                subset=[pollutant]
            )
            if chart_data.empty:
                st.info(f"No {pollutant.upper()} observations are available in this range.")
            else:
                st.line_chart(
                    chart_data,
                    x="date",
                    y=pollutant,
                    color="location_id",
                    y_label="Concentration (source units)",
                )

        if available_weather:
            st.subheader("Daily weather")
            weather = (
                observed.groupby("date", as_index=False)[available_weather]
                .mean(numeric_only=True)
                .sort_values("date")
                .set_index("date")
                .rename(columns=WEATHER_FIELDS)
            )
            st.line_chart(weather, y_label="Daily summary")

        st.subheader("Station records")
        st.dataframe(observed.sort_values(["date", "location_id"]), use_container_width=True)
        st.download_button(
            "Download filtered records",
            observed.to_csv(index=False).encode("utf-8"),
            file_name="delhi_air_quality_filtered.csv",
            mime="text/csv",
        )

with forecast_tab:
    st.caption(
        "This forecast estimates next-day PM2.5 concentration. Its category uses the "
        "project's PM2.5 thresholds and is not an official multi-pollutant AQI."
    )
    try:
        health = get_json(f"{API_BASE_URL.rstrip('/')}/health")
    except requests.RequestException:
        st.error(f"Cannot reach the prediction API at {API_BASE_URL}.")
        st.code(".venv/bin/uvicorn app:app --app-dir src/api --reload", language="bash")
        st.stop()

    if not health.get("model_ready"):
        st.warning("The API is running, but a trained model is not available yet.")
        st.info("Build a historical feature dataset and train a model first.")
    else:
        try:
            model_info = get_json(f"{API_BASE_URL.rstrip('/')}/model-info")
        except requests.RequestException as error:
            st.error(f"Could not retrieve model metadata: {error}")
            st.stop()

        st.success(f"Model ready: {model_info['model_name']}")
        st.write("Enter the latest available feature values.")
        features = {}
        columns = st.columns(2)
        for index, feature_name in enumerate(model_info["feature_columns"]):
            with columns[index % 2]:
                features[feature_name] = st.number_input(
                    feature_name, value=0.0, key=feature_name
                )

        if st.button("Predict next-day PM2.5", type="primary"):
            try:
                result = predict(API_BASE_URL, features)
            except requests.RequestException as error:
                st.error(f"Prediction request failed: {error}")
            else:
                st.metric(
                    "Predicted PM2.5 (next day)",
                    f"{result['predicted_pm25_next_day']:.2f} µg/m³",
                )
                st.subheader(f"PM2.5 category: {result['predicted_aqi_category']}")
                if result["missing_features"]:
                    st.warning("The model imputed: " + ", ".join(result["missing_features"]))
