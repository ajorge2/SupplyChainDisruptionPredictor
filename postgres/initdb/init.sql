-- Create weather_historical table
CREATE TABLE IF NOT EXISTS weather_historical (
    id SERIAL PRIMARY KEY,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    location VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL UNIQUE
);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    location VARCHAR(100) NOT NULL,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    avg_temperature_last_5_days FLOAT NOT NULL,
    avg_humidity_last_5_days FLOAT NOT NULL,
    disruption_probability FLOAT NOT NULL,
    disruption BOOLEAN NOT NULL DEFAULT FALSE
);

-- Insert Sample Data
INSERT INTO predictions (location, temperature, humidity, avg_temperature_last_5_days, avg_humidity_last_5_days, disruption_probability, disruption)
VALUES
('Warehouse_A', 25.5, 60, 24.8, 58, 0.2, TRUE),
('Warehouse_B', 30.2, 55, 29.5, 54, 0.1, FALSE);

-- Insert Sample Data
INSERT INTO weather_historical (temperature, humidity, location, timestamp) VALUES
(25.5, 60, 'Warehouse_A', '2025-01-01 12:00:00'),
(30.2, 55, 'Warehouse_B', '2025-01-02 12:00:00');
