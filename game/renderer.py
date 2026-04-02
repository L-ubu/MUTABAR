# game/renderer.py
import math
import colorsys
from dataclasses import dataclass, field


@dataclass
class Cell:
    char: str = " "
    color: tuple[int, int, int] = (200, 200, 200)
    animation: str | None = None  # "pulse", "shimmer", "glow", "rainbow"


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def _apply_animation(color: tuple[int, int, int], animation: str | None,
                     t: float, x: int, y: int) -> tuple[int, int, int]:
    if animation is None:
        return color
    if animation == "pulse":
        factor = 0.7 + 0.3 * math.sin(t * 3)
        return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))
    elif animation == "shimmer":
        wave = 0.6 + 0.4 * math.sin(t * 4 - x * 0.5)
        return (int(color[0] * wave), int(color[1] * wave), int(color[2] * wave))
    elif animation == "glow":
        shift = int(30 * math.sin(t * 2))
        return (min(255, max(0, color[0] + shift)),
                min(255, max(0, color[1] + shift)),
                min(255, max(0, color[2] + shift)))
    elif animation == "rainbow":
        hue = (t * 0.5 + x * 0.05 + y * 0.02) % 1.0
        return _hsv_to_rgb(hue, 0.8, 1.0)
    return color


class TextBuffer:
    """A character grid buffer for ASCII rendering."""

    def __init__(self, cols: int = 50, rows: int = 35):
        self.cols = cols
        self.rows = rows
        self._grid: list[list[Cell]] = [
            [Cell() for _ in range(cols)] for _ in range(rows)
        ]

    def clear(self, color: tuple[int, int, int] = (200, 200, 200)):
        for row in self._grid:
            for cell in row:
                cell.char = " "
                cell.color = color
                cell.animation = None

    def write(self, x: int, y: int, text: str, color: tuple[int, int, int] = (200, 200, 200)):
        for i, ch in enumerate(text):
            cx = x + i
            if cx >= self.cols:
                break
            if 0 <= y < self.rows and 0 <= cx < self.cols:
                self._grid[y][cx].char = ch
                self._grid[y][cx].color = color

    def write_animated(self, x: int, y: int, text: str, color: tuple[int, int, int],
                       animation: str | None = None):
        for i, ch in enumerate(text):
            cx = x + i
            if cx >= self.cols:
                break
            if 0 <= y < self.rows and 0 <= cx < self.cols:
                self._grid[y][cx].char = ch
                self._grid[y][cx].color = color
                self._grid[y][cx].animation = animation

    def get_char(self, x: int, y: int) -> str:
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self._grid[y][x].char
        return " "

    def get_color(self, x: int, y: int) -> tuple[int, int, int]:
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self._grid[y][x].color
        return (200, 200, 200)

    def get_line_text(self, y: int) -> str:
        if 0 <= y < self.rows:
            return "".join(cell.char for cell in self._grid[y])
        return ""

    def draw_box(self, x: int, y: int, width: int, height: int,
                 color: tuple[int, int, int] = (200, 200, 200)):
        self.write(x, y, "\u250c" + "\u2500" * (width - 2) + "\u2510", color)
        for row in range(1, height - 1):
            self.write(x, y + row, "\u2502" + " " * (width - 2) + "\u2502", color)
        self.write(x, y + height - 1, "\u2514" + "\u2500" * (width - 2) + "\u2518", color)

    def draw_hp_bar(self, x: int, y: int, width: int, current: int, maximum: int,
                    fill_color: tuple[int, int, int] = (158, 206, 106),
                    empty_color: tuple[int, int, int] = (86, 95, 137)):
        ratio = max(0, min(1, current / max(maximum, 1)))
        filled = int(ratio * width)
        empty = width - filled
        for i in range(filled):
            self.write(x + i, y, "\u2588", fill_color)
        for i in range(empty):
            self.write(x + filled + i, y, "\u2591", empty_color)

    def render_to_surface(self, surface, font, bg_color: tuple[int, int, int]):
        """Render the text buffer to a pygame surface."""
        import pygame
        surface.fill(bg_color)
        char_w = font.size("M")[0]
        char_h = font.get_linesize()
        for y, row in enumerate(self._grid):
            for x, cell in enumerate(row):
                if cell.char != " ":
                    rendered = font.render(cell.char, True, cell.color)
                    surface.blit(rendered, (x * char_w, y * char_h))

    def render_to_surface_animated(self, surface, font, bg_color: tuple[int, int, int], t: float):
        """Render with animation transforms applied based on time."""
        import pygame
        surface.fill(bg_color)
        char_w = font.size("M")[0]
        char_h = font.get_linesize()
        for y, row in enumerate(self._grid):
            for x, cell in enumerate(row):
                if cell.char != " ":
                    color = _apply_animation(cell.color, cell.animation, t, x, y)
                    rendered = font.render(cell.char, True, color)
                    surface.blit(rendered, (x * char_w, y * char_h))
