import tarfile
from pathlib import Path

import pytest

from linuxcord import updater


def test_safe_extract_prevents_traversal(tmp_path: Path) -> None:
    tar_path = tmp_path / "evil.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        info = tarfile.TarInfo(name="../evil.txt")
        info.size = 0
        tar.addfile(info)

    with tarfile.open(tar_path, "r:gz") as tar:
        with pytest.raises(ValueError):
            updater._safe_extract(tar, tmp_path)  # pyright: ignore[reportPrivateUsage]


def test_update_if_needed_no_install(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_resolve_latest_version(_updates_url: str, _discord_tgz_url: str) -> str:
        return "1.0"

    def fake_installed_version() -> str:
        return "1.0"

    monkeypatch.setattr(updater, "resolve_latest_version", fake_resolve_latest_version)
    monkeypatch.setattr(updater, "get_installed_version", fake_installed_version)
    result = updater.update_if_needed(perform_install=False)
    assert result.updated is False
    assert result.installed_version == "1.0"
