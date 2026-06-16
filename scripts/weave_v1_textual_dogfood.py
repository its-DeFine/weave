#!/usr/bin/env python3
"""Drive the WEAVE v1 Textual cockpit through QA and capture proof artifacts.

This proof uses the Textual app surface directly. It does not deploy WEAVE,
open provider credentials, send public messages, spend money, or mutate
external accounts. When Codex CLI is available, Engineering uses the real
Codex executor path through the backend facade.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import shutil
import sys
import time
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import weave_backend  # noqa: E402
import weave_prompt_library  # noqa: E402
import weave_runtime_slice as runtime  # noqa: E402
import weave_textual_app  # noqa: E402


APP_ID = "launch-studio-textual-v1"
APP_NAME = "Launch Studio Textual v1"
INTENT = (
    "Build a launch readiness cockpit for a founder to review lifecycle status, "
    "risks, QA, SEO, and launch boundaries before deciding whether to launch."
)
TARGET_USER = "Founder preparing a product launch."
OWNER_EXPERIENCE = "product and engineering operator"
COWORKER_STYLE = "direct, concise, proof-backed, explicit about assumptions and non-claims"

STAGE_BODIES = {
    "intent": (
        "Goal: build a launch readiness cockpit for a founder. Target user: founder preparing a launch. "
        "Core flows: inspect lifecycle state, inspect launch risks, inspect QA state, inspect SEO readiness, and see hard launch boundaries. "
        "Success metric: the owner can decide whether launch is ready from one local cockpit. "
        "Boundary: no credentials, deployment, public sends, paid spend, destructive operations, analytics beacons, or external account mutation."
    ),
    "research": (
        "Research plan: identify founder launch-readiness workflows, QA evidence patterns, SEO launch basics, risk registers, "
        "and safe local proof boundaries. Findings: a founder needs compact lifecycle status, visible blockers, source-backed claims, "
        "surface-adapted QA, and explicit non-claims before launch. Public-web research is represented as local proof notes in this TUI dogfood; "
        "live browsing is not claimed by this artifact."
    ),
    "selection": (
        "Selected option: a local static launch readiness cockpit with lifecycle rail, risk board, QA/SEO evidence panels, and launch boundary checklist. "
        "Rejected options: live deployment, analytics, provider credentials, paid ads, and public publishing during this proof. "
        "Reason: the selected path maximizes owner-reviewable proof while preserving local-only safety."
    ),
    "plan": (
        "Business plan: help a founder make a launch/no-launch decision with visible proof and risks. "
        "Engineering plan: create a local website workspace with semantic HTML, client-side state, no external calls, and source/executor manifests. "
        "QA plan: verify required files, semantic markup, SEO metadata, local state behavior, launch-boundary copy, source manifest, executor manifest, "
        "public-safe constraints, and owner-reviewable evidence."
    ),
    "qa": (
        "QA proof: validate the generated website source, executor/source manifests, SEO metadata, semantic HTML, local-only JavaScript, "
        "launch-boundary messaging, and WEAVE event/prompt/evaluation artifacts. QA is website-adapted plus operator-surface adapted; "
        "browser-only proof is not used to claim backend or CLI behavior."
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    weave_prompt_library.ensure_public_safe(path.name, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def capture_frame(app: Any, output_dir: Path, index: int, slug: str, title: str, actions: list[dict[str, Any]]) -> dict[str, Any]:
    """Export the actual Textual screen as SVG and record a public-safe frame."""

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{index:02d}-{slug}.svg"
    svg = app.export_screenshot(title=title)
    path.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n", encoding="utf-8")
    frame = {
        "index": index,
        "slug": slug,
        "title": title,
        "path": repo_relative(path),
        "view": getattr(app, "view", ""),
        "route": getattr(app, "route", ""),
        "activity_state": getattr(app, "activity", {}).get("state", ""),
        "action_count": len(actions),
    }
    weave_prompt_library.ensure_public_safe("textual frame", frame)
    return frame


def record_action(actions: list[dict[str, Any]], action: str, detail: str = "") -> None:
    actions.append({"at": utc_now(), "action": action, "detail": detail})


def set_composer(app: Any, text: str, actions: list[dict[str, Any]], detail: str) -> None:
    app.query_one("#composer").value = text
    record_action(actions, "composer.write", detail)


async def wait_for_idle(app: Any, pilot: Any, actions: list[dict[str, Any]], *, timeout: float = 900.0) -> None:
    started = time.time()
    while getattr(app, "activity", {}).get("state") == "running":
        if time.time() - started > timeout:
            raise TimeoutError(f"Timed out waiting for {getattr(app, 'route', 'unknown')} action to finish")
        await pilot.pause(0.25)
    record_action(actions, "wait.idle", f"{getattr(app, 'route', '')}:{getattr(app, 'activity', {}).get('state', '')}")


async def open_stage_route(app: Any, pilot: Any, stage: str, actions: list[dict[str, Any]]) -> None:
    """Navigate the lifecycle rail with keyboard focus and Enter like a user."""

    stage_list = app.query_one("#stage-list")
    stage_list.focus()
    target = app.stage_order.index(stage)
    current = stage_list.index or 0
    key = "down" if target >= current else "up"
    for _ in range(abs(target - current)):
        await pilot.press(key)
    await pilot.press("enter")
    await pilot.pause()
    record_action(actions, "rail.enter", stage)


BUTTON_KEYS = {
    "#create-app": "c",
    "#save-setup": "s",
    "#prepare-prompt": "p",
    "#run-executor": "x",
    "#submit-stage": "u",
    "#evaluate-stage": "e",
    "#approve-stage": "a",
    "#advance-stage": "n",
    "#record-feedback": "g",
}


async def click_button(app: Any, pilot: Any, selector: str, actions: list[dict[str, Any]], detail: str) -> None:
    key = BUTTON_KEYS.get(selector)
    if key:
        await pilot.press(key)
    else:
        await pilot.click(selector)
    await pilot.pause()
    record_action(actions, "button.key", f"{detail}:{key or selector}")


async def stage_roundtrip(app: Any, pilot: Any, stage: str, body: str, actions: list[dict[str, Any]]) -> None:
    """Use visible route navigation and buttons for one lifecycle stage."""

    await open_stage_route(app, pilot, stage, actions)
    set_composer(app, body, actions, f"{stage} owner input")
    await click_button(app, pilot, "#prepare-prompt", actions, f"{stage}:prepare_prompt")
    await click_button(app, pilot, "#submit-stage", actions, f"{stage}:submit_stage")
    await click_button(app, pilot, "#evaluate-stage", actions, f"{stage}:evaluate_stage")
    await click_button(app, pilot, "#approve-stage", actions, f"{stage}:approve_stage")


def artifact_counts(root: Path, app_id: str) -> dict[str, int]:
    app_root = runtime.app_root(root, app_id)
    return {
        "artifacts": len(runtime.list_artifacts(root, app_id)),
        "turns": len(runtime.read_conversation_turns(root, app_id)),
        "prompt_packets": len(list((app_root / "lifecycle").glob("*/artifacts/prompt-packets/*.json"))),
        "source_files": len([path for path in (app_root / "repo" / "primary").rglob("*") if path.is_file()])
        if (app_root / "repo" / "primary").exists()
        else 0,
    }


def collect_manifest_refs(root: Path, app_id: str) -> dict[str, str]:
    app_root = runtime.app_root(root, app_id)
    refs: dict[str, str] = {}
    for path in sorted((app_root / "lifecycle").glob("*/artifacts/**/*")):
        if not path.is_file():
            continue
        name = path.name
        if name in {"executor-manifest.json", "source-manifest.json"}:
            refs[name.replace(".json", "").replace("-", "_")] = runtime.relative(path, root)
    return refs


def scrub_non_reviewable_runtime_state(root: Path) -> list[str]:
    """Remove local runtime material that is useful to execution, not review.

    The runtime slice creates local service material for live local execution.
    The Textual dogfood does not need those values as evidence, and committed
    proof state must stay public-safe, so token and local source-map material is
    removed before QA gates and before the report points reviewers at the state
    tree.
    """

    removed: list[str] = []
    token_dir = root / "runtime" / "tokens"
    if token_dir.exists():
        for path in sorted(token_dir.rglob("*"), reverse=True):
            if path.is_file():
                removed.append(runtime.relative(path, root))
                path.unlink()
        for path in sorted(token_dir.rglob("*"), reverse=True):
            if path.is_dir():
                path.rmdir()
        token_dir.rmdir()
        removed.append("runtime/tokens/")
    source_map = root / "runtime" / "source-map.json"
    if source_map.exists():
        removed.append(runtime.relative(source_map, root))
        source_map.unlink()
    return removed


def write_playback_svg(output_dir: Path, frames: list[dict[str, Any]]) -> str:
    """Build a self-contained animated SVG from the Textual SVG frames."""

    if not frames:
        return ""
    path = output_dir / "weave-v1-textual-dogfood-recording.svg"
    duration = max(3, len(frames) * 2)
    images = []
    for position, frame in enumerate(frames):
        frame_path = REPO_ROOT / frame["path"]
        encoded = base64.b64encode(frame_path.read_bytes()).decode("ascii")
        begin = position * 2
        images.append(
            "\n".join(
                [
                    f'<image href="data:image/svg+xml;base64,{encoded}" x="0" y="0" width="1600" height="960" opacity="0">',
                    f'  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.04;0.96;1" begin="{begin}s" dur="2s" repeatCount="1" fill="remove" />',
                    "</image>",
                ]
            )
        )
    content = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="960" viewBox="0 0 1600 960">',
            '<rect width="1600" height="960" fill="#070b0f"/>',
            *images,
            f'<set attributeName="display" to="none" begin="{duration}s" />',
            "</svg>",
        ]
    )
    path.write_text(content, encoding="utf-8")
    return repo_relative(path)


async def run_textual_dogfood(args: argparse.Namespace) -> dict[str, Any]:
    if not weave_textual_app.textual_available():
        raise RuntimeError(weave_textual_app.missing_textual_message())

    if args.clean and args.state_root.exists():
        shutil.rmtree(args.state_root)
    if args.clean and args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    args.state_root.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    textual_args = Namespace(
        weave_root=args.state_root,
        app_id=APP_ID,
        app_name=APP_NAME,
        owner_experience=OWNER_EXPERIENCE,
        coworker_style=COWORKER_STYLE,
        intent=INTENT,
        target_user=TARGET_USER,
        codex_timeout=args.codex_timeout,
        run_engineering_gates=True,
    )
    actions: list[dict[str, Any]] = []
    frames: list[dict[str, Any]] = []
    app = weave_textual_app.build_app(textual_args)
    started = time.time()

    async with app.run_test(size=(160, 44)) as pilot:
        await pilot.pause()
        frames.append(capture_frame(app, args.output_dir, 1, "first-run", "WEAVE Textual - First Run", actions))

        await open_stage_route(app, pilot, "first_run", actions)
        frames.append(capture_frame(app, args.output_dir, 2, "first-run-entered", "WEAVE Textual - First Run Entered", actions))

        await click_button(app, pilot, "#create-app", actions, f"create app {APP_ID}")
        frames.append(capture_frame(app, args.output_dir, 3, "owner-profile", "WEAVE Textual - Owner Profile", actions))

        set_composer(app, INTENT, actions, "foundation intent")
        await click_button(app, pilot, "#save-setup", actions, "owner profile and foundation context")
        frames.append(capture_frame(app, args.output_dir, 4, "app-workspace", "WEAVE Textual - App Workspace", actions))

        for frame_index, stage in enumerate(("intent", "research", "selection", "plan"), 5):
            await stage_roundtrip(app, pilot, stage, STAGE_BODIES[stage], actions)
            frames.append(capture_frame(app, args.output_dir, frame_index, f"{stage}-approved", f"WEAVE Textual - {stage.title()} Approved", actions))
            await click_button(app, pilot, "#advance-stage", actions, f"{stage}:advance_stage")

        await pilot.pause()
        frames.append(capture_frame(app, args.output_dir, 9, "engineering-ready", "WEAVE Textual - Engineering Ready", actions))

        await open_stage_route(app, pilot, "engineering", actions)
        set_composer(app, INTENT, actions, "engineering owner build request")
        await click_button(app, pilot, "#prepare-prompt", actions, "engineering:prepare_prompt")
        await click_button(app, pilot, "#run-executor", actions, "engineering:run_codex")
        frames.append(capture_frame(app, args.output_dir, 10, "engineering-codex-running", "WEAVE Textual - Engineering Codex Running", actions))
        await wait_for_idle(app, pilot, actions, timeout=max(30, args.codex_timeout + 30))
        frames.append(capture_frame(app, args.output_dir, 11, "engineering-codex-result", "WEAVE Textual - Engineering Codex Result", actions))

        # Exercise file-specific feedback before approving Engineering.
        file_ref = f"apps/{APP_ID}/repo/primary/src/app.js"
        feedback_text = f"file:{file_ref}: Keep launch risks above secondary metrics in the review flow."
        set_composer(app, feedback_text, actions, "file-specific feedback")
        await click_button(app, pilot, "#record-feedback", actions, "engineering:file_feedback")
        await click_button(app, pilot, "#evaluate-stage", actions, "engineering:evaluate_stage")
        await click_button(app, pilot, "#approve-stage", actions, "engineering:approve_stage")
        frames.append(capture_frame(app, args.output_dir, 12, "engineering-approved", "WEAVE Textual - Engineering Approved", actions))

        await click_button(app, pilot, "#advance-stage", actions, "engineering:advance_stage")
        pre_qa_scrubbed_refs = scrub_non_reviewable_runtime_state(args.state_root)
        await stage_roundtrip(app, pilot, "qa", STAGE_BODIES["qa"], actions)
        frames.append(capture_frame(app, args.output_dir, 13, "qa-approved", "WEAVE Textual - QA Approved", actions))

        for offset, stage in enumerate(("deployment", "kpi", "marketing", "iteration", "analysis"), 14):
            await open_stage_route(app, pilot, stage, actions)
            frames.append(capture_frame(app, args.output_dir, offset, f"gated-{stage}", f"WEAVE Textual - {stage.title()} Gated Screen", actions))

    # Reopen the Textual app against the same state root to prove the operator
    # can resume at the QA state instead of only seeing a one-shot script run.
    resume_app = weave_textual_app.build_app(textual_args)
    async with resume_app.run_test(size=(160, 44)) as pilot:
        await pilot.pause()
        record_action(actions, "session.resume", "reopened Textual cockpit from saved state")
        frames.append(capture_frame(resume_app, args.output_dir, 19, "resume-qa", "WEAVE Textual - Resume At QA", actions))
        view_actions = [
            ("overview", resume_app.action_view_overview),
            ("stages", resume_app.action_view_stages),
            ("artifacts", resume_app.action_view_artifacts),
            ("files", resume_app.action_view_files),
            ("reviews", resume_app.action_view_reviews),
            ("help", resume_app.action_view_help),
            ("resume", resume_app.action_view_resume),
        ]
        for offset, (view, action) in enumerate(view_actions, 20):
            action()
            record_action(actions, "view.switch", view)
            await pilot.pause()
            frames.append(capture_frame(resume_app, args.output_dir, offset, f"view-{view}", f"WEAVE Textual - {view.title()} View", actions))

    scrubbed_refs = [*pre_qa_scrubbed_refs, *scrub_non_reviewable_runtime_state(args.state_root)]
    app_state = runtime.load_app(args.state_root, APP_ID)
    counts = artifact_counts(args.state_root, APP_ID)
    manifest_refs = collect_manifest_refs(args.state_root, APP_ID)
    playback_ref = write_playback_svg(args.output_dir, frames)
    required_views = list(weave_textual_app.TEXTUAL_VIEWS)
    captured_views = sorted({str(frame.get("view") or "") for frame in frames if frame.get("view")})
    required_routes = [
        "first_run",
        "owner_profile",
        "app",
        "intent",
        "research",
        "selection",
        "plan",
        "engineering",
        "qa",
        "deployment",
        "kpi",
        "marketing",
        "iteration",
        "analysis",
    ]
    captured_routes = sorted({str(frame.get("route") or "") for frame in frames if frame.get("route")})
    qa_approved = "qa" in app_state.get("approved_stages", [])
    all_views_captured = all(view in captured_views for view in required_views)
    all_routes_captured = all(route in captured_routes for route in required_routes)
    report = {
        "schema": "weave-v1-textual-dogfood/v1",
        "created_at": utc_now(),
        "duration_seconds": round(time.time() - started, 3),
        "passed": qa_approved and all_views_captured and all_routes_captured,
        "reason": (
            "completed_through_qa_all_views_and_routes_captured"
            if qa_approved and all_views_captured and all_routes_captured
            else (
                "missing_required_tui_routes"
                if qa_approved and all_views_captured
                else ("missing_required_tui_views" if qa_approved else "qa_not_approved")
            )
        ),
        "app": {
            "app_id": app_state["app_id"],
            "name": app_state["name"],
            "current_stage": app_state.get("current_stage"),
            "approved_stages": app_state.get("approved_stages", []),
        },
        "proof": {
            **counts,
            "frame_count": len(frames),
            "frames": frames,
            "required_views": required_views,
            "captured_views": captured_views,
            "all_views_captured": all_views_captured,
            "required_routes": required_routes,
            "captured_routes": captured_routes,
            "all_routes_captured": all_routes_captured,
            "screen_recording_ref": playback_ref,
            "state_root_ref": repo_relative(args.state_root),
            "executor_manifest_ref": manifest_refs.get("executor_manifest", ""),
            "source_manifest_ref": manifest_refs.get("source_manifest", ""),
            "external_effects_executed": [],
            "secret_value_printed": False,
            "scrubbed_non_reviewable_refs": scrubbed_refs,
            "used_textual_app": True,
            "used_codex_executor": bool(manifest_refs.get("executor_manifest")),
            "resume_stage": resume_app.projection.get("app", {}).get("current_stage", ""),
            "human_journey_actions": actions,
        },
        "non_claims": [
            "WEAVE itself was not deployed and does not need a URL",
            "no live Telegram/Hermes gateway proof",
            "no raw credentials captured",
            "no public sends",
            "no paid spend",
            "no market validation",
        ],
    }
    write_json(args.report_out, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Dogfood WEAVE Textual TUI through QA and capture proof.")
    parser.add_argument("--state-root", type=Path, default=REPO_ROOT / "docs" / "proof" / "weave-v1-textual-dogfood-state")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "docs" / "ux" / "weave-v1-textual-dogfood")
    parser.add_argument("--report-out", type=Path, default=REPO_ROOT / "docs" / "proof" / "weave-v1-textual-dogfood.json")
    parser.add_argument("--codex-timeout", type=int, default=600)
    parser.add_argument("--clean", action="store_true", help="remove previous dogfood state and captures before running")
    args = parser.parse_args()
    try:
        report = asyncio.run(run_textual_dogfood(args))
    except Exception as exc:  # noqa: BLE001
        failure = {
            "schema": "weave-v1-textual-dogfood/v1",
            "created_at": utc_now(),
            "passed": False,
            "reason": "exception",
            "error": str(exc),
            "non_claims": ["no completion claim was made"],
        }
        write_json(args.report_out, failure)
        print(f"weave v1 textual dogfood: fail ({args.report_out})", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1
    print(f"weave v1 textual dogfood: {'ok' if report.get('passed') else 'fail'} ({args.report_out})")
    if report.get("proof", {}).get("screen_recording_ref"):
        print(f"screen recording: {report['proof']['screen_recording_ref']}")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
