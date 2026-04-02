from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.progression.lootbox import RollResult, Rarity


class LootboxScreen(Screen):
    """CS:GO-style rolling lootbox animation."""

    STRIP_VISIBLE = 5
    CELL_WIDTH = 6

    def __init__(self, buffer: TextBuffer, theme: Theme, roll_result: RollResult):
        super().__init__(buffer, theme)
        self.roll = roll_result
        self.offset = 0.0
        self.speed = 25.0
        self.target_offset = float(roll_result.winner_index)
        self.phase = "rolling"  # "rolling", "reveal"
        self.decel_start = self.target_offset - 8.0
        self._reveal_timer = 0.0

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if self.phase == "rolling" and action == Action.CONFIRM:
            self.offset = self.target_offset
            self.phase = "reveal"
        elif self.phase == "reveal" and action == Action.CONFIRM:
            return "post_lootbox"
        return None

    def update(self, dt: float):
        if self.phase == "rolling":
            if self.offset >= self.decel_start:
                remaining = self.target_offset - self.offset
                self.speed = max(1.0, remaining * 3)
            self.offset += self.speed * dt
            if self.offset >= self.target_offset:
                self.offset = self.target_offset
                self.phase = "reveal"
        elif self.phase == "reveal":
            self._reveal_timer += dt

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols

        center_title = (W - 13) // 2
        self.buffer.write(center_title, 1, "L O O T B O X", t.accent_color)
        self.buffer.write(5, 3, "\u2500" * (W - 10), t.border_color)

        center_x = W // 2
        strip_w = self.STRIP_VISIBLE * self.CELL_WIDTH
        strip_x = center_x - strip_w // 2

        self.buffer.write(center_x, 5, "\u25bc", t.highlight_color)
        self.buffer.draw_box(strip_x - 1, 6, strip_w + 2, 3, t.accent_color)

        int_offset = int(self.offset)
        for i in range(self.STRIP_VISIBLE):
            idx = int_offset - self.STRIP_VISIBLE // 2 + i
            if 0 <= idx < len(self.roll.strip):
                creature = self.roll.strip[idx]
                name = creature.name[:4].upper()
                x = strip_x + i * self.CELL_WIDTH
                is_center = (i == self.STRIP_VISIBLE // 2)
                color = t.highlight_color if is_center and self.phase == "reveal" else t.text_color
                self.buffer.write(x, 7, f" {name} ", color)

        if self.phase == "reveal":
            rarity_colors = {
                Rarity.COMMON: t.text_color,
                Rarity.UNCOMMON: (158, 206, 106),
                Rarity.RARE: (122, 162, 247),
                Rarity.EPIC: (187, 154, 247),
                Rarity.LEGENDARY: (224, 175, 104),
            }
            rc = rarity_colors.get(self.roll.rarity, t.text_color)
            creature = self.roll.template

            self.buffer.draw_box(4, 11, W - 8, 10, rc)
            self.buffer.write(7, 12, f"\u2605 {self.roll.rarity.name} \u2605", rc)
            self.buffer.write(7, 14, creature.name, t.text_color)
            self.buffer.write(7, 16, "Traits:", t.dim_text_color)
            for j, trait in enumerate(creature.traits[:3]):
                self.buffer.write(9, 17 + j, f"\u2022 {trait.name}", t.text_color)

            center_cont = (W - 20) // 2
            self.buffer.write(center_cont, 23, "[Enter] to continue", t.dim_text_color)
