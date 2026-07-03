"""Tests for typo detection: distinguishing a single-word typo of a real
command ("sl" for "ls") from natural-language input, which decides whether
command_not_found_handle.sh should defer to apt's own spelling correction.

Real system PATH contents vary by machine and OS, so _verfuegbare_befehlsnamen
is patched to a fixed, known set rather than relying on whatever happens to
be installed on the machine running the tests.
"""

from terminalhelfer import typo

FAKE_BEFEHLE = frozenset({"ls", "grep", "cat", "reboot", "firewall-cmd"})


def test_single_letter_swap_typo_is_detected(monkeypatch):
    monkeypatch.setattr(typo, "_verfuegbare_befehlsnamen", lambda: FAKE_BEFEHLE)

    assert typo.ist_wahrscheinlich_tippfehler("sl") is True


def test_transposed_letters_typo_is_detected(monkeypatch):
    monkeypatch.setattr(typo, "_verfuegbare_befehlsnamen", lambda: FAKE_BEFEHLE)

    assert typo.ist_wahrscheinlich_tippfehler("gerp") is True


def test_natural_language_word_is_not_a_typo(monkeypatch):
    monkeypatch.setattr(typo, "_verfuegbare_befehlsnamen", lambda: FAKE_BEFEHLE)

    assert typo.ist_wahrscheinlich_tippfehler("neustart") is False
    assert typo.ist_wahrscheinlich_tippfehler("firewall") is False


def test_multiword_input_is_never_a_typo(monkeypatch):
    monkeypatch.setattr(typo, "_verfuegbare_befehlsnamen", lambda: FAKE_BEFEHLE)

    assert typo.ist_wahrscheinlich_tippfehler("alle dateien loeschen") is False
    assert typo.ist_wahrscheinlich_tippfehler("firewall ausschalten") is False


def test_exact_match_is_not_flagged_as_typo(monkeypatch):
    """An exact match would already have been handled by direct.py earlier -
    this function shouldn't need to (and doesn't) special-case it, but it
    must not crash or misbehave either.
    """
    monkeypatch.setattr(typo, "_verfuegbare_befehlsnamen", lambda: FAKE_BEFEHLE)

    assert typo.ist_wahrscheinlich_tippfehler("ls") is False


def test_empty_input_is_not_a_typo(monkeypatch):
    monkeypatch.setattr(typo, "_verfuegbare_befehlsnamen", lambda: FAKE_BEFEHLE)

    assert typo.ist_wahrscheinlich_tippfehler("") is False
