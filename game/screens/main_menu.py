from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme


class MainMenuScreen(Screen):
    ITEMS = ["Start Run", "Settings", "Quit"]

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
            elif item == "Settings":
                return "settings"
            elif item == "Quit":
                return "quit"
        elif action == Action.BACK:
            return "quit"
        return None

    def draw(self):
        self.buffer.clear()
        self.buffer.write(15, 2, "M U T A B A R", self.theme.accent_color)
        self.buffer.write(10, 4, "Monster Battle Simulator", self.theme.dim_text_color)
        self.buffer.write(6, 5, "\u2500" * 38, self.theme.border_color)

        for i, item in enumerate(self.ITEMS):
            y = 8 + i * 3
            if i == self.selected:
                self.buffer.draw_box(8, y - 1, 34, 3, self.theme.accent_color)
                self.buffer.write(10, y, f"> {item}", self.theme.text_color)
            else:
                self.buffer.draw_box(8, y - 1, 34, 3, self.theme.border_color)
                self.buffer.write(10, y, f"  {item}", self.theme.dim_text_color)

        self.buffer.write(10, 22, "Arrow keys + Enter", self.theme.dim_text_color)
        self.buffer.write(10, 23, "ESC to close", self.theme.dim_text_color)
