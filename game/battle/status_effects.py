from dataclasses import dataclass, field
from enum import Enum
from typing import List


class StatusType(Enum):
    BURN   = "BURN"
    FREEZE = "FREEZE"
    POISON = "POISON"
    PHASE  = "PHASE"
    STUN   = "STUN"
    DRAIN  = "DRAIN"
    FEAR   = "FEAR"
    SHIELD = "SHIELD"


@dataclass
class StatusEffect:
    status_type: StatusType
    duration: int
    remaining_turns: int = field(init=False)
    turns_elapsed: int = field(init=False, default=0)

    def __post_init__(self):
        self.remaining_turns = self.duration

    @property
    def is_expired(self) -> bool:
        return self.remaining_turns <= 0


def apply_tick(effect: StatusEffect) -> int:
    """
    Advance the effect by one turn.

    Decrements remaining_turns and increments turns_elapsed.
    Returns the DoT damage for this tick:
      - BURN:   8 (flat)
      - POISON: 5 * turns_elapsed (scales each turn)
      - Others: 0
    """
    effect.remaining_turns -= 1
    effect.turns_elapsed += 1

    if effect.status_type == StatusType.BURN:
        return 8
    if effect.status_type == StatusType.POISON:
        return 5 * effect.turns_elapsed
    return 0


def apply_damage_modifier(
    base_damage: int,
    effects: List[StatusEffect],
    is_attacker: bool,
) -> int:
    """
    Apply active status-effect modifiers to a damage value.

    Attacker modifiers (reduce outgoing damage):
      - FEAR:   *= 0.8

    Defender modifiers (applied to incoming damage):
      - BURN:   *= 1.1  (burning target takes more damage)
      - SHIELD: *= 0.7  (shielded target takes less damage)

    Expired effects are ignored.
    Returns max(1, round(result)).
    """
    result = float(base_damage)

    for effect in effects:
        if effect.is_expired:
            continue

        if is_attacker:
            if effect.status_type == StatusType.FEAR:
                result *= 0.8
        else:
            if effect.status_type == StatusType.BURN:
                result *= 1.1
            elif effect.status_type == StatusType.SHIELD:
                result *= 0.7

    return max(1, round(result))
