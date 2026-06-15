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
import shlex
import shutil
import subprocess
import sys
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
CODEX_PROOF_SCHEMA = "weave-codex-adapter-proof/v0.1"
SEO_ARTIFACT_SCHEMA = "weave-seo-artifact/v0.1"
DEFAULT_APP_SURFACE = "website"
APP_SURFACES = ("website", "cli", "backend", "api", "mixed")
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
SAFE_CODEX_PROBE_ARGS = {("--version",), ("-V",), ("--help",), ("help",)}
REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_MODE_ALIASES = {
    "hands-on": "hands-on",
    "hands-off": "hands-off",
    "handoff": "hands-off",
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


def write_engineering_markdown(inputs: TuiInputs, codex_proof: dict[str, Any]) -> str:
    seo_line = "Website SEO checklist and QA are included." if inputs.app_surface == "website" else "SEO is not applicable to this primary surface."
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
            "- Create or update local files only.",
            "- Keep credentials, provider auth, deployment, public sends, and paid spend gated.",
            "- Record proof artifacts before asking the owner to accept the stage.",
            f"- {seo_line}",
            "",
            "## Codex Adapter Boundary",
            "",
            f"- Local Codex metadata proof status: {codex_proof['status']}",
            "- Live model execution is not claimed in this v1 local-safe smoke.",
            "- A future adapter can replace this metadata proof with an approved invoke/capture bridge.",
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

    scaffold_path = eng_dir / "local-implementation-scaffold.md"
    scaffold_text = write_engineering_markdown(inputs, codex_proof)
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
        "summary": f"scaffold ready, eval {evaluation_decision}, Codex proof {codex_proof['status']}",
        "artifact_refs": [rel(scaffold_path, root), rel(codex_path, root), *seo_refs],
        "codex_status": codex_proof["status"],
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
        "claims": ["TUI v1 exercised the local lifecycle through QA"],
        "non_claims": ["not deployed", "not live marketing", "not live Codex model invocation", "not provider-auth proof"],
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

    qa_args = module_args(
        args,
        inputs,
        surface=QA_SURFACE_BY_APP_SURFACE[inputs.app_surface],
        qa_command=args.qa_command,
        target_label=f"local {inputs.app_surface} proof",
        create_app=False,
    )
    steps.append(run_lifecycle_module("QA proof", weave_qa_proof.run, qa_args))
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
    lines = [
        render_intro(inputs, palette),
        "",
        render_step_table(step_results, palette),
        "",
        palette.paint("Proof boundary", "bold", "magenta"),
        "  external_effects_executed: none",
        "  stopped_before: credentials, deployment, public sends, paid spend, raw secret handling",
        "  Codex v1: local CLI metadata proof only; live invoke/capture remains unproven",
    ]
    if inputs.app_surface == "website":
        seo_state = "checklist and local QA artifact written" if manifest else "checklist and local QA artifact will be written"
        lines.extend([f"  SEO: {seo_state}"])
    if manifest:
        lines.extend(["", palette.paint("Written", "bold", "green"), f"  tui_manifest: {manifest['manifest_ref']}"])
    else:
        lines.extend(["", palette.paint("Next", "bold", "cyan"), "  rerun with --write to create local WEAVE state and QA proof"])
    return "\n".join(lines) + "\n"


def run(args: Any, *, input_stream: TextIO = sys.stdin, output: TextIO = sys.stdout) -> int:
    palette = Palette(color_enabled(args, output))
    try:
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
