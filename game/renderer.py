# game/renderer.py
from dataclasses import dataclass, field


@dataclass
class Cell:
    char: str = " "
    color: tuple[int, int, int] = (200, 200, 200)


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

    def write(self, x: int, y: int, text: str, color: tuple[int, int, int] = (200, 200, 200)):
        for i, ch in enumerate(text):
            cx = x + i
            if cx >= self.cols:
                break
            if 0 <= y < self.rows and 0 <= cx < self.cols:
                self._grid[y][cx].char = ch
                self._grid[y][cx].color = color

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
