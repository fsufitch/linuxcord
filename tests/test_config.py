import pytest

from linuxcord import config


def test_config_resolution_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINUXCORD_DISCORD_TGZ_URL", "env-url")
    monkeypatch.setenv("LINUXCORD_UPDATES_URL", "env-updates")
    resolved = config.resolve()
    assert resolved.discord_tgz_url == "env-url"
    assert resolved.updates_url == "env-updates"


def test_config_resolution_cli_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINUXCORD_DISCORD_TGZ_URL", "env-url")
    resolved = config.resolve(discord_tgz_url="cli-url", updates_url="cli-updates")
    assert resolved.discord_tgz_url == "cli-url"
    assert resolved.updates_url == "cli-updates"
