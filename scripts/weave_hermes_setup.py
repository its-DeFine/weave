#!/usr/bin/env python3
"""Non-secret Hermes setup readiness helpers for WEAVE.

Hermes owns provider authentication, model selection, and provider-route
verification. WEAVE only records whether the operator has completed normal
Hermes setup, or whether this runtime is intentionally slash-only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


SCHEMA = "weave-hermes-setup/v0.1"
STATUS_FILE = "weave-hermes-setup.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def status_path(hermes_home: Path) -> Path:
    return hermes_home / STATUS_FILE


def load_recorded_status(hermes_home: Path) -> dict[str, Any]:
    path = status_path(hermes_home)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def hermes_binary_status(hermes_command: str = "hermes") -> dict[str, Any]:
    explicit = Path(hermes_command).expanduser()
    if explicit.exists():
        return {"command": hermes_command, "found": True, "path": str(explicit.resolve())}
    found = shutil.which(hermes_command)
    return {"command": hermes_command, "found": bool(found), "path": found or ""}


def setup_commands(hermes_home: Path) -> list[str]:
    home = str(hermes_home)
    return [
        f"HERMES_HOME={home} hermes setup --portal",
        f"HERMES_HOME={home} hermes model",
        "weave hermes confirm-ready",
        "weave onboard --slash-only",
    ]


def hermes_setup_status(hermes_home: Path, *, hermes_command: str = "hermes") -> dict[str, Any]:
    hermes_home = hermes_home.expanduser().resolve()
    recorded = load_recorded_status(hermes_home)
    mode = recorded.get("mode")
    if mode == "slash_only":
        state = "slash_only"
        normal_chat_assumed_ready = False
        blocker = "normal Hermes chat intentionally disabled; deterministic slash commands remain available"
    elif mode == "operator_confirmed_ready":
        state = "operator_confirmed_ready"
        normal_chat_assumed_ready = True
        blocker = ""
    else:
        state = "needs_hermes_setup"
        normal_chat_assumed_ready = False
        blocker = "run normal Hermes setup and confirm Hermes can chat before WEAVE normal-chat onboarding"
    return {
        "schema": SCHEMA,
        "hermes_home": str(hermes_home),
        "state": state,
        "normal_chat_assumed_ready": normal_chat_assumed_ready,
        "route_verification_owner": "hermes",
        "binary": hermes_binary_status(hermes_command),
        "recorded": recorded,
        "blocker": blocker,
        "setup_commands": setup_commands(hermes_home),
        "secret_value_printed": False,
        "recorded_at": utc_now(),
    }


def write_status_file(hermes_home: Path, payload: dict[str, Any]) -> dict[str, Any]:
    hermes_home.mkdir(parents=True, exist_ok=True)
    hermes_home.chmod(0o700)
    payload = dict(payload)
    payload["schema"] = SCHEMA
    payload["secret_value_printed"] = False
    payload["recorded_at"] = utc_now()
    fd, name = tempfile.mkstemp(prefix=".weave-hermes-setup.", dir=str(hermes_home), text=True)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        tmp.chmod(0o600)
        tmp.replace(status_path(hermes_home))
        status_path(hermes_home).chmod(0o600)
    finally:
        if tmp.exists():
            tmp.unlink()
    return payload


def confirm_ready(hermes_home: Path, *, reason: str = "operator_confirmed_hermes_setup") -> dict[str, Any]:
    return write_status_file(
        hermes_home,
        {
            "mode": "operator_confirmed_ready",
            "reason": reason,
            "normal_chat_assumed_ready": True,
            "route_verification_owner": "hermes",
        },
    )


def mark_slash_only(hermes_home: Path, *, reason: str = "operator_selected_slash_only") -> dict[str, Any]:
    return write_status_file(
        hermes_home,
        {
            "mode": "slash_only",
            "reason": reason,
            "normal_chat_assumed_ready": False,
            "route_verification_owner": "hermes",
        },
    )


def print_status(status: dict[str, Any], output: TextIO = sys.stdout) -> None:
    print("WEAVE Hermes Setup", file=output)
    print(f"- state: {status['state']}", file=output)
    print(f"- normal_chat_assumed_ready: {str(status['normal_chat_assumed_ready']).lower()}", file=output)
    print(f"- route_verification_owner: {status['route_verification_owner']}", file=output)
    print(f"- hermes_binary_found: {str(status['binary']['found']).lower()}", file=output)
    print(f"- secret_value_printed: {str(status['secret_value_printed']).lower()}", file=output)
    if status["blocker"]:
        print(f"- blocker: {status['blocker']}", file=output)
        print("- next:", file=output)
        for command in status["setup_commands"][:3]:
            print(f"  {command}", file=output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record Hermes setup readiness for WEAVE.")
    parser.add_argument("--hermes-home", type=Path, default=Path(os.environ.get("HERMES_HOME", "~/.hermes")))
    parser.add_argument("--hermes-command", default="hermes")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status", help="show non-secret Hermes setup readiness")
    subparsers.add_parser("confirm-ready", help="record that normal Hermes setup already works")
    subparsers.add_parser("mark-slash-only", help="record slash-only mode for deterministic commands")
    return parser


def main(argv: list[str] | None = None, *, output: TextIO = sys.stdout) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    hermes_home = args.hermes_home.expanduser().resolve()
    if args.command in {None, "status"}:
        print_status(hermes_setup_status(hermes_home, hermes_command=args.hermes_command), output)
        return 0
    if args.command == "confirm-ready":
        confirm_ready(hermes_home)
        print_status(hermes_setup_status(hermes_home, hermes_command=args.hermes_command), output)
        return 0
    if args.command == "mark-slash-only":
        mark_slash_only(hermes_home)
        print_status(hermes_setup_status(hermes_home, hermes_command=args.hermes_command), output)
        return 0
    parser.print_help(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
