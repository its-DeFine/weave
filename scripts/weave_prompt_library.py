#!/usr/bin/env python3
"""WEAVE prompt library and prompt packet assembly.

This module is deliberately standard-library only. The Textual UI and Codex
executor should depend on this layer instead of hardcoding prompt text in UI
widgets or process wrappers.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import weave_runtime_slice


PROMPT_LIBRARY_SCHEMA = "weave/prompt-library/v1"
PROMPT_PACKET_SCHEMA = "weave/prompt-packet/v1"
OWNER_FEEDBACK_SCHEMA = "weave/owner-feedback/v1"
STAGE_HANDOFF_SCHEMA = "weave/stage-handoff/v1"

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY_PATH = REPO_ROOT / "prompts" / "weave" / "prompt-library.v1.json"
DEFAULT_GLOBAL_PRELUDE_PATH = REPO_ROOT / "prompts" / "weave" / "global" / "prelude.v1.md"

STAGE_DIRECTORIES = {
    "first_run": "00-first-run",
    "first-run": "00-first-run",
    "owner_profile": "00-owner-profile",
    "owner-profile": "00-owner-profile",
    "app": "00-app",
    "intent": "01-intent",
    "research": "02-research",
    "selection": "03-selection",
    "plan": "04-plan",
    "engineering": "05-engineering",
    "qa": "06-qa",
    "deployment": "07-deployment",
    "kpi": "08-kpi",
    "marketing": "09-marketing",
    "iteration": "10-iteration",
    "analysis": "11-analysis",
    "completion": "12-completion",
}

DEFAULT_STAGE_FOR_PROMPT = "intent"


class PromptLibraryError(Exception):
    """Raised when the prompt library or a prompt packet is invalid."""


@dataclass(frozen=True)
class PromptTemplate:
    stage: str
    substage: str
    worker_role: str
    owner_visible_goal: str
    required_context: tuple[str, ...]
    required_outputs: tuple[str, ...]
    text: str

    @property
    def prompt_ref(self) -> str:
        return f"prompt://weave/stages/{self.stage}/{self.substage}/v1"


def normalize_stage(value: str | None) -> str:
    stage = str(value or DEFAULT_STAGE_FOR_PROMPT).strip().lower().replace("-", "_")
    aliases = {
        "first": "first_run",
        "first_run": "first_run",
        "first-run": "first_run",
        "owner": "owner_profile",
        "owner-profile": "owner_profile",
        "select": "selection",
        "engineer": "engineering",
        "deploy": "deployment",
        "market": "marketing",
        "iterate": "iteration",
        "analyze": "analysis",
    }
    return aliases.get(stage, stage)


def normalize_substage(value: str | None) -> str:
    return str(value or "start").strip().lower().replace("-", "_")


def prompt_packet_stage_dir(root: Path, app_id: str, stage: str) -> Path:
    clean_stage = normalize_stage(stage)
    directory = STAGE_DIRECTORIES.get(clean_stage)
    if not directory:
        raise PromptLibraryError(f"unsupported prompt stage: {stage}")
    return weave_runtime_slice.app_root(root, app_id) / "lifecycle" / directory / "artifacts" / "prompt-packets"


def load_prompt_library(path: Path | None = None) -> dict[str, Any]:
    library_path = path or DEFAULT_LIBRARY_PATH
    try:
        data = json.loads(library_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromptLibraryError(f"prompt library not found: {library_path}") from exc
    except json.JSONDecodeError as exc:
        raise PromptLibraryError(f"invalid prompt library JSON: {exc}") from exc
    validate_prompt_library(data)
    return data


def load_global_prelude(path: Path | None = None) -> str:
    prelude_path = path or DEFAULT_GLOBAL_PRELUDE_PATH
    try:
        text = prelude_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PromptLibraryError(f"global prelude not found: {prelude_path}") from exc
    ensure_public_safe("global prelude", text)
    return text


def ensure_public_safe(label: str, value: Any) -> None:
    if weave_runtime_slice.contains_secret_like_value(value):
        raise PromptLibraryError(f"{label} contains secret-looking content")
    if contains_private_locator_for_prompt(value):
        raise PromptLibraryError(f"{label} contains private locator content")


PRIVATE_PROMPT_LOCATOR_RE = re.compile(
    r"(^|[\s\"'`=({\[,;])(?:/|~(?:/|$)|[A-Za-z]:[\\/])|"
    r"\bfile:(?://)?|"
    r"\b(?:localhost|127\.\d{1,3}\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b",
    re.IGNORECASE,
)


def contains_private_locator_for_prompt(value: Any) -> bool:
    """Reject private locations while allowing public artifact refs.

    Prompt packets intentionally contain repo-relative refs such as
    `lifecycle/intent/artifacts/intent.md`. Those are public-safe and necessary
    for traceability, so this guard only rejects absolute/local/private
    locations and private-network names.
    """

    if isinstance(value, str):
        text = value.strip()
        if PRIVATE_PROMPT_LOCATOR_RE.search(text):
            return True
        lowered = text.lower()
        return any(suffix in lowered for suffix in (".local", ".localhost", ".lan", ".internal", ".home.arpa"))
    if isinstance(value, dict):
        return any(contains_private_locator_for_prompt(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_private_locator_for_prompt(item) for item in value)
    return False


def validate_prompt_library(data: dict[str, Any]) -> None:
    if data.get("schema") != PROMPT_LIBRARY_SCHEMA:
        raise PromptLibraryError(f"prompt library schema must be {PROMPT_LIBRARY_SCHEMA}")
    if not data.get("version"):
        raise PromptLibraryError("prompt library version is required")
    if not data.get("global_prelude_ref"):
        raise PromptLibraryError("prompt library global_prelude_ref is required")
    stages = data.get("stages")
    if not isinstance(stages, dict) or not stages:
        raise PromptLibraryError("prompt library stages must be a non-empty object")
    for stage_id, stage in stages.items():
        validate_stage_definition(str(stage_id), stage)
    ensure_public_safe("prompt library", data)


def validate_stage_definition(stage_id: str, stage: Any) -> None:
    if not isinstance(stage, dict):
        raise PromptLibraryError(f"stage {stage_id} must be an object")
    for field in ("worker_role", "owner_visible_goal", "required_context", "subprompts", "required_outputs"):
        if field not in stage:
            raise PromptLibraryError(f"stage {stage_id} missing {field}")
    if not isinstance(stage["required_context"], list):
        raise PromptLibraryError(f"stage {stage_id} required_context must be a list")
    if not isinstance(stage["required_outputs"], list) or not stage["required_outputs"]:
        raise PromptLibraryError(f"stage {stage_id} required_outputs must be a non-empty list")
    subprompts = stage["subprompts"]
    if not isinstance(subprompts, dict) or not subprompts:
        raise PromptLibraryError(f"stage {stage_id} subprompts must be a non-empty object")
    for substage, prompt in subprompts.items():
        if not str(substage).strip():
            raise PromptLibraryError(f"stage {stage_id} has empty substage")
        if not isinstance(prompt, str) or len(prompt.strip()) < 20:
            raise PromptLibraryError(f"stage {stage_id}/{substage} prompt is too short")


def stage_definition(stage: str, *, library: dict[str, Any] | None = None) -> dict[str, Any]:
    data = library or load_prompt_library()
    clean_stage = normalize_stage(stage)
    stages = data["stages"]
    if clean_stage not in stages:
        raise PromptLibraryError(f"unknown prompt stage: {stage}")
    return stages[clean_stage]


def prompt_template(stage: str, substage: str, *, library: dict[str, Any] | None = None) -> PromptTemplate:
    clean_stage = normalize_stage(stage)
    clean_substage = normalize_substage(substage)
    definition = stage_definition(clean_stage, library=library)
    subprompts = definition["subprompts"]
    if clean_substage not in subprompts:
        available = ", ".join(sorted(subprompts))
        raise PromptLibraryError(f"unknown substage {stage}/{substage}; available: {available}")
    return PromptTemplate(
        stage=clean_stage,
        substage=clean_substage,
        worker_role=str(definition["worker_role"]),
        owner_visible_goal=str(definition["owner_visible_goal"]),
        required_context=tuple(str(item) for item in definition["required_context"]),
        required_outputs=tuple(str(item) for item in definition["required_outputs"]),
        text=str(subprompts[clean_substage]),
    )


def prompt_library_summary(path: Path | None = None) -> dict[str, Any]:
    data = load_prompt_library(path)
    stages = data["stages"]
    return {
        "schema": "weave/prompt-library-summary/v1",
        "version": data["version"],
        "stage_count": len(stages),
        "prompt_count": sum(len(stage["subprompts"]) for stage in stages.values()),
        "stages": {
            stage_id: {
                "worker_role": stage["worker_role"],
                "subprompts": sorted(stage["subprompts"]),
                "required_outputs": stage["required_outputs"],
            }
            for stage_id, stage in sorted(stages.items())
        },
        "global_prelude_ref": data["global_prelude_ref"],
    }


def stable_packet_id(payload: dict[str, Any]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()[:16]
    return f"prompt-{payload['stage']}-{payload['substage']}-{digest}"


def render_prompt_markdown(packet: dict[str, Any], *, global_prelude: str, template: PromptTemplate) -> str:
    owner_message = packet.get("latest_owner_message") or "(none provided)"
    feedback = packet.get("feedback") or {}
    feedback_text = json.dumps(feedback, indent=2, sort_keys=True) if feedback else "(none)"
    context_lines = "\n".join(f"- {ref}" for ref in packet.get("selected_context_refs", [])) or "- none"
    input_lines = "\n".join(f"- {ref}" for ref in packet.get("input_refs", [])) or "- none"
    output_lines = "\n".join(f"- {item}" for item in packet.get("required_outputs", [])) or "- none"
    stop_lines = "\n".join(f"- {item}" for item in packet.get("stop_boundaries", [])) or "- none"
    return f"""# WEAVE Prompt Packet

Packet: {packet['packet_id']}
App: {packet['app_id']}
Stage: {packet['stage']}
Substage: {packet['substage']}
Worker role: {template.worker_role}

## 1. Global WEAVE Prelude

{global_prelude.strip()}

## 2. Current Worker Role

You are the WEAVE {template.worker_role}. Your owner-visible goal is:
{template.owner_visible_goal}

## 3. Stage/Substage Instruction

{template.text}

## 4. Owner Profile

{packet.get('owner_profile_summary') or 'No owner profile artifact is available yet.'}

## 5. App World Model

{packet.get('world_model_summary') or 'No world model summary is available yet.'}

## 6. Prior Artifacts To Read

{input_lines}

## 7. Selected Context References

{context_lines}

## 8. Latest Owner Input

{owner_message}

## 9. Structured Feedback

```json
{feedback_text}
```

## 10. Required Outputs

{output_lines}

## 11. Gate Criteria

{', '.join(packet.get('gate_criteria', [])) or 'Stage-specific gate criteria must be evaluated honestly.'}

## 12. Stop Boundaries

{stop_lines}

## 13. Response Format

Return a short owner-readable summary. Write or update the required artifacts.
Separate claims from non-claims and identify the next review choice.
"""


def build_feedback(
    *,
    app_id: str,
    stage: str,
    owner_text: str,
    target_type: str = "stage",
    target_ref: str = "",
    feedback_class: str = "preference",
) -> dict[str, Any]:
    feedback = {
        "schema": OWNER_FEEDBACK_SCHEMA,
        "feedback_id": stable_feedback_id(app_id, stage, owner_text, target_type, target_ref),
        "app_id": weave_runtime_slice.slugify(app_id),
        "stage": normalize_stage(stage),
        "target_type": target_type,
        "target_ref": target_ref,
        "owner_text": owner_text,
        "feedback_class": feedback_class,
        "created_at": weave_runtime_slice.utc_now(),
        "public_safe": True,
    }
    ensure_public_safe("owner feedback", feedback)
    return feedback


def stable_feedback_id(app_id: str, stage: str, owner_text: str, target_type: str, target_ref: str) -> str:
    material = {
        "app_id": weave_runtime_slice.slugify(app_id),
        "stage": normalize_stage(stage),
        "owner_text": owner_text,
        "target_type": target_type,
        "target_ref": target_ref,
    }
    digest = hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return f"fb-{digest}"


def build_prompt_packet(
    *,
    root: Path,
    app_id: str,
    stage: str,
    substage: str,
    latest_owner_message: str = "",
    input_refs: list[str] | None = None,
    selected_context_refs: list[str] | None = None,
    owner_profile_summary: str = "",
    world_model_summary: str = "",
    feedback: dict[str, Any] | None = None,
    executor: str = "codex",
    reason: str = "",
    allowed_actions: list[str] | None = None,
    forbidden_actions: list[str] | None = None,
    gate_criteria: list[str] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    weave_runtime_slice.load_app(root, app_id)
    library = load_prompt_library()
    template = prompt_template(stage, substage, library=library)
    global_prelude = load_global_prelude()
    stop_boundaries = [str(item) for item in library.get("default_stop_boundaries", [])]
    payload = {
        "schema": PROMPT_PACKET_SCHEMA,
        "packet_id": "",
        "app_id": weave_runtime_slice.slugify(app_id),
        "stage": template.stage,
        "substage": template.substage,
        "created_at": weave_runtime_slice.utc_now(),
        "executor": executor,
        "reason": reason or f"{template.stage}/{template.substage} agent action requested",
        "global_prelude_ref": library["global_prelude_ref"],
        "stage_prompt_ref": template.prompt_ref,
        "worker_role": template.worker_role,
        "owner_visible_goal": template.owner_visible_goal,
        "required_context": list(template.required_context),
        "required_outputs": list(template.required_outputs),
        "input_refs": input_refs or [],
        "selected_context_refs": selected_context_refs or [],
        "latest_owner_message": latest_owner_message,
        "owner_profile_summary": owner_profile_summary,
        "world_model_summary": world_model_summary,
        "feedback": feedback or {},
        "allowed_actions": allowed_actions or ["write_artifacts", "summarize", "ask_clarifying_questions"],
        "forbidden_actions": forbidden_actions
        or ["deploy", "public_send", "paid_spend", "read_raw_secrets", "destructive_change"],
        "stop_boundaries": stop_boundaries,
        "gate_criteria": gate_criteria or ["required_outputs_exist", "public_safe", "owner_review_ready"],
        "claims": ["prompt packet assembled from versioned WEAVE prompt library"],
        "non_claims": ["does not prove agent execution", "does not prove stage completion"],
        "public_safe": True,
        "secret_value_printed": False,
    }
    payload["packet_id"] = stable_packet_id(payload)
    ensure_public_safe("prompt packet", payload)
    rendered = render_prompt_markdown(payload, global_prelude=global_prelude, template=template)
    ensure_public_safe("rendered prompt packet", rendered)
    if write:
        packet_dir = prompt_packet_stage_dir(root, app_id, template.stage)
        packet_dir.mkdir(parents=True, exist_ok=True)
        json_path = packet_dir / f"{payload['packet_id']}.json"
        md_path = packet_dir / f"{payload['packet_id']}.md"
        payload["packet_ref"] = weave_runtime_slice.relative(json_path, root)
        payload["rendered_prompt_ref"] = weave_runtime_slice.relative(md_path, root)
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(rendered, encoding="utf-8")
        weave_runtime_slice.append_event(
            root,
            app_id,
            weave_runtime_slice.new_event(
                "artifact.created",
                app_id,
                template.stage if template.stage in weave_runtime_slice.stage_ids() else "intent",
                f"Prompt packet prepared for {template.stage}/{template.substage}.",
                payload={"prompt_packet": payload["packet_ref"], "rendered_prompt": payload["rendered_prompt_ref"]},
                artifact_refs=[
                    {"path": payload["packet_ref"], "stage": template.stage},
                    {"path": payload["rendered_prompt_ref"], "stage": template.stage},
                ],
            ),
        )
    return payload


def build_stage_handoff(
    *,
    app_id: str,
    from_stage: str,
    to_stage: str,
    summary: str,
    approved_artifact_refs: list[str],
    must_preserve: list[str] | None = None,
    open_questions: list[str] | None = None,
    capability_requirements: list[str] | None = None,
    stop_boundaries: list[str] | None = None,
) -> dict[str, Any]:
    handoff = {
        "schema": STAGE_HANDOFF_SCHEMA,
        "from_stage": normalize_stage(from_stage),
        "to_stage": normalize_stage(to_stage),
        "app_id": weave_runtime_slice.slugify(app_id),
        "summary": summary,
        "must_preserve": must_preserve or [],
        "approved_artifact_refs": approved_artifact_refs,
        "open_questions": open_questions or [],
        "capability_requirements": capability_requirements or [],
        "stop_boundaries": stop_boundaries or load_prompt_library().get("default_stop_boundaries", []),
        "next_worker_role": stage_definition(to_stage)["worker_role"],
        "public_safe": True,
    }
    ensure_public_safe("stage handoff", handoff)
    return handoff
