#!/usr/bin/env python3
"""Serve the public-safe WEAVE operator UI locally.

Usage:
    python3 scripts/run_operator_ui.py
    python3 scripts/run_operator_ui.py --port 8787

The server binds to 127.0.0.1 and serves only files under operator-ui/.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = REPO_ROOT / "operator-ui"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    if not UI_ROOT.exists():
        raise SystemExit(f"operator UI directory missing: {UI_ROOT}")

    handler = functools.partial(QuietHandler, directory=str(UI_ROOT))
    with socketserver.TCPServer((args.host, args.port), handler) as server:
        print(f"WEAVE operator UI: http://{args.host}:{args.port}/")
        print("Press Ctrl-C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
