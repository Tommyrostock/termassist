"""Persistent user settings for termassist (e.g. whether Ollama should be
used by default). Stored as a small JSON file under the user's config
directory, independent of the per-invocation ``--ki`` / ``--no-ai`` flags.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "termassist"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS: dict[str, Any] = {"ki_aktiviert": False}


def load() -> dict[str, Any]:
    """Load persisted settings, falling back to defaults if none exist yet."""
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save(settings: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def is_ki_enabled() -> bool:
    """Whether the user has persistently opted in to Ollama-based refinement."""
    return bool(load().get("ki_aktiviert", False))


def set_ki_enabled(enabled: bool) -> None:
    settings = load()
    settings["ki_aktiviert"] = enabled
    save(settings)
