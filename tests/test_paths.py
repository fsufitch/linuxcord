from __future__ import annotations

from pathlib import Path

from linuxcord.paths import APP_NAME, LinuxcordPaths
from linuxcord.types import DiscordVersion

from .helpers import MockPyXDG


def test_base_directories_use_xdg_values(tmp_path: Path) -> None:
    xdg = MockPyXDG(
        xdg_data_home=tmp_path / "data",
        xdg_cache_home=tmp_path / "cache",
        xdg_state_home=tmp_path / "state",
    )
    paths = LinuxcordPaths(xdg)

    assert paths.data_dir == tmp_path / "data" / APP_NAME
    assert paths.cache_dir == tmp_path / "cache" / APP_NAME
    assert paths.state_dir == tmp_path / "state" / APP_NAME


def test_applications_dir_uses_save_data_path(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path / "data")
    paths = LinuxcordPaths(xdg)

    assert paths.applications_dir == tmp_path / "data" / "applications"


def test_discord_paths_properties(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path / "data")
    paths = LinuxcordPaths(xdg)
    version = DiscordVersion("1.2.3")

    discord_paths = paths.discord_paths(version)
    base = tmp_path / "data" / APP_NAME / "versions" / version.string

    assert discord_paths.dir == base
    assert discord_paths.icon == base / "discord.png"
    assert discord_paths.executable == base / "Discord"
    assert discord_paths.build_info == base / "resources" / "build_info.json"


def test_runtime_dir_from_xdg(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    xdg = MockPyXDG(runtime_dir=runtime_dir)
    paths = LinuxcordPaths(xdg)

    assert paths.runtime_dir == runtime_dir


def test_runtime_dir_returns_none_on_error() -> None:
    xdg = MockPyXDG(runtime_exception=RuntimeError("boom"))
    paths = LinuxcordPaths(xdg)

    assert paths.runtime_dir is None


def test_acquire_lock_prefers_runtime_dir(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    xdg = MockPyXDG(runtime_dir=runtime_dir, xdg_state_home=tmp_path / "state")
    paths = LinuxcordPaths(xdg)

    lock = paths.acquire_lock()
    try:
        assert Path(lock.lock_file) == runtime_dir / f"{APP_NAME}.lock"
    finally:
        lock.release()


def test_acquire_lock_falls_back_to_state_dir(tmp_path: Path) -> None:
    xdg = MockPyXDG(xdg_state_home=tmp_path / "state")
    paths = LinuxcordPaths(xdg)

    lock = paths.acquire_lock()
    try:
        assert Path(lock.lock_file) == tmp_path / "state" / APP_NAME / "lock"
    finally:
        lock.release()


def test_ensure_base_dirs_create_directories(tmp_path: Path) -> None:
    xdg = MockPyXDG(
        xdg_data_home=tmp_path / "data",
        xdg_cache_home=tmp_path / "cache",
        xdg_state_home=tmp_path / "state",
    )
    paths = LinuxcordPaths(xdg)

    paths.ensure_base_dirs()

    assert paths.data_dir.exists()
    assert paths.cache_dir.exists()
    assert paths.state_dir.exists()
    assert paths.discord_versions_dir.exists()
