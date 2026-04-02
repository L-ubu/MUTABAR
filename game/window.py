import os
import pygame


class GameWindow:
    """Borderless pygame window positioned below the macOS menu bar."""

    WIDTH = 400
    HEIGHT = 500
    FPS = 30

    def __init__(self, font_path: str = None):
        pygame.init()

        self.surface = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.NOFRAME,
        )
        pygame.display.set_caption("MUTABAR")

        # Position below menu bar using SDL2 window API
        self._reposition()

        # Load font
        if font_path and os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, 13)
        else:
            self.font = pygame.font.SysFont("Menlo", 13)

        self.clock = pygame.time.Clock()
        self.visible = True

        # Hide from Dock, then re-activate so we can receive keyboard input
        self._setup_as_menubar_app()

    def _reposition(self):
        """Move window to sit below the menu bar, right-aligned."""
        import AppKit

        screen = AppKit.NSScreen.mainScreen()
        screen_width = int(screen.frame().size.width)
        menu_height = (
            screen.frame().size.height
            - screen.visibleFrame().size.height
            - screen.visibleFrame().origin.y
        )

        x = screen_width - self.WIDTH - 10
        y = int(menu_height)

        from pygame._sdl2.video import Window as SDLWindow
        sdl_window = SDLWindow.from_display_module()
        sdl_window.position = (x, y)

    def _setup_as_menubar_app(self):
        """Hide from Dock but keep keyboard focus for text input."""
        import AppKit

        ns_app = AppKit.NSApplication.sharedApplication()
        ns_app.setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory
        )
        # Re-activate after setting accessory policy so text input works
        ns_app.activateIgnoringOtherApps_(True)
        # Make the pygame window the key window
        for win in ns_app.windows():
            win.makeKeyAndOrderFront_(None)
            break

    def focus(self):
        """Bring window to front and give it keyboard focus."""
        import AppKit

        ns_app = AppKit.NSApplication.sharedApplication()
        ns_app.activateIgnoringOtherApps_(True)
        for win in ns_app.windows():
            win.makeKeyAndOrderFront_(None)
            break

    def show(self):
        self.visible = True
        self.focus()

    def hide(self):
        self.visible = False

    def tick(self) -> list:
        """Process events and return them. Call each frame."""
        self.clock.tick(self.FPS)
        events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append(("quit", None))
            elif event.type == pygame.KEYDOWN:
                events.append(("key", event))
            elif event.type == pygame.ACTIVEEVENT:
                if event.state == 1 and event.gain == 0:
                    events.append(("focus_lost", None))
        return events

    def flip(self):
        pygame.display.flip()

    def quit(self):
        pygame.quit()
