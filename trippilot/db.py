"""SQLite persistence for TripPilot — gives the skill session memory.

A trip is the unit of state: destination, dates, budget, interests,
generated itinerary and weather snapshot. All JSON fields are stored as text.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT '',
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    budget_usd REAL NOT NULL DEFAULT 0,
    budget_local REAL NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    interests TEXT NOT NULL DEFAULT '[]',
    itinerary TEXT NOT NULL DEFAULT '[]',
    weather TEXT NOT NULL DEFAULT '{}',
    notes TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def db_path() -> str:
    path = os.environ.get("TRIPPILOT_DB")
    if path:
        return path
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(here, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "trips.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_trip(record: dict) -> int:
    conn = connect()
    try:
        cur = conn.execute(
            """INSERT INTO trips
               (destination, country, start_date, end_date, budget_usd, budget_local,
                currency, interests, itinerary, weather, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record["destination"], record.get("country", ""),
                record["start_date"], record["end_date"],
                record.get("budget_usd", 0), record.get("budget_local", 0),
                record.get("currency", "USD"),
                json.dumps(record.get("interests", [])),
                json.dumps(record.get("itinerary", [])),
                json.dumps(record.get("weather", {})),
                json.dumps(record.get("notes", [])),
                _now(), _now(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_trip(trip_id: int) -> dict | None:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def list_trips(limit: int = 20) -> list[dict]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM trips ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def add_note(trip_id: int, note: str) -> bool:
    trip = get_trip(trip_id)
    if not trip:
        return False
    notes = trip["notes"] + [{"at": _now(), "text": note}]
    conn = connect()
    try:
        conn.execute(
            "UPDATE trips SET notes = ?, updated_at = ? WHERE id = ?",
            (json.dumps(notes), _now(), trip_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def delete_trip(trip_id: int) -> bool:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for key in ("interests", "itinerary", "weather", "notes"):
        d[key] = json.loads(d[key]) if d[key] else ([] if key != "weather" else {})
    return d
