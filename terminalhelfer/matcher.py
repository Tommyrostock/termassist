"""Coordinates between the local Ollama AI matcher and the offline fallback."""

from __future__ import annotations

from typing import Any

from . import fallback, ollama_client


def match(
    query: str,
    commands: list[dict[str, Any]] | None = None,
    use_ai: bool = True,
    model: str | None = None,
    debug: bool = False,
) -> tuple[list[dict[str, Any]], str]:
    """Find the best matching commands for a free-text query.

    Tries the local Ollama model first (if enabled and reachable), validates
    its suggestions against the real database to guard against hallucinated
    commands, and falls back to the offline fuzzy matcher whenever the AI
    path is unavailable, fails, times out, or yields zero valid hits.

    Returns a tuple of ``(results, mode)`` where ``mode`` is ``"ki"`` or
    ``"fallback"``, telling the caller which strategy actually produced the
    result.
    """
    if commands is None:
        commands = fallback.load_commands()

    if use_ai and ollama_client.is_available():
        raw_cmds = ollama_client.query_ollama(query, commands, model=model, debug=debug)
        if raw_cmds:
            validated = _validate(raw_cmds, commands)
            if validated:
                return validated[:5], "ki"

    return fallback.fuzzy_search(query, commands, limit=5), "fallback"


def _validate(cmd_strings: list[str], commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter AI-suggested cmd strings down to entries that really exist in the DB.

    This is the safeguard against hallucinated commands: anything the model
    returns that isn't a verbatim match of a "cmd" field in the database is
    silently discarded.
    """
    by_cmd = {entry["cmd"]: entry for entry in commands}
    results = []
    seen = set()
    for cmd in cmd_strings:
        entry = by_cmd.get(cmd)
        if entry and entry["cmd"] not in seen:
            seen.add(entry["cmd"])
            results.append({"cmd": entry["cmd"], "kurz": entry["kurz"]})
    return results
