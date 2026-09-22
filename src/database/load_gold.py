import pandas as pd
from sqlalchemy import create_engine


DATABASE_URL = "postgresql+psycopg2://tejjjj@host.docker.internal/aqi_database"

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