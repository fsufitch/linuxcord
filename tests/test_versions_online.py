from __future__ import annotations

from typing import cast

import requests
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from linuxcord.types import DiscordVersion
from linuxcord.versions import OnlineVersioner


def test_get_latest_version_from_updates_api(mocker: MockerFixture) -> None:
    session: MagicMock = mocker.MagicMock(spec=requests.Session)
    response: MagicMock = mocker.MagicMock(spec=requests.Response)
    response_json = cast(MagicMock, response.json)
    response_raise_for_status = cast(MagicMock, response.raise_for_status)
    response_json.return_value = {"name": "3.4.5"}
    get = cast(MagicMock, session.get)
    get.return_value = response

    versioner = OnlineVersioner("tgz-url", "updates-url", session)

    assert versioner.get_latest_version() == DiscordVersion("3.4.5")
    get.assert_called_once_with("updates-url", timeout=10)
    response_raise_for_status.assert_called_once_with()
    response_json.assert_called_once_with()
    cast(MagicMock, session.head).assert_not_called()


def test_get_latest_version_falls_back_to_download_url(mocker: MockerFixture) -> None:
    session: MagicMock = mocker.MagicMock(spec=requests.Session)
    get = cast(MagicMock, session.get)
    get.side_effect = RuntimeError("API down")
    head_response: MagicMock = mocker.MagicMock(spec=requests.Response)
    head_response.url = "https://example.com/discord-5.6.7.tar.gz"
    head = cast(MagicMock, session.head)
    head.return_value = head_response
    head_raise_for_status = cast(MagicMock, head_response.raise_for_status)
    head_close = cast(MagicMock, head_response.close)

    versioner = OnlineVersioner("tgz-url", "updates-url", session)

    assert versioner.get_latest_version() == DiscordVersion("5.6.7")
    get.assert_called_once_with("updates-url", timeout=10)
    head.assert_called_once_with(
        "tgz-url", allow_redirects=True, timeout=10, stream=True
    )
    head_raise_for_status.assert_called_once_with()
    head_close.assert_called_once_with()


def test_get_latest_version_returns_none_on_failures(mocker: MockerFixture) -> None:
    session: MagicMock = mocker.MagicMock(spec=requests.Session)
    get = cast(MagicMock, session.get)
    head = cast(MagicMock, session.head)
    get.side_effect = RuntimeError("API down")
    head.side_effect = RuntimeError("HEAD down")

    versioner = OnlineVersioner("tgz-url", "updates-url", session)

    assert versioner.get_latest_version() is None
    get.assert_called_once_with("updates-url", timeout=10)
    head.assert_called_once_with(
        "tgz-url", allow_redirects=True, timeout=10, stream=True
    )


def test_get_latest_download_url_returns_final_url(mocker: MockerFixture) -> None:
    session: MagicMock = mocker.MagicMock(spec=requests.Session)
    head_response: MagicMock = mocker.MagicMock(spec=requests.Response)
    head_response.url = "https://cdn.discordapp.com/client/stable.tar.gz"
    head = cast(MagicMock, session.head)
    head.return_value = head_response
    head_raise_for_status = cast(MagicMock, head_response.raise_for_status)
    head_close = cast(MagicMock, head_response.close)

    versioner = OnlineVersioner("tgz-url", "updates-url", session)

    assert versioner.get_latest_download_url() == (
        "https://cdn.discordapp.com/client/stable.tar.gz"
    )
    head.assert_called_once_with(
        "tgz-url", allow_redirects=True, timeout=10, stream=True
    )
    head_raise_for_status.assert_called_once_with()
    head_close.assert_called_once_with()
