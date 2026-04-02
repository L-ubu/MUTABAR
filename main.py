import os
import sys
import time
import threading

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
from game.llm.engine import load_model, generate
from game.llm.prompts import build_battle_prompt
from persistence.config import MutabarConfig
from persistence.database import MutabarDB

APP_SUPPORT = os.path.expanduser("~/Library/Application Support/MUTABAR")
os.makedirs(APP_SUPPORT, exist_ok=True)


class StatusBarDelegate(NSObject):
    """Handles status bar clicks via PyObjC."""

    app = objc.ivar()

    def statusBarClicked_(self, sender):
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
        self.buffer = TextBuffer(cols=43, rows=26)
        self.run_manager = None
        self.current_screen = None
        self._running = True
        self._visible = True
        self._window = None
        self._llm_ready = False
        self._llm_loading = False

    def _setup_status_bar(self):
        """Create macOS status bar icon — clicking M toggles the game window."""
        self._delegate = StatusBarDelegate.alloc().init()
        self._delegate.app = self

        status_bar = NSStatusBar.systemStatusBar()
        self._status_item = status_bar.statusItemWithLength_(
            NSVariableStatusItemLength
        )

        button = self._status_item.button()
        button.setTitle_("M")
        button.setAction_(objc.selector(self._delegate.statusBarClicked_, signature=b"v@:@"))
        button.setTarget_(self._delegate)

        # Right-click menu for Quit only
        menu = NSMenu.alloc().init()
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", "q"
        )
        quit_item.setTarget_(self._delegate)
        menu.addItem_(quit_item)
        # Store menu but don't set it on the status item — we handle left click via action
        self._right_click_menu = menu

    def _position_window_under_status_item(self):
        """Position game window directly below the M status bar icon."""
        import AppKit

        button = self._status_item.button()
        if not button or not button.window():
            return

        btn_win = button.window()
        btn_frame = btn_win.frame()

        # Get the screen the status item is on (use its window's screen, not mainScreen)
        screen = btn_win.screen() or AppKit.NSScreen.mainScreen()
        screen_frame = screen.frame()
        visible_frame = screen.visibleFrame()

        # The button window frame gives us the status item position in global coords
        # x: align left edge of game window with left edge of status item
        x = int(btn_frame.origin.x)
        # y: place game window top edge directly below the menu bar
        # Menu bar bottom = visible_frame top = visibleFrame.origin.y + visibleFrame.size.height
        menu_bar_bottom = visible_frame.origin.y + visible_frame.size.height
        y = int(menu_bar_bottom) - self._window.HEIGHT

        # Clamp to screen bounds so window doesn't go off-screen
        screen_right = int(screen_frame.origin.x + screen_frame.size.width)
        if x + self._window.WIDTH > screen_right:
            x = screen_right - self._window.WIDTH - 5
        screen_left = int(screen_frame.origin.x)
        if x < screen_left:
            x = screen_left + 5

        self._window.set_position(x, y)

    def toggle_visible(self):
        self._visible = not self._visible
        if self._window:
            if self._visible:
                self._position_window_under_status_item()
                self._window.show()
            else:
                self._window.hide()

    def request_quit(self):
        self._running = False

    def _load_llm_async(self):
        """Load LLM model in background thread."""
        model_path = os.path.join(
            os.path.dirname(__file__), "models", "Qwen3-1.7B.Q8_0.gguf"
        )
        if not os.path.exists(model_path):
            return
        self._llm_loading = True
        def _load():
            try:
                load_model(
                    model_path,
                    n_gpu_layers=self.config.llm_n_gpu_layers,
                    n_ctx=self.config.llm_n_ctx,
                    n_threads=4,
                )
                self._llm_ready = True
            except Exception as e:
                print(f"LLM load failed: {e}")
            self._llm_loading = False
        t = threading.Thread(target=_load, daemon=True)
        t.start()

    def generate_battle_narration(self, battle, command, result):
        """Generate LLM narration for a battle turn, or fallback to template."""
        if not self._llm_ready:
            return self._template_narration(battle, command, result)

        try:
            eff = result.player_damage_result
            effectiveness = "normal"
            is_critical = False
            if eff:
                effectiveness = eff.effectiveness or "normal"
                is_critical = eff.is_critical

            prompt = build_battle_prompt(
                attacker=battle.player_active,
                defender=battle.cpu_active,
                command=command,
                damage=result.damage_dealt,
                effectiveness=effectiveness,
                is_critical=is_critical,
            )
            text = generate(
                prompt,
                max_tokens=self.config.llm_max_tokens,
                temperature=self.config.llm_temperature,
            )
            # Take first 2 sentences max and cap length at ~150 chars
            sentences = text.split(".")
            text = ".".join(sentences[:2]).strip()
            if text and not text.endswith("."):
                text += "."
            if len(text) > 150:
                text = text[:147] + "..."
            return text if text else self._template_narration(battle, command, result)
        except Exception:
            return self._template_narration(battle, command, result)

    def _template_narration(self, battle, command, result):
        """Fallback template narration when LLM is unavailable."""
        return (
            f"The {battle.player_active.mutation_type.name} "
            f"{battle.player_active.name} attacks! "
            f"{result.damage_dealt} damage dealt."
        )

    def run(self):
        font_path = os.path.join(
            os.path.dirname(__file__), "assets", "fonts", "Iosevka-Regular.ttf"
        )
        self._window = GameWindow(font_path=font_path)

        # Set up status bar after pygame init (NSApplication already exists from SDL)
        self._setup_status_bar()

        # Position window under the M icon
        self._position_window_under_status_item()

        # Start loading LLM in background
        self._load_llm_async()

        self.current_screen = MainMenuScreen(self.buffer, self.theme)
        last_time = time.time()

        while self._running:
            now = time.time()
            dt = now - last_time
            last_time = now

            events = self._window.tick()
            for event_type, event_data in events:
                if event_type == "quit":
                    self._running = False
                elif event_type == "focus_lost":
                    pass
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
            elif not self._visible:
                # Still tick the clock to keep event loop alive
                pass

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
            self.current_screen = BattleScreen(self.buffer, self.theme, battle, self)
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
                self.current_screen = BattleScreen(self.buffer, self.theme, battle, self)
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
