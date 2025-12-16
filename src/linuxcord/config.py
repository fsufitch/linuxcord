from __future__ import annotations

import os
from dataclasses import dataclass

from linuxcord import DEFAULT_DISCORD_TGZ_URL, DEFAULT_UPDATES_URL


@dataclass
class ResolvedConfig:
    discord_tgz_url: str
    updates_url: str


def resolve(
    discord_tgz_url: str | None = None, updates_url: str | None = None
) -> ResolvedConfig:
    env_discord = os.environ.get("LINUXCORD_DISCORD_TGZ_URL")
    env_updates = os.environ.get("LINUXCORD_UPDATES_URL")

    discord_url = discord_tgz_url or env_discord or DEFAULT_DISCORD_TGZ_URL
    updates = updates_url or env_updates or DEFAULT_UPDATES_URL
    return ResolvedConfig(discord_tgz_url=discord_url, updates_url=updates)
