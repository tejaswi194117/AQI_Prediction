"""Small HTTP client used by the Streamlit AQI dashboard."""

import requests


def get_json(url, request_get=requests.get):
    response = request_get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def predict(api_base_url, features, request_post=requests.post):
    response = request_post(
        f"{api_base_url.rstrip('/')}/predict",
        json={"features": features},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()
