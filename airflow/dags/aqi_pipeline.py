from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow"


with DAG(
    dag_id="aqi_air_quality_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    tags=["AQI", "Data Engineering", "MLOps"],
) as dag:

    ingest_openaq = BashOperator(
        task_id="ingest_openaq",
        bash_command=(
            "cd /opt/airflow && "
            "python src/ingestion/openaq_ingestion.py"
        ),
    )

    clean_stations = BashOperator(
        task_id="clean_stations",
        bash_command=(
            "cd /opt/airflow && "
            "python src/etl/clean_openaq.py"
        ),
    )

    ingest_sensors = BashOperator(
        task_id="ingest_sensors",
        bash_command=(
            "cd /opt/airflow && "
            "python src/ingestion/openaq_sensors.py"
        ),
    )

    ingest_measurements = BashOperator(
        task_id="ingest_measurements",
        bash_command=(
            "cd /opt/airflow && "
            "python src/ingestion/openaq_measurements.py"
        ),
    )

    clean_measurements = BashOperator(
        task_id="clean_measurements",
        bash_command=(
            "cd /opt/airflow && "
            "python src/etl/clean_measurements.py"
        ),
    )

    ingest_weather = BashOperator(
        task_id="ingest_weather",
        bash_command=(
            "cd /opt/airflow && "
            "python src/ingestion/weather_ingestion.py"
        ),
    )

    clean_weather = BashOperator(
        task_id="clean_weather",
        bash_command=(
            "cd /opt/airflow && "
            "python src/etl/clean_weather.py"
        ),
    )

    join_data = BashOperator(
        task_id="join_pollution_weather",
        bash_command=(
            "cd /opt/airflow && "
            "python src/etl/join_pollution_weather.py"
        ),
    )

    create_gold = BashOperator(
        task_id="create_analytical_dataset",
        bash_command=(
            "cd /opt/airflow && "
            "python src/etl/create_analytical_dataset.py"
        ),
    )

    quality_check = BashOperator(
        task_id="data_quality_validation",
        bash_command=(
            "cd /opt/airflow && "
            "python src/etl/data_quality.py"
        ),
    )

    (
        ingest_openaq
        >> clean_stations
        >> ingest_sensors
        >> ingest_measurements
        >> clean_measurements
    )

    ingest_weather >> clean_weather

    load_gold = BashOperator(
    task_id="load_gold",
    bash_command=(
        "cd /opt/airflow && "
        "python src/database/load_gold.py"
    ),
 )

    (
        [
            clean_measurements,
            clean_weather,
        ]
        >> join_data
        >> create_gold
        >> quality_check
        >> load_gold
    )