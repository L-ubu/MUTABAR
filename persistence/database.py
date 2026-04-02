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
    # Wallet
    # ------------------------------------------------------------------

    def get_mutagen(self) -> int:
        cursor = self._conn.execute("SELECT mutagen FROM wallet WHERE id = 1;")
        return int(cursor.fetchone()["mutagen"])

    def add_mutagen(self, amount: int) -> None:
        self._conn.execute("UPDATE wallet SET mutagen = mutagen + ? WHERE id = 1;", (amount,))
        self._conn.commit()

    def spend_mutagen(self, amount: int) -> bool:
        if self.get_mutagen() < amount:
            return False
        self._conn.execute("UPDATE wallet SET mutagen = mutagen - ? WHERE id = 1;", (amount,))
        self._conn.commit()
        return True

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def save_creature(self, name: str, species: str, category: str, mutation_type: str,
                      base_hp: int, base_atk: int, base_def: int, traits_json: str, is_shiny: int) -> int:
        cursor = self._conn.execute(
            """INSERT INTO monsters (name, species, category, mutation_type, hp, atk, defense, traits, is_shiny)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
            (name, species, category, mutation_type, base_hp, base_atk, base_def, traits_json, is_shiny),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_collection(self) -> list[dict]:
        cursor = self._conn.execute("SELECT * FROM monsters ORDER BY id;")
        result = []
        for row in cursor.fetchall():
            d = dict(row)
            if d.get("traits") and isinstance(d["traits"], str):
                try:
                    d["traits"] = json.loads(d["traits"])
                except Exception:
                    pass
            result.append(d)
        return result

    def get_discovered_species(self) -> set[str]:
        cursor = self._conn.execute("SELECT DISTINCT species FROM monsters WHERE species IS NOT NULL;")
        return {row["species"] for row in cursor.fetchall()}

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        creatures_discovered = int(self._conn.execute("SELECT COUNT(*) FROM monsters;").fetchone()[0])
        shinies_found = int(self._conn.execute("SELECT COUNT(*) FROM monsters WHERE is_shiny = 1;").fetchone()[0])
        runs_completed = int(self._conn.execute("SELECT COUNT(*) FROM runs WHERE ended_at IS NOT NULL;").fetchone()[0])
        highest_wave = int(self._conn.execute("SELECT COALESCE(MAX(waves_survived), 0) FROM runs;").fetchone()[0])
        total_mutagen = self.get_mutagen()
        return {
            "creatures_discovered": creatures_discovered,
            "shinies_found": shinies_found,
            "runs_completed": runs_completed,
            "highest_wave": highest_wave,
            "total_mutagen": total_mutagen,
        }

    # ------------------------------------------------------------------
    # Idle Arena
    # ------------------------------------------------------------------

    def get_idle_team(self) -> list[dict]:
        cursor = self._conn.execute("""
            SELECT ia.slot, m.* FROM idle_arena ia
            JOIN monsters m ON m.id = ia.monster_id
            ORDER BY ia.slot;
        """)
        result = []
        for row in cursor.fetchall():
            d = dict(row)
            if d.get("traits") and isinstance(d["traits"], str):
                try:
                    d["traits"] = json.loads(d["traits"])
                except Exception:
                    pass
            result.append(d)
        return result

    def set_idle_slot(self, slot: int, monster_id: int) -> None:
        self._conn.execute("INSERT OR REPLACE INTO idle_arena (slot, monster_id) VALUES (?, ?);", (slot, monster_id))
        self._conn.commit()

    def clear_idle_slot(self, slot: int) -> None:
        self._conn.execute("DELETE FROM idle_arena WHERE slot = ?;", (slot,))
        self._conn.commit()

    def get_idle_monster_ids(self) -> set[int]:
        cursor = self._conn.execute("SELECT monster_id FROM idle_arena;")
        return {row["monster_id"] for row in cursor.fetchall()}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._conn.close()
