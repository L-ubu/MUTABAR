import os
import pygame


class GameWindow:
    """Borderless pygame window positioned below the macOS menu bar."""

    PADDING = 6
    FPS = 30

    def __init__(self, cols: int = 36, rows: int = 22, font_path: str = None):
        pygame.init()

        if font_path and os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, 13)
        else:
            self.font = pygame.font.SysFont("Menlo", 13)

        self.char_h = self.font.get_linesize()
        self.char_w = self.font.size("M")[0]
        self.max_rows = rows
        self.max_cols = cols

        self.WIDTH = cols * self.char_w + self.PADDING * 2
        self.HEIGHT = rows * self.char_h + self.PADDING * 2

        self.surface = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.NOFRAME,
        )
        pygame.display.set_caption("MUTABAR")

        self.clock = pygame.time.Clock()
        self.visible = True
        self._ns_window = None

        self._setup_macos()

    def _setup_macos(self):
        """Hide from Dock, configure window with rounded corners and floating level."""
        import AppKit

        ns_app = AppKit.NSApplication.sharedApplication()
        ns_app.setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory
        )

        for win in ns_app.windows():
            self._ns_window = win
            win.setLevel_(3)  # NSFloatingWindowLevel
            win.setOpaque_(False)
            win.setBackgroundColor_(AppKit.NSColor.clearColor())
            win.setHasShadow_(True)

            # Round the content view corners
            content_view = win.contentView()
            content_view.setWantsLayer_(True)
            layer = content_view.layer()
            if layer:
                layer.setCornerRadius_(12.0)
                layer.setMasksToBounds_(True)

            win.makeKeyAndOrderFront_(None)
            break

        ns_app.activateIgnoringOtherApps_(True)

    def set_position(self, x: int, y: int):
        """Position the window at screen coordinates."""
        import AppKit

        if self._ns_window:
            frame = AppKit.NSMakeRect(x, y, self.WIDTH, self.HEIGHT)
            self._ns_window.setFrame_display_(frame, True)

    def focus(self):
        """Bring window to front and give it keyboard focus."""
        import AppKit

        ns_app = AppKit.NSApplication.sharedApplication()
        ns_app.activateIgnoringOtherApps_(True)
        if self._ns_window:
            self._ns_window.makeKeyAndOrderFront_(None)

    def show(self):
        self.visible = True
        if self._ns_window:
            self._ns_window.orderFront_(None)
        self.focus()

    def hide(self):
        self.visible = False
        if self._ns_window:
            self._ns_window.orderOut_(None)

    def tick(self) -> list:
        """Process events and return them."""
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
