from __future__ import annotations

import logging
import shutil

from linuxcord import config as config_module
from linuxcord import paths
from linuxcord.desktop import create_desktop_entry, install_desktop_entry
from linuxcord.launcher import launch_discord
from linuxcord.updater import UpdateResult, update_if_needed, write_state

logger = logging.getLogger(__name__)

__all__ = ["init", "update", "run", "status", "uninstall", "UpdateResult"]


def init(
    force: bool = False,
    discord_tgz_url: str | None = None,
    updates_url: str | None = None,
) -> UpdateResult:
    paths.ensure_base_dirs()
    result = update_if_needed(
        discord_tgz_url=discord_tgz_url, updates_url=updates_url, force=force
    )
    write_state(
        result.installed_version or result.latest_version, result.latest_version
    )
    icon_path = paths.data_dir() / "discord.png"
    entry_path = create_desktop_entry(icon_path)
    _ = install_desktop_entry(entry_path)
    return result


def update(
    discord_tgz_url: str | None = None, updates_url: str | None = None
) -> UpdateResult:
    result = update_if_needed(discord_tgz_url=discord_tgz_url, updates_url=updates_url)
    write_state(result.installed_version, result.latest_version)
    return result


def run(
    discord_tgz_url: str | None = None, updates_url: str | None = None
) -> UpdateResult:
    result = update(discord_tgz_url=discord_tgz_url, updates_url=updates_url)
    launch_discord()
    return result


def status(
    discord_tgz_url: str | None = None, updates_url: str | None = None
) -> UpdateResult:
    cfg = config_module.resolve(discord_tgz_url, updates_url)
    paths.ensure_base_dirs()
    return update_if_needed(
        discord_tgz_url=cfg.discord_tgz_url,
        updates_url=cfg.updates_url,
        force=False,
        perform_install=False,
    )


def uninstall() -> None:
    data = paths.data_dir()
    cache = paths.cache_dir()
    state = paths.state_dir()
    desktop = paths.desktop_entry_path()
    desktop_install = paths.desktop_install_path()

    for path in (desktop_install, desktop):
        try:
            logger.debug("Removing desktop entry %s", path)
            path.unlink()
        except FileNotFoundError:
            pass
    for directory in (data, cache, state):
        logger.debug("Removing directory %s", directory)
        shutil.rmtree(directory, ignore_errors=True)
    logger.info("Uninstalled linuxcord-managed files")
