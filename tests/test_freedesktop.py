from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from linuxcord.freedesktop import DESKTOP_NAME, FreeDesktop
from linuxcord.paths import LinuxcordPaths

from .helpers import MockPyXDG


class StubDesktopEntry:
    def __init__(self) -> None:
        self.groups: list[str] = []
        self.set_calls: list[tuple[str, str]] = []
        self.written_paths: list[str] = []

    def addGroup(self, name: str) -> None:  # noqa: N802 - external API naming
        self.groups.append(name)

    def set(self, key: str, value: str) -> None:
        self.set_calls.append((key, value))

    def write(self, path: str) -> None:
        self.written_paths.append(path)


class StubMenuEntry:
    def __init__(self, name: str, dir: str) -> None:  # noqa: A002 - external API naming
        self.name: str = name
        self.dir: str = dir
        self.DesktopEntry: object | None = None
        self.saved: bool = False

    def save(self) -> None:
        self.saved = True


def test_create_desktop_entry_writes_expected_values(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path / "data")
    freedesktop = FreeDesktop(LinuxcordPaths(xdg))

    desktop_entry_path = freedesktop.desktop_entry
    desktop = StubDesktopEntry()
    _ = mocker.patch("linuxcord.freedesktop.DesktopEntry", return_value=desktop)

    result = freedesktop.create_desktop_entry()

    assert result == desktop_entry_path
    assert desktop_entry_path.parent.exists()

    assert desktop.groups == ["Desktop Entry"]
    assert ("Version", "1.0") in desktop.set_calls
    assert ("Type", "Application") in desktop.set_calls
    assert ("Name", DESKTOP_NAME) in desktop.set_calls
    assert ("Exec", "linuxcord run") in desktop.set_calls
    assert ("Terminal", "false") in desktop.set_calls
    assert ("Categories", "Network;InstantMessaging;") in desktop.set_calls
    assert ("StartupWMClass", "discord") in desktop.set_calls
    assert (
        "Icon",
        str(tmp_path / "data" / "linuxcord" / "discord.png"),
    ) in desktop.set_calls
    assert desktop.written_paths == [str(desktop_entry_path)]


def test_create_application_symlink_requires_desktop_entry(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path / "data")
    freedesktop = FreeDesktop(LinuxcordPaths(xdg))

    _ = mocker.patch("linuxcord.freedesktop.MenuEntry", StubMenuEntry)
    _ = mocker.patch("linuxcord.freedesktop.DesktopEntry", StubDesktopEntry)

    with pytest.raises(FileNotFoundError, match="Desktop entry .* does not exist"):
        _ = freedesktop.create_application_symlink()

    assert not freedesktop.application_symlink.exists()


def test_create_application_symlink_replaces_existing_and_saves_menu_entry(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    xdg = MockPyXDG(xdg_data_home=tmp_path / "data")
    freedesktop = FreeDesktop(LinuxcordPaths(xdg))
    desktop_entry_path = freedesktop.desktop_entry
    application_symlink_path = freedesktop.application_symlink

    _ = desktop_entry_path.parent.mkdir(parents=True, exist_ok=True)
    _ = desktop_entry_path.write_text("[Desktop Entry]")

    _ = application_symlink_path.parent.mkdir(parents=True, exist_ok=True)
    _ = application_symlink_path.write_text("stale entry")

    menu_entries: list[StubMenuEntry] = []

    def make_menu_entry(name: str, dir: str) -> StubMenuEntry:
        entry = StubMenuEntry(name, dir)
        menu_entries.append(entry)
        return entry

    _ = mocker.patch("linuxcord.freedesktop.MenuEntry", side_effect=make_menu_entry)

    desktop_entry_loader = StubDesktopEntry()
    _ = mocker.patch(
        "linuxcord.freedesktop.DesktopEntry", return_value=desktop_entry_loader
    )

    result = freedesktop.create_application_symlink()

    assert result == application_symlink_path
    assert application_symlink_path.is_symlink()
    assert application_symlink_path.resolve() == desktop_entry_path

    assert len(menu_entries) == 1
    menu_entry = menu_entries[0]
    assert menu_entry.name == application_symlink_path.name
    assert menu_entry.dir == str(freedesktop.application_symlink.parent)
    assert menu_entry.DesktopEntry is desktop_entry_loader
    assert menu_entry.saved
