from __future__ import annotations

import logging
import os
from pathlib import Path

from xdg.DesktopEntry import DesktopEntry
from xdg.Menu import MenuEntry

from linuxcord.paths import LinuxcordPaths


logger = logging.getLogger(__name__)
DESKTOP_NAME = "Linuxcord (Discord)"


class FreeDesktop:
    def __init__(self, paths: LinuxcordPaths):
        self._paths = paths

    @property
    def desktop_entry(self) -> Path:
        return self._paths.data_dir / "linuxcord.desktop"

    @property
    def application_symlink(self) -> Path:
        return self._paths.applications_dir / "linuxcord.desktop"

    def create_desktop_entry(self) -> Path:
        icon_path = self._paths.data_dir / "discord.png"
        self.desktop_entry.parent.mkdir(parents=True, exist_ok=True)

        desktop = DesktopEntry()
        desktop.addGroup("Desktop Entry")
        desktop.set("Version", "1.0")
        desktop.set("Type", "Application")
        desktop.set("Name", DESKTOP_NAME)
        desktop.set("Exec", "linuxcord run")
        desktop.set("Terminal", "false")
        desktop.set("Categories", "Network;InstantMessaging;")
        desktop.set("StartupWMClass", "discord")
        desktop.set("Icon", str(icon_path))
        logger.debug("Writing desktop entry to %s", self.desktop_entry)
        desktop.write(str(self.desktop_entry))
        return self.desktop_entry

    def create_application_symlink(self) -> Path:
        self.application_symlink.parent.mkdir(parents=True, exist_ok=True)
        if self.application_symlink.exists() or self.application_symlink.is_symlink():
            logger.debug("Removing existing desktop link at %s", self.application_symlink)
            self.application_symlink.unlink()

        if not self.desktop_entry.exists():
            raise FileNotFoundError(
                f"Desktop entry {self.desktop_entry} does not exist; create it first"
            )

        logger.debug(
            "Symlinking desktop entry from %s to %s",
            self.desktop_entry,
            self.application_symlink,
        )
        target = os.fspath(self.desktop_entry)
        self.application_symlink.symlink_to(target)

        menu_entry = MenuEntry(self.application_symlink.name, dir=str(self._paths.applications_dir))
        menu_entry.DesktopEntry = DesktopEntry(str(self.application_symlink))
        menu_entry.save()
        return self.application_symlink

