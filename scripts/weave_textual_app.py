#!/usr/bin/env python3
"""Optional Textual implementation of the WEAVE lifecycle cockpit."""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Any

import weave_backend

TEXTUAL_VIEWS = ("overview", "stages", "artifacts", "files", "reviews", "help", "resume")
ROUTE_STAGES = tuple(weave_backend.ALL_STAGES)
SETUP_ROUTES = tuple(weave_backend.SETUP_STAGES)
PRODUCT_ROUTES = tuple(weave_backend.PRODUCT_STAGES)
GATED_LIVE_ROUTES = ("deployment", "kpi", "marketing", "iteration", "analysis")
PREVIEW_LIMIT = 1400
SPINNER_FRAMES = ("|", "/", "-", "\\")


SERVICE_BLUEPRINT_COPY: dict[str, dict[str, Any]] = {
    "first_run": {
        "headline": "First Run / Environment Detection",
        "ask": "I will inspect local WEAVE, Codex, and Hermes-adjacent surfaces, then ask which environment to attach to.",
        "choices": [
            "Attach an existing local environment",
            "Create or load a local WEAVE app workspace",
            "Connect a remote environment later when an authenticated connector exists",
            "Keep this run local-only with no live effects",
        ],
        "backstage": [
            "Read local state root and app registry",
            "Check Codex CLI availability without running it",
            "Show unsupported remote lanes as blockers instead of pretending they work",
        ],
        "proof": ["session state", "environment signal", "public-safe proof boundary"],
        "next": "Choose Create app to enter the local onboarding path.",
        "boundary": "No credentials, deployment, public sends, paid spend, or destructive mutation.",
    },
    "owner_profile": {
        "headline": "Owner Profile / Collaboration Style",
        "ask": "Tell WEAVE your experience level and the coworker style you want from the agent.",
        "choices": [
            "Save the default owner profile from launch arguments",
            "Type profile edits in the reply box and Save setup",
            "Skip optional style detail but keep public-safe defaults",
        ],
        "backstage": [
            "Write owner-profile and soul artifacts",
            "Make later prompt packets aware of the owner style",
            "Never store raw credentials or private topology here",
        ],
        "proof": ["owner-profile.md", "soul.md", "foundation.completed event"],
        "next": "Save setup, then review the app workspace.",
        "boundary": "Profile text must stay public-safe and non-secret.",
    },
    "app": {
        "headline": "App Workspace / Create Or Resume",
        "ask": "Create, load, or inspect the app workspace before lifecycle work begins.",
        "choices": [
            "Create or load the local app workspace",
            "Inspect app registry and prior artifacts",
            "Continue to Intent once foundation context exists",
        ],
        "backstage": [
            "Create app registry entry",
            "Initialize world model and review queue",
            "Keep generated source under apps/<app>/repo/primary",
        ],
        "proof": ["app.weave.json", "worldmodel.json", "review-queue.json"],
        "next": "Move to Intent when the app workspace exists.",
        "boundary": "Workspace creation is local file state only.",
    },
    "intent": {
        "headline": "Intent / Make The App Buildable",
        "ask": "Describe the product, users, flows, constraints, regions, budget posture, examples, and non-goals.",
        "choices": [
            "Save intent and prepare the intent prompt packet",
            "Ask WEAVE what is missing",
            "Submit intent proof for evaluation",
            "Approve only when the intent gate passes",
        ],
        "backstage": [
            "Validate intent against WEAVE sufficiency axioms",
            "Record missing information instead of inventing it",
            "Create research handoff when approved",
        ],
        "proof": ["intent artifact", "intent-sufficiency-review", "missing-information-list", "research-handoff"],
        "next": "Prepare prompt, submit proof, evaluate, approve, then advance to Research.",
        "boundary": "No implementation starts before intent is reviewable.",
    },
    "research": {
        "headline": "Research / Decide What Must Be Learned",
        "ask": "Review the research plan, add or remove questions, then approve the plan and research artifacts.",
        "choices": [
            "Draft or revise research plan",
            "Accept/edit the research plan",
            "Review research artifacts",
            "Continue research or approve enough evidence",
        ],
        "backstage": [
            "Unpack the approved intent into procedural and lateral research tracks",
            "Record source assumptions and local-only non-claims",
            "Prepare evidence for Selection",
        ],
        "proof": ["research-plan", "research-synthesis", "source-log", "selection-handoff"],
        "next": "Submit research proof and approve when enough information exists for options.",
        "boundary": "Public-web research is only claimed when an authorized research adapter actually ran.",
    },
    "selection": {
        "headline": "Selection / Choose The Product Direction",
        "ask": "Compare the best options from research, select one, edit one, or ask for a custom option.",
        "choices": [
            "Select one proposed option",
            "Discuss and edit an option",
            "Create a new custom option",
            "Approve selected direction for planning",
        ],
        "backstage": [
            "Tie option rationale to research artifacts",
            "Record rejected options and tradeoffs",
            "Update world model with selected direction",
        ],
        "proof": ["option-comparison", "selected-option", "selection-rationale"],
        "next": "Approve the selected option, then advance to Plan.",
        "boundary": "No planning lock-in without an owner-visible selected direction.",
    },
    "plan": {
        "headline": "Plan / Business And Engineering Operating Plan",
        "ask": "Review business, engineering, QA, deployment, KPI, marketing, iteration, risk, and capability plans.",
        "choices": [
            "Edit business plan",
            "Edit engineering plan",
            "Revise QA/deployment/KPI/marketing tracks",
            "Approve the plan for Engineering",
        ],
        "backstage": [
            "Convert intent, research, and selection into executable tracks",
            "Represent provider credentials as future capability requirements",
            "Write QA plan draft before Engineering begins",
        ],
        "proof": ["business-plan", "engineering-plan", "qa-plan", "deployment-plan", "kpi-plan", "marketing-plan"],
        "next": "Approve the plan, then advance to Engineering.",
        "boundary": "Provider credentials are not collected in this stage.",
    },
    "engineering": {
        "headline": "Engineering / Codex Builds Local Files",
        "ask": "Run Codex from the approved WEAVE context, inspect generated files, and attach feedback if needed.",
        "choices": [
            "Prepare the engineering prompt packet",
            "Run Codex with visible progress",
            "Inspect generated files",
            "Attach file:path feedback and rerun if needed",
        ],
        "backstage": [
            "Route execution through the backend Codex adapter",
            "Write executor and source manifests",
            "Route failures to the review queue instead of hiding them",
        ],
        "proof": ["executor-manifest", "source-manifest", "generated files", "file-feedback prompt packet"],
        "next": "Run Codex, inspect files, evaluate, approve, then advance to QA.",
        "boundary": "Codex may write only the local generated app workspace.",
    },
    "qa": {
        "headline": "QA / Surface-Aware Proof",
        "ask": "Authorize QA, review the surface-adapted QA proof, then approve or route failures back to Engineering.",
        "choices": [
            "Review the QA plan",
            "Run or record QA proof",
            "Rerun QA after feedback",
            "Approve QA when proof matches the app surface",
        ],
        "backstage": [
            "Adapt QA to website, CLI/TUI, backend/API, or mixed surfaces",
            "Record hard-gate results and artifacts",
            "Separate bad product behavior from bad QA method",
        ],
        "proof": ["qa-plan", "qa-result", "surface proof", "failure routing"],
        "next": "Approve QA only after evidence is reviewable.",
        "boundary": "QA does not imply deployment or production readiness.",
    },
    "deployment": {
        "headline": "Deployment Planning / Gated Live Effect",
        "ask": "Record deployment preferences and blockers without collecting credentials or mutating providers.",
        "choices": [
            "Record preferred provider and region",
            "Record domain/provider credential requirements",
            "Mark deployment blocked until authorized",
        ],
        "backstage": [
            "Convert deployment needs into capability refs",
            "Keep staging/production mutation behind a separate approval packet",
        ],
        "proof": ["deployment-plan", "capability-requirements", "blocked-live-effect note"],
        "next": "Keep deployment gated unless the owner creates a separate live-effect approval.",
        "boundary": "No domain purchase, provider mutation, or deploy happens here.",
    },
    "kpi": {
        "headline": "KPI Setup / Production Boundary Visible",
        "ask": "Choose 3 to 5 starter KPIs and decide which remain local placeholders until deployment exists.",
        "choices": ["Accept KPIs", "Edit KPI names", "Add or remove KPI", "Mark production analytics blocked"],
        "backstage": [
            "Tie KPIs to current world model",
            "Separate local counters from production instrumentation",
        ],
        "proof": ["kpi-plan", "local-vs-production instrumentation boundary"],
        "next": "Approve KPI plan or keep it blocked by deployment.",
        "boundary": "No production analytics writes occur.",
    },
    "marketing": {
        "headline": "Marketing / Organic And Paid Plans Stay Gated",
        "ask": "Record budget, allowed channels, organic cadence, and paid-channel blockers.",
        "choices": ["Plan organic work", "Record budget", "Create gated heartbeat jobs", "Hold public sends"],
        "backstage": [
            "Create marketing plan from latest world model",
            "Represent recurring jobs as gated local plans",
        ],
        "proof": ["marketing-plan", "budget posture", "gated heartbeat plan"],
        "next": "Use planning artifacts only until public-send/spend approval exists.",
        "boundary": "No public post, email, message, or paid ad is sent.",
    },
    "iteration": {
        "headline": "Iteration / Feedback Into Engineering Loops",
        "ask": "Turn feedback, QA findings, and owner notes into proposed issues for approval.",
        "choices": ["Approve issue", "Reject issue", "Route to Engineering", "Inspect evidence"],
        "backstage": [
            "Aggregate feedback into review queue items",
            "Route accepted items back through Engineering and QA",
        ],
        "proof": ["iteration-plan", "issue candidates", "accepted/rejected decisions"],
        "next": "Approve an iteration item to start a new engineering/QA loop.",
        "boundary": "No live recurring schedule starts without separate approval.",
    },
    "analysis": {
        "headline": "Analysis / Improvement Cadence",
        "ask": "Review improvement candidates, sources, and cadence for future analysis work.",
        "choices": ["Accept cadence", "Edit sources", "Run local analysis", "Hold external scanning"],
        "backstage": [
            "Summarize feedback and competitive assumptions",
            "Keep external scanning gated until authorized",
        ],
        "proof": ["analysis-plan", "improvement candidates", "evidence links"],
        "next": "Approve local analysis cadence or keep it gated.",
        "boundary": "No external scanning is claimed without an authorized adapter.",
    },
    "completion": {
        "headline": "Completion / Audit The Claim",
        "ask": "Review whether the lifecycle claim is actually proven, then accept or keep gaps open.",
        "choices": ["Audit proof", "List gaps", "Accept completion", "Keep the goal open"],
        "backstage": [
            "Compare product contract against artifacts",
            "Record non-claims and remaining blockers",
        ],
        "proof": ["completion-matrix", "proof ledger", "non-claims"],
        "next": "Close only when the proof surface and owner mental model match.",
        "boundary": "Never close on a PR, test run, or demo alone.",
    },
}


def textual_available() -> bool:
    try:
        import textual  # noqa: F401
    except Exception:
        return False
    return True


def missing_textual_message() -> str:
    return (
        "Textual is required for the full-screen WEAVE cockpit. "
        "Install dependencies with `python3 -m pip install -r requirements.txt`, "
        "or run non-interactive proof commands with `bin/weave tui --plain --no-color`."
    )


def prepare_textual_color_environment(textual_args: Any) -> None:
    """Keep Textual rich even when non-interactive harness shells disable color.

    The legacy/plain renderer honors --no-color. The Textual product surface is
    the visual TUI, so proof captures and normal launches should not inherit
    NO_COLOR/TERM=dumb from Codex's automation shell unless the operator
    explicitly requested no color.
    """

    if getattr(textual_args, "no_color", False):
        return
    os.environ.pop("NO_COLOR", None)
    os.environ.setdefault("COLORTERM", "truecolor")
    if os.environ.get("TERM", "") in {"", "dumb"}:
        os.environ["TERM"] = "xterm-256color"
    os.environ.setdefault("FORCE_COLOR", "1")


def parse_feedback_target(text: str, *, default_stage: str) -> dict[str, str]:
    """Parse lightweight file/artifact feedback commands from the composer."""

    cleaned = text.strip()
    lowered = cleaned.lower()
    for prefix, target_type in (("file:", "file"), ("artifact:", "artifact")):
        if not lowered.startswith(prefix):
            continue
        remainder = cleaned[len(prefix) :].strip()
        if ":" not in remainder:
            return {
                "stage": default_stage,
                "owner_text": remainder,
                "target_type": target_type,
                "target_ref": "",
                "feedback_class": "correction",
            }
        target_ref, owner_text = remainder.split(":", 1)
        return {
            "stage": default_stage,
            "owner_text": owner_text.strip(),
            "target_type": target_type,
            "target_ref": target_ref.strip(),
            "feedback_class": "correction",
        }
    return {
        "stage": default_stage,
        "owner_text": cleaned,
        "target_type": "stage",
        "target_ref": "",
        "feedback_class": "preference",
    }


def feedback_hint() -> str:
    return "Feedback syntax: plain text, file:path: change, or artifact:path: change."


def safe_preview(root: Path, relative_ref: str, *, limit: int = PREVIEW_LIMIT) -> str:
    """Return a short public-safe preview for a WEAVE-local artifact or file."""

    if not relative_ref:
        return "No reference available."
    try:
        candidate = (root / relative_ref).resolve()
        candidate.relative_to(root.resolve())
    except (OSError, ValueError):
        return "Preview blocked: reference is outside the WEAVE root."
    if not candidate.exists() or not candidate.is_file():
        return "Preview unavailable: file is missing."
    text = candidate.read_text(encoding="utf-8", errors="replace")
    cleaned = text.strip()
    if len(cleaned) > limit:
        return cleaned[:limit].rstrip() + "\n... [preview truncated]"
    return cleaned or "[empty file]"


def route_copy(stage: str) -> dict[str, Any]:
    return SERVICE_BLUEPRINT_COPY.get(stage, SERVICE_BLUEPRINT_COPY["completion"])


def status_badge(status: str) -> str:
    color = {
        "active": "bold cyan",
        "approved": "bold green",
        "ready": "bold blue",
        "blocked": "bold red",
        "not_started": "dim",
    }.get(status, "white")
    return f"[{color}]{status.replace('_', ' ')}[/{color}]"


def plain_status(status: str) -> str:
    return status.replace("_", " ")


def progress_rail(rows: list[dict[str, Any]], selected_stage: str) -> str:
    parts: list[str] = []
    for row in rows:
        stage = str(row.get("stage") or "")
        status = str(row.get("status") or "not_started")
        label = weave_backend.stage_label(stage)[:4].upper()
        if stage == selected_stage:
            marker = "SEL"
            color = "bold cyan"
        elif status == "approved":
            marker = "OK"
            color = "green"
        elif status == "active":
            marker = "NOW"
            color = "yellow"
        elif status == "ready":
            marker = "RDY"
            color = "blue"
        else:
            marker = "--"
            color = "dim"
        parts.append(f"[{color}]{label}:{marker}[/{color}]")
    return "  ".join(parts)


def environment_signal(root: Path, app_id: str) -> dict[str, Any]:
    """Collect local-only setup facts for the first-run screen."""

    try:
        app = weave_backend.weave_runtime_slice.load_app(root, app_id)
        app_exists = True
        current_stage = app.get("current_stage", "intent")
    except Exception:
        app_exists = False
        current_stage = ""
    return {
        "weave_root_exists": root.exists(),
        "root_ready": weave_backend.root_ready(root),
        "codex_cli": bool(shutil.which("codex")),
        "app_exists": app_exists,
        "current_stage": current_stage,
        "hermes_remote_attach": "not_configured",
        "live_effects": False,
    }


def build_app(args: Any):
    prepare_textual_color_environment(args)
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, LoadingIndicator, RichLog, Static
    except Exception:
        raise RuntimeError(missing_textual_message())

    class WeaveTextualApp(App[None]):
        CSS = """
        Screen {
            background: #071016;
            color: #f5efe7;
        }

        Header {
            background: #0b1b24;
            color: #38d6ff;
            text-style: bold;
        }

        Footer {
            background: #0b1b24;
            color: #d6f7ff;
        }

        #layout {
            height: 1fr;
        }

        #rail {
            width: 32;
            min-width: 28;
            background: #0b141b;
            border: solid #2c5870;
            padding: 1;
        }

        #work {
            width: 1fr;
            padding: 1 2;
            background: #08121a;
        }

        #evidence {
            width: 46;
            min-width: 38;
            background: #0b141b;
            border: solid #2c5870;
            padding: 1;
        }

        #brand {
            color: #38d6ff;
            text-style: bold;
            margin-bottom: 1;
        }

        #nav, #focus-hint {
            color: #9fb9c5;
            margin-bottom: 1;
        }

        #stage-list {
            height: 1fr;
            border: tall #1f3543;
            background: #101820;
        }

        #view-title {
            color: #38d6ff;
            text-style: bold;
            margin-bottom: 1;
        }

        #hero {
            border: tall #31718d;
            background: #0d1c26;
            padding: 1 2;
            margin-bottom: 1;
            height: 7;
        }

        #activity {
            border: tall #3c5b39;
            background: #101c18;
            color: #b7f7bf;
            padding: 0 2;
            height: 3;
            margin-bottom: 1;
        }

        #loader {
            height: 1;
            margin-bottom: 1;
        }

        #transcript {
            height: 1fr;
            border: tall #273f50;
            background: #0e1821;
            padding: 1 2;
            margin-bottom: 1;
        }

        #actions {
            height: auto;
            border: tall #273f50;
            background: #111923;
            padding: 1;
            margin-bottom: 1;
        }

        #evidence-log {
            height: 1fr;
            border: tall #273f50;
            background: #111820;
            padding: 1;
        }

        Button {
            margin-right: 0;
            min-width: 9;
        }

        Button.-primary {
            background: #1688d9;
            color: #ffffff;
            text-style: bold;
        }

        #composer {
            dock: bottom;
            height: 3;
            border: solid #2c5870;
            background: #080f14;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("escape", "back", "Back"),
            ("b", "back", "Back"),
            ("r", "refresh_projection", "Refresh"),
            ("o", "view_overview", "Overview"),
            ("t", "view_stages", "Stages"),
            ("i", "view_artifacts", "Artifacts"),
            ("l", "view_files", "Files"),
            ("v", "view_reviews", "Reviews"),
            ("h", "view_help", "Help"),
            ("m", "view_resume", "Resume"),
            ("c", "create_app", "Create app"),
            ("s", "save_setup", "Setup"),
            ("p", "prepare_prompt", "Prompt"),
            ("x", "run_executor", "Run Codex"),
            ("u", "submit_stage", "Submit"),
            ("e", "evaluate_stage", "Evaluate"),
            ("a", "approve_stage", "Approve"),
            ("n", "advance_stage", "Advance"),
            ("f", "focus_composer", "Feedback"),
            ("g", "record_feedback", "Record feedback"),
        ]

        def __init__(self, textual_args: Any) -> None:
            super().__init__()
            self.args = textual_args
            self.root = Path(textual_args.weave_root)
            self.app_id = textual_args.app_id
            self.app_name = textual_args.app_name
            self.view = self.restore_view()
            self.route = self.restore_route()
            self.route_history: list[str] = []
            self.stage_order: list[str] = []
            self.spinner_index = 0
            self.activity: dict[str, Any] = {"state": "idle", "label": "Idle", "message": "Ready for owner input."}
            self.projection = self.load_projection(self.route)

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Horizontal(id="layout"):
                with Vertical(id="rail"):
                    yield Static("WEAVE Cockpit", id="brand")
                    yield Static(id="nav")
                    yield Static("Lifecycle", classes="accent")
                    yield ListView(id="stage-list")
                    yield Static(id="focus-hint")
                with Vertical(id="work"):
                    yield Static(id="view-title")
                    yield Static(id="hero")
                    yield Static(id="activity")
                    yield LoadingIndicator(id="loader")
                    yield RichLog(id="transcript", wrap=True, highlight=True, markup=True)
                    with Horizontal(id="actions"):
                        yield Button("Create app", id="create-app", variant="primary")
                        yield Button("Save setup", id="save-setup")
                        yield Button("Prepare prompt", id="prepare-prompt")
                        yield Button("Run Codex", id="run-executor")
                        yield Button("Submit stage", id="submit-stage")
                        yield Button("Evaluate", id="evaluate-stage")
                        yield Button("Approve", id="approve-stage")
                        yield Button("Advance", id="advance-stage")
                        yield Button("Record feedback", id="record-feedback")
                        yield Button("Refresh", id="refresh")
                with Vertical(id="evidence"):
                    yield Static("Evidence", id="evidence-title")
                    yield RichLog(id="evidence-log", wrap=True, highlight=True, markup=True)
            yield Input(placeholder="Reply, give feedback, or use file:path: / artifact:path: feedback...", id="composer")
            yield Footer()

        def on_mount(self) -> None:
            self.set_interval(0.4, self.tick_activity)
            self.render_projection("Opened WEAVE Textual cockpit.")
            self.query_one("#stage-list", ListView).focus()

        def restore_view(self) -> str:
            try:
                path = weave_backend.textual_session_path(self.root, self.app_id)
                if not path.exists():
                    return "overview"
                session = json.loads(path.read_text(encoding="utf-8"))
                view = str(session.get("active_view") or "overview")
                return view if view in TEXTUAL_VIEWS else "overview"
            except Exception:
                return "overview"

        def restore_route(self) -> str:
            try:
                path = weave_backend.textual_session_path(self.root, self.app_id)
                if path.exists():
                    session = json.loads(path.read_text(encoding="utf-8"))
                    route = str(session.get("active_route") or session.get("current_stage") or "first_run")
                    return route if route in ROUTE_STAGES else "first_run"
            except Exception:
                pass
            projection = weave_backend.dashboard_projection(self.root, app_id=self.app_id, app_name=self.app_name)
            route = str(projection.get("app", {}).get("current_stage") or "first_run")
            return route if route in ROUTE_STAGES else "first_run"

        def app_exists(self) -> bool:
            try:
                weave_backend.weave_runtime_slice.load_app(self.root, self.app_id)
                return True
            except Exception:
                return False

        def load_projection(self, selected_stage: str | None = None) -> dict[str, Any]:
            selected = selected_stage if selected_stage in ROUTE_STAGES else "first_run"
            projection = weave_backend.dashboard_projection(self.root, app_id=self.app_id, app_name=self.app_name)
            projection["selected_stage"] = selected
            projection["environment"] = environment_signal(self.root, self.app_id)
            projection["stage"] = weave_backend.stage_projection(self.root, self.app_id if self.app_exists() else None, selected)
            return projection

        def save_session(self, reason: str) -> None:
            """Persist both visible view and selected lifecycle route."""

            app = self.projection.get("app", {})
            payload = {
                "schema": weave_backend.TEXTUAL_SESSION_SCHEMA,
                "app_id": self.app_id,
                "app_name": self.app_name,
                "active_view": self.view,
                "active_route": self.route,
                "current_stage": app.get("current_stage", "first_run"),
                "stage_state": app.get("stage_state", ""),
                "last_activity_state": self.activity.get("state", "idle"),
                "reason": reason,
                "public_safe": True,
                "secret_value_printed": False,
            }
            path = weave_backend.textual_session_path(self.root, self.app_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        def actual_current_stage(self) -> str:
            stage = str(self.projection.get("app", {}).get("current_stage") or "first_run")
            return stage if stage in ROUTE_STAGES else "first_run"

        def selected_stage(self) -> str:
            return self.route if self.route in ROUTE_STAGES else "first_run"

        def command_stage(self) -> str:
            """Use the actual runtime stage for mutations, not a previewed future route."""

            stage = self.actual_current_stage()
            return stage if stage in PRODUCT_ROUTES else "intent"

        def set_view(self, view: str, note: str = "") -> None:
            if view not in TEXTUAL_VIEWS:
                view = "overview"
            self.view = view
            self.projection = self.load_projection(self.route)
            self.render_projection(note or f"Switched to {view} view.")

        def activate_route(self, stage: str, note: str = "", *, push_history: bool = True) -> None:
            if stage not in ROUTE_STAGES:
                return
            if push_history and self.route != stage:
                self.route_history.append(self.route)
            self.route = stage
            self.view = "overview"
            self.projection = self.load_projection(stage)
            self.render_projection(note or f"Opened {weave_backend.stage_label(stage)}.")

        def tick_activity(self) -> None:
            if self.activity.get("state") != "running":
                return
            self.spinner_index += 1
            self.render_activity()

        def render_projection(self, note: str = "") -> None:
            stage_list = self.query_one("#stage-list", ListView)
            stage_list.clear()
            self.stage_order = []
            selected = self.selected_stage()
            rows = self.projection.get("lifecycle_rail", [])
            for row in rows:
                stage = str(row.get("stage") or "")
                self.stage_order.append(stage)
                active = stage == selected
                current = stage == self.actual_current_stage()
                prefix = ">" if active else ("*" if current else " ")
                label = (
                    f"{prefix} {int(row.get('index') or 0):02d} "
                    f"[b]{row.get('label')}[/b]\n"
                    f"   {status_badge(str(row.get('status') or 'not_started'))}"
                )
                # ListView.clear removes children asynchronously in Textual 8,
                # so row widgets intentionally avoid stable IDs; the stage
                # mapping lives in stage_order instead.
                stage_list.append(ListItem(Label(label)))
            if selected in self.stage_order:
                stage_list.index = self.stage_order.index(selected)

            self.render_nav()
            self.render_hero()
            self.render_activity()
            self.render_buttons()

            transcript = self.query_one("#transcript", RichLog)
            transcript.clear()
            if note:
                transcript.write(f"[bold green]{note}[/bold green]\n")
            self.render_active_view(transcript)

            evidence = self.query_one("#evidence-log", RichLog)
            evidence.clear()
            self.render_evidence(evidence)
            self.save_session(f"render:{self.view}:{self.route}")

        def render_nav(self) -> None:
            env = self.projection.get("environment", {})
            self.query_one("#nav", Static).update(
                "\n".join(
                    [
                        "[bold cyan]views[/bold cyan]",
                        "o overview",
                        "t stages",
                        "i artifacts",
                        "l files",
                        "v reviews",
                        "h help",
                        "m resume",
                        "",
                        f"codex: {'ready' if env.get('codex_cli') else 'missing'}",
                        f"state: {'ready' if env.get('root_ready') else 'setup'}",
                    ]
                )
            )
            self.query_one("#focus-hint", Static).update("Arrows select stages. Enter/click opens. Tab moves panes. Esc goes back.")
            title = f"{self.view.upper()} / {weave_backend.stage_label(self.selected_stage()).upper()}"
            self.query_one("#view-title", Static).update(title)

        def render_hero(self) -> None:
            app = self.projection.get("app", {})
            copy = route_copy(self.selected_stage())
            rows = self.projection.get("lifecycle_rail", [])
            boundary = self.projection.get("proof_boundary", {})
            self.query_one("#hero", Static).update(
                "\n".join(
                    [
                        f"[bold #38d6ff]{copy['headline']}[/bold #38d6ff]",
                        f"[bold]{app.get('name', self.app_name)}[/bold]  id={app.get('app_id', self.app_id)}  mode={app.get('control_mode', 'handoff')}",
                        f"runtime stage: [yellow]{self.actual_current_stage()}[/yellow]  selected screen: [cyan]{self.selected_stage()}[/cyan]",
                        f"proof boundary: stop before {', '.join(boundary.get('stop_before', []))}",
                        progress_rail(rows, self.selected_stage()),
                    ]
                )
            )

        def render_activity(self) -> None:
            loader = self.query_one("#loader", LoadingIndicator)
            state = str(self.activity.get("state") or "idle")
            if state == "running":
                started = float(self.activity.get("started_at") or time.time())
                elapsed = max(0.0, time.time() - started)
                frame = SPINNER_FRAMES[self.spinner_index % len(SPINNER_FRAMES)]
                width = 20
                filled = min(width, int(elapsed) % (width + 1))
                bar = "#" * filled + "." * (width - filled)
                loader.display = True
                self.query_one("#activity", Static).update(
                    f"[bold green]{frame} {self.activity.get('label', 'Working')}[/bold green]  "
                    f"elapsed={elapsed:0.1f}s  [{bar}]\n{self.activity.get('message', '')}"
                )
                return
            loader.display = False
            color = "green" if state == "complete" else ("red" if state == "failed" else "dim")
            self.query_one("#activity", Static).update(
                f"[{color}]state={plain_status(state)}[/{color}]  {self.activity.get('label', 'Idle')}\n{self.activity.get('message', 'Ready.')}"
            )

        def render_buttons(self) -> None:
            selected = self.selected_stage()
            current = self.actual_current_stage()
            running = self.activity.get("state") == "running"
            app_exists = self.app_exists()
            primary_button = "refresh"
            if not app_exists or selected in {"first_run", "app"}:
                primary_button = "create-app"
            elif selected == "owner_profile":
                primary_button = "save-setup"
            elif selected == "engineering" and selected == current:
                primary_button = "run-executor"
            elif selected in PRODUCT_ROUTES and selected == current:
                gate = self.projection.get("stage", {}).get("gate", {})
                evaluation = self.projection.get("stage", {}).get("evaluation", {})
                if not gate.get("passed"):
                    primary_button = "submit-stage"
                elif evaluation and evaluation.get("decision") not in {"accepted", "pass", "passed"}:
                    primary_button = "evaluate-stage"
                elif selected not in self.projection.get("app", {}).get("approved_stages", []):
                    primary_button = "approve-stage"
                else:
                    primary_button = "advance-stage"
            button_state = {
                "create-app": (selected in {"first_run", "app"} or not app_exists, "Create app"),
                "save-setup": (selected in {"owner_profile", "first_run", "intent"} and app_exists, "Save setup"),
                "prepare-prompt": (selected in PRODUCT_ROUTES and app_exists and selected == current, "Prompt"),
                "run-executor": (selected == "engineering" and app_exists and selected == current, "Run Codex"),
                "submit-stage": (selected in PRODUCT_ROUTES and app_exists and selected == current, "Submit"),
                "evaluate-stage": (selected in PRODUCT_ROUTES and app_exists and selected == current, "Evaluate"),
                "approve-stage": (selected in PRODUCT_ROUTES and app_exists and selected == current, "Approve"),
                "advance-stage": (selected in PRODUCT_ROUTES and app_exists and selected == current, "Advance"),
                "record-feedback": (app_exists and selected not in {"first_run"}, "Revise"),
                "refresh": (False, "Refresh"),
            }
            for button_id, (enabled, label) in button_state.items():
                button = self.query_one(f"#{button_id}", Button)
                button.label = label
                button.display = enabled
                button.disabled = running or not enabled
                button.variant = "primary" if button_id == primary_button and enabled else "default"

        def render_active_view(self, transcript: Any) -> None:
            if self.view == "overview":
                self.render_route_screen(transcript)
            elif self.view == "stages":
                self.render_stages(transcript)
            elif self.view == "artifacts":
                self.render_artifacts(transcript)
            elif self.view == "files":
                self.render_files(transcript)
            elif self.view == "reviews":
                self.render_reviews(transcript)
            elif self.view == "help":
                self.render_help(transcript)
            elif self.view == "resume":
                self.render_resume(transcript)
            else:
                self.render_route_screen(transcript)

        def render_route_screen(self, transcript: Any) -> None:
            selected = self.selected_stage()
            copy = route_copy(selected)
            stage = self.projection.get("stage", {})
            current = self.actual_current_stage()
            transcript.write(f"[bold cyan]{copy['headline']}[/bold cyan]")
            transcript.write(f"[bold]Ask[/bold]\n{copy['ask']}\n")
            if selected in GATED_LIVE_ROUTES:
                transcript.write("[bold yellow]Gated live-effect planning screen[/bold yellow]")
                transcript.write("This screen is real for planning and review, but live provider actions require a separate approval packet.\n")
            if selected in PRODUCT_ROUTES and selected != current:
                transcript.write(
                    f"[bold yellow]Preview mode[/bold yellow]: runtime is currently at [b]{current}[/b]. "
                    "Visible mutation buttons unlock when this becomes the active runtime stage.\n"
                )
            if selected == "first_run":
                self.render_environment(transcript)
            elif selected == "owner_profile":
                self.render_owner_profile(transcript)
            elif selected == "app":
                self.render_app_workspace(transcript)
            transcript.write("[bold]Choices[/bold]")
            for index, choice in enumerate(copy.get("choices", []), 1):
                transcript.write(f"  [cyan]{index}[/cyan]. {choice}")
            transcript.write("")
            transcript.write("[bold]Backstage system[/bold]")
            for item in copy.get("backstage", []):
                transcript.write(f"  - {item}")
            transcript.write("")
            transcript.write("[bold]Required proof[/bold]")
            for item in copy.get("proof", []):
                transcript.write(f"  - {item}")
            transcript.write("")
            transcript.write(f"[bold]Next action[/bold]\n{copy.get('next', 'Choose the next safe action.')}")
            transcript.write(f"\n[bold red]Stop boundary[/bold red]\n{copy.get('boundary', 'No unsafe live effects.')}")
            required_outputs = stage.get("required_outputs", [])
            if required_outputs:
                transcript.write("\n[bold]Prompt-library outputs[/bold]")
                for output in required_outputs:
                    transcript.write(f"  - {output}")
            self.render_gate_summary(transcript, stage)
            transcript.write("\n" + feedback_hint())

        def render_environment(self, transcript: Any) -> None:
            env = self.projection.get("environment", {})
            transcript.write("[bold]Environment signal[/bold]")
            transcript.write(f"  - WEAVE state root: {'present' if env.get('weave_root_exists') else 'missing'}")
            transcript.write(f"  - root initialized: {env.get('root_ready')}")
            transcript.write(f"  - Codex CLI: {'available' if env.get('codex_cli') else 'missing'}")
            transcript.write(f"  - app workspace: {'present' if env.get('app_exists') else 'missing'}")
            transcript.write(f"  - remote Hermes attach: {env.get('hermes_remote_attach')}")
            transcript.write("")

        def render_owner_profile(self, transcript: Any) -> None:
            transcript.write("[bold]Current owner defaults[/bold]")
            transcript.write(f"  - experience: {getattr(self.args, 'owner_experience', '') or 'not provided'}")
            transcript.write(f"  - coworker style: {getattr(self.args, 'coworker_style', '') or 'not provided'}")
            transcript.write(f"  - target user: {getattr(self.args, 'target_user', '') or 'not provided'}")
            transcript.write("Type edits in the reply box, then use Save setup.\n")

        def render_app_workspace(self, transcript: Any) -> None:
            app = self.projection.get("app", {})
            env = self.projection.get("environment", {})
            transcript.write("[bold]Workspace[/bold]")
            transcript.write(f"  - app id: {app.get('app_id', self.app_id)}")
            transcript.write(f"  - app name: {app.get('name', self.app_name)}")
            transcript.write(f"  - app exists: {env.get('app_exists')}")
            transcript.write(f"  - current runtime stage: {app.get('current_stage', 'first_run')}")
            transcript.write("Use Create app if the workspace is missing. Use Intent when foundation context is ready.\n")

        def render_gate_summary(self, transcript: Any, stage: dict[str, Any]) -> None:
            gate = stage.get("gate", {})
            if not gate:
                return
            transcript.write("\n[bold]Gate[/bold]")
            transcript.write(f"  - state: {'passing' if gate.get('passed') else 'blocked'}")
            for missing in gate.get("missing", [])[:8]:
                transcript.write(f"  - missing: [yellow]{missing}[/yellow]")
            evaluation = stage.get("evaluation", {})
            if evaluation:
                transcript.write(f"  - evaluation: {evaluation.get('decision') or evaluation.get('status')}")

        def render_stages(self, transcript: Any) -> None:
            transcript.write("[bold cyan]Lifecycle map[/bold cyan]")
            transcript.write("Click a row or focus the lifecycle rail with arrows and press Enter to open a screen.\n")
            for row in self.projection.get("lifecycle_rail", []):
                stage = str(row.get("stage") or "")
                marker = "selected" if stage == self.selected_stage() else ("runtime" if stage == self.actual_current_stage() else "")
                transcript.write(
                    f"  {int(row.get('index') or 0):02d}. [b]{row.get('label')}[/b] "
                    f"{status_badge(str(row.get('status') or 'not_started'))} {marker}"
                )
            transcript.write("\n[bold]Stage rule[/bold]")
            transcript.write("A selected future screen is inspectable, but mutation buttons unlock only on the current runtime stage.")

        def render_artifacts(self, transcript: Any) -> None:
            artifacts = self.projection.get("artifacts", [])
            transcript.write(f"[bold cyan]Artifacts ({len(artifacts)})[/bold cyan]")
            if not artifacts:
                transcript.write("No artifacts yet. Create the app, prepare prompts, or submit stage proof.")
                return
            for item in artifacts[-12:]:
                transcript.write(f"  - {item['path']}")
            latest = artifacts[-1]
            transcript.write(f"\n[bold]Latest artifact preview[/bold]\n{latest['path']}")
            transcript.write(safe_preview(self.root, latest["path"]))
            transcript.write("\nUse artifact:path: feedback to ask the agent to revise an artifact.")

        def render_files(self, transcript: Any) -> None:
            files = self.projection.get("files", [])
            transcript.write(f"[bold cyan]Generated files ({len(files)})[/bold cyan]")
            if not files:
                transcript.write("No generated app files yet. Run Engineering with Codex after Plan is approved.")
                return
            for item in files[-14:]:
                transcript.write(f"  - {item['path']}")
            latest = files[-1]
            transcript.write(f"\n[bold]Latest file preview[/bold]\n{latest['path']}")
            transcript.write(safe_preview(self.root, latest["path"]))
            transcript.write("\nUse file:path: feedback to attach revision feedback to a source file.")

        def render_reviews(self, transcript: Any) -> None:
            queue = self.projection.get("review_queue", {}).get("items", [])
            transcript.write(f"[bold cyan]Review queue ({len(queue)})[/bold cyan]")
            if not queue:
                transcript.write("No review items yet.")
            for item in queue[-14:]:
                target = f" -> {item.get('target_ref')}" if item.get("target_ref") else ""
                transcript.write(f"  - {item.get('stage')} [{item.get('kind')}] {item.get('text')}{target}")
            self.render_gate_summary(transcript, self.projection.get("stage", {}))
            transcript.write("\nOwner actions: approve only after review; use feedback to request revisions.")

        def render_help(self, transcript: Any) -> None:
            transcript.write("[bold cyan]How to operate WEAVE[/bold cyan]")
            transcript.write("This is a Textual TUI, not a plain CLI. You stay inside the cockpit and move between screens.")
            transcript.write("")
            transcript.write("[bold]Navigation[/bold]")
            transcript.write("  - Arrow through the lifecycle rail; Enter or mouse click opens the highlighted screen.")
            transcript.write("  - Tab and Shift-Tab move between rail, work pane, buttons, and reply box.")
            transcript.write("  - Esc or b returns from secondary views or previous lifecycle route.")
            transcript.write("  - o/t/i/l/v/h/m switch overview, stages, artifacts, files, reviews, help, resume.")
            transcript.write("")
            transcript.write("[bold]Workflow[/bold]")
            transcript.write("  - First Run -> Owner Profile -> App Workspace -> Intent -> Research -> Selection -> Plan -> Engineering -> QA.")
            transcript.write("  - Later stages are real planning screens but live effects remain gated.")
            transcript.write("")
            transcript.write("[bold]Actions[/bold]")
            transcript.write("  - Create app, Save setup, Prepare prompt, Submit stage, Evaluate, Approve, Advance, Run Codex.")
            transcript.write("  - Run Codex shows non-blocking progress and writes executor/source manifests.")
            transcript.write("")
            transcript.write(feedback_hint())
            transcript.write("Hard stop boundaries: credentials, deployment, public sends, paid spend, destructive changes, raw secret handling.")

        def render_resume(self, transcript: Any) -> None:
            session_path = weave_backend.textual_session_path(self.root, self.app_id)
            transcript.write("[bold cyan]Resume state[/bold cyan]")
            transcript.write(f"  - active_view: {self.view}")
            transcript.write(f"  - active_route: {self.route}")
            transcript.write(f"  - current_runtime_stage: {self.actual_current_stage()}")
            transcript.write(f"  - activity: {self.activity.get('state')}")
            try:
                session_ref = session_path.relative_to(self.root)
            except ValueError:
                session_ref = "local session file"
            transcript.write(f"  - session_ref: {session_ref}")
            transcript.write("")
            transcript.write("[bold]Proof boundary[/bold]")
            boundary = self.projection.get("proof_boundary", {})
            transcript.write(f"  - external_effects_executed: {boundary.get('external_effects_executed', [])}")
            transcript.write(f"  - stop_before: {', '.join(boundary.get('stop_before', []))}")
            transcript.write(f"  - secret_value_printed: {boundary.get('secret_value_printed', False)}")

        def render_evidence(self, evidence: Any) -> None:
            evidence.write(f"[bold cyan]Selected[/bold cyan] {weave_backend.stage_label(self.selected_stage())}")
            evidence.write(f"[bold yellow]Runtime[/bold yellow] {self.actual_current_stage()}")
            env = self.projection.get("environment", {})
            evidence.write(f"Codex {'ready' if env.get('codex_cli') else 'missing'} | app {'present' if env.get('app_exists') else 'missing'}\n")
            evidence.write("[bold]Review queue[/bold]")
            for item in self.projection.get("review_queue", {}).get("items", [])[:8]:
                evidence.write(f"- {item.get('stage')}: {item.get('text')}")
            evidence.write("\n[bold]Artifacts[/bold]")
            for item in self.projection.get("artifacts", [])[-8:]:
                evidence.write(f"- {item['path']}")
            evidence.write("\n[bold]Files[/bold]")
            for item in self.projection.get("files", [])[-8:]:
                evidence.write(f"- {item['path']}")

        def composer_text(self) -> str:
            return self.query_one("#composer", Input).value.strip()

        def run_backend_command(self, command: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
            result = weave_backend.dispatch(
                self.root,
                command,
                app_id=self.app_id,
                app_name=self.app_name,
                payload=payload or {},
            )
            self.projection = self.load_projection(self.route)
            if result.get("projection"):
                # Keep selected route independent from the backend's current-stage projection.
                self.projection.update({key: value for key, value in result["projection"].items() if key not in {"stage", "selected_stage"}})
                self.projection["stage"] = weave_backend.stage_projection(
                    self.root,
                    self.app_id if self.app_exists() else None,
                    self.route,
                )
                self.projection["selected_stage"] = self.route
                self.projection["environment"] = environment_signal(self.root, self.app_id)
            return result

        def action_refresh_projection(self) -> None:
            self.projection = self.load_projection(self.route)
            self.render_projection("Refreshed projection.")

        def action_view_overview(self) -> None:
            self.set_view("overview")

        def action_view_stages(self) -> None:
            self.set_view("stages")

        def action_view_artifacts(self) -> None:
            self.set_view("artifacts")

        def action_view_files(self) -> None:
            self.set_view("files")

        def action_view_reviews(self) -> None:
            self.set_view("reviews")

        def action_view_help(self) -> None:
            self.set_view("help")

        def action_view_resume(self) -> None:
            self.set_view("resume")

        def action_back(self) -> None:
            if self.view != "overview":
                self.set_view("overview", "Returned to the active lifecycle screen.")
                return
            if not self.route_history:
                self.render_projection("No previous lifecycle screen in this session.")
                return
            previous = self.route_history.pop()
            self.activate_route(previous, f"Returned to {weave_backend.stage_label(previous)}.", push_history=False)

        def action_create_app(self) -> None:
            result = weave_backend.dispatch(self.root, "workspace.create_app", app_id=self.app_id, app_name=self.app_name)
            self.route = "owner_profile"
            self.projection = self.load_projection(self.route)
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Create app", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Create app command completed."))

        def action_save_setup(self) -> None:
            text = self.composer_text()
            result = self.run_backend_command(
                "foundation.save",
                {
                    "owner_experience": getattr(self.args, "owner_experience", ""),
                    "coworker_style": getattr(self.args, "coworker_style", ""),
                    "app_intent": text or getattr(self.args, "intent", ""),
                    "target_user": getattr(self.args, "target_user", ""),
                },
            )
            self.route = "app" if result.get("ok") else self.route
            self.projection = self.load_projection(self.route)
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Save setup", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Setup saved."))

        def action_prepare_prompt(self) -> None:
            stage = self.command_stage()
            result = self.run_backend_command(
                "prompt.prepare",
                {"stage": stage, "substage": "start", "owner_message": self.composer_text()},
            )
            self.route = stage
            self.projection = self.load_projection(self.route)
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Prepare prompt", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Prompt prepared."))

        def action_submit_stage(self) -> None:
            stage = self.command_stage()
            owner_text = self.composer_text() or getattr(self.args, "intent", "")
            result = self.run_backend_command(
                "stage.submit",
                {
                    "stage": stage,
                    "owner_text": owner_text,
                    "agent_text": f"{weave_backend.stage_label(stage)} proof is ready for evaluation and owner review.",
                    "artifact_body": owner_text,
                },
            )
            self.route = stage
            self.projection = self.load_projection(self.route)
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Submit stage", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Stage submitted."))

        def action_run_executor(self) -> None:
            if self.activity.get("state") == "running":
                self.render_projection("A backend action is already running.")
                return
            payload = {
                "executor": "codex",
                "owner_message": self.composer_text() or getattr(self.args, "intent", ""),
                "timeout_seconds": getattr(self.args, "codex_timeout", 600),
            }
            self.route = "engineering"
            self.activity = {
                "state": "running",
                "label": "Codex engineering",
                "message": "Backend executor is building local app files. The TUI remains responsive.",
                "started_at": time.time(),
            }
            self.projection = self.load_projection(self.route)
            self.render_projection("Codex engineering started.")
            thread = threading.Thread(target=self._executor_thread, args=(payload,), daemon=True)
            thread.start()

        def _executor_thread(self, payload: dict[str, Any]) -> None:
            try:
                result = weave_backend.dispatch(
                    self.root,
                    "executor.run",
                    app_id=self.app_id,
                    app_name=self.app_name,
                    payload=payload,
                )
            except Exception as exc:  # noqa: BLE001
                result = {
                    "ok": False,
                    "message": f"Codex executor crashed before producing a backend result: {type(exc).__name__}",
                    "projection": weave_backend.dashboard_projection(self.root, app_id=self.app_id, app_name=self.app_name),
                }
            self.call_from_thread(self.finish_executor, result)

        def finish_executor(self, result: dict[str, Any]) -> None:
            self.route = "engineering"
            self.projection = self.load_projection(self.route)
            state = "complete" if result.get("ok") else "failed"
            self.activity = {
                "state": state,
                "label": "Codex engineering",
                "message": result.get("message", "Executor command completed."),
            }
            self.render_projection(result.get("message", "Executor command completed."))

        def action_evaluate_stage(self) -> None:
            stage = self.command_stage()
            run_hard_gates = bool(getattr(self.args, "run_engineering_gates", False)) and stage in {"engineering", "qa"}
            result = self.run_backend_command("stage.evaluate", {"stage": stage, "run_gates": run_hard_gates})
            self.route = stage
            self.projection = self.load_projection(self.route)
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Evaluate", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Evaluation completed."))

        def action_approve_stage(self) -> None:
            stage = self.command_stage()
            result = self.run_backend_command("stage.approve", {"stage": stage, "note": "Approved in Textual cockpit."})
            self.route = stage
            self.projection = self.load_projection(self.route)
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Approve", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Approval command completed."))

        def action_advance_stage(self) -> None:
            result = self.run_backend_command("stage.advance", {"note": "Advanced in Textual cockpit."})
            self.projection = self.load_projection(self.route)
            runtime_stage = str(result.get("projection", {}).get("app", {}).get("current_stage") or self.actual_current_stage())
            if result.get("ok") and runtime_stage in ROUTE_STAGES:
                self.route = runtime_stage
            self.projection = self.load_projection(self.route)
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Advance", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Advance command completed."))

        def action_focus_composer(self) -> None:
            self.query_one("#composer", Input).focus()

        def action_record_feedback(self) -> None:
            composer = self.query_one("#composer", Input)
            result = self.run_backend_command("feedback.record", parse_feedback_target(composer.value, default_stage=self.command_stage()))
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Feedback", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Feedback recorded."))

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            if event.list_view.id != "stage-list":
                return
            if 0 <= event.index < len(self.stage_order):
                stage = self.stage_order[event.index]
                self.activate_route(stage, f"Opened {weave_backend.stage_label(stage)} from lifecycle rail.")
                event.stop()

        def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
            if event.list_view.id != "stage-list":
                return
            index = event.list_view.index
            if index is not None and 0 <= index < len(self.stage_order):
                stage = self.stage_order[index]
                self.query_one("#focus-hint", Static).update(
                    f"Highlighted {weave_backend.stage_label(stage)}. Press Enter or click to open."
                )

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "create-app":
                self.action_create_app()
            elif event.button.id == "save-setup":
                self.action_save_setup()
            elif event.button.id == "prepare-prompt":
                self.action_prepare_prompt()
            elif event.button.id == "run-executor":
                self.action_run_executor()
            elif event.button.id == "submit-stage":
                self.action_submit_stage()
            elif event.button.id == "evaluate-stage":
                self.action_evaluate_stage()
            elif event.button.id == "approve-stage":
                self.action_approve_stage()
            elif event.button.id == "advance-stage":
                self.action_advance_stage()
            elif event.button.id == "record-feedback":
                self.action_record_feedback()
            elif event.button.id == "refresh":
                self.action_refresh_projection()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            text = event.value.strip()
            if not text:
                return
            result = self.run_backend_command("feedback.record", parse_feedback_target(text, default_stage=self.command_stage()))
            event.input.value = ""
            self.activity = {"state": "complete" if result.get("ok") else "failed", "label": "Feedback", "message": result.get("message", "")}
            self.render_projection(result.get("message", "Feedback recorded."))

    return WeaveTextualApp(args)


def run(args: Any) -> int:
    try:
        app = build_app(args)
    except RuntimeError as exc:
        print(str(exc))
        return 1
    app.run()
    return 0
