from __future__ import annotations

from pathlib import Path
from typing import cast

import requests
import linuxcord.linuxcord as linuxcord
from linuxcord.launcher import DiscordLauncher
from linuxcord.paths import LinuxcordPaths
from linuxcord.types import DiscordVersion
from pytest_mock import MockerFixture
from tests.e2e.server import discord_test_server
from tests.e2e.tarball import build_discord_tarball
from tests.helpers import MockPyXDG


def create_xdg(tmp_path: Path) -> MockPyXDG:
    base = tmp_path / "xdg"
    return MockPyXDG(
        xdg_data_home=base / "data",
        xdg_cache_home=base / "cache",
        xdg_state_home=base / "state",
        runtime_dir=base / "runtime",
    )


def test_update_and_status_use_remote_endpoints(tmp_path: Path) -> None:
    version = DiscordVersion("11.22.33")
    tarball_path = build_discord_tarball(tmp_path, version)
    xdg = create_xdg(tmp_path)
    paths = LinuxcordPaths(xdg)

    with (
        discord_test_server(version, tarball_path) as base_url,
        requests.Session() as session,
    ):
        result = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
        )

        assert result.updated is True
        assert result.installed_version == version
        assert result.latest_version == version
        assert paths.discord_paths(version).executable.exists()
        current_path = paths.discord_current_version_dir_symlink.resolve(strict=True)
        assert current_path == paths.discord_paths(version).dir
        assert paths.data_dir.joinpath("linuxcord.desktop").exists()
        assert paths.applications_dir.joinpath("linuxcord.desktop").exists()

        status_result = linuxcord.status(
            xdg=xdg,
            session=session,
            discord_updates_url=f"{base_url}/update_version",
        )

        assert status_result.installed_version == version
        assert status_result.latest_version == version
        assert status_result.current_path == paths.discord_paths(version).dir


def test_run_launches_current_version(tmp_path: Path, mocker: MockerFixture) -> None:
    version = DiscordVersion("20.40.60")
    tarball_path = build_discord_tarball(tmp_path, version)
    xdg = create_xdg(tmp_path)

    with (
        discord_test_server(version, tarball_path) as base_url,
        requests.Session() as session,
    ):
        _ = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
        )

        launch = mocker.patch.object(DiscordLauncher, "launch", autospec=True)

        linuxcord.run(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
            no_update=True,
        )

        paths = LinuxcordPaths(xdg)
        launch.assert_called_once()
        called_self, called_version = cast(
            tuple[DiscordLauncher, DiscordVersion], launch.call_args.args[:2]
        )
        assert isinstance(called_self, DiscordLauncher)
        assert called_version == version
        assert paths.discord_current_version_dir_symlink.exists()


def test_uninstall_removes_installed_files(tmp_path: Path) -> None:
    version = DiscordVersion("9.9.9")
    tarball_path = build_discord_tarball(tmp_path, version)
    xdg = create_xdg(tmp_path)
    paths = LinuxcordPaths(xdg)

    with (
        discord_test_server(version, tarball_path) as base_url,
        requests.Session() as session,
    ):
        _ = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
        )

    linuxcord.uninstall(xdg=xdg)

    for directory in (
        paths.discord_versions_dir,
        paths.cache_dir,
        paths.state_dir,
        paths.data_dir,
    ):
        assert not directory.exists()


def test_update_prunes_previous_version(tmp_path: Path) -> None:
    first_version = DiscordVersion("1.2.3")
    second_version = DiscordVersion("1.2.4")

    first_tarball = build_discord_tarball(tmp_path / "first", first_version)
    second_tarball = build_discord_tarball(tmp_path / "second", second_version)

    xdg = create_xdg(tmp_path)
    paths = LinuxcordPaths(xdg)

    with (
        discord_test_server(first_version, first_tarball) as base_url,
        requests.Session() as session,
    ):
        _ = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
        )

    assert paths.discord_paths(first_version).dir.exists()

    with (
        discord_test_server(second_version, second_tarball) as base_url,
        requests.Session() as session,
    ):
        _ = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
        )

    current_dir = paths.discord_paths(second_version).dir
    old_dir = paths.discord_paths(first_version).dir

    assert current_dir.exists()
    assert not old_dir.exists()
    assert paths.discord_current_version_dir_symlink.resolve(strict=True) == current_dir


def test_update_respects_no_pruning_flag(tmp_path: Path) -> None:
    first_version = DiscordVersion("1.2.3")
    second_version = DiscordVersion("1.2.4")

    first_tarball = build_discord_tarball(tmp_path / "first", first_version)
    second_tarball = build_discord_tarball(tmp_path / "second", second_version)

    xdg = create_xdg(tmp_path)
    paths = LinuxcordPaths(xdg)

    with (
        discord_test_server(first_version, first_tarball) as base_url,
        requests.Session() as session,
    ):
        _ = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
        )

    no_pruning_flag = paths.discord_versions_dir / "NO_PRUNING"
    _ = no_pruning_flag.write_text("")

    with (
        discord_test_server(second_version, second_tarball) as base_url,
        requests.Session() as session,
    ):
        _ = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url=f"{base_url}/download/discord_latest.tar.gz",
            discord_updates_url=f"{base_url}/update_version",
        )

    current_dir = paths.discord_paths(second_version).dir
    old_dir = paths.discord_paths(first_version).dir

    assert current_dir.exists()
    assert old_dir.exists()
    assert no_pruning_flag.exists()
    assert paths.discord_current_version_dir_symlink.resolve(strict=True) == current_dir
