# AQI Prediction Project

An Airflow-orchestrated data pipeline that collects Delhi air-quality and weather data, produces a daily analytical dataset, validates it, and can load it into PostgreSQL. It is the data foundation for a future AQI prediction model; no machine-learning model is included yet.

## Pipeline

```text
OpenAQ locations → stations → sensors → measurements ┐
                                                       ├→ weather-aware join → daily gold AQI dataset
Open-Meteo historical weather ─────────────────────────┘
```

The default geographic focus is Delhi (28.6139, 77.2090) within a 0.5-degree bounding box. All location, date-range, and database settings are configurable through `.env`.

For a one-time historical backfill, set `AQI_HISTORY_DAYS=365` and keep `OPENAQ_GRANULARITY=days` in `.env`, then run the pipeline. This requests paginated daily sensor values and matching daily Open-Meteo summaries. Reset the window to a short rolling value afterward for normal daily Airflow runs.

## Setup

```bash
cp .env.example .env
# Set OPENAQ_API_KEY. Set AQI_DATABASE_URL if PostgreSQL loading is required.
.venv/bin/python -m pip install -r requirments.txt
```

Run the local pipeline from the repository root:

```bash
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
```

For Airflow, run `docker compose up --build` from `airflow/`; the UI is at <http://localhost:8080>. The Compose environment reads `.env` from the project root.

## Outputs

- `data/staging/`: cleaned station, measurement, and weather extracts.
- `data/cleaned/pollution_weather_joined.csv`: hourly pollution/weather records.
- `data/gold/delhi_daily_air_quality.csv`: daily per-location analytical dataset.
- `data/gold/ml_aqi_features.csv`: leakage-safe daily ML features and the next-day PM2.5 target.

The feature-builder requires a much larger historical dataset before model training. It produces lag-1/3/7-day PM2.5 values, trailing rolling means, calendar fields, and a next-day PM2.5/category label without crossing missing dates.

Once the backfill produces at least 100 trainable rows, run `.venv/bin/python src/models/train_pm25_model.py`. It uses a chronological 80/20 split, compares mean, linear-regression, and random-forest baselines by test MAE, and saves the selected model plus metrics under `models/`.

## Prediction API

After training a model, start the API from the project root:

```bash
.venv/bin/uvicorn app:app --app-dir src/api --reload
```

Visit <http://127.0.0.1:8000/docs> for interactive API documentation. `GET /health` reports whether a model is ready, `GET /model-info` returns required input fields, and `POST /predict` returns predicted next-day PM2.5 and its AQI category.

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for the full architecture, schemas, data contracts, and known next steps.
