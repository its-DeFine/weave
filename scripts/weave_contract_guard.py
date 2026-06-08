#!/usr/bin/env python3
"""Guard the public Hermes Gestalt Runtime Pack claim."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import weave_hermes_gestalt_pack as gestalt_pack


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-runtime-evidence", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    try:
        gestalt_pack.validate_pack()
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))

    if args.require_runtime_evidence:
        try:
            gestalt_pack.read_proof()
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("contract guard: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
