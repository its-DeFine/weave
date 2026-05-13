#!/usr/bin/env python3
"""Validate the public-safe WEAVE operator UI files.

This smoke is filesystem-only. It does not start a browser or make network
calls; it verifies that the UI can load its sample runtime data and that the
sample preserves the public runtime boundaries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = REPO_ROOT / "operator-ui"
REQUIRED_FILES = [
    UI_ROOT / "index.html",
    UI_ROOT / "styles.css",
    UI_ROOT / "app.js",
    UI_ROOT / "sample-runtime.json",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    data = json.loads((UI_ROOT / "sample-runtime.json").read_text(encoding="utf-8"))
    runtime = data.get("runtime", {})
    apps = data.get("apps", [])
    if runtime.get("name") != "OpenClaw solo":
        print("operator UI sample must identify OpenClaw solo runtime", file=sys.stderr)
        return 1
    if runtime.get("releaseVersion") != "2026.05.13":
        print("operator UI sample must identify release version 2026.05.13", file=sys.stderr)
        return 1
    if runtime.get("externalRuntimeBoundary") != "public-safe dry-run":
        print("operator UI sample must declare the public runtime boundary", file=sys.stderr)
        return 1
    if not apps:
        print("operator UI sample must include at least one app", file=sys.stderr)
        return 1

    app = apps[0]
    stages = [stage.get("id") for stage in app.get("stages", [])]
    expected = ["intent", "research", "selection", "plan", "engineering", "qa", "kpi", "marketing", "iteration"]
    if stages != expected:
        print(f"operator UI lifecycle stages mismatch: {stages}", file=sys.stderr)
        return 1
    if app.get("currentStage") != "marketing":
        print("operator UI sample should show marketing as the current blocked stage", file=sys.stderr)
        return 1
    if "approval" not in app.get("blocker", {}).get("title", "").lower():
        print("operator UI sample should explain the marketing approval gate", file=sys.stderr)
        return 1

    print("operator-ui smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
