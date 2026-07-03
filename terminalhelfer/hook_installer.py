"""Runs the bundled install_hook.sh script (see terminalhelfer/shell/) to wire
terminalhelfer into bash's command_not_found_handle, so it works invisibly in
the background instead of requiring the user to invoke it explicitly.
"""

from __future__ import annotations

import subprocess
import sys
from importlib import resources


def install() -> int:
    """Run install_hook.sh and relay its output and exit code to the caller."""
    script = resources.files("terminalhelfer") / "shell" / "install_hook.sh"

    try:
        result = subprocess.run(["bash", str(script)], check=False)
    except FileNotFoundError:
        print(
            "Fehler: 'bash' wurde nicht gefunden. Die Hook-Installation setzt eine Bash-Shell voraus.",
            file=sys.stderr,
        )
        return 1

    return result.returncode
