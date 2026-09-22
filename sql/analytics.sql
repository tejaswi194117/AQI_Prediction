-- ============================================================
-- AQI PROJECT - ANALYTICAL / GOLD LAYER
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. HOURLY POLLUTION AVERAGES
-- ============================================================

DROP TABLE IF EXISTS analytics.hourly_pollution;

CREATE TABLE analytics.hourly_pollution AS
SELECT
    location_id,
    sensor_id,
    parameter,
    unit,
    DATE_TRUNC('hour', timestamp) AS hour,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS measurement_count
FROM aqi.pollution_data
GROUP BY
    location_id,
    sensor_id,
    parameter,
    unit,
    DATE_TRUNC('hour', timestamp);


-- ============================================================
-- 2. DAILY POLLUTION AVERAGES
-- ============================================================

DROP TABLE IF EXISTS analytics.daily_pollution;

CREATE TABLE analytics.daily_pollution AS
SELECT
    location_id,
    parameter,
    unit,
    DATE(timestamp) AS date,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS measurement_count
FROM aqi.pollution_data
GROUP BY
    location_id,
    parameter,
    unit,
    DATE(timestamp);


-- ============================================================
-- 3. POLLUTANT SUMMARY
-- ============================================================

DROP TABLE IF EXISTS analytics.pollutant_summary;

CREATE TABLE analytics.pollutant_summary AS
SELECT
    parameter,
    unit,
    COUNT(*) AS total_measurements,
    AVG(value) AS average_value,
    MIN(value) AS minimum_value,
    MAX(value) AS maximum_value,
    STDDEV(value) AS standard_deviation
FROM aqi.pollution_data
GROUP BY
    parameter,
    unit;


-- ============================================================
-- 4. STATION SUMMARY
-- ============================================================

DROP TABLE IF EXISTS analytics.station_summary;

CREATE TABLE analytics.station_summary AS
SELECT
    location_id,
    COUNT(*) AS total_measurements,
    COUNT(DISTINCT sensor_id) AS sensor_count,
    COUNT(DISTINCT parameter) AS pollutant_count,
    AVG(value) AS overall_average_value,
    MIN(timestamp) AS first_measurement,
    MAX(timestamp) AS last_measurement
FROM aqi.pollution_data
GROUP BY location_id;


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_hourly_pollution_hour
ON analytics.hourly_pollution(hour);

CREATE INDEX IF NOT EXISTS idx_daily_pollution_date
ON analytics.daily_pollution(date);

CREATE INDEX IF NOT EXISTS idx_daily_pollution_parameter
ON analytics.daily_pollution(parameter);