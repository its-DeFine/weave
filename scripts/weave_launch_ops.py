#!/usr/bin/env python3
"""Capability-gated deployment, KPI, marketing, and iteration flow for WEAVE."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import validate_lifecycle_artifacts
import weave_runtime_slice


LAUNCH_OPS_SCHEMA = "weave-launch-ops/v0.1"
DEFAULT_MARKETING_BUDGET = "none"
DEFAULT_DEPLOYMENT_REGION = "global"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_public_safe_text(label: str, value: str) -> None:
    if weave_runtime_slice.contains_secret_like_value(value):
        raise ValueError(f"{label} contains secret-looking content")
    if weave_runtime_slice.contains_private_locator(value):
        raise ValueError(f"{label} contains private locator content")


def artifact_dir(root: Path, app_id: str, stage_id: str) -> Path:
    # Resolve through the runtime stage registry so a renamed or reordered
    # lifecycle shelf fails loudly instead of writing artifacts into stale dirs.
    stage = weave_runtime_slice.stage_by_id(stage_id)
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage.directory / "artifacts"


def launch_manifest_path(root: Path, app_id: str) -> Path:
    return artifact_dir(root, app_id, "deployment") / "launch-ops-manifest.json"


def lifecycle_bundle_path(root: Path, app_id: str) -> Path:
    return artifact_dir(root, app_id, "deployment") / "launch-ops-lifecycle-bundle.json"


def snapshot_from_args(args: Any) -> dict[str, Any]:
    app_id = weave_runtime_slice.slugify(args.app_id)
    # These values can appear in owner-visible artifacts, so reject accidental
    # secrets or host locators before any file write happens.
    for label, value in (
        ("deployment_region", args.deployment_region),
        ("marketing_budget", args.marketing_budget),
        ("feedback_source", args.feedback_source),
    ):
        ensure_public_safe_text(label, str(value))
    return {
        "schema": LAUNCH_OPS_SCHEMA,
        "generated_at": utc_now(),
        "mode": "write" if args.write else "preview",
        "write_requested": bool(args.write),
        "create_app": bool(args.create_app),
        "live_effects": False,
        "secret_value_printed": False,
        "app_id": app_id,
        "app_name": args.app_name,
        "deployment_region": args.deployment_region,
        "marketing_budget": args.marketing_budget,
        "feedback_source": args.feedback_source,
        "approved_external_actions": [],
    }


def ensure_app(root: Path, snapshot: dict[str, Any], *, create_app: bool) -> None:
    app_path = weave_runtime_slice.app_metadata_path(root, snapshot["app_id"])
    if create_app:
        weave_runtime_slice.create_app(root, snapshot["app_id"], snapshot["app_name"])
        return
    # A missing app without --create-app usually means the operator expected a
    # no-side-effect preview. Writes require an explicit local app boundary.
    if not app_path.exists():
        raise ValueError("launch-ops write requires an existing app; pass --create-app to create local app state")


def write_stage_plan(root: Path, app_id: str, stage_id: str, title: str, lines: list[str]) -> str:
    path = artifact_dir(root, app_id, stage_id) / f"launch-{stage_id}-plan.md"
    text = "# " + title + "\n\n" + "\n".join(f"- {line}" for line in lines) + "\n"
    ensure_public_safe_text(path.name, text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return weave_runtime_slice.relative(path, root)


def capability_inventory(now: str) -> dict[str, Any]:
    # The inventory intentionally models missing launch powers instead of using
    # real provider credentials. That lets the TUI/CLI expose the launch UX
    # without gaining deployment, analytics, marketing, or paid-spend authority.
    return {
        "schema": validate_lifecycle_artifacts.SCHEMAS["capability_inventory"],
        "updated_at": now,
        "capabilities": [
            {
                "id": "repo-worktree",
                "display_name": "Repository worktree",
                "type": "repo",
                "status": "granted",
                "owner_approval_policy": "not_required_for_read_only",
                "risk_level": "low",
                "allowed_actions": ["local-write"],
                "public_safe": True,
            },
            {
                "id": "deployment-provider",
                "display_name": "Deployment provider",
                "type": "cloud",
                "status": "deferred",
                "owner_approval_policy": "always_required",
                "risk_level": "high",
                "blocked_actions": ["production-deploy"],
                "non_claims": ["no production deployment capability connected"],
                "public_safe": True,
            },
            {
                "id": "analytics-provider",
                "display_name": "Analytics provider",
                "type": "analytics",
                "status": "deferred",
                "owner_approval_policy": "required_for_external_effects",
                "risk_level": "medium",
                "blocked_actions": ["live-analytics-write"],
                "public_safe": True,
            },
            {
                "id": "marketing-accounts",
                "display_name": "Marketing accounts",
                "type": "social",
                "status": "deferred",
                "owner_approval_policy": "always_required",
                "risk_level": "high",
                "blocked_actions": ["public-send", "paid-spend"],
                "public_safe": True,
            },
            {
                "id": "feedback-inbox",
                "display_name": "Feedback inbox",
                "type": "messaging",
                "status": "available_unconnected",
                "owner_approval_policy": "required_for_external_effects",
                "risk_level": "medium",
                "allowed_actions": ["read-only-summary"],
                "public_safe": True,
            },
        ],
    }


def kill_switches(app_id: str, now: str) -> list[dict[str, Any]]:
    return [
        {
            "schema": validate_lifecycle_artifacts.SCHEMAS["kill_switch"],
            "switch_id": "ks-public-actions",
            "status": "enabled",
            "created_at": now,
            "scope": {
                "app_ids": [app_id],
                "external_effects": ["public_send", "paid_spend", "production_write"],
            },
            "reason": "Block unapproved public sends, paid spend, and production writes.",
            "created_by": "weave-runtime",
            "public_safe": True,
        }
    ]


def recurring_jobs(snapshot: dict[str, Any], now: str) -> list[dict[str, Any]]:
    app_id = snapshot["app_id"]
    # If the owner has not named a paid budget, paid marketing is blocked. If a
    # budget is named, the job still waits for approval; it never spends here.
    paid_status = "pending_owner_approval" if snapshot["marketing_budget"] != "none" else "blocked"
    return [
        {
            "schema": validate_lifecycle_artifacts.SCHEMAS["recurring_job"],
            "job_id": "job-market-001",
            "app_id": app_id,
            "job_type": "marketing_engagement",
            "status": "pending_owner_approval",
            "created_at": now,
            "cadence": {"kind": "weekly", "description": "Draft organic engagement suggestions for owner review."},
            "owner_visible_name": "Organic marketing heartbeat",
            "purpose": "Prepare organic posts and replies without sending them.",
            "lifecycle_stages": ["marketing", "iteration"],
            "capability_refs": ["capability:marketing-accounts"],
            "approval_required_for": ["public-send"],
            "external_effect": "read_only",
            "kill_switch_refs": ["kill-switch:ks-public-actions"],
            "evidence_refs": ["artifact:launch-marketing-plan-v1"],
            "non_claims": ["no public message is sent"],
            "public_safe": True,
        },
        {
            "schema": validate_lifecycle_artifacts.SCHEMAS["recurring_job"],
            "job_id": "job-paid-001",
            "app_id": app_id,
            "job_type": "marketing_engagement",
            "status": paid_status,
            "created_at": now,
            "cadence": {"kind": "manual", "description": "Only run after owner approves paid campaign capability."},
            "owner_visible_name": "Paid marketing gate",
            "purpose": "Represent paid-spend planning without spending.",
            "lifecycle_stages": ["marketing"],
            "capability_refs": ["capability:marketing-accounts"],
            "approval_required_for": ["paid-spend", "public-send"],
            "external_effect": "paid_spend",
            "kill_switch_refs": ["kill-switch:ks-public-actions"],
            "evidence_refs": ["artifact:launch-marketing-plan-v1"],
            "non_claims": ["no paid spend is performed"],
            "public_safe": True,
        },
        {
            "schema": validate_lifecycle_artifacts.SCHEMAS["recurring_job"],
            "job_id": "job-feedback-001",
            "app_id": app_id,
            "job_type": "feedback_intake",
            "status": "active",
            "created_at": now,
            "cadence": {"kind": "daily", "description": "Aggregate local feedback artifacts."},
            "owner_visible_name": "Feedback intake heartbeat",
            "purpose": "Turn owner and QA feedback into iteration candidates.",
            "lifecycle_stages": ["iteration", "analysis"],
            "capability_refs": ["capability:feedback-inbox"],
            "approval_required_for": ["create-production-change"],
            "external_effect": "local_write",
            "kill_switch_refs": [],
            "evidence_refs": ["artifact:launch-iteration-plan-v1"],
            "public_safe": True,
        },
        {
            "schema": validate_lifecycle_artifacts.SCHEMAS["recurring_job"],
            "job_id": "job-ideas-001",
            "app_id": app_id,
            "job_type": "feature_recommendation",
            "status": "active",
            "created_at": now,
            "cadence": {"kind": "weekly", "description": "Summarize feedback and suggest owner-reviewed iteration items."},
            "owner_visible_name": "Iteration analysis heartbeat",
            "purpose": "Recommend improvements from local evidence.",
            "lifecycle_stages": ["iteration", "analysis"],
            "capability_refs": ["capability:repo-worktree"],
            "approval_required_for": ["staged-implementation"],
            "external_effect": "local_write",
            "kill_switch_refs": [],
            "evidence_refs": ["artifact:launch-iteration-plan-v1"],
            "public_safe": True,
        },
    ]


def notifications(snapshot: dict[str, Any], now: str) -> list[dict[str, Any]]:
    return [
        {
            "schema": validate_lifecycle_artifacts.SCHEMAS["owner_notification"],
            "notification_id": "note-launch-caps",
            "app_id": snapshot["app_id"],
            "created_at": now,
            "source": "capability",
            "severity": "blocked",
            "status": "open",
            "title": "Launch capabilities deferred",
            "body": "Deployment, analytics, and marketing account capabilities are deferred until owner approval.",
            "action_refs": ["capability:deployment-provider", "capability:analytics-provider", "capability:marketing-accounts"],
            "evidence_refs": ["artifact:launch-ops-manifest-v1"],
            "public_safe": True,
        }
    ]


def build_manifest(snapshot: dict[str, Any], stage_artifacts: dict[str, str], jobs: list[dict[str, Any]], now: str) -> dict[str, Any]:
    # The manifest is the owner-facing launch wall: what is ready, what is
    # blocked, and which recurring fixtures exist. It records non-claims beside
    # claims so a local rehearsal cannot be mistaken for a production launch.
    return {
        "schema": LAUNCH_OPS_SCHEMA,
        "app_id": snapshot["app_id"],
        "updated_at": now,
        "deployment": {
            "status": "blocked_on_capability",
            "region": snapshot["deployment_region"],
            "post_deploy_qa_required": True,
            "artifact_ref": stage_artifacts["deployment"],
        },
        "kpi": {
            "status": "draft",
            "base_kpis": ["activation-review", "qa-pass-rate", "owner-decision-latency"],
            "instrumentation_boundary": "local counters until analytics provider is approved",
            "artifact_ref": stage_artifacts["kpi"],
        },
        "marketing": {
            "status": "draft",
            "budget": snapshot["marketing_budget"],
            "organic_supported": True,
            "paid_blocked_without_owner_approval": True,
            "artifact_ref": stage_artifacts["marketing"],
        },
        "iteration": {
            "status": "active_local_loop",
            "feedback_source": snapshot["feedback_source"],
            "artifact_ref": stage_artifacts["iteration"],
        },
        "jobs": jobs,
        "capability_inventory": capability_inventory(now),
        "kill_switches": kill_switches(snapshot["app_id"], now),
        "owner_notifications": notifications(snapshot, now),
        "external_effects_executed": [],
        "non_claims": ["no deployment", "no public send", "no paid spend", "no raw credential handling"],
        "public_safe": True,
        "secret_value_printed": False,
    }


def ledger_event(event_id: str, app_id: str, stage: str, event_type: str, summary: str, evidence_refs: list[str]) -> dict[str, Any]:
    return {
        "schema": validate_lifecycle_artifacts.SCHEMAS["event_ledger_entry"],
        "event_id": event_id,
        "at": utc_now(),
        "app_id": app_id,
        "stage": stage,
        "actor": "weave-runtime",
        "event_type": event_type,
        "summary": summary,
        "evidence_refs": evidence_refs,
        "claims": [summary],
        "non_claims": ["no external effect occurred"],
        "requires_owner_review": False,
        "public_safe": True,
    }


def build_lifecycle_bundle(snapshot: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    app_id = snapshot["app_id"]
    inv = manifest["capability_inventory"]
    jobs = manifest["jobs"]
    notes = manifest["owner_notifications"]
    switches = manifest["kill_switches"]
    # Deployment owns this bundle because later KPI and marketing stages depend
    # on deployment reality. In this slice the deployment is deliberately
    # blocked, and downstream stages become plans/fixtures rather than claims.
    bundle = {
        "schema": "weave/lifecycle-artifact-bundle/v0.1",
        "updated_at": utc_now(),
        "lifecycle_state": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["lifecycle_state"],
            "app_id": app_id,
            "updated_at": utc_now(),
            "current_stage": "deployment",
            "stage_source": "event-ledger",
            "stages": [
                {"stage": "deployment", "status": "blocked", "artifact_refs": ["artifact:launch-deployment-plan-v1"], "proof_refs": ["artifact:launch-ops-manifest-v1"], "claims": ["deployment plan exists"], "non_claims": ["not deployed"]},
                {"stage": "kpi", "status": "deferred", "artifact_refs": ["artifact:launch-kpi-plan-v1"], "proof_refs": ["artifact:launch-ops-manifest-v1"], "claims": ["KPI plan exists"], "non_claims": ["analytics not connected"]},
                {"stage": "marketing", "status": "deferred", "artifact_refs": ["artifact:launch-marketing-plan-v1"], "proof_refs": ["artifact:launch-ops-manifest-v1"], "claims": ["marketing plan exists"], "non_claims": ["no public send"]},
                {"stage": "iteration", "status": "running", "artifact_refs": ["artifact:launch-iteration-plan-v1"], "proof_refs": ["artifact:launch-ops-manifest-v1"], "claims": ["local iteration heartbeat fixtures exist"], "non_claims": ["no production change"]},
            ],
            "attention": {"state": "blocked_on_capability", "summary": "Launch work is blocked on owner-approved capabilities.", "decision_refs": []},
            "approval_boundaries": ["production_deploy_requires_owner_approval", "public_send_requires_owner_approval", "paid_spend_requires_owner_approval", "credential_scope_requires_owner_approval"],
            "capability_gaps": ["deployment provider not connected", "analytics provider not connected", "marketing accounts not connected"],
            "claims": ["launch operations are represented locally"],
            "non_claims": ["no live launch action occurred"],
        },
        "world_model": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["world_model"],
            "app_id": app_id,
            "updated_at": utc_now(),
            "current_stage": "deployment",
            "owner_preferences": {},
            "selected_approach": {"summary": "Keep launch operations local until capabilities are owner-approved.", "source_artifact_refs": ["artifact:launch-ops-manifest-v1"]},
            "plans": {"deployment": "artifact:launch-deployment-plan-v1", "kpi": "artifact:launch-kpi-plan-v1", "marketing": "artifact:launch-marketing-plan-v1", "iteration": "artifact:launch-iteration-plan-v1"},
            "deployment_state": {"status": "blocked_on_capability", "region": snapshot["deployment_region"], "non_claims": ["not deployed"]},
            "kpi_definitions": [
                {"id": "activation-review", "name": "Activation review", "definition": "Owner can review the staged/local proof.", "proof_boundary": "local_deterministic"},
                {"id": "qa-pass-rate", "name": "QA pass rate", "definition": "Share of local QA checks passing before deploy.", "proof_boundary": "local_deterministic"},
                {"id": "owner-decision-latency", "name": "Owner decision latency", "definition": "Time from decision card opened to resolved.", "proof_boundary": "local_deterministic"},
            ],
            "marketing_state": {"status": "draft", "budget": snapshot["marketing_budget"], "non_claims": ["no public campaign has started"]},
            "active_jobs": [{"job_ref": job["job_id"], "status": job["status"], "summary": job["owner_visible_name"]} for job in jobs],
            "known_risks": ["capabilities are deferred", "post-deploy QA cannot run before deployment exists"],
            "approval_boundaries": ["production deploy", "public send", "paid spend", "credential scope"],
            "capability_gaps": ["deployment provider not connected", "analytics provider not connected", "marketing accounts not connected"],
            "proof_boundary": {"highest_proven_surface": "local_deterministic", "proof_refs": ["artifact:launch-ops-manifest-v1"], "non_claims": ["not deployed", "not external-write proof"]},
            "claims": ["world model reflects launch capability gates"],
            "non_claims": ["does not prove live launch operations"],
        },
        "event_ledger": [
            ledger_event("evt-launch-001", app_id, "deployment", "stage.blocked", "Deployment blocked on capability gates.", ["artifact:launch-ops-manifest-v1"]),
            ledger_event("evt-launch-002", app_id, "marketing", "job.created", "Marketing and iteration scheduler fixtures created.", ["artifact:launch-ops-manifest-v1"]),
            ledger_event("evt-launch-003", app_id, "deployment", "proof.recorded", "Launch operations bundle validated locally.", ["artifact:launch-ops-manifest-v1"]),
        ],
        "owner_decision_cards": [],
        "capability_inventory": inv,
        "capability_grants": [
            {"schema": validate_lifecycle_artifacts.SCHEMAS["capability_grant"], "grant_id": "grant-launch-local-001", "capability_id": "repo-worktree", "app_id": app_id, "status": "active", "external_effect": "local_write", "approved_by": "owner", "scope": "write local launch operation artifacts", "public_safe": True}
        ],
        "capability_audit_events": [
            {"schema": validate_lifecycle_artifacts.SCHEMAS["capability_audit_event"], "event_id": "cap-audit-launch-001", "capability_id": "repo-worktree", "grant_id": "grant-launch-local-001", "app_id": app_id, "external_effect": "local_write", "summary": "WEAVE wrote local launch operation artifacts.", "public_safe": True}
        ],
        "recurring_jobs": jobs,
        "job_run_events": [],
        "owner_notifications": notes,
        "kill_switches": switches,
    }
    validate_lifecycle_artifacts.validate_bundle(bundle)
    return bundle


def write_launch_ops(snapshot: dict[str, Any], args: Any) -> dict[str, Any]:
    root = args.weave_root
    app_id = snapshot["app_id"]
    ensure_app(root, snapshot, create_app=args.create_app)
    # Write each stage's plan to its own lifecycle shelf so review can point to
    # the exact stage that owns a decision, instead of hiding launch operations
    # inside one large mixed artifact.
    stage_artifacts = {
        "deployment": write_stage_plan(root, app_id, "deployment", "Deployment Plan", [
            f"region preference: {snapshot['deployment_region']}",
            "deployment provider capability is deferred",
            "post-deploy QA must run after staging or production exists",
        ]),
        "kpi": write_stage_plan(root, app_id, "kpi", "KPI Plan", [
            "track activation review, QA pass rate, and owner decision latency locally",
            "analytics provider remains deferred",
            "production analytics requires owner-approved capability",
        ]),
        "marketing": write_stage_plan(root, app_id, "marketing", "Marketing Plan", [
            "organic drafts are allowed as read-only/local artifacts",
            f"paid budget setting: {snapshot['marketing_budget']}",
            "public send and paid spend require owner approval",
        ]),
        "iteration": write_stage_plan(root, app_id, "iteration", "Iteration Plan", [
            f"feedback source: {snapshot['feedback_source']}",
            "local feedback aggregation can run as local_write",
            "production changes require staged implementation and QA",
        ]),
    }
    now = utc_now()
    jobs = recurring_jobs(snapshot, now)
    manifest = build_manifest(snapshot, stage_artifacts, jobs, now)
    m_path = launch_manifest_path(root, app_id)
    b_path = lifecycle_bundle_path(root, app_id)
    weave_runtime_slice.write_json_artifact(m_path, manifest)
    weave_runtime_slice.write_json_artifact(b_path, build_lifecycle_bundle(snapshot, manifest))
    app = weave_runtime_slice.load_app(root, app_id)
    # Persist the blocked state in app metadata so /apps, /lifecycle, and future
    # TUI surfaces all see the same owner-action-needed condition.
    app["launch_ops"] = {"manifest_path": weave_runtime_slice.relative(m_path, root), "status": "blocked_on_capability", "external_effects_executed": []}
    app["credential_requirements"] = [
        {"id": "deployment-provider", "label": "Deployment provider", "status": "deferred", "stages": ["deployment"], "required": True},
        {"id": "analytics-provider", "label": "Analytics provider", "status": "deferred", "stages": ["kpi"], "required": True},
        {"id": "marketing-accounts", "label": "Marketing accounts", "status": "deferred", "stages": ["marketing"], "required": True},
    ]
    app["current_stage"] = "deployment"
    app["stage_state"] = "blocked"
    app["blockers"] = sorted(set(app.get("blockers", []) + ["launch capabilities deferred"]))
    weave_runtime_slice.write_app(root, app)
    weave_runtime_slice.update_registry_entry(root, app)
    weave_runtime_slice.append_event(root, app_id, weave_runtime_slice.new_event("artifact.created", app_id, "deployment", "Launch operations artifacts written.", payload={"manifest_path": weave_runtime_slice.relative(m_path, root)}, artifact_refs=[{"path": weave_runtime_slice.relative(m_path, root), "stage": "deployment"}]))
    return {"app_id": app_id, "status": "blocked_on_capability", "manifest_path": str(m_path), "bundle_path": str(b_path), "job_count": len(jobs), "external_effects_executed": [], "live_effects": False}


def render_text(snapshot: dict[str, Any], *, write_result: dict[str, Any] | None = None) -> str:
    lines = [
        "+------------------------------------------------------------+",
        "| WEAVE Launch Ops                                           |",
        "| deployment, KPI, marketing, iteration behind gates          |",
        "+------------------------------------------------------------+",
        "",
        "[Plan]",
        f"  app: {snapshot['app_id']}",
        f"  deployment_region: {snapshot['deployment_region']}",
        f"  marketing_budget: {snapshot['marketing_budget']}",
        f"  feedback_source: {snapshot['feedback_source']}",
        "",
        "[Gates]",
        "  deployment_provider: deferred",
        "  analytics_provider: deferred",
        "  marketing_accounts: deferred",
        "  external_effects_executed: none",
    ]
    if write_result:
        lines.extend(["", "[Written]", f"  status: {write_result['status']}", f"  jobs: {write_result['job_count']}", f"  manifest: {write_result['manifest_path']}", f"  lifecycle_bundle: {write_result['bundle_path']}"])
    else:
        lines.extend(["", "[Next]", "  rerun with --write to create local launch operation artifacts"])
    return "\n".join(lines) + "\n"


def run(args: Any, *, output: TextIO = sys.stdout) -> int:
    try:
        snapshot = snapshot_from_args(args)
        # Preview is intentionally pure: no root setup and no app creation unless
        # --write is present. Tests assert this because it is a UX trust boundary.
        write_result = write_launch_ops(snapshot, args) if args.write else None
    except (OSError, ValueError, validate_lifecycle_artifacts.ValidationError, weave_runtime_slice.RuntimeSliceError) as exc:
        print(f"launch-ops failed: {exc}", file=output)
        return 1
    if args.json:
        payload = dict(snapshot)
        if write_result:
            payload["write_result"] = write_result
        print(json.dumps(payload, indent=2, sort_keys=True), file=output)
        return 0
    print(render_text(snapshot, write_result=write_result), end="", file=output)
    return 0
