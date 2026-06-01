#!/usr/bin/env python3
"""Configure an approval-gated Hermes Telegram gateway.

This helper is intentionally narrow. It writes Telegram gateway settings into
Hermes' local ``.env`` file from a token file, without printing the token or
placing it in tracked repository state. It does not install a service, start a
daemon, call Telegram, or send messages.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import weave_runtime_slice


SCHEMA = "weave-gateway-setup/v0.1"
TELEGRAM_BOT_PATTERN_RE = re.compile(r"^[0-9]{6,20}:[A-Za-z0-9_-]{20,}$")
CSV_USER_RE = re.compile(r"^[0-9]+(?:,[0-9]+)*$")
SECRET_KEYS = {"TELEGRAM_BOT_TOKEN"}
MANAGED_KEYS = {
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_ALLOWED_USERS",
    "TELEGRAM_GROUP_ALLOWED_USERS",
    "TELEGRAM_HOME_CHANNEL",
    "GATEWAY_ALLOW_ALL_USERS",
    "WEAVE_AUTONOMY_MODE",
}


class GatewaySetupError(Exception):
    """Raised when gateway setup cannot be completed safely."""


def default_hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()


def read_secret_file(path: Path) -> str:
    if not path.exists():
        raise GatewaySetupError("token file does not exist")
    if not path.is_file():
        raise GatewaySetupError("token file is not a regular file")
    bot_value = path.read_text(encoding="utf-8").strip()
    if not bot_value:
        raise GatewaySetupError("token file is empty")
    if not TELEGRAM_BOT_PATTERN_RE.fullmatch(bot_value):
        raise GatewaySetupError("token file does not look like a Telegram bot token")
    return bot_value


def validate_csv_users(value: str, label: str) -> str:
    normalized = value.replace(" ", "")
    if not CSV_USER_RE.fullmatch(normalized):
        raise GatewaySetupError(f"{label} must be a comma-separated list of numeric Telegram ids")
    return normalized


def parse_env_lines(text: str) -> tuple[list[str], dict[str, str]]:
    lines = text.splitlines()
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return lines, values


def update_env_lines(existing_lines: list[str], updates: dict[str, str], removals: set[str]) -> list[str]:
    written: set[str] = set()
    result: list[str] = []
    for line in existing_lines:
        if "=" not in line or line.lstrip().startswith("#"):
            result.append(line)
            continue
        key, _value = line.split("=", 1)
        clean_key = key.strip()
        if clean_key in removals:
            continue
        if clean_key in updates:
            result.append(f"{clean_key}={updates[clean_key]}")
            written.add(clean_key)
        else:
            result.append(line)
    if result and result[-1].strip():
        result.append("")
    for key in sorted(updates):
        if key not in written:
            result.append(f"{key}={updates[key]}")
    return result


def atomic_write_env(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    data = "\n".join(lines).rstrip() + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=".env.", dir=str(path.parent), text=True)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
        tmp_path.chmod(0o600)
        tmp_path.replace(path)
        path.chmod(0o600)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def env_has_private_mode(path: Path) -> bool:
    if not path.exists():
        return False
    mode = stat.S_IMODE(path.stat().st_mode)
    return mode == 0o600


def configure_gateway(
    *,
    hermes_home: Path,
    bot_file: Path,
    allowed_users: str | None = None,
    group_allowed_users: str | None = None,
    allow_all_users: bool = False,
    home_channel: str | None = None,
    autonomy_mode: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    if allow_all_users and allowed_users:
        raise GatewaySetupError("use either --allowed-users or --allow-all-users, not both")
    if not allow_all_users and not allowed_users:
        raise GatewaySetupError("gateway setup requires --allowed-users or temporary --allow-all-users")

    bot_value = read_secret_file(bot_file)
    env_path = hermes_home / ".env"
    existing_text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    existing_lines, existing_values = parse_env_lines(existing_text)

    normalized_autonomy_mode = weave_runtime_slice.normalize_autonomy_mode(autonomy_mode)
    updates = {
        "TELEGRAM_BOT_TOKEN": bot_value,
        "WEAVE_AUTONOMY_MODE": normalized_autonomy_mode,
    }
    removals: set[str] = set()
    allowlist_mode = "allow_all_users" if allow_all_users else "allowed_users"

    if allow_all_users:
        updates["GATEWAY_ALLOW_ALL_USERS"] = "true"
        removals.add("TELEGRAM_ALLOWED_USERS")
    else:
        updates["TELEGRAM_ALLOWED_USERS"] = validate_csv_users(allowed_users or "", "allowed users")
        removals.add("GATEWAY_ALLOW_ALL_USERS")

    if group_allowed_users:
        updates["TELEGRAM_GROUP_ALLOWED_USERS"] = validate_csv_users(group_allowed_users, "group allowed users")
    if home_channel:
        updates["TELEGRAM_HOME_CHANNEL"] = home_channel.strip()

    new_lines = update_env_lines(existing_lines, updates, removals)
    if not dry_run:
        atomic_write_env(env_path, new_lines)

    public_existing_keys = sorted(key for key in existing_values if key in MANAGED_KEYS and key not in SECRET_KEYS)
    return {
        "schema": SCHEMA,
        "channel": "telegram",
        "hermes_home": str(hermes_home),
        "env_path": str(env_path),
        "dry_run": dry_run,
        "env_written": not dry_run,
        "env_private_mode": env_has_private_mode(env_path) if not dry_run else None,
        "telegram_bot_token_configured": True,
        "token_value_printed": False,
        "allowlist_mode": allowlist_mode,
        "allowed_user_count": len((allowed_users or "").split(",")) if allowed_users else 0,
        "group_allowed_user_count": len((group_allowed_users or "").split(",")) if group_allowed_users else 0,
        "home_channel_configured": bool(home_channel),
        "autonomy_mode": normalized_autonomy_mode,
        "hard_approval_gates": [gate["id"] for gate in weave_runtime_slice.HARD_APPROVAL_GATES],
        "managed_keys_already_present": public_existing_keys,
        "next_checks": [
            "hermes status",
            "hermes gateway status",
            "hermes gateway run",
        ],
        "service_installed": False,
        "gateway_started": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure Hermes Telegram gateway env from a token file.")
    parser.add_argument("--hermes-home", type=Path, default=default_hermes_home())
    parser.add_argument(
        "--token-file",
        dest="bot_file",
        type=Path,
        required=True,
        help="file containing the Telegram bot token",
    )
    parser.add_argument("--allowed-users", help="comma-separated Telegram numeric user ids")
    parser.add_argument("--group-allowed-users", help="comma-separated Telegram numeric group user ids")
    parser.add_argument(
        "--allow-all-users",
        action="store_true",
        help="temporary discovery mode; replace with --allowed-users after capturing the owner id",
    )
    parser.add_argument("--home-channel", help="optional Telegram home channel/chat id")
    parser.add_argument(
        "--autonomy-mode",
        choices=sorted(weave_runtime_slice.AUTONOMY_MODES),
        default=weave_runtime_slice.DEFAULT_AUTONOMY_MODE,
        help="runtime confirmation mode; yolo proceeds on non-gated work and asks through the LLM for hard gates",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = configure_gateway(
            hermes_home=args.hermes_home.expanduser(),
            bot_file=args.bot_file.expanduser(),
            allowed_users=args.allowed_users,
            group_allowed_users=args.group_allowed_users,
            allow_all_users=args.allow_all_users,
            home_channel=args.home_channel,
            autonomy_mode=args.autonomy_mode,
            dry_run=args.dry_run,
        )
    except GatewaySetupError as exc:
        print(f"gateway setup failed: {exc}")
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("gateway setup: ready")
        print(f"channel: {result['channel']}")
        print(f"env_written: {str(result['env_written']).lower()}")
        print(f"telegram_bot_token_configured: {str(result['telegram_bot_token_configured']).lower()}")
        print(f"allowlist_mode: {result['allowlist_mode']}")
        print(f"autonomy_mode: {result['autonomy_mode']}")
        print(f"token_value_printed: {str(result['token_value_printed']).lower()}")
        print("next: hermes status && hermes gateway run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
