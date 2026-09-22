import requests
import json
import os
from datetime import datetime

# Delhi representative coordinates
LATITUDE = 28.63
LONGITUDE = 77.20

START_DATE = "2025-02-18"
END_DATE = "2025-02-21"

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

print("Starting Delhi weather ingestion...")

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