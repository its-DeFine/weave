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
import shlex
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
    "full_conversation_dogfood",
}
DEFAULT_OUTPUT_DIR = Path("artifacts") / "scripted-user-live-agent-runs"
COMMON_NON_CLAIMS = [
    "scripted user prompts only; user messages are not live human input",
    "fixture mode is not live Hermes or deployed-agent proof",
    "Hermes CLI mode is live agent generation but not Telegram/deployed gateway proof",
    "the runner itself does not deploy apps, call analytics, handle payments, or post publicly",
]
HERMES_CLI_NON_CLAIMS = [
    "Hermes CLI adapter invokes a live local Hermes process; absence of agent/tool external side effects is not proven by this runner unless Hermes is separately sandboxed or tool-gated",
]
DEPLOYED_GATEWAY_NON_CLAIMS = [
    "deployed-gateway adapter proof requires an owner-approved command that performs send/wait/readback against the real target surface; CI or test-double commands prove adapter plumbing only",
]


def explicit_non_claims_for_adapter(adapter_name: str) -> list[str]:
    claims = list(COMMON_NON_CLAIMS)
    if adapter_name == "hermes-cli":
        claims.extend(HERMES_CLI_NON_CLAIMS)
    elif adapter_name == "deployed-gateway":
        claims.extend(DEPLOYED_GATEWAY_NON_CLAIMS)
    else:
        claims.append("fixture adapter performs no live external sends")
    return claims


class ScenarioError(RuntimeError):
    """A scenario is invalid or failed an explicit gate."""


class StepTimeout(ScenarioError):
    """The selected adapter did not return a reply within the step timeout."""


class SourceModeError(ScenarioError):
    """The observed reply source violated the declared proof mode."""


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


def validate_scenario_schema(scenario: dict[str, Any], path: Path) -> None:
    schema = str(scenario.get("schema") or "").strip()
    if schema != SCENARIO_SCHEMA:
        raise ScenarioError(f"Scenario {path} requires schema={SCENARIO_SCHEMA!r}; got {schema!r}")


def canonical_source_label(source: str) -> str:
    return re.sub(r"[\s-]+", "_", str(source or "").strip().lower())


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
    canonical = canonical_source_label(clean)
    if not clean:
        raise ScenarioError("Agent reply source is required")
    if mode == "live" and canonical not in LIVE_AGENT_SOURCES:
        raise SourceModeError(
            "Declared live mode cannot use fixture/replay/deterministic agent replies: "
            f"source={clean!r} canonical={canonical!r}"
        )
    if mode == "fixture":
        if canonical in LIVE_AGENT_SOURCES:
            raise SourceModeError(
                "Fixture mode cannot impersonate a live agent reply source: "
                f"source={clean!r} canonical={canonical!r}"
            )
        if canonical not in FIXTURE_AGENT_SOURCES:
            raise SourceModeError(
                "Fixture mode requires deterministic fixture/replay source labels: "
                f"source={clean!r} canonical={canonical!r}"
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


class DeployedGatewayCommandAdapter(AgentAdapter):
    name = "deployed-gateway"

    def __init__(self, *, command: str, allow_external_send: bool) -> None:
        if not allow_external_send:
            raise ScenarioError("deployed-gateway adapter requires --allow-external-send owner approval")
        clean = command.strip()
        if not clean:
            raise ScenarioError("deployed-gateway adapter requires --gateway-command or WEAVE_DEPLOYED_GATEWAY_ADAPTER_CMD")
        self.command = shlex.split(clean)
        if not self.command:
            raise ScenarioError("deployed-gateway adapter command is empty")

    def reply(self, *, scenario: dict[str, Any], step: dict[str, Any], prompt: str, cwd: Path, timeout: int) -> AgentReply:
        request = {
            "schema": "weave-deployed-gateway-adapter-request/v0.1",
            "created_at": utc_now(),
            "scenario_id": scenario_id(scenario),
            "step_label": step["label"],
            "stage": step["stage"],
            "scripted_user_message": step["user_message"],
            "prompt": prompt,
            "cwd": str(cwd),
            "timeout_seconds": timeout,
            "required_reply_source": "deployed_agent",
        }
        started = time.monotonic()
        try:
            result = subprocess.run(
                self.command,
                cwd=cwd,
                input=json.dumps(request, sort_keys=True),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise StepTimeout(f"deployed-gateway adapter timed out after {timeout}s for step {step['label']!r}") from exc
        elapsed = round(time.monotonic() - started, 3)
        if result.returncode != 0:
            raise ScenarioError(
                "deployed-gateway adapter command failed; "
                f"returncode={result.returncode}; stderr_sha256={sha256_text(result.stderr)}"
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ScenarioError("deployed-gateway adapter command must return JSON on stdout") from exc
        if not isinstance(payload, dict):
            raise ScenarioError("deployed-gateway adapter response must be a JSON object")
        text = str(payload.get("text") or payload.get("reply") or "").strip()
        source = str(payload.get("source") or "").strip()
        if not text:
            raise ScenarioError("deployed-gateway adapter returned no reviewable reply text")
        if canonical_source_label(source) != "deployed_agent":
            raise ScenarioError("deployed-gateway adapter response must include source='deployed_agent' after send/wait/readback")
        raw_metadata = payload.get("metadata")
        metadata: dict[str, Any] = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
        metadata["command_shape"] = "owner-approved deployed gateway adapter command via JSON stdin/stdout"
        return AgentReply(
            text=text,
            source=source,
            elapsed_seconds=elapsed,
            session_id=str(payload.get("session_id") or payload.get("message_id") or ""),
            model=str(payload.get("model") or "deployed-gateway"),
            provider=str(payload.get("provider") or "deployed-gateway"),
            stdout_sha256=sha256_text(result.stdout),
            stderr_sha256=sha256_text(result.stderr),
            metadata=metadata,
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
    if args.agent == "deployed-gateway":
        return DeployedGatewayCommandAdapter(command=args.gateway_command, allow_external_send=args.allow_external_send)
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
        "Complete the requested lifecycle step within this single adapter invocation; do not leave the work in a max-turn/tool-cap partial state.\n"
        "Do not claim external sends, deploys, analytics, payments, or credentials. Keep secrets out.\n"
        "If the step asks you to make app files and your working directory is the app repo, create only local public-safe files there, verify required files exist, and summarize what changed.\n"
        "If you cannot create or verify the required local files, say that plainly rather than claiming implementation.\n"
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
    artifact_slug: str = "agent-reply",
) -> dict[str, Any]:
    stage = runtime.stage_by_id(step["stage"])
    path = (
        runtime.app_root(root, app_id)
        / "lifecycle"
        / stage.directory
        / "artifacts"
        / f"{step_index:02d}-{safe_label(step['label'])}-{safe_label(artifact_slug)}.md"
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


NEGATED_NON_CLAIM_PATTERNS = (
    "does not claim",
    "do not claim",
    "did not claim",
    "doesn't claim",
    "don't claim",
    "no claim",
    "not claim",
    "not claimed",
    "not claiming",
    "does not assert",
    "do not assert",
    "no external",
    "not sent",
    "not emailed",
    "not deployed",
    "not connected",
    "not enabled",
    "not live",
    "without",
    "never",
)

LIVE_ADAPTER_CAP_MARKERS = (
    "Reached maximum iterations",
    "maximum iterations reached",
)


def _sentence_bounds(text: str, start: int) -> tuple[int, int]:
    left_candidates = [text.rfind(mark, 0, start) for mark in (".", "!", "?", "\n")]
    left = max(left_candidates) + 1
    right_candidates = [idx for idx in (text.find(mark, start) for mark in (".", "!", "?", "\n")) if idx != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return left, right


def _is_negated_non_claim_occurrence(text: str, phrase: str, start: int) -> bool:
    """Return true when a forbidden phrase appears only as an explicit non-claim.

    The benchmark forbids affirmative claims such as "sent to users". It should not
    fail a proof-boundary sentence like "does not claim ... sent to users".
    """
    left, right = _sentence_bounds(text, start)
    sentence_prefix = text[left:start].lower()
    sentence = text[left:right].lower()
    phrase_l = phrase.lower()
    return phrase_l in sentence and any(pattern in sentence_prefix for pattern in NEGATED_NON_CLAIM_PATTERNS)


def _forbidden_phrase_hits(text: str, phrases: list[str]) -> tuple[list[str], list[str]]:
    found: list[str] = []
    ignored_negated: list[str] = []
    lowered = text.lower()
    for phrase in phrases:
        phrase_l = phrase.lower()
        if not phrase_l:
            continue
        start = 0
        phrase_found = False
        phrase_ignored = False
        while True:
            idx = lowered.find(phrase_l, start)
            if idx == -1:
                break
            if _is_negated_non_claim_occurrence(text, phrase, idx):
                phrase_ignored = True
            else:
                phrase_found = True
            start = idx + max(len(phrase_l), 1)
        if phrase_found:
            found.append(phrase)
        elif phrase_ignored:
            ignored_negated.append(phrase)
    return found, ignored_negated


def evaluate_expectations(
    *,
    step: dict[str, Any],
    reply: AgentReply,
    before_turn_count: int,
    after_turn_count: int,
    after_state: dict[str, Any],
    stage_message_count: int,
    app_repo: Path | None = None,
) -> list[dict[str, Any]]:
    raw_expect = step.get("expect")
    expect: dict[str, Any] = raw_expect if isinstance(raw_expect, dict) else {}
    checks: list[dict[str, Any]] = []
    text = reply.text

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    if reply.source == "live_hermes":
        cap_hits = [marker for marker in LIVE_ADAPTER_CAP_MARKERS if marker.lower() in text.lower()]
        add("live_adapter_completed_without_turn_cap", not cap_hits, "found=" + json.dumps(cap_hits))

    for key in ("reply_contains_all", "contains_all"):
        if isinstance(expect.get(key), list):
            missing = [str(item) for item in expect[key] if str(item) not in text]
            add(key, not missing, "missing=" + json.dumps(missing))
    for key in ("reply_contains_any", "contains_any"):
        if isinstance(expect.get(key), list):
            values = [str(item) for item in expect[key]]
            add(key, any(item in text for item in values), "options=" + json.dumps(values))
    raw_not_contains = expect.get("reply_not_contains_any")
    if isinstance(raw_not_contains, list):
        values = [str(item) for item in raw_not_contains]
        found, ignored_negated = _forbidden_phrase_hits(text, values)
        detail = "found=" + json.dumps(found)
        if ignored_negated:
            detail += " ignored_negated=" + json.dumps(ignored_negated)
        add("reply_not_contains_any", not found, detail)
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
    if isinstance(expect.get("app_repo_required_files"), list):
        required_files = [str(item) for item in expect["app_repo_required_files"]]
        missing: list[str] = []
        unsafe: list[str] = []
        if app_repo is None:
            missing = required_files
        else:
            for item in required_files:
                rel = Path(item)
                if rel.is_absolute() or ".." in rel.parts:
                    unsafe.append(item)
                    continue
                candidate = app_repo / rel
                if candidate.is_symlink():
                    unsafe.append(item)
                    continue
                try:
                    candidate.resolve().relative_to(app_repo.resolve())
                except ValueError:
                    unsafe.append(item)
                    continue
                if not candidate.is_file():
                    missing.append(item)
        detail = "missing=" + json.dumps(missing)
        if unsafe:
            detail += " unsafe=" + json.dumps(unsafe)
        add("app_repo_required_files", not missing and not unsafe, detail)
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
            evaluation = runtime.complete_evaluation_from_latest_artifact(
                root,
                app_id,
                step["stage"],
                reviewer="scripted-user-runner-local-evaluator",
                run_gates=True,
            )
            results.append({"action": "complete_evaluation", "result": evaluation})
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


def effective_step_timeout(*, step: dict[str, Any], default_timeout: int, mode: str, agent_name: str) -> int:
    """Return the timeout used for an adapter call while preserving configured intent.

    Live Hermes turns can need enough wall-clock to read lifecycle artifacts,
    create local files, and produce calibrated proof-boundary analysis. The
    default keeps only the analysis-stage floor for backwards compatibility;
    benchmark loops may set WEAVE_LIVE_HERMES_STEP_TIMEOUT_SECONDS to apply a
    broader live-Hermes floor across stages.
    """
    configured = int(step.get("timeout_seconds") or default_timeout)
    if mode == "live" and agent_name == "hermes-cli":
        stage = str(step.get("stage") or "")
        general_floor = int(os.environ.get("WEAVE_LIVE_HERMES_STEP_TIMEOUT_SECONDS", "0"))
        analysis_floor = int(os.environ.get("WEAVE_LIVE_HERMES_ANALYSIS_TIMEOUT_SECONDS", "360")) if stage == "analysis" else 0
        floor = max(general_floor, analysis_floor)
        if floor > 0:
            return max(configured, floor)
    return configured


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
    configured_timeout = int(step.get("timeout_seconds") or default_timeout)
    timeout = effective_step_timeout(step=step, default_timeout=default_timeout, mode=mode, agent_name=adapter.name)
    cwd_role = str(step.get("cwd") or "weave_root")
    cwd = app_repo if cwd_role == "app_repo" else root
    cwd.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(scenario=scenario, app_id=app_id, app_name=app_name, step=step, root=root, app_repo=app_repo)
    reply = adapter.reply(scenario=scenario, step=step, prompt=prompt, cwd=cwd, timeout=timeout)
    validate_agent_reply_source_for_mode(mode, reply.source)
    artifact_ref = write_step_artifact(
        root=root,
        app_id=app_id,
        step_index=step_index,
        step=step,
        reply=reply,
        expectations=[
            {
                "name": "pending_post_turn_expectation_evaluation",
                "passed": True,
                "detail": "final expectation results are written after the conversation turn is appended",
            }
        ],
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
            "to_state": "ready_for_review",
            "reason": "scripted user turn received a generated/captured agent reply",
        },
        next_action=str(step.get("next_action") or "Evaluate scenario predicates and branch."),
    )
    appended = runtime.append_conversation_turn(root, app_id, turn)
    after_turns = runtime.read_conversation_turns(root, app_id)
    after_stage_count = stage_turn_count(root, app_id, step["stage"])
    post_turn_state = runtime.app_state(root, app_id)
    pre_post_expectations = evaluate_expectations(
        step=step,
        reply=reply,
        before_turn_count=len(before_turns),
        after_turn_count=len(after_turns),
        after_state=post_turn_state,
        stage_message_count=after_stage_count,
        app_repo=app_repo,
    )
    state_expectation_names = {"stage_in", "stage_state_in"}
    non_state_passed = all(item["passed"] for item in pre_post_expectations if item["name"] not in state_expectation_names)
    post_actions = apply_post_actions(root, app_id, step) if non_state_passed else []
    final_state = runtime.app_state(root, app_id)
    expectations = evaluate_expectations(
        step=step,
        reply=reply,
        before_turn_count=len(before_turns),
        after_turn_count=len(after_turns),
        after_state=final_state,
        stage_message_count=after_stage_count,
        app_repo=app_repo,
    )
    artifact_ref = write_step_artifact(
        root=root,
        app_id=app_id,
        step_index=step_index,
        step=step,
        reply=reply,
        expectations=expectations,
        artifact_slug="expectations",
    )
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
        "configured_timeout_seconds": configured_timeout,
        "effective_timeout_seconds": timeout,
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
    raw_app_config = scenario.get("app")
    app_config: dict[str, Any] = raw_app_config if isinstance(raw_app_config, dict) else {}
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
    pending_failure: dict[str, Any] | None = None
    terminal_reason = "completed"
    step_results: list[dict[str, Any]] = []
    branch_history: list[dict[str, Any]] = []
    next_step_is_recovery = False

    while index < len(steps):
        if executed >= max_executed_steps:
            passed = False
            terminal_reason = f"max_executed_steps exceeded: {max_executed_steps}"
            break
        step = steps[index]
        entered_as_recovery = next_step_is_recovery
        next_step_is_recovery = False
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
        except SourceModeError as exc:
            result = {
                "label": step["label"],
                "stage": step["stage"],
                "status": "source_mode_violation",
                "error": str(exc),
            }
            action = "abort"
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
        if result["status"] == "passed":
            if pending_failure is None or entered_as_recovery:
                pending_failure = None
        else:
            pending_failure = result
        branch_kind, target = resolve_action(action, labels=labels, current_index=index)
        if branch_kind == "abort":
            passed = False
            terminal_reason = f"aborted at {step['label']}: {result['status']}"
            break
        if branch_kind == "stop":
            if pending_failure is not None:
                passed = False
                terminal_reason = (
                    f"stopped after unrecovered {pending_failure['status']} at {pending_failure['label']}"
                )
            else:
                terminal_reason = f"stopped at {step['label']}"
            break
        if target is None:
            raise ScenarioError(f"Branch action produced no target: {action}")
        if result["status"] != "passed" and str(action).strip().startswith("goto:"):
            next_step_is_recovery = True
        index = target

    if passed and pending_failure is not None:
        passed = False
        terminal_reason = f"completed with unrecovered {pending_failure['status']} at {pending_failure['label']}"

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
        "explicit_non_claims": explicit_non_claims_for_adapter(adapter.name),
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
    scenarios: list[tuple[Path, dict[str, Any]]] = []
    for raw_path in args.scenario:
        path = Path(raw_path)
        scenario = load_json(path)
        validate_scenario_schema(scenario, path)
        scenarios.append((path, scenario))
    tasks: list[tuple[Path, dict[str, Any], int]] = []
    run_index = 1
    for path, scenario in scenarios:
        for _ in range(args.repeat):
            tasks.append((path, scenario, run_index))
            run_index += 1
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(run_scenario_instance, scenario=scenario, scenario_path=path, args=args, run_id=run_id, run_index=index): (
                path,
                scenario,
                index,
            )
            for path, scenario, index in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            path, scenario, index = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                sid = scenario_id(scenario)
                raw_app_config = scenario.get("app")
                app_config: dict[str, Any] = raw_app_config if isinstance(raw_app_config, dict) else {}
                app_id_template = str(app_config.get("id_template") or f"{sid}-{{run_index}}")
                app_name_template = str(app_config.get("name_template") or scenario.get("app_name") or sid.replace("-", " ").title())
                app_id = runtime.slugify(render_template(app_id_template, scenario_id=sid, run_id=run_id, run_index=index))
                results.append(
                    {
                        "scenario_id": sid,
                        "scenario_path": str(path),
                        "run_index": index,
                        "app_id": app_id,
                        "app_name": render_template(app_name_template, scenario_id=sid, run_id=run_id, run_index=index),
                        "scenario_dir": str(output_root / f"{sid}-{index}"),
                        "report": str(output_root / f"{sid}-{index}" / "scenario-report.json"),
                        "passed": False,
                        "terminal_reason": str(exc),
                        "error_type": type(exc).__name__,
                    }
                )
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
        "explicit_non_claims": explicit_non_claims_for_adapter(args.agent),
    }
    write_json(output_root / "aggregate-report.json", aggregate)
    return aggregate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", action="append", required=True, help="Path to a JSON scenario file. Repeatable.")
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture", help="Declared proof mode.")
    parser.add_argument(
        "--agent",
        choices=("fixture", "hermes-cli", "deployed-gateway"),
        default="fixture",
        help="Agent adapter to use.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for run artifacts.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--repeat", type=int, default=1, help="Number of instances to run per scenario.")
    parser.add_argument("--parallel", type=int, default=1, help="Max parallel scenario instances.")
    parser.add_argument("--timeout", type=int, default=120, help="Default seconds per agent reply.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scenario output directories for this run id.")
    parser.add_argument("--hermes-bin", default=os.environ.get("WEAVE_HERMES_BIN", "hermes"))
    parser.add_argument("--model", default=os.environ.get("WEAVE_HERMES_MODEL", "gpt-5.5"))
    parser.add_argument("--provider", default=os.environ.get("WEAVE_HERMES_PROVIDER_ADAPTER", "codex"))
    parser.add_argument(
        "--max-turns",
        type=int,
        default=int(os.environ.get("WEAVE_HERMES_MAX_TURNS", "12")),
        help="Hermes CLI internal max turns per scripted user message; live app-writing proof needs enough turns to create and verify files.",
    )
    parser.add_argument("--no-yolo", dest="yolo", action="store_false", help="Disable Hermes --yolo/--accept-hooks for live app-writing runs.")
    parser.add_argument(
        "--gateway-command",
        default=os.environ.get("WEAVE_DEPLOYED_GATEWAY_ADAPTER_CMD", ""),
        help="Owner-approved deployed gateway adapter command. Receives JSON on stdin and returns JSON on stdout.",
    )
    parser.add_argument(
        "--allow-external-send",
        action="store_true",
        help="Required for --agent deployed-gateway because real target-surface proof may send/read Telegram messages.",
    )
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
    if args.mode == "fixture" and args.agent != "fixture":
        parser.error("--mode fixture requires --agent fixture")
    if args.agent == "deployed-gateway":
        if args.mode != "live":
            parser.error("--agent deployed-gateway requires --mode live")
        if not args.allow_external_send:
            parser.error("--agent deployed-gateway requires --allow-external-send owner approval")
        if not str(args.gateway_command).strip():
            parser.error("--agent deployed-gateway requires --gateway-command or WEAVE_DEPLOYED_GATEWAY_ADAPTER_CMD")
    try:
        report = run_all(args)
    except Exception as exc:
        print(f"scripted-user/live-agent runner failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"passed": report["passed"], "run_id": report["run_id"], "output_root": report["output_root"]}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
