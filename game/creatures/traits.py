from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Trait:
    name: str
    description: str
    keywords: List[str]


_BONUS_PER_MATCH = 0.1
_MAX_BONUS = 1.3


def compute_trait_bonus(command: str, traits: List[Trait]) -> float:
    """
    Match trait keywords against the player's command (word-level and substring).
    Returns a multiplier between 1.0 and 1.3.
    """
    if not command or not traits:
        return 1.0

    command_lower = command.lower()
    command_words = set(command_lower.split())

    matched = 0
    for trait in traits:
        for keyword in trait.keywords:
            kw = keyword.lower()
            # Word-level match OR substring match
            if kw in command_words or kw in command_lower:
                matched += 1
                break  # one match per trait is enough

    if matched == 0:
        return 1.0

    bonus = 1.0 + matched * _BONUS_PER_MATCH
    return min(bonus, _MAX_BONUS)
