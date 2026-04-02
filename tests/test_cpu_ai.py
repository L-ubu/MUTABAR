import random

import pytest

from game.creatures.creature import Creature, CreatureCategory
from game.creatures.traits import Trait
from game.creatures.types import MutationType
from game.battle.cpu_ai import CpuDifficulty, generate_cpu_command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_creature(traits=None):
    return Creature(
        name="TestMon",
        category=CreatureCategory.ANIMAL,
        mutation_type=MutationType.FIRE,
        traits=traits or [],
        base_hp=50,
        base_atk=10,
        base_def=8,
    )


def make_trait(name="Flame Fist", keywords=None):
    return Trait(
        name=name,
        description="A fiery attack",
        keywords=keywords or ["fire", "burn", "flame"],
    )


# ---------------------------------------------------------------------------
# BASIC difficulty
# ---------------------------------------------------------------------------

def test_basic_returns_non_empty_string():
    random.seed(42)
    creature = make_creature()
    result = generate_cpu_command(creature, CpuDifficulty.BASIC)
    assert isinstance(result, str)
    assert len(result) > 0


def test_basic_ignores_traits():
    """BASIC difficulty should return a generic command even if creature has traits."""
    random.seed(42)
    creature = make_creature(traits=[make_trait()])
    result = generate_cpu_command(creature, CpuDifficulty.BASIC)
    assert isinstance(result, str)
    assert len(result) > 0


def test_basic_varies_over_calls():
    """BASIC should produce different commands over many calls (not always same)."""
    creature = make_creature()
    commands = {generate_cpu_command(creature, CpuDifficulty.BASIC) for _ in range(50)}
    assert len(commands) > 1


# ---------------------------------------------------------------------------
# TACTICAL difficulty
# ---------------------------------------------------------------------------

def test_tactical_returns_non_empty_string():
    random.seed(42)
    creature = make_creature(traits=[make_trait()])
    result = generate_cpu_command(creature, CpuDifficulty.TACTICAL)
    assert isinstance(result, str)
    assert len(result) > 0


def test_tactical_with_no_traits_falls_back_to_generic():
    random.seed(42)
    creature = make_creature(traits=[])
    result = generate_cpu_command(creature, CpuDifficulty.TACTICAL)
    assert isinstance(result, str)
    assert len(result) > 0


def test_tactical_command_contains_trait_keyword():
    """TACTICAL command should reference a keyword from the creature's traits."""
    random.seed(42)
    trait = make_trait(keywords=["inferno", "blaze"])
    creature = make_creature(traits=[trait])
    # Run many times; at least some should contain one of the keywords
    found = False
    for seed in range(30):
        random.seed(seed)
        cmd = generate_cpu_command(creature, CpuDifficulty.TACTICAL)
        if "inferno" in cmd or "blaze" in cmd:
            found = True
            break
    assert found, "TACTICAL command never referenced a trait keyword"


def test_tactical_trait_with_no_keywords_falls_back():
    random.seed(42)
    trait = Trait(name="Empty Trait", description="no keywords", keywords=[])
    creature = make_creature(traits=[trait])
    result = generate_cpu_command(creature, CpuDifficulty.TACTICAL)
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# ADAPTIVE difficulty
# ---------------------------------------------------------------------------

def test_adaptive_returns_non_empty_string():
    random.seed(42)
    trait = make_trait(keywords=["fire", "burn", "flame", "scorch"])
    creature = make_creature(traits=[trait])
    result = generate_cpu_command(creature, CpuDifficulty.ADAPTIVE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_adaptive_with_no_traits_falls_back_to_generic():
    random.seed(42)
    creature = make_creature(traits=[])
    result = generate_cpu_command(creature, CpuDifficulty.ADAPTIVE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_adaptive_picks_trait_with_most_keywords():
    """
    Adaptive should favour the trait with the most keywords.
    We verify the output contains keywords from that trait.
    """
    random.seed(42)
    small_trait = make_trait(name="Small", keywords=["tiny"])
    big_trait = make_trait(name="Big", keywords=["alpha", "beta", "gamma", "delta"])
    creature = make_creature(traits=[small_trait, big_trait])

    hits = 0
    for seed in range(20):
        random.seed(seed)
        cmd = generate_cpu_command(creature, CpuDifficulty.ADAPTIVE)
        if any(kw in cmd for kw in big_trait.keywords):
            hits += 1

    # Since adaptive picks the trait with most keywords, majority should match big_trait
    assert hits >= 15, f"Only {hits}/20 commands referenced the dominant trait"


def test_adaptive_combines_two_keywords():
    """ADAPTIVE with a trait of >= 2 keywords should produce a '<kw1> <kw2> strike' form."""
    random.seed(42)
    trait = make_trait(keywords=["fierce", "relentless"])
    creature = make_creature(traits=[trait])
    result = generate_cpu_command(creature, CpuDifficulty.ADAPTIVE)
    assert "strike" in result


def test_adaptive_single_keyword_trait():
    """ADAPTIVE with a trait of exactly 1 keyword should still return a valid command."""
    random.seed(42)
    trait = Trait(name="Solo", description="one kw", keywords=["singular"])
    creature = make_creature(traits=[trait])
    result = generate_cpu_command(creature, CpuDifficulty.ADAPTIVE)
    assert isinstance(result, str)
    assert len(result) > 0
