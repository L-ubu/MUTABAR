import pytest
from game.creatures.types import MutationType
from game.creatures.traits import Trait
from game.creatures.creature import Creature, CreatureCategory


def make_creature(**kwargs):
    defaults = dict(
        name="Emberfox",
        category=CreatureCategory.ANIMAL,
        mutation_type=MutationType.FIRE,
        traits=[],
        base_hp=50,
        base_atk=10,
        base_def=8,
    )
    defaults.update(kwargs)
    return Creature(**defaults)


# --- CreatureCategory ---

def test_creature_category_values():
    assert CreatureCategory.ANIMAL.value == "animal"
    assert CreatureCategory.MYTHOLOGICAL.value == "mythological"
    assert CreatureCategory.ORIGINAL.value == "original"


# --- Basic creation ---

def test_create_creature_defaults():
    c = make_creature()
    assert c.name == "Emberfox"
    assert c.category == CreatureCategory.ANIMAL
    assert c.mutation_type == MutationType.FIRE
    assert c.traits == []
    assert c.base_hp == 50
    assert c.base_atk == 10
    assert c.base_def == 8
    assert c.level == 1
    assert c.xp == 0


def test_current_hp_starts_at_max_hp():
    c = make_creature()
    assert c.current_hp == c.max_hp


# --- Properties at level 1 ---

def test_max_hp_level_1():
    c = make_creature(base_hp=50)
    assert c.max_hp == 50  # 50 + (1-1)*5


def test_atk_level_1():
    c = make_creature(base_atk=10)
    assert c.atk == 10  # 10 + (1-1)*2


def test_defense_level_1():
    c = make_creature(base_def=8)
    assert c.defense == 8  # 8 + (1-1)*2


# --- Properties scale with level ---

def test_max_hp_scales_with_level():
    c = make_creature(base_hp=50, level=5)
    assert c.max_hp == 50 + (5 - 1) * 5  # 70


def test_atk_scales_with_level():
    c = make_creature(base_atk=10, level=5)
    assert c.atk == 10 + (5 - 1) * 2  # 18


def test_defense_scales_with_level():
    c = make_creature(base_def=8, level=5)
    assert c.defense == 8 + (5 - 1) * 2  # 16


# --- take_damage ---

def test_take_damage_reduces_hp():
    c = make_creature(base_hp=50)
    c.take_damage(10)
    assert c.current_hp == 40


def test_take_damage_floor_at_zero():
    c = make_creature(base_hp=50)
    c.take_damage(999)
    assert c.current_hp == 0


def test_hp_cannot_go_below_zero():
    c = make_creature(base_hp=50)
    c.take_damage(50)
    c.take_damage(1)
    assert c.current_hp == 0


# --- heal ---

def test_heal_increases_hp():
    c = make_creature(base_hp=50)
    c.take_damage(20)
    c.heal(10)
    assert c.current_hp == 40


def test_heal_capped_at_max_hp():
    c = make_creature(base_hp=50)
    c.take_damage(10)
    c.heal(999)
    assert c.current_hp == c.max_hp


# --- full_heal ---

def test_full_heal_restores_to_max():
    c = make_creature(base_hp=50)
    c.take_damage(30)
    c.full_heal()
    assert c.current_hp == c.max_hp


# --- is_fainted ---

def test_is_not_fainted_when_hp_positive():
    c = make_creature(base_hp=50)
    assert not c.is_fainted


def test_is_fainted_when_hp_zero():
    c = make_creature(base_hp=50)
    c.take_damage(50)
    assert c.is_fainted


def test_is_fainted_when_hp_below_zero_guarded():
    c = make_creature(base_hp=50)
    c.take_damage(9999)
    assert c.is_fainted
    assert c.current_hp == 0


# --- Traits integration ---

def test_creature_with_traits():
    t = Trait(name="Flaming Fists", description="Burns", keywords=["fire", "punch"])
    c = make_creature(traits=[t])
    assert len(c.traits) == 1
    assert c.traits[0].name == "Flaming Fists"


# --- current_hp starts at level-appropriate max_hp ---

def test_current_hp_at_level_5():
    c = make_creature(base_hp=50, level=5)
    assert c.current_hp == c.max_hp  # 70
