from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.creatures.database import CREATURE_ROSTER
from game.creatures.ascii_art import get_art
from game.progression.mutabox import MutaboxTier
from game.progression.lootbox import _get_creature_rarity, Rarity


_RARITY_COLORS = {
    Rarity.COMMON: (169, 177, 214),
    Rarity.UNCOMMON: (158, 206, 106),
    Rarity.RARE: (122, 162, 247),
    Rarity.EPIC: (187, 154, 247),
    Rarity.LEGENDARY: (224, 175, 104),
    Rarity.MUTAGEN: (0, 255, 130),
}

_SHOP_ITEMS = [
    ("Standard Mutabox", "Standard odds", MutaboxTier.STANDARD),
    ("Premium Mutabox", "Better rarity!", MutaboxTier.PREMIUM),
    ("Shiny Mutabox", "5x shiny chance!", MutaboxTier.SHINY),
]

_COLLECTION_VISIBLE = 12


class MutadexScreen(Screen):
    TABS = ["Collection", "Shop", "Idle", "Stats"]

    def __init__(self, buffer: TextBuffer, theme: Theme, db):
        super().__init__(buffer, theme)
        self.db = db
        self.active_tab = 0
        self.scroll = 0
        self.cursor = 0
        self.detail_creature = None
        self.roster = sorted(CREATURE_ROSTER, key=lambda t: t.name)
        self.shop_cursor = 0
        self.pending_mutabox_tier = None
        self.idle_cursor = 0
        self.idle_picking = False
        self.idle_pick_cursor = 0
        self.idle_pick_scroll = 0

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.BACK:
            if self.detail_creature:
                self.detail_creature = None
                return None
            if self.idle_picking:
                self.idle_picking = False
                return None
            return "main_menu"
        if action == Action.LEFT and not self.detail_creature and not self.idle_picking:
            self.active_tab = (self.active_tab - 1) % 4
            self._reset_tab_state()
        elif action == Action.RIGHT and not self.detail_creature and not self.idle_picking:
            self.active_tab = (self.active_tab + 1) % 4
            self._reset_tab_state()
        else:
            handlers = [
                self._handle_collection,
                self._handle_shop,
                self._handle_idle,
                self._handle_stats,
            ]
            return handlers[self.active_tab](action)
        return None

    def _reset_tab_state(self):
        self.scroll = 0
        self.cursor = 0
        self.detail_creature = None
        self.shop_cursor = 0
        self.idle_cursor = 0
        self.idle_picking = False

    # ------------------------------------------------------------------
    # Tab 0: Collection — input
    # ------------------------------------------------------------------

    def _handle_collection(self, action: Action) -> str | None:
        if self.detail_creature:
            if action in (Action.CONFIRM, Action.UP, Action.DOWN):
                self.detail_creature = None
            return None

        n = len(self.roster)
        if action == Action.UP:
            self.cursor = max(0, self.cursor - 1)
            if self.cursor < self.scroll:
                self.scroll = self.cursor
        elif action == Action.DOWN:
            self.cursor = min(n - 1, self.cursor + 1)
            if self.cursor >= self.scroll + _COLLECTION_VISIBLE:
                self.scroll = self.cursor - _COLLECTION_VISIBLE + 1
        elif action == Action.CONFIRM:
            template = self.roster[self.cursor]
            discovered = self.db.get_discovered_species()
            if template.name in discovered:
                collection = self.db.get_collection()
                owned = [m for m in collection if m.get("species") == template.name]
                shiny_count = sum(1 for m in owned if m.get("is_shiny"))
                rarity = _get_creature_rarity(template)
                self.detail_creature = {
                    "template": template,
                    "rarity": rarity,
                    "count": len(owned),
                    "shiny_count": shiny_count,
                }
        return None

    # ------------------------------------------------------------------
    # Tab 1: Shop — input
    # ------------------------------------------------------------------

    def _handle_shop(self, action: Action) -> str | None:
        if action == Action.UP:
            self.shop_cursor = max(0, self.shop_cursor - 1)
        elif action == Action.DOWN:
            self.shop_cursor = min(len(_SHOP_ITEMS) - 1, self.shop_cursor + 1)
        elif action == Action.CONFIRM:
            _, _, tier = _SHOP_ITEMS[self.shop_cursor]
            cost = tier.cost
            if self.db.get_mutagen() >= cost:
                self.db.spend_mutagen(cost)
                self.pending_mutabox_tier = tier
                return "open_mutabox"
        return None

    # ------------------------------------------------------------------
    # Tab 2: Idle Arena — input
    # ------------------------------------------------------------------

    def _handle_idle(self, action: Action) -> str | None:
        idle_team = self.db.get_idle_team()
        slots_filled = {entry["slot"]: entry for entry in idle_team}

        if self.idle_picking:
            idle_ids = self.db.get_idle_monster_ids()
            all_monsters = self.db.get_collection()
            eligible = [m for m in all_monsters if m["id"] not in idle_ids]

            n = len(eligible)
            visible = 10
            if action == Action.UP:
                self.idle_pick_cursor = max(0, self.idle_pick_cursor - 1)
                if self.idle_pick_cursor < self.idle_pick_scroll:
                    self.idle_pick_scroll = self.idle_pick_cursor
            elif action == Action.DOWN:
                self.idle_pick_cursor = min(max(n - 1, 0), self.idle_pick_cursor + 1)
                if self.idle_pick_cursor >= self.idle_pick_scroll + visible:
                    self.idle_pick_scroll = self.idle_pick_cursor - visible + 1
            elif action == Action.CONFIRM and eligible:
                chosen = eligible[self.idle_pick_cursor]
                slot = self.idle_cursor + 1
                self.db.set_idle_slot(slot, chosen["id"])
                self.idle_picking = False
                self.idle_pick_cursor = 0
                self.idle_pick_scroll = 0
            return None

        if action == Action.UP:
            self.idle_cursor = max(0, self.idle_cursor - 1)
        elif action == Action.DOWN:
            self.idle_cursor = min(2, self.idle_cursor + 1)
        elif action == Action.CONFIRM:
            slot = self.idle_cursor + 1
            if slot in slots_filled:
                self.db.clear_idle_slot(slot)
            else:
                self.idle_picking = True
                self.idle_pick_cursor = 0
                self.idle_pick_scroll = 0
        return None

    # ------------------------------------------------------------------
    # Tab 3: Stats — input
    # ------------------------------------------------------------------

    def _handle_stats(self, action: Action) -> str | None:
        return None

    def update(self, dt: float):
        pass

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols
        H = self.buffer.rows

        # Tab bar
        x = 1
        for i, tab in enumerate(self.TABS):
            color = t.accent_color if i == self.active_tab else t.dim_text_color
            label = f"[{tab}]" if i == self.active_tab else f" {tab} "
            self.buffer.write(x, 0, label, color)
            x += len(label) + 1
        self.buffer.write(1, 1, "\u2500" * (W - 2), t.border_color)

        drawers = [
            self._draw_collection,
            self._draw_shop,
            self._draw_idle,
            self._draw_stats,
        ]
        drawers[self.active_tab]()

    # ------------------------------------------------------------------
    # Tab 0: Collection — draw
    # ------------------------------------------------------------------

    def _draw_collection(self):
        t = self.theme
        W = self.buffer.cols
        discovered = self.db.get_discovered_species()
        collection = self.db.get_collection()
        species_counts = {}
        for m in collection:
            sp = m.get("species", "")
            species_counts[sp] = species_counts.get(sp, 0) + 1

        if self.detail_creature:
            self._draw_collection_detail(self.detail_creature)
            return

        self.buffer.write(1, 2, f"{len(discovered)}/{len(self.roster)}", t.accent_color)
        self.buffer.write(1, 3, "\u2500" * (W - 2), t.border_color)

        for row_idx in range(_COLLECTION_VISIBLE):
            roster_idx = self.scroll + row_idx
            if roster_idx >= len(self.roster):
                break
            template = self.roster[roster_idx]
            y = 4 + row_idx
            is_cursor = (roster_idx == self.cursor)
            cursor_ch = "\u25b8 " if is_cursor else "  "

            if template.name in discovered:
                rarity = _get_creature_rarity(template)
                rarity_color = _RARITY_COLORS.get(rarity, t.text_color)
                name_col = rarity_color if is_cursor else t.text_color
                self.buffer.write(1, y, cursor_ch, t.accent_color if is_cursor else t.dim_text_color)
                self.buffer.write(3, y, f"{template.name:<13}", name_col)
                self.buffer.write(17, y, rarity.name[:6], rarity_color)
                count = species_counts.get(template.name, 0)
                if count > 1:
                    self.buffer.write(W - 4, y, f"x{count}", t.dim_text_color)
            else:
                dim = t.dim_text_color
                self.buffer.write(1, y, cursor_ch, dim)
                self.buffer.write(3, y, "???", dim)

        if self.scroll > 0:
            self.buffer.write(W - 2, 4, "\u2191", t.dim_text_color)
        if self.scroll + _COLLECTION_VISIBLE < len(self.roster):
            self.buffer.write(W - 2, 4 + _COLLECTION_VISIBLE - 1, "\u2193", t.dim_text_color)

        self.buffer.write(1, 17, "\u2500" * (W - 2), t.border_color)
        self.buffer.write(1, 18, "[Enter] Details [\u2190\u2192] Tabs", t.dim_text_color)

    def _draw_collection_detail(self, detail: dict):
        t = self.theme
        W = self.buffer.cols
        template = detail["template"]
        rarity = detail["rarity"]
        rarity_color = _RARITY_COLORS.get(rarity, t.text_color)
        is_shiny = detail["shiny_count"] > 0

        # Pick animation based on rarity / shiny
        anim = None
        if is_shiny:
            anim = "golden"
        elif rarity == Rarity.LEGENDARY:
            anim = "legendary"
        elif rarity == Rarity.MUTAGEN:
            anim = "mutagen"
        elif rarity == Rarity.EPIC:
            anim = "glow"

        # Animated box border for special rarities
        if anim:
            # Draw box manually with animation
            top = "\u250c" + "\u2500" * (W - 4) + "\u2510"
            bot = "\u2514" + "\u2500" * (W - 4) + "\u2518"
            self.buffer.write_animated(1, 2, top, rarity_color, anim)
            for row in range(1, 15):
                self.buffer.write_animated(1, 2 + row, "\u2502", rarity_color, anim)
                self.buffer.write_animated(W - 2, 2 + row, "\u2502", rarity_color, anim)
            self.buffer.write_animated(1, 17, bot, rarity_color, anim)
        else:
            self.buffer.draw_box(1, 2, W - 2, 16, rarity_color)

        # Name with animation for special creatures
        if anim:
            self.buffer.write_animated(3, 3, template.name, rarity_color, anim)
        else:
            self.buffer.write(3, 3, template.name, rarity_color)
        self.buffer.write(3, 4, f"{rarity.name.capitalize()} \u2022 {template.category.value.capitalize()}", t.dim_text_color)
        self.buffer.write(2, 5, "\u2500" * (W - 4), t.border_color)
        # ASCII art (5 lines, centered) — animated for special creatures
        art = get_art(template.name)
        art_color = (255, 200, 80) if is_shiny else rarity_color
        for i, line in enumerate(art):
            ax = max(3, (W - len(line)) // 2)
            if anim:
                self.buffer.write_animated(ax, 6 + i, line, art_color, anim)
            else:
                self.buffer.write(ax, 6 + i, line, rarity_color)
        self.buffer.write(2, 11, "\u2500" * (W - 4), t.border_color)
        self.buffer.write(3, 12, f"HP:{template.base_hp} ATK:{template.base_atk} DEF:{template.base_def}", t.text_color)
        for i, trait in enumerate(template.traits[:3]):
            self.buffer.write(3, 13 + i, f"\u2022 {trait.name}", t.dim_text_color)
        self.buffer.write(2, 16, "\u2500" * (W - 4), t.border_color)
        owned_str = f"Owned: {detail['count']}"
        shiny_str = f"\u2605 {detail['shiny_count']}"
        shiny_color = (224, 175, 104) if detail["shiny_count"] > 0 else t.dim_text_color
        self.buffer.write(3, 17, owned_str, t.text_color)
        self.buffer.write(W - 2 - len(shiny_str), 17, shiny_str, shiny_color)
        self.buffer.write(3, 19, "[ESC] Back", t.dim_text_color)

    # ------------------------------------------------------------------
    # Tab 1: Shop — draw
    # ------------------------------------------------------------------

    def _draw_shop(self):
        t = self.theme
        W = self.buffer.cols
        mutagen = self.db.get_mutagen()

        self.buffer.write(1, 2, f"Mutagen: {mutagen:,}", t.accent_color)
        self.buffer.write(1, 3, "\u2500" * (W - 2), t.border_color)

        tier_colors = [(169, 177, 214), (122, 162, 247), (224, 175, 104)]
        for i, (name, subtitle, tier) in enumerate(_SHOP_ITEMS):
            y = 4 + i * 5
            cost = tier.cost
            affordable = mutagen >= cost
            is_cur = i == self.shop_cursor
            box_color = tier_colors[i] if is_cur else t.border_color
            name_color = tier_colors[i] if affordable else t.dim_text_color

            self.buffer.draw_box(1, y, W - 2, 4, box_color)
            cursor_ch = "\u25b8" if is_cur else " "
            self.buffer.write(3, y + 1, f"{cursor_ch} {name}", name_color)
            cost_str = f"{cost:,}m"
            self.buffer.write(W - 2 - len(cost_str), y + 1, cost_str, t.highlight_color if affordable else t.dim_text_color)
            self.buffer.write(5, y + 2, subtitle, t.dim_text_color)

        self.buffer.write(1, 20, "[Enter] Buy [\u2190\u2192] Tabs", t.dim_text_color)

    # ------------------------------------------------------------------
    # Tab 2: Idle Arena — draw
    # ------------------------------------------------------------------

    def _draw_idle(self):
        t = self.theme
        W = self.buffer.cols
        idle_team = self.db.get_idle_team()
        slots_filled = {entry["slot"]: entry for entry in idle_team}

        if self.idle_picking:
            self._draw_idle_pick()
            return

        self.buffer.write(1, 2, "Idle Arena", t.accent_color)
        self.buffer.write(1, 3, "\u2500" * (W - 2), t.border_color)

        for slot_idx in range(3):
            slot = slot_idx + 1
            y = 4 + slot_idx * 5
            is_cursor = (slot_idx == self.idle_cursor)
            box_color = t.accent_color if is_cursor else t.border_color
            cursor_ch = "\u25b8" if is_cursor else " "

            self.buffer.draw_box(1, y, W - 2, 4, box_color)
            if slot in slots_filled:
                m = slots_filled[slot]
                shiny_mark = " \u2605" if m.get("is_shiny") else ""
                name_disp = f"{m['name']}{shiny_mark}"
                name_color = (224, 175, 104) if m.get("is_shiny") else t.text_color
                self.buffer.write(3, y + 1, f"{cursor_ch} {name_disp}", name_color)
                hp = m.get("hp", 0)
                atk = m.get("atk", 0)
                defense = m.get("defense", 0)
                c_rate = (hp + atk + defense) / 20.0
                if m.get("is_shiny"):
                    c_rate *= 1.15
                stats = f"HP:{hp} ATK:{atk} \u2192{c_rate:.1f}/m"
                self.buffer.write(3, y + 2, f"  {stats}", t.dim_text_color)
            else:
                self.buffer.write(3, y + 1, f"{cursor_ch} [Empty]", t.dim_text_color)

        from game.progression.idle import calculate_idle_rate
        creatures = list(slots_filled.values())
        rate = calculate_idle_rate(creatures)
        n_active = len(slots_filled)
        self.buffer.write(1, 19, f"~{rate:.1f} mutagen/min ({n_active}/3)", t.dim_text_color)
        self.buffer.write(1, 20, "[Enter] Assign/Remove", t.dim_text_color)

    def _draw_idle_pick(self):
        t = self.theme
        W = self.buffer.cols
        idle_ids = self.db.get_idle_monster_ids()
        all_monsters = self.db.get_collection()
        eligible = [m for m in all_monsters if m["id"] not in idle_ids]

        self.buffer.write(1, 2, f"Pick for Slot {self.idle_cursor + 1}", t.accent_color)
        self.buffer.write(1, 3, "\u2500" * (W - 2), t.border_color)

        visible = 10
        if not eligible:
            self.buffer.write(3, 6, "No creatures.", t.dim_text_color)
        else:
            for row_idx in range(visible):
                m_idx = self.idle_pick_scroll + row_idx
                if m_idx >= len(eligible):
                    break
                m = eligible[m_idx]
                y = 4 + row_idx
                is_cursor = (m_idx == self.idle_pick_cursor)
                cursor_ch = "\u25b8 " if is_cursor else "  "
                shiny_mark = " \u2605" if m.get("is_shiny") else ""
                name_disp = f"{m['name']}{shiny_mark}"
                name_color = (224, 175, 104) if m.get("is_shiny") else (t.accent_color if is_cursor else t.text_color)
                # Per-creature idle rate
                hp = m.get("hp", 0)
                atk = m.get("atk", 0)
                defense = m.get("defense", 0)
                rate = (hp + atk + defense) / 20.0
                if m.get("is_shiny"):
                    rate *= 1.15
                rate_str = f" {rate:.1f}/m"
                self.buffer.write(1, y, cursor_ch, t.accent_color)
                self.buffer.write(3, y, name_disp, name_color)
                self.buffer.write(W - len(rate_str) - 1, y, rate_str, t.dim_text_color)

        if self.idle_pick_scroll > 0:
            self.buffer.write(W - 2, 4, "\u2191", t.dim_text_color)
        if self.idle_pick_scroll + visible < len(eligible):
            self.buffer.write(W - 2, 4 + visible - 1, "\u2193", t.dim_text_color)

        self.buffer.write(1, 20, "[Enter] Assign [ESC] Back", t.dim_text_color)

    # ------------------------------------------------------------------
    # Tab 3: Stats — draw
    # ------------------------------------------------------------------

    def _draw_stats(self):
        t = self.theme
        W = self.buffer.cols
        stats = self.db.get_stats()

        self.buffer.write(1, 2, "Statistics", t.accent_color)
        self.buffer.write(1, 3, "\u2500" * (W - 2), t.border_color)

        rows = [
            ("Discovered", f"{stats['creatures_discovered']}/{len(self.roster)}"),
            ("Shinies", str(stats["shinies_found"])),
            ("Runs", str(stats["runs_completed"])),
            ("Best wave", str(stats["highest_wave"])),
            ("Mutagen", f"{stats['total_mutagen']:,}"),
        ]

        for i, (label, value) in enumerate(rows):
            y = 5 + i * 3
            self.buffer.draw_box(1, y - 1, W - 2, 3, t.border_color)
            self.buffer.write(3, y, label, t.dim_text_color)
            self.buffer.write(W - 2 - len(value), y, value, t.accent_color)

        self.buffer.write(1, 20, "[\u2190\u2192] Tabs", t.dim_text_color)
