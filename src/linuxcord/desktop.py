from __future__ import annotations

import logging
import shutil
from pathlib import Path

from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry
from xdg.Menu import MenuEntry

from linuxcord import paths


DESKTOP_NAME = "Linuxcord (Discord)"
LOGGER = logging.getLogger(__name__)


def create_desktop_entry(icon_path: Path) -> Path:
    entry_path = paths.desktop_entry_path()
    entry_path.parent.mkdir(parents=True, exist_ok=True)

    if not icon_path.exists():
        LOGGER.warning(
            "Icon file %s does not exist; desktop entry will reference a missing icon.",
            icon_path,
        )

    desktop = DesktopEntry()
    desktop.set("Version", "1.0")
    desktop.set("Type", "Application")
    desktop.set("Name", DESKTOP_NAME)
    desktop.set("Exec", "linuxcord run")
    desktop.set("Terminal", "false")
    desktop.set("Categories", "Network;InstantMessaging;")
    desktop.set("StartupWMClass", "discord")
    desktop.set("Icon", str(icon_path))
    LOGGER.debug("Writing desktop entry to %s", entry_path)
    desktop.write(str(entry_path))
    return entry_path


def install_desktop_entry(entry_path: Path | None = None) -> Path:
    if entry_path is None:
        entry_path = paths.desktop_entry_path()
    target_path = paths.desktop_install_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() or target_path.is_symlink():
        LOGGER.debug("Removing existing desktop entry at %s", target_path)
        target_path.unlink()

    LOGGER.debug("Copying desktop entry from %s to %s", entry_path, target_path)
    _ = shutil.copy(entry_path, target_path)

    applications_dir = Path(BaseDirectory.save_data_path("applications"))
    LOGGER.debug("Saving menu entry in %s", applications_dir)
    menu_entry = MenuEntry(target_path.name, dir=str(applications_dir))
    menu_entry.DesktopEntry = DesktopEntry(str(target_path))
    menu_entry.save()
    return target_path
