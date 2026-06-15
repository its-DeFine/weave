#!/usr/bin/env python3
"""Deterministic local Intent -> Plan lifecycle runner for WEAVE.

The runner is a product-surface rehearsal, not an autonomous build agent. It
writes reviewable artifacts, conversation turns, evaluator reviews, approvals,
and a validated lifecycle bundle so operators can inspect the early lifecycle
shape before live Hermes or provider credentials are involved.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import validate_lifecycle_artifacts
import weave_runtime_slice


EARLY_LIFECYCLE_SCHEMA = "weave-early-lifecycle/v0.1"
EARLY_STAGES = ("intent", "research", "selection", "plan")
DEFAULT_INTENT = "Build a small local proof app with explicit owner review before any live deployment."
DEFAULT_TARGET_USER = "operator reviewing a local WEAVE product proof"
DEFAULT_DEPLOYMENT_REGION = "global"
DEFAULT_MARKETING_BUDGET = "none"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_public_safe_text(label: str, value: str) -> None:
    if weave_runtime_slice.contains_secret_like_value(value):
        raise ValueError(f"{label} contains secret-looking content")
    if weave_runtime_slice.contains_private_locator(value):
        raise ValueError(f"{label} contains private locator content")


def ensure_public_safe_inputs(snapshot: dict[str, Any]) -> None:
    # Owner-provided text is allowed to shape artifacts, but it must not become a
    # path for leaking tokens, private URLs, host paths, or local topology into a
    # committed/public-safe WEAVE runtime artifact.
    for label, value in (
        ("intent", snapshot["intent"]),
        ("target_user", snapshot["target_user"]),
        ("deployment_region", snapshot["deployment_region"]),
        ("marketing_budget", snapshot["marketing_budget"]),
        ("owner_feedback", snapshot["owner_feedback"]),
    ):
        ensure_public_safe_text(label, str(value))


def root_ready(weave_root: Path) -> bool:
    return (weave_root / "apps" / "registry.json").exists() and (weave_root / "ledger" / "events.jsonl").exists()


def app_exists(weave_root: Path, app_id: str) -> bool:
    return weave_runtime_slice.app_metadata_path(weave_root, app_id).exists()


def snapshot_from_args(args: Any) -> dict[str, Any]:
    clean_app_id = weave_runtime_slice.slugify(args.app_id)
    snapshot = {
        "schema": EARLY_LIFECYCLE_SCHEMA,
        "generated_at": utc_now(),
        "mode": "write" if args.write else "preview",
        "write_requested": bool(args.write),
        "create_app": bool(args.create_app),
        "live_effects": False,
        "secret_value_printed": False,
        "app_id": clean_app_id,
        "app_name": args.app_name,
        "intent": args.intent,
        "target_user": args.target_user,
        "deployment_region": args.deployment_region,
        "marketing_budget": args.marketing_budget,
        "owner_feedback": args.owner_feedback,
        "control_mode": args.control_mode,
        "environment": {
            "runtime_home": str(args.runtime_home),
            "weave_root": str(args.weave_root),
            "root_ready": root_ready(args.weave_root),
            "app_exists": app_exists(args.weave_root, clean_app_id),
        },
        "proof_boundary": {
            "highest_surface": "local_deterministic" if args.write else "none",
            "non_claims": [
                "not live Hermes proof",
                "not public web research",
                "not deployed",
                "not live analytics or marketing proof",
            ],
        },
    }
    ensure_public_safe_inputs(snapshot)
    return snapshot


def foundation_text(title: str, body: str) -> str:
    return f"# {title}\n\nStatus: complete\n\n{body}\n"


def ensure_foundation_context(root: Path, app_id: str, snapshot: dict[str, Any]) -> None:
    base = weave_runtime_slice.app_root(root, app_id)
    # The runtime refuses stage approval until foundation documents are no
    # longer templates. These deterministic files are intentionally narrow:
    # enough to let the local lifecycle gate run, not a claim of full product
    # discovery or live organizational readiness.
    files = {
        root / "artifacts" / "general" / "soul.md": foundation_text(
            "Hermes Soul",
            "Operate with explicit assumptions, owner-reviewable rationale, and hard boundaries around credentials, public sends, and deployments.",
        ),
        root / "artifacts" / "general" / "owner-profile.md": foundation_text(
            "Owner Profile",
            f"Control mode: {snapshot['control_mode']}. Preferred collaboration: ask before consequential lifecycle choices.",
        ),
        base / "context" / "app-context.md": foundation_text(
            "App Context",
            f"Intent: {snapshot['intent']}\n\nTarget user: {snapshot['target_user']}",
        ),
        base / "inventory" / "app-inventory.md": foundation_text(
            "App Inventory",
            "Local WEAVE app workspace with lifecycle artifacts, conversation ledger, evaluation artifacts, and no connected providers.",
        ),
        base / "contract" / "gestaltian-contract.md": foundation_text(
            "Gestaltian Contract",
            "Early lifecycle work must pass Intent, Research, Selection, and Plan gates before Engineering starts.",
        ),
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def stage_artifact_path(root: Path, app_id: str, stage_id: str) -> Path:
    stage = weave_runtime_slice.stage_by_id(stage_id)
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage.directory / "artifacts" / f"early-{stage_id}.md"


def lifecycle_bundle_path(root: Path, app_id: str) -> Path:
    stage = weave_runtime_slice.stage_by_id("plan")
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage.directory / "artifacts" / "early-lifecycle-bundle.json"


def markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def intent_artifact(snapshot: dict[str, Any]) -> str:
    return f"""# Intent Artifact

Status: ready for owner review

## Normalized Intent
{snapshot['intent']}

## Target User
{snapshot['target_user']}

## Success Definition
The owner can recognize the intended product, review the selected proof shape, and see which actions remain gated.

## Boundaries
{markdown_list([
    'No credentials are connected in this local workflow.',
    'No Telegram or public messages are sent.',
    'No deployment is performed.',
    f"Deployment region preference recorded as {snapshot['deployment_region']}.",
])}

## Owner Feedback Loop
The owner can approve the normalized intent, request a rewrite, or add missing constraints before research starts.
"""


def research_artifact(snapshot: dict[str, Any]) -> str:
    return f"""# Research Artifact

Status: ready for owner review

## Research Plan
{markdown_list([
    'Unpack the intent into product, technical, regulatory, deployment, QA, KPI, marketing, iteration, and capability questions.',
    'Separate public-web research needs from local deterministic assumptions.',
    'Identify what evidence would be required before selection.',
])}

## Research Synthesis
This local rehearsal records the research workflow shape and required evidence classes. It does not claim live public-web research was performed.

## Required Evidence Classes
{markdown_list([
    'target-user workflow evidence',
    'domain and competitor evidence',
    'regulatory/deployment-region constraints',
    'technical library/framework options',
    'QA surface requirements for web, backend, CLI, or other product types',
])}

## Sufficiency Gate
Research is sufficient for selection when candidate options are traceable to evidence classes and missing live research is explicitly labeled.
"""


def selection_artifact(snapshot: dict[str, Any]) -> str:
    return f"""# Selection Artifact

Status: ready for owner review

## Candidate Options
1. Local deterministic proof first
   - fastest owner-reviewable path
   - keeps credentials and deployment deferred
2. Hosted staging proof
   - requires deployment provider capability before QA can finish
   - useful after the local proof is coherent
3. Marketing-first smoke test
   - requires public-send approval and channel credentials
   - not appropriate before product intent and QA are coherent

## Selected Option
Local deterministic proof first.

## Rationale
The selected option is the smallest credible proof that can proceed into planning without live credentials, public sends, paid spend, or deployment.

## Owner Feedback Loop
The owner can accept this option, edit it with constraints, or propose a new option before planning starts.
"""


def plan_artifact(snapshot: dict[str, Any]) -> str:
    marketing_lane = "organic-only until budget/capabilities are approved" if snapshot["marketing_budget"] == "none" else f"budget noted as {snapshot['marketing_budget']} but spend remains owner-gated"
    return f"""# Plan Artifact

Status: ready for owner review

## Business Plan
{markdown_list([
    'ship a local deterministic proof before live deployment',
    'keep owner review at each hard boundary',
    f'marketing lane: {marketing_lane}',
])}

## Engineering Plan
{markdown_list([
    'create or reuse a local repo/workspace target during Engineering',
    'record implementation packet, source files, and verification commands',
    'stop for hands-on owner decisions when scope changes materially',
])}

## Deployment Plan
{markdown_list([
    f"deployment region preference: {snapshot['deployment_region']}",
    'domain/provider credentials are deferred to capability broker gates',
    'QA must rerun against staging or production only after deployment exists',
])}

## QA Plan
{markdown_list([
    'adapt QA to product surface: web, backend, CLI, API, worker, or mixed',
    'record deterministic checks and owner-reviewable artifacts',
    'capture screenshots/video only when the product surface makes that meaningful',
])}

## KPI Plan
{markdown_list([
    'define 3-5 starting KPIs before live analytics',
    'separate local counters from production analytics',
    'defer analytics credentials until deployment is real',
])}

## Marketing Plan
{markdown_list([
    'prepare organic channels first',
    'public posts, paid spend, and account actions require explicit approval',
    'convert approved marketing work into recurring jobs only after capability gates pass',
])}

## Iteration Plan
{markdown_list([
    'aggregate feedback, bugs, analytics, and competitor changes',
    'create owner-authorized iteration items',
    'run implementation and QA loops before promoting changes',
])}

## Capability Gaps
{markdown_list([
    'deployment provider not connected',
    'analytics provider not connected',
    'marketing accounts not connected',
    'domain purchase/control not connected',
])}
"""


ARTIFACT_BUILDERS = {
    "intent": intent_artifact,
    "research": research_artifact,
    "selection": selection_artifact,
    "plan": plan_artifact,
}


def write_stage_artifact(root: Path, app_id: str, stage_id: str, snapshot: dict[str, Any]) -> Path:
    path = stage_artifact_path(root, app_id, stage_id)
    text = ARTIFACT_BUILDERS[stage_id](snapshot)
    ensure_public_safe_text(f"{stage_id}_artifact", text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    weave_runtime_slice.append_event(
        root,
        app_id,
        weave_runtime_slice.new_event(
            "artifact.created",
            app_id,
            stage_id,
            f"Early lifecycle {stage_id} artifact written.",
            payload={"artifact_path": weave_runtime_slice.relative(path, root), "live_effects": False},
            artifact_refs=[{"path": weave_runtime_slice.relative(path, root), "stage": stage_id}],
        ),
    )
    return path


def append_ready_turn(root: Path, app_id: str, stage_id: str, artifact_path: Path) -> dict[str, Any]:
    rel = weave_runtime_slice.relative(artifact_path, root)
    # A ready-for-review turn is the runtime-recognized bridge between an
    # artifact existing on disk and a stage gate that can be evaluated. Writing
    # the artifact alone would leave the lifecycle blocked by transcript capture.
    turn = weave_runtime_slice.new_conversation_turn(
        app_id,
        stage_id,
        f"Owner reviewed the local {stage_id} workflow packet.",
        f"WEAVE recorded {stage_id} evidence and is requesting owner review.",
        channel="local-cli",
        created_by="weave-runtime",
        agent_rationale={
            "summary": f"{stage_id} artifact is ready for deterministic local evaluation.",
            "gate_questions": [
                "Is the stage artifact present?",
                "Are non-claims and approval boundaries explicit?",
            ],
            "missing_information": [],
            "decision_basis": [f"{stage_id} artifact written at {rel}"],
            "chain_of_thought_captured": False,
        },
        artifact_refs=[{"path": rel, "action": "created"}],
        state_transition={
            "from_stage": stage_id,
            "from_state": "collecting",
            "to_stage": stage_id,
            "to_state": "ready_for_review",
        },
        next_action=f"Evaluate and approve {stage_id}, then advance if the gate passes.",
    )
    return weave_runtime_slice.append_conversation_turn(root, app_id, turn)


def run_stage(root: Path, app_id: str, stage_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    artifact_path = write_stage_artifact(root, app_id, stage_id, snapshot)
    turn = append_ready_turn(root, app_id, stage_id, artifact_path)
    evaluation = weave_runtime_slice.complete_evaluation_from_latest_artifact(root, app_id, stage_id)
    approval = weave_runtime_slice.approve_stage(root, app_id, stage_id, note=f"local early-lifecycle {stage_id} rehearsal approved")
    if not approval["approved"]:
        raise weave_runtime_slice.RuntimeSliceError(f"{stage_id} approval blocked: {approval['gate']['missing']}")
    advance = weave_runtime_slice.advance_stage(root, app_id, note=f"advance after local {stage_id} approval")
    if not advance["advanced"]:
        raise weave_runtime_slice.RuntimeSliceError(f"{stage_id} advance blocked: {advance.get('error', 'unknown')}")
    return {
        "stage": stage_id,
        "artifact_path": str(artifact_path),
        "artifact_ref": weave_runtime_slice.relative(artifact_path, root),
        "turn_id": turn["turn_id"],
        "evaluation_decision": evaluation["result"]["decision"],
        "approved": approval["approved"],
        "advanced_to": advance["stage"],
    }


def stage_row(stage: str, status: str, *, artifact_refs: list[str], decision_refs: list[str] | None = None) -> dict[str, Any]:
    return {
        "stage": stage,
        "status": status,
        "artifact_refs": artifact_refs,
        "proof_refs": artifact_refs,
        "decision_refs": decision_refs or [],
        "claims": [f"{stage} local deterministic artifact was approved"],
        "non_claims": ["does not prove live external execution"],
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
        "non_claims": ["no live external effect occurred"],
        "requires_owner_review": False,
        "public_safe": True,
    }


def build_lifecycle_bundle(snapshot: dict[str, Any], stage_results: list[dict[str, Any]]) -> dict[str, Any]:
    app_id = snapshot["app_id"]
    now = utc_now()
    artifact_refs = {item["stage"]: [f"artifact:early-{item['stage']}-v1"] for item in stage_results}
    bundle = {
        "schema": "weave/lifecycle-artifact-bundle/v0.1",
        "updated_at": now,
        "lifecycle_state": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["lifecycle_state"],
            "app_id": app_id,
            "updated_at": now,
            "current_stage": "engineering",
            "stage_source": "event-ledger",
            "stages": [
                stage_row("intent", "approved", artifact_refs=artifact_refs["intent"]),
                stage_row("research", "approved", artifact_refs=artifact_refs["research"]),
                stage_row("selection", "approved", artifact_refs=artifact_refs["selection"], decision_refs=["decision-card:selection-option-001"]),
                stage_row("plan", "approved", artifact_refs=artifact_refs["plan"]),
                {
                    "stage": "engineering",
                    "status": "collecting",
                    "artifact_refs": [],
                    "proof_refs": [],
                    "claims": ["engineering can begin from approved plan"],
                    "non_claims": ["no implementation has been done by this workflow"],
                },
            ],
            "attention": {
                "state": "no_attention_needed",
                "summary": "Early lifecycle stages are approved locally; Engineering is the next stage.",
                "decision_refs": [],
            },
            "approval_boundaries": [
                "credential_use_requires_owner_approval",
                "public_send_requires_owner_approval",
                "paid_spend_requires_owner_approval",
                "production_deploy_requires_owner_approval",
            ],
            "capability_gaps": ["deployment provider not connected", "analytics provider not connected", "marketing accounts not connected"],
            "claims": ["Intent, Research, Selection, and Plan passed deterministic local gates"],
            "non_claims": ["not live Hermes proof", "not public-web research proof", "not deployed production proof"],
        },
        "world_model": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["world_model"],
            "app_id": app_id,
            "updated_at": now,
            "current_stage": "engineering",
            "owner_preferences": {
                "control_mode": snapshot["control_mode"],
                "owner_feedback": snapshot["owner_feedback"] or "none",
            },
            "selected_approach": {
                "summary": "Local deterministic proof first, with credentials and deployment deferred behind capability gates.",
                "source_artifact_refs": artifact_refs["selection"],
            },
            "plans": {
                "business": "artifact:early-plan-v1",
                "engineering": "artifact:early-plan-v1",
                "deployment": "artifact:early-plan-v1",
                "qa": "artifact:early-plan-v1",
                "kpi": "artifact:early-plan-v1",
                "marketing": "artifact:early-plan-v1",
                "iteration": "artifact:early-plan-v1",
            },
            "deployment_state": {
                "status": "not_started",
                "region_preference": snapshot["deployment_region"],
                "non_claims": ["deployment provider is not connected"],
            },
            "kpi_definitions": [
                {
                    "id": "owner-review-readiness",
                    "name": "Owner review readiness",
                    "definition": "The owner can inspect the local deterministic product proof before live deployment.",
                    "proof_boundary": "local_deterministic",
                }
            ],
            "marketing_state": {
                "status": "draft",
                "budget": snapshot["marketing_budget"],
                "non_claims": ["no public campaign has started"],
            },
            "active_jobs": [],
            "known_risks": [
                "live public-web research still needs source collection",
                "deployment and analytics credentials are deferred",
            ],
            "approval_boundaries": ["credentials", "production deploy", "public send", "paid spend"],
            "capability_gaps": ["deployment provider not connected", "analytics provider not connected", "marketing accounts not connected"],
            "proof_boundary": {
                "highest_proven_surface": "local_deterministic",
                "proof_refs": ["artifact:early-lifecycle-bundle-v1"],
                "non_claims": ["not live Hermes proof", "not deployed", "not live-market validated"],
            },
            "claims": ["world model reflects approved early lifecycle local workflow"],
            "non_claims": ["does not prove runtime implementation beyond local deterministic stage gates"],
        },
        "event_ledger": [
            ledger_event("evt-early-intent-review-001", app_id, "intent", "stage.review_requested", "Intent review requested from local artifact.", artifact_refs["intent"]),
            ledger_event("evt-early-intent-approved-001", app_id, "intent", "stage.approved", "Intent approved for research.", artifact_refs["intent"]),
            ledger_event("evt-early-research-review-001", app_id, "research", "stage.review_requested", "Research plan and sufficiency review requested.", artifact_refs["research"]),
            ledger_event("evt-early-research-approved-001", app_id, "research", "stage.approved", "Research approved for selection.", artifact_refs["research"]),
            ledger_event("evt-early-selection-decision-001", app_id, "selection", "decision.created", "Selection options were presented.", ["decision-card:selection-option-001"]),
            ledger_event("evt-early-selection-answer-001", app_id, "selection", "decision.answered", "Local deterministic proof first was selected.", ["decision-card:selection-option-001"]),
            ledger_event("evt-early-selection-approved-001", app_id, "selection", "stage.approved", "Selection approved for planning.", artifact_refs["selection"]),
            ledger_event("evt-early-plan-review-001", app_id, "plan", "stage.review_requested", "Business and engineering plan review requested.", artifact_refs["plan"]),
            ledger_event("evt-early-plan-approved-001", app_id, "plan", "stage.approved", "Plan approved for Engineering.", artifact_refs["plan"]),
            ledger_event("evt-early-proof-001", app_id, "plan", "proof.recorded", "Early lifecycle bundle validated locally.", ["artifact:early-lifecycle-bundle-v1"]),
        ],
        "owner_decision_cards": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["owner_decision_card"],
                "decision_id": "selection-option-001",
                "app_id": app_id,
                "stage": "selection",
                "status": "answered",
                "created_at": now,
                "decision_type": "product_direction",
                "question": "Which researched option should proceed into planning?",
                "why_it_matters": "The selected option determines engineering, QA, deployment, KPI, and marketing scope.",
                "options": [
                    {
                        "id": "local-deterministic-proof",
                        "label": "Local deterministic proof first",
                        "description": "Proceed without live credentials, deployment, public sends, or paid spend.",
                        "agent_recommendation": True,
                        "consequences": ["fastest local QA", "keeps external effects gated"],
                    },
                    {
                        "id": "hosted-staging-proof",
                        "label": "Hosted staging proof",
                        "description": "Connect deployment provider earlier.",
                        "agent_recommendation": False,
                        "consequences": ["requires credentials", "broadens QA surface"],
                    },
                ],
                "answer": "local-deterministic-proof",
                "hard_boundary_flags": ["deployment_shape", "credential_scope"],
                "evidence_refs": artifact_refs["selection"],
                "claims": ["selection decision was represented as an answered decision card"],
                "non_claims": ["no live option was executed"],
            }
        ],
        "capability_inventory": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["capability_inventory"],
            "updated_at": now,
            "capabilities": [
                {"id": "local-filesystem", "name": "Local filesystem workspace", "status": "granted", "owner": "weave-runtime", "public_safe": True},
                {"id": "web-research", "name": "Public web research", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "deployment-provider", "name": "Deployment provider", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "analytics-provider", "name": "Analytics provider", "status": "deferred", "owner": "owner", "public_safe": True},
                {"id": "marketing-accounts", "name": "Marketing accounts", "status": "deferred", "owner": "owner", "public_safe": True},
            ],
        },
        "capability_grants": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_grant"],
                "grant_id": "grant-early-local-filesystem-001",
                "capability_id": "local-filesystem",
                "app_id": app_id,
                "status": "active",
                "external_effect": "local_write",
                "approved_by": "owner",
                "scope": "write local early lifecycle artifacts and runtime ledger entries",
                "public_safe": True,
            }
        ],
        "capability_audit_events": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_audit_event"],
                "event_id": "capability-audit-early-lifecycle-001",
                "capability_id": "local-filesystem",
                "grant_id": "grant-early-local-filesystem-001",
                "app_id": app_id,
                "external_effect": "local_write",
                "summary": "WEAVE wrote local Intent, Research, Selection, and Plan workflow artifacts.",
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


def write_bundle(root: Path, app_id: str, snapshot: dict[str, Any], stage_results: list[dict[str, Any]]) -> Path:
    bundle = build_lifecycle_bundle(snapshot, stage_results)
    path = lifecycle_bundle_path(root, app_id)
    weave_runtime_slice.write_json_artifact(path, bundle)
    return path


def write_workflow(snapshot: dict[str, Any], args: Any) -> dict[str, Any]:
    root = args.weave_root
    app_id = snapshot["app_id"]
    if args.create_app:
        weave_runtime_slice.create_app(root, app_id, snapshot["app_name"])
    elif not root_ready(root) or not app_exists(root, app_id):
        raise ValueError("early-lifecycle write requires an existing app; pass --create-app to create local app state")

    app = weave_runtime_slice.load_app(root, app_id)
    current_stage = weave_runtime_slice.normalize_stage_id(app.get("current_stage"), default="intent")
    if current_stage != "intent" or app.get("approved_stages"):
        # Replaying approval/advance over a partially progressed app would blur
        # which artifacts caused the final Engineering state. Keep this first
        # local workflow deterministic until resumable lanes are implemented.
        raise ValueError("early-lifecycle write expects an app at fresh intent stage")

    ensure_foundation_context(root, app_id, snapshot)
    gate = weave_runtime_slice.foundation_gate(root, app_id)
    if not gate["passed"]:
        raise weave_runtime_slice.RuntimeSliceError(f"foundation gate still blocking: {gate['missing'] + gate['incomplete']}")

    stage_results = [run_stage(root, app_id, stage, snapshot) for stage in EARLY_STAGES]
    bundle_path = write_bundle(root, app_id, snapshot, stage_results)
    return {
        "app_id": app_id,
        "stage_results": stage_results,
        "bundle_path": str(bundle_path),
        "bundle_ref": weave_runtime_slice.relative(bundle_path, root),
        "current_stage": weave_runtime_slice.load_app(root, app_id).get("current_stage"),
        "live_effects": False,
    }


def render_text(snapshot: dict[str, Any], *, write_result: dict[str, Any] | None = None) -> str:
    lines = [
        "+------------------------------------------------------------+",
        "| WEAVE Early Lifecycle Runner                               |",
        "| Intent -> Research -> Selection -> Plan                    |",
        "+------------------------------------------------------------+",
        "",
        "[Signal]",
        f"  root_ready: {str(snapshot['environment']['root_ready']).lower()}",
        f"  app_exists: {str(snapshot['environment']['app_exists']).lower()}",
        f"  create_app: {str(snapshot['create_app']).lower()}",
        "",
        "[Inputs]",
        f"  app: {snapshot['app_id']} / {snapshot['app_name']}",
        f"  target_user: {snapshot['target_user']}",
        f"  deployment_region: {snapshot['deployment_region']}",
        f"  marketing_budget: {snapshot['marketing_budget']}",
        "",
        "[Lifecycle]",
        "  intent: normalize and validate owner intent",
        "  research: propose plan, record sufficiency gate",
        "  selection: present options, answer decision card",
        "  plan: business + engineering plan with QA/KPI/marketing/iteration lanes",
        "",
        "[Proof Boundary]",
        "  live_effects: false",
        "  secret_value_printed: false",
        "  non_claims: no live Hermes, no public web research, no deployment, no public sends",
    ]
    if write_result:
        lines.extend(["", "[Written]"])
        for result in write_result["stage_results"]:
            lines.append(f"  {result['stage']}: approved -> {result['advanced_to']} ({result['artifact_ref']})")
        lines.extend(
            [
                f"  lifecycle_bundle: {write_result['bundle_path']}",
                f"  current_stage: {write_result['current_stage']}",
                "  artifact_valid: true",
            ]
        )
    else:
        lines.extend(["", "[Next]", "  rerun with --write --create-app for a fresh local app, or --write for an existing fresh app"])
    return "\n".join(lines) + "\n"


def run(args: Any, *, output: TextIO = sys.stdout) -> int:
    try:
        snapshot = snapshot_from_args(args)
        write_result = write_workflow(snapshot, args) if args.write else None
    except (OSError, ValueError, validate_lifecycle_artifacts.ValidationError, weave_runtime_slice.RuntimeSliceError) as exc:
        print(f"early-lifecycle failed: {exc}", file=output)
        return 1
    if args.json:
        payload = dict(snapshot)
        if write_result:
            payload["write_result"] = write_result
        print(json.dumps(payload, indent=2, sort_keys=True), file=output)
        return 0
    print(render_text(snapshot, write_result=write_result), end="", file=output)
    return 0
