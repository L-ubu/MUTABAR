import os
import pygame


class GameWindow:
    """Borderless pygame window that acts as a menu bar dropdown."""

    WIDTH = 400
    HEIGHT = 500
    FPS = 30

    def __init__(self, font_path: str = None):
        pygame.init()

        # Hide from Dock and Cmd+Tab
        import AppKit
        AppKit.NSApplication.sharedApplication().setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory
        )

        # Position below menu bar before creating the window
        self._position_env()

        self.surface = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.NOFRAME,
        )
        pygame.display.set_caption("MUTABAR")

        if font_path and os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, 13)
        else:
            self.font = pygame.font.SysFont("Menlo", 13)

        self.clock = pygame.time.Clock()
        self.visible = True

    def _position_env(self, x: int = None):
        """Set SDL_VIDEO_WINDOW_POS to place window below the macOS menu bar."""
        import AppKit
        screen = AppKit.NSScreen.mainScreen()
        menu_height = (
            screen.frame().size.height
            - screen.visibleFrame().size.height
            - screen.visibleFrame().origin.y
        )
        if x is None:
            screen_width = int(screen.frame().size.width)
            x = screen_width - self.WIDTH - 10
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{x},{int(menu_height)}"

    def show(self):
        self.visible = True

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
