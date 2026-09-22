CREATE SCHEMA IF NOT EXISTS analytics;

DROP TABLE IF EXISTS analytics.aqi_daily;

CREATE TABLE analytics.aqi_daily AS

WITH daily AS (

    SELECT
        location_id,
        DATE(timestamp::timestamp) AS date,

        AVG(
            CASE
                WHEN parameter = 'pm25'
                AND unit = 'µg/m³'
                THEN value::double precision
            END
        ) AS pm25,

        AVG(
            CASE
                WHEN parameter = 'pm10'
                AND unit = 'µg/m³'
                THEN value::double precision
            END
        ) AS pm10,

        AVG(
            CASE
                WHEN parameter = 'o3'
                AND unit = 'µg/m³'
                THEN value::double precision
            END
        ) AS o3,

        AVG(
            CASE
                WHEN parameter = 'no2'
                AND unit = 'µg/m³'
                THEN value::double precision
            END
        ) AS no2,

        AVG(
            CASE
                WHEN parameter = 'so2'
                AND unit = 'µg/m³'
                THEN value::double precision
            END
        ) AS so2,

        AVG(
            CASE
                WHEN parameter = 'co'
                AND unit = 'µg/m³'
                THEN value::double precision
            END
        ) AS co

    FROM aqi.pollution_data

    WHERE parameter IN (
        'pm25',
        'pm10',
        'o3',
        'no2',
        'so2',
        'co'
    )

    GROUP BY
        location_id,
        DATE(timestamp::timestamp)
)

SELECT
    location_id,
    date,
    pm25,
    pm10,
    o3,
    no2,
    so2,
    co,

    CASE
        WHEN pm25 IS NULL THEN NULL
        WHEN pm25 <= 30 THEN 'Good'
        WHEN pm25 <= 60 THEN 'Satisfactory'
        WHEN pm25 <= 90 THEN 'Moderate'
        WHEN pm25 <= 120 THEN 'Poor'
        WHEN pm25 <= 250 THEN 'Very Poor'
        ELSE 'Severe'
    END AS pm25_category

FROM daily;