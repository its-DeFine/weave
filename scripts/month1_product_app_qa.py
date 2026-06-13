#!/usr/bin/env python3
"""QA the Month 1 proof web app and rehearse its WEAVE lifecycle.

This is local-only. It does not deploy, publish, send marketing, call payment
providers, or contact external networks.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.request import urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import weave_runtime_slice as runtime  # noqa: E402

DEFAULT_APP_DIR = REPO_ROOT / "apps" / "fableframe-studio"
DEFAULT_REPORT_DIR = Path.home() / "Documents" / "Codex" / "artifacts" / "weave-month1-product-qa"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: Any) -> None:
        return


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def fill(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\nStatus: complete\n\n{body}\n", encoding="utf-8")


def complete_foundation(root: Path, app_id: str) -> None:
    fill(root / "artifacts" / "general" / "soul.md", "Hermes Soul", "Hermes acts as a careful product operator.")
    fill(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile", "The owner wants concrete product evidence.")
    fill(root / "apps" / app_id / "context" / "app-context.md", "App Context", "FableFrame Studio is the Month 1 proof app.")
    fill(root / "apps" / app_id / "inventory" / "app-inventory.md", "App Inventory", "Static app source, Vercel config, QA script, and local proof.")
    fill(root / "apps" / app_id / "contract" / "gestaltian-contract.md", "Gestaltian Contract", "Move through lifecycle stages with evidence and gates.")


def write_stage_artifact(root: Path, app_id: str, stage_id: str, title: str, body: str) -> Path:
    stage = runtime.stage_by_id(stage_id)
    path = root / "apps" / app_id / "lifecycle" / stage.directory / "artifacts" / f"{stage_id}-fableframe.md"
    fill(path, title, body)
    return path


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return {
        "command": command,
        "cwd": rel(cwd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "passed": result.returncode == 0,
    }


def node_command(app_dir: Path, args: list[str]) -> dict[str, Any]:
    primary_command = ["node", *args]
    check = run_command(primary_command, app_dir)
    empty_abort = check["returncode"] in {-6, 134} and not check["stderr"]
    if check["passed"] or not empty_abort:
        return check

    fallback = run_command(["npm", "exec", "--", "node", *args], app_dir)
    fallback["fallback_for_empty_node_abort"] = True
    fallback["primary_command"] = primary_command
    fallback["primary_returncode"] = check["returncode"]
    return fallback


def node_syntax_check(app_dir: Path, source_path: str) -> dict[str, Any]:
    return node_command(app_dir, ["--check", source_path])


def assert_pass(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def required_files(app_dir: Path) -> list[Path]:
    return [
        app_dir / "index.html",
        app_dir / "src" / "app.js",
        app_dir / "src" / "story-engine.mjs",
        app_dir / "src" / "styles.css",
        app_dir / "public" / "config.json",
        app_dir / "vercel.json",
    ]


def static_checks(app_dir: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for path in required_files(app_dir):
        checks.append({"name": f"file exists: {rel(path)}", "passed": path.exists()})
        assert_pass(path.exists(), f"required file missing: {path}")
    html = (app_dir / "index.html").read_text(encoding="utf-8")
    checks.append({"name": "html mounts module app", "passed": 'type="module"' in html and "src/app.js" in html})
    assert_pass(checks[-1]["passed"], "index.html does not load module app")
    config = json.loads((app_dir / "public" / "config.json").read_text(encoding="utf-8"))
    checks.append({"name": "checkout disabled by default", "passed": config.get("checkoutUrl", "") == ""})
    assert_pass(checks[-1]["passed"], "checkout must be disabled by default")
    vercel = json.loads((app_dir / "vercel.json").read_text(encoding="utf-8"))
    checks.append({"name": "vercel config present", "passed": "rewrites" in vercel and "headers" in vercel})
    assert_pass(checks[-1]["passed"], "vercel config missing rewrites or headers")
    return checks


def node_checks(app_dir: Path) -> list[dict[str, Any]]:
    checks = [
        node_syntax_check(app_dir, "src/app.js"),
        node_syntax_check(app_dir, "src/story-engine.mjs"),
    ]
    engine_script = """
import { createStory, applyFeedback, exportStory, monetizationState } from './src/story-engine.mjs';
const story = createStory({
  title: 'QA Story',
  audience: 'reviewers',
  premise: 'a runtime creates a concrete app proof',
  tone: 'curious',
  style: 'arcade',
  sceneCount: 5,
  priceCents: 1200
});
if (story.scenes.length !== 5) throw new Error('scene count mismatch');
if (story.kpis.completionEstimate <= 0) throw new Error('missing completion KPI');
if (monetizationState({ checkoutUrl: '' }).enabled) throw new Error('empty checkout should be disabled');
if (!monetizationState({ checkoutUrl: 'https://example.com/pay', priceCents: 1200 }).enabled) throw new Error('https checkout should enable');
const revised = applyFeedback(story, { note: 'make the payment ask later' });
if (!revised.iteration || revised.kpis.conversionIntent <= story.kpis.conversionIntent) throw new Error('iteration did not improve conversion intent');
const exported = exportStory(revised);
if (exported.schema !== 'fableframe-export/v0.1') throw new Error('export schema mismatch');
console.log(JSON.stringify({
  scenes: story.scenes.length,
  completionEstimate: story.kpis.completionEstimate,
  revisedConversionIntent: revised.kpis.conversionIntent,
  checkoutDefault: monetizationState({ checkoutUrl: '' }).status
}));
"""
    checks.append(node_command(app_dir, ["--input-type=module", "-e", engine_script]))
    for check in checks:
        assert_pass(check["passed"], f"node check failed: {check}")
    return checks


def http_checks(app_dir: Path) -> tuple[list[dict[str, Any]], str]:
    handler = partial(QuietHandler, directory=str(app_dir))
    host = ".".join(["127", "0", "0", "1"])
    server = ThreadingHTTPServer((host, 0), handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{host}:{port}"
    checks: list[dict[str, Any]] = []
    try:
        for path in ["/", "/src/app.js", "/src/story-engine.mjs", "/src/styles.css", "/public/config.json"]:
            with urlopen(base_url + path, timeout=8) as response:
                body = response.read(400).decode("utf-8", "replace")
                passed = response.status == 200 and len(body) > 0
                checks.append({"name": f"http {path}", "status": response.status, "passed": passed})
                assert_pass(passed, f"HTTP check failed for {path}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    return checks, base_url


def record_stage_review_turn(root: Path, app_id: str, stage_id: str, artifact_path: Path, title: str) -> dict[str, Any]:
    stage_label = runtime.owner_stage_label(stage_id)
    artifact_ref = {"path": runtime.relative(artifact_path, root), "action": "created"}
    turn = runtime.new_conversation_turn(
        app_id,
        stage_id,
        {
            "role": "owner",
            "source": "qa_rehearsal",
            "text": f"Review the {stage_label} proof for the Month 1 product QA rehearsal.",
        },
        {
            "role": "hermes",
            "source": "qa_rehearsal",
            "text": f"{title} proof is ready for review and linked to its lifecycle artifact.",
        },
        channel="local-qa",
        created_by="execution-agent",
        agent_rationale={
            "summary": f"The {stage_label} stage has an owner-reviewable artifact and can be checked by deterministic gates.",
            "gate_questions": [f"Does the {stage_label} artifact satisfy the stage proof contract?"],
            "missing_information": [],
            "decision_basis": ["stage artifact exists", "foundation context exists", "local QA rehearsal captured this turn"],
            "chain_of_thought_captured": False,
        },
        gate_checks={
            "foundation_gate_passed": True,
            "stage_artifact_present": True,
            "owner_approval_required": True,
        },
        artifact_refs=[artifact_ref],
        state_transition={
            "from_stage": stage_id,
            "from_state": "collecting",
            "to_stage": stage_id,
            "to_state": "ready_for_review",
            "initiated_by": "local-qa",
            "reason": f"{stage_label} artifact was generated for deterministic lifecycle rehearsal.",
        },
        next_action=f"Approve {stage_label} if the linked artifact is acceptable.",
    )
    appended = runtime.append_conversation_turn(root, app_id, turn)
    evaluation = runtime.complete_evaluation_from_latest_artifact(
        root,
        app_id,
        stage_id,
        reviewer="month1-product-qa-local-evaluator",
        run_gates=True,
    )
    assert_pass(
        evaluation["result"].get("decision") in runtime.EVALUATION_PASS_DECISIONS,
        f"evaluation failed for {stage_id}: {evaluation}",
    )
    return appended


def approve_and_advance(root: Path, app_id: str, stage_id: str, *, defer_capability: bool = False) -> dict[str, Any]:
    approval = runtime.approve_stage(root, app_id, stage_id, defer_capability=defer_capability)
    assert_pass(approval["approved"], f"approval failed for {stage_id}: {approval}")
    advanced = runtime.advance_stage(root, app_id)
    return {"approval": approval["stage"], "advanced_to": advanced.get("stage"), "advanced": advanced.get("advanced")}


def lifecycle_rehearsal(app_dir: Path, qa_summary: dict[str, Any]) -> dict[str, Any]:
    app_id = "fableframe-studio"
    mocked_owner_replies = [
        "I want a concrete web app proof, not only runtime docs.",
        "Use a visual-novel app because it is simple enough to QA and expressive enough to inspect.",
        "Do not take real payments or publish marketing without approval.",
    ]
    mocked_feedback = "the first scene needs a clearer reason to pay"
    with tempfile.TemporaryDirectory(prefix="weave-fableframe-lifecycle-") as tmpdir:
        root = Path(tmpdir) / "weave-root"
        runtime.setup_weave_root(root)
        runtime.create_app(root, app_id, "FableFrame Studio")
        complete_foundation(root, app_id)

        completed: list[dict[str, Any]] = []
        stage_artifacts = {
            "intent": ("Intent", "Owner asks for a real app proof with mocked user replies and lifecycle evidence."),
            "research": ("Research", "Static web app plus Vercel config is the fastest reviewable path. Live deploy remains gated."),
            "selection": ("Selection", "FableFrame Studio selected as the compact visual-novel proof app."),
            "plan": ("Plan", "Build static app, QA locally, prepare Vercel, keep checkout disabled until configured."),
            "engineering": ("Engineering", f"Implemented source under {rel(app_dir)} with deterministic story engine and canvas UI."),
            "qa": ("QA", f"Local QA passed with {qa_summary['check_count']} deterministic checks."),
            "kpi": ("KPI Setup", "KPI estimates are generated locally: completion, share intent, conversion intent."),
            "marketing": ("Marketing", "Marketing is emulated as draft positioning only; no public send is performed."),
            "iteration": ("Iteration", f"Mocked feedback applied: {mocked_feedback}."),
        }
        for stage_id, (title, body) in stage_artifacts.items():
            artifact_path = write_stage_artifact(root, app_id, stage_id, title, body)
            if stage_id == "marketing":
                app = runtime.load_app(root, app_id)
                app.setdefault("credential_requirements", []).append(
                    {
                        "id": "distribution-account",
                        "label": "Distribution account",
                        "required": True,
                        "status": "missing",
                    }
                )
                runtime.write_app(root, app)
                record_stage_review_turn(root, app_id, stage_id, artifact_path, title)
                completed.append(approve_and_advance(root, app_id, stage_id, defer_capability=True))
            elif stage_id == "iteration":
                record_stage_review_turn(root, app_id, stage_id, artifact_path, title)
                approval = runtime.approve_stage(root, app_id, stage_id)
                assert_pass(approval["approved"], "iteration approval failed")
                advanced = runtime.advance_stage(root, app_id)
                assert_pass(advanced["advanced"], "advance into analysis failed")
                completed.append({"approval": approval["stage"], "advanced_to": advanced.get("stage"), "advanced": True})
            else:
                record_stage_review_turn(root, app_id, stage_id, artifact_path, title)
                completed.append(approve_and_advance(root, app_id, stage_id))

        state = runtime.app_state(root, app_id)
        status = runtime.dispatch_telegram_command(root, f"/status {app_id}")
        return {
            "schema": "weave-month1-product-lifecycle/v0.1",
            "mocked_owner_replies": mocked_owner_replies,
            "mocked_feedback": mocked_feedback,
            "completed_stages": [item["approval"] for item in completed],
            "final_stage": state["stage_status"]["stage"],
            "final_stage_state": state["stage_status"]["stage_state"],
            "approved_stages": state["app"].get("approved_stages", []),
            "stage_gate_missing": state["stage_status"]["stage_gate_missing"],
            "telegram_status_excerpt": "\n".join(status["text"].splitlines()[:18]),
        }


def write_report(report: dict[str, Any], path: Path | None) -> Path:
    if path is None:
        DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = DEFAULT_REPORT_DIR / f"fableframe-product-qa-{stamp}.json"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run(app_dir: Path) -> dict[str, Any]:
    app_dir = app_dir.resolve()
    static = static_checks(app_dir)
    node = node_checks(app_dir)
    http, local_url = http_checks(app_dir)
    qa_summary = {
        "check_count": len(static) + len(node) + len(http),
        "static_checks": static,
        "node_checks": node,
        "http_checks": http,
    }
    lifecycle = lifecycle_rehearsal(app_dir, qa_summary)
    return {
        "schema": "weave-month1-product-qa/v0.1",
        "created_at": utc_now(),
        "passed": True,
        "app": {
            "name": "FableFrame Studio",
            "source": rel(app_dir),
            "local_preview_url": local_url,
            "vercel_ready": True,
            "vercel_url": "",
            "vercel_deploy_status": "not_deployed_owner_approval_required",
        },
        "monetization": {
            "default_status": "checkout_not_configured",
            "can_be_configured": True,
            "live_payment_status": "not_enabled_owner_approval_required",
        },
        "qa": qa_summary,
        "lifecycle": lifecycle,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="QA the Month 1 product proof app.")
    parser.add_argument("--app-dir", type=Path, default=DEFAULT_APP_DIR)
    parser.add_argument("--report-out", type=Path, default=None)
    args = parser.parse_args()
    started = time.time()
    try:
        report = run(args.app_dir)
    except Exception as exc:  # noqa: BLE001
        failure = {
            "schema": "weave-month1-product-qa/v0.1",
            "created_at": utc_now(),
            "passed": False,
            "error": str(exc),
        }
        path = write_report(failure, args.report_out)
        print(f"month1 product app qa: fail ({path})")
        return 1
    report["duration_seconds"] = round(time.time() - started, 3)
    path = write_report(report, args.report_out)
    print(f"month1 product app qa: ok ({path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
