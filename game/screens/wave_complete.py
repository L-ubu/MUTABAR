from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme


class WaveCompleteScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, wave: int,
                 mutagen_this_wave: int, mutagen_run_total: int):
        super().__init__(buffer, theme)
        self.wave = wave
        self.mutagen_this_wave = mutagen_this_wave
        self.mutagen_run_total = mutagen_run_total

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.CONFIRM:
            return "next_wave"
        return None

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols
        title = f"Wave {self.wave} Cleared!"
        self.buffer.write((W - len(title)) // 2, 8, title, t.accent_color)
        earned = f"+{self.mutagen_this_wave} mutagen"
        self.buffer.write((W - len(earned)) // 2, 11, earned, t.text_color)
        total = f"Run total: {self.mutagen_run_total} mutagen"
        self.buffer.write((W - len(total)) // 2, 13, total, t.dim_text_color)
        hint = "[Enter] Next Wave"
        self.buffer.write((W - len(hint)) // 2, 18, hint, t.dim_text_color)
