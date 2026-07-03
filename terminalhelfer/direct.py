"""Detects when the user already typed a real, existing shell command.

If so, terminalhelfer should skip the matcher/AI entirely and jump straight
to the existing confirm-and-execute flow, instead of showing a suggestion
list for something that isn't even ambiguous.
"""

from __future__ import annotations

import shutil


def ist_direkter_befehl(eingabe: str) -> bool:
    """Return True if the first word of ``eingabe`` is a real, resolvable command."""
    erstes_wort = eingabe.strip().split()[0] if eingabe.strip() else ""
    return shutil.which(erstes_wort) is not None
