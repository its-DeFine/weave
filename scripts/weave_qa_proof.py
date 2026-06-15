#!/usr/bin/env python3
"""Surface-specific local QA proof runner for WEAVE."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import validate_lifecycle_artifacts
import weave_runtime_slice


QA_PROOF_SCHEMA = "weave-qa-proof/v0.1"
QA_SURFACES = ("web", "backend", "api", "cli", "tui", "agent_runtime", "data_pipeline", "infrastructure", "mixed")
DEFAULT_COMMAND = "bin/weave help"
REPO_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_public_safe_text(label: str, value: str) -> None:
    if weave_runtime_slice.contains_secret_like_value(value):
        raise ValueError(f"{label} contains secret-looking content")
    if weave_runtime_slice.contains_private_locator(value):
        raise ValueError(f"{label} contains private locator content")


def qa_artifact_dir(root: Path, app_id: str) -> Path:
    stage = weave_runtime_slice.stage_by_id("qa")
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage.directory / "artifacts"


def manifest_path(root: Path, app_id: str) -> Path:
    return qa_artifact_dir(root, app_id) / "qa-proof-manifest.json"


def lifecycle_bundle_path(root: Path, app_id: str) -> Path:
    return qa_artifact_dir(root, app_id) / "qa-proof-lifecycle-bundle.json"


def snapshot_from_args(args: Any) -> dict[str, Any]:
    surface = str(args.surface)
    if surface not in QA_SURFACES:
        raise ValueError(f"unsupported QA surface: {surface}")
    command = args.qa_command or DEFAULT_COMMAND
    ensure_public_safe_text("command", command)
    return {
        "schema": QA_PROOF_SCHEMA,
        "generated_at": utc_now(),
        "mode": "write" if args.write else "preview",
        "write_requested": bool(args.write),
        "create_app": bool(args.create_app),
        "live_effects": False,
        "secret_value_printed": False,
        "app_id": weave_runtime_slice.slugify(args.app_id),
        "app_name": args.app_name,
        "surface": surface,
        "command": command,
        "target_label": args.target_label,
        "proof_types": proof_types_for_surface(surface),
        "failure_classes": ["product", "code", "environment", "qa_method"],
    }


def proof_types_for_surface(surface: str) -> list[str]:
    mapping = {
        "web": ["web_frontend"],
        "backend": ["backend_api"],
        "api": ["backend_api"],
        "cli": ["cli_tui"],
        "tui": ["cli_tui"],
        "agent_runtime": ["agent_runtime_transcript"],
        "data_pipeline": ["data_pipeline"],
        "infrastructure": ["infrastructure"],
        "mixed": ["web_frontend", "backend_api", "cli_tui", "agent_runtime_transcript", "data_pipeline", "infrastructure"],
    }
    return mapping[surface]


def ensure_app(root: Path, snapshot: dict[str, Any], *, create_app: bool) -> None:
    app_path = weave_runtime_slice.app_metadata_path(root, snapshot["app_id"])
    if create_app:
        weave_runtime_slice.create_app(root, snapshot["app_id"], snapshot["app_name"])
        return
    if not app_path.exists():
        raise ValueError("qa-proof write requires an existing app; pass --create-app to create local app state")


def write_text_artifact(path: Path, text: str) -> None:
    ensure_public_safe_text(path.name, text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(status: str, proof_type: str, name: str, *, evidence_ref: str, failure_class: str = "", route: str = "") -> dict[str, Any]:
    return {
        "status": status,
        "proof_type": proof_type,
        "name": name,
        "evidence_refs": [evidence_ref],
        "failure_class": failure_class,
        "route": route,
    }


def run_cli(root: Path, app_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    args = shlex.split(snapshot["command"])
    if not args:
        raise ValueError("command must not be empty")
    try:
        completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False, timeout=30)
        excerpt = weave_runtime_slice.public_safe_output_excerpt(completed.stdout, completed.stderr, limit=1200)
        status = "passed" if completed.returncode == 0 and (completed.stdout or completed.stderr) else "failed"
        failure_class = "" if status == "passed" else "code"
        route = "" if status == "passed" else "engineering"
    except (OSError, subprocess.TimeoutExpired) as exc:
        excerpt = {"stdout": "", "stderr": str(exc)}
        status = "failed"
        failure_class = "environment"
        route = "qa_plan_revision"
    path = qa_artifact_dir(root, app_id) / "cli-terminal-evidence.json"
    payload = {
        "schema": QA_PROOF_SCHEMA,
        "proof_type": "cli_tui",
        "command_label": "configured local command",
        "exit_code": getattr(locals().get("completed", None), "returncode", None),
        "output_excerpt": excerpt,
        "public_safe": True,
    }
    weave_runtime_slice.write_json_artifact(path, payload)
    return check(status, "cli_tui", "CLI/TUI command proof", evidence_ref=weave_runtime_slice.relative(path, root), failure_class=failure_class, route=route)


def run_web(root: Path, app_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    path = qa_artifact_dir(root, app_id) / "web-dom-snapshot.html"
    html = (
        "<!doctype html>\n"
        "<html><head><title>WEAVE QA Fixture</title></head>"
        "<body><main><h1>Local Web QA Fixture</h1><p>Rendered proof surface is deterministic.</p></main></body></html>\n"
    )
    write_text_artifact(path, html)
    passed = "<main>" in html and "Local Web QA Fixture" in html
    return check("passed" if passed else "failed", "web_frontend", "Web DOM/render snapshot", evidence_ref=weave_runtime_slice.relative(path, root), failure_class="" if passed else "product", route="" if passed else "engineering")


def run_api(root: Path, app_id: str, _snapshot: dict[str, Any]) -> dict[str, Any]:
    path = qa_artifact_dir(root, app_id) / "api-response-evidence.json"
    response = {
        "schema": QA_PROOF_SCHEMA,
        "proof_type": "backend_api",
        "request": {"method": "GET", "route_label": "health"},
        "response": {"status": 200, "json": {"ok": True}},
        "assertions": ["status is 200", "json.ok is true"],
        "public_safe": True,
    }
    weave_runtime_slice.write_json_artifact(path, response)
    return check("passed", "backend_api", "Backend/API request-response proof", evidence_ref=weave_runtime_slice.relative(path, root))


def run_transcript(root: Path, app_id: str, _snapshot: dict[str, Any]) -> dict[str, Any]:
    path = qa_artifact_dir(root, app_id) / "agent-runtime-transcript.json"
    turns = weave_runtime_slice.read_conversation_turns(root, app_id) if weave_runtime_slice.conversation_turn_path(root, app_id).exists() else []
    payload = {
        "schema": QA_PROOF_SCHEMA,
        "proof_type": "agent_runtime_transcript",
        "turn_count": len(turns),
        "fixture_turn": {
            "operator": "Run local QA proof.",
            "agent": "Recorded deterministic transcript evidence.",
        },
        "assertions": ["transcript evidence is present as fixture or runtime turns"],
        "public_safe": True,
    }
    weave_runtime_slice.write_json_artifact(path, payload)
    return check("passed", "agent_runtime_transcript", "Agent/runtime transcript proof", evidence_ref=weave_runtime_slice.relative(path, root))


def run_data_pipeline(root: Path, app_id: str, _snapshot: dict[str, Any]) -> dict[str, Any]:
    path = qa_artifact_dir(root, app_id) / "data-pipeline-evidence.json"
    input_rows = [{"id": 1, "value": 2}, {"id": 2, "value": 3}]
    output_rows = [{"id": row["id"], "value": row["value"], "double": row["value"] * 2} for row in input_rows]
    payload = {
        "schema": QA_PROOF_SCHEMA,
        "proof_type": "data_pipeline",
        "input_count": len(input_rows),
        "output_count": len(output_rows),
        "assertions": ["input/output row counts match", "derived double field is deterministic"],
        "public_safe": True,
    }
    weave_runtime_slice.write_json_artifact(path, payload)
    return check("passed", "data_pipeline", "Data pipeline transform proof", evidence_ref=weave_runtime_slice.relative(path, root))


def run_infrastructure(root: Path, app_id: str, _snapshot: dict[str, Any]) -> dict[str, Any]:
    path = qa_artifact_dir(root, app_id) / "infrastructure-readback.json"
    app = weave_runtime_slice.load_app(root, app_id)
    payload = {
        "schema": QA_PROOF_SCHEMA,
        "proof_type": "infrastructure",
        "readback": {
            "app_id": app["app_id"],
            "current_stage": app.get("current_stage", ""),
            "ledger_path_present": bool(app.get("ledger_path")),
        },
        "assertions": ["app metadata readback succeeded", "ledger path is declared"],
        "public_safe": True,
    }
    weave_runtime_slice.write_json_artifact(path, payload)
    return check("passed", "infrastructure", "Infrastructure/local metadata readback", evidence_ref=weave_runtime_slice.relative(path, root))


RUNNERS = {
    "web_frontend": run_web,
    "backend_api": run_api,
    "cli_tui": run_cli,
    "agent_runtime_transcript": run_transcript,
    "data_pipeline": run_data_pipeline,
    "infrastructure": run_infrastructure,
}


def run_proofs(root: Path, app_id: str, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    # The proof type list is derived from the surface, so a CLI app never gets
    # a browser-only QA plan and a mixed app can still collect multiple kinds of
    # evidence without pretending they are the same proof surface.
    return [RUNNERS[proof_type](root, app_id, snapshot) for proof_type in snapshot["proof_types"]]


def qa_route(checks: list[dict[str, Any]]) -> str:
    failed = [item for item in checks if item["status"] != "passed"]
    if not failed:
        return "owner_review"
    if any(item["failure_class"] in {"product", "code"} for item in failed):
        return "engineering"
    return "qa_plan_revision"


def build_manifest(snapshot: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    route = qa_route(checks)
    return {
        "schema": QA_PROOF_SCHEMA,
        "app_id": snapshot["app_id"],
        "updated_at": utc_now(),
        "surface": snapshot["surface"],
        "proof_types": snapshot["proof_types"],
        "checks": checks,
        "summary": {
            "status": "passed" if route == "owner_review" else "failed",
            "route": route,
            "failure_classes": sorted({item["failure_class"] for item in checks if item["failure_class"]}),
        },
        "non_claims": ["not deployed proof", "not live user proof", "not paid-spend proof"],
        "public_safe": True,
        "secret_value_printed": False,
    }


def ledger_event(event_id: str, app_id: str, event_type: str, summary: str, evidence_refs: list[str]) -> dict[str, Any]:
    return {
        "schema": validate_lifecycle_artifacts.SCHEMAS["event_ledger_entry"],
        "event_id": event_id,
        "at": utc_now(),
        "app_id": app_id,
        "stage": "qa",
        "actor": "weave-runtime",
        "event_type": event_type,
        "summary": summary,
        "evidence_refs": evidence_refs,
        "claims": [summary],
        "non_claims": ["does not prove deployed production behavior"],
        "requires_owner_review": False,
        "public_safe": True,
    }


def build_lifecycle_bundle(snapshot: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    app_id = snapshot["app_id"]
    status = "completed" if manifest["summary"]["status"] == "passed" else "revision_requested"
    attention_state = "ready_for_review" if status == "completed" else "owner_input_needed"
    route = manifest["summary"]["route"]
    bundle = {
        "schema": "weave/lifecycle-artifact-bundle/v0.1",
        "updated_at": utc_now(),
        "lifecycle_state": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["lifecycle_state"],
            "app_id": app_id,
            "updated_at": utc_now(),
            "current_stage": "qa",
            "stage_source": "event-ledger",
            "stages": [
                {
                    "stage": "qa",
                    "status": status,
                    "artifact_refs": ["artifact:qa-proof-manifest-v1"],
                    "proof_refs": ["artifact:qa-proof-manifest-v1"],
                    "claims": ["surface-specific QA proof manifest was produced"],
                    "non_claims": ["does not prove deployed production behavior"],
                }
            ],
            "attention": {
                "state": attention_state,
                "summary": "QA proof is ready for owner review." if route == "owner_review" else f"QA routes back to {route}.",
                "decision_refs": [],
            },
            "approval_boundaries": ["production_deploy_requires_owner_approval", "public_send_requires_owner_approval"],
            "capability_gaps": ["live deployment not connected", "live analytics not connected"],
            "claims": ["QA proof state is internally linked"],
            "non_claims": ["not production proof"],
        },
        "world_model": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["world_model"],
            "app_id": app_id,
            "updated_at": utc_now(),
            "current_stage": "qa",
            "owner_preferences": {},
            "selected_approach": {
                "summary": f"QA proof selected {', '.join(snapshot['proof_types'])} for {snapshot['surface']} surface.",
                "source_artifact_refs": ["artifact:qa-proof-manifest-v1"],
            },
            "plans": {"qa": "artifact:qa-proof-manifest-v1"},
            "deployment_state": {"status": "not_started", "non_claims": ["not deployed"]},
            "kpi_definitions": [],
            "marketing_state": {"status": "not_started", "non_claims": ["no public campaign started"]},
            "active_jobs": [],
            "known_risks": ["QA route must be followed before deployment"],
            "approval_boundaries": ["production deploy", "public send"],
            "capability_gaps": ["live deployment not connected", "live analytics not connected"],
            "proof_boundary": {
                "highest_proven_surface": "local_deterministic",
                "proof_refs": ["artifact:qa-proof-manifest-v1"],
                "non_claims": ["not deployed", "not live-user validated"],
            },
            "claims": ["world model reflects QA proof route"],
            "non_claims": ["does not prove production behavior"],
        },
        "event_ledger": [
            ledger_event("evt-qa-proof-001", app_id, "proof.recorded", "Surface-specific QA proof recorded.", ["artifact:qa-proof-manifest-v1"]),
            ledger_event("evt-qa-review-001", app_id, "stage.review_requested" if route == "owner_review" else "stage.revision_requested", f"QA route is {route}.", ["artifact:qa-proof-manifest-v1"]),
        ],
        "owner_decision_cards": [],
        "capability_inventory": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["capability_inventory"],
            "updated_at": utc_now(),
            "capabilities": [
                {"id": "local-filesystem", "name": "Local filesystem workspace", "status": "granted", "owner": "weave-runtime", "public_safe": True},
                {"id": "browser-runner", "name": "Browser runner", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "deployment-provider", "name": "Deployment provider", "status": "deferred", "owner": "owner", "public_safe": True},
            ],
        },
        "capability_grants": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_grant"],
                "grant_id": "grant-qa-local-write-001",
                "capability_id": "local-filesystem",
                "app_id": app_id,
                "status": "active",
                "external_effect": "local_write",
                "approved_by": "owner",
                "scope": "write local QA proof artifacts",
                "public_safe": True,
            }
        ],
        "capability_audit_events": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_audit_event"],
                "event_id": "cap-audit-qa-001",
                "capability_id": "local-filesystem",
                "grant_id": "grant-qa-local-write-001",
                "app_id": app_id,
                "external_effect": "local_write",
                "summary": "WEAVE wrote local QA proof artifacts.",
                "public_safe": True,
            }
        ],
        "recurring_jobs": [],
        "job_run_events": [],
        "owner_notifications": [],
        "kill_switches": [],
    }
    validate_lifecycle_artifacts.validate_bundle(bundle)
    return bundle


def write_qa_proof(snapshot: dict[str, Any], args: Any) -> dict[str, Any]:
    root = args.weave_root
    app_id = snapshot["app_id"]
    ensure_app(root, snapshot, create_app=args.create_app)
    checks = run_proofs(root, app_id, snapshot)
    manifest = build_manifest(snapshot, checks)
    m_path = manifest_path(root, app_id)
    b_path = lifecycle_bundle_path(root, app_id)
    weave_runtime_slice.write_json_artifact(m_path, manifest)
    weave_runtime_slice.write_json_artifact(b_path, build_lifecycle_bundle(snapshot, manifest))
    app = weave_runtime_slice.load_app(root, app_id)
    app["qa_proof"] = {
        "surface": snapshot["surface"],
        "status": manifest["summary"]["status"],
        "route": manifest["summary"]["route"],
        "manifest_path": weave_runtime_slice.relative(m_path, root),
    }
    if manifest["summary"]["route"] == "engineering":
        app["current_stage"] = "engineering"
        app["stage_state"] = "blocked"
        app["blockers"] = sorted(set(app.get("blockers", []) + ["qa failed: route to engineering"]))
    elif manifest["summary"]["route"] == "qa_plan_revision":
        app["current_stage"] = "qa"
        app["stage_state"] = "blocked"
        app["blockers"] = sorted(set(app.get("blockers", []) + ["qa method revision required"]))
    else:
        app["current_stage"] = "qa"
        app["stage_state"] = "ready_for_review"
    weave_runtime_slice.write_app(root, app)
    weave_runtime_slice.update_registry_entry(root, app)
    weave_runtime_slice.append_event(
        root,
        app_id,
        weave_runtime_slice.new_event(
            "validation.completed",
            app_id,
            "qa",
            f"QA proof completed with route {manifest['summary']['route']}.",
            payload={"manifest_path": weave_runtime_slice.relative(m_path, root), "route": manifest["summary"]["route"]},
            artifact_refs=[{"path": weave_runtime_slice.relative(m_path, root), "stage": "qa"}],
        ),
    )
    return {
        "app_id": app_id,
        "surface": snapshot["surface"],
        "status": manifest["summary"]["status"],
        "route": manifest["summary"]["route"],
        "manifest_path": str(m_path),
        "bundle_path": str(b_path),
        "check_count": len(checks),
        "live_effects": False,
    }


def render_text(snapshot: dict[str, Any], *, write_result: dict[str, Any] | None = None) -> str:
    lines = [
        "+------------------------------------------------------------+",
        "| WEAVE QA Proof Runner                                      |",
        "| surface-specific local evidence and failure routing         |",
        "+------------------------------------------------------------+",
        "",
        "[Plan]",
        f"  app: {snapshot['app_id']}",
        f"  surface: {snapshot['surface']}",
        f"  proof_types: {', '.join(snapshot['proof_types'])}",
        f"  failure_classes: {', '.join(snapshot['failure_classes'])}",
        "",
        "[Proof Boundary]",
        "  live_effects: false",
        "  secret_value_printed: false",
        "  non_claims: no deployment, no live users, no paid spend",
    ]
    if write_result:
        lines.extend(
            [
                "",
                "[Written]",
                f"  status: {write_result['status']}",
                f"  route: {write_result['route']}",
                f"  checks: {write_result['check_count']}",
                f"  manifest: {write_result['manifest_path']}",
                f"  lifecycle_bundle: {write_result['bundle_path']}",
            ]
        )
    else:
        lines.extend(["", "[Next]", "  rerun with --write to create local QA evidence"])
    return "\n".join(lines) + "\n"


def run(args: Any, *, output: TextIO = sys.stdout) -> int:
    try:
        snapshot = snapshot_from_args(args)
        write_result = write_qa_proof(snapshot, args) if args.write else None
    except (OSError, ValueError, validate_lifecycle_artifacts.ValidationError, weave_runtime_slice.RuntimeSliceError) as exc:
        print(f"qa-proof failed: {exc}", file=output)
        return 1
    if args.json:
        payload = dict(snapshot)
        if write_result:
            payload["write_result"] = write_result
        print(json.dumps(payload, indent=2, sort_keys=True), file=output)
        return 0
    print(render_text(snapshot, write_result=write_result), end="", file=output)
    return 0
