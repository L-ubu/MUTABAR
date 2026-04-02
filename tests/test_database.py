import pytest
from game.creatures.creature import CreatureCategory
from game.creatures.database import (
    CREATURE_ROSTER,
    CreatureTemplate,
    get_creature_by_name,
    get_creatures_by_category,
)


def test_roster_has_at_least_50_entries():
    assert len(CREATURE_ROSTER) >= 50


def test_roster_has_at_least_40_animals():
    animals = [c for c in CREATURE_ROSTER if c.category == CreatureCategory.ANIMAL]
    assert len(animals) >= 40


def test_roster_has_at_least_10_mythologicals():
    myths = [c for c in CREATURE_ROSTER if c.category == CreatureCategory.MYTHOLOGICAL]
    assert len(myths) >= 10


def test_roster_has_at_least_3_originals():
    originals = [c for c in CREATURE_ROSTER if c.category == CreatureCategory.ORIGINAL]
    assert len(originals) >= 3


def test_snorerelax_exists_and_is_original():
    creature = get_creature_by_name("Snorerelax")
    assert creature is not None
    assert creature.category == CreatureCategory.ORIGINAL


def test_snorerelax_stats():
    creature = get_creature_by_name("Snorerelax")
    assert creature is not None
    assert creature.base_hp == 200
    assert creature.base_atk == 10
    assert creature.base_def == 18


def test_every_creature_has_at_least_2_traits():
    for creature in CREATURE_ROSTER:
        assert len(creature.traits) >= 2, (
            f"{creature.name} has only {len(creature.traits)} trait(s)"
        )


def test_get_creature_by_name_case_insensitive():
    result = get_creature_by_name("wolf")
    assert result is not None
    assert result.name == "Wolf"

    result_upper = get_creature_by_name("WOLF")
    assert result_upper is not None
    assert result_upper.name == "Wolf"


def test_get_creature_by_name_nonexistent_returns_none():
    assert get_creature_by_name("Nonexistent") is None


def test_get_creature_by_name_exact():
    result = get_creature_by_name("Dragon")
    assert result is not None
    assert result.category == CreatureCategory.MYTHOLOGICAL


def test_get_creatures_by_category_animals():
    animals = get_creatures_by_category(CreatureCategory.ANIMAL)
    assert len(animals) >= 40
    for c in animals:
        assert c.category == CreatureCategory.ANIMAL


def test_get_creatures_by_category_mythologicals():
    myths = get_creatures_by_category(CreatureCategory.MYTHOLOGICAL)
    assert len(myths) >= 10
    for c in myths:
        assert c.category == CreatureCategory.MYTHOLOGICAL


def test_get_creatures_by_category_originals():
    originals = get_creatures_by_category(CreatureCategory.ORIGINAL)
    assert len(originals) >= 3
    for c in originals:
        assert c.category == CreatureCategory.ORIGINAL


def test_creature_template_is_frozen():
    creature = get_creature_by_name("Wolf")
    assert creature is not None
    with pytest.raises((AttributeError, TypeError)):
        creature.name = "changed"  # type: ignore


def test_creature_names_are_unique():
    names = [c.name for c in CREATURE_ROSTER]
    assert len(names) == len(set(names)), "Duplicate creature names found"


def test_all_original_names_present():
    names = {c.name for c in CREATURE_ROSTER}
    for expected in ("Snorerelax", "Glitchfang", "Voidmaw"):
        assert expected in names, f"{expected} not found in roster"


def test_glitchfang_is_original():
    creature = get_creature_by_name("Glitchfang")
    assert creature is not None
    assert creature.category == CreatureCategory.ORIGINAL


def test_voidmaw_is_original():
    creature = get_creature_by_name("Voidmaw")
    assert creature is not None
    assert creature.category == CreatureCategory.ORIGINAL
