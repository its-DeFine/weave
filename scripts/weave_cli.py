#!/usr/bin/env python3
"""Human-facing WEAVE CLI."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TextIO

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import setup_gateway
import setup_runtime
import weave_dashboard
import weave_early_lifecycle
import weave_engineering_decisions
import weave_eval
import weave_first_run
import weave_hermes_setup
import weave_launch_ops
import weave_qa_proof
import weave_tui


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
RUNTIME_QA_MANIFEST_SCHEMA = "weave.runtime-qa-manifest/v0.1"
RUNTIME_QA_CLEANUP_POLICY_SCHEMA = "weave.runtime-cleanup-policy/v0.1"
RUNTIME_QA_RESOURCE_STATES = [
    "created",
    "running",
    "completed",
    "teardown_requested",
    "stopped",
    "removed",
    "phased_out",
]
RUNTIME_QA_CLAIM_BOUNDARIES = [
    "plan-only",
    "provisioned-only",
    "ready-readback",
    "local-only verified",
    "container-mesh verified",
    "live-transport verified",
    "external-write verified",
    "cleanup-verified",
    "rehydration-verified",
]
SECRET_EXPORT_NAMES = {
    ".env",
    ".env.local",
    ".envrc",
    ".netrc",
    ".npmrc",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
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
    ".ssh",
    "secrets",
    "tokens",
}
SECRET_EXPORT_CONTENT_RE = re.compile(
    r"("
    r"sk-[A-Za-z0-9_-]{20,}"
    r"|sk-or-v1-[A-Za-z0-9_-]{16,}"
    r"|gh[pousr]_[A-Za-z0-9_]{20,}"
    r"|Bearer\s+[A-Za-z0-9._-]{20,}"
    r"|\b[0-9]{8,12}:[A-Za-z0-9_-]{24,}\b"
    r"|\b[A-Z0-9_]*(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSCODE|CREDENTIAL|PRIVATE[_-]?KEY|SEED|2FA|OTP)[A-Z0-9_]*"
    r"\s*=\s*['\"]?(?!<|\$|\{|your|example|placeholder|xxx|todo|changeme|redacted|true|false|1|0|none|null|empty|\s)"
    r"[^\s'\"]{8,}"
    r")",
    re.IGNORECASE,
)


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
    if hasattr(args, "out") and args.out:
        args.out = args.out.expanduser().resolve()
    if hasattr(args, "archive") and args.archive:
        args.archive = args.archive.expanduser().resolve()
    if getattr(args, "existing_hermes", False):
        args.local = True
        args.install_hermes = False
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
        raise CliError("gateway env is missing; run bin/weave onboard before bin/weave start")
    if not gateway_workdir.exists():
        raise CliError("gateway workdir is missing; run bin/weave onboard before bin/weave start")
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
        if hermes_setup["state"] == "needs_hermes_setup":
            print_line(output, "- next: choose a setup mode")
            print_line(output, "  - normal chat: finish Hermes setup, then run bin/weave onboard --hermes-ready")
            print_line(output, "  - existing Hermes: run bin/weave onboard --existing-hermes --hermes-ready")
            print_line(output, "  - deterministic only: run bin/weave onboard --slash-only")
        else:
            print_line(output, "- next: run bin/weave onboard")
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


def tui(args: argparse.Namespace, input_stream: TextIO, output: TextIO) -> int:
    return weave_tui.run(args, input_stream=input_stream, output=output)


def first_run(args: argparse.Namespace, output: TextIO) -> int:
    return weave_first_run.run(args, output=output)


def early_lifecycle(args: argparse.Namespace, output: TextIO) -> int:
    return weave_early_lifecycle.run(args, output=output)


def engineering_decisions(args: argparse.Namespace, output: TextIO) -> int:
    return weave_engineering_decisions.run(args, output=output)


def qa_proof(args: argparse.Namespace, output: TextIO) -> int:
    return weave_qa_proof.run(args, output=output)


def launch_ops(args: argparse.Namespace, output: TextIO) -> int:
    return weave_launch_ops.run(args, output=output)


def docker_status(container_name: str) -> str:
    docker = shutil.which("docker")
    if not docker:
        return "unknown; docker unavailable"
    result = run_process(
        [
            docker,
            "ps",
            "-a",
            "--filter",
            f"name={container_name}",
            "--format",
            "{{.Names}}\t{{.Status}}\t{{.Image}}",
        ]
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return f"error; {detail}"
    text = result.stdout.strip()
    return text or f"not_found; name={container_name}"


def doctor(args: argparse.Namespace, output: TextIO) -> int:
    hermes_setup = weave_hermes_setup.hermes_setup_status(args.hermes_home)
    root_ready = setup_runtime.weave_runtime_slice.root_ready(args.weave_root)
    plugin_path = args.hermes_home / "plugins" / setup_runtime.HERMES_PLUGIN_NAME / "plugin.yaml"
    env_file = args.hermes_home / ".env"
    token_configured = env_file.exists() and "TELEGRAM_BOT_TOKEN=" in env_file.read_text(encoding="utf-8", errors="ignore")

    print_line(output, "WEAVE Doctor")
    print_line(output, "")
    print_line(output, "Runtime")
    print_line(output, f"- runtime_home: {args.runtime_home} ({path_state(args.runtime_home)})")
    print_line(output, f"- weave_root: {args.weave_root} ({path_state(args.weave_root)})")
    print_line(output, f"- hermes_home: {args.hermes_home} ({path_state(args.hermes_home)})")
    print_line(output, f"- runtime_profile: {args.profile_out} ({path_state(args.profile_out)})")
    print_line(output, f"- deterministic_layer_ready: {str(root_ready).lower()}")
    print_line(output, "")
    print_line(output, "Hermes")
    print_line(output, f"- setup_state: {hermes_setup['state']}")
    print_line(output, f"- normal_chat_assumed_ready: {str(hermes_setup['normal_chat_assumed_ready']).lower()}")
    print_line(output, f"- binary_found: {str(hermes_setup['binary']['found']).lower()}")
    if hermes_setup["binary"].get("path"):
        print_line(output, f"- binary_path: {hermes_setup['binary']['path']}")
    print_line(output, f"- weave_plugin: {path_state(plugin_path)}")
    print_line(output, "")
    print_line(output, "Telegram/Gateway")
    print_line(output, f"- gateway_env: {env_status(env_file)}")
    print_line(output, f"- telegram_token_configured: {str(token_configured).lower()}")
    print_line(output, f"- container: {docker_status(args.container_name)}")
    print_line(output, "")
    print_line(output, "Next")
    if not root_ready:
        if hermes_setup["state"] == "needs_hermes_setup":
            print_line(output, "- normal chat: bin/weave onboard --hermes-ready after Hermes works")
            print_line(output, "- existing Hermes attach: bin/weave onboard --existing-hermes --hermes-ready")
            print_line(output, "- deterministic only: bin/weave onboard --slash-only")
        else:
            print_line(output, "- run bin/weave onboard")
    elif not token_configured:
        print_line(output, "- pair Telegram: bin/weave onboard --slash-only or bin/weave onboard --hermes-ready")
    else:
        print_line(output, "- inspect deterministic wall: bin/weave command /status")
    print_line(output, "- secret_value_printed: false")
    return 0


def command_runtime(args: argparse.Namespace, output: TextIO) -> int:
    text = " ".join(args.telegram_command).strip()
    if not text:
        raise CliError("command requires a deterministic WEAVE command, e.g. bin/weave command /status")
    setup_runtime.weave_runtime_slice.setup_weave_root(args.weave_root)
    response = setup_runtime.weave_runtime_slice.dispatch_telegram_command(args.weave_root, text)
    if args.json:
        print_line(output, json.dumps(response, indent=2, sort_keys=True))
    else:
        print_line(output, f"deterministic: {str(response.get('deterministic', False)).lower()}; llm_used: {str(response.get('llm_used', True)).lower()}")
        print_line(output, "")
        print_line(output, str(response.get("text", "")))
    return 0 if response.get("handled") else 1

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
    print_line(output, "    bin/weave onboard --hermes-ready")
    print_line(output, "  Or record readiness directly:")
    print_line(output, "    bin/weave hermes confirm-ready")
    print_line(output, "  For deterministic Telegram commands only, rerun:")
    print_line(output, "    bin/weave onboard --slash-only")


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
        if args.slash_only:
            warn(output, "slash-only dry run: normal Hermes chat will remain blocked")
            print_line(output, "  deterministic Telegram commands will be configured without normal-chat readiness")
        elif args.existing_hermes:
            print_line(output, "  mode: existing Hermes attach")
            print_line(output, "  WEAVE will not install Hermes, mutate provider auth, start a service, or change autostart")
            print_line(output, "  would require --hermes-ready once the selected Hermes profile can chat")
        elif args.hermes_ready:
            print_line(output, "  would record operator-confirmed Hermes readiness for this runtime home")
        else:
            print_hermes_setup_guidance(output, args.hermes_home)
            print_line(output, "  would require normal Hermes setup confirmation or explicit --slash-only")
        print_step(output, 2, 6, "Runtime", "Create a local WEAVE root and Hermes gateway context.")
        warn(output, "dry run: no Telegram token will be requested or written")
        if args.existing_hermes:
            print_line(output, "  mode: existing Hermes attach")
            print_line(output, "  would attach WEAVE plugin/config to the selected Hermes home")
            if args.runtime_binary:
                print_line(output, f"  would use Hermes binary: {args.runtime_binary}")
            else:
                print_line(output, "  would discover Hermes binary from PATH")
        elif args.local:
            print_line(output, "  mode: local host install")
            if args.install_hermes:
                print_line(output, "  would install pinned Hermes into ignored local state")
            else:
                print_line(output, "  would use an existing host Hermes binary")
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
        continue_flags = []
        if args.existing_hermes:
            continue_flags.append("--existing-hermes")
        if args.slash_only:
            continue_flags.append("--slash-only")
        elif args.hermes_ready:
            continue_flags.append("--hermes-ready")
        if args.local and not args.existing_hermes:
            continue_flags.append("--local")
        if args.install_hermes:
            continue_flags.append("--install-hermes")
        print_line(output, "  bin/weave onboard" + (" " + " ".join(continue_flags) if continue_flags else ""))
        return 0

    hermes_setup = require_or_mark_hermes(args, output)
    if hermes_setup["state"] == "slash_only":
        print_line(output, "  /status, /apps, and /help will work without normal Hermes chat.")

    print_step(output, 2, 6, "Runtime", "Create a local WEAVE root and Hermes gateway context.")
    if args.local:
        if getattr(args, "existing_hermes", False):
            success(output, "existing Hermes attach selected; WEAVE will not install Hermes")
        else:
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
        print_line(output, "    bin/weave start")
        print_line(output, "  Inspect it:")
        print_line(output, "    bin/weave status")

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


def export_file_contains_secret(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        if path.stat().st_size > 1_000_000:
            return False
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    return bool(SECRET_EXPORT_CONTENT_RE.search(text))


def add_json_to_tar(tar: tarfile.TarFile, arcname: str, payload: dict[str, object]) -> None:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    info = tarfile.TarInfo(arcname)
    info.size = len(encoded)
    info.mode = 0o600
    tar.addfile(info, io.BytesIO(encoded))


def export_runtime(args: argparse.Namespace, output: TextIO) -> int:
    if not args.runtime_home.exists():
        raise CliError("runtime home is missing; run bin/weave onboard before exporting")
    args.export_out.parent.mkdir(parents=True, exist_ok=True)
    excluded: list[str] = []
    included = 0
    with tarfile.open(args.export_out, "w:gz") as tar:
        for path in sorted(args.runtime_home.rglob("*")):
            if path.resolve() == args.export_out:
                continue
            rel = path.relative_to(args.runtime_home)
            if should_exclude_export(rel) or export_file_contains_secret(path):
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


def runtime_qa_safe_label(value: str) -> str:
    label = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip()).strip("-.")
    return label[:80] or "runtime-qa"


def default_runtime_qa_run_id(app_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"qa-{stamp}-{runtime_qa_safe_label(app_id)}"


def runtime_qa_cleanup_labels(args: argparse.Namespace, qa_run_id: str) -> dict[str, str]:
    return {
        "weave.qa.disposable": "true",
        "weave.qa.run_id": qa_run_id,
        "weave.app_id": args.app_id,
        "weave.lifecycle_stage": "06-qa",
    }


def runtime_qa_planned_commands(args: argparse.Namespace, qa_run_id: str, compose_project: str) -> list[dict[str, object]]:
    labels = runtime_qa_cleanup_labels(args, qa_run_id)
    label_flags = [flag for key, value in labels.items() for flag in ("--label", f"{key}={value}")]
    return [
        {
            "id": "export-runtime-before-removal",
            "purpose": "archive sanitized runtime-home state before deleting disposable surfaces",
            "command": [
                "bin/weave",
                "export-runtime",
                "--runtime-home",
                str(args.runtime_home),
                "--out",
                f"runs/runtime-qa/{qa_run_id}/runtime-export.tar.gz",
            ],
            "executes_in_dry_run": False,
        },
        {
            "id": "launch-container",
            "purpose": "create the disposable QA container with cleanup labels",
            "command": [
                "docker",
                "run",
                "-d",
                "--name",
                args.container_name,
                *label_flags,
                args.container_image,
            ],
            "executes_in_dry_run": False,
        },
        {
            "id": "stop-container",
            "purpose": "stop accepting work after scenario/evidence capture",
            "command": ["docker", "stop", "--time", "20", args.container_name],
            "executes_in_dry_run": False,
        },
        {
            "id": "remove-container",
            "purpose": "delete the disposable container after archive and drain gates pass",
            "command": ["docker", "rm", args.container_name],
            "executes_in_dry_run": False,
        },
        {
            "id": "compose-down",
            "purpose": "phase out a compose-backed QA room without deleting durable named volumes by default",
            "command": ["docker", "compose", "-p", compose_project, "down", "--remove-orphans"],
            "executes_in_dry_run": False,
        },
        {
            "id": "verify-rehydrated-runtime",
            "purpose": "prove a future re-up/import before making renewed behavior claims",
            "command": ["bin/weave", "verify-runtime", "--runtime-home", str(args.runtime_home)],
            "executes_in_dry_run": False,
        },
    ]


def build_runtime_qa_manifest(args: argparse.Namespace) -> dict[str, object]:
    qa_run_id = args.qa_run_id or default_runtime_qa_run_id(args.app_id)
    compose_project = args.compose_project or f"weave-qa-{runtime_qa_safe_label(qa_run_id)}"
    labels = runtime_qa_cleanup_labels(args, qa_run_id)
    evidence_ref = f"runs/runtime-qa/{qa_run_id}/evidence"
    archive_ref = f"runs/runtime-qa/{qa_run_id}/runtime-export.tar.gz"
    claim_boundary = "plan-only"
    return {
        "schema": RUNTIME_QA_MANIFEST_SCHEMA,
        "qa_run_id": qa_run_id,
        "app_id": args.app_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dry_run": bool(args.dry_run),
        "claim_boundary": claim_boundary,
        "allowed_claims": RUNTIME_QA_CLAIM_BOUNDARIES,
        "resource_states": RUNTIME_QA_RESOURCE_STATES,
        "topology": {
            "agent_count": args.agent_count,
            "isolation": args.isolation,
            "runtime_surface": args.runtime_surface,
            "proof_boundary_requested": args.proof_boundary,
            "runtime_home": str(args.runtime_home),
            "weave_root": str(args.weave_root),
            "hermes_home": str(args.hermes_home),
            "profile_out": str(args.profile_out),
            "credential_source_ref_only": True,
        },
        "resources": [
            {
                "id": args.container_name,
                "type": "docker-container",
                "current_state": "planned_only",
                "planned_states": RUNTIME_QA_RESOURCE_STATES,
                "image": args.container_image,
                "labels": labels,
                "evidence": "not created in this plan/dry-run slice",
            },
            {
                "id": compose_project,
                "type": "docker-compose-project",
                "current_state": "planned_only",
                "planned_states": RUNTIME_QA_RESOURCE_STATES,
                "remove_orphans": True,
                "remove_named_volumes_by_default": False,
                "evidence": "not created in this plan/dry-run slice",
            },
            {
                "id": str(args.runtime_home),
                "type": "runtime-home",
                "current_state": "planned_only",
                "planned_states": ["created", "completed", "teardown_requested", "phased_out"],
                "archive_required_before_delete": True,
                "evidence": archive_ref,
            },
        ],
        "teardown_policy": {
            "schema": RUNTIME_QA_CLEANUP_POLICY_SCHEMA,
            "required": True,
            "archive_required_before_remove": True,
            "evidence_ref": evidence_ref,
            "archive_ref": archive_ref,
            "redaction_scan_required": True,
            "raw_secrets_in_contract": False,
            "raw_secrets_in_evidence": False,
            "credential_source_ref_only": True,
            "stop_policy": {
                "drain_timeout_seconds": 60,
                "stop_grace_seconds": 20,
                "force_stop_after_seconds": 120,
                "accept_new_work_during_drain": False,
            },
            "container_policy": {
                "remove_after_stop": True,
                "required_labels": [f"{key}={value}" for key, value in labels.items()],
            },
            "compose_policy": {
                "compose_project": compose_project,
                "remove_orphans": True,
                "remove_named_volumes": False,
                "remove_anonymous_volumes": True,
                "delete_images": False,
            },
            "profile_policy": {
                "archive_before_delete": True,
                "delete_ephemeral_homes": True,
                "preserve_sanitized_export": True,
            },
            "quarantine_on": [
                "secret_scan_failed",
                "unexpected_external_write",
                "failed_drain",
                "cleanup_incomplete",
            ],
        },
        "rehydrate_policy": {
            "source": archive_ref,
            "requires_secret_relink": True,
            "requires_verify_runtime": True,
            "requires_scenario_rerun_for_behavior_claim": True,
        },
        "planned_commands": runtime_qa_planned_commands(args, qa_run_id, compose_project),
        "proof_requirements": [
            "inside-runtime provider/model/tool/MCP readback before scenario claims",
            "sender and receiver readback for communication claims",
            "no pending work accepted after teardown_requested",
            "sanitized runtime export checksum before removal",
            "container/compose absence proof after removal",
            "verify-runtime pass before any rehydration claim",
        ],
        "explicit_non_claims": [
            "No Docker command was executed by this plan/dry-run slice.",
            "No container was created, started, stopped, or removed by this manifest generation.",
            "Plan-only does not prove runtime behavior, live transport, cleanup completion, or rehydration.",
        ],
    }


def runtime_qa(args: argparse.Namespace, output: TextIO) -> int:
    manifest = build_runtime_qa_manifest(args)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print_line(output, json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print_line(output, "WEAVE Runtime QA Plan")
        print_line(output, f"- qa_run_id: {manifest['qa_run_id']}")
        print_line(output, "- state: plan-only")
        print_line(output, f"- manifest: {args.out if args.out else 'stdout only'}")
        print_line(output, "- teardown_policy_required: true")
        print_line(output, "- resource_states: " + ", ".join(RUNTIME_QA_RESOURCE_STATES))
        print_line(output, "- no_docker_executed: true")
        print_line(output, "- next: execute in an isolated container only after approval, then export evidence before remove")
    return 0


def eval_contract(args: argparse.Namespace, output: TextIO) -> int:
    eval_args: list[str] = []
    if args.eval_stage:
        eval_args.append(args.eval_stage)
    if args.list_eval_contracts:
        eval_args.append("--list")
    if args.contract_file:
        eval_args.extend(["--contract-file", str(args.contract_file)])
    if args.review_file:
        eval_args.extend(["--review-file", str(args.review_file)])
    if args.review_template:
        eval_args.append("--review-template")
    if args.artifact:
        eval_args.extend(["--artifact", args.artifact])
    if args.run_gates:
        eval_args.append("--run-gates")
    if args.strict:
        eval_args.append("--strict")
    if args.json:
        eval_args.append("--json")
    return weave_eval.main(eval_args, output=output)


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
    onboard_parser.add_argument(
        "--existing-hermes",
        action="store_true",
        help="attach WEAVE deterministic state/plugin to an already working Hermes install; do not install Hermes",
    )
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
        ("doctor", "diagnose WEAVE setup and print the next exact action"),
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

    tui_parser = subparsers.add_parser("tui", help="run the interactive WEAVE lifecycle cockpit")
    tui_parser.add_argument("--runtime-home", type=Path, default=None)
    tui_parser.add_argument("--weave-root", type=Path, default=None)
    tui_parser.add_argument("--hermes-home", type=Path, default=None)
    tui_parser.add_argument("--profile-out", type=Path, default=None)
    tui_parser.add_argument("--app-id", default="tui-demo")
    tui_parser.add_argument("--app-name", default="TUI Demo")
    tui_parser.add_argument("--app-surface", choices=weave_tui.APP_SURFACES, default=weave_tui.DEFAULT_APP_SURFACE)
    tui_parser.add_argument("--owner-experience", default=weave_first_run.DEFAULT_OWNER_EXPERIENCE)
    tui_parser.add_argument("--coworker-style", default=weave_first_run.DEFAULT_COWORKER_STYLE)
    tui_parser.add_argument(
        "--control-mode",
        choices=("hands-on", "hands-off", "handoff"),
        default=weave_first_run.DEFAULT_CONTROL_MODE,
        help="hands-off/handoff means full handoff until a hard gate is reached",
    )
    tui_parser.add_argument("--intent", default=weave_tui.DEFAULT_INTENT)
    tui_parser.add_argument("--target-user", default=weave_tui.DEFAULT_TARGET_USER)
    tui_parser.add_argument("--deployment-region", default=weave_early_lifecycle.DEFAULT_DEPLOYMENT_REGION)
    tui_parser.add_argument("--marketing-budget", default=weave_early_lifecycle.DEFAULT_MARKETING_BUDGET)
    tui_parser.add_argument("--owner-feedback", default="")
    tui_parser.add_argument("--engineering-owner-response", default="owner accepts local-safe engineering scaffold")
    tui_parser.add_argument("--qa-command", default=weave_tui.DEFAULT_QA_COMMAND)
    tui_parser.add_argument("--codex-command", default=weave_tui.DEFAULT_CODEX_COMMAND)
    tui_parser.add_argument("--codex-timeout", type=int, default=5)
    tui_parser.add_argument("--skip-codex-proof", action="store_true")
    tui_parser.add_argument("--run-engineering-gates", action="store_true", help="run Engineering eval command gates before formal approval")
    tui_parser.add_argument("--scripted-demo", action="store_true", help="run non-interactively for CI and local proof")
    tui_parser.add_argument("--write", action="store_true", help="write local lifecycle artifacts through QA and gated launch plans")
    tui_parser.add_argument("--no-color", action="store_true", help="disable ANSI color")
    tui_parser.add_argument("--json", action="store_true", help="print machine-readable TUI session proof")

    first_run_parser = subparsers.add_parser("first-run", help="preview or write local WEAVE product first-run state")
    first_run_parser.add_argument("--runtime-home", type=Path, default=None)
    first_run_parser.add_argument("--weave-root", type=Path, default=None)
    first_run_parser.add_argument("--hermes-home", type=Path, default=None)
    first_run_parser.add_argument("--profile-out", type=Path, default=None)
    first_run_parser.add_argument("--hermes-command", default="hermes")
    first_run_parser.add_argument("--app-id", default="new-app")
    first_run_parser.add_argument("--app-name", default="New App")
    first_run_parser.add_argument("--owner-experience", default=weave_first_run.DEFAULT_OWNER_EXPERIENCE)
    first_run_parser.add_argument("--coworker-style", default=weave_first_run.DEFAULT_COWORKER_STYLE)
    first_run_parser.add_argument(
        "--control-mode",
        choices=("hands-on", "hands-off"),
        default=weave_first_run.DEFAULT_CONTROL_MODE,
        help="whether future lifecycle agents should stop for consequential owner decisions",
    )
    first_run_parser.add_argument(
        "--setup-choice",
        choices=("create-local", "attach-existing", "defer-runtime"),
        default=weave_first_run.DEFAULT_SETUP_CHOICE,
        help="local runtime posture for this product surface; remote attach is deliberately deferred in ATM-245",
    )
    first_run_parser.add_argument("--write", action="store_true", help="create local runtime/app state and validated first-run artifact")
    first_run_parser.add_argument("--json", action="store_true", help="print first-run snapshot as JSON")

    early_lifecycle_parser = subparsers.add_parser(
        "early-lifecycle",
        help="run the local Intent, Research, Selection, and Plan workflow",
    )
    early_lifecycle_parser.add_argument("--runtime-home", type=Path, default=None)
    early_lifecycle_parser.add_argument("--weave-root", type=Path, default=None)
    early_lifecycle_parser.add_argument("--hermes-home", type=Path, default=None)
    early_lifecycle_parser.add_argument("--profile-out", type=Path, default=None)
    early_lifecycle_parser.add_argument("--app-id", default="new-app")
    early_lifecycle_parser.add_argument("--app-name", default="New App")
    early_lifecycle_parser.add_argument("--intent", default=weave_early_lifecycle.DEFAULT_INTENT)
    early_lifecycle_parser.add_argument("--target-user", default=weave_early_lifecycle.DEFAULT_TARGET_USER)
    early_lifecycle_parser.add_argument("--deployment-region", default=weave_early_lifecycle.DEFAULT_DEPLOYMENT_REGION)
    early_lifecycle_parser.add_argument("--marketing-budget", default=weave_early_lifecycle.DEFAULT_MARKETING_BUDGET)
    early_lifecycle_parser.add_argument("--owner-feedback", default="")
    early_lifecycle_parser.add_argument(
        "--control-mode",
        choices=("hands-on", "hands-off"),
        default=weave_first_run.DEFAULT_CONTROL_MODE,
        help="whether later lifecycle agents should stop for consequential owner decisions",
    )
    early_lifecycle_parser.add_argument("--create-app", action="store_true", help="create the local app if it does not exist")
    early_lifecycle_parser.add_argument("--write", action="store_true", help="write stage artifacts, reviews, approvals, and lifecycle bundle")
    early_lifecycle_parser.add_argument("--json", action="store_true", help="print early lifecycle snapshot as JSON")

    engineering_decisions_parser = subparsers.add_parser(
        "engineering-decisions",
        help="record Engineering owner decisions, notifications, assumptions, and hard-stop state",
    )
    engineering_decisions_parser.add_argument("--runtime-home", type=Path, default=None)
    engineering_decisions_parser.add_argument("--weave-root", type=Path, default=None)
    engineering_decisions_parser.add_argument("--hermes-home", type=Path, default=None)
    engineering_decisions_parser.add_argument("--profile-out", type=Path, default=None)
    engineering_decisions_parser.add_argument("--app-id", default="new-app")
    engineering_decisions_parser.add_argument("--decision-id", default=weave_engineering_decisions.DEFAULT_DECISION_ID)
    engineering_decisions_parser.add_argument("--question", default=weave_engineering_decisions.DEFAULT_QUESTION)
    engineering_decisions_parser.add_argument(
        "--control-mode",
        choices=("hands-on", "hands-off"),
        default=weave_first_run.DEFAULT_CONTROL_MODE,
    )
    engineering_decisions_parser.add_argument(
        "--decision-type",
        choices=("architecture", "library", "scope", "cost", "security", "deployment", "product", "capability", "public_action", "other"),
        default="architecture",
    )
    engineering_decisions_parser.add_argument(
        "--hard-boundary",
        action="append",
        choices=weave_engineering_decisions.HARD_BOUNDARIES,
        help="hard owner boundary touched by this decision; can be passed more than once",
    )
    engineering_decisions_parser.add_argument("--selected-option", default="local-safe-path")
    engineering_decisions_parser.add_argument("--owner-response", default=weave_engineering_decisions.DEFAULT_OWNER_RESPONSE)
    engineering_decisions_parser.add_argument("--write", action="store_true", help="write local engineering decision queue state")
    engineering_decisions_parser.add_argument("--json", action="store_true", help="print engineering decision snapshot as JSON")

    qa_proof_parser = subparsers.add_parser(
        "qa-proof",
        help="run surface-specific local QA proof and failure routing",
    )
    qa_proof_parser.add_argument("--runtime-home", type=Path, default=None)
    qa_proof_parser.add_argument("--weave-root", type=Path, default=None)
    qa_proof_parser.add_argument("--hermes-home", type=Path, default=None)
    qa_proof_parser.add_argument("--profile-out", type=Path, default=None)
    qa_proof_parser.add_argument("--app-id", default="new-app")
    qa_proof_parser.add_argument("--app-name", default="New App")
    qa_proof_parser.add_argument("--surface", choices=weave_qa_proof.QA_SURFACES, default="mixed")
    qa_proof_parser.add_argument("--command", dest="qa_command", default=weave_qa_proof.DEFAULT_COMMAND)
    qa_proof_parser.add_argument("--target-label", default="local deterministic fixture")
    qa_proof_parser.add_argument("--create-app", action="store_true", help="create the local app if it does not exist")
    qa_proof_parser.add_argument("--write", action="store_true", help="write local QA proof evidence and lifecycle bundle")
    qa_proof_parser.add_argument("--json", action="store_true", help="print QA proof snapshot as JSON")

    launch_ops_parser = subparsers.add_parser(
        "launch-ops",
        help="write gated deployment, KPI, marketing, and iteration local workflows",
    )
    launch_ops_parser.add_argument("--runtime-home", type=Path, default=None)
    launch_ops_parser.add_argument("--weave-root", type=Path, default=None)
    launch_ops_parser.add_argument("--hermes-home", type=Path, default=None)
    launch_ops_parser.add_argument("--profile-out", type=Path, default=None)
    launch_ops_parser.add_argument("--app-id", default="new-app")
    launch_ops_parser.add_argument("--app-name", default="New App")
    launch_ops_parser.add_argument("--deployment-region", default=weave_launch_ops.DEFAULT_DEPLOYMENT_REGION)
    launch_ops_parser.add_argument("--marketing-budget", default=weave_launch_ops.DEFAULT_MARKETING_BUDGET)
    launch_ops_parser.add_argument("--feedback-source", default="local feedback artifacts")
    launch_ops_parser.add_argument("--create-app", action="store_true", help="create the local app if it does not exist")
    launch_ops_parser.add_argument("--write", action="store_true", help="write local launch operation artifacts")
    launch_ops_parser.add_argument("--json", action="store_true", help="print launch operation snapshot as JSON")

    command_parser = subparsers.add_parser("command", help="run a deterministic WEAVE slash command locally")
    command_parser.add_argument("--runtime-home", type=Path, default=None)
    command_parser.add_argument("--weave-root", type=Path, default=None)
    command_parser.add_argument("--hermes-home", type=Path, default=None)
    command_parser.add_argument("--profile-out", type=Path, default=None)
    command_parser.add_argument("--json", action="store_true", help="print the full deterministic response JSON")
    command_parser.add_argument("telegram_command", nargs=argparse.REMAINDER, help="slash command, e.g. /status or /apps --all")

    eval_parser = subparsers.add_parser("eval", help="run evidence-bound lifecycle or release-readiness evals")
    eval_parser.add_argument("eval_stage", nargs="?", help="lifecycle stage or release-readiness")
    eval_parser.add_argument("--list", dest="list_eval_contracts", action="store_true", help="list available eval contracts")
    eval_parser.add_argument("--contract-file", type=Path, help="load an explicit eval contract file")
    eval_parser.add_argument("--review-file", type=Path, help="JSON/YAML review with rubric scores and evidence")
    eval_parser.add_argument("--review-template", action="store_true", help="print a review template for this contract")
    eval_parser.add_argument("--artifact", default="current", help="artifact label/path being evaluated")
    eval_parser.add_argument("--run-gates", action="store_true", help="execute command hard gates")
    eval_parser.add_argument("--strict", action="store_true", help="exit non-zero unless decision can advance")
    eval_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")

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

    runtime_qa_parser = subparsers.add_parser("runtime-qa", help="plan disposable runtime QA lifecycle and teardown")
    runtime_qa_parser.add_argument("--runtime-home", type=Path, default=None)
    runtime_qa_parser.add_argument("--weave-root", type=Path, default=None)
    runtime_qa_parser.add_argument("--hermes-home", type=Path, default=None)
    runtime_qa_parser.add_argument("--profile-out", type=Path, default=None)
    runtime_qa_parser.add_argument("--container-image", default=DEFAULT_CONTAINER_IMAGE)
    runtime_qa_parser.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME)
    runtime_qa_parser.add_argument("--qa-run-id")
    runtime_qa_parser.add_argument("--app-id", default=DEFAULT_APP_ID)
    runtime_qa_parser.add_argument("--compose-project")
    runtime_qa_parser.add_argument("--agent-count", type=int, default=2)
    runtime_qa_parser.add_argument("--isolation", choices=("container", "worktree", "profile", "mixed"), default="container")
    runtime_qa_parser.add_argument(
        "--runtime-surface",
        choices=("hermes-cli", "hermes-gateway", "mcp-server", "a2a-transport", "xmtp-adapter", "mixed"),
        default="mixed",
    )
    runtime_qa_parser.add_argument(
        "--proof-boundary",
        choices=("local-only", "container-mesh", "live-transport", "external-write-verified"),
        default="container-mesh",
    )
    runtime_qa_parser.add_argument("--out", type=Path, help="write the runtime QA manifest JSON here")
    runtime_qa_parser.add_argument("--dry-run", action="store_true", help="plan only; never execute Docker or mutate runtimes")
    runtime_qa_parser.add_argument("--json", action="store_true", help="print the manifest JSON")

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


def subparser_choices(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:  # argparse exposes no public lookup for subcommands.
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    return {}


def print_help_alias(parser: argparse.ArgumentParser, argv: list[str], output: TextIO) -> int:
    if len(argv) == 1:
        parser.print_help(output)
        print_line(output, "")
        print_line(output, "Convenience aliases:")
        print_line(output, "  weave help [command]")
        print_line(output, "  weave attach-hermes [onboard flags]  # alias for weave onboard --existing-hermes")
        print_line(output, "  weave tui --scripted-demo --write --no-color")
        print_line(output, "  weave first-run --app-id demo --app-name 'Demo App'")
        print_line(output, "  weave early-lifecycle --app-id demo --create-app --write")
        print_line(output, "  weave engineering-decisions --app-id demo --hard-boundary production_deploy --write")
        print_line(output, "  weave qa-proof --app-id demo --surface mixed --create-app --write")
        print_line(output, "  weave launch-ops --app-id demo --create-app --write")
        print_line(output, "  weave runtime-qa --dry-run --out runs/runtime-qa/plan.json")
        print_line(output, "  weave eval --list")
        return 0
    topic = argv[1]
    if topic == "attach-hermes":
        topic = "onboard"
        print_line(output, "Alias: weave attach-hermes is weave onboard --existing-hermes")
        print_line(output, "")
    choices = subparser_choices(parser)
    command_parser = choices.get(topic)
    if command_parser is None:
        raise CliError(f"unknown help topic: {argv[1]}")
    command_parser.print_help(output)
    return 0


def normalize_alias_argv(argv: list[str]) -> list[str]:
    if argv and argv[0] == "attach-hermes":
        return ["onboard", "--existing-hermes", *argv[1:]]
    return argv


def main(
    argv: list[str] | None = None,
    *,
    input_stream: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    hidden_reader: Callable[[str], str] | None = None,
) -> int:
    parser = build_parser()
    argv_list = sys.argv[1:] if argv is None else list(argv)
    try:
        if argv_list and argv_list[0] == "help":
            return print_help_alias(parser, argv_list, output)
        argv_list = normalize_alias_argv(argv_list)
        args = parser.parse_args(argv_list)
        if args.command:
            args = resolve_runtime_paths(args)
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
        if args.command == "tui":
            return tui(args, input_stream, output)
        if args.command == "first-run":
            return first_run(args, output)
        if args.command == "early-lifecycle":
            return early_lifecycle(args, output)
        if args.command == "engineering-decisions":
            return engineering_decisions(args, output)
        if args.command == "qa-proof":
            return qa_proof(args, output)
        if args.command == "launch-ops":
            return launch_ops(args, output)
        if args.command == "doctor":
            return doctor(args, output)
        if args.command == "command":
            return command_runtime(args, output)
        if args.command == "eval":
            return eval_contract(args, output)
        if args.command == "export-runtime":
            return export_runtime(args, output)
        if args.command == "import-runtime":
            return import_runtime(args, output)
        if args.command == "verify-runtime":
            return verify_runtime(args, output)
        if args.command == "runtime-qa":
            return runtime_qa(args, output)
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
