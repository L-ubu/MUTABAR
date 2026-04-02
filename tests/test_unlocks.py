"""
tests/test_unlocks.py
Tests for game/progression/unlocks.py.
"""

import pytest

from game.progression.unlocks import TIER_REQUIREMENTS, UnlockManager


class TestTierRequirements:
    def test_all_five_tiers_defined(self):
        expected = {"COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"}
        assert set(TIER_REQUIREMENTS.keys()) == expected

    def test_requirements_are_ascending(self):
        """Each tier should require at least as many runs as the previous."""
        ordered = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"]
        values = [TIER_REQUIREMENTS[t] for t in ordered]
        assert values == sorted(values), "TIER_REQUIREMENTS are not in ascending order"

    def test_common_requires_zero_runs(self):
        assert TIER_REQUIREMENTS["COMMON"] == 0

    def test_uncommon_requires_3(self):
        assert TIER_REQUIREMENTS["UNCOMMON"] == 3

    def test_rare_requires_10(self):
        assert TIER_REQUIREMENTS["RARE"] == 10

    def test_epic_requires_25(self):
        assert TIER_REQUIREMENTS["EPIC"] == 25

    def test_legendary_requires_50(self):
        assert TIER_REQUIREMENTS["LEGENDARY"] == 50


class TestUnlockManagerUnlockedTiers:
    def test_zero_runs_only_common(self):
        mgr = UnlockManager(0)
        assert mgr.unlocked_tiers == {"COMMON"}

    def test_two_runs_only_common(self):
        mgr = UnlockManager(2)
        assert mgr.unlocked_tiers == {"COMMON"}

    def test_three_runs_includes_uncommon(self):
        mgr = UnlockManager(3)
        assert "COMMON" in mgr.unlocked_tiers
        assert "UNCOMMON" in mgr.unlocked_tiers

    def test_ten_runs_includes_rare(self):
        mgr = UnlockManager(10)
        for tier in ("COMMON", "UNCOMMON", "RARE"):
            assert tier in mgr.unlocked_tiers

    def test_twenty_five_runs_includes_epic(self):
        mgr = UnlockManager(25)
        for tier in ("COMMON", "UNCOMMON", "RARE", "EPIC"):
            assert tier in mgr.unlocked_tiers

    def test_fifty_runs_all_tiers(self):
        mgr = UnlockManager(50)
        assert mgr.unlocked_tiers == {"COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"}

    def test_hundred_runs_all_tiers(self):
        mgr = UnlockManager(100)
        assert mgr.unlocked_tiers == {"COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"}

    def test_exactly_at_boundary(self):
        """Players at exact boundary values should have the tier unlocked."""
        for tier, required in TIER_REQUIREMENTS.items():
            mgr = UnlockManager(required)
            assert tier in mgr.unlocked_tiers

    def test_one_below_boundary(self):
        """Players one below a threshold should NOT have that tier."""
        for tier, required in TIER_REQUIREMENTS.items():
            if required == 0:
                continue
            mgr = UnlockManager(required - 1)
            assert tier not in mgr.unlocked_tiers


class TestUnlockManagerCheckNewUnlocks:
    def test_no_new_unlocks_same_runs(self):
        mgr = UnlockManager(5)
        assert mgr.check_new_unlocks(5, 5) == []

    def test_unlock_uncommon_crossing_threshold(self):
        mgr = UnlockManager(3)
        new = mgr.check_new_unlocks(2, 3)
        assert "UNCOMMON" in new

    def test_unlock_rare_crossing_threshold(self):
        mgr = UnlockManager(10)
        new = mgr.check_new_unlocks(9, 10)
        assert "RARE" in new

    def test_no_duplicate_unlocks(self):
        mgr = UnlockManager(10)
        # Going from 3 to 10 should unlock RARE only (UNCOMMON was already at 3)
        new = mgr.check_new_unlocks(3, 10)
        assert "RARE" in new
        assert "UNCOMMON" not in new
        assert "COMMON" not in new

    def test_multiple_unlocks_at_once(self):
        mgr = UnlockManager(10)
        # Jumping from 0 to 10 should unlock UNCOMMON and RARE together
        new = mgr.check_new_unlocks(0, 10)
        assert "UNCOMMON" in new
        assert "RARE" in new
        assert "COMMON" not in new  # was already unlocked at 0

    def test_returns_sorted_list(self):
        mgr = UnlockManager(50)
        new = mgr.check_new_unlocks(0, 50)
        assert new == sorted(new)
