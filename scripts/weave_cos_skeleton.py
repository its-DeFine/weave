#!/usr/bin/env python3
"""Repo-owned COS WEAVE skeleton for prompt-first first run.

The skeleton is the default vNext product path. It creates public-safe local
state inside the WEAVE repo/workspace, records app lifecycle truth, writes
deterministic procedure prompts, creates worker packets, and produces readback
from files. It does not require hidden orchestration, live worker services,
trackers, credentials, deploys, public sends, billing, or production services.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA = "weave-cos-skeleton/v0.1"
BOOTSTRAP_SCHEMA = "weave-cos-bootstrap/v0.1"
READBACK_SCHEMA = "weave-cos-readback/v0.1"

LIFECYCLE_STAGES: list[tuple[str, str]] = [
    ("intent", "Intent"),
    ("research", "Research"),
    ("selection", "Selection"),
    ("plan", "Plan"),
    ("engineering", "Engineering"),
    ("qa", "QA"),
    ("deployment", "Deployment"),
    ("kpi-setup", "KPI Setup"),
    ("marketing", "Marketing"),
    ("iteration", "Iteration"),
    ("analysis", "Analysis"),
]

BASE_STAGE_SKILLS = [
    "packages/weave-tool/skills/cos-weave/SKILL.md",
    "packages/weave-tool/skills/weave-lifecycle/SKILL.md",
    "packages/weave-tool/skills/evidence-packet/SKILL.md",
]

STAGE_SKILL_REFS: dict[str, list[str]] = {
    "intent": ["packages/weave-tool/skills/compound-engineering/SKILL.md"],
    "research": ["packages/weave-tool/skills/primitive-market-research/SKILL.md"],
    "selection": ["packages/weave-tool/skills/implementation-planning/SKILL.md"],
    "plan": ["packages/weave-tool/skills/implementation-planning/SKILL.md"],
    "engineering": [
        "packages/weave-tool/skills/codebase-orientation/SKILL.md",
        "packages/weave-tool/skills/engineering-execution/SKILL.md",
    ],
    "qa": ["packages/weave-tool/skills/qa-verification/SKILL.md"],
    "deployment": [
        "packages/weave-tool/skills/qa-verification/SKILL.md",
        "packages/weave-tool/skills/security-release-review/SKILL.md",
    ],
    "kpi-setup": ["packages/weave-tool/skills/evidence-packet/SKILL.md"],
    "marketing": ["packages/weave-tool/skills/security-release-review/SKILL.md"],
    "iteration": ["packages/weave-tool/skills/compound-engineering/SKILL.md"],
    "analysis": ["packages/weave-tool/skills/evidence-packet/SKILL.md"],
}

REVIEW_LOOP = ["observe", "validate", "govern", "review", "sync"]

ONBOARDING_QUESTIONS = [
    "What should I call you, if you want the draft owner profile personalized?",
    "What app or application should we work on first?",
    "What outcome would make this first WEAVE session useful?",
    "What constraints or hard gates apply, such as no deploy, no public send, no tracker mutation, no paid calls, or credential restrictions?",
]

SAFE_CONTEXT_CHECKED = [
    "AGENTS.md",
    "docs/COS_WEAVE_BOOTSTRAP.md",
    "docs/COS_WEAVE_REPO_SKELETON.md",
    "packages/weave-tool/skills/cos-weave/SKILL.md",
    "packages/weave-tool/skills/weave-lifecycle/SKILL.md",
    "packages/weave-tool/evals/lifecycle/<stage>.yaml",
    "packages/weave-tool/primitives/registry.json",
    "runs/cos-weave-home/procedures/lifecycle/<stage>.md",
    "runs/cos-weave-home/apps/<app-id>/lifecycle/<stage>/procedure.md",
]

SAFE_CONTEXT_AVOIDED = [
    "raw secrets",
    "raw logs",
    "raw transcripts",
    "cookies",
    "browser sessions",
    "database dumps",
    "broad private data",
]

NON_CLAIMS = [
    "does not prove Codex app-server execution",
    "does not prove live tracker or Linear mutation",
    "does not prove public deployment, billing, or public send",
    "does not prove full lifecycle completion",
    "does not access credentials or secret values",
]

HARD_GATES = [
    "credential_use_requires_owner_approval",
    "public_send_requires_owner_approval",
    "paid_spend_requires_owner_approval",
    "production_deploy_requires_owner_approval",
    "tracker_mutation_requires_owner_approval",
    "live_worker_orchestration_requires_host_support",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip().lower()).strip("-.")
    return slug[:80] or "new-app"


def titleize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_\s]+", value) if part) or "New App"


def clean_app_candidate(value: str) -> str:
    candidate = value.strip()
    candidate = re.split(r"[.;\n]", candidate, maxsplit=1)[0].strip()
    candidate = re.sub(
        r"\b(work locally only|local only|no deploys?|no public sends?|no secrets?)\b.*$",
        "",
        candidate,
        flags=re.IGNORECASE,
    ).strip()
    candidate = re.sub(r"\b(for|with|that|to)\b.*$", "", candidate, flags=re.IGNORECASE).strip()
    return candidate


def stage_index(stage_id: str) -> int:
    for index, (candidate, _label) in enumerate(LIFECYCLE_STAGES):
        if candidate == stage_id:
            return index
    return 0


def stage_skill_refs(stage_id: str) -> list[str]:
    refs = BASE_STAGE_SKILLS + STAGE_SKILL_REFS.get(stage_id, [])
    deduped: list[str] = []
    for ref in refs:
        if ref not in deduped:
            deduped.append(ref)
    return deduped


def stage_contract(stage_id: str, label: str, index: int, app_id: str | None = None) -> dict[str, Any]:
    stage_dir = f"{index:02d}-{stage_id}"
    app_procedure_ref = (
        f"apps/{app_id}/lifecycle/{stage_dir}/procedure.md"
        if app_id
        else f"apps/<app-id>/lifecycle/{stage_dir}/procedure.md"
    )
    return {
        "schema": "weave-stage-entry-contract/v0.1",
        "stage": stage_id,
        "label": label,
        "eval_ref": f"packages/weave-tool/evals/lifecycle/{stage_id}.yaml",
        "home_procedure_ref": f"procedures/lifecycle/{stage_dir}.md",
        "app_procedure_ref": app_procedure_ref,
        "primitive_registry_ref": "packages/weave-tool/primitives/registry.json",
        "primitive_stage": stage_id,
        "skill_refs": stage_skill_refs(stage_id),
        "required_before_action": True,
        "owner_stage_classification_required": False,
        "missing_or_contradictory_contract_state": "REVISE_OR_BLOCKED",
    }


def all_stage_contracts(app_id: str | None = None) -> list[dict[str, Any]]:
    return [
        stage_contract(stage_id, label, index, app_id=app_id)
        for index, (stage_id, label) in enumerate(LIFECYCLE_STAGES, start=1)
    ]


def verify_stage_contracts(source: Path) -> tuple[list[dict[str, Any]], list[str]]:
    contracts = all_stage_contracts()
    findings: list[str] = []
    primitive_registry = source / "packages/weave-tool/primitives/registry.json"
    primitive_stages: set[str] = set()
    if primitive_registry.exists():
        try:
            payload = json.loads(primitive_registry.read_text(encoding="utf-8"))
            primitives = payload.get("primitives", [])
            if isinstance(primitives, list):
                primitive_stages = {
                    str(item.get("lifecycleStage"))
                    for item in primitives
                    if isinstance(item, dict) and item.get("lifecycleStage")
                }
        except json.JSONDecodeError as exc:
            findings.append(f"packages/weave-tool/primitives/registry.json is not valid JSON: {exc}")
    else:
        findings.append("missing packages/weave-tool/primitives/registry.json")

    for contract in contracts:
        eval_ref = str(contract["eval_ref"])
        if not (source / eval_ref).exists():
            findings.append(f"missing {eval_ref}")
        stage = str(contract["stage"])
        if stage not in primitive_stages:
            findings.append(f"missing primitive registry entry for lifecycle stage {stage}")
        for skill_ref in contract["skill_refs"]:
            if not (source / str(skill_ref)).exists():
                findings.append(f"missing {skill_ref}")
    return contracts, findings


def infer_requested_stage(intent: str) -> str:
    text = intent.lower()
    if re.search(r"\b(deploy|ship|release|publish live|production)\b", text):
        return "deployment"
    if re.search(r"\b(kpi|metric|analytics|measure)\b", text):
        return "kpi-setup"
    if re.search(r"\b(marketing|launch campaign|social|gtm)\b", text):
        return "marketing"
    if re.search(r"\b(iterate|improve|revise)\b", text):
        return "iteration"
    if re.search(r"\b(analy[sz]e|analysis|report)\b", text):
        return "analysis"
    if re.search(r"\b(test|qa|verify|validate)\b", text):
        return "qa"
    if re.search(r"\b(code|implement|build|make|create)\b", text):
        return "engineering"
    if re.search(r"\b(plan|architecture|design)\b", text):
        return "plan"
    if re.search(r"\b(research|compare|investigate)\b", text):
        return "research"
    return "intent"


def infer_app_name(intent: str, app_id: str | None = None, app_name: str | None = None) -> tuple[str, str]:
    if app_id:
        clean = slugify(app_id)
        return clean, app_name or titleize(clean)
    if app_name:
        return slugify(app_name), app_name

    text = intent.strip()
    match = re.search(
        r"\b(?:build|create|make|start)\s+(?:a|an|the)?\s*([^.;,\n]+)",
        text,
        flags=re.IGNORECASE,
    )
    candidate = match.group(1).strip() if match else ""
    candidate = clean_app_candidate(candidate)
    if not candidate or candidate.lower() in {"something", "app", "application", "a simple local app", "simple local app"}:
        candidate = "simple local app" if "simple local app" in text.lower() else "new app"
    return slugify(candidate), titleize(candidate)


def infer_apps(intent: str, app_id: str | None = None, app_name: str | None = None) -> list[tuple[str, str]]:
    if app_id or app_name:
        return [infer_app_name(intent, app_id=app_id, app_name=app_name)]

    text = intent.strip()
    tail = text.split(":", 1)[1] if ":" in text else text
    if re.search(r"\b(two|2|multiple|several)\s+app ideas?\b", text, re.IGNORECASE) or ":" in text:
        pieces = re.split(r"\s*(?:,|;|\band\b|\n)\s*", tail)
        apps: list[tuple[str, str]] = []
        for piece in pieces:
            cleaned = re.sub(r"^(?:and\s+)?(?:a|an|the|one is|second is|another)\s+", "", piece.strip(), flags=re.IGNORECASE)
            cleaned = clean_app_candidate(cleaned)
            if not cleaned or cleaned.lower() in {"i have two app ideas", "two app ideas"}:
                continue
            if re.search(r"\b(app|tool|calculator|tracker|planner|site|dashboard)\b", cleaned, re.IGNORECASE):
                apps.append((slugify(cleaned), titleize(cleaned)))
        if len(apps) >= 2:
            deduped: list[tuple[str, str]] = []
            seen: set[str] = set()
            for candidate_id, candidate_name in apps:
                if candidate_id in seen:
                    continue
                seen.add(candidate_id)
                deduped.append((candidate_id, candidate_name))
            return deduped

    return [infer_app_name(intent)]


def missing_gates_for(requested_stage: str) -> list[str]:
    requested_index = stage_index(requested_stage)
    if requested_index <= 0:
        return [
            "app purpose and target user",
            "desired outcome",
            "acceptance checks",
            "constraints and hard gates",
        ]
    gates = []
    for stage_id, label in LIFECYCLE_STAGES[:requested_index]:
        gates.append(f"{label} gate is not complete")
    return gates


def intent_truth_record(app_id: str, app_name: str, intent: str, requested_stage: str, missing_gates: list[str]) -> dict[str, Any]:
    not_required = []
    for stage_id, label in LIFECYCLE_STAGES:
        if stage_id == "intent":
            continue
        not_required.append(
            {
                "stage": stage_id,
                "label": label,
                "reason": "not required until owner intent, acceptance checks, and hard gates are recorded",
            }
        )
    return {
        "schema": "weave-intent-truth/v0.1",
        "app_id": app_id,
        "app_name": app_name,
        "state": "partial",
        "intent_frame": {
            "user_goal": intent,
            "best_current_case": "multi_app_intake" if len(infer_apps(intent)) > 1 else "intent_discovery",
            "case_confidence": "medium_for_app_names_low_for_product_details",
            "target_outcome": "create local WEAVE app state and identify missing owner context before worker dispatch",
        },
        "scope_lattice": {
            "active_slice": "local_file_skeleton_intake",
            "required_stages": ["intent"],
            "not_required_stages": not_required,
            "full_lifecycle_claim": False,
        },
        "completion_contract": {
            "allowed_done_state": "ACCEPT_FOR_SCOPE",
            "controller_review_required": True,
            "missing_gates": missing_gates,
            "proof_required": "local skeleton files and proof envelope only",
        },
        "owner_boundary": {
            "mode": "local_files_only",
            "forbidden_without_separate_approval": HARD_GATES,
        },
        "non_claims": NON_CLAIMS,
    }


def lifecycle_rows(current_stage: str, requested_stage: str, app_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current_index = stage_index(current_stage)
    requested_index = stage_index(requested_stage)
    for index, (stage_id, label) in enumerate(LIFECYCLE_STAGES, start=1):
        zero_index = index - 1
        if zero_index < current_index:
            state = "complete"
        elif zero_index == current_index:
            state = "active"
        elif zero_index <= requested_index:
            state = "blocked_by_prior_gates"
        else:
            state = "not_started"
        rows.append(
            {
                "stage": stage_id,
                "label": label,
                "state": state,
                "procedure_ref": f"procedures/lifecycle/{index:02d}-{stage_id}.md",
                "app_procedure_ref": f"apps/{app_id}/lifecycle/{index:02d}-{stage_id}/procedure.md",
                "stage_entry_contract": stage_contract(stage_id, label, index, app_id=app_id),
                "proof_state": "missing" if state in {"active", "blocked_by_prior_gates"} else "not_required_yet",
            }
        )
    return rows


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event_key = (payload.get("event"), payload.get("app_id"), payload.get("intent"))
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (existing.get("event"), existing.get("app_id"), existing.get("intent")) == event_key:
                return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def load_json(path: Path, default: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def procedure_text(stage_id: str, label: str, contract: dict[str, Any] | None = None) -> str:
    loop = " -> ".join(REVIEW_LOOP)
    stage_number = stage_index(stage_id) + 1
    contract = contract or stage_contract(stage_id, label, stage_number)
    skills = "\n".join(f"- `{ref}`" for ref in contract["skill_refs"])
    return (
        f"# {label} Procedure\n\n"
        "Use this deterministic procedure after context compaction, model changes, or worker handoff.\n\n"
        "## Stage-Entry Contract\n\n"
        "Before planning or executing this lifecycle stage, infer the active or requested stage from owner intent and app state, then load these contracts:\n\n"
        f"- eval: `{contract['eval_ref']}`\n"
        f"- home procedure: `{contract['home_procedure_ref']}`\n"
        f"- app-local procedure: `{contract['app_procedure_ref']}`\n"
        f"- primitive registry: `{contract['primitive_registry_ref']}` entry where `lifecycleStage` is `{contract['primitive_stage']}`\n"
        "- relevant skills:\n"
        f"{skills}\n\n"
        "Record the consulted contracts in proof and readback. If any contract is missing or contradicts the requested work, return `REVISE` or `BLOCKED` before acting.\n\n"
        "## Inputs\n\n"
        "- current app record\n"
        "- lifecycle-state.json\n"
        "- blockers and proof tray\n"
        "- owner constraints and hard gates\n\n"
        "## Steps\n\n"
        f"1. Observe current `{stage_id}` state, artifacts, blockers, and prior proof.\n"
        "2. Validate the requested claim against lifecycle scope and non-claims.\n"
        "3. Govern hard gates before any external, public, paid, credential, or destructive action.\n"
        "4. Review worker output or local artifacts before accepting completion.\n"
        "5. Sync readback files, proof tray, blockers, and next action.\n\n"
        "## Review Loop\n\n"
        f"`{loop}` is mandatory before a lifecycle step can be accepted.\n\n"
        "## Forbidden Defaults\n\n"
        "- do not claim full lifecycle completion from this stage alone\n"
        "- do not mutate trackers, deploy, send public messages, spend money, or touch credentials without approval\n"
        "- do not require hidden orchestration for default first-run WEAVE behavior\n"
    )


def worker_packet_text(app: dict[str, Any], packet_id: str) -> str:
    loop = " -> ".join(REVIEW_LOOP)
    missing = "\n".join(f"- {item}" for item in app["missing_gates"])
    non_claims = "\n".join(f"- {item}" for item in NON_CLAIMS)
    intent_truth = app["intent_truth"]
    active_contract = stage_contract(
        app["current_stage"],
        titleize(app["current_stage"]),
        stage_index(app["current_stage"]) + 1,
        app_id=app["app_id"],
    )
    contract_refs = [
        active_contract["eval_ref"],
        active_contract["home_procedure_ref"],
        active_contract["app_procedure_ref"],
        f"{active_contract['primitive_registry_ref']}#lifecycleStage={active_contract['primitive_stage']}",
        *active_contract["skill_refs"],
    ]
    contract_refs_text = "\n".join(f"- `{ref}`" for ref in contract_refs)
    return (
        f"# Worker Packet {packet_id}\n\n"
        f"App: {app['name']} (`{app['app_id']}`)\n"
        f"Current lifecycle stage: `{app['current_stage']}`\n"
        f"Requested stage from owner words: `{app['requested_stage']}`\n\n"
        "## Stage-Entry Contract\n\n"
        "Before planning or executing this packet, load the active lifecycle stage contract inferred from owner intent and app state. Consulted contract refs must include:\n\n"
        f"{contract_refs_text}\n\n"
        "If the eval, generated procedure, primitive registry entry, or selected skill files are missing or contradictory, return `REVISE` or `BLOCKED` instead of improvising.\n\n"
        "## Intent Truth Boundary\n\n"
        f"Active slice: `{intent_truth['scope_lattice']['active_slice']}`\n"
        f"Allowed done state: `{intent_truth['completion_contract']['allowed_done_state']}`\n"
        f"Full lifecycle claim: `{intent_truth['scope_lattice']['full_lifecycle_claim']}`\n\n"
        "## Objective\n\n"
        "Prepare the next bounded lifecycle artifact or identify the exact owner input needed. "
        "Launch/pin visible Codex workers when the host supports thread creation. "
        "If no visible worker surface is available, keep this packet local and report that limitation.\n\n"
        "## Missing Gates\n\n"
        f"{missing}\n\n"
        "## Review Loop\n\n"
        f"Worker output must pass `{loop}` before COS WEAVE accepts a lifecycle step.\n\n"
        "## Allowed\n\n"
        "- public-safe repo files\n"
        "- local WEAVE skeleton state\n"
        "- deterministic lifecycle procedure prompts\n"
        "- public documentation and tests\n\n"
        "## Forbidden\n\n"
        "- raw secrets, raw logs, raw transcripts, cookies, browser sessions, or database dumps\n"
        "- live tracker mutation, deploy, public send, billing, paid calls, credentials, or production orchestration without approval\n"
        "- claiming full lifecycle completion from local packet creation\n\n"
        "## Non-Claims\n\n"
        f"{non_claims}\n"
    )


def app_record(app_id: str, app_name: str, intent: str) -> dict[str, Any]:
    requested_stage = infer_requested_stage(intent)
    current_stage = "intent"
    missing_gates = missing_gates_for(requested_stage)
    intent_truth = intent_truth_record(app_id, app_name, intent, requested_stage, missing_gates)
    return {
        "schema": "weave-cos-app/v0.1",
        "app_id": app_id,
        "name": app_name,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "owner_intent": intent,
        "current_stage": current_stage,
        "requested_stage": requested_stage,
        "state": "local_skeleton_ready",
        "scope_truth": {
            "in_scope": [
                "create local WEAVE skeleton app state",
                "record lifecycle truth and missing gates",
                "prepare deterministic procedures and worker packet",
                "ask lightweight onboarding questions",
            ],
            "not_claimed": NON_CLAIMS,
            "missing_gates": missing_gates,
        },
        "intent_truth": intent_truth,
        "missing_gates": missing_gates,
        "tracker": {
            "mode": "local",
            "linear_required": False,
            "message": "Tracker access is optional; local WEAVE task ledger is authoritative until a tracker is connected and approved.",
        },
        "worker_orchestration": {
            "mode": "local_packet_recorded",
            "visible_worker_instruction": "Launch/pin visible Codex workers when the host supports thread creation; otherwise keep local packets and report the limitation.",
        },
        "review_loop": REVIEW_LOOP,
        "non_claims": NON_CLAIMS,
        "next_action": "continue with local planning while collecting lightweight answers for outcome, constraints, and acceptance checks",
    }


def ensure_global_procedures(home: Path) -> list[str]:
    refs: list[str] = []
    for index, (stage_id, label) in enumerate(LIFECYCLE_STAGES, start=1):
        rel = f"procedures/lifecycle/{index:02d}-{stage_id}.md"
        write_text(home / rel, procedure_text(stage_id, label, stage_contract(stage_id, label, index)))
        refs.append(rel)
    return refs


def write_app(home: Path, app: dict[str, Any]) -> dict[str, Any]:
    app_root = home / "apps" / str(app["app_id"])
    packet_id = "WP-0001"
    lifecycle = {
        "schema": "weave-cos-lifecycle/v0.1",
        "app_id": app["app_id"],
        "current_stage": app["current_stage"],
        "requested_stage": app["requested_stage"],
        "updated_at": utc_now(),
        "stages": lifecycle_rows(app["current_stage"], app["requested_stage"], str(app["app_id"])),
        "stage_entry_rule": "infer stage from owner intent and app state, load eval/procedure/primitive/skills before acting, then record consulted contracts in proof/readback",
        "stage_contracts": all_stage_contracts(app_id=str(app["app_id"])),
        "missing_gates": app["missing_gates"] if "missing_gates" in app else app["scope_truth"]["missing_gates"],
        "review_loop": REVIEW_LOOP,
        "non_claims": NON_CLAIMS,
    }
    task = {
        "schema": "weave-cos-task/v0.1",
        "task_id": "TASK-0001",
        "app_id": app["app_id"],
        "state": "local_skeleton_ready",
        "stage": app["current_stage"],
        "objective": "clarify first app intent and acceptance checks",
        "worker_packet_ref": f"apps/{app['app_id']}/tasks/worker-packets/{packet_id}.md",
        "review_loop": REVIEW_LOOP,
    }
    proof = {
        "schema": "weave-proof-envelope/v0.1",
        "app_id": app["app_id"],
        "task_id": task["task_id"],
        "state": "recorded",
        "claim": "COS WEAVE skeleton home and app state were created locally",
        "proof_surface": "TOOL_VERIFIED_LOCAL",
        "artifact_refs": [
            f"apps/{app['app_id']}/app.json",
            f"apps/{app['app_id']}/intent-truth.json",
            f"apps/{app['app_id']}/lifecycle/lifecycle-state.json",
            f"apps/{app['app_id']}/tasks/worker-packets/{packet_id}.md",
        ],
        "consulted_contract_refs": [
            row["stage_entry_contract"]
            for row in lifecycle["stages"]
            if row["stage"] in {app["current_stage"], app["requested_stage"]}
        ],
        "review_loop_state": {
            "observe": "recorded",
            "validate": "pending_owner_context",
            "govern": "hard_gates_recorded",
            "review": "pending",
            "sync": "readback_written",
        },
        "non_claims": NON_CLAIMS,
    }
    blockers = {
        "schema": "weave-cos-blocker-tray/v0.1",
        "app_id": app["app_id"],
        "blockers": [
            {
                "id": "owner-context-needed",
                "state": "open_question",
                "missing": app["scope_truth"]["missing_gates"],
                "next_action": app["next_action"],
            }
        ],
    }
    review_queue = {
        "schema": "weave-cos-review-queue/v0.1",
        "app_id": app["app_id"],
        "items": [
            {
                "id": "review-bootstrap-state",
                "state": "pending_owner_context",
                "loop": REVIEW_LOOP,
                "artifact_refs": proof["artifact_refs"],
                "decision": "not_accepted_as_done",
            }
        ],
    }
    readback = {
        "schema": READBACK_SCHEMA,
        "app_id": app["app_id"],
        "app_name": app["name"],
        "state": app["state"],
        "current_stage": app["current_stage"],
        "requested_stage": app["requested_stage"],
        "consulted_contract_refs": [
            row["stage_entry_contract"]
            for row in lifecycle["stages"]
            if row["stage"] in {app["current_stage"], app["requested_stage"]}
        ],
        "missing_gates": app["scope_truth"]["missing_gates"],
        "blockers": blockers["blockers"],
        "proof_refs": [f"apps/{app['app_id']}/proof/proof-tray.json"],
        "review_refs": [f"apps/{app['app_id']}/review/review-queue.json"],
        "next_action": app["next_action"],
        "non_claims": NON_CLAIMS,
    }

    write_json(app_root / "app.json", app)
    write_text(
        app_root / "intent.md",
        f"# Intent\n\nOwner words:\n\n> {app['owner_intent']}\n\n"
        f"Current lifecycle stage: `{app['current_stage']}`\n"
        f"Requested stage inferred from words: `{app['requested_stage']}`\n\n"
        "This is enough to create local app state. Missing owner profile details are questions, not a hard gate.\n",
    )
    write_json(
        app_root / "intent.json",
        {
            "schema": "weave-cos-intent/v0.1",
            "app_id": app["app_id"],
            "owner_words": app["owner_intent"],
            "intent_truth": app["intent_truth"],
            "current_stage": app["current_stage"],
            "requested_stage": app["requested_stage"],
            "missing_gates": app["scope_truth"]["missing_gates"],
            "non_claims": NON_CLAIMS,
        },
    )
    write_json(app_root / "intent-truth.json", app["intent_truth"])
    write_json(app_root / "lifecycle.json", lifecycle)
    write_json(app_root / "lifecycle" / "lifecycle-state.json", lifecycle)
    for index, (stage_id, label) in enumerate(LIFECYCLE_STAGES, start=1):
        stage_root = app_root / "lifecycle" / f"{index:02d}-{stage_id}"
        contract = stage_contract(stage_id, label, index, app_id=str(app["app_id"]))
        write_text(stage_root / "procedure.md", procedure_text(stage_id, label, contract))
        write_json(
            stage_root / "state.json",
            {
                "schema": "weave-cos-stage-state/v0.1",
                "app_id": app["app_id"],
                "stage": stage_id,
                "state": next(row["state"] for row in lifecycle["stages"] if row["stage"] == stage_id),
                "stage_entry_contract": contract,
                "review_loop": REVIEW_LOOP,
            },
        )
    write_json(app_root / "tasks" / "tasks.json", {"schema": "weave-cos-task-ledger/v0.1", "tasks": [task]})
    write_text(
        app_root / "todos.md",
        "# Todos\n\n"
        "- [ ] Clarify app purpose and target user.\n"
        "- [ ] Define acceptance checks for the first local proof.\n"
        "- [ ] Confirm constraints and hard gates.\n"
        "- [ ] Decide whether a visible worker thread is needed for implementation.\n",
    )
    write_json(app_root / "tasks.json", {"schema": "weave-cos-task-ledger/v0.1", "tasks": [task]})
    write_text(app_root / "tasks" / "worker-packets" / f"{packet_id}.md", worker_packet_text(app, packet_id))
    write_text(app_root / "worker-packets" / f"{packet_id}.md", worker_packet_text(app, packet_id))
    write_json(app_root / "proof" / "proof-tray.json", {"schema": "weave-cos-proof-tray/v0.1", "items": [proof]})
    write_json(app_root / "blockers" / "blocker-tray.json", blockers)
    write_json(app_root / "review" / "review-queue.json", review_queue)
    write_json(app_root / "updates" / "readback.json", readback)
    return readback


def update_registry(home: Path, app: dict[str, Any]) -> dict[str, Any]:
    registry_path = home / "apps" / "registry.json"
    registry = load_json(
        registry_path,
        {
            "schema": "weave-cos-app-registry/v0.1",
            "active_app_id": app["app_id"],
            "apps": [],
        },
    )
    assert isinstance(registry, dict)
    apps = [item for item in registry.get("apps", []) if item.get("app_id") != app["app_id"]]
    apps.append(
        {
            "app_id": app["app_id"],
            "name": app["name"],
            "current_stage": app["current_stage"],
            "state": app["state"],
            "readback_ref": f"apps/{app['app_id']}/updates/readback.json",
        }
    )
    apps.sort(key=lambda item: item["app_id"])
    registry.update({"active_app_id": app["app_id"], "apps": apps, "updated_at": utc_now()})
    write_json(registry_path, registry)
    return registry


def write_global_state(
    home: Path,
    source: Path,
    surface: str,
    registry: dict[str, Any],
    procedure_refs: list[str],
    stage_entry_contracts: list[dict[str, Any]],
    stage_contract_findings: list[str],
) -> None:
    write_json(
        home / "owner-profile.json",
        {
            "schema": "weave-cos-owner-profile/v0.1",
            "state": "draft",
            "assumption": "assumed_for_local_scope",
            "display_name": "owner",
            "partner_behavior": "concise, proof-backed, ask only when needed",
            "hard_gate": False,
            "todo": "Personalize this if useful; local app intake is not blocked on identity.",
        },
    )
    write_text(
        home / "owner-profile.md",
        "# Owner Profile\n\n"
        "State: draft / assumed_for_local_scope.\n\n"
        "Local file-only app intake is allowed without a formal identity ritual. "
        "Missing preferences are normal todos/questions, not a hard blocker.\n",
    )
    write_json(
        home / "state.json",
        {
            "schema": SCHEMA,
            "updated_at": utc_now(),
            "source_repo": str(source),
            "surface": surface,
            "active_app_id": registry["active_app_id"],
            "app_count": len(registry["apps"]),
            "state": "local_skeleton_ready",
            "standard_home": "runs/cos-weave-home",
            "procedure_refs": procedure_refs,
            "stage_entry_rule": "infer stage from owner intent and app state, load eval/procedure/primitive/skills before acting, then record consulted contracts in proof/readback",
            "stage_entry_contracts": stage_entry_contracts,
            "stage_contract_state": "verified" if not stage_contract_findings else "revise",
            "stage_contract_findings": stage_contract_findings,
            "review_loop": REVIEW_LOOP,
            "non_claims": NON_CLAIMS,
        },
    )
    write_text(
        home / "README.md",
        "# COS WEAVE Home\n\n"
        "This repo-owned home stores app registry, app lifecycle records, worker packets, proof, blockers, review queue, updates, and readback.\n\n"
        "WEAVE is one Chief-of-Staff chat for operating applications through lifecycle steps. "
        "No hidden orchestration backend is required for first-run app intake.\n",
    )


def write_global_trays(home: Path, registry: dict[str, Any]) -> None:
    app_refs = [f"apps/{item['app_id']}/updates/readback.json" for item in registry["apps"]]
    write_json(home / "tasks" / "worker-packets.json", {"schema": "weave-cos-worker-packets/v0.1", "app_readback_refs": app_refs})
    write_json(home / "proof" / "tray.json", {"schema": "weave-cos-proof-tray/v0.1", "app_readback_refs": app_refs})
    write_json(home / "blockers" / "tray.json", {"schema": "weave-cos-blocker-tray/v0.1", "app_readback_refs": app_refs})
    write_json(home / "review" / "queue.json", {"schema": "weave-cos-review-queue/v0.1", "app_readback_refs": app_refs, "review_loop": REVIEW_LOOP})
    write_json(home / "inbox" / "review-queue.json", {"schema": "weave-cos-review-inbox/v0.1", "app_readback_refs": app_refs, "review_loop": REVIEW_LOOP})


def state_line(app: dict[str, Any], home: Path) -> str:
    return (
        "WEAVE | "
        f"Home={home} | "
        f"App={app['name']} | "
        f"Stage={titleize(app['current_stage'])} | "
        "Scope=local-file-skeleton | "
        f"State={app['state']} | "
        "Truth=partial | "
        "Proof=local-skeleton | "
        f"Next={app['next_action']}"
    )


def readback(home: Path) -> dict[str, Any]:
    state = load_json(home / "state.json", {})
    registry = load_json(home / "apps" / "registry.json", {"apps": [], "active_app_id": ""})
    assert isinstance(state, dict)
    assert isinstance(registry, dict)
    apps = []
    for item in registry.get("apps", []):
        readback_path = home / str(item["readback_ref"])
        app_readback = load_json(readback_path, {})
        if isinstance(app_readback, dict):
            apps.append(app_readback)
    active_app_id = registry.get("active_app_id", "")
    active = next((app for app in apps if app.get("app_id") == active_app_id), apps[0] if apps else {})
    payload = {
        "schema": READBACK_SCHEMA,
        "home": str(home),
        "state": state.get("state", "local_skeleton_ready"),
        "stage_entry_rule": state.get("stage_entry_rule", ""),
        "stage_entry_contracts": state.get("stage_entry_contracts", []),
        "stage_contract_state": state.get("stage_contract_state", "unknown"),
        "stage_contract_findings": state.get("stage_contract_findings", []),
        "active_app_id": active_app_id,
        "apps": apps,
        "active_app": active,
        "review_loop": REVIEW_LOOP,
        "next_action": active.get("next_action", "answer onboarding questions"),
        "non_claims": NON_CLAIMS,
    }
    write_json(home / "updates" / "readback.json", payload)
    return payload


def bootstrap(
    *,
    source: Path,
    home: Path,
    surface: str,
    intent: str,
    app_id: str | None = None,
    app_name: str | None = None,
) -> dict[str, Any]:
    stage_entry_contracts, stage_contract_findings = verify_stage_contracts(source)
    inferred_apps = infer_apps(intent, app_id=app_id, app_name=app_name)
    procedure_refs = ensure_global_procedures(home)
    app_readbacks: list[dict[str, Any]] = []
    registry: dict[str, Any] = {"schema": "weave-cos-app-registry/v0.1", "active_app_id": "", "apps": []}
    active_app: dict[str, Any] | None = None
    for clean_app_id, clean_app_name in inferred_apps:
        app = app_record(clean_app_id, clean_app_name, intent)
        if active_app is None:
            active_app = app
        app_readbacks.append(write_app(home, app))
        registry = update_registry(home, app)
    assert active_app is not None
    active_app_id = str(registry["active_app_id"])
    active_app = app_record(active_app_id, next(name for app_id_value, name in inferred_apps if app_id_value == active_app_id), intent)
    write_global_state(home, source, surface, registry, procedure_refs, stage_entry_contracts, stage_contract_findings)
    write_global_trays(home, registry)
    append_event(
        home / "updates" / "events.jsonl",
        {
            "schema": "weave-cos-event/v0.1",
            "at": utc_now(),
            "event": "cos_bootstrap.app_recorded",
            "app_id": active_app_id,
            "intent": intent,
            "state": "local_skeleton_ready" if not stage_contract_findings else "revise_stage_entry_contracts",
            "stage_contract_findings": stage_contract_findings,
        },
    )
    full_readback = readback(home)
    payload = {
        "schema": BOOTSTRAP_SCHEMA,
        "state": "ACCEPT_FOR_SCOPE" if not stage_contract_findings else "REVISE",
        "surface": surface,
        "home": str(home),
        "source": str(source),
        "intent": intent,
        "role": "COS WEAVE",
        "role_explanation": "WEAVE is one Chief-of-Staff chat for organizing and executing multiple app/application efforts through lifecycle steps.",
        "state_line": state_line(active_app, home),
        "app_id": active_app_id,
        "app_name": active_app["name"],
        "apps": [{"app_id": item[0], "name": item[1]} for item in inferred_apps],
        "app_count": len(registry["apps"]),
        "app_registry_path": str(home / "apps" / "registry.json"),
        "app_state_path": str(home / "apps" / active_app_id / "app.json"),
        "intent_path": str(home / "apps" / active_app_id / "intent.md"),
        "todos_path": str(home / "apps" / active_app_id / "todos.md"),
        "lifecycle_state_path": str(home / "apps" / active_app_id / "lifecycle.json"),
        "worker_packet_path": str(home / "apps" / active_app_id / "worker-packets" / "WP-0001.md"),
        "proof_path": str(home / "apps" / active_app_id / "proof" / "proof-tray.json"),
        "blocker_tray_path": str(home / "apps" / active_app_id / "blockers" / "blocker-tray.json"),
        "review_queue_path": str(home / "apps" / active_app_id / "review" / "review-queue.json"),
        "owner_profile_path": str(home / "owner-profile.json"),
        "readback_path": str(home / "updates" / "readback.json"),
        "procedure_refs": procedure_refs,
        "stage_entry_rule": "infer stage from owner intent and app state, load eval/procedure/primitive/skills before acting, then record consulted contracts in proof/readback",
        "stage_entry_contracts": stage_entry_contracts,
        "stage_contract_state": "verified" if not stage_contract_findings else "revise",
        "stage_contract_findings": stage_contract_findings,
        "revise_reason": "missing or contradictory stage-entry contracts" if stage_contract_findings else "",
        "inferred_lifecycle_stage": active_app["current_stage"],
        "requested_lifecycle_stage": active_app["requested_stage"],
        "missing_gates": active_app["scope_truth"]["missing_gates"],
        "onboarding_questions": ONBOARDING_QUESTIONS,
        "safe_context_policy": {
            "checked": SAFE_CONTEXT_CHECKED,
            "avoided": SAFE_CONTEXT_AVOIDED,
        },
        "tracker": active_app["tracker"],
        "worker_dispatch": active_app["worker_orchestration"],
        "manual_steps_required": [],
        "manual_queue_commands_required": False,
        "manual_lifecycle_classification_required": False,
        "live_effects": False,
        "readback": full_readback,
        "app_readback": next((item for item in app_readbacks if item["app_id"] == active_app_id), app_readbacks[0]),
        "non_claims": NON_CLAIMS,
    }
    write_json(home / "cos-bootstrap" / "latest.json", payload)
    return payload
