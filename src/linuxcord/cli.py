from __future__ import annotations

import logging
import sys

import click

from linuxcord import DEFAULT_DISCORD_TGZ_URL, DEFAULT_UPDATES_URL
from linuxcord import api
from linuxcord.logging_config import configure_logging

logger = logging.getLogger(__name__)


class Context:
    discord_tgz_url: str | None
    updates_url: str | None

    def __init__(self, discord_tgz_url: str | None, updates_url: str | None):
        self.discord_tgz_url = discord_tgz_url
        self.updates_url = updates_url


def _build_context(discord_tgz_url: str | None, updates_url: str | None) -> Context:
    return Context(discord_tgz_url=discord_tgz_url, updates_url=updates_url)


@click.group()
@click.option("--verbose", "verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--discord-tgz-url",
    "discord_tgz_url",
    default=None,
    help=f"Discord tarball URL (default: {DEFAULT_DISCORD_TGZ_URL})",
)
@click.option(
    "--updates-url",
    "updates_url",
    default=None,
    help=f"Updates API URL (default: {DEFAULT_UPDATES_URL})",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: bool,
    discord_tgz_url: str | None,
    updates_url: str | None,
) -> None:
    configure_logging(verbose)
    ctx.obj = _build_context(discord_tgz_url, updates_url)
    if verbose:
        logger.debug(
            "Using discord_tgz_url=%s, updates_url=%s", discord_tgz_url, updates_url
        )


def _print_status(result: api.UpdateResult) -> None:
    click.echo(f"Installed version: {result.installed_version or 'none'}")
    click.echo(f"Latest online version: {result.latest_version or 'unknown'}")
    current_path = result.current_path
    click.echo(f"Current install path: {current_path if current_path else 'none'}")


@cli.command()
@click.option("--force", is_flag=True, help="Force reinstall even if up to date")
@click.pass_obj
def init(ctx: Context, force: bool) -> None:
    result = api.init(
        force=force, discord_tgz_url=ctx.discord_tgz_url, updates_url=ctx.updates_url
    )
    _print_status(result)


@cli.command()
@click.pass_obj
def update(ctx: Context) -> None:
    result = api.update(
        discord_tgz_url=ctx.discord_tgz_url, updates_url=ctx.updates_url
    )
    _print_status(result)


@cli.command()
@click.pass_obj
def run(ctx: Context) -> None:
    result = api.run(discord_tgz_url=ctx.discord_tgz_url, updates_url=ctx.updates_url)
    _print_status(result)


@cli.command()
@click.pass_obj
def status(ctx: Context) -> None:
    result = api.status(
        discord_tgz_url=ctx.discord_tgz_url, updates_url=ctx.updates_url
    )
    _print_status(result)


@cli.command()
@click.option("--yes", is_flag=True, help="Do not prompt for confirmation")
@click.pass_obj
def uninstall(ctx: Context, yes: bool) -> None:
    _ = ctx
    if not yes and not click.confirm("Remove linuxcord data and desktop entries?"):
        click.echo("Aborted")
        raise SystemExit(1)
    api.uninstall()
    click.echo("linuxcord files removed")


def main(argv: list[str] | None = None) -> None:
    cli.main(args=argv, prog_name="linuxcord")


if __name__ == "__main__":
    main(sys.argv[1:])
