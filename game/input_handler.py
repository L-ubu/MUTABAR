from enum import Enum, auto


class Action(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    CONFIRM = auto()
    BACK = auto()
    CHAR = auto()
    BACKSPACE = auto()


def pygame_event_to_action(event) -> tuple[Action, str] | None:
    import pygame
    key_map = {
        pygame.K_UP: (Action.UP, ""),
        pygame.K_DOWN: (Action.DOWN, ""),
        pygame.K_LEFT: (Action.LEFT, ""),
        pygame.K_RIGHT: (Action.RIGHT, ""),
        pygame.K_RETURN: (Action.CONFIRM, ""),
        pygame.K_ESCAPE: (Action.BACK, ""),
        pygame.K_BACKSPACE: (Action.BACKSPACE, ""),
    }
    if event.key in key_map:
        return key_map[event.key]
    if event.unicode and event.unicode.isprintable():
        return (Action.CHAR, event.unicode)
    return None
