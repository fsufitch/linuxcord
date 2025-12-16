from __future__ import annotations

from pathlib import Path

from linuxcord.paths import LinuxcordPaths
from linuxcord.types import DiscordVersion
from linuxcord.versions import LocalVersioner
from tests.helpers import MockPyXDG


def write_build_info(version_dir: Path, version: str) -> None:
    build_info = version_dir / "resources" / "build_info.json"
    build_info.parent.mkdir(parents=True, exist_ok=True)
    _ = build_info.write_text(f'{{"version": "{version}"}}')


def test_get_version_returns_value_when_build_info_exists(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path)
    paths = LinuxcordPaths(xdg)
    version_dir = tmp_path / "versions" / "Discord-1.2.3"
    write_build_info(version_dir, "1.2.3")

    versioner = LocalVersioner(paths)

    assert versioner.get_version(version_dir) == DiscordVersion("1.2.3")


def test_get_version_returns_none_when_build_info_is_missing(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path)
    paths = LinuxcordPaths(xdg)
    version_dir = tmp_path / "versions" / "Discord-9.9.9"

    versioner = LocalVersioner(paths)

    assert versioner.get_version(version_dir) is None


def test_get_current_version_uses_symlink(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path)
    paths = LinuxcordPaths(xdg)
    paths.ensure_base_dirs()

    version_dir = paths.discord_versions_dir / "Discord-2.0.0"
    write_build_info(version_dir, "2.0.0")
    paths.discord_current_version_dir_symlink.symlink_to(version_dir)

    versioner = LocalVersioner(paths)

    assert versioner.get_current_version() == DiscordVersion("2.0.0")


def test_get_current_version_handles_missing_symlink(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path)
    paths = LinuxcordPaths(xdg)

    versioner = LocalVersioner(paths)

    assert versioner.get_current_version() is None


def test_get_current_version_handles_broken_symlink(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path)
    paths = LinuxcordPaths(xdg)
    paths.ensure_base_dirs()
    missing_target = paths.discord_versions_dir / "Discord-3.0.0"
    paths.discord_current_version_dir_symlink.symlink_to(missing_target)

    versioner = LocalVersioner(paths)

    assert versioner.get_current_version() is None
