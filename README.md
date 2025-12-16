# linuxcord

linuxcord is a user-space Discord launcher/updater for Linux. It installs Discord into your XDG data directory, manages a versioned `current` symlink, and launches Discord without needing system-level packages.

## What it does
- Resolves the latest Discord build from the official update API, falling back to the redirected tarball URL if the API is unavailable.
- Downloads and safely extracts the official Discord tarball into a versioned directory under `$XDG_DATA_HOME/linuxcord/versions/`.
- Copies the Discord icon into the data directory, writes a FreeDesktop desktop entry that calls `linuxcord run`, and symlinks it into your applications directory.
- Maintains a file lock in the XDG runtime directory (or state directory) to avoid concurrent installs/updates.
- Prunes old installs after a successful update, keeping only the active version unless a `NO_PRUNING` file is present.
- Provides both a Python API and a Click-based CLI for automation.

## Installation
Install via `pipx` directly from the repository:

```bash
pipx install git+https://github.com/fsufitch/linuxcord.git
```

After installation the `linuxcord` command is available on your PATH, and you can also run `python -m linuxcord`.

## Usage

All commands honour the same URL resolution: CLI flags override environment variables (`LINUXCORD_DISCORD_TGZ_URL`, `LINUXCORD_UPDATES_URL`), which in turn override the baked-in defaults. Updates are serialized via a file lock to avoid concurrent installs.

### Install or update
Install the data directories, desktop entry, and Discord itself (or reinstall with `--force`). The command also refreshes the desktop entry and application symlink after installing and prunes older installs unless `NO_PRUNING` is present:

```bash
linuxcord update
linuxcord update --force
```

### Run
Launch Discord. By default, linuxcord checks for updates and installs them before launching; add `--no-update` to skip the check. Running as root is disallowed to avoid polluting system locations:

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
- Discord installs: `$XDG_DATA_HOME/linuxcord/versions/<version>/`
- Current symlink: `$XDG_DATA_HOME/linuxcord/versions/current`
- Lock file: `$XDG_RUNTIME_DIR/linuxcord.lock` (falls back to `$XDG_STATE_HOME/linuxcord/lock`)
- Icon and desktop entry: `$XDG_DATA_HOME/linuxcord/discord.png` and `$XDG_DATA_HOME/linuxcord/linuxcord.desktop`
- Installed desktop entry symlink: typically `~/.local/share/applications/linuxcord.desktop`
- linuxcord prunes older Discord installs after an update, keeping only the active version to limit disk usage. Create an empty `NO_PRUNING` file in the versions directory to disable pruning.

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
Run the test suite and view coverage:

```bash
uv run pytest
uv run pytest --cov --cov-report=term-missing
```
