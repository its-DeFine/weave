#!/usr/bin/env python3
"""Human-facing WEAVE CLI."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import subprocess
from pathlib import Path
from typing import Callable, TextIO

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import setup_gateway
import setup_runtime
import weave_dashboard
import weave_hermes_setup


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_HOME = REPO_ROOT / "runs" / "runtime-home"
DEFAULT_WEAVE_STATE_DIR = "weave-state"
DEFAULT_HERMES_HOME_DIR = "hermes-home"
DEFAULT_PROFILE_NAME = "runtime-profile.json"
DEFAULT_PROFILE_OUT = DEFAULT_RUNTIME_HOME / DEFAULT_PROFILE_NAME
DEFAULT_WEAVE_ROOT = DEFAULT_RUNTIME_HOME / DEFAULT_WEAVE_STATE_DIR
DEFAULT_HERMES_HOME = DEFAULT_RUNTIME_HOME / DEFAULT_HERMES_HOME_DIR
DEFAULT_APP_ID = "weave"
DEFAULT_APP_NAME = "WEAVE App"
DEFAULT_CONTAINER_IMAGE = "weave-hermes-runtime:local"
DEFAULT_CONTAINER_NAME = "weave-hermes-runtime"
CONTAINER_DOCKERFILE = REPO_ROOT / "container" / "hermes" / "Dockerfile"
EXPORT_SCHEMA = "weave-runtime-export/v0.1"
SECRET_EXPORT_NAMES = {
    ".env",
    "local-api-token",
    "telegram.secret",
}
SECRET_EXPORT_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".secret",
}
SECRET_EXPORT_DIRS = {
    "tokens",
}


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


def resolve_runtime_paths(args: argparse.Namespace) -> argparse.Namespace:
    runtime_home = getattr(args, "runtime_home", None) or DEFAULT_RUNTIME_HOME
    args.runtime_home = runtime_home.expanduser().resolve()
    if hasattr(args, "weave_root"):
        weave_root = args.weave_root or (args.runtime_home / DEFAULT_WEAVE_STATE_DIR)
        args.weave_root = weave_root.expanduser().resolve()
    if hasattr(args, "hermes_home"):
        hermes_home = args.hermes_home or (args.runtime_home / DEFAULT_HERMES_HOME_DIR)
        args.hermes_home = hermes_home.expanduser().resolve()
    if hasattr(args, "profile_out"):
        profile_out = args.profile_out or (args.runtime_home / DEFAULT_PROFILE_NAME)
        args.profile_out = profile_out.expanduser().resolve()
    if hasattr(args, "export_out") and args.export_out:
        args.export_out = args.export_out.expanduser().resolve()
    if hasattr(args, "archive") and args.archive:
        args.archive = args.archive.expanduser().resolve()
    return args


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


def run_process(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    except OSError as exc:
        raise CliError(f"could not run {command[0]!r}: {exc}") from exc


def docker_binary() -> str:
    docker = shutil.which("docker")
    if not docker:
        raise CliError("Docker is required for container onboarding. Install Docker or rerun with --local.")
    return docker


def build_container_image(image: str, output: TextIO) -> None:
    docker = docker_binary()
    if not CONTAINER_DOCKERFILE.exists():
        raise CliError(f"container Dockerfile is missing: {CONTAINER_DOCKERFILE}")
    print_line(output, f"  building image: {image}")
    result = run_process(
        [
            docker,
            "build",
            "-f",
            str(CONTAINER_DOCKERFILE),
            "--build-arg",
            f"HERMES_COMMIT={setup_runtime.provision_hermes.HERMES_PINNED_COMMIT}",
            "--build-arg",
            "HERMES_EXTRAS=cli,messaging",
            "-t",
            image,
            str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise CliError(f"container image build failed\n{detail}")


def container_start_command(args: argparse.Namespace) -> list[str]:
    docker = docker_binary()
    gateway_workdir = args.weave_root / "runtime" / "hermes-gateway"
    env_file = args.hermes_home / ".env"
    if not env_file.exists():
        raise CliError("gateway env is missing; run weave onboard before weave start")
    if not gateway_workdir.exists():
        raise CliError("gateway workdir is missing; run weave onboard before weave start")
    volume_flags: list[str] = []
    seen_mounts: set[str] = set()
    mount_specs = [
        (REPO_ROOT, REPO_ROOT, "ro"),
        (args.runtime_home, args.runtime_home, ""),
    ]
    for path in (args.weave_root, args.hermes_home):
        if not path.is_relative_to(args.runtime_home):
            mount_specs.append((path, path, ""))
    for source, target, mode in mount_specs:
        key = str(source)
        if key in seen_mounts:
            continue
        seen_mounts.add(key)
        suffix = f":{mode}" if mode else ""
        volume_flags.extend(["-v", f"{source}:{target}{suffix}"])
    return [
        docker,
        "run",
        "-d",
        "--name",
        args.container_name,
        "--restart",
        "unless-stopped",
        "--env-file",
        str(env_file),
        "-e",
        f"HERMES_HOME={args.hermes_home}",
        "-e",
        "WEAVE_RUNTIME_HOME=" + str(args.runtime_home),
        "-e",
        "WEAVE_RUNTIME_REPO=" + str(REPO_ROOT),
        "-e",
        "WEAVE_RUNTIME_ROOT=" + str(args.weave_root),
        *volume_flags,
        "-w",
        str(gateway_workdir),
        args.container_image,
        "gateway",
        "run",
        "--replace",
    ]


def start_container_runtime(args: argparse.Namespace, output: TextIO) -> int:
    command = container_start_command(args)
    docker = docker_binary()
    run_process([docker, "rm", "-f", args.container_name])
    result = run_process(command)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise CliError(f"container start failed\n{detail}")
    success(output, f"container started: {args.container_name}")
    print_line(output, f"  {result.stdout.strip()}")
    return 0


def stop_container_runtime(args: argparse.Namespace, output: TextIO) -> int:
    docker = docker_binary()
    result = run_process([docker, "stop", args.container_name])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise CliError(f"container stop failed\n{detail}")
    success(output, f"container stopped: {args.container_name}")
    return 0


def status_container_runtime(args: argparse.Namespace, output: TextIO) -> int:
    print_line(output, "WEAVE Runtime Status")
    print_line(output, "")
    print_line(output, "Runtime Home")
    print_line(output, f"- runtime_home: {args.runtime_home} ({path_state(args.runtime_home)})")
    print_line(output, f"- weave_state: {args.weave_root} ({path_state(args.weave_root)})")
    print_line(output, f"- hermes_home: {args.hermes_home} ({path_state(args.hermes_home)})")
    print_line(output, f"- profile: {getattr(args, 'profile_out', DEFAULT_PROFILE_OUT)} ({path_state(getattr(args, 'profile_out', DEFAULT_PROFILE_OUT))})")
    env_file = args.hermes_home / ".env"
    print_line(output, f"- gateway_env: {env_status(env_file)}")
    hermes_setup = weave_hermes_setup.hermes_setup_status(args.hermes_home)
    print_line(output, "")
    print_line(output, "Hermes Setup")
    print_line(output, f"- state: {hermes_setup['state']}")
    print_line(output, f"- normal_chat_assumed_ready: {str(hermes_setup['normal_chat_assumed_ready']).lower()}")
    print_line(output, f"- route_verification_owner: {hermes_setup['route_verification_owner']}")
    print_line(output, f"- hermes_binary_found: {str(hermes_setup['binary']['found']).lower()}")
    print_line(output, f"- secret_value_printed: {str(hermes_setup['secret_value_printed']).lower()}")
    print_line(output, "")
    print_line(output, "Container")
    docker = shutil.which("docker")
    if not docker:
        print_line(output, "- state: unknown; container engine unavailable")
    else:
        result = run_process(
            [
                docker,
                "ps",
                "-a",
                "--filter",
                f"name={args.container_name}",
                "--format",
                "{{.Names}}\t{{.Status}}\t{{.Image}}",
            ]
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise CliError(f"container status failed\n{detail}")
        text = result.stdout.strip()
        if not text:
            print_line(output, f"- state: not_found; name={args.container_name}")
        else:
            print_line(output, f"- {text}")
    print_line(output, "")
    print_line(output, "State")
    if setup_runtime.weave_runtime_slice.root_ready(args.weave_root):
        status = setup_runtime.weave_runtime_slice.runtime_status_command(args.weave_root)
        payload = status["payload"]
        active = payload.get("active_app", {})
        print_line(output, "- root_ready: true")
        print_line(output, f"- product_apps: {payload.get('app_count', 0)}")
        print_line(output, f"- system_apps: {payload.get('system_app_count', 0)}")
        print_line(output, f"- active_app: {active.get('app_id') or 'none'}")
        print_line(output, f"- blocked_apps: {payload.get('blocked_app_count', 0)}")
        print_line(output, f"- next: {payload.get('next_action', '')}")
    else:
        print_line(output, "- root_ready: false")
        print_line(output, "- next: run weave onboard")
    return 0


def dashboard(args: argparse.Namespace, output: TextIO) -> int:
    snapshot = weave_dashboard.dashboard_snapshot(
        runtime_home=args.runtime_home,
        weave_root=args.weave_root,
        hermes_home=args.hermes_home,
        profile_path=args.profile_out,
        container_name=args.container_name,
        check_container=not args.no_container_check,
    )
    weave_dashboard.print_dashboard(snapshot, output=output, as_json=args.json)
    return 0


def path_state(path: Path) -> str:
    if path.exists() and path.is_dir():
        return "directory"
    if path.exists() and path.is_file():
        return "file"
    return "missing"


def env_status(path: Path) -> str:
    if not path.exists():
        return "missing; secret_relink_required"
    mode = path.stat().st_mode & 0o777
    private = "private" if mode == 0o600 else f"mode={oct(mode)}"
    return f"present; {private}; secret_value_printed=false"


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
        "--runtime-home",
        str(args.runtime_home),
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
    if not args.local:
        setup_args.extend(["--runtime-container-image", args.container_image])
    if args.local and args.install_hermes:
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
    print_line(output, "  Telegram steps:")
    print_line(output, "    1. Open Telegram and search for BotFather.")
    print_line(output, "    2. Send /newbot.")
    print_line(output, "    3. Choose a bot display name for this WEAVE runtime.")
    print_line(output, "    4. Choose a bot username ending in bot.")
    print_line(output, "    5. Copy the token BotFather shows; keep it private.")
    print_line(output, "    6. Return here and paste the token at the hidden prompt.")
    print_line(output, "  Do not reuse a live or production bot token.")
    print_line(output, "  WEAVE will hide token input and will not print it back.")


def print_hermes_setup_guidance(output: TextIO, hermes_home: Path) -> None:
    print_line(output, "  Hermes must be installed and set up before WEAVE normal-chat onboarding.")
    print_line(output, "  First complete normal Hermes setup:")
    print_line(output, f"    HERMES_HOME={hermes_home} hermes setup --portal")
    print_line(output, f"    HERMES_HOME={hermes_home} hermes model")
    print_line(output, "  Confirm Hermes itself can chat, then rerun:")
    print_line(output, "    weave onboard --hermes-ready")
    print_line(output, "  Or record readiness directly:")
    print_line(output, "    weave hermes confirm-ready")
    print_line(output, "  For deterministic Telegram commands only, rerun:")
    print_line(output, "    weave onboard --slash-only")


def require_or_mark_hermes(args: argparse.Namespace, output: TextIO) -> dict[str, object]:
    if args.slash_only:
        weave_hermes_setup.mark_slash_only(args.hermes_home)
        status = weave_hermes_setup.hermes_setup_status(args.hermes_home)
        warn(output, "slash-only mode selected; normal Hermes chat will stay blocked until Hermes setup is confirmed")
        return status
    if args.hermes_ready:
        weave_hermes_setup.confirm_ready(args.hermes_home)
        status = weave_hermes_setup.hermes_setup_status(args.hermes_home)
        success(output, "Hermes setup confirmed by operator")
        return status
    status = weave_hermes_setup.hermes_setup_status(args.hermes_home)
    if status["normal_chat_assumed_ready"]:
        success(output, "Hermes setup already confirmed")
        return status
    print_hermes_setup_guidance(output, args.hermes_home)
    raise CliError(
        "normal Hermes setup must be completed or explicitly confirmed before WEAVE normal-chat onboarding; "
        "rerun with --hermes-ready after Hermes works, or --slash-only for deterministic commands only"
    )


def onboard(
    args: argparse.Namespace,
    *,
    input_stream: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    hidden_reader: Callable[[str], str] | None = None,
) -> int:
    hidden_reader = hidden_reader or default_hidden_reader
    print_header(output)

    print_step(output, 1, 6, "Hermes Setup", "Confirm normal Hermes setup before WEAVE normal chat.")
    if args.dry_run:
        print_hermes_setup_guidance(output, args.hermes_home)
        print_line(output, "  would require normal Hermes setup confirmation or explicit --slash-only")
        print_step(output, 2, 6, "Runtime", "Create a local WEAVE root and Hermes gateway context.")
        warn(output, "dry run: no Telegram token will be requested or written")
        if args.local:
            print_line(output, "  mode: local host install")
            print_line(output, "  would check or install pinned Hermes on the host")
        else:
            print_line(output, "  mode: container")
            print_line(output, f"  would verify Docker and build image: {args.container_image}")
        print_line(output, f"  would create WEAVE root: {args.weave_root}")
        print_line(output, f"  would use runtime home: {args.runtime_home}")
        print_line(output, f"  would prepare Hermes home: {args.hermes_home}")
        print_step(output, 3, 6, "Telegram", "Pair a dedicated bot for this WEAVE runtime.")
        print_token_guidance(output)
        warn(output, "stopped before token entry")
        print_line(output)
        print_line(output, "Continue later with:")
        print_line(output, "  weave onboard")
        return 0

    hermes_setup = require_or_mark_hermes(args, output)
    if hermes_setup["state"] == "slash_only":
        print_line(output, "  /status, /apps, and /help will work without normal Hermes chat.")

    print_step(output, 2, 6, "Runtime", "Create a local WEAVE root and Hermes gateway context.")
    if args.local:
        success(output, "local mode selected")
    else:
        docker_binary()
        success(output, "Docker available")
        if args.skip_image_build:
            warn(output, f"using existing image without rebuild: {args.container_image}")
        else:
            build_container_image(args.container_image, output)
            success(output, f"Hermes image ready: {args.container_image}")

    run_setup_runtime(runtime_setup_args(args, include_gateway=False))
    success(output, f"runtime home ready: {args.runtime_home}")
    success(output, f"WEAVE root ready: {args.weave_root}")
    success(output, f"Hermes home ready: {args.hermes_home}")

    print_step(output, 3, 6, "Telegram", "Pair a dedicated bot for this WEAVE runtime.")
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

    print_step(output, 4, 6, "Foundation", "Hermes must collect owner, agent, app, inventory, and contract context.")
    success(output, "Foundation onboarding files created")

    print_step(output, 5, 6, "Run", "Start Hermes from the generated gateway workdir.")
    if args.local:
        print_line(output, "  Next local check:")
        print_line(output, "    hermes status")
        print_line(output, "  Start the gateway:")
        print_line(output, "    hermes gateway run")
    else:
        print_line(output, "  Start the containerized gateway:")
        print_line(output, "    weave start")
        print_line(output, "  Inspect it:")
        print_line(output, "    weave status")

    print_step(output, 6, 6, "Telegram Commands", "Use deterministic status before app work.")
    print_line(output, "  /start")
    print_line(output, "  /status")
    print_line(output, "  /apps")
    print_line(output, "  /create_app my-app")
    print_line(output)
    success(output, "onboarding complete")
    return 0


def should_exclude_export(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if any(part in SECRET_EXPORT_DIRS for part in parts):
        return True
    if name in SECRET_EXPORT_NAMES:
        return True
    if name.startswith(".weave-telegram-token."):
        return True
    if path.suffix.lower() in SECRET_EXPORT_SUFFIXES:
        return True
    return False


def add_json_to_tar(tar: tarfile.TarFile, arcname: str, payload: dict[str, object]) -> None:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    info = tarfile.TarInfo(arcname)
    info.size = len(encoded)
    info.mode = 0o600
    tar.addfile(info, io.BytesIO(encoded))


def export_runtime(args: argparse.Namespace, output: TextIO) -> int:
    if not args.runtime_home.exists():
        raise CliError("runtime home is missing; run weave onboard before exporting")
    args.export_out.parent.mkdir(parents=True, exist_ok=True)
    excluded: list[str] = []
    included = 0
    with tarfile.open(args.export_out, "w:gz") as tar:
        for path in sorted(args.runtime_home.rglob("*")):
            if path.resolve() == args.export_out:
                continue
            rel = path.relative_to(args.runtime_home)
            if should_exclude_export(rel):
                if path.is_file():
                    excluded.append(rel.as_posix())
                continue
            tar.add(path, arcname=(Path("runtime-home") / rel).as_posix(), recursive=False)
            included += 1
        add_json_to_tar(
            tar,
            "runtime-home/export-manifest.json",
            {
                "schema": EXPORT_SCHEMA,
                "runtime_home_layout": setup_runtime.weave_runtime_slice.RUNTIME_HOME_SCHEMA,
                "secrets_exported": False,
                "secret_relink_required_after_import": True,
                "excluded_secret_refs": excluded,
                "state_root": DEFAULT_WEAVE_STATE_DIR,
                "hermes_home": DEFAULT_HERMES_HOME_DIR,
            },
        )
    success(output, f"runtime export written: {args.export_out}")
    print_line(output, f"  included_entries: {included}")
    print_line(output, f"  excluded_secret_refs: {len(excluded)}")
    print_line(output, "  secrets_exported: false")
    return 0


def safe_tar_member_path(member_name: str) -> Path:
    path = Path(member_name)
    if path.is_absolute() or ".." in path.parts:
        raise CliError(f"unsafe archive member: {member_name}")
    if path.parts and path.parts[0] == "runtime-home":
        path = Path(*path.parts[1:]) if len(path.parts) > 1 else Path()
    return path


def import_runtime(args: argparse.Namespace, output: TextIO) -> int:
    if not args.archive.exists():
        raise CliError("runtime archive does not exist")
    if args.runtime_home.exists() and any(args.runtime_home.iterdir()) and not args.force:
        raise CliError("runtime home is not empty; rerun with --force to overlay imported state")
    args.runtime_home.mkdir(parents=True, exist_ok=True)
    imported = 0
    skipped = 0
    with tarfile.open(args.archive, "r:gz") as tar:
        for member in tar.getmembers():
            rel = safe_tar_member_path(member.name)
            if not rel.parts:
                continue
            target = args.runtime_home / rel
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                imported += 1
                continue
            if not member.isfile():
                skipped += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            if source is None:
                skipped += 1
                continue
            with source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            os.chmod(target, 0o600 if target.name.endswith((".json", ".jsonl", ".md", ".txt", ".yaml", ".yml")) else 0o600)
            imported += 1
    if args.weave_root.exists():
        setup_runtime.weave_runtime_slice.setup_weave_root(args.weave_root)
    success(output, f"runtime import completed: {args.runtime_home}")
    print_line(output, f"  imported_entries: {imported}")
    print_line(output, f"  skipped_non_regular_entries: {skipped}")
    print_line(output, "  secrets_imported: false")
    print_line(output, "  next: relink gateway credentials, then run weave verify-runtime")
    return 0


def verify_runtime(args: argparse.Namespace, output: TextIO) -> int:
    profile_ready = args.profile_out.exists()
    root_ready = setup_runtime.weave_runtime_slice.root_ready(args.weave_root)
    hermes_home_ready = args.hermes_home.exists()
    env_ready = (args.hermes_home / ".env").exists()
    gateway_ready = (args.weave_root / "runtime" / "hermes-gateway").exists()
    print_line(output, "WEAVE Runtime Verify")
    print_line(output, f"- runtime_home: {path_state(args.runtime_home)}")
    print_line(output, f"- weave_state: {path_state(args.weave_root)}")
    print_line(output, f"- hermes_home: {path_state(args.hermes_home)}")
    print_line(output, f"- profile: {'ready' if profile_ready else 'missing'}")
    print_line(output, f"- root_ready: {str(root_ready).lower()}")
    print_line(output, f"- gateway_context: {'ready' if gateway_ready else 'missing'}")
    print_line(output, f"- gateway_env: {env_status(args.hermes_home / '.env')}")
    hermes_setup = weave_hermes_setup.hermes_setup_status(args.hermes_home)
    print_line(output, f"- hermes_setup: {hermes_setup['state']}")
    print_line(output, f"- hermes_normal_chat_assumed_ready: {str(hermes_setup['normal_chat_assumed_ready']).lower()}")
    print_line(output, f"- secret_relink_required: {str(not env_ready).lower()}")
    if root_ready:
        status = setup_runtime.weave_runtime_slice.runtime_status_command(args.weave_root)
        payload = status["payload"]
        print_line(output, f"- product_apps: {payload.get('app_count', 0)}")
        print_line(output, f"- blocked_apps: {payload.get('blocked_app_count', 0)}")
        print_line(output, f"- next: {payload.get('next_action', '')}")
    required_ready = args.runtime_home.exists() and root_ready and profile_ready
    print_line(output, f"- verification: {'passed' if required_ready else 'failed'}")
    return 0 if required_ready else 1


def hermes_command(args: argparse.Namespace, output: TextIO) -> int:
    if args.hermes_command_name in {None, "status"}:
        weave_hermes_setup.print_status(
            weave_hermes_setup.hermes_setup_status(args.hermes_home, hermes_command=args.hermes_command),
            output,
        )
        return 0
    if args.hermes_command_name == "confirm-ready":
        weave_hermes_setup.confirm_ready(args.hermes_home)
        weave_hermes_setup.print_status(
            weave_hermes_setup.hermes_setup_status(args.hermes_home, hermes_command=args.hermes_command),
            output,
        )
        return 0
    if args.hermes_command_name == "mark-slash-only":
        weave_hermes_setup.mark_slash_only(args.hermes_home)
        weave_hermes_setup.print_status(
            weave_hermes_setup.hermes_setup_status(args.hermes_home, hermes_command=args.hermes_command),
            output,
        )
        return 0
    raise CliError(f"unknown Hermes command: {args.hermes_command_name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="weave", description="WEAVE command line")
    subparsers = parser.add_subparsers(dest="command")

    onboard_parser = subparsers.add_parser("onboard", help="guided Hermes + Telegram setup")
    onboard_parser.add_argument("--runtime-home", type=Path, default=None)
    onboard_parser.add_argument("--weave-root", type=Path, default=None)
    onboard_parser.add_argument("--hermes-home", type=Path, default=None)
    onboard_parser.add_argument("--profile-out", type=Path, default=None)
    onboard_parser.add_argument("--foundation-app-id", default=DEFAULT_APP_ID)
    onboard_parser.add_argument("--foundation-app-name", default=DEFAULT_APP_NAME)
    onboard_parser.add_argument("--runtime-binary", type=Path)
    onboard_parser.add_argument("--local", action="store_true", help="install and run Hermes on the host instead of in a container")
    onboard_parser.add_argument("--install-hermes", action="store_true", help="with --local, install pinned Hermes into ignored local state")
    onboard_parser.add_argument("--hermes-extras", default="cli,messaging")
    onboard_parser.add_argument("--container-image", default=DEFAULT_CONTAINER_IMAGE)
    onboard_parser.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME)
    onboard_parser.add_argument("--skip-image-build", action="store_true", help="use an existing container image")
    onboard_parser.add_argument(
        "--slash-only",
        action="store_true",
        help="complete setup for deterministic Telegram commands while leaving normal Hermes chat blocked",
    )
    onboard_parser.add_argument(
        "--hermes-ready",
        action="store_true",
        help="confirm normal Hermes setup already works",
    )
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

    for name, help_text in (
        ("start", "start the containerized Hermes gateway"),
        ("stop", "stop the containerized Hermes gateway"),
        ("status", "show containerized Hermes gateway status"),
    ):
        runtime_parser = subparsers.add_parser(name, help=help_text)
        runtime_parser.add_argument("--runtime-home", type=Path, default=None)
        runtime_parser.add_argument("--weave-root", type=Path, default=None)
        runtime_parser.add_argument("--hermes-home", type=Path, default=None)
        runtime_parser.add_argument("--profile-out", type=Path, default=None)
        runtime_parser.add_argument("--container-image", default=DEFAULT_CONTAINER_IMAGE)
        runtime_parser.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME)

    dashboard_parser = subparsers.add_parser("dashboard", help="show a read-only WEAVE control dashboard")
    dashboard_parser.add_argument("--runtime-home", type=Path, default=None)
    dashboard_parser.add_argument("--weave-root", type=Path, default=None)
    dashboard_parser.add_argument("--hermes-home", type=Path, default=None)
    dashboard_parser.add_argument("--profile-out", type=Path, default=None)
    dashboard_parser.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME)
    dashboard_parser.add_argument("--no-container-check", action="store_true", help="skip the read-only container status probe")
    dashboard_parser.add_argument("--json", action="store_true", help="print dashboard snapshot as JSON")

    export_parser = subparsers.add_parser("export-runtime", help="export reviewable runtime state without secrets")
    export_parser.add_argument("--runtime-home", type=Path, default=None)
    export_parser.add_argument("--weave-root", type=Path, default=None)
    export_parser.add_argument("--hermes-home", type=Path, default=None)
    export_parser.add_argument("--profile-out", type=Path, default=None)
    export_parser.add_argument("--out", dest="export_out", type=Path, required=True)

    import_parser = subparsers.add_parser("import-runtime", help="import a WEAVE runtime state archive")
    import_parser.add_argument("archive", type=Path)
    import_parser.add_argument("--runtime-home", type=Path, default=None)
    import_parser.add_argument("--weave-root", type=Path, default=None)
    import_parser.add_argument("--hermes-home", type=Path, default=None)
    import_parser.add_argument("--profile-out", type=Path, default=None)
    import_parser.add_argument("--force", action="store_true")

    verify_parser = subparsers.add_parser("verify-runtime", help="verify runtime-home state and migration blockers")
    verify_parser.add_argument("--runtime-home", type=Path, default=None)
    verify_parser.add_argument("--weave-root", type=Path, default=None)
    verify_parser.add_argument("--hermes-home", type=Path, default=None)
    verify_parser.add_argument("--profile-out", type=Path, default=None)
    verify_parser.add_argument("--container-image", default=DEFAULT_CONTAINER_IMAGE)
    verify_parser.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME)

    hermes_parser = subparsers.add_parser("hermes", help="inspect or record normal Hermes setup readiness")
    hermes_parser.add_argument("--runtime-home", type=Path, default=None)
    hermes_parser.add_argument("--weave-root", type=Path, default=None)
    hermes_parser.add_argument("--hermes-home", type=Path, default=None)
    hermes_parser.add_argument("--profile-out", type=Path, default=None)
    hermes_parser.add_argument("--hermes-command", default="hermes")
    hermes_subparsers = hermes_parser.add_subparsers(dest="hermes_command_name")
    hermes_subparsers.add_parser("status", help="show non-secret Hermes setup readiness")
    hermes_subparsers.add_parser("confirm-ready", help="record that normal Hermes setup already works")
    hermes_subparsers.add_parser("mark-slash-only", help="record slash-only mode")
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
    if args.command:
        args = resolve_runtime_paths(args)
    try:
        if args.command == "onboard":
            return onboard(args, input_stream=input_stream, output=output, hidden_reader=hidden_reader)
        if args.command == "start":
            return start_container_runtime(args, output)
        if args.command == "stop":
            return stop_container_runtime(args, output)
        if args.command == "status":
            return status_container_runtime(args, output)
        if args.command == "dashboard":
            return dashboard(args, output)
        if args.command == "export-runtime":
            return export_runtime(args, output)
        if args.command == "import-runtime":
            return import_runtime(args, output)
        if args.command == "verify-runtime":
            return verify_runtime(args, output)
        if args.command == "hermes":
            return hermes_command(args, output)
        parser.print_help(output)
        return 0
    except (CliError, setup_gateway.GatewaySetupError, setup_runtime.RuntimeSetupError) as exc:
        print_line(output)
        warn(output, str(exc))
        print_line(output, "  No raw token was printed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
