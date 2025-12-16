from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

import requests
from xdg import BaseDirectory

from linuxcord import DEFAULT_DISCORD_TGZ_URL, DEFAULT_UPDATES_URL
from linuxcord.freedesktop import FreeDesktop
from linuxcord.installer import DiscordInstaller
from linuxcord.launcher import DiscordLauncher
from linuxcord.paths import LinuxcordPaths
from linuxcord.types import DiscordVersion, PyXDG
from linuxcord.versions import LocalVersioner, OnlineVersioner


logger = logging.getLogger(__name__)


@dataclass
class UpdateResult:
    installed_version: DiscordVersion | None
    latest_version: DiscordVersion | None
    updated: bool
    current_path: Path | None


def _build_paths(xdg: PyXDG | None) -> LinuxcordPaths:
    return LinuxcordPaths(xdg or BaseDirectory)


def update(
    *,
    xdg: PyXDG | None = None,
    session: requests.Session | None = None,
    discord_tgz_url: str | None = None,
    discord_updates_url: str | None = None,
    force: bool = False,
) -> UpdateResult:
    linuxcord_paths = _build_paths(xdg)
    linuxcord_paths.ensure_base_dirs()
    lock = linuxcord_paths.acquire_lock()
    try:
        logger.debug("Starting update process")
        session = session or requests.Session()
        discord_tgz_url = discord_tgz_url or DEFAULT_DISCORD_TGZ_URL
        discord_updates_url = discord_updates_url or DEFAULT_UPDATES_URL

        local_versioner = LocalVersioner(linuxcord_paths)
        installed_version = local_versioner.get_current_version()

        online_versioner = OnlineVersioner(discord_tgz_url, discord_updates_url, session)
        latest_version = online_versioner.get_latest_version()

        logger.info("Installed version: %s", installed_version.string if installed_version else "none")
        logger.info("Latest available version: %s", latest_version.string if latest_version else "unknown")

        needs_install = installed_version is None
        needs_update = latest_version is not None and installed_version != latest_version

        if not force and not needs_install and not needs_update:
            current_path = (
                linuxcord_paths.discord_current_version_dir_symlink.resolve(strict=False)
                if linuxcord_paths.discord_current_version_dir_symlink.exists()
                else None
            )
            return UpdateResult(installed_version, latest_version, False, current_path)

        if latest_version is None and not force:
            current_path = (
                linuxcord_paths.discord_current_version_dir_symlink.resolve(strict=False)
                if linuxcord_paths.discord_current_version_dir_symlink.exists()
                else None
            )
            return UpdateResult(installed_version, latest_version, False, current_path)

        if latest_version is None:
            raise RuntimeError("Cannot determine the latest Discord version to install")

        installer = DiscordInstaller(linuxcord_paths)
        download_url = online_versioner.get_latest_download_url()
        target_version = latest_version

        discord_paths = installer.install(target_version, download_url, force=force)
        installer.link_current(target_version)

        desktop = FreeDesktop(linuxcord_paths)
        desktop.create_desktop_entry()
        desktop.create_application_symlink()

        return UpdateResult(target_version, latest_version or target_version, True, discord_paths.dir)
    finally:
        lock.release()


def status(
    *,
    xdg: PyXDG | None = None,
    session: requests.Session | None = None,
    discord_updates_url: str | None = None,
) -> UpdateResult:
    linuxcord_paths = _build_paths(xdg)
    linuxcord_paths.ensure_base_dirs()
    local_versioner = LocalVersioner(linuxcord_paths)
    session = session or requests.Session()
    discord_updates_url = discord_updates_url or DEFAULT_UPDATES_URL

    installed_version = local_versioner.get_current_version()
    current_path = (
        linuxcord_paths.discord_current_version_dir_symlink.resolve(strict=True)
        if linuxcord_paths.discord_current_version_dir_symlink.exists()
        else None
    )

    online_versioner = OnlineVersioner(DEFAULT_DISCORD_TGZ_URL, discord_updates_url, session)
    latest_version = online_versioner.get_latest_version()
    return UpdateResult(installed_version, latest_version, False, current_path)


def run(*, xdg: PyXDG | None = None) -> None:
    linuxcord_paths = _build_paths(xdg)
    local_versioner = LocalVersioner(linuxcord_paths)
    current_version = local_versioner.get_current_version()
    if current_version is None:
        raise RuntimeError("Discord is not installed. Run 'linuxcord update' first.")
    launcher = DiscordLauncher(linuxcord_paths)
    launcher.launch(current_version)


def uninstall(*, xdg: PyXDG | None = None) -> None:
    linuxcord_paths = _build_paths(xdg)
    desktop = FreeDesktop(linuxcord_paths)

    for path in (desktop.application_symlink, desktop.desktop_entry):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    for directory in (
        linuxcord_paths.discord_versions_dir,
        linuxcord_paths.cache_dir,
        linuxcord_paths.state_dir,
        linuxcord_paths.data_dir,
    ):
        shutil.rmtree(directory, ignore_errors=True)
    logger.info("Uninstalled linuxcord-managed files")

