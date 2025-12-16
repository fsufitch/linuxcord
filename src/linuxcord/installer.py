from __future__ import annotations

import logging
import shutil
import tarfile
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import requests

from linuxcord.paths import DiscordPaths, LinuxcordPaths
from linuxcord.types import DiscordVersion


logger = logging.getLogger(__name__)
CHUNK_SIZE = 8192


def _validate_tar_member(member: tarfile.TarInfo) -> None:
    name = member.name
    if name.startswith("/"):
        raise ValueError("Absolute paths are not allowed in archive")
    member_path = Path(name)
    if any(part == ".." for part in member_path.parts):
        raise ValueError("Path traversal detected in archive")


def _safe_extract(tar: tarfile.TarFile, target: Path) -> None:
    logger.debug("Extracting tarball to %s", target)
    for member in tar.getmembers():
        _validate_tar_member(member)
    tar.extractall(path=target)


class DiscordInstaller:
    def __init__(self, linuxcord_paths: LinuxcordPaths):
        self._paths = linuxcord_paths

    def install(self, version: DiscordVersion, tgz_url: str, force: bool = False) -> DiscordPaths:
        destination = self._paths.discord_paths(version).dir
        if destination.exists():
            if not force:
                raise FileExistsError(f"Destination {destination} already exists")
            shutil.rmtree(destination)

        destination.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            tarball_path = tmpdir / "discord.tar.gz"
            self._download_tarball(tgz_url, tarball_path)
            with tarfile.open(tarball_path, "r:gz") as tar:
                _safe_extract(tar, tmpdir)

            extracted = tmpdir / "Discord"
            if not extracted.exists():
                raise ValueError("Extracted archive missing Discord directory")

            logger.debug("Moving extracted Discord directory to %s", destination)
            shutil.move(str(extracted), destination)

        discord_paths = DiscordPaths(destination)
        for required in (discord_paths.icon, discord_paths.executable, discord_paths.build_info):
            if not required.exists():
                raise FileNotFoundError(f"Expected file {required} not found after install")

        installed_version = DiscordVersion.from_build_info(discord_paths.build_info)
        if installed_version != version:
            raise ValueError(
                "Installed version does not match expected version",
            )

        icon_target = self._paths.data_dir / "discord.png"
        try:
            shutil.copy(discord_paths.icon, icon_target)
        except FileNotFoundError:
            logger.warning("Icon not found at %s; desktop entry may be missing icon", discord_paths.icon)

        return discord_paths

    def _download_tarball(self, url: str, dest: Path) -> None:
        logger.info("Downloading Discord from %s", url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=15, allow_redirects=True) as response:
            response.raise_for_status()
            with dest.open("wb") as f:
                for chunk_bytes in cast(Iterable[bytes], response.iter_content(chunk_size=CHUNK_SIZE)):
                    if not chunk_bytes:
                        continue
                    _ = f.write(chunk_bytes)
        logger.debug("Download complete: %s", dest)

    def link_current(self, version: DiscordVersion) -> None:
        target_dir = self._paths.discord_paths(version).dir
        symlink = self._paths.discord_current_version_dir_symlink
        symlink.parent.mkdir(parents=True, exist_ok=True)
        if symlink.exists() or symlink.is_symlink():
            logger.debug("Removing existing current link %s", symlink)
            symlink.unlink()
        logger.info("Linking %s to current install", target_dir)
        symlink.symlink_to(target_dir)

