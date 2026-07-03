"""Tests for the offline fuzzy search fallback."""

from terminalhelfer.fallback import fuzzy_search, load_commands


def test_load_commands_returns_valid_entries():
    commands = load_commands()
    assert len(commands) >= 80
    for entry in commands:
        assert "cmd" in entry
        assert "kurz" in entry
        assert "keywords" in entry


def test_neustart_finds_reboot_among_top_results():
    commands = load_commands()
    results = fuzzy_search("neustart", commands)

    assert results
    assert any(r["cmd"] == "sudo reboot" for r in results)
    # "neustart" is a literal keyword of "sudo reboot", so it should win.
    assert results[0]["cmd"] == "sudo reboot"


def test_full_sentence_query_still_finds_reboot():
    commands = load_commands()
    results = fuzzy_search("ich will den rechner neu starten", commands)

    assert any(r["cmd"] == "sudo reboot" for r in results)


def test_empty_query_returns_empty_list():
    commands = load_commands()
    assert fuzzy_search("", commands) == []
    assert fuzzy_search("   ", commands) == []


def test_limit_is_respected():
    commands = load_commands()
    results = fuzzy_search("datei", commands, limit=3)
    assert len(results) <= 3


def test_results_only_contain_cmd_and_kurz():
    commands = load_commands()
    results = fuzzy_search("firewall aktivieren", commands)
    for entry in results:
        assert set(entry.keys()) == {"cmd", "kurz"}
