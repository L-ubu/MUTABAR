from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme


class MainMenuScreen(Screen):
    ITEMS = ["Start Run", "Mutadex", "Settings", "Quit"]

    def __init__(self, buffer: TextBuffer, theme: Theme):
        super().__init__(buffer, theme)
        self.selected = 0

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.UP:
            self.selected = (self.selected - 1) % len(self.ITEMS)
        elif action == Action.DOWN:
            self.selected = (self.selected + 1) % len(self.ITEMS)
        elif action == Action.CONFIRM:
            item = self.ITEMS[self.selected]
            if item == "Start Run":
                return "run"
            elif item == "Mutadex":
                return "mutadex"
            elif item == "Settings":
                return "settings"
            elif item == "Quit":
                return "quit"
        elif action == Action.BACK:
            return "quit"
        return None

    def draw(self):
        self.buffer.clear()
        W = self.buffer.cols
        t = self.theme

        center = (W - 13) // 2
        self.buffer.write(center, 2, "M U T A B A R", t.accent_color)
        sub = "Monster Battle Simulator"
        self.buffer.write((W - len(sub)) // 2, 4, sub, t.dim_text_color)
        self.buffer.write(3, 5, "\u2500" * (W - 6), t.border_color)

        for i, item in enumerate(self.ITEMS):
            y = 8 + i * 3
            if i == self.selected:
                self.buffer.draw_box(5, y - 1, W - 10, 3, t.accent_color)
                self.buffer.write(7, y, f"\u25b8 {item}", t.text_color)
            else:
                self.buffer.draw_box(5, y - 1, W - 10, 3, t.border_color)
                self.buffer.write(7, y, f"  {item}", t.dim_text_color)

        self.buffer.write(7, 20, "Arrow keys + Enter", t.dim_text_color)
        self.buffer.write(7, 21, "ESC to close", t.dim_text_color)
