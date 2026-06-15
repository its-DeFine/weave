#!/usr/bin/env python3
"""Validate a WEAVE lifecycle artifact bundle.

The validator is intentionally stdlib-only. The JSON Schema files are the public
contract, while this script enforces the cross-object invariants that matter for
local deterministic fixtures and early implementation work.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMAS = {
    "lifecycle_state": "weave/lifecycle-state/v0.1",
    "world_model": "weave/world-model/v0.1",
    "event_ledger_entry": "weave/event-ledger-entry/v0.1",
    "owner_decision_card": "weave/owner-decision-card/v0.1",
    "capability_inventory": "weave/capability-inventory/v0.1",
    "capability_grant": "weave/capability-grant/v0.1",
    "capability_audit_event": "weave/capability-audit-event/v0.1",
    "recurring_job": "weave/recurring-job/v0.1",
    "job_run_event": "weave/job-run-event/v0.1",
    "owner_notification": "weave/owner-notification/v0.1",
    "kill_switch": "weave/kill-switch/v0.1",
}

STAGES = {
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
STAGE_STATUSES = {
    "not_started",
    "collecting",
    "drafting",
    "review",
    "revision_requested",
    "approved",
    "running",
    "owner_input_needed",
    "blocked",
    "ready_for_review",
    "completed",
    "deferred",
}
ATTENTION_STATES = {
    "no_attention_needed",
    "agent_working",
    "owner_input_needed",
    "blocked_on_capability",
    "ready_for_review",
}
EVENT_TYPES = {
    "stage.entered",
    "stage.artifact_created",
    "stage.review_requested",
    "stage.revision_requested",
    "stage.approved",
    "stage.blocked",
    "decision.created",
    "decision.answered",
    "decision.deferred",
    "world_model.updated",
    "proof.recorded",
    "non_claim.recorded",
    "capability.requested",
    "capability.deferred",
    "job.created",
    "job.paused",
    "job.cancelled",
}
CAPABILITY_STATUSES = {
    "unavailable",
    "available_unconnected",
    "connection_requested",
    "connected",
    "owner_provided",
    "agent_created_pending_owner",
    "granted",
    "suspended",
    "revoked",
    "deferred",
    "failed",
}
GRANT_STATUSES = {"requested", "active", "denied", "suspended", "revoked", "expired", "used", "failed"}
JOB_TYPES = {
    "marketing_engagement",
    "feedback_intake",
    "competitor_scan",
    "staged_implementation",
    "feature_recommendation",
    "analytics_review",
    "owner_followup",
    "capability_health_check",
}
JOB_STATUSES = {
    "draft",
    "pending_owner_approval",
    "active",
    "paused",
    "blocked",
    "kill_switched",
    "completed",
    "cancelled",
    "failed",
}
RUN_RESULTS = {"started", "succeeded", "blocked", "failed", "skipped", "cancelled", "timed_out", "needs_owner"}
EXTERNAL_EFFECTS = {
    "none",
    "read_only",
    "local_write",
    "staging_write",
    "production_write",
    "public_send",
    "paid_spend",
    "credential_scope_change",
    "destructive_change",
}
HIGH_RISK_EFFECTS = {"production_write", "public_send", "paid_spend", "credential_scope_change", "destructive_change"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
APP_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SECRET_REF_RE = re.compile(r"^secret_ref:[a-z0-9][a-z0-9_.:-]*$")


class ValidationError(Exception):
    """Raised when a lifecycle artifact bundle cannot be trusted by WEAVE."""


def ensure_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def ensure_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be a list")
    return value


def ensure_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a non-empty string")
    return value


def ensure_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{label} must be a boolean")
    return value


def ensure_schema(obj: dict[str, Any], schema: str, label: str) -> None:
    if obj.get("schema") != schema:
        raise ValidationError(f"{label}: schema must be {schema}")


def ensure_enum(value: Any, allowed: set[str], label: str) -> str:
    text = ensure_string(value, label)
    if text not in allowed:
        raise ValidationError(f"{label}: invalid value {text}")
    return text


def ensure_id(value: Any, label: str, *, app_id: bool = False) -> str:
    text = ensure_string(value, label)
    pattern = APP_ID_RE if app_id else ID_RE
    if not pattern.fullmatch(text):
        raise ValidationError(f"{label}: invalid id {text}")
    return text


def ensure_string_list(value: Any, label: str) -> list[str]:
    output: list[str] = []
    for index, item in enumerate(ensure_list(value, label)):
        output.append(ensure_string(item, f"{label}[{index}]"))
    return output


def optional_string_list(obj: dict[str, Any], key: str, label: str) -> list[str]:
    if key not in obj:
        return []
    return ensure_string_list(obj[key], f"{label}.{key}")


def require_public_safe(obj: dict[str, Any], label: str) -> None:
    if "public_safe" in obj:
        ensure_bool(obj["public_safe"], f"{label}.public_safe")
        if obj["public_safe"] is not True:
            raise ValidationError(f"{label}: public_safe must be true")


def validate_lifecycle_state(state: dict[str, Any]) -> tuple[str, set[str], set[str]]:
    ensure_schema(state, SCHEMAS["lifecycle_state"], "lifecycle_state")
    app_id = ensure_id(state.get("app_id"), "lifecycle_state.app_id", app_id=True)
    current_stage = ensure_enum(state.get("current_stage"), STAGES, "lifecycle_state.current_stage")
    ensure_enum(state.get("stage_source"), {"derived", "event-ledger", "owner-approved", "agent-proposed", "system-imported"}, "lifecycle_state.stage_source")
    stages = ensure_list(state.get("stages"), "lifecycle_state.stages")
    attention = ensure_object(state.get("attention"), "lifecycle_state.attention")
    ensure_enum(attention.get("state"), ATTENTION_STATES, "lifecycle_state.attention.state")

    stage_names: set[str] = set()
    decision_refs: set[str] = set()
    for index, item in enumerate(stages):
        stage = ensure_object(item, f"lifecycle_state.stages[{index}]")
        stage_name = ensure_enum(stage.get("stage"), STAGES, f"lifecycle_state.stages[{index}].stage")
        stage_names.add(stage_name)
        ensure_enum(stage.get("status"), STAGE_STATUSES, f"lifecycle_state.stages[{index}].status")
        decision_refs.update(optional_string_list(stage, "decision_refs", f"lifecycle_state.stages[{index}]"))
        optional_string_list(stage, "claims", f"lifecycle_state.stages[{index}]")
        optional_string_list(stage, "non_claims", f"lifecycle_state.stages[{index}]")

    if current_stage not in stage_names:
        raise ValidationError("lifecycle_state.current_stage must be present in stages")

    decision_refs.update(optional_string_list(attention, "decision_refs", "lifecycle_state.attention"))
    return app_id, stage_names, decision_refs


def validate_world_model(world_model: dict[str, Any], app_id: str) -> None:
    ensure_schema(world_model, SCHEMAS["world_model"], "world_model")
    if ensure_id(world_model.get("app_id"), "world_model.app_id", app_id=True) != app_id:
        raise ValidationError("world_model.app_id must match lifecycle_state.app_id")
    ensure_enum(world_model.get("current_stage"), STAGES, "world_model.current_stage")
    proof_boundary = ensure_object(world_model.get("proof_boundary"), "world_model.proof_boundary")
    ensure_enum(
        proof_boundary.get("highest_proven_surface"),
        {
            "none",
            "spec_only",
            "local_deterministic",
            "local_runtime",
            "container_mesh",
            "live_transport",
            "deployed_staging",
            "deployed_production",
            "external_write_readback",
        },
        "world_model.proof_boundary.highest_proven_surface",
    )
    # A proof boundary without non-claims is too easy to overread as runtime or
    # production proof. Keep the adjacent non-truths first-class in every fixture.
    non_claims = optional_string_list(proof_boundary, "non_claims", "world_model.proof_boundary")
    if not non_claims:
        raise ValidationError("world_model.proof_boundary.non_claims must not be empty")
    optional_string_list(world_model, "approval_boundaries", "world_model")
    optional_string_list(world_model, "capability_gaps", "world_model")


def validate_event_ledger(entries: list[Any], app_id: str) -> set[str]:
    event_ids: set[str] = set()
    for index, value in enumerate(entries):
        entry = ensure_object(value, f"event_ledger[{index}]")
        ensure_schema(entry, SCHEMAS["event_ledger_entry"], f"event_ledger[{index}]")
        event_id = ensure_id(entry.get("event_id"), f"event_ledger[{index}].event_id")
        if event_id in event_ids:
            raise ValidationError(f"event_ledger[{index}]: duplicate event_id {event_id}")
        event_ids.add(event_id)
        if ensure_id(entry.get("app_id"), f"event_ledger[{index}].app_id", app_id=True) != app_id:
            raise ValidationError(f"event_ledger[{index}].app_id must match lifecycle_state.app_id")
        if "stage" in entry:
            ensure_enum(entry["stage"], STAGES, f"event_ledger[{index}].stage")
        ensure_enum(entry.get("event_type"), EVENT_TYPES, f"event_ledger[{index}].event_type")
        ensure_string(entry.get("summary"), f"event_ledger[{index}].summary")
        require_public_safe(entry, f"event_ledger[{index}]")
        optional_string_list(entry, "claims", f"event_ledger[{index}]")
        optional_string_list(entry, "non_claims", f"event_ledger[{index}]")
    return event_ids


def validate_decision_cards(cards: list[Any], app_id: str, lifecycle_decision_refs: set[str]) -> set[str]:
    decision_ids: set[str] = set()
    for index, value in enumerate(cards):
        card = ensure_object(value, f"owner_decision_cards[{index}]")
        ensure_schema(card, SCHEMAS["owner_decision_card"], f"owner_decision_cards[{index}]")
        decision_id = ensure_id(card.get("decision_id"), f"owner_decision_cards[{index}].decision_id")
        if decision_id in decision_ids:
            raise ValidationError(f"owner_decision_cards[{index}]: duplicate decision_id {decision_id}")
        decision_ids.add(decision_id)
        if ensure_id(card.get("app_id"), f"owner_decision_cards[{index}].app_id", app_id=True) != app_id:
            raise ValidationError(f"owner_decision_cards[{index}].app_id must match lifecycle_state.app_id")
        ensure_enum(card.get("stage"), STAGES, f"owner_decision_cards[{index}].stage")
        ensure_enum(card.get("status"), {"open", "answered", "deferred", "blocked", "superseded"}, f"owner_decision_cards[{index}].status")
        ensure_string(card.get("question"), f"owner_decision_cards[{index}].question")
        ensure_string(card.get("why_it_matters"), f"owner_decision_cards[{index}].why_it_matters")
        if not ensure_list(card.get("options"), f"owner_decision_cards[{index}].options"):
            raise ValidationError(f"owner_decision_cards[{index}].options must not be empty")

    # Decision references may be stored as either raw ids or prefixed references
    # in the UI-facing lifecycle state. Normalize both before checking linkage.
    normalized_refs = {ref.removeprefix("decision-card:") for ref in lifecycle_decision_refs}
    missing = sorted(normalized_refs - decision_ids)
    if missing:
        raise ValidationError(f"lifecycle_state references missing decision cards: {', '.join(missing)}")
    return decision_ids


def validate_capabilities(inventory: dict[str, Any], grants: list[Any], audit_events: list[Any], app_id: str) -> set[str]:
    ensure_schema(inventory, SCHEMAS["capability_inventory"], "capability_inventory")
    capability_ids: set[str] = set()
    for index, value in enumerate(ensure_list(inventory.get("capabilities"), "capability_inventory.capabilities")):
        capability = ensure_object(value, f"capability_inventory.capabilities[{index}]")
        capability_id = ensure_id(capability.get("id"), f"capability_inventory.capabilities[{index}].id", app_id=True)
        if capability_id in capability_ids:
            raise ValidationError(f"capability_inventory.capabilities[{index}]: duplicate id {capability_id}")
        capability_ids.add(capability_id)
        ensure_enum(capability.get("status"), CAPABILITY_STATUSES, f"capability_inventory.capabilities[{index}].status")
        if "secret_ref" in capability:
            secret_ref = ensure_string(capability["secret_ref"], f"capability_inventory.capabilities[{index}].secret_ref")
            if not SECRET_REF_RE.fullmatch(secret_ref):
                raise ValidationError(f"capability_inventory.capabilities[{index}].secret_ref must be opaque secret_ref")

    grant_ids: set[str] = set()
    for index, value in enumerate(grants):
        grant = ensure_object(value, f"capability_grants[{index}]")
        ensure_schema(grant, SCHEMAS["capability_grant"], f"capability_grants[{index}]")
        grant_id = ensure_id(grant.get("grant_id"), f"capability_grants[{index}].grant_id")
        grant_ids.add(grant_id)
        capability_id = ensure_id(grant.get("capability_id"), f"capability_grants[{index}].capability_id", app_id=True)
        if capability_id not in capability_ids:
            raise ValidationError(f"capability_grants[{index}].capability_id is not in inventory")
        if ensure_id(grant.get("app_id"), f"capability_grants[{index}].app_id", app_id=True) != app_id:
            raise ValidationError(f"capability_grants[{index}].app_id must match lifecycle_state.app_id")
        ensure_enum(grant.get("status"), GRANT_STATUSES, f"capability_grants[{index}].status")
        effect = ensure_enum(grant.get("external_effect"), EXTERNAL_EFFECTS, f"capability_grants[{index}].external_effect")
        if effect in HIGH_RISK_EFFECTS and grant.get("approved_by") != "owner":
            raise ValidationError(f"capability_grants[{index}]: high-risk external effect requires owner approval")
        require_public_safe(grant, f"capability_grants[{index}]")

    for index, value in enumerate(audit_events):
        event = ensure_object(value, f"capability_audit_events[{index}]")
        ensure_schema(event, SCHEMAS["capability_audit_event"], f"capability_audit_events[{index}]")
        capability_id = ensure_id(event.get("capability_id"), f"capability_audit_events[{index}].capability_id", app_id=True)
        if capability_id not in capability_ids:
            raise ValidationError(f"capability_audit_events[{index}].capability_id is not in inventory")
        if event.get("grant_id") and str(event["grant_id"]) not in grant_ids:
            raise ValidationError(f"capability_audit_events[{index}].grant_id is not in grants")
        if ensure_id(event.get("app_id"), f"capability_audit_events[{index}].app_id", app_id=True) != app_id:
            raise ValidationError(f"capability_audit_events[{index}].app_id must match lifecycle_state.app_id")
        ensure_enum(event.get("external_effect"), EXTERNAL_EFFECTS, f"capability_audit_events[{index}].external_effect")
        require_public_safe(event, f"capability_audit_events[{index}]")
    return capability_ids


def validate_scheduler(
    jobs: list[Any],
    runs: list[Any],
    notifications: list[Any],
    kill_switches: list[Any],
    app_id: str,
) -> None:
    job_ids: set[str] = set()
    for index, value in enumerate(jobs):
        job = ensure_object(value, f"recurring_jobs[{index}]")
        ensure_schema(job, SCHEMAS["recurring_job"], f"recurring_jobs[{index}]")
        job_id = ensure_id(job.get("job_id"), f"recurring_jobs[{index}].job_id")
        job_ids.add(job_id)
        if ensure_id(job.get("app_id"), f"recurring_jobs[{index}].app_id", app_id=True) != app_id:
            raise ValidationError(f"recurring_jobs[{index}].app_id must match lifecycle_state.app_id")
        ensure_enum(job.get("job_type"), JOB_TYPES, f"recurring_jobs[{index}].job_type")
        ensure_enum(job.get("status"), JOB_STATUSES, f"recurring_jobs[{index}].status")
        effect = ensure_enum(job.get("external_effect"), EXTERNAL_EFFECTS, f"recurring_jobs[{index}].external_effect")
        if effect in HIGH_RISK_EFFECTS and not optional_string_list(job, "approval_required_for", f"recurring_jobs[{index}]"):
            raise ValidationError(f"recurring_jobs[{index}]: high-risk external effect requires approval_required_for")
        require_public_safe(job, f"recurring_jobs[{index}]")

    notification_ids: set[str] = set()
    for index, value in enumerate(notifications):
        notification = ensure_object(value, f"owner_notifications[{index}]")
        ensure_schema(notification, SCHEMAS["owner_notification"], f"owner_notifications[{index}]")
        notification_id = ensure_id(notification.get("notification_id"), f"owner_notifications[{index}].notification_id")
        notification_ids.add(notification_id)
        if ensure_id(notification.get("app_id"), f"owner_notifications[{index}].app_id", app_id=True) != app_id:
            raise ValidationError(f"owner_notifications[{index}].app_id must match lifecycle_state.app_id")
        require_public_safe(notification, f"owner_notifications[{index}]")

    for index, value in enumerate(runs):
        run = ensure_object(value, f"job_run_events[{index}]")
        ensure_schema(run, SCHEMAS["job_run_event"], f"job_run_events[{index}]")
        job_id = ensure_id(run.get("job_id"), f"job_run_events[{index}].job_id")
        if job_id not in job_ids:
            raise ValidationError(f"job_run_events[{index}].job_id is not in recurring_jobs")
        if ensure_id(run.get("app_id"), f"job_run_events[{index}].app_id", app_id=True) != app_id:
            raise ValidationError(f"job_run_events[{index}].app_id must match lifecycle_state.app_id")
        ensure_enum(run.get("result"), RUN_RESULTS, f"job_run_events[{index}].result")
        ensure_enum(run.get("external_effect"), EXTERNAL_EFFECTS, f"job_run_events[{index}].external_effect")
        missing_notifications = sorted(
            ref.removeprefix("notification:") for ref in optional_string_list(run, "notification_refs", f"job_run_events[{index}]")
            if ref.removeprefix("notification:") not in notification_ids
        )
        if missing_notifications:
            raise ValidationError(f"job_run_events[{index}] references missing notifications: {', '.join(missing_notifications)}")
        require_public_safe(run, f"job_run_events[{index}]")

    for index, value in enumerate(kill_switches):
        switch = ensure_object(value, f"kill_switches[{index}]")
        ensure_schema(switch, SCHEMAS["kill_switch"], f"kill_switches[{index}]")
        ensure_id(switch.get("switch_id"), f"kill_switches[{index}].switch_id")
        require_public_safe(switch, f"kill_switches[{index}]")


def validate_bundle(bundle: dict[str, Any]) -> None:
    app_id, _stage_names, decision_refs = validate_lifecycle_state(ensure_object(bundle.get("lifecycle_state"), "lifecycle_state"))
    validate_world_model(ensure_object(bundle.get("world_model"), "world_model"), app_id)
    validate_event_ledger(ensure_list(bundle.get("event_ledger"), "event_ledger"), app_id)
    validate_decision_cards(ensure_list(bundle.get("owner_decision_cards"), "owner_decision_cards"), app_id, decision_refs)
    validate_capabilities(
        ensure_object(bundle.get("capability_inventory"), "capability_inventory"),
        ensure_list(bundle.get("capability_grants"), "capability_grants"),
        ensure_list(bundle.get("capability_audit_events"), "capability_audit_events"),
        app_id,
    )
    validate_scheduler(
        ensure_list(bundle.get("recurring_jobs"), "recurring_jobs"),
        ensure_list(bundle.get("job_run_events"), "job_run_events"),
        ensure_list(bundle.get("owner_notifications"), "owner_notifications"),
        ensure_list(bundle.get("kill_switches"), "kill_switches"),
        app_id,
    )


def load_bundle(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return ensure_object(data, "bundle")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=Path("docs/samples/lifecycle-artifacts.example.json"))
    args = parser.parse_args(argv)

    try:
        validate_bundle(load_bundle(args.path))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"invalid WEAVE lifecycle artifact bundle: {exc}", file=sys.stderr)
        return 1

    print(f"valid WEAVE lifecycle artifact bundle: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
