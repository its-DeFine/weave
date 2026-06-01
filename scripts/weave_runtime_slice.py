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
import re
import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_SCHEMA = "weave-root/v0.1"
APP_SCHEMA = "weave-app/v0.1"
REGISTRY_SCHEMA = "weave-app-registry/v0.1"
EVENT_SCHEMA = "weave-event/v0.1"
FOUNDATION_SCHEMA = "weave-foundation-gate/v0.1"
REST_SCHEMA = "weave-rest-dispatch/v0.1"
GATEWAY_CONTEXT_SCHEMA = "weave-gateway-context/v0.1"
TELEGRAM_COMMAND_SCHEMA = "weave-telegram-command/v0.1"

TEMPLATE_MARKER = "template-needs-owner-input"

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
}

CREATORS = {"hermes", "weave-runtime", "owner"}

LIFECYCLE_STAGES = [
    ("intent", "01-intent"),
    ("kernel", "02-kernel"),
    ("contract", "03-contract"),
    ("premortem", "04-premortem"),
    ("handoff", "05-handoff"),
    ("implementation", "06-implementation"),
    ("qa", "07-qa"),
    ("kpi-setup", "08-kpi-setup"),
    ("marketing", "09-marketing"),
    ("iteration", "10-iteration"),
    ("analysis", "11-analysis"),
]

APP_DIRS = [
    "context/reality-briefs",
    "inventory",
    "repos/primary",
    "repos/worktrees",
    "repos/prs",
    "contract/versions",
    "contract/diffs",
    "evidence",
    "approvals",
    "ledger/procedure-feedback",
    "exports",
]

TELEGRAM_COMMANDS = {
    "/start": "Show the deterministic WEAVE command surface.",
    "/help": "List deterministic WEAVE commands.",
    "/status": "Show runtime readiness and aggregate app status.",
    "/apps": "List apps, lifecycle stages, and foundation gate state.",
    "/app": "Show one app state. Usage: /app <app_id>",
    "/blockers": "Show apps that need owner or Hermes action.",
    "/changes": "Show latest recorded changes. Usage: /changes [app_id]",
    "/next": "Show the next deterministic owner-visible action.",
}


class RuntimeSliceError(Exception):
    """Raised when the local runtime slice rejects an invalid operation."""


@dataclass(frozen=True)
class Stage:
    id: str
    directory: str


STAGES = [Stage(stage_id, directory) for stage_id, directory in LIFECYCLE_STAGES]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "app"


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


def setup_weave_root(root: Path, *, init_git: bool = True) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    git_tracked = ensure_git_repo(root) if init_git else (root / ".git").exists()

    for directory in ("artifacts/general", "apps", "runtime/profiles", "runtime/logs", "runtime/tokens"):
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
    return {
        "schema": ROOT_SCHEMA,
        "root": str(root),
        "git_tracked": git_tracked,
        "registry_path": "apps/registry.json",
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
        "status": "active",
        "created_at": now,
        "current_stage": "intent",
        "stage_source": "derived",
        "contract_version": "0.1-template",
        "primary_repo": "repos/primary",
        "context_paths": [
            "context/app-context.md",
            "context/user-context-for-this-app.md",
            "context/domain-context.md",
            "context/decisions.md",
        ],
        "ledger_path": "ledger/events.jsonl",
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
            "path": f"apps/{clean_id}",
            "stage": "intent",
            "stage_source": "derived",
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
                "Foundation context is incomplete; Hermes must ask through Telegram before serious app work.",
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
) -> str:
    clean_id = slugify(app_id)
    base = app_root(root, clean_id)
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

## Unskippable Foundation Gate

Before doing app work, implementation planning, approval routing, external
sends, provider changes, deployments, or repo mutations, read the foundation
gate and the required source documents.

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
5. Do not continue into app work until the missing answers are reflected into
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

Normal conversation stays with Hermes through Telegram. Deterministic slash
commands such as `/status`, `/apps`, `/app`, `/blockers`, `/changes`, and
`/next` are handled by the WEAVE runtime command layer and must not be answered
with model-generated text.
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


def setup_foundation_onboarding(root: Path, app_id: str, app_name: str) -> dict[str, Any]:
    root_status = setup_weave_root(root)
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
        "gateway_workdir": str(workdir),
        "required_before_app_work": True,
        "question_limit": 3,
        "deterministic_telegram_commands": sorted(TELEGRAM_COMMANDS),
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
        "gateway_workdir": str(workdir),
        "agents_path": str(agents_path),
        "soul_path": str(soul_path),
        "context_path": str(context_path),
        "gateway_start_cwd": str(workdir),
    }


def stage_has_artifacts(stage_root: Path) -> bool:
    for child in ("artifacts", "refs"):
        directory = stage_root / child
        if directory.exists() and any(path.is_file() for path in directory.iterdir()):
            return True
    return False


def derive_stage(root: Path, app_id: str) -> dict[str, Any]:
    base = app_root(root, app_id)
    derived = "intent"
    source_path = ""
    for stage in STAGES:
        stage_root = base / "lifecycle" / stage.directory
        if stage_has_artifacts(stage_root):
            derived = stage.id
            source_path = relative(stage_root, root)
    app = load_app(root, app_id)
    if app.get("current_stage") != derived or app.get("stage_source") != "derived":
        app["current_stage"] = derived
        app["stage_source"] = "derived"
        write_app(root, app)
    return {"stage": derived, "stage_source": "derived", "source_path": source_path}


def artifact_checksum(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def list_artifacts(root: Path, app_id: str) -> list[dict[str, str]]:
    base = app_root(root, app_id) / "lifecycle"
    artifacts: list[dict[str, str]] = []
    if not base.exists():
        return artifacts
    for stage in STAGES:
        stage_root = base / stage.directory
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
    return {
        "schema": "weave-app-state/v0.1",
        "app": app,
        "stage": stage,
        "foundation_gate": foundation_gate(root, app_id),
        "latest_changes": latest_changes(root, app_id),
        "artifacts": list_artifacts(root, app_id),
        "contract_diff": contract_diff(root, app_id),
    }


def list_apps(root: Path) -> list[dict[str, Any]]:
    registry = load_registry(root)
    apps: list[dict[str, Any]] = []
    for entry in registry["apps"]:
        state = app_state(root, entry["app_id"])
        app = state["app"]
        apps.append(
            {
                "app_id": app["app_id"],
                "name": app["name"],
                "path": entry["path"],
                "stage": state["stage"]["stage"],
                "stage_source": state["stage"]["stage_source"],
                "foundation_passed": state["foundation_gate"]["passed"],
                "last_changed_at": entry.get("last_changed_at", app.get("created_at", "")),
                "contract_version": app.get("contract_version", ""),
            }
        )
    return apps


def root_ready(root: Path) -> bool:
    return registry_path(root).exists()


def safe_list_apps(root: Path) -> list[dict[str, Any]]:
    if not root_ready(root):
        return []
    return list_apps(root)


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
    return f"{app['name']} ({app['app_id']}): stage={app['stage']}; foundation={gate}"


def runtime_status_command(root: Path) -> dict[str, Any]:
    apps = safe_list_apps(root)
    blocked = [app for app in apps if not app["foundation_passed"]]
    lines = [
        "WEAVE runtime status",
        f"root_ready: {str(root_ready(root)).lower()}",
        f"apps: {len(apps)}",
        f"blocked_apps: {len(blocked)}",
    ]
    if blocked:
        lines.append(f"next: Hermes must complete foundation onboarding for {blocked[0]['app_id']}.")
    elif apps:
        lines.append("next: no foundation blockers recorded.")
    else:
        lines.append("next: create or attach an app workspace.")
    return telegram_command_response(
        command="/status",
        text="\n".join(lines),
        payload={
            "root_ready": root_ready(root),
            "app_count": len(apps),
            "blocked_app_count": len(blocked),
            "blocked_apps": [app["app_id"] for app in blocked],
        },
    )


def apps_command(root: Path) -> dict[str, Any]:
    apps = safe_list_apps(root)
    if not apps:
        text = "No WEAVE apps are registered yet."
    else:
        text = "WEAVE apps:\n" + "\n".join(app_status_line(app) for app in apps)
    return telegram_command_response(command="/apps", text=text, payload={"apps": apps})


def app_command(root: Path, args: list[str]) -> dict[str, Any]:
    if not args:
        return telegram_command_response(
            command="/app",
            handled=False,
            error="missing_app_id",
            text="Usage: /app <app_id>",
            payload={"usage": "/app <app_id>"},
        )
    app_id = slugify(args[0])
    try:
        state = app_state(root, app_id)
    except RuntimeSliceError as exc:
        return telegram_command_response(
            command="/app",
            handled=False,
            error="app_not_found",
            text=f"App not found: {app_id}",
            payload={"app_id": app_id, "detail": str(exc)},
        )
    gate = state["foundation_gate"]
    app = state["app"]
    text = "\n".join(
        [
            f"{app['name']} ({app['app_id']})",
            f"stage: {state['stage']['stage']} ({state['stage']['stage_source']})",
            f"foundation: {foundation_status_label(gate)}",
            f"contract_version: {app.get('contract_version', '')}",
            f"artifacts: {len(state['artifacts'])}",
        ]
    )
    payload = {
        "app_id": app["app_id"],
        "name": app["name"],
        "stage": state["stage"],
        "foundation_gate": gate,
        "contract_version": app.get("contract_version", ""),
        "artifact_count": len(state["artifacts"]),
        "latest_changes": state["latest_changes"],
    }
    return telegram_command_response(command="/app", text=text, payload=payload)


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
        return runtime_status_command(root)
    if command == "/apps":
        return apps_command(root)
    if command == "/app":
        return app_command(root, args)
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
        return 200, {
            "schema": REST_SCHEMA,
            "root_ready": (root / "apps" / "registry.json").exists(),
            "app_count": len(load_registry(root)["apps"]),
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
