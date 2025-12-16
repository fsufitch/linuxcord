from __future__ import annotations

from click.testing import CliRunner
from pytest_mock import MockerFixture

from linuxcord.cli import cli
from linuxcord.linuxcord import UpdateResult


def test_update_invokes_linuxcord_update_with_context(mocker: MockerFixture) -> None:
    runner = CliRunner()
    mock_update = mocker.patch(
        "linuxcord.cli.linuxcord.update",
        return_value=UpdateResult(None, None, False, None),
    )

    result = runner.invoke(
        cli,
        [
            "--discord-tgz-url",
            "http://example.com/dl",
            "--updates-url",
            "http://example.com/upd",
            "update",
            "--force",
        ],
    )

    assert result.exit_code == 0
    mock_update.assert_called_once_with(
        discord_tgz_url="http://example.com/dl",
        discord_updates_url="http://example.com/upd",
        force=True,
    )


def test_run_invokes_linuxcord_run_with_context(mocker: MockerFixture) -> None:
    runner = CliRunner()
    mock_run = mocker.patch("linuxcord.cli.linuxcord.run")

    result = runner.invoke(
        cli,
        [
            "--discord-tgz-url",
            "http://example.com/dl2",
            "--updates-url",
            "http://example.com/upd2",
            "run",
            "--no-update",
        ],
    )

    assert result.exit_code == 0
    mock_run.assert_called_once_with(
        discord_tgz_url="http://example.com/dl2",
        discord_updates_url="http://example.com/upd2",
        no_update=True,
    )


def test_status_invokes_linuxcord_status_and_prints(mocker: MockerFixture) -> None:
    runner = CliRunner()
    mock_status = mocker.patch(
        "linuxcord.cli.linuxcord.status",
        return_value=UpdateResult(None, None, False, None),
    )

    result = runner.invoke(
        cli,
        ["--updates-url", "http://example.com/upd3", "status"],
    )

    assert result.exit_code == 0
    mock_status.assert_called_once_with(discord_updates_url="http://example.com/upd3")
    assert "Installed version: none" in result.output
    assert "Latest online version: unknown" in result.output


def test_uninstall_invokes_linuxcord_uninstall(mocker: MockerFixture) -> None:
    runner = CliRunner()
    mock_uninstall = mocker.patch("linuxcord.cli.linuxcord.uninstall")

    result = runner.invoke(cli, ["uninstall", "--yes"])

    assert result.exit_code == 0
    mock_uninstall.assert_called_once_with()
    assert "linuxcord files removed" in result.output


def test_update_resolves_urls_from_environment_when_options_missing(
    mocker: MockerFixture,
) -> None:
    runner = CliRunner()
    mock_update = mocker.patch(
        "linuxcord.cli.linuxcord.update",
        return_value=UpdateResult(None, None, False, None),
    )

    result = runner.invoke(
        cli,
        ["update", "--force"],
        env={
            "LINUXCORD_DISCORD_TGZ_URL": "http://env.example.com/dl",
            "LINUXCORD_UPDATES_URL": "http://env.example.com/upd",
        },
    )

    assert result.exit_code == 0
    mock_update.assert_called_once_with(
        discord_tgz_url="http://env.example.com/dl",
        discord_updates_url="http://env.example.com/upd",
        force=True,
    )


def test_cli_arguments_override_environment(mocker: MockerFixture) -> None:
    runner = CliRunner()
    mock_run = mocker.patch("linuxcord.cli.linuxcord.run")

    result = runner.invoke(
        cli,
        [
            "--discord-tgz-url",
            "http://cli.example.com/dl",
            "--updates-url",
            "http://cli.example.com/upd",
            "run",
        ],
        env={
            "LINUXCORD_DISCORD_TGZ_URL": "http://env.example.com/dl",
            "LINUXCORD_UPDATES_URL": "http://env.example.com/upd",
        },
    )

    assert result.exit_code == 0
    mock_run.assert_called_once_with(
        discord_tgz_url="http://cli.example.com/dl",
        discord_updates_url="http://cli.example.com/upd",
        no_update=False,
    )
