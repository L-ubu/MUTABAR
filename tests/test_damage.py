import random

import pytest

from game.creatures.creature import Creature, CreatureCategory
from game.creatures.traits import Trait
from game.creatures.types import MutationType
from game.battle.damage import DamageResult, calculate_damage


def make_creature(
    name="Emberfox",
    mutation_type=MutationType.FIRE,
    base_atk=10,
    base_def=8,
    base_hp=50,
    level=1,
):
    return Creature(
        name=name,
        category=CreatureCategory.ANIMAL,
        mutation_type=mutation_type,
        traits=[],
        base_hp=base_hp,
        base_atk=base_atk,
        base_def=base_def,
        level=level,
    )


# --- DamageResult dataclass ---

def test_damage_result_fields():
    result = DamageResult(
        damage=15,
        is_critical=False,
        is_miss=False,
        effectiveness="neutral",
        trait_bonus=1.0,
    )
    assert result.damage == 15
    assert result.is_critical is False
    assert result.is_miss is False
    assert result.effectiveness == "neutral"
    assert result.trait_bonus == 1.0


def test_damage_result_critical_flag():
    result = DamageResult(
        damage=20,
        is_critical=True,
        is_miss=False,
        effectiveness="super_effective",
        trait_bonus=1.2,
    )
    assert result.is_critical is True
    assert result.effectiveness == "super_effective"


# --- calculate_damage ---

def test_basic_damage_is_positive():
    random.seed(42)
    attacker = make_creature(base_atk=10, base_def=5)
    defender = make_creature(base_atk=5, base_def=8)
    result = calculate_damage(attacker, defender, "attack")
    assert result.damage >= 1


def test_damage_result_has_correct_type():
    random.seed(42)
    attacker = make_creature()
    defender = make_creature()
    result = calculate_damage(attacker, defender, "attack")
    assert isinstance(result, DamageResult)
    assert isinstance(result.damage, int)
    assert isinstance(result.is_critical, bool)
    assert isinstance(result.is_miss, bool)
    assert result.effectiveness in ("super_effective", "resisted", "neutral")
    assert isinstance(result.trait_bonus, float)


def test_super_effective_does_more_than_neutral():
    """FIRE > AIR is super effective; FIRE vs EARTH is neutral."""
    random.seed(42)
    attacker_fire = make_creature(name="FireMon", mutation_type=MutationType.FIRE, base_atk=20)
    defender_air = make_creature(name="AirMon", mutation_type=MutationType.AIR, base_def=10)
    defender_earth = make_creature(name="EarthMon", mutation_type=MutationType.EARTH, base_def=10)

    # Run many trials with the same seed to average out RNG
    super_effective_total = 0
    neutral_total = 0
    trials = 50
    for i in range(trials):
        random.seed(i)
        r_super = calculate_damage(attacker_fire, defender_air, "attack")
        random.seed(i)
        r_neutral = calculate_damage(attacker_fire, defender_earth, "attack")
        super_effective_total += r_super.damage
        neutral_total += r_neutral.damage

    assert super_effective_total > neutral_total


def test_super_effective_label():
    """Check effectiveness label is set to super_effective when type_mult > 1."""
    random.seed(42)
    attacker = make_creature(name="FireMon", mutation_type=MutationType.FIRE, base_atk=20)
    defender = make_creature(name="AirMon", mutation_type=MutationType.AIR, base_def=10)
    result = calculate_damage(attacker, defender, "attack")
    assert result.effectiveness == "super_effective"


def test_resisted_does_less_than_neutral():
    """AIR > FIRE is resisted from FIRE's perspective (FIRE vs EARTH neutral, AIR resists FIRE)."""
    # FIRE -> AIR is super effective (type mult 1.5)
    # AIR -> FIRE: let's check: AIR is at index 0 of... wait,
    # Cycle 1: FIRE(0) > AIR(1) > EARTH(2) > WATER(3)
    # So WATER -> FIRE is super effective (water index 3, fire index 0: (3+1)%4==0 yes)
    # FIRE -> WATER: FIRE(0), WATER(3): (0+1)%4=1 != 3, so check reverse: (3+1)%4=0==0 yes => resisted
    random.seed(42)
    attacker_fire = make_creature(name="FireMon", mutation_type=MutationType.FIRE, base_atk=20)
    defender_water = make_creature(name="WaterMon", mutation_type=MutationType.WATER, base_def=10)
    defender_earth = make_creature(name="EarthMon", mutation_type=MutationType.EARTH, base_def=10)

    resisted_total = 0
    neutral_total = 0
    trials = 50
    for i in range(trials):
        random.seed(i)
        r_resisted = calculate_damage(attacker_fire, defender_water, "attack")
        random.seed(i)
        r_neutral = calculate_damage(attacker_fire, defender_earth, "attack")
        resisted_total += r_resisted.damage
        neutral_total += r_neutral.damage

    assert resisted_total < neutral_total


def test_resisted_label():
    """Check effectiveness label is resisted when type_mult < 1."""
    random.seed(42)
    # FIRE vs WATER: FIRE(0), WATER(3): (def_idx+1)%n = (3+1)%4 = 0 == att_idx -> resisted
    attacker = make_creature(name="FireMon", mutation_type=MutationType.FIRE, base_atk=20)
    defender = make_creature(name="WaterMon", mutation_type=MutationType.WATER, base_def=10)
    result = calculate_damage(attacker, defender, "attack")
    assert result.effectiveness == "resisted"


def test_neutral_label():
    """Check effectiveness label is neutral for cross-group matchup."""
    random.seed(42)
    attacker = make_creature(name="FireMon", mutation_type=MutationType.FIRE, base_atk=20)
    defender = make_creature(name="TechMon", mutation_type=MutationType.TECH, base_def=10)
    result = calculate_damage(attacker, defender, "attack")
    assert result.effectiveness == "neutral"


def test_trait_bonus_increases_damage():
    random.seed(42)
    attacker = make_creature(base_atk=20)
    defender = make_creature(base_def=10)

    no_bonus_total = 0
    bonus_total = 0
    trials = 50
    for i in range(trials):
        random.seed(i)
        r_no_bonus = calculate_damage(attacker, defender, "attack", trait_bonus=1.0)
        random.seed(i)
        r_bonus = calculate_damage(attacker, defender, "attack", trait_bonus=1.3)
        no_bonus_total += r_no_bonus.damage
        bonus_total += r_bonus.damage

    assert bonus_total > no_bonus_total


def test_damage_never_below_1_extreme_defense():
    """Even with atk=1, def=999, damage should be at least 1."""
    attacker = make_creature(base_atk=1)
    defender = make_creature(base_def=999)
    for seed in range(20):
        random.seed(seed)
        result = calculate_damage(attacker, defender, "weak attack")
        assert result.damage >= 1, f"Damage was {result.damage} with seed {seed}"


def test_damage_never_below_1_with_trait_bonus_zero():
    """Even with minimum possible inputs, damage stays >= 1."""
    attacker = make_creature(base_atk=1)
    defender = make_creature(base_def=999)
    for seed in range(20):
        random.seed(seed)
        result = calculate_damage(attacker, defender, "attack", trait_bonus=0.5)
        assert result.damage >= 1


def test_trait_bonus_stored_in_result():
    random.seed(42)
    attacker = make_creature()
    defender = make_creature()
    result = calculate_damage(attacker, defender, "attack", trait_bonus=1.2)
    assert result.trait_bonus == 1.2


def test_default_trait_bonus_is_1():
    random.seed(42)
    attacker = make_creature()
    defender = make_creature()
    result = calculate_damage(attacker, defender, "attack")
    assert result.trait_bonus == 1.0
