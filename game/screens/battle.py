from __future__ import annotations

from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.battle.engine import Battle, BattleState, TurnResult

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import MutabarApp


class BattleScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, battle: Battle, app: MutabarApp | None = None):
        super().__init__(buffer, theme)
        self.battle = battle
        self.app = app
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
            if len(self.command_input) < 35:
                self.command_input += char
        elif action == Action.BACKSPACE:
            self.command_input = self.command_input[:-1]
        elif action == Action.CONFIRM and self.command_input.strip():
            self.last_result = self.battle.execute_player_turn(self.command_input)
            if self.app:
                self.narration_text = self.app.generate_battle_narration(
                    self.battle, self.command_input, self.last_result
                )
            else:
                self.narration_text = (
                    f"The {self.battle.player_active.mutation_type.name} "
                    f"{self.battle.player_active.name} attacks! "
                    f"{self.last_result.damage_dealt} damage dealt."
                )
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
        W = self.buffer.cols  # 43

        # Header — row 0
        header = "\u2501\u2501 BATTLE " + "\u2501" * (W - 11)
        self.buffer.write(1, 0, header, t.accent_color)

        # Player creature — row 2
        p_color = t.type_colors.get(p.mutation_type, t.text_color)
        self.buffer.write(1, 2, p.mutation_type.name, p_color)
        self.buffer.write(1 + len(p.mutation_type.name) + 1, 2, p.name, t.text_color)
        self.buffer.write(1, 3, "HP ", t.dim_text_color)
        self.buffer.draw_hp_bar(4, 3, 12, p.current_hp, p.max_hp)
        self.buffer.write(17, 3, f" {p.current_hp}/{p.max_hp}", t.dim_text_color)

        # CPU creature — row 2 right
        c_color = t.type_colors.get(c.mutation_type, t.text_color)
        rx = 24
        self.buffer.write(rx, 2, c.mutation_type.name, c_color)
        self.buffer.write(rx + len(c.mutation_type.name) + 1, 2, c.name, t.text_color)
        self.buffer.write(rx, 3, "HP ", t.dim_text_color)
        self.buffer.draw_hp_bar(rx + 3, 3, 12, c.current_hp, c.max_hp)

        # Narration box — rows 5-10 (6 tall)
        box_w = W - 2
        self.buffer.draw_box(1, 5, box_w, 6, t.border_color)
        if self.narration_text:
            visible = self.narration_text[:self.narration_visible]
            lines = self._wrap_text(visible, box_w - 4)
            for i, line in enumerate(lines[:4]):
                self.buffer.write(3, 6 + i, line, t.text_color)

        # Damage display — rows 12-13
        if self.last_result and self.state == "result":
            dmg_text = f"\u25b8 {self.last_result.damage_dealt} DMG"
            eff = self.last_result.player_damage_result
            if eff and eff.effectiveness == "super_effective":
                dmg_text += " (super effective!)"
            elif eff and eff.effectiveness == "resisted":
                dmg_text += " (resisted)"
            if eff and eff.is_critical:
                dmg_text += " CRIT!"
            self.buffer.write(2, 12, dmg_text, t.highlight_color)

            if self.last_result.damage_received > 0:
                self.buffer.write(2, 13, f"\u25c2 {self.last_result.damage_received} DMG received", t.dim_text_color)

        # Status effects — row 15
        effects_text = ""
        for eff in self.battle.cpu_active_effects:
            effects_text += f"[{eff.status_type.value}:{eff.remaining_turns}t] "
        if effects_text:
            self.buffer.write(1, 15, effects_text.strip(), t.accent_color)

        # Bottom section — input or end state
        if self.battle.state == BattleState.ACTIVE:
            if self.state == "input":
                # Trait hints — rows 17-19
                self.buffer.write(1, 17, "Traits:", t.dim_text_color)
                for i, trait in enumerate(p.traits[:3]):
                    kw = ", ".join(trait.keywords[:2])
                    self.buffer.write(2, 18 + i, f"\u2022 {trait.name} ({kw})", t.dim_text_color)

                # Input prompt — row 22
                self.buffer.write(1, 21, "\u2500" * (W - 2), t.border_color)
                self.buffer.write(1, 22, "\u276f " + self.command_input + "\u258c", t.accent_color)
                self.buffer.write(1, 24, "Use trait keywords for bonus dmg!", t.dim_text_color)
            elif self.state == "narrating":
                self.buffer.write(1, 22, "[Enter] to skip", t.dim_text_color)
            else:
                self.buffer.write(1, 22, "[Enter] to continue", t.dim_text_color)
        else:
            msg = "VICTORY!" if self.battle.state == BattleState.PLAYER_WIN else "DEFEATED..."
            color = t.accent_color if self.battle.state == BattleState.PLAYER_WIN else (247, 118, 142)
            center = (W - len(msg)) // 2
            self.buffer.write(center, 19, msg, color)
            center2 = (W - 20) // 2
            self.buffer.write(center2, 21, "[Enter] to continue", t.dim_text_color)

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
