from game.renderer import TextBuffer
from game.theme import Theme
from game.input_handler import Action


class Screen:
    """Base class for all game screens."""

    def __init__(self, buffer: TextBuffer, theme: Theme):
        self.buffer = buffer
        self.theme = theme

    def handle_input(self, action: Action, char: str = "") -> str | None:
        """Handle input. Return screen name to switch to, or None to stay."""
        return None

    def update(self, dt: float):
        """Update animations/state. dt is seconds since last frame."""
        pass

    def draw(self):
        """Draw the screen to the buffer."""
        pass
