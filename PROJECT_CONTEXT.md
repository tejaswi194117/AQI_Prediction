# Project context

## Current scope

This repository contains a Delhi-focused air-quality ETL pipeline, a historical trend dashboard, and code for a next-day PM2.5 baseline model and prediction API. The forecast output is PM2.5 concentration plus a category derived from the project's PM2.5 thresholds; this is not an official multi-pollutant AQI calculation.

The checked-in CSVs are a small historical snapshot. The repository does **not** currently include a generated ML feature dataset, trained model artifact, model metrics, successful service-run evidence, or an external dashboard deployment link. Do not claim these as completed until generated and recorded.

## Data sources and configuration

- OpenAQ API v3: locations, sensors, and measurements. Requires `OPENAQ_API_KEY` in a local `.env` file.
- Open-Meteo Historical Weather API: hourly weather for the configured point and requested dates; no key is configured in this project.
- `.env.example` documents the location, station-count, granularity, page-size, and date-window settings. Never commit `.env` or API keys.

Ingestion writes timestamped raw JSON under `data/raw/` and appends source, UTC extraction time, status, output path, row count, and any error to `data/raw/extraction_manifest.jsonl`. `data/raw/` is git-ignored. Staging CSVs are written under `data/staging/`; the joined hourly/daily source data and quality log are under `data/cleaned/`; the daily station-level analytical CSV is `data/gold/delhi_daily_air_quality.csv`.

## Pipeline and files

1. `src/ingestion/openaq_ingestion.py` collects locations.
2. `src/etl/clean_openaq.py` filters and stages station metadata.
3. `src/ingestion/openaq_sensors.py` collects station sensors.
4. `src/ingestion/openaq_measurements.py` collects paginated sensor history.
5. `src/etl/clean_measurements.py` normalizes pollutant observations.
6. `src/ingestion/weather_ingestion.py` and `src/etl/clean_weather.py` retrieve and stage weather.
7. `src/etl/join_pollution_weather.py` aligns the source time windows and joins weather.
8. `src/etl/create_analytical_dataset.py` creates daily station summaries and PM2.5 threshold categories.
9. `src/etl/data_quality.py` writes validation issues to `data/cleaned/data_quality_errors.csv`.
10. `src/features/build_training_dataset.py` generates lag/rolling features and a next-day PM2.5 target.
11. `src/database/load_gold.py` optionally replaces `analytics.delhi_daily_air_quality` in the configured target database.

Run steps 1–10 with `bash scripts/run_pipeline.sh`; it exits immediately if any step fails, preventing accidental use of stale output files.

`airflow/dags/aqi_pipeline.py` defines the scheduled daily orchestration through feature generation and PostgreSQL load. The Airflow Compose PostgreSQL service is the metadata database and is also the default `AQI_DATABASE_URL` destination for local development; `.env` can override it. Airflow and database definitions are not evidence that the stack or a DAG run has succeeded.

## Model and dashboard

`src/models/train_pm25_model.py` compares a mean baseline, linear regression, and random forest using a chronological split. By default, it requires at least 100 target rows and writes a model and metrics under `models/`. Generated artifacts are ignored by Git. The prediction API in `src/api/` exposes health, model information, and prediction routes.

`dashboard/app.py` reads the local gold CSV and presents date/station-filtered pollutant and weather trends. Its prediction tab calls the API and requires a separately trained model. A Docker build copies the tracked gold snapshot into the dashboard image; regenerating the data or image is required to refresh it.

## Data contracts

- Stations: `station_name, city, country, latitude, longitude, station_id, source`
- Measurements: `location_id, sensor_id, parameter, value, unit, timestamp` (the history extractor also carries aggregation metadata where available)
- Weather: `city, latitude, longitude, timestamp, temperature, humidity, wind_speed, precipitation, source`
- Gold: one row per `location_id,date`, pollutant fields, daily weather fields, and `pm25_category`

The database base tables are in `sql/schema.sql`; analytical SQL examples are in `sql/`. The gold loader creates/replaces its table from the CSV rather than applying a versioned gold-table migration.

## Remaining evidence and limitations

- Refresh the source data with a real OpenAQ key and retain the raw files and extraction manifest for review.
- Confirm station selection and the weather coordinate are appropriate for the analysis; a single weather coordinate is reused across selected stations.
- Review and preserve validation results; the sample gold file currently has missing pollutant values.
- Generate sufficient contiguous historical observations, train the model, and record test window, metrics, and artifact version.
- Exercise Airflow, PostgreSQL, API, and dashboard; attach successful run logs, screenshots, or deployment links.
- The dashboard currently charts the available city/station snapshot; it does not establish a live public dashboard.

See `README.md` for setup and run instructions.
