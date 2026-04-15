"""
persistence/config.py
JSON-backed configuration for MUTABAR.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any


_DEFAULTS: dict[str, Any] = {
    "theme": "tokyo_night",
    "llm": {
        "n_gpu_layers": -1,
        "n_ctx": 4096,
        "n_threads": 4,
        "temperature": 0.8,
        "max_tokens": 60,
    },
    "load_side": "right",
    "typewriter_speed": 30,
    "sound_enabled": True,
    "idle_last_check": None,
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Return a new dict that is a deep copy of *base* updated with *override* recursively."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class MutabarConfig:
    """Load, mutate, and persist MUTABAR configuration."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: dict[str, Any] = _deep_merge(_DEFAULTS, {})

        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    loaded = json.load(fh)
                self._data = _deep_merge(_DEFAULTS, loaded)
            except (json.JSONDecodeError, OSError):
                # Fall back to defaults silently
                self._data = _deep_merge(_DEFAULTS, {})

    # ------------------------------------------------------------------
    # theme
    # ------------------------------------------------------------------

    @property
    def theme(self) -> str:
        return self._data["theme"]

    @theme.setter
    def theme(self, value: str) -> None:
        self._data["theme"] = value

    # ------------------------------------------------------------------
    # llm sub-keys
    # ------------------------------------------------------------------

    @property
    def llm_temperature(self) -> float:
        return float(self._data["llm"]["temperature"])

    @llm_temperature.setter
    def llm_temperature(self, value: float) -> None:
        self._data["llm"]["temperature"] = value

    @property
    def llm_max_tokens(self) -> int:
        return int(self._data["llm"]["max_tokens"])

    @llm_max_tokens.setter
    def llm_max_tokens(self, value: int) -> None:
        self._data["llm"]["max_tokens"] = value

    @property
    def llm_n_gpu_layers(self) -> int:
        return int(self._data["llm"]["n_gpu_layers"])

    @llm_n_gpu_layers.setter
    def llm_n_gpu_layers(self, value: int) -> None:
        self._data["llm"]["n_gpu_layers"] = value

    @property
    def llm_n_ctx(self) -> int:
        return int(self._data["llm"]["n_ctx"])

    @llm_n_ctx.setter
    def llm_n_ctx(self, value: int) -> None:
        self._data["llm"]["n_ctx"] = value

    @property
    def typewriter_speed(self) -> int:
        return int(self._data["typewriter_speed"])

    @typewriter_speed.setter
    def typewriter_speed(self, value: int) -> None:
        self._data["typewriter_speed"] = value

    # ------------------------------------------------------------------
    # sound_enabled
    # ------------------------------------------------------------------

    @property
    def sound_enabled(self) -> bool:
        return bool(self._data.get("sound_enabled", True))

    @sound_enabled.setter
    def sound_enabled(self, value: bool) -> None:
        self._data["sound_enabled"] = bool(value)

    # ------------------------------------------------------------------
    # idle_last_check
    # ------------------------------------------------------------------

    @property
    def idle_last_check(self):
        return self._data.get("idle_last_check", None)

    @idle_last_check.setter
    def idle_last_check(self, value) -> None:
        self._data["idle_last_check"] = value

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Write current configuration to the JSON file."""
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
