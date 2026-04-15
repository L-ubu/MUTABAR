"""
tests/test_persistence.py
Tests for persistence/database.py and persistence/config.py.
"""

import json
import os
import sqlite3
import tempfile

import pytest

from persistence.database import MutabarDB
from persistence.config import MutabarConfig


# ===========================================================================
# MutabarDB tests
# ===========================================================================


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = MutabarDB(db_path)
    yield db
    db.close()


class TestMutabarDBSchema:
    def test_creates_expected_tables(self, tmp_db):
        tables = tmp_db.list_tables()
        assert "monsters" in tables
        assert "runs" in tables
        assert "unlocks" in tables

    def test_list_tables_returns_list(self, tmp_db):
        result = tmp_db.list_tables()
        assert isinstance(result, list)


class TestMutabarDBMonsters:
    def test_save_monster_returns_int(self, tmp_db):
        row_id = tmp_db.save_monster(name="Wolf", species="Wolf", category="ANIMAL")
        assert isinstance(row_id, int)
        assert row_id >= 1

    def test_save_and_load_monster(self, tmp_db):
        tmp_db.save_monster(
            name="Dragon",
            species="Dragon",
            category="MYTHOLOGICAL",
            level=3,
            xp=50,
            hp=180,
            atk=18,
            defense=15,
        )
        monsters = tmp_db.load_all_monsters()
        assert len(monsters) == 1
        m = monsters[0]
        assert m["name"] == "Dragon"
        assert m["category"] == "MYTHOLOGICAL"
        assert m["level"] == 3

    def test_save_multiple_monsters_preserves_order(self, tmp_db):
        tmp_db.save_monster(name="Alpha")
        tmp_db.save_monster(name="Beta")
        tmp_db.save_monster(name="Gamma")
        monsters = tmp_db.load_all_monsters()
        assert [m["name"] for m in monsters] == ["Alpha", "Beta", "Gamma"]

    def test_traits_serialized_as_list(self, tmp_db):
        traits = ["Pack Hunter", "Feral Bite"]
        tmp_db.save_monster(name="Wolf", traits=traits)
        monsters = tmp_db.load_all_monsters()
        assert monsters[0]["traits"] == traits

    def test_traits_stored_as_json_string(self, tmp_db):
        traits_str = '["Roar", "Mane Guard"]'
        tmp_db.save_monster(name="Lion", traits=traits_str)
        monsters = tmp_db.load_all_monsters()
        # Should deserialize JSON strings back to list
        assert monsters[0]["traits"] == ["Roar", "Mane Guard"]

    def test_load_all_monsters_empty(self, tmp_db):
        assert tmp_db.load_all_monsters() == []

    def test_save_monster_with_fusion_parents(self, tmp_db):
        row_id = tmp_db.save_monster(
            name="FusionBeast",
            fusion_parent_1="Wolf",
            fusion_parent_2="Dragon",
        )
        monsters = tmp_db.load_all_monsters()
        assert monsters[0]["fusion_parent_1"] == "Wolf"
        assert monsters[0]["fusion_parent_2"] == "Dragon"


class TestMutabarDBRuns:
    def test_start_run_returns_int(self, tmp_db):
        run_id = tmp_db.start_run()
        assert isinstance(run_id, int)
        assert run_id >= 1

    def test_start_run_creates_row(self, tmp_db):
        run_id = tmp_db.start_run()
        runs = tmp_db.load_all_runs()
        assert len(runs) == 1
        assert runs[0]["id"] == run_id

    def test_end_run_updates_row(self, tmp_db):
        run_id = tmp_db.start_run()
        tmp_db.end_run(run_id, waves_survived=5, mutagen_earned=120)
        runs = tmp_db.load_all_runs()
        r = runs[0]
        assert r["waves_survived"] == 5
        assert r["mutagen_earned"] == 120
        assert r["ended_at"] is not None

    def test_load_all_runs_empty(self, tmp_db):
        assert tmp_db.load_all_runs() == []

    def test_multiple_runs(self, tmp_db):
        id1 = tmp_db.start_run()
        id2 = tmp_db.start_run()
        tmp_db.end_run(id1, 3, 60)
        tmp_db.end_run(id2, 7, 200)
        runs = tmp_db.load_all_runs()
        assert len(runs) == 2
        assert runs[0]["waves_survived"] == 3
        assert runs[1]["waves_survived"] == 7

    def test_get_total_mutagen_empty(self, tmp_db):
        assert tmp_db.get_total_mutagen() == 0

    def test_get_total_mutagen_sum(self, tmp_db):
        id1 = tmp_db.start_run()
        id2 = tmp_db.start_run()
        tmp_db.end_run(id1, 2, 50)
        tmp_db.end_run(id2, 4, 150)
        assert tmp_db.get_total_mutagen() == 200

    def test_get_total_mutagen_partial_ended(self, tmp_db):
        id1 = tmp_db.start_run()
        _id2 = tmp_db.start_run()  # never ended → mutagen_earned stays 0
        tmp_db.end_run(id1, 1, 100)
        assert tmp_db.get_total_mutagen() == 100


# ===========================================================================
# MutabarConfig tests
# ===========================================================================


@pytest.fixture
def tmp_config_path(tmp_path):
    return str(tmp_path / "config.json")


class TestMutabarConfigDefaults:
    def test_default_theme(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.theme == "tokyo_night"

    def test_default_llm_temperature(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.llm_temperature == pytest.approx(0.8)

    def test_default_llm_max_tokens(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.llm_max_tokens == 60

    def test_default_llm_n_gpu_layers(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.llm_n_gpu_layers == -1

    def test_default_llm_n_ctx(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.llm_n_ctx == 4096

    def test_default_typewriter_speed(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.typewriter_speed == 30


class TestMutabarConfigSaveReload:
    def test_save_creates_file(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        cfg.save()
        assert os.path.isfile(tmp_config_path)

    def test_save_and_reload_theme(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        cfg.theme = "dracula"
        cfg.save()

        cfg2 = MutabarConfig(tmp_config_path)
        assert cfg2.theme == "dracula"

    def test_save_and_reload_llm_temperature(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        cfg.llm_temperature = 0.3
        cfg.save()

        cfg2 = MutabarConfig(tmp_config_path)
        assert cfg2.llm_temperature == pytest.approx(0.3)

    def test_save_and_reload_llm_max_tokens(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        cfg.llm_max_tokens = 256
        cfg.save()

        cfg2 = MutabarConfig(tmp_config_path)
        assert cfg2.llm_max_tokens == 256

    def test_save_and_reload_typewriter_speed(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        cfg.typewriter_speed = 60
        cfg.save()

        cfg2 = MutabarConfig(tmp_config_path)
        assert cfg2.typewriter_speed == 60

    def test_partial_file_preserves_defaults(self, tmp_config_path):
        """A config file with only some keys should still have correct defaults."""
        with open(tmp_config_path, "w") as fh:
            json.dump({"theme": "nord"}, fh)

        cfg = MutabarConfig(tmp_config_path)
        assert cfg.theme == "nord"
        assert cfg.llm_temperature == pytest.approx(0.8)
        assert cfg.typewriter_speed == 30

    def test_nonexistent_path_uses_defaults(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path + ".nonexistent")
        assert cfg.theme == "tokyo_night"
        assert cfg.llm_n_ctx == 4096


class TestMutabarDBSchemaV2:
    def test_wallet_table_exists_with_seed_row(self, tmp_db):
        cursor = tmp_db._conn.execute("SELECT mutagen FROM wallet WHERE id = 1;")
        row = cursor.fetchone()
        assert row is not None
        assert row["mutagen"] == 0

    def test_wallet_id_constraint_rejects_id_2(self, tmp_db):
        with pytest.raises(sqlite3.IntegrityError):
            tmp_db._conn.execute("INSERT INTO wallet (id, mutagen) VALUES (2, 100);")

    def test_monsters_has_is_shiny_column(self, tmp_db):
        cursor = tmp_db._conn.execute("PRAGMA table_info(monsters);")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert "is_shiny" in columns
        assert columns["is_shiny"]["dflt_value"] == "0"
        assert columns["is_shiny"]["notnull"] == 1

    def test_idle_arena_table_exists(self, tmp_db):
        cursor = tmp_db._conn.execute("PRAGMA table_info(idle_arena);")
        columns = {row["name"] for row in cursor.fetchall()}
        assert {"slot", "monster_id"} <= columns

    def test_idle_arena_slot_constraint_rejects_slot_0(self, tmp_db):
        monster_id = tmp_db.save_monster(name="X", species="X")
        with pytest.raises(sqlite3.IntegrityError):
            tmp_db._conn.execute(
                "INSERT INTO idle_arena (slot, monster_id) VALUES (0, ?);", (monster_id,)
            )

    def test_idle_arena_slot_constraint_rejects_slot_4(self, tmp_db):
        monster_id = tmp_db.save_monster(name="X", species="X")
        with pytest.raises(sqlite3.IntegrityError):
            tmp_db._conn.execute(
                "INSERT INTO idle_arena (slot, monster_id) VALUES (4, ?);", (monster_id,)
            )
