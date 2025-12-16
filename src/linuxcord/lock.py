from __future__ import annotations

import fcntl
import logging
from collections.abc import Iterator
from contextlib import contextmanager

from linuxcord import paths

LOGGER = logging.getLogger(__name__)


@contextmanager
def exclusive_lock() -> Iterator[None]:
    lock_path = paths.lock_file()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock_fd:
        LOGGER.debug("Acquiring lock on %s", lock_path)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            LOGGER.debug("Released lock on %s", lock_path)
