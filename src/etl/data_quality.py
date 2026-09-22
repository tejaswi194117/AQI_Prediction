import pandas as pd
import os
from datetime import datetime


INPUT_FILE = "data/gold/delhi_daily_air_quality.csv"
ERROR_FILE = "data/cleaned/data_quality_errors.csv"


def run_quality_checks():

    print("Starting data quality validation...\n")

    df = pd.read_csv(INPUT_FILE)

    errors = []

    # --------------------------------------------------
    # CHECK 1: Missing critical values
    # --------------------------------------------------

    critical_columns = [
        "location_id",
        "date"
    ]

    for column in critical_columns:

        missing_count = df[column].isna().sum()

        if missing_count > 0:
            errors.append({
                "check": "Missing critical value",
                "column": column,
                "issue_count": missing_count,
                "status": "FAIL"
            })
        else:
            print(f"PASS: No missing values in {column}")

    # --------------------------------------------------
    # CHECK 2: Negative pollutant values
    # --------------------------------------------------

    pollutant_columns = [
        "pm25",
        "pm10",
        "no2",
        "so2",
        "o3",
        "co"
    ]

    for column in pollutant_columns:

        if column not in df.columns:
            continue

        invalid_count = (df[column] < 0).sum()

        if invalid_count > 0:

            errors.append({
                "check": "Negative pollutant value",
                "column": column,
                "issue_count": invalid_count,
                "status": "FAIL"
            })

        else:
            print(f"PASS: No negative values in {column}")

    # --------------------------------------------------
    # CHECK 3: Humidity range
    # --------------------------------------------------

    invalid_humidity = (
        (df["average_humidity"] < 0) |
        (df["average_humidity"] > 100)
    ).sum()

    if invalid_humidity > 0:

        errors.append({
            "check": "Invalid humidity",
            "column": "average_humidity",
            "issue_count": invalid_humidity,
            "status": "FAIL"
        })

    else:
        print("PASS: Humidity values are between 0 and 100")

    # --------------------------------------------------
    # CHECK 4: Wind speed
    # --------------------------------------------------

    invalid_wind = (
        df["average_wind_speed"] < 0
    ).sum()

    if invalid_wind > 0:

        errors.append({
            "check": "Negative wind speed",
            "column": "average_wind_speed",
            "issue_count": invalid_wind,
            "status": "FAIL"
        })

    else:
        print("PASS: Wind speed values are valid")

    # --------------------------------------------------
    # CHECK 5: Duplicate station/date
    # --------------------------------------------------

    duplicates = df.duplicated(
        subset=["location_id", "date"]
    ).sum()

    if duplicates > 0:

        errors.append({
            "check": "Duplicate station/date",
            "column": "location_id,date",
            "issue_count": duplicates,
            "status": "FAIL"
        })

    else:
        print("PASS: No duplicate station/date records")

    # --------------------------------------------------
    # CHECK 6: AQI category validation
    # --------------------------------------------------

    valid_categories = [
        "Good",
        "Satisfactory",
        "Moderate",
        "Poor",
        "Very Poor",
        "Severe",
        "Unknown"
    ]

    invalid_categories = (
        ~df["pm25_category"].isin(valid_categories)
    ).sum()

    if invalid_categories > 0:

        errors.append({
            "check": "Invalid AQI category",
            "column": "pm25_category",
            "issue_count": invalid_categories,
            "status": "FAIL"
        })

    else:
        print("PASS: AQI categories are valid")

    # --------------------------------------------------
    # CHECK 7: Missing PM2.5
    # --------------------------------------------------

    missing_pm25 = df["pm25"].isna().sum()

    if missing_pm25 > 0:

        print(
            f"WARNING: {missing_pm25} records have missing PM2.5"
        )

        errors.append({
            "check": "Missing PM2.5",
            "column": "pm25",
            "issue_count": missing_pm25,
            "status": "WARNING"
        })

    else:
        print("PASS: No missing PM2.5 values")

    # --------------------------------------------------
    # SAVE ERROR LOG
    # --------------------------------------------------

    os.makedirs(
        os.path.dirname(ERROR_FILE),
        exist_ok=True
    )

    if errors:

        error_df = pd.DataFrame(errors)

        error_df["validation_timestamp"] = datetime.now()

        error_df.to_csv(
            ERROR_FILE,
            index=False
        )

        print(
            f"\nValidation issues logged to: {ERROR_FILE}"
        )

    else:

        print("\nNo data quality issues found.")

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print("\n================================")
    print("DATA QUALITY SUMMARY")
    print("================================")

    print("Total records:", len(df))
    print("Total validation issues:", len(errors))

    if errors:
        print("\nIssues:")
        print(
            pd.DataFrame(errors)[
                ["check", "issue_count", "status"]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    run_quality_checks()