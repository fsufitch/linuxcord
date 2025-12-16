from __future__ import annotations

import logging
import os
import subprocess
from collections.abc import Callable

from linuxcord.paths import LinuxcordPaths
from linuxcord.types import DiscordVersion


logger = logging.getLogger(__name__)
PopenType = Callable[..., subprocess.Popen[bytes]] | type[subprocess.Popen[bytes]]


class DiscordLauncher:
    def __init__(
        self,
        linuxcord_paths: LinuxcordPaths,
        popen: PopenType | None = None,
    ):
        self._paths: LinuxcordPaths = linuxcord_paths
        self.popen: PopenType = popen or subprocess.Popen

    def _ensure_not_root(self) -> None:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            raise RuntimeError("Do not run linuxcord as root")

    def launch(self, discord_version: DiscordVersion) -> None:
        self._ensure_not_root()
        discord_paths = self._paths.discord_paths(discord_version)
        install_dir = discord_paths.dir
        executable = discord_paths.executable
        if not executable.exists():
            raise RuntimeError("Discord executable not found; is it installed?")

        env = os.environ.copy()
        logger.debug("Launching Discord with cwd=%s", install_dir)
        logger.info("Launching Discord from %s", executable)
        popen = self.popen
        _ = popen([str(executable)], cwd=str(install_dir), env=env)
