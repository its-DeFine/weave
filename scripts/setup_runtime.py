#!/usr/bin/env python3
"""Set up a local WEAVE runtime profile.

This command is public-safe by construction: it reads package metadata, selects
the default runtime, checks whether the runtime executable is already present,
and writes a local ignored profile under runs/. It does not download binaries,
install services, read env files, or write secrets.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
DEFAULT_PROFILE_PATH = REPO_ROOT / "runs" / "runtime-profile.json"

RUNTIME_BINARIES = {
    "hermes-default": ["hermes", "hermes-agent", "nous-hermes"],
    "openclaw-solo": ["openclaw"],
}

RUNTIME_AGENT = {
    "hermes-default": "ceo-hermes",
    "openclaw-solo": "ceo-openclaw",
}


class RuntimeSetupError(Exception):
    pass


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise RuntimeSetupError(f"{path}: missing frontmatter")
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("- ") or line.startswith("  "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def find_runtime_binary(runtime: str, explicit_binary: str | None = None) -> dict[str, str | bool | None]:
    candidates = [explicit_binary] if explicit_binary else RUNTIME_BINARIES.get(runtime, [])
    for candidate in candidates:
        if not candidate:
            continue
        path = shutil.which(candidate)
        if path:
            return {"found": True, "name": candidate, "path": path}
    return {"found": False, "name": candidates[0] if candidates else None, "path": None}


def runtime_profile(runtime: str, runtime_binary: str | None = None) -> dict[str, object]:
    company = parse_frontmatter(PACKAGE_ROOT / "COMPANY.md")
    default_runtime = company.get("runtime")
    fallback_runtime = company.get("runtimeFallback")
    if runtime not in {default_runtime, fallback_runtime}:
        raise RuntimeSetupError(
            f"runtime must be {default_runtime} or fallback {fallback_runtime}; got {runtime}"
        )

    agent_slug = RUNTIME_AGENT[runtime]
    agent_path = PACKAGE_ROOT / "agents" / agent_slug / "AGENTS.md"
    agent = parse_frontmatter(agent_path)
    binary = find_runtime_binary(runtime, runtime_binary)
    is_default = runtime == default_runtime

    return {
        "schema": "weave-runtime-profile/v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "package": {
            "slug": company.get("slug"),
            "version": company.get("version"),
            "default_runtime": default_runtime,
            "fallback_runtime": fallback_runtime,
        },
        "runtime": {
            "id": runtime,
            "is_default": is_default,
            "agent_slug": agent_slug,
            "agent_name": agent.get("name"),
            "adapter_type": agent.get("adapterType"),
            "agent_contract": str(agent_path.relative_to(REPO_ROOT)),
            "binary": binary,
        },
        "authority": {
            "public_safe": True,
            "network_install_performed": False,
            "service_installed": False,
            "secrets_loaded": False,
            "external_actions": "blocked",
            "approval_gates": [
                "runtime pairing",
                "gateway pairing",
                "autostart or service enablement",
                "production deploys",
                "credential changes",
                "paid jobs or metered external API calls",
                "public posts or external sends",
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Set up a local WEAVE runtime profile.")
    parser.add_argument(
        "--runtime",
        choices=sorted(RUNTIME_AGENT),
        default=None,
        help="runtime to select; defaults to COMPANY.md runtime",
    )
    parser.add_argument("--runtime-binary", help="explicit runtime executable to check")
    parser.add_argument(
        "--profile-out",
        type=Path,
        default=DEFAULT_PROFILE_PATH,
        help="local profile path to write",
    )
    parser.add_argument(
        "--require-runtime-binary",
        action="store_true",
        help="fail when the selected runtime executable is not on PATH",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate setup inputs and print the profile without writing it",
    )
    args = parser.parse_args(argv)

    try:
        company = parse_frontmatter(PACKAGE_ROOT / "COMPANY.md")
        runtime = args.runtime or company["runtime"]
        profile = runtime_profile(runtime, args.runtime_binary)
        if args.require_runtime_binary and not profile["runtime"]["binary"]["found"]:
            raise RuntimeSetupError(f"{runtime} binary was not found on PATH")
        if args.check:
            print(json.dumps(profile, indent=2, sort_keys=True))
            return 0
        args.profile_out.parent.mkdir(parents=True, exist_ok=True)
        args.profile_out.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except RuntimeSetupError as exc:
        print(f"runtime setup failed: {exc}", file=sys.stderr)
        return 1

    status = "ready" if profile["runtime"]["binary"]["found"] else "profile_written_runtime_binary_missing"
    print(f"runtime setup: {status}")
    print(f"profile: {args.profile_out}")
    print(f"runtime: {profile['runtime']['id']}")
    print(f"agent: {profile['runtime']['agent_slug']}")
    print("network_install_performed: false")
    print("service_installed: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
