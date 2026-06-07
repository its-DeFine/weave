#!/usr/bin/env python3
"""Run a live Hermes-backed WEAVE lifecycle QA proof.

This is intentionally separate from lifecycle_rehearsal_smoke.py. The rehearsal
smoke is deterministic runtime coverage. This runner requires an installed
Hermes executable and fails if Hermes does not produce the stage replies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import weave_runtime_slice as runtime


APP_ID = "lantern-archive-live"
APP_NAME = "Lantern Archive Live Proof"
APP_INTENT = (
    "Lantern Archive is a small browser visual novel where a visitor helps a "
    "keeper restore lost memories into lantern cards. The proof should feel like "
    "an actual product slice, work locally without a backend, expose restored "
    "cards and exportable state, and keep hosting, analytics, and paid story "
    "packs gated until the owner supplies credentials and approval."
)
REQUIRED_APP_FILES = ("index.html", "styles.css", "app.js", "README.md")


OWNER_STAGE_MESSAGES = {
    "intent": (
        "I want to create Lantern Archive, a tiny but finished browser visual "
        "novel. The first playable slice should have an opening scene, a keeper "
        "character, memory cards, meaningful choices, local progress, exportable "
        "state, and a future paid story-pack path. No real payments, public "
        "launch, analytics, or credential collection should happen in this local proof."
    ),
    "research": (
        "Before choosing the build shape, research what would make Lantern "
        "Archive viable as a static first slice. I care about emotional specificity, "
        "reviewable evidence, local QA, and what must stay gated before launch."
    ),
    "selection": (
        "Choose the smallest implementation direction that still feels like a "
        "real product, not a placeholder. Say what you reject and why."
    ),
    "plan": (
        "Give me the implementation plan. Include files, user flows, QA checks, "
        "credentials needed later, stop boundaries, and what you will not claim."
    ),
    "engineering": (
        "Implement the first playable local app in the current working directory. "
        "Create index.html, styles.css, app.js, and README.md. The app should be "
        "usable in a browser, have scene progression, restored memory cards, "
        "local state or export, and a visibly disabled future paid-pack path. "
        "Do not use network services, external secrets, or real payments."
    ),
    "qa": (
        "QA the app as a reviewer would. Use the current source files as evidence. "
        "Separate what is proven locally from what is not proven."
    ),
    "kpi": (
        "Define the KPI and measurement plan for Lantern Archive. Identify what "
        "can be checked locally and what needs analytics credentials later."
    ),
    "marketing": (
        "Create the first marketing and launch-readiness plan. Keep public sends, "
        "hosting, analytics, and payments gated behind owner approval and credentials."
    ),
    "iteration": (
        "Assume the first owner QA feedback is: the story needs clearer emotional "
        "payoff, the restored cards should feel more collectible, and the disabled "
        "paid-pack path must not look like a broken checkout. Propose the iteration."
    ),
    "analysis": (
        "Analyze the end-to-end lifecycle result. Say whether this can be reviewed "
        "as a month-one proof, what remains blocked, and the next decision."
    ),
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def clip_for_prompt(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head_chars = max_chars // 2
    tail_chars = max_chars - head_chars
    return (
        text[:head_chars].rstrip()
        + "\n\n[...draft clipped for follow-up prompt; full draft is preserved in the transcript artifact...]\n\n"
        + text[-tail_chars:].lstrip()
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def stage_artifact_path(root: Path, stage_id: str, revision: str = "final") -> Path:
    stage = runtime.stage_by_id(stage_id)
    return (
        runtime.app_root(root, APP_ID)
        / "lifecycle"
        / stage.directory
        / "artifacts"
        / f"{stage_id}-{revision}-live-hermes.md"
    )


def setup_clean_runtime(root: Path, model: str, provider: str, reasoning_effort: str) -> None:
    created = runtime.create_app(root, APP_ID, APP_NAME)
    base = runtime.app_root(root, APP_ID)
    write_text(
        root / "artifacts" / "general" / "soul.md",
        """
        # Hermes Soul For Live Proof

        Act as a careful product operator and creative engineering partner. Do
        not move lifecycle stages unless the stage artifact, transcript turn,
        and owner-review gate are present. Ask for missing information when it
        is genuinely blocking. Keep launch, credentials, and public effects
        gated.
        """,
    )
    write_text(
        root / "artifacts" / "general" / "owner-profile.md",
        """
        # Owner Profile For Live Proof

        The owner wants real app substance, not only runtime mechanics. They
        prefer direct evidence, clean state, readable artifacts, no overclaiming,
        and explicit separation between local proof, mocked capability, and live
        deployment.
        """,
    )
    write_text(
        base / "context" / "app-context.md",
        f"""
        # App Context

        {APP_INTENT}
        """,
    )
    write_text(
        base / "context" / "user-context-for-this-app.md",
        """
        # User Context For This App

        The user wants a short, polished product proof that can be inspected by
        reviewers. The app should be emotionally specific and easy to review locally.
        """,
    )
    write_text(
        base / "context" / "domain-context.md",
        """
        # Domain Context

        The domain is small narrative web apps and visual-novel prototypes.
        Proof quality depends on story clarity, interaction, browser reliability,
        and honest boundaries around future monetization.
        """,
    )
    write_text(
        base / "inventory" / "app-inventory.md",
        """
        # App Inventory

        - Product app workspace
        - Static source under repo/primary
        - Lifecycle artifacts under lifecycle/*
        - Conversation review under exports/conversation
        """,
    )
    write_text(
        base / "contract" / "gestaltian-contract.md",
        """
        # Gestaltian Contract

        Lantern Archive must progress through intent, research, selection, plan,
        engineering, QA, KPI, marketing, iteration, and analysis. Each stage needs
        a live Hermes transcript turn, stage artifact, gate check, and owner
        approval before advancement.
        """,
    )
    app = runtime.load_app(root, APP_ID)
    app["credential_requirements"] = [
        {
            "id": "hosting-provider",
            "label": "Hosting provider access",
            "stages": ["marketing", "analysis"],
            "required": True,
            "status": "missing",
        },
        {
            "id": "analytics-provider",
            "label": "Analytics provider access",
            "stages": ["kpi", "analysis"],
            "required": True,
            "status": "missing",
        },
        {
            "id": "payment-provider",
            "label": "Payment provider access",
            "stages": ["marketing", "analysis"],
            "required": True,
            "status": "missing",
        },
    ]
    runtime.write_app(root, app)
    profile = runtime.default_agent_profile(root)
    profile["model"] = model
    profile["provider_adapter"] = provider
    profile["reasoning_effort"] = reasoning_effort
    profile["recorded_at"] = runtime.utc_now()
    profile["profile_hash"] = runtime.profile_hash(profile)
    runtime.write_agent_profile(root, profile)
    runtime.append_event(
        root,
        APP_ID,
        runtime.new_event(
            "foundation.completed",
            APP_ID,
            "intent",
            "Live proof foundation context was populated before lifecycle work.",
            payload={"created_paths": created["created"]},
        ),
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


def run_hermes(
    *,
    hermes_bin: Path,
    prompt: str,
    cwd: Path,
    model: str,
    provider: str,
    max_turns: int,
    timeout: int,
    yolo: bool,
) -> dict[str, Any]:
    command = [
        str(hermes_bin),
        "chat",
        "--quiet",
        "--source",
        "tool",
        "--max-turns",
        str(max_turns),
        "--model",
        model,
        "--provider",
        provider,
    ]
    if yolo:
        command.extend(["--yolo", "--accept-hooks"])
    command.extend(["--query", prompt])
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    elapsed = round(time.monotonic() - started, 3)
    parsed = parse_hermes_stdout(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(
            "Hermes invocation failed for live QA. "
            f"returncode={result.returncode}; stderr_sha256={sha256_text(result.stderr)}"
        )
    if not parsed["reply"]:
        raise RuntimeError("Hermes invocation returned no reviewable reply text.")
    return {
        "reply": parsed["reply"],
        "session_id": parsed["session_id"],
        "stdout_sha256": sha256_text(result.stdout),
        "stderr_sha256": sha256_text(result.stderr),
        "elapsed_seconds": elapsed,
        "returncode": result.returncode,
        "command_shape": "hermes chat --quiet --source tool --max-turns N --model MODEL --provider PROVIDER --query PROMPT",
    }


def build_stage_prompt(stage_id: str, root: Path, app_repo: Path, prior_summary: str) -> str:
    current_state = runtime.app_state(root, APP_ID)
    gate = runtime.stage_gate_status(root, APP_ID, stage_id)
    owner_message = OWNER_STAGE_MESSAGES[stage_id]
    engineering_instruction = ""
    if stage_id == "engineering":
        engineering_instruction = f"""
        Keep this stage reply concise. Do not output full source code here.
        After this stage reply, WEAVE will ask you for the four source files in
        smaller live Hermes file-generation calls and will write those exact
        outputs to:
        {app_repo}

        In this reply, state the implementation approach, file list, proof
        behavior, local QA checks, and gated non-goals.
        """
    return textwrap.dedent(
        f"""
        You are Hermes operating inside a clean WEAVE lifecycle proof run.

        Application: {APP_NAME}
        Intent: {APP_INTENT}
        Current lifecycle stage: {stage_id}
        Current runtime gate passed before your reply: {gate["passed"]}
        Current runtime gate missing items: {gate["missing"]}
        Prior lifecycle summary:
        {prior_summary or "No prior stage summary yet."}

        Owner/operator message:
        {owner_message}

        {engineering_instruction}

        Response budget:
        - Keep the whole reply under 900 words.
        - Keep Artifact content reviewable: concise sections, no exhaustive
          file trees, no repeated lifecycle history.
        - For plan, name only the first-slice files the WEAVE runtime will create:
          index.html, styles.css, app.js, and README.md.
        - If more detail would be useful later, put it under Deferred items or
          Next action instead of expanding this turn.

        Reply in a reviewable operational format with these headings:

        Hermes reply
        Owner-reviewable rationale
        Gate questions
        Missing information
        Decision basis
        Artifact content
        Next action

        Rules:
        - Do not include hidden chain-of-thought.
        - Do not write files, edit JSONL ledgers, call transcript-capture tools,
          or append lifecycle state yourself. The WEAVE runtime will capture
          your reply, write the stage artifact, and append the transcript turn.
        - Do not invent live credentials, live users, revenue, analytics, public
          deploys, or payment processing.
        - If something is blocked, name the exact blocker and what should happen.
        - If the stage can proceed to owner review, say why in concrete terms.
        - Keep the response specific to Lantern Archive, not generic WEAVE work.

        Runtime state snapshot for your context:
        {json.dumps({"stage": current_state["stage_status"], "foundation_gate": current_state["foundation_gate"]}, indent=2, sort_keys=True)}
        """
    ).strip()


def write_stage_artifact(
    root: Path,
    stage_id: str,
    hermes_result: dict[str, Any],
    *,
    revision: str,
    extra: str = "",
) -> Path:
    path = stage_artifact_path(root, stage_id, revision)
    body = f"""# {stage_id.title()} Live Hermes Artifact

Source: live_hermes
Revision: {revision}
Session: {hermes_result.get("session_id") or "not-reported"}
Stdout checksum: {hermes_result["stdout_sha256"]}

## Hermes Reply

{hermes_result["reply"]}
"""
    if extra.strip():
        body += f"\n## Deterministic Verification\n\n{extra.strip()}\n"
    write_text(path, body)
    runtime.append_event(
        root,
        APP_ID,
        runtime.new_event(
            "artifact.created" if revision == "draft" else "artifact.updated",
            APP_ID,
            stage_id,
            f"Recorded {stage_id} {revision} live Hermes artifact.",
            created_by="hermes",
            payload={
                "source": "live_hermes",
                "revision": revision,
                "session_id": hermes_result.get("session_id", ""),
                "stdout_sha256": hermes_result["stdout_sha256"],
            },
            artifact_refs=[{"path": runtime.relative(path, root), "action": "created"}],
        ),
    )
    return path


def build_stage_completion_prompt(
    *,
    stage_id: str,
    draft_reply: str,
    stage_extra: str,
    prior_summary: str,
) -> str:
    extra = stage_extra.strip() or "No deterministic side-effect or verification output was needed for this stage."
    draft_excerpt = clip_for_prompt(draft_reply, 10000)
    return textwrap.dedent(
        f"""
        You are still Hermes working on the same WEAVE lifecycle stage.

        Application: {APP_NAME}
        Stage: {stage_id}
        Prior lifecycle summary:
        {prior_summary or "No prior stage summary yet."}

        Your draft response excerpt for this stage was:
        {draft_excerpt}

        Runtime or implementation evidence now available:
        {extra}

        Owner/operator follow-up:
        Do not advance yet. First complete this lifecycle stage properly. Review
        your draft, identify the recommendations or gaps you created, then either
        implement them, mark them as intentionally deferred with a concrete reason,
        or ask a blocking question if completion is impossible. For this proof
        run, avoid blocking unless a real secret, public action, or external
        credential is required.

        Response budget:
        - Keep the whole completion reply under 700 words.
        - Do not repeat the full draft artifact.
        - Summarize which recommendations were handled, deferred, or blocked.

        Reply in the same reviewable operational format with these headings:

        Hermes reply
        Owner-reviewable rationale
        Gate questions
        Missing information
        Decision basis
        Artifact content
        Recommendations handled
        Deferred items
        Next action

        Rules:
        - Do not include hidden chain-of-thought.
        - Do not write files, edit JSONL ledgers, call transcript-capture tools,
          or append lifecycle state yourself. The WEAVE runtime will capture
          your reply, write the final stage artifact, and append the transcript
          turn.
        - Do not invent live credentials, live users, revenue, analytics, public
          deploys, or payment processing.
        - Keep the response specific to Lantern Archive.
        - The stage is only ready for owner review if the stage artifact and
          transcript now show what was done, what was verified, and what remains
          gated.
        """
    ).strip()


def extract_named_files(reply: str) -> dict[str, str]:
    files: dict[str, str] = {}
    pattern = re.compile(
        r"FILE:\s*(?P<name>index\.html|styles\.css|app\.js|README\.md)\s*"
        r"```[^\n`]*\n(?P<body>.*?)\n```",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(reply):
        name = match.group("name")
        canonical = next(item for item in REQUIRED_APP_FILES if item.lower() == name.lower())
        body = match.group("body").strip()
        if body:
            files[canonical] = body + "\n"
    return files


def write_live_generated_files(app_repo: Path, files: dict[str, str]) -> dict[str, Any]:
    written: dict[str, dict[str, Any]] = {}
    for name, content in files.items():
        if name not in REQUIRED_APP_FILES:
            continue
        path = app_repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written[name] = {
            "bytes": path.stat().st_size,
            "sha256": runtime.artifact_checksum(path),
            "source": "live_hermes_named_code_block",
        }
    return written


def strip_single_code_fence(text: str) -> str:
    cleaned = text.strip()
    match = re.fullmatch(r"```[^\n`]*\n(?P<body>.*?)\n```", cleaned, flags=re.DOTALL)
    if match:
        return match.group("body").strip() + "\n"
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[^\n`]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip() + "\n"


def build_file_generation_prompt(file_name: str) -> str:
    shared = (
        "Generate exactly one file for the Lantern Archive static browser app. "
        "Return only raw file content, no explanations and no surrounding fences. "
        "Do not write files or edit WEAVE ledgers yourself; the WEAVE runtime writes "
        "the exact content you return. "
        "No network calls, no external secrets, no real payments. The app is a "
        "local proof visual novel with scene progression, restored memory cards, "
        "exportable local state, and a disabled future paid-pack path. Export is "
        "required; import state is out of scope unless you fully implement it. "
        "Future paid/story-pack controls must remain non-interactive and disabled: "
        "no click handler, no paid-click counter, no checkout-like action, and no "
        "runtime code that sets a paid control disabled=false."
    )
    if file_name == "index.html":
        return (
            shared
            + " File: index.html. Include semantic HTML, references to styles.css and app.js, "
            "main app regions, buttons, memory-card area, export area, and disabled paid-pack section. "
            "Keep it under 180 lines."
        )
    if file_name == "styles.css":
        return (
            shared
            + " File: styles.css. Create a polished readable product UI, responsive layout, "
            "button states, card styling, disabled paid-pack styling, and no external font imports. "
            "Keep it under 220 lines."
        )
    if file_name == "app.js":
        return (
            shared
            + " File: app.js. Implement deterministic scenes, choices, restored memory cards, "
            "localStorage progress, export JSON, reset, simple KPI counters, and disabled paid-pack behavior. "
            "Do not restore any memory card before an explicit visitor choice/action. "
            "Keep it compact under 180 lines. Prefer simple arrays and functions over framework-style structure."
        )
    if file_name == "README.md":
        return (
            shared
            + " File: README.md. Document local open/run instructions, app behavior, lifecycle proof boundary, "
            "disabled monetization, local-only KPI proof, and credentials required before real launch. "
            "Keep it under 120 lines."
        )
    raise ValueError(f"unsupported file: {file_name}")


def build_compact_file_generation_prompt(file_name: str) -> str:
    return (
        f"Return only raw {file_name} content for a minimal static browser proof called "
        "Lantern Archive. No explanations, no fences, no network, no secrets, no real "
        "payments. Keep it short but functional. It must fit with index.html, "
        "styles.css, app.js, and README.md. Include disabled future paid-pack behavior "
        "where relevant."
    )


def generate_engineering_files(
    *,
    hermes_bin: Path,
    app_repo: Path,
    model: str,
    provider: str,
    max_turns: int,
    timeout: int,
    yolo: bool,
) -> dict[str, Any]:
    generated: dict[str, dict[str, Any]] = {}
    for file_name in REQUIRED_APP_FILES:
        try:
            result = run_hermes(
                hermes_bin=hermes_bin,
                prompt=build_file_generation_prompt(file_name),
                cwd=app_repo,
                model=model,
                provider=provider,
                max_turns=max_turns,
                timeout=timeout,
                yolo=yolo,
            )
        except subprocess.TimeoutExpired:
            result = run_hermes(
                hermes_bin=hermes_bin,
                prompt=build_compact_file_generation_prompt(file_name),
                cwd=app_repo,
                model=model,
                provider=provider,
                max_turns=max_turns,
                timeout=timeout,
                yolo=yolo,
            )
        content = strip_single_code_fence(result["reply"])
        write_live_generated_files(app_repo, {file_name: content})
        path = app_repo / file_name
        generated[file_name] = {
            "source": "live_hermes_file_generation",
            "stdout_sha256": result["stdout_sha256"],
            "session_id": result.get("session_id", ""),
            "bytes": path.stat().st_size,
            "sha256": runtime.artifact_checksum(path),
        }
    return generated


def append_live_turn(
    *,
    root: Path,
    stage_id: str,
    owner_message: str,
    hermes_result: dict[str, Any],
    artifact_path: Path,
    model: str,
    provider: str,
    reasoning_effort: str,
    turn_kind: str,
    to_state: str,
    next_action: str,
    rationale_summary: str,
) -> dict[str, Any]:
    before_gate = runtime.stage_gate_status(root, APP_ID, stage_id)
    gate_checks = {
        "foundation_gate_passed": bool(before_gate.get("foundation_gate", {}).get("passed")),
        "stage_gate_passed_before_turn": bool(before_gate.get("passed")),
        "stage_gate_missing_before_turn": before_gate.get("missing", []),
        "stage_gate_warnings_before_turn": before_gate.get("warnings", []),
        "transcript_capture_passed_before_turn": bool(before_gate.get("transcript_capture", {}).get("passed")),
        "transcript_capture_missing_before_turn": before_gate.get("transcript_capture", {}).get("missing", []),
        "artifact_created_for_turn": artifact_path.exists(),
        "owner_review_required": True,
    }
    turn = runtime.new_conversation_turn(
        APP_ID,
        stage_id,
        {
            "role": "owner",
            "source": "qa_owner_emulation",
            "captured_by": "scripts/live_hermes_lifecycle_qa.py",
            "turn_kind": turn_kind,
            "text": owner_message,
        },
        {
            "role": "hermes",
            "source": "live_hermes",
            "model": model,
            "provider": provider,
            "reasoning_effort": reasoning_effort,
            "session_id": hermes_result.get("session_id", ""),
            "captured_by": "scripts/live_hermes_lifecycle_qa.py",
            "turn_kind": turn_kind,
            "raw_stdout_sha256": hermes_result["stdout_sha256"],
            "elapsed_seconds": hermes_result["elapsed_seconds"],
            "text": hermes_result["reply"],
        },
        channel="direct-hermes-cli",
        created_by="hermes",
        agent_rationale={
            "summary": rationale_summary,
            "gate_questions": [
                "Did live Hermes answer this lifecycle-stage owner message?",
                "Was a current-stage artifact created from that answer?",
                "Can the deterministic gate be reviewed before approval?",
            ],
            "missing_information": before_gate["missing"],
            "decision_basis": [
                "live Hermes response captured",
                "stage artifact written",
                "runtime gate evaluated",
            ],
            "chain_of_thought_captured": False,
        },
        gate_checks=gate_checks,
        artifact_refs=[{"path": runtime.relative(artifact_path, root), "action": "created"}],
        state_transition={
            "from_stage": stage_id,
            "from_state": "collecting",
            "to_stage": stage_id,
            "to_state": "ready_for_review",
            "initiated_by": "hermes",
            "reason": rationale_summary,
        },
        next_action=next_action,
    )
    turn["state_transition"]["to_state"] = to_state
    return runtime.append_conversation_turn(root, APP_ID, turn)


def verify_engineering_files(app_repo: Path) -> dict[str, Any]:
    files = {}
    missing = []
    for name in REQUIRED_APP_FILES:
        path = app_repo / name
        if path.exists() and path.is_file() and path.stat().st_size > 0:
            files[name] = {
                "bytes": path.stat().st_size,
                "sha256": runtime.artifact_checksum(path),
            }
        else:
            missing.append(name)
    return {"passed": not missing, "missing": missing, "files": files}


def run_app_verification(app_repo: Path) -> dict[str, Any]:
    checks: dict[str, Any] = {"schema": "weave-live-app-verification/v0.1"}
    engineering = verify_engineering_files(app_repo)
    checks["required_files"] = engineering
    index = (app_repo / "index.html").read_text(encoding="utf-8") if (app_repo / "index.html").exists() else ""
    styles = (app_repo / "styles.css").read_text(encoding="utf-8") if (app_repo / "styles.css").exists() else ""
    script = (app_repo / "app.js").read_text(encoding="utf-8") if (app_repo / "app.js").exists() else ""
    readme = (app_repo / "README.md").read_text(encoding="utf-8") if (app_repo / "README.md").exists() else ""
    checks["html_refs"] = {
        "styles_css": "styles.css" in index,
        "app_js": "app.js" in index,
    }
    checks["product_terms"] = {
        "lantern": "lantern" in (index + styles + script + readme).lower(),
        "memory": "memory" in (index + styles + script + readme).lower(),
        "export": "export" in (index + script + readme).lower(),
        "paid_pack_disabled": "disabled" in (index + script + readme).lower() and "paid" in (index + script + readme).lower(),
    }
    paid_enable_patterns = [
        r"\$\(\s*['\"]#paid['\"]\s*\)\.disabled\s*=\s*false",
        r"getElementById\(\s*['\"]paid['\"]\s*\)\.disabled\s*=\s*false",
        r"querySelector\(\s*['\"]#paid['\"]\s*\)\.disabled\s*=\s*false",
        r"\bpaid(?:Button|Btn|Control|El|Element)?\.disabled\s*=\s*false",
    ]
    paid_control_enabled = any(re.search(pattern, script) for pattern in paid_enable_patterns)
    paid_click_counter = bool(re.search(r"\bpaidClicks\b", script))
    index_import_control = bool(
        re.search(r"\b(id|for|name)=['\"][^'\"]*import", index, re.IGNORECASE)
        or re.search(r"<button[^>]*>\s*import\b", index, re.IGNORECASE)
        or re.search(r"<textarea[^>]*\bimport\b", index, re.IGNORECASE)
    )
    readme_import_promise = bool(re.search(r"\bimport\b", readme, re.IGNORECASE)) and not bool(
        re.search(r"import(?:ing)?[^.\n]{0,100}out of scope", readme, re.IGNORECASE)
        or re.search(r"out of scope[^.\n]{0,100}import", readme, re.IGNORECASE)
    )
    import_runtime = bool(re.search(r"\bimport(?:State|Archive|Json|JSON)\b", script))
    initial_restore_before_action = bool(
        re.search(r"function\s+render[^{]*\{[\s\S]{0,1800}\brestore\([^)]*scene\.card[^)]*\)", script)
        or re.search(r"\brender\s*=\s*\([^)]*\)\s*=>\s*\{[\s\S]{0,1800}\brestore\([^)]*scene\.card[^)]*\)", script)
    )
    checks["runtime_boundaries"] = {
        "paid_control_remains_disabled": not paid_control_enabled,
        "paid_click_counter_absent": not paid_click_counter,
        "import_not_advertised_without_runtime": not (index_import_control or readme_import_promise) or import_runtime,
        "no_initial_restore_before_action_pattern": not initial_restore_before_action,
    }
    try:
        result = subprocess.run(
            ["node", "--check", str(app_repo / "app.js")],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        checks["javascript_syntax"] = {
            "passed": result.returncode == 0,
            "returncode": result.returncode,
            "stderr_sha256": sha256_text(result.stderr),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        checks["javascript_syntax"] = {
            "passed": False,
            "error": exc.__class__.__name__,
        }
    checks["passed"] = (
        engineering["passed"]
        and all(checks["html_refs"].values())
        and all(checks["product_terms"].values())
        and all(checks["runtime_boundaries"].values())
        and bool(checks["javascript_syntax"].get("passed"))
    )
    return checks


def approve_and_advance(root: Path, stage_id: str) -> dict[str, Any]:
    defer = stage_id in {"kpi", "marketing", "analysis"}
    approval = runtime.approve_stage(
        root,
        APP_ID,
        stage_id,
        note="Live proof owner-emulation approval after reviewing stage artifact.",
        defer_capability=defer,
        defer_reason="Credential capability intentionally deferred in the local live proof; no public launch or live measurement is in scope.",
    )
    if not approval.get("approved"):
        raise RuntimeError(f"Stage approval failed for {stage_id}: {approval.get('gate', {}).get('missing')}")
    if runtime.next_stage_id(stage_id) is None:
        return {"approval": approval, "advance": {"advanced": False, "reason": "final_stage"}}
    advance = runtime.advance_stage(root, APP_ID, note="Live proof advanced after owner-emulated approval.")
    if not advance.get("advanced"):
        raise RuntimeError(f"Stage advance failed for {stage_id}: {advance}")
    return {"approval": approval, "advance": advance}


def copy_tree_snapshot(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def run_live_qa(args: argparse.Namespace) -> dict[str, Any]:
    hermes_bin = Path(args.hermes_bin).expanduser()
    if not hermes_bin.exists():
        raise RuntimeError(f"Hermes executable does not exist: {hermes_bin}")
    run_id = args.run_id or f"{utc_timestamp()}-live-hermes-lifecycle"
    report_dir = Path(args.report_dir).expanduser() / run_id
    root = report_dir / "weave-root"
    if report_dir.exists() and not args.force:
        raise RuntimeError(f"Report directory already exists: {report_dir}")
    if report_dir.exists():
        shutil.rmtree(report_dir)
    app_repo = root / "apps" / APP_ID / "repo" / "primary"
    report_dir.mkdir(parents=True, exist_ok=True)
    setup_clean_runtime(root, args.model, args.provider, args.reasoning_effort)

    stage_reports: list[dict[str, Any]] = []
    prior_summary = ""
    for stage_id in runtime.stage_ids():
        prompt = build_stage_prompt(stage_id, root, app_repo, prior_summary)
        max_turns = args.engineering_max_turns if stage_id == "engineering" else args.max_turns
        cwd = app_repo if stage_id == "engineering" else root
        draft_result = run_hermes(
            hermes_bin=hermes_bin,
            prompt=prompt,
            cwd=cwd,
            model=args.model,
            provider=args.provider,
            max_turns=max_turns,
            timeout=args.timeout,
            yolo=args.yolo,
        )
        draft_artifact_path = write_stage_artifact(root, stage_id, draft_result, revision="draft")
        draft_turn = append_live_turn(
            root=root,
            stage_id=stage_id,
            owner_message=OWNER_STAGE_MESSAGES[stage_id],
            hermes_result=draft_result,
            artifact_path=draft_artifact_path,
            model=args.model,
            provider=args.provider,
            reasoning_effort=args.reasoning_effort,
            turn_kind="stage_draft",
            to_state="in_progress",
            next_action="Owner-emulated follow-up asks Hermes to resolve recommendations, implement work, or defer blockers before review.",
            rationale_summary="Live Hermes produced a draft stage response; the stage remains in progress until follow-up completion.",
        )
        stage_extra = ""
        deterministic_work: dict[str, Any] = {}
        if stage_id == "engineering":
            generated_files = generate_engineering_files(
                hermes_bin=hermes_bin,
                app_repo=app_repo,
                model=args.model,
                provider=args.provider,
                max_turns=args.max_turns,
                timeout=args.timeout,
                yolo=args.yolo,
            )
            verification = verify_engineering_files(app_repo)
            if not verification["passed"]:
                raise RuntimeError(f"Engineering files missing after live Hermes run: {verification['missing']}")
            deterministic_work = {
                "file_write_source": "WEAVE wrote exact contents from live Hermes file-generation replies.",
                "generated_files": generated_files,
                "verification": verification,
            }
            stage_extra = json.dumps(deterministic_work, indent=2, sort_keys=True)
        elif stage_id == "qa":
            deterministic_work = {"local_app_verification": run_app_verification(app_repo)}
            if not deterministic_work["local_app_verification"]["passed"]:
                raise RuntimeError(
                    "Local app verification failed before QA completion: "
                    + json.dumps(deterministic_work["local_app_verification"], sort_keys=True)
                )
            stage_extra = json.dumps(deterministic_work, indent=2, sort_keys=True)

        completion_prompt = build_stage_completion_prompt(
            stage_id=stage_id,
            draft_reply=draft_result["reply"],
            stage_extra=stage_extra,
            prior_summary=prior_summary,
        )
        completion_result = run_hermes(
            hermes_bin=hermes_bin,
            prompt=completion_prompt,
            cwd=cwd,
            model=args.model,
            provider=args.provider,
            max_turns=max_turns,
            timeout=args.timeout,
            yolo=args.yolo,
        )
        final_artifact_path = write_stage_artifact(root, stage_id, completion_result, revision="final", extra=stage_extra)
        completion_turn = append_live_turn(
            root=root,
            stage_id=stage_id,
            owner_message=(
                "Follow up on your draft for this lifecycle stage. Implement, verify, "
                "ask, or explicitly defer the recommendations and gaps before owner review."
            ),
            hermes_result=completion_result,
            artifact_path=final_artifact_path,
            model=args.model,
            provider=args.provider,
            reasoning_effort=args.reasoning_effort,
            turn_kind="stage_completion",
            to_state="ready_for_review",
            next_action="Owner reviews the completed stage artifact, then the runtime may approve and advance if gates pass.",
            rationale_summary="Live Hermes completed the stage follow-up and linked the final stage artifact for owner review.",
        )
        gate_after_turn = runtime.stage_gate_status(root, APP_ID, stage_id)
        transition = approve_and_advance(root, stage_id)
        stage_reports.append(
            {
                "stage": stage_id,
                "draft_turn_id": draft_turn["turn_id"],
                "completion_turn_id": completion_turn["turn_id"],
                "draft_session_id": draft_result.get("session_id", ""),
                "completion_session_id": completion_result.get("session_id", ""),
                "draft_artifact": runtime.relative(draft_artifact_path, root),
                "final_artifact": runtime.relative(final_artifact_path, root),
                "gate_after_turn": gate_after_turn,
                "transition": transition,
                "draft_stdout_sha256": draft_result["stdout_sha256"],
                "completion_stdout_sha256": completion_result["stdout_sha256"],
                "deterministic_work": deterministic_work,
            }
        )
        prior_summary = (
            prior_summary
            + f"\n- {stage_id}: draft_turn={draft_turn['turn_id']}; completion_turn={completion_turn['turn_id']}; "
            + f"artifact={runtime.relative(final_artifact_path, root)}; "
            + f"session={completion_result.get('session_id') or 'not-reported'}"
        )

    export = runtime.export_conversation_review(root, APP_ID)
    final_state = runtime.app_state(root, APP_ID)
    app_snapshot = report_dir / "app-source-snapshot"
    copy_tree_snapshot(app_repo, app_snapshot)
    qa_report = {
        "schema": "weave-live-hermes-lifecycle-qa/v0.1",
        "run_id": run_id,
        "created_at": runtime.utc_now(),
        "reply_source_requirement": "Every Hermes reply in the transcript must have agent_reply.source=live_hermes.",
        "runtime_root": str(root),
        "app_id": APP_ID,
        "app_name": APP_NAME,
        "model": args.model,
        "provider": args.provider,
        "reasoning_effort": args.reasoning_effort,
        "hermes_bin_exists": hermes_bin.exists(),
        "conversation_turn_model": "multi-turn per lifecycle stage: draft turn, work/verification, completion turn, then approval",
        "max_turns_note": "Hermes --max-turns controls internal tool iterations per model call; it is not the number of owner/Hermes messages allowed per lifecycle stage.",
        "hermes_max_turns_per_call": args.max_turns,
        "stage_count": len(stage_reports),
        "stage_reports": stage_reports,
        "conversation_review": export,
        "final_stage": final_state["stage_status"],
        "engineering_files": verify_engineering_files(app_repo),
        "app_source_snapshot": str(app_snapshot),
    }
    qa_report_path = report_dir / "qa-report.json"
    write_text(qa_report_path, json.dumps(qa_report, indent=2, sort_keys=True))
    return {
        "run_id": run_id,
        "report_dir": str(report_dir),
        "qa_report": str(qa_report_path),
        "review_html": str(root / export["exports"]["html_review"]),
        "conversation_events": str(root / export["exports"]["event_stream"]),
        "app_source_snapshot": str(app_snapshot),
        "stage_count": len(stage_reports),
        "turn_count": export["turn_count"],
        "source_summary": export["source_summary"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-bin", default=os.environ.get("WEAVE_HERMES_BIN", "hermes"))
    parser.add_argument("--report-dir", default=str(Path.home() / "Documents" / "Codex" / "artifacts" / "weave-runtime-proof"))
    parser.add_argument("--run-id", default="")
    parser.add_argument("--model", default=os.environ.get("WEAVE_HERMES_MODEL", "gpt-5.5"))
    parser.add_argument("--provider", default=os.environ.get("WEAVE_HERMES_PROVIDER_ADAPTER", "codex"))
    parser.add_argument("--reasoning-effort", default=os.environ.get("WEAVE_HERMES_REASONING_EFFORT", "xhigh"))
    parser.add_argument("--max-turns", type=int, default=4)
    parser.add_argument("--engineering-max-turns", type=int, default=4)
    parser.add_argument("--repair-attempts", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-yolo", dest="yolo", action="store_false")
    parser.set_defaults(yolo=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_live_qa(args)
    except Exception as exc:
        print(f"live Hermes lifecycle QA failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
