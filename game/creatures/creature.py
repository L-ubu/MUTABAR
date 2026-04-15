from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, List

from game.creatures.types import MutationType
from game.creatures.traits import Trait


class CreatureCategory(Enum):
    ANIMAL       = "animal"
    MYTHOLOGICAL = "mythological"
    FAMOUS       = "famous"
    ORIGINAL     = "original"
    HYBRID       = "hybrid"


@dataclass
class Creature:
    name: str
    category: CreatureCategory
    mutation_type: MutationType
    traits: List[Trait]
    base_hp: int
    base_atk: int
    base_def: int
    level: int = 1
    xp: int = 0
    is_shiny: bool = False

    _SHINY_BOOST: ClassVar[float] = 1.15

    # current_hp is not part of __init__ arguments; it is set in __post_init__
    current_hp: int = field(init=False)

    def __post_init__(self):
        if self.is_shiny:
            self.base_hp = round(self.base_hp * self._SHINY_BOOST)
            self.base_atk = round(self.base_atk * self._SHINY_BOOST)
            self.base_def = round(self.base_def * self._SHINY_BOOST)
        self.current_hp = self.max_hp

    # --- Scaled stats ---

    @property
    def max_hp(self) -> int:
        return self.base_hp + (self.level - 1) * 5

    @property
    def atk(self) -> int:
        return self.base_atk + (self.level - 1) * 2

    @property
    def defense(self) -> int:
        return self.base_def + (self.level - 1) * 2

    # --- Combat ---

    def take_damage(self, amount: int) -> None:
        self.current_hp = max(0, self.current_hp - amount)

    def heal(self, amount: int) -> None:
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def full_heal(self) -> None:
        self.current_hp = self.max_hp

    @property
    def is_fainted(self) -> bool:
        return self.current_hp <= 0
