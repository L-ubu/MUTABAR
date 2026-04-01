import pytest
from game.creatures.traits import Trait, compute_trait_bonus


def test_trait_is_frozen_dataclass():
    t = Trait(name="Flaming Fists", description="Burns on punch", keywords=["punch", "fire"])
    assert t.name == "Flaming Fists"
    assert t.description == "Burns on punch"
    assert t.keywords == ["punch", "fire"]


def test_trait_is_immutable():
    t = Trait(name="Flaming Fists", description="Burns on punch", keywords=["punch", "fire"])
    with pytest.raises((AttributeError, TypeError)):
        t.name = "changed"


def test_no_match_returns_1_0():
    t = Trait(name="Aqua Slam", description="Water slam", keywords=["swim", "splash"])
    result = compute_trait_bonus("punch hard", [t])
    assert result == 1.0


def test_exact_word_match_gives_bonus():
    t = Trait(name="Aqua Slam", description="Water slam", keywords=["swim", "splash"])
    result = compute_trait_bonus("swim to the target", [t])
    assert result >= 1.1


def test_substring_match_gives_bonus():
    t = Trait(name="Flame Burst", description="Fiery burst", keywords=["fire", "burn"])
    result = compute_trait_bonus("unleash a fireball", [t])
    assert result >= 1.1


def test_multiple_matching_traits_stack():
    t1 = Trait(name="Flaming Fists", description="Burns", keywords=["punch", "fire"])
    t2 = Trait(name="Quick Strike", description="Fast attack", keywords=["strike", "fast"])
    result = compute_trait_bonus("punch and strike fast", [t1, t2])
    assert result > 1.1


def test_bonus_capped_at_1_3():
    traits = [
        Trait(name=f"Trait{i}", description="desc", keywords=[f"word{i}"])
        for i in range(20)
    ]
    command = " ".join([f"word{i}" for i in range(20)])
    result = compute_trait_bonus(command, traits)
    assert result <= 1.3


def test_empty_traits_returns_1_0():
    result = compute_trait_bonus("attack fiercely", [])
    assert result == 1.0


def test_empty_command_returns_1_0():
    t = Trait(name="Fire", description="Fire", keywords=["fire"])
    result = compute_trait_bonus("", [t])
    assert result == 1.0
