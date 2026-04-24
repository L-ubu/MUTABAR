```
         /\    \                  /\    \              /\    \                  /\    \                  /\    \                  /\    \                  /\    \
        /::\____\                /::\____\            /::\    \                /::\    \                /::\    \                /::\    \                /::\    \
       /::::|   |               /:::/    /            \:::\    \              /::::\    \              /::::\    \              /::::\    \              /::::\    \
      /:::::|   |              /:::/    /              \:::\    \            /::::::\    \            /::::::\    \            /::::::\    \            /::::::\    \
     /::::::|   |             /:::/    /                \:::\    \          /:::/\:::\    \          /:::/\:::\    \          /:::/\:::\    \          /:::/\:::\    \
    /:::/|::|   |            /:::/    /                  \:::\    \        /:::/__\:::\    \        /:::/__\:::\    \        /:::/__\:::\    \        /:::/__\:::\    \
   /:::/ |::|   |           /:::/    /                   /::::\    \      /::::\   \:::\    \      /::::\   \:::\    \      /::::\   \:::\    \      /::::\   \:::\    \
  /:::/  |::|___|______    /:::/    /      _____        /::::::\    \    /::::::\   \:::\    \    /::::::\   \:::\    \    /::::::\   \:::\    \    /::::::\   \:::\    \
 /:::/   |::::::::\    \  /:::/____/      /\    \      /:::/\:::\    \  /:::/\:::\   \:::\    \  /:::/\:::\   \:::\ ___\  /:::/\:::\   \:::\    \  /:::/\:::\   \:::\____\
/:::/    |:::::::::\____\|:::|    /      /::\____\    /:::/  \:::\____\/:::/  \:::\   \:::\____\/:::/__\:::\   \:::|    |/:::/  \:::\   \:::\____\/:::/  \:::\   \:::|    |
\::/    / ~~~~~/:::/    /|:::|____\     /:::/    /   /:::/    \::/    /\::/    \:::\  /:::/    /\:::\   \:::\  /:::|____|\::/    \:::\  /:::/    /\::/   |::::\  /:::|____|
 \/____/      /:::/    /  \:::\    \   /:::/    /   /:::/    / \/____/  \/____/ \:::\/:::/    /  \:::\   \:::\/:::/    /  \/____/ \:::\/:::/    /  \/____|:::::\/:::/    /
             /:::/    /    \:::\    \ /:::/    /   /:::/    /                    \::::::/    /    \:::\   \::::::/    /            \::::::/    /         |:::::::::/    /
            /:::/    /      \:::\    /:::/    /   /:::/    /                      \::::/    /      \:::\   \::::/    /              \::::/    /          |::|\::::/    /
           /:::/    /        \:::\__/:::/    /    \::/    /                       /:::/    /        \:::\  /:::/    /               /:::/    /           |::| \::/____/
          /:::/    /          \::::::::/    /      \/____/                       /:::/    /          \:::\/:::/    /               /:::/    /            |::|  ~|
         /:::/    /            \::::::/    /                                    /:::/    /            \::::::/    /               /:::/    /             |::|   |
        /:::/    /              \::::/    /                                    /:::/    /              \::::/    /               /:::/    /              \::|   |
        \::/    /                \::/____/                                     \::/    /                \::/____/                \::/    /                \:|   |
         \/____/                  ~~                                            \/____/                  ~~                       \/____/                  \|___|
```

# MUTABAR

A monster battler that lives in your macOS menu bar. Collect 80+ creatures, battle with AI-narrated combat, open lootboxes, and earn idle income — all from a tiny window under your status bar.

<p align="center">
  <img src="assets/icon.png" alt="MUTABAR icon" width="128">
</p>

## Features

**Battle**
- Type free-form attack commands — a local LLM narrates the action
- 8 mutation types with rock-paper-scissors effectiveness
- Status effects, traits, and critical hits add combat depth
- Boss waves every 5th round with tougher creatures

**Collect**
- 82 creatures across 6 rarities: Common, Uncommon, Rare, Epic, Legendary, Mutagen
- Animals, Mythological beasts, Famous monsters, Original creations, and Hybrids
- Shiny variants with +15% stat boost and special visual effects
- ASCII art for every creature in the Mutadex

**Progress**
- Roguelite runs with escalating waves
- Earn mutagen currency from battles to spend on lootboxes
- Three mutabox tiers: Standard (50), Premium (150), Legendary (300)
- CS:GO-style rolling animation on lootbox reveals
- Random between-wave events (Healing Spring, Mysterious Trader, Shrine, etc.)

**Idle**
- Assign creatures to the idle arena for passive mutagen income
- Offline earnings calculated on next launch (up to 8 hours)

**Polish**
- Borderless window anchored below the menu bar icon
- 4 switchable color themes (Tokyo Night, Phosphor, Frosted Glass, Adaptive)
- Rarity-specific animations: golden shimmer, legendary rainbow, mutagen pulse
- Sound effects with mute toggle
- Single-instance enforcement — launching again brings the window to front

## Requirements

- macOS 12+
- Python 3.11+

## Install

```bash
git clone https://github.com/lucavdw/mutabar.git
cd mutabar
./install.sh
```

The installer creates a virtual environment, installs dependencies, and optionally downloads the AI model (~2 GB).

## Run

```bash
source venv/bin/activate
mutabar
```

Or directly: `./venv/bin/mutabar`

## Build standalone app

```bash
./build_app.sh
```

Produces `dist/MUTABAR.zip` — send it to anyone with a Mac. They unzip and double-click.

## Controls

| Key | Action |
| --- | --- |
| Arrow keys | Navigate menus |
| Enter | Confirm / submit command |
| Esc | Back / hide window |
| I | Inspect creature (in battle) |
| R | Reroll lootbox |
| Tab | Switch tabs (Mutadex) |

## AI narration

Battles and events are narrated by a local Qwen3 1.7B model running entirely on your Mac. The model downloads automatically on first launch (~2 GB). If you skip it, everything uses template text instead — no internet required to play.

To install AI support separately:

```bash
pip install 'mutabar[ai]'
```

## Project structure

```
mutabar/
  main.py                   # App entry point and screen routing
  game/
    battle/                 # Battle engine, damage calc, CPU AI, status effects
    creatures/              # Creature model, 82-entry roster, types, traits, ASCII art
    events/                 # Random between-wave encounters
    llm/                    # LLM engine wrapper and prompt builders
    progression/            # Runs, lootboxes, mutaboxes, mutagen, idle arena
    screens/                # All game screens (battle, mutadex, lootbox, etc.)
    renderer.py             # ASCII text buffer with animation support
    window.py               # Borderless pygame window with macOS integration
    theme.py                # Color themes
    audio.py                # Sound manager
  persistence/
    database.py             # SQLite storage for collection, runs, wallet, idle team
    config.py               # JSON config for settings
  assets/                   # Icons and fonts
  tests/                    # pytest test suite
```

## License

MIT
