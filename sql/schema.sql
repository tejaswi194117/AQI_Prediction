CREATE SCHEMA IF NOT EXISTS aqi;

CREATE TABLE IF NOT EXISTS aqi.pollution_data (
    id SERIAL PRIMARY KEY,
    station_name VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    timestamp TIMESTAMP,
    pollutant VARCHAR(50),
    concentration DOUBLE PRECISION,
    unit VARCHAR(50),
    source VARCHAR(100),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aqi.weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    timestamp TIMESTAMP,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    source VARCHAR(100),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);