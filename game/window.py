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

        # Load font
        if font_path and os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, 13)
        else:
            self.font = pygame.font.SysFont("Menlo", 13)

        self.clock = pygame.time.Clock()
        self.visible = True

        # Calculate how many rows actually fit
        self.char_h = self.font.get_linesize()
        self.max_rows = self.HEIGHT // self.char_h

        # macOS setup: hide from Dock, position, and focus
        self._setup_macos()

    def _setup_macos(self):
        """Hide from Dock, position below menu bar, grab keyboard focus."""
        import AppKit

        ns_app = AppKit.NSApplication.sharedApplication()

        # Hide from Dock and Cmd+Tab
        ns_app.setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory
        )

        # Find our NSWindow and position it
        screen = AppKit.NSScreen.mainScreen()
        screen_height = screen.frame().size.height
        screen_width = int(screen.frame().size.width)
        menu_height = (
            screen_height
            - screen.visibleFrame().size.height
            - screen.visibleFrame().origin.y
        )

        x = screen_width - self.WIDTH - 10
        # NSWindow y = distance from bottom of screen to bottom of window
        y = screen_height - int(menu_height) - self.HEIGHT

        for win in ns_app.windows():
            frame = AppKit.NSMakeRect(x, y, self.WIDTH, self.HEIGHT)
            win.setFrame_display_(frame, True)
            win.setLevel_(3)  # NSFloatingWindowLevel — stays on top
            win.makeKeyAndOrderFront_(None)
            break

        # Activate so we receive keyboard text input
        ns_app.activateIgnoringOtherApps_(True)

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
