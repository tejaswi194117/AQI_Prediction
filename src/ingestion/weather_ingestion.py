import requests
import json
import os
from datetime import datetime, timedelta

# Defaults retrieve the prior 30 complete days, avoiding the hard-coded 2025
# window. Explicit dates make historical backfills reproducible.
LATITUDE = float(os.getenv("AQI_LATITUDE", "28.6139"))
LONGITUDE = float(os.getenv("AQI_LONGITUDE", "77.2090"))
today = datetime.now().date()
START_DATE = os.getenv(
    "WEATHER_START_DATE", (today - timedelta(days=31)).isoformat()
)
END_DATE = os.getenv("WEATHER_END_DATE", (today - timedelta(days=1)).isoformat())

URL = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": (
        "temperature_2m,"
        "relative_humidity_2m,"
        "wind_speed_10m,"
        "precipitation"
    ),
    "timezone": "Asia/Kolkata"
}

print(f"Starting weather ingestion for {START_DATE} to {END_DATE}...")

response = requests.get(URL, params=params, timeout=30)

print("HTTP Status:", response.status_code)

if response.status_code != 200:
    print("Error:", response.text)
    raise SystemExit(1)

data = response.json()

os.makedirs("data/raw", exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"data/raw/weather_delhi_{timestamp}.json"

with open(output_file, "w") as f:
    json.dump(data, f, indent=2)

print(f"Raw weather data saved to: {output_file}")
print("Number of hourly records:", len(data["hourly"]["time"]))
