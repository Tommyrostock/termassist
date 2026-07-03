"""Offline fuzzy search fallback for termassist.

Matches free-text user input against the curated command database without any
AI involved. Prefers rapidfuzz for speed and quality, but falls back to the
stdlib difflib if rapidfuzz is not installed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from rapidfuzz import fuzz

    _HAVE_RAPIDFUZZ = True
except ImportError:  # pragma: no cover - exercised only without rapidfuzz installed
    import difflib

    _HAVE_RAPIDFUZZ = False


DEFAULT_DB_PATH = Path(__file__).parent / "data" / "commands.json"

# Below this score, a match is considered noise rather than a real suggestion.
# Genuine queries (even single keywords) reliably score 50+ against their
# intended entry; unrelated gibberish tops out around 40-45 (see fallback
# scoring notes). This lets fuzzy_search return an empty list for input that
# doesn't match anything - important for command_not_found_handle, which uses
# an empty result to decide whether to fall back to the plain shell error.
MIN_RELEVANCE_SCORE = 45.0


def load_commands(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load the curated command database from disk."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _difflib_token_set_ratio(a: str, b: str) -> float:
    """Reimplementation of rapidfuzz's token_set_ratio using only difflib.

    Compares strings by shared vs. differing whitespace-separated tokens
    instead of raw characters, so a short candidate like "date" doesn't score
    unreasonably high just because it happens to be a substring of "datei".
    """
    tokens_a, tokens_b = set(a.split()), set(b.split())
    common = tokens_a & tokens_b
    sorted_common = " ".join(sorted(common))
    combined_a = (sorted_common + " " + " ".join(sorted(tokens_a - tokens_b))).strip()
    combined_b = (sorted_common + " " + " ".join(sorted(tokens_b - tokens_a))).strip()

    ratios = [
        difflib.SequenceMatcher(None, sorted_common, combined_a).ratio(),
        difflib.SequenceMatcher(None, sorted_common, combined_b).ratio(),
        difflib.SequenceMatcher(None, combined_a, combined_b).ratio(),
    ]
    return max(ratios) * 100


def _similarity(a: str, b: str) -> float:
    """Return a similarity score between 0 and 100 for two strings.

    Uses token-set based matching rather than raw-character ratios (like
    rapidfuzz's WRatio would): otherwise a short keyword such as "date" scores
    unreasonably high against a query containing "datei", since its few
    characters are trivially found as a substring.
    """
    a, b = a.lower().strip(), b.lower().strip()
    if not a or not b:
        return 0.0
    if _HAVE_RAPIDFUZZ:
        return fuzz.token_set_ratio(a, b)
    return _difflib_token_set_ratio(a, b)


def _best_score(query: str, entry: dict[str, Any]) -> float:
    """Return the best similarity score between the query and an entry's keywords/kurz."""
    candidates = [*entry.get("keywords", []), entry.get("kurz", "")]
    return max((_similarity(query, candidate) for candidate in candidates), default=0.0)


def fuzzy_search(
    query: str,
    commands: list[dict[str, Any]] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find the best matching commands for a free-text query.

    Returns a list of ``{"cmd": ..., "kurz": ...}`` dicts, best match first.
    """
    if commands is None:
        commands = load_commands()

    query = (query or "").strip()
    if not query:
        return []

    scored = [(entry, _best_score(query, entry)) for entry in commands]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    results = []
    for entry, score in scored[:limit]:
        if score < MIN_RELEVANCE_SCORE:
            continue
        results.append({"cmd": entry["cmd"], "kurz": entry["kurz"]})
    return results
