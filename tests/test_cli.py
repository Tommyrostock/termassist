"""Tests for cli.py exit-code semantics, which command_not_found_handle.sh
relies on to decide whether to also print the plain shell error message.
"""

from unittest.mock import patch

from terminalhelfer import cli


def test_single_shot_exit_code_is_zero_when_something_is_found():
    with patch("terminalhelfer.ui.show_mode_banner"), patch("terminalhelfer.ui.handle_results"):
        code = cli.main(["neustart"])

    assert code == 0


def test_single_shot_exit_code_is_one_when_nothing_is_found():
    with patch("terminalhelfer.ui.show_mode_banner"), patch("terminalhelfer.ui.handle_results"):
        code = cli.main(["xxxxyyyzzzzqqqqwwwwuuuu"])

    assert code == 1


def test_direct_command_short_circuits_matcher():
    """A directly valid command (e.g. 'git status') must skip the matcher
    entirely and go straight to the confirm/execute flow.
    """
    with patch("terminalhelfer.direct.ist_direkter_befehl", return_value=True), patch(
        "terminalhelfer.ui.confirm_and_execute"
    ) as mock_confirm, patch("terminalhelfer.matcher.match") as mock_match:
        code = cli.main(["git status"])

    mock_confirm.assert_called_once_with("git status")
    mock_match.assert_not_called()
    assert code == 0


def test_ai_disabled_by_default_end_to_end():
    with patch("terminalhelfer.ui.show_mode_banner"), patch("terminalhelfer.ui.handle_results"), patch(
        "terminalhelfer.ollama_client.is_available", return_value=True
    ) as mock_available:
        cli.main(["neustart"])

    mock_available.assert_not_called()
