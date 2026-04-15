"""
game/audio.py
Sound manager for MUTABAR — generates tones programmatically.
"""

from __future__ import annotations

import math
import array

SAMPLE_RATE = 22050


def generate_tone(freq: float, duration_ms: int, volume: float = 0.3) -> bytes:
    """Generate raw PCM bytes for a sine wave tone (16-bit mono)."""
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    buf = array.array("h")  # signed short
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        sample = int(volume * 32767 * math.sin(2 * math.pi * freq * t))
        buf.append(max(-32767, min(32767, sample)))
    return buf.tobytes()


def _make_sound(freq: float, duration_ms: int):
    """Create a pygame Sound from generated tone data."""
    import pygame
    raw = generate_tone(freq, duration_ms)
    return pygame.mixer.Sound(buffer=raw)


class SoundManager:
    """Plays rarity-specific beep sequences. Respects mute toggle."""

    def __init__(self, muted: bool = False):
        self.muted = muted
        self._initialized = False
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self._initialized = True
        except Exception:
            pass

    def play_rarity(self, rarity_name: str) -> None:
        if self.muted or not self._initialized:
            return
        try:
            sequences = {
                "COMMON": [(440, 100)],
                "UNCOMMON": [(440, 100), (440, 100)],
                "RARE": [(440, 100), (440, 100), (440, 100)],
                "EPIC": [(440, 100), (523, 100), (659, 100)],
                "LEGENDARY": [(440, 50), (440, 50), (440, 50), (440, 50), (440, 50)],
            }
            seq = sequences.get(rarity_name, [(440, 100)])
            import threading

            def _play():
                import time
                for freq, dur in seq:
                    sound = _make_sound(freq, dur)
                    sound.play()
                    time.sleep((dur + 50) / 1000.0)
            threading.Thread(target=_play, daemon=True).start()
        except Exception:
            pass
