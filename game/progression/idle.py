"""
game/progression/idle.py
Idle arena earnings calculator.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

MAX_OFFLINE_MINUTES = 480


def calculate_idle_rate(creatures: list[dict]) -> float:
    """Calculate total mutagen per minute for idle team."""
    total = 0.0
    for c in creatures:
        base = (c.get("atk", 0) + c.get("defense", 0)) / 10.0
        if c.get("is_shiny"):
            base *= 1.15
        total += base
    return round(total, 2)


def calculate_offline_earnings(creatures: list[dict], last_check_iso: str,
                               now: datetime | None = None) -> int:
    """Calculate offline earnings since last check, capped at MAX_OFFLINE_MINUTES."""
    if not creatures:
        return 0
    if now is None:
        now = datetime.now(timezone.utc)
    last = datetime.fromisoformat(last_check_iso)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    minutes = min((now - last).total_seconds() / 60.0, MAX_OFFLINE_MINUTES)
    return math.floor(calculate_idle_rate(creatures) * max(0, minutes))
