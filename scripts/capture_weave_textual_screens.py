#!/usr/bin/env python3
"""Capture reviewable SVG screenshots of the WEAVE Textual cockpit.

The script is local-only. It creates a temporary WEAVE state root, drives the
Textual app through the first stage lifecycle, and writes SVG captures that can
be attached to UX review or PR proof.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import weave_textual_app  # noqa: E402


def write_svg(path: Path, svg: str) -> None:
    path.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n", encoding="utf-8")


async def capture(output_dir: Path) -> list[Path]:
    if not weave_textual_app.textual_available():
        raise RuntimeError(weave_textual_app.missing_textual_message())

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="weave-textual-capture-") as tmpdir:
        args = Namespace(
            weave_root=Path(tmpdir) / "weave-state",
            app_id="launch-studio",
            app_name="Launch Studio",
            owner_experience="operator with product and engineering context",
            coworker_style="direct, proof-backed, concise, no overclaiming",
            intent="Build a launch readiness cockpit for a founder to review lifecycle status, risks, QA, SEO, and launch boundaries.",
            target_user="founder",
        )
        app = weave_textual_app.build_app(args)
        async with app.run_test(size=(150, 42)) as pilot:
            await pilot.pause()
            first = output_dir / "01-first-run.svg"
            write_svg(first, app.export_screenshot(title="WEAVE v1 Textual Cockpit - First Run"))
            written.append(first)

            app.action_create_app()
            await pilot.pause()
            owner = output_dir / "02-owner-profile.svg"
            write_svg(owner, app.export_screenshot(title="WEAVE v1 Textual Cockpit - Owner Profile"))
            written.append(owner)

            app.action_save_setup()
            await pilot.pause()
            workspace = output_dir / "03-app-workspace.svg"
            write_svg(workspace, app.export_screenshot(title="WEAVE v1 Textual Cockpit - App Workspace"))
            written.append(workspace)

            app.activate_route("intent")
            app.action_prepare_prompt()
            await pilot.pause()
            intent = output_dir / "04-intent-prompt-ready.svg"
            write_svg(intent, app.export_screenshot(title="WEAVE v1 Textual Cockpit - Intent Prompt Ready"))
            written.append(intent)

            app.query_one("#composer").value = (
                "Goal: launch readiness cockpit. Target user: founder. "
                "Success metric: the owner can inspect lifecycle risks before launch. "
                "Boundary: no credentials, deployment, public sends, or paid spend."
            )
            app.action_submit_stage()
            app.action_evaluate_stage()
            app.action_approve_stage()
            app.action_advance_stage()
            await pilot.pause()
            research = output_dir / "05-research-active.svg"
            write_svg(research, app.export_screenshot(title="WEAVE v1 Textual Cockpit - Research Active"))
            written.append(research)

            for index, stage in enumerate(("selection", "plan", "engineering", "qa", "deployment", "kpi", "marketing", "iteration", "analysis"), 6):
                app.activate_route(stage)
                await pilot.pause()
                path = output_dir / f"{index:02d}-{stage}.svg"
                write_svg(path, app.export_screenshot(title=f"WEAVE v1 Textual Cockpit - {stage.title()}"))
                written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture WEAVE Textual cockpit SVG proof screens.")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "docs" / "ux" / "weave-v1-textual-proof")
    args = parser.parse_args()
    try:
        written = asyncio.run(capture(args.output_dir))
    except Exception as exc:  # noqa: BLE001
        print(f"textual capture failed: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
