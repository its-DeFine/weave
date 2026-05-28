#!/usr/bin/env python3
"""Local runtime smoke test.

Prints the WEAVE lifecycle plus parallel growth loop, validates the company
package, and checks that the public-safe operator UI can be instantiated
locally. No network access. No secrets. Exits 0 on success.

Usage:
    python3 scripts/runtime_smoke.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
VALIDATOR = PACKAGE_ROOT / "scripts" / "validate_company_package.py"
OPERATOR_UI_SMOKE = REPO_ROOT / "scripts" / "operator_ui_smoke.py"
SETUP_RUNTIME = REPO_ROOT / "scripts" / "setup_runtime.py"

LIFECYCLE_STAGES = [
    "1. Intent",
    "2. Research",
    "3. Selection",
    "4. Plan",
    "5. Engineering",
    "6. QA",
    "7. KPI Setup",
    "8. Marketing",
]

GROWTH_LOOP = [
    "A. Iteration",
    "B. Analysis",
]


def print_lifecycle() -> None:
    print("WEAVE lifecycle stages:")
    for stage in LIFECYCLE_STAGES:
        print(f"  {stage}")
    print("Parallel growth loop:")
    for phase in GROWTH_LOOP:
        print(f"  {phase}")
    print()


def validate_package() -> int:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(PACKAGE_ROOT)],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def validate_operator_ui() -> int:
    result = subprocess.run(
        [sys.executable, str(OPERATOR_UI_SMOKE)],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def validate_runtime_setup() -> int:
    result = subprocess.run(
        [sys.executable, str(SETUP_RUNTIME), "--check"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    try:
        profile = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"runtime setup check returned invalid JSON: {exc}", file=sys.stderr)
        return 1

    package = profile.get("package", {})
    runtime = profile.get("runtime", {})
    if runtime.get("id") != package.get("default_runtime"):
        print("runtime setup check did not select the default runtime", file=sys.stderr)
        return 1
    if package.get("fallback_runtime") != "openclaw-solo":
        print("runtime setup check did not preserve OpenClaw fallback", file=sys.stderr)
        return 1
    if runtime.get("agent_slug") != "ceo-hermes":
        print("runtime setup check did not select the Hermes CEO agent", file=sys.stderr)
        return 1

    print("runtime setup check: ok")
    return 0


def main() -> int:
    print_lifecycle()
    rc = validate_package()
    if rc == 0:
        rc = validate_runtime_setup()
    if rc == 0:
        rc = validate_operator_ui()
    if rc == 0:
        print("smoke: ok")
    else:
        print("smoke: FAILED", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
