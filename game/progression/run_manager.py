"""
game/progression/run_manager.py
Run lifecycle management for MUTABAR.
"""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import List

from game.battle.cpu_ai import CpuDifficulty
from game.creatures.creature import Creature, CreatureCategory
from game.creatures.database import CREATURE_ROSTER, CreatureTemplate
from game.creatures.types import MutationType


# ---------------------------------------------------------------------------
# RunState
# ---------------------------------------------------------------------------


class RunState(Enum):
    IDLE = auto()
    TEAM_SELECT = auto()
    BATTLE = auto()
    POST_BATTLE = auto()
    LOOTBOX = auto()
    ENDED = auto()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _instantiate(template: CreatureTemplate) -> Creature:
    """Create a Creature from a CreatureTemplate with a random MutationType."""
    mutation_type = random.choice(list(MutationType))
    return Creature(
        name=template.name,
        category=template.category,
        mutation_type=mutation_type,
        traits=list(template.traits),
        base_hp=template.base_hp,
        base_atk=template.base_atk,
        base_def=template.base_def,
    )


# ---------------------------------------------------------------------------
# RunManager
# ---------------------------------------------------------------------------


class RunManager:
    def __init__(self, unlocked_tiers: set[str]) -> None:
        self.unlocked_tiers = unlocked_tiers
        self.state: RunState = RunState.IDLE
        self.wave: int = 0
        self.player_team: List[Creature] = []
        self.cpu_team: List[Creature] = []

    # --- Run lifecycle ---

    def start_new_run(self) -> None:
        """Transition to TEAM_SELECT state and reset wave and teams."""
        self.state = RunState.TEAM_SELECT
        self.wave = 0
        self.player_team = []
        self.cpu_team = []

    def roll_starting_team(self) -> List[Creature]:
        """Pick 3 random creatures from the unlocked pool, each with a random MutationType."""
        pool = list(CREATURE_ROSTER)
        templates = random.sample(pool, min(3, len(pool)))
        self.player_team = [_instantiate(t) for t in templates]
        return self.player_team

    def advance_wave(self) -> None:
        """Increment the wave counter and transition to BATTLE state."""
        self.wave += 1
        self.state = RunState.BATTLE

    @property
    def is_boss_wave(self) -> bool:
        return self.wave > 0 and self.wave % 5 == 0

    def generate_cpu_team(self) -> List[Creature]:
        """
        Generate the CPU team for the current wave.

        Boss waves (every 5th): pick from FAMOUS/ORIGINAL/HYBRID categories,
        higher shiny chance, level = wave + 2.
        Normal waves: pick from ANIMAL/MYTHOLOGICAL, small shiny chance.
        """
        count = min(1 + self.wave // 5, 3)
        roster = list(CREATURE_ROSTER)

        if self.is_boss_wave:
            boss_cats = {CreatureCategory.FAMOUS, CreatureCategory.ORIGINAL, CreatureCategory.HYBRID}
            pool = [t for t in roster if t.category in boss_cats]
            shiny_chance = 0.10
            level_bonus = 2
        else:
            normal_cats = {CreatureCategory.ANIMAL, CreatureCategory.MYTHOLOGICAL}
            pool = [t for t in roster if t.category in normal_cats]
            shiny_chance = 0.03
            level_bonus = 0

        if not pool:
            pool = roster

        templates = random.sample(pool, min(count, len(pool)))
        self.cpu_team = []
        for template in templates:
            creature = _instantiate(template)
            creature.level = self.wave + level_bonus
            creature.is_shiny = random.random() < shiny_chance
            self.cpu_team.append(creature)
        return self.cpu_team

    @property
    def cpu_difficulty(self) -> CpuDifficulty:
        """
        Determine CPU difficulty based on wave:
        - Waves  1-5:  BASIC
        - Waves  6-15: TACTICAL
        - Waves 16+:   ADAPTIVE
        """
        if self.wave <= 5:
            return CpuDifficulty.BASIC
        if self.wave <= 15:
            return CpuDifficulty.TACTICAL
        return CpuDifficulty.ADAPTIVE

    def end_run(self) -> dict:
        """
        End the current run and return a summary dict.

        Returns: {waves_survived: int, mutagen_earned: int}
        """
        self.state = RunState.ENDED
        return {
            "waves_survived": self.wave,
            "mutagen_earned": self.wave * 5,
        }
