#!/usr/bin/env python3
"""Run scripted-user/live-agent WEAVE scenario batches.

This runner is the live counterpart to the deterministic full-conversation
fixture: scenario files script only the owner/user turns. Agent replies must come
from the selected adapter. CI can exercise the orchestration with fixture mode,
but declared live mode fails if any reply is fixture/replay sourced.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import weave_runtime_slice as runtime  # noqa: E402

SCENARIO_SCHEMA = "weave-scripted-user-live-agent-scenario/v0.1"
AGGREGATE_SCHEMA = "weave-scripted-user-live-agent-run/v0.1"
SCENARIO_REPORT_SCHEMA = "weave-scripted-user-live-agent-scenario-report/v0.1"

SCRIPTED_USER_SOURCE = "scripted_user_scenario"
LIVE_AGENT_SOURCES = {"live_hermes", "live_agent", "deployed_agent"}
FIXTURE_AGENT_SOURCES = {
    "fixture",
    "scripted",
    "scripted_fixture",
    "deterministic_fixture",
    "fake_agent",
    "replay",
    "full-conversation-dogfood",
}
DEFAULT_OUTPUT_DIR = Path("artifacts") / "scripted-user-live-agent-runs"
DEFAULT_NON_CLAIMS = [
    "scripted user prompts only; user messages are not live human input",
    "fixture mode is not live Hermes or deployed-agent proof",
    "Hermes CLI mode is live agent generation but not Telegram/deployed gateway proof",
    "no deploy, analytics, payments, provider credentials, public posts, or external sends are performed by this runner",
]


class ScenarioError(RuntimeError):
    """A scenario is invalid or failed an explicit gate."""


class StepTimeout(ScenarioError):
    """The selected adapter did not return a reply within the step timeout."""


@dataclass
class AgentReply:
    text: str
    source: str
    elapsed_seconds: float
    session_id: str = ""
    model: str = ""
    provider: str = ""
    stdout_sha256: str = ""
    stderr_sha256: str = ""
    metadata: dict[str, Any] | None = None

    def as_message(self) -> dict[str, Any]:
        message: dict[str, Any] = {
            "role": "hermes",
            "source": self.source,
            "text": self.text,
            "elapsed_seconds": self.elapsed_seconds,
        }
        if self.session_id:
            message["session_id"] = self.session_id
        if self.model:
            message["model"] = self.model
        if self.provider:
            message["provider"] = self.provider
        if self.stdout_sha256:
            message["stdout_sha256"] = self.stdout_sha256
        if self.stderr_sha256:
            message["stderr_sha256"] = self.stderr_sha256
        if self.metadata:
            message["metadata"] = self.metadata
        return message


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_label(value: str) -> str:
    label = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip().lower()).strip("-._")
    return label or "step"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def render_template(value: str, *, scenario_id: str, run_id: str, run_index: int) -> str:
    return value.format(scenario_id=scenario_id, run_id=run_id, run_index=run_index)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScenarioError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ScenarioError(f"Scenario must be a JSON object: {path}")
    return payload


def scenario_id(scenario: dict[str, Any]) -> str:
    raw = str(scenario.get("scenario_id") or scenario.get("id") or "").strip()
    if not raw:
        raise ScenarioError("Scenario requires scenario_id")
    return safe_label(raw)


def scenario_steps(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    steps = scenario.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ScenarioError("Scenario requires a non-empty steps[] list")
    normalized: list[dict[str, Any]] = []
    labels: set[str] = set()
    for index, raw in enumerate(steps, start=1):
        if not isinstance(raw, dict):
            raise ScenarioError(f"Scenario step {index} must be an object")
        label = safe_label(str(raw.get("label") or f"step-{index}"))
        if label in labels:
            raise ScenarioError(f"Duplicate scenario step label: {label}")
        labels.add(label)
        stage = runtime.normalize_stage_id(str(raw.get("stage") or "intent"))
        message = str(raw.get("user_message") or raw.get("owner_message") or "").strip()
        if not message:
            raise ScenarioError(f"Scenario step {label} requires user_message")
        step = dict(raw)
        step["label"] = label
        step["stage"] = stage
        step["user_message"] = message
        normalized.append(step)
    return normalized


def fixture_replies_by_label(scenario: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    replies: dict[str, list[dict[str, Any]]] = {}
    for raw in scenario.get("fixture_replies", []):
        if not isinstance(raw, dict):
            raise ScenarioError("fixture_replies[] entries must be objects")
        label = safe_label(str(raw.get("label") or raw.get("step") or ""))
        if not label:
            raise ScenarioError("fixture reply requires label")
        text = str(raw.get("text") or raw.get("reply") or "").strip()
        if not text:
            raise ScenarioError(f"fixture reply for {label} requires text")
        source = str(raw.get("source") or "scripted_fixture").strip()
        if not source:
            raise ScenarioError(f"fixture reply for {label} requires non-empty source")
        replies.setdefault(label, []).append(dict(raw, text=text, source=source))
    return replies


def validate_agent_reply_source_for_mode(mode: str, source: str) -> None:
    clean = str(source or "").strip()
    if not clean:
        raise ScenarioError("Agent reply source is required")
    if mode == "live" and clean not in LIVE_AGENT_SOURCES:
        raise ScenarioError(
            "Declared live mode cannot use fixture/replay/deterministic agent replies: "
            f"source={clean!r}"
        )
    if mode == "fixture" and clean in LIVE_AGENT_SOURCES:
        raise ScenarioError(
            "Fixture mode cannot impersonate a live agent reply source: "
            f"source={clean!r}"
        )


def parse_hermes_stdout(stdout: str) -> dict[str, str]:
    session_id = ""
    reply_lines: list[str] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "tirith security scanner" in stripped:
            continue
        if stripped.startswith("session_id:"):
            session_id = stripped.split(":", 1)[1].strip()
            continue
        reply_lines.append(line.rstrip())
    return {"session_id": session_id, "reply": "\n".join(reply_lines).strip()}


class AgentAdapter:
    name = "base"

    def reply(self, *, scenario: dict[str, Any], step: dict[str, Any], prompt: str, cwd: Path, timeout: int) -> AgentReply:
        raise NotImplementedError


class FixtureAgentAdapter(AgentAdapter):
    name = "fixture"

    def __init__(self, replies: dict[str, list[dict[str, Any]]]) -> None:
        self.replies = {label: list(items) for label, items in replies.items()}
        self.indexes: dict[str, int] = {}

    def reply(self, *, scenario: dict[str, Any], step: dict[str, Any], prompt: str, cwd: Path, timeout: int) -> AgentReply:
        label = step["label"]
        items = self.replies.get(label, [])
        position = self.indexes.get(label, 0)
        if position >= len(items):
            raise ScenarioError(f"No fixture reply available for step {label!r}")
        self.indexes[label] = position + 1
        item = items[position]
        delay = float(item.get("delay_seconds") or 0)
        if delay > timeout:
            raise StepTimeout(f"Fixture reply for {label!r} simulated timeout after {timeout}s")
        if delay > 0:
            time.sleep(delay)
        return AgentReply(
            text=str(item["text"]),
            source=str(item.get("source") or "scripted_fixture"),
            elapsed_seconds=round(delay, 3),
            session_id=str(item.get("session_id") or f"fixture-{label}-{position + 1}"),
            model=str(item.get("model") or "fixture"),
            provider=str(item.get("provider") or "fixture"),
            stdout_sha256=sha256_text(str(item["text"])),
            stderr_sha256=sha256_text(""),
            metadata={"fixture_label": label, "fixture_index": position},
        )


class HermesCliAgentAdapter(AgentAdapter):
    name = "hermes-cli"

    def __init__(self, *, hermes_bin: Path, model: str, provider: str, max_turns: int, yolo: bool) -> None:
        self.hermes_bin = hermes_bin.expanduser()
        self.model = model
        self.provider = provider
        self.max_turns = max_turns
        self.yolo = yolo

    def reply(self, *, scenario: dict[str, Any], step: dict[str, Any], prompt: str, cwd: Path, timeout: int) -> AgentReply:
        if not self.hermes_bin.exists() and not shutil.which(str(self.hermes_bin)):
            raise ScenarioError(f"Hermes executable does not exist or is not on PATH: {self.hermes_bin}")
        command = [
            str(self.hermes_bin),
            "chat",
            "--quiet",
            "--source",
            "tool",
            "--max-turns",
            str(self.max_turns),
            "--model",
            self.model,
            "--provider",
            self.provider,
        ]
        if self.yolo:
            command.extend(["--yolo", "--accept-hooks"])
        command.extend(["--query", prompt])
        started = time.monotonic()
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise StepTimeout(f"Hermes CLI timed out after {timeout}s for step {step['label']!r}") from exc
        elapsed = round(time.monotonic() - started, 3)
        parsed = parse_hermes_stdout(result.stdout)
        if result.returncode != 0:
            raise ScenarioError(
                "Hermes CLI invocation failed; "
                f"returncode={result.returncode}; stderr_sha256={sha256_text(result.stderr)}"
            )
        if not parsed["reply"]:
            raise ScenarioError("Hermes CLI returned no reviewable reply text")
        return AgentReply(
            text=parsed["reply"],
            source="live_hermes",
            elapsed_seconds=elapsed,
            session_id=parsed["session_id"],
            model=self.model,
            provider=self.provider,
            stdout_sha256=sha256_text(result.stdout),
            stderr_sha256=sha256_text(result.stderr),
            metadata={
                "command_shape": "hermes chat --quiet --source tool --max-turns N --model MODEL --provider PROVIDER --query PROMPT",
                "cwd_role": str(step.get("cwd") or "weave_root"),
            },
        )


def build_adapter(args: argparse.Namespace, scenario: dict[str, Any]) -> AgentAdapter:
    if args.agent == "fixture":
        return FixtureAgentAdapter(fixture_replies_by_label(scenario))
    if args.agent == "hermes-cli":
        return HermesCliAgentAdapter(
            hermes_bin=Path(args.hermes_bin),
            model=args.model,
            provider=args.provider,
            max_turns=args.max_turns,
            yolo=args.yolo,
        )
    raise ScenarioError(f"Unsupported agent adapter: {args.agent}")


def populate_foundation(root: Path, app_id: str, app_name: str, scenario: dict[str, Any]) -> None:
    foundation_obj = scenario.get("foundation")
    foundation: dict[str, Any] = foundation_obj if isinstance(foundation_obj, dict) else {}
    base = runtime.app_root(root, app_id)
    write_text(
        root / "artifacts" / "general" / "soul.md",
        str(
            foundation.get("soul")
            or "WEAVE scripted-user/live-agent scenario runner proof root. Public-safe local evidence only."
        ),
    )
    write_text(
        root / "artifacts" / "general" / "owner-profile.md",
        str(
            foundation.get("owner_profile")
            or "Owner wants fast scripted-user/live-agent application dogfood with explicit approval and safety gates."
        ),
    )
    intent = str(foundation.get("app_context") or scenario.get("intent") or "Scripted user/live agent app-production scenario.")
    write_text(
        base / "context" / "app-context.md",
        f"# App Context\n\nApp: {app_name}\n\nIntent: {intent}\n\nThis context was seeded by the scenario runner so lifecycle gates can evaluate real agent replies.",
    )
    write_text(
        base / "context" / "user-context-for-this-app.md",
        "# User Context\n\nThe user turns are scripted by the scenario file. Agent replies must be produced by the selected adapter.",
    )
    write_text(
        base / "inventory" / "app-inventory.md",
        "# App Inventory\n\nInitial inventory seeded for scenario execution. Generated app files, if any, live in repo/primary.",
    )
    write_text(
        base / "contract" / "gestaltian-contract.md",
        "# Gestaltian Contract\n\nKeep external actions gated. Record public-safe proof artifacts. Do not claim fixture replies as live agent proof.",
    )
    app = runtime.load_app(root, app_id)
    app["required_inputs"] = []
    app["owner_questions"] = []
    app["blockers"] = []
    app.setdefault("capabilities", ["local-runtime", "conversation-capture", "stage-artifacts"])
    runtime.write_app(root, app)
    runtime.append_event(
        root,
        app_id,
        runtime.new_event(
            "foundation.completed",
            app_id,
            "intent",
            "Scenario runner seeded public-safe foundation context before scripted-user/live-agent execution.",
            payload={"scenario_id": scenario_id(scenario)},
        ),
    )


def stage_turn_count(root: Path, app_id: str, stage: str) -> int:
    return sum(1 for turn in runtime.read_conversation_turns(root, app_id) if turn.get("stage") == stage)


def build_prompt(
    *,
    scenario: dict[str, Any],
    app_id: str,
    app_name: str,
    step: dict[str, Any],
    root: Path,
    app_repo: Path,
) -> str:
    recent_turns = runtime.read_conversation_turns(root, app_id)[-4:]
    recent_summary = [
        {
            "stage": turn.get("stage"),
            "operator": str(turn.get("operator_message", {}).get("text", ""))[:500],
            "agent_source": turn.get("agent_reply", {}).get("source", ""),
            "agent": str(turn.get("agent_reply", {}).get("text", ""))[:500],
        }
        for turn in recent_turns
    ]
    prompt_context = {
        "scenario_id": scenario_id(scenario),
        "app_id": app_id,
        "app_name": app_name,
        "stage": step["stage"],
        "step_label": step["label"],
        "scripted_user_message": step["user_message"],
        "expect": step.get("expect", {}),
        "app_repo": str(app_repo),
        "recent_turns": recent_summary,
        "stage_gate_before": runtime.stage_gate_status(root, app_id, step["stage"]),
    }
    return (
        "You are the live WEAVE/Hermes agent in a scripted-user/live-agent dogfood run.\n"
        "The user message below is scripted by the test harness; your reply must be generated now by the live agent adapter.\n"
        "Do not claim external sends, deploys, analytics, payments, or credentials. Keep secrets out.\n"
        "If the step asks you to make app files and your working directory is the app repo, create only local public-safe files there and summarize what changed.\n"
        "Record only owner-reviewable reasoning summaries; do not expose hidden chain-of-thought.\n\n"
        "RUN CONTEXT JSON:\n"
        + json.dumps(prompt_context, indent=2, sort_keys=True)
        + "\n\nSCRIPTED USER MESSAGE:\n"
        + step["user_message"]
        + "\n\nReply as the agent to the user."
    )


def write_step_artifact(
    *,
    root: Path,
    app_id: str,
    step_index: int,
    step: dict[str, Any],
    reply: AgentReply,
    expectations: list[dict[str, Any]],
) -> dict[str, Any]:
    stage = runtime.stage_by_id(step["stage"])
    path = (
        runtime.app_root(root, app_id)
        / "lifecycle"
        / stage.directory
        / "artifacts"
        / f"{step_index:02d}-{safe_label(step['label'])}-agent-reply.md"
    )
    body = [
        f"# {step['label']} Agent Reply Proof",
        "",
        f"Schema: `{SCENARIO_REPORT_SCHEMA}`",
        f"Stage: `{step['stage']}`",
        f"Agent source: `{reply.source}`",
        f"Elapsed seconds: `{reply.elapsed_seconds}`",
        "",
        "## Scripted User Message",
        "",
        step["user_message"],
        "",
        "## Agent Reply",
        "",
        reply.text,
        "",
        "## Expectation Results",
        "",
    ]
    for item in expectations:
        marker = "pass" if item["passed"] else "fail"
        body.append(f"- {marker}: {item['name']} — {item.get('detail', '')}")
    write_text(path, "\n".join(body))
    ref = {"path": runtime.relative(path, root), "action": "created", "kind": "artifact", "checksum": runtime.artifact_checksum(path)}
    runtime.append_event(
        root,
        app_id,
        runtime.new_event(
            "artifact.created",
            app_id,
            step["stage"],
            f"Recorded scripted-user/live-agent reply proof for step {step['label']}.",
            payload={"step_label": step["label"], "agent_source": reply.source},
            artifact_refs=[ref],
        ),
    )
    return ref


def evaluate_expectations(
    *,
    step: dict[str, Any],
    reply: AgentReply,
    before_turn_count: int,
    after_turn_count: int,
    after_state: dict[str, Any],
    stage_message_count: int,
) -> list[dict[str, Any]]:
    expect = step.get("expect") if isinstance(step.get("expect"), dict) else {}
    checks: list[dict[str, Any]] = []
    text = reply.text

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    for key in ("reply_contains_all", "contains_all"):
        if isinstance(expect.get(key), list):
            missing = [str(item) for item in expect[key] if str(item) not in text]
            add(key, not missing, "missing=" + json.dumps(missing))
    for key in ("reply_contains_any", "contains_any"):
        if isinstance(expect.get(key), list):
            values = [str(item) for item in expect[key]]
            add(key, any(item in text for item in values), "options=" + json.dumps(values))
    if isinstance(expect.get("reply_not_contains_any"), list):
        found = [str(item) for item in expect["reply_not_contains_any"] if str(item) in text]
        add("reply_not_contains_any", not found, "found=" + json.dumps(found))
    if isinstance(expect.get("reply_regex_any"), list):
        patterns = [str(item) for item in expect["reply_regex_any"]]
        add("reply_regex_any", any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in patterns), "patterns=" + json.dumps(patterns))
    if "reply_min_chars" in expect:
        minimum = int(expect["reply_min_chars"])
        add("reply_min_chars", len(text) >= minimum, f"len={len(text)} minimum={minimum}")
    if isinstance(expect.get("agent_source_in"), list):
        allowed = {str(item) for item in expect["agent_source_in"]}
        add("agent_source_in", reply.source in allowed, f"source={reply.source} allowed={sorted(allowed)}")
    if "turn_count_delta_at_least" in expect:
        minimum = int(expect["turn_count_delta_at_least"])
        delta = after_turn_count - before_turn_count
        add("turn_count_delta_at_least", delta >= minimum, f"delta={delta} minimum={minimum}")
    if isinstance(expect.get("stage_in"), list):
        stage = after_state["stage_status"]["stage"]
        allowed = {str(item) for item in expect["stage_in"]}
        add("stage_in", stage in allowed, f"stage={stage} allowed={sorted(allowed)}")
    if isinstance(expect.get("stage_state_in"), list):
        stage_state = after_state["stage_status"].get("stage_state")
        allowed = {str(item) for item in expect["stage_state_in"]}
        add("stage_state_in", stage_state in allowed, f"stage_state={stage_state} allowed={sorted(allowed)}")
    if "stage_message_count_at_most" in expect:
        maximum = int(expect["stage_message_count_at_most"])
        add("stage_message_count_at_most", stage_message_count <= maximum, f"count={stage_message_count} maximum={maximum}")
    if not checks:
        add("non_empty_agent_reply", bool(text.strip()), f"len={len(text)}")
    return checks


def resolve_action(action: str, *, labels: dict[str, int], current_index: int) -> tuple[str, int | None]:
    clean = (action or "next").strip()
    if clean == "next":
        return "goto_index", current_index + 1
    if clean == "stop":
        return "stop", None
    if clean == "abort":
        return "abort", None
    if clean.startswith("goto:"):
        label = safe_label(clean.split(":", 1)[1])
        if label not in labels:
            raise ScenarioError(f"Branch target not found: {label}")
        return "goto_index", labels[label]
    raise ScenarioError(f"Unsupported branch action: {action}")


def apply_post_actions(root: Path, app_id: str, step: dict[str, Any]) -> list[dict[str, Any]]:
    actions = step.get("post_actions") if isinstance(step.get("post_actions"), list) else []
    results: list[dict[str, Any]] = []
    for action in actions:
        clean = str(action).strip()
        if clean == "approve_stage":
            results.append(
                {
                    "action": clean,
                    "result": runtime.approve_stage(
                        root,
                        app_id,
                        step["stage"],
                        note=f"Scenario runner owner-scripted approval after step {step['label']}.",
                        defer_capability=bool(step.get("defer_credentials")),
                        defer_reason=str(step.get("defer_reason") or "Scenario explicitly deferred credentials."),
                    ),
                }
            )
        elif clean == "advance_stage":
            results.append(
                {
                    "action": clean,
                    "result": runtime.advance_stage(root, app_id, note=f"Scenario runner advanced after step {step['label']}."),
                }
            )
        else:
            raise ScenarioError(f"Unsupported post_action: {clean}")
    return results


def run_step(
    *,
    scenario: dict[str, Any],
    mode: str,
    adapter: AgentAdapter,
    root: Path,
    app_id: str,
    app_name: str,
    app_repo: Path,
    step_index: int,
    step: dict[str, Any],
    default_timeout: int,
) -> dict[str, Any]:
    before_turns = runtime.read_conversation_turns(root, app_id)
    before_state = runtime.app_state(root, app_id)
    before_stage_count = stage_turn_count(root, app_id, step["stage"])
    timeout = int(step.get("timeout_seconds") or default_timeout)
    cwd_role = str(step.get("cwd") or "weave_root")
    cwd = app_repo if cwd_role == "app_repo" else root
    cwd.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(scenario=scenario, app_id=app_id, app_name=app_name, step=step, root=root, app_repo=app_repo)
    reply = adapter.reply(scenario=scenario, step=step, prompt=prompt, cwd=cwd, timeout=timeout)
    validate_agent_reply_source_for_mode(mode, reply.source)

    predicted_after_turn_count = len(before_turns) + 1
    predicted_after_stage_count = before_stage_count + 1
    expectations = evaluate_expectations(
        step=step,
        reply=reply,
        before_turn_count=len(before_turns),
        after_turn_count=predicted_after_turn_count,
        after_state=before_state,
        stage_message_count=predicted_after_stage_count,
    )
    artifact_ref = write_step_artifact(
        root=root,
        app_id=app_id,
        step_index=step_index,
        step=step,
        reply=reply,
        expectations=expectations,
    )
    gate_before_turn = runtime.stage_gate_status(root, app_id, step["stage"])
    turn = runtime.new_conversation_turn(
        app_id,
        step["stage"],
        {
            "role": "owner",
            "source": SCRIPTED_USER_SOURCE,
            "text": step["user_message"],
            "scenario_step": step["label"],
        },
        reply.as_message(),
        channel="scripted-user-live-agent-runner",
        created_by="execution-agent",
        agent_rationale={
            "summary": f"Scenario runner captured an agent reply from {reply.source} for scripted user step {step['label']}.",
            "gate_questions": ["Did the reply satisfy the scripted scenario predicates?"],
            "missing_information": [],
            "decision_basis": [f"adapter={adapter.name}", f"artifact={artifact_ref['path']}"],
            "chain_of_thought_captured": False,
        },
        gate_checks={
            "source_mode_guard_passed": True,
            "foundation_gate_passed_before_turn": gate_before_turn["foundation_gate"]["passed"],
            "stage_gate_passed_before_turn": gate_before_turn["passed"],
            "stage_gate_missing_before_turn": gate_before_turn["missing"],
        },
        artifact_refs=[artifact_ref],
        state_transition={
            "from_stage": before_state["stage_status"]["stage"],
            "from_state": before_state["stage_status"].get("stage_state"),
            "to_stage": step["stage"],
            "to_state": "agent_reply_captured",
            "reason": "scripted user turn received a generated/captured agent reply",
        },
        next_action=str(step.get("next_action") or "Evaluate scenario predicates and branch."),
    )
    appended = runtime.append_conversation_turn(root, app_id, turn)
    after_turns = runtime.read_conversation_turns(root, app_id)
    after_stage_count = stage_turn_count(root, app_id, step["stage"])
    post_actions = apply_post_actions(root, app_id, step) if all(item["passed"] for item in expectations) else []
    final_state = runtime.app_state(root, app_id)
    return {
        "label": step["label"],
        "stage": step["stage"],
        "status": "passed" if all(item["passed"] for item in expectations) else "failed_expectations",
        "user_message_sha256": sha256_text(step["user_message"]),
        "agent_source": reply.source,
        "agent_reply_sha256": sha256_text(reply.text),
        "agent_reply_excerpt": reply.text[:800],
        "session_id": reply.session_id,
        "elapsed_seconds": reply.elapsed_seconds,
        "before_turn_count": len(before_turns),
        "after_turn_count": len(after_turns),
        "before_stage_message_count": before_stage_count,
        "after_stage_message_count": after_stage_count,
        "expectations": expectations,
        "artifact_ref": artifact_ref,
        "turn_id": appended["turn_id"],
        "post_actions": post_actions,
        "before_stage_status": before_state["stage_status"],
        "after_stage_status": final_state["stage_status"],
    }


def snapshot_app_repo(app_repo: Path, snapshot_dir: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    if app_repo.exists():
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
        shutil.copytree(app_repo, snapshot_dir)
        for path in sorted(snapshot_dir.rglob("*")):
            if path.is_file():
                files[str(path.relative_to(snapshot_dir))] = runtime.artifact_checksum(path)
    return {"path": str(snapshot_dir), "file_count": len(files), "checksums": files}


def run_scenario_instance(
    *,
    scenario: dict[str, Any],
    scenario_path: Path,
    args: argparse.Namespace,
    run_id: str,
    run_index: int,
) -> dict[str, Any]:
    sid = scenario_id(scenario)
    steps = scenario_steps(scenario)
    adapter = build_adapter(args, scenario)
    app_config = scenario.get("app") if isinstance(scenario.get("app"), dict) else {}
    app_id_template = str(app_config.get("id_template") or f"{sid}-{{run_index}}")
    app_name_template = str(app_config.get("name_template") or scenario.get("app_name") or sid.replace("-", " ").title())
    app_id = runtime.slugify(render_template(app_id_template, scenario_id=sid, run_id=run_id, run_index=run_index))
    app_name = render_template(app_name_template, scenario_id=sid, run_id=run_id, run_index=run_index)
    scenario_dir = Path(args.output_dir).expanduser() / run_id / f"{sid}-{run_index}"
    if scenario_dir.exists() and args.force:
        shutil.rmtree(scenario_dir)
    if scenario_dir.exists():
        raise ScenarioError(f"Scenario output already exists: {scenario_dir}")
    root = scenario_dir / "weave-root"
    report_path = scenario_dir / "scenario-report.json"
    root.mkdir(parents=True, exist_ok=True)
    runtime.setup_weave_root(root)
    runtime.create_app(root, app_id, app_name)
    populate_foundation(root, app_id, app_name, scenario)
    app_repo = root / "apps" / app_id / "repo" / "primary"
    app_repo.mkdir(parents=True, exist_ok=True)

    labels = {step["label"]: index for index, step in enumerate(steps)}
    max_executed_steps = int(scenario.get("max_executed_steps") or max(20, len(steps) * 4))
    index = 0
    executed = 0
    passed = True
    terminal_reason = "completed"
    step_results: list[dict[str, Any]] = []
    branch_history: list[dict[str, Any]] = []

    while index < len(steps):
        if executed >= max_executed_steps:
            passed = False
            terminal_reason = f"max_executed_steps exceeded: {max_executed_steps}"
            break
        step = steps[index]
        executed += 1
        try:
            result = run_step(
                scenario=scenario,
                mode=args.mode,
                adapter=adapter,
                root=root,
                app_id=app_id,
                app_name=app_name,
                app_repo=app_repo,
                step_index=executed,
                step=step,
                default_timeout=args.timeout,
            )
        except StepTimeout as exc:
            result = {"label": step["label"], "stage": step["stage"], "status": "timeout", "error": str(exc)}
            action = str(step.get("on_timeout") or "abort")
        except Exception as exc:
            result = {"label": step["label"], "stage": step["stage"], "status": "error", "error": str(exc)}
            action = str(step.get("on_error") or step.get("on_fail") or "abort")
        else:
            action = str(step.get("on_pass") or "next")
            max_stage_messages = step.get("max_stage_messages")
            if isinstance(max_stage_messages, int) and result.get("after_stage_message_count", 0) > max_stage_messages:
                result["status"] = "max_stage_messages_exceeded"
                action = str(step.get("on_max_stage_messages") or step.get("on_fail") or "abort")
            elif result["status"] != "passed":
                action = str(step.get("on_fail") or "abort")
        step_results.append(result)
        branch_history.append({"from": step["label"], "status": result["status"], "action": action})
        branch_kind, target = resolve_action(action, labels=labels, current_index=index)
        if branch_kind == "abort":
            passed = False
            terminal_reason = f"aborted at {step['label']}: {result['status']}"
            break
        if branch_kind == "stop":
            terminal_reason = f"stopped at {step['label']}"
            break
        if target is None:
            raise ScenarioError(f"Branch action produced no target: {action}")
        index = target

    export = runtime.export_conversation_review(root, app_id)
    final_state = runtime.app_state(root, app_id)
    app_snapshot = snapshot_app_repo(app_repo, scenario_dir / "app-source-snapshot")
    turns = runtime.read_conversation_turns(root, app_id)
    source_summary = runtime.conversation_source_summary(turns)
    report = {
        "schema": SCENARIO_REPORT_SCHEMA,
        "scenario_schema": scenario.get("schema", ""),
        "scenario_path": str(scenario_path),
        "scenario_id": sid,
        "run_id": run_id,
        "run_index": run_index,
        "created_at": utc_now(),
        "passed": passed,
        "terminal_reason": terminal_reason,
        "mode": args.mode,
        "agent_adapter": adapter.name,
        "reply_source_requirement": "live mode requires live_hermes/live_agent/deployed_agent; fixture/replay sources fail live mode",
        "app_id": app_id,
        "app_name": app_name,
        "runtime_root": str(root),
        "step_count": len(step_results),
        "steps": step_results,
        "branch_history": branch_history,
        "conversation_review": export,
        "source_summary": source_summary,
        "final_stage": final_state["stage_status"],
        "app_source_snapshot": app_snapshot,
        "explicit_non_claims": DEFAULT_NON_CLAIMS,
    }
    write_json(report_path, report)
    return {
        "scenario_id": sid,
        "run_index": run_index,
        "passed": passed,
        "terminal_reason": terminal_reason,
        "scenario_dir": str(scenario_dir),
        "report": str(report_path),
        "app_id": app_id,
        "turn_count": len(turns),
        "source_summary": source_summary,
    }


def run_all(args: argparse.Namespace) -> dict[str, Any]:
    run_id = args.run_id or f"{utc_stamp()}-scripted-user-live-agent"
    output_root = Path(args.output_dir).expanduser() / run_id
    output_root.mkdir(parents=True, exist_ok=True)
    scenarios = [(Path(path), load_json(Path(path))) for path in args.scenario]
    tasks: list[tuple[Path, dict[str, Any], int]] = []
    run_index = 1
    for path, scenario in scenarios:
        for _ in range(args.repeat):
            tasks.append((path, scenario, run_index))
            run_index += 1
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = [
            executor.submit(run_scenario_instance, scenario=scenario, scenario_path=path, args=args, run_id=run_id, run_index=index)
            for path, scenario, index in tasks
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append({"passed": False, "terminal_reason": str(exc), "error_type": type(exc).__name__})
    results.sort(key=lambda item: (str(item.get("scenario_id", "")), int(item.get("run_index", 0))))
    aggregate = {
        "schema": AGGREGATE_SCHEMA,
        "run_id": run_id,
        "created_at": utc_now(),
        "passed": all(item.get("passed") is True for item in results),
        "mode": args.mode,
        "agent": args.agent,
        "parallel": args.parallel,
        "repeat": args.repeat,
        "scenario_count": len(scenarios),
        "instance_count": len(results),
        "results": results,
        "output_root": str(output_root),
        "explicit_non_claims": DEFAULT_NON_CLAIMS,
    }
    write_json(output_root / "aggregate-report.json", aggregate)
    return aggregate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", action="append", required=True, help="Path to a JSON scenario file. Repeatable.")
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture", help="Declared proof mode.")
    parser.add_argument("--agent", choices=("fixture", "hermes-cli"), default="fixture", help="Agent adapter to use.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for run artifacts.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--repeat", type=int, default=1, help="Number of instances to run per scenario.")
    parser.add_argument("--parallel", type=int, default=1, help="Max parallel scenario instances.")
    parser.add_argument("--timeout", type=int, default=120, help="Default seconds per agent reply.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scenario output directories for this run id.")
    parser.add_argument("--hermes-bin", default=os.environ.get("WEAVE_HERMES_BIN", "hermes"))
    parser.add_argument("--model", default=os.environ.get("WEAVE_HERMES_MODEL", "gpt-5.5"))
    parser.add_argument("--provider", default=os.environ.get("WEAVE_HERMES_PROVIDER_ADAPTER", "codex"))
    parser.add_argument("--max-turns", type=int, default=4, help="Hermes CLI internal max turns per scripted user message.")
    parser.add_argument("--no-yolo", dest="yolo", action="store_false", help="Disable Hermes --yolo/--accept-hooks for live app-writing runs.")
    parser.set_defaults(yolo=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat must be >= 1")
    if args.parallel < 1:
        parser.error("--parallel must be >= 1")
    if args.mode == "live" and args.agent == "fixture":
        # Keep this as an early, explicit failure; runtime source validation is
        # still present for mocked adapters and future adapter additions.
        parser.error("--mode live cannot use --agent fixture")
    try:
        report = run_all(args)
    except Exception as exc:
        print(f"scripted-user/live-agent runner failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"passed": report["passed"], "run_id": report["run_id"], "output_root": report["output_root"]}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
