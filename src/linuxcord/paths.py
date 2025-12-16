from __future__ import annotations

import os
from pathlib import Path

from xdg import BaseDirectory

APP_NAME = "linuxcord"


def _xdg_dir(value: str | None, default: str) -> Path:
    return Path(value) if value else Path(default)


def data_dir() -> Path:
    base = _xdg_dir(BaseDirectory.xdg_data_home, os.path.expanduser("~/.local/share"))
    return base / APP_NAME


def cache_dir() -> Path:
    base = _xdg_dir(BaseDirectory.xdg_cache_home, os.path.expanduser("~/.cache"))
    return base / APP_NAME


def state_dir() -> Path:
    base = _xdg_dir(BaseDirectory.xdg_state_home, os.path.expanduser("~/.local/state"))
    return base / APP_NAME


def discord_root() -> Path:
    return data_dir() / "discord"


def versions_dir() -> Path:
    return discord_root() / "versions"


def current_symlink() -> Path:
    return discord_root() / "current"


def state_file() -> Path:
    return state_dir() / "state.json"


def desktop_entry_path() -> Path:
    return data_dir() / "linuxcord.desktop"


def desktop_install_path() -> Path:
    applications_dir = Path(BaseDirectory.save_data_path("applications"))
    return applications_dir / "linuxcord.desktop"


def lock_file() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / f"{APP_NAME}.lock"
    return state_dir() / "lock"


def ensure_base_dirs() -> None:
    for path in (data_dir(), cache_dir(), state_dir(), discord_root(), versions_dir()):
        path.mkdir(parents=True, exist_ok=True)
