#!/usr/bin/env python3
"""Local WEAVE runtime first-slice primitives.

This module is intentionally small and standard-library only. It creates a
public-safe local operating substrate for tests and future CLI/API wrappers:
root folders, app rooms, lifecycle shelves, app registry, append-only ledger,
foundation gate checks, deterministic stage derivation, and REST-like dispatch.
It does not contact Hermes, Telegram, external networks, or private runtimes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import weave_provider_auth


ROOT_SCHEMA = "weave-root/v0.1"
RUNTIME_HOME_SCHEMA = "weave-runtime-home/v0.1"
APP_SCHEMA = "weave-app/v0.1"
REGISTRY_SCHEMA = "weave-app-registry/v0.1"
EVENT_SCHEMA = "weave-event/v0.1"
FOUNDATION_SCHEMA = "weave-foundation-gate/v0.1"
REST_SCHEMA = "weave-rest-dispatch/v0.1"
GATEWAY_CONTEXT_SCHEMA = "weave-gateway-context/v0.1"
TELEGRAM_COMMAND_SCHEMA = "weave-telegram-command/v0.1"
AUTONOMY_SCHEMA = "weave-autonomy-policy/v0.1"
SOURCE_MAP_SCHEMA = "weave-runtime-source-map/v0.1"
AGENT_PROFILE_SCHEMA = "weave-agent-profile/v0.1"
ACTIVE_APP_SCHEMA = "weave-active-app/v0.1"

TEMPLATE_MARKER = "template-needs-owner-input"
DEFAULT_AUTONOMY_MODE = "yolo"
AUTONOMY_MODES = {"confirm_everything", "yolo"}

EVENT_TYPES = {
    "app.created",
    "foundation.missing_context",
    "foundation.completed",
    "soul.updated",
    "owner_profile.updated",
    "app_context.updated",
    "lifecycle.stage_registered",
    "lifecycle.stage_derived",
    "artifact.created",
    "artifact.updated",
    "artifact.reference_recorded",
    "contract.updated",
    "contract.diff_recorded",
    "approval.requested",
    "approval.resolved",
    "procedure.violation",
    "procedure.feedback_sent",
    "validation.completed",
    "window.changed",
    "runtime.agent_profile.recorded",
    "runtime.agent_profile.changed",
    "runtime.active_app.changed",
}

CREATORS = {"hermes", "weave-runtime", "owner"}

LIFECYCLE_STAGES = [
    ("intent", "01-intent"),
    ("research", "02-research"),
    ("selection", "03-selection"),
    ("plan", "04-plan"),
    ("engineering", "05-engineering"),
    ("qa", "06-qa"),
    ("kpi", "07-kpi"),
    ("marketing", "08-marketing"),
    ("iteration", "09-iteration"),
    ("analysis", "10-analysis"),
]

APP_DIRS = [
    "context/reality-briefs",
    "inventory",
    "repo/primary",
    "repo/worktrees",
    "repo/prs",
    "contract/versions",
    "contract/diffs",
    "evidence",
    "approvals",
    "ledger/procedure-feedback",
    "exports",
    "outputs",
    "refs",
    "other",
]

TELEGRAM_COMMANDS = {
    "/start": "Show the deterministic WEAVE command surface.",
    "/help": "List deterministic WEAVE commands.",
    "/autonomy": "Show autonomy mode and hard approval gates.",
    "/status": "Show the WEAVE wall or one app wall. Usage: /status [app_id]",
    "/sources": "Show runtime history and source-of-truth surfaces.",
    "/apps": "List product apps, lifecycle stages, and attention state.",
    "/app": "Show one app wall. Usage: /app <app_id>",
    "/create_app": "Create and select a product app workspace. Usage: /create_app <name>",
    "/switch_app": "Select the active Telegram app. Usage: /switch_app <app_id>",
    "/stage": "Show lifecycle stage state. Usage: /stage [app_id]",
    "/requirements": "Show current-stage requirements. Usage: /requirements [app_id]",
    "/blockers": "Show apps that need owner or Hermes action.",
    "/changes": "Show latest recorded changes. Usage: /changes [app_id]",
    "/next": "Show the next deterministic owner-visible action.",
}

STAGE_STATES = {"not_started", "collecting", "blocked", "ready_for_review", "approved", "active"}

LEGACY_STAGE_ALIASES = {
    "02-kernel": "research",
    "03-contract": "selection",
    "04-premortem": "plan",
    "05-handoff": "engineering",
    "06-implementation": "engineering",
    "07-qa": "qa",
    "08-kpi-setup": "kpi",
    "09-marketing": "marketing",
    "10-iteration": "iteration",
    "11-analysis": "analysis",
}

SYSTEM_APP_IDS = {"weave", "weave-runtime", "weave-tooling"}

DEFAULT_ACTIVE_SKILLS = [
    "weave-lifecycle",
    "implementation-planning",
    "qa-verification",
    "evidence-packet",
]

HARD_APPROVAL_GATES = [
    {
        "id": "secrets_credentials_auth",
        "label": "Secrets, credentials, auth, or allowlist changes",
        "examples": ["tokens", "API keys", "passwords", "gateway allowlists", "login state"],
    },
    {
        "id": "external_public_send",
        "label": "External sends or public publication",
        "examples": ["public posts", "emails", "partner messages", "ads", "distribution"],
    },
    {
        "id": "paid_or_metered_work",
        "label": "Paid jobs, purchases, or metered provider actions",
        "examples": ["payments", "paid compute", "metered APIs", "checkout"],
    },
    {
        "id": "production_or_service_change",
        "label": "Production, runtime service, or transport changes",
        "examples": ["production deploys", "service installation", "autostart", "non-local transport"],
    },
    {
        "id": "destructive_or_irreversible_change",
        "label": "Destructive or irreversible changes",
        "examples": ["deletes", "data migration", "account removal", "history rewrite"],
    },
]


class RuntimeSliceError(Exception):
    """Raised when the local runtime slice rejects an invalid operation."""


@dataclass(frozen=True)
class Stage:
    id: str
    directory: str


STAGES = [Stage(stage_id, directory) for stage_id, directory in LIFECYCLE_STAGES]


def stage_by_id(stage_id: str) -> Stage:
    for stage in STAGES:
        if stage.id == stage_id:
            return stage
    raise RuntimeSliceError(f"unsupported lifecycle stage: {stage_id}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "app"


def normalize_autonomy_mode(value: str | None) -> str:
    mode = str(value or DEFAULT_AUTONOMY_MODE).strip().lower().replace("-", "_")
    if mode in {"confirm", "manual", "ask", "ask_everything"}:
        return "confirm_everything"
    if mode in {"yolo", "auto", "auto_proceed", "autonomous"}:
        return "yolo"
    if mode not in AUTONOMY_MODES:
        raise RuntimeSliceError(f"unsupported autonomy mode: {value}")
    return mode


def autonomy_policy(mode: str | None = None) -> dict[str, Any]:
    normalized = normalize_autonomy_mode(mode)
    if normalized == "yolo":
        default_action = "proceed_without_confirmation_for_non_gated_work"
        confirmation_policy = (
            "Hermes should keep working without routine confirmation, but must ask "
            "the owner through the LLM conversation before any hard-gated action."
        )
    else:
        default_action = "ask_before_nontrivial_work"
        confirmation_policy = "Hermes should ask before non-trivial work and before every hard-gated action."
    return {
        "schema": AUTONOMY_SCHEMA,
        "mode": normalized,
        "default_action": default_action,
        "approval_channel": "telegram_llm_conversation",
        "llm_must_request_owner_authorization_for_hard_gates": True,
        "confirmation_policy": confirmation_policy,
        "allowed_without_confirmation": [
            "deterministic slash-command status",
            "read-only inspection",
            "local app workspace edits",
            "local repository edits inside the active work packet",
            "test, validation, and formatting commands",
            "append-only ledger and lifecycle status updates",
        ],
        "hard_approval_gates": HARD_APPROVAL_GATES,
    }


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def write_new(path: Path, content: str, created: list[str], root: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(relative(path, root))


def template(title: str, purpose: str) -> str:
    return f"""# {title}

Status: {TEMPLATE_MARKER}

Purpose: {purpose}

## Required Facts

- TODO

## Known Unknowns

- TODO

## Update Rules

- Record meaningful changes in git and the local ledger.
"""


def ensure_git_repo(root: Path) -> bool:
    if (root / ".git").exists():
        return True
    try:
        result = subprocess.run(
            ["git", "init"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and (root / ".git").exists()


def ensure_runtime_token(root: Path, created: list[str]) -> Path:
    token_path = root / "runtime" / "tokens" / "local-api-token"
    if token_path.exists():
        return token_path
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
    created.append(relative(token_path, root))
    return token_path


def autonomy_policy_path(root: Path) -> Path:
    return root / "runtime" / "profiles" / "autonomy-policy.json"


def source_map_path(root: Path) -> Path:
    return root / "runtime" / "source-map.json"


def write_autonomy_policy(root: Path, mode: str | None = None) -> dict[str, Any]:
    policy = autonomy_policy(mode)
    path = autonomy_policy_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return policy


def load_autonomy_policy(root: Path) -> dict[str, Any]:
    path = autonomy_policy_path(root)
    if not path.exists():
        return autonomy_policy(DEFAULT_AUTONOMY_MODE)
    data = load_json(path)
    if data.get("schema") != AUTONOMY_SCHEMA:
        raise RuntimeSliceError(f"autonomy policy schema must be {AUTONOMY_SCHEMA}")
    return autonomy_policy(str(data.get("mode") or DEFAULT_AUTONOMY_MODE))


def path_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "kind": "missing"}
    if path.is_dir():
        return {"exists": True, "kind": "directory"}
    return {"exists": True, "kind": "file", "size_bytes": path.stat().st_size}


def summarize_source_map(source_map: dict[str, Any]) -> dict[str, Any]:
    sources = source_map.get("sources", [])
    if not isinstance(sources, list):
        sources = []
    statuses: dict[str, int] = {}
    for source in sources:
        status = str(source.get("status") or "unknown") if isinstance(source, dict) else "unknown"
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "source_count": len(sources),
        "status_counts": statuses,
        "canonical_source_id": source_map.get("canonical_source_id", ""),
        "history_source_ids": source_map.get("history_source_ids", []),
    }


def runtime_home_from_root(root: Path) -> Path:
    if root.name == "weave-state":
        return root.parent
    return root


def default_source_map(root: Path) -> dict[str, Any]:
    runtime_home = runtime_home_from_root(root)
    sources = [
        {
            "id": "runtime-home",
            "label": "Runtime home",
            "kind": "workspace",
            "role": "durable local home for WEAVE state, Hermes home, profiles, logs, and migration archives",
            "status": "active" if runtime_home.exists() else "missing",
            "path": str(runtime_home),
            "mutable": True,
            "sensitive": False,
            "path_status": path_status(runtime_home),
            "layout_schema": RUNTIME_HOME_SCHEMA,
        },
        {
            "id": "weave-root",
            "label": "WEAVE state root",
            "kind": "workspace",
            "role": "canonical local app, lifecycle, ledger, and review state",
            "status": "active" if root.exists() else "missing",
            "path": str(root),
            "mutable": True,
            "sensitive": False,
            "path_status": path_status(root),
        },
        {
            "id": "app-registry",
            "label": "App registry",
            "kind": "json",
            "role": "registered apps and lifecycle stage summary",
            "status": "active" if registry_path(root).exists() else "missing",
            "path": str(registry_path(root)),
            "mutable": True,
            "sensitive": False,
            "path_status": path_status(registry_path(root)),
        },
        {
            "id": "autonomy-policy",
            "label": "Autonomy policy",
            "kind": "json",
            "role": "runtime confirmation and approval-gate policy",
            "status": "active" if autonomy_policy_path(root).exists() else "missing",
            "path": str(autonomy_policy_path(root)),
            "mutable": True,
            "sensitive": False,
            "path_status": path_status(autonomy_policy_path(root)),
        },
        {
            "id": "agent-profile",
            "label": "Hermes agent profile",
            "kind": "json",
            "role": "active model, reasoning effort, prompt pack, and skill profile",
            "status": "active" if agent_profile_path(root).exists() else "missing",
            "path": str(agent_profile_path(root)),
            "mutable": True,
            "sensitive": False,
            "path_status": path_status(agent_profile_path(root)),
        },
        {
            "id": "active-app",
            "label": "Active app profile",
            "kind": "json",
            "role": "one active product app for the Telegram UX",
            "status": "active" if active_app_path(root).exists() else "missing",
            "path": str(active_app_path(root)),
            "mutable": True,
            "sensitive": False,
            "path_status": path_status(active_app_path(root)),
        },
        {
            "id": "local-api-token",
            "label": "Local API token",
            "kind": "secret_ref",
            "role": "loopback REST authorization",
            "status": "active" if (root / "runtime" / "tokens" / "local-api-token").exists() else "missing",
            "path": "runtime/tokens/local-api-token",
            "mutable": False,
            "sensitive": True,
            "secret_value_printed": False,
        },
    ]
    return {
        "schema": SOURCE_MAP_SCHEMA,
        "generated_at": utc_now(),
        "canonical_source_id": "weave-root",
        "history_source_ids": ["runtime-home", "app-registry"],
        "sources": sources,
        "next_unification_action": "Attach external history ledgers or Hermes session stores with the source-map generator.",
    }


def validate_source_map(source_map: dict[str, Any]) -> None:
    if source_map.get("schema") != SOURCE_MAP_SCHEMA:
        raise RuntimeSliceError(f"source map schema must be {SOURCE_MAP_SCHEMA}")
    sources = source_map.get("sources")
    if not isinstance(sources, list):
        raise RuntimeSliceError("source map sources must be a list")
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise RuntimeSliceError("source map entries must be objects")
        source_id = str(source.get("id") or "")
        if not source_id:
            raise RuntimeSliceError("source map entry id is required")
        if source_id in seen:
            raise RuntimeSliceError(f"duplicate source map entry id: {source_id}")
        seen.add(source_id)
        if "status" not in source:
            raise RuntimeSliceError(f"source map entry {source_id} missing status")
        if source.get("sensitive") is True and source.get("secret_value_printed") is not False:
            raise RuntimeSliceError(f"sensitive source map entry {source_id} must prove secret_value_printed=false")


def write_source_map(root: Path, source_map: dict[str, Any]) -> dict[str, Any]:
    validate_source_map(source_map)
    path = source_map_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(source_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return source_map


def ensure_source_map(root: Path) -> dict[str, Any]:
    path = source_map_path(root)
    if not path.exists():
        return write_source_map(root, default_source_map(root))
    source_map = load_source_map(root)
    defaults = default_source_map(root)
    changed = False
    defaults_by_id = {source["id"]: source for source in defaults["sources"]}
    existing_ids = {source["id"] for source in source_map.get("sources", []) if isinstance(source, dict)}
    for source in source_map.get("sources", []):
        if not isinstance(source, dict) or source.get("id") not in defaults_by_id:
            continue
        default_source = defaults_by_id[source["id"]]
        for field in ("status", "path_status"):
            if source.get(field) != default_source.get(field):
                source[field] = default_source.get(field)
                changed = True
    missing_sources = [source for source in defaults["sources"] if source["id"] not in existing_ids]
    if missing_sources:
        source_map["sources"].extend(missing_sources)
        changed = True
    if changed:
        source_map["generated_at"] = utc_now()
        return write_source_map(root, source_map)
    return source_map


def load_source_map(root: Path) -> dict[str, Any]:
    path = source_map_path(root)
    if not path.exists():
        return default_source_map(root)
    source_map = load_json(path)
    validate_source_map(source_map)
    return source_map


def runtime_ledger_path(root: Path) -> Path:
    return root / "ledger" / "events.jsonl"


def active_app_path(root: Path) -> Path:
    return root / "runtime" / "profiles" / "active-app.json"


def agent_profile_path(root: Path) -> Path:
    return root / "runtime" / "profiles" / "agent-profile.json"


def profile_hash(profile: dict[str, Any]) -> str:
    material = {key: value for key, value in profile.items() if key != "profile_hash"}
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def default_agent_profile(root: Path) -> dict[str, Any]:
    profile = {
        "schema": AGENT_PROFILE_SCHEMA,
        "model": os.environ.get("WEAVE_HERMES_MODEL", "unknown"),
        "reasoning_effort": os.environ.get("WEAVE_HERMES_REASONING_EFFORT", "unknown"),
        "provider_adapter": os.environ.get("WEAVE_HERMES_PROVIDER_ADAPTER", "unknown"),
        "autonomy_mode": load_autonomy_policy(root)["mode"],
        "prompt_pack": os.environ.get("WEAVE_HERMES_PROMPT_PACK", "hermes-gestalt-runtime-pack"),
        "active_skills": DEFAULT_ACTIVE_SKILLS,
        "recorded_at": utc_now(),
    }
    profile["profile_hash"] = profile_hash(profile)
    return profile


def validate_agent_profile(profile: dict[str, Any]) -> None:
    if profile.get("schema") != AGENT_PROFILE_SCHEMA:
        raise RuntimeSliceError(f"agent profile schema must be {AGENT_PROFILE_SCHEMA}")
    for field in ("model", "reasoning_effort", "provider_adapter", "autonomy_mode", "prompt_pack", "recorded_at"):
        if field not in profile:
            raise RuntimeSliceError(f"agent profile missing {field}")
    if not isinstance(profile.get("active_skills"), list):
        raise RuntimeSliceError("agent profile active_skills must be a list")
    expected_hash = profile_hash(profile)
    if profile.get("profile_hash") and profile["profile_hash"] != expected_hash:
        raise RuntimeSliceError("agent profile hash does not match profile content")
    profile["profile_hash"] = expected_hash


def append_runtime_event(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    validate_event(event)
    path = runtime_ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def read_runtime_events(root: Path) -> list[dict[str, Any]]:
    path = runtime_ledger_path(root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeSliceError(f"invalid runtime ledger JSON at line {line_number}: {exc}") from exc
        validate_event(event)
        events.append(event)
    return events


def write_agent_profile(root: Path, profile: dict[str, Any], *, event_type: str = "runtime.agent_profile.changed") -> dict[str, Any]:
    validate_agent_profile(profile)
    path = agent_profile_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_runtime_event(
        root,
        new_event(
            event_type,
            "weave-runtime",
            "runtime",
            f"Recorded Hermes agent profile {profile['model']} / {profile['reasoning_effort']}.",
            payload={"agent_profile": profile},
        ),
    )
    return profile


def ensure_agent_profile(root: Path) -> dict[str, Any]:
    path = agent_profile_path(root)
    if path.exists():
        profile = load_json(path)
        validate_agent_profile(profile)
        return profile
    return write_agent_profile(root, default_agent_profile(root), event_type="runtime.agent_profile.recorded")


def is_system_app(app: dict[str, Any] | str) -> bool:
    if isinstance(app, str):
        app_id = slugify(app)
        return app_id in SYSTEM_APP_IDS
    app_id = slugify(str(app.get("app_id") or ""))
    return app.get("app_type") == "system" or app_id in SYSTEM_APP_IDS


def load_active_app(root: Path) -> dict[str, Any]:
    path = active_app_path(root)
    if not path.exists():
        return {
            "schema": ACTIVE_APP_SCHEMA,
            "app_id": "",
            "source": "unset",
            "updated_at": "",
        }
    data = load_json(path)
    if data.get("schema") != ACTIVE_APP_SCHEMA:
        raise RuntimeSliceError(f"active app schema must be {ACTIVE_APP_SCHEMA}")
    return data


def set_active_app(root: Path, app_id: str, *, created_by: str = "weave-runtime") -> dict[str, Any]:
    clean_id = slugify(app_id)
    app = load_app(root, clean_id)
    if is_system_app(app):
        raise RuntimeSliceError(f"system app cannot be selected as the Telegram active product app: {clean_id}")
    data = {
        "schema": ACTIVE_APP_SCHEMA,
        "app_id": clean_id,
        "source": "telegram",
        "updated_at": utc_now(),
    }
    path = active_app_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ensure_source_map(root)
    append_runtime_event(
        root,
        new_event(
            "runtime.active_app.changed",
            "weave-runtime",
            "runtime",
            f"Active Telegram app changed to {clean_id}.",
            created_by=created_by,
            payload={"active_app": data},
        ),
    )
    return data


def setup_weave_root(root: Path, *, init_git: bool = True, autonomy_mode: str | None = None) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    git_tracked = ensure_git_repo(root) if init_git else (root / ".git").exists()

    for directory in ("artifacts/general", "apps", "ledger", "runtime/profiles", "runtime/logs", "runtime/tokens"):
        path = root / directory
        if not path.exists():
            path.mkdir(parents=True)
            created.append(directory + "/")

    write_new(
        root / "artifacts" / "general" / "soul.md",
        template("Hermes Soul", "Define how Hermes should think, behave, ask, challenge, and proceed."),
        created,
        root,
    )
    write_new(
        root / "artifacts" / "general" / "owner-profile.md",
        template("Owner Profile", "Define who Hermes is helping and how to help them well."),
        created,
        root,
    )
    write_new(
        root / "apps" / "registry.json",
        json.dumps({"schema": REGISTRY_SCHEMA, "apps": []}, indent=2) + "\n",
        created,
        root,
    )
    ensure_runtime_token(root, created)
    policy = write_autonomy_policy(root, autonomy_mode)
    agent_profile = ensure_agent_profile(root)
    source_map = ensure_source_map(root)
    return {
        "schema": ROOT_SCHEMA,
        "root": str(root),
        "runtime_home_schema": RUNTIME_HOME_SCHEMA,
        "runtime_home": str(runtime_home_from_root(root)),
        "git_tracked": git_tracked,
        "registry_path": "apps/registry.json",
        "runtime_ledger_path": "ledger/events.jsonl",
        "autonomy": policy,
        "agent_profile": agent_profile,
        "autonomy_policy_path": "runtime/profiles/autonomy-policy.json",
        "agent_profile_path": "runtime/profiles/agent-profile.json",
        "source_map_path": "runtime/source-map.json",
        "source_map_summary": summarize_source_map(source_map),
        "created": created,
        "rest_api": {
            "bind": "loopback-only",
            "auth": "generated-bearer-token",
            "token_path": "runtime/tokens/local-api-token",
        },
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeSliceError(f"invalid JSON in {path}: {exc}") from exc


def registry_path(root: Path) -> Path:
    return root / "apps" / "registry.json"


def load_registry(root: Path) -> dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        raise RuntimeSliceError("WEAVE app registry is missing")
    registry = load_json(path)
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise RuntimeSliceError(f"registry schema must be {REGISTRY_SCHEMA}")
    if not isinstance(registry.get("apps"), list):
        raise RuntimeSliceError("registry apps must be a list")
    return registry


def write_registry(root: Path, registry: dict[str, Any]) -> None:
    registry_path(root).write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def app_root(root: Path, app_id: str) -> Path:
    return root / "apps" / slugify(app_id)


def app_metadata_path(root: Path, app_id: str) -> Path:
    return app_root(root, app_id) / "app.weave.json"


def load_app(root: Path, app_id: str) -> dict[str, Any]:
    path = app_metadata_path(root, app_id)
    if not path.exists():
        raise RuntimeSliceError(f"app does not exist: {app_id}")
    app = load_json(path)
    if app.get("schema") != APP_SCHEMA:
        raise RuntimeSliceError(f"app schema must be {APP_SCHEMA}")
    return app


def write_app(root: Path, app: dict[str, Any]) -> None:
    app_metadata_path(root, app["app_id"]).write_text(
        json.dumps(app, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def create_app(root: Path, app_id: str, name: str) -> dict[str, Any]:
    setup_weave_root(root)
    clean_id = slugify(app_id)
    base = app_root(root, clean_id)
    created: list[str] = []
    for directory in APP_DIRS:
        path = base / directory
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(relative(path, root) + "/")
    for stage in STAGES:
        for child in ("artifacts", "refs"):
            path = base / "lifecycle" / stage.directory / child
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created.append(relative(path, root) + "/")

    write_new(
        base / "context" / "app-context.md",
        template("App Context", "Define the app users, domain, constraints, reality sources, and operating context."),
        created,
        root,
    )
    write_new(
        base / "context" / "user-context-for-this-app.md",
        template("User Context For This App", "Define how the owner wants Hermes to think about this specific app."),
        created,
        root,
    )
    write_new(
        base / "context" / "domain-context.md",
        template("Domain Context", "Define the domain facts and evidence sources for this app."),
        created,
        root,
    )
    write_new(
        base / "context" / "decisions.md",
        template("App Decisions", "Record app-specific decisions that should shape future lifecycle work."),
        created,
        root,
    )
    write_new(
        base / "inventory" / "app-inventory.md",
        template("App Inventory", "List repos, artifacts, environments, proofs, owners, and current state."),
        created,
        root,
    )
    write_new(
        base / "contract" / "gestaltian-contract.md",
        template("Gestaltian Contract", "Define the app kernel, acceptance checks, failure modes, and lifecycle contract."),
        created,
        root,
    )
    write_new(base / "ledger" / "events.jsonl", "", created, root)

    now = utc_now()
    metadata = {
        "schema": APP_SCHEMA,
        "app_id": clean_id,
        "name": name,
        "app_type": "system" if clean_id in SYSTEM_APP_IDS else "product",
        "status": "active",
        "created_at": now,
        "current_stage": "intent",
        "stage_source": "derived",
        "stage_state": "collecting",
        "stage_completion_requires_owner_review": True,
        "contract_version": "0.1-template",
        "primary_repo": "repo/primary",
        "context_paths": [
            "context/app-context.md",
            "context/user-context-for-this-app.md",
            "context/domain-context.md",
            "context/decisions.md",
        ],
        "ledger_path": "ledger/events.jsonl",
        "decision_log_path": "context/decisions.md",
        "required_inputs": [],
        "owner_questions": [],
        "tasks": [],
        "credential_requirements": [],
        "capabilities": [
            "local-filesystem",
            "git-tracked-workspace",
            "append-only-ledger",
            "rest-dispatch-skeleton",
            "telegram-deterministic-slash-commands",
        ],
        "blockers": [],
    }
    write_app(root, metadata)

    registry = load_registry(root)
    apps = [entry for entry in registry["apps"] if entry.get("app_id") != clean_id]
    apps.append(
        {
            "app_id": clean_id,
            "name": name,
            "app_type": metadata["app_type"],
            "path": f"apps/{clean_id}",
            "stage": "intent",
            "stage_source": "derived",
            "stage_state": metadata["stage_state"],
            "last_changed_at": now,
            "contract_version": metadata["contract_version"],
        }
    )
    registry["apps"] = sorted(apps, key=lambda item: item["app_id"])
    write_registry(root, registry)

    append_event(
        root,
        clean_id,
        new_event(
            "app.created",
            clean_id,
            "intent",
            f"Created app workspace for {name}.",
            payload={"created_paths": created},
        ),
    )
    gate = foundation_gate(root, clean_id)
    if not gate["passed"]:
        append_event(
            root,
            clean_id,
            new_event(
                "foundation.missing_context",
                clean_id,
                "intent",
                "Foundation context is incomplete; Hermes must enter an elicitation loop through Telegram before serious app work.",
                payload={"missing": gate["missing"], "incomplete": gate["incomplete"]},
            ),
        )
    return {"app": metadata, "created": created, "foundation_gate": gate}


def event_path(root: Path, app_id: str) -> Path:
    return app_root(root, app_id) / "ledger" / "events.jsonl"


def new_event(
    event_type: str,
    app_id: str,
    stage: str,
    summary: str,
    *,
    created_by: str = "weave-runtime",
    payload: dict[str, Any] | None = None,
    artifact_refs: list[dict[str, Any]] | None = None,
    contract_version: str = "",
    approval_ref: str = "",
    git_commit: str = "",
) -> dict[str, Any]:
    return {
        "schema": EVENT_SCHEMA,
        "event_id": secrets.token_hex(12),
        "type": event_type,
        "app_id": slugify(app_id),
        "created_at": utc_now(),
        "created_by": created_by,
        "stage": stage,
        "summary": summary,
        "payload": payload or {},
        "artifact_refs": artifact_refs or [],
        "contract_version": contract_version,
        "approval_ref": approval_ref,
        "git_commit": git_commit,
    }


def validate_event(event: dict[str, Any]) -> None:
    required = {
        "schema",
        "event_id",
        "type",
        "app_id",
        "created_at",
        "created_by",
        "stage",
        "summary",
        "payload",
        "artifact_refs",
        "contract_version",
        "approval_ref",
        "git_commit",
    }
    missing = sorted(required - set(event))
    if missing:
        raise RuntimeSliceError(f"event missing required fields: {', '.join(missing)}")
    if event["schema"] != EVENT_SCHEMA:
        raise RuntimeSliceError(f"event schema must be {EVENT_SCHEMA}")
    if event["type"] not in EVENT_TYPES:
        raise RuntimeSliceError(f"unsupported event type: {event['type']}")
    if event["created_by"] not in CREATORS:
        raise RuntimeSliceError(f"unsupported event creator: {event['created_by']}")
    if not event["app_id"]:
        raise RuntimeSliceError("event app_id is required")
    if not event["summary"]:
        raise RuntimeSliceError("event summary is required")
    if not isinstance(event["payload"], dict):
        raise RuntimeSliceError("event payload must be an object")
    if not isinstance(event["artifact_refs"], list):
        raise RuntimeSliceError("event artifact_refs must be a list")


def append_event(root: Path, app_id: str, event: dict[str, Any]) -> dict[str, Any]:
    load_app(root, app_id)
    validate_event(event)
    path = event_path(root, app_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def read_events(root: Path, app_id: str) -> list[dict[str, Any]]:
    path = event_path(root, app_id)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeSliceError(f"invalid ledger JSON at line {line_number}: {exc}") from exc
        validate_event(event)
        events.append(event)
    return events


def file_incomplete(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").strip()
    return not text or TEMPLATE_MARKER in text or "TODO" in text


def foundation_gate(root: Path, app_id: str) -> dict[str, Any]:
    base = app_root(root, app_id)
    app = load_app(root, app_id)
    required_files = {
        "soul.md": root / "artifacts" / "general" / "soul.md",
        "owner-profile.md": root / "artifacts" / "general" / "owner-profile.md",
        "context/app-context.md": base / "context" / "app-context.md",
        "inventory/app-inventory.md": base / "inventory" / "app-inventory.md",
        "contract/gestaltian-contract.md": base / "contract" / "gestaltian-contract.md",
    }
    missing = [label for label, path in required_files.items() if not path.exists()]
    incomplete = [label for label, path in required_files.items() if file_incomplete(path)]
    if not app.get("current_stage"):
        missing.append("lifecycle stage")
    if not app.get("capabilities"):
        missing.append("available capabilities")
    if "blockers" not in app:
        missing.append("blockers")
    passed = not missing and not incomplete
    return {
        "schema": FOUNDATION_SCHEMA,
        "app_id": slugify(app_id),
        "passed": passed,
        "missing": missing,
        "incomplete": incomplete,
        "communication_channel": "telegram",
        "next_action": "continue" if passed else "Hermes must ask the owner through Telegram and update the missing context.",
    }


def foundation_gate_profile_path(root: Path, app_id: str) -> Path:
    return root / "runtime" / "profiles" / f"foundation-gate-{slugify(app_id)}.json"


def gateway_workdir(root: Path) -> Path:
    return root / "runtime" / "hermes-gateway"


def render_gateway_agents(
    *,
    root: Path,
    app_id: str,
    app_name: str,
    gate_path: Path,
    context_path: Path,
    autonomy: dict[str, Any],
) -> str:
    clean_id = slugify(app_id)
    base = app_root(root, clean_id)
    hard_gates = "\n".join(f"- {gate['label']}" for gate in autonomy["hard_approval_gates"])
    return f"""# WEAVE Hermes Gateway Enforcement

This generated local runtime file is loaded by Hermes when the Telegram gateway
starts from this directory. It turns the WEAVE foundation contract into an
active operating rule.

## Runtime Pointers

- WEAVE root: `{root}`
- Active app id: `{clean_id}`
- Active app name: `{app_name}`
- App workspace: `{base}`
- Foundation gate: `{gate_path}`
- Gateway context: `{context_path}`
- App registry: `{root / "apps" / "registry.json"}`
- Ledger: `{base / "ledger" / "events.jsonl"}`
- Communication channel: Telegram
- Autonomy mode: `{autonomy["mode"]}`
- Autonomy policy: `{autonomy_policy_path(root)}`
- Agent profile: `{agent_profile_path(root)}`
- Active app profile: `{active_app_path(root)}`
- Source map: `{source_map_path(root)}`

## Autonomy Mode

Mode `{autonomy["mode"]}` means: {autonomy["confirmation_policy"]}

Hermes may continue without routine confirmation for non-gated local work,
including read-only inspection, local app workspace edits, local repo edits
inside the active work packet, tests, validation, formatting, and append-only
ledger/status updates.

Hermes must ask the owner through the LLM conversation in Telegram and wait for
explicit authorization before crossing any hard approval gate:

{hard_gates}

The approval question must name the action, target surface, likely effect,
rollback or stop boundary, and acceptance check. Record the approval request
and resolution in the app ledger when the app is known.

## Unskippable Foundation Gate

Before doing app work, implementation planning, approval routing, external
sends, provider changes, deployments, or repo mutations, read the foundation
gate, source map, and the required source documents.

Required source documents:

- `{root / "artifacts" / "general" / "soul.md"}`
- `{root / "artifacts" / "general" / "owner-profile.md"}`
- `{base / "context" / "app-context.md"}`
- `{base / "inventory" / "app-inventory.md"}`
- `{base / "contract" / "gestaltian-contract.md"}`

The gate is blocking when `passed` is false, when any required document is
missing, when any required document still contains `{TEMPLATE_MARKER}` or
`TODO`, or when your confidence that the context is complete is not high.

When the gate is blocking:

1. Stay in Foundation Onboarding Mode.
2. Ask the owner through Telegram only.
3. Ask at most three blocking questions in one message.
4. Ask for the missing context in this order: Hermes character, owner profile,
   active app context, app inventory, Gestaltian contract.
5. Keep the owner moving with an elicitation loop: explain what is missing, why
   it matters, and what answer is needed next.
6. Do not continue into app work until the missing answers are reflected into
   the canonical documents and the gate can pass.

## How To Proceed

When the owner answers, update the canonical markdown documents under the WEAVE
root. Record meaningful changes in the app ledger. Refresh or re-read the
foundation gate before moving on.

When the foundation gate passes, continue with the Hermes Gestalt Runtime Pack:

Raw whole-first vision -> Gestalt Kernel -> Gestaltian Contract -> Premortem
Report -> Build-Ready Handoff Packet -> Implementation Report -> Validation
Result -> Contract Update Log.

## Operator-Facing Summary

Normal conversation stays with Hermes through Telegram. There is no dashboard
or UI in this phase. Deterministic slash commands such as `/status`,
`/status <app_id>`, `/apps`, `/app`, `/create_app`, `/switch_app`, `/stage`,
`/requirements`, `/blockers`, `/changes`, and `/next` are handled by the WEAVE
runtime command layer and must not be answered with model-generated text.

Use product lifecycle language in owner-facing communication:
intent -> research -> selection -> plan -> engineering -> qa -> kpi ->
marketing -> iteration -> analysis.
"""


def render_gateway_soul(*, root: Path, app_id: str, app_name: str, gate_path: Path) -> str:
    clean_id = slugify(app_id)
    return f"""# WEAVE Gateway Soul Bootstrap

You are Hermes operating inside the WEAVE gateway context.

Your first responsibility is not to code. Your first responsibility is to make
sure you have enough durable context to help the owner correctly.

If `{gate_path}` is not passing, ask the owner through Telegram for the missing
foundation answers and stop there. Keep questions precise, ask no more than
three blocking questions at once, and write the answers into the canonical
WEAVE documents under `{root}` for app `{clean_id}` (`{app_name}`).

Use the canonical `artifacts/general/soul.md` and `artifacts/general/owner-profile.md`
as soon as they are complete. Until then, this bootstrap soul is the active
guardrail: do not proceed without the character, owner, app, inventory, and
contract context required by the foundation gate.
"""


def setup_foundation_onboarding(
    root: Path,
    app_id: str,
    app_name: str,
    *,
    autonomy_mode: str | None = None,
) -> dict[str, Any]:
    root_status = setup_weave_root(root, autonomy_mode=autonomy_mode)
    autonomy = root_status["autonomy"]
    clean_id = slugify(app_id)
    if app_metadata_path(root, clean_id).exists():
        app = load_app(root, clean_id)
        if app.get("name") != app_name:
            app["name"] = app_name
            write_app(root, app)
    else:
        create_app(root, clean_id, app_name)

    gate = foundation_gate(root, clean_id)
    gate_with_meta = {
        **gate,
        "generated_at": utc_now(),
        "required_documents": {
            "soul.md": "artifacts/general/soul.md",
            "owner-profile.md": "artifacts/general/owner-profile.md",
            "context/app-context.md": f"apps/{clean_id}/context/app-context.md",
            "inventory/app-inventory.md": f"apps/{clean_id}/inventory/app-inventory.md",
            "contract/gestaltian-contract.md": f"apps/{clean_id}/contract/gestaltian-contract.md",
        },
    }
    gate_path = foundation_gate_profile_path(root, clean_id)
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(json.dumps(gate_with_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    workdir = gateway_workdir(root)
    workdir.mkdir(parents=True, exist_ok=True)
    context_path = workdir / "weave-gateway-context.json"
    context = {
        "schema": GATEWAY_CONTEXT_SCHEMA,
        "generated_at": gate_with_meta["generated_at"],
        "weave_root": str(root),
        "app_id": clean_id,
        "app_name": app_name,
        "communication_channel": "telegram",
        "foundation_gate_path": str(gate_path),
        "source_map_path": str(source_map_path(root)),
        "agent_profile_path": str(agent_profile_path(root)),
        "active_app_path": str(active_app_path(root)),
        "gateway_workdir": str(workdir),
        "required_before_app_work": True,
        "question_limit": 3,
        "dashboard_ui_enabled": False,
        "product_lifecycle": [stage.id for stage in STAGES],
        "deterministic_telegram_commands": sorted(TELEGRAM_COMMANDS),
        "autonomy": autonomy,
        "agent_profile": ensure_agent_profile(root),
    }
    context_path.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    agents_path = workdir / "AGENTS.md"
    agents_path.write_text(
        render_gateway_agents(
            root=root,
            app_id=clean_id,
            app_name=app_name,
            gate_path=gate_path,
            context_path=context_path,
            autonomy=autonomy,
        ),
        encoding="utf-8",
    )
    soul_path = workdir / "SOUL.md"
    soul_path.write_text(
        render_gateway_soul(root=root, app_id=clean_id, app_name=app_name, gate_path=gate_path),
        encoding="utf-8",
    )
    return {
        "schema": GATEWAY_CONTEXT_SCHEMA,
        "root_status": root_status,
        "app_id": clean_id,
        "app_name": app_name,
        "foundation_gate": gate_with_meta,
        "foundation_gate_path": str(gate_path),
        "source_map_path": str(source_map_path(root)),
        "gateway_workdir": str(workdir),
        "agents_path": str(agents_path),
        "soul_path": str(soul_path),
        "context_path": str(context_path),
        "gateway_start_cwd": str(workdir),
        "autonomy": autonomy,
    }


def stage_has_artifacts(stage_root: Path) -> bool:
    for child in ("artifacts", "refs"):
        directory = stage_root / child
        if directory.exists() and any(path.is_file() for path in directory.iterdir()):
            return True
    return False


def stage_roots(base: Path, stage: Stage) -> list[Path]:
    roots = [base / "lifecycle" / stage.directory]
    for legacy_directory, mapped_stage in LEGACY_STAGE_ALIASES.items():
        if mapped_stage == stage.id:
            roots.append(base / "lifecycle" / legacy_directory)
    return roots


def derive_stage(root: Path, app_id: str) -> dict[str, Any]:
    base = app_root(root, app_id)
    derived = "intent"
    source_path = ""
    for stage in STAGES:
        matched_root = next((stage_root for stage_root in stage_roots(base, stage) if stage_has_artifacts(stage_root)), None)
        if matched_root:
            derived = stage.id
            source_path = relative(matched_root, root)
    app = load_app(root, app_id)
    if app.get("current_stage") != derived or app.get("stage_source") != "derived":
        app["current_stage"] = derived
        app["stage_source"] = "derived"
        write_app(root, app)
    return {"stage": derived, "stage_source": "derived", "source_path": source_path}


def artifact_checksum(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def list_artifacts(root: Path, app_id: str) -> list[dict[str, str]]:
    base = app_root(root, app_id)
    artifacts: list[dict[str, str]] = []
    if not (base / "lifecycle").exists():
        return artifacts
    for stage in STAGES:
        for stage_root in stage_roots(base, stage):
            for kind in ("artifacts", "refs"):
                directory = stage_root / kind
                if not directory.exists():
                    continue
                for path in sorted(directory.iterdir()):
                    if path.is_file():
                        artifacts.append(
                            {
                                "stage": stage.id,
                                "kind": kind[:-1],
                                "path": relative(path, root),
                                "checksum": artifact_checksum(path),
                            }
                        )
    return artifacts


def latest_changes(root: Path, app_id: str) -> dict[str, Any]:
    categories = {
        "contract": {"types": {"contract.updated", "contract.diff_recorded"}, "latest": None},
        "app_context": {"types": {"app_context.updated"}, "latest": None},
        "artifact": {"types": {"artifact.created", "artifact.updated", "artifact.reference_recorded"}, "latest": None},
        "stage": {"types": {"lifecycle.stage_registered", "lifecycle.stage_derived"}, "latest": None},
        "approval": {"types": {"approval.requested", "approval.resolved"}, "latest": None},
        "window": {"types": {"window.changed"}, "latest": None},
    }
    for event in read_events(root, app_id):
        for bucket in categories.values():
            if event["type"] in bucket["types"]:
                bucket["latest"] = event
    return {name: data["latest"] for name, data in categories.items()}


STAGE_REQUIREMENTS = {
    "intent": [
        "owner intent and success definition",
        "app context",
        "owner preferences for this app",
        "initial lifecycle expectations",
        "likely credential and capability needs",
    ],
    "research": [
        "research questions",
        "evidence sources",
        "domain constraints",
        "unknowns that must be answered before selection",
    ],
    "selection": [
        "candidate approaches",
        "tradeoff decision",
        "selected direction",
        "decision rationale",
    ],
    "plan": [
        "implementation plan",
        "tasks",
        "acceptance checks",
        "risks and stop boundaries",
    ],
    "engineering": [
        "repo/worktree target",
        "implementation packet",
        "code changes",
        "local verification evidence",
    ],
    "qa": [
        "test results",
        "known issues",
        "acceptance check evidence",
        "owner review request",
    ],
    "kpi": [
        "success metrics",
        "instrumentation plan",
        "analytics or reporting capability",
    ],
    "marketing": [
        "marketing goal",
        "channel plan",
        "credential requirements",
        "approval for external/public sends",
    ],
    "iteration": [
        "feedback or observed issue",
        "iteration goal",
        "proposed change",
        "review target",
    ],
    "analysis": [
        "outcome evidence",
        "lessons learned",
        "next decision",
    ],
}


def short_list(values: list[Any], limit: int = 5) -> list[str]:
    items = [str(value) for value in values if str(value).strip()]
    if len(items) <= limit:
        return items
    return items[:limit] + [f"... {len(items) - limit} more"]


def stage_index(stage_id: str) -> int:
    for index, stage in enumerate(STAGES):
        if stage.id == stage_id:
            return index
    return 0


def artifact_counts_by_stage(artifacts: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for artifact in artifacts:
        stage = artifact["stage"]
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def app_stage_state(root: Path, app_id: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = state or app_state(root, app_id)
    app = state["app"]
    gate = state["foundation_gate"]
    stage = state["stage"]["stage"]
    raw_stage_state = str(app.get("stage_state") or "collecting")
    stage_state = raw_stage_state if raw_stage_state in STAGE_STATES else "collecting"
    missing_inputs = short_list(app.get("required_inputs", []), 10)
    owner_questions = short_list(app.get("owner_questions", []), 10)
    required_capabilities = app.get("credential_requirements", [])
    credential_blockers = [
        str(item.get("label") or item.get("id") or item)
        for item in required_capabilities
        if isinstance(item, dict) and item.get("required") is not False and item.get("status") not in {"available", "deferred"}
    ]
    if not gate["passed"]:
        stage_state = "collecting"
        missing_inputs = short_list(gate["missing"] + gate["incomplete"], 10)
        next_action = "Hermes should ask focused foundation questions and update the required documents."
    elif app.get("blockers"):
        stage_state = "blocked"
        next_action = f"Resolve blocker: {app['blockers'][0]}"
    elif credential_blockers and stage in {"kpi", "marketing"}:
        stage_state = "blocked"
        next_action = f"Provide or defer credential capability: {credential_blockers[0]}"
    elif stage_state == "ready_for_review":
        next_action = "Owner review is needed before the lifecycle stage can be marked approved."
    elif stage_state == "approved":
        next_action = "Hermes may continue to the next admitted lifecycle stage."
    else:
        next_action = "Hermes should continue eliciting missing context or drafting the current stage packet."
    requirements = STAGE_REQUIREMENTS.get(stage, [])
    return {
        "stage": stage,
        "stage_state": stage_state,
        "requirements": requirements,
        "missing_inputs": missing_inputs,
        "owner_questions": owner_questions,
        "credential_blockers": credential_blockers,
        "tasks": short_list(app.get("tasks", []), 10),
        "next_action": next_action,
    }


def lifecycle_rows(state: dict[str, Any], stage_status: dict[str, Any]) -> list[dict[str, Any]]:
    current_stage = state["stage"]["stage"]
    current_index = stage_index(current_stage)
    approved = set(state["app"].get("approved_stages", []))
    counts = artifact_counts_by_stage(state["artifacts"])
    rows: list[dict[str, Any]] = []
    for index, stage in enumerate(STAGES):
        if stage.id in approved:
            display_state = "approved"
        elif stage.id == current_stage:
            display_state = stage_status["stage_state"]
        elif counts.get(stage.id):
            display_state = "evidence_recorded"
        elif index < current_index:
            display_state = "not_approved"
        else:
            display_state = "not_started"
        rows.append({"stage": stage.id, "state": display_state, "artifact_count": counts.get(stage.id, 0)})
    return rows


def recent_event_summaries(root: Path, app_id: str, limit: int = 5) -> list[str]:
    events = read_events(root, app_id)
    return [f"{event['type']}: {event['summary']} [{event['stage']}]" for event in events[-limit:]]


def decision_summaries(state: dict[str, Any], limit: int = 5) -> list[str]:
    app_decisions = short_list(state["app"].get("decisions", []), limit)
    if app_decisions:
        return app_decisions
    lines = []
    for category, event in state["latest_changes"].items():
        if event and category in {"contract", "app_context", "approval"}:
            lines.append(f"{category}: {event['summary']}")
    return short_list(lines, limit)


def format_agent_line(profile: dict[str, Any]) -> str:
    return (
        f"model={profile.get('model', 'unknown')}; "
        f"reasoning={profile.get('reasoning_effort', 'unknown')}; "
        f"adapter={profile.get('provider_adapter', 'unknown')}; "
        f"prompt_pack={profile.get('prompt_pack', 'unknown')}"
    )


def contract_diff(root: Path, app_id: str) -> dict[str, Any]:
    diff_dir = app_root(root, app_id) / "contract" / "diffs"
    files = sorted(path for path in diff_dir.glob("*") if path.is_file()) if diff_dir.exists() else []
    return {
        "available": bool(files),
        "diffs": [relative(path, root) for path in files],
    }


def app_state(root: Path, app_id: str) -> dict[str, Any]:
    stage = derive_stage(root, app_id)
    app = load_app(root, app_id)
    state = {
        "schema": "weave-app-state/v0.1",
        "app": app,
        "stage": stage,
        "foundation_gate": foundation_gate(root, app_id),
        "latest_changes": latest_changes(root, app_id),
        "artifacts": list_artifacts(root, app_id),
        "contract_diff": contract_diff(root, app_id),
    }
    stage_status = app_stage_state(root, app_id, state)
    state["stage_status"] = stage_status
    state["lifecycle"] = lifecycle_rows(state, stage_status)
    return state


def list_apps(root: Path, *, include_system: bool = False) -> list[dict[str, Any]]:
    registry = load_registry(root)
    apps: list[dict[str, Any]] = []
    for entry in registry["apps"]:
        state = app_state(root, entry["app_id"])
        app = state["app"]
        if is_system_app(app) and not include_system:
            continue
        apps.append(
            {
                "app_id": app["app_id"],
                "name": app["name"],
                "app_type": "system" if is_system_app(app) else app.get("app_type", "product"),
                "path": entry["path"],
                "stage": state["stage"]["stage"],
                "stage_source": state["stage"]["stage_source"],
                "stage_state": state["stage_status"]["stage_state"],
                "foundation_passed": state["foundation_gate"]["passed"],
                "blocker_count": len(app.get("blockers", [])),
                "next_action": state["stage_status"]["next_action"],
                "last_changed_at": entry.get("last_changed_at", app.get("created_at", "")),
                "contract_version": app.get("contract_version", ""),
            }
        )
    return apps


def root_ready(root: Path) -> bool:
    return registry_path(root).exists()


def safe_list_apps(root: Path, *, include_system: bool = False) -> list[dict[str, Any]]:
    if not root_ready(root):
        return []
    return list_apps(root, include_system=include_system)


def telegram_command_response(
    *,
    command: str,
    text: str,
    payload: dict[str, Any] | None = None,
    handled: bool = True,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema": TELEGRAM_COMMAND_SCHEMA,
        "command": command,
        "handled": handled,
        "deterministic": True,
        "llm_used": False,
        "communication_channel": "telegram",
        "text": text,
        "payload": payload or {},
        "error": error,
    }


def parse_telegram_command(text: str) -> tuple[str, list[str]]:
    stripped = text.strip()
    if not stripped.startswith("/"):
        return "", []
    parts = stripped.split()
    command = parts[0].split("@", 1)[0].lower()
    return command, parts[1:]


def telegram_help_text() -> str:
    lines = ["WEAVE deterministic commands:"]
    for command in sorted(TELEGRAM_COMMANDS):
        lines.append(f"{command} - {TELEGRAM_COMMANDS[command]}")
    return "\n".join(lines)


def foundation_status_label(gate: dict[str, Any]) -> str:
    if gate["passed"]:
        return "passed"
    needed = gate["missing"] + gate["incomplete"]
    if not needed:
        return "blocking"
    return "blocking: " + ", ".join(needed)


def app_status_line(app: dict[str, Any]) -> str:
    gate = "passed" if app["foundation_passed"] else "blocking"
    blockers = f"; blockers={app['blocker_count']}" if app.get("blocker_count") else ""
    return f"- {app['name']} ({app['app_id']}): {app['stage']} / {app['stage_state']}; foundation={gate}{blockers}"


def next_from_apps(apps: list[dict[str, Any]], foundation_blocked: list[dict[str, Any]], app_blocked_ids: list[str]) -> str:
    if foundation_blocked:
        return f"Hermes should collect foundation answers for {foundation_blocked[0]['app_id']}."
    if app_blocked_ids:
        return f"Resolve blocker for {app_blocked_ids[0]}."
    if apps:
        return "No deterministic blocker is recorded; Hermes can continue from the active stage."
    return "Create or select a product app workspace."


def active_app_label(active_app: dict[str, Any]) -> str:
    return active_app.get("app_id") or "none"


def runtime_status_command(root: Path) -> dict[str, Any]:
    runtime_home = runtime_home_from_root(root)
    apps = safe_list_apps(root)
    all_apps = safe_list_apps(root, include_system=True)
    system_apps = [app for app in all_apps if app["app_type"] == "system"]
    foundation_blocked = [app for app in apps if not app["foundation_passed"]]
    app_blocked_ids: list[str] = []
    for app in apps:
        try:
            state = app_state(root, app["app_id"])
        except RuntimeSliceError:
            continue
        if state["app"].get("blockers"):
            app_blocked_ids.append(app["app_id"])
    blocked_ids = sorted({app["app_id"] for app in foundation_blocked} | set(app_blocked_ids))
    autonomy = load_autonomy_policy(root)
    agent_profile = ensure_agent_profile(root)
    provider_status = weave_provider_auth.provider_auth_status(runtime_home / "hermes-home")
    active_app = load_active_app(root)
    source_map = load_source_map(root)
    source_summary = summarize_source_map(source_map)
    next_action = next_from_apps(apps, foundation_blocked, app_blocked_ids)
    attention: list[str] = []
    attention.extend(f"{app['app_id']}: foundation onboarding" for app in foundation_blocked)
    attention.extend(f"{app_id}: app blocker" for app_id in app_blocked_ids)
    if not attention:
        attention.append("none")
    lines = [
        "WEAVE Status",
        "",
        "Agent",
        f"- {format_agent_line(agent_profile)}",
        f"- autonomy={autonomy['mode']}",
        "",
        "Provider Auth",
        f"- state: {provider_status['state']}",
        f"- chat_ready: {str(provider_status['chat_ready']).lower()}",
        f"- provider: {provider_status['provider']}",
        f"- model: {provider_status['model']}",
        "",
        "Apps",
        f"- active_app: {active_app_label(active_app)}",
        f"- product_apps: {len(apps)}",
        f"- system_apps_hidden: {len(system_apps)}",
        f"- blocked_apps: {len(blocked_ids)}",
        f"- foundation_blocked_apps: {len(foundation_blocked)}",
        f"- app_blocked_apps: {len(app_blocked_ids)}",
    ]
    if apps:
        lines.extend(app_status_line(app) for app in apps)
    else:
        lines.append("- none registered")
    lines.extend(
        [
            "",
            "Attention",
            *[f"- {item}" for item in attention],
            "",
            "System",
            f"- runtime_home: {runtime_home}",
            f"- state_root: {root}",
            f"- root_ready: {str(root_ready(root)).lower()}",
            f"- sources: {source_summary['source_count']}",
            f"- canonical_source: {source_summary['canonical_source_id']}",
            f"- runtime_events: {len(read_runtime_events(root))}",
            "",
            "Next",
            f"- {next_action}",
        ]
    )
    return telegram_command_response(
        command="/status",
        text="\n".join(lines),
        payload={
            "root_ready": root_ready(root),
            "runtime_home": str(runtime_home),
            "state_root": str(root),
            "app_count": len(apps),
            "system_app_count": len(system_apps),
            "blocked_app_count": len(blocked_ids),
            "blocked_apps": blocked_ids,
            "foundation_blocked_apps": [app["app_id"] for app in foundation_blocked],
            "app_blocked_apps": app_blocked_ids,
            "active_app": active_app,
            "agent_profile": agent_profile,
            "provider_auth": provider_status,
            "autonomy": autonomy,
            "source_map": source_summary,
            "attention": attention,
            "next_action": next_action,
        },
    )


def source_status_line(source: dict[str, Any]) -> str:
    marker = "sensitive" if source.get("sensitive") else "public"
    return f"{source['label']} ({source['id']}): {source['status']}; {source['role']}; {marker}"


def sources_command(root: Path) -> dict[str, Any]:
    source_map = load_source_map(root)
    sources = source_map.get("sources", [])
    lines = [
        "WEAVE source map",
        f"canonical_source: {source_map.get('canonical_source_id', '')}",
        f"history_sources: {', '.join(source_map.get('history_source_ids', [])) or 'none'}",
    ]
    lines.extend(source_status_line(source) for source in sources)
    next_action = source_map.get("next_unification_action")
    if next_action:
        lines.append(f"next: {next_action}")
    return telegram_command_response(
        command="/sources",
        text="\n".join(lines),
        payload={"source_map": source_map, "summary": summarize_source_map(source_map)},
    )


def autonomy_command(root: Path) -> dict[str, Any]:
    policy = load_autonomy_policy(root)
    lines = [
        "WEAVE autonomy",
        f"mode: {policy['mode']}",
        f"default_action: {policy['default_action']}",
        "approval_channel: telegram_llm_conversation",
        "hard_gates:",
    ]
    lines.extend(f"- {gate['label']}" for gate in policy["hard_approval_gates"])
    return telegram_command_response(command="/autonomy", text="\n".join(lines), payload={"autonomy": policy})


def apps_command(root: Path, args: list[str] | None = None) -> dict[str, Any]:
    args = args or []
    include_system = "--all" in args
    apps = safe_list_apps(root, include_system=include_system)
    if not apps:
        text = "No WEAVE product apps are registered yet." if not include_system else "No WEAVE apps are registered yet."
    else:
        header = "WEAVE apps:" if include_system else "WEAVE product apps:"
        text = header + "\n" + "\n".join(app_status_line(app) for app in apps)
    return telegram_command_response(command="/apps", text=text, payload={"apps": apps, "include_system": include_system})


def resolve_app_id(root: Path, args: list[str]) -> tuple[str, str]:
    if args:
        return slugify(args[0]), "argument"
    active = load_active_app(root)
    if active.get("app_id"):
        return active["app_id"], "active_app"
    apps = safe_list_apps(root)
    if len(apps) == 1:
        return apps[0]["app_id"], "single_product_app"
    raise RuntimeSliceError("No app id was provided and no active app is selected.")


def lifecycle_line(row: dict[str, Any]) -> str:
    suffix = f"; artifacts={row['artifact_count']}" if row["artifact_count"] else ""
    return f"- {row['stage']}: {row['state']}{suffix}"


def render_app_wall(root: Path, app_id: str) -> tuple[str, dict[str, Any]]:
    state = app_state(root, app_id)
    app = state["app"]
    gate = state["foundation_gate"]
    stage_status = state["stage_status"]
    profile = ensure_agent_profile(root)
    decisions = decision_summaries(state)
    recent = recent_event_summaries(root, app_id)
    blockers = [str(blocker) for blocker in app.get("blockers", [])]
    if not gate["passed"]:
        blockers.append(f"foundation {foundation_status_label(gate)}")
    if stage_status["credential_blockers"]:
        blockers.extend(f"credential: {item}" for item in stage_status["credential_blockers"])
    needs = stage_status["missing_inputs"] + stage_status["owner_questions"]
    lines = [
        f"WEAVE App Status: {app['name']} ({app['app_id']})",
        "",
        "Summary",
        f"- type: {'system' if is_system_app(app) else 'product'}",
        f"- stage: {stage_status['stage']}",
        f"- state: {stage_status['stage_state']}",
        f"- foundation: {foundation_status_label(gate)}",
        f"- contract_version: {app.get('contract_version', '')}",
        "",
        "Lifecycle",
        *[lifecycle_line(row) for row in state["lifecycle"]],
        "",
        "Current Stage",
        *[f"- requires: {item}" for item in stage_status["requirements"]],
    ]
    lines.extend(["", "Needs You"])
    lines.extend(f"- {item}" for item in (needs or ["none"]))
    lines.extend(["", "Tasks"])
    lines.extend(f"- {item}" for item in (stage_status["tasks"] or ["none recorded"]))
    lines.extend(["", "Decisions"])
    lines.extend(f"- {item}" for item in (decisions or ["none recorded"]))
    lines.extend(["", "Recent Work"])
    lines.extend(f"- {item}" for item in (recent or ["none recorded"]))
    lines.extend(["", "Blockers"])
    lines.extend(f"- {item}" for item in (blockers or ["none"]))
    lines.extend(
        [
            "",
            "Agent",
            f"- {format_agent_line(profile)}",
            "",
            "Next",
            f"- {stage_status['next_action']}",
        ]
    )
    payload = {
        "app_id": app["app_id"],
        "name": app["name"],
        "app_type": "system" if is_system_app(app) else "product",
        "stage": state["stage"],
        "stage_status": stage_status,
        "lifecycle": state["lifecycle"],
        "foundation_gate": gate,
        "contract_version": app.get("contract_version", ""),
        "artifact_count": len(state["artifacts"]),
        "latest_changes": state["latest_changes"],
        "decisions": decisions,
        "recent_work": recent,
        "blockers": blockers,
        "agent_profile": profile,
    }
    return "\n".join(lines), payload


def app_wall_command(root: Path, args: list[str], *, command: str) -> dict[str, Any]:
    try:
        app_id, source = resolve_app_id(root, args)
        text, payload = render_app_wall(root, app_id)
        payload["app_resolution_source"] = source
        return telegram_command_response(command=command, text=text, payload=payload)
    except RuntimeSliceError as exc:
        return telegram_command_response(
            command=command,
            handled=False,
            error="app_not_found_or_unselected",
            text=str(exc),
            payload={"usage": f"{command} [app_id]"},
        )


def app_command(root: Path, args: list[str]) -> dict[str, Any]:
    return app_wall_command(root, args, command="/app")


def create_app_command(root: Path, args: list[str]) -> dict[str, Any]:
    if not args:
        return telegram_command_response(
            command="/create_app",
            handled=False,
            error="missing_app_name",
            text="Usage: /create_app <name>",
            payload={"usage": "/create_app <name>"},
        )
    name = " ".join(args).strip()
    clean_id = slugify(name)
    if clean_id in SYSTEM_APP_IDS:
        return telegram_command_response(
            command="/create_app",
            handled=False,
            error="reserved_system_app",
            text=f"Reserved system app id cannot be created as a product app: {clean_id}",
            payload={"app_id": clean_id},
        )
    result = create_app(root, clean_id, name)
    active = set_active_app(root, clean_id)
    text = "\n".join(
        [
            f"Created product app: {name} ({clean_id})",
            f"Active app: {active['app_id']}",
            "Next: Hermes should collect or update intent-stage context before lifecycle progress.",
        ]
    )
    return telegram_command_response(
        command="/create_app",
        text=text,
        payload={"result": result, "active_app": active},
    )


def switch_app_command(root: Path, args: list[str]) -> dict[str, Any]:
    if not args:
        return telegram_command_response(
            command="/switch_app",
            handled=False,
            error="missing_app_id",
            text="Usage: /switch_app <app_id>",
            payload={"usage": "/switch_app <app_id>"},
        )
    try:
        active = set_active_app(root, args[0])
    except RuntimeSliceError as exc:
        return telegram_command_response(
            command="/switch_app",
            handled=False,
            error="app_not_found",
            text=str(exc),
            payload={"app_id": slugify(args[0]), "detail": str(exc)},
        )
    return telegram_command_response(
        command="/switch_app",
        text=f"Active app: {active['app_id']}",
        payload={"active_app": active},
    )


def stage_command(root: Path, args: list[str]) -> dict[str, Any]:
    try:
        app_id, source = resolve_app_id(root, args)
        state = app_state(root, app_id)
    except RuntimeSliceError as exc:
        return telegram_command_response(
            command="/stage",
            handled=False,
            error="app_not_found_or_unselected",
            text=str(exc),
            payload={"usage": "/stage [app_id]"},
        )
    stage_status = state["stage_status"]
    lines = [
        f"WEAVE Stage: {state['app']['name']} ({app_id})",
        f"- stage: {stage_status['stage']}",
        f"- state: {stage_status['stage_state']}",
        f"- source: {state['stage']['stage_source']}",
        "Lifecycle:",
        *[lifecycle_line(row) for row in state["lifecycle"]],
        f"Next: {stage_status['next_action']}",
    ]
    return telegram_command_response(
        command="/stage",
        text="\n".join(lines),
        payload={"app_id": app_id, "app_resolution_source": source, "stage_status": stage_status, "lifecycle": state["lifecycle"]},
    )


def requirements_command(root: Path, args: list[str]) -> dict[str, Any]:
    try:
        app_id, source = resolve_app_id(root, args)
        state = app_state(root, app_id)
    except RuntimeSliceError as exc:
        return telegram_command_response(
            command="/requirements",
            handled=False,
            error="app_not_found_or_unselected",
            text=str(exc),
            payload={"usage": "/requirements [app_id]"},
        )
    stage_status = state["stage_status"]
    lines = [
        f"WEAVE Requirements: {state['app']['name']} ({app_id})",
        f"- stage: {stage_status['stage']}",
        f"- state: {stage_status['stage_state']}",
        "Requires:",
        *[f"- {item}" for item in stage_status["requirements"]],
        "Missing or needed:",
        *[f"- {item}" for item in (stage_status["missing_inputs"] + stage_status["owner_questions"] or ["none"])],
    ]
    if stage_status["credential_blockers"]:
        lines.append("Credential capabilities:")
        lines.extend(f"- {item}" for item in stage_status["credential_blockers"])
    return telegram_command_response(
        command="/requirements",
        text="\n".join(lines),
        payload={"app_id": app_id, "app_resolution_source": source, "stage_status": stage_status},
    )


def blockers_command(root: Path) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    lines: list[str] = []
    for app in safe_list_apps(root):
        state = app_state(root, app["app_id"])
        gate = state["foundation_gate"]
        app_blockers = state["app"].get("blockers", [])
        if gate["passed"] and not app_blockers:
            continue
        entry = {
            "app_id": app["app_id"],
            "name": app["name"],
            "stage": app["stage"],
            "foundation_gate": gate,
            "blockers": app_blockers,
        }
        blockers.append(entry)
        reasons = []
        if not gate["passed"]:
            reasons.append(f"foundation {foundation_status_label(gate)}")
        reasons.extend(str(blocker) for blocker in app_blockers)
        lines.append(f"{app['name']} ({app['app_id']}): " + "; ".join(reasons))
    text = "No WEAVE blockers are recorded." if not lines else "WEAVE blockers:\n" + "\n".join(lines)
    return telegram_command_response(command="/blockers", text=text, payload={"blockers": blockers})


def summarize_change_event(category: str, event: dict[str, Any] | None) -> str | None:
    if not event:
        return None
    return f"{category}: {event['summary']} [{event['stage']}]"


def changes_for_app(root: Path, app_id: str) -> dict[str, Any]:
    load_app(root, app_id)
    changes = latest_changes(root, app_id)
    lines = [
        line
        for category, event in changes.items()
        for line in [summarize_change_event(category, event)]
        if line
    ]
    return {"app_id": app_id, "changes": changes, "lines": lines}


def changes_command(root: Path, args: list[str]) -> dict[str, Any]:
    app_ids = [slugify(args[0])] if args else [app["app_id"] for app in safe_list_apps(root)]
    summaries: list[dict[str, Any]] = []
    lines: list[str] = []
    for app_id in app_ids:
        try:
            summary = changes_for_app(root, app_id)
        except RuntimeSliceError as exc:
            return telegram_command_response(
                command="/changes",
                handled=False,
                error="app_not_found",
                text=f"App not found: {app_id}",
                payload={"app_id": app_id, "detail": str(exc)},
            )
        summaries.append(summary)
        if summary["lines"]:
            lines.append(f"{app_id}:\n" + "\n".join(f"- {line}" for line in summary["lines"]))
        else:
            lines.append(f"{app_id}: no categorized changes recorded.")
    text = "No WEAVE apps are registered yet." if not app_ids else "WEAVE changes:\n" + "\n".join(lines)
    return telegram_command_response(command="/changes", text=text, payload={"apps": summaries})


def next_command(root: Path) -> dict[str, Any]:
    apps = safe_list_apps(root)
    for app in apps:
        state = app_state(root, app["app_id"])
        gate = state["foundation_gate"]
        if not gate["passed"]:
            return telegram_command_response(
                command="/next",
                text=(
                    f"Next: Hermes must ask foundation onboarding questions for {app['name']} "
                    f"({app['app_id']}) and update the required documents."
                ),
                payload={"app_id": app["app_id"], "next_action": gate["next_action"], "foundation_gate": gate},
            )
        blockers = state["app"].get("blockers", [])
        if blockers:
            return telegram_command_response(
                command="/next",
                text=f"Next: resolve blocker for {app['name']} ({app['app_id']}): {blockers[0]}",
                payload={"app_id": app["app_id"], "next_action": blockers[0]},
            )
    if apps:
        return telegram_command_response(
            command="/next",
            text="Next: no deterministic blocker is recorded; Hermes can continue from the current lifecycle stage.",
            payload={"app_count": len(apps), "next_action": "continue"},
        )
    return telegram_command_response(
        command="/next",
        text="Next: create or attach a WEAVE app workspace.",
        payload={"app_count": 0, "next_action": "create_app"},
    )


def dispatch_telegram_command(root: Path, text: str) -> dict[str, Any]:
    command, args = parse_telegram_command(text)
    if not command:
        return telegram_command_response(
            command="",
            handled=False,
            error="not_slash_command",
            text="Not a deterministic WEAVE slash command.",
        )
    if command in {"/start", "/help"}:
        return telegram_command_response(
            command=command,
            text=telegram_help_text(),
            payload={"commands": TELEGRAM_COMMANDS, "root_ready": root_ready(root)},
        )
    if command == "/status":
        if args:
            return app_wall_command(root, args, command="/status")
        return runtime_status_command(root)
    if command == "/sources":
        return sources_command(root)
    if command == "/autonomy":
        return autonomy_command(root)
    if command == "/apps":
        return apps_command(root, args)
    if command == "/app":
        return app_command(root, args)
    if command == "/create_app":
        return create_app_command(root, args)
    if command == "/switch_app":
        return switch_app_command(root, args)
    if command == "/stage":
        return stage_command(root, args)
    if command == "/requirements":
        return requirements_command(root, args)
    if command == "/blockers":
        return blockers_command(root)
    if command == "/changes":
        return changes_command(root, args)
    if command == "/next":
        return next_command(root)
    return telegram_command_response(
        command=command,
        handled=False,
        error="unknown_command",
        text=f"Unknown WEAVE command: {command}\n\n{telegram_help_text()}",
        payload={"commands": TELEGRAM_COMMANDS},
    )


def dispatch_rest(root: Path, method: str, request_path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    method = method.upper()
    parts = [part for part in request_path.strip("/").split("/") if part]
    body = body or {}
    if method == "GET" and parts == ["health"]:
        return 200, {
            "schema": REST_SCHEMA,
            "status": "ok",
            "bind": "loopback-only",
            "auth": "generated-bearer-token",
            "real_hermes_runtime": False,
        }
    if method == "GET" and parts == ["runtime", "status"]:
        source_map = load_source_map(root)
        return 200, {
            "schema": REST_SCHEMA,
            "root_ready": (root / "apps" / "registry.json").exists(),
            "app_count": len(load_registry(root)["apps"]),
            "autonomy": load_autonomy_policy(root),
            "source_map": summarize_source_map(source_map),
            "real_hermes_runtime": False,
            "claim": "local first-slice substrate only",
        }
    if method == "POST" and parts == ["runtime", "stop"]:
        return 202, {"schema": REST_SCHEMA, "status": "accepted", "action": "runtime.stop", "effect": "skeleton-no-process"}
    if method == "POST" and parts == ["runtime", "restart-hermes"]:
        return 202, {"schema": REST_SCHEMA, "status": "accepted", "action": "runtime.restart-hermes", "effect": "stub-no-real-hermes"}
    if method == "GET" and parts == ["apps"]:
        return 200, {"schema": REST_SCHEMA, "apps": list_apps(root)}
    if method == "GET" and parts == ["telegram", "commands"]:
        return 200, {"schema": REST_SCHEMA, "commands": TELEGRAM_COMMANDS, "deterministic": True, "llm_used": False}
    if method == "GET" and parts == ["runtime", "autonomy"]:
        return 200, {"schema": REST_SCHEMA, "autonomy": load_autonomy_policy(root)}
    if method == "GET" and parts == ["runtime", "sources"]:
        return 200, {"schema": REST_SCHEMA, "source_map": load_source_map(root)}
    if method == "POST" and parts == ["apps"]:
        result = create_app(root, body.get("app_id", body.get("name", "app")), body.get("name", "Untitled app"))
        return 201, {"schema": REST_SCHEMA, "result": result}
    if len(parts) >= 2 and parts[0] == "apps":
        app_id = parts[1]
        if method == "GET" and parts[2:] == ["state"]:
            return 200, app_state(root, app_id)
        if method == "GET" and parts[2:] == ["events"]:
            return 200, {"schema": REST_SCHEMA, "events": read_events(root, app_id)}
        if method == "POST" and parts[2:] == ["events"]:
            return 201, {"schema": REST_SCHEMA, "event": append_event(root, app_id, body)}
        if method == "GET" and parts[2:] == ["artifacts"]:
            return 200, {"schema": REST_SCHEMA, "artifacts": list_artifacts(root, app_id)}
        if method == "GET" and parts[2:] == ["contract", "diff"]:
            return 200, {"schema": REST_SCHEMA, "contract_diff": contract_diff(root, app_id)}
        if method == "POST" and parts[2:] == ["procedure-feedback"]:
            event = new_event(
                "procedure.feedback_sent",
                app_id,
                load_app(root, app_id).get("current_stage", "intent"),
                body.get("summary", "Procedure feedback recorded."),
                payload=body,
            )
            append_event(root, app_id, event)
            return 201, {"schema": REST_SCHEMA, "event": event}
    return 404, {"schema": REST_SCHEMA, "error": "not_found", "path": request_path}
