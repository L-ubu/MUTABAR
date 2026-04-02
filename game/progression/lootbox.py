"""
game/progression/lootbox.py
Lootbox roll system for MUTABAR.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

from game.creatures.creature import CreatureCategory
from game.creatures.database import CREATURE_ROSTER, CreatureTemplate


# ---------------------------------------------------------------------------
# Rarity
# ---------------------------------------------------------------------------


class Rarity(IntEnum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5


# ---------------------------------------------------------------------------
# Template → Rarity mapping
# ---------------------------------------------------------------------------


def _get_creature_rarity(template: CreatureTemplate) -> Rarity:
    """Derive the rarity of a creature template from its category and stats."""
    if template.category == CreatureCategory.ORIGINAL:
        return Rarity.LEGENDARY
    if template.category == CreatureCategory.MYTHOLOGICAL:
        return Rarity.RARE
    # ANIMAL
    total = template.base_hp + template.base_atk + template.base_def
    if total >= 140:
        return Rarity.UNCOMMON
    return Rarity.COMMON


# ---------------------------------------------------------------------------
# Rarity pools (computed once at import time)
# ---------------------------------------------------------------------------


def _build_rarity_pools() -> dict[Rarity, list[CreatureTemplate]]:
    pools: dict[Rarity, list[CreatureTemplate]] = {r: [] for r in Rarity}
    for template in CREATURE_ROSTER:
        pools[_get_creature_rarity(template)].append(template)
    return pools


_RARITY_POOLS: dict[Rarity, list[CreatureTemplate]] = _build_rarity_pools()


# ---------------------------------------------------------------------------
# Weight calculation
# ---------------------------------------------------------------------------


_BASE_WEIGHTS: dict[Rarity, float] = {
    Rarity.COMMON: 50.0,
    Rarity.UNCOMMON: 30.0,
    Rarity.RARE: 15.0,
    Rarity.EPIC: 4.0,
    Rarity.LEGENDARY: 1.0,
}

_WAVE_SHIFT_CAP = 31  # no more shifts after wave 31


def get_rarity_weights(wave: int, unlocked_tiers: set[str]) -> dict[Rarity, float]:
    """
    Return normalized rarity weights for a given wave and set of unlocked tiers.

    - Each wave past 1 shifts 1 point from COMMON to higher tiers (capped at wave 31).
    - Tiers not in *unlocked_tiers* are zeroed out.
    - The remaining weights are normalized so they sum to 100.
    """
    weights = dict(_BASE_WEIGHTS)

    # Wave scaling: shift n points from COMMON, distribute 1 pt each to higher rarities
    shifts = min(max(wave - 1, 0), _WAVE_SHIFT_CAP - 1)
    if shifts > 0:
        # We have shifts points to move away from COMMON
        higher = [Rarity.UNCOMMON, Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY]
        per_tier = shifts / len(higher)
        weights[Rarity.COMMON] = max(0.0, weights[Rarity.COMMON] - shifts)
        for tier in higher:
            weights[tier] = weights[tier] + per_tier

    # Zero out locked tiers (and tiers with empty pools)
    tier_name_map: dict[str, Rarity] = {r.name: r for r in Rarity}
    for rarity in list(weights.keys()):
        if rarity.name not in unlocked_tiers:
            weights[rarity] = 0.0
        if not _RARITY_POOLS.get(rarity):
            weights[rarity] = 0.0

    # Normalize
    total = sum(weights.values())
    if total <= 0:
        # Fallback: only COMMON
        weights = {r: 0.0 for r in Rarity}
        weights[Rarity.COMMON] = 100.0
    else:
        factor = 100.0 / total
        weights = {r: v * factor for r, v in weights.items()}

    return weights


# ---------------------------------------------------------------------------
# RollResult
# ---------------------------------------------------------------------------


@dataclass
class RollResult:
    rarity: Rarity
    template: CreatureTemplate
    strip: list[CreatureTemplate]
    winner_index: int
    is_shiny: bool = False


# ---------------------------------------------------------------------------
# Roll
# ---------------------------------------------------------------------------


_DEFAULT_SHINY_CHANCE: float = 0.01


def roll_creature(
    wave: int, unlocked_tiers: set[str],
    rarity_weights: dict[Rarity, float] | None = None,
    shiny_chance: float = _DEFAULT_SHINY_CHANCE,
) -> RollResult:
    """
    Perform a lootbox roll and return a RollResult.

    - Picks the winning rarity via weighted random.
    - Picks a random creature from that rarity's pool.
    - Builds an animation strip of 20 random creatures with the winner
      inserted near the end (index = size - randint(2, 5)).
    """
    weights = rarity_weights if rarity_weights is not None else get_rarity_weights(wave, unlocked_tiers)

    # Collect available rarities (non-zero weight)
    available_rarities = [r for r, w in weights.items() if w > 0]
    available_weights = [weights[r] for r in available_rarities]

    winning_rarity = random.choices(available_rarities, weights=available_weights, k=1)[0]
    pool = _RARITY_POOLS[winning_rarity]
    winner = random.choice(pool)

    # Build animation strip: 20 random creatures from the full roster
    strip_size = 20
    strip: list[CreatureTemplate] = random.choices(CREATURE_ROSTER, k=strip_size)

    # Insert winner near the end
    winner_index = strip_size - random.randint(2, 5)
    strip = list(strip)
    strip.insert(winner_index, winner)

    is_shiny = random.random() < shiny_chance

    return RollResult(
        rarity=winning_rarity,
        template=winner,
        strip=strip,
        winner_index=winner_index,
        is_shiny=is_shiny,
    )
