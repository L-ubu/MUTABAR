"""
persistence/database.py
SQLite persistence layer for MUTABAR.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


class MutabarDB:
    """Manages the SQLite database for MUTABAR game data."""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self) -> None:
        cursor = self._conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS monsters (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                name             TEXT    NOT NULL,
                species          TEXT,
                category         TEXT,
                mutation_type    TEXT,
                level            INTEGER DEFAULT 1,
                xp               INTEGER DEFAULT 0,
                hp               INTEGER,
                atk              INTEGER,
                defense          INTEGER,
                traits           TEXT,
                fusion_parent_1  TEXT,
                fusion_parent_2  TEXT,
                acquired_from    TEXT,
                is_shiny         INTEGER NOT NULL DEFAULT 0,
                created_at       TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS runs (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at     TEXT    NOT NULL,
                ended_at       TEXT,
                waves_survived INTEGER DEFAULT 0,
                mutagen_earned INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS unlocks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tier        TEXT    NOT NULL,
                unlocked_at TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS wallet (
                id      INTEGER PRIMARY KEY CHECK (id = 1),
                mutagen INTEGER NOT NULL DEFAULT 0
            );
            INSERT OR IGNORE INTO wallet (id, mutagen) VALUES (1, 0);

            CREATE TABLE IF NOT EXISTS idle_arena (
                slot       INTEGER PRIMARY KEY CHECK (slot BETWEEN 1 AND 3),
                monster_id INTEGER NOT NULL REFERENCES monsters(id)
            );
        """)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_tables(self) -> list[str]:
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        return [row[0] for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Monsters
    # ------------------------------------------------------------------

    def save_monster(self, **kwargs: Any) -> int:
        """Insert a monster row and return its lastrowid."""
        # Serialize traits list to JSON string if needed
        if "traits" in kwargs and not isinstance(kwargs["traits"], str):
            kwargs["traits"] = json.dumps(kwargs["traits"])

        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join("?" for _ in kwargs)
        sql = f"INSERT INTO monsters ({columns}) VALUES ({placeholders})"
        cursor = self._conn.execute(sql, list(kwargs.values()))
        self._conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def load_all_monsters(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM monsters ORDER BY id;")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            # Deserialize traits back to list if it's a JSON string
            if d.get("traits") and isinstance(d["traits"], str):
                try:
                    d["traits"] = json.loads(d["traits"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------

    def start_run(self) -> int:
        """Insert a new run row and return its id."""
        started_at = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.execute(
            "INSERT INTO runs (started_at) VALUES (?);",
            (started_at,),
        )
        self._conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def end_run(self, run_id: int, waves_survived: int, mutagen_earned: int) -> None:
        """Update a run row with end data."""
        ended_at = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE runs
            SET ended_at = ?, waves_survived = ?, mutagen_earned = ?
            WHERE id = ?;
            """,
            (ended_at, waves_survived, mutagen_earned, run_id),
        )
        self._conn.commit()

    def load_all_runs(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM runs ORDER BY id;")
        return [dict(row) for row in cursor.fetchall()]

    def get_total_mutagen(self) -> int:
        cursor = self._conn.execute(
            "SELECT COALESCE(SUM(mutagen_earned), 0) FROM runs;"
        )
        return int(cursor.fetchone()[0])

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._conn.close()
