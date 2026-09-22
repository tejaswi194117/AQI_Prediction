import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

URL = "https://api.openaq.org/v3/locations"


def fetch_openaq_data():

    if not API_KEY:
        print("ERROR: OPENAQ_API_KEY not found in .env")
        return

    print("Starting OpenAQ data ingestion...")

    headers = {
        "X-API-Key": API_KEY
    }

    try:
        response = requests.get(
            URL,
            headers=headers,
            params={
                "iso": "IN",
                "limit": 100
            },
            timeout=30
        )

        print("HTTP Status:", response.status_code)

        response.raise_for_status()

        data = response.json()

        # Create raw directory
        raw_dir = Path("data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Timestamp for reproducibility
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_file = raw_dir / f"openaq_{timestamp}.json"

        # Store untouched API response
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        print("Raw data saved to:", output_file)
        print(
            "Number of records:",
            len(data.get("results", []))
        )

    except requests.exceptions.RequestException as error:
        print("API request failed:", error)

    except Exception as error:
        print("Unexpected error:", error)


if __name__ == "__main__":
    fetch_openaq_data()