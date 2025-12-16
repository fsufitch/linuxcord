from __future__ import annotations

import json
import logging
import re
import shutil
import tarfile
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import requests
from linuxcord import config as config_module
from linuxcord import paths
from linuxcord.lock import exclusive_lock

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192
DOWNLOAD_TIMEOUT = 15
UPDATES_TIMEOUT = 10


@dataclass
class UpdateResult:
    installed_version: str | None
    latest_version: str | None
    updated: bool
    current_path: Path | None


def _read_build_version(build_info: Path) -> str | None:
    if not build_info.exists():
        logger.debug("build_info.json does not exist at %s", build_info)
        return None
    try:
        data = cast(dict[str, object], json.loads(build_info.read_text()))
        version = data.get("version")
        if isinstance(version, str):
            return version
    except Exception:
        logger.debug("Failed to read build_info.json at %s", build_info)
        return None
    return None


def get_current_install() -> Path | None:
    current = paths.current_symlink()
    if current.is_symlink() or current.exists():
        try:
            resolved = current.resolve(strict=True)
            logger.debug("Resolved current install to %s", resolved)
            return resolved
        except FileNotFoundError:
            logger.debug("Current symlink %s is broken", current)
            return None
    return None


def get_installed_version() -> str | None:
    current = get_current_install()
    if current is None:
        return None
    build_info = current / "Discord/resources/build_info.json"
    return _read_build_version(build_info)


def _extract_version_from_url(url: str) -> str | None:
    patterns = [
        r"/([0-9]+\.[0-9]+\.[0-9]+)/",
        r"-([0-9]+\.[0-9]+\.[0-9]+)\.tar\.gz",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def resolve_latest_version(updates_url: str, discord_tgz_url: str) -> str | None:
    logger.debug("Fetching latest version from %s", updates_url)
    try:
        response = requests.get(updates_url, timeout=UPDATES_TIMEOUT)
        logger.debug("Updates API status code: %s", response.status_code)
        response.raise_for_status()
        data = cast(dict[str, object], response.json())
        name = data.get("name")
        if isinstance(name, str):
            logger.debug("Latest version from updates API: %s", name)
            return name
    except Exception as exc:
        logger.debug("Updates API failed: %s", exc)

    logger.debug("Falling back to resolving version from download URL")
    try:
        resp = requests.get(
            discord_tgz_url, stream=True, allow_redirects=True, timeout=UPDATES_TIMEOUT
        )
        logger.debug("Download URL status code: %s", resp.status_code)
        resp.raise_for_status()
        final_url = resp.url
        resp.close()
        logger.debug("Resolved download redirect to %s", final_url)
        return _extract_version_from_url(final_url)
    except Exception as exc:
        logger.debug("Could not resolve version from redirect: %s", exc)
        return None


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


def _download_tarball(url: str, dest: Path) -> Path:
    logger.info("Downloading Discord from %s", url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.debug("Downloading to %s", dest)
    with requests.get(
        url, stream=True, timeout=DOWNLOAD_TIMEOUT, allow_redirects=True
    ) as response:
        logger.debug("Download request status code: %s", response.status_code)
        response.raise_for_status()
        total = response.headers.get("Content-Length")
        total_bytes = int(total) if total and total.isdigit() else None
        downloaded = 0
        logger.debug("Response Content-Length: %s", total_bytes)
        with dest.open("wb") as f:
            for chunk_bytes in cast(
                Iterable[bytes], response.iter_content(chunk_size=CHUNK_SIZE)
            ):
                if not chunk_bytes:
                    continue
                _ = f.write(chunk_bytes)
                downloaded += len(chunk_bytes)
                if total_bytes:
                    percent = downloaded * 100 // total_bytes
                    logger.info("Download progress: %s%%", percent)
                else:
                    logger.info("Downloaded %s bytes", downloaded)
    logger.info("Download complete: %s", dest)
    return dest


def _extract_and_install(tarball: Path) -> str:
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        logger.debug("Opened temporary directory %s", tmpdir)
        with tarfile.open(tarball, "r:gz") as tar:
            _safe_extract(tar, tmpdir)

        discord_dir = tmpdir / "Discord"
        if not discord_dir.exists():
            raise ValueError("Extracted archive missing Discord directory")

        build_info = discord_dir / "resources/build_info.json"
        version = _read_build_version(build_info)
        if not version:
            raise ValueError("Could not determine version from build_info.json")

        destination = paths.versions_dir() / f"Discord-{version}"
        if destination.exists():
            logger.debug("Removing existing destination %s", destination)
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Moving extracted Discord to %s", destination)
        _ = shutil.move(str(discord_dir), destination)

        _update_current_symlink(destination)
        _copy_icon(destination)
        _remove_other_versions(destination)
        return version


def _update_current_symlink(target: Path) -> None:
    current = paths.current_symlink()
    current.parent.mkdir(parents=True, exist_ok=True)
    if current.exists() or current.is_symlink():
        logger.debug("Removing existing current symlink at %s", current)
        current.unlink()
    current.symlink_to(target)
    logger.info("Updated current symlink to %s", target)


def _copy_icon(install_dir: Path) -> None:
    icon_candidates = [
        install_dir / "discord.png",
        install_dir / "Discord.png",
        install_dir / "resources/discord.png",
    ]
    icon_target = paths.data_dir() / "discord.png"
    for candidate in icon_candidates:
        if candidate.exists():
            _ = shutil.copy(candidate, icon_target)
            logger.debug("Copied icon from %s to %s", candidate, icon_target)
            break
    else:
        logger.debug("No icon found in %s; skipping icon copy", install_dir)


def _remove_other_versions(active_version: Path) -> None:
    versions_path = paths.versions_dir()
    if not versions_path.exists():
        return

    try:
        active_resolved = active_version.resolve(strict=True)
    except FileNotFoundError:
        active_resolved = active_version

    for candidate in versions_path.iterdir():
        if not candidate.is_dir() or not candidate.name.startswith("Discord-"):
            continue
        if candidate.resolve() == active_resolved:
            continue
        shutil.rmtree(candidate, ignore_errors=True)
        logger.debug("Removed old version %s", candidate)


def update_if_needed(
    discord_tgz_url: str | None = None,
    updates_url: str | None = None,
    force: bool = False,
    perform_install: bool = True,
) -> UpdateResult:
    cfg = config_module.resolve(discord_tgz_url, updates_url)
    paths.ensure_base_dirs()
    with exclusive_lock():
        installed_version = get_installed_version()
        latest_version = resolve_latest_version(cfg.updates_url, cfg.discord_tgz_url)
        logger.info("Installed version: %s", installed_version or "none")
        logger.info("Latest available version: %s", latest_version or "unknown")

        needs_install = installed_version is None
        needs_update = (
            latest_version is not None and installed_version != latest_version
        )

        if not force and not needs_install and not needs_update:
            logger.debug("No update needed; installed version matches latest")
            current = get_current_install()
            return UpdateResult(installed_version, latest_version, False, current)

        if not force and latest_version is None and installed_version is not None:
            logger.debug("Latest version unknown; skipping update without force flag")
            current = get_current_install()
            return UpdateResult(installed_version, latest_version, False, current)

        if not perform_install:
            logger.debug("Perform_install is False; returning current status only")
            current = get_current_install()
            return UpdateResult(installed_version, latest_version, False, current)

        tarball_path = paths.cache_dir() / "discord.tar.gz"
        _ = _download_tarball(cfg.discord_tgz_url, tarball_path)
        new_version = _extract_and_install(tarball_path)
        current = get_current_install()
        return UpdateResult(new_version, latest_version or new_version, True, current)


def write_state(installed_version: str | None, latest_version: str | None) -> None:
    state_path = paths.state_file()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "installed_version": installed_version,
        "latest_version": latest_version,
    }
    logger.debug("Writing state to %s", state_path)
    _ = state_path.write_text(json.dumps(payload, indent=2))
