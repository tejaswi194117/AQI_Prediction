# Air Quality Analysis and PM2.5 Forecasting

This project builds a Delhi-focused air-quality data pipeline and a dashboard for historical pollution trends. It also contains an optional next-day PM2.5 baseline model, API, and prediction view. The tracked CSV files are small historical examples; they are not evidence of a current live ingestion or a trained model.

## Scope and AQI terminology

The forecast target is next-day **PM2.5 concentration**. The displayed category is derived from this project's PM2.5 thresholds (Good through Severe). It is a PM2.5 category proxy, not an official multi-pollutant AQI calculation. The dashboard shows daily pollutant and weather trends for the locations present in the gold dataset; the default configuration is centered on Delhi.

## Data sources and access

- **OpenAQ API v3** supplies monitoring locations, sensors, and pollutant measurements. Create an API key through OpenAQ, set `OPENAQ_API_KEY` in a local `.env` file, and do not commit that file.
- **Open-Meteo Historical Weather API** supplies hourly temperature, relative humidity, wind speed, and precipitation for the configured coordinates and dates. The code calls its public archive endpoint without an API key.
- The project does not currently ingest CPCB data or depend on a Kaggle dataset. The committed CSVs are derived project artifacts, not a replacement for source attribution in a submitted report.

## Pipeline

```text
OpenAQ locations -> stations -> sensors -> measurements -> staging CSV
Open-Meteo historical weather -----------------------> staging CSV
                                              \\      /
                                    time-aligned join
                                            |
                            daily station-level gold CSV
                                            |
                      quality checks -> ML feature CSV
                                            |
                      optional PostgreSQL gold load
```

Airflow defines daily ingestion, transformation, quality, feature-build, and database-load tasks in `airflow/dags/aqi_pipeline.py`. Compose files define the Airflow stack and a separate API/dashboard stack. Code and Compose definitions do not establish that services have been run successfully.

## Setup

```bash
cp .env.example .env
# Set OPENAQ_API_KEY. Set AQI_DATABASE_URL only if loading the gold CSV to PostgreSQL.
python -m pip install -r requirments.txt
```

Optional configuration is listed in `.env.example`. `AQI_HISTORY_DAYS` controls the default shared lookback; `OPENAQ_HISTORY_START_DATE` / `OPENAQ_HISTORY_END_DATE` and `WEATHER_START_DATE` / `WEATHER_END_DATE` allow explicit source windows. `ANALYSIS_START_DATE` / `ANALYSIS_END_DATE` can narrow the join. Use a long historical window for model training, then choose an appropriate rolling window for scheduled operation.

Run the complete ingestion and ETL sequence from the repository root:

```bash
bash scripts/run_pipeline.sh
```

The helper stops on the first error so later steps cannot silently reuse stale outputs. To run a single step manually, use `.venv/bin/python` and run each command only after the previous step succeeds.

The ingestion scripts retain timestamped raw JSON under `data/raw/` locally; that directory is ignored by Git. Staging outputs go under `data/staging/`, the hourly join and quality log under `data/cleaned/`, and daily analytical data under `data/gold/`.

## Dashboard

Run from the repository root:

```bash
streamlit run dashboard/app.py
```

The **Pollution trends** view reads `data/gold/delhi_daily_air_quality.csv` and provides date/station filters, daily pollutant charts, weather charts, a table, and CSV download. It reflects the local gold file; rerun the pipeline to refresh it. The **Next-day prediction** view requires a running API and trained model.

## Forecast model and API

The feature builder creates PM2.5 lag and rolling features and a next-day target without treating missing dates as adjacent days. It writes the ignored file `data/gold/ml_aqi_features.csv`. The training script requires at least 100 rows by default and uses a chronological date split to compare mean, linear-regression, and random-forest baselines. It writes `models/pm25_next_day_model.joblib` and `models/pm25_next_day_metrics.json`; generated files are intentionally excluded from Git.

After a successful feature build with sufficient history:

```bash
python src/models/train_pm25_model.py
uvicorn app:app --app-dir src/api --reload
```

The API exposes `/health`, `/model-info`, and `/predict`. Open `http://127.0.0.1:8000/docs` for local interactive documentation. Do not describe the model as validated or deployed until the backfill, training, evaluation, and serving steps have actually succeeded and their evidence is recorded.

## Airflow and PostgreSQL

Airflow can be started from `airflow/` with `docker compose up --build`; its local UI is at `http://localhost:8080`. The compose file starts PostgreSQL for Airflow metadata and defaults `AQI_DATABASE_URL` to that same local database for the gold load. Set `AQI_DATABASE_URL` in `.env` to use a separate target database. The loader writes `analytics.delhi_daily_air_quality` through `src/database/load_gold.py`.

## Docker prediction stack

Once the model artifact exists, run from the repository root:

```bash
docker compose -f docker-compose.app.yml up --build
```

The API is exposed on port 8000 and the dashboard on port 8501. This app stack does not include Airflow or the analytics database.

## Current limitations and evidence to collect

- The checked-in gold data is a small historical snapshot with missing pollutant values; it is not sufficient to train the default model.
- The dashboard and prediction API are source code only. No deployment URL, successful Airflow run, populated target database, trained model, or evaluation report is committed.
- The database loader creates/replaces the gold table from the CSV; no migration or committed gold-table DDL is supplied.
- Record a successful end-to-end backfill, quality output, train/test date ranges and metrics, model artifact version, API response, and dashboard screenshot/link before claiming operational completion.
- `tests/` contains unit tests for feature creation, training, API utilities, the dashboard client, and OpenAQ pagination. Their existence alone does not prove that they pass.

## Repository map

- `src/ingestion/`: OpenAQ and Open-Meteo extraction
- `src/etl/`: staging cleanup, time alignment, daily aggregation, validation
- `src/features/` and `src/models/`: next-day PM2.5 feature generation and training
- `src/api/` and `dashboard/`: prediction service and analysis UI
- `airflow/`: scheduled pipeline definition and local Compose stack
- `sql/`: base and analytical SQL examples
- `data/`: checked-in sample CSV outputs; raw extracts and generated ML artifacts are ignored
