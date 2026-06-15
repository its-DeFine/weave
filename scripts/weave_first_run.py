#!/usr/bin/env python3
"""Local first-run product surface for WEAVE.

This module is deliberately local-only. It turns the service-blueprint first-run
lane into a reviewable setup artifact without contacting Hermes, Telegram,
model providers, deployment systems, analytics systems, or public channels.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import validate_lifecycle_artifacts
import weave_hermes_setup
import weave_runtime_slice


FIRST_RUN_SCHEMA = "weave-first-run/v0.1"
DEFAULT_OWNER_EXPERIENCE = "not specified"
DEFAULT_COWORKER_STYLE = "decision-first, explicit assumptions, proof-backed, calm about uncertainty"
DEFAULT_CONTROL_MODE = "hands-on"
DEFAULT_SETUP_CHOICE = "create-local"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_state(path: Path) -> str:
    return "present" if path.exists() else "missing"


def weave_root_ready(weave_root: Path) -> bool:
    return (weave_root / "apps" / "registry.json").exists() and (weave_root / "ledger" / "events.jsonl").exists()


def lifecycle_bundle_path(weave_root: Path, app_id: str) -> Path:
    intent_stage = weave_runtime_slice.stage_by_id("intent")
    # The public artifact contract already includes first_run, owner_profile,
    # and create_app stages, but the current runtime directory layout starts at
    # intent. Keep pre-intent proof inside the first runtime-backed stage until
    # the runtime gains dedicated pre-intent shelves.
    return (
        weave_runtime_slice.app_root(weave_root, app_id)
        / "lifecycle"
        / intent_stage.directory
        / "artifacts"
        / "first-run-lifecycle-bundle.json"
    )


def detect_environment(args: Any) -> dict[str, Any]:
    hermes_status = weave_hermes_setup.hermes_setup_status(args.hermes_home, hermes_command=getattr(args, "hermes_command", "hermes"))
    return {
        "runtime_home": {
            "path": str(args.runtime_home),
            "state": path_state(args.runtime_home),
        },
        "weave_root": {
            "path": str(args.weave_root),
            "state": path_state(args.weave_root),
            "ready": weave_root_ready(args.weave_root),
        },
        "hermes_home": {
            "path": str(args.hermes_home),
            "state": path_state(args.hermes_home),
            "setup_state": hermes_status["state"],
            "normal_chat_assumed_ready": hermes_status["normal_chat_assumed_ready"],
        },
        "profile": {
            "path": str(args.profile_out),
            "state": path_state(args.profile_out),
        },
        "remote_attach": {
            "supported": False,
            "reason": "ATM-245 creates the local product surface first; remote Hermes attach remains a later capability-gated flow.",
        },
        "live_effects": False,
    }


def first_run_snapshot(args: Any) -> dict[str, Any]:
    clean_app_id = weave_runtime_slice.slugify(args.app_id)
    return {
        "schema": FIRST_RUN_SCHEMA,
        "generated_at": utc_now(),
        "mode": "write" if args.write else "preview",
        "write_requested": bool(args.write),
        "live_effects": False,
        "secret_value_printed": False,
        "setup_choice": args.setup_choice,
        "control_mode": args.control_mode,
        "owner": {
            "experience": args.owner_experience,
            "preferred_coworker_style": args.coworker_style,
        },
        "app": {
            "app_id": clean_app_id,
            "name": args.app_name,
        },
        "environment": detect_environment(args),
        "proof_boundary": {
            "highest_surface": "local_deterministic" if args.write else "none",
            "claims": [
                "first-run choices can be normalized into a public-safe lifecycle artifact",
            ],
            "non_claims": [
                "does not prove live Hermes chat",
                "does not connect credentials",
                "does not deploy",
                "does not send Telegram or public messages",
            ],
        },
    }


def stage_row(stage: str, status: str, *, artifact_refs: list[str] | None = None, claims: list[str] | None = None, non_claims: list[str] | None = None) -> dict[str, Any]:
    row = {
        "stage": stage,
        "status": status,
        "artifact_refs": artifact_refs or [],
        "proof_refs": artifact_refs or [],
        "claims": claims or [],
        "non_claims": non_claims or [],
    }
    return row


def ledger_event(event_id: str, app_id: str, stage: str, event_type: str, summary: str, *, claims: list[str], non_claims: list[str]) -> dict[str, Any]:
    return {
        "schema": validate_lifecycle_artifacts.SCHEMAS["event_ledger_entry"],
        "event_id": event_id,
        "at": utc_now(),
        "app_id": app_id,
        "stage": stage,
        "actor": "weave-runtime",
        "event_type": event_type,
        "summary": summary,
        "evidence_refs": ["artifact:first-run-lifecycle-bundle-v1"],
        "claims": claims,
        "non_claims": non_claims,
        "requires_owner_review": False,
        "public_safe": True,
    }


def build_lifecycle_bundle(snapshot: dict[str, Any]) -> dict[str, Any]:
    app_id = snapshot["app"]["app_id"]
    now = utc_now()
    # The bundle is validated before it is written. That keeps the CLI from
    # creating app state that later lifecycle agents would have to reinterpret
    # after discovering malformed ownership or proof-boundary data.
    bundle = {
        "schema": "weave/lifecycle-artifact-bundle/v0.1",
        "updated_at": now,
        "lifecycle_state": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["lifecycle_state"],
            "app_id": app_id,
            "updated_at": now,
            "current_stage": "intent",
            "stage_source": "event-ledger",
            "stages": [
                stage_row(
                    "first_run",
                    "approved",
                    artifact_refs=["artifact:first-run-lifecycle-bundle-v1"],
                    claims=["operator completed the local first-run choice surface"],
                    non_claims=["does not prove any live runtime transport"],
                ),
                stage_row(
                    "owner_profile",
                    "approved",
                    artifact_refs=["artifact:owner-profile-v1"],
                    claims=["owner experience and coworker style were captured"],
                    non_claims=["does not prove the agent has applied those preferences in a live session"],
                ),
                stage_row(
                    "create_app",
                    "approved",
                    artifact_refs=["artifact:app-workspace-v1"],
                    claims=["local app workspace was created"],
                    non_claims=["does not prove engineering work has started"],
                ),
                stage_row(
                    "intent",
                    "collecting",
                    artifact_refs=["artifact:first-run-lifecycle-bundle-v1"],
                    claims=["intent stage is ready to collect product intent"],
                    non_claims=["intent has not been validated against WEAVE axioms"],
                ),
            ],
            "attention": {
                "state": "owner_input_needed",
                "summary": "Collect and validate product intent before research begins.",
                "decision_refs": [],
            },
            "approval_boundaries": [
                "credential_use_requires_owner_approval",
                "public_send_requires_owner_approval",
                "paid_spend_requires_owner_approval",
                "production_deploy_requires_owner_approval",
            ],
            "capability_gaps": ["provider credentials deferred", "deployment provider not connected"],
            "claims": ["local deterministic first-run state is internally linked"],
            "non_claims": ["not live Hermes proof", "not deployed production proof"],
        },
        "world_model": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["world_model"],
            "app_id": app_id,
            "updated_at": now,
            "current_stage": "intent",
            "owner_preferences": {
                "control_mode": snapshot["control_mode"],
                "experience": snapshot["owner"]["experience"],
                "communication_style": snapshot["owner"]["preferred_coworker_style"],
            },
            "selected_approach": {
                "summary": "Start with a local deterministic WEAVE app workspace and defer credentials until capability gates.",
                "source_artifact_refs": ["artifact:first-run-lifecycle-bundle-v1"],
            },
            "plans": {
                "intent": "artifact:first-run-lifecycle-bundle-v1",
            },
            "deployment_state": {
                "status": "not_started",
                "non_claims": ["deployment provider is not connected"],
            },
            "kpi_definitions": [],
            "marketing_state": {
                "status": "not_started",
                "non_claims": ["no public campaign has started"],
            },
            "active_jobs": [],
            "known_risks": [
                "remote Hermes attach is not implemented in this milestone",
                "provider credentials must stay outside agent-visible text",
            ],
            "approval_boundaries": ["credentials", "production deploy", "public send", "paid spend"],
            "capability_gaps": ["provider credentials deferred", "deployment provider not connected"],
            "proof_boundary": {
                "highest_proven_surface": "local_deterministic",
                "proof_refs": ["artifact:first-run-lifecycle-bundle-v1"],
                "non_claims": [
                    "not live Hermes proof",
                    "not Telegram proof",
                    "not deployed",
                    "not live-market validated",
                ],
            },
            "claims": ["world model reflects current local first-run choices"],
            "non_claims": ["does not prove runtime execution"],
        },
        "event_ledger": [
            ledger_event(
                "evt-first-run-0001",
                app_id,
                "first_run",
                "stage.approved",
                "Local first-run choices were recorded.",
                claims=["first-run choice surface completed"],
                non_claims=["no external system was contacted"],
            ),
            ledger_event(
                "evt-first-run-0002",
                app_id,
                "owner_profile",
                "stage.artifact_created",
                "Owner profile preferences were captured for future agent behavior.",
                claims=["owner profile artifact exists"],
                non_claims=["does not enforce behavior in Hermes yet"],
            ),
            ledger_event(
                "evt-first-run-0003",
                app_id,
                "create_app",
                "stage.artifact_created",
                "Local app workspace was created.",
                claims=["app workspace exists in local WEAVE state"],
                non_claims=["no repo, deployment, or public surface was created"],
            ),
            ledger_event(
                "evt-first-run-0004",
                app_id,
                "intent",
                "proof.recorded",
                "First-run lifecycle bundle passed deterministic validation.",
                claims=["artifact bundle validated locally"],
                non_claims=["not live runtime proof"],
            ),
        ],
        "owner_decision_cards": [],
        "capability_inventory": {
            "schema": validate_lifecycle_artifacts.SCHEMAS["capability_inventory"],
            "updated_at": now,
            "capabilities": [
                {
                    "id": "local-filesystem",
                    "name": "Local filesystem workspace",
                    "status": "granted",
                    "owner": "weave-runtime",
                    "public_safe": True,
                },
                {
                    "id": "provider-credentials",
                    "name": "Provider credentials",
                    "status": "deferred",
                    "owner": "owner",
                    "public_safe": True,
                },
                {
                    "id": "deployment-provider",
                    "name": "Deployment provider",
                    "status": "deferred",
                    "owner": "owner",
                    "public_safe": True,
                },
            ],
        },
        "capability_grants": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_grant"],
                "grant_id": "grant-local-filesystem-001",
                "capability_id": "local-filesystem",
                "app_id": app_id,
                "status": "active",
                "external_effect": "local_write",
                "approved_by": "owner",
                "scope": "create local WEAVE app workspace and first-run artifact",
                "public_safe": True,
            }
        ],
        "capability_audit_events": [
            {
                "schema": validate_lifecycle_artifacts.SCHEMAS["capability_audit_event"],
                "event_id": "capability-audit-first-run-001",
                "capability_id": "local-filesystem",
                "grant_id": "grant-local-filesystem-001",
                "app_id": app_id,
                "external_effect": "local_write",
                "summary": "WEAVE wrote local first-run app state only.",
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


def owner_profile_markdown(snapshot: dict[str, Any]) -> str:
    owner = snapshot["owner"]
    return (
        "# Owner Profile\n\n"
        f"- Experience: {owner['experience']}\n"
        f"- Preferred coworker style: {owner['preferred_coworker_style']}\n"
        f"- Control mode: {snapshot['control_mode']}\n\n"
        "Boundary: this file stores owner preferences only. Provider credentials, "
        "tokens, and private authorization material stay in the capability broker "
        "or a local vault, never in agent-visible prose.\n"
    )


def app_context_markdown(snapshot: dict[str, Any]) -> str:
    app = snapshot["app"]
    return (
        "# User Context For This App\n\n"
        f"- App: {app['name']} (`{app['app_id']}`)\n"
        f"- Setup choice: {snapshot['setup_choice']}\n"
        f"- Control mode: {snapshot['control_mode']}\n\n"
        "Next lifecycle action: collect product intent, validate it against WEAVE "
        "axioms, and do not enter research until the owner approves the normalized intent.\n"
    )


def append_runtime_note(weave_root: Path, app_id: str, artifact_path: Path, snapshot: dict[str, Any]) -> None:
    # Runtime events are separate from the public lifecycle artifact ledger.
    # Keeping both lets operators inspect what the local CLI wrote without
    # confusing runtime-local bookkeeping with reviewable lifecycle claims.
    weave_runtime_slice.append_event(
        weave_root,
        app_id,
        weave_runtime_slice.new_event(
            "artifact.created",
            app_id,
            "intent",
            "First-run lifecycle bundle created from local setup choices.",
            payload={
                "artifact_path": str(artifact_path.relative_to(weave_root)),
                "control_mode": snapshot["control_mode"],
                "setup_choice": snapshot["setup_choice"],
                "live_effects": False,
            },
            artifact_refs=[
                {
                    "id": "first-run-lifecycle-bundle-v1",
                    "path": str(artifact_path.relative_to(weave_root)),
                }
            ],
        ),
    )


def write_first_run(snapshot: dict[str, Any], args: Any) -> dict[str, Any]:
    if args.setup_choice == "defer-runtime":
        raise ValueError("defer-runtime is preview-only; choose create-local or attach-existing before writing app state")
    if args.setup_choice == "attach-existing" and not weave_root_ready(args.weave_root):
        # "Attach" must be a readback of an existing deterministic layer. If a
        # missing root were created here, the owner would see an attach claim
        # while the filesystem actually shows a new local runtime.
        raise ValueError("attach-existing requires an initialized WEAVE root; choose create-local for a new local runtime")

    app_id = snapshot["app"]["app_id"]
    # setup_weave_root/create_app are the existing deterministic runtime
    # primitives. Reusing them prevents the first-run TUI from drifting into a
    # second app-state format that slash commands and dashboards cannot read.
    root_result = weave_runtime_slice.setup_weave_root(args.weave_root)
    app_result = weave_runtime_slice.create_app(args.weave_root, app_id, snapshot["app"]["name"])
    active_app = weave_runtime_slice.set_active_app(args.weave_root, app_id, created_by="weave-runtime")

    owner_profile_path = args.weave_root / "artifacts" / "general" / "owner-profile.md"
    owner_profile_path.write_text(owner_profile_markdown(snapshot), encoding="utf-8")

    user_context_path = weave_runtime_slice.app_root(args.weave_root, app_id) / "context" / "user-context-for-this-app.md"
    user_context_path.write_text(app_context_markdown(snapshot), encoding="utf-8")

    bundle = build_lifecycle_bundle(snapshot)
    artifact_path = lifecycle_bundle_path(args.weave_root, app_id)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_runtime_note(args.weave_root, app_id, artifact_path, snapshot)

    return {
        "root_result": root_result,
        "app_result": app_result,
        "active_app": active_app,
        "owner_profile_path": str(owner_profile_path),
        "user_context_path": str(user_context_path),
        "artifact_path": str(artifact_path),
        "artifact_valid": True,
    }


def render_text(snapshot: dict[str, Any], *, write_result: dict[str, Any] | None = None) -> str:
    env = snapshot["environment"]
    app = snapshot["app"]
    lines = [
        "+------------------------------------------------------------+",
        "| WEAVE First Run Console                                    |",
        "| local product setup, owner profile, create-app proof        |",
        "+------------------------------------------------------------+",
        "",
        "[Signal]",
        f"  runtime_home: {env['runtime_home']['state']}",
        f"  weave_root: {env['weave_root']['state']}  ready={str(env['weave_root']['ready']).lower()}",
        f"  hermes_setup: {env['hermes_home']['setup_state']}  normal_chat={str(env['hermes_home']['normal_chat_assumed_ready']).lower()}",
        f"  profile: {env['profile']['state']}",
        "",
        "[Choice]",
        f"  setup: {snapshot['setup_choice']}",
        f"  control_mode: {snapshot['control_mode']}",
        "  remote_attach: deferred",
        "",
        "[Owner]",
        f"  experience: {snapshot['owner']['experience']}",
        f"  coworker_style: {snapshot['owner']['preferred_coworker_style']}",
        "",
        "[App]",
        f"  id: {app['app_id']}",
        f"  name: {app['name']}",
        "",
        "[Proof Boundary]",
        "  live_effects: false",
        "  secret_value_printed: false",
        "  claims: local deterministic first-run choices only",
        "  non_claims: no credentials, no Telegram send, no deployment, no live Hermes proof",
    ]
    if write_result:
        lines.extend(
            [
                "",
                "[Written]",
                f"  app_workspace: apps/{app['app_id']}",
                f"  active_app: {write_result['active_app']['app_id']}",
                f"  owner_profile: {write_result['owner_profile_path']}",
                f"  user_context: {write_result['user_context_path']}",
                f"  lifecycle_bundle: {write_result['artifact_path']}",
                "  artifact_valid: true",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "[Next]",
                "  rerun with --write to create local WEAVE app state",
                "  then collect intent before research begins",
            ]
        )
    return "\n".join(lines) + "\n"


def run(args: Any, *, output: TextIO = sys.stdout) -> int:
    snapshot = first_run_snapshot(args)
    write_result = None
    if args.write:
        try:
            write_result = write_first_run(snapshot, args)
        except (OSError, ValueError, validate_lifecycle_artifacts.ValidationError, weave_runtime_slice.RuntimeSliceError) as exc:
            print(f"first-run failed: {exc}", file=output)
            return 1
    if args.json:
        payload = dict(snapshot)
        if write_result:
            payload["write_result"] = write_result
        print(json.dumps(payload, indent=2, sort_keys=True), file=output)
        return 0
    print(render_text(snapshot, write_result=write_result), end="", file=output)
    return 0
