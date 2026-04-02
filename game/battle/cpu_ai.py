import random
from enum import Enum

from game.creatures.creature import Creature


class CpuDifficulty(Enum):
    BASIC    = "BASIC"
    TACTICAL = "TACTICAL"
    ADAPTIVE = "ADAPTIVE"


_GENERIC_COMMANDS = [
    "strike with full force",
    "launch a devastating attack",
    "unleash a powerful blow",
    "charge with full strength",
    "deliver a crushing strike",
    "attack fiercely",
    "slam with brute force",
]


def generate_cpu_command(creature: Creature, difficulty: CpuDifficulty) -> str:
    """
    Generate a CPU battle command based on difficulty.

    BASIC:    random generic command
    TACTICAL: random command built from trait keywords
    ADAPTIVE: picks the trait with the most keywords, combines 2 of them
    """
    if difficulty == CpuDifficulty.BASIC:
        return random.choice(_GENERIC_COMMANDS)

    if difficulty == CpuDifficulty.TACTICAL:
        if not creature.traits:
            return random.choice(_GENERIC_COMMANDS)
        trait = random.choice(creature.traits)
        if not trait.keywords:
            return random.choice(_GENERIC_COMMANDS)
        keyword = random.choice(trait.keywords)
        return f"attack with {keyword} power"

    # ADAPTIVE: pick the trait with the most keywords
    if not creature.traits:
        return random.choice(_GENERIC_COMMANDS)

    best_trait = max(creature.traits, key=lambda t: len(t.keywords))
    keywords = best_trait.keywords

    if len(keywords) >= 2:
        chosen = random.sample(keywords, 2)
        return f"{chosen[0]} {chosen[1]} strike"
    elif len(keywords) == 1:
        return f"{keywords[0]} strike"
    else:
        return random.choice(_GENERIC_COMMANDS)
