CREATE SCHEMA IF NOT EXISTS aqi;

CREATE TABLE IF NOT EXISTS aqi.pollution_data (
    location_id BIGINT NOT NULL,
    sensor_id BIGINT NOT NULL,
    parameter VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50),
    timestamp TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS aqi.weather_data (
    city VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    source VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_pollution_location_timestamp
ON aqi.pollution_data(location_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_weather_timestamp
ON aqi.weather_data(timestamp);
