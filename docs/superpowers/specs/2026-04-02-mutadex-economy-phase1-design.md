# Phase 1: Mutadex, Shinies, Rarity FX & Mutabox Economy

## Goal

Transform MUTABAR from a simple wave battler into a collectible creature game with persistent progression. Players earn mutagen from roguelike runs, spend it on mutaboxes to collect creatures, build teams from their collection, and chase shinies.

## Architecture

The existing screen state machine and TextBuffer renderer stay the same. New screens plug into `_switch_screen()` in `main.py`. The persistence layer (`MutabarDB`) gains new tables for the collection and currency. The lootbox system gets reworked to support mutabox tiers and shiny rolls.

---

## 1. Currency: Mutagen

Mutagen is the single persistent currency. Already tracked in `runs.mutagen_earned` — now it also has a persistent **balance** stored in a new `wallet` table.

### Earning

- Base reward per battle won: `wave * 5`
- Bonus: +50% mutagen if the killing blow was super effective
- Bonus: +25% mutagen if the killing blow was a critical hit
- Bonuses stack multiplicatively
- Mutagen earned during a run is shown per-wave and banked when the run ends (win or lose)

### Spending

- Mutabox Shop (see section 3)

### Storage

New DB table:

```sql
CREATE TABLE wallet (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mutagen INTEGER NOT NULL DEFAULT 0
);
```

Single-row table. `MutabarDB` gets `get_mutagen() -> int` and `add_mutagen(amount: int)` and `spend_mutagen(amount: int) -> bool` (returns False if insufficient).

---

## 2. Shiny System

### Roll Mechanics

- Base shiny chance: **1%** (0.01)
- Shiny Mutabox chance: **5%** (0.05)
- Determined at roll time, independent of rarity
- Stored as `is_shiny: bool` on the creature record

### Stat Boost

- Shiny creatures get **+15% to all base stats** (hp, atk, def), applied at instantiation
- Rounded to nearest integer
- Example: base_hp=100 becomes 115 for a shiny

### Visuals

- **Name color:** Cycling rainbow — hue shifts based on `time.time()`, rendered per-character with offset so the rainbow scrolls across the name
- **Mutadex marker:** `✦` prefix before the creature name
- **Lootbox reveal:** 3-frame white flash (entire surface goes white) before the reveal card appears

### Data

`Creature` dataclass gains `is_shiny: bool = False` field. `monsters` DB table gains `is_shiny INTEGER DEFAULT 0` column.

---

## 3. Mutabox Shop

Three tiers of mutaboxes with different costs and odds:

### Standard Mutabox — 50 mutagen

- Normal rarity weights (existing: Common 50, Uncommon 30, Rare 15, Epic 4, Legendary 1)
- Normal shiny chance (1%)

### Premium Mutabox — 150 mutagen

- Boosted rarity weights: Common 25, Uncommon 30, Rare 25, Epic 15, Legendary 5
- Normal shiny chance (1%)

### Shiny Mutabox — 300 mutagen

- Normal rarity weights
- Boosted shiny chance (5%)

### Implementation

New enum `MutaboxTier` with `STANDARD`, `PREMIUM`, `SHINY`. Each tier defines:
- `cost: int`
- `rarity_weights: dict[Rarity, float]`
- `shiny_chance: float`

The existing `roll_creature()` function gains optional parameters for custom weights and shiny chance. `RollResult` gains `is_shiny: bool`.

---

## 4. Rarity Visual Effects

### Lootbox Reveal

Each rarity has a distinct visual treatment on the reveal card:

| Rarity | Border Color | Text Animation | Sound Cue |
|--------|-------------|----------------|-----------|
| Common | `(120, 120, 120)` gray | Static (no animation) | 1 short beep |
| Uncommon | `(158, 206, 106)` green | Pulse: brightness oscillates via `sin(time * 3)` | 2 beeps |
| Rare | `(122, 162, 247)` blue | Shimmer: per-character brightness wave left→right | 3 beeps |
| Epic | `(187, 154, 247)` purple | Glow: border color cycles through purple shades | 3 ascending beeps |
| Legendary | `(224, 175, 104)` gold | Rainbow: border chars each get hue-shifted color based on position + time, gold text pulses | 5 rapid beeps (fanfare) |

### Animation Implementation

TextBuffer gets a new `render_to_surface_animated(surface, font, bg_color, time)` method. Screens that need animation pass `time.time()` each frame. The reveal card in `LootboxScreen` uses the rarity to select which color transform to apply.

Color transforms are pure functions: `(base_color, time, x, y) -> rendered_color`. The screen's `draw()` method tags cells with an animation type, and the renderer applies the transform.

### Sound

- `pygame.mixer.init()` at startup
- Generate tones programmatically using `pygame.sndarray` (numpy not required — use `pygame.mixer.Sound` with raw sample bytes)
- Frequencies: 440Hz (A4) for beeps, ascending 440→523→659 for epic, rapid 440Hz for legendary
- Duration: 100ms per beep, 50ms gap between
- **Mute toggle** in Settings, stored in config as `"sound_enabled": true/false`

---

## 5. Mutadex Hub

New screen accessible from the main menu. Has 3 tabs navigated with Left/Right arrows.

### Tab 1: Collection

- Scrollable list of all 53 creature templates
- **Discovered** (owned at least 1): Shows `name | TYPE | rarity_color_name | ✦ if any shiny owned`
- **Undiscovered**: Shows `??? | ??? | ???` in dim gray
- Header: `Collection: 12/53 discovered`
- Up/Down scrolls, Enter opens detail view for discovered creatures
- Detail view shows: name, type (colored), base stats, traits with keywords, count owned, shiny count

### Tab 2: Mutabox Shop

- Header shows mutagen balance: `Mutagen: 1,250`
- Lists 3 mutabox tiers as selectable cards:
  - `Standard Mutabox — 50 mutagen`
  - `Premium Mutabox — 150 mutagen` (labeled "Better rarity!")
  - `Shiny Mutabox — 300 mutagen` (labeled "5x shiny chance!")
- Unaffordable boxes shown in dim text
- Enter on an affordable box: deducts mutagen, transitions to lootbox animation
- After reveal: creature saved to DB collection, back to shop

### Tab 3: Stats

- Creatures discovered: X/53
- Shinies found: X
- Runs completed: X
- Highest wave: X (new column in `runs` table — `waves_survived` already tracks this)
- Total mutagen earned: X (sum from `runs` table)

### Navigation

- Left/Right arrows switch tabs (wrapping)
- Tab indicator at top: `[Collection] Shop Stats` (active tab highlighted)
- Up/Down scrolls within tab
- Enter selects/interacts
- ESC returns to main menu

---

## 6. Team Select Screen

New screen shown when starting a run, before the first battle.

### Layout

- Header: `SELECT YOUR TEAM (1-3)`
- Scrollable list of owned creatures (from DB `monsters` table)
- Each entry: `name | TYPE | HP/ATK/DEF | ✦ if shiny`
- Enter toggles selection (marked with ★)
- Selected count shown: `Selected: 2/3`
- When 1-3 selected: hint `[S] Start Run` appears at bottom
- S key or pressing right starts the run with selected team

### Starter Creatures

New players (empty `monsters` table) automatically receive 3 starter creatures on first launch:
- Wolf (FIRE, Common)
- Crab (WATER, Common)
- Hawk (AIR, Common)

These are inserted into the DB if the `monsters` table is empty.

### Creature Instantiation

Selected DB creatures are instantiated as `Creature` objects for the run. Shiny stat boost (+15%) is applied during instantiation. Level and XP from DB are preserved.

---

## 7. Updated Run Flow

### Main Menu

```
M U T A B A R
──────────────────────
▸ Start Run
  Mutadex
  Settings
  Quit
```

### Run Sequence

1. **Team Select** → Pick 1-3 creatures from collection
2. **Battle** → Fight wave (LLM narration, type-command system)
3. **Wave Complete** → Show: `Wave X cleared! +Y mutagen` with running total
4. **Next wave** → Auto-advance, heal team, generate new CPU team
5. **Defeat** → Show: `Run Over! Survived X waves. +Y mutagen banked.`
6. → Return to main menu (mutagen added to wallet)

### Post-battle (replaces old lootbox)

New `WaveCompleteScreen`:
- Shows wave number cleared
- Shows mutagen earned this wave (with bonus breakdown)
- Shows total mutagen this run so far
- `[Enter] Next Wave`

---

## 8. Idle Arena

### Concept

You assign a team of up to 3 creatures to the Idle Arena. They automatically fight waves in the background and earn mutagen passively. This works even when the app is closed — on next launch, offline earnings are calculated and awarded.

### Mechanics

- **Earnings rate:** Each creature earns `(atk + def) / 10` mutagen per minute (shinies earn 15% more)
- **Team of 3 max** — same creatures can't be used in a run simultaneously
- **Offline cap:** Max 8 hours of offline earnings (480 minutes)
- **On app launch:** Calculate `min(minutes_since_last_check, 480) * team_earnings_per_minute`, add to wallet
- **Visible in Mutadex Stats tab** and as a small indicator on the main menu: `Idle: +X/min`

### Idle Arena Screen

Accessible as a 4th tab in the Mutadex: `Collection | Shop | Idle | Stats`

- Shows currently assigned idle team (up to 3 slots)
- Shows earnings rate: `+X mutagen/min`
- Shows accumulated idle earnings since last collection
- `[Enter]` on empty slot → pick creature from collection
- `[Enter]` on filled slot → remove creature
- Creatures in idle arena shown with `[IDLE]` tag in collection tab (can't be selected for runs)

### Storage

New DB table:

```sql
CREATE TABLE idle_arena (
    slot INTEGER PRIMARY KEY CHECK (slot BETWEEN 1 AND 3),
    monster_id INTEGER NOT NULL REFERENCES monsters(id)
);
```

New config key: `"idle_last_check": "<ISO timestamp>"` — updated each time idle earnings are collected.

### Offline Earnings Flow

On app launch (in `MutabarApp.__init__` or `run()`):
1. Read `idle_last_check` from config
2. Query idle_arena for assigned creatures
3. Calculate per-minute rate from creature stats
4. Calculate elapsed minutes (capped at 480)
5. Add `elapsed * rate` to wallet
6. Update `idle_last_check` to now
7. Show notification on main menu: `Idle earnings: +X mutagen collected!`

---

## 9. Updated Screen Map

```
MainMenuScreen (shows idle earnings notification if any)
├─ "run" → TeamSelectScreen (idle creatures excluded)
│   └─ "start_run" → BattleScreen
│       └─ "wave_complete" → WaveCompleteScreen
│           └─ "next_wave" → BattleScreen (loop)
│       └─ "run_over" → RunOverScreen
│           └─ "main_menu" → MainMenuScreen
├─ "mutadex" → MutadexScreen (tabbed)
│   ├─ Tab: Collection (browse/detail, shows [IDLE] tags)
│   ├─ Tab: Shop → "open_mutabox" → LootboxScreen
│   │   └─ "post_lootbox" → MutadexScreen (back to shop)
│   ├─ Tab: Idle Arena (assign/remove creatures)
│   └─ Tab: Stats
├─ "settings" → SettingsScreen
└─ "quit" → exit
```

---

## 10. Database Changes

### New table: `wallet`

```sql
CREATE TABLE wallet (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mutagen INTEGER NOT NULL DEFAULT 0
);
INSERT INTO wallet (id, mutagen) VALUES (1, 0);
```

### New table: `idle_arena`

```sql
CREATE TABLE idle_arena (
    slot INTEGER PRIMARY KEY CHECK (slot BETWEEN 1 AND 3),
    monster_id INTEGER NOT NULL REFERENCES monsters(id)
);
```

### Modified table: `monsters`

Add column: `is_shiny INTEGER NOT NULL DEFAULT 0`

### New DB methods on `MutabarDB`

- `get_mutagen() -> int`
- `add_mutagen(amount: int)`
- `spend_mutagen(amount: int) -> bool`
- `save_creature(name, species, category, mutation_type, base_hp, base_atk, base_def, traits_json, is_shiny) -> int`
- `get_collection() -> list[dict]` (all monsters)
- `get_discovered_species() -> set[str]` (unique species names)
- `get_stats() -> dict` (aggregated stats for Stats tab)
- `get_idle_team() -> list[dict]` (creatures in idle arena with stats)
- `set_idle_slot(slot: int, monster_id: int)`
- `clear_idle_slot(slot: int)`
- `get_idle_monster_ids() -> set[int]` (for excluding from team select)

---

## 11. New Files

```
game/screens/team_select.py    — TeamSelectScreen
game/screens/mutadex.py        — MutadexScreen (tabbed: collection, shop, idle, stats)
game/screens/wave_complete.py  — WaveCompleteScreen
game/screens/run_over.py       — RunOverScreen
game/progression/mutabox.py    — MutaboxTier enum, roll logic
game/progression/idle.py       — Idle earnings calculator
game/audio.py                  — Sound manager (generate tones, mute toggle)
```

### Modified Files

```
main.py                        — New screen routes, starter creature seeding, idle earnings on launch
game/creatures/creature.py     — is_shiny field, shiny stat boost
game/progression/lootbox.py    — Custom weights/shiny params on roll_creature
game/screens/lootbox.py        — Rarity FX animations, shiny flash
game/screens/main_menu.py      — Add Mutadex menu item, idle earnings notification
game/screens/settings.py       — Add sound mute toggle
game/renderer.py               — Animated render method, rainbow color util
game/battle/damage.py          — Mutagen bonus tracking on DamageResult
persistence/database.py        — New tables (wallet, idle_arena), new methods, schema migration
persistence/config.py          — sound_enabled + idle_last_check config keys
```

---

## 12. Config Changes

Add to defaults:

```python
"sound_enabled": True,
"idle_last_check": None,  # ISO timestamp string, set on first idle collection
```
