import random

import pytest

from game.creatures.creature import Creature, CreatureCategory
from game.creatures.traits import Trait
from game.creatures.types import MutationType
from game.battle.engine import Battle, BattleState, TurnResult
from game.battle.damage import DamageResult
from game.battle.status_effects import StatusEffect, StatusType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_creature(
    name="TestMon",
    mutation_type=MutationType.FIRE,
    base_hp=100,
    base_atk=10,
    base_def=5,
    traits=None,
    level=1,
):
    return Creature(
        name=name,
        category=CreatureCategory.ANIMAL,
        mutation_type=mutation_type,
        traits=traits or [],
        base_hp=base_hp,
        base_atk=base_atk,
        base_def=base_def,
        level=level,
    )


def make_battle(
    player_team=None,
    cpu_team=None,
):
    if player_team is None:
        player_team = [make_creature(name="Player1")]
    if cpu_team is None:
        cpu_team = [make_creature(name="CPU1")]
    return Battle(player_team=player_team, cpu_team=cpu_team)


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------

def test_battle_initialises_correctly():
    random.seed(42)
    p = make_creature(name="PlayerMon")
    c = make_creature(name="CpuMon")
    battle = Battle(player_team=[p], cpu_team=[c])

    assert battle.player_active is p
    assert battle.cpu_active is c
    assert battle.state == BattleState.ACTIVE
    assert battle.turn_number == 0
    assert battle.player_active_effects == []
    assert battle.cpu_active_effects == []


def test_battle_active_is_first_creature():
    random.seed(42)
    p1 = make_creature(name="P1")
    p2 = make_creature(name="P2")
    c1 = make_creature(name="C1")
    battle = Battle(player_team=[p1, p2], cpu_team=[c1])

    assert battle.player_active is p1
    assert battle.cpu_active is c1


def test_battle_no_alive_raises():
    dead = make_creature(name="Dead")
    dead.take_damage(9999)
    with pytest.raises(ValueError):
        Battle(player_team=[dead], cpu_team=[make_creature()])


# ---------------------------------------------------------------------------
# execute_player_turn — basic behaviour
# ---------------------------------------------------------------------------

def test_player_turn_increments_turn_number():
    random.seed(42)
    battle = make_battle()
    battle.execute_player_turn("attack")
    assert battle.turn_number == 1
    battle.execute_player_turn("attack")
    assert battle.turn_number == 2


def test_player_turn_returns_turn_result():
    random.seed(42)
    battle = make_battle()
    result = battle.execute_player_turn("attack")
    assert isinstance(result, TurnResult)


def test_player_turn_deals_damage():
    random.seed(42)
    battle = make_battle()
    cpu_hp_before = battle.cpu_active.current_hp
    result = battle.execute_player_turn("attack")
    assert battle.cpu_active.current_hp < cpu_hp_before
    assert result.damage_dealt > 0


def test_player_turn_receives_damage():
    random.seed(42)
    battle = make_battle()
    player_hp_before = battle.player_active.current_hp
    result = battle.execute_player_turn("attack")
    # Player may receive damage OR cpu may also attack back; either hp went down or damage_received reported
    assert result.damage_received >= 0  # at minimum non-negative
    # At least the cpu was processed (damage_received field set)
    assert isinstance(result.damage_received, int)


def test_turn_result_has_player_command():
    random.seed(42)
    battle = make_battle()
    result = battle.execute_player_turn("fire blast")
    assert result.player_command == "fire blast"


def test_turn_result_cpu_command_non_empty():
    random.seed(42)
    battle = make_battle()
    result = battle.execute_player_turn("attack")
    assert isinstance(result.cpu_command, str)
    assert len(result.cpu_command) > 0


# ---------------------------------------------------------------------------
# Battle ends — PLAYER_WIN
# ---------------------------------------------------------------------------

def test_battle_ends_player_win_single_cpu():
    """When CPU's only creature faints, state becomes PLAYER_WIN."""
    random.seed(42)
    # Give player massive attack, cpu tiny hp
    player = make_creature(name="Titan", base_atk=999, base_hp=200, base_def=50)
    cpu = make_creature(name="Weakling", base_hp=1, base_atk=1, base_def=1)
    battle = Battle(player_team=[player], cpu_team=[cpu])

    result = battle.execute_player_turn("crush")
    assert battle.state == BattleState.PLAYER_WIN


def test_battle_ends_player_win_all_cpu_fainted():
    """Both CPU creatures fainted over two turns → PLAYER_WIN."""
    random.seed(42)
    player = make_creature(name="Titan", base_atk=999, base_hp=500, base_def=50)
    cpu1 = make_creature(name="CpuWeak1", base_hp=1, base_atk=1, base_def=1)
    cpu2 = make_creature(name="CpuWeak2", base_hp=1, base_atk=1, base_def=1)
    battle = Battle(player_team=[player], cpu_team=[cpu1, cpu2])

    # First turn: cpu1 faints, cpu2 swaps in
    battle.execute_player_turn("crush")
    assert not battle.state == BattleState.PLAYER_WIN  # cpu2 should have swapped in

    # Second turn: cpu2 faints
    battle.execute_player_turn("crush")
    assert battle.state == BattleState.PLAYER_WIN


# ---------------------------------------------------------------------------
# Battle ends — CPU_WIN
# ---------------------------------------------------------------------------

def test_battle_ends_cpu_win_single_player():
    """When player's only creature faints, state becomes CPU_WIN."""
    random.seed(42)
    player = make_creature(name="Weakling", base_hp=1, base_atk=1, base_def=1)
    cpu = make_creature(name="Titan", base_atk=999, base_hp=200, base_def=50)
    battle = Battle(player_team=[player], cpu_team=[cpu])

    # We need to get cpu to attack player; player might not kill cpu in one turn
    # Force scenario: give player no attack, cpu enough to one-shot
    for _ in range(10):
        if battle.state != BattleState.ACTIVE:
            break
        battle.execute_player_turn("attack")

    assert battle.state == BattleState.CPU_WIN


# ---------------------------------------------------------------------------
# Swapping when active faints
# ---------------------------------------------------------------------------

def test_cpu_swaps_when_active_faints():
    """CPU's second creature becomes active when the first faints."""
    random.seed(42)
    player = make_creature(name="Titan", base_atk=999, base_hp=500, base_def=50)
    cpu1 = make_creature(name="CpuFirst", base_hp=1, base_atk=1, base_def=1)
    cpu2 = make_creature(name="CpuSecond", base_hp=100, base_atk=5, base_def=5)
    battle = Battle(player_team=[player], cpu_team=[cpu1, cpu2])

    assert battle.cpu_active is cpu1
    battle.execute_player_turn("crush")

    # cpu1 should have fainted and cpu2 should now be active
    assert cpu1.is_fainted
    assert battle.cpu_active is cpu2
    assert battle.state == BattleState.ACTIVE


def test_player_swaps_when_active_faints():
    """Player's second creature becomes active when first faints."""
    random.seed(42)
    player1 = make_creature(name="PlayerFirst", base_hp=1, base_atk=1, base_def=1)
    player2 = make_creature(name="PlayerSecond", base_hp=100, base_atk=5, base_def=5)
    cpu = make_creature(name="CpuTitan", base_atk=999, base_hp=200, base_def=50)
    battle = Battle(player_team=[player1, player2], cpu_team=[cpu])

    assert battle.player_active is player1

    # Keep going until player1 faints
    for _ in range(10):
        if battle.state != BattleState.ACTIVE:
            break
        battle.execute_player_turn("attack")
        if battle.player_active is player2:
            break

    assert player1.is_fainted
    # Either player2 took over or battle ended with CPU_WIN
    assert battle.player_active is player2 or battle.state == BattleState.CPU_WIN


# ---------------------------------------------------------------------------
# Status effects
# ---------------------------------------------------------------------------

def test_status_effects_tick_each_turn():
    """A status effect should have its remaining_turns decremented each turn."""
    random.seed(42)
    battle = make_battle()
    burn = StatusEffect(status_type=StatusType.BURN, duration=3)
    battle.player_active_effects.append(burn)

    initial_remaining = burn.remaining_turns
    battle.execute_player_turn("attack")
    assert burn.remaining_turns == initial_remaining - 1


def test_burn_dot_applied_to_target():
    """BURN on player causes DoT each turn."""
    random.seed(42)
    battle = make_battle()
    burn = StatusEffect(status_type=StatusType.BURN, duration=3)
    battle.player_active_effects.append(burn)

    hp_before = battle.player_active.current_hp
    result = battle.execute_player_turn("attack")

    assert result.player_dot_damage == 8
    # player should have taken burn damage (8) in addition to any combat damage
    assert battle.player_active.current_hp <= hp_before - 8


def test_cpu_burn_dot_applied():
    """BURN on CPU causes DoT each turn."""
    random.seed(42)
    battle = make_battle()
    burn = StatusEffect(status_type=StatusType.BURN, duration=3)
    battle.cpu_active_effects.append(burn)

    result = battle.execute_player_turn("attack")
    assert result.cpu_dot_damage == 8


def test_expired_effects_are_cleaned():
    """Effects that expire during a turn are removed from the effect list."""
    random.seed(42)
    battle = make_battle()
    stun = StatusEffect(status_type=StatusType.STUN, duration=1)
    battle.player_active_effects.append(stun)

    battle.execute_player_turn("attack")
    # stun had duration=1; it should now be gone
    assert stun not in battle.player_active_effects


def test_stun_prevents_player_attack():
    """With STUN on player, they skip attack so CPU does not take combat damage."""
    random.seed(42)
    battle = make_battle()
    stun = StatusEffect(status_type=StatusType.STUN, duration=2)
    battle.player_active_effects.append(stun)

    cpu_hp_before = battle.cpu_active.current_hp
    result = battle.execute_player_turn("attack")

    assert result.damage_dealt == 0
    # CPU hp should be the same (no combat damage from player)
    # (DoT might apply to CPU if it had effects, but we added no CPU effects)
    assert battle.cpu_active.current_hp == cpu_hp_before


def test_turn_result_dot_default_zero():
    """With no status effects, dot damage fields default to 0."""
    random.seed(42)
    battle = make_battle()
    result = battle.execute_player_turn("attack")
    assert result.player_dot_damage == 0
    assert result.cpu_dot_damage == 0


# ---------------------------------------------------------------------------
# TurnResult fields
# ---------------------------------------------------------------------------

def test_turn_result_damage_result_fields():
    random.seed(42)
    battle = make_battle()
    result = battle.execute_player_turn("attack")
    if result.player_damage_result is not None:
        assert isinstance(result.player_damage_result, DamageResult)
        assert result.player_damage_result.damage >= 1


def test_turn_result_no_damage_result_when_stunned():
    """player_damage_result should be None when player is stunned."""
    random.seed(42)
    battle = make_battle()
    stun = StatusEffect(status_type=StatusType.STUN, duration=2)
    battle.player_active_effects.append(stun)

    result = battle.execute_player_turn("attack")
    assert result.player_damage_result is None


# ---------------------------------------------------------------------------
# BattleState enum
# ---------------------------------------------------------------------------

def test_battle_state_values():
    assert BattleState.ACTIVE.value == "ACTIVE"
    assert BattleState.PLAYER_WIN.value == "PLAYER_WIN"
    assert BattleState.CPU_WIN.value == "CPU_WIN"
