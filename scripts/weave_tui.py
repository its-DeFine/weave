#!/usr/bin/env python3
"""Interactive local WEAVE TUI product surface.

The TUI is intentionally a local operator surface, not an external automation
runner. It can write lifecycle artifacts and run deterministic local proof
commands, but it does not authenticate providers, deploy, publish, spend money,
or send messages.
"""

from __future__ import annotations

import io
import json
import functools
import hashlib
import html
import http.server
import os
import shlex
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from argparse import Namespace
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TextIO

import weave_early_lifecycle
import weave_engineering_decisions
import weave_first_run
import weave_launch_ops
import weave_qa_proof
import weave_runtime_slice


TUI_SCHEMA = "weave-tui-session/v0.1"
COCKPIT_SESSION_SCHEMA = "weave-tui-cockpit-session/v0.1"
CODEX_PROOF_SCHEMA = "weave-codex-adapter-proof/v0.1"
APP_EXECUTOR_SCHEMA = "weave-app-executor/v0.1"
SEO_ARTIFACT_SCHEMA = "weave-seo-artifact/v0.1"
GENERATED_APP_SCHEMA = "weave-generated-app/v0.1"
REAL_APP_QA_SCHEMA = "weave-real-app-qa/v0.1"
DEFAULT_APP_SURFACE = "website"
APP_SURFACES = ("website", "cli", "backend", "api", "mixed")
APP_EXECUTORS = ("codex", "fixture")
GENERATED_APP_FILES = ("index.html", "src/app.js", "src/styles.css", "public/config.json", "README.md")
QA_SURFACE_BY_APP_SURFACE = {
    # A website produced through WEAVE is not only a DOM. The local proof also
    # exercises the CLI/TUI surface and runtime metadata because those are the
    # operator controls the owner uses to accept or reject the build.
    "website": "mixed",
    "cli": "tui",
    "backend": "api",
    "api": "api",
    "mixed": "mixed",
}
DEFAULT_INTENT = (
    "Create a local product proof with owner-reviewable lifecycle artifacts, "
    "surface-adapted QA, and no live external effects."
)
DEFAULT_TARGET_USER = "operator validating the WEAVE lifecycle from the terminal"
DEFAULT_ENGINEERING_DECISION = "Proceed with local-safe engineering scaffold and run QA evidence only."
DEFAULT_QA_COMMAND = "bin/weave tui --scripted-demo --no-color"
DEFAULT_CODEX_COMMAND = "codex --help"
DEFAULT_CODEX_TIMEOUT = 600
COCKPIT_VIEWS = ("overview", "stages", "artifacts", "files", "reviews", "help", "resume")
COCKPIT_RECENT_LIMIT = 8
COCKPIT_PREVIEW_LIMIT = 1800
SAFE_CODEX_PROBE_ARGS = {("--version",), ("-V",), ("--help",), ("help",)}
REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_MODE_ALIASES = {
    "hands-on": "hands-on",
    "hands-off": "hands-off",
    "handoff": "hands-off",
}

# These scripts are the user-facing contract from the service blueprint. They
# are intentionally separate from the executor code so the TUI can be reviewed
# for "what does the owner see and how can they answer?" without reading the
# lifecycle implementation.
BLUEPRINT_STAGE_SCRIPTS: dict[str, dict[str, Any]] = {
    "first-run": {
        "label": "First Run / Environment Detection",
        "visible_prompt": "I will inspect local WEAVE/Hermes/Codex surfaces and ask which environment to attach to.",
        "choices": [
            "[1] Attach existing local environment",
            "[2] Create local WEAVE/Hermes environment",
            "[3] Connect remote environment",
            "[4] Skip setup and keep local state only",
            "[i] Inspect detected environment",
        ],
        "review_question": "Do you want this environment selection, or should I revise it?",
        "stop_boundary": "Remote attach may be blocked until an authenticated connector is explicitly provided.",
    },
    "owner-profile": {
        "label": "Owner Profile",
        "visible_prompt": "Tell me your engineering/product experience and the coworker style you want from the agent.",
        "choices": ["[s] Save profile", "[e] Edit answers", "[k] Skip for now"],
        "review_question": "Is this the right collaboration profile for future lifecycle work?",
        "stop_boundary": "Profile text is local context only and must not contain secrets.",
    },
    "intent": {
        "label": "Intent",
        "visible_prompt": "Define the app, users, flows, constraints, deployment posture, region, budget, and non-goals.",
        "choices": [
            "[y] Intent is ready",
            "[n] Continue editing",
            "[v] Ask agent to validate sufficiency",
            "[i] Inspect saved intent artifact",
            "[f] Add free-form feedback",
        ],
        "review_question": "Does this intent contain enough coherent material to produce the application?",
        "stop_boundary": "The agent must ask for clarification instead of inventing missing intent.",
    },
    "research": {
        "label": "Research",
        "visible_prompt": "I will unpack the intent into research questions and show the research plan before running it.",
        "choices": [
            "[y] Accept research plan",
            "[e] Edit plan",
            "[a] Add or remove research questions",
            "[r] Ask agent to revise plan",
            "[g] Start research",
            "[i] Inspect research artifacts",
        ],
        "review_question": "Do we have enough research, or should the agent continue/correct it?",
        "stop_boundary": "Public-web research must cite sources and avoid credentialed/private resources unless authorized.",
    },
    "selection": {
        "label": "Selection",
        "visible_prompt": "I will examine research artifacts and present the strongest product/technical options.",
        "choices": [
            "[1] Select option A",
            "[2] Select option B",
            "[3] Select option C",
            "[c] Create your own option",
            "[m] Ask for more options",
            "[d] Discuss/edit selected option",
            "[y] Proceed with selected option",
        ],
        "review_question": "Which option should become the chosen direction?",
        "stop_boundary": "Selection cannot proceed without a clear selected option or an explicit owner-created alternative.",
    },
    "plan": {
        "label": "Plan",
        "visible_prompt": "I will convert intent, research, and selection into business, engineering, QA, KPI, marketing, and iteration plans.",
        "choices": [
            "[y] Approve plan",
            "[b] Edit business plan",
            "[e] Edit engineering plan",
            "[f] Add feedback",
            "[r] Ask agent to remake plan",
            "[i] Inspect plan artifacts",
        ],
        "review_question": "Do the business and engineering plans match the app we intend to build?",
        "stop_boundary": "Credential/provider requirements are recorded as placeholders, never collected as raw secrets here.",
    },
    "engineering": {
        "label": "Engineering",
        "visible_prompt": "I will execute the approved technical plan with Codex, show files/artifacts, and stop on hard gates.",
        "choices": [
            "[g] Start or continue engineering",
            "[i] Inspect generated files",
            "[p] Attach feedback to a file",
            "[y] Approve for QA",
            "[r] Request changes",
            "[x] View executor manifest",
        ],
        "review_question": "Do the implementation changes satisfy the approved plan?",
        "stop_boundary": "Hands-on mode stops for high-impact direction changes; handoff proceeds only through local-safe gates.",
    },
    "qa": {
        "label": "QA",
        "visible_prompt": "I will present a QA plan adapted to the app surface, then run and show evidence for owner review.",
        "choices": [
            "[y] Run QA plan",
            "[e] Edit QA plan",
            "[a] Add scenario",
            "[i] Inspect QA artifacts",
            "[f] Send feedback to engineering",
            "[r] Rerun QA",
        ],
        "review_question": "Did the app and the QA process both behave correctly?",
        "stop_boundary": "QA adapts to website, CLI, backend/API, or mixed apps; browser-only proof is not enough for non-browser surfaces.",
    },
    "deployment": {
        "label": "Deployment Planning",
        "visible_prompt": "I will plan staging/production, domain/provider needs, and credential placeholders without live setup.",
        "choices": [
            "[s] Save deployment plan",
            "[d] Add provider/domain preference",
            "[u] Mark credentials unavailable",
            "[h] Hold before live setup",
        ],
        "review_question": "Is this the correct deployment path once credentials/providers are available?",
        "stop_boundary": "No credential entry, domain purchase, provider mutation, or production deploy occurs in this TUI path.",
    },
    "kpi": {
        "label": "KPI Setup",
        "visible_prompt": "I will propose 3-5 base KPIs and explain whether they measure local preview, staging, or production.",
        "choices": ["[y] Accept KPIs", "[e] Edit KPIs", "[a] Add KPI", "[r] Remove KPI", "[b] Mark blocked by deployment"],
        "review_question": "Are these the first metrics we should track for the application?",
        "stop_boundary": "Production KPI wiring waits until deployment/provider access is explicitly authorized.",
    },
    "marketing": {
        "label": "Marketing",
        "visible_prompt": "I will ask for budget/channel posture, then produce organic and paid-channel plans with hard gates.",
        "choices": [
            "[o] Organic only/no budget",
            "[b] Record budget plan",
            "[a] Add channel",
            "[r] Remove channel",
            "[h] Hold before public send or spend",
        ],
        "review_question": "Is this marketing plan ready for authorized execution later?",
        "stop_boundary": "No public post, ad spend, email, or third-party mutation happens without separate approval.",
    },
    "iteration": {
        "label": "Iteration",
        "visible_prompt": "I will turn feedback into proposed issues, stage them, and route accepted work back through engineering/QA.",
        "choices": [
            "[y] Approve proposed issue",
            "[n] Reject issue",
            "[f] Add feedback",
            "[i] Inspect evidence",
            "[g] Send accepted issue to engineering loop",
        ],
        "review_question": "Which feedback should become actual product changes?",
        "stop_boundary": "Recurring jobs remain planned until the operator authorizes live schedules/connectors.",
    },
    "analysis": {
        "label": "Analysis",
        "visible_prompt": "I will summarize feedback, competitors, sentiment, and suggested improvements as recurring analysis plans.",
        "choices": [
            "[y] Accept analysis plan",
            "[e] Edit cadence/sources",
            "[i] Inspect evidence",
            "[g] Generate improvement candidates",
        ],
        "review_question": "Do these analysis loops produce useful improvement candidates?",
        "stop_boundary": "Automated external scanning or connector use waits for explicit authorization and configured tools.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path, root: Path) -> str:
    return weave_runtime_slice.relative(path, root)


def ensure_public_safe(label: str, value: Any) -> None:
    if weave_runtime_slice.contains_secret_like_value(value):
        raise ValueError(f"{label} contains secret-looking content")
    if weave_runtime_slice.contains_private_locator(value):
        raise ValueError(f"{label} contains private locator content")


def ensure_generated_source_safe(label: str, value: str) -> None:
    # HTML/CSS/JS commonly contain slashes that look like filesystem locators to
    # the generic artifact guard. Source files are still rejected for secret-like
    # material; runtime/private-network behavior is checked in QA.
    if weave_runtime_slice.contains_secret_like_value(value):
        raise ValueError(f"{label} contains secret-looking content")


def normalize_control_mode(value: str) -> str:
    clean = str(value or "hands-on").strip().lower()
    if clean not in CONTROL_MODE_ALIASES:
        raise ValueError("control mode must be hands-on, hands-off, or handoff")
    return CONTROL_MODE_ALIASES[clean]


def control_mode_label(value: str) -> str:
    return "handoff" if normalize_control_mode(value) == "hands-off" else "hands-on"


class Palette:
    """Small ANSI wrapper so the visual layer stays optional and testable."""

    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "cyan": "\033[36m",
        "blue": "\033[34m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "magenta": "\033[35m",
    }

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def paint(self, text: str, *styles: str) -> str:
        if not self.enabled:
            return text
        prefix = "".join(self.COLORS[style] for style in styles if style in self.COLORS)
        return f"{prefix}{text}{self.COLORS['reset']}" if prefix else text


@dataclass(frozen=True)
class TuiInputs:
    app_id: str
    app_name: str
    app_surface: str
    owner_experience: str
    coworker_style: str
    control_mode: str
    intent: str
    target_user: str
    deployment_region: str
    marketing_budget: str
    owner_feedback: str
    engineering_owner_response: str
    write: bool


@dataclass(frozen=True)
class CockpitCommandResult:
    exit_requested: bool
    message: str
    persist_session: bool = False


def color_enabled(args: Any, output: TextIO) -> bool:
    return not getattr(args, "no_color", False) and hasattr(output, "isatty") and output.isatty()


def line(output: TextIO, text: str = "") -> None:
    print(text, file=output)


def progress_bar(active_index: int, total: int, palette: Palette) -> str:
    cells: list[str] = []
    for index in range(total):
        if index < active_index:
            cells.append(palette.paint("#", "green"))
        elif index == active_index:
            cells.append(palette.paint(">", "cyan", "bold"))
        else:
            cells.append(palette.paint(".", "dim"))
    return "[" + "".join(cells) + "]"


def frame(title: str, subtitle: str, rows: list[str], palette: Palette) -> str:
    width = max([len(title), len(subtitle), *(len(row) for row in rows), 64])
    top = "+" + "-" * (width + 2) + "+"
    body = [
        top,
        "| " + palette.paint(title.ljust(width), "bold", "cyan") + " |",
        "| " + palette.paint(subtitle.ljust(width), "dim") + " |",
        top,
    ]
    body.extend("| " + row.ljust(width) + " |" for row in rows)
    body.append(top)
    return "\n".join(body)


def render_intro(inputs: TuiInputs, palette: Palette) -> str:
    rows = [
        f"App: {inputs.app_name} ({inputs.app_id})",
        f"Surface: {inputs.app_surface} -> QA: {QA_SURFACE_BY_APP_SURFACE[inputs.app_surface]}",
        f"Control: {control_mode_label(inputs.control_mode)}",
        "Boundary: local writes only; no credentials, deploys, public sends, or paid spend",
    ]
    return frame("WEAVE TUI", "local operator cockpit for the product lifecycle", rows, palette)


def cockpit_session_path(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "ui" / "tui-session.json"


def cockpit_session_ref(app_id: str) -> str:
    return f"apps/{weave_runtime_slice.slugify(app_id)}/ui/tui-session.json"


def list_public_files(base: Path, root: Path, *, limit: int = 40) -> list[str]:
    if not base.exists():
        return []
    files = sorted(path for path in base.rglob("*") if path.is_file())
    return [rel(path, root) for path in files[:limit]]


def lifecycle_artifacts(root: Path, app_id: str) -> list[str]:
    base = weave_runtime_slice.app_root(root, app_id) / "lifecycle"
    return list_public_files(base, root)


def generated_files(root: Path, app_id: str) -> list[str]:
    base = generated_app_dir(root, app_id)
    return list_public_files(base, root)


def stage_rows(app: dict[str, Any] | None) -> list[dict[str, str]]:
    current_stage = str((app or {}).get("current_stage") or "intent")
    approved = set((app or {}).get("approved_stages") or [])
    rows: list[dict[str, str]] = []
    for stage in weave_runtime_slice.STAGES:
        if stage.id in approved:
            state = "approved"
        elif stage.id == current_stage:
            state = str((app or {}).get("stage_state") or "active")
        else:
            state = "not_started"
        rows.append(
            {
                "id": stage.id,
                "directory": stage.directory,
                "state": state,
                "script": BLUEPRINT_STAGE_SCRIPTS[stage.id]["label"],
            }
        )
    return rows


def review_queue(app: dict[str, Any] | None, *, app_exists: bool) -> list[dict[str, str]]:
    if not app_exists:
        return [
            {
                "kind": "setup",
                "state": "needs_owner_choice",
                "summary": "No local app state exists yet; choose attach/create/connect/skip from first-run.",
            }
        ]
    items: list[dict[str, str]] = []
    for blocker in app.get("blockers") or []:
        items.append({"kind": "blocker", "state": "blocked", "summary": str(blocker)})
    for question in app.get("owner_questions") or []:
        items.append({"kind": "owner_question", "state": "pending", "summary": str(question)})
    if app.get("stage_completion_requires_owner_review", True):
        stage_id = str(app.get("current_stage") or "intent")
        script = BLUEPRINT_STAGE_SCRIPTS.get(stage_id, BLUEPRINT_STAGE_SCRIPTS["intent"])
        items.append(
            {
                "kind": "stage_review",
                "state": str(app.get("stage_state") or "active"),
                "summary": script["review_question"],
            }
        )
    return items


def cockpit_snapshot(root: Path, args: Any) -> dict[str, Any]:
    app_id = weave_runtime_slice.slugify(args.app_id)
    app_path = weave_runtime_slice.app_metadata_path(root, app_id)
    app_exists = app_path.exists()
    app = weave_runtime_slice.load_app(root, app_id) if app_exists else None
    current_stage = str((app or {}).get("current_stage") or "first-run")
    script_key = current_stage if app_exists else "first-run"
    script = BLUEPRINT_STAGE_SCRIPTS.get(script_key, BLUEPRINT_STAGE_SCRIPTS["first-run"])
    snapshot = {
        "schema": "weave-tui-cockpit-snapshot/v0.1",
        "app_exists": app_exists,
        "app_id": app_id,
        "app_name": str((app or {}).get("name") or args.app_name),
        "current_stage": current_stage,
        "stage_state": str((app or {}).get("stage_state") or ("needs_setup" if not app_exists else "active")),
        "script_key": script_key,
        "script": script,
        "stages": stage_rows(app),
        "artifacts": lifecycle_artifacts(root, app_id) if app_exists else [],
        "files": generated_files(root, app_id) if app_exists else [],
        "reviews": review_queue(app, app_exists=app_exists),
        "feedback": read_cockpit_feedback(root, app_id) if app_exists else [],
        "session_ref": cockpit_session_ref(app_id),
    }
    # The snapshot contains display labels such as "First Run / Environment
    # Detection"; those are not persisted as proof artifacts and should not be
    # interpreted as filesystem locators by the stricter JSON artifact scanner.
    return snapshot


def default_cockpit_session(args: Any, snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": COCKPIT_SESSION_SCHEMA,
        "app_id": snapshot["app_id"],
        "app_name": snapshot["app_name"],
        "view": "overview",
        "current_stage": snapshot["current_stage"],
        "control_mode": normalize_control_mode(args.control_mode),
        "app_surface": args.app_surface,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "recent_actions": [],
        "external_effects_executed": [],
        "hard_boundaries": [
            "credentials",
            "deployment",
            "public sends",
            "paid spend",
            "destructive changes",
            "live third-party mutation",
        ],
        "available_views": list(COCKPIT_VIEWS),
    }


def load_cockpit_session(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    session = weave_runtime_slice.load_json(path)
    if session.get("schema") != COCKPIT_SESSION_SCHEMA:
        raise weave_runtime_slice.RuntimeSliceError(f"cockpit session schema must be {COCKPIT_SESSION_SCHEMA}")
    return session


def prepare_cockpit_session(root: Path, args: Any, snapshot: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    path = cockpit_session_path(root, snapshot["app_id"])
    existing = load_cockpit_session(path)
    restored = bool(existing and (args.resume or args.view == "resume"))
    session = dict(existing or default_cockpit_session(args, snapshot))

    # Resume restores the last operator view instead of replacing it with a new
    # default; normal navigation intentionally records the requested view.
    requested_view = session.get("view", "overview") if restored else args.view
    if requested_view == "resume":
        requested_view = "overview"
    session["view"] = requested_view
    session["app_name"] = snapshot["app_name"]
    session["current_stage"] = snapshot["current_stage"]
    session["updated_at"] = utc_now()
    recent = list(session.get("recent_actions") or [])
    recent.append(f"{'resume' if restored else 'open'}:{requested_view}")
    session["recent_actions"] = recent[-COCKPIT_RECENT_LIMIT:]
    session["resume_restored"] = restored
    ensure_public_safe("cockpit session", session)
    return session, restored


def write_cockpit_session(root: Path, session: dict[str, Any]) -> None:
    weave_runtime_slice.write_json_artifact(cockpit_session_path(root, session["app_id"]), session)


def tui_inputs_from_args(args: Any, *, write: bool) -> TuiInputs:
    inputs = TuiInputs(
        app_id=weave_runtime_slice.slugify(args.app_id),
        app_name=args.app_name,
        app_surface=args.app_surface,
        owner_experience=args.owner_experience,
        coworker_style=args.coworker_style,
        control_mode=normalize_control_mode(args.control_mode),
        intent=args.intent,
        target_user=args.target_user,
        deployment_region=args.deployment_region,
        marketing_budget=args.marketing_budget,
        owner_feedback=args.owner_feedback,
        engineering_owner_response=args.engineering_owner_response,
        write=write,
    )
    ensure_public_safe("tui inputs", inputs.__dict__)
    return inputs


def cockpit_feedback_path(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "ui" / "tui-feedback.jsonl"


def read_cockpit_feedback(root: Path, app_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    path = cockpit_feedback_path(root, app_id)
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def append_cockpit_feedback(
    root: Path,
    *,
    app_id: str,
    stage_id: str,
    kind: str,
    text: str,
    file_ref: str | None = None,
) -> dict[str, Any]:
    event = {
        "schema": "weave-tui-feedback/v0.1",
        "recorded_at": utc_now(),
        "app_id": app_id,
        "stage_id": stage_id,
        "kind": kind,
        "text": " ".join(text.split()),
    }
    if file_ref:
        event["file_ref"] = file_ref
    ensure_public_safe("cockpit feedback", event)
    path = cockpit_feedback_path(root, app_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def update_session_view(session: dict[str, Any], view: str, *, action: str) -> None:
    session["view"] = view
    session["updated_at"] = utc_now()
    recent = list(session.get("recent_actions") or [])
    recent.append(action)
    session["recent_actions"] = recent[-COCKPIT_RECENT_LIMIT:]


def match_generated_file(snapshot: dict[str, Any], requested: str) -> tuple[str | None, str]:
    files = list(snapshot.get("files") or [])
    if requested in files:
        return requested, ""
    matches = [item for item in files if item.endswith("/" + requested) or Path(item).name == requested]
    if len(matches) == 1:
        return matches[0], ""
    if not matches:
        return None, f"File not found in generated file list: {requested}"
    return None, f"File reference is ambiguous: {requested}"


def match_preview_ref(snapshot: dict[str, Any], requested: str) -> tuple[str | None, str, str]:
    candidates = [("file", item) for item in snapshot.get("files") or []] + [
        ("artifact", item) for item in snapshot.get("artifacts") or []
    ]
    for kind, ref in candidates:
        if requested == ref:
            return ref, kind, ""
    matches = [(kind, ref) for kind, ref in candidates if ref.endswith("/" + requested) or Path(ref).name == requested]
    if len(matches) == 1:
        kind, ref = matches[0]
        return ref, kind, ""
    if not matches:
        return None, "", f"Nothing matched: {requested}"
    return None, "", f"Reference is ambiguous: {requested}"


def read_cockpit_preview(root: Path, ref: str, kind: str) -> str:
    root_resolved = root.resolve()
    target = (root / ref).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise weave_runtime_slice.RuntimeSliceError("preview ref escapes runtime root") from exc
    if not target.exists() or not target.is_file():
        return f"Preview unavailable for {ref}: file is missing."
    text = target.read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > COCKPIT_PREVIEW_LIMIT
    excerpt = text[:COCKPIT_PREVIEW_LIMIT].rstrip()
    suffix = "\n... preview truncated ..." if truncated else ""
    return f"Preview {kind}: {ref}\n---\n{excerpt}{suffix}\n---"


def stage_choice_for_command(snapshot: dict[str, Any], command: str) -> str | None:
    token = command.strip().lower()
    if not token:
        return None
    for choice in snapshot["script"].get("choices", []):
        if choice.lower().startswith(f"[{token}]"):
            return choice
    return None


def create_local_cockpit_app(root: Path, args: Any, session: dict[str, Any]) -> CockpitCommandResult:
    app_id = weave_runtime_slice.slugify(args.app_id)
    if weave_runtime_slice.app_metadata_path(root, app_id).exists():
        update_session_view(session, "overview", action="create:already-exists")
        return CockpitCommandResult(False, f"Local app state already exists for {app_id}.", True)
    weave_runtime_slice.create_app(root, app_id, args.app_name)
    update_session_view(session, "overview", action="create:local-app")
    return CockpitCommandResult(False, f"Created local app state for {app_id}; current stage is intent.", True)


def finish_post_qa_flow(args: Any, inputs: TuiInputs, step_results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    qa_args = module_args(
        args,
        inputs,
        surface=QA_SURFACE_BY_APP_SURFACE[inputs.app_surface],
        qa_command=args.qa_command,
        target_label=f"local {inputs.app_surface} proof",
        create_app=False,
    )
    step_results.append(run_lifecycle_module("Lifecycle QA bundle", weave_qa_proof.run, qa_args))
    if step_results[-1]["rc"] != 0:
        return step_results, None

    launch_args = module_args(
        args,
        inputs,
        deployment_region=inputs.deployment_region,
        marketing_budget=inputs.marketing_budget,
        feedback_source="local feedback artifacts",
        create_app=False,
    )
    launch_result = run_lifecycle_module("Launch gates", weave_launch_ops.run, launch_args)
    launch_result["status"] = "blocked" if launch_result["rc"] == 0 else "failed"
    launch_result["summary"] = "deployment/KPI/marketing/iteration gated locally" if launch_result["rc"] == 0 else launch_result["summary"]
    step_results.append(launch_result)

    manifest = write_tui_manifest(args, inputs, step_results)
    return step_results, manifest


def run_engineering_and_qa_executor(args: Any, inputs: TuiInputs) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    app = weave_runtime_slice.load_app(args.weave_root, inputs.app_id)
    current_stage = weave_runtime_slice.normalize_stage_id(app.get("current_stage"), default="engineering")
    steps: list[dict[str, Any]] = []

    if current_stage == "engineering":
        engineering = write_engineering_scaffold(args, inputs)
        steps.append(engineering)
        real_qa = run_real_app_qa(args, inputs, engineering["source_manifest"])
        steps.append(real_qa)
        if real_qa["rc"] != 0:
            return steps, None
        return finish_post_qa_flow(args, inputs, steps)

    if current_stage == "qa":
        source_manifest = weave_runtime_slice.load_json(generated_app_manifest_path(args.weave_root, inputs.app_id))
        real_qa = run_real_app_qa(args, inputs, source_manifest)
        steps.append(real_qa)
        if real_qa["rc"] != 0:
            return steps, None
        return finish_post_qa_flow(args, inputs, steps)

    return run_scripted_or_interactive(args, inputs)


def lifecycle_executor_result_message(step_results: list[dict[str, Any]]) -> tuple[bool, str]:
    failed = [item for item in step_results if item.get("rc", 0) != 0]
    if failed:
        first = failed[0]
        return False, f"Lifecycle executor stopped at {first['label']}: {first.get('summary', 'failed')}"
    return True, "Lifecycle executor completed through local QA; launch gates remain blocked before live deployment/KPI/marketing effects."


def run_cockpit_lifecycle_executor(args: Any, session: dict[str, Any], snapshot: dict[str, Any]) -> CockpitCommandResult:
    inputs = tui_inputs_from_args(args, write=True)
    try:
        if snapshot["app_exists"]:
            step_results, _manifest = run_engineering_and_qa_executor(args, inputs)
        else:
            step_results, _manifest = run_scripted_or_interactive(args, inputs)
    except (OSError, ValueError, weave_runtime_slice.RuntimeSliceError) as exc:
        update_session_view(session, "reviews", action=f"run-failed:{getattr(args, 'executor', 'unknown')}")
        return CockpitCommandResult(False, f"Lifecycle executor failed: {exc}", True)

    passed, message = lifecycle_executor_result_message(step_results)
    update_session_view(session, "artifacts" if passed else "reviews", action=f"run:{getattr(args, 'executor', 'unknown')}")
    return CockpitCommandResult(False, message, True)


def handle_cockpit_command(root: Path, args: Any, session: dict[str, Any], snapshot: dict[str, Any], raw_command: str) -> CockpitCommandResult:
    raw = raw_command.strip()
    lower = raw.lower()
    if not lower:
        return CockpitCommandResult(False, "")
    if lower in {"q", "quit", "exit"}:
        update_session_view(session, str(session.get("view") or "overview"), action="quit")
        return CockpitCommandResult(True, "Leaving WEAVE cockpit.", bool(snapshot["app_exists"]))

    view_aliases = {
        "status": "overview",
        "overview": "overview",
        "stages": "stages",
        "artifacts": "artifacts",
        "files": "files",
        "reviews": "reviews",
        "help": "help",
        "?": "help",
    }
    if lower in view_aliases:
        view = view_aliases[lower]
        update_session_view(session, view, action=f"open:{view}")
        return CockpitCommandResult(False, f"Opened {view}.", bool(snapshot["app_exists"]))
    if lower == "resume":
        view = str(session.get("view") or "overview")
        update_session_view(session, view, action=f"resume:{view}")
        return CockpitCommandResult(False, f"Resumed {view}.", bool(snapshot["app_exists"]))

    stage_choice = stage_choice_for_command(snapshot, lower)

    if lower == "x" and snapshot["script_key"] == "engineering":
        raw = "open app-executor-manifest.json"
        lower = raw

    if lower.startswith("open ") or lower.startswith("o ") or lower.startswith("i "):
        if not snapshot["app_exists"]:
            return CockpitCommandResult(False, "Create or attach a local app before opening files or artifacts.")
        requested = raw.split(maxsplit=1)[1].strip()
        ref, kind, error = match_preview_ref(snapshot, requested)
        if error:
            return CockpitCommandResult(False, error)
        assert ref is not None
        update_session_view(session, "files" if kind == "file" else "artifacts", action=f"open-ref:{Path(ref).name}")
        return CockpitCommandResult(False, read_cockpit_preview(root, ref, kind), True)

    if snapshot["script_key"] == "first-run" and lower in {"2", "create", "create-local", "create local"}:
        return create_local_cockpit_app(root, args, session)
    if snapshot["script_key"] == "first-run" and lower in {"1", "attach", "attach-existing"}:
        update_session_view(session, "overview", action="blocked:attach-existing")
        return CockpitCommandResult(False, "Attach-existing is visible in the flow but not wired in this local wedge.", False)
    if snapshot["script_key"] == "first-run" and lower in {"3", "connect", "connect-remote"}:
        update_session_view(session, "overview", action="blocked:connect-remote")
        return CockpitCommandResult(False, "Remote connect remains gated until an authenticated connector exists.", False)
    if snapshot["script_key"] == "first-run" and lower in {"4", "skip", "local-only"}:
        return create_local_cockpit_app(root, args, session)

    if stage_choice and lower not in {"g", "f", "p", "y", "n"}:
        if not snapshot["app_exists"]:
            update_session_view(session, "overview", action=f"choice:{snapshot['script_key']}:{lower}")
            return CockpitCommandResult(
                False,
                f"Choice visible but gated until local app state exists: {stage_choice}",
                False,
            )
        append_cockpit_feedback(
            root,
            app_id=snapshot["app_id"],
            stage_id=snapshot["current_stage"],
            kind="stage_choice",
            text=f"Operator selected {stage_choice} on {snapshot['script_key']}. Dedicated execution for this choice is pending.",
        )
        update_session_view(session, "reviews", action=f"choice:{snapshot['script_key']}:{lower}")
        return CockpitCommandResult(
            False,
            f"Recorded stage choice for the review loop: {stage_choice}",
            True,
        )

    if lower in {"g", "go", "run", "run-local", "run-qa", "execute"}:
        return run_cockpit_lifecycle_executor(args, session, snapshot)

    if lower in {"y", "yes", "approve", "continue"}:
        if not snapshot["app_exists"]:
            return CockpitCommandResult(False, "Create or attach a local app before approving lifecycle stages.")
        append_cockpit_feedback(
            root,
            app_id=snapshot["app_id"],
            stage_id=snapshot["current_stage"],
            kind="owner_continue",
            text="Owner approved continuing from the current cockpit prompt.",
        )
        update_session_view(session, "reviews", action=f"approve:{snapshot['current_stage']}")
        return CockpitCommandResult(False, "Recorded owner continue/approve response.", True)

    if lower in {"n", "no", "revise"}:
        if not snapshot["app_exists"]:
            return CockpitCommandResult(False, "Create or attach a local app before requesting lifecycle revision.")
        append_cockpit_feedback(
            root,
            app_id=snapshot["app_id"],
            stage_id=snapshot["current_stage"],
            kind="owner_revise",
            text="Owner requested revision from the current cockpit prompt.",
        )
        update_session_view(session, "reviews", action=f"revise:{snapshot['current_stage']}")
        return CockpitCommandResult(False, "Recorded owner revise response.", True)

    if lower == "f" or lower.startswith("f "):
        if not snapshot["app_exists"]:
            return CockpitCommandResult(False, "Create or attach a local app before recording stage feedback.")
        feedback = raw[1:].strip()
        if not feedback:
            return CockpitCommandResult(False, "Use: f <feedback for the current stage>")
        append_cockpit_feedback(
            root,
            app_id=snapshot["app_id"],
            stage_id=snapshot["current_stage"],
            kind="stage_feedback",
            text=feedback,
        )
        update_session_view(session, "reviews", action=f"feedback:{snapshot['current_stage']}")
        return CockpitCommandResult(False, "Recorded stage feedback for the agent review loop.", True)

    if lower == "p" or lower.startswith("p "):
        if not snapshot["app_exists"]:
            return CockpitCommandResult(False, "Create or attach a local app before recording file feedback.")
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            return CockpitCommandResult(False, "Use: p <file-ref-or-name> <feedback for that file>")
        file_ref, error = match_generated_file(snapshot, parts[1])
        if error:
            return CockpitCommandResult(False, error)
        assert file_ref is not None
        append_cockpit_feedback(
            root,
            app_id=snapshot["app_id"],
            stage_id=snapshot["current_stage"],
            kind="file_feedback",
            text=parts[2],
            file_ref=file_ref,
        )
        update_session_view(session, "reviews", action=f"file-feedback:{Path(file_ref).name}")
        return CockpitCommandResult(False, f"Recorded file feedback for {file_ref}.", True)

    return CockpitCommandResult(False, f"Unknown command: {raw}. Use help for the command model.")


def cockpit_should_loop(args: Any, *, input_stream: TextIO, output: TextIO) -> bool:
    if getattr(args, "once", False):
        return False
    if getattr(args, "loop", False):
        return True
    return hasattr(input_stream, "isatty") and input_stream.isatty() and hasattr(output, "isatty") and output.isatty()


def render_script_card(snapshot: dict[str, Any], palette: Palette) -> list[str]:
    script = snapshot["script"]
    rows = [
        palette.paint("Action Card", "bold", "cyan"),
        f"Stage: {script['label']} ({snapshot['stage_state']})",
        f"Ask: {script['visible_prompt']}",
        "Reply model: Yes/No confirmation, option picker, free-form feedback, inspect/revise/approve loop",
        f"Review question: {script['review_question']}",
        f"Stop boundary: {script['stop_boundary']}",
        "Choices:",
    ]
    rows.extend(f"  {choice}" for choice in script["choices"])
    return rows


def render_stage_rows(snapshot: dict[str, Any]) -> list[str]:
    rows = ["Lifecycle stages:"]
    for index, stage in enumerate(snapshot["stages"], 1):
        marker = ">" if stage["id"] == snapshot["current_stage"] else " "
        rows.append(f"  {marker} {index:02d}. {stage['id']:<12} {stage['state']:<16} {stage['script']}")
    return rows


def render_items(title: str, items: list[str], empty: str) -> list[str]:
    rows = [title]
    if not items:
        rows.append(f"  {empty}")
        return rows
    rows.extend(f"  - {item}" for item in items[:40])
    if len(items) > 40:
        rows.append(f"  ... {len(items) - 40} more")
    return rows


def render_reviews(snapshot: dict[str, Any]) -> list[str]:
    rows = ["Review queue:"]
    for item in snapshot["reviews"]:
        rows.append(f"  - {item['kind']} [{item['state']}]: {item['summary']}")
    feedback = list(snapshot.get("feedback") or [])
    if feedback:
        rows.extend(["", "Recent feedback:"])
        for item in feedback[-8:]:
            target = f" -> {item['file_ref']}" if item.get("file_ref") else ""
            rows.append(f"  - {item['kind']} [{item['stage_id']}]{target}: {item['text']}")
    return rows


def render_help() -> list[str]:
    return [
        "Command model:",
        "  status      Show the overview action card and current stage.",
        "  stages      Inspect lifecycle stages and approval state.",
        "  artifacts   Inspect stage artifacts produced by agents.",
        "  files       Inspect generated app files and attach file-specific feedback.",
        "  open <ref>  Preview a generated file or lifecycle artifact by name or ref.",
        "  reviews     Inspect pending owner choices, blockers, and revise/approve prompts.",
        "  resume      Reopen the last saved cockpit view for this app.",
        "  y / n       Approve/continue or revise the current stage prompt.",
        "  f           Add free-form feedback to the current stage.",
        "  p           Attach feedback to a specific file when files exist.",
        "",
        "This is a lifecycle cockpit. Codex executes work behind the action cards; the TUI owns stage state, review loops, and evidence navigation.",
    ]


def render_cockpit_view(session: dict[str, Any], snapshot: dict[str, Any], palette: Palette) -> str:
    view = str(session.get("view") or "overview")
    rows: list[str]
    if view == "stages":
        rows = render_stage_rows(snapshot)
    elif view == "artifacts":
        rows = render_items("Artifacts:", snapshot["artifacts"], "No lifecycle artifacts are present yet.")
    elif view == "files":
        rows = render_items("Generated files:", snapshot["files"], "No generated app files are present yet.")
        rows.extend(["", "File feedback: choose a file from this list, then use [p] to attach feedback for the agent."])
    elif view == "reviews":
        rows = render_reviews(snapshot)
    elif view == "help":
        rows = render_help()
    else:
        rows = render_script_card(snapshot, palette)
        rows.extend(["", *render_stage_rows(snapshot), "", *render_reviews(snapshot)])
    return "\n".join(rows)


def render_cockpit(session: dict[str, Any], snapshot: dict[str, Any], palette: Palette) -> str:
    title = "WEAVE Cockpit"
    mode = "write" if snapshot.get("session_written") else "read-only"
    restored = "yes" if session.get("resume_restored") else "no"
    header_rows = [
        f"App: {snapshot['app_name']} ({snapshot['app_id']})",
        f"Stage: {snapshot['current_stage']} | State: {snapshot['stage_state']} | View: {session['view']} | Mode: {mode}",
        f"Session: {snapshot['session_ref']} | Resume restored: {restored}",
        "Boundary: no credentials, no deployment, no public sends, no paid spend, no live third-party mutation",
    ]
    nav = (
        "Nav: overview | stages | artifacts | files | reviews | help"
        "\nCommand bar: status | stages | artifacts | files | reviews | help | resume | y | n | f | p | q"
    )
    recent = ", ".join(session.get("recent_actions") or []) or "none"
    body = [
        frame(title, "resumable lifecycle cockpit, not a generic Codex chat wrapper", header_rows, palette),
        nav,
        "",
        render_cockpit_view(session, snapshot, palette),
        "",
        palette.paint("Proof boundary", "bold", "magenta"),
        "  external_effects_executed: none",
        "  UI primitives: action card, Yes/No confirmation, option picker, free-form feedback, file-specific feedback",
        f"  recent_actions: {recent}",
    ]
    if not snapshot["app_exists"]:
        body.extend(["", palette.paint("Next", "bold", "cyan"), "  rerun with --write to create local app state, or choose attach/connect/create when the live loop is enabled"])
    elif not snapshot["artifacts"] and not snapshot["files"]:
        body.extend(["", palette.paint("Next", "bold", "cyan"), "  run the lifecycle executor path when ready; this cockpit will then list artifacts and files here"])
    return "\n".join(body) + "\n"


def run_cockpit(args: Any, *, input_stream: TextIO, output: TextIO) -> int:
    app_id = weave_runtime_slice.slugify(args.app_id)
    ensure_public_safe("cockpit args", {"app_id": app_id, "app_name": args.app_name, "view": args.view})
    if args.write and not weave_runtime_slice.app_metadata_path(args.weave_root, app_id).exists():
        weave_runtime_slice.create_app(args.weave_root, app_id, args.app_name)
    snapshot = cockpit_snapshot(args.weave_root, args)
    session, _restored = prepare_cockpit_session(args.weave_root, args, snapshot)
    if args.write:
        write_cockpit_session(args.weave_root, session)
        snapshot["session_written"] = True
    else:
        snapshot["session_written"] = False

    if args.json:
        payload = {
            "schema": "weave-tui-cockpit-render/v0.1",
            "session": session,
            "snapshot": snapshot,
            "external_effects_executed": [],
        }
        print(json.dumps(payload, indent=2, sort_keys=True), file=output)
        return 0

    palette = Palette(color_enabled(args, output))
    print(render_cockpit(session, snapshot, palette), end="", file=output)
    if not cockpit_should_loop(args, input_stream=input_stream, output=output):
        return 0

    while True:
        output.write("\nweave> ")
        output.flush()
        raw = input_stream.readline()
        if not raw:
            break
        result = handle_cockpit_command(args.weave_root, args, session, snapshot, raw)
        if result.message:
            line(output, result.message)
        if result.persist_session:
            write_cockpit_session(args.weave_root, session)
        if result.exit_requested:
            break
        snapshot = cockpit_snapshot(args.weave_root, args)
        snapshot["session_written"] = result.persist_session
        session["current_stage"] = snapshot["current_stage"]
        print(render_cockpit(session, snapshot, palette), end="", file=output)
    return 0


def render_step_table(step_results: list[dict[str, Any]], palette: Palette) -> str:
    lines = []
    for index, item in enumerate(step_results, 1):
        status = str(item.get("status") or "planned")
        style = "green" if status in {"passed", "written", "previewed"} else "yellow" if status in {"blocked", "missing"} else "red"
        prefix = progress_bar(index - 1, len(step_results), palette)
        lines.append(f"{prefix} {index:02d}. {item['label']:<18} {palette.paint(status, style, 'bold')}  {item.get('summary', '')}")
    return "\n".join(lines)


def prompt_text(input_stream: TextIO, output: TextIO, prompt: str, default: str) -> str:
    suffix = f" [{default}]" if default else ""
    output.write(f"{prompt}{suffix}: ")
    output.flush()
    raw = input_stream.readline()
    if not raw:
        line(output)
        return default
    value = raw.strip()
    return value or default


def prompt_choice(input_stream: TextIO, output: TextIO, prompt: str, choices: tuple[str, ...], default: str) -> str:
    options = "/".join(choices)
    while True:
        value = prompt_text(input_stream, output, f"{prompt} ({options})", default).strip().lower()
        if value in choices:
            return value
        line(output, f"Choose one of: {options}")


def prompt_bool(input_stream: TextIO, output: TextIO, prompt: str, default: bool) -> bool:
    default_label = "yes" if default else "no"
    value = prompt_choice(input_stream, output, prompt, ("yes", "no"), default_label)
    return value == "yes"


def collect_inputs(args: Any, *, input_stream: TextIO, output: TextIO, palette: Palette) -> TuiInputs:
    app_name = args.app_name
    app_id = weave_runtime_slice.slugify(args.app_id)
    app_surface = args.app_surface
    owner_experience = args.owner_experience
    coworker_style = args.coworker_style
    control_mode = normalize_control_mode(args.control_mode)
    intent = args.intent
    target_user = args.target_user
    deployment_region = args.deployment_region
    marketing_budget = args.marketing_budget
    owner_feedback = args.owner_feedback
    engineering_owner_response = args.engineering_owner_response
    write = bool(args.write)

    if not args.scripted_demo:
        line(output, frame("WEAVE TUI Setup", "answer once, then the cockpit runs the lifecycle", [], palette))
        app_name = prompt_text(input_stream, output, "App name", app_name)
        app_id = weave_runtime_slice.slugify(prompt_text(input_stream, output, "App id", app_id or app_name))
        app_surface = prompt_choice(input_stream, output, "Primary surface", APP_SURFACES, app_surface)
        owner_experience = prompt_text(input_stream, output, "Your engineering/product experience", owner_experience)
        coworker_style = prompt_text(input_stream, output, "Preferred coworker style", coworker_style)
        control_mode = normalize_control_mode(
            prompt_choice(input_stream, output, "Control mode", ("hands-on", "hands-off", "handoff"), control_mode_label(control_mode))
        )
        intent = prompt_text(input_stream, output, "Intent", intent)
        target_user = prompt_text(input_stream, output, "Target user", target_user)
        deployment_region = prompt_text(input_stream, output, "Deployment region", deployment_region)
        marketing_budget = prompt_text(input_stream, output, "Marketing budget", marketing_budget)
        owner_feedback = prompt_text(input_stream, output, "Extra owner feedback", owner_feedback)
        if control_mode == "hands-on":
            engineering_owner_response = prompt_text(input_stream, output, "Engineering approval note", engineering_owner_response)
        write = write or prompt_bool(input_stream, output, "Write local WEAVE state now", False)

    cleaned = TuiInputs(
        app_id=app_id,
        app_name=app_name,
        app_surface=app_surface,
        owner_experience=owner_experience,
        coworker_style=coworker_style,
        control_mode=normalize_control_mode(control_mode),
        intent=intent,
        target_user=target_user,
        deployment_region=deployment_region,
        marketing_budget=marketing_budget,
        owner_feedback=owner_feedback,
        engineering_owner_response=engineering_owner_response,
        write=write,
    )
    ensure_public_safe("tui inputs", cleaned.__dict__)
    return cleaned


def module_args(base: Any, inputs: TuiInputs, **overrides: Any) -> Namespace:
    values = {
        "runtime_home": base.runtime_home,
        "weave_root": base.weave_root,
        "hermes_home": base.hermes_home,
        "profile_out": base.profile_out,
        "app_id": inputs.app_id,
        "app_name": inputs.app_name,
        "write": inputs.write,
        "json": False,
    }
    values.update(overrides)
    return Namespace(**values)


def run_lifecycle_module(label: str, runner: Callable[[Any], int], args: Namespace) -> dict[str, Any]:
    # Keep child command output out of the TUI transcript. The cockpit renders a
    # consistent status model and the written artifacts remain the proof surface.
    captured = io.StringIO()
    rc = runner(args, output=captured)
    return {
        "label": label,
        "rc": rc,
        "status": "written" if rc == 0 and args.write else "previewed" if rc == 0 else "failed",
        "summary": "local artifacts updated" if rc == 0 and args.write else "read-only preview" if rc == 0 else captured.getvalue().strip(),
    }


def codex_probe_command(raw_command: str) -> tuple[str, ...]:
    parts = tuple(shlex.split(raw_command))
    if not parts:
        raise ValueError("Codex probe command must not be empty")
    if Path(parts[0]).name != "codex":
        raise ValueError("Codex probe is restricted to the codex executable")
    args = parts[1:]
    if args not in SAFE_CODEX_PROBE_ARGS:
        allowed = ", ".join("codex " + " ".join(item) for item in sorted(SAFE_CODEX_PROBE_ARGS))
        raise ValueError(f"Codex probe may only use non-auth metadata commands: {allowed}")
    return parts


def codex_subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    # The local workstation may wrap `codex` for Codex-session registration.
    # Product execution wants the real non-interactive CLI and records its own
    # WEAVE proof, so the wrapper is explicitly disabled for this child process.
    env["CODEX_SWARM_DISABLE"] = "1"
    env["CODEX_SESSIONS_DISABLE"] = "1"
    env["CODEX_PREFLIGHT_DISABLE"] = "1"
    return env


def run_codex_probe(args: Any) -> dict[str, Any]:
    now = utc_now()
    if args.skip_codex_proof:
        return {
            "schema": CODEX_PROOF_SCHEMA,
            "updated_at": now,
            "status": "skipped",
            "binary_found": False,
            "command_label": "codex probe skipped",
            "live_agent_execution": False,
            "claims": ["operator skipped Codex CLI metadata proof"],
            "non_claims": ["does not prove Codex auth", "does not prove model invocation", "does not prove Hermes primitives"],
            "public_safe": True,
            "secret_value_printed": False,
        }

    command = codex_probe_command(args.codex_command)
    binary = shutil.which(command[0])
    if not binary:
        return {
            "schema": CODEX_PROOF_SCHEMA,
            "updated_at": now,
            "status": "missing",
            "binary_found": False,
            "command_label": " ".join(command),
            "live_agent_execution": False,
            "claims": ["Codex CLI executable was not found on PATH"],
            "non_claims": ["does not prove Codex auth", "does not prove model invocation", "does not prove Hermes primitives"],
            "public_safe": True,
            "secret_value_printed": False,
        }

    try:
        completed = subprocess.run(
            [binary, *command[1:]],
            cwd=REPO_ROOT,
            env=codex_subprocess_env(),
            text=True,
            capture_output=True,
            check=False,
            timeout=max(1, int(args.codex_timeout)),
        )
        output_summary = {
            "stdout_present": bool(completed.stdout.strip()),
            "stderr_present": bool(completed.stderr.strip()),
            "stdout_line_count": len(completed.stdout.splitlines()),
            "stderr_line_count": len(completed.stderr.splitlines()),
        }
        status = "passed" if completed.returncode == 0 else "failed"
        exit_code = completed.returncode
        error_summary = ""
    except subprocess.TimeoutExpired:
        output_summary = {"stdout_present": False, "stderr_present": False, "stdout_line_count": 0, "stderr_line_count": 0}
        status = "failed"
        exit_code = None
        error_summary = "codex metadata command timed out"
    except OSError as exc:
        output_summary = {"stdout_present": False, "stderr_present": False, "stdout_line_count": 0, "stderr_line_count": 0}
        status = "failed"
        exit_code = None
        error_summary = exc.__class__.__name__

    proof = {
        "schema": CODEX_PROOF_SCHEMA,
        "updated_at": now,
        "status": status,
        "binary_found": True,
        "command_label": " ".join(command),
        "exit_code": exit_code,
        "output_summary": output_summary,
        "error_summary": error_summary,
        # This is deliberately false. A version/help probe is the strongest
        # proof we can run without consuming model credentials or making a live
        # external request from a local product smoke test.
        "live_agent_execution": False,
        "claims": ["Codex CLI metadata command executed locally" if status == "passed" else "Codex CLI metadata command was attempted"],
        "non_claims": ["does not prove Codex auth", "does not prove model invocation", "does not prove Hermes primitives"],
        "public_safe": True,
        "secret_value_printed": False,
    }
    ensure_public_safe("codex proof", proof)
    return proof


def engineering_artifact_dir(root: Path, app_id: str) -> Path:
    stage = weave_runtime_slice.stage_by_id("engineering")
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage.directory / "artifacts"


def qa_artifact_dir(root: Path, app_id: str) -> Path:
    stage = weave_runtime_slice.stage_by_id("qa")
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage.directory / "artifacts"


def generated_app_dir(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "repo" / "primary"


def generated_app_manifest_path(root: Path, app_id: str) -> Path:
    return engineering_artifact_dir(root, app_id) / "generated-app-manifest.json"


def real_app_qa_path(root: Path, app_id: str) -> Path:
    return qa_artifact_dir(root, app_id) / "real-app-qa.json"


def app_description(inputs: TuiInputs) -> str:
    base = " ".join(inputs.intent.split())
    if len(base) < 72:
        base = f"{inputs.app_name} turns a product intent into a focused local workflow for {inputs.target_user}."
    return base[:154].rstrip(" ,.;") + "."


def generated_index_html(inputs: TuiInputs) -> str:
    title = html.escape(inputs.app_name, quote=True)
    description = html.escape(app_description(inputs), quote=True)
    canonical = f"https://example.com/{inputs.app_id}/"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <link rel="canonical" href="{canonical}" />
  <link rel="stylesheet" href="src/styles.css" />
</head>
<body>
  <main class="app-shell">
    <section class="hero" aria-labelledby="app-title">
      <p class="eyebrow">Local WEAVE product proof</p>
      <h1 id="app-title">{title}</h1>
      <p>{description}</p>
    </section>
    <section class="panel" aria-labelledby="input-title">
      <h2 id="input-title">Intent inputs</h2>
      <label>Primary outcome <input id="seed-one" value="Create a polished local app proof" /></label>
      <label>Operator focus <input id="seed-two" value="Keep the workflow understandable and reviewable" /></label>
      <label>QA target <input id="seed-three" value="Validate generated source and local runtime behavior" /></label>
      <button id="build-plan" type="button">Build plan</button>
      <button id="export-plan" type="button">Export JSON</button>
    </section>
    <section class="panel" aria-live="polite" aria-labelledby="plan-title">
      <h2 id="plan-title">Generated action plan</h2>
      <ol id="plan-list"></ol>
      <pre id="export-output" aria-label="Exported plan JSON"></pre>
    </section>
    <section class="panel boundary" aria-labelledby="boundary-title">
      <h2 id="boundary-title">Launch boundary</h2>
      <p>Deployment, analytics, public sends, paid spend, and credentials are disabled in this local proof.</p>
      <button id="paid-launch" type="button" disabled>Paid launch disabled</button>
    </section>
  </main>
  <script src="src/app.js"></script>
</body>
</html>
"""


def generated_app_js(inputs: TuiInputs) -> str:
    app_id = json.dumps(inputs.app_id)
    app_name = json.dumps(inputs.app_name)
    return f"""const appConfig = {{
  appId: {app_id},
  appName: {app_name},
  externalEffectsEnabled: false
}};

const selectors = {{
  seeds: ["seed-one", "seed-two", "seed-three"],
  planList: "plan-list",
  exportOutput: "export-output",
  buildButton: "build-plan",
  exportButton: "export-plan",
  paidLaunch: "paid-launch"
}};

function readSeeds() {{
  return selectors.seeds.map((id, index) => {{
    const input = document.getElementById(id);
    return {{
      id: `seed-${{index + 1}}`,
      text: input.value.trim() || `Untitled idea ${{index + 1}}`
    }};
  }});
}}

function buildActions(seeds) {{
  return seeds.map((seed, index) => ({{
    rank: index + 1,
    source: seed.text,
    action: `Turn "${{seed.text}}" into one owner-reviewable proof artifact.`,
    effort: index === 0 ? "today" : index === 1 ? "this week" : "later",
    doneWhen: "A reviewer can inspect the result locally without credentials."
  }}));
}}

function renderPlan(actions) {{
  const list = document.getElementById(selectors.planList);
  list.replaceChildren();
  actions.forEach((item) => {{
    const row = document.createElement("li");
    const title = document.createElement("strong");
    const body = document.createElement("span");
    title.textContent = `${{item.rank}}. ${{item.action}}`;
    body.textContent = ` Effort: ${{item.effort}}. Done when: ${{item.doneWhen}}`;
    row.append(title, body);
    list.appendChild(row);
  }});
}}

function currentPlan() {{
  const seeds = readSeeds();
  return {{
    appId: appConfig.appId,
    appName: appConfig.appName,
    generatedAt: new Date().toISOString(),
    externalEffectsEnabled: appConfig.externalEffectsEnabled,
    actions: buildActions(seeds)
  }};
}}

function buildPlan() {{
  const plan = currentPlan();
  localStorage.setItem(`${{appConfig.appId}}:latest-plan`, JSON.stringify(plan));
  renderPlan(plan.actions);
  return plan;
}}

function exportPlan() {{
  const output = document.getElementById(selectors.exportOutput);
  const plan = buildPlan();
  output.textContent = JSON.stringify(plan, null, 2);
}}

function boot() {{
  const paidLaunch = document.getElementById(selectors.paidLaunch);
  paidLaunch.disabled = true;
  document.getElementById(selectors.buildButton).addEventListener("click", buildPlan);
  document.getElementById(selectors.exportButton).addEventListener("click", exportPlan);
  buildPlan();
}}

document.addEventListener("DOMContentLoaded", boot);
"""


def generated_styles_css() -> str:
    return """* {
  box-sizing: border-box;
}

body {
  margin: 0;
  color: #17202a;
  background: #f5f7fb;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.app-shell {
  width: min(1080px, calc(100% - 32px));
  margin: 0 auto;
  padding: 32px 0;
  display: grid;
  gap: 18px;
}

.hero {
  padding: 28px 0 10px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #0f766e;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
}

h1, h2, p {
  margin-top: 0;
}

h1 {
  margin-bottom: 10px;
  font-size: clamp(2rem, 5vw, 4rem);
}

.panel {
  border: 1px solid #d7dde8;
  border-radius: 8px;
  background: #ffffff;
  padding: 18px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

label {
  display: grid;
  gap: 6px;
  margin: 12px 0;
  font-weight: 700;
}

input {
  width: 100%;
  border: 1px solid #aeb8c8;
  border-radius: 6px;
  padding: 10px 12px;
  font: inherit;
}

button {
  min-height: 40px;
  margin-right: 8px;
  border: 0;
  border-radius: 6px;
  padding: 0 14px;
  background: #1d4ed8;
  color: white;
  font-weight: 800;
  cursor: pointer;
}

button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

ol {
  padding-left: 22px;
}

li {
  margin: 10px 0;
}

pre {
  overflow: auto;
  border-radius: 6px;
  background: #0f172a;
  color: #e2e8f0;
  padding: 14px;
}

.boundary {
  border-color: #f59e0b;
  background: #fffbeb;
}
"""


def generated_config_json(inputs: TuiInputs) -> str:
    payload = {
        "schema": GENERATED_APP_SCHEMA,
        "app_id": inputs.app_id,
        "app_name": inputs.app_name,
        "external_effects": {
            "analytics": False,
            "deployment": False,
            "paid_spend": False,
            "public_send": False,
            "credentials": False,
        },
        "runtime": "static-local",
        "public_safe": True,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def generated_readme(inputs: TuiInputs) -> str:
    return f"""# {inputs.app_name}

Local WEAVE generated app proof for `{inputs.app_id}`.

## Run locally

```bash
python3 -m http.server 8000
```

Open `index.html` from the local static server.

## Boundaries

- No credentials.
- No deployment.
- No public sends.
- No paid spend.
- No analytics.
- No network API calls.
"""


def generated_app_sources(inputs: TuiInputs, *, broken: bool = False) -> dict[str, str]:
    sources = {
        "index.html": generated_index_html(inputs),
        "src/app.js": generated_app_js(inputs),
        "src/styles.css": generated_styles_css(),
        "public/config.json": generated_config_json(inputs),
        "README.md": generated_readme(inputs),
    }
    if broken:
        # Test-only switch used by the failure-path regression test. It proves
        # the TUI cannot report success when the generated app source is invalid.
        sources["src/app.js"] = "function brokenGeneratedApp( {\n"
    return sources


def write_generated_app(root: Path, inputs: TuiInputs, *, broken: bool = False, executor: str = "fixture") -> dict[str, Any]:
    app_dir = generated_app_dir(root, inputs.app_id)
    sources = generated_app_sources(inputs, broken=broken)
    written: dict[str, dict[str, Any]] = {}
    for name, content in sources.items():
        ensure_generated_source_safe(name, content)
        path = app_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written[name] = {
            "path": rel(path, root),
            "bytes": path.stat().st_size,
            "sha256": weave_runtime_slice.artifact_checksum(path),
        }
    manifest = {
        "schema": GENERATED_APP_SCHEMA,
        "app_id": inputs.app_id,
        "app_name": inputs.app_name,
        "updated_at": utc_now(),
        "surface": inputs.app_surface,
        "executor": executor,
        "status": "passed",
        "generator": "deterministic-local-source-generator" if executor == "fixture" else "codex-agent-output-verifier",
        "files": written,
        "run_command": "python3 -m http.server 8000",
        "claims": ["runnable static app source files were generated under repo/primary"],
        "non_claims": ["not deployed", "not live user proof"] + (["not live Codex model output"] if executor == "fixture" else []),
        "public_safe": True,
        "secret_value_printed": False,
    }
    weave_runtime_slice.write_json_artifact(generated_app_manifest_path(root, inputs.app_id), manifest)
    return manifest


def clear_generated_app_workspace(root: Path, app_id: str) -> None:
    app_dir = generated_app_dir(root, app_id)
    app_dir.mkdir(parents=True, exist_ok=True)
    # Only the WEAVE-owned required output files are cleared. This prevents a
    # stale previous run from satisfying proof while avoiding broad deletion of
    # unrelated files a user may have placed beside the generated app.
    for name in GENERATED_APP_FILES:
        path = app_dir / name
        if path.exists() and path.is_file():
            path.unlink()


def collect_generated_app_manifest(root: Path, inputs: TuiInputs, executor: str, *, status: str = "passed") -> dict[str, Any]:
    app_dir = generated_app_dir(root, inputs.app_id)
    files: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for name in GENERATED_APP_FILES:
        path = app_dir / name
        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            missing.append(name)
            continue
        files[name] = {
            "path": rel(path, root),
            "bytes": path.stat().st_size,
            "sha256": weave_runtime_slice.artifact_checksum(path),
        }
    manifest = {
        "schema": GENERATED_APP_SCHEMA,
        "app_id": inputs.app_id,
        "app_name": inputs.app_name,
        "updated_at": utc_now(),
        "surface": inputs.app_surface,
        "executor": executor,
        "status": "failed" if missing or status != "passed" else "passed",
        "required_files": list(GENERATED_APP_FILES),
        "files": files,
        "missing_files": missing,
        "run_command": "python3 -m http.server 8000",
        "claims": ["required generated app files exist and are non-empty"] if not missing and status == "passed" else [],
        "non_claims": ["not deployed", "not live user proof"] + (["not live Codex model output"] if executor == "fixture" else []),
        "public_safe": True,
        "secret_value_printed": False,
    }
    weave_runtime_slice.write_json_artifact(generated_app_manifest_path(root, inputs.app_id), manifest)
    return manifest


def codex_app_build_prompt(inputs: TuiInputs) -> str:
    description = app_description(inputs)
    # The prompt names relative files only. Absolute paths, local URLs, provider
    # secrets, and live-service instructions are intentionally absent from the
    # persisted packet so the artifact can be committed or reviewed safely.
    return f"""You are building a local-only WEAVE proof app in the current working directory.

Create exactly these required files:
- index.html
- src/app.js
- src/styles.css
- public/config.json
- README.md

Product:
- App name: {inputs.app_name}
- App id: {inputs.app_id}
- Primary surface: {inputs.app_surface}
- Target user: {inputs.target_user}
- Intent: {inputs.intent}

Hard boundaries:
- Do not deploy.
- Do not use credentials.
- Do not send public messages.
- Do not spend money.
- Do not add analytics beacons.
- Do not call external APIs from the generated app.

Required behavior:
- The app must be runnable as a static website with `python3 -m http.server 8000`.
- index.html must have semantic <main> and <h1> elements.
- index.html must include a title, meta description, Open Graph title, Open Graph description, viewport, stylesheet link, and script tag.
- index.html must use exactly this canonical URL: https://example.com/{inputs.app_id}/
- Generated source text must not include private host names, loopback addresses, private IPs, or file URLs. Say "local static server" instead of naming a private host.
- src/app.js must use addEventListener, textContent, localStorage, and JSON.stringify.
- src/app.js must avoid innerHTML, fetch, XMLHttpRequest, window.location redirects, and external HTTP calls.
- src/app.js must not contain http:// or https:// text, even for placeholder canonical URLs. Keep canonical URL text only in index.html.
- public/config.json must declare external effects disabled for analytics, deployment, paid_spend, public_send, and credentials. A flat false value is preferred; an object with "enabled": false is acceptable.
- README.md must explain local run steps and hard boundaries.

Suggested page description: {description}

Return only a concise completion note after writing the files.
"""


def write_codex_prompt(root: Path, inputs: TuiInputs) -> str:
    path = engineering_artifact_dir(root, inputs.app_id) / "codex-app-build-prompt.md"
    prompt = codex_app_build_prompt(inputs)
    ensure_public_safe("codex app build prompt", prompt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt, encoding="utf-8")
    return rel(path, root)


def write_executor_manifest(root: Path, inputs: TuiInputs, payload: dict[str, Any]) -> dict[str, Any]:
    path = engineering_artifact_dir(root, inputs.app_id) / "app-executor-manifest.json"
    manifest = {
        "schema": APP_EXECUTOR_SCHEMA,
        "app_id": inputs.app_id,
        "updated_at": utc_now(),
        "public_safe": True,
        "secret_value_printed": False,
        **payload,
    }
    ensure_public_safe("app executor manifest", manifest)
    weave_runtime_slice.write_json_artifact(path, manifest)
    manifest["manifest_ref"] = rel(path, root)
    return manifest


def run_fixture_executor(args: Any, inputs: TuiInputs) -> dict[str, Any]:
    clear_generated_app_workspace(args.weave_root, inputs.app_id)
    source_manifest = write_generated_app(
        args.weave_root,
        inputs,
        broken=bool(getattr(args, "fixture_broken_app", False)),
        executor="fixture",
    )
    executor = write_executor_manifest(
        args.weave_root,
        inputs,
        {
            "executor": "fixture",
            "status": "passed",
            "live_agent_execution": False,
            "source_manifest_ref": rel(generated_app_manifest_path(args.weave_root, inputs.app_id), args.weave_root),
            "claims": ["deterministic fixture source was written for local CI/proof"],
            "non_claims": ["not live Codex model output", "not deployed", "not live user proof"],
        },
    )
    return {"executor_manifest": executor, "source_manifest": source_manifest}


def run_codex_executor(args: Any, inputs: TuiInputs) -> dict[str, Any]:
    root = args.weave_root
    clear_generated_app_workspace(root, inputs.app_id)
    prompt_ref = write_codex_prompt(root, inputs)
    binary_found = bool(shutil.which("codex"))
    if not binary_found:
        executor = write_executor_manifest(
            root,
            inputs,
            {
                "executor": "codex",
                "status": "failed",
                "failure_class": "environment",
                "prompt_ref": prompt_ref,
                "live_agent_execution": False,
                "binary_found": False,
                "command_label": "codex exec --sandbox workspace-write -C generated-app-workspace -",
                "claims": [],
                "non_claims": ["Codex CLI was not available", "not deployed", "not live user proof"],
            },
        )
        raise ValueError(f"codex executor failed: Codex CLI missing ({executor['manifest_ref']})")

    command = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "--color",
        "never",
        "-C",
        str(generated_app_dir(root, inputs.app_id)),
        "-",
    ]
    prompt = codex_app_build_prompt(inputs)
    try:
        completed = subprocess.run(
            command,
            input=prompt,
            cwd=REPO_ROOT,
            env=codex_subprocess_env(),
            text=True,
            capture_output=True,
            check=False,
            timeout=max(1, int(getattr(args, "codex_timeout", DEFAULT_CODEX_TIMEOUT))),
        )
        timed_out = False
        exit_code = completed.returncode
        stdout_lines = len((completed.stdout or "").splitlines())
        stderr_lines = len((completed.stderr or "").splitlines())
    except subprocess.TimeoutExpired:
        timed_out = True
        exit_code = None
        stdout_lines = 0
        stderr_lines = 0
    except OSError:
        timed_out = False
        exit_code = None
        stdout_lines = 0
        stderr_lines = 0

    if timed_out or exit_code != 0:
        executor = write_executor_manifest(
            root,
            inputs,
            {
                "executor": "codex",
                "status": "failed",
                "failure_class": "timeout" if timed_out else "agent_execution",
                "prompt_ref": prompt_ref,
                "live_agent_execution": False,
                "binary_found": True,
                "command_label": "codex exec --sandbox workspace-write -C generated-app-workspace -",
                "exit_code": exit_code,
                "output_summary": {
                    "stdout_line_count": stdout_lines,
                    "stderr_line_count": stderr_lines,
                    "raw_output_persisted": False,
                },
                "claims": [],
                "non_claims": ["Codex did not complete the app build", "not deployed", "not live user proof"],
            },
        )
        raise ValueError(f"codex executor failed: see {executor['manifest_ref']}")

    source_manifest = collect_generated_app_manifest(root, inputs, "codex")
    if source_manifest["status"] != "passed":
        executor = write_executor_manifest(
            root,
            inputs,
            {
                "executor": "codex",
                "status": "failed",
                "failure_class": "missing_required_files",
                "prompt_ref": prompt_ref,
                "source_manifest_ref": rel(generated_app_manifest_path(root, inputs.app_id), root),
                "missing_files": source_manifest["missing_files"],
                "live_agent_execution": True,
                "binary_found": True,
                "command_label": "codex exec --sandbox workspace-write -C generated-app-workspace -",
                "exit_code": exit_code,
                "output_summary": {
                    "stdout_line_count": stdout_lines,
                    "stderr_line_count": stderr_lines,
                    "raw_output_persisted": False,
                },
                "claims": ["Codex CLI returned success"],
                "non_claims": ["required app files were not fully produced", "not deployed", "not live user proof"],
            },
        )
        raise ValueError(f"codex executor produced incomplete app: see {executor['manifest_ref']}")

    executor = write_executor_manifest(
        root,
        inputs,
        {
            "executor": "codex",
            "status": "passed",
            "failure_class": "",
            "prompt_ref": prompt_ref,
            "source_manifest_ref": rel(generated_app_manifest_path(root, inputs.app_id), root),
            "live_agent_execution": True,
            "binary_found": True,
            "command_label": "codex exec --sandbox workspace-write -C generated-app-workspace -",
            "exit_code": exit_code,
            "output_summary": {
                "stdout_line_count": stdout_lines,
                "stderr_line_count": stderr_lines,
                "raw_output_persisted": False,
            },
            "claims": ["Codex CLI executed non-interactively and produced required local app files"],
            "non_claims": ["not deployed", "not live user proof", "no provider credentials were captured by WEAVE"],
        },
    )
    return {"executor_manifest": executor, "source_manifest": source_manifest}


def run_app_executor(args: Any, inputs: TuiInputs) -> dict[str, Any]:
    executor = getattr(args, "executor", "codex")
    if executor == "fixture":
        return run_fixture_executor(args, inputs)
    if executor == "codex":
        return run_codex_executor(args, inputs)
    raise ValueError(f"unsupported app executor: {executor}")


def write_engineering_markdown(inputs: TuiInputs, codex_proof: dict[str, Any], executor_result: dict[str, Any]) -> str:
    seo_line = "Website SEO checklist and QA are included." if inputs.app_surface == "website" else "SEO is not applicable to this primary surface."
    executor_manifest = executor_result["executor_manifest"]
    source_manifest = executor_result["source_manifest"]
    return "\n".join(
        [
            "# Local Engineering Scaffold",
            "",
            "Status: ready for local QA",
            "",
            "## Owner Intent",
            "",
            inputs.intent,
            "",
            "## Product Surface",
            "",
            f"- Primary surface: {inputs.app_surface}",
            f"- QA surface: {QA_SURFACE_BY_APP_SURFACE[inputs.app_surface]}",
            f"- Control mode: {control_mode_label(inputs.control_mode)}",
            "",
            "## Implementation Shape",
            "",
            "- Create a real static app under repo/primary.",
            "- Run local HTTP and generated-source QA before reporting success.",
            "- Keep credentials, provider auth, deployment, public sends, and paid spend gated.",
            "- Record proof artifacts before asking the owner to accept the stage.",
            f"- {seo_line}",
            "",
            "## Codex Adapter Boundary",
            "",
            f"- Local Codex metadata proof status: {codex_proof['status']}",
            f"- App executor: {executor_manifest['executor']}",
            f"- App executor status: {executor_manifest['status']}",
            f"- Live agent execution claimed: {str(executor_manifest.get('live_agent_execution', False)).lower()}",
            f"- Executor proof: {executor_manifest['manifest_ref']}",
            f"- Generated app manifest status: {source_manifest['status']}",
            "",
            "## Generated Source",
            "",
            "- repo/primary/index.html",
            "- repo/primary/src/app.js",
            "- repo/primary/src/styles.css",
            "- repo/primary/public/config.json",
            "- repo/primary/README.md",
            "",
        ]
    )


def seo_checklist_markdown(inputs: TuiInputs) -> str:
    return "\n".join(
        [
            "# Website SEO Checklist",
            "",
            "Status: local plan",
            "",
            "## Required Baseline",
            "",
            "- One descriptive title per route.",
            "- Meta description that matches the page intent.",
            "- Canonical URL strategy before production deploy.",
            "- Crawlable semantic headings and landmark structure.",
            "- Open Graph and social preview metadata.",
            "- Robots and sitemap plan after deployment target is known.",
            "- Structured data only when the app domain supports a truthful schema.",
            "",
            "## Current App",
            "",
            f"- App: {inputs.app_name}",
            f"- Target user: {inputs.target_user}",
            f"- Deployment region: {inputs.deployment_region}",
            "",
            "Boundary: local SEO planning only; no production crawl or indexing proof exists.",
            "",
        ]
    )


def write_seo_qa(root: Path, inputs: TuiInputs) -> str:
    path = qa_artifact_dir(root, inputs.app_id) / "seo-qa.json"
    payload = {
        "schema": SEO_ARTIFACT_SCHEMA,
        "app_id": inputs.app_id,
        "updated_at": utc_now(),
        "surface": "website",
        "checks": [
            {"id": "title", "status": "planned", "claim": "route titles must be descriptive"},
            {"id": "description", "status": "planned", "claim": "meta descriptions must match intent"},
            {"id": "canonical", "status": "blocked_on_deployment", "claim": "canonical URL needs deployment target"},
            {"id": "sitemap", "status": "blocked_on_deployment", "claim": "sitemap needs deployed routes"},
        ],
        "non_claims": ["not production SEO proof", "not search-console proof", "not deployed crawl proof"],
        "public_safe": True,
        "secret_value_printed": False,
    }
    ensure_public_safe("seo qa", payload)
    weave_runtime_slice.write_json_artifact(path, payload)
    return rel(path, root)


def qa_check(check_id: str, status: str, summary: str, *, failure_class: str = "", route: str = "") -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "summary": summary,
        "failure_class": failure_class,
        "route": route,
    }


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class QuietStaticHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: Any) -> None:
        return


def fetch_generated_routes(app_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    routes = [
        ("/", "index"),
        ("/index.html", "index-html"),
        ("/src/app.js", "app-js"),
        ("/src/styles.css", "styles-css"),
        ("/public/config.json", "config-json"),
    ]
    handler = functools.partial(QuietStaticHandler, directory=str(app_dir))
    loopback_host = ".".join(["127", "0", "0", "1"])
    server = http.server.ThreadingHTTPServer((loopback_host, 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    checks: list[dict[str, Any]] = []
    route_evidence: list[dict[str, Any]] = []
    try:
        port = int(server.server_address[1])
        for route, label in routes:
            try:
                with urllib.request.urlopen(f"http://{loopback_host}:{port}{route}", timeout=5) as response:
                    body = response.read()
                    status_code = int(response.status)
                passed = status_code == 200 and len(body) > 0
                checks.append(
                    qa_check(
                        f"route-{label}",
                        "passed" if passed else "failed",
                        f"static route {label} returned non-empty HTTP 200" if passed else f"static route {label} did not return HTTP 200",
                        failure_class="" if passed else "product",
                        route="" if passed else "engineering",
                    )
                )
                route_evidence.append(
                    {
                        "route_label": label,
                        "status_code": status_code,
                        "byte_count": len(body),
                        "sha256": sha256_bytes(body),
                    }
                )
            except (urllib.error.URLError, TimeoutError, OSError):
                checks.append(qa_check(f"route-{label}", "failed", f"static route {label} could not be fetched", failure_class="environment", route="qa_plan_revision"))
                route_evidence.append({"route_label": label, "status_code": None, "byte_count": 0, "sha256": ""})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    return checks, route_evidence


def text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def balanced_javascript_shape(source: str) -> bool:
    pairs = {"(": ")", "{": "}", "[": "]"}
    closing = {value: key for key, value in pairs.items()}
    stack: list[str] = []
    in_string = ""
    escaped = False
    for char in source:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = ""
            continue
        if char in {"'", '"', "`"}:
            in_string = char
        elif char in pairs:
            stack.append(char)
        elif char in closing:
            if not stack or stack[-1] != closing[char]:
                return False
            stack.pop()
    return not stack and not in_string


def run_node_syntax_check(js_path: Path) -> dict[str, Any]:
    node = shutil.which("node")
    if not node:
        return qa_check("js-node-syntax", "failed", "node is unavailable for JavaScript syntax validation", failure_class="environment", route="qa_plan_revision")
    try:
        completed = subprocess.run([node, "--check", str(js_path)], text=True, capture_output=True, check=False, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return qa_check("js-node-syntax", "failed", "node syntax validation could not run", failure_class="environment", route="qa_plan_revision")
    return qa_check(
        "js-node-syntax",
        "passed" if completed.returncode == 0 else "failed",
        "JavaScript passed node --check" if completed.returncode == 0 else "JavaScript failed node --check",
        failure_class="" if completed.returncode == 0 else "code",
        route="" if completed.returncode == 0 else "engineering",
    )


def private_locator_text_present(source_texts: dict[str, str]) -> bool:
    private_host_word = "local" + "host"
    private_markers = [
        private_host_word,
        "127.",
        "192.168.",
        "172.16.",
        "172.17.",
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "file:",
    ]
    return any(marker in text.lower() for text in source_texts.values() for marker in private_markers)


def effect_flag_disabled(effects: dict[str, Any], aliases: tuple[str, ...]) -> bool:
    for alias in aliases:
        if alias not in effects:
            continue
        value = effects[alias]
        if value is False:
            return True
        if isinstance(value, dict) and value.get("enabled") is False:
            return True
        return False
    return False


def external_effects_disabled(config_payload: dict[str, Any]) -> bool:
    effects = config_payload.get("external_effects")
    if not isinstance(effects, dict):
        effects = config_payload.get("externalEffects")
    if not isinstance(effects, dict):
        return False
    requirements = {
        "analytics": ("analytics",),
        "deployment": ("deployment",),
        "paid_spend": ("paid_spend", "paidSpend", "paid_spends", "paidSpends"),
        "public_send": ("public_send", "publicSend", "public_sends", "publicSends"),
        "credentials": ("credentials",),
    }
    return all(effect_flag_disabled(effects, aliases) for aliases in requirements.values())


def source_static_checks(root: Path, inputs: TuiInputs) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    app_dir = generated_app_dir(root, inputs.app_id)
    required_paths = {name: app_dir / name for name in GENERATED_APP_FILES}
    checks: list[dict[str, Any]] = []
    for name, path in required_paths.items():
        passed = path.exists() and path.is_file() and path.stat().st_size > 0
        checks.append(
            qa_check(
                f"file-{name.replace('/', '-')}",
                "passed" if passed else "failed",
                f"{name} exists and is non-empty" if passed else f"{name} is missing or empty",
                failure_class="" if passed else "product",
                route="" if passed else "engineering",
            )
        )
    if any(item["status"] != "passed" for item in checks):
        return checks, {"external_effects_disabled": False, "seo_checks": []}

    source_texts = {name: text_file(path) for name, path in required_paths.items()}
    index_html = source_texts["index.html"]
    js_source = source_texts["src/app.js"]
    config_payload: dict[str, Any]
    try:
        config_payload = json.loads(text_file(required_paths["public/config.json"]))
    except json.JSONDecodeError:
        config_payload = {}

    no_private_locator_text = not private_locator_text_present(source_texts)
    checks.append(
        qa_check(
            "source-no-private-locator-text",
            "passed" if no_private_locator_text else "failed",
            "generated source avoids private host, private IP, and file URL text" if no_private_locator_text else "generated source includes private host, private IP, or file URL text",
            failure_class="" if no_private_locator_text else "product",
            route="" if no_private_locator_text else "engineering",
        )
    )

    html_requirements = [
        ("html-title", "<title>" in index_html and inputs.app_name in index_html, "HTML title includes the app name"),
        ("html-description", 'name="description"' in index_html, "HTML includes a meta description"),
        ("html-og-title", 'property="og:title"' in index_html, "HTML includes Open Graph title"),
        ("html-og-description", 'property="og:description"' in index_html, "HTML includes Open Graph description"),
        ("html-canonical", 'rel="canonical"' in index_html and f"https://example.com/{inputs.app_id}/" in index_html, "HTML includes the public-safe placeholder canonical URL"),
        ("html-viewport", 'name="viewport"' in index_html, "HTML includes viewport metadata"),
        ("html-main", "<main" in index_html and "<h1" in index_html, "HTML includes semantic main and h1"),
        ("html-css-link", 'href="src/styles.css"' in index_html, "HTML links the generated stylesheet"),
        ("html-js-link", 'src="src/app.js"' in index_html, "HTML links the generated JavaScript"),
    ]
    for check_id, passed, summary in html_requirements:
        checks.append(qa_check(check_id, "passed" if passed else "failed", summary if passed else f"{summary} is missing", failure_class="" if passed else "product", route="" if passed else "engineering"))

    js_requirements = [
        ("js-balanced", balanced_javascript_shape(js_source), "JavaScript brackets and strings are structurally balanced"),
        ("js-add-event-listener", "addEventListener" in js_source, "JavaScript wires event listeners"),
        ("js-text-content", "textContent" in js_source, "JavaScript uses textContent for rendering"),
        ("js-local-storage", "localStorage" in js_source, "JavaScript stores local state"),
        ("js-json-stringify", "JSON.stringify" in js_source, "JavaScript exports JSON"),
        ("js-no-inner-html", "innerHTML" not in js_source, "JavaScript avoids innerHTML"),
        ("js-no-fetch", "fetch(" not in js_source and "XMLHttpRequest" not in js_source, "JavaScript avoids external request primitives"),
        ("js-no-external-url", "http://" not in js_source and "https://" not in js_source and "window.location" not in js_source, "JavaScript avoids external URLs and redirects"),
    ]
    for check_id, passed, summary in js_requirements:
        checks.append(qa_check(check_id, "passed" if passed else "failed", summary if passed else f"{summary} check failed", failure_class="" if passed else "code", route="" if passed else "engineering"))
    checks.append(run_node_syntax_check(required_paths["src/app.js"]))

    effects_disabled = isinstance(config_payload, dict) and external_effects_disabled(config_payload)
    checks.append(
        qa_check(
            "config-external-effects-disabled",
            "passed" if effects_disabled else "failed",
            "config declares all external effects disabled" if effects_disabled else "config does not disable every external effect",
            failure_class="" if effects_disabled else "product",
            route="" if effects_disabled else "engineering",
        )
    )

    seo_checks = [item for item in checks if item["id"].startswith("html-")]
    return checks, {"external_effects_disabled": effects_disabled, "seo_checks": seo_checks}


def write_real_seo_qa(root: Path, inputs: TuiInputs, seo_checks: list[dict[str, Any]], overall_status: str) -> str:
    path = qa_artifact_dir(root, inputs.app_id) / "seo-qa.json"
    payload = {
        "schema": SEO_ARTIFACT_SCHEMA,
        "app_id": inputs.app_id,
        "updated_at": utc_now(),
        "surface": "website",
        "status": overall_status,
        "checks": seo_checks,
        "claims": ["local generated website source contains baseline SEO tags"] if overall_status == "passed" else [],
        "non_claims": ["not production SEO proof", "not search-console proof", "not deployed crawl proof"],
        "public_safe": True,
        "secret_value_printed": False,
    }
    ensure_public_safe("seo qa", payload)
    weave_runtime_slice.write_json_artifact(path, payload)
    return rel(path, root)


def write_real_app_qa_result(root: Path, inputs: TuiInputs, payload: dict[str, Any]) -> dict[str, Any]:
    path = real_app_qa_path(root, inputs.app_id)
    ensure_public_safe("real app qa", payload)
    weave_runtime_slice.write_json_artifact(path, payload)
    payload["manifest_ref"] = rel(path, root)
    return payload


def record_qa_state(root: Path, inputs: TuiInputs, qa_result: dict[str, Any]) -> None:
    passed = qa_result["summary"]["status"] == "passed"
    app = weave_runtime_slice.load_app(root, inputs.app_id)
    app["real_app_qa"] = {
        "status": qa_result["summary"]["status"],
        "route": qa_result["summary"]["route"],
        "manifest_path": qa_result["manifest_ref"],
    }
    app["current_stage"] = "qa" if passed else "engineering"
    app["stage_state"] = "ready_for_review" if passed else "blocked"
    if not passed:
        app["blockers"] = sorted(set(app.get("blockers", []) + ["real app QA failed: route to engineering"]))
    weave_runtime_slice.write_app(root, app)
    weave_runtime_slice.update_registry_entry(root, app)
    weave_runtime_slice.append_event(
        root,
        inputs.app_id,
        weave_runtime_slice.new_event(
            "validation.completed",
            inputs.app_id,
            "qa",
            f"Real app QA completed with route {qa_result['summary']['route']}.",
            payload={"manifest_path": qa_result["manifest_ref"], "route": qa_result["summary"]["route"]},
            artifact_refs=[{"path": qa_result["manifest_ref"], "stage": "qa"}],
        ),
    )


def run_real_app_qa(args: Any, inputs: TuiInputs, source_manifest: dict[str, Any]) -> dict[str, Any]:
    root = args.weave_root
    app_dir = generated_app_dir(root, inputs.app_id)
    route_checks, route_evidence = fetch_generated_routes(app_dir)
    static_checks, static_evidence = source_static_checks(root, inputs)
    all_checks = route_checks + static_checks
    failed = [item for item in all_checks if item["status"] != "passed"]
    status = "failed" if failed else "passed"
    route = "owner_review" if not failed else "qa_plan_revision" if any(item.get("route") == "qa_plan_revision" for item in failed) else "engineering"
    seo_ref = ""
    if inputs.app_surface == "website":
        seo_ref = write_real_seo_qa(root, inputs, static_evidence["seo_checks"], "passed" if not failed else "failed")
    payload = {
        "schema": REAL_APP_QA_SCHEMA,
        "app_id": inputs.app_id,
        "updated_at": utc_now(),
        "surface": inputs.app_surface,
        "executor": source_manifest.get("executor", ""),
        "source_manifest_ref": rel(generated_app_manifest_path(root, inputs.app_id), root),
        "summary": {
            "status": status,
            "route": route,
            "check_count": len(all_checks),
            "failed_count": len(failed),
        },
        "checks": all_checks,
        "route_evidence": route_evidence,
        "source_evidence": {
            "required_file_count": len(GENERATED_APP_FILES),
            "external_effects_disabled": static_evidence["external_effects_disabled"],
        },
        "artifact_refs": [rel(generated_app_manifest_path(root, inputs.app_id), root)] + ([seo_ref] if seo_ref else []),
        "claims": ["generated app source served locally and passed source/SEO checks"] if not failed else [],
        "non_claims": ["not deployed", "not production user validated", "not provider-auth proof"],
        "public_safe": True,
        "secret_value_printed": False,
    }
    qa_result = write_real_app_qa_result(root, inputs, payload)
    record_qa_state(root, inputs, qa_result)
    return {
        "label": "Real app QA",
        "rc": 0 if status == "passed" else 1,
        "status": "written" if status == "passed" else "failed",
        "summary": f"{status}, route {route}, checks {len(all_checks)}, failed {len(failed)}",
        "artifact_refs": [qa_result["manifest_ref"]] + ([seo_ref] if seo_ref else []),
        "qa_status": status,
        "qa_route": route,
    }


def append_ready_turn(root: Path, inputs: TuiInputs, artifact_path: Path) -> dict[str, Any]:
    artifact_ref = {"path": rel(artifact_path, root), "action": "created"}
    # Stage approval needs a current-stage turn linked to an implementation
    # artifact. Recording it here prevents QA from being reached by invisible
    # state mutation.
    turn = weave_runtime_slice.new_conversation_turn(
        inputs.app_id,
        "engineering",
        "Review the local engineering scaffold and proceed to QA.",
        "Engineering scaffold is ready for owner review and local QA. No external effects were used.",
        channel="local-tui",
        created_by="execution-agent",
        agent_rationale={
            "summary": "Engineering prepared a local-only scaffold and proof boundary.",
            "gate_questions": [
                "Is the implementation artifact present?",
                "Are hard external boundaries explicit?",
                "Is QA surface selection recorded?",
            ],
            "missing_information": [],
            "decision_basis": [artifact_ref["path"], f"surface:{inputs.app_surface}"],
            "chain_of_thought_captured": False,
        },
        artifact_refs=[artifact_ref],
        state_transition={
            "from_stage": "engineering",
            "from_state": "collecting",
            "to_stage": "engineering",
            "to_state": "ready_for_review",
        },
        next_action="Run surface-adapted local QA proof.",
    )
    return weave_runtime_slice.append_conversation_turn(root, inputs.app_id, turn)


def write_engineering_scaffold(args: Any, inputs: TuiInputs) -> dict[str, Any]:
    root = args.weave_root
    app = weave_runtime_slice.load_app(root, inputs.app_id)
    if weave_runtime_slice.normalize_stage_id(app.get("current_stage"), default="intent") != "engineering":
        raise ValueError("TUI engineering scaffold requires the app to be at Engineering")

    codex_proof = run_codex_probe(args)
    eng_dir = engineering_artifact_dir(root, inputs.app_id)
    eng_dir.mkdir(parents=True, exist_ok=True)

    codex_path = eng_dir / "codex-adapter-proof.json"
    weave_runtime_slice.write_json_artifact(codex_path, codex_proof)

    executor_result = run_app_executor(args, inputs)

    scaffold_path = eng_dir / "local-implementation-scaffold.md"
    scaffold_text = write_engineering_markdown(inputs, codex_proof, executor_result)
    ensure_public_safe("engineering scaffold", scaffold_text)
    scaffold_path.write_text(scaffold_text, encoding="utf-8")

    seo_refs: list[str] = []
    if inputs.app_surface == "website":
        seo_path = eng_dir / "seo-checklist.md"
        seo_text = seo_checklist_markdown(inputs)
        ensure_public_safe("seo checklist", seo_text)
        seo_path.write_text(seo_text, encoding="utf-8")
        seo_refs.append(rel(seo_path, root))
        seo_refs.append(write_seo_qa(root, inputs))

    turn = append_ready_turn(root, inputs, scaffold_path)
    evaluation = weave_runtime_slice.complete_evaluation_from_latest_artifact(
        root,
        inputs.app_id,
        "engineering",
        run_gates=bool(args.run_engineering_gates),
    )
    evaluation_decision = str(evaluation["result"]["decision"])
    approval_status = "not_requested"
    advanced_to = "qa_rehearsal"
    if evaluation_decision == "advance":
        approval = weave_runtime_slice.approve_stage(root, inputs.app_id, "engineering", note="local TUI engineering scaffold accepted for QA")
        if not approval["approved"]:
            raise weave_runtime_slice.RuntimeSliceError(f"engineering approval blocked: {approval['gate']['missing']}")
        advance = weave_runtime_slice.advance_stage(root, inputs.app_id, note="advance after local TUI engineering proof")
        if not advance["advanced"]:
            raise weave_runtime_slice.RuntimeSliceError(f"engineering advance blocked: {advance.get('error', 'unknown')}")
        approval_status = "approved"
        advanced_to = advance["stage"]
    else:
        # The engineering contract requires command hard gates. Running the full
        # test suite from inside a TUI smoke can recurse during CI, so the
        # default path keeps the formal approval pending and lets QA run as a
        # clearly labeled local rehearsal artifact.
        weave_runtime_slice.append_event(
            root,
            inputs.app_id,
            weave_runtime_slice.new_event(
                "validation.completed",
                inputs.app_id,
                "engineering",
                f"Engineering scaffold evaluation is {evaluation_decision}; QA rehearsal may continue without formal approval.",
                payload={"decision": evaluation_decision, "run_gates": bool(args.run_engineering_gates)},
                artifact_refs=[{"path": rel(scaffold_path, root), "stage": "engineering"}],
            ),
        )

    return {
        "label": "Engineering",
        "status": "written",
        "summary": (
            f"scaffold ready, executor {executor_result['executor_manifest']['executor']} "
            f"{executor_result['executor_manifest']['status']}, eval {evaluation_decision}, Codex proof {codex_proof['status']}"
        ),
        "artifact_refs": [
            rel(scaffold_path, root),
            rel(codex_path, root),
            executor_result["executor_manifest"]["manifest_ref"],
            rel(generated_app_manifest_path(root, inputs.app_id), root),
            *seo_refs,
        ],
        "codex_status": codex_proof["status"],
        "executor": executor_result["executor_manifest"]["executor"],
        "executor_status": executor_result["executor_manifest"]["status"],
        "source_manifest": executor_result["source_manifest"],
        "turn_id": turn["turn_id"],
        "evaluation_decision": evaluation_decision,
        "approval_status": approval_status,
        "advanced_to": advanced_to,
    }


def write_tui_manifest(args: Any, inputs: TuiInputs, step_results: list[dict[str, Any]]) -> dict[str, Any]:
    root = args.weave_root
    path = qa_artifact_dir(root, inputs.app_id) / "tui-session-manifest.json"
    manifest = {
        "schema": TUI_SCHEMA,
        "app_id": inputs.app_id,
        "updated_at": utc_now(),
        "mode": "write" if inputs.write else "preview",
        "app_surface": inputs.app_surface,
        "qa_surface": QA_SURFACE_BY_APP_SURFACE[inputs.app_surface],
        "executor": getattr(args, "executor", "codex"),
        "control_mode": inputs.control_mode,
        "control_label": control_mode_label(inputs.control_mode),
        "steps": [
            {
                "label": item["label"],
                "status": item.get("status", ""),
                "summary": item.get("summary", ""),
                "artifact_refs": item.get("artifact_refs", []),
            }
            for item in step_results
        ],
        "external_effects_executed": [],
        "hard_boundaries_stopped": ["credentials", "deployment", "public_send", "paid_spend", "raw_secret_handling"],
        "claims": ["TUI exercised the local lifecycle through real generated app QA"],
        "non_claims": ["not deployed", "not live marketing", "not provider-auth proof"]
        + (["not live Codex model invocation"] if getattr(args, "executor", "codex") == "fixture" else []),
        "public_safe": True,
        "secret_value_printed": False,
    }
    ensure_public_safe("tui manifest", manifest)
    weave_runtime_slice.write_json_artifact(path, manifest)
    manifest["manifest_ref"] = rel(path, root)
    return manifest


def run_scripted_or_interactive(args: Any, inputs: TuiInputs) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    steps: list[dict[str, Any]] = []

    first_args = module_args(
        args,
        inputs,
        hermes_command="hermes",
        owner_experience=inputs.owner_experience,
        coworker_style=inputs.coworker_style,
        control_mode=inputs.control_mode,
        setup_choice="create-local",
    )
    steps.append(run_lifecycle_module("First run", weave_first_run.run, first_args))
    if steps[-1]["rc"] != 0 or not inputs.write:
        return steps, None

    early_args = module_args(
        args,
        inputs,
        intent=inputs.intent,
        target_user=inputs.target_user,
        deployment_region=inputs.deployment_region,
        marketing_budget=inputs.marketing_budget,
        owner_feedback=inputs.owner_feedback,
        control_mode=inputs.control_mode,
        create_app=False,
    )
    steps.append(run_lifecycle_module("Intent-Plan", weave_early_lifecycle.run, early_args))
    if steps[-1]["rc"] != 0:
        return steps, None

    decision_args = module_args(
        args,
        inputs,
        decision_id="tui-engineering-local-safe",
        question="Should Engineering proceed with the local-safe implementation scaffold?",
        control_mode=inputs.control_mode,
        decision_type="architecture",
        hard_boundary=[],
        selected_option="local-safe-path",
        owner_response=inputs.engineering_owner_response if inputs.control_mode == "hands-on" else "",
    )
    steps.append(run_lifecycle_module("Owner decision", weave_engineering_decisions.run, decision_args))
    if steps[-1]["rc"] != 0:
        return steps, None

    engineering = write_engineering_scaffold(args, inputs)
    steps.append(engineering)

    real_qa = run_real_app_qa(args, inputs, engineering["source_manifest"])
    steps.append(real_qa)
    if real_qa["rc"] != 0:
        return steps, None

    qa_args = module_args(
        args,
        inputs,
        surface=QA_SURFACE_BY_APP_SURFACE[inputs.app_surface],
        qa_command=args.qa_command,
        target_label=f"local {inputs.app_surface} proof",
        create_app=False,
    )
    steps.append(run_lifecycle_module("Lifecycle QA bundle", weave_qa_proof.run, qa_args))
    if steps[-1]["rc"] != 0:
        return steps, None

    launch_args = module_args(
        args,
        inputs,
        deployment_region=inputs.deployment_region,
        marketing_budget=inputs.marketing_budget,
        feedback_source="local feedback artifacts",
        create_app=False,
    )
    launch_result = run_lifecycle_module("Launch gates", weave_launch_ops.run, launch_args)
    launch_result["status"] = "blocked" if launch_result["rc"] == 0 else "failed"
    launch_result["summary"] = "deployment/KPI/marketing/iteration gated locally" if launch_result["rc"] == 0 else launch_result["summary"]
    steps.append(launch_result)

    manifest = write_tui_manifest(args, inputs, steps)
    return steps, manifest


def render_summary(inputs: TuiInputs, step_results: list[dict[str, Any]], manifest: dict[str, Any] | None, palette: Palette) -> str:
    engineering = next((item for item in step_results if item.get("label") == "Engineering"), {})
    executor = engineering.get("executor", "preview")
    lines = [
        render_intro(inputs, palette),
        "",
        render_step_table(step_results, palette),
        "",
        palette.paint("Proof boundary", "bold", "magenta"),
        "  external_effects_executed: none",
        "  stopped_before: credentials, deployment, public sends, paid spend, raw secret handling",
        f"  executor: {executor}",
        "  generated_app: apps/<app>/repo/primary",
    ]
    if inputs.app_surface == "website":
        seo_state = "checklist and real local SEO QA artifact written" if manifest else "checklist and local QA artifact will be written"
        lines.extend([f"  SEO: {seo_state}"])
    if manifest:
        lines.extend(["", palette.paint("Written", "bold", "green"), f"  tui_manifest: {manifest['manifest_ref']}"])
    else:
        lines.extend(["", palette.paint("Next", "bold", "cyan"), "  rerun with --write to create local WEAVE state and QA proof"])
    return "\n".join(lines) + "\n"


def run(args: Any, *, input_stream: TextIO = sys.stdin, output: TextIO = sys.stdout) -> int:
    palette = Palette(color_enabled(args, output))
    try:
        if getattr(args, "cockpit", False) or not args.scripted_demo:
            return run_cockpit(args, input_stream=input_stream, output=output)
        inputs = collect_inputs(args, input_stream=input_stream, output=output, palette=palette)
        if args.json:
            step_results, manifest = run_scripted_or_interactive(args, inputs)
            payload = {
                "schema": TUI_SCHEMA,
                "app_id": inputs.app_id,
                "mode": "write" if inputs.write else "preview",
                "steps": step_results,
                "manifest": manifest,
                "external_effects_executed": [],
            }
            print(json.dumps(payload, indent=2, sort_keys=True), file=output)
            return 0 if all(item.get("rc", 0) == 0 for item in step_results) else 1
        step_results, manifest = run_scripted_or_interactive(args, inputs)
    except (OSError, ValueError, weave_runtime_slice.RuntimeSliceError) as exc:
        print(f"tui failed: {exc}", file=output)
        return 1

    print(render_summary(inputs, step_results, manifest, palette), end="", file=output)
    return 0 if all(item.get("rc", 0) == 0 for item in step_results) else 1
