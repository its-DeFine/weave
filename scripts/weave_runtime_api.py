#!/usr/bin/env python3
"""Serve the first-slice WEAVE runtime REST skeleton locally.

The server binds to loopback by default and requires the generated local token
from the ignored WEAVE root. It delegates all behavior to
``weave_runtime_slice.dispatch_rest`` and does not contact Hermes, Telegram,
external networks, or private runtimes.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import socketserver
from pathlib import Path

import weave_runtime_slice


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEAVE_ROOT = REPO_ROOT / "runs" / "weave-root"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}


class RuntimeApiHandler(http.server.BaseHTTPRequestHandler):
    server_version = "WEAVERuntimeAPI/0.1"

    def __init__(self, *args: object, weave_root: Path, **kwargs: object) -> None:
        self.weave_root = weave_root
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802
        self.handle_request()

    def do_POST(self) -> None:  # noqa: N802
        self.handle_request()

    def handle_request(self) -> None:
        weave_runtime_slice.setup_weave_root(self.weave_root)
        if not self.authorized():
            self.write_json(401, {"error": "unauthorized", "auth": "generated-bearer-token-required"})
            return
        try:
            body = self.read_json_body()
            status, payload = weave_runtime_slice.dispatch_rest(self.weave_root, self.command, self.path, body)
        except weave_runtime_slice.RuntimeSliceError as exc:
            status, payload = 400, {"error": "runtime_slice_error", "detail": str(exc)}
        self.write_json(status, payload)

    def authorized(self) -> bool:
        auth_file = self.weave_root / "runtime" / "tokens" / "local-api-token"
        auth_value = auth_file.read_text(encoding="utf-8").strip() if auth_file.exists() else ""
        expected = f"Bearer {auth_value}"
        return bool(auth_value) and self.headers.get("Authorization") == expected

    def read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise weave_runtime_slice.RuntimeSliceError("request body must be a JSON object")
        return parsed

    def write_json(self, status: int, payload: dict[str, object]) -> None:
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_WEAVE_ROOT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()

    if args.host not in LOOPBACK_HOSTS:
        raise SystemExit("WEAVE runtime API first slice only binds to loopback")

    weave_runtime_slice.setup_weave_root(args.root)
    handler = functools.partial(RuntimeApiHandler, weave_root=args.root)
    with socketserver.TCPServer((args.host, args.port), handler) as server:
        print(f"WEAVE runtime API: http://{args.host}:{args.port}/")
        print("Auth: generated local bearer token required.")
        print("Press Ctrl-C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
