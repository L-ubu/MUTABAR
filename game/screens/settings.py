from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme, list_themes, get_theme


class SettingsScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, current_theme_name: str,
                 sound_enabled: bool = True):
        super().__init__(buffer, theme)
        self.themes = list_themes()
        self.theme_idx = self.themes.index(current_theme_name) if current_theme_name in self.themes else 0
        self.changed_theme: str | None = None
        self.sound_enabled = sound_enabled
        self.sound_toggled = False
        self.row = 0  # 0 = theme, 1 = sound

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.BACK:
            return "main_menu"
        if action == Action.UP:
            self.row = max(0, self.row - 1)
        elif action == Action.DOWN:
            self.row = min(1, self.row + 1)
        elif action == Action.LEFT:
            if self.row == 0:
                self.theme_idx = (self.theme_idx - 1) % len(self.themes)
            elif self.row == 1:
                self.sound_enabled = not self.sound_enabled
                self.sound_toggled = True
        elif action == Action.RIGHT:
            if self.row == 0:
                self.theme_idx = (self.theme_idx + 1) % len(self.themes)
            elif self.row == 1:
                self.sound_enabled = not self.sound_enabled
                self.sound_toggled = True
        elif action == Action.CONFIRM:
            if self.row == 0:
                self.changed_theme = self.themes[self.theme_idx]
                return "apply_theme"
            elif self.row == 1:
                self.sound_enabled = not self.sound_enabled
                self.sound_toggled = True
        return None

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols

        center = (W - 15) // 2
        self.buffer.write(center, 2, "S E T T I N G S", t.accent_color)
        self.buffer.write(5, 4, "\u2500" * (W - 10), t.border_color)

        # Theme row
        theme_color = t.accent_color if self.row == 0 else t.dim_text_color
        prefix = "\u25b8" if self.row == 0 else " "
        theme_obj = get_theme(self.themes[self.theme_idx])
        self.buffer.write(5, 6, f"{prefix} Theme:", theme_color)
        self.buffer.write(5, 8, f"  \u25c0 {theme_obj.display_name} \u25b6", t.text_color if self.row == 0 else t.dim_text_color)

        # Sound row
        sound_color = t.accent_color if self.row == 1 else t.dim_text_color
        prefix_s = "\u25b8" if self.row == 1 else " "
        sound_label = "ON" if self.sound_enabled else "OFF"
        self.buffer.write(5, 11, f"{prefix_s} Sound:", sound_color)
        self.buffer.write(5, 13, f"  \u25c0 {sound_label} \u25b6", t.text_color if self.row == 1 else t.dim_text_color)

        self.buffer.write(5, 16, "\u2500" * (W - 10), t.border_color)
        self.buffer.write(5, 18, "\u2190/\u2192: change  Enter: apply", t.dim_text_color)
        self.buffer.write(5, 19, "ESC: back", t.dim_text_color)
