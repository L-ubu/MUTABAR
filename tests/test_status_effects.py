import pytest

from game.battle.status_effects import (
    StatusType,
    StatusEffect,
    apply_tick,
    apply_damage_modifier,
)


# --- StatusType enum ---

def test_status_type_values_exist():
    assert StatusType.BURN
    assert StatusType.FREEZE
    assert StatusType.POISON
    assert StatusType.PHASE
    assert StatusType.STUN
    assert StatusType.DRAIN
    assert StatusType.FEAR
    assert StatusType.SHIELD


# --- StatusEffect dataclass ---

def test_status_effect_creation():
    effect = StatusEffect(status_type=StatusType.BURN, duration=3)
    assert effect.status_type == StatusType.BURN
    assert effect.duration == 3
    assert effect.remaining_turns == 3


def test_status_effect_remaining_starts_at_duration():
    effect = StatusEffect(status_type=StatusType.POISON, duration=5)
    assert effect.remaining_turns == 5


def test_status_effect_not_expired_initially():
    effect = StatusEffect(status_type=StatusType.STUN, duration=2)
    assert not effect.is_expired


def test_status_effect_expired_when_remaining_zero():
    effect = StatusEffect(status_type=StatusType.BURN, duration=1)
    apply_tick(effect)
    assert effect.is_expired


def test_status_effect_not_expired_after_partial_ticks():
    effect = StatusEffect(status_type=StatusType.FREEZE, duration=3)
    apply_tick(effect)
    assert not effect.is_expired
    apply_tick(effect)
    assert not effect.is_expired


# --- apply_tick ---

def test_tick_decrements_remaining_turns():
    effect = StatusEffect(status_type=StatusType.BURN, duration=3)
    apply_tick(effect)
    assert effect.remaining_turns == 2


def test_burn_tick_returns_flat_dot():
    effect = StatusEffect(status_type=StatusType.BURN, duration=3)
    dot = apply_tick(effect)
    assert dot == 8


def test_burn_dot_is_always_flat_8():
    effect = StatusEffect(status_type=StatusType.BURN, duration=5)
    for _ in range(4):
        dot = apply_tick(effect)
        assert dot == 8


def test_poison_tick_scales_with_turns_elapsed():
    effect = StatusEffect(status_type=StatusType.POISON, duration=5)
    # First tick: turns_elapsed becomes 1 after tick, dot = 5 * 1
    dot1 = apply_tick(effect)
    assert dot1 == 5
    # Second tick: turns_elapsed becomes 2, dot = 5 * 2
    dot2 = apply_tick(effect)
    assert dot2 == 10
    # Third tick: turns_elapsed becomes 3, dot = 5 * 3
    dot3 = apply_tick(effect)
    assert dot3 == 15


def test_freeze_tick_returns_zero_dot():
    effect = StatusEffect(status_type=StatusType.FREEZE, duration=3)
    dot = apply_tick(effect)
    assert dot == 0


def test_stun_tick_returns_zero_dot():
    effect = StatusEffect(status_type=StatusType.STUN, duration=2)
    dot = apply_tick(effect)
    assert dot == 0


def test_drain_tick_returns_zero_dot():
    effect = StatusEffect(status_type=StatusType.DRAIN, duration=2)
    dot = apply_tick(effect)
    assert dot == 0


def test_fear_tick_returns_zero_dot():
    effect = StatusEffect(status_type=StatusType.FEAR, duration=2)
    dot = apply_tick(effect)
    assert dot == 0


def test_shield_tick_returns_zero_dot():
    effect = StatusEffect(status_type=StatusType.SHIELD, duration=2)
    dot = apply_tick(effect)
    assert dot == 0


def test_phase_tick_returns_zero_dot():
    effect = StatusEffect(status_type=StatusType.PHASE, duration=2)
    dot = apply_tick(effect)
    assert dot == 0


# --- apply_damage_modifier ---

def test_no_effects_returns_base_damage():
    result = apply_damage_modifier(100, [], is_attacker=True)
    assert result == 100


def test_no_effects_defender_returns_base_damage():
    result = apply_damage_modifier(100, [], is_attacker=False)
    assert result == 100


def test_burn_increases_damage_taken_by_defender():
    """Defender with BURN takes 10% more damage."""
    burn = StatusEffect(status_type=StatusType.BURN, duration=3)
    result = apply_damage_modifier(100, [burn], is_attacker=False)
    assert result == 110  # 100 * 1.1


def test_burn_does_not_affect_attacker_output():
    """BURN on an attacker does not change their outgoing damage."""
    burn = StatusEffect(status_type=StatusType.BURN, duration=3)
    result = apply_damage_modifier(100, [burn], is_attacker=True)
    assert result == 100


def test_shield_reduces_damage_taken_by_defender():
    """Defender with SHIELD takes 30% less damage."""
    shield = StatusEffect(status_type=StatusType.SHIELD, duration=3)
    result = apply_damage_modifier(100, [shield], is_attacker=False)
    assert result == 70  # 100 * 0.7


def test_shield_does_not_affect_attacker_output():
    shield = StatusEffect(status_type=StatusType.SHIELD, duration=3)
    result = apply_damage_modifier(100, [shield], is_attacker=True)
    assert result == 100


def test_fear_reduces_attacker_output():
    """Attacker with FEAR deals 20% less damage."""
    fear = StatusEffect(status_type=StatusType.FEAR, duration=3)
    result = apply_damage_modifier(100, [fear], is_attacker=True)
    assert result == 80  # 100 * 0.8


def test_fear_does_not_affect_defender():
    fear = StatusEffect(status_type=StatusType.FEAR, duration=3)
    result = apply_damage_modifier(100, [fear], is_attacker=False)
    assert result == 100


def test_expired_effects_are_skipped():
    """Expired effects should not apply modifiers."""
    burn = StatusEffect(status_type=StatusType.BURN, duration=1)
    # Expire the effect
    apply_tick(burn)
    assert burn.is_expired

    result = apply_damage_modifier(100, [burn], is_attacker=False)
    assert result == 100  # No burn modifier since it's expired


def test_minimum_damage_is_1():
    """apply_damage_modifier should never return less than 1."""
    fear = StatusEffect(status_type=StatusType.FEAR, duration=3)
    shield = StatusEffect(status_type=StatusType.SHIELD, duration=3)
    # With very low base damage and stacking reductions
    result = apply_damage_modifier(1, [fear, shield], is_attacker=True)
    assert result >= 1


def test_multiple_active_effects_attacker():
    """FEAR with other non-relevant effects still applies fear reduction."""
    fear = StatusEffect(status_type=StatusType.FEAR, duration=3)
    freeze = StatusEffect(status_type=StatusType.FREEZE, duration=3)
    result = apply_damage_modifier(100, [fear, freeze], is_attacker=True)
    assert result == 80


def test_multiple_defender_effects_stacking():
    """Both BURN and SHIELD active on defender: 1.1 * 0.7 = 0.77 -> round to 77."""
    burn = StatusEffect(status_type=StatusType.BURN, duration=3)
    shield = StatusEffect(status_type=StatusType.SHIELD, duration=3)
    result = apply_damage_modifier(100, [burn, shield], is_attacker=False)
    assert result == round(100 * 1.1 * 0.7)
