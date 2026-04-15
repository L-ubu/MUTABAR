from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme


class RunOverScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme,
                 waves_survived: int, mutagen_earned: int, run_id: int, db):
        super().__init__(buffer, theme)
        self.waves_survived = waves_survived
        self.mutagen_earned = mutagen_earned
        db.add_mutagen(mutagen_earned)
        db.end_run(run_id, waves_survived, mutagen_earned)

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.CONFIRM:
            return "main_menu"
        return None

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols
        H = self.buffer.rows
        title = "Run Over!"
        self.buffer.write((W - len(title)) // 2, 4, title, t.accent_color)
        self.buffer.write(1, 6, "\u2500" * (W - 2), t.border_color)
        waves = f"Survived {self.waves_survived} waves"
        self.buffer.write((W - len(waves)) // 2, 8, waves, t.text_color)
        earned = f"+{self.mutagen_earned} mutagen banked"
        self.buffer.write((W - len(earned)) // 2, 10, earned, t.highlight_color)
        self.buffer.write(1, 12, "\u2500" * (W - 2), t.border_color)
        hint = "[Enter] Main Menu"
        self.buffer.write((W - len(hint)) // 2, 14, hint, t.dim_text_color)
