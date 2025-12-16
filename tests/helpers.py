from __future__ import annotations

from pathlib import Path

from linuxcord.types import PyXDG
from typing_extensions import override


class MockPyXDG(PyXDG):
    xdg_data_home: str | None
    xdg_cache_home: str | None
    xdg_state_home: str | None
    _runtime_dir: str | None
    _runtime_exception: Exception | None

    def __init__(
        self,
        *,
        xdg_data_home: str | Path | None = None,
        xdg_cache_home: str | Path | None = None,
        xdg_state_home: str | Path | None = None,
        runtime_dir: str | Path | None = None,
        runtime_exception: Exception | None = None,
    ) -> None:
        self.xdg_data_home = str(xdg_data_home) if xdg_data_home is not None else None
        self.xdg_cache_home = (
            str(xdg_cache_home) if xdg_cache_home is not None else None
        )
        self.xdg_state_home = (
            str(xdg_state_home) if xdg_state_home is not None else None
        )
        self._runtime_dir = str(runtime_dir) if runtime_dir is not None else None
        self._runtime_exception = runtime_exception

    @override
    def save_data_path(self, xdg_dir_name: str) -> str:
        base = Path(self.xdg_data_home or "")
        return str(base / xdg_dir_name)

    @override
    def get_runtime_dir(self, strict: bool = True) -> str:
        if self._runtime_exception:
            raise self._runtime_exception
        if strict and self._runtime_dir is None:
            raise RuntimeError("runtime dir is not set")
        return self._runtime_dir or ""
