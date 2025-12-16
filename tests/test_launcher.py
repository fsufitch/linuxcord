from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from pytest_mock import MockerFixture

from linuxcord.launcher import DiscordLauncher
from linuxcord.paths import DiscordPaths, LinuxcordPaths
from linuxcord.types import DiscordVersion


def test_launch_rejects_root(mocker: MockerFixture) -> None:
    paths = mocker.create_autospec(LinuxcordPaths, instance=True)
    launcher = DiscordLauncher(cast(LinuxcordPaths, paths), popen=mocker.Mock())
    _ = mocker.patch("os.geteuid", return_value=0)

    with pytest.raises(RuntimeError, match="Do not run linuxcord as root"):
        launcher.launch(DiscordVersion("1.2.3"))

    paths.discord_paths.assert_not_called()  # pyright: ignore[reportAny]


def test_launch_requires_executable(tmp_path: Path, mocker: MockerFixture) -> None:
    install_dir = tmp_path / "install"

    discord_paths = DiscordPaths(install_dir)

    paths = mocker.create_autospec(LinuxcordPaths, instance=True)
    paths.discord_paths.return_value = discord_paths  # pyright: ignore[reportAny]
    popen = mocker.Mock()
    launcher = DiscordLauncher(cast(LinuxcordPaths, paths), popen=popen)
    _ = mocker.patch("os.geteuid", return_value=1000)

    version = DiscordVersion("1.0.0")

    with pytest.raises(RuntimeError, match="Discord executable not found"):
        launcher.launch(version)

    popen.assert_not_called()
    paths.discord_paths.assert_called_once_with(version)  # pyright: ignore[reportAny]


def test_launch_invokes_popen_with_expected_values(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    install_dir = tmp_path / "install"
    install_dir.mkdir(parents=True)
    executable = install_dir / "Discord"
    _ = executable.write_text("")

    discord_paths = DiscordPaths(install_dir)

    paths = mocker.create_autospec(LinuxcordPaths, instance=True)
    paths.discord_paths.return_value = discord_paths  # pyright: ignore[reportAny]
    popen = mocker.Mock()
    launcher = DiscordLauncher(cast(LinuxcordPaths, paths), popen=popen)
    _ = mocker.patch("os.geteuid", return_value=1000)

    version = DiscordVersion("2.3.4")
    launcher.launch(version)

    paths.discord_paths.assert_called_once_with(version)  # pyright: ignore[reportAny]
    popen.assert_called_once()
    call = popen.call_args
    assert call.args[0] == [str(executable)]
    assert call.kwargs["cwd"] == str(install_dir)
    env = cast(dict[str, str], call.kwargs["env"])
    assert "PATH" in env
