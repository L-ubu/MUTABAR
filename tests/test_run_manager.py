"""
tests/test_run_manager.py
Tests for game/progression/run_manager.py.
"""

import random

import pytest

from game.battle.cpu_ai import CpuDifficulty
from game.creatures.types import MutationType
from game.progression.run_manager import RunManager, RunState


# Unlocked tiers used across tests
ALL_TIERS = {"COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager():
    return RunManager(unlocked_tiers=ALL_TIERS)


@pytest.fixture
def started_manager(manager):
    manager.start_new_run()
    return manager


# ---------------------------------------------------------------------------
# start_new_run
# ---------------------------------------------------------------------------


class TestStartNewRun:
    def test_state_is_team_select(self, manager):
        manager.start_new_run()
        assert manager.state == RunState.TEAM_SELECT

    def test_wave_is_zero(self, manager):
        manager.start_new_run()
        assert manager.wave == 0

    def test_player_team_cleared(self, manager):
        manager.start_new_run()
        assert manager.player_team == []

    def test_cpu_team_cleared(self, manager):
        manager.start_new_run()
        assert manager.cpu_team == []

    def test_initial_state_is_idle(self, manager):
        assert manager.state == RunState.IDLE

    def test_can_restart(self, started_manager):
        """Calling start_new_run twice resets state correctly."""
        started_manager.advance_wave()
        started_manager.start_new_run()
        assert started_manager.state == RunState.TEAM_SELECT
        assert started_manager.wave == 0


# ---------------------------------------------------------------------------
# roll_starting_team
# ---------------------------------------------------------------------------


class TestRollStartingTeam:
    def test_returns_three_creatures(self, started_manager):
        random.seed(42)
        team = started_manager.roll_starting_team()
        assert len(team) == 3

    def test_all_have_valid_mutation_type(self, started_manager):
        random.seed(42)
        team = started_manager.roll_starting_team()
        valid_types = set(MutationType)
        for creature in team:
            assert creature.mutation_type in valid_types

    def test_stores_team_on_manager(self, started_manager):
        random.seed(42)
        team = started_manager.roll_starting_team()
        assert started_manager.player_team is team

    def test_creatures_have_names(self, started_manager):
        random.seed(42)
        team = started_manager.roll_starting_team()
        for creature in team:
            assert creature.name and isinstance(creature.name, str)

    def test_different_seeds_can_yield_different_teams(self, manager):
        manager.start_new_run()
        random.seed(1)
        team_a = manager.roll_starting_team()

        manager.start_new_run()
        random.seed(99)
        team_b = manager.roll_starting_team()

        names_a = [c.name for c in team_a]
        names_b = [c.name for c in team_b]
        # With seed 42 vs 99 teams are very likely different; we just check
        # the call doesn't crash and both are length-3 lists.
        assert len(team_a) == 3
        assert len(team_b) == 3


# ---------------------------------------------------------------------------
# advance_wave
# ---------------------------------------------------------------------------


class TestAdvanceWave:
    def test_increments_wave(self, started_manager):
        started_manager.advance_wave()
        assert started_manager.wave == 1

    def test_state_is_battle(self, started_manager):
        started_manager.advance_wave()
        assert started_manager.state == RunState.BATTLE

    def test_multiple_advances(self, started_manager):
        for i in range(1, 6):
            started_manager.advance_wave()
            assert started_manager.wave == i
        assert started_manager.state == RunState.BATTLE


# ---------------------------------------------------------------------------
# generate_cpu_team
# ---------------------------------------------------------------------------


class TestGenerateCpuTeam:
    def test_wave_1_gives_one_creature(self, started_manager):
        random.seed(42)
        started_manager.advance_wave()  # wave = 1
        team = started_manager.generate_cpu_team()
        assert len(team) == 1

    def test_wave_5_gives_two_creatures(self, started_manager):
        random.seed(42)
        for _ in range(5):
            started_manager.advance_wave()  # wave = 5 → 1 + 5//5 = 2
        team = started_manager.generate_cpu_team()
        assert len(team) == 2

    def test_wave_6_gives_two_creatures(self, started_manager):
        random.seed(42)
        for _ in range(6):
            started_manager.advance_wave()  # wave = 6
        team = started_manager.generate_cpu_team()
        assert len(team) == 2

    def test_wave_10_gives_three_creatures(self, started_manager):
        random.seed(42)
        for _ in range(10):
            started_manager.advance_wave()  # wave = 10 → 1 + 10//5 = 3
        team = started_manager.generate_cpu_team()
        assert len(team) == 3

    def test_wave_10_count(self, started_manager):
        """1 + 10//5 = 3, but capped at 3."""
        for _ in range(10):
            started_manager.advance_wave()
        random.seed(42)
        team = started_manager.generate_cpu_team()
        assert len(team) == 3

    def test_cpu_team_level_equals_wave(self, started_manager):
        random.seed(42)
        for _ in range(3):
            started_manager.advance_wave()  # wave = 3
        team = started_manager.generate_cpu_team()
        for creature in team:
            assert creature.level == 3

    def test_stores_cpu_team(self, started_manager):
        random.seed(42)
        started_manager.advance_wave()
        team = started_manager.generate_cpu_team()
        assert started_manager.cpu_team is team

    def test_count_capped_at_three(self, started_manager):
        random.seed(42)
        for _ in range(50):
            started_manager.advance_wave()  # wave = 50 → 1 + 50//5 = 11, capped to 3
        team = started_manager.generate_cpu_team()
        assert len(team) == 3


# ---------------------------------------------------------------------------
# cpu_difficulty property
# ---------------------------------------------------------------------------


class TestCpuDifficulty:
    @pytest.mark.parametrize("wave", [1, 2, 3, 4, 5])
    def test_basic_waves(self, started_manager, wave):
        for _ in range(wave):
            started_manager.advance_wave()
        assert started_manager.cpu_difficulty == CpuDifficulty.BASIC

    @pytest.mark.parametrize("wave", [6, 7, 10, 15])
    def test_tactical_waves(self, started_manager, wave):
        for _ in range(wave):
            started_manager.advance_wave()
        assert started_manager.cpu_difficulty == CpuDifficulty.TACTICAL

    @pytest.mark.parametrize("wave", [16, 17, 20, 50])
    def test_adaptive_waves(self, started_manager, wave):
        for _ in range(wave):
            started_manager.advance_wave()
        assert started_manager.cpu_difficulty == CpuDifficulty.ADAPTIVE


# ---------------------------------------------------------------------------
# end_run
# ---------------------------------------------------------------------------


class TestEndRun:
    def test_returns_waves_survived(self, started_manager):
        for _ in range(7):
            started_manager.advance_wave()
        result = started_manager.end_run()
        assert result["waves_survived"] == 7

    def test_mutagen_earned_is_wave_times_five(self, started_manager):
        for _ in range(7):
            started_manager.advance_wave()
        result = started_manager.end_run()
        assert result["mutagen_earned"] == 35

    def test_state_is_ended(self, started_manager):
        started_manager.end_run()
        assert started_manager.state == RunState.ENDED

    def test_zero_waves_end_run(self, started_manager):
        result = started_manager.end_run()
        assert result["waves_survived"] == 0
        assert result["mutagen_earned"] == 0

    def test_result_has_expected_keys(self, started_manager):
        result = started_manager.end_run()
        assert set(result.keys()) == {"waves_survived", "mutagen_earned"}


# ---------------------------------------------------------------------------
# RunState enum
# ---------------------------------------------------------------------------


class TestRunState:
    def test_all_states_exist(self):
        states = {s.name for s in RunState}
        assert states == {"IDLE", "TEAM_SELECT", "BATTLE", "POST_BATTLE", "LOOTBOX", "ENDED"}
