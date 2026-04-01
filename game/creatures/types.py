from enum import Enum
from typing import Tuple


class MutationType(Enum):
    FIRE  = ("FIRE",  (247, 118, 142), "Passionate and intense")
    WATER = ("WATER", (115, 218, 202), "Fluid, patient, like the tide")
    AIR   = ("AIR",   (122, 162, 247), "Light and playful")
    EARTH = ("EARTH", (158, 206, 106), "Steadfast and immovable")
    MUTA  = ("MUTA",  (224, 175, 104), "Broken, unhinged, and grotesque")
    TECH  = ("TECH",  (169, 177, 214), "Calculated and precise, like a machine")
    COSM  = ("COSM",  (187, 154, 247), "Detached and ethereal, cosmic and mystical")
    SHAD  = ("SHAD",  (130, 100, 180), "Hollow and deathly, nightmarish")

    def __init__(self, key: str, color: Tuple[int, int, int], personality: str):
        self.key = key
        self.color = color
        self.personality = personality


# Cycle 1: FIRE > AIR > EARTH > WATER > (back to FIRE)
_CYCLE_1 = [MutationType.FIRE, MutationType.AIR, MutationType.EARTH, MutationType.WATER]

# Cycle 2: TECH > MUTA > COSM > SHAD > (back to TECH)
_CYCLE_2 = [MutationType.TECH, MutationType.MUTA, MutationType.COSM, MutationType.SHAD]


def get_type_effectiveness(attacker: MutationType, defender: MutationType) -> float:
    """
    Return the type effectiveness multiplier for an attacker hitting a defender.
    - 1.5  super effective (attacker is next in cycle after defender's predecessor)
    - 0.75 resisted       (reverse of super effective)
    - 1.0  neutral        (same-cycle unrelated, cross-group, or same type)
    """
    for cycle in (_CYCLE_1, _CYCLE_2):
        if attacker in cycle and defender in cycle:
            n = len(cycle)
            att_idx = cycle.index(attacker)
            def_idx = cycle.index(defender)
            # attacker beats the type that comes AFTER it in the cycle
            # i.e., FIRE (0) beats AIR (1): att_idx + 1 == def_idx
            if (att_idx + 1) % n == def_idx:
                return 1.5
            if (def_idx + 1) % n == att_idx:
                return 0.75
            return 1.0
    # Cross-group or same type
    return 1.0
