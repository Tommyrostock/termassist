"""Tests for hook_installer.py: the PATH-export bug fix (a fresh install must
add both the hook block AND the PATH line), the "only repair what's missing"
logic for pre-existing incomplete installs, and shell auto-detection.
"""

from unittest.mock import patch

from termassist import hook_installer

MARKER_START = hook_installer.MARKER_START
MARKER_END = hook_installer.MARKER_END
PATH_LINE = hook_installer.PATH_EXPORT_LINE


def test_fresh_install_adds_both_block_and_path_line(tmp_path):
    """Regression test for the reported bug: a brand new .bashrc must end up
    with both the hook block and the PATH export line, not just the block.
    """
    rc_pfad = tmp_path / ".bashrc"

    code = hook_installer.install(shell="bash", rc_pfad=rc_pfad)

    assert code == 0
    inhalt = rc_pfad.read_text(encoding="utf-8")
    assert MARKER_START in inhalt
    assert MARKER_END in inhalt
    assert PATH_LINE in inhalt
    assert "command_not_found_handle" in inhalt


def test_fresh_install_on_nonexistent_rc_file_creates_it(tmp_path):
    rc_pfad = tmp_path / "unterordner" / ".bashrc"

    code = hook_installer.install(shell="bash", rc_pfad=rc_pfad)

    assert code == 0
    assert rc_pfad.exists()
    assert PATH_LINE in rc_pfad.read_text(encoding="utf-8")


def test_incomplete_existing_block_gets_path_line_repaired(tmp_path):
    """Simulates a user who already installed an older termassist version
    (v0.1-v0.4) whose hook block never included the PATH line - re-running
    --install-hook must add just the missing line, not duplicate the block.
    """
    rc_pfad = tmp_path / ".bashrc"
    alter_block = "\n".join(
        [
            "# eigene Zeile davor",
            MARKER_START,
            "# Bindet termassist ein - alte Version ohne PATH-Zeile.",
            "command_not_found_handle () {",
            "    echo alt",
            "}",
            MARKER_END,
            "",
        ]
    )
    rc_pfad.write_text(alter_block, encoding="utf-8")

    code = hook_installer.install(shell="bash", rc_pfad=rc_pfad)

    assert code == 0
    inhalt = rc_pfad.read_text(encoding="utf-8")
    assert PATH_LINE in inhalt
    # Der Rest des alten Blocks darf nicht angetastet/dupliziert werden.
    assert inhalt.count(MARKER_START) == 1
    assert inhalt.count(MARKER_END) == 1
    assert "echo alt" in inhalt
    assert "# eigene Zeile davor" in inhalt


def test_fully_installed_hook_is_left_untouched(tmp_path):
    rc_pfad = tmp_path / ".bashrc"
    hook_installer.install(shell="bash", rc_pfad=rc_pfad)
    inhalt_nach_erstem_lauf = rc_pfad.read_text(encoding="utf-8")

    code = hook_installer.install(shell="bash", rc_pfad=rc_pfad)

    assert code == 0
    assert rc_pfad.read_text(encoding="utf-8") == inhalt_nach_erstem_lauf


def test_path_line_not_duplicated_if_already_present_elsewhere(tmp_path):
    rc_pfad = tmp_path / ".bashrc"
    rc_pfad.write_text(f'{PATH_LINE}\n# war schon vorher da\n', encoding="utf-8")

    hook_installer.install(shell="bash", rc_pfad=rc_pfad)

    inhalt = rc_pfad.read_text(encoding="utf-8")
    assert inhalt.count(hook_installer.PATH_MARKER_SUBSTRING) == 1


def test_zsh_install_uses_zsh_handler_script(tmp_path):
    rc_pfad = tmp_path / ".zshrc"

    code = hook_installer.install(shell="zsh", rc_pfad=rc_pfad)

    assert code == 0
    inhalt = rc_pfad.read_text(encoding="utf-8")
    assert "command_not_found_handler" in inhalt
    assert PATH_LINE in inhalt


def test_shell_detection_prefers_ppid_process_name():
    fake_ps_result = type("R", (), {"stdout": "zsh\n"})()
    with patch("termassist.hook_installer.subprocess.run", return_value=fake_ps_result):
        assert hook_installer.erkenne_shell() == "zsh"


def test_shell_detection_falls_back_to_shell_env_var(monkeypatch):
    with patch("termassist.hook_installer.subprocess.run", side_effect=OSError("kein ps")):
        monkeypatch.setenv("SHELL", "/usr/bin/zsh")
        assert hook_installer.erkenne_shell() == "zsh"

        monkeypatch.setenv("SHELL", "/bin/bash")
        assert hook_installer.erkenne_shell() == "bash"


def test_shell_detection_returns_none_when_unknown():
    fake_ps_result = type("R", (), {"stdout": "fish\n"})()
    with patch("termassist.hook_installer.subprocess.run", return_value=fake_ps_result):
        with patch.dict("os.environ", {"SHELL": "/usr/bin/fish"}, clear=False):
            assert hook_installer.erkenne_shell() is None


def test_install_without_rc_override_reports_when_shell_unknown():
    with patch("termassist.hook_installer.erkenne_shell", return_value=None):
        code = hook_installer.install()

    assert code == 1
