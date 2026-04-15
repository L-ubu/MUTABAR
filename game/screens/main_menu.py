from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme


class MainMenuScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme,
                 idle_notification: int | None = None,
                 has_active_run: bool = False):
        super().__init__(buffer, theme)
        self.has_active_run = has_active_run
        self.items = [
            "Continue Run" if has_active_run else "Start Run",
            "Mutadex", "Settings", "Quit",
        ]
        self.selected = 0
        self.idle_notification = idle_notification

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.UP:
            self.selected = (self.selected - 1) % len(self.items)
        elif action == Action.DOWN:
            self.selected = (self.selected + 1) % len(self.items)
        elif action == Action.CONFIRM:
            item = self.items[self.selected]
            if item == "Continue Run":
                return "continue_run"
            elif item == "Start Run":
                return "run"
            elif item == "Mutadex":
                return "mutadex"
            elif item == "Settings":
                return "settings"
            elif item == "Quit":
                return "quit"
        elif action == Action.BACK:
            return "hide"
        return None

    def draw(self):
        self.buffer.clear()
        W = self.buffer.cols
        H = self.buffer.rows
        t = self.theme

        self.buffer.write((W - 13) // 2, 1, "M U T A B A R", t.accent_color)
        self.buffer.write((W - 24) // 2, 2, "Monster Battle Simulator", t.dim_text_color)
        self.buffer.write(1, 3, "\u2500" * (W - 2), t.border_color)

        self.buffer.draw_box(3, 5, W - 6, len(self.items) * 2 + 1, t.border_color)
        for i, item in enumerate(self.items):
            y = 6 + i * 2
            if i == self.selected:
                self.buffer.write(5, y, f"\u25b8 {item}", t.accent_color)
            else:
                self.buffer.write(5, y, f"  {item}", t.dim_text_color)

        self.buffer.write(3, 15, "\u2191\u2193 + Enter", t.dim_text_color)
        self.buffer.write(3, 16, "ESC to hide", t.dim_text_color)

        if self.idle_notification:
            self.buffer.write(3, 18, f"+{self.idle_notification} idle mutagen!", t.accent_color)
