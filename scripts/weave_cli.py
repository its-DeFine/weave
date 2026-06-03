#!/usr/bin/env python3
"""Human-facing WEAVE CLI."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import io
import os
import sys
import tempfile
from pathlib import Path
from typing import Callable, TextIO

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import setup_gateway
import setup_runtime


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE_OUT = REPO_ROOT / "runs" / "runtime-profile.json"
DEFAULT_WEAVE_ROOT = REPO_ROOT / "runs" / "weave-root"
DEFAULT_HERMES_HOME = setup_gateway.default_hermes_home()
DEFAULT_APP_ID = "weave"
DEFAULT_APP_NAME = "WEAVE App"


class CliError(Exception):
    """Raised when the WEAVE CLI cannot complete a requested flow."""


def print_line(output: TextIO, text: str = "") -> None:
    print(text, file=output)


def print_header(output: TextIO) -> None:
    print_line(output, "+--------------------------------------------------+")
    print_line(output, "| WEAVE Onboarding                                 |")
    print_line(output, "| Hermes + Telegram runtime setup                  |")
    print_line(output, "+--------------------------------------------------+")


def print_step(output: TextIO, number: int, total: int, title: str, detail: str = "") -> None:
    print_line(output)
    print_line(output, f"Step {number}/{total}  {title}")
    if detail:
        print_line(output, f"  {detail}")


def success(output: TextIO, text: str) -> None:
    print_line(output, f"  [ok] {text}")


def warn(output: TextIO, text: str) -> None:
    print_line(output, f"  [!] {text}")


def prompt_text(input_stream: TextIO, output: TextIO, prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    print(f"{prompt}{suffix}: ", end="", file=output, flush=True)
    value = input_stream.readline()
    if value == "":
        return default or ""
    value = value.strip()
    return value or (default or "")


def default_hidden_reader(prompt: str) -> str:
    return getpass.getpass(prompt)


def write_private_bot_file(directory: Path, bot_value: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".weave-telegram-token.", dir=str(directory), text=True)
    path = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(bot_value.strip() + "\n")
        path.chmod(0o600)
        return path
    except Exception:
        if path.exists():
            path.unlink()
        raise


def run_setup_runtime(args: list[str]) -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = setup_runtime.main(args)
    if rc != 0:
        raise CliError(buffer.getvalue().strip() or "runtime setup failed")
    return buffer.getvalue()


def runtime_setup_args(args: argparse.Namespace, *, include_gateway: bool, bot_file_path: Path | None = None) -> list[str]:
    setup_args = [
        "--runtime",
        "hermes-default",
        "--weave-root",
        str(args.weave_root),
        "--gateway-hermes-home",
        str(args.hermes_home),
        "--profile-out",
        str(args.profile_out),
        "--foundation-app-id",
        args.foundation_app_id,
        "--foundation-app-name",
        args.foundation_app_name,
        "--autonomy-mode",
        args.autonomy_mode,
    ]
    if args.runtime_binary:
        setup_args.extend(["--runtime-binary", str(args.runtime_binary)])
    if args.install_hermes:
        setup_args.append("--install-hermes")
        setup_args.extend(["--hermes-extras", args.hermes_extras])
    if include_gateway:
        if bot_file_path is None:
            raise CliError("token file is required for gateway setup")
        setup_args.extend(["--gateway-token-file", str(bot_file_path)])
        if args.allowed_users:
            setup_args.extend(["--gateway-allowed-users", args.allowed_users])
        elif args.allow_all_users:
            setup_args.append("--gateway-allow-all-users")
        else:
            raise CliError("gateway setup needs allowed users or temporary discovery mode")
        if args.group_allowed_users:
            setup_args.extend(["--gateway-group-allowed-users", args.group_allowed_users])
        if args.home_channel:
            setup_args.extend(["--gateway-home-channel", args.home_channel])
    else:
        setup_args.append("--configure-gateway-context")
    return setup_args


def print_token_guidance(output: TextIO) -> None:
    print_line(output, "  Create a dedicated Telegram bot with BotFather.")
    print_line(output, "  Do not reuse a live or production bot token.")
    print_line(output, "  WEAVE will hide token input and will not print it back.")


def onboard(
    args: argparse.Namespace,
    *,
    input_stream: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    hidden_reader: Callable[[str], str] | None = None,
) -> int:
    hidden_reader = hidden_reader or default_hidden_reader
    print_header(output)

    print_step(output, 1, 5, "Runtime", "Create a local WEAVE root and Hermes gateway context.")
    if args.dry_run:
        warn(output, "dry run: no Telegram token will be requested or written")
        print_line(output, f"  would create WEAVE root: {args.weave_root}")
        print_line(output, f"  would prepare Hermes home: {args.hermes_home}")
        print_step(output, 2, 5, "Telegram", "Pair a dedicated bot for this WEAVE runtime.")
        print_token_guidance(output)
        warn(output, "stopped before token entry")
        print_line(output)
        print_line(output, "Continue later with:")
        print_line(output, "  weave onboard")
        return 0
    run_setup_runtime(runtime_setup_args(args, include_gateway=False))
    success(output, f"WEAVE root ready: {args.weave_root}")
    success(output, f"Hermes home ready: {args.hermes_home}")

    print_step(output, 2, 5, "Telegram", "Pair a dedicated bot for this WEAVE runtime.")
    print_token_guidance(output)

    allowed_users = args.allowed_users
    allow_all_users = args.allow_all_users
    if not allowed_users and not allow_all_users:
        allowed_users = prompt_text(
            input_stream,
            output,
            "Telegram numeric user id(s), comma-separated",
        )
        if not allowed_users:
            answer = prompt_text(
                input_stream,
                output,
                "No id yet. Use temporary discovery mode? Type YES to continue",
            )
            allow_all_users = answer == "YES"
            if not allow_all_users:
                raise CliError("onboarding stopped before Telegram pairing")

    bot_file_path: Path | None = None
    if args.token_file:
        bot_file_path = args.token_file
    else:
        bot_value = hidden_reader("Telegram bot token: ").strip()
        if not bot_value:
            raise CliError("onboarding stopped before Telegram pairing")
        bot_file_path = write_private_bot_file(args.weave_root / "runtime" / "tokens", bot_value)

    try:
        args.allowed_users = allowed_users
        args.allow_all_users = allow_all_users
        run_setup_runtime(runtime_setup_args(args, include_gateway=True, bot_file_path=bot_file_path))
    finally:
        if bot_file_path and not args.token_file and bot_file_path.exists():
            bot_file_path.unlink()

    success(output, "Telegram token stored in local Hermes environment")
    success(output, "WEAVE deterministic command plugin installed")
    success(output, "Gateway context refreshed")

    print_step(output, 3, 5, "Foundation", "Hermes must collect owner, agent, app, inventory, and contract context.")
    success(output, "Foundation onboarding files created")

    print_step(output, 4, 5, "Run", "Start Hermes from the generated gateway workdir.")
    print_line(output, "  Next local check:")
    print_line(output, "    hermes status")
    print_line(output, "  Start the gateway:")
    print_line(output, "    hermes gateway run")

    print_step(output, 5, 5, "Telegram Commands", "Use deterministic status before app work.")
    print_line(output, "  /start")
    print_line(output, "  /status")
    print_line(output, "  /apps")
    print_line(output, "  /create_app my-app")
    print_line(output)
    success(output, "onboarding complete")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="weave", description="WEAVE command line")
    subparsers = parser.add_subparsers(dest="command")

    onboard_parser = subparsers.add_parser("onboard", help="guided Hermes + Telegram setup")
    onboard_parser.add_argument("--weave-root", type=Path, default=DEFAULT_WEAVE_ROOT)
    onboard_parser.add_argument("--hermes-home", type=Path, default=DEFAULT_HERMES_HOME)
    onboard_parser.add_argument("--profile-out", type=Path, default=DEFAULT_PROFILE_OUT)
    onboard_parser.add_argument("--foundation-app-id", default=DEFAULT_APP_ID)
    onboard_parser.add_argument("--foundation-app-name", default=DEFAULT_APP_NAME)
    onboard_parser.add_argument("--runtime-binary", type=Path)
    onboard_parser.add_argument("--install-hermes", action="store_true", help="install pinned Hermes into ignored local state")
    onboard_parser.add_argument("--hermes-extras", default="cli,messaging")
    onboard_parser.add_argument("--token-file", type=Path, help=argparse.SUPPRESS)
    onboard_parser.add_argument("--allowed-users", help=argparse.SUPPRESS)
    onboard_parser.add_argument("--group-allowed-users", help=argparse.SUPPRESS)
    onboard_parser.add_argument("--home-channel", help=argparse.SUPPRESS)
    onboard_parser.add_argument("--allow-all-users", action="store_true", help=argparse.SUPPRESS)
    onboard_parser.add_argument(
        "--autonomy-mode",
        choices=sorted(setup_runtime.weave_runtime_slice.AUTONOMY_MODES),
        default=setup_runtime.weave_runtime_slice.DEFAULT_AUTONOMY_MODE,
    )
    onboard_parser.add_argument("--dry-run", action="store_true", help="show the setup flow and stop before token entry")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    input_stream: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    hidden_reader: Callable[[str], str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "onboard":
            return onboard(args, input_stream=input_stream, output=output, hidden_reader=hidden_reader)
        parser.print_help(output)
        return 0
    except (CliError, setup_gateway.GatewaySetupError, setup_runtime.RuntimeSetupError) as exc:
        print_line(output)
        warn(output, str(exc))
        print_line(output, "  No raw token was printed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
