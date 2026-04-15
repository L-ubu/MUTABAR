from __future__ import annotations

from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.battle.engine import Battle, BattleState, TurnResult
from game.creatures.ascii_art import get_art

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import MutabarApp


class BattleScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, battle: Battle,
                 app: MutabarApp | None = None, is_boss: bool = False):
        super().__init__(buffer, theme)
        self.battle = battle
        self.app = app
        self.is_boss = is_boss
        self.command_input = ""
        self.narration_text = ""
        self.narration_visible = 0
        self.narration_cpu_text = ""
        self.narration_cpu_visible = 0
        self.last_result: TurnResult | None = None
        # States: input, narrating_player, result_player, narrating_cpu, result, inspect
        self.state = "input"
        self._type_timer = 0.0
        self._cpu_type_timer = 0.0
        self._inspect_player = True

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if self.state == "inspect":
            if action in (Action.CONFIRM, Action.BACK):
                self.state = "input"
            elif action in (Action.LEFT, Action.RIGHT):
                self._inspect_player = not self._inspect_player
            return None

        if self.battle.state != BattleState.ACTIVE:
            if action == Action.CONFIRM:
                return "post_battle"
            return None

        if self.state == "narrating_player":
            if action == Action.CONFIRM:
                self.narration_visible = len(self.narration_text)
                self.state = "result_player"
            return None

        if self.state == "result_player":
            if action == Action.CONFIRM:
                # Skip CPU phase if battle ended or no damage received
                if (self.battle.state != BattleState.ACTIVE or
                        (self.last_result and self.last_result.damage_received == 0)):
                    self.state = "result"
                    return None
                # Generate CPU narration
                if self.app and self.last_result:
                    self.narration_cpu_text = self.app.generate_cpu_battle_narration(
                        self.battle, self.last_result
                    )
                else:
                    cpu = self.battle.cpu_active
                    self.narration_cpu_text = (
                        f"The {cpu.mutation_type.name} {cpu.name} strikes back! "
                        f"{self.last_result.damage_received} damage."
                    )
                self.narration_cpu_visible = 0
                self._cpu_type_timer = 0.0
                self.state = "narrating_cpu"
            return None

        if self.state == "narrating_cpu":
            if action == Action.CONFIRM:
                self.narration_cpu_visible = len(self.narration_cpu_text)
                self.state = "result"
            return None

        if self.state == "result":
            if action == Action.CONFIRM:
                self.state = "input"
                self.command_input = ""
                self.narration_text = ""
                self.narration_visible = 0
                self.narration_cpu_text = ""
                self.narration_cpu_visible = 0
            return None

        # Input state
        if action == Action.CHAR:
            if char.lower() == "\t" or char.lower() == "i":
                if not self.command_input.strip():
                    self.state = "inspect"
                    return None
            if len(self.command_input) < 80:
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
                p = self.battle.player_active
                self.narration_text = (
                    f"The {p.mutation_type.name} {p.name} attacks! "
                    f"{self.last_result.damage_dealt} damage dealt."
                )
            self.narration_visible = 0
            self._type_timer = 0.0
            self.state = "narrating_player"
        elif action == Action.BACK:
            return "main_menu"
        return None

    def update(self, dt: float):
        chars_per_sec = 30
        if self.state == "narrating_player" and self.narration_visible < len(self.narration_text):
            self._type_timer += dt
            while self._type_timer > 1.0 / chars_per_sec and self.narration_visible < len(self.narration_text):
                self.narration_visible += 1
                self._type_timer -= 1.0 / chars_per_sec
            if self.narration_visible >= len(self.narration_text):
                self.state = "result_player"
        elif self.state == "narrating_cpu" and self.narration_cpu_visible < len(self.narration_cpu_text):
            self._cpu_type_timer += dt
            while self._cpu_type_timer > 1.0 / chars_per_sec and self.narration_cpu_visible < len(self.narration_cpu_text):
                self.narration_cpu_visible += 1
                self._cpu_type_timer -= 1.0 / chars_per_sec
            if self.narration_cpu_visible >= len(self.narration_cpu_text):
                self.state = "result"

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols
        H = self.buffer.rows

        if self.state == "inspect":
            self._draw_inspect()
            return

        p = self.battle.player_active
        c = self.battle.cpu_active

        # Header
        if self.is_boss:
            self.buffer.write_animated(1, 1, "\u2501\u2501 BOSS BATTLE " + "\u2501" * (W - 17),
                                       (247, 118, 142), "glow")
        else:
            self.buffer.write(1, 1, "\u2501\u2501 BATTLE " + "\u2501" * (W - 12), t.accent_color)

        # Player creature
        p_color = t.type_colors.get(p.mutation_type, t.text_color)
        self.buffer.write(1, 3, p.name, t.text_color)
        self.buffer.write(1, 4, p.mutation_type.name[:4], p_color)
        self.buffer.draw_hp_bar(6, 4, 8, p.current_hp, p.max_hp)
        self.buffer.write(15, 4, f"{p.current_hp}", t.dim_text_color)

        # CPU creature
        cx = W // 2 + 1
        c_color = t.type_colors.get(c.mutation_type, t.text_color)
        self.buffer.write(cx, 3, c.name, t.text_color)
        self.buffer.write(cx, 4, c.mutation_type.name[:4], c_color)
        self.buffer.draw_hp_bar(cx + 5, 4, 8, c.current_hp, c.max_hp)

        # Narration box — show last 4 visible lines (scrolling)
        box_lines = 4
        self.buffer.draw_box(1, 6, W - 2, box_lines + 2, t.border_color)

        # Pick which narration text to show based on phase
        if self.state in ("narrating_cpu", "result"):
            # CPU phase: show CPU narration
            vis_text = self.narration_cpu_text[:self.narration_cpu_visible] if self.narration_cpu_text else ""
        else:
            # Player phase: show player narration
            vis_text = self.narration_text[:self.narration_visible] if self.narration_text else ""
        if vis_text:
            lines = self._wrap_text(vis_text, W - 6)
            show = lines[-box_lines:] if len(lines) > box_lines else lines
            for i, line in enumerate(show):
                self.buffer.write(3, 7 + i, line, t.text_color)

        # Damage display — show progressively
        if self.last_result:
            show_player_dmg = self.state in ("result_player", "narrating_cpu", "result")
            show_cpu_dmg = self.state == "result"

            if show_player_dmg:
                dmg_text = f"\u25b8 {self.last_result.damage_dealt} DMG"
                eff = self.last_result.player_damage_result
                if eff and eff.effectiveness == "super_effective":
                    dmg_text += " (SE!)"
                elif eff and eff.effectiveness == "resisted":
                    dmg_text += " (resist)"
                if eff and eff.is_critical:
                    dmg_text += " CRIT!"
                self.buffer.write(1, 13, dmg_text, t.highlight_color)
            if show_cpu_dmg and self.last_result.damage_received > 0:
                self.buffer.write(1, 14, f"\u25c2 {self.last_result.damage_received} DMG", t.dim_text_color)

        # Status effects
        effects_text = ""
        for eff in self.battle.cpu_active_effects:
            effects_text += f"[{eff.status_type.value}:{eff.remaining_turns}] "
        if effects_text:
            self.buffer.write(1, 15, effects_text.strip()[:W-2], t.accent_color)

        # Bottom section
        if self.battle.state == BattleState.ACTIVE:
            if self.state == "input":
                self.buffer.write(1, 16, "Traits:", t.dim_text_color)
                for i, trait in enumerate(p.traits[:2]):
                    kw = ", ".join(trait.keywords[:2])
                    self.buffer.write(1, 17 + i, f"\u2022 {trait.name} ({kw})", t.dim_text_color)
                self.buffer.write(1, 19, "\u2500" * (W - 2), t.border_color)
                max_input_w = W - 4
                display_text = self.command_input
                if len(display_text) > max_input_w:
                    display_text = display_text[-(max_input_w):]
                self.buffer.write(1, 20, "\u276f " + display_text + "\u258c", t.accent_color)
                self.buffer.write(W - 12, 21, "[I] Inspect", t.dim_text_color)
            elif self.state in ("narrating_player", "narrating_cpu"):
                self.buffer.write(1, 20, "[Enter] skip", t.dim_text_color)
            else:
                self.buffer.write(1, 20, "[Enter] continue", t.dim_text_color)
        else:
            msg = "VICTORY!" if self.battle.state == BattleState.PLAYER_WIN else "DEFEATED..."
            color = t.accent_color if self.battle.state == BattleState.PLAYER_WIN else (247, 118, 142)
            self.buffer.write((W - len(msg)) // 2, 17, msg, color)
            self.buffer.write((W - 18) // 2, 19, "[Enter] continue", t.dim_text_color)

    def _draw_inspect(self):
        """Draw creature stat card overlay."""
        t = self.theme
        W = self.buffer.cols
        creature = self.battle.player_active if self._inspect_player else self.battle.cpu_active
        label = "YOUR" if self._inspect_player else "ENEMY"

        if creature.is_shiny:
            # Animated golden border for shinies
            top = "\u250c" + "\u2500" * (W - 4) + "\u2510"
            bot = "\u2514" + "\u2500" * (W - 4) + "\u2518"
            self.buffer.write_animated(1, 1, top, (255, 200, 80), "golden")
            for row in range(1, 17):
                self.buffer.write_animated(1, 1 + row, "\u2502", (255, 200, 80), "golden")
                self.buffer.write_animated(W - 2, 1 + row, "\u2502", (255, 200, 80), "golden")
            self.buffer.write_animated(1, 18, bot, (255, 200, 80), "golden")
        else:
            self.buffer.draw_box(1, 1, W - 2, 18, t.accent_color)
        self.buffer.write(3, 2, f"{label} CREATURE", t.dim_text_color)
        self.buffer.write(3, 3, "\u2500" * (W - 6), t.border_color)

        c_color = t.type_colors.get(creature.mutation_type, t.text_color)
        if creature.is_shiny:
            self.buffer.write_animated(3, 4, creature.name, (255, 200, 80), "golden")
        else:
            self.buffer.write(3, 4, creature.name, t.text_color)
        self.buffer.write(3, 5, creature.mutation_type.name, c_color)
        if creature.is_shiny:
            self.buffer.write_animated(3 + len(creature.mutation_type.name) + 1, 5, "\u2726 SHINY", (255, 200, 80), "golden")

        self.buffer.write(3, 7, f"HP:  {creature.current_hp}/{creature.max_hp}", t.text_color)
        self.buffer.write(3, 8, f"ATK: {creature.atk}", t.text_color)
        self.buffer.write(3, 9, f"DEF: {creature.defense}", t.text_color)
        self.buffer.write(3, 10, f"LVL: {creature.level}", t.dim_text_color)

        # ASCII art on the right side
        art = get_art(creature.name)
        art_color = (255, 200, 80) if creature.is_shiny else c_color
        art_anim = "golden" if creature.is_shiny else None
        for i, line in enumerate(art):
            if art_anim:
                self.buffer.write_animated(23, 6 + i, line[:11], art_color, art_anim)
            else:
                self.buffer.write(23, 6 + i, line[:11], art_color)

        self.buffer.write(3, 12, "Traits:", t.dim_text_color)
        for i, trait in enumerate(creature.traits[:4]):
            self.buffer.write(3, 13 + i, f"\u2022 {trait.name}", t.text_color)

        self.buffer.write(3, 19, "[\u2190\u2192] Switch  [ESC] Back", t.dim_text_color)

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
