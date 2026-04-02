import os
import sys
import random
import threading
import time

import rumps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.window import GameWindow
from game.renderer import TextBuffer
from game.theme import get_theme
from game.input_handler import pygame_event_to_action, Action
from game.screens.main_menu import MainMenuScreen
from game.screens.battle import BattleScreen
from game.screens.lootbox import LootboxScreen
from game.screens.settings import SettingsScreen
from game.battle.engine import Battle, BattleState
from game.battle.cpu_ai import generate_cpu_command
from game.creatures.creature import Creature, CreatureCategory
from game.creatures.types import MutationType
from game.progression.run_manager import RunManager, RunState
from game.progression.unlocks import UnlockManager
from game.progression.lootbox import roll_creature
from persistence.config import MutabarConfig
from persistence.database import MutabarDB

APP_SUPPORT = os.path.expanduser("~/Library/Application Support/MUTABAR")
os.makedirs(APP_SUPPORT, exist_ok=True)


class MutabarApp(rumps.App):
    def __init__(self):
        super().__init__("MUTABAR", title="M")
        self.config = MutabarConfig(os.path.join(APP_SUPPORT, "config.json"))
        self.db = MutabarDB(os.path.join(APP_SUPPORT, "mutabar.db"))
        self.theme = get_theme(self.config.theme)
        self.buffer = TextBuffer(cols=50, rows=35)
        self._game_thread = None
        self._running = False
        self.current_screen = None
        self.run_manager = None

    @rumps.clicked("Toggle Game")
    def toggle_game(self, _):
        if self._running:
            self._running = False
            return
        self._running = True
        self._game_thread = threading.Thread(target=self._run_game, daemon=True)
        self._game_thread.start()

    @rumps.clicked("Quit")
    def quit_app(self, _):
        self._running = False
        self.db.close()
        rumps.quit_application()

    def _run_game(self):
        font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "Iosevka-Regular.ttf")
        window = GameWindow(font_path=font_path)
        window.position_below_menubar()
        window.show()

        self.current_screen = MainMenuScreen(self.buffer, self.theme)
        last_time = time.time()

        while self._running:
            now = time.time()
            dt = now - last_time
            last_time = now

            events = window.tick()
            for event_type, event_data in events:
                if event_type == "quit" or event_type == "focus_lost":
                    self._running = False
                elif event_type == "key":
                    parsed = pygame_event_to_action(event_data)
                    if parsed:
                        action, char = parsed
                        next_screen = self.current_screen.handle_input(action, char)
                        if next_screen:
                            self._switch_screen(next_screen)

            if self.current_screen:
                self.current_screen.update(dt)
                self.current_screen.draw()

            self.buffer.render_to_surface(window.surface, window.font, self.theme.bg_color)
            window.flip()

        window.quit()

    def _switch_screen(self, name: str):
        completed_runs = len(self.db.load_all_runs())
        unlock_mgr = UnlockManager(completed_runs)

        if name == "quit":
            self._running = False
        elif name == "main_menu":
            self.current_screen = MainMenuScreen(self.buffer, self.theme)
        elif name == "run":
            self.run_manager = RunManager(unlock_mgr.unlocked_tiers)
            self.run_manager.start_new_run()
            self.run_manager.roll_starting_team()
            self.run_manager.advance_wave()
            cpu_team = self.run_manager.generate_cpu_team()
            for c in self.run_manager.player_team:
                c.full_heal()
            battle = Battle(self.run_manager.player_team, cpu_team)
            self.current_screen = BattleScreen(self.buffer, self.theme, battle)
        elif name == "post_battle":
            if self.run_manager:
                result = roll_creature(
                    wave=self.run_manager.wave,
                    unlocked_tiers=self.run_manager.unlocked_tiers,
                )
                self.current_screen = LootboxScreen(self.buffer, self.theme, result)
        elif name == "post_lootbox":
            if self.run_manager:
                self.run_manager.advance_wave()
                cpu_team = self.run_manager.generate_cpu_team()
                for c in self.run_manager.player_team:
                    c.full_heal()
                battle = Battle(self.run_manager.player_team, cpu_team)
                self.current_screen = BattleScreen(self.buffer, self.theme, battle)
        elif name == "settings":
            self.current_screen = SettingsScreen(self.buffer, self.theme, self.config.theme)
        elif name == "apply_theme":
            if isinstance(self.current_screen, SettingsScreen) and self.current_screen.changed_theme:
                self.config.theme = self.current_screen.changed_theme
                self.config.save()
                self.theme = get_theme(self.config.theme)
                self.current_screen = MainMenuScreen(self.buffer, self.theme)


if __name__ == "__main__":
    MutabarApp().run()
