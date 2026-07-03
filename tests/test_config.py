"""Tests for the persistent KI-enabled setting."""

from terminalhelfer import config


def test_defaults_to_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path / "terminalhelfer")
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "terminalhelfer" / "config.json")

    assert config.is_ki_enabled() is False


def test_set_ki_enabled_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path / "terminalhelfer")
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "terminalhelfer" / "config.json")

    config.set_ki_enabled(True)
    assert config.is_ki_enabled() is True

    config.set_ki_enabled(False)
    assert config.is_ki_enabled() is False


def test_corrupt_config_file_falls_back_to_defaults(tmp_path, monkeypatch):
    config_dir = tmp_path / "terminalhelfer"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config_path.write_text("das ist kein json", encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    assert config.is_ki_enabled() is False
