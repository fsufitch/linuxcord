from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager

from linuxcord import paths


@contextmanager
def exclusive_lock() -> Iterator[None]:
    lock_path = paths.lock_file()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
