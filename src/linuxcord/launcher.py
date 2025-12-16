from __future__ import annotations

import logging
import os
import subprocess

from linuxcord.updater import get_current_install

logger = logging.getLogger(__name__)


def _ensure_not_root() -> None:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise RuntimeError("Do not run linuxcord as root")


def launch_discord() -> None:
    _ensure_not_root()
    current_dir = get_current_install()
    if current_dir is None:
        raise RuntimeError("Discord is not installed. Run 'linuxcord init' first.")
    binary = current_dir / "Discord"
    if not binary.exists():
        raise RuntimeError("Discord binary not found in current installation")

    env = os.environ.copy()
    logger.debug("Launching Discord with cwd=%s", current_dir)
    logger.info("Launching Discord from %s", binary)
    _ = subprocess.Popen([str(binary)], cwd=str(current_dir), env=env)
