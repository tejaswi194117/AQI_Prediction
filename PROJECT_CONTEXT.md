# AQI Prediction Project — Context for an AI Assistant

## Project purpose

This repository implements an Air Quality Index (AQI) **data-engineering pipeline** for Delhi. It retrieves air-pollution data from OpenAQ and historical hourly weather data from Open-Meteo, cleans and joins them, creates a daily analytical (gold) dataset, validates it, and can load the gold table into PostgreSQL. Apache Airflow orchestrates the workflow daily.

Despite its directory name, this repository currently contains **no trained ML model, feature-training code, model evaluation, or prediction-serving API**. It is the data foundation for a future AQI-prediction project.

## External data sources

- OpenAQ API v3 locations: <https://api.openaq.org/v3/locations>
- OpenAQ API v3 sensors: <https://api.openaq.org/v3/sensors>
- Open-Meteo Historical Weather API: <https://archive-api.open-meteo.com/v1/archive>
- OpenAQ needs an `OPENAQ_API_KEY` environment variable. It is read from `.env` locally and passed into Airflow containers.

## Repository structure

```text
AQI_Prediction_Project/
├── airflow/
│   ├── dags/aqi_pipeline.py              # Daily Airflow DAG
│   ├── docker-compose.yml                # Airflow + Postgres (Airflow metadata DB)
│   ├── Dockerfile                        # apache/airflow:2.10.4 image
│   └── requirements-airflow.txt
├── data/
│   ├── raw/                              # Timestamped untouched OpenAQ/Open-Meteo JSON responses
│   ├── staging/                          # Cleaned source-level CSVs
│   ├── cleaned/                          # Hourly pollution-weather join + validation issues
│   └── gold/                             # Daily analytical AQI CSV
├── sql/
│   ├── schema.sql                        # Base `aqi` schema/tables
│   ├── analytics.sql                     # Aggregate SQL over pollution data
│   ├── aqi_analysis.sql                  # Daily pollutant/AQI category SQL
│   └── final_aqi.sql                     # Final AQI proxy SQL over gold table
├── src/
│   ├── ingestion/                        # API clients
│   ├── etl/                              # Transformations, join, gold creation, checks
│   ├── features/                         # ML feature dataset construction
│   └── database/                         # PostgreSQL loads
├── dashboard/                            # Empty
├── docs/                                 # Empty
├── notebooks/                            # Empty
├── tests/                                # Empty
├── .env.example                          # Safe configuration template
├── README.md                              # Setup and overview
└── requirments.txt                       # Note: filename is misspelled; Python dependencies
```

## Pipeline flow

```text
OpenAQ locations ──> raw/openaq_*.json ──> staging/openaq_stations.csv
                                              │
                                              └─> OpenAQ sensors ─> raw/openaq_sensors_*.json
                                                                           │
OpenAQ measurements <─────────────────────────────────────────────────────┘
       │
       └─> raw/openaq_measurements_*.json ─> staging/openaq_measurements.csv
                                                        │
Open-Meteo historical weather ─> raw/weather_delhi_*.json ─> staging/weather_delhi.csv
                                                        │                    │
                                                        └──── hourly join ──┘
                                                              │
                                      cleaned/pollution_weather_joined.csv
                                                              │
                                          gold/delhi_daily_air_quality.csv
                                                              │
                                   data-quality checks + PostgreSQL gold load
```

## Source files and responsibilities

| File | What it does |
|---|---|
| `src/ingestion/openaq_ingestion.py` | Calls OpenAQ locations with `iso=IN` and `limit=100`; stores an untouched response under `data/raw/openaq_<timestamp>.json`. |
| `src/etl/clean_openaq.py` | Takes the newest main locations file, validates coordinates, filters stations to a configurable Delhi-centred bounding box, and writes `data/staging/openaq_stations.csv`. |
| `src/ingestion/openaq_sensors.py` | Reads staged Delhi station IDs, uses up to configurable `OPENAQ_MAX_STATIONS` (20 by default), calls `/locations/{id}/sensors`, and writes a raw sensor JSON file. |
| `src/ingestion/openaq_measurements.py` | Reads the newest sensor file, calls `/sensors/{id}/measurements?limit=100` for every sensor, adds sensor/location metadata, and writes raw measurements. |
| `src/etl/clean_measurements.py` | Extracts `location_id`, `sensor_id`, pollutant name, value, unit, and UTC period start; removes missing/negative/duplicate records; writes `data/staging/openaq_measurements.csv`. |
| `src/ingestion/weather_ingestion.py` | Retrieves weather at configurable Delhi coordinates. By default it fetches the prior 30 complete days; `WEATHER_START_DATE`/`WEATHER_END_DATE` provide reproducible backfills. |
| `src/etl/clean_weather.py` | Converts the newest Delhi weather response to validated hourly CSV data in `data/staging/weather_delhi.csv`. |
| `src/etl/join_pollution_weather.py` | Converts OpenAQ UTC timestamps to IST, restricts data to the actual common coverage of pollution and weather (with optional configured limits), floors both sources to an hour, left-joins weather, and writes the joined CSV. |
| `src/etl/create_analytical_dataset.py` | Aggregates pollutant data daily by location, pivots six pollutants to columns, summarizes daily weather, derives a PM2.5 category, and writes the gold CSV. |
| `src/etl/data_quality.py` | Checks critical IDs/dates, non-negative pollutants/wind, humidity range, duplicate location/date, AQI labels, and missing PM2.5. Logs issues to CSV. |
| `src/features/build_training_dataset.py` | Creates leakage-safe location/day features: PM2.5 lags, trailing rolling averages, calendar fields, and next-day PM2.5/AQI targets. It expands missing calendar days before feature calculations. |
| `src/database/load_gold.py` | Replaces PostgreSQL `analytics.delhi_daily_air_quality` from the gold CSV. |
| `src/database/load_data.py` | Older base-table loader; it targets a different connection and refers to `data/staging/weather.csv`, not the current `weather_delhi.csv`. |
| `airflow/dags/aqi_pipeline.py` | Defines the orchestrated DAG and task dependencies. |

## Current data contracts

### Staging tables/files

- `openaq_stations.csv`: `station_name, city, country, latitude, longitude, station_id, source`
- `openaq_measurements.csv`: `location_id, sensor_id, parameter, value, unit, timestamp`
- `weather_delhi.csv`: `city, latitude, longitude, timestamp, temperature, humidity, wind_speed, precipitation, source`
- `pollution_weather_joined.csv`: pollution fields plus `hour, temperature, humidity, wind_speed, precipitation`

### Gold dataset

`data/gold/delhi_daily_air_quality.csv` contains one row per `location_id` and date. Its key fields are pollutant average columns such as `pm25`, `pm10`, `o3`, `no2`, `so2`, `co`; daily weather fields `average_temperature`, `average_humidity`, `average_wind_speed`, `total_precipitation`; and `pm25_category`.

The PM2.5 category thresholds are:

| PM2.5 value | Category |
|---:|---|
| ≤30 | Good |
| ≤60 | Satisfactory |
| ≤90 | Moderate |
| ≤120 | Poor |
| ≤250 | Very Poor |
| >250 | Severe |
| missing | Unknown |

These are threshold labels used by the project; they are not a full official multi-pollutant AQI calculation.

## Current materialized data (last inspected)

- `openaq_stations.csv`: 100 records
- `openaq_measurements.csv`: 5,885 records
- `weather_delhi.csv`: 96 hourly records (four days)
- `pollution_weather_joined.csv`: 2,800 records
- `delhi_daily_air_quality.csv`: 7 rows
- Data-quality output has one warning: one row has missing PM2.5.

## Orchestration and running

The Airflow DAG ID is `aqi_air_quality_pipeline`. It is scheduled as `0 6 * * *` (06:00 daily), `catchup=False`, and uses `BashOperator` tasks in this order:

```text
ingest_openaq → clean_stations → ingest_sensors → ingest_measurements → clean_measurements
ingest_weather → clean_weather
[clean_measurements, clean_weather] → join_pollution_weather
→ create_analytical_dataset → data_quality_validation → load_gold
```

Container setup uses Airflow 2.10.4 and PostgreSQL 16. The Airflow UI is exposed on <http://localhost:8080>; the compose file configures login as `admin` / `admin` (change this outside local development).

Typical local commands:

```bash
# Install ordinary Python dependencies (the file is named requirments.txt).
python -m pip install -r requirments.txt

# Put OPENAQ_API_KEY=... in .env, then run scripts from repository root.
python src/ingestion/openaq_ingestion.py
python src/etl/clean_openaq.py
python src/ingestion/openaq_sensors.py
python src/ingestion/openaq_measurements.py
python src/etl/clean_measurements.py
python src/ingestion/weather_ingestion.py
python src/etl/clean_weather.py
python src/etl/join_pollution_weather.py
python src/etl/create_analytical_dataset.py
python src/etl/data_quality.py

# Run Airflow stack from the airflow directory.
cd airflow
docker compose up --build
```

## Important implementation gaps / likely questions

1. **Not a prediction system yet.** There is no ML training, validation split, model artifact, inference endpoint, or dashboard. Unit coverage currently covers the feature-builder only.
2. **Data volume is deliberately limited.** Measurements fetch only up to 100 results per sensor, and API pagination is not implemented. The present gold dataset produces zero trainable next-day rows; collect substantially more contiguous daily history before model training.
5. **Time and duplicate logic needs review.** The cleaned measurement duplicate key is only `(sensor_id, timestamp)`, potentially removing distinct values at the same time. The pipeline uses period start time rather than an explicit observation time.
6. **Database setup still needs an external target.** Set `AQI_DATABASE_URL` to the database that should contain the `aqi` and `analytics` schemas. The scripts now use this one setting and create schemas automatically.
7. **Fragile latest-file selection.** Most steps choose a lexically or modification-time latest raw file, which harms reproducibility and can combine unrelated runs.

## Ready-to-paste prompt

```text
I need help improving a Python/Airflow AQI data-engineering project. Please first understand the following repository context, then answer my next question based on it. Do not assume there is already an ML model: this project currently creates data for a future AQI-prediction system.

[Paste the rest of this PROJECT_CONTEXT.md here, followed by your question.]
```

## Useful follow-up prompts

- “Turn this pipeline into a reproducible Delhi-only AQI prediction project. Propose the target variable, data model, feature engineering, train/test split, and code structure.”
- “Audit every schema and database inconsistency in this project and give me exact corrected files.”
- “Replace the fixed 2025 date window with a configurable incremental pipeline that safely supports daily Airflow runs.”
- “Implement official Indian AQI or US EPA AQI calculation correctly, including pollutant-specific breakpoints and units.”
- “Create tests for all ETL transformations and an Airflow-friendly data-quality strategy.”
- “Explain why this current gold dataset is insufficient for training a forecast model and tell me what data needs to be collected.”
