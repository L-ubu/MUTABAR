"""
tests/test_lootbox.py
Tests for game/progression/lootbox.py.
"""

import pytest

from game.creatures.creature import CreatureCategory
from game.creatures.database import CREATURE_ROSTER, CreatureTemplate, get_creature_by_name
from game.progression.lootbox import (
    Rarity,
    RollResult,
    _get_creature_rarity,
    _RARITY_POOLS,
    get_rarity_weights,
    roll_creature,
)


ALL_TIERS = {"COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"}


# ===========================================================================
# Rarity enum
# ===========================================================================


class TestRarityEnum:
    def test_rarity_values(self):
        assert Rarity.COMMON == 1
        assert Rarity.UNCOMMON == 2
        assert Rarity.RARE == 3
        assert Rarity.EPIC == 4
        assert Rarity.LEGENDARY == 5

    def test_rarity_ordering(self):
        assert Rarity.COMMON < Rarity.UNCOMMON < Rarity.RARE < Rarity.EPIC < Rarity.LEGENDARY

    def test_rarity_is_int_enum(self):
        assert isinstance(Rarity.COMMON, int)


# ===========================================================================
# _get_creature_rarity
# ===========================================================================


class TestGetCreatureRarity:
    def test_original_is_legendary(self):
        snorerelax = get_creature_by_name("Snorerelax")
        assert snorerelax is not None
        assert _get_creature_rarity(snorerelax) == Rarity.LEGENDARY

    def test_all_originals_are_legendary(self):
        for t in CREATURE_ROSTER:
            if t.category == CreatureCategory.ORIGINAL:
                assert _get_creature_rarity(t) == Rarity.LEGENDARY

    def test_mythological_is_rare(self):
        dragon = get_creature_by_name("Dragon")
        assert dragon is not None
        assert _get_creature_rarity(dragon) == Rarity.RARE

    def test_all_mythologicals_are_rare(self):
        for t in CREATURE_ROSTER:
            if t.category == CreatureCategory.MYTHOLOGICAL:
                assert _get_creature_rarity(t) == Rarity.RARE

    def test_animal_high_stats_is_uncommon(self):
        # Elephant: 150 + 15 + 20 = 185 >= 140
        elephant = get_creature_by_name("Elephant")
        assert elephant is not None
        assert _get_creature_rarity(elephant) == Rarity.UNCOMMON

    def test_animal_low_stats_is_common(self):
        # Jellyfish: 40 + 8 + 4 = 52 < 140
        jellyfish = get_creature_by_name("Jellyfish")
        assert jellyfish is not None
        assert _get_creature_rarity(jellyfish) == Rarity.COMMON

    def test_animal_exactly_140_is_uncommon(self):
        # Create a synthetic template with total == 140
        template = CreatureTemplate(
            name="TestBeast",
            category=CreatureCategory.ANIMAL,
            traits=[],
            base_hp=100,
            base_atk=20,
            base_def=20,
        )
        assert _get_creature_rarity(template) == Rarity.UNCOMMON

    def test_animal_exactly_139_is_common(self):
        template = CreatureTemplate(
            name="TestBeast2",
            category=CreatureCategory.ANIMAL,
            traits=[],
            base_hp=100,
            base_atk=20,
            base_def=19,
        )
        assert _get_creature_rarity(template) == Rarity.COMMON


# ===========================================================================
# get_rarity_weights
# ===========================================================================


class TestGetRarityWeights:
    def test_weights_sum_to_100_wave1(self):
        weights = get_rarity_weights(1, ALL_TIERS)
        assert sum(weights.values()) == pytest.approx(100.0, rel=1e-6)

    def test_weights_sum_to_100_wave10(self):
        weights = get_rarity_weights(10, ALL_TIERS)
        assert sum(weights.values()) == pytest.approx(100.0, rel=1e-6)

    def test_weights_sum_to_100_wave31(self):
        weights = get_rarity_weights(31, ALL_TIERS)
        assert sum(weights.values()) == pytest.approx(100.0, rel=1e-6)

    def test_higher_wave_reduces_common_weight(self):
        w1 = get_rarity_weights(1, ALL_TIERS)
        w10 = get_rarity_weights(10, ALL_TIERS)
        assert w10[Rarity.COMMON] < w1[Rarity.COMMON]

    def test_higher_wave_increases_higher_tiers(self):
        w1 = get_rarity_weights(1, ALL_TIERS)
        w10 = get_rarity_weights(10, ALL_TIERS)
        assert w10[Rarity.RARE] > w1[Rarity.RARE]

    def test_capped_at_wave_31(self):
        w31 = get_rarity_weights(31, ALL_TIERS)
        w100 = get_rarity_weights(100, ALL_TIERS)
        for rarity in Rarity:
            assert w31[rarity] == pytest.approx(w100[rarity], rel=1e-6)

    def test_locked_tier_has_zero_weight(self):
        # Unlock only COMMON and UNCOMMON
        unlocked = {"COMMON", "UNCOMMON"}
        weights = get_rarity_weights(1, unlocked)
        assert weights[Rarity.RARE] == pytest.approx(0.0)
        assert weights[Rarity.EPIC] == pytest.approx(0.0)
        assert weights[Rarity.LEGENDARY] == pytest.approx(0.0)

    def test_locked_tiers_still_sums_to_100(self):
        unlocked = {"COMMON", "UNCOMMON"}
        weights = get_rarity_weights(1, unlocked)
        assert sum(weights.values()) == pytest.approx(100.0, rel=1e-6)

    def test_all_weights_non_negative(self):
        for wave in (1, 5, 15, 31):
            weights = get_rarity_weights(wave, ALL_TIERS)
            for rarity, w in weights.items():
                assert w >= 0.0

    def test_returns_all_rarity_keys(self):
        weights = get_rarity_weights(1, ALL_TIERS)
        assert set(weights.keys()) == set(Rarity)


# ===========================================================================
# roll_creature
# ===========================================================================


class TestRollCreature:
    def test_returns_roll_result(self):
        result = roll_creature(1, ALL_TIERS)
        assert isinstance(result, RollResult)

    def test_rarity_in_unlocked_tiers(self):
        result = roll_creature(1, ALL_TIERS)
        assert result.rarity.name in ALL_TIERS

    def test_template_is_creature_template(self):
        result = roll_creature(1, ALL_TIERS)
        assert isinstance(result.template, CreatureTemplate)

    def test_strip_has_at_least_15_items(self):
        for _ in range(5):
            result = roll_creature(1, ALL_TIERS)
            assert len(result.strip) >= 15

    def test_winner_near_end_of_strip(self):
        """winner_index should be within the last 6 positions of the strip."""
        for _ in range(10):
            result = roll_creature(1, ALL_TIERS)
            strip_len = len(result.strip)
            # strip_size=20, winner inserted at 20-randint(2,5)=15..18, final strip len=21.
            # So winner_index is at most strip_len-3 and at least strip_len-6.
            assert result.winner_index >= strip_len - 6
            assert result.winner_index < strip_len

    def test_winner_in_strip(self):
        result = roll_creature(1, ALL_TIERS)
        assert result.strip[result.winner_index] is result.template

    def test_only_common_when_locked(self):
        """With only COMMON unlocked, all rolls must be COMMON."""
        for _ in range(20):
            result = roll_creature(1, {"COMMON"})
            assert result.rarity == Rarity.COMMON

    def test_strip_contains_creature_templates(self):
        result = roll_creature(1, ALL_TIERS)
        for item in result.strip:
            assert isinstance(item, CreatureTemplate)

    def test_no_error_on_high_waves(self):
        result = roll_creature(50, ALL_TIERS)
        assert result is not None
