#!/usr/bin/env python3
"""Engineering owner-decision queue for WEAVE.

The queue models the moment an engineering agent hits a consequential decision.
It is deterministic and local-only: no external capability is exercised, and
hard-boundary items remain blocked until an owner response is recorded.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import validate_lifecycle_artifacts
import weave_runtime_slice


ENGINEERING_DECISIONS_SCHEMA = "weave-engineering-decisions/v0.1"
HARD_BOUNDARIES = (
    "spend",
    "public_send",
    "production_deploy",
    "destructive_action",
    "security_boundary",
    "credential_scope",
)
DEFAULT_DECISION_ID = "engineering-decision-001"
DEFAULT_QUESTION = "Should Engineering proceed with the local-safe implementation path?"
DEFAULT_OWNER_RESPONSE = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_public_safe_text(label: str, value: str) -> None:
    if weave_runtime_slice.contains_secret_like_value(value):
        raise ValueError(f"{label} contains secret-looking content")
    if weave_runtime_slice.contains_private_locator(value):
        raise ValueError(f"{label} contains private locator content")


def engineering_artifact_dir(root: Path, app_id: str) -> Path:
    stage = weave_runtime_slice.stage_by_id("engineering")
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage.directory / "artifacts"


def queue_path(root: Path, app_id: str) -> Path:
    return engineering_artifact_dir(root, app_id) / "owner-decision-queue.json"


def assumption_log_path(root: Path, app_id: str) -> Path:
    return engineering_artifact_dir(root, app_id) / "assumption-log.md"


def notification_board_path(root: Path, app_id: str) -> Path:
    return engineering_artifact_dir(root, app_id) / "notification-board.json"


def lifecycle_bundle_path(root: Path, app_id: str) -> Path:
    return engineering_artifact_dir(root, app_id) / "engineering-decision-bundle.json"


def snapshot_from_args(args: Any) -> dict[str, Any]:
    app_id = weave_runtime_slice.slugify(args.app_id)
    boundaries = list(dict.fromkeys(args.hard_boundary or []))
    for boundary in boundaries:
        if boundary not in HARD_BOUNDARIES:
            raise ValueError(f"unsupported hard boundary: {boundary}")
    snapshot = {
        "schema": ENGINEERING_DECISIONS_SCHEMA,
        "generated_at": utc_now(),
        "mode": "write" if args.write else "preview",
        "write_requested": bool(args.write),
        "live_effects": False,
        "secret_value_printed": False,
        "app_id": app_id,
        "decision_id": weave_runtime_slice.slugify(args.decision_id),
        "control_mode": args.control_mode,
        "decision_type": args.decision_type,
        "question": args.question,
        "selected_option": args.selected_option,
        "owner_response": args.owner_response,
        "hard_boundaries": boundaries,
        "requires_owner": args.control_mode == "hands-on" or bool(boundaries),
        "hard_stop_boundaries": list(HARD_BOUNDARIES),
    }
    for label in ("decision_id", "question", "selected_option", "owner_response"):
        ensure_public_safe_text(label, str(snapshot[label]))
    return snapshot


def load_engineering_app(root: Path, app_id: str) -> dict[str, Any]:
    app = weave_runtime_slice.load_app(root, app_id)
    current = weave_runtime_slice.normalize_stage_id(app.get("current_stage"), default="intent")
    if current != "engineering":
        raise ValueError("engineering decision queue requires an app currently at Engineering")
    return app


def decision_card(snapshot: dict[str, Any]) -> dict[str, Any]:
    answered = bool(snapshot["owner_response"].strip())
    requires_owner = bool(snapshot["requires_owner"])
    now = utc_now()
    card = {
        "schema": validate_lifecycle_artifacts.SCHEMAS["owner_decision_card"],
        "decision_id": snapshot["decision_id"],
        "app_id": snapshot["app_id"],
        "stage": "engineering",
        "status": "answered" if answered else "open" if requires_owner else "deferred",
        "created_at": now,
        "updated_at": now,
        "decision_type": snapshot["decision_type"],
        "question": snapshot["question"],
        "why_it_matters": "Engineering behavior changes source scope, QA burden, capability needs, or owner-visible product behavior.",
        "options": [
            {
                "id": "local-safe-path",
                "label": "Local-safe path",
                "description": "Proceed only inside local files and deterministic checks.",
                "agent_recommendation": True,
                "consequences": ["keeps external effects at none/local_write", "can continue without provider credentials"],
            },
            {
                "id": "external-effect-path",
                "label": "External-effect path",
                "description": "Proceed with an action that crosses a hard owner boundary.",
                "agent_recommendation": False,
                "consequences": ["requires owner approval", "may require credentials, spend, public send, deploy, security, or destructive approval"],
            },
        ],
        "selected_option_id": snapshot["selected_option"] if answered or not requires_owner else "",
        "owner_response": snapshot["owner_response"] if answered else "deferred by hands-off safe-assumption policy" if not requires_owner else "",
        "hard_boundary_flags": snapshot["hard_boundaries"],
        "evidence_refs": ["artifact:owner-decision-queue-v1"],
        "claims": ["engineering decision card is recorded"],
        "non_claims": ["does not execute the selected engineering action"],
    }
    if answered:
        card["answered_at"] = now
    return card


def notification(snapshot: dict[str, Any], card: dict[str, Any]) -> dict[str, Any]:
    open_status = card["status"] == "open"
    severity = "blocked" if snapshot["hard_boundaries"] else "action_required" if open_status else "review"
    return {
        "schema": validate_lifecycle_artifacts.SCHEMAS["owner_notification"],
        # Avoid long hyphenated public IDs here; the repo's leak scanner treats
        # those as token-shaped even when they are deterministic identifiers.
        "notification_id": f"note-eng-{snapshot['decision_id'].split('-')[-1]}",
        "app_id": snapshot["app_id"],
        "created_at": utc_now(),
        "source": "lifecycle",
        "severity": severity,
        "status": "open" if open_status else "resolved",
        "title": "Engineering owner decision required" if open_status else "Engineering owner decision resolved",
        "body": snapshot["question"],
        "action_refs": [f"decision-card:{snapshot['decision_id']}"],
        "evidence_refs": ["artifact:owner-decision-queue-v1"],
        "public_safe": True,
    }


def assumptions(snapshot: dict[str, Any], card: dict[str, Any]) -> list[dict[str, Any]]:
    safe_to_continue = snapshot["control_mode"] == "hands-off" and not snapshot["hard_boundaries"] and card["status"] != "open"
    if snapshot["control_mode"] == "hands-off" and not snapshot["hard_boundaries"] and card["status"] == "open":
        # Hands-off mode can use safe assumptions for non-hard-boundary work.
        # The queue still records the assumption so a future bug can distinguish
        # "agent guessed safely" from "owner approved a consequential change."
        safe_to_continue = True
    return [
        {
            "assumption_id": "assumption-local-only-001",
            "status": "active" if safe_to_continue else "blocked_by_owner_decision",
            "summary": "Engineering may proceed only with local filesystem work and deterministic checks.",
            "boundary": "external_effects_none_or_local_write",
            "evidence_refs": ["artifact:owner-decision-queue-v1"],
        }
    ]


def queue_payload(snapshot: dict[str, Any], card: dict[str, Any], note: dict[str, Any], assumption_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": ENGINEERING_DECISIONS_SCHEMA,
        "app_id": snapshot["app_id"],
        "updated_at": utc_now(),
        "control_mode": snapshot["control_mode"],
        "hard_stop_boundaries": snapshot["hard_stop_boundaries"],
        "decisions": [card],
        "notifications": [note],
        "assumptions": assumption_rows,
        "resume": {
            "allowed": card["status"] == "answered" or (snapshot["control_mode"] == "hands-off" and not snapshot["hard_boundaries"]),
            "reason": "owner answered decision" if card["status"] == "answered" else "hands-off safe assumption" if snapshot["control_mode"] == "hands-off" and not snapshot["hard_boundaries"] else "owner decision required",
        },
        "live_effects": False,
        "secret_value_printed": False,
    }


def assumption_markdown(snapshot: dict[str, Any], assumption_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Engineering Assumption Log",
        "",
        f"Control mode: {snapshot['control_mode']}",
        "",
        "## Hard Stop Boundaries",
        *[f"- {item}" for item in HARD_BOUNDARIES],
        "",
        "## Assumptions",
    ]
    for item in assumption_rows:
        lines.extend(
            [
                f"- {item['assumption_id']}: {item['status']}",
                f"  - {item['summary']}",
                f"  - boundary: {item['boundary']}",
            ]
        )
    lines.extend(["", "Boundary: assumptions never authorize spend, public sends, production deploys, destructive actions, security boundary changes, or credential-scope changes."])
    return "\n".join(lines) + "\n"


def update_app_state(root: Path, app: dict[str, Any], payload: dict[str, Any], card: dict[str, Any]) -> None:
    app["engineering_control_mode"] = payload["control_mode"]
    app["owner_decision_queue"] = [
        {
            "decision_id": card["decision_id"],
            "status": card["status"],
            "question": card["question"],
            "hard_boundary_flags": card.get("hard_boundary_flags", []),
        }
    ]
    app["notification_board"] = [
        {
            "notification_id": payload["notifications"][0]["notification_id"],
            "status": payload["notifications"][0]["status"],
            "severity": payload["notifications"][0]["severity"],
        }
    ]
    app["assumptions"] = payload["assumptions"]
    if payload["resume"]["allowed"]:
        app["blockers"] = [item for item in app.get("blockers", []) if not str(item).startswith("owner decision:")]
        app["stage_state"] = "collecting"
    else:
        blocker = f"owner decision: {card['decision_id']}"
        blockers = [item for item in app.get("blockers", []) if item != blocker]
        blockers.append(blocker)
        app["blockers"] = blockers
        app["stage_state"] = "blocked"
    weave_runtime_slice.write_app(root, app)
    weave_runtime_slice.update_registry_entry(root, app)


def append_decision_log(root: Path, app_id: str, card: dict[str, Any], payload: dict[str, Any]) -> None:
    path = weave_runtime_slice.app_root(root, app_id) / "context" / "decisions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# App Decisions\n\n"
    entry = (
        f"\n## {card['decision_id']}\n\n"
        f"- Status: {card['status']}\n"
        f"- Question: {card['question']}\n"
        f"- Control mode: {payload['control_mode']}\n"
        f"- Resume allowed: {str(payload['resume']['allowed']).lower()}\n"
        f"- Hard boundaries: {', '.join(card.get('hard_boundary_flags', [])) or 'none'}\n"
    )
    path.write_text(existing.rstrip() + "\n" + entry, encoding="utf-8")


def ledger_event(event_id: str, snapshot: dict[str, Any], event_type: str, summary: str, evidence_refs: list[str]) -> dict[str, Any]:
    return {
        "schema": validate_lifecycle_artifacts.SCHEMAS["event_ledger_entry"],
        "event_id": event_id,
        "at": utc_now(),
        "app_id": snapshot["app_id"],
        "stage": "engineering",
        "actor": "weave-runtime",
        "event_type": event_type,
        "summary": summary,
        "evidence_refs": evidence_refs,
        "claims": [summary],
        "non_claims": ["does not execute engineering action"],
        "requires_owner_review": False,
        "public_safe": True,
    }


def build_lifecycle_bundle(snapshot: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    card = payload["decisions"][0]
    note = payload["notifications"][0]
    open_decision = card["status"] == "open"
    status = "owner_input_needed" if open_decision else "running"
    attention = "owner_input_needed" if open_decision else "no_attention_needed"
    event_ledger = [
        ledger_event("evt-eng-created-001", snapshot, "decision.created", "Engineering owner decision card recorded.", ["decision-card:" + card["decision_id"]]),
        ledger_event("evt-eng-world-001", snapshot, "world_model.updated", "Engineering world model updated with decision queue and assumptions.", ["artifact:engineering-decision-bundle-v1"]),
        ledger_event("evt-eng-proof-001", snapshot, "proof.recorded", "Engineering decision bundle validated locally.", ["artifact:engineering-decision-bundle-v1"]),
    ]
    if card["status"] == "answered":
        event_ledger.insert(1, ledger_event("evt-eng-answered-001", snapshot, "decision.answered", "Owner response recorded and Engineering resume allowed.", ["decision-card:" + card["decision_id"]]))
    bundle = {
        "schema": "weave/lifecycle-artifact-bundle/v0.1",
        "updated_at": utc_now(),
        "lifecycle_state": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["lifecycle_state"],
            "app_id": snapshot["app_id"],
            "updated_at": utc_now(),
            "current_stage": "engineering",
            "stage_source": "event-ledger",
            "stages": [
                {
                    "stage": "engineering",
                    "status": status,
                    "artifact_refs": ["artifact:owner-decision-queue-v1", "artifact:assumption-log-v1"],
                    "proof_refs": ["artifact:engineering-decision-bundle-v1"],
                    "decision_refs": ["decision-card:" + card["decision_id"]],
                    "claims": ["engineering decision queue is recorded"],
                    "non_claims": ["no engineering action was executed"],
                }
            ],
            "attention": {
                "state": attention,
                "summary": "Owner decision required before Engineering resumes." if open_decision else "Owner decision recorded; Engineering may resume inside boundaries.",
                "decision_refs": ["decision-card:" + card["decision_id"]] if open_decision else [],
            },
            "approval_boundaries": list(HARD_BOUNDARIES),
            "capability_gaps": ["credentials deferred", "deployment provider not connected", "public-send channel not connected"],
            "claims": ["engineering owner-decision state is internally linked"],
            "non_claims": ["does not authorize external effects"],
        },
        "world_model": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["world_model"],
            "app_id": snapshot["app_id"],
            "updated_at": utc_now(),
            "current_stage": "engineering",
            "owner_preferences": {
                "control_mode": snapshot["control_mode"],
            },
            "selected_approach": {
                "summary": "Proceed only when the decision card is answered or when hands-off mode has no hard-boundary flags.",
                "source_artifact_refs": ["artifact:owner-decision-queue-v1"],
            },
            "plans": {
                "engineering": "artifact:owner-decision-queue-v1",
                "qa": "artifact:assumption-log-v1",
            },
            "deployment_state": {
                "status": "not_started",
                "non_claims": ["production deploy remains hard-gated"],
            },
            "kpi_definitions": [],
            "marketing_state": {
                "status": "not_started",
                "non_claims": ["public sends remain hard-gated"],
            },
            "active_jobs": [],
            "known_risks": ["hard-boundary work must not proceed without owner approval"],
            "approval_boundaries": list(HARD_BOUNDARIES),
            "capability_gaps": ["credentials deferred", "deployment provider not connected", "public-send channel not connected"],
            "proof_boundary": {
                "highest_proven_surface": "local_deterministic",
                "proof_refs": ["artifact:engineering-decision-bundle-v1"],
                "non_claims": ["not live Hermes proof", "not deployed", "not external-write proof"],
            },
            "claims": ["world model reflects current engineering decision queue"],
            "non_claims": ["does not prove implementation execution"],
        },
        "event_ledger": event_ledger,
        "owner_decision_cards": [card],
        "capability_inventory": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["capability_inventory"],
            "updated_at": utc_now(),
            "capabilities": [
                {"id": "local-filesystem", "name": "Local filesystem workspace", "status": "granted", "owner": "weave-runtime", "public_safe": True},
                {"id": "paid-spend", "name": "Paid spend", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "public-send", "name": "Public send channel", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "production-deploy", "name": "Production deploy", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "destructive-change", "name": "Destructive action", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "security-boundary", "name": "Security boundary change", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "credential-scope", "name": "Credential scope change", "status": "deferred", "owner": "owner", "public_safe": True},
            ],
        },
        "capability_grants": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_grant"],
                "grant_id": "grant-engineering-local-write-001",
                "capability_id": "local-filesystem",
                "app_id": snapshot["app_id"],
                "status": "active",
                "external_effect": "local_write",
                "approved_by": "owner",
                "scope": "write local engineering decision queue artifacts",
                "public_safe": True,
            }
        ],
        "capability_audit_events": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_audit_event"],
                "event_id": "capability-audit-engineering-decision-001",
                "capability_id": "local-filesystem",
                "grant_id": "grant-engineering-local-write-001",
                "app_id": snapshot["app_id"],
                "external_effect": "local_write",
                "summary": "WEAVE wrote local engineering owner-decision artifacts.",
                "public_safe": True,
            }
        ],
        "recurring_jobs": [],
        "job_run_events": [],
        "owner_notifications": [note],
        "kill_switches": [],
    }
    validate_lifecycle_artifacts.validate_bundle(bundle)
    return bundle


def write_decision_state(snapshot: dict[str, Any], args: Any) -> dict[str, Any]:
    root = args.weave_root
    app_id = snapshot["app_id"]
    app = load_engineering_app(root, app_id)
    card = decision_card(snapshot)
    note = notification(snapshot, card)
    assumption_rows = assumptions(snapshot, card)
    payload = queue_payload(snapshot, card, note, assumption_rows)
    update_app_state(root, app, payload, card)
    append_decision_log(root, app_id, card, payload)

    q_path = queue_path(root, app_id)
    n_path = notification_board_path(root, app_id)
    a_path = assumption_log_path(root, app_id)
    b_path = lifecycle_bundle_path(root, app_id)
    weave_runtime_slice.write_json_artifact(q_path, payload)
    weave_runtime_slice.write_json_artifact(n_path, {"schema": ENGINEERING_DECISIONS_SCHEMA, "notifications": [note], "public_safe": True})
    a_path.parent.mkdir(parents=True, exist_ok=True)
    a_path.write_text(assumption_markdown(snapshot, assumption_rows), encoding="utf-8")
    weave_runtime_slice.write_json_artifact(b_path, build_lifecycle_bundle(snapshot, payload))
    weave_runtime_slice.append_event(
        root,
        app_id,
        weave_runtime_slice.new_event(
            "artifact.created",
            app_id,
            "engineering",
            "Engineering owner-decision queue artifacts written.",
            payload={
                "queue_path": weave_runtime_slice.relative(q_path, root),
                "notification_board_path": weave_runtime_slice.relative(n_path, root),
                "assumption_log_path": weave_runtime_slice.relative(a_path, root),
                "bundle_path": weave_runtime_slice.relative(b_path, root),
                "resume_allowed": payload["resume"]["allowed"],
            },
            artifact_refs=[
                {"path": weave_runtime_slice.relative(q_path, root), "stage": "engineering"},
                {"path": weave_runtime_slice.relative(a_path, root), "stage": "engineering"},
                {"path": weave_runtime_slice.relative(b_path, root), "stage": "engineering"},
            ],
        ),
    )
    return {
        "app_id": app_id,
        "decision_status": card["status"],
        "notification_status": note["status"],
        "resume_allowed": payload["resume"]["allowed"],
        "stage_state": weave_runtime_slice.load_app(root, app_id).get("stage_state"),
        "queue_path": str(q_path),
        "notification_board_path": str(n_path),
        "assumption_log_path": str(a_path),
        "bundle_path": str(b_path),
        "live_effects": False,
    }


def render_text(snapshot: dict[str, Any], *, write_result: dict[str, Any] | None = None) -> str:
    lines = [
        "+------------------------------------------------------------+",
        "| WEAVE Engineering Decision Queue                           |",
        "| owner decisions, notifications, assumptions, hard stops     |",
        "+------------------------------------------------------------+",
        "",
        "[Decision]",
        f"  app: {snapshot['app_id']}",
        f"  control_mode: {snapshot['control_mode']}",
        f"  decision_id: {snapshot['decision_id']}",
        f"  type: {snapshot['decision_type']}",
        f"  hard_boundaries: {', '.join(snapshot['hard_boundaries']) or 'none'}",
        f"  requires_owner: {str(snapshot['requires_owner']).lower()}",
        "",
        "[Hard Stops]",
        *[f"  - {item}" for item in HARD_BOUNDARIES],
        "",
        "[Proof Boundary]",
        "  live_effects: false",
        "  secret_value_printed: false",
        "  non_claims: no engineering action executed, no external write, no deploy, no public send",
    ]
    if write_result:
        lines.extend(
            [
                "",
                "[Written]",
                f"  decision_status: {write_result['decision_status']}",
                f"  notification_status: {write_result['notification_status']}",
                f"  resume_allowed: {str(write_result['resume_allowed']).lower()}",
                f"  stage_state: {write_result['stage_state']}",
                f"  queue: {write_result['queue_path']}",
                f"  assumption_log: {write_result['assumption_log_path']}",
                f"  lifecycle_bundle: {write_result['bundle_path']}",
            ]
        )
    else:
        lines.extend(["", "[Next]", "  rerun with --write against an app currently at Engineering"])
    return "\n".join(lines) + "\n"


def run(args: Any, *, output: TextIO = sys.stdout) -> int:
    try:
        snapshot = snapshot_from_args(args)
        write_result = write_decision_state(snapshot, args) if args.write else None
    except (OSError, ValueError, validate_lifecycle_artifacts.ValidationError, weave_runtime_slice.RuntimeSliceError) as exc:
        print(f"engineering-decisions failed: {exc}", file=output)
        return 1
    if args.json:
        payload = dict(snapshot)
        if write_result:
            payload["write_result"] = write_result
        print(json.dumps(payload, indent=2, sort_keys=True), file=output)
        return 0
    print(render_text(snapshot, write_result=write_result), end="", file=output)
    return 0
