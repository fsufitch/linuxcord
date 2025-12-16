from __future__ import annotations

import io
import shutil
import tarfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
import requests

from linuxcord.installer import DiscordInstaller
from linuxcord.paths import LinuxcordPaths
from linuxcord.types import DiscordVersion
from tests.helpers import MockPyXDG


def write_tarball(
    dest: Path,
    version: str,
    *,
    include_icon: bool = True,
    build_version: str | None = None,
) -> None:
    contents_dir = dest.parent / "archive-contents"
    if contents_dir.exists():
        shutil.rmtree(contents_dir)
    discord_dir = contents_dir / "Discord"
    resources_dir = discord_dir / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    _ = (discord_dir / "Discord").write_text("#!/bin/sh\necho discord")
    if include_icon:
        _ = (discord_dir / "discord.png").write_text("icon")
    _ = (resources_dir / "build_info.json").write_text(
        f'{{"version": "{build_version or version}"}}'
    )

    with tarfile.open(dest, "w:gz") as tar:
        tar.add(discord_dir, arcname="Discord")


def write_malicious_tarball(dest: Path, member_name: str) -> None:
    with tarfile.open(dest, "w:gz") as tar:
        data = b"malicious"
        info = tarfile.TarInfo(member_name)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))


@pytest.fixture()
def session() -> Iterator[requests.Session]:
    with requests.Session() as session:
        yield session


def create_installer(
    tmp_path: Path, session: requests.Session
) -> tuple[DiscordInstaller, LinuxcordPaths]:
    xdg = MockPyXDG(
        xdg_data_home=tmp_path, xdg_cache_home=tmp_path, xdg_state_home=tmp_path
    )
    paths = LinuxcordPaths(xdg)
    installer = DiscordInstaller(paths, session)
    return installer, paths


def test_install_extracts_and_validates_archive(
    tmp_path: Path, mocker: MockerFixture, session: requests.Session
) -> None:
    installer, paths = create_installer(tmp_path, session)
    version = DiscordVersion("1.2.3")

    def download_tarball(_url: str, dest: Path) -> None:
        write_tarball(dest, version.string)

    download = mocker.patch.object(
        installer, "_download_tarball", side_effect=download_tarball
    )

    result = installer.install(version, "https://example.com/discord.tar.gz")

    download.assert_called_once()
    assert result.dir == paths.discord_paths(version).dir
    assert result.executable.exists()
    assert result.icon.exists()
    assert result.build_info.read_text() == '{"version": "1.2.3"}'
    assert (paths.data_dir / "discord.png").exists()


def test_install_overwrites_destination_when_forced(
    tmp_path: Path, mocker: MockerFixture, session: requests.Session
) -> None:
    installer, paths = create_installer(tmp_path, session)
    version = DiscordVersion("2.0.0")
    existing = paths.discord_paths(version).dir
    existing.mkdir(parents=True)
    stale_file = existing / "stale.txt"
    _ = stale_file.write_text("old")

    def download_tarball(_url: str, dest: Path) -> None:
        write_tarball(dest, version.string)

    download = mocker.patch.object(
        installer, "_download_tarball", side_effect=download_tarball
    )

    result = installer.install(
        version, "https://example.com/discord.tar.gz", force=True
    )

    download.assert_called_once()
    assert not stale_file.exists()
    assert result.executable.exists()


def test_install_refuses_existing_destination_without_force(
    tmp_path: Path, mocker: MockerFixture, session: requests.Session
) -> None:
    installer, paths = create_installer(tmp_path, session)
    version = DiscordVersion("3.0.0")
    destination = paths.discord_paths(version).dir
    destination.mkdir(parents=True)

    download = mocker.patch.object(installer, "_download_tarball")

    with pytest.raises(FileExistsError):
        _ = installer.install(version, "https://example.com/discord.tar.gz")

    download.assert_not_called()


def test_install_raises_when_discord_dir_missing(
    tmp_path: Path, mocker: MockerFixture, session: requests.Session
) -> None:
    installer, _paths = create_installer(tmp_path, session)
    version = DiscordVersion("4.0.0")

    download = mocker.patch.object(installer, "_download_tarball")

    def write_invalid_tarball(_url: str, dest: Path) -> None:
        with tarfile.open(dest, "w:gz") as tar:
            data = b"no discord here"
            info = tarfile.TarInfo("README.txt")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

    download.side_effect = write_invalid_tarball

    with pytest.raises(ValueError, match="Discord directory"):
        _ = installer.install(version, "https://example.com/discord.tar.gz")


def test_install_raises_when_required_files_missing(
    tmp_path: Path, mocker: MockerFixture, session: requests.Session
) -> None:
    installer, _paths = create_installer(tmp_path, session)
    version = DiscordVersion("5.0.0")

    def download_tarball(_url: str, dest: Path) -> None:
        write_tarball(dest, version.string, include_icon=False)

    download = mocker.patch.object(
        installer, "_download_tarball", side_effect=download_tarball
    )

    with pytest.raises(FileNotFoundError):
        _ = installer.install(version, "https://example.com/discord.tar.gz")

    download.assert_called_once()


def test_install_rejects_version_mismatch(
    tmp_path: Path, mocker: MockerFixture, session: requests.Session
) -> None:
    installer, _paths = create_installer(tmp_path, session)
    expected = DiscordVersion("6.0.0")

    def download_tarball(_url: str, dest: Path) -> None:
        write_tarball(dest, expected.string, build_version="7.0.0")

    download = mocker.patch.object(
        installer, "_download_tarball", side_effect=download_tarball
    )

    with pytest.raises(ValueError, match="Installed version does not match"):
        _ = installer.install(expected, "https://example.com/discord.tar.gz")

    download.assert_called_once()


def test_install_rejects_unsafe_tar_entries(
    tmp_path: Path, mocker: MockerFixture, session: requests.Session
) -> None:
    installer, paths = create_installer(tmp_path, session)
    version = DiscordVersion("8.0.0")

    def download_tarball(_url: str, dest: Path) -> None:
        write_malicious_tarball(dest, "../evil.txt")

    download = mocker.patch.object(
        installer, "_download_tarball", side_effect=download_tarball
    )

    with pytest.raises(ValueError):
        _ = installer.install(version, "https://example.com/discord.tar.gz")

    download.assert_called_once()
    assert not paths.discord_paths(version).dir.exists()


def test_link_current_updates_symlink(
    tmp_path: Path, session: requests.Session
) -> None:
    installer, paths = create_installer(tmp_path, session)
    paths.ensure_base_dirs()
    version_a = DiscordVersion("9.0.0")
    version_b = DiscordVersion("10.0.0")
    target_a = paths.discord_paths(version_a).dir
    target_b = paths.discord_paths(version_b).dir
    target_a.mkdir(parents=True)
    target_b.mkdir(parents=True)

    installer.link_current(version_a)
    assert paths.discord_current_version_dir_symlink.readlink() == target_a

    installer.link_current(version_b)
    assert paths.discord_current_version_dir_symlink.readlink() == target_b


def test_prune_removes_old_versions(tmp_path: Path, session: requests.Session) -> None:
    installer, paths = create_installer(tmp_path, session)
    paths.ensure_base_dirs()
    current_version = DiscordVersion("11.0.0")
    old_version = DiscordVersion("10.0.0")

    current_dir = paths.discord_paths(current_version).dir
    old_dir = paths.discord_paths(old_version).dir
    current_dir.mkdir(parents=True)
    old_dir.mkdir(parents=True)
    paths.discord_current_version_dir_symlink.symlink_to(current_dir)

    installer.prune_old_versions(current_version)

    assert current_dir.exists()
    assert not old_dir.exists()
    assert paths.discord_current_version_dir_symlink.exists()


def test_prune_respects_no_pruning_flag(
    tmp_path: Path, session: requests.Session
) -> None:
    installer, paths = create_installer(tmp_path, session)
    paths.ensure_base_dirs()
    current_version = DiscordVersion("12.0.0")
    old_version = DiscordVersion("12.0.1")

    current_dir = paths.discord_paths(current_version).dir
    old_dir = paths.discord_paths(old_version).dir
    current_dir.mkdir(parents=True)
    old_dir.mkdir(parents=True)
    paths.discord_current_version_dir_symlink.symlink_to(current_dir)
    no_pruning_flag = paths.discord_versions_dir / "NO_PRUNING"
    _ = no_pruning_flag.write_text("")

    installer.prune_old_versions(current_version)

    assert current_dir.exists()
    assert old_dir.exists()
    assert no_pruning_flag.exists()
