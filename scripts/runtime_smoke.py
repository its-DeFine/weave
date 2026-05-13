#!/usr/bin/env python3
"""Local runtime smoke test.

Prints the 9 WEAVE lifecycle stages, validates the company package, and checks
that the public-safe operator UI can be instantiated locally. No network access.
No secrets. Exits 0 on success.

Usage:
    python3 scripts/runtime_smoke.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
VALIDATOR = PACKAGE_ROOT / "scripts" / "validate_company_package.py"
OPERATOR_UI_SMOKE = REPO_ROOT / "scripts" / "operator_ui_smoke.py"

LIFECYCLE_STAGES = [
    "1. Intent",
    "2. Research",
    "3. Selection",
    "4. Plan",
    "5. Engineering",
    "6. QA",
    "7. KPI Setup",
    "8. Marketing",
    "9. Iteration",
]


def print_lifecycle() -> None:
    print("WEAVE lifecycle stages:")
    for stage in LIFECYCLE_STAGES:
        print(f"  {stage}")
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


def main() -> int:
    print_lifecycle()
    rc = validate_package()
    if rc == 0:
        rc = validate_operator_ui()
    if rc == 0:
        print("smoke: ok")
    else:
        print("smoke: FAILED", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
