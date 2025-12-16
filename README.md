# linuxcord

linuxcord is a user-space Discord launcher for Linux. It downloads the official Discord tarball, installs it under XDG directories, keeps host (the installed application on your machine) updates current, and launches Discord without needing system-level packages.

## Features
- Installs Discord from the official tar.gz into user directories.
- Checks for host updates on each run and upgrades if needed.
- Desktop entry installation for desktop environments.
- Pure-Python API plus Click-based CLI.
- Configurable download and updates endpoints for testing.

## Installation
Install via `pipx` directly from the repository:

```bash
pipx install git+https://github.com/fsufitch/linuxcord.git
```

After installation the `linuxcord` command is available on your PATH, and you can also run `python -m linuxcord`.

## Usage

### Install or update
Install the data directories, desktop entry, and Discord itself (or reinstall with `--force`):

```bash
linuxcord update
linuxcord update --force
```

### Run
Launch Discord. By default, linuxcord checks for updates and installs them before launching; add `--no-update` to skip the check:

```bash
linuxcord run
linuxcord run --no-update
```

### Update without launching

```bash
linuxcord update
```

### Status
Show installed and latest versions plus paths:

```bash
linuxcord status
```

### Uninstall
Remove linuxcord-managed data, cache, and desktop entries:

```bash
linuxcord uninstall
```

Add `--yes` to skip the confirmation prompt.

## Configuration
Discord URLs can be overridden for end-to-end testing:

- Discord tarball URL: environment variable `LINUXCORD_DISCORD_TGZ_URL` or CLI `--discord-tgz-url`.
- Updates API URL: environment variable `LINUXCORD_UPDATES_URL` or CLI `--updates-url`.

CLI options take precedence over environment variables. Defaults:
- Discord tarball: `https://discord.com/api/download?platform=linux&format=tar.gz`
- Updates API: `https://discord.com/api/updates/stable?platform=linux`

### Host vs. in-app updates
linuxcord only manages **host updates**, meaning the version of Discord installed on your system from the downloaded tarball. Discord also performs its own **in-app UI/content updates** after launch; linuxcord does not interfere with or manage those in-app downloads.

## XDG Paths
linuxcord stores files under standard XDG locations:
- Data: `$XDG_DATA_HOME/linuxcord` (default `~/.local/share/linuxcord`)
- Cache: `$XDG_CACHE_HOME/linuxcord` (default `~/.cache/linuxcord`)
- State: `$XDG_STATE_HOME/linuxcord` (default `~/.local/state/linuxcord`)
- Discord installs: `$XDG_DATA_HOME/linuxcord/discord/versions/Discord-<version>/`
- Current symlink: `$XDG_DATA_HOME/linuxcord/discord/current`
- State file: `$XDG_STATE_HOME/linuxcord/state.json`
- Desktop entry: `$XDG_DATA_HOME/linuxcord/linuxcord.desktop`
- Installed desktop entry: `~/.local/share/applications/linuxcord.desktop`
- linuxcord prunes older Discord installs after an update, keeping only the active version to limit disk usage.

## Desktop Entry
linuxcord creates a desktop entry pointing to `linuxcord run` with a bundled Discord icon stored in `$XDG_DATA_HOME/linuxcord/discord.png`. The entry is symlinked (or copied if necessary) to `~/.local/share/applications/linuxcord.desktop`.

## Development
The project uses [uv](https://github.com/astral-sh/uv) for dependency management and building.

Create a virtual environment and install dependencies:

```bash
uv venv
uv sync
```

Run formatting and checks:

```bash
uv run black .
uv run flake8
uv run basedpyright
```

Build the project with uv's backend:

```bash
uv build
```

## Testing
Automated tests are currently absent and will be added after refactoring the code to reduce monkeypatching requirements. TODO: reintroduce pytest-based coverage that exercises all non-launch code paths and document the coverage commands here.
