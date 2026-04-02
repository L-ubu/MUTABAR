# tests/test_theme.py
from game.theme import Theme, get_theme, list_themes


def test_four_themes_exist():
    names = list_themes()
    assert set(names) == {"frosted_glass", "tokyo_night", "phosphor", "adaptive"}


def test_theme_has_required_colors():
    theme = get_theme("tokyo_night")
    assert theme.bg_color is not None
    assert theme.text_color is not None
    assert theme.accent_color is not None
    assert theme.border_color is not None
    assert theme.highlight_color is not None


def test_each_theme_has_type_colors():
    for name in list_themes():
        theme = get_theme(name)
        assert len(theme.type_colors) == 8


def test_phosphor_is_green():
    theme = get_theme("phosphor")
    assert theme.text_color[1] > theme.text_color[0]  # green > red
    assert theme.text_color[1] > theme.text_color[2]  # green > blue


def test_invalid_theme_raises():
    try:
        get_theme("nonexistent")
        assert False, "Should have raised"
    except KeyError:
        pass
