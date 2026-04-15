from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.progression.lootbox import RollResult, Rarity, _get_creature_rarity
from game.creatures.ascii_art import get_art

_RARITY_COLORS = {
    Rarity.COMMON: (120, 120, 120),
    Rarity.UNCOMMON: (158, 206, 106),
    Rarity.RARE: (122, 162, 247),
    Rarity.EPIC: (187, 154, 247),
    Rarity.LEGENDARY: (224, 175, 104),
    Rarity.MUTAGEN: (0, 255, 130),
}

_RARITY_ANIMATION = {
    Rarity.COMMON: None,
    Rarity.UNCOMMON: "pulse",
    Rarity.RARE: "shimmer",
    Rarity.EPIC: "glow",
    Rarity.LEGENDARY: "legendary",
    Rarity.MUTAGEN: "mutagen",
}


class LootboxScreen(Screen):
    """CS:GO-style rolling lootbox animation."""

    STRIP_VISIBLE = 5
    CELL_WIDTH = 6

    def __init__(self, buffer: TextBuffer, theme: Theme, roll_result: RollResult,
                 mutabox_tier=None):
        super().__init__(buffer, theme)
        self.roll = roll_result
        self.mutabox_tier = mutabox_tier
        self.offset = 0.0
        self.speed = 12.0
        self.target_offset = float(roll_result.winner_index)
        self.phase = "rolling"  # "rolling", "flash", "reveal"
        self.decel_start = self.target_offset - 18.0
        self._reveal_timer = 0.0
        self.flash_frames = 0
        self.needs_animation = False
        self.wants_reroll = False

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if self.phase == "rolling" and action == Action.CONFIRM:
            self.offset = self.target_offset
            if self.roll.is_shiny:
                self.phase = "flash"
                self.flash_frames = 3
            else:
                self.phase = "reveal"
                self.needs_animation = True
        elif self.phase == "reveal":
            if action == Action.CONFIRM or action == Action.BACK:
                return "post_lootbox"
            if action == Action.CHAR and char.lower() == "r":
                self.wants_reroll = True
                return "post_lootbox"
        return None

    def update(self, dt: float):
        if self.phase == "rolling":
            if self.offset >= self.decel_start:
                remaining = max(0.01, self.target_offset - self.offset)
                total_decel = self.target_offset - self.decel_start
                progress = 1.0 - (remaining / max(total_decel, 0.01))
                # Cubic ease-out: slow crawl to build suspense
                self.speed = max(0.4, 12.0 * (1.0 - progress * progress * progress))
            self.offset += self.speed * dt
            if self.offset >= self.target_offset:
                self.offset = self.target_offset
                if self.roll.is_shiny:
                    self.phase = "flash"
                    self.flash_frames = 3
                else:
                    self.phase = "reveal"
                    self.needs_animation = True
        elif self.phase == "flash":
            self.flash_frames -= 1
            if self.flash_frames <= 0:
                self.phase = "reveal"
                self.needs_animation = True
        elif self.phase == "reveal":
            self._reveal_timer += dt

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols
        H = self.buffer.rows

        # Shiny flash: fill entire buffer white
        if self.phase == "flash":
            for y in range(H):
                self.buffer.write(0, y, " " * W, (255, 255, 255))
            return

        self.buffer.write((W - 13) // 2, 0, "L O O T B O X", t.accent_color)

        center_x = W // 2
        strip_w = self.STRIP_VISIBLE * self.CELL_WIDTH
        strip_x = center_x - strip_w // 2

        self.buffer.write(center_x, 2, "\u25bc", t.highlight_color)
        self.buffer.draw_box(strip_x - 1, 3, strip_w + 2, 3, t.accent_color)

        int_offset = int(self.offset)
        for i in range(self.STRIP_VISIBLE):
            idx = int_offset - self.STRIP_VISIBLE // 2 + i
            if 0 <= idx < len(self.roll.strip):
                creature = self.roll.strip[idx]
                name = creature.name[:4].upper()
                x = strip_x + i * self.CELL_WIDTH
                is_center = (i == self.STRIP_VISIBLE // 2)
                rarity = _get_creature_rarity(creature)
                rarity_color = _RARITY_COLORS.get(rarity, t.text_color)
                if is_center and self.phase == "reveal":
                    color = t.highlight_color
                else:
                    color = rarity_color
                self.buffer.write(x, 4, f" {name} ", color)

        if self.phase == "reveal":
            rarity = self.roll.rarity
            rc = _RARITY_COLORS.get(rarity, t.text_color)
            anim = _RARITY_ANIMATION.get(rarity)
            creature = self.roll.template

            box_x, box_y, box_w, box_h = 2, 7, W - 4, 11
            top = "\u250c" + "\u2500" * (box_w - 2) + "\u2510"
            bot = "\u2514" + "\u2500" * (box_w - 2) + "\u2518"
            self.buffer.write_animated(box_x, box_y, top, rc, anim)
            for row in range(1, box_h - 1):
                self.buffer.write_animated(box_x, box_y + row, "\u2502", rc, anim)
                self.buffer.write_animated(box_x + box_w - 1, box_y + row, "\u2502", rc, anim)
            self.buffer.write_animated(box_x, box_y + box_h - 1, bot, rc, anim)

            self.buffer.write_animated(4, 8, f"\u2605 {rarity.name} \u2605", rc, anim)

            # ASCII art (5 lines) — animated for special pulls
            art = get_art(creature.name)
            if self.roll.is_shiny:
                art_anim = "golden"
                art_color = (255, 200, 80)
            elif rarity == Rarity.LEGENDARY:
                art_anim = "legendary"
                art_color = rc
            elif rarity == Rarity.MUTAGEN:
                art_anim = "mutagen"
                art_color = rc
            elif rarity == Rarity.EPIC:
                art_anim = "glow"
                art_color = rc
            else:
                art_anim = anim
                art_color = rc
            for i, line in enumerate(art):
                ax = max(4, (W - len(line)) // 2)
                self.buffer.write_animated(ax, 9 + i, line, art_color, art_anim)

            if self.roll.is_shiny:
                self.buffer.write_animated(4, 14, f"\u2726 {creature.name}", (255, 200, 80), "golden")
            elif rarity in (Rarity.LEGENDARY, Rarity.MUTAGEN):
                self.buffer.write_animated(4, 14, creature.name, rc, anim)
            else:
                self.buffer.write(4, 14, creature.name, t.text_color)

            for j, trait in enumerate(creature.traits[:2]):
                self.buffer.write(4, 15 + j, f"\u2022 {trait.name}", t.dim_text_color)

            self.buffer.write(2, H - 3, "[Enter] Continue", t.dim_text_color)
            self.buffer.write(2, H - 2, "[R] Open Another", t.dim_text_color)
