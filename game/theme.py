# game/theme.py
from dataclasses import dataclass
from game.creatures.types import MutationType


@dataclass(frozen=True)
class Theme:
    name: str
    display_name: str
    bg_color: tuple[int, int, int]
    text_color: tuple[int, int, int]
    dim_text_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    border_color: tuple[int, int, int]
    highlight_color: tuple[int, int, int]
    type_colors: dict[MutationType, tuple[int, int, int]]


_STANDARD_TYPE_COLORS = {
    MutationType.FIRE: (247, 118, 142),
    MutationType.WATER: (115, 218, 202),
    MutationType.AIR: (122, 162, 247),
    MutationType.EARTH: (158, 206, 106),
    MutationType.MUTA: (224, 175, 104),
    MutationType.TECH: (169, 177, 214),
    MutationType.COSM: (187, 154, 247),
    MutationType.SHAD: (130, 100, 180),
}

_PHOSPHOR_TYPE_COLORS = {
    MutationType.FIRE: (255, 107, 53),
    MutationType.WATER: (0, 200, 255),
    MutationType.AIR: (150, 220, 255),
    MutationType.EARTH: (100, 255, 100),
    MutationType.MUTA: (255, 255, 0),
    MutationType.TECH: (200, 200, 200),
    MutationType.COSM: (168, 85, 247),
    MutationType.SHAD: (150, 80, 200),
}

_THEMES: dict[str, Theme] = {
    "frosted_glass": Theme(
        name="frosted_glass", display_name="Frosted Glass",
        bg_color=(30, 30, 30), text_color=(224, 224, 224),
        dim_text_color=(120, 120, 120), accent_color=(126, 231, 135),
        border_color=(60, 60, 60), highlight_color=(126, 231, 135),
        type_colors=_STANDARD_TYPE_COLORS,
    ),
    "tokyo_night": Theme(
        name="tokyo_night", display_name="Tokyo Night",
        bg_color=(26, 27, 38), text_color=(169, 177, 214),
        dim_text_color=(86, 95, 137), accent_color=(187, 154, 247),
        border_color=(41, 46, 66), highlight_color=(224, 175, 104),
        type_colors=_STANDARD_TYPE_COLORS,
    ),
    "phosphor": Theme(
        name="phosphor", display_name="Phosphor",
        bg_color=(10, 15, 10), text_color=(0, 255, 65),
        dim_text_color=(0, 130, 30), accent_color=(0, 255, 65),
        border_color=(0, 80, 20), highlight_color=(0, 255, 65),
        type_colors=_PHOSPHOR_TYPE_COLORS,
    ),
    "adaptive": Theme(
        name="adaptive", display_name="Adaptive macOS",
        bg_color=(28, 28, 30), text_color=(229, 229, 231),
        dim_text_color=(142, 142, 147), accent_color=(10, 132, 255),
        border_color=(58, 58, 60), highlight_color=(48, 209, 88),
        type_colors=_STANDARD_TYPE_COLORS,
    ),
}


def get_theme(name: str) -> Theme:
    if name not in _THEMES:
        raise KeyError(f"Unknown theme: {name}")
    return _THEMES[name]


def list_themes() -> list[str]:
    return list(_THEMES.keys())
