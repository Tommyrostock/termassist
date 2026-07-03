"""Tests for direct valid-command detection."""

from termassist.direct import ist_direkter_befehl


def test_real_command_is_direct():
    assert ist_direkter_befehl("ls") is True


def test_real_command_with_arguments_is_direct():
    assert ist_direkter_befehl("ls -la") is True


def test_unknown_word_is_not_direct():
    assert ist_direkter_befehl("neustart") is False


def test_empty_input_is_not_direct():
    assert ist_direkter_befehl("") is False
    assert ist_direkter_befehl("   ") is False
