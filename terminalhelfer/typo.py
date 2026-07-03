"""Detects whether an unrecognized single word is likely a typo of a real,
installed command (e.g. "sl" for "ls", "gerp" for "grep") rather than a
natural-language request (e.g. "firewall ausschalten").

This matters for the command_not_found_handle integration: Ubuntu's own
apt-based command-not-found tool is actually quite good at raw binary-name
spelling correction (it has its own package database for that), while
terminalhelfer's curated database is optimized for intent, not spelling
correction. So when the input looks like a plain typo of some installed
binary, terminalhelfer intentionally steps aside and lets apt's logic take
over instead of guessing.

Multi-word input is never considered a typo case here - see
command_not_found_handle.sh for how the two signals are combined.
"""

from __future__ import annotations

import os
from functools import lru_cache

try:
    from rapidfuzz.distance import DamerauLevenshtein

    def _edit_distance(a: str, b: str) -> int:
        return DamerauLevenshtein.distance(a, b)

except ImportError:  # pragma: no cover - exercised only without rapidfuzz installed

    def _edit_distance(a: str, b: str) -> int:
        """Plain Levenshtein distance (no transposition) as a fallback."""
        if a == b:
            return 0
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, start=1):
            curr = [i] + [0] * len(b)
            for j, cb in enumerate(b, start=1):
                curr[j] = min(
                    prev[j] + 1,
                    curr[j - 1] + 1,
                    prev[j - 1] + (ca != cb),
                )
            prev = curr
        return prev[-1]


# Wie viele Buchstaben duerfen abweichen, damit es noch als Tippfehler zaehlt?
# Kurze Woerter verzeihen weniger, sonst waeren fast alle 2-3 Buchstaben langen
# Woerter "nah dran" an irgendeinem der vielen kurzen Systembefehle.
def _max_erlaubte_distanz(wortlaenge: int) -> int:
    if wortlaenge <= 5:
        return 1
    return 2


@lru_cache(maxsize=1)
def _verfuegbare_befehlsnamen() -> frozenset[str]:
    """Collect the names of all executables found on $PATH."""
    namen = set()
    for verzeichnis in os.environ.get("PATH", "").split(os.pathsep):
        try:
            with os.scandir(verzeichnis) as eintraege:
                for eintrag in eintraege:
                    try:
                        if eintrag.is_file() and os.access(eintrag.path, os.X_OK):
                            namen.add(eintrag.name)
                    except OSError:
                        continue
        except OSError:
            continue
    return frozenset(namen)


def ist_wahrscheinlich_tippfehler(eingabe: str) -> bool:
    """True if `eingabe` is a single word that closely resembles a real,
    installed command - i.e. more likely a typo ("sl" -> "ls") than a
    natural-language request.
    """
    eingabe = eingabe.strip()
    if not eingabe or " " in eingabe:
        return False  # mehrwortige Eingaben sind so gut wie nie ein binaer-tippfehler

    max_distanz = _max_erlaubte_distanz(len(eingabe))
    eingabe_klein = eingabe.lower()

    for name in _verfuegbare_befehlsnamen():
        if name == eingabe:
            continue  # waere schon vorher als gueltiger Befehl erkannt worden
        if abs(len(name) - len(eingabe)) > max_distanz:
            continue
        if _edit_distance(eingabe_klein, name.lower()) <= max_distanz:
            return True

    return False
