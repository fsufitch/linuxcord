import json
from pathlib import Path

import pytest

from linuxcord.types import DiscordVersion
from linuxcord.types import _is_str_key_dict  # pyright: ignore [reportPrivateUsage]


def test_is_str_key_dict():
    assert _is_str_key_dict({"a": 1, "b": object()}) is True
    assert _is_str_key_dict({1: "a"}) is False
    assert _is_str_key_dict(["not", "a", "dict"]) is False


def test_discord_version_comparison():
    older = DiscordVersion("0.0.100")
    newer = DiscordVersion("0.0.101")

    assert older < newer
    assert newer > older
    assert newer >= older
    assert older <= newer


def test_discord_version_equality():
    version_a = DiscordVersion("0.0.100")
    version_b = DiscordVersion("0.0.100")
    version_c = DiscordVersion("0.0.101")

    assert version_a == version_b
    assert version_a != version_c
    assert version_a != "0.0.100"


def test_discord_version_from_build_info(tmp_path: Path):
    build_info = tmp_path / "build_info.json"
    _ = build_info.write_text(json.dumps({"version": "1.2.3"}))

    version = DiscordVersion.from_build_info(build_info)

    assert str(version) == "1.2.3"


def test_from_build_info_invalid_structure(tmp_path: Path):
    build_info = tmp_path / "build_info.json"
    _ = build_info.write_text(json.dumps(["not", "an", "object"]))

    with pytest.raises(ValueError, match="build_info.json is not a valid object"):
        _ = DiscordVersion.from_build_info(build_info)


def test_from_build_info_missing_version(tmp_path: Path):
    build_info = tmp_path / "build_info.json"
    _ = build_info.write_text(json.dumps({}))

    with pytest.raises(
        ValueError, match="build_info.json does not contain a version string"
    ):
        _ = DiscordVersion.from_build_info(build_info)
