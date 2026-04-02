from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.creatures.database import CREATURE_ROSTER
from game.progression.mutabox import MutaboxTier
from game.progression.lootbox import _get_creature_rarity, Rarity


_RARITY_COLORS = {
    Rarity.COMMON: (169, 177, 214),
    Rarity.UNCOMMON: (158, 206, 106),
    Rarity.RARE: (122, 162, 247),
    Rarity.EPIC: (187, 154, 247),
    Rarity.LEGENDARY: (224, 175, 104),
}

_SHOP_ITEMS = [
    ("Standard Mutabox", "Standard odds", MutaboxTier.STANDARD),
    ("Premium Mutabox", "Better rarity!", MutaboxTier.PREMIUM),
    ("Shiny Mutabox", "5x shiny chance!", MutaboxTier.SHINY),
]

_COLLECTION_VISIBLE = 16  # rows y=4..y=19


class MutadexScreen(Screen):
    TABS = ["Collection", "Shop", "Idle", "Stats"]

    def __init__(self, buffer: TextBuffer, theme: Theme, db):
        super().__init__(buffer, theme)
        self.db = db
        self.active_tab = 0
        # Collection state
        self.scroll = 0
        self.cursor = 0
        self.detail_creature = None  # None = list view, dict = detail view
        self.roster = sorted(CREATURE_ROSTER, key=lambda t: t.name)
        # Shop state
        self.shop_cursor = 0
        self.pending_mutabox_tier = None  # set before returning "open_mutabox"
        # Idle state
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
            # Detail view: any navigation or confirm closes it
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
            # Build pick list: all collection minus already-idle monsters
            idle_ids = self.db.get_idle_monster_ids()
            all_monsters = self.db.get_collection()
            eligible = [m for m in all_monsters if m["id"] not in idle_ids]

            n = len(eligible)
            visible = 14
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
                slot = self.idle_cursor + 1  # slots are 1-indexed
                self.db.set_idle_slot(slot, chosen["id"])
                self.idle_picking = False
                self.idle_pick_cursor = 0
                self.idle_pick_scroll = 0
            return None

        # Normal idle slot navigation
        if action == Action.UP:
            self.idle_cursor = max(0, self.idle_cursor - 1)
        elif action == Action.DOWN:
            self.idle_cursor = min(2, self.idle_cursor + 1)
        elif action == Action.CONFIRM:
            slot = self.idle_cursor + 1
            if slot in slots_filled:
                self.db.clear_idle_slot(slot)
            else:
                # Enter pick mode
                self.idle_picking = True
                self.idle_pick_cursor = 0
                self.idle_pick_scroll = 0
        return None

    # ------------------------------------------------------------------
    # Tab 3: Stats — input
    # ------------------------------------------------------------------

    def _handle_stats(self, action: Action) -> str | None:
        return None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float):
        pass

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols

        # Tab bar at row 0
        x = 2
        for i, tab in enumerate(self.TABS):
            color = t.accent_color if i == self.active_tab else t.dim_text_color
            label = f"[{tab}]" if i == self.active_tab else f" {tab} "
            self.buffer.write(x, 0, label, color)
            x += len(label) + 1
        self.buffer.write(2, 1, "\u2500" * (W - 4), t.border_color)

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
        n_discovered = len(discovered)

        if self.detail_creature:
            self._draw_collection_detail(self.detail_creature)
            return

        # Header
        header = f"Collection: {n_discovered}/53 discovered"
        self.buffer.write(2, 2, header, t.text_color)
        self.buffer.write(2, 3, "\u2500" * (W - 4), t.border_color)

        # Column headings
        self.buffer.write(4, 3, " Name", t.dim_text_color)
        self.buffer.write(22, 3, "Rarity", t.dim_text_color)

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
                rarity_name = rarity.name.capitalize()
                name_col = t.highlight_color if is_cursor else t.text_color
                self.buffer.write(2, y, cursor_ch, t.accent_color)
                self.buffer.write(4, y, f"{template.name:<16}", name_col)
                self.buffer.write(21, y, f"{rarity_name:<10}", rarity_color)
            else:
                dim = t.dim_text_color
                self.buffer.write(2, y, cursor_ch, dim)
                self.buffer.write(4, y, "???             ", dim)
                self.buffer.write(21, y, "???       ", dim)

        # Scroll indicators
        if self.scroll > 0:
            self.buffer.write(W - 4, 4, "\u2191", t.dim_text_color)
        if self.scroll + _COLLECTION_VISIBLE < len(self.roster):
            self.buffer.write(W - 4, 4 + _COLLECTION_VISIBLE - 1, "\u2193", t.dim_text_color)

        self.buffer.write(2, 21, "\u2500" * (W - 4), t.border_color)
        self.buffer.write(2, 22, "[Enter] View details  [\u2190\u2192] Switch tabs", t.dim_text_color)

    def _draw_collection_detail(self, detail: dict):
        t = self.theme
        W = self.buffer.cols
        template = detail["template"]
        rarity = detail["rarity"]
        rarity_color = _RARITY_COLORS.get(rarity, t.text_color)

        self.buffer.draw_box(2, 2, W - 4, 22, t.border_color)
        self.buffer.write(4, 3, template.name, t.highlight_color)
        self.buffer.write(4, 4, f"Rarity: {rarity.name.capitalize()}", rarity_color)
        self.buffer.write(4, 5, f"Category: {template.category.value.capitalize()}", t.dim_text_color)
        self.buffer.write(4, 6, "\u2500" * (W - 8), t.border_color)

        # Base stats
        self.buffer.write(4, 7, "Base Stats:", t.text_color)
        self.buffer.write(4, 8, f"  HP:  {template.base_hp}", t.text_color)
        self.buffer.write(4, 9, f"  ATK: {template.base_atk}", t.text_color)
        self.buffer.write(4, 10, f"  DEF: {template.base_def}", t.text_color)
        self.buffer.write(4, 11, "\u2500" * (W - 8), t.border_color)

        # Traits
        self.buffer.write(4, 12, "Traits:", t.text_color)
        for i, trait in enumerate(template.traits):
            if i >= 4:
                break
            self.buffer.write(4, 13 + i, f"  \u2022 {trait.name}", t.dim_text_color)

        trait_end_y = 13 + min(len(template.traits), 4)
        self.buffer.write(4, trait_end_y, "\u2500" * (W - 8), t.border_color)

        # Owned counts
        self.buffer.write(4, trait_end_y + 1, f"Owned: {detail['count']}", t.text_color)
        shiny_color = (224, 175, 104) if detail["shiny_count"] > 0 else t.dim_text_color
        self.buffer.write(4, trait_end_y + 2, f"\u2605 Shiny: {detail['shiny_count']}", shiny_color)

        self.buffer.write(4, 22, "[ESC/Enter] Back", t.dim_text_color)

    # ------------------------------------------------------------------
    # Tab 1: Shop — draw
    # ------------------------------------------------------------------

    def _draw_shop(self):
        t = self.theme
        W = self.buffer.cols
        mutagen = self.db.get_mutagen()

        self.buffer.write(2, 2, f"Mutagen: {mutagen:,}", t.accent_color)
        self.buffer.write(2, 3, "\u2500" * (W - 4), t.border_color)

        for i, (name, subtitle, tier) in enumerate(_SHOP_ITEMS):
            y = 5 + i * 5
            cost = tier.cost
            affordable = mutagen >= cost
            cursor_ch = "\u25b8" if i == self.shop_cursor else " "
            box_color = t.accent_color if i == self.shop_cursor else t.border_color
            name_color = t.text_color if affordable else t.dim_text_color
            cost_color = t.highlight_color if affordable else t.dim_text_color

            self.buffer.draw_box(3, y - 1, W - 6, 4, box_color)
            self.buffer.write(5, y, f"{cursor_ch} {name}", name_color)
            self.buffer.write(5, y + 1, f"  {subtitle}", t.dim_text_color)
            cost_str = f"{cost:,} mutagen"
            self.buffer.write(W - 4 - len(cost_str), y, cost_str, cost_color)

        self.buffer.write(2, 20, "\u2500" * (W - 4), t.border_color)
        self.buffer.write(2, 21, "[Enter] Purchase  [\u2190\u2192] Switch tabs", t.dim_text_color)

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

        self.buffer.write(2, 2, "Idle Arena  (3 slots)", t.text_color)
        self.buffer.write(2, 3, "\u2500" * (W - 4), t.border_color)

        for slot_idx in range(3):
            slot = slot_idx + 1
            y = 5 + slot_idx * 5
            is_cursor = (slot_idx == self.idle_cursor)
            box_color = t.accent_color if is_cursor else t.border_color
            cursor_ch = "\u25b8" if is_cursor else " "

            self.buffer.draw_box(3, y - 1, W - 6, 4, box_color)
            if slot in slots_filled:
                m = slots_filled[slot]
                shiny_mark = " \u2605" if m.get("is_shiny") else ""
                name_disp = f"{m['name']}{shiny_mark}"
                name_color = (224, 175, 104) if m.get("is_shiny") else t.text_color
                self.buffer.write(5, y, f"{cursor_ch} Slot {slot}: {name_disp}", name_color)
                stats = f"HP:{m.get('hp', '?')} ATK:{m.get('atk', '?')} DEF:{m.get('defense', '?')}"
                self.buffer.write(7, y + 1, stats, t.dim_text_color)
                self.buffer.write(W - 16, y, "[Enter] Remove", t.dim_text_color)
            else:
                self.buffer.write(5, y, f"{cursor_ch} Slot {slot}: [Empty Slot]", t.dim_text_color)
                self.buffer.write(W - 16, y, "[Enter] Assign", t.dim_text_color)

        # Earnings rate at bottom
        n_active = len(slots_filled)
        earnings_rate = n_active * 5  # 5 mutagen/min per slot (placeholder rate)
        self.buffer.write(2, 19, "\u2500" * (W - 4), t.border_color)
        self.buffer.write(2, 20, f"Earnings: ~{earnings_rate} mutagen/min  ({n_active}/3 active)", t.dim_text_color)
        self.buffer.write(2, 21, "\u2500" * (W - 4), t.border_color)
        self.buffer.write(2, 22, "[Enter] Assign/Remove  [\u2190\u2192] Switch tabs", t.dim_text_color)

    def _draw_idle_pick(self):
        t = self.theme
        W = self.buffer.cols
        idle_ids = self.db.get_idle_monster_ids()
        all_monsters = self.db.get_collection()
        eligible = [m for m in all_monsters if m["id"] not in idle_ids]

        self.buffer.write(2, 2, f"Choose creature for Slot {self.idle_cursor + 1}", t.accent_color)
        self.buffer.write(2, 3, "\u2500" * (W - 4), t.border_color)

        visible = 14
        if not eligible:
            self.buffer.write(4, 6, "No eligible creatures available.", t.dim_text_color)
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
                name_color = (224, 175, 104) if m.get("is_shiny") else (t.highlight_color if is_cursor else t.text_color)
                stats = f"HP:{m.get('hp', '?')} ATK:{m.get('atk', '?')}"
                self.buffer.write(2, y, cursor_ch, t.accent_color)
                self.buffer.write(4, y, f"{name_disp:<18}", name_color)
                self.buffer.write(23, y, stats, t.dim_text_color)

        # Scroll indicators
        if self.idle_pick_scroll > 0:
            self.buffer.write(W - 4, 4, "\u2191", t.dim_text_color)
        if self.idle_pick_scroll + visible < len(eligible):
            self.buffer.write(W - 4, 4 + visible - 1, "\u2193", t.dim_text_color)

        self.buffer.write(2, 19, "\u2500" * (W - 4), t.border_color)
        self.buffer.write(2, 20, "[Enter] Assign  [ESC] Cancel", t.dim_text_color)

    # ------------------------------------------------------------------
    # Tab 3: Stats — draw
    # ------------------------------------------------------------------

    def _draw_stats(self):
        t = self.theme
        W = self.buffer.cols
        stats = self.db.get_stats()

        self.buffer.write(2, 2, "Statistics", t.text_color)
        self.buffer.write(2, 3, "\u2500" * (W - 4), t.border_color)

        rows = [
            ("Creatures discovered", f"{stats['creatures_discovered']}/53"),
            ("Shinies found", str(stats["shinies_found"])),
            ("Runs completed", str(stats["runs_completed"])),
            ("Highest wave", str(stats["highest_wave"])),
            ("Total mutagen", f"{stats['total_mutagen']:,}"),
        ]

        for i, (label, value) in enumerate(rows):
            y = 5 + i * 3
            self.buffer.draw_box(3, y - 1, W - 6, 3, t.border_color)
            self.buffer.write(5, y, label, t.dim_text_color)
            value_x = W - 4 - len(value)
            self.buffer.write(value_x, y, value, t.accent_color)

        self.buffer.write(2, 21, "\u2500" * (W - 4), t.border_color)
        self.buffer.write(2, 22, "[\u2190\u2192] Switch tabs", t.dim_text_color)
