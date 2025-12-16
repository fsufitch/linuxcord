import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def xdg_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    data: Path = tmp_path / "data"
    cache: Path = tmp_path / "cache"
    state: Path = tmp_path / "state"
    for name, path in [
        ("XDG_DATA_HOME", data),
        ("XDG_CACHE_HOME", cache),
        ("XDG_STATE_HOME", state),
    ]:
        monkeypatch.setenv(name, str(path))
    yield
    shutil.rmtree(data, ignore_errors=True)
    shutil.rmtree(cache, ignore_errors=True)
    shutil.rmtree(state, ignore_errors=True)
