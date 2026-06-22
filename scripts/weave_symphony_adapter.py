#!/usr/bin/env python3
"""Local WEAVE-to-Symphony adapter MVP.

This module is intentionally local-first. It validates public-safe WEAVE work
items, presents them as Symphony-like dispatch items, renders a WEAVE worker
prompt, accepts proof envelopes, and maps the result back to owner-facing WEAVE
state. It does not start Symphony, Codex app-server, Linear, deploys, public
sends, billing, or credential flows.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO


WORK_ITEM_SCHEMA = "weave-work-item/v0.1"
PROOF_ENVELOPE_SCHEMA = "weave-proof-envelope/v0.1"
DISPATCH_SCHEMA = "weave-symphony-dispatch-item/v0.1"

ALLOWED_LIFECYCLE_STAGES = {
    "first_run",
    "owner_profile",
    "create_app",
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
}

DISPATCH_STATES = {
    "queued",
    "running",
    "retrying",
    "blocked",
    "completed",
    "cancelled",
    "stale",
}
ACTIVE_DISPATCH_STATES = {"queued", "running", "retrying", "blocked"}
TERMINAL_DISPATCH_STATES = {"completed", "cancelled", "stale"}

PROOF_STATES = {
    "done",
    "blocked",
    "needs_owner_action",
    "revise",
    "accepted_for_scope",
}
READBACK_STATES = {
    "accepted_for_scope",
    "revise",
    "blocked",
    "needs_owner_action",
    "agent_in_progress",
}
PROOF_SURFACES = {
    "SELF_REPORTED",
    "TOOL_VERIFIED_LOCAL",
    "TARGET_SURFACE_VERIFIED",
    "HUMAN_APPROVED",
    "EXTERNAL_SIDE_EFFECT",
    "SANITIZED_SUMMARY",
    "BLOCKED_PENDING_INPUT",
    "REVIEW_REQUIRED",
}
PUBLIC_GATE_STATES = {
    "not_required",
    "approved",
    "pending_owner_approval",
    "blocked",
    "denied",
}

UNSAFE_ACTION_RE = re.compile(
    r"\b("
    r"deploy|publish|public send|post publicly|billing|payment|paid|"
    r"credential|secret|token|delete|destroy|destructive|production|"
    r"live tracker|linear mutation|merge|push"
    r")\b",
    re.IGNORECASE,
)
OVERCLAIM_RE = re.compile(
    r"\b("
    r"live|deployed|production|published|launched|linear|codex app-server|"
    r"symphony service|billing|payment|revenue|full lifecycle|publicly"
    r")\b",
    re.IGNORECASE,
)
LOOPBACK_HOST_TOKEN = "local" + "host"
PRIVATE_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("local-user-path", re.compile(r"/Users/[A-Za-z0-9_.-]+")),
    ("home-path", re.compile(r"/home/[A-Za-z0-9_.-]+")),
    ("private-ipv4", re.compile(r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168|100\.\d{1,3})\.\d{1,3}\.\d{1,3}\b")),
    ("loopback-host", re.compile(r"\b(?:127\.0\.0\.1|" + LOOPBACK_HOST_TOKEN + r"|host\.docker\.internal)\b", re.IGNORECASE)),
    ("credential-like-token", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|sk-or-v1-[A-Za-z0-9_-]{16,}|sk_live_[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})\b")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)


class AdapterValidationError(ValueError):
    """Raised when an adapter record is invalid."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class AdapterStateError(RuntimeError):
    """Raised when queue state prevents the requested transition."""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any, length: int = 16) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def slugify(value: str, *, max_length: int = 54) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        slug = "work-item"
    return slug[:max_length].strip("-") or "work-item"


def ensure_dict(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def ensure_non_empty_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")


def ensure_non_empty_list(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path} must be a non-empty list")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}[{index}] must be a non-empty string")


def public_safe_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                errors.append(f"{path} contains a non-string key")
                continue
            errors.extend(public_safe_errors(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(public_safe_errors(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for label, pattern in PRIVATE_VALUE_PATTERNS:
            match = pattern.search(value)
            if match:
                errors.append(f"{path} contains {label}: {match.group(0)!r}")
                break
    return errors


def raise_if_errors(errors: list[str]) -> None:
    if errors:
        raise AdapterValidationError(errors)


def validate_public_gate(public_gate: Any, errors: list[str]) -> dict[str, Any]:
    gate = ensure_dict(public_gate, "public_gate", errors)
    if not gate:
        return gate
    if "required" not in gate:
        errors.append("public_gate.required is required")
    elif not isinstance(gate.get("required"), bool):
        errors.append("public_gate.required must be a boolean")
    state = gate.get("state")
    if not isinstance(state, str) or state not in PUBLIC_GATE_STATES:
        errors.append(f"public_gate.state must be one of {sorted(PUBLIC_GATE_STATES)}")
    if gate.get("required") is False and state != "not_required":
        errors.append("public_gate.state must be not_required when public_gate.required is false")
    if gate.get("required") is True and "state" not in gate:
        errors.append("unsafe or gated work must include a public_gate.state")
    if gate.get("required") is True and state == "not_required":
        errors.append("public_gate.state cannot be not_required when public_gate.required is true")
    reason = gate.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("public_gate.reason is required")
    return gate


def validate_work_item(work_item: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    ensure_dict(work_item, "$", errors)
    required = [
        "schema",
        "work_item_id",
        "app_id",
        "lifecycle_stage",
        "intent_truth",
        "owner_boundary",
        "worker_packet",
        "proof_required",
        "allowed_actions",
        "forbidden_actions",
        "public_gate",
        "non_claims",
    ]
    for field in required:
        if field not in work_item:
            errors.append(f"{field} is required")

    if work_item.get("schema") != WORK_ITEM_SCHEMA:
        errors.append(f"schema must be {WORK_ITEM_SCHEMA}")
    for field in ("work_item_id", "app_id", "lifecycle_stage"):
        if field in work_item:
            ensure_non_empty_string(work_item.get(field), field, errors)
    if work_item.get("lifecycle_stage") not in ALLOWED_LIFECYCLE_STAGES:
        errors.append(f"lifecycle_stage must be one of {sorted(ALLOWED_LIFECYCLE_STAGES)}")

    for field in ("intent_truth", "owner_boundary", "worker_packet"):
        if field in work_item:
            ensure_dict(work_item.get(field), field, errors)
            if isinstance(work_item.get(field), dict) and not work_item.get(field):
                errors.append(f"{field} cannot be empty")

    for field in ("proof_required", "allowed_actions", "forbidden_actions", "non_claims"):
        if field in work_item:
            ensure_non_empty_list(work_item.get(field), field, errors)

    gate = validate_public_gate(work_item.get("public_gate"), errors) if "public_gate" in work_item else {}
    unsafe_text = " ".join(
        str(item)
        for field in ("allowed_actions", "worker_packet")
        for item in (
            work_item.get(field, [])
            if isinstance(work_item.get(field), list)
            else [json.dumps(work_item.get(field, {}), sort_keys=True)]
        )
    )
    if UNSAFE_ACTION_RE.search(unsafe_text):
        if not gate.get("required"):
            errors.append("unsafe or external-effect work must set public_gate.required to true")
        if gate.get("state") not in {"approved", "pending_owner_approval", "blocked", "denied"}:
            errors.append("unsafe or gated work must record a non-empty gate state")

    errors.extend(public_safe_errors(work_item))
    raise_if_errors(errors)
    return work_item


def is_work_item_dispatchable(work_item: dict[str, Any]) -> bool:
    validate_work_item(work_item)
    gate = work_item["public_gate"]
    return gate.get("required") is False or gate.get("state") == "approved"


def validate_dispatch_item(dispatch_item: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    ensure_dict(dispatch_item, "$", errors)
    required = [
        "schema",
        "id",
        "identifier",
        "title",
        "description",
        "state",
        "labels",
        "branch_name",
        "url",
        "weave",
    ]
    for field in required:
        if field not in dispatch_item:
            errors.append(f"{field} is required")
    if dispatch_item.get("schema") != DISPATCH_SCHEMA:
        errors.append(f"schema must be {DISPATCH_SCHEMA}")
    for field in ("id", "identifier", "title", "description", "branch_name", "url"):
        if field in dispatch_item:
            ensure_non_empty_string(dispatch_item.get(field), field, errors)
    if dispatch_item.get("state") not in DISPATCH_STATES:
        errors.append(f"state must be one of {sorted(DISPATCH_STATES)}")
    if "labels" in dispatch_item:
        ensure_non_empty_list(dispatch_item.get("labels"), "labels", errors)

    weave = ensure_dict(dispatch_item.get("weave"), "weave", errors)
    for field in ("app_id", "lifecycle_stage", "work_item_id", "proof_required", "non_claims"):
        if field not in weave:
            errors.append(f"weave.{field} is required")
    for field in ("app_id", "lifecycle_stage", "work_item_id"):
        if field in weave:
            ensure_non_empty_string(weave.get(field), f"weave.{field}", errors)
    if weave.get("lifecycle_stage") not in ALLOWED_LIFECYCLE_STAGES:
        errors.append(f"weave.lifecycle_stage must be one of {sorted(ALLOWED_LIFECYCLE_STAGES)}")
    for field in ("proof_required", "non_claims"):
        if field in weave:
            ensure_non_empty_list(weave.get(field), f"weave.{field}", errors)
    for field in ("intent_truth", "owner_boundary", "worker_packet", "public_gate"):
        if field in weave:
            ensure_dict(weave.get(field), f"weave.{field}", errors)

    errors.extend(public_safe_errors(dispatch_item))
    raise_if_errors(errors)
    return dispatch_item


def validate_proof_envelope(
    proof_envelope: dict[str, Any],
    *,
    dispatch_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    ensure_dict(proof_envelope, "$", errors)
    required = [
        "schema",
        "work_item_id",
        "app_id",
        "lifecycle_stage",
        "state",
        "claim",
        "proof_surface",
        "commands",
        "artifacts",
        "non_claims",
        "reviewer",
        "next_action",
    ]
    for field in required:
        if field not in proof_envelope:
            errors.append(f"{field} is required")

    if proof_envelope.get("schema") != PROOF_ENVELOPE_SCHEMA:
        errors.append(f"schema must be {PROOF_ENVELOPE_SCHEMA}")
    for field in ("work_item_id", "app_id", "lifecycle_stage", "state", "claim", "proof_surface", "reviewer", "next_action"):
        if field in proof_envelope:
            ensure_non_empty_string(proof_envelope.get(field), field, errors)
    if proof_envelope.get("lifecycle_stage") not in ALLOWED_LIFECYCLE_STAGES:
        errors.append(f"lifecycle_stage must be one of {sorted(ALLOWED_LIFECYCLE_STAGES)}")
    if proof_envelope.get("state") not in PROOF_STATES:
        errors.append(f"state must be one of {sorted(PROOF_STATES)}")
    if proof_envelope.get("proof_surface") not in PROOF_SURFACES:
        errors.append(f"proof_surface must be one of {sorted(PROOF_SURFACES)}")
    for field in ("commands", "artifacts", "non_claims"):
        if field in proof_envelope:
            ensure_non_empty_list(proof_envelope.get(field), field, errors)

    if proof_envelope.get("state") in {"done", "accepted_for_scope"}:
        if not proof_envelope.get("commands"):
            errors.append("done proof must name at least one command")
        if not proof_envelope.get("artifacts"):
            errors.append("done proof must name at least one artifact")
    if proof_envelope.get("state") in {"blocked", "needs_owner_action"}:
        next_action = str(proof_envelope.get("next_action", "")).strip().lower()
        if next_action in {"none", "n/a", "blocked", "unknown"} or len(next_action) < 12:
            errors.append("blocked proof must name an exact owner action")

    if dispatch_item is not None:
        validate_dispatch_item(dispatch_item)
        weave = dispatch_item["weave"]
        for field in ("work_item_id", "app_id", "lifecycle_stage"):
            if proof_envelope.get(field) != weave.get(field):
                errors.append(f"{field} must match dispatch weave.{field}")
        missing_non_claims = [
            item for item in weave.get("non_claims", []) if item not in proof_envelope.get("non_claims", [])
        ]
        if missing_non_claims:
            errors.append(f"proof envelope must preserve dispatch non_claims: {missing_non_claims}")

    claim = str(proof_envelope.get("claim", ""))
    proof_surface = proof_envelope.get("proof_surface")
    if OVERCLAIM_RE.search(claim) and proof_surface not in {"TARGET_SURFACE_VERIFIED", "EXTERNAL_SIDE_EFFECT", "HUMAN_APPROVED"}:
        errors.append("claim exceeds proof surface; live/public/full-lifecycle claims need target-surface proof")

    errors.extend(public_safe_errors(proof_envelope))
    raise_if_errors(errors)
    return proof_envelope


def infer_lifecycle_stage(intent: str) -> str:
    lowered = intent.lower()
    if re.search(r"\b(qa|test|verify|validation|bug)\b", lowered):
        return "qa"
    if re.search(r"\b(build|implement|code|adapter|script|module|worker|runner|integration)\b", lowered):
        return "engineering"
    if re.search(r"\b(plan|roadmap|design|spec)\b", lowered):
        return "plan"
    if re.search(r"\b(research|compare|investigate|market)\b", lowered):
        return "research"
    if re.search(r"\b(launch|deploy|production)\b", lowered):
        return "deployment"
    if re.search(r"\b(kpi|analytics|metric)\b", lowered):
        return "kpi"
    if re.search(r"\b(marketing|gtm|campaign)\b", lowered):
        return "marketing"
    return "intent"


def work_item_from_intent(
    intent: str,
    *,
    app_id: str,
    work_item_id: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    stage = infer_lifecycle_stage(intent)
    stable_id = work_item_id or f"wi-{slugify(app_id)}-{stable_hash({'app_id': app_id, 'intent': intent}, 10)}"
    target_surface = "local deterministic adapter fixture"
    return {
        "schema": WORK_ITEM_SCHEMA,
        "work_item_id": stable_id,
        "app_id": app_id,
        "title": title or "Local WEAVE adapter work item",
        "lifecycle_stage": stage,
        "intent_truth": {
            "schema": "weave-intent-truth/v0.1",
            "state": "resolved",
            "intent_frame": {
                "user_goal": intent,
                "best_current_case": f"{stage}_slice",
                "case_confidence": "medium_from_local_intent_heuristic",
                "target_outcome": "complete the bounded local slice with proof-envelope readback",
            },
            "scope_lattice": {
                "active_slice": stage,
                "required_stages": [stage],
                "not_required_stages": [
                    {"stage": "deployment", "reason": "local adapter proof does not require production deployment"},
                    {"stage": "marketing", "reason": "local adapter proof does not require public messaging"},
                ],
                "full_lifecycle_claim": False,
            },
            "completion_contract": {
                "allowed_done_state": "DONE_FOR_SCOPE_ONLY",
                "controller_review_required": True,
            },
        },
        "owner_boundary": {
            "allowed_without_owner": [
                "edit repo-local adapter files",
                "write public-safe local queue fixtures",
                "run deterministic local tests",
            ],
            "requires_owner_approval": [
                "public deploy",
                "public send",
                "paid call",
                "credential access",
                "live tracker mutation",
            ],
            "stop_conditions": [
                "missing proof surface",
                "unsafe external effect without approved gate",
                "need for live Symphony or Codex app-server run",
            ],
        },
        "worker_packet": {
            "objective": title or "Complete the local WEAVE adapter slice",
            "target_surface": target_surface,
            "expected_change": "repo-local adapter behavior and proof envelope closeout",
            "acceptance_checks": [
                "validated WorkItem",
                "single dispatch item",
                "WEAVE workflow prompt rendered",
                "valid proof envelope accepted for scope",
                "readback preserves non-claims",
            ],
        },
        "proof_required": [
            "targeted adapter unit tests pass",
            "valid proof envelope references local deterministic commands",
            "readback state is accepted_for_scope only after proof validation",
        ],
        "allowed_actions": [
            "create local queue events",
            "render WEAVE worker prompt",
            "write proof envelope",
            "summarize readback state",
        ],
        "forbidden_actions": [
            "do not start live Symphony",
            "do not start Codex app-server against real work",
            "do not mutate live tracker state",
            "do not deploy, publish, bill, or send public messages",
            "do not access credentials or print secrets",
        ],
        "public_gate": {
            "required": False,
            "state": "not_required",
            "reason": "local deterministic adapter slice only",
        },
        "non_claims": [
            "does not prove live Symphony service execution",
            "does not prove Codex app-server execution",
            "does not prove live tracker mutation",
            "does not prove public deployment, billing, or public send",
        ],
    }


def work_item_to_dispatch_item(work_item: dict[str, Any]) -> dict[str, Any]:
    validate_work_item(work_item)
    if not is_work_item_dispatchable(work_item):
        gate = work_item["public_gate"]
        raise AdapterStateError(f"work item is gated and not dispatchable: {gate.get('state')}")
    identifier = f"WEAVE-{stable_hash(work_item['work_item_id'], 8).upper()}"
    dispatch_id = f"dispatch-{stable_hash({'work_item_id': work_item['work_item_id'], 'schema': DISPATCH_SCHEMA}, 16)}"
    title = str(work_item.get("title") or work_item["worker_packet"].get("objective") or work_item["work_item_id"])
    description = (
        f"WEAVE work item {work_item['work_item_id']} for app {work_item['app_id']} "
        f"at lifecycle stage {work_item['lifecycle_stage']}."
    )
    dispatch_item = {
        "schema": DISPATCH_SCHEMA,
        "id": dispatch_id,
        "identifier": identifier,
        "title": title,
        "description": description,
        "state": "queued",
        "labels": ["weave", f"weave:{work_item['lifecycle_stage']}", "local-adapter"],
        "branch_name": f"codex/weave-{slugify(work_item['work_item_id'])}",
        "url": f"weave://work-items/{slugify(work_item['work_item_id'])}",
        "weave": {
            "app_id": work_item["app_id"],
            "lifecycle_stage": work_item["lifecycle_stage"],
            "work_item_id": work_item["work_item_id"],
            "proof_required": copy.deepcopy(work_item["proof_required"]),
            "non_claims": copy.deepcopy(work_item["non_claims"]),
            "intent_truth": copy.deepcopy(work_item["intent_truth"]),
            "owner_boundary": copy.deepcopy(work_item["owner_boundary"]),
            "worker_packet": copy.deepcopy(work_item["worker_packet"]),
            "allowed_actions": copy.deepcopy(work_item["allowed_actions"]),
            "forbidden_actions": copy.deepcopy(work_item["forbidden_actions"]),
            "public_gate": copy.deepcopy(work_item["public_gate"]),
        },
    }
    validate_dispatch_item(dispatch_item)
    return dispatch_item


def render_workflow_prompt(dispatch_item: dict[str, Any]) -> str:
    validate_dispatch_item(dispatch_item)
    weave = dispatch_item["weave"]
    proof_template = {
        "schema": PROOF_ENVELOPE_SCHEMA,
        "work_item_id": weave["work_item_id"],
        "app_id": weave["app_id"],
        "lifecycle_stage": weave["lifecycle_stage"],
        "state": "done | blocked | needs_owner_action | revise | accepted_for_scope",
        "claim": "bounded claim for this lifecycle slice only",
        "proof_surface": "TOOL_VERIFIED_LOCAL",
        "commands": ["exact local command or check that was run"],
        "artifacts": ["repo-relative or queue-relative artifact reference"],
        "non_claims": weave["non_claims"],
        "reviewer": "local-worker | codex-worker | controller",
        "next_action": "exact next action or controller review request",
    }
    sections = [
        "# WEAVE Worker Workflow",
        "",
        "You are operating as a WEAVE lifecycle worker under the WEAVE Chief of Staff.",
        "Symphony is only the orchestra for workspace/session mechanics. WEAVE owns user intent, lifecycle truth, proof envelopes, owner gates, and readback.",
        "Do not ask the owner to classify lifecycle stages manually. WEAVE already inferred the stage for this dispatch item.",
        "",
        "## Dispatch",
        f"- Dispatch id: `{dispatch_item['id']}`",
        f"- Identifier: `{dispatch_item['identifier']}`",
        f"- State: `{dispatch_item['state']}`",
        f"- App id: `{weave['app_id']}`",
        f"- Work item id: `{weave['work_item_id']}`",
        f"- Lifecycle stage: `{weave['lifecycle_stage']}`",
        "",
        "## Intent Truth",
        "```json",
        json.dumps(weave["intent_truth"], indent=2, sort_keys=True),
        "```",
        "",
        "## Owner Boundary",
        "```json",
        json.dumps(weave["owner_boundary"], indent=2, sort_keys=True),
        "```",
        "",
        "## Worker Packet",
        "```json",
        json.dumps(weave["worker_packet"], indent=2, sort_keys=True),
        "```",
        "",
        "## Allowed Actions",
    ]
    sections.extend(f"- {item}" for item in weave.get("allowed_actions", []))
    sections.extend(["", "## Forbidden Actions"])
    sections.extend(f"- {item}" for item in weave.get("forbidden_actions", []))
    sections.extend(
        [
            "- Do not deploy, publish, bill, send public messages, mutate live trackers, access credentials, or perform destructive work unless the dispatch public gate is approved and the packet explicitly requires it.",
            "",
            "## Public Gate",
            "```json",
            json.dumps(weave["public_gate"], indent=2, sort_keys=True),
            "```",
            "",
            "## Proof Required",
        ]
    )
    sections.extend(f"- {item}" for item in weave["proof_required"])
    sections.extend(["", "## Explicit Non-Claims"])
    sections.extend(f"- {item}" for item in weave["non_claims"])
    sections.extend(
        [
            "",
            "## Stop Conditions",
            "- Stop as `blocked` or `needs_owner_action` if required proof, approval, credentials, live tracker access, deploy permission, billing permission, or public-send permission is missing.",
            "- A completed worker result without a valid proof envelope is `revise`, not done.",
            "- A queue or tracker terminal state is not WEAVE lifecycle completion.",
            "- Never claim live Symphony, Linear, Codex app-server, production, deployment, billing, or public-send proof unless that exact approved surface was exercised and recorded.",
            "",
            "## Required Proof Envelope Closeout",
            "Write a public-safe JSON proof envelope with this shape:",
            "```json",
            json.dumps(proof_template, indent=2, sort_keys=True),
            "```",
            "",
            "Allowed closeout states: `done`, `blocked`, `needs_owner_action`, `revise`, `accepted_for_scope`.",
            "The final WEAVE readback may accept scope only after this proof envelope validates against the dispatch item.",
        ]
    )
    return "\n".join(sections) + "\n"


@dataclass(frozen=True)
class QueueState:
    events: list[dict[str, Any]]
    work_items: dict[str, dict[str, Any]]
    dispatches: dict[str, dict[str, Any]]
    dispatch_by_work_item: dict[str, str]
    proofs_by_work_item: dict[str, dict[str, Any]]
    proof_paths_by_work_item: dict[str, str]


class LocalQueueStore:
    """Append-only local queue that can be replayed after restart."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.events_path = root / "events.jsonl"
        self.proofs_dir = root / "proofs"
        self.prompts_dir = root / "prompts"
        self.workspaces_dir = root / "workspaces"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.proofs_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        if not self.events_path.exists():
            self.events_path.write_text("", encoding="utf-8")

    def events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(self.events_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AdapterStateError(f"invalid queue event at line {line_number}: {exc}") from exc
        return events

    def append_event(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.ensure()
        next_sequence = len(self.events()) + 1
        event = {
            "schema": "weave-symphony-adapter-event/v0.1",
            "sequence": next_sequence,
            "at": utc_now(),
            "event_type": event_type,
            "payload": payload,
        }
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def state(self) -> QueueState:
        events = self.events()
        work_items: dict[str, dict[str, Any]] = {}
        dispatches: dict[str, dict[str, Any]] = {}
        dispatch_by_work_item: dict[str, str] = {}
        proofs_by_work_item: dict[str, dict[str, Any]] = {}
        proof_paths_by_work_item: dict[str, str] = {}

        for event in events:
            event_type = event.get("event_type")
            payload = event.get("payload", {})
            if event_type == "work_item_received":
                work_item = payload["work_item"]
                work_items[work_item["work_item_id"]] = work_item
            elif event_type == "dispatch_created":
                dispatch = payload["dispatch_item"]
                dispatches[dispatch["id"]] = dispatch
                dispatch_by_work_item[dispatch["weave"]["work_item_id"]] = dispatch["id"]
            elif event_type == "dispatch_state_changed":
                dispatch_id = payload["dispatch_id"]
                if dispatch_id in dispatches:
                    dispatches[dispatch_id] = copy.deepcopy(dispatches[dispatch_id])
                    dispatches[dispatch_id]["state"] = payload["state"]
            elif event_type == "proof_envelope_written":
                envelope = payload["proof_envelope"]
                work_item_id = envelope.get("work_item_id")
                if isinstance(work_item_id, str):
                    proofs_by_work_item[work_item_id] = envelope
                    proof_path = payload.get("proof_path")
                    if isinstance(proof_path, str):
                        proof_paths_by_work_item[work_item_id] = proof_path

        return QueueState(
            events=events,
            work_items=work_items,
            dispatches=dispatches,
            dispatch_by_work_item=dispatch_by_work_item,
            proofs_by_work_item=proofs_by_work_item,
            proof_paths_by_work_item=proof_paths_by_work_item,
        )

    def enqueue_work_item(self, work_item: dict[str, Any]) -> dict[str, Any]:
        validate_work_item(work_item)
        current = self.state()
        if work_item["work_item_id"] in current.work_items:
            return current.work_items[work_item["work_item_id"]]
        self.append_event("work_item_received", {"work_item": work_item})
        return work_item

    def dispatch_work_item(self, work_item_id: str) -> dict[str, Any]:
        current = self.state()
        if work_item_id not in current.work_items:
            raise AdapterStateError(f"unknown work item: {work_item_id}")
        existing_dispatch_id = current.dispatch_by_work_item.get(work_item_id)
        if existing_dispatch_id:
            existing = current.dispatches[existing_dispatch_id]
            if existing.get("state") in ACTIVE_DISPATCH_STATES:
                return existing
            if existing.get("state") in TERMINAL_DISPATCH_STATES:
                raise AdapterStateError(f"work item already has terminal dispatch state: {existing.get('state')}")

        work_item = current.work_items[work_item_id]
        if not is_work_item_dispatchable(work_item):
            raise AdapterStateError(f"work item is not dispatchable because public_gate is {work_item['public_gate']['state']}")
        dispatch_item = work_item_to_dispatch_item(work_item)
        self.append_event("dispatch_created", {"dispatch_item": dispatch_item})
        return dispatch_item

    def dispatch_next(self) -> dict[str, Any]:
        current = self.state()
        for work_item_id in current.work_items:
            if work_item_id in current.dispatch_by_work_item:
                dispatch = current.dispatches[current.dispatch_by_work_item[work_item_id]]
                if dispatch.get("state") in ACTIVE_DISPATCH_STATES:
                    return dispatch
                continue
            return self.dispatch_work_item(work_item_id)
        raise AdapterStateError("no dispatchable work item found")

    def mark_dispatch_state(self, dispatch_id: str, state: str) -> dict[str, Any]:
        if state not in DISPATCH_STATES:
            raise AdapterValidationError([f"state must be one of {sorted(DISPATCH_STATES)}"])
        current = self.state()
        if dispatch_id not in current.dispatches:
            raise AdapterStateError(f"unknown dispatch: {dispatch_id}")
        self.append_event("dispatch_state_changed", {"dispatch_id": dispatch_id, "state": state})
        refreshed = self.state()
        return refreshed.dispatches[dispatch_id]

    def dispatch_for(self, *, work_item_id: str | None = None, dispatch_id: str | None = None) -> dict[str, Any]:
        current = self.state()
        if dispatch_id:
            if dispatch_id not in current.dispatches:
                raise AdapterStateError(f"unknown dispatch: {dispatch_id}")
            return current.dispatches[dispatch_id]
        if work_item_id:
            dispatch_id = current.dispatch_by_work_item.get(work_item_id)
            if not dispatch_id:
                raise AdapterStateError(f"work item has no dispatch: {work_item_id}")
            return current.dispatches[dispatch_id]
        return self.dispatch_next()

    def write_prompt(self, dispatch_item: dict[str, Any]) -> Path:
        self.ensure()
        prompt_path = self.prompts_dir / f"{dispatch_item['id']}.WORKFLOW.md"
        prompt_path.write_text(render_workflow_prompt(dispatch_item), encoding="utf-8")
        return prompt_path

    def prepare_worker_workspace(self, dispatch_item: dict[str, Any]) -> dict[str, Path]:
        validate_dispatch_item(dispatch_item)
        self.ensure()
        workspace_path = self.workspaces_dir / dispatch_item["id"]
        workspace_path.mkdir(parents=True, exist_ok=True)
        dispatch_path = workspace_path / "dispatch.json"
        prompt_path = workspace_path / "WORKFLOW.md"
        proof_path = workspace_path / "proof.json"
        dispatch_path.write_text(json.dumps(dispatch_item, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        prompt_path.write_text(render_workflow_prompt(dispatch_item), encoding="utf-8")
        workspace_rel = workspace_path.relative_to(self.root).as_posix()
        self.append_event(
            "worker_workspace_prepared",
            {
                "dispatch_id": dispatch_item["id"],
                "workspace_path": workspace_rel,
                "dispatch_path": f"{workspace_rel}/dispatch.json",
                "prompt_path": f"{workspace_rel}/WORKFLOW.md",
            },
        )
        return {
            "workspace": workspace_path,
            "dispatch": dispatch_path,
            "prompt": prompt_path,
            "proof": proof_path,
        }

    def write_proof_envelope(self, dispatch_item: dict[str, Any], proof_envelope: dict[str, Any]) -> Path:
        self.ensure()
        proof_path = self.proofs_dir / f"{dispatch_item['id']}.proof.json"
        proof_path.write_text(json.dumps(proof_envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        relative_proof_path = proof_path.relative_to(self.root).as_posix()
        self.append_event(
            "proof_envelope_written",
            {
                "dispatch_id": dispatch_item["id"],
                "proof_path": relative_proof_path,
                "proof_envelope": proof_envelope,
            },
        )
        return proof_path


def proof_envelope_for_outcome(dispatch_item: dict[str, Any], outcome: str) -> dict[str, Any]:
    validate_dispatch_item(dispatch_item)
    weave = dispatch_item["weave"]
    base = {
        "schema": PROOF_ENVELOPE_SCHEMA,
        "work_item_id": weave["work_item_id"],
        "app_id": weave["app_id"],
        "lifecycle_stage": weave["lifecycle_stage"],
        "claim": "Local adapter worker completed the bounded WEAVE lifecycle slice for local proof only.",
        "proof_surface": "TOOL_VERIFIED_LOCAL",
        "commands": [
            "python3 -m unittest tests.test_weave_symphony_adapter",
        ],
        "artifacts": [
            f"proofs/{dispatch_item['id']}.proof.json",
            f"prompts/{dispatch_item['id']}.WORKFLOW.md",
        ],
        "non_claims": copy.deepcopy(weave["non_claims"]),
        "reviewer": "fake-worker",
        "next_action": "controller reviews local adapter proof and non-claims",
    }
    if outcome == "done":
        envelope = copy.deepcopy(base)
        envelope["state"] = "done"
        return envelope
    if outcome == "blocked":
        envelope = copy.deepcopy(base)
        envelope["state"] = "blocked"
        envelope["claim"] = "Worker stopped before an external-effect action."
        envelope["proof_surface"] = "BLOCKED_PENDING_INPUT"
        envelope["next_action"] = "Owner must approve the named external-effect gate before worker may continue."
        envelope["artifacts"] = [f"prompts/{dispatch_item['id']}.WORKFLOW.md"]
        return envelope
    if outcome == "incomplete":
        envelope = copy.deepcopy(base)
        envelope["state"] = "done"
        envelope.pop("non_claims")
        envelope["artifacts"] = []
        return envelope
    if outcome == "overclaim":
        envelope = copy.deepcopy(base)
        envelope["state"] = "done"
        envelope["claim"] = "The app is live, deployed, publicly launched, and full lifecycle done."
        return envelope
    raise AdapterValidationError([f"unsupported fake worker outcome: {outcome}"])


def run_fake_worker(
    store: LocalQueueStore,
    *,
    outcome: str = "done",
    work_item_id: str | None = None,
    dispatch_id: str | None = None,
) -> dict[str, Any]:
    dispatch_item = store.dispatch_for(work_item_id=work_item_id, dispatch_id=dispatch_id)
    if dispatch_item["state"] == "queued":
        dispatch_item = store.mark_dispatch_state(dispatch_item["id"], "running")
    store.write_prompt(dispatch_item)
    envelope = proof_envelope_for_outcome(dispatch_item, outcome)
    store.write_proof_envelope(dispatch_item, envelope)
    if outcome == "blocked":
        store.mark_dispatch_state(dispatch_item["id"], "blocked")
    else:
        store.mark_dispatch_state(dispatch_item["id"], "completed")
    return envelope


def execute_local_worker(
    *,
    dispatch_path: Path,
    prompt_path: Path,
    proof_out: Path,
    workspace_rel: str,
) -> dict[str, Any]:
    """Actual deterministic local worker used by the MVP runner.

    The worker consumes the rendered prompt and dispatch file from its workspace,
    checks the WEAVE policy markers it was asked to obey, writes a readback
    artifact, and emits a proof envelope. It is deliberately boring, but it is a
    real process boundary when invoked through ``run_local_worker``.
    """

    dispatch_item = validate_dispatch_item(load_json(dispatch_path))
    prompt = prompt_path.read_text(encoding="utf-8")
    required_prompt_markers = [
        "WEAVE Worker Workflow",
        "Intent Truth",
        "Owner Boundary",
        "Proof Required",
        "Required Proof Envelope Closeout",
        "Do not ask the owner to classify lifecycle stages manually",
        "A completed worker result without a valid proof envelope is `revise`, not done",
    ]
    missing_markers = [marker for marker in required_prompt_markers if marker not in prompt]
    if missing_markers:
        raise AdapterValidationError([f"rendered prompt missing marker: {marker}" for marker in missing_markers])

    weave = dispatch_item["weave"]
    prompt_digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    worker_readback = {
        "schema": "weave-local-worker-readback/v0.1",
        "dispatch_id": dispatch_item["id"],
        "work_item_id": weave["work_item_id"],
        "app_id": weave["app_id"],
        "lifecycle_stage": weave["lifecycle_stage"],
        "prompt_sha256": prompt_digest,
        "checked_markers": required_prompt_markers,
        "accepted_scope": "local deterministic worker execution only",
        "non_claims": copy.deepcopy(weave["non_claims"]),
    }
    readback_path = proof_out.parent / "worker-readback.json"
    readback_path.write_text(json.dumps(worker_readback, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    envelope = {
        "schema": PROOF_ENVELOPE_SCHEMA,
        "work_item_id": weave["work_item_id"],
        "app_id": weave["app_id"],
        "lifecycle_stage": weave["lifecycle_stage"],
        "state": "done",
        "claim": (
            "Local worker process consumed the WEAVE dispatch and rendered prompt, "
            "checked the required policy markers, and wrote a proof envelope for this bounded local slice."
        ),
        "proof_surface": "TOOL_VERIFIED_LOCAL",
        "commands": [
            "python3 scripts/weave_symphony_adapter.py local-worker-execute --dispatch dispatch.json --prompt WORKFLOW.md --proof-out proof.json",
        ],
        "artifacts": [
            f"{workspace_rel}/dispatch.json",
            f"{workspace_rel}/WORKFLOW.md",
            f"{workspace_rel}/worker-readback.json",
            f"{workspace_rel}/proof.json",
        ],
        "non_claims": copy.deepcopy(weave["non_claims"]),
        "reviewer": "local-worker",
        "next_action": "controller reviews local worker proof and non-claims",
    }
    validate_proof_envelope(envelope, dispatch_item=dispatch_item)
    proof_out.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return envelope


def run_local_worker(
    store: LocalQueueStore,
    *,
    work_item_id: str | None = None,
    dispatch_id: str | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    dispatch_item = store.dispatch_for(work_item_id=work_item_id, dispatch_id=dispatch_id)
    if dispatch_item["state"] == "queued":
        dispatch_item = store.mark_dispatch_state(dispatch_item["id"], "running")
    paths = store.prepare_worker_workspace(dispatch_item)
    workspace_rel = paths["workspace"].relative_to(store.root).as_posix()
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "local-worker-execute",
        "--dispatch",
        str(paths["dispatch"].resolve()),
        "--prompt",
        str(paths["prompt"].resolve()),
        "--proof-out",
        str(paths["proof"].resolve()),
        "--workspace-rel",
        workspace_rel,
    ]
    result = subprocess.run(
        command,
        cwd=paths["workspace"],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    stdout_path = paths["workspace"] / "stdout.txt"
    stderr_path = paths["workspace"] / "stderr.txt"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    store.append_event(
        "worker_run_completed",
        {
            "dispatch_id": dispatch_item["id"],
            "worker": "local-worker",
            "exit_code": result.returncode,
            "stdout_path": f"{workspace_rel}/stdout.txt",
            "stderr_path": f"{workspace_rel}/stderr.txt",
        },
    )

    if result.returncode != 0:
        store.mark_dispatch_state(dispatch_item["id"], "completed")
        raise AdapterStateError(f"local worker failed with exit code {result.returncode}")
    if not paths["proof"].exists():
        store.mark_dispatch_state(dispatch_item["id"], "completed")
        raise AdapterStateError("local worker did not write proof.json")

    envelope = load_json(paths["proof"])
    try:
        validate_proof_envelope(envelope, dispatch_item=dispatch_item)
    except AdapterValidationError:
        store.write_proof_envelope(dispatch_item, envelope)
        store.mark_dispatch_state(dispatch_item["id"], "completed")
        raise

    store.write_proof_envelope(dispatch_item, envelope)
    if envelope["state"] == "blocked":
        store.mark_dispatch_state(dispatch_item["id"], "blocked")
    else:
        store.mark_dispatch_state(dispatch_item["id"], "completed")
    return envelope


def readback_for_dispatch(
    dispatch_item: dict[str, Any],
    *,
    proof_envelope: dict[str, Any] | None = None,
    proof_path: str | None = None,
) -> dict[str, Any]:
    validate_dispatch_item(dispatch_item)
    weave = dispatch_item["weave"]
    base = {
        "schema": "weave-symphony-readback/v0.1",
        "app_id": weave["app_id"],
        "work_item_id": weave["work_item_id"],
        "dispatch_id": dispatch_item["id"],
        "lifecycle_stage": weave["lifecycle_stage"],
        "dispatch_state": dispatch_item["state"],
        "state": "agent_in_progress",
        "proof_state": "missing",
        "claim": "",
        "proof_path": proof_path or "",
        "next_action": "worker is still running or queued",
        "non_claims": copy.deepcopy(weave["non_claims"]),
        "validation_errors": [],
    }

    if proof_envelope is None:
        if dispatch_item["state"] in ACTIVE_DISPATCH_STATES:
            return base
        base["state"] = "revise"
        base["next_action"] = "worker reached terminal queue state without a valid proof envelope"
        return base

    try:
        validate_proof_envelope(proof_envelope, dispatch_item=dispatch_item)
    except AdapterValidationError as exc:
        base["state"] = "revise"
        base["proof_state"] = "invalid"
        base["claim"] = str(proof_envelope.get("claim", ""))
        base["next_action"] = "revise worker closeout until proof envelope validates"
        base["validation_errors"] = exc.errors
        if isinstance(proof_envelope.get("non_claims"), list):
            base["non_claims"] = proof_envelope["non_claims"]
        return base

    base["proof_state"] = "valid"
    base["claim"] = proof_envelope["claim"]
    base["non_claims"] = proof_envelope["non_claims"]
    base["next_action"] = proof_envelope["next_action"]
    if proof_envelope["state"] in {"done", "accepted_for_scope"}:
        base["state"] = "accepted_for_scope"
    elif proof_envelope["state"] == "needs_owner_action":
        base["state"] = "needs_owner_action"
    elif proof_envelope["state"] == "blocked":
        base["state"] = "blocked"
    else:
        base["state"] = "revise"
    return base


def readback_from_store(
    store: LocalQueueStore,
    *,
    work_item_id: str | None = None,
    dispatch_id: str | None = None,
) -> dict[str, Any]:
    dispatch_item = store.dispatch_for(work_item_id=work_item_id, dispatch_id=dispatch_id)
    current = store.state()
    work_item = dispatch_item["weave"]["work_item_id"]
    return readback_for_dispatch(
        dispatch_item,
        proof_envelope=current.proofs_by_work_item.get(work_item),
        proof_path=current.proof_paths_by_work_item.get(work_item),
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdapterValidationError([f"{path}: invalid JSON: {exc}"]) from exc
    if not isinstance(value, dict):
        raise AdapterValidationError([f"{path}: top-level JSON must be an object"])
    return value


def write_json_or_print(value: dict[str, Any], output_path: Path | None, output: TextIO) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    else:
        output.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local WEAVE-to-Symphony adapter MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    from_intent = subparsers.add_parser("from-intent", help="Create a WorkItem from ordinary intent")
    from_intent.add_argument("--intent", required=True)
    from_intent.add_argument("--app-id", required=True)
    from_intent.add_argument("--work-item-id")
    from_intent.add_argument("--title")
    from_intent.add_argument("--output", type=Path)

    validate = subparsers.add_parser("validate", help="Validate an adapter JSON record")
    validate.add_argument("path", type=Path)
    validate.add_argument("--kind", choices=["work-item", "dispatch-item", "proof-envelope"], required=True)
    validate.add_argument("--dispatch", type=Path, help="Dispatch context for proof-envelope validation")

    enqueue = subparsers.add_parser("enqueue", help="Append a WorkItem to the local queue")
    enqueue.add_argument("--queue-root", type=Path, required=True)
    enqueue.add_argument("--work-item", type=Path, required=True)

    dispatch_next = subparsers.add_parser("dispatch-next", help="Create or replay the next dispatch item")
    dispatch_next.add_argument("--queue-root", type=Path, required=True)

    render = subparsers.add_parser("render-prompt", help="Render the WEAVE worker prompt")
    render.add_argument("--queue-root", type=Path, required=True)
    render.add_argument("--work-item-id")
    render.add_argument("--dispatch-id")
    render.add_argument("--output", type=Path)

    local_worker = subparsers.add_parser("run-local-worker", help="Run the actual deterministic local worker process")
    local_worker.add_argument("--queue-root", type=Path, required=True)
    local_worker.add_argument("--work-item-id")
    local_worker.add_argument("--dispatch-id")
    local_worker.add_argument("--timeout-seconds", type=int, default=30)

    worker_execute = subparsers.add_parser("local-worker-execute", help="Worker entrypoint used by run-local-worker")
    worker_execute.add_argument("--dispatch", type=Path, required=True)
    worker_execute.add_argument("--prompt", type=Path, required=True)
    worker_execute.add_argument("--proof-out", type=Path, required=True)
    worker_execute.add_argument("--workspace-rel", required=True)

    fake = subparsers.add_parser("fake-worker", help="Run the adversarial simulated worker")
    fake.add_argument("--queue-root", type=Path, required=True)
    fake.add_argument("--work-item-id")
    fake.add_argument("--dispatch-id")
    fake.add_argument("--outcome", choices=["done", "blocked", "incomplete", "overclaim"], default="done")

    readback = subparsers.add_parser("readback", help="Map dispatch plus proof state into WEAVE readback")
    readback.add_argument("--queue-root", type=Path, required=True)
    readback.add_argument("--work-item-id")
    readback.add_argument("--dispatch-id")

    return parser


def main(argv: list[str] | None = None, *, output: TextIO = sys.stdout, error: TextIO = sys.stderr) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "from-intent":
            work_item = work_item_from_intent(
                args.intent,
                app_id=args.app_id,
                work_item_id=args.work_item_id,
                title=args.title,
            )
            validate_work_item(work_item)
            write_json_or_print(work_item, args.output, output)
            return 0
        if args.command == "validate":
            record = load_json(args.path)
            if args.kind == "work-item":
                validate_work_item(record)
            elif args.kind == "dispatch-item":
                validate_dispatch_item(record)
            else:
                dispatch_item = load_json(args.dispatch) if args.dispatch else None
                validate_proof_envelope(record, dispatch_item=dispatch_item)
            output.write("ok\n")
            return 0
        if args.command == "enqueue":
            store = LocalQueueStore(args.queue_root)
            work_item = load_json(args.work_item)
            store.enqueue_work_item(work_item)
            write_json_or_print(work_item, None, output)
            return 0
        if args.command == "dispatch-next":
            store = LocalQueueStore(args.queue_root)
            dispatch_item = store.dispatch_next()
            write_json_or_print(dispatch_item, None, output)
            return 0
        if args.command == "render-prompt":
            store = LocalQueueStore(args.queue_root)
            dispatch_item = store.dispatch_for(work_item_id=args.work_item_id, dispatch_id=args.dispatch_id)
            prompt = render_workflow_prompt(dispatch_item)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(prompt, encoding="utf-8")
            else:
                output.write(prompt)
            return 0
        if args.command == "run-local-worker":
            store = LocalQueueStore(args.queue_root)
            envelope = run_local_worker(
                store,
                work_item_id=args.work_item_id,
                dispatch_id=args.dispatch_id,
                timeout_seconds=args.timeout_seconds,
            )
            write_json_or_print(envelope, None, output)
            return 0
        if args.command == "local-worker-execute":
            envelope = execute_local_worker(
                dispatch_path=args.dispatch,
                prompt_path=args.prompt,
                proof_out=args.proof_out,
                workspace_rel=args.workspace_rel,
            )
            write_json_or_print(envelope, None, output)
            return 0
        if args.command == "fake-worker":
            store = LocalQueueStore(args.queue_root)
            envelope = run_fake_worker(
                store,
                outcome=args.outcome,
                work_item_id=args.work_item_id,
                dispatch_id=args.dispatch_id,
            )
            write_json_or_print(envelope, None, output)
            return 0
        if args.command == "readback":
            store = LocalQueueStore(args.queue_root)
            readback = readback_from_store(store, work_item_id=args.work_item_id, dispatch_id=args.dispatch_id)
            write_json_or_print(readback, None, output)
            return 0
    except (AdapterValidationError, AdapterStateError) as exc:
        error.write(f"error: {exc}\n")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
