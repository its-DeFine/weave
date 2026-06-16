#!/usr/bin/env python3
"""Optional Textual implementation of the WEAVE lifecycle cockpit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import weave_backend

TEXTUAL_VIEWS = ("overview", "stages", "artifacts", "files", "reviews", "help", "resume")
PREVIEW_LIMIT = 1400


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


def parse_feedback_target(text: str, *, default_stage: str) -> dict[str, str]:
    """Parse lightweight file/artifact feedback commands from the composer.

    The TUI keeps the interaction conversational, but operators still need a
    precise way to point at a file or artifact. Supported forms are:
    `file:path: feedback`, `artifact:path: feedback`, and plain stage feedback.
    """

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
    """Return a short public-safe preview for a WEAVE-local artifact or file.

    The TUI needs to let the owner inspect work without dropping them to a
    separate editor. Keep previews bounded and scoped under the configured
    WEAVE root so screenshots and proof artifacts do not expose host paths.
    """

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


def build_app(args: Any):
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, RichLog, Static
    except Exception:
        raise RuntimeError(missing_textual_message())

    class WeaveTextualApp(App[None]):
        CSS = """
        Screen {
            background: #070b0f;
            color: #f6f0e7;
        }

        #layout {
            height: 1fr;
        }

        #rail {
            width: 28;
            min-width: 24;
            background: #0d141b;
            border: solid #304353;
            padding: 1;
        }

        #work {
            width: 1fr;
            padding: 1 2;
        }

        #evidence {
            width: 42;
            min-width: 36;
            background: #0d141b;
            border: solid #304353;
            padding: 1;
        }

        .panel {
            border: solid #304353;
            background: #111820;
            padding: 1 2;
            margin-bottom: 1;
        }

        .accent {
            color: #38d6ff;
            text-style: bold;
        }

        .warning {
            color: #ffd75f;
        }

        Button {
            margin-right: 1;
        }

        #composer {
            dock: bottom;
            height: 3;
            border: solid #304353;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
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
        ]

        def __init__(self, textual_args: Any) -> None:
            super().__init__()
            self.args = textual_args
            self.root = Path(textual_args.weave_root)
            self.app_id = textual_args.app_id
            self.app_name = textual_args.app_name
            self.view = self.restore_view()
            self.projection = weave_backend.dashboard_projection(self.root, app_id=self.app_id, app_name=self.app_name)

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Horizontal(id="layout"):
                with Vertical(id="rail"):
                    yield Static("WEAVE Cockpit", classes="accent")
                    yield Static(id="nav")
                    yield Static("Lifecycle")
                    yield ListView(id="stage-list")
                with Vertical(id="work"):
                    yield Static(id="view-title", classes="accent")
                    yield Static(id="hero", classes="panel")
                    yield RichLog(id="transcript", classes="panel", wrap=True, highlight=True)
                    with Horizontal(id="actions", classes="panel"):
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
                    yield Static("Evidence", classes="accent")
                    yield RichLog(id="evidence-log", wrap=True, highlight=True)
            yield Input(placeholder="Reply, give feedback, or ask to inspect an artifact...", id="composer")
            yield Footer()

        def on_mount(self) -> None:
            self.render_projection("Opened WEAVE Textual cockpit.")

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

        def save_session(self, reason: str) -> None:
            """Persist the operator's visible cockpit position for resume."""

            app = self.projection.get("app", {})
            payload = {
                "schema": weave_backend.TEXTUAL_SESSION_SCHEMA,
                "app_id": self.app_id,
                "app_name": self.app_name,
                "active_view": self.view,
                "current_stage": app.get("current_stage", "first_run"),
                "stage_state": app.get("stage_state", ""),
                "reason": reason,
                "public_safe": True,
                "secret_value_printed": False,
            }
            path = weave_backend.textual_session_path(self.root, self.app_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        def set_view(self, view: str, note: str = "") -> None:
            if view not in TEXTUAL_VIEWS:
                view = "overview"
            self.view = view
            self.render_projection(note or f"Switched to {view} view.")

        def render_projection(self, note: str = "") -> None:
            stage_list = self.query_one("#stage-list", ListView)
            stage_list.clear()
            for row in self.projection.get("lifecycle_rail", []):
                marker = ">" if row.get("status") == "active" else " "
                stage_list.append(ListItem(Label(f"{marker} {row['index']:02d} {row['label']} [{row['status']}]")))

            self.query_one("#nav", Static).update(
                "\n".join(
                    [
                        "[o] overview",
                        "[t] stages",
                        "[i] artifacts",
                        "[l] files",
                        "[v] reviews",
                        "[h] help",
                        "[m] resume",
                    ]
                )
            )
            self.query_one("#view-title", Static).update(f"{self.view.upper()} VIEW")

            app = self.projection.get("app", {})
            stage = self.projection.get("stage", {})
            self.query_one("#hero", Static).update(
                f"[b]{app.get('name', self.app_name)}[/b]\n"
                f"Stage: {stage.get('label', app.get('current_stage', 'first_run'))} | "
                f"Worker: {stage.get('worker_role', 'WEAVE guide')}\n"
                f"{stage.get('owner_visible_goal', 'Choose the next safe action.')}"
            )

            transcript = self.query_one("#transcript", RichLog)
            transcript.clear()
            if note:
                transcript.write(note)
            self.render_active_view(transcript, stage)

            evidence = self.query_one("#evidence-log", RichLog)
            evidence.clear()
            self.render_evidence(evidence)
            self.save_session(f"render:{self.view}")

        def render_active_view(self, transcript: Any, stage: dict[str, Any]) -> None:
            if self.view == "overview":
                self.render_overview(transcript, stage)
            elif self.view == "stages":
                self.render_stages(transcript)
            elif self.view == "artifacts":
                self.render_artifacts(transcript)
            elif self.view == "files":
                self.render_files(transcript)
            elif self.view == "reviews":
                self.render_reviews(transcript, stage)
            elif self.view == "help":
                self.render_help(transcript)
            elif self.view == "resume":
                self.render_resume(transcript, stage)
            else:
                self.render_overview(transcript, stage)

        def render_overview(self, transcript: Any, stage: dict[str, Any]) -> None:
            transcript.write("Available actions:")
            for action in stage.get("actions", []):
                transcript.write(f"  - {action['label']}")
            transcript.write("")
            transcript.write("Required outputs:")
            for output in stage.get("required_outputs", []):
                transcript.write(f"  - {output}")
            transcript.write("")
            transcript.write(feedback_hint())
            gate = stage.get("gate", {})
            if gate:
                transcript.write("")
                transcript.write(f"Gate: {'passing' if gate.get('passed') else 'blocked'}")
                for missing in gate.get("missing", [])[:6]:
                    transcript.write(f"  ! {missing}")
                evaluation = stage.get("evaluation", {})
                if evaluation:
                    transcript.write(f"Evaluation: {evaluation.get('decision') or evaluation.get('status')}")

        def render_stages(self, transcript: Any) -> None:
            transcript.write("Lifecycle map")
            for row in self.projection.get("lifecycle_rail", []):
                transcript.write(f"  {row['index']:02d}. {row['label']} - {row['status']}")
            stage = self.projection.get("stage", {})
            transcript.write("")
            transcript.write(f"Current stage prompt substages: {', '.join(stage.get('subprompts', [])) or 'none'}")
            transcript.write("Each stage must produce artifacts, transcript turns, evaluation, owner approval, and an explicit advance.")

        def render_artifacts(self, transcript: Any) -> None:
            artifacts = self.projection.get("artifacts", [])
            transcript.write(f"Artifacts ({len(artifacts)})")
            if not artifacts:
                transcript.write("  No artifacts yet. Create the app, prepare prompts, or submit stage proof.")
                return
            for item in artifacts[-10:]:
                transcript.write(f"  - {item['path']}")
            transcript.write("")
            latest = artifacts[-1]
            transcript.write(f"Latest artifact preview: {latest['path']}")
            transcript.write(safe_preview(self.root, latest["path"]))
            transcript.write("")
            transcript.write("Use artifact:path: feedback to ask the agent to revise an artifact.")

        def render_files(self, transcript: Any) -> None:
            files = self.projection.get("files", [])
            transcript.write(f"Generated files ({len(files)})")
            if not files:
                transcript.write("  No generated app files yet. Run Engineering with Codex after Plan is approved.")
                return
            for item in files[-12:]:
                transcript.write(f"  - {item['path']}")
            transcript.write("")
            latest = files[-1]
            transcript.write(f"Latest file preview: {latest['path']}")
            transcript.write(safe_preview(self.root, latest["path"]))
            transcript.write("")
            transcript.write("Use file:path: feedback to attach revision feedback to a source file.")

        def render_reviews(self, transcript: Any, stage: dict[str, Any]) -> None:
            queue = self.projection.get("review_queue", {}).get("items", [])
            transcript.write(f"Review queue ({len(queue)})")
            for item in queue[-12:]:
                target = f" -> {item.get('target_ref')}" if item.get("target_ref") else ""
                transcript.write(f"  - {item.get('stage')} [{item.get('kind')}] {item.get('text')}{target}")
            gate = stage.get("gate", {})
            transcript.write("")
            transcript.write(f"Current gate: {'passing' if gate.get('passed') else 'blocked'}")
            for missing in gate.get("missing", [])[:10]:
                transcript.write(f"  ! {missing}")
            transcript.write("")
            transcript.write("Owner actions: approve only after review; use feedback to request revisions.")

        def render_help(self, transcript: Any) -> None:
            transcript.write("WEAVE Textual is the local product surface. It does not need a deployed URL.")
            transcript.write("")
            transcript.write("Views: [o] overview, [t] stages, [i] artifacts, [l] files, [v] reviews, [h] help, [m] resume.")
            transcript.write("Actions: [c] create app, [s] save setup, [p] prepare prompt, [x] run Codex, [u] submit, [e] evaluate, [a] approve, [n] advance.")
            transcript.write("")
            transcript.write(feedback_hint())
            transcript.write("Hard stop boundaries: credentials, deployment, public sends, paid spend, destructive changes, raw secret handling.")
            transcript.write("Connectivity: Codex runs through the backend executor and records prompt, executor, and source manifests.")

        def render_resume(self, transcript: Any, stage: dict[str, Any]) -> None:
            session_path = weave_backend.textual_session_path(self.root, self.app_id)
            transcript.write("Resume state")
            transcript.write(f"  active_view: {self.view}")
            transcript.write(f"  current_stage: {self.projection.get('app', {}).get('current_stage', 'first_run')}")
            transcript.write(f"  stage_state: {self.projection.get('app', {}).get('stage_state', '')}")
            transcript.write(f"  session_ref: {session_path.relative_to(self.root) if session_path.is_relative_to(self.root) else 'local session file'}")
            transcript.write("")
            transcript.write("Proof boundary")
            boundary = self.projection.get("proof_boundary", {})
            transcript.write(f"  external_effects_executed: {boundary.get('external_effects_executed', [])}")
            transcript.write(f"  stop_before: {', '.join(boundary.get('stop_before', []))}")
            transcript.write(f"  secret_value_printed: {boundary.get('secret_value_printed', False)}")
            transcript.write("")
            transcript.write("Resume proves the operator can reopen the same local app state instead of relying on a one-shot script.")

        def render_evidence(self, evidence: Any) -> None:
            evidence.write("Review queue")
            for item in self.projection.get("review_queue", {}).get("items", [])[:8]:
                evidence.write(f"- {item.get('stage')}: {item.get('text')}")
            evidence.write("")
            evidence.write("Artifacts")
            for item in self.projection.get("artifacts", [])[-8:]:
                evidence.write(f"- {item['path']}")
            evidence.write("")
            evidence.write("Files")
            for item in self.projection.get("files", [])[-8:]:
                evidence.write(f"- {item['path']}")

        def current_stage(self) -> str:
            return self.projection.get("app", {}).get("current_stage") or "intent"

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
            self.projection = result.get("projection") or weave_backend.dashboard_projection(self.root, app_id=self.app_id, app_name=self.app_name)
            return result

        def action_refresh_projection(self) -> None:
            self.projection = weave_backend.dashboard_projection(self.root, app_id=self.app_id, app_name=self.app_name)
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

        def action_create_app(self) -> None:
            result = weave_backend.dispatch(self.root, "workspace.create_app", app_id=self.app_id, app_name=self.app_name)
            self.projection = result.get("projection") or weave_backend.dashboard_projection(self.root, app_id=self.app_id, app_name=self.app_name)
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
            self.render_projection(result.get("message", "Setup saved."))

        def action_prepare_prompt(self) -> None:
            stage = self.current_stage()
            result = self.run_backend_command(
                "prompt.prepare",
                {"stage": stage, "substage": "start", "owner_message": self.composer_text()},
            )
            self.render_projection(result.get("message", "Prompt prepared."))

        def action_submit_stage(self) -> None:
            stage = self.current_stage()
            owner_text = self.composer_text() or getattr(self.args, "intent", "")
            result = self.run_backend_command(
                "stage.submit",
                {
                    "stage": stage,
                    "owner_text": owner_text,
                    "agent_text": f"{stage.title()} proof is ready for evaluation and owner review.",
                    "artifact_body": owner_text,
                },
            )
            self.render_projection(result.get("message", "Stage submitted."))

        def action_run_executor(self) -> None:
            result = self.run_backend_command(
                "executor.run",
                {
                    "executor": "codex",
                    "owner_message": self.composer_text() or getattr(self.args, "intent", ""),
                    "timeout_seconds": getattr(self.args, "codex_timeout", 600),
                },
            )
            self.render_projection(result.get("message", "Executor command completed."))

        def action_evaluate_stage(self) -> None:
            stage = self.current_stage()
            run_hard_gates = bool(getattr(self.args, "run_engineering_gates", False)) and stage in {"engineering", "qa"}
            result = self.run_backend_command("stage.evaluate", {"stage": stage, "run_gates": run_hard_gates})
            self.render_projection(result.get("message", "Evaluation completed."))

        def action_approve_stage(self) -> None:
            result = self.run_backend_command("stage.approve", {"stage": self.current_stage(), "note": "Approved in Textual cockpit."})
            self.render_projection(result.get("message", "Approval command completed."))

        def action_advance_stage(self) -> None:
            result = self.run_backend_command("stage.advance", {"note": "Advanced in Textual cockpit."})
            self.render_projection(result.get("message", "Advance command completed."))

        def action_focus_composer(self) -> None:
            self.query_one("#composer", Input).focus()

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
                composer = self.query_one("#composer", Input)
                result = self.run_backend_command("feedback.record", parse_feedback_target(composer.value, default_stage=self.current_stage()))
                self.render_projection(result.get("message", "Feedback recorded."))
            elif event.button.id == "refresh":
                self.action_refresh_projection()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            text = event.value.strip()
            if not text:
                return
            result = self.run_backend_command("feedback.record", parse_feedback_target(text, default_stage=self.current_stage()))
            event.input.value = ""
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
