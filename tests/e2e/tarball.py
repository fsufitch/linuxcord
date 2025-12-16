from __future__ import annotations

import shutil
import tarfile
from pathlib import Path

from linuxcord.types import DiscordVersion


def build_discord_tarball(dest_dir: Path, version: DiscordVersion) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    tarball_path = dest_dir / "discord_latest.tar.gz"

    contents_dir = dest_dir / "archive-contents"
    if contents_dir.exists():
        shutil.rmtree(contents_dir)

    discord_dir = contents_dir / "Discord"
    resources_dir = discord_dir / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)

    _ = (discord_dir / "Discord").write_text("#!/bin/sh\necho discord")
    _ = (discord_dir / "discord.png").write_text("icon")
    _ = (resources_dir / "build_info.json").write_text(
        f'{{"version": "{version.string}"}}'
    )

    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(discord_dir, arcname="Discord")

    return tarball_path
