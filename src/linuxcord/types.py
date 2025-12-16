from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, TypeGuard, cast

from typing_extensions import override

from packaging.version import Version


class PyXDG(Protocol):
    xdg_data_home: str | None
    xdg_cache_home: str | None
    xdg_state_home: str | None

    def save_data_path(self, xdg_dir_name: str) -> str:
        """Return the XDG data directory for the given name."""

        ...

    def get_runtime_dir(self, strict: bool = True) -> str:
        """Return the runtime directory path."""

        ...


@dataclass(frozen=True)
class DiscordVersion:
    """Simple helper for comparing Discord versions."""

    string: str
    _version: Version = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_version", Version(self.string))

    @override
    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.string

    @override
    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"DiscordVersion('{self.string}')"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, DiscordVersion):
            return NotImplemented
        return self._version < other._version

    def __le__(self, other: object) -> bool:
        if not isinstance(other, DiscordVersion):
            return NotImplemented
        return self._version <= other._version

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, DiscordVersion):
            return NotImplemented
        return self._version > other._version

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, DiscordVersion):
            return NotImplemented
        return self._version >= other._version

    @staticmethod
    def from_build_info(path: Path | str) -> "DiscordVersion":
        build_info_path = Path(path)
        data_raw = cast(object, json.loads(build_info_path.read_text()))
        if not _is_str_key_dict(data_raw):
            raise ValueError("build_info.json is not a valid object")

        data: dict[str, object] = data_raw
        version_obj = data.get("version")
        if not isinstance(version_obj, str):
            raise ValueError("build_info.json does not contain a version string")
        return DiscordVersion(version_obj)


def _is_str_key_dict(value: object) -> TypeGuard[dict[str, object]]:
    if not isinstance(value, dict):
        return False
    dict_value = cast(dict[object, object], value)
    return all(isinstance(key, str) for key in dict_value.keys())
