#!/usr/bin/env python3
"""Dogfood the WEAVE v1 backend lifecycle through QA.

This is a local-only proof. It may invoke the local Codex CLI for the
Engineering stage, but it does not deploy, capture credentials, send public
messages, spend money, or mutate external accounts.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import weave_backend  # noqa: E402
import weave_runtime_slice as runtime  # noqa: E402


APP_ID = "launch-studio-v1-dogfood"
APP_NAME = "Launch Studio v1 Dogfood"
INTENT = "Build a launch readiness cockpit for a founder to review lifecycle status, risks, QA, SEO, and launch boundaries."
TARGET_USER = "Founder preparing a product launch."


STAGE_BODIES = {
    "intent": (
        "Goal: build a launch readiness cockpit. Target user: founder. "
        "Success metric: the owner can inspect lifecycle status, risks, QA state, SEO readiness, and launch boundaries before launch. "
        "Approval boundary: no credentials, deployment, public sends, paid spend, or destructive operations."
    ),
    "research": (
        "Research plan and findings: inspect lifecycle cockpit patterns, founder launch-review workflows, QA proof expectations, SEO basics, "
        "and regulated launch-boundary risks. Facts, assumptions, and opinions are separated; source refs are represented as local proof placeholders "
        "because this dogfood is local-only."
    ),
    "selection": (
        "Selected option: a local static cockpit first, with lifecycle rail, risk board, QA/SEO evidence, and launch-boundary checklist. "
        "Rejected options: live deployment, account integrations, analytics, and paid marketing during this proof."
    ),
    "plan": (
        "Business plan: help a founder decide whether a launch is ready. Engineering plan: generate a local app workspace with semantic HTML, "
        "client-side state, source manifest, executor manifest, and no external effects. QA plan: verify local files, static source safety, "
        "public-safe repository checks, and owner-reviewable proof artifacts."
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def dispatch(root: Path, command: str, payload: dict[str, Any] | None = None, *, allow_fail: bool = False) -> dict[str, Any]:
    result = weave_backend.dispatch(root, command, app_id=APP_ID, app_name=APP_NAME, payload=payload or {})
    if not allow_fail and not result.get("ok"):
        raise AssertionError(f"{command} failed: {json.dumps(result, sort_keys=True)}")
    return result


def complete_stage(root: Path, stage: str, body: str, *, run_gates: bool = False) -> dict[str, Any]:
    dispatch(root, "prompt.prepare", {"stage": stage, "substage": "start", "owner_message": body})
    submit = dispatch(
        root,
        "stage.submit",
        {
            "stage": stage,
            "owner_text": body,
            "agent_text": f"{stage.title()} proof is ready for evaluation and owner review.",
            "artifact_body": body,
            "artifact_name": f"{stage}-v1-dogfood-proof",
        },
    )
    evaluate = dispatch(root, "stage.evaluate", {"stage": stage, "run_gates": run_gates})
    approve = dispatch(root, "stage.approve", {"stage": stage, "note": f"Approved {stage} during v1 dogfood."})
    return {"submit": submit, "evaluate": evaluate, "approve": approve}


def run(timeout_seconds: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="weave-v1-backend-dogfood-") as tmpdir:
        root = Path(tmpdir) / "weave-state"
        dispatch(root, "workspace.create_app", {})
        dispatch(
            root,
            "foundation.save",
            {
                "owner_experience": "product/engineering operator",
                "coworker_style": "direct, concise, proof-backed, explicit about non-claims",
                "intent": INTENT,
                "target_user": TARGET_USER,
            },
        )

        stage_results: dict[str, Any] = {}
        for stage in ("intent", "research", "selection", "plan"):
            stage_results[stage] = complete_stage(root, stage, STAGE_BODIES[stage])
            dispatch(root, "stage.advance", {"note": f"Advance after {stage} dogfood approval."})

        executor = dispatch(
            root,
            "executor.run",
            {"executor": "codex", "owner_message": INTENT, "timeout_seconds": timeout_seconds},
            allow_fail=True,
        )
        if not executor.get("ok"):
            return build_report(root, executor, stage_results, passed=False, reason="codex_executor_unavailable_or_failed")

        engineering_eval = dispatch(root, "stage.evaluate", {"stage": "engineering", "run_gates": True})
        engineering_approve = dispatch(root, "stage.approve", {"stage": "engineering", "note": "Approved Codex engineering output during v1 dogfood."})
        stage_results["engineering"] = {"executor": executor, "evaluate": engineering_eval, "approve": engineering_approve}
        dispatch(root, "stage.advance", {"note": "Advance to QA after engineering approval."})

        qa_body = (
            "QA proof: Engineering produced local source and executor/source manifests. "
            "QA validates local-only boundaries, repository safety gates, package validation, runtime smoke, and owner-reviewable evidence. "
            "Remaining non-claims: no live deployment, no real users, no analytics, no public sends."
        )
        stage_results["qa"] = complete_stage(root, "qa", qa_body, run_gates=True)
        return build_report(root, executor, stage_results, passed=True, reason="completed_through_qa")


def build_report(root: Path, executor: dict[str, Any], stage_results: dict[str, Any], *, passed: bool, reason: str) -> dict[str, Any]:
    app = runtime.load_app(root, APP_ID)
    artifacts = runtime.list_artifacts(root, APP_ID)
    turns = runtime.read_conversation_turns(root, APP_ID)
    prompt_packets = sorted((runtime.app_root(root, APP_ID) / "lifecycle").glob("*/artifacts/prompt-packets/*.json"))
    executor_manifest_ref = ""
    source_manifest_ref = ""
    for ref in executor.get("artifacts_written", []):
        if str(ref).endswith("executor-manifest.json"):
            executor_manifest_ref = str(ref)
        if str(ref).endswith("source-manifest.json"):
            source_manifest_ref = str(ref)
    return {
        "schema": "weave-v1-backend-dogfood/v0.1",
        "created_at": utc_now(),
        "passed": passed,
        "reason": reason,
        "app": {
            "app_id": app["app_id"],
            "name": app["name"],
            "current_stage": app.get("current_stage"),
            "stage_state": app.get("stage_state"),
            "approved_stages": app.get("approved_stages", []),
        },
        "proof": {
            "artifact_count": len(artifacts),
            "conversation_turn_count": len(turns),
            "prompt_packet_count": len(prompt_packets),
            "prompt_packet_refs": [runtime.relative(path, root) for path in prompt_packets],
            "executor_manifest_ref": executor_manifest_ref,
            "source_manifest_ref": source_manifest_ref,
            "external_effects_executed": [],
            "secret_value_printed": False,
        },
        "executor": {
            "ok": bool(executor.get("ok")),
            "blocked_by": executor.get("blocked_by", []),
            "artifacts_written": executor.get("artifacts_written", []),
        },
        "stage_results": {
            stage: {
                key: {
                    "ok": value.get("ok"),
                    "message": value.get("message"),
                    "blocked_by": value.get("blocked_by", []),
                    "artifacts_written": value.get("artifacts_written", []),
                }
                for key, value in result.items()
                if isinstance(value, dict)
            }
            for stage, result in stage_results.items()
        },
        "non_claims": [
            "not deployed",
            "not live Telegram/Hermes gateway proof",
            "no raw credentials captured",
            "no public sends",
            "no paid spend",
            "no market validation",
        ],
    }


def write_report(report: dict[str, Any], report_out: Path) -> None:
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WEAVE v1 backend dogfood through QA.")
    parser.add_argument("--report-out", type=Path, default=Path("/tmp/weave-v1-backend-dogfood.json"))
    parser.add_argument("--codex-timeout", type=int, default=600)
    args = parser.parse_args()
    started = time.time()
    try:
        report = run(args.codex_timeout)
    except Exception as exc:  # noqa: BLE001
        report = {
            "schema": "weave-v1-backend-dogfood/v0.1",
            "created_at": utc_now(),
            "passed": False,
            "reason": "exception",
            "error": str(exc),
        }
    report["duration_seconds"] = round(time.time() - started, 3)
    write_report(report, args.report_out)
    print(f"weave v1 backend dogfood: {'ok' if report.get('passed') else 'fail'} ({args.report_out})")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
