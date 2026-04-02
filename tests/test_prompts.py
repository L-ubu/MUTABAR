"""
tests/test_prompts.py
Tests for game/llm/prompts.py — prompt builders for battle narration and creature reveal.
"""

import pytest

from game.creatures.creature import Creature, CreatureCategory
from game.creatures.traits import Trait
from game.creatures.types import MutationType
from game.llm.prompts import build_battle_prompt, build_reveal_prompt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fire_wolf():
    return Creature(
        name="Wolf",
        category=CreatureCategory.ANIMAL,
        mutation_type=MutationType.FIRE,
        traits=[
            Trait(name="Pack Hunter", description="Bonus when allies assist", keywords=["pack", "howl"]),
            Trait(name="Feral Bite", description="Savage tearing bite", keywords=["bite", "tear"]),
        ],
        base_hp=70,
        base_atk=14,
        base_def=8,
    )


@pytest.fixture
def water_bear():
    return Creature(
        name="Bear",
        category=CreatureCategory.ANIMAL,
        mutation_type=MutationType.WATER,
        traits=[
            Trait(name="Crushing Swipe", description="Massive paw swipe", keywords=["swipe", "crush"]),
            Trait(name="Thick Hide", description="Tough fur absorbs blows", keywords=["hide", "tough"]),
        ],
        base_hp=120,
        base_atk=15,
        base_def=14,
    )


# ---------------------------------------------------------------------------
# build_battle_prompt tests
# ---------------------------------------------------------------------------


class TestBuildBattlePrompt:
    def test_includes_attacker_name(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="attack with feral bite", damage=25,
            effectiveness="super_effective", is_critical=False,
        )
        assert "Wolf" in prompt

    def test_includes_defender_name(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="attack with feral bite", damage=25,
            effectiveness="super_effective", is_critical=False,
        )
        assert "Bear" in prompt

    def test_includes_command_text(self, fire_wolf, water_bear):
        command = "unleash howling fury"
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command=command, damage=18,
            effectiveness="neutral", is_critical=False,
        )
        assert command in prompt

    def test_includes_attacker_type_name(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="strike", damage=10,
            effectiveness="neutral", is_critical=False,
        )
        assert "FIRE" in prompt

    def test_includes_defender_type_name(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="strike", damage=10,
            effectiveness="neutral", is_critical=False,
        )
        assert "WATER" in prompt

    def test_includes_damage(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="strike hard", damage=42,
            effectiveness="neutral", is_critical=False,
        )
        assert "42" in prompt

    def test_includes_effectiveness(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="strike hard", damage=10,
            effectiveness="super_effective", is_critical=False,
        )
        assert "super effective" in prompt

    def test_mentions_critical_when_true(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="strike hard", damage=30,
            effectiveness="neutral", is_critical=True,
        )
        assert "critical" in prompt.lower()

    def test_no_critical_mention_when_false(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="strike hard", damage=30,
            effectiveness="neutral", is_critical=False,
        )
        assert "critical" not in prompt.lower()

    def test_includes_narrate_instruction(self, fire_wolf, water_bear):
        prompt = build_battle_prompt(
            attacker=fire_wolf, defender=water_bear,
            command="bite and tear", damage=20,
            effectiveness="neutral", is_critical=False,
        )
        assert "narrate" in prompt.lower()


# ---------------------------------------------------------------------------
# build_reveal_prompt tests
# ---------------------------------------------------------------------------


class TestBuildRevealPrompt:
    def test_includes_creature_name(self):
        prompt = build_reveal_prompt(
            creature_name="Glitchfang",
            mutation_type=MutationType.TECH,
            traits=["Data Rend", "Pixel Shift", "Error Cascade"],
        )
        assert "Glitchfang" in prompt

    def test_includes_type_name(self):
        prompt = build_reveal_prompt(
            creature_name="Glitchfang",
            mutation_type=MutationType.TECH,
            traits=["Data Rend", "Pixel Shift"],
        )
        assert "TECH" in prompt

    def test_includes_trait_names(self):
        prompt = build_reveal_prompt(
            creature_name="Phoenix",
            mutation_type=MutationType.FIRE,
            traits=["Rebirth Flame", "Solar Burst"],
        )
        assert "Rebirth Flame" in prompt or "Solar Burst" in prompt

    def test_requests_one_sentence(self):
        prompt = build_reveal_prompt(
            creature_name="Dragon",
            mutation_type=MutationType.FIRE,
            traits=["Fire Breath", "Dragon Scales"],
        )
        assert "one sentence" in prompt.lower() or "one-sentence" in prompt.lower()

    def test_empty_traits_does_not_crash(self):
        prompt = build_reveal_prompt(
            creature_name="Wolf",
            mutation_type=MutationType.EARTH,
            traits=[],
        )
        assert "Wolf" in prompt
        assert "EARTH" in prompt
