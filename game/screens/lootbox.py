from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.progression.lootbox import RollResult, Rarity


class LootboxScreen(Screen):
    """CS:GO-style rolling lootbox animation."""

    STRIP_VISIBLE = 7
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

        self.buffer.write(15, 2, "L O O T B O X", t.accent_color)
        self.buffer.write(10, 4, "\u2500" * 30, t.border_color)

        center_x = 25
        marker_y = 7
        strip_y = 9

        self.buffer.write(center_x, marker_y, "\u25bc", t.highlight_color)

        self.buffer.draw_box(center_x - self.STRIP_VISIBLE * self.CELL_WIDTH // 2 - 1, strip_y - 1,
                            self.STRIP_VISIBLE * self.CELL_WIDTH + 2, 3, t.accent_color)

        int_offset = int(self.offset)
        for i in range(self.STRIP_VISIBLE):
            idx = int_offset - self.STRIP_VISIBLE // 2 + i
            if 0 <= idx < len(self.roll.strip):
                creature = self.roll.strip[idx]
                name = creature.name[:4].upper()
                x = center_x - self.STRIP_VISIBLE * self.CELL_WIDTH // 2 + i * self.CELL_WIDTH
                is_center = (i == self.STRIP_VISIBLE // 2)
                color = t.highlight_color if is_center and self.phase == "reveal" else t.text_color
                self.buffer.write(x, strip_y, f" {name} ", color)

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

            self.buffer.draw_box(8, 14, 34, 12, rc)
            self.buffer.write(12, 15, f"\u2605 {self.roll.rarity.name} \u2605", rc)
            self.buffer.write(12, 17, creature.name, t.text_color)
            self.buffer.write(12, 19, "Traits:", t.dim_text_color)
            for j, trait in enumerate(creature.traits[:4]):
                self.buffer.write(14, 20 + j, f"\u2022 {trait.name}", t.text_color)

            self.buffer.write(10, 28, "[Enter] to continue", t.dim_text_color)
