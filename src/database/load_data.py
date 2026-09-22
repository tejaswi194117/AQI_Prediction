import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("AQI_DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("AQI_DATABASE_URL must be set in the environment or .env")

engine = create_engine(DATABASE_URL)


def load_pollution_data():

    file_path = "data/staging/openaq_measurements.csv"

    df = pd.read_csv(file_path)

    print("Pollution records:", len(df))

    df.to_sql(
        "pollution_data",
        engine,
        schema="aqi",
        if_exists="replace",
        index=False
    )

    print("Pollution data loaded successfully.")


def load_weather_data():

    file_path = "data/staging/weather_delhi.csv"

    df = pd.read_csv(file_path)

    print("Weather records:", len(df))

    df.to_sql(
        "weather_data",
        engine,
        schema="aqi",
        if_exists="replace",
        index=False
    )

    print("Weather data loaded successfully.")


def main():

    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS aqi"))

    load_pollution_data()

    load_weather_data()

    print("\nAll data loaded into PostgreSQL.")


if __name__ == "__main__":
    main()
