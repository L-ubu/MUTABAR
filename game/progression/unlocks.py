"""
game/progression/unlocks.py
Tier unlock system for MUTABAR.
"""

from __future__ import annotations

# Minimum completed runs required to unlock each rarity tier.
TIER_REQUIREMENTS: dict[str, int] = {
    "COMMON": 0,
    "UNCOMMON": 3,
    "RARE": 10,
    "EPIC": 25,
    "LEGENDARY": 50,
}


class UnlockManager:
    """Tracks which rarity tiers the player has unlocked based on completed runs."""

    def __init__(self, completed_runs: int) -> None:
        self._completed_runs = completed_runs

    @property
    def unlocked_tiers(self) -> set[str]:
        """Return the set of tier names the player has currently unlocked."""
        return {
            tier
            for tier, required in TIER_REQUIREMENTS.items()
            if self._completed_runs >= required
        }

    def check_new_unlocks(self, old_runs: int, new_runs: int) -> list[str]:
        """
        Return the list of tier names newly unlocked when going from
        *old_runs* to *new_runs* completed runs.
        """
        old_unlocked = {
            tier
            for tier, required in TIER_REQUIREMENTS.items()
            if old_runs >= required
        }
        new_unlocked = {
            tier
            for tier, required in TIER_REQUIREMENTS.items()
            if new_runs >= required
        }
        return sorted(new_unlocked - old_unlocked)
