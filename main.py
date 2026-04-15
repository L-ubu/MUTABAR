import os
import sys
import time
import fcntl
import threading
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import objc
from AppKit import (
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenu,
    NSMenuItem,
    NSRunningApplication,
    NSWorkspace,
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
from game.screens.team_select import TeamSelectScreen, creature_from_db_row
from game.screens.mutadex import MutadexScreen
from game.screens.wave_complete import WaveCompleteScreen
from game.screens.run_over import RunOverScreen
from game.battle.engine import Battle, BattleState
from game.progression.run_manager import RunManager
from game.progression.unlocks import UnlockManager
from game.progression.lootbox import roll_creature
from game.progression.mutabox import open_mutabox
from game.progression.starters import seed_starters_if_needed
from game.progression.mutagen import calculate_wave_mutagen
from game.audio import SoundManager
from game.progression.idle import calculate_offline_earnings
from game.llm.engine import load_model, generate
from game.llm.prompts import build_battle_prompt, build_cpu_battle_prompt
from persistence.config import MutabarConfig
from persistence.database import MutabarDB

APP_SUPPORT = os.path.expanduser("~/Library/Application Support/MUTABAR")
os.makedirs(APP_SUPPORT, exist_ok=True)


def _bundle_dir() -> str:
    """Return the base directory — works for both dev and PyInstaller bundles."""
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


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
        self.buffer = TextBuffer(cols=36, rows=22)
        self.run_manager = None
        self.current_screen = None
        self._running = True
        self._visible = True
        self._window = None
        self._llm_ready = False
        self._llm_loading = False
        self._run_id = None
        self._mutagen_run_total = 0
        self._wave = 0
        self._idle_notification = None
        self._paused_battle_screen = None
        self._idle_tick_timer = 0.0

        self.sound_manager = SoundManager(muted=not self.config.sound_enabled)

        seed_starters_if_needed(self.db)

    def _setup_status_bar(self):
        """Create macOS status bar icon — clicking M toggles the game window."""
        self._delegate = StatusBarDelegate.alloc().init()
        self._delegate.app = self

        status_bar = NSStatusBar.systemStatusBar()
        self._status_item = status_bar.statusItemWithLength_(
            NSVariableStatusItemLength
        )

        button = self._status_item.button()
        icon_path = os.path.join(_bundle_dir(), "assets", "icon_menubar.png")
        if os.path.exists(icon_path):
            from AppKit import NSImage, NSMakeSize
            icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
            icon.setTemplate_(True)
            icon.setSize_(NSMakeSize(18, 18))
            button.setImage_(icon)
            button.setTitle_("")
        else:
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
        """Load LLM model in background thread, downloading if needed."""
        model_dir = os.path.join(APP_SUPPORT, "models")
        model_path = os.path.join(model_dir, "Qwen3-1.7B.Q8_0.gguf")
        self._llm_loading = True

        def _load():
            try:
                from llama_cpp import Llama  # noqa: F401 — verify import works
            except ImportError:
                print("llama-cpp-python not installed — AI narration disabled.")
                print("Install with: pip install 'mutabar[ai]'")
                self._llm_loading = False
                return

            if not os.path.exists(model_path):
                self._download_model(model_dir, model_path)
            if not os.path.exists(model_path):
                self._llm_loading = False
                return
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

    @staticmethod
    def _download_model(model_dir, model_path):
        """Download the Qwen3 model from Hugging Face."""
        import urllib.request
        url = (
            "https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/main/"
            "Qwen3-1.7B-Q8_0.gguf"
        )
        os.makedirs(model_dir, exist_ok=True)
        tmp_path = model_path + ".download"
        print(f"Downloading AI model (~2 GB) ...")
        print(f"  {url}")
        try:
            def _progress(block, block_size, total):
                done = block * block_size
                if total > 0:
                    pct = min(100, done * 100 // total)
                    mb = done // (1024 * 1024)
                    total_mb = total // (1024 * 1024)
                    print(f"\r  {mb}/{total_mb} MB ({pct}%)", end="", flush=True)

            urllib.request.urlretrieve(url, tmp_path, reporthook=_progress)
            print()  # newline after progress
            os.rename(tmp_path, model_path)
            print("Model downloaded successfully.")
        except Exception as e:
            print(f"\nModel download failed: {e}")
            print("AI narration will use template fallback.")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

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
            # Take first 3 sentences max and cap length at ~300 chars
            sentences = text.split(".")
            text = ".".join(sentences[:3]).strip()
            if text and not text.endswith("."):
                text += "."
            if len(text) > 300:
                text = text[:297] + "..."
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

    def generate_cpu_battle_narration(self, battle, result):
        """Generate LLM narration for the CPU's counterattack."""
        if not self._llm_ready:
            return self._template_cpu_narration(battle, result)
        try:
            eff = result.cpu_damage_result
            effectiveness = "normal"
            is_critical = False
            if eff:
                effectiveness = eff.effectiveness or "normal"
                is_critical = eff.is_critical
            prompt = build_cpu_battle_prompt(
                attacker=battle.cpu_active,
                defender=battle.player_active,
                cpu_command=result.cpu_command or "a swift attack",
                damage=result.damage_received,
                effectiveness=effectiveness,
                is_critical=is_critical,
            )
            text = generate(
                prompt,
                max_tokens=self.config.llm_max_tokens,
                temperature=self.config.llm_temperature,
            )
            sentences = text.split(".")
            text = ".".join(sentences[:3]).strip()
            if text and not text.endswith("."):
                text += "."
            if len(text) > 300:
                text = text[:297] + "..."
            return text if text else self._template_cpu_narration(battle, result)
        except Exception:
            return self._template_cpu_narration(battle, result)

    def _template_cpu_narration(self, battle, result):
        """Fallback CPU narration."""
        cpu = battle.cpu_active
        return (
            f"The {cpu.mutation_type.name} {cpu.name} strikes back! "
            f"{result.damage_received} damage."
        )

    def run(self):
        font_path = os.path.join(
            _bundle_dir(), "assets", "fonts", "Iosevka-Regular.ttf"
        )
        self._window = GameWindow(cols=self.buffer.cols, rows=self.buffer.rows, font_path=font_path)

        # Set up status bar after pygame init (NSApplication already exists from SDL)
        self._setup_status_bar()

        # Defer positioning — status item window isn't ready yet at startup
        self._needs_initial_position = True

        # Start loading LLM in background
        self._load_llm_async()

        # Collect idle earnings
        idle_team = self.db.get_idle_team()
        last_check = self.config.idle_last_check
        if last_check and idle_team:
            earned = calculate_offline_earnings(idle_team, last_check)
            if earned > 0:
                self.db.add_mutagen(earned)
                self._idle_notification = earned
            self.config.idle_last_check = datetime.now(timezone.utc).isoformat()
            self.config.save()
        elif not last_check:
            self.config.idle_last_check = datetime.now(timezone.utc).isoformat()
            self.config.save()

        notif = self._idle_notification
        self._idle_notification = None
        self.current_screen = MainMenuScreen(self.buffer, self.theme, idle_notification=notif)
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

            # Retry initial positioning once the status item window is ready
            if self._needs_initial_position:
                button = self._status_item.button()
                if button and button.window():
                    self._position_window_under_status_item()
                    self._needs_initial_position = False

            if self._visible and self.current_screen:
                self.current_screen.update(dt)
                self.current_screen.draw()
                if getattr(self.current_screen, 'needs_animation', False):
                    import time as time_mod
                    self.buffer.render_to_surface_animated(
                        self._window.surface, self._window.font, self.theme.bg_color, time_mod.time()
                    )
                else:
                    self.buffer.render_to_surface(
                        self._window.surface, self._window.font, self.theme.bg_color
                    )
                self._window.flip()
            elif not self._visible:
                # Still tick the clock to keep event loop alive
                pass

            # Periodic idle earnings (every 60 seconds)
            self._idle_tick_timer += dt
            if self._idle_tick_timer >= 60.0:
                self._idle_tick_timer = 0.0
                idle_team = self.db.get_idle_team()
                if idle_team:
                    earned = calculate_offline_earnings(
                        idle_team,
                        self.config.idle_last_check or datetime.now(timezone.utc).isoformat(),
                    )
                    if earned > 0:
                        self.db.add_mutagen(earned)
                    self.config.idle_last_check = datetime.now(timezone.utc).isoformat()
                    self.config.save()

        self._window.quit()
        # Save idle timestamp on exit
        self.config.idle_last_check = datetime.now(timezone.utc).isoformat()
        self.config.save()
        self.db.close()

    def _switch_screen(self, name: str):
        if name == "quit":
            self._running = False

        elif name == "hide":
            self._visible = False
            if self._window:
                self._window.hide()

        elif name == "main_menu":
            # Save sound toggle if coming from settings
            if isinstance(self.current_screen, SettingsScreen) and self.current_screen.sound_toggled:
                self.config.sound_enabled = self.current_screen.sound_enabled
                self.sound_manager.muted = not self.config.sound_enabled
                self.config.save()
            # Preserve battle state if escaping mid-battle
            if isinstance(self.current_screen, BattleScreen) and self.run_manager:
                self._paused_battle_screen = self.current_screen
            else:
                self._paused_battle_screen = None
                self.run_manager = None
                self._run_id = None
            notif = self._idle_notification
            self._idle_notification = None
            has_run = self._paused_battle_screen is not None
            self.current_screen = MainMenuScreen(self.buffer, self.theme, idle_notification=notif, has_active_run=has_run)

        elif name == "continue_run":
            if self._paused_battle_screen:
                self.current_screen = self._paused_battle_screen
                self._paused_battle_screen = None

        elif name == "run":
            self.current_screen = TeamSelectScreen(self.buffer, self.theme, self.db)

        elif name == "start_run":
            if isinstance(self.current_screen, TeamSelectScreen):
                team = self.current_screen.selected_team
                if not team:
                    return
                self._run_id = self.db.start_run()
                self._mutagen_run_total = 0
                self._wave = 0
                completed_runs = len(self.db.load_all_runs())
                unlock_mgr = UnlockManager(completed_runs)
                self.run_manager = RunManager(unlock_mgr.unlocked_tiers)
                self.run_manager.start_new_run()
                self.run_manager.player_team = team
                self.run_manager.advance_wave()
                self._wave = self.run_manager.wave
                cpu_team = self.run_manager.generate_cpu_team()
                battle = Battle(self.run_manager.player_team, cpu_team)
                self.current_screen = BattleScreen(self.buffer, self.theme, battle, self,
                                                    is_boss=self.run_manager.is_boss_wave)

        elif name == "post_battle":
            # Route based on battle outcome
            if isinstance(self.current_screen, BattleScreen):
                if self.current_screen.battle.state == BattleState.PLAYER_WIN:
                    self._switch_screen("wave_complete")
                else:
                    self._switch_screen("run_over")
            else:
                self._switch_screen("wave_complete")

        elif name == "wave_complete":
            if self.run_manager:
                wave_mutagen = calculate_wave_mutagen(self._wave)
                self._mutagen_run_total += wave_mutagen
                self.current_screen = WaveCompleteScreen(
                    self.buffer, self.theme,
                    wave=self._wave,
                    mutagen_this_wave=wave_mutagen,
                    mutagen_run_total=self._mutagen_run_total,
                )

        elif name == "next_wave":
            if self.run_manager:
                # Roll for random event before advancing
                from game.events.resolver import roll_for_event
                event = roll_for_event(self._wave)
                if event:
                    self._pending_event = event
                    self._switch_screen("show_event")
                    return
                self._do_advance_wave()

        elif name == "show_event":
            if hasattr(self, '_pending_event') and self._pending_event:
                from game.screens.event import EventScreen
                self.current_screen = EventScreen(
                    self.buffer, self.theme, self._pending_event,
                    self._wave, self.run_manager.player_team, self,
                )

        elif name == "post_event":
            if hasattr(self, '_pending_event'):
                self._pending_event = None
            self._do_advance_wave()

        elif name == "run_over":
            self._paused_battle_screen = None
            if self.run_manager and self._run_id:
                self.current_screen = RunOverScreen(
                    self.buffer, self.theme,
                    waves_survived=self._wave,
                    mutagen_earned=self._mutagen_run_total,
                    run_id=self._run_id,
                    db=self.db,
                )

        elif name == "mutadex":
            self.current_screen = MutadexScreen(self.buffer, self.theme, self.db)

        elif name == "open_mutabox":
            tier = None
            if isinstance(self.current_screen, MutadexScreen) and self.current_screen.pending_mutabox_tier:
                tier = self.current_screen.pending_mutabox_tier
            elif hasattr(self, '_last_mutabox_tier') and self._last_mutabox_tier:
                tier = self._last_mutabox_tier
            if tier:
                result = open_mutabox(tier)
                self._last_mutabox_result = result
                self._last_mutabox_tier = tier
                self.current_screen = LootboxScreen(self.buffer, self.theme, result, mutabox_tier=tier)

        elif name == "post_lootbox":
            import json
            wants_reroll = False
            tier = getattr(self, '_last_mutabox_tier', None)
            if isinstance(self.current_screen, LootboxScreen) and self.current_screen.wants_reroll:
                wants_reroll = True
            # Save the creature from the last mutabox roll to DB
            if hasattr(self, '_last_mutabox_result') and self._last_mutabox_result:
                result = self._last_mutabox_result
                tmpl = result.template
                existing_count = self.db.get_species_count(tmpl.name)
                if existing_count > 0 and not result.is_shiny:
                    # Duplicate: boost existing creature stats
                    self.db.boost_creature_stats(tmpl.name, hp_boost=2, atk_boost=1, def_boost=1)
                else:
                    self.db.save_creature(
                        name=tmpl.name, species=tmpl.name,
                        category=tmpl.category.value.upper(),
                        mutation_type="FIRE",
                        base_hp=tmpl.base_hp, base_atk=tmpl.base_atk, base_def=tmpl.base_def,
                        traits_json=json.dumps([t.name for t in tmpl.traits]),
                        is_shiny=int(result.is_shiny),
                    )
                self._last_mutabox_result = None
            # Reroll if requested and affordable
            if wants_reroll and tier and self.db.get_mutagen() >= tier.cost:
                self.db.spend_mutagen(tier.cost)
                self._switch_screen("open_mutabox")
                return
            # Return to mutadex on shop tab
            screen = MutadexScreen(self.buffer, self.theme, self.db)
            screen.active_tab = 1  # Shop tab
            self.current_screen = screen

        elif name == "settings":
            self.current_screen = SettingsScreen(self.buffer, self.theme, self.config.theme,
                                                 sound_enabled=self.config.sound_enabled)

        elif name == "apply_theme":
            if isinstance(self.current_screen, SettingsScreen):
                # Handle sound toggle
                if self.current_screen.sound_toggled:
                    self.config.sound_enabled = self.current_screen.sound_enabled
                    self.sound_manager.muted = not self.config.sound_enabled
                    self.config.save()
                # Handle theme change
                if self.current_screen.changed_theme:
                    self.config.theme = self.current_screen.changed_theme
                    self.config.save()
                    self.theme = get_theme(self.config.theme)
                self.current_screen = MainMenuScreen(self.buffer, self.theme)

    def _do_advance_wave(self):
        """Advance to the next wave and start a battle."""
        self.run_manager.advance_wave()
        self._wave = self.run_manager.wave
        cpu_team = self.run_manager.generate_cpu_team()
        for c in self.run_manager.player_team:
            c.full_heal()
        battle = Battle(self.run_manager.player_team, cpu_team)
        self.current_screen = BattleScreen(self.buffer, self.theme, battle, self,
                                            is_boss=self.run_manager.is_boss_wave)

    def generate_event_scene(self, event, wave, player_team):
        """Generate LLM narration for a random event scene."""
        if not self._llm_ready:
            return event.description_template
        try:
            from game.llm.prompts import build_event_scene_prompt
            prompt = build_event_scene_prompt(event, wave, player_team)
            text = generate(prompt, max_tokens=self.config.llm_max_tokens,
                           temperature=self.config.llm_temperature)
            sentences = text.split(".")
            text = ".".join(sentences[:4]).strip()
            if text and not text.endswith("."):
                text += "."
            return text if text else event.description_template
        except Exception:
            return event.description_template

    def generate_event_outcome(self, event, player_action, choice):
        """Generate LLM narration for event outcome."""
        if not self._llm_ready:
            return choice.outcome_template
        try:
            from game.llm.prompts import build_event_outcome_prompt
            prompt = build_event_outcome_prompt(event, player_action, choice)
            text = generate(prompt, max_tokens=self.config.llm_max_tokens,
                           temperature=self.config.llm_temperature)
            sentences = text.split(".")
            text = ".".join(sentences[:3]).strip()
            if text and not text.endswith("."):
                text += "."
            return text if text else choice.outcome_template
        except Exception:
            return choice.outcome_template


_lock_fd = None


def _ensure_single_instance():
    """If MUTABAR is already running, activate it and exit."""
    global _lock_fd
    lock_path = os.path.join(APP_SUPPORT, ".mutabar.lock")
    _lock_fd = open(lock_path, "w")
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
    except IOError:
        # Already running — try to bring the existing window to front
        _lock_fd.close()
        _lock_fd = None
        _activate_existing()
        sys.exit(0)


def _activate_existing():
    """Bring the already-running MUTABAR instance to the foreground."""
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        bid = app.bundleIdentifier()
        if bid and "mutabar" in bid.lower():
            app.activateWithOptions_(0)
            return
    # Fallback: find by process name
    pid_path = os.path.join(APP_SUPPORT, ".mutabar.lock")
    try:
        with open(pid_path) as f:
            pid = int(f.read().strip())
        app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        if app:
            app.activateWithOptions_(0)
    except Exception:
        pass


def main():
    _ensure_single_instance()
    MutabarApp().run()


if __name__ == "__main__":
    main()
