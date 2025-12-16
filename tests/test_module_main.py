from __future__ import annotations

import runpy

from pytest_mock import MockerFixture


def test_module_main_invokes_cli_main(mocker: MockerFixture) -> None:
    mock_main = mocker.patch("linuxcord.cli.main")

    _ = runpy.run_module("linuxcord", run_name="__main__", alter_sys=True)

    mock_main.assert_called_once_with()
