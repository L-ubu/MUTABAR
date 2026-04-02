import random
from dataclasses import dataclass

from game.creatures.creature import Creature
from game.creatures.types import get_type_effectiveness


@dataclass
class DamageResult:
    damage: int
    is_critical: bool
    is_miss: bool
    effectiveness: str  # "super_effective" | "resisted" | "neutral"
    trait_bonus: float


def calculate_damage(
    attacker: Creature,
    defender: Creature,
    command: str,
    trait_bonus: float = 1.0,
) -> DamageResult:
    """
    Calculate damage dealt by attacker to defender.

    Formula:
        base       = (attacker.atk / max(defender.defense, 1)) * 10
        raw        = base * type_mult * trait_bonus * rng_factor * crit_mult
        final      = max(1, int(round(raw)))
    """
    type_mult = get_type_effectiveness(attacker.mutation_type, defender.mutation_type)

    if type_mult > 1.0:
        effectiveness = "super_effective"
    elif type_mult < 1.0:
        effectiveness = "resisted"
    else:
        effectiveness = "neutral"

    is_critical = random.random() < 0.05
    crit_mult = 1.5 if is_critical else 1.0

    rng_factor = random.uniform(0.85, 1.15)

    base = (attacker.atk / max(defender.defense, 1)) * 10
    raw = base * type_mult * trait_bonus * rng_factor * crit_mult
    final = max(1, int(round(raw)))

    return DamageResult(
        damage=final,
        is_critical=is_critical,
        is_miss=False,
        effectiveness=effectiveness,
        trait_bonus=trait_bonus,
    )
