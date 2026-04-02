import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import objc
from AppKit import (
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenu,
    NSMenuItem,
)
from Foundation import NSObject

from game.window import GameWindow
from game.renderer import TextBuffer
from game.theme import get_theme
from game.input_handler import pygame_event_to_action
from game.screens.main_menu import MainMenuScreen
from game.screens.battle import BattleScreen
from game.screens.lootbox import LootboxScreen
from game.screens.settings import SettingsScreen
from game.battle.engine import Battle
from game.progression.run_manager import RunManager
from game.progression.unlocks import UnlockManager
from game.progression.lootbox import roll_creature
from persistence.config import MutabarConfig
from persistence.database import MutabarDB

APP_SUPPORT = os.path.expanduser("~/Library/Application Support/MUTABAR")
os.makedirs(APP_SUPPORT, exist_ok=True)


class StatusBarDelegate(NSObject):
    """Handles status bar menu clicks via PyObjC."""

    app = objc.ivar()

    def toggleGame_(self, sender):
        if self.app:
            self.app.toggle_visible()

    def quitApp_(self, sender):
        if self.app:
            self.app.request_quit()


class MutabarApp:
    def __init__(self):
        self.config = MutabarConfig(os.path.join(APP_SUPPORT, "config.json"))
        self.db = MutabarDB(os.path.join(APP_SUPPORT, "mutabar.db"))
        self.theme = get_theme(self.config.theme)
        self.buffer = TextBuffer(cols=50, rows=35)
        self.run_manager = None
        self.current_screen = None
        self._running = True
        self._visible = True
        self._window = None

    def _setup_status_bar(self):
        """Create macOS status bar icon with Toggle/Quit menu."""
        self._delegate = StatusBarDelegate.alloc().init()
        self._delegate.app = self

        status_bar = NSStatusBar.systemStatusBar()
        self._status_item = status_bar.statusItemWithLength_(
            NSVariableStatusItemLength
        )
        self._status_item.setTitle_("M")

        menu = NSMenu.alloc().init()

        toggle_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Toggle Game", "toggleGame:", ""
        )
        toggle_item.setTarget_(self._delegate)
        menu.addItem_(toggle_item)

        menu.addItem_(NSMenuItem.separatorItem())

        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", "q"
        )
        quit_item.setTarget_(self._delegate)
        menu.addItem_(quit_item)

        self._status_item.setMenu_(menu)

    def toggle_visible(self):
        self._visible = not self._visible

    def request_quit(self):
        self._running = False

    def run(self):
        # Initialize pygame + window on main thread (macOS requirement)
        font_path = os.path.join(
            os.path.dirname(__file__), "assets", "fonts", "Iosevka-Regular.ttf"
        )
        self._window = GameWindow(font_path=font_path)

        # Set up status bar after pygame init (NSApplication already exists from SDL)
        self._setup_status_bar()

        self.current_screen = MainMenuScreen(self.buffer, self.theme)
        last_time = time.time()

        while self._running:
            now = time.time()
            dt = now - last_time
            last_time = now

            # pygame.event.get() pumps the macOS event loop internally,
            # keeping the status bar menu responsive
            events = self._window.tick()
            for event_type, event_data in events:
                if event_type == "quit":
                    self._running = False
                elif event_type == "focus_lost":
                    pass  # keep running, user can toggle via status bar
                elif event_type == "key":
                    if self._visible:
                        parsed = pygame_event_to_action(event_data)
                        if parsed:
                            action, char = parsed
                            result = self.current_screen.handle_input(action, char)
                            if result:
                                self._switch_screen(result)

            if self._visible and self.current_screen:
                self.current_screen.update(dt)
                self.current_screen.draw()
                self.buffer.render_to_surface(
                    self._window.surface, self._window.font, self.theme.bg_color
                )
                self._window.flip()

        self._window.quit()
        self.db.close()

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
