"""Streamlit user interface for the next-day Delhi PM2.5 prediction API."""

import os
import sys

import requests
import streamlit as st


sys.path.insert(0, os.path.dirname(__file__))
from api_client import get_json, predict


API_BASE_URL = os.getenv("AQI_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Delhi AQI Forecast", page_icon="🌫️")
st.title("Delhi AQI Forecast")
st.caption("Predict next-day PM2.5 from the trained AQI pipeline model.")

try:
    health = get_json(f"{API_BASE_URL.rstrip('/')}/health")
except requests.RequestException:
    st.error(f"Cannot reach the prediction API at {API_BASE_URL}.")
    st.code(".venv/bin/uvicorn app:app --app-dir src/api --reload", language="bash")
    st.stop()

if not health.get("model_ready"):
    st.warning("The API is running, but no trained model is available yet.")
    st.info("Complete the historical backfill, build features, and run model training first.")
    st.stop()

try:
    model_info = get_json(f"{API_BASE_URL.rstrip('/')}/model-info")
except requests.RequestException as error:
    st.error(f"Could not retrieve model metadata: {error}")
    st.stop()

st.success(f"Model ready: {model_info['model_name']}")
st.write("Enter the latest available feature values. Missing values are handled by the model's imputation step.")

features = {}
columns = st.columns(2)
for index, feature_name in enumerate(model_info["feature_columns"]):
    with columns[index % 2]:
        value = st.number_input(feature_name, value=0.0, key=feature_name)
        features[feature_name] = value

if st.button("Predict next-day PM2.5", type="primary"):
    try:
        result = predict(API_BASE_URL, features)
    except requests.RequestException as error:
        st.error(f"Prediction request failed: {error}")
    else:
        st.metric("Predicted PM2.5 (next day)", f"{result['predicted_pm25_next_day']:.2f} µg/m³")
        st.subheader(f"AQI category: {result['predicted_aqi_category']}")
        if result["missing_features"]:
            st.warning("The model imputed: " + ", ".join(result["missing_features"]))
