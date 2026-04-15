import json
from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.creatures.creature import Creature, CreatureCategory
from game.creatures.types import MutationType
from game.creatures.traits import Trait


def creature_from_db_row(row: dict) -> Creature:
    traits_raw = row.get("traits", [])
    if isinstance(traits_raw, str):
        traits_raw = json.loads(traits_raw)
    traits = [Trait(name=t, description="", keywords=[]) if isinstance(t, str) else t for t in traits_raw]
    return Creature(
        name=row["name"],
        category=CreatureCategory(row["category"].lower()) if row.get("category") else CreatureCategory.ANIMAL,
        mutation_type=MutationType[row["mutation_type"]] if row.get("mutation_type") else MutationType.FIRE,
        traits=traits,
        base_hp=row.get("hp", 50),
        base_atk=row.get("atk", 10),
        base_def=row.get("defense", 10),
        level=row.get("level", 1),
        xp=row.get("xp", 0),
        is_shiny=bool(row.get("is_shiny", 0)),
    )


class TeamSelectScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, db):
        super().__init__(buffer, theme)
        self.db = db
        idle_ids = db.get_idle_monster_ids()
        all_monsters = db.load_all_monsters()
        self.available = [m for m in all_monsters if m["id"] not in idle_ids]
        self.cursor = 0
        self.selected_indices: set[int] = set()
        self.scroll = 0

    @property
    def selected_team(self) -> list[Creature]:
        return [creature_from_db_row(self.available[i]) for i in sorted(self.selected_indices)]

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if action == Action.BACK:
            return "main_menu"
        if not self.available:
            return None
        if action == Action.UP:
            self.cursor = max(0, self.cursor - 1)
            if self.cursor < self.scroll:
                self.scroll = self.cursor
        elif action == Action.DOWN:
            self.cursor = min(len(self.available) - 1, self.cursor + 1)
            visible = self.buffer.rows - 6
            if self.cursor >= self.scroll + visible:
                self.scroll = self.cursor - visible + 1
        elif action == Action.CONFIRM:
            if self.cursor in self.selected_indices:
                self.selected_indices.discard(self.cursor)
            elif len(self.selected_indices) < 3:
                self.selected_indices.add(self.cursor)
        elif action == Action.CHAR and char.lower() == "s" and self.selected_indices:
            return "start_run"
        return None

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols
        H = self.buffer.rows
        self.buffer.write(1, 1, "SELECT TEAM (1-3)", t.accent_color)
        sel_text = f"{len(self.selected_indices)}/3"
        self.buffer.write(W - 1 - len(sel_text), 1, sel_text, t.highlight_color)
        self.buffer.write(1, 2, "\u2500" * (W - 2), t.border_color)

        visible = H - 6
        for vi in range(visible):
            idx = self.scroll + vi
            if idx >= len(self.available):
                break
            m = self.available[idx]
            y = 4 + vi
            is_sel = idx in self.selected_indices
            is_cur = idx == self.cursor
            prefix = "\u2605" if is_sel else "\u25b8" if is_cur else " "
            shiny = "\u2726" if m.get("is_shiny") else ""
            name = m["name"][:10]
            hp = m.get("hp", "?")
            atk = m.get("atk", "?")
            color = t.accent_color if is_cur else (t.highlight_color if is_sel else t.text_color)
            self.buffer.write(1, y, f"{prefix} {name:<11}{shiny}", color)
            self.buffer.write(W - 11, y, f"{hp}/{atk}", t.dim_text_color)

        if self.selected_indices:
            self.buffer.write(1, H - 2, "[S] Start Run", t.accent_color)
        self.buffer.write(1, H - 1, "Enter:toggle ESC:back", t.dim_text_color)
