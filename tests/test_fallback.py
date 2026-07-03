"""Tests for the offline fuzzy search fallback."""

from termassist.fallback import fuzzy_search, load_commands


def test_load_commands_returns_valid_entries():
    commands = load_commands()
    assert len(commands) >= 200
    for entry in commands:
        assert "cmd" in entry
        assert "kurz" in entry
        assert "keywords" in entry
        assert len(entry["keywords"]) >= 6


def test_single_keyword_query_finds_reboot():
    """A bare single-word query must match, not just full sentences."""
    commands = load_commands()
    results = fuzzy_search("neustart", commands)

    assert results
    # "neustart" is a literal keyword of "sudo reboot", so it should win.
    assert results[0]["cmd"] == "sudo reboot"


def test_full_sentence_query_finds_reboot():
    commands = load_commands()
    results = fuzzy_search("ich moechte den computer neustarten", commands)

    assert results
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


def test_slow_pc_question_finds_top_or_htop():
    commands = load_commands()
    results = fuzzy_search("warum ist mein pc so langsam", commands)

    gefundene_befehle = {r["cmd"] for r in results}
    assert gefundene_befehle & {"top", "htop"}


def test_network_overview_prefers_ip_a_over_ping():
    """Regression test: "netzwerk info" used to surface `ping ZIEL` (a
    reachability test) instead of an actual overview command.
    """
    commands = load_commands()
    results = fuzzy_search("netzwerk info", commands)

    assert results
    assert results[0]["cmd"] == "ip a"


def test_free_up_disk_space_finds_cleanup_commands():
    """Regression test: "mach mal platz frei" used to surface unrelated
    entries like `crontab -e` and `last` instead of real disk-cleanup
    commands.
    """
    commands = load_commands()
    results = fuzzy_search("mach mal platz frei", commands)

    gefundene_befehle = {r["cmd"] for r in results}
    erwartete_befehle = {
        "sudo apt autoremove",
        "sudo apt clean",
        "du -sh * | sort -rh | head -10",
        "journalctl --vacuum-size=100M",
    }
    assert gefundene_befehle & erwartete_befehle
    assert "crontab -e" not in gefundene_befehle
    assert "last" not in gefundene_befehle
