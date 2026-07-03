"""Tests for the matcher, especially validation of AI (Ollama) results against
the real database - the safeguard against hallucinated commands.
"""

from unittest.mock import patch

from terminalhelfer import matcher

SAMPLE_COMMANDS = [
    {"cmd": "sudo reboot", "kurz": "Startet den Computer sofort neu", "keywords": ["neustart"]},
    {"cmd": "ls -la", "kurz": "Listet alle Dateien auf", "keywords": ["dateien anzeigen"]},
]


def test_match_uses_ai_result_when_valid():
    with patch("terminalhelfer.matcher.ollama_client.is_available", return_value=True), patch(
        "terminalhelfer.matcher.ollama_client.query_ollama", return_value=["sudo reboot"]
    ):
        results, mode = matcher.match("neustart", commands=SAMPLE_COMMANDS)

    assert mode == "ki"
    assert results == [{"cmd": "sudo reboot", "kurz": "Startet den Computer sofort neu"}]


def test_match_filters_out_hallucinated_commands():
    with patch("terminalhelfer.matcher.ollama_client.is_available", return_value=True), patch(
        "terminalhelfer.matcher.ollama_client.query_ollama",
        return_value=["sudo rm -rf /", "sudo reboot"],
    ):
        results, mode = matcher.match("neustart", commands=SAMPLE_COMMANDS)

    assert mode == "ki"
    assert results == [{"cmd": "sudo reboot", "kurz": "Startet den Computer sofort neu"}]
    assert all(r["cmd"] != "sudo rm -rf /" for r in results)


def test_match_falls_back_when_ollama_unavailable():
    with patch("terminalhelfer.matcher.ollama_client.is_available", return_value=False):
        results, mode = matcher.match("neustart", commands=SAMPLE_COMMANDS)

    assert mode == "fallback"
    assert results
    assert results[0]["cmd"] == "sudo reboot"


def test_match_falls_back_when_all_ai_results_are_hallucinated():
    with patch("terminalhelfer.matcher.ollama_client.is_available", return_value=True), patch(
        "terminalhelfer.matcher.ollama_client.query_ollama", return_value=["frei erfundener befehl"]
    ):
        results, mode = matcher.match("neustart", commands=SAMPLE_COMMANDS)

    assert mode == "fallback"
    assert results[0]["cmd"] == "sudo reboot"


def test_match_falls_back_when_ollama_returns_none():
    with patch("terminalhelfer.matcher.ollama_client.is_available", return_value=True), patch(
        "terminalhelfer.matcher.ollama_client.query_ollama", return_value=None
    ):
        results, mode = matcher.match("neustart", commands=SAMPLE_COMMANDS)

    assert mode == "fallback"


def test_no_ai_flag_skips_ollama_entirely():
    with patch("terminalhelfer.matcher.ollama_client.is_available", return_value=True) as mock_available:
        results, mode = matcher.match("neustart", commands=SAMPLE_COMMANDS, use_ai=False)

    mock_available.assert_not_called()
    assert mode == "fallback"
    assert results[0]["cmd"] == "sudo reboot"
