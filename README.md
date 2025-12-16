# linuxcord

linuxcord is a user-space Discord launcher for Linux. It downloads the official Discord tarball, installs it under XDG directories, keeps host updates current, and launches Discord without needing system-level packages.

## Features
- Installs Discord from the official tar.gz into user directories.
- Checks for host updates on each run and upgrades if needed.
- Desktop entry installation for desktop environments.
- Pure-Python API plus Click-based CLI.
- Configurable download and updates endpoints for testing.

## Installation
Install via `pipx` directly from the repository:

```bash
pipx install git+https://github.com/<user>/linuxcord.git
```

After installation the `linuxcord` command is available on your PATH, and you can also run `python -m linuxcord`.

## Usage

### Initialize
Initialize the data directories, install the desktop entry, and install Discord if missing (or reinstall with `--force`):

```bash
linuxcord init
linuxcord init --force
```

### Run
Update if needed and launch Discord:

```bash
linuxcord run
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
uv run pytest
```

Build the project with uv's backend:

```bash
uv build
```
