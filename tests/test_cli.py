"""Tests for cli.py exit-code semantics, which command_not_found_handle.sh
relies on to decide whether to also print the plain shell error message.
"""

from unittest.mock import patch

from termassist import cli


def test_single_shot_exit_code_is_zero_when_something_is_found():
    with patch("termassist.ui.show_mode_banner"), patch("termassist.ui.handle_results"):
        code = cli.main(["neustart"])

    assert code == 0


def test_single_shot_exit_code_is_one_when_nothing_is_found():
    with patch("termassist.ui.show_mode_banner"), patch("termassist.ui.handle_results"):
        code = cli.main(["xxxxyyyzzzzqqqqwwwwuuuu"])

    assert code == 1


def test_direct_command_short_circuits_matcher():
    """A directly valid command (e.g. 'git status') must skip the matcher
    entirely and go straight to the confirm/execute flow.
    """
    with patch("termassist.direct.ist_direkter_befehl", return_value=True), patch(
        "termassist.ui.confirm_and_execute"
    ) as mock_confirm, patch("termassist.matcher.match") as mock_match:
        code = cli.main(["git status"])

    mock_confirm.assert_called_once_with("git status")
    mock_match.assert_not_called()
    assert code == 0


def test_ai_disabled_by_default_end_to_end():
    with patch("termassist.ui.show_mode_banner"), patch("termassist.ui.handle_results"), patch(
        "termassist.ollama_client.is_available", return_value=True
    ) as mock_available:
        cli.main(["neustart"])

    mock_available.assert_not_called()


def test_single_word_typo_returns_exit_code_two():
    """When nothing was found in the database but the word looks like a typo
    of a real installed command, cli.main must signal exit code 2 so
    command_not_found_handle.sh knows to defer to apt's own spelling
    correction instead of showing "nothing found".
    """
    with patch("termassist.matcher.match", return_value=([], "fallback")), patch(
        "termassist.typo.ist_wahrscheinlich_tippfehler", return_value=True
    ):
        code = cli.main(["sl"])

    assert code == 2


def test_exit_code_is_one_when_typo_check_also_says_no():
    """If neither the database nor the typo check find anything plausible,
    cli.main must fall back to exit code 1 ("nothing found at all"), not 2.
    The actual "multi-word input is never a typo" guard lives in typo.py
    itself (see test_typo.py) - here we just verify cli.py wires the result
    of that check through correctly.
    """
    with patch("termassist.matcher.match", return_value=([], "fallback")), patch(
        "termassist.typo.ist_wahrscheinlich_tippfehler", return_value=False
    ) as mock_typo:
        code = cli.main(["alle dateien loeschen"])

    mock_typo.assert_called_once_with("alle dateien loeschen")
    assert code == 1
