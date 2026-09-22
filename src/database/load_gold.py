import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("AQI_DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("AQI_DATABASE_URL must be set in the environment or .env")

engine = create_engine(DATABASE_URL)


def load_gold_data():

    input_file = "data/gold/delhi_daily_air_quality.csv"

    print(f"Reading: {input_file}")

    df = pd.read_csv(input_file)

    print("Gold records:", len(df))

    # Convert date
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    ).dt.date

    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))

    # Load into analytics schema
    df.to_sql(
        "delhi_daily_air_quality",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    print("\nGold dataset loaded successfully!")

    print("Table:")
    print("analytics.delhi_daily_air_quality")


if __name__ == "__main__":
    load_gold_data()
