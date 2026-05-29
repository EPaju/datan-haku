from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.openaq.org/v3"
PAGE_LIMIT = 1000


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def init_database(connection: sqlite3.Connection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    connection.executescript(schema_path.read_text(encoding="utf-8"))


def upsert_country(connection: sqlite3.Connection, code: str, name: str) -> int:
    connection.execute(
        """
        INSERT INTO countries (code, name)
        VALUES (?, ?)
        ON CONFLICT(code) DO UPDATE SET name = excluded.name
        """,
        (code, name),
    )
    row = connection.execute("SELECT id FROM countries WHERE code = ?", (code,)).fetchone()
    return int(row["id"])


def upsert_city(connection: sqlite3.Connection, country_id: int, name: str) -> int:
    connection.execute(
        """
        INSERT INTO cities (country_id, name)
        VALUES (?, ?)
        ON CONFLICT(country_id, name) DO NOTHING
        """,
        (country_id, name),
    )
    row = connection.execute(
        "SELECT id FROM cities WHERE country_id = ? AND name = ?",
        (country_id, name),
    ).fetchone()
    return int(row["id"])


def upsert_location(
    connection: sqlite3.Connection,
    location_id: int,
    city_id: int,
    name: str,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> int:
    connection.execute(
        """
        INSERT INTO locations (id, city_id, name, latitude, longitude, timezone)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            city_id = excluded.city_id,
            name = excluded.name,
            latitude = COALESCE(excluded.latitude, locations.latitude),
            longitude = COALESCE(excluded.longitude, locations.longitude),
            timezone = COALESCE(excluded.timezone, locations.timezone)
        """,
        (location_id, city_id, name, latitude, longitude, timezone),
    )
    return location_id


def upsert_sensor(
    connection: sqlite3.Connection,
    sensor_id: int,
    location_id: int,
    parameter_name: str,
    parameter_display_name: str | None,
    unit: str,
) -> int:
    connection.execute(
        """
        INSERT INTO sensors (id, location_id, parameter_name, parameter_display_name, unit)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            location_id = excluded.location_id,
            parameter_name = excluded.parameter_name,
            parameter_display_name = excluded.parameter_display_name,
            unit = excluded.unit
        """,
        (sensor_id, location_id, parameter_name, parameter_display_name, unit),
    )
    return sensor_id


def fetch_measurements(api_key: str, sensor_id: int, date_from: str, date_to: str) -> list[dict[str, Any]]:
    measurements: list[dict[str, Any]] = []
    page = 1

    while True:
        response = requests.get(
            f"{BASE_URL}/sensors/{sensor_id}/measurements",
            headers={"X-API-Key": api_key},
            params={
                "datetime_from": date_from,
                "datetime_to": date_to,
                "limit": PAGE_LIMIT,
                "page": page,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        measurements.extend(results)

        meta = payload.get("meta", {})
        found = int(meta.get("found", len(measurements)))
        if len(measurements) >= found or not results:
            break
        page += 1

    return measurements


def get_datetime_value(measurement: dict[str, Any], key: str) -> str | None:
    value = measurement.get(key)
    if isinstance(value, dict):
        return value.get("utc") or value.get("local")
    if isinstance(value, str):
        return value
    return None


def get_period_datetime(measurement: dict[str, Any], key: str, zone: str = "utc") -> str | None:
    period = measurement.get("period")
    if not isinstance(period, dict):
        return None
    value = period.get(key)
    if isinstance(value, dict):
        return value.get(zone) or value.get("utc") or value.get("local")
    return None


def save_measurements(
    connection: sqlite3.Connection,
    sensor_id: int,
    measurements: list[dict[str, Any]],
    fallback_unit: str,
) -> int:
    inserted = 0
    for measurement in measurements:
        measured_at_utc = (
            get_datetime_value(measurement, "date")
            or get_period_datetime(measurement, "datetimeFrom")
        )
        if not measured_at_utc:
            continue
        measured_at_local = get_period_datetime(measurement, "datetimeFrom", "local")

        coordinates = measurement.get("coordinates") or {}
        source = measurement.get("source") or {}
        parameter = measurement.get("parameter") or {}
        before = connection.total_changes
        connection.execute(
            """
            INSERT OR IGNORE INTO measurements (
                sensor_id,
                measured_at_utc,
                measured_at_local,
                value,
                unit,
                latitude,
                longitude,
                source_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sensor_id,
                measured_at_utc,
                measured_at_local,
                measurement.get("value"),
                measurement.get("unit") or parameter.get("units") or fallback_unit,
                coordinates.get("latitude"),
                coordinates.get("longitude"),
                source.get("name"),
            ),
        )
        if connection.total_changes > before:
            inserted += 1
    return inserted


def main() -> None:
    load_dotenv()

    api_key = get_required_env("OPENAQ_API_KEY")
    sensor_id = int(get_required_env("OPENAQ_SENSOR_ID"))
    location_id = int(get_required_env("OPENAQ_LOCATION_ID"))
    date_from = get_required_env("DATE_FROM")
    date_to = get_required_env("DATE_TO")
    database_path = Path(os.getenv("DATABASE_PATH", "../air_quality.sqlite"))

    country_code = get_required_env("OPENAQ_COUNTRY_CODE")
    country_name = get_required_env("OPENAQ_COUNTRY_NAME")
    city_name = get_required_env("OPENAQ_CITY_NAME")
    location_name = get_required_env("OPENAQ_LOCATION_NAME")
    parameter_name = os.getenv("OPENAQ_PARAMETER_NAME", "pm25")
    parameter_display_name = os.getenv("OPENAQ_PARAMETER_DISPLAY_NAME", "PM2.5")
    unit = os.getenv("OPENAQ_UNIT", "ug/m3")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    try:
        init_database(connection)
        country_id = upsert_country(connection, country_code, country_name)
        city_id = upsert_city(connection, country_id, city_name)
        upsert_location(connection, location_id, city_id, location_name)
        upsert_sensor(connection, sensor_id, location_id, parameter_name, parameter_display_name, unit)

        measurements = fetch_measurements(api_key, sensor_id, date_from, date_to)
        inserted = save_measurements(connection, sensor_id, measurements, unit)
        connection.commit()
    finally:
        connection.close()

    print(f"Fetched {len(measurements)} measurements, inserted {inserted} new rows.")


if __name__ == "__main__":
    main()
