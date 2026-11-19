#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Missing .env in the project root. Copy .env.example to .env and set OPENAQ_API_KEY."
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Create it with: python3 -m venv .venv"
  exit 1
fi

.venv/bin/python -c 'from dotenv import load_dotenv; import os; load_dotenv(); assert os.getenv("OPENAQ_API_KEY"), "OPENAQ_API_KEY is missing or empty in .env"; print("OpenAQ key found.")'

.venv/bin/python src/ingestion/openaq_ingestion.py
.venv/bin/python src/etl/clean_openaq.py
.venv/bin/python src/ingestion/openaq_sensors.py
.venv/bin/python src/ingestion/openaq_measurements.py
.venv/bin/python src/etl/clean_measurements.py
.venv/bin/python src/ingestion/weather_ingestion.py
.venv/bin/python src/etl/clean_weather.py
.venv/bin/python src/etl/join_pollution_weather.py
.venv/bin/python src/etl/create_analytical_dataset.py
.venv/bin/python src/etl/data_quality.py
.venv/bin/python src/features/build_training_dataset.py

echo "Pipeline finished. Review data/cleaned/data_quality_errors.csv and the row counts above."
