from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme, list_themes, get_theme


class SettingsScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, current_theme_name: str):
        super().__init__(buffer, theme)
        self.themes = list_themes()
        self.selected = self.themes.index(current_theme_name) if current_theme_name in self.themes else 0
        self.changed_theme: str | None = None

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.UP:
            self.selected = (self.selected - 1) % len(self.themes)
        elif action == Action.DOWN:
            self.selected = (self.selected + 1) % len(self.themes)
        elif action == Action.CONFIRM:
            self.changed_theme = self.themes[self.selected]
            return "apply_theme"
        elif action == Action.BACK:
            return "main_menu"
        return None

    def draw(self):
        self.buffer.clear()
        t = self.theme

        self.buffer.write(15, 2, "S E T T I N G S", t.accent_color)
        self.buffer.write(10, 4, "\u2500" * 30, t.border_color)
        self.buffer.write(10, 6, "Theme:", t.text_color)

        for i, name in enumerate(self.themes):
            y = 8 + i * 2
            theme_obj = get_theme(name)
            prefix = ">" if i == self.selected else " "
            color = t.accent_color if i == self.selected else t.dim_text_color
            self.buffer.write(10, y, f"{prefix} {theme_obj.display_name}", color)

        self.buffer.write(10, 20, "Enter: select theme", t.dim_text_color)
        self.buffer.write(10, 21, "ESC: back", t.dim_text_color)
