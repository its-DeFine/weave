#!/usr/bin/env python3
"""Backend facade for the WEAVE v1 Textual cockpit.

The facade gives the TUI one stable surface for projections and commands while
delegating durable state to the existing runtime slice. It is intentionally
local-only and standard-library based.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import weave_prompt_library
import weave_runtime_slice


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PROJECTION_SCHEMA = "weave/backend-projection/v1"
BACKEND_COMMAND_RESULT_SCHEMA = "weave/backend-command-result/v1"
REVIEW_QUEUE_SCHEMA = "weave/review-queue/v1"
WORLD_MODEL_SCHEMA = "weave/world-model-local/v1"
TEXTUAL_SESSION_SCHEMA = "weave/textual-session/v1"
EXECUTOR_MANIFEST_SCHEMA = "weave/executor-manifest/v1"
SOURCE_MANIFEST_SCHEMA = "weave/source-manifest/v1"

SETUP_STAGES = ["first_run", "owner_profile", "app"]
PRODUCT_STAGES = [
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
]
ALL_STAGES = [*SETUP_STAGES, *PRODUCT_STAGES, "completion"]


class BackendError(Exception):
    """Raised when a backend command cannot be completed safely."""


@dataclass(frozen=True)
class BackendCommandResult:
    ok: bool
    message: str
    failure_class: str = ""
    events_written: tuple[str, ...] = ()
    artifacts_written: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    safe_next_actions: tuple[str, ...] = ()
    projection: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": BACKEND_COMMAND_RESULT_SCHEMA,
            "ok": self.ok,
            "message": self.message,
            "failure_class": self.failure_class,
            "events_written": list(self.events_written),
            "artifacts_written": list(self.artifacts_written),
            "blocked_by": list(self.blocked_by),
            "safe_next_actions": list(self.safe_next_actions),
            "projection": self.projection or {},
        }


def normalize_stage(stage: str | None) -> str:
    return weave_prompt_library.normalize_stage(stage)


def stage_label(stage: str) -> str:
    labels = {
        "first_run": "First Run",
        "owner_profile": "Owner Profile",
        "app": "App Workspace",
        "intent": "Intent",
        "research": "Research",
        "selection": "Selection",
        "plan": "Plan",
        "engineering": "Engineering",
        "qa": "QA",
        "deployment": "Deployment",
        "kpi": "KPI",
        "marketing": "Marketing",
        "iteration": "Iteration",
        "analysis": "Analysis",
        "completion": "Completion",
    }
    return labels.get(stage, stage.replace("_", " ").title())


def root_ready(root: Path) -> bool:
    try:
        return weave_runtime_slice.root_ready(root)
    except Exception:
        return False


def safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return weave_runtime_slice.load_json(path)


def textual_session_path(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "ui" / "textual-session.json"


def review_queue_path(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / "review-queue.json"


def world_model_path(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "worldmodel.json"


def world_model_markdown_path(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "worldmodel.md"


def stage_artifact_dir(root: Path, app_id: str, stage: str) -> Path:
    stage_def = weave_runtime_slice.stage_by_id(normalize_stage(stage))
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / stage_def.directory / "artifacts"


def primary_repo_dir(root: Path, app_id: str) -> Path:
    return weave_runtime_slice.app_root(root, app_id) / "repo" / "primary"


def default_world_model(app_id: str, app_name: str) -> dict[str, Any]:
    return {
        "schema": WORLD_MODEL_SCHEMA,
        "app_id": weave_runtime_slice.slugify(app_id),
        "app_name": app_name,
        "updated_at": weave_runtime_slice.utc_now(),
        "summary": "New WEAVE app. Intent is not approved yet.",
        "current_truth": ["No live deployment", "No public sends", "No paid spend"],
        "open_questions": ["Owner intent must be captured and validated."],
        "source_artifact_refs": [],
        "public_safe": True,
    }


def ensure_world_model(root: Path, app_id: str) -> dict[str, Any]:
    app = weave_runtime_slice.load_app(root, app_id)
    path = world_model_path(root, app_id)
    if path.exists():
        return weave_runtime_slice.load_json(path)
    model = default_world_model(app["app_id"], app["name"])
    path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    world_model_markdown_path(root, app_id).write_text(
        f"# {app['name']} World Model\n\n{model['summary']}\n\n## Current Truth\n\n"
        + "\n".join(f"- {item}" for item in model["current_truth"])
        + "\n",
        encoding="utf-8",
    )
    return model


def ensure_review_queue(root: Path, app_id: str) -> dict[str, Any]:
    path = review_queue_path(root, app_id)
    if path.exists():
        return weave_runtime_slice.load_json(path)
    queue = {
        "schema": REVIEW_QUEUE_SCHEMA,
        "app_id": weave_runtime_slice.slugify(app_id),
        "updated_at": weave_runtime_slice.utc_now(),
        "items": [],
        "public_safe": True,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return queue


def add_review_item(
    root: Path,
    app_id: str,
    *,
    stage: str,
    kind: str,
    text: str,
    target_ref: str = "",
    severity: str = "action_required",
) -> dict[str, Any]:
    queue = ensure_review_queue(root, app_id)
    item = {
        "id": f"review-{len(queue['items']) + 1:04d}",
        "stage": normalize_stage(stage),
        "kind": kind,
        "text": text,
        "target_ref": target_ref,
        "severity": severity,
        "created_at": weave_runtime_slice.utc_now(),
        "status": "open",
    }
    queue["items"].append(item)
    queue["updated_at"] = weave_runtime_slice.utc_now()
    review_queue_path(root, app_id).write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return item


def create_or_load_app(root: Path, app_id: str, app_name: str) -> dict[str, Any]:
    clean_id = weave_runtime_slice.slugify(app_id)
    try:
        app = weave_runtime_slice.load_app(root, clean_id)
    except weave_runtime_slice.RuntimeSliceError:
        created = weave_runtime_slice.create_app(root, clean_id, app_name)
        app = created["app"]
        ensure_world_model(root, clean_id)
        ensure_review_queue(root, clean_id)
        add_review_item(
            root,
            clean_id,
            stage="intent",
            kind="stage_input_needed",
            text="Capture and validate the app intent before research.",
        )
    return app


def record_foundation_context(
    root: Path,
    app_id: str,
    *,
    owner_experience: str = "",
    coworker_style: str = "",
    app_intent: str = "",
    target_user: str = "",
) -> dict[str, Any]:
    """Write the owner/app context surfaces required by the foundation gate.

    The Textual cockpit owns first-run collection, but the existing runtime owns
    the gate. This helper bridges them by writing only public-safe context
    artifacts, never credentials or live provider state.
    """

    app = weave_runtime_slice.load_app(root, app_id)
    clean_id = app["app_id"]
    owner_experience = owner_experience.strip() or "Owner experience was not specified yet."
    coworker_style = coworker_style.strip() or "Owner wants direct, proof-backed collaboration."
    app_intent = app_intent.strip() or "Intent is still being shaped through the WEAVE lifecycle."
    target_user = target_user.strip() or "Target user is still being clarified."
    payload = {
        "owner_experience": owner_experience,
        "coworker_style": coworker_style,
        "app_intent": app_intent,
        "target_user": target_user,
    }
    weave_prompt_library.ensure_public_safe("foundation context", payload)

    general = root / "artifacts" / "general"
    general.mkdir(parents=True, exist_ok=True)
    (general / "soul.md").write_text(
        "\n".join(
            [
                "# WEAVE Working Soul",
                "",
                "WEAVE acts as a lifecycle operator: it asks for missing context, creates proof artifacts, records owner-visible rationale, and stops before credentials, deployment, public sends, or paid spend.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (general / "owner-profile.md").write_text(
        "\n".join(
            [
                "# Owner Profile",
                "",
                f"Experience: {owner_experience}",
                "",
                f"Preferred coworker style: {coworker_style}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    base = weave_runtime_slice.app_root(root, clean_id)
    (base / "context" / "app-context.md").write_text(
        "\n".join(
            [
                f"# {app['name']} Context",
                "",
                f"Intent: {app_intent}",
                "",
                f"Target user: {target_user}",
                "",
                "Boundary: local proof only until the owner explicitly approves credentials, deployment, public sends, or paid spend.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (base / "inventory" / "app-inventory.md").write_text(
        "\n".join(
            [
                f"# {app['name']} Inventory",
                "",
                "- Workspace: local WEAVE app tree.",
                "- Primary repo: repo/primary.",
                "- Lifecycle artifacts: lifecycle/<stage>/artifacts.",
                "- Live providers: not connected.",
                "- Public effects: none authorized.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (base / "contract" / "gestaltian-contract.md").write_text(
        "\n".join(
            [
                f"# {app['name']} Contract",
                "",
                "The app may advance only through stage artifacts, transcript capture, evaluation, owner approval, and explicit advance.",
                "",
                "Hard stop boundaries: raw secrets, external account mutation, deployment, public sends, paid spend, and destructive operations.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    model = ensure_world_model(root, clean_id)
    model["summary"] = app_intent
    model["current_truth"] = [
        f"Target user: {target_user}",
        "No live deployment",
        "No public sends",
        "No paid spend",
        "No raw credentials captured",
    ]
    model["open_questions"] = ["Intent must still pass the formal intent gate."]
    model["updated_at"] = weave_runtime_slice.utc_now()
    world_model_path(root, clean_id).write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    world_model_markdown_path(root, clean_id).write_text(
        f"# {app['name']} World Model\n\n{model['summary']}\n\n## Current Truth\n\n"
        + "\n".join(f"- {item}" for item in model["current_truth"])
        + "\n",
        encoding="utf-8",
    )

    event = weave_runtime_slice.append_event(
        root,
        clean_id,
        weave_runtime_slice.new_event(
            "foundation.completed",
            clean_id,
            normalize_stage(app.get("current_stage") or "intent"),
            "Textual cockpit recorded owner/app foundation context.",
            created_by="weave-runtime",
            payload={"foundation_gate": weave_runtime_slice.foundation_gate(root, clean_id)},
        ),
    )
    return {"app": weave_runtime_slice.load_app(root, clean_id), "event": event, "foundation_gate": weave_runtime_slice.foundation_gate(root, clean_id)}


def write_stage_artifact(
    root: Path,
    app_id: str,
    *,
    stage: str,
    title: str,
    body: str,
    artifact_name: str = "",
) -> dict[str, str]:
    clean_stage = normalize_stage(stage)
    directory = stage_artifact_dir(root, app_id, clean_stage)
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = weave_runtime_slice.slugify(artifact_name or f"{clean_stage}-proof")
    path = directory / f"{safe_name}.md"
    content = "\n".join(
        [
            f"# {title.strip() or stage_label(clean_stage) + ' Proof'}",
            "",
            body.strip() or "No owner text was provided; this artifact should be revised before approval.",
            "",
            "## Boundary",
            "",
            "No credentials, deployment, public sends, paid spend, or destructive operations were executed by this artifact.",
            "",
        ]
    )
    weave_prompt_library.ensure_public_safe("stage artifact", content)
    path.write_text(content, encoding="utf-8")
    return {
        "stage": clean_stage,
        "kind": "artifact",
        "path": weave_runtime_slice.relative(path, root),
        "checksum": weave_runtime_slice.artifact_checksum(path),
    }


def record_stage_turn(
    root: Path,
    app_id: str,
    *,
    stage: str,
    artifact: dict[str, str],
    owner_text: str,
    agent_text: str,
    ready_for_review: bool = True,
) -> dict[str, Any]:
    clean_stage = normalize_stage(stage)
    gate_before = weave_runtime_slice.stage_gate_status(root, app_id, clean_stage, include_evaluation=False)
    turn = weave_runtime_slice.new_conversation_turn(
        app_id,
        clean_stage,
        {"role": "owner", "source": "textual", "text": owner_text.strip() or f"Review {stage_label(clean_stage)}."},
        {"role": "hermes", "source": "textual", "text": agent_text.strip() or f"{stage_label(clean_stage)} proof is ready for owner review."},
        channel="textual",
        created_by="execution-agent",
        agent_rationale={
            "summary": f"The {stage_label(clean_stage)} stage now has a proof artifact linked to the owner review turn.",
            "gate_questions": [f"Does the {stage_label(clean_stage)} artifact satisfy the current stage contract?"],
            "missing_information": gate_before.get("missing", []),
            "decision_basis": ["stage artifact exists", "owner-visible review turn was recorded"],
            "chain_of_thought_captured": False,
        },
        gate_checks={
            "foundation_gate_passed": gate_before.get("foundation_gate", {}).get("passed", False),
            "stage_gate_passed_before_append": gate_before.get("passed", False),
            "stage_gate_missing_before_append": gate_before.get("missing", []),
        },
        artifact_refs=[{"path": artifact["path"], "action": "created", "kind": "stage-proof"}],
        state_transition={"from_state": "collecting", "to_state": "ready_for_review"} if ready_for_review else {},
        next_action="Run or complete evaluation, then approve this stage if the proof is acceptable.",
    )
    return weave_runtime_slice.append_conversation_turn(root, app_id, turn)


def submit_stage_proof(
    root: Path,
    app_id: str,
    *,
    stage: str,
    owner_text: str,
    agent_text: str,
    artifact_title: str = "",
    artifact_body: str = "",
    artifact_name: str = "",
) -> dict[str, Any]:
    clean_stage = normalize_stage(stage)
    body = artifact_body.strip() or "\n\n".join(
        part
        for part in (
            f"Owner input:\n{owner_text.strip()}",
            f"Agent response:\n{agent_text.strip()}",
        )
        if part.strip()
    )
    artifact = write_stage_artifact(
        root,
        app_id,
        stage=clean_stage,
        title=artifact_title or f"{stage_label(clean_stage)} Proof",
        body=body,
        artifact_name=artifact_name or f"{clean_stage}-proof",
    )
    turn = record_stage_turn(root, app_id, stage=clean_stage, artifact=artifact, owner_text=owner_text, agent_text=agent_text)
    add_review_item(
        root,
        app_id,
        stage=clean_stage,
        kind="stage_ready_for_review",
        text=f"{stage_label(clean_stage)} proof is ready for evaluation and owner approval.",
        target_ref=artifact["path"],
    )
    return {"artifact": artifact, "turn": turn, "stage_gate": weave_runtime_slice.stage_gate_status(root, app_id, clean_stage)}


def complete_stage_evaluation(root: Path, app_id: str, *, stage: str, run_gates: bool = False) -> dict[str, Any]:
    result = weave_runtime_slice.complete_evaluation_from_latest_artifact(
        root,
        app_id,
        normalize_stage(stage),
        reviewer="textual-local-evaluator",
        run_gates=run_gates,
    )
    return result


def codex_subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    # Disable local Codex session wrappers for child execution. WEAVE records
    # its own prompt packet, source manifest, and executor manifest.
    env["CODEX_SWARM_DISABLE"] = "1"
    env["CODEX_SESSIONS_DISABLE"] = "1"
    env["CODEX_PREFLIGHT_DISABLE"] = "1"
    return env


def source_manifest(root: Path, app_id: str, *, executor: str, status: str) -> dict[str, Any]:
    repo = primary_repo_dir(root, app_id)
    files: list[dict[str, Any]] = []
    if repo.exists():
        for path in sorted(repo.rglob("*")):
            if not path.is_file():
                continue
            files.append(
                {
                    "path": weave_runtime_slice.relative(path, root),
                    "bytes": path.stat().st_size,
                    "checksum": weave_runtime_slice.artifact_checksum(path),
                }
            )
    manifest = {
        "schema": SOURCE_MANIFEST_SCHEMA,
        "app_id": weave_runtime_slice.slugify(app_id),
        "updated_at": weave_runtime_slice.utc_now(),
        "executor": executor,
        "status": status,
        "file_count": len(files),
        "files": files,
        "public_safe": True,
        "secret_value_printed": False,
    }
    weave_prompt_library.ensure_public_safe("source manifest", manifest)
    path = stage_artifact_dir(root, app_id, "engineering") / "source-manifest.json"
    weave_runtime_slice.write_json_artifact(path, manifest)
    manifest["manifest_ref"] = weave_runtime_slice.relative(path, root)
    return manifest


def executor_manifest(root: Path, app_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "schema": EXECUTOR_MANIFEST_SCHEMA,
        "app_id": weave_runtime_slice.slugify(app_id),
        "updated_at": weave_runtime_slice.utc_now(),
        "public_safe": True,
        "secret_value_printed": False,
        **payload,
    }
    weave_prompt_library.ensure_public_safe("executor manifest", manifest)
    path = stage_artifact_dir(root, app_id, "engineering") / "executor-manifest.json"
    weave_runtime_slice.write_json_artifact(path, manifest)
    manifest["manifest_ref"] = weave_runtime_slice.relative(path, root)
    return manifest


def codex_engineering_execution_prompt(app: dict[str, Any], packet: dict[str, Any], owner_message: str) -> str:
    prompt = f"""You are executing the WEAVE Engineering stage in the current working directory.

Build a local-only static app for:
- App name: {app['name']}
- App id: {app['app_id']}
- Owner intent: {owner_message}

Create these files:
- index.html
- src/app.js
- src/styles.css
- public/config.json
- README.md

Hard boundaries:
- Do not deploy.
- Do not use or request credentials.
- Do not send public messages.
- Do not spend money.
- Do not call external APIs.
- Do not add analytics beacons.
- Do not include private hostnames, loopback addresses, private IPs, absolute local paths, or file URLs.

Product requirements:
- The app should be a launch readiness cockpit for a founder.
- Show lifecycle status, launch risks, QA state, SEO readiness, and launch boundaries.
- Make the UI useful without any backend.
- Use semantic HTML with main and h1.
- Include a title, meta description, Open Graph title/description, viewport, stylesheet link, and script tag.
- Use client-side JavaScript with addEventListener, textContent, localStorage, and JSON.stringify.
- Avoid innerHTML, fetch, XMLHttpRequest, redirects, and external HTTP calls.
- public/config.json must mark analytics, deployment, paid_spend, public_send, and credentials as disabled.
- README.md must explain local run steps and the hard boundaries.

WEAVE prompt packet evidence:
- packet_id: {packet['packet_id']}
- packet_ref: {packet.get('packet_ref', '')}
- rendered_prompt_ref: {packet.get('rendered_prompt_ref', '')}

Return only a concise completion note after writing the files.
"""
    weave_prompt_library.ensure_public_safe("codex engineering execution prompt", prompt)
    return prompt


def run_codex_engineering(root: Path, app_id: str, *, owner_message: str = "", timeout_seconds: int = 600) -> dict[str, Any]:
    app = weave_runtime_slice.load_app(root, app_id)
    repo = primary_repo_dir(root, app_id)
    repo.mkdir(parents=True, exist_ok=True)
    packet = create_prompt_for_stage(
        root,
        app_id,
        stage="engineering",
        substage="build",
        owner_message=owner_message or f"Build the approved {app['name']} app from the lifecycle artifacts.",
    )
    rendered_prompt = codex_engineering_execution_prompt(app, packet, owner_message or f"Build the approved {app['name']} app.")
    binary_found = bool(shutil.which("codex"))
    command_label = "codex exec --sandbox workspace-write -C app repo -"
    if not binary_found:
        source = source_manifest(root, app_id, executor="codex", status="not_run")
        manifest = executor_manifest(
            root,
            app_id,
            {
                "executor": "codex",
                "status": "failed",
                "failure_class": "codex_cli_missing",
                "live_agent_execution": False,
                "binary_found": False,
                "command_label": command_label,
                "prompt_packet_ref": packet.get("packet_ref", ""),
                "rendered_prompt_ref": packet.get("rendered_prompt_ref", ""),
                "source_manifest_ref": source["manifest_ref"],
                "claims": [],
                "non_claims": ["Codex CLI did not run", "no deployment", "no live user proof"],
            },
        )
        add_review_item(
            root,
            app_id,
            stage="engineering",
            kind="executor_blocked",
            text="Codex CLI is unavailable; install/auth Codex or choose a different executor before engineering can proceed.",
            target_ref=manifest["manifest_ref"],
        )
        return {"ok": False, "executor_manifest": manifest, "source_manifest": source, "packet": packet}

    command = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "--color",
        "never",
        "-C",
        str(repo),
        "-",
    ]
    timed_out = False
    exit_code: int | None
    stdout_lines = 0
    stderr_lines = 0
    try:
        completed = subprocess.run(
            command,
            input=rendered_prompt,
            cwd=REPO_ROOT,
            env=codex_subprocess_env(),
            text=True,
            capture_output=True,
            check=False,
            timeout=max(1, int(timeout_seconds)),
        )
        exit_code = completed.returncode
        stdout_lines = len((completed.stdout or "").splitlines())
        stderr_lines = len((completed.stderr or "").splitlines())
    except subprocess.TimeoutExpired:
        timed_out = True
        exit_code = None
    except OSError:
        exit_code = None

    status = "passed" if exit_code == 0 and not timed_out else "failed"
    source = source_manifest(root, app_id, executor="codex", status=status)
    if status == "passed" and source["file_count"] == 0:
        status = "failed"
        failure_class = "no_source_files_written"
        source = source_manifest(root, app_id, executor="codex", status=status)
    elif timed_out:
        failure_class = "timeout"
    elif exit_code == 0:
        failure_class = ""
    else:
        failure_class = "agent_execution"
    manifest = executor_manifest(
        root,
        app_id,
        {
            "executor": "codex",
            "status": status,
            "failure_class": failure_class,
            "live_agent_execution": status == "passed",
            "binary_found": True,
            "command_label": command_label,
            "exit_code": exit_code,
            "prompt_packet_ref": packet.get("packet_ref", ""),
            "rendered_prompt_ref": packet.get("rendered_prompt_ref", ""),
            "source_manifest_ref": source["manifest_ref"],
            "output_summary": {
                "stdout_line_count": stdout_lines,
                "stderr_line_count": stderr_lines,
                "raw_output_persisted": False,
            },
            "claims": ["Codex CLI ran and wrote local app files"] if status == "passed" else [],
            "non_claims": ["not deployed", "not live user proof", "no provider credentials were captured by WEAVE"],
        },
    )
    if status == "passed":
        turn = record_stage_turn(
            root,
            app_id,
            stage="engineering",
            artifact={
                "stage": "engineering",
                "kind": "artifact",
                "path": manifest["manifest_ref"],
                "checksum": weave_runtime_slice.artifact_checksum(root / manifest["manifest_ref"]),
            },
            owner_text=owner_message or f"Build the approved {app['name']} app.",
            agent_text="Codex completed local engineering execution and wrote a source manifest for review.",
            ready_for_review=True,
        )
    else:
        turn = weave_runtime_slice.append_conversation_turn(
            root,
            app_id,
            weave_runtime_slice.new_conversation_turn(
                app_id,
                "engineering",
                {"role": "owner", "source": "textual", "text": owner_message or f"Build the approved {app['name']} app."},
                {"role": "hermes", "source": "textual", "text": f"Codex engineering execution did not pass: {failure_class or 'unknown failure'}."},
                channel="textual",
                created_by="execution-agent",
                agent_rationale={
                    "summary": "Engineering remains blocked because the executor did not produce accepted local source proof.",
                    "gate_questions": ["Should the owner retry Codex, change executor, or revise the engineering packet?"],
                    "missing_information": [failure_class or "executor_failed"],
                    "decision_basis": ["executor manifest status is failed"],
                    "chain_of_thought_captured": False,
                },
                artifact_refs=[{"path": manifest["manifest_ref"], "action": "created", "kind": "executor-manifest"}],
                next_action="Fix executor blocker, then rerun engineering.",
            ),
        )
        add_review_item(
            root,
            app_id,
            stage="engineering",
            kind="executor_failed",
            text=f"Codex engineering execution failed: {failure_class or 'executor_failed'}.",
            target_ref=manifest["manifest_ref"],
        )
    return {"ok": status == "passed", "executor_manifest": manifest, "source_manifest": source, "packet": packet, "turn": turn}


def lifecycle_rail(root: Path, app_id: str | None = None) -> list[dict[str, Any]]:
    current = "first_run"
    approved: set[str] = set()
    if app_id:
        try:
            app = weave_runtime_slice.load_app(root, app_id)
        except weave_runtime_slice.RuntimeSliceError:
            app = {}
        current = normalize_stage(str(app.get("current_stage") or "intent")) if app else "first_run"
        approved = set(str(item) for item in app.get("approved_stages", [])) if app else set()
    rows = []
    for index, stage in enumerate(ALL_STAGES, 1):
        status = "not_started"
        if stage in approved:
            status = "approved"
        if stage == current:
            status = "active"
        if stage in SETUP_STAGES and root_ready(root):
            status = "ready" if status == "not_started" else status
        rows.append({"index": index, "stage": stage, "label": stage_label(stage), "status": status})
    return rows


def artifact_refs(root: Path, app_id: str) -> list[dict[str, Any]]:
    base = weave_runtime_slice.app_root(root, app_id)
    refs: list[dict[str, Any]] = []
    for path in sorted((base / "lifecycle").glob("*/artifacts/**/*")):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt"}:
            refs.append({"path": weave_runtime_slice.relative(path, root), "name": path.name, "kind": "artifact"})
    return refs


def source_file_refs(root: Path, app_id: str) -> list[dict[str, Any]]:
    base = weave_runtime_slice.app_root(root, app_id) / "repo" / "primary"
    refs: list[dict[str, Any]] = []
    if not base.exists():
        return refs
    for path in sorted(base.rglob("*")):
        if path.is_file():
            refs.append({"path": weave_runtime_slice.relative(path, root), "name": path.name, "kind": "file"})
    return refs


def stage_actions(stage: str, app_exists: bool) -> list[dict[str, str]]:
    if not app_exists:
        return [
            {"id": "create_app", "label": "Create local app"},
            {"id": "attach_existing", "label": "Attach existing"},
            {"id": "connect_remote", "label": "Connect remote"},
            {"id": "local_only", "label": "Keep local only"},
        ]
    action_map = {
        "intent": ["Save intent", "Ask missing", "Validate", "Approve"],
        "research": ["Draft plan", "Run research", "Review artifacts", "Approve"],
        "selection": ["Generate options", "Select option", "Discuss/edit", "Approve"],
        "plan": ["Draft plan", "Edit business", "Edit engineering", "Approve"],
        "engineering": ["Run Codex", "Inspect files", "File feedback", "Pause"],
        "qa": ["Authorize QA", "Run QA", "Rerun QA", "Accept QA"],
        "deployment": ["Record provider", "Mark blocked", "Inspect plan", "Defer"],
        "kpi": ["Accept KPIs", "Edit KPI", "Add KPI", "Defer"],
        "marketing": ["Organic only", "Record budget", "Create jobs", "Hold sends"],
        "iteration": ["Approve issue", "Reject issue", "Route to engineering", "Inspect"],
        "analysis": ["Accept cadence", "Edit sources", "Run local", "Hold heartbeat"],
        "completion": ["Audit proof", "List gaps", "Accept", "Keep open"],
    }
    return [{"id": item.lower().replace(" ", "_"), "label": item} for item in action_map.get(stage, ["Approve", "Revise", "Inspect", "Feedback"])]


def stage_projection(root: Path, app_id: str | None, stage: str | None = None) -> dict[str, Any]:
    app_exists = False
    app: dict[str, Any] = {}
    if app_id:
        try:
            app = weave_runtime_slice.load_app(root, app_id)
            app_exists = True
        except weave_runtime_slice.RuntimeSliceError:
            app_exists = False
    clean_stage = normalize_stage(stage or (app.get("current_stage") if app else "first_run"))
    try:
        stage_def = weave_prompt_library.stage_definition(clean_stage)
        worker_role = stage_def["worker_role"]
        goal = stage_def["owner_visible_goal"]
        subprompts = sorted(stage_def["subprompts"])
        required_outputs = stage_def["required_outputs"]
    except weave_prompt_library.PromptLibraryError:
        worker_role = "WEAVE guide"
        goal = "Prepare the workspace."
        subprompts = ["start"]
        required_outputs = []
    gate: dict[str, Any] = {}
    evaluation: dict[str, Any] = {}
    if app_exists and app_id:
        try:
            gate = weave_runtime_slice.stage_gate_status(root, app_id, clean_stage)
            evaluation = gate.get("evaluation") if isinstance(gate.get("evaluation"), dict) else {}
        except weave_runtime_slice.RuntimeSliceError:
            gate = {}
            evaluation = {}
    return {
        "stage": clean_stage,
        "label": stage_label(clean_stage),
        "worker_role": worker_role,
        "owner_visible_goal": goal,
        "subprompts": subprompts,
        "required_outputs": required_outputs,
        "actions": stage_actions(clean_stage, app_exists),
        "app_exists": app_exists,
        "gate": gate,
        "evaluation": evaluation,
    }


def app_projection(root: Path, app_id: str, *, stage: str | None = None) -> dict[str, Any]:
    app = weave_runtime_slice.load_app(root, app_id)
    world_model = ensure_world_model(root, app_id)
    review_queue = ensure_review_queue(root, app_id)
    current_stage = normalize_stage(stage or str(app.get("current_stage") or "intent"))
    return {
        "schema": BACKEND_PROJECTION_SCHEMA,
        "generated_at": weave_runtime_slice.utc_now(),
        "app": {
            "app_id": app["app_id"],
            "name": app["name"],
            "current_stage": current_stage,
            "stage_state": app.get("stage_state", "active"),
            "control_mode": app.get("control_mode", "handoff"),
        },
        "lifecycle_rail": lifecycle_rail(root, app_id),
        "stage": stage_projection(root, app_id, current_stage),
        "world_model": world_model,
        "review_queue": review_queue,
        "artifacts": artifact_refs(root, app_id),
        "files": source_file_refs(root, app_id),
        "proof_boundary": {
            "external_effects_executed": [],
            "stop_before": ["credentials", "deployment", "public_sends", "paid_spend", "destructive_changes"],
            "secret_value_printed": False,
        },
    }


def dashboard_projection(root: Path, *, app_id: str = "", app_name: str = "New App") -> dict[str, Any]:
    ready = root_ready(root)
    app: dict[str, Any] | None = None
    if app_id:
        try:
            app = weave_runtime_slice.load_app(root, app_id)
        except weave_runtime_slice.RuntimeSliceError:
            app = None
    apps = []
    if ready:
        try:
            registry = weave_runtime_slice.load_registry(root)
            apps = registry.get("apps", [])
        except weave_runtime_slice.RuntimeSliceError:
            apps = []
    if app:
        return app_projection(root, app["app_id"])
    return {
        "schema": BACKEND_PROJECTION_SCHEMA,
        "generated_at": weave_runtime_slice.utc_now(),
        "app": {"app_id": weave_runtime_slice.slugify(app_id or app_name), "name": app_name, "current_stage": "first_run", "stage_state": "needs_setup"},
        "lifecycle_rail": lifecycle_rail(root, None),
        "stage": stage_projection(root, None, "first_run"),
        "world_model": {},
        "review_queue": {
            "schema": REVIEW_QUEUE_SCHEMA,
            "items": [
                {
                    "id": "setup",
                    "stage": "first_run",
                    "kind": "needs_owner_choice",
                    "text": "Choose local app creation, attach existing, connect remote, or local-only.",
                    "status": "open",
                }
            ],
        },
        "artifacts": [],
        "files": [],
        "apps": apps,
        "proof_boundary": {
            "external_effects_executed": [],
            "stop_before": ["credentials", "deployment", "public_sends", "paid_spend", "destructive_changes"],
            "secret_value_printed": False,
        },
    }


def create_prompt_for_stage(
    root: Path,
    app_id: str,
    *,
    stage: str,
    substage: str,
    owner_message: str = "",
    feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    app = weave_runtime_slice.load_app(root, app_id)
    world_model = ensure_world_model(root, app_id)
    context_refs = [app.get("ledger_path", "ledger/events.jsonl")]
    if world_model_markdown_path(root, app_id).exists():
        context_refs.append(weave_runtime_slice.relative(world_model_markdown_path(root, app_id), root))
    packet = weave_prompt_library.build_prompt_packet(
        root=root,
        app_id=app_id,
        stage=stage,
        substage=substage,
        latest_owner_message=owner_message,
        input_refs=[ref["path"] for ref in artifact_refs(root, app_id)[-8:]],
        selected_context_refs=context_refs,
        owner_profile_summary="Use the owner profile artifact when present; otherwise ask concise clarifying questions.",
        world_model_summary=str(world_model.get("summary") or ""),
        feedback=feedback,
        reason=f"Textual backend requested {stage}/{substage} prompt packet",
    )
    add_review_item(
        root,
        app_id,
        stage=stage,
        kind="prompt_packet_ready",
        text=f"Prompt packet ready for {stage}/{substage}.",
        target_ref=packet.get("packet_ref", ""),
        severity="info",
    )
    return packet


def default_feedback_substage(stage: str, *, target_type: str = "stage") -> str:
    """Choose a valid prompt-library substage for owner feedback.

    Lifecycle stages do not all name revision work the same way. Engineering,
    for example, has a dedicated `file_feedback` prompt because the owner can
    point at generated source files. This helper prevents feedback capture from
    writing a review item while failing to create the prompt packet that should
    drive the next agent action.
    """

    clean_stage = normalize_stage(stage)
    try:
        stage_def = weave_prompt_library.stage_definition(clean_stage)
        subprompts = set(stage_def.get("subprompts", {}))
    except weave_prompt_library.PromptLibraryError:
        return "revise"
    if target_type == "file" and "file_feedback" in subprompts:
        return "file_feedback"
    if target_type == "artifact" and "artifact_feedback" in subprompts:
        return "artifact_feedback"
    if "revise" in subprompts:
        return "revise"
    if "status" in subprompts:
        return "status"
    if "start" in subprompts:
        return "start"
    return sorted(subprompts)[0] if subprompts else "revise"


def dispatch(root: Path, command: str, *, app_id: str = "", app_name: str = "New App", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    try:
        if command == "workspace.create_app":
            app = create_or_load_app(root, app_id or app_name, app_name)
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(True, f"Created or loaded app {app['app_id']}.", projection=projection).to_dict()
        if command == "foundation.save":
            app = create_or_load_app(root, app_id or app_name, app_name)
            foundation = record_foundation_context(
                root,
                app["app_id"],
                owner_experience=str(payload.get("owner_experience") or ""),
                coworker_style=str(payload.get("coworker_style") or ""),
                app_intent=str(payload.get("app_intent") or payload.get("intent") or ""),
                target_user=str(payload.get("target_user") or ""),
            )
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(
                bool(foundation["foundation_gate"]["passed"]),
                "Saved owner/app foundation context.",
                events_written=(foundation["event"]["event_id"],),
                projection=projection,
            ).to_dict()
        if command == "prompt.prepare":
            app = create_or_load_app(root, app_id or app_name, app_name)
            packet = create_prompt_for_stage(
                root,
                app["app_id"],
                stage=str(payload.get("stage") or app.get("current_stage") or "intent"),
                substage=str(payload.get("substage") or "start"),
                owner_message=str(payload.get("owner_message") or ""),
                feedback=payload.get("feedback") if isinstance(payload.get("feedback"), dict) else None,
            )
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(
                True,
                f"Prepared prompt packet {packet['packet_id']}.",
                artifacts_written=(packet.get("packet_ref", ""), packet.get("rendered_prompt_ref", "")),
                projection=projection,
            ).to_dict()
        if command == "feedback.record":
            app = create_or_load_app(root, app_id or app_name, app_name)
            feedback = weave_prompt_library.build_feedback(
                app_id=app["app_id"],
                stage=str(payload.get("stage") or app.get("current_stage") or "intent"),
                owner_text=str(payload.get("owner_text") or ""),
                target_type=str(payload.get("target_type") or "stage"),
                target_ref=str(payload.get("target_ref") or ""),
                feedback_class=str(payload.get("feedback_class") or "preference"),
            )
            add_review_item(
                root,
                app["app_id"],
                stage=feedback["stage"],
                kind="owner_feedback",
                text=feedback["owner_text"],
                target_ref=feedback["target_ref"],
            )
            packet = create_prompt_for_stage(
                root,
                app["app_id"],
                stage=feedback["stage"],
                substage=str(payload.get("substage") or default_feedback_substage(feedback["stage"], target_type=feedback["target_type"])),
                owner_message=feedback["owner_text"],
                feedback=feedback,
            )
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(
                True,
                f"Recorded feedback and prepared revision packet {packet['packet_id']}.",
                artifacts_written=(packet.get("packet_ref", ""),),
                projection=projection,
            ).to_dict()
        if command == "stage.submit":
            app = create_or_load_app(root, app_id or app_name, app_name)
            stage = str(payload.get("stage") or app.get("current_stage") or "intent")
            submitted = submit_stage_proof(
                root,
                app["app_id"],
                stage=stage,
                owner_text=str(payload.get("owner_text") or ""),
                agent_text=str(payload.get("agent_text") or ""),
                artifact_title=str(payload.get("artifact_title") or ""),
                artifact_body=str(payload.get("artifact_body") or ""),
                artifact_name=str(payload.get("artifact_name") or ""),
            )
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(
                True,
                f"Submitted {normalize_stage(stage)} proof and transcript turn.",
                artifacts_written=(submitted["artifact"]["path"],),
                events_written=(submitted["turn"]["turn_id"],),
                projection=projection,
            ).to_dict()
        if command == "stage.evaluate":
            app = create_or_load_app(root, app_id or app_name, app_name)
            stage = str(payload.get("stage") or app.get("current_stage") or "intent")
            evaluation = complete_stage_evaluation(root, app["app_id"], stage=stage, run_gates=bool(payload.get("run_gates", False)))
            projection = app_projection(root, app["app_id"])
            ok = evaluation["result"].get("decision") in weave_runtime_slice.EVALUATION_PASS_DECISIONS
            return BackendCommandResult(
                ok,
                f"Evaluation completed for {normalize_stage(stage)}: {evaluation['result'].get('decision')}.",
                artifacts_written=(evaluation["duty"].get("result_path", ""), evaluation["duty"].get("review_path", "")),
                blocked_by=tuple(evaluation["result"].get("blockers", [])),
                projection=projection,
            ).to_dict()
        if command == "stage.approve":
            app = create_or_load_app(root, app_id or app_name, app_name)
            stage = str(payload.get("stage") or app.get("current_stage") or "intent")
            result = weave_runtime_slice.approve_stage(
                root,
                app["app_id"],
                stage,
                note=str(payload.get("note") or "Approved through Textual cockpit."),
                defer_capability=bool(payload.get("defer_credentials", False)),
                defer_reason=str(payload.get("defer_reason") or payload.get("note") or ""),
            )
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(
                bool(result.get("approved")),
                f"Stage approval {'recorded' if result.get('approved') else 'blocked'} for {normalize_stage(stage)}.",
                blocked_by=tuple(result.get("gate", {}).get("missing", [])) if not result.get("approved") else (),
                projection=projection,
            ).to_dict()
        if command == "stage.advance":
            app = create_or_load_app(root, app_id or app_name, app_name)
            result = weave_runtime_slice.advance_stage(root, app["app_id"], note=str(payload.get("note") or "Advanced through Textual cockpit."))
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(
                bool(result.get("advanced")),
                f"Stage advance {'completed' if result.get('advanced') else 'blocked'}: {result.get('from_stage', result.get('stage'))} -> {result.get('stage')}.",
                blocked_by=tuple(result.get("gate", {}).get("missing", [])) if not result.get("advanced") else (),
                projection=projection,
            ).to_dict()
        if command == "executor.run":
            app = create_or_load_app(root, app_id or app_name, app_name)
            executor = str(payload.get("executor") or "codex")
            if executor != "codex":
                return BackendCommandResult(
                    False,
                    f"Unsupported executor: {executor}",
                    failure_class="validation_error",
                    blocked_by=("unsupported_executor",),
                    projection=app_projection(root, app["app_id"]),
                ).to_dict()
            result = run_codex_engineering(
                root,
                app["app_id"],
                owner_message=str(payload.get("owner_message") or ""),
                timeout_seconds=int(payload.get("timeout_seconds") or 600),
            )
            projection = app_projection(root, app["app_id"])
            return BackendCommandResult(
                bool(result["ok"]),
                "Codex engineering execution completed." if result["ok"] else "Codex engineering execution failed or was unavailable.",
                artifacts_written=(
                    result["executor_manifest"].get("manifest_ref", ""),
                    result["source_manifest"].get("manifest_ref", ""),
                    result["packet"].get("packet_ref", ""),
                ),
                blocked_by=() if result["ok"] else (result["executor_manifest"].get("failure_class", "executor_failed"),),
                projection=projection,
            ).to_dict()
        return BackendCommandResult(
            False,
            f"Unsupported backend command: {command}",
            failure_class="validation_error",
            blocked_by=("unknown_command",),
            safe_next_actions=(
                "workspace.create_app",
                "foundation.save",
                "prompt.prepare",
                "stage.submit",
                "stage.evaluate",
                "stage.approve",
                "stage.advance",
                "executor.run",
            ),
            projection=dashboard_projection(root, app_id=app_id, app_name=app_name),
        ).to_dict()
    except (weave_runtime_slice.RuntimeSliceError, weave_prompt_library.PromptLibraryError, BackendError) as exc:
        return BackendCommandResult(
            False,
            str(exc),
            failure_class="backend_error",
            blocked_by=(type(exc).__name__,),
            safe_next_actions=("inspect state", "fix missing artifact", "retry command"),
            projection=dashboard_projection(root, app_id=app_id, app_name=app_name),
        ).to_dict()
