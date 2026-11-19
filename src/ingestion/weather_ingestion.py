import requests
import json
import os
from datetime import datetime, timedelta
from run_manifest import record_extraction

# Defaults retrieve the prior 30 complete days, avoiding the hard-coded 2025
# window. Explicit dates make historical backfills reproducible.
LATITUDE = float(os.getenv("AQI_LATITUDE", "28.6139"))
LONGITUDE = float(os.getenv("AQI_LONGITUDE", "77.2090"))
today = datetime.now().date()
HISTORY_DAYS = int(os.getenv("AQI_HISTORY_DAYS", "30"))
START_DATE = os.getenv(
    "WEATHER_START_DATE", (today - timedelta(days=HISTORY_DAYS)).isoformat()
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

try:
    response = requests.get(URL, params=params, timeout=30)
    response.raise_for_status()
except requests.RequestException as error:
    record_extraction("Open-Meteo historical weather", "failed", error=error)
    raise

print("HTTP Status:", response.status_code)

data = response.json()

os.makedirs("data/raw", exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"data/raw/weather_delhi_{timestamp}.json"

with open(output_file, "w") as f:
    json.dump(data, f, indent=2)

print(f"Raw weather data saved to: {output_file}")
print("Number of hourly records:", len(data["hourly"]["time"]))
record_extraction(
    "Open-Meteo historical weather",
    "success",
    output_file,
    len(data["hourly"]["time"]),
)
