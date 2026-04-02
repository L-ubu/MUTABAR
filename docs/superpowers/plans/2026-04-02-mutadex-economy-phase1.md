# Phase 1: Mutadex Economy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform MUTABAR from a simple wave battler into a collectible creature game with persistent progression, shiny system, mutabox shop, and idle arena.

**Architecture:** New DB tables (wallet, idle_arena) + is_shiny column. New screens plug into `_switch_screen()` in `main.py`. Lootbox system gains MutaboxTier enum with custom weights. TextBuffer gains animated rendering for rarity FX.

**Tech Stack:** Python 3.11+, pygame-ce 2.5.7, SQLite3, PyObjC (macOS)

**Spec:** `docs/superpowers/specs/2026-04-02-mutadex-economy-phase1-design.md`

---

## Codebase Module Reference

**IMPORTANT:** Subagents MUST use these exact import paths — not guesses.

```
game/screens/base.py       → Screen, Action (re-exported from game.input_handler)
game/renderer.py           → TextBuffer, Cell
game/theme.py              → Theme, get_theme, list_themes
game/input_handler.py      → Action enum, pygame_event_to_action
game/creatures/creature.py → Creature, CreatureCategory
game/creatures/types.py    → MutationType
game/creatures/traits.py   → Trait, compute_trait_bonus
game/creatures/database.py → CREATURE_ROSTER, CreatureTemplate, get_creature_by_name
game/progression/lootbox.py → Rarity, RollResult, roll_creature, get_rarity_weights
game/progression/run_manager.py → RunManager, RunState
game/progression/unlocks.py → UnlockManager
game/battle/engine.py      → Battle, BattleState, TurnResult
game/battle/damage.py      → calculate_damage, DamageResult
persistence/database.py    → MutabarDB
persistence/config.py      → MutabarConfig
main.py                    → MutabarApp
```

**Theme properties:** `bg_color`, `text_color`, `dim_text_color`, `accent_color`, `border_color`, `highlight_color`, `type_colors`

**TextBuffer methods:** `clear()`, `write(x, y, text, color)`, `draw_box(x, y, w, h, color)`, `draw_hp_bar(x, y, w, cur, max, fill_color, empty_color)`, `render_to_surface(surface, font, bg_color)` — Grid is 43 cols × 26 rows.

**Screen pattern:** `__init__(buffer, theme)`, `handle_input(action, char) -> str | None`, `update(dt)`, `draw()`

---

## Part 1: Database, Currency & Config (Tasks 1–4)

### Task 1: Schema Migration — `wallet`, `is_shiny`, and `idle_arena`

**Files:**
- Modify: `persistence/database.py`
- Test: `tests/test_persistence.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_persistence.py` — add `import sqlite3` at top:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_persistence.py::TestMutabarDBSchemaV2 -v`

- [ ] **Step 3: Implement**

In `persistence/database.py`, update `_create_tables` to add the new tables and column:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_persistence.py::TestMutabarDBSchemaV2 -v`

- [ ] **Step 5: Commit**

```
git add persistence/database.py tests/test_persistence.py
git commit -m "feat: add wallet, is_shiny, idle_arena schema"
```

---

### Task 2: DB Methods — Wallet, Collection, Species, Stats

**Files:**
- Modify: `persistence/database.py`
- Test: `tests/test_persistence.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_persistence.py`:

```python
class TestMutabarDBWallet:
    def test_get_mutagen_returns_zero_initially(self, tmp_db):
        assert tmp_db.get_mutagen() == 0

    def test_add_mutagen_increases_balance(self, tmp_db):
        tmp_db.add_mutagen(50)
        assert tmp_db.get_mutagen() == 50

    def test_add_mutagen_accumulates(self, tmp_db):
        tmp_db.add_mutagen(30)
        tmp_db.add_mutagen(20)
        assert tmp_db.get_mutagen() == 50

    def test_spend_mutagen_returns_true_and_deducts(self, tmp_db):
        tmp_db.add_mutagen(100)
        assert tmp_db.spend_mutagen(40) is True
        assert tmp_db.get_mutagen() == 60

    def test_spend_mutagen_returns_false_when_insufficient(self, tmp_db):
        tmp_db.add_mutagen(10)
        assert tmp_db.spend_mutagen(50) is False
        assert tmp_db.get_mutagen() == 10

    def test_spend_mutagen_exact_balance(self, tmp_db):
        tmp_db.add_mutagen(25)
        assert tmp_db.spend_mutagen(25) is True
        assert tmp_db.get_mutagen() == 0


class TestMutabarDBCollection:
    def test_save_creature_returns_int(self, tmp_db):
        cid = tmp_db.save_creature(
            name="Wolf", species="Wolf", category="ANIMAL",
            mutation_type="FIRE", base_hp=70, base_atk=14, base_def=8,
            traits_json='["Pack Hunter"]', is_shiny=0,
        )
        assert isinstance(cid, int) and cid >= 1

    def test_save_creature_persists_is_shiny(self, tmp_db):
        cid = tmp_db.save_creature(
            name="Wolf", species="Wolf", category="ANIMAL",
            mutation_type="FIRE", base_hp=70, base_atk=14, base_def=8,
            traits_json='[]', is_shiny=1,
        )
        row = tmp_db._conn.execute("SELECT is_shiny FROM monsters WHERE id = ?;", (cid,)).fetchone()
        assert row["is_shiny"] == 1

    def test_get_collection_returns_all(self, tmp_db):
        tmp_db.save_creature(name="A", species="A", category="ANIMAL", mutation_type="FIRE", base_hp=50, base_atk=10, base_def=5, traits_json="[]", is_shiny=0)
        tmp_db.save_creature(name="B", species="B", category="ANIMAL", mutation_type="WATER", base_hp=60, base_atk=11, base_def=6, traits_json="[]", is_shiny=1)
        assert len(tmp_db.get_collection()) == 2

    def test_get_discovered_species(self, tmp_db):
        tmp_db.save_creature(name="A", species="Wolf", category="ANIMAL", mutation_type="FIRE", base_hp=50, base_atk=10, base_def=5, traits_json="[]", is_shiny=0)
        tmp_db.save_creature(name="B", species="Wolf", category="ANIMAL", mutation_type="FIRE", base_hp=50, base_atk=10, base_def=5, traits_json="[]", is_shiny=0)
        tmp_db.save_creature(name="C", species="Hawk", category="ANIMAL", mutation_type="AIR", base_hp=50, base_atk=13, base_def=6, traits_json="[]", is_shiny=0)
        assert tmp_db.get_discovered_species() == {"Wolf", "Hawk"}

    def test_get_discovered_species_empty(self, tmp_db):
        assert tmp_db.get_discovered_species() == set()


class TestMutabarDBStats:
    def test_get_stats_keys(self, tmp_db):
        stats = tmp_db.get_stats()
        assert set(stats.keys()) == {"creatures_discovered", "shinies_found", "runs_completed", "highest_wave", "total_mutagen"}

    def test_get_stats_zero_state(self, tmp_db):
        stats = tmp_db.get_stats()
        assert all(v == 0 for v in stats.values())

    def test_get_stats_counts(self, tmp_db):
        tmp_db.save_creature(name="A", species="A", category="ANIMAL", mutation_type="FIRE", base_hp=50, base_atk=10, base_def=5, traits_json="[]", is_shiny=0)
        tmp_db.save_creature(name="B", species="B", category="ANIMAL", mutation_type="FIRE", base_hp=50, base_atk=10, base_def=5, traits_json="[]", is_shiny=1)
        tmp_db.add_mutagen(200)
        run1 = tmp_db.start_run()
        tmp_db.end_run(run1, 5, 50)
        run2 = tmp_db.start_run()
        tmp_db.end_run(run2, 12, 120)
        stats = tmp_db.get_stats()
        assert stats["creatures_discovered"] == 2
        assert stats["shinies_found"] == 1
        assert stats["runs_completed"] == 2
        assert stats["highest_wave"] == 12
        assert stats["total_mutagen"] == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_persistence.py::TestMutabarDBWallet tests/test_persistence.py::TestMutabarDBCollection tests/test_persistence.py::TestMutabarDBStats -v`

- [ ] **Step 3: Implement**

Add to `MutabarDB` class in `persistence/database.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_persistence.py -v`

- [ ] **Step 5: Commit**

```
git add persistence/database.py tests/test_persistence.py
git commit -m "feat: add wallet, collection, species, stats DB methods"
```

---

### Task 3: DB Methods — Idle Arena

**Files:**
- Modify: `persistence/database.py`
- Test: `tests/test_persistence.py`

- [ ] **Step 1: Write failing tests**

```python
class TestMutabarDBIdleArena:
    def _add_creature(self, db, name="Wolf"):
        return db.save_creature(name=name, species=name, category="ANIMAL", mutation_type="FIRE",
                                base_hp=70, base_atk=14, base_def=8, traits_json="[]", is_shiny=0)

    def test_get_idle_team_empty(self, tmp_db):
        assert tmp_db.get_idle_team() == []

    def test_set_and_get_idle_slot(self, tmp_db):
        mid = self._add_creature(tmp_db)
        tmp_db.set_idle_slot(1, mid)
        team = tmp_db.get_idle_team()
        assert len(team) == 1 and team[0]["slot"] == 1

    def test_set_idle_slot_replaces(self, tmp_db):
        m1 = self._add_creature(tmp_db, "A")
        m2 = self._add_creature(tmp_db, "B")
        tmp_db.set_idle_slot(2, m1)
        tmp_db.set_idle_slot(2, m2)
        team = tmp_db.get_idle_team()
        assert len(team) == 1 and team[0]["id"] == m2

    def test_clear_idle_slot(self, tmp_db):
        mid = self._add_creature(tmp_db)
        tmp_db.set_idle_slot(1, mid)
        tmp_db.clear_idle_slot(1)
        assert tmp_db.get_idle_team() == []

    def test_get_idle_monster_ids(self, tmp_db):
        m1 = self._add_creature(tmp_db, "A")
        m2 = self._add_creature(tmp_db, "B")
        tmp_db.set_idle_slot(1, m1)
        tmp_db.set_idle_slot(2, m2)
        assert tmp_db.get_idle_monster_ids() == {m1, m2}

    def test_get_idle_monster_ids_empty(self, tmp_db):
        assert tmp_db.get_idle_monster_ids() == set()

    def test_idle_team_includes_stats(self, tmp_db):
        mid = self._add_creature(tmp_db)
        tmp_db.set_idle_slot(1, mid)
        row = tmp_db.get_idle_team()[0]
        assert "name" in row and "hp" in row and "atk" in row
```

- [ ] **Step 2: Run tests** → `python -m pytest tests/test_persistence.py::TestMutabarDBIdleArena -v`

- [ ] **Step 3: Implement**

```python
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
```

- [ ] **Step 4: Run tests** → `python -m pytest tests/test_persistence.py -v`

- [ ] **Step 5: Commit**

```
git add persistence/database.py tests/test_persistence.py
git commit -m "feat: add idle arena DB methods"
```

---

### Task 4: Config Keys — `sound_enabled` and `idle_last_check`

**Files:**
- Modify: `persistence/config.py`
- Test: `tests/test_persistence.py`

- [ ] **Step 1: Write failing tests**

```python
class TestMutabarConfigSoundAndIdle:
    def test_sound_enabled_default_true(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.sound_enabled is True

    def test_sound_enabled_roundtrip(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        cfg.sound_enabled = False
        cfg.save()
        assert MutabarConfig(tmp_config_path).sound_enabled is False

    def test_idle_last_check_default_none(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        assert cfg.idle_last_check is None

    def test_idle_last_check_roundtrip(self, tmp_config_path):
        cfg = MutabarConfig(tmp_config_path)
        cfg.idle_last_check = "2026-04-01T12:00:00"
        cfg.save()
        assert MutabarConfig(tmp_config_path).idle_last_check == "2026-04-01T12:00:00"
```

- [ ] **Step 2: Run tests** → `python -m pytest tests/test_persistence.py::TestMutabarConfigSoundAndIdle -v`

- [ ] **Step 3: Implement**

In `persistence/config.py`, add to `_DEFAULTS`:

```python
_DEFAULTS = {
    "theme": "tokyo_night",
    "llm": {"n_gpu_layers": -1, "n_ctx": 4096, "n_threads": 4, "temperature": 0.8, "max_tokens": 60},
    "load_side": "right",
    "typewriter_speed": 30,
    "sound_enabled": True,
    "idle_last_check": None,
}
```

Add properties to `MutabarConfig`:

```python
@property
def sound_enabled(self) -> bool:
    return bool(self._data.get("sound_enabled", True))

@sound_enabled.setter
def sound_enabled(self, value: bool) -> None:
    self._data["sound_enabled"] = bool(value)

@property
def idle_last_check(self) -> str | None:
    return self._data.get("idle_last_check", None)

@idle_last_check.setter
def idle_last_check(self, value: str | None) -> None:
    self._data["idle_last_check"] = value
```

- [ ] **Step 4: Run full test suite** → `python -m pytest tests/test_persistence.py -v`

- [ ] **Step 5: Commit**

```
git add persistence/config.py tests/test_persistence.py
git commit -m "feat: add sound_enabled and idle_last_check config keys"
```

---

## Part 2: Shiny System, Mutabox Tiers & Lootbox Rework (Tasks 5–8)

### Task 5: Add `is_shiny` to `Creature` with +15% Stat Boost

**Files:**
- Modify: `game/creatures/creature.py`
- Test: `tests/test_creature_shiny.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_creature_shiny.py`:

```python
from game.creatures.creature import Creature, CreatureCategory
from game.creatures.types import MutationType

def _make(**kw):
    defaults = dict(name="T", category=CreatureCategory.ANIMAL, mutation_type=MutationType.FIRE,
                    traits=[], base_hp=100, base_atk=50, base_def=40)
    defaults.update(kw)
    return Creature(**defaults)

def test_is_shiny_defaults_false():
    assert _make().is_shiny is False

def test_non_shiny_stats_unchanged():
    c = _make()
    assert c.base_hp == 100 and c.base_atk == 50 and c.base_def == 40

def test_shiny_stat_boost():
    c = _make(is_shiny=True)
    assert c.base_hp == 115 and c.base_atk == 58 and c.base_def == 46

def test_shiny_rounding():
    c = _make(base_hp=33, base_atk=33, base_def=33, is_shiny=True)
    assert c.base_hp == 38 and c.base_atk == 38 and c.base_def == 38

def test_shiny_current_hp_matches_max():
    c = _make(is_shiny=True)
    assert c.current_hp == c.max_hp == 115
```

- [ ] **Step 2: Run** → `python -m pytest tests/test_creature_shiny.py -v`

- [ ] **Step 3: Implement**

In `game/creatures/creature.py`, add `is_shiny` field and boost in `__post_init__`:

```python
from typing import ClassVar

@dataclass
class Creature:
    name: str
    category: CreatureCategory
    mutation_type: MutationType
    traits: List[Trait]
    base_hp: int
    base_atk: int
    base_def: int
    level: int = 1
    xp: int = 0
    is_shiny: bool = False
    current_hp: int = field(init=False)

    _SHINY_BOOST: ClassVar[float] = 1.15

    def __post_init__(self):
        if self.is_shiny:
            self.base_hp = round(self.base_hp * self._SHINY_BOOST)
            self.base_atk = round(self.base_atk * self._SHINY_BOOST)
            self.base_def = round(self.base_def * self._SHINY_BOOST)
        self.current_hp = self.max_hp
```

- [ ] **Step 4: Run** → `python -m pytest tests/test_creature_shiny.py -v`

- [ ] **Step 5: Commit**

```
git add game/creatures/creature.py tests/test_creature_shiny.py
git commit -m "feat: add is_shiny field with +15% stat boost"
```

---

### Task 6: Create `MutaboxTier` Enum

**Files:**
- Create: `game/progression/mutabox.py`
- Test: `tests/test_mutabox.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_mutabox.py`:

```python
import pytest
from game.progression.mutabox import MutaboxTier
from game.progression.lootbox import Rarity

def test_standard_cost():
    assert MutaboxTier.STANDARD.cost == 50

def test_premium_cost():
    assert MutaboxTier.PREMIUM.cost == 150

def test_shiny_cost():
    assert MutaboxTier.SHINY.cost == 300

def test_standard_weights():
    w = MutaboxTier.STANDARD.rarity_weights
    assert w[Rarity.COMMON] == 50 and w[Rarity.LEGENDARY] == 1

def test_premium_weights():
    w = MutaboxTier.PREMIUM.rarity_weights
    assert w[Rarity.COMMON] == 25 and w[Rarity.RARE] == 25 and w[Rarity.LEGENDARY] == 5

def test_shiny_uses_standard_weights():
    assert MutaboxTier.SHINY.rarity_weights == MutaboxTier.STANDARD.rarity_weights

def test_standard_shiny_chance():
    assert MutaboxTier.STANDARD.shiny_chance == pytest.approx(0.01)

def test_shiny_tier_shiny_chance():
    assert MutaboxTier.SHINY.shiny_chance == pytest.approx(0.05)

def test_all_weights_sum_100():
    for tier in MutaboxTier:
        assert sum(tier.rarity_weights.values()) == pytest.approx(100.0)
```

- [ ] **Step 2: Run** → `python -m pytest tests/test_mutabox.py -v`

- [ ] **Step 3: Implement**

Create `game/progression/mutabox.py`:

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from game.progression.lootbox import Rarity, RollResult, roll_creature

@dataclass(frozen=True)
class _TierConfig:
    cost: int
    rarity_weights: dict[Rarity, float]
    shiny_chance: float

_STANDARD_WEIGHTS = {Rarity.COMMON: 50.0, Rarity.UNCOMMON: 30.0, Rarity.RARE: 15.0, Rarity.EPIC: 4.0, Rarity.LEGENDARY: 1.0}
_PREMIUM_WEIGHTS = {Rarity.COMMON: 25.0, Rarity.UNCOMMON: 30.0, Rarity.RARE: 25.0, Rarity.EPIC: 15.0, Rarity.LEGENDARY: 5.0}

class MutaboxTier(Enum):
    STANDARD = _TierConfig(cost=50, rarity_weights=_STANDARD_WEIGHTS, shiny_chance=0.01)
    PREMIUM = _TierConfig(cost=150, rarity_weights=_PREMIUM_WEIGHTS, shiny_chance=0.01)
    SHINY = _TierConfig(cost=300, rarity_weights=_STANDARD_WEIGHTS, shiny_chance=0.05)

    @property
    def cost(self) -> int: return self.value.cost
    @property
    def rarity_weights(self) -> dict[Rarity, float]: return self.value.rarity_weights
    @property
    def shiny_chance(self) -> float: return self.value.shiny_chance

def open_mutabox(tier: MutaboxTier) -> RollResult:
    return roll_creature(wave=1, unlocked_tiers=set(), rarity_weights=tier.rarity_weights, shiny_chance=tier.shiny_chance)
```

- [ ] **Step 4: Run** → `python -m pytest tests/test_mutabox.py -v`

- [ ] **Step 5: Commit**

```
git add game/progression/mutabox.py tests/test_mutabox.py
git commit -m "feat: add MutaboxTier enum with STANDARD/PREMIUM/SHINY"
```

---

### Task 7: Rework `roll_creature()` — Custom Weights + Shiny

**Files:**
- Modify: `game/progression/lootbox.py`
- Test: `tests/test_lootbox_rework.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_lootbox_rework.py`:

```python
import pytest
from unittest.mock import patch
from game.progression.lootbox import RollResult, roll_creature, Rarity

def test_roll_result_has_is_shiny():
    result = roll_creature(wave=1, unlocked_tiers=set())
    assert hasattr(result, "is_shiny")

def test_shiny_false_when_random_high():
    with patch("game.progression.lootbox.random.random", return_value=0.99):
        assert roll_creature(wave=1, unlocked_tiers=set()).is_shiny is False

def test_shiny_true_when_random_low():
    with patch("game.progression.lootbox.random.random", return_value=0.005):
        assert roll_creature(wave=1, unlocked_tiers=set()).is_shiny is True

def test_custom_weights_override():
    w = {Rarity.COMMON: 0, Rarity.UNCOMMON: 0, Rarity.RARE: 0, Rarity.EPIC: 0, Rarity.LEGENDARY: 100}
    for _ in range(20):
        assert roll_creature(wave=1, unlocked_tiers=set(), rarity_weights=w).rarity == Rarity.LEGENDARY

def test_custom_shiny_chance_zero():
    with patch("game.progression.lootbox.random.random", return_value=0.0):
        assert roll_creature(wave=1, unlocked_tiers=set(), shiny_chance=0.0).is_shiny is False

def test_custom_shiny_chance_one():
    with patch("game.progression.lootbox.random.random", return_value=0.5):
        assert roll_creature(wave=1, unlocked_tiers=set(), shiny_chance=1.0).is_shiny is True
```

- [ ] **Step 2: Run** → `python -m pytest tests/test_lootbox_rework.py -v`

- [ ] **Step 3: Implement**

Update `game/progression/lootbox.py`:

```python
_DEFAULT_SHINY_CHANCE: float = 0.01

@dataclass
class RollResult:
    rarity: Rarity
    template: CreatureTemplate
    strip: list[CreatureTemplate]
    winner_index: int
    is_shiny: bool = False

def roll_creature(
    wave: int, unlocked_tiers: set[str],
    rarity_weights: dict[Rarity, float] | None = None,
    shiny_chance: float = _DEFAULT_SHINY_CHANCE,
) -> RollResult:
    weights = rarity_weights if rarity_weights is not None else get_rarity_weights(wave, unlocked_tiers)
    available = [r for r, w in weights.items() if w > 0]
    w_values = [weights[r] for r in available]
    winning_rarity = random.choices(available, weights=w_values, k=1)[0]
    pool = _RARITY_POOLS[winning_rarity]
    winner = random.choice(pool)
    strip_size = 20
    strip = list(random.choices(CREATURE_ROSTER, k=strip_size))
    winner_index = strip_size - random.randint(2, 5)
    strip.insert(winner_index, winner)
    is_shiny = random.random() < shiny_chance
    return RollResult(rarity=winning_rarity, template=winner, strip=strip, winner_index=winner_index, is_shiny=is_shiny)
```

- [ ] **Step 4: Run** → `python -m pytest tests/test_lootbox_rework.py -v`

- [ ] **Step 5: Commit**

```
git add game/progression/lootbox.py tests/test_lootbox_rework.py
git commit -m "feat: add is_shiny to RollResult, custom weights/shiny params"
```

---

### Task 8: `open_mutabox()` Integration Test

**Files:**
- Test: `tests/test_mutabox.py` (append)

- [ ] **Step 1: Write tests**

Append to `tests/test_mutabox.py`:

```python
from unittest.mock import patch
from game.progression.mutabox import open_mutabox

def test_open_mutabox_returns_roll_result():
    from game.progression.lootbox import RollResult
    assert isinstance(open_mutabox(MutaboxTier.STANDARD), RollResult)

def test_open_mutabox_shiny_tier_triggers():
    with patch("game.progression.lootbox.random.random", return_value=0.04):
        assert open_mutabox(MutaboxTier.SHINY).is_shiny is True

def test_open_mutabox_standard_does_not_trigger_at_same_value():
    with patch("game.progression.lootbox.random.random", return_value=0.04):
        assert open_mutabox(MutaboxTier.STANDARD).is_shiny is False
```

- [ ] **Step 2: Run** → `python -m pytest tests/test_mutabox.py -v`

- [ ] **Step 3: Commit**

```
git add tests/test_mutabox.py
git commit -m "test: add open_mutabox integration tests"
```

---

## Part 3: Mutadex Hub Screen (Tasks 9–12)

### Task 9: MutadexScreen Shell + Tab Navigation + Collection Tab

**Files:**
- Create: `game/screens/mutadex.py`
- Test: `tests/test_mutadex.py`

- [ ] **Step 1: Write tests**

Create `tests/test_mutadex.py`. The screen takes `(buffer, theme, db)`. Test tab navigation (LEFT/RIGHT wrapping over 4 tabs), ESC returns `"main_menu"`, Collection tab shows discovered/undiscovered creatures, scroll with UP/DOWN, Enter on discovered opens detail view, BACK from detail closes it. Use mock DB returning controlled data. See spec section 5 for full requirements.

Key test cases:
- `test_initial_tab_is_0`
- `test_right_advances_tab`
- `test_left_wraps_from_0_to_3`
- `test_right_wraps_from_3_to_0`
- `test_esc_returns_main_menu`
- `test_collection_scroll_down`
- `test_collection_enter_discovered_opens_detail`
- `test_collection_enter_undiscovered_does_nothing`
- `test_collection_detail_shows_count_and_shiny_count`
- `test_back_from_detail_closes_it`

- [ ] **Step 2: Run tests to verify failure**

- [ ] **Step 3: Implement `game/screens/mutadex.py`**

The MutadexScreen constructor: `__init__(self, buffer, theme, db)` where `db` is a `MutabarDB` instance. Store `self.db = db`. Use `CREATURE_ROSTER` from `game.creatures.database` as the template list (53 creatures). The screen has `active_tab: int` (0-3), `TABS = ["Collection", "Shop", "Idle", "Stats"]`.

Collection tab: scrollable list of CREATURE_ROSTER sorted by name. Check `db.get_discovered_species()` to mark discovered vs `???`. Detail view stores selected creature info with owned count and shiny count from `db.get_collection()`.

Shop/Idle/Stats tabs: stub with placeholder text for now (tasks 10-12).

Draw tab bar at top, divider on row 2, content below.

- [ ] **Step 4: Run tests** → `python -m pytest tests/test_mutadex.py -v`

- [ ] **Step 5: Commit**

```
git add game/screens/mutadex.py tests/test_mutadex.py
git commit -m "feat: add MutadexScreen with tab navigation and Collection tab"
```

---

### Task 10: Mutadex Shop Tab

**Files:**
- Modify: `game/screens/mutadex.py`
- Test: `tests/test_mutadex.py` (append)

- [ ] **Step 1: Write tests**

Test shop tab behavior:
- UP/DOWN navigates 3 tiers (STANDARD=0, PREMIUM=1, SHINY=2), clamped
- Enter on unaffordable tier does nothing
- Enter on affordable tier calls `db.spend_mutagen(cost)` and returns `"open_mutabox"`
- Screen stores `pending_mutabox_tier` so main.py knows which tier was chosen
- Draw shows mutagen balance formatted with commas

- [ ] **Step 2: Implement shop tab**

Replace `_handle_shop` and `_draw_shop` stubs. Define `_SHOP_TIERS` list with key/cost/label/desc for each tier. On CONFIRM: check `db.get_mutagen() >= cost`, call `db.spend_mutagen(cost)`, set `self.pending_mutabox_tier`, return `"open_mutabox"`.

- [ ] **Step 3: Run tests + commit**

---

### Task 11: Mutadex Idle Arena Tab

**Files:**
- Modify: `game/screens/mutadex.py`
- Test: `tests/test_mutadex.py` (append)

- [ ] **Step 1: Write tests**

Test idle tab: 3 slots, Enter on empty enters picking mode, Enter on filled calls `db.clear_idle_slot()`, picking mode shows eligible creatures (excluding already-idle), Enter in picking calls `db.set_idle_slot()`, ESC from picking returns to slots, earnings rate calculation.

- [ ] **Step 2: Implement**

Replace `_handle_idle` and `_draw_idle` stubs. Add `idle_picking`, `idle_pick_selected`, `idle_pick_scroll` state. Earnings rate: `len(idle_team) * base_rate` (detailed calc in task 20).

- [ ] **Step 3: Run tests + commit**

---

### Task 12: Mutadex Stats Tab

**Files:**
- Modify: `game/screens/mutadex.py`
- Test: `tests/test_mutadex.py` (append)

- [ ] **Step 1: Write tests**

Test stats tab displays all 5 stats from `db.get_stats()`: creatures discovered X/53, shinies found, runs completed, highest wave, total mutagen earned (formatted with commas).

- [ ] **Step 2: Implement**

Replace `_draw_stats` stub. Call `db.get_stats()`, render each stat on its own row with label + value.

- [ ] **Step 3: Run tests + commit**

---

## Part 4: Team Select, Run Flow & Main Menu (Tasks 13–16)

### Task 13: TeamSelectScreen

**Files:**
- Create: `game/screens/team_select.py`
- Test: `tests/test_team_select.py`

- [ ] **Step 1: Write tests**

Test: screen takes `(buffer, theme, db)`, lists creatures excluding idle monster IDs, Enter toggles selection (★ marker), max 3 selected, S key returns `"start_run"` when ≥1 selected, ESC returns `"main_menu"`, `selected_team` property returns `Creature` objects instantiated from DB rows (with shiny boost).

- [ ] **Step 2: Implement**

Constructor: loads `db.load_all_monsters()`, filters out `db.get_idle_monster_ids()`. Stores `available: list[dict]`, `cursor: int`, `selected_indices: set[int]`.

Helper `creature_from_db_row(row) -> Creature`:
```python
import json
from game.creatures.creature import Creature, CreatureCategory
from game.creatures.types import MutationType
from game.creatures.traits import Trait

def creature_from_db_row(row: dict) -> Creature:
    traits_raw = row.get("traits", [])
    if isinstance(traits_raw, str):
        traits_raw = json.loads(traits_raw)
    traits = [Trait(name=t, description="", keywords=[]) if isinstance(t, str) else t for t in traits_raw]
    return Creature(
        name=row["name"],
        category=CreatureCategory(row["category"].lower()) if row.get("category") else CreatureCategory.ANIMAL,
        mutation_type=MutationType[row["mutation_type"]] if row.get("mutation_type") else MutationType.FIRE,
        traits=traits,
        base_hp=row.get("hp", 50),
        base_atk=row.get("atk", 10),
        base_def=row.get("defense", 10),
        level=row.get("level", 1),
        xp=row.get("xp", 0),
        is_shiny=bool(row.get("is_shiny", 0)),
    )
```

Draw: Header `SELECT YOUR TEAM (1-3)`, scrollable list with `name | TYPE | HP/ATK/DEF | ✦`, selected count, `[S] Start Run` hint.

- [ ] **Step 3: Run tests + commit**

---

### Task 14: WaveCompleteScreen + RunOverScreen

**Files:**
- Create: `game/screens/wave_complete.py`
- Create: `game/screens/run_over.py`
- Test: `tests/test_wave_run_screens.py`

- [ ] **Step 1: Write tests**

WaveCompleteScreen: takes `(buffer, theme, wave, mutagen_this_wave, mutagen_run_total)`. Enter returns `"next_wave"`. Draw shows wave number, mutagen earned, running total.

RunOverScreen: takes `(buffer, theme, waves_survived, mutagen_earned, run_id, db)`. On init: calls `db.add_mutagen(mutagen_earned)` and `db.end_run(run_id, waves_survived, mutagen_earned)`. Enter returns `"main_menu"`. Does NOT bank twice on redraw.

- [ ] **Step 2: Implement both screens**

- [ ] **Step 3: Run tests + commit**

---

### Task 15: MainMenu Update + main.py Routing

**Files:**
- Modify: `game/screens/main_menu.py`
- Modify: `main.py`
- Test: `tests/test_main_menu.py`

- [ ] **Step 1: Write tests**

Test MainMenu has 4 items: "Start Run", "Mutadex", "Settings", "Quit". Selecting "Mutadex" returns `"mutadex"`.

- [ ] **Step 2: Update MainMenu**

```python
ITEMS = ["Start Run", "Mutadex", "Settings", "Quit"]
```

Add `"Mutadex"` mapping in `handle_input`:
```python
elif item == "Mutadex":
    return "mutadex"
```

- [ ] **Step 3: Update `_switch_screen` in `main.py`**

Add new routes:
- `"run"` → Create RunManager, start run in DB, show TeamSelectScreen
- `"start_run"` → Get `selected_team` from TeamSelectScreen, set on RunManager, advance wave, create Battle
- `"wave_complete"` → Show WaveCompleteScreen with mutagen info
- `"next_wave"` → Advance wave, heal team, create new Battle
- `"run_over"` → Show RunOverScreen (banks mutagen), clear run state
- `"mutadex"` → Show MutadexScreen(buffer, theme, db)
- `"open_mutabox"` → Get `pending_mutabox_tier` from MutadexScreen, call `open_mutabox(tier)`, show LootboxScreen
- `"post_lootbox"` → Save creature to DB, return to MutadexScreen

Add new imports at top of main.py, add `self._run_id`, `self._mutagen_run_total` attributes.

- [ ] **Step 4: Run tests + commit**

---

### Task 16: Starter Creature Seeding + Mutagen Earning

**Files:**
- Create: `game/progression/starters.py`
- Create: `game/progression/mutagen.py`
- Modify: `main.py`
- Test: `tests/test_starters.py`, `tests/test_mutagen.py`

- [ ] **Step 1: Write tests for seeding**

`seed_starters_if_needed(db)`: if `db.load_all_monsters()` is empty, insert Wolf (FIRE), Crab (WATER), Hawk (AIR) using `db.save_creature()`. Does nothing if monsters exist.

- [ ] **Step 2: Write tests for mutagen earning**

`calculate_wave_mutagen(wave, super_effective_kill=False, crit_kill=False) -> int`:
- Base: `wave * 5`
- +50% if super effective kill (× 1.5)
- +25% if crit kill (× 1.25)
- Stack multiplicatively, round to int

- [ ] **Step 3: Implement both**

`game/progression/starters.py`:
```python
from game.creatures.database import get_creature_by_name

_STARTERS = [
    ("Wolf", "FIRE"),
    ("Crab", "WATER"),
    ("Hawk", "AIR"),
]

def seed_starters_if_needed(db) -> None:
    if db.load_all_monsters():
        return
    for name, mutation_type in _STARTERS:
        tmpl = get_creature_by_name(name)
        if tmpl:
            import json
            db.save_creature(
                name=tmpl.name, species=tmpl.name, category=tmpl.category.value.upper(),
                mutation_type=mutation_type, base_hp=tmpl.base_hp, base_atk=tmpl.base_atk,
                base_def=tmpl.base_def, traits_json=json.dumps([t.name for t in tmpl.traits]),
                is_shiny=0,
            )
```

`game/progression/mutagen.py`:
```python
def calculate_wave_mutagen(wave: int, super_effective_kill: bool = False, crit_kill: bool = False) -> int:
    base = wave * 5
    if base == 0:
        return 0
    mult = 1.0
    if super_effective_kill:
        mult *= 1.5
    if crit_kill:
        mult *= 1.25
    return round(base * mult)
```

Call `seed_starters_if_needed(self.db)` in `MutabarApp.__init__` after DB init.

- [ ] **Step 4: Run tests + commit**

---

## Part 5: Rarity FX, Sound, Animated Renderer & Idle Earnings (Tasks 17–20)

### Task 17: Animated Renderer + Cell Animation Field

**Files:**
- Modify: `game/renderer.py`
- Test: `tests/test_renderer_animated.py`

- [ ] **Step 1: Write tests**

Test `Cell` gains `animation: str | None = None`. Test `write_animated(x, y, text, color, animation)` stores animation tag on cells. Test `render_to_surface_animated(surface, font, bg_color, time)` applies color transforms for `pulse`, `shimmer`, `glow`, `rainbow`. Test each transform is a pure function returning valid RGB tuple.

- [ ] **Step 2: Implement**

Add `animation` to Cell, add `write_animated`, add 4 transform functions (pulse/shimmer/glow/rainbow), add `_hsv_to_rgb` helper, add `render_to_surface_animated`. Update main.py render loop to use animated render when `getattr(screen, "needs_animation", False)` is True.

- [ ] **Step 3: Run tests + commit**

---

### Task 18: Rarity FX on LootboxScreen + Shiny Flash

**Files:**
- Modify: `game/screens/lootbox.py`
- Test: `tests/test_lootbox_fx.py`

- [ ] **Step 1: Write tests**

Test reveal phase sets `needs_animation = True`. Test rarity→animation mapping (Common=None, Uncommon=pulse, Rare=shimmer, Epic=glow, Legendary=rainbow). Test shiny roll prefixes name with `✦` and uses rainbow animation. Test 3-frame white flash before reveal.

- [ ] **Step 2: Implement**

Add `flash_frames`, `needs_animation` to LootboxScreen. On reveal transition: `flash_frames = 3`, `needs_animation = True`. In draw: if `flash_frames > 0`, fill surface white and return. Use `write_animated` for border and name with rarity-appropriate animation. Shiny name: `✦ {name}` with rainbow animation.

Rarity color map:
```python
{Rarity.COMMON: (120,120,120), Rarity.UNCOMMON: (158,206,106), Rarity.RARE: (122,162,247),
 Rarity.EPIC: (187,154,247), Rarity.LEGENDARY: (224,175,104)}
```

- [ ] **Step 3: Run tests + commit**

---

### Task 19: Sound System + Settings Mute Toggle

**Files:**
- Create: `game/audio.py`
- Modify: `game/screens/settings.py`
- Modify: `main.py`
- Test: `tests/test_audio.py`, `tests/test_settings_sound.py`

- [ ] **Step 1: Write tests**

Test `generate_tone(freq, duration_ms)` returns bytes of correct length. Test `SoundManager` with muted=True does not play. Test SettingsScreen now has theme + sound toggle rows, Enter on sound row toggles `config.sound_enabled`.

- [ ] **Step 2: Implement**

`game/audio.py`: Generate tones with raw PCM bytes (22050 Hz, 16-bit mono). `SoundManager(muted)` with `play_rarity(rarity)` method. Rarity sequences per spec.

SettingsScreen: Add sound toggle below theme selector. Two-row settings (theme, sound). DOWN/UP navigates rows, Enter on sound toggles.

Init `pygame.mixer` in `GameWindow.__init__`. Create `SoundManager` in `MutabarApp.__init__`.

- [ ] **Step 3: Run tests + commit**

---

### Task 20: Idle Earnings Calculator + Offline Earnings on Launch

**Files:**
- Create: `game/progression/idle.py`
- Modify: `main.py`
- Test: `tests/test_idle.py`

- [ ] **Step 1: Write tests**

Test `calculate_idle_rate(creatures) -> float`: each creature earns `(atk + defense) / 10` per minute, shinies × 1.15. Test `calculate_offline_earnings(creatures, last_check_iso, now) -> int`: elapsed minutes capped at 480, returns `floor(rate * minutes)`.

Note: DB rows use `"defense"` column (not `"def"`) and `"is_shiny"` (not `"shiny"`).

- [ ] **Step 2: Implement**

```python
from datetime import datetime, timezone
import math

MAX_OFFLINE_MINUTES = 480

def calculate_idle_rate(creatures: list[dict]) -> float:
    total = 0.0
    for c in creatures:
        base = (c.get("atk", 0) + c.get("defense", 0)) / 10.0
        if c.get("is_shiny"):
            base *= 1.15
        total += base
    return round(total, 2)

def calculate_offline_earnings(creatures: list[dict], last_check_iso: str, now: datetime | None = None) -> int:
    if not creatures:
        return 0
    if now is None:
        now = datetime.now(timezone.utc)
    last = datetime.fromisoformat(last_check_iso)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    minutes = min((now - last).total_seconds() / 60.0, MAX_OFFLINE_MINUTES)
    return math.floor(calculate_idle_rate(creatures) * max(0, minutes))
```

- [ ] **Step 3: Hook into main.py**

In `MutabarApp.run()`, before entering the main loop:
```python
idle_team = self.db.get_idle_team()
last_check = self.config.idle_last_check
if last_check and idle_team:
    earned = calculate_offline_earnings(idle_team, last_check)
    if earned > 0:
        self.db.add_mutagen(earned)
        self._idle_notification = earned
    self.config.idle_last_check = datetime.now(timezone.utc).isoformat()
    self.config.save()
elif not last_check:
    self.config.idle_last_check = datetime.now(timezone.utc).isoformat()
    self.config.save()
```

Show notification on MainMenu: `f"Idle earnings: +{earned} mutagen!"`

- [ ] **Step 4: Run tests + commit**
