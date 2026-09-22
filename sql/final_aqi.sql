CREATE SCHEMA IF NOT EXISTS analytics;

DROP TABLE IF EXISTS analytics.final_aqi;

CREATE TABLE analytics.final_aqi AS
SELECT
    location_id,
    date,

    pm25,
    pm10,
    no2,
    so2,
    o3,
    co,

    average_temperature,
    average_humidity,
    average_wind_speed,
    total_precipitation,

    -- PM2.5 based analytical AQI category
    CASE
        WHEN pm25 IS NULL THEN 'Unknown'
        WHEN pm25 <= 30 THEN 'Good'
        WHEN pm25 <= 60 THEN 'Satisfactory'
        WHEN pm25 <= 90 THEN 'Moderate'
        WHEN pm25 <= 120 THEN 'Poor'
        WHEN pm25 <= 250 THEN 'Very Poor'
        ELSE 'Severe'
    END AS aqi_category,

    -- Numeric analytical AQI proxy based on PM2.5
    CASE
        WHEN pm25 IS NULL THEN NULL
        WHEN pm25 <= 30 THEN ROUND((pm25 / 30.0) * 50)
        WHEN pm25 <= 60 THEN ROUND(50 + ((pm25 - 30) / 30.0) * 50)
        WHEN pm25 <= 90 THEN ROUND(100 + ((pm25 - 60) / 30.0) * 100)
        WHEN pm25 <= 120 THEN ROUND(200 + ((pm25 - 90) / 30.0) * 100)
        WHEN pm25 <= 250 THEN ROUND(300 + ((pm25 - 120) / 130.0) * 100)
        ELSE 500
    END AS aqi_proxy

FROM analytics.delhi_daily_air_quality;