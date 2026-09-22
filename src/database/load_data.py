import pandas as pd
from sqlalchemy import create_engine


# PostgreSQL connection
DATABASE_URL = "postgresql+psycopg2://localhost/aqi_database"

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

    file_path = "data/staging/weather.csv"

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

    load_pollution_data()

    load_weather_data()

    print("\nAll data loaded into PostgreSQL.")


if __name__ == "__main__":
    main()