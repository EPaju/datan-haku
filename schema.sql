PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id),
    UNIQUE (country_id, name)
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    timezone TEXT,
    FOREIGN KEY (city_id) REFERENCES cities(id)
);

CREATE TABLE IF NOT EXISTS sensors (
    id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL,
    parameter_name TEXT NOT NULL,
    parameter_display_name TEXT,
    unit TEXT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    UNIQUE (location_id, parameter_name, unit)
);

CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL,
    measured_at_utc TEXT NOT NULL,
    measured_at_local TEXT,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    source_name TEXT,
    FOREIGN KEY (sensor_id) REFERENCES sensors(id),
    UNIQUE (sensor_id, measured_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_measurements_sensor_time
ON measurements (sensor_id, measured_at_utc);

CREATE INDEX IF NOT EXISTS idx_sensors_location
ON sensors (location_id);
