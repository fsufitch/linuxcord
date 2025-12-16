from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import cast

import requests

from linuxcord.paths import DiscordPaths, LinuxcordPaths
from linuxcord.types import DiscordVersion


logger = logging.getLogger(__name__)


class LocalVersioner:
    def __init__(self, linuxcord_paths: LinuxcordPaths):
        self._paths: LinuxcordPaths = linuxcord_paths

    def get_version(self, path: str | Path) -> DiscordVersion | None:
        try:
            return DiscordVersion.from_build_info(DiscordPaths(path).build_info)
        except FileNotFoundError:
            return None

    def get_current_version(self) -> DiscordVersion | None:
        current = self._paths.discord_current_version_dir_symlink
        if not current.exists():
            return None
        try:
            resolved = current.resolve(strict=True)
        except OSError:
            return None
        return self.get_version(resolved)


class OnlineVersioner:
    def __init__(
        self,
        discord_tgz_url: str,
        discord_updates_url: str,
        session: requests.Session,
    ):
        self._tgz_url: str = discord_tgz_url
        self._updates_url: str = discord_updates_url
        self._session: requests.Session = session

    def _extract_version_from_url(self, url: str) -> DiscordVersion | None:
        pattern = r"([0-9]+\.[0-9]+\.[0-9]+)"
        match = re.search(pattern, url)
        if match:
            return DiscordVersion(match.group(1))
        return None

    def get_latest_version(self) -> DiscordVersion | None:
        logger.debug("Fetching latest version from %s", self._updates_url)
        try:
            response = self._session.get(self._updates_url, timeout=10)
            response.raise_for_status()
            data = cast(dict[str, object], response.json())
            name = data.get("name")
            if isinstance(name, str):
                return DiscordVersion(name)
        except Exception:
            logger.error("Failed to fetch version from updates API", exc_info=True)

        logger.debug("Falling back to resolving version from download URL")
        try:
            resolved_url = self.get_latest_download_url()
            return self._extract_version_from_url(resolved_url)
        except Exception:
            logger.error("Failed to resolve version from download URL", exc_info=True)
            return None

    def get_latest_download_url(self) -> str:
        response = self._session.head(
            self._tgz_url, allow_redirects=True, timeout=10, stream=True
        )
        response.raise_for_status()
        final_url = response.url
        response.close()
        return final_url
