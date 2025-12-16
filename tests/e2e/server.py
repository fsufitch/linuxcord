from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from linuxcord.types import DiscordVersion
from typing_extensions import override

_CONTENT_PATH = "/download/discord_latest.tar.gz"
_UPDATE_PATH = "/update_version"


def _build_handler(version: DiscordVersion, tarball_path: Path):
    update_payload = json.dumps({"name": version.string}).encode()

    class DiscordRequestHandler(BaseHTTPRequestHandler):  # type: ignore[misc]
        def _send_tarball_headers(self) -> None:
            tarball_size = tarball_path.stat().st_size
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Length", str(tarball_size))
            self.end_headers()

        def _send_update_headers(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(update_payload)))
            self.end_headers()

        def do_HEAD(self) -> None:  # noqa: N802
            if self.path == _UPDATE_PATH:
                self._send_update_headers()
            elif self.path == _CONTENT_PATH:
                self._send_tarball_headers()
            else:
                self.send_error(404)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == _UPDATE_PATH:
                self._send_update_headers()
                _ = self.wfile.write(update_payload)
            elif self.path == _CONTENT_PATH:
                self._send_tarball_headers()
                with tarball_path.open("rb") as f:
                    _ = self.wfile.write(f.read())
            else:
                self.send_error(404)

        @override
        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    return DiscordRequestHandler


@contextmanager
def discord_test_server(version: DiscordVersion, tarball_path: Path) -> Iterator[str]:
    handler = _build_handler(version, tarball_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"
    try:
        yield base_url
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
