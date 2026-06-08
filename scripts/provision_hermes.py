#!/usr/bin/env python3
"""Provision the real Nous Hermes Agent for local WEAVE runtime use.

The provisioner intentionally avoids the upstream curl-pipe-shell installer.
It performs explicit, reviewable steps inside the ignored local ``runs/``
directory:

1. clone or update the upstream repository
2. check out a pinned commit
3. create an isolated virtual environment
4. install the Hermes package into that environment
5. write a local proof profile

It does not install services, mutate shell startup files, load secrets, pair a
gateway, or start Hermes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INSTALL_ROOT = REPO_ROOT / "runs" / "hermes-agent"
DEFAULT_PROFILE_PATH = DEFAULT_INSTALL_ROOT / "profile.json"
HERMES_REPO_URL = "https://github.com/NousResearch/hermes-agent.git"
HERMES_PINNED_COMMIT = "5921d667855880b0aa2083a50f001748aed52f3e"
HERMES_MIN_PYTHON = (3, 11)
HERMES_UV_PYTHON = "3.13"
PROFILE_SCHEMA = "weave-hermes-provision-profile/v0.1"


class HermesProvisionError(Exception):
    pass


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    cwd: str | None
    returncode: int
    stdout: str
    stderr: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except OSError as exc:
        raise HermesProvisionError(f"failed to run {command[0]!r}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise HermesProvisionError(f"command timed out: {' '.join(command)}") from exc

    command_result = CommandResult(
        command=command,
        cwd=str(cwd) if cwd else None,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise HermesProvisionError(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return command_result


def ensure_git() -> None:
    if shutil.which("git") is None:
        raise HermesProvisionError("git is required to provision Hermes")


def ensure_python(python: str) -> str:
    result = run_command(
        [python, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
        timeout=30,
    )
    version_text = result.stdout.strip()
    try:
        major, minor = (int(part) for part in version_text.split(".", 1))
    except ValueError as exc:
        raise HermesProvisionError(f"could not parse Python version from {python!r}: {version_text}") from exc
    if (major, minor) < HERMES_MIN_PYTHON:
        required = ".".join(str(part) for part in HERMES_MIN_PYTHON)
        raise HermesProvisionError(f"Hermes requires Python >= {required}; got {version_text}")
    return python


def git_head(path: Path) -> str:
    result = run_command(["git", "rev-parse", "HEAD"], cwd=path, timeout=30)
    return result.stdout.strip()


def assert_commit(value: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise HermesProvisionError("Hermes commit must be a full 40-character SHA-1")


def clone_or_update_source(
    *,
    source_path: Path,
    repo_url: str,
    commit: str,
    source_repo: Path | None,
    timeout: int,
) -> None:
    assert_commit(commit)
    ensure_git()
    source_path.parent.mkdir(parents=True, exist_ok=True)
    remote = str(source_repo.resolve()) if source_repo else repo_url

    if not (source_path / ".git").exists():
        if source_path.exists() and any(source_path.iterdir()):
            raise HermesProvisionError(f"{source_path} exists and is not an empty git checkout")
        source_path.mkdir(parents=True, exist_ok=True)
        run_command(["git", "init", "-q"], cwd=source_path, timeout=30)
        run_command(["git", "remote", "add", "origin", remote], cwd=source_path, timeout=30)
    else:
        existing_remote = run_command(
            ["git", "remote", "get-url", "origin"],
            cwd=source_path,
            timeout=30,
            check=False,
        )
        if existing_remote.returncode != 0:
            run_command(["git", "remote", "add", "origin", remote], cwd=source_path, timeout=30)
        elif existing_remote.stdout.strip() != remote:
            run_command(["git", "remote", "set-url", "origin", remote], cwd=source_path, timeout=30)

    run_command(["git", "fetch", "--depth", "1", "origin", commit], cwd=source_path, timeout=timeout)
    run_command(["git", "checkout", "--detach", commit], cwd=source_path, timeout=timeout)
    head = git_head(source_path)
    if head != commit:
        raise HermesProvisionError(f"Hermes source checkout mismatch: expected {commit}, got {head}")


def validate_source_shape(source_path: Path) -> dict[str, str]:
    pyproject = source_path / "pyproject.toml"
    cli = source_path / "hermes_cli" / "main.py"
    runner = source_path / "run_agent.py"
    missing = [str(path.relative_to(source_path)) for path in (pyproject, cli, runner) if not path.exists()]
    if missing:
        raise HermesProvisionError(f"Hermes source checkout missing required file(s): {', '.join(missing)}")

    pyproject_text = pyproject.read_text(encoding="utf-8")
    if 'name = "hermes-agent"' not in pyproject_text:
        raise HermesProvisionError("Hermes pyproject does not identify package name hermes-agent")
    if 'hermes = "hermes_cli.main:main"' not in pyproject_text:
        raise HermesProvisionError("Hermes pyproject does not expose the hermes console script")

    version_match = re.search(r'^version = "([^"]+)"$', pyproject_text, flags=re.MULTILINE)
    return {
        "package_name": "hermes-agent",
        "package_version": version_match.group(1) if version_match else "unknown",
    }


def create_venv(*, install_root: Path, python: str, timeout: int) -> Path:
    venv_path = install_root / "venv"
    if (venv_path / "bin" / "python").exists():
        return venv_path

    uv = shutil.which("uv")
    if uv:
        run_command([uv, "venv", str(venv_path), "--python", HERMES_UV_PYTHON], timeout=timeout)
    else:
        python = ensure_python(python)
        run_command([python, "-m", "venv", str(venv_path)], timeout=timeout)
    return venv_path


def install_package(
    *,
    source_path: Path,
    venv_path: Path,
    extras: str,
    timeout: int,
) -> None:
    python = venv_path / "bin" / "python"
    if not python.exists():
        raise HermesProvisionError(f"virtualenv python missing at {python}")

    target = "-e"
    package_spec = "."
    extras = extras.strip()
    if extras:
        package_spec = f".[{extras}]"

    uv = shutil.which("uv")
    if uv:
        run_command([uv, "pip", "install", "--python", str(python), target, package_spec], cwd=source_path, timeout=timeout)
    else:
        run_command([str(python), "-m", "pip", "install", "--upgrade", "pip"], timeout=timeout)
        run_command([str(python), "-m", "pip", "install", target, package_spec], cwd=source_path, timeout=timeout)


def hermes_binary(venv_path: Path) -> Path:
    return venv_path / "bin" / "hermes"


def write_wrapper(*, install_root: Path, binary: Path) -> Path:
    wrapper_dir = install_root / "bin"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    wrapper = wrapper_dir / "hermes"
    wrapper.write_text(
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        f"exec {shlex.quote(str(binary))} \"$@\"\n",
        encoding="utf-8",
    )
    current_mode = wrapper.stat().st_mode
    wrapper.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return wrapper


def read_version(binary: Path, *, timeout: int) -> dict[str, Any]:
    if not binary.exists():
        return {"ok": False, "output": "", "error": "binary missing"}
    result = run_command([str(binary), "version"], timeout=timeout, check=False)
    output = sanitize_local_paths((result.stdout or result.stderr).strip())
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "output": output,
    }


def write_profile(profile_path: Path, profile: dict[str, Any]) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def relative_or_absolute(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def sanitize_local_paths(text: str) -> str:
    return text.replace(str(REPO_ROOT), "<repo-root>")


def build_profile(
    *,
    install_root: Path,
    source_path: Path,
    repo_url: str,
    commit: str,
    source_shape: dict[str, str],
    venv_path: Path | None,
    wrapper_path: Path | None,
    version_check: dict[str, Any] | None,
    install_deps: bool,
) -> dict[str, Any]:
    binary_path = hermes_binary(venv_path) if venv_path else None
    return {
        "schema": PROFILE_SCHEMA,
        "created_at": utc_now(),
        "upstream": {
            "repo_url": repo_url,
            "pinned_commit": commit,
            "checked_out_commit": git_head(source_path),
            "package_name": source_shape["package_name"],
            "package_version": source_shape["package_version"],
        },
        "local": {
            "install_root": relative_or_absolute(install_root),
            "source_path": relative_or_absolute(source_path),
            "venv_path": relative_or_absolute(venv_path) if venv_path else None,
            "binary_path": relative_or_absolute(binary_path) if binary_path else None,
            "wrapper_path": relative_or_absolute(wrapper_path) if wrapper_path else None,
        },
        "status": {
            "source_verified": git_head(source_path) == commit,
            "dependencies_installed": install_deps,
            "binary_present": bool(binary_path and binary_path.exists()),
            "version_check": version_check or {"ok": False, "output": "", "error": "not run"},
        },
        "authority": {
            "service_installed": False,
            "shell_startup_mutated": False,
            "secrets_loaded": False,
            "gateway_paired": False,
            "setup_wizard_ran": False,
            "external_actions": "blocked",
        },
    }


def provision_hermes(
    *,
    install_root: Path = DEFAULT_INSTALL_ROOT,
    repo_url: str = HERMES_REPO_URL,
    commit: str = HERMES_PINNED_COMMIT,
    source_repo: Path | None = None,
    python: str = sys.executable,
    extras: str = "cli",
    install_deps: bool = True,
    timeout: int = 900,
    profile_path: Path | None = None,
) -> dict[str, Any]:
    install_root = install_root.resolve()
    source_path = install_root / "source"
    profile_path = profile_path or DEFAULT_PROFILE_PATH

    clone_or_update_source(
        source_path=source_path,
        repo_url=repo_url,
        commit=commit,
        source_repo=source_repo,
        timeout=timeout,
    )
    source_shape = validate_source_shape(source_path)

    venv_path: Path | None = None
    wrapper_path: Path | None = None
    version_check: dict[str, Any] | None = None
    if install_deps:
        venv_path = create_venv(install_root=install_root, python=python, timeout=timeout)
        install_package(source_path=source_path, venv_path=venv_path, extras=extras, timeout=timeout)
        binary = hermes_binary(venv_path)
        wrapper_path = write_wrapper(install_root=install_root, binary=binary)
        version_check = read_version(wrapper_path, timeout=120)

    profile = build_profile(
        install_root=install_root,
        source_path=source_path,
        repo_url=repo_url,
        commit=commit,
        source_shape=source_shape,
        venv_path=venv_path,
        wrapper_path=wrapper_path,
        version_check=version_check,
        install_deps=install_deps,
    )
    write_profile(profile_path, profile)
    return profile


def check_profile(profile_path: Path) -> dict[str, Any]:
    if not profile_path.exists():
        raise HermesProvisionError(f"Hermes provision profile missing at {profile_path}")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if profile.get("schema") != PROFILE_SCHEMA:
        raise HermesProvisionError(f"profile schema must be {PROFILE_SCHEMA}")
    status = profile.get("status", {})
    if status.get("source_verified") is not True:
        raise HermesProvisionError("Hermes source is not verified in the provision profile")
    return profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-root", type=Path, default=DEFAULT_INSTALL_ROOT)
    parser.add_argument("--profile-out", type=Path, default=DEFAULT_PROFILE_PATH)
    parser.add_argument("--repo-url", default=HERMES_REPO_URL)
    parser.add_argument("--commit", default=HERMES_PINNED_COMMIT)
    parser.add_argument("--source-repo", type=Path, help="local source git repo for tests or mirrors")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--extras", default="cli", help="Hermes extras to install, default: cli")
    parser.add_argument("--no-install-deps", action="store_true", help="clone and verify source only")
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("WEAVE_HERMES_PROVISION_TIMEOUT", "900")))
    parser.add_argument("--check", action="store_true", help="validate the existing provision profile")
    args = parser.parse_args(argv)

    try:
        if args.check:
            profile = check_profile(args.profile_out)
            print(json.dumps(profile, indent=2, sort_keys=True))
            return 0
        profile = provision_hermes(
            install_root=args.install_root,
            repo_url=args.repo_url,
            commit=args.commit,
            source_repo=args.source_repo,
            python=args.python,
            extras=args.extras,
            install_deps=not args.no_install_deps,
            timeout=args.timeout,
            profile_path=args.profile_out,
        )
    except HermesProvisionError as exc:
        print(f"Hermes provision failed: {exc}", file=sys.stderr)
        return 1

    status = profile["status"]
    print("Hermes provision: ok")
    print(f"profile: {args.profile_out}")
    print(f"commit: {profile['upstream']['checked_out_commit']}")
    print(f"package: {profile['upstream']['package_name']} {profile['upstream']['package_version']}")
    print(f"dependencies_installed: {str(status['dependencies_installed']).lower()}")
    print(f"binary_present: {str(status['binary_present']).lower()}")
    print(f"service_installed: {str(profile['authority']['service_installed']).lower()}")
    print(f"secrets_loaded: {str(profile['authority']['secrets_loaded']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
