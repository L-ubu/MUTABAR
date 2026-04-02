import time
from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.battle.engine import Battle, BattleState, TurnResult


class BattleScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, battle: Battle):
        super().__init__(buffer, theme)
        self.battle = battle
        self.command_input = ""
        self.narration_text = ""
        self.narration_visible = 0
        self.last_result: TurnResult | None = None
        self.state = "input"  # "input", "narrating", "result"
        self._type_timer = 0.0

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if self.battle.state != BattleState.ACTIVE:
            if action == Action.CONFIRM:
                return "post_battle"
            return None

        if self.state == "narrating":
            if action == Action.CONFIRM:
                self.narration_visible = len(self.narration_text)
                self.state = "result"
            return None

        if self.state == "result":
            if action == Action.CONFIRM:
                self.state = "input"
                self.command_input = ""
                self.narration_text = ""
                self.narration_visible = 0
            return None

        # Input state
        if action == Action.CHAR:
            if len(self.command_input) < 40:
                self.command_input += char
        elif action == Action.BACKSPACE:
            self.command_input = self.command_input[:-1]
        elif action == Action.CONFIRM and self.command_input.strip():
            self.last_result = self.battle.execute_player_turn(self.command_input)
            self.narration_text = f"The {self.battle.player_active.mutation_type.name} {self.battle.player_active.name} attacks! {self.last_result.damage_dealt} damage dealt."
            self.narration_visible = 0
            self.state = "narrating"
        elif action == Action.BACK:
            return "main_menu"
        return None

    def update(self, dt: float):
        if self.state == "narrating" and self.narration_visible < len(self.narration_text):
            self._type_timer += dt
            chars_per_sec = 30
            while self._type_timer > 1.0 / chars_per_sec and self.narration_visible < len(self.narration_text):
                self.narration_visible += 1
                self._type_timer -= 1.0 / chars_per_sec
            if self.narration_visible >= len(self.narration_text):
                self.state = "result"

    def draw(self):
        self.buffer.clear()
        t = self.theme
        p = self.battle.player_active
        c = self.battle.cpu_active

        # Header
        self.buffer.write(2, 1, "\u2501\u2501\u2501 BATTLE \u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501", t.accent_color)

        # Player monster (left)
        p_color = t.type_colors.get(p.mutation_type, t.text_color)
        self.buffer.write(2, 3, p.mutation_type.name, p_color)
        self.buffer.write(2 + len(p.mutation_type.name) + 1, 3, p.name, t.text_color)
        self.buffer.write(2, 4, "HP ", t.dim_text_color)
        self.buffer.draw_hp_bar(5, 4, 15, p.current_hp, p.max_hp)
        self.buffer.write(21, 4, f" {p.current_hp}/{p.max_hp}", t.dim_text_color)

        # CPU monster (right)
        c_color = t.type_colors.get(c.mutation_type, t.text_color)
        rx = 28
        self.buffer.write(rx, 3, c.mutation_type.name, c_color)
        self.buffer.write(rx + len(c.mutation_type.name) + 1, 3, c.name, t.text_color)
        self.buffer.write(rx, 4, "HP ", t.dim_text_color)
        self.buffer.draw_hp_bar(rx + 3, 4, 15, c.current_hp, c.max_hp)

        # Narration box
        self.buffer.draw_box(1, 7, 48, 10, t.border_color)
        if self.narration_text:
            visible = self.narration_text[:self.narration_visible]
            lines = self._wrap_text(visible, 44)
            for i, line in enumerate(lines[:7]):
                self.buffer.write(3, 8 + i, line, t.text_color)

        # Damage display
        if self.last_result and self.state == "result":
            dmg_text = f"\u25b8 {self.last_result.damage_dealt} DMG"
            eff = self.last_result.player_damage_result
            if eff and eff.effectiveness == "super_effective":
                dmg_text += " (super effective!)"
            elif eff and eff.effectiveness == "resisted":
                dmg_text += " (resisted)"
            if eff and eff.is_critical:
                dmg_text += " CRITICAL!"
            self.buffer.write(3, 16, dmg_text, t.highlight_color)

            if self.last_result.damage_received > 0:
                self.buffer.write(3, 17, f"\u25c2 {self.last_result.damage_received} DMG received", t.dim_text_color)

        # Status effects
        y_status = 19
        for eff in self.battle.cpu_active_effects:
            self.buffer.write(2, y_status, f"[{eff.status_type.value}:{eff.remaining_turns}t]", t.accent_color)
            y_status += 1

        # Input area
        if self.battle.state == BattleState.ACTIVE:
            self.buffer.write(2, 30, "\u2500" * 46, t.border_color)
            if self.state == "input":
                self.buffer.write(2, 31, "\u276f " + self.command_input + "\u258c", t.accent_color)
            elif self.state == "narrating":
                self.buffer.write(2, 31, "[Enter] to skip", t.dim_text_color)
            else:
                self.buffer.write(2, 31, "[Enter] to continue", t.dim_text_color)
        else:
            msg = "VICTORY!" if self.battle.state == BattleState.PLAYER_WIN else "DEFEATED..."
            color = t.accent_color if self.battle.state == BattleState.PLAYER_WIN else (247, 118, 142)
            self.buffer.write(18, 25, msg, color)
            self.buffer.write(12, 27, "[Enter] to continue", t.dim_text_color)

    def _wrap_text(self, text: str, width: int) -> list[str]:
        words = text.split()
        lines, current = [], ""
        for word in words:
            if len(current) + len(word) + 1 <= width:
                current = f"{current} {word}".strip()
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
