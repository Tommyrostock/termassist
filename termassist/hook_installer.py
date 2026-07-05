"""Installs the command_not_found_handle(r) shell integration for bash or
zsh, so termassist works invisibly in the background instead of requiring
the user to invoke it explicitly.

The rc-file patching happens directly here in Python rather than by shelling
out to a separate install script: it needs to check the hook block and the
PATH export line independently (and repair whichever is actually missing)
and pick between ~/.bashrc and ~/.zshrc depending on the detected shell -
both are far easier to get right, and to test, with plain file I/O than with
shell script text-processing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from importlib import resources
from pathlib import Path

MARKER_START = "# >>> termassist >>>"
MARKER_END = "# <<< termassist <<<"

# Without this on $PATH, the console-script installed by `pip install -e .`
# (into ~/.local/bin for a user-level/non-root install) can't be found - pip
# already warns about this during install, but the warning is easy to miss,
# and users then hit "termassist: command not found" right after setup.
PATH_EXPORT_LINE = 'export PATH="$HOME/.local/bin:$PATH"'
PATH_MARKER_SUBSTRING = "$HOME/.local/bin"

# Marker comments are identical for both shells on purpose, so uninstalling
# (removing the block between them) works the same way regardless of shell.
_SHELLS: dict[str, dict[str, object]] = {
    "bash": {
        "rc_datei": lambda: Path.home() / ".bashrc",
        "handler_datei": "command_not_found_handle.sh",
    },
    "zsh": {
        "rc_datei": lambda: Path.home() / ".zshrc",
        "handler_datei": "command_not_found_handler.zsh",
    },
}


def erkenne_shell() -> str | None:
    """Best-effort detection of the user's current interactive shell.

    Prefers the parent process' name (the shell that actually invoked this
    command) over $SHELL (the user's configured login shell, which can
    differ from what's currently running, e.g. bash started from within a
    zsh login shell).
    """
    try:
        ergebnis = subprocess.run(
            ["ps", "-p", str(os.getppid()), "-o", "comm="],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        name = ergebnis.stdout.strip().lower()
        if "zsh" in name:
            return "zsh"
        if "bash" in name:
            return "bash"
    except (OSError, subprocess.SubprocessError):
        pass

    shell_env = os.environ.get("SHELL", "").lower()
    if "zsh" in shell_env:
        return "zsh"
    if "bash" in shell_env:
        return "bash"

    return None


def _handler_text(handler_datei: str) -> str:
    pfad = resources.files("termassist") / "shell" / handler_datei
    return pfad.read_text(encoding="utf-8").rstrip("\n")


def _neuer_block(handler_text: str, mit_path_zeile: bool) -> str:
    zeilen = [MARKER_START, "# Bindet termassist in command_not_found_handle(r) ein - siehe README."]
    if mit_path_zeile:
        zeilen.append(PATH_EXPORT_LINE)
    zeilen.append(handler_text)
    zeilen.append(MARKER_END)
    return "\n".join(zeilen)


def install(shell: str | None = None, rc_pfad: Path | None = None) -> int:
    """Idempotently install (or repair) the shell hook.

    The hook block and the PATH export line are checked independently, and
    only whichever of the two is actually missing gets added - so re-running
    this on an older, incomplete installation (e.g. one made before the PATH
    line was introduced) repairs it in place instead of requiring the user to
    manually clean up their rc file first.

    `rc_pfad` lets callers (mainly tests) target a specific file directly
    instead of relying on shell auto-detection and `Path.home()`; `shell`
    still determines which handler script content gets embedded.
    """
    shell = shell or erkenne_shell()

    if rc_pfad is None:
        if shell not in _SHELLS:
            print(
                "Konnte deine Shell nicht sicher erkennen (weder bash noch zsh gefunden).\n"
                "Bitte pruefe manuell, ob du bash (~/.bashrc) oder zsh (~/.zshrc) nutzt, und fuehre\n"
                "z.B. 'termassist --install-hook --shell bash' oder '--shell zsh' erneut aus.",
                file=sys.stderr,
            )
            return 1
        rc_pfad = _SHELLS[shell]["rc_datei"]()

    shell = shell if shell in _SHELLS else "bash"
    handler_text = _handler_text(_SHELLS[shell]["handler_datei"])

    inhalt = rc_pfad.read_text(encoding="utf-8") if rc_pfad.exists() else ""

    block_vorhanden = MARKER_START in inhalt
    path_zeile_vorhanden = PATH_MARKER_SUBSTRING in inhalt

    if block_vorhanden and path_zeile_vorhanden:
        print(f"termassist-Hook ist bereits vollstaendig in {rc_pfad} eingerichtet. Nichts zu tun.")
        return 0

    if not block_vorhanden:
        praefix = inhalt if (not inhalt or inhalt.endswith("\n")) else inhalt + "\n"
        neuer_block = _neuer_block(handler_text, mit_path_zeile=not path_zeile_vorhanden)
        rc_pfad.parent.mkdir(parents=True, exist_ok=True)
        rc_pfad.write_text(praefix + "\n" + neuer_block + "\n", encoding="utf-8")
        print(f"termassist-Hook wurde zu {rc_pfad} hinzugefuegt.")
    else:
        # Block existiert bereits (z.B. aus einer aelteren termassist-Version),
        # aber die PATH-Zeile fehlt - nur diese eine Zeile direkt nach dem
        # Marker-Anfang nachtragen, ohne den Rest des Blocks anzufassen.
        neue_zeilen = []
        for zeile in inhalt.splitlines():
            neue_zeilen.append(zeile)
            if zeile.strip() == MARKER_START:
                neue_zeilen.append(PATH_EXPORT_LINE)
        rc_pfad.write_text("\n".join(neue_zeilen) + "\n", encoding="utf-8")
        print(f"PATH-Zeile in {rc_pfad} ergaenzt (Hook war bereits vorhanden, aber unvollstaendig).")

    print("Bitte 'source ~/.bashrc' bzw. 'source ~/.zshrc' ausfuehren oder das Terminal neu starten.")
    return 0
