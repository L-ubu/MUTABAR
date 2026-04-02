from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from game.progression.lootbox import Rarity, RollResult, roll_creature

@dataclass(frozen=True)
class _TierConfig:
    cost: int
    rarity_weights: dict[Rarity, float]
    shiny_chance: float

_STANDARD_WEIGHTS = {Rarity.COMMON: 50.0, Rarity.UNCOMMON: 30.0, Rarity.RARE: 15.0, Rarity.EPIC: 4.0, Rarity.LEGENDARY: 1.0}
_PREMIUM_WEIGHTS = {Rarity.COMMON: 25.0, Rarity.UNCOMMON: 30.0, Rarity.RARE: 25.0, Rarity.EPIC: 15.0, Rarity.LEGENDARY: 5.0}

class MutaboxTier(Enum):
    STANDARD = _TierConfig(cost=50, rarity_weights=_STANDARD_WEIGHTS, shiny_chance=0.01)
    PREMIUM = _TierConfig(cost=150, rarity_weights=_PREMIUM_WEIGHTS, shiny_chance=0.01)
    SHINY = _TierConfig(cost=300, rarity_weights=_STANDARD_WEIGHTS, shiny_chance=0.05)

    @property
    def cost(self) -> int: return self.value.cost
    @property
    def rarity_weights(self) -> dict[Rarity, float]: return self.value.rarity_weights
    @property
    def shiny_chance(self) -> float: return self.value.shiny_chance

def open_mutabox(tier: MutaboxTier) -> RollResult:
    return roll_creature(wave=1, unlocked_tiers=set(), rarity_weights=tier.rarity_weights, shiny_chance=tier.shiny_chance)
