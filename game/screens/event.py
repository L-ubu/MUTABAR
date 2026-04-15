"""
game/screens/event.py
Random event screen — Slay the Spire-style encounters between waves.
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from game.screens.base import Screen, Action
from game.renderer import TextBuffer
from game.theme import Theme
from game.creatures.creature import Creature
from game.events.event_types import Event, EventChoice
from game.events.resolver import resolve_choice, apply_event_effect

if TYPE_CHECKING:
    from main import MutabarApp


class EventScreen(Screen):
    def __init__(self, buffer: TextBuffer, theme: Theme, event: Event,
                 wave: int, player_team: List[Creature],
                 app: MutabarApp | None = None):
        super().__init__(buffer, theme)
        self.event = event
        self.wave = wave
        self.player_team = player_team
        self.app = app

        # States: scene -> input -> narrating_outcome -> result
        self.state = "scene"
        self.scene_text = ""
        self.scene_visible = 0
        self.outcome_text = ""
        self.outcome_visible = 0
        self.command_input = ""
        self.chosen: EventChoice | None = None
        self._type_timer = 0.0

        # Generate scene narration
        if self.app:
            self.scene_text = self.app.generate_event_scene(event, wave, player_team)
        else:
            self.scene_text = event.description_template

    def handle_input(self, action: Action, char: str = "") -> str | None:
        if self.state == "scene":
            if action == Action.CONFIRM:
                if self.scene_visible < len(self.scene_text):
                    self.scene_visible = len(self.scene_text)
                else:
                    self.state = "input"
            return None

        if self.state == "input":
            if action == Action.CHAR:
                if len(self.command_input) < 80:
                    self.command_input += char
            elif action == Action.BACKSPACE:
                self.command_input = self.command_input[:-1]
            elif action == Action.CONFIRM and self.command_input.strip():
                self.chosen = resolve_choice(self.command_input, self.event)
                apply_event_effect(self.chosen, self.player_team,
                                   db=self.app.db if self.app else None)
                # Generate outcome narration
                if self.app:
                    self.outcome_text = self.app.generate_event_outcome(
                        self.event, self.command_input, self.chosen
                    )
                else:
                    self.outcome_text = self.chosen.outcome_template
                self.outcome_visible = 0
                self._type_timer = 0.0
                self.state = "narrating_outcome"
            return None

        if self.state == "narrating_outcome":
            if action == Action.CONFIRM:
                self.outcome_visible = len(self.outcome_text)
                self.state = "result"
            return None

        if self.state == "result":
            if action == Action.CONFIRM:
                return "post_event"
            return None

        return None

    def update(self, dt: float):
        chars_per_sec = 30
        if self.state == "scene" and self.scene_visible < len(self.scene_text):
            self._type_timer += dt
            while self._type_timer > 1.0 / chars_per_sec and self.scene_visible < len(self.scene_text):
                self.scene_visible += 1
                self._type_timer -= 1.0 / chars_per_sec

        elif self.state == "narrating_outcome" and self.outcome_visible < len(self.outcome_text):
            self._type_timer += dt
            while self._type_timer > 1.0 / chars_per_sec and self.outcome_visible < len(self.outcome_text):
                self.outcome_visible += 1
                self._type_timer -= 1.0 / chars_per_sec
            if self.outcome_visible >= len(self.outcome_text):
                self.state = "result"

    def draw(self):
        self.buffer.clear()
        t = self.theme
        W = self.buffer.cols
        H = self.buffer.rows

        # Header
        title = self.event.event_type.name.replace("_", " ").title()
        self.buffer.write_animated(1, 1, "\u2501\u2501 " + title + " " + "\u2501" * max(1, W - len(title) - 5),
                                    t.accent_color, "shimmer")
        self.buffer.write(1, 2, f"Wave {self.wave}", t.dim_text_color)

        if self.state in ("scene", "input"):
            # Show scene text
            vis = self.scene_text[:self.scene_visible]
            if vis:
                lines = self._wrap_text(vis, W - 4)
                for i, line in enumerate(lines[:8]):
                    self.buffer.write(2, 4 + i, line, t.text_color)

            if self.state == "scene":
                if self.scene_visible >= len(self.scene_text):
                    self.buffer.write(1, 19, "[Enter] respond", t.dim_text_color)
                else:
                    self.buffer.write(1, 19, "[Enter] skip", t.dim_text_color)
            else:
                # Input state — show choices as hints
                self.buffer.write(1, 13, "What do you do?", t.accent_color)
                for i, choice in enumerate(self.event.choices[:3]):
                    hint = ", ".join(choice.keywords[:3])
                    self.buffer.write(2, 14 + i, f"\u2022 {hint}", t.dim_text_color)

                self.buffer.write(1, 18, "\u2500" * (W - 2), t.border_color)
                max_w = W - 4
                display = self.command_input
                if len(display) > max_w:
                    display = display[-max_w:]
                self.buffer.write(1, 19, "\u276f " + display + "\u258c", t.accent_color)

        elif self.state in ("narrating_outcome", "result"):
            # Show outcome
            vis = self.outcome_text[:self.outcome_visible]
            if vis:
                lines = self._wrap_text(vis, W - 4)
                for i, line in enumerate(lines[:6]):
                    self.buffer.write(2, 4 + i, line, t.text_color)

            # Show effect summary in result state
            if self.state == "result" and self.chosen:
                eff = self.chosen.effect
                y = 12
                if eff.heal_percent > 0:
                    self.buffer.write(2, y, f"\u2764 Team healed {int(eff.heal_percent * 100)}%", (130, 255, 130))
                    y += 1
                if eff.hp_cost_percent > 0:
                    self.buffer.write(2, y, f"\u2661 Leader lost {int(eff.hp_cost_percent * 100)}% HP", (255, 130, 130))
                    y += 1
                if eff.stat_buff:
                    for stat, val in eff.stat_buff.items():
                        self.buffer.write(2, y, f"\u25b2 Leader {stat.upper()} +{val}", (130, 200, 255))
                        y += 1
                if eff.mutagen_reward > 0:
                    self.buffer.write(2, y, f"\u2726 +{eff.mutagen_reward} mutagen", t.accent_color)
                    y += 1
                if eff.mutagen_cost > 0:
                    self.buffer.write(2, y, f"\u25bc -{eff.mutagen_cost} mutagen", t.dim_text_color)

                self.buffer.write(1, 20, "[Enter] continue", t.dim_text_color)
            elif self.state == "narrating_outcome":
                self.buffer.write(1, 20, "[Enter] skip", t.dim_text_color)

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
