from pathlib import Path
from types import SimpleNamespace

import requests
from pytest_mock import MockerFixture

from linuxcord import linuxcord
from linuxcord.paths import LinuxcordPaths
from linuxcord.types import DiscordVersion
from tests.helpers import MockPyXDG


def test_update_prunes_after_install(mocker: MockerFixture, tmp_path: Path) -> None:
    xdg = MockPyXDG(
        xdg_data_home=tmp_path / "data",
        xdg_cache_home=tmp_path / "cache",
        xdg_state_home=tmp_path / "state",
    )
    paths = LinuxcordPaths(xdg)

    latest_version = DiscordVersion("13.0.0")

    class LocalVersionerStub:
        def get_current_version(self) -> DiscordVersion | None:
            return DiscordVersion("12.9.9")

    class OnlineVersionerStub:
        def get_latest_version(self) -> DiscordVersion | None:
            return latest_version

        def get_latest_download_url(self) -> str:
            return "https://example.com/discord.tar.gz"

    mock_install_result = SimpleNamespace(dir=paths.discord_paths(latest_version).dir)

    class InstallerStub:
        def __init__(self) -> None:
            self.pruned_versions: list[DiscordVersion] = []

        def install(
            self,
            version: DiscordVersion,
            download_url: str,
            *,
            force: bool = False,
        ) -> SimpleNamespace:
            _ = version
            _ = download_url
            _ = force
            return mock_install_result

        def link_current(self, version: DiscordVersion) -> None:
            _ = version

        def prune_old_versions(self, version: DiscordVersion) -> None:
            self.pruned_versions.append(version)

    class DesktopStub:
        def create_desktop_entry(self) -> Path:
            return paths.data_dir / "linuxcord.desktop"

        def create_application_symlink(self) -> Path:
            return paths.data_dir / "linuxcord.desktop"

    installer_stub = InstallerStub()

    _ = mocker.patch(
        "linuxcord.linuxcord.LocalVersioner", return_value=LocalVersionerStub()
    )
    _ = mocker.patch(
        "linuxcord.linuxcord.OnlineVersioner", return_value=OnlineVersionerStub()
    )
    _ = mocker.patch(
        "linuxcord.linuxcord.DiscordInstaller", return_value=installer_stub
    )
    _ = mocker.patch("linuxcord.linuxcord.FreeDesktop", return_value=DesktopStub())

    with requests.Session() as session:
        _ = linuxcord.update(
            xdg=xdg,
            session=session,
            discord_tgz_url="https://example.com/discord.tar.gz",
            discord_updates_url="https://example.com/updates.json",
        )

    assert installer_stub.pruned_versions == [latest_version]
