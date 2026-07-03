"""Client for talking to a local Ollama instance for AI-assisted matching.

This module never invents commands itself - it only asks the model to pick
and rank entries from the curated database. Callers must still validate the
returned ``cmd`` values against the real database before trusting them.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from .fallback import fuzzy_search

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:1.5b-instruct"
AVAILABILITY_TIMEOUT = 1.5
REQUEST_TIMEOUT = 20

# Above this many DB entries, pre-filter with the offline fuzzy matcher before
# building the prompt, to keep the context sent to the model small.
PREFILTER_THRESHOLD = 40
PREFILTER_LIMIT = 30


def get_model_name(override: str | None = None) -> str:
    """Resolve the Ollama model name from CLI flag, env var, or default."""
    return override or os.environ.get("TERMINALHELFER_MODEL") or DEFAULT_MODEL


def is_available(host: str = DEFAULT_HOST, timeout: float = AVAILABILITY_TIMEOUT) -> bool:
    """Check whether a local Ollama instance is reachable."""
    try:
        response = requests.get(f"{host}/api/tags", timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _build_prompt(query: str, commands: list[dict[str, Any]]) -> str:
    context = json.dumps(
        [{"cmd": c["cmd"], "kurz": c["kurz"]} for c in commands],
        ensure_ascii=False,
    )
    return (
        "Du hilfst einem deutschsprachigen Linux-Einsteiger, den richtigen Terminal-Befehl zu finden.\n"
        f'Nutzeranfrage: "{query}"\n\n'
        "Waehle ausschliesslich aus der folgenden Befehlsliste die am besten passenden Befehle aus, "
        'anhand des exakten "cmd"-Feldes. Sortiere nach Relevanz, das beste Ergebnis zuerst. '
        "Gib maximal 5 Eintraege zurueck. Erfinde niemals eigene Befehle, "
        "die nicht woertlich in der Liste stehen.\n\n"
        f"Befehlsliste (JSON):\n{context}\n\n"
        'Antworte ausschliesslich mit einem JSON-Objekt der Form {"befehle": ["cmd1", "cmd2", ...]}.'
    )


def query_ollama(
    query: str,
    commands: list[dict[str, Any]],
    model: str | None = None,
    host: str = DEFAULT_HOST,
    timeout: float = REQUEST_TIMEOUT,
    debug: bool = False,
) -> list[str] | None:
    """Ask a local Ollama model to rank matching commands.

    Returns a list of ``cmd`` strings in ranked order, or ``None`` if the
    request failed, timed out, or produced no usable response. The caller is
    responsible for validating the returned commands against the real
    database (protection against hallucination).
    """
    candidates = commands
    if len(commands) > PREFILTER_THRESHOLD:
        prefiltered = fuzzy_search(query, commands, limit=PREFILTER_LIMIT)
        prefiltered_cmds = {entry["cmd"] for entry in prefiltered}
        candidates = [c for c in commands if c["cmd"] in prefiltered_cmds] or commands

    payload = {
        "model": get_model_name(model),
        "prompt": _build_prompt(query, candidates),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(f"{host}/api/generate", json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        if debug:
            print(f"[debug] Ollama-Anfrage fehlgeschlagen: {exc}")
        return None

    try:
        body = response.json()
        raw = body["response"]
        parsed = json.loads(raw)
    except (KeyError, ValueError) as exc:
        if debug:
            print(f"[debug] Ollama-Antwort konnte nicht geparst werden: {exc}")
        return None

    result = parsed.get("befehle") if isinstance(parsed, dict) else parsed
    if not isinstance(result, list):
        if debug:
            print(f"[debug] Unerwartetes Antwortformat von Ollama: {parsed!r}")
        return None

    return [item for item in result if isinstance(item, str)]
