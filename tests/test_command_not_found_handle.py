"""Tests for command_not_found_handle.sh: verifies the reversed priority
(terminalhelfer is always asked first; apt's own "did you mean" logic is
only consulted afterwards, and never at all for multi-word input) using a
fake terminalhelfer stub whose exit code we fully control.
"""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SHELL_SCRIPT = Path(__file__).resolve().parent.parent / "terminalhelfer" / "shell" / "command_not_found_handle.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="benoetigt eine bash-Shell")


def _make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_hook(tmp_path, thf_exit_code, *woerter, apt_ausgabe=None):
    """Simulate bash calling command_not_found_handle with `woerter` as the
    words of an unrecognized command line, with a fake terminalhelfer that
    always exits with `thf_exit_code`, and (optionally) a fake apt tool.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _make_executable(
        bin_dir / "terminalhelfer",
        f"#!/usr/bin/env bash\necho \"THF_CALLED_WITH:$*\"\nexit {thf_exit_code}\n",
    )

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

    if apt_ausgabe is not None:
        apt_tool = tmp_path / "fake_apt_tool"
        _make_executable(apt_tool, f"#!/usr/bin/env bash\necho \"{apt_ausgabe}\"\nexit 127\n")
        env["TERMINALHELFER_APT_TOOL_UEBERSCHREIBEN"] = str(apt_tool)

    skript = f'source "{SHELL_SCRIPT.as_posix()}"\ncommand_not_found_handle "$@"\necho "HOOK_EXIT:$?"\n'
    return subprocess.run(
        ["bash", "-c", skript, "_", *woerter],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def test_multiword_input_is_passed_to_terminalhelfer_as_one_query(tmp_path):
    result = _run_hook(tmp_path, 0, "alle", "dateien", "loeschen")

    assert "THF_CALLED_WITH:alle dateien loeschen" in result.stdout
    assert "HOOK_EXIT:0" in result.stdout


def test_multiword_input_never_triggers_apt_guess_when_nothing_found(tmp_path):
    result = _run_hook(
        tmp_path,
        1,
        "alle",
        "dateien",
        "loeschen",
        apt_ausgabe="sudo apt install allec-vermutung",
    )

    # terminalhelfer wurde befragt, hat aber nichts gefunden (exit 1). Weil
    # die Eingabe mehrwortig ist, darf die apt-Vermutung gar nicht erst
    # aufgerufen werden - ihre Ausgabe darf also nirgends auftauchen.
    assert "THF_CALLED_WITH:alle dateien loeschen" in result.stdout
    assert "allec-vermutung" not in result.stdout
    assert "allec-vermutung" not in result.stderr
    assert "HOOK_EXIT:127" in result.stdout


def test_single_word_typo_falls_through_to_apt_guess(tmp_path):
    # terminalhelfer signalisiert per Exit-Code 2: "sl" sieht nach einem
    # Tippfehler eines echten Programms aus, kein Datenbank-Fall.
    result = _run_hook(tmp_path, 2, "sl", apt_ausgabe="sudo apt install ls-vermutung")

    assert "THF_CALLED_WITH:sl" in result.stdout
    assert "ls-vermutung" in result.stderr
    assert "HOOK_EXIT:127" in result.stdout


def test_single_word_nothing_found_still_tries_apt_guess(tmp_path):
    result = _run_hook(tmp_path, 1, "xyzzy", apt_ausgabe="sudo apt install xyzzy-paket-install")

    assert "THF_CALLED_WITH:xyzzy" in result.stdout
    assert "xyzzy-paket-install" in result.stderr
    assert "HOOK_EXIT:127" in result.stdout


def test_plain_not_found_message_when_neither_finds_anything(tmp_path):
    result = _run_hook(tmp_path, 1, "xyzzy")  # kein apt-Tool ueberschrieben -> keins gefunden

    assert "xyzzy: Befehl nicht gefunden" in result.stderr
    assert "HOOK_EXIT:127" in result.stdout
