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

    index = (UI_ROOT / "index.html").read_text(encoding="utf-8")
    app_js = (UI_ROOT / "app.js").read_text(encoding="utf-8")
    for marker in (
        "data-create-form",
        "data-stage-track",
        "data-iteration-loop",
        "data-work-card=\"plan\"",
        "data-work-card=\"review\"",
        "data-work-card=\"execute\"",
        "data-evidence-list",
        "data-decision-list",
        "data-kpi-list",
        "data-command-list",
        "data-chat-log",
        "data-command-preview",
    ):
        if marker not in index:
            print(f"operator UI missing marker: {marker}", file=sys.stderr)
            return 1
    if "weave-agent-command-draft/v0.1" not in app_js:
        print("operator UI app must draft runtime command records", file=sys.stderr)
        return 1

    data = json.loads((UI_ROOT / "sample-runtime.json").read_text(encoding="utf-8"))
    runtime = data.get("runtime", {})
    apps = data.get("apps", [])
    if data.get("schema") != "weave-operator-ui-sample/v0.2":
        print("operator UI sample must use schema weave-operator-ui-sample/v0.2", file=sys.stderr)
        return 1
    if runtime.get("name") != "Hermes default":
        print("operator UI sample must identify Hermes default runtime", file=sys.stderr)
        return 1
    if runtime.get("releaseVersion") != "2026.05.13-console":
        print("operator UI sample must identify release version 2026.05.13-console", file=sys.stderr)
        return 1
    if runtime.get("externalRuntimeBoundary") != "public-safe dry-run":
        print("operator UI sample must declare the public runtime boundary", file=sys.stderr)
        return 1
    if len(apps) < 3:
        print("operator UI sample must include at least three app examples", file=sys.stderr)
        return 1

    app = apps[0]
    stages = [stage.get("id") for stage in app.get("stages", [])]
    expected = ["intent", "research", "selection", "plan", "engineering", "qa", "kpi", "marketing"]
    if stages != expected:
        print(f"operator UI lifecycle stages mismatch: {stages}", file=sys.stderr)
        return 1
    loop = [phase.get("id") for phase in app.get("iterationLoop", [])]
    if loop != ["iteration", "analysis"]:
        print(f"operator UI iteration loop mismatch: {loop}", file=sys.stderr)
        return 1
    if app.get("currentStage") != "marketing":
        print("operator UI sample should show marketing as the current blocked stage", file=sys.stderr)
        return 1
    if "parallel" not in app.get("summary", "").lower():
        print("operator UI sample should explain the parallel marketing iteration loop", file=sys.stderr)
        return 1
    if "approval" not in app.get("blocker", {}).get("title", "").lower():
        print("operator UI sample should explain the marketing approval gate", file=sys.stderr)
        return 1
    for key in ("workCards", "evidence", "decisions", "kpis", "commands", "chat"):
        if not app.get(key):
            print(f"operator UI sample app must include {key}", file=sys.stderr)
            return 1
    if {card.get("id") for card in app.get("workCards", [])} != {"plan", "review", "execute"}:
        print("operator UI sample must include plan/review/execute cards", file=sys.stderr)
        return 1

    print("operator-ui smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
