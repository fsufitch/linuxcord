from __future__ import annotations

import os
from pathlib import Path

from filelock import BaseFileLock, FileLock

from linuxcord.types import DiscordVersion, PyXDG

APP_NAME = "linuxcord"


class LinuxcordPaths:
    def __init__(self, xdg: PyXDG):
        self._xdg: PyXDG = xdg

    @property
    def data_dir(self) -> Path:
        base = Path(self._xdg.xdg_data_home or os.path.expanduser("~/.local/share"))
        return base / APP_NAME

    @property
    def state_dir(self) -> Path:
        base = Path(self._xdg.xdg_state_home or os.path.expanduser("~/.local/state"))
        return base / APP_NAME

    @property
    def cache_dir(self) -> Path:
        base = Path(self._xdg.xdg_cache_home or os.path.expanduser("~/.cache"))
        return base / APP_NAME

    @property
    def applications_dir(self) -> Path:
        return Path(self._xdg.save_data_path("applications"))

    @property
    def discord_versions_dir(self) -> Path:
        return self.data_dir / "versions"

    @property
    def discord_current_version_dir_symlink(self) -> Path:
        return self.discord_versions_dir / "current"

    @property
    def runtime_dir(self) -> Path | None:
        try:
            value = self._xdg.get_runtime_dir(strict=False)
        except Exception:
            return None
        return Path(value) if value else None

    def acquire_lock(self) -> BaseFileLock:
        lock_path = (
            self.runtime_dir / f"{APP_NAME}.lock"
            if self.runtime_dir
            else self.state_dir / "lock"
        )
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = FileLock(lock_path)
        _ = lock.acquire()
        return lock

    def ensure_base_dirs(self) -> None:
        for directory in (
            self.data_dir,
            self.cache_dir,
            self.state_dir,
            self.discord_versions_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def discord_paths(self, discord_version: DiscordVersion) -> "DiscordPaths":
        return DiscordPaths(self.discord_versions_dir / discord_version.string)


class DiscordPaths:
    def __init__(self, location: Path | str):
        self._dir: Path = Path(location)

    @property
    def dir(self) -> Path:
        return self._dir

    @property
    def icon(self) -> Path:
        return self._dir / "icon.png"

    @property
    def executable(self) -> Path:
        return self._dir / "Discord"

    @property
    def build_info(self) -> Path:
        return self._dir / "resources" / "build_info.json"
