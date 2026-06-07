#!/usr/bin/env python3
"""Run a deterministic WEAVE lifecycle rehearsal and write a proof artifact.

The rehearsal uses an isolated temporary WEAVE root. It does not contact
Telegram, Hermes, external providers, live runtimes, or networks. It exercises
the same deterministic command dispatcher that Telegram and REST wrappers use.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import weave_runtime_slice as runtime


DEFAULT_REPORT_DIR = Path.home() / "Documents" / "Codex" / "artifacts" / "weave-lifecycle-rehearsals"
APP_ID = "lantern-archive"
APP_NAME = "Lantern Archive"
APP_INTENT = (
    "Build a small, polished browser visual novel where a visitor helps a keeper "
    "restore lost memories into lantern cards. The app should feel emotionally "
    "specific, be easy to QA locally, work without a backend, and leave a clear "
    "future path for paid story packs without taking real payments during QA."
)

FOUNDATION_DOCS = {
    "soul": (
        "Hermes should act like a careful product operator and creative director: "
        "first clarify the human intent, then move through lifecycle gates with "
        "evidence, visible tradeoffs, and owner review before stage movement."
    ),
    "owner": (
        "The owner wants concrete application substance, not only runtime mechanics. "
        "They prefer direct evidence, clean state, strong UX thinking, and no claim "
        "that a lifecycle is complete unless the artifact shows the actual work."
    ),
    "app_context": (
        f"{APP_NAME} is a proof app for the WEAVE lifecycle. It is a browser-based "
        "micro visual novel with a memory-restoration loop, scene cards, local "
        "progress, exportable JSON, KPI estimates, and a disabled monetization "
        "surface that can be enabled only after owner-approved credentials exist."
    ),
    "inventory": (
        "Expected inventory: static web source, story engine, visual scene layout, "
        "local QA proof, KPI model, marketing draft, feedback iteration note, "
        "and analysis of what would be required before monetized launch."
    ),
    "contract": (
        "The app must progress in order through intent, research, selection, plan, "
        "engineering, qa, kpi, marketing, iteration, and analysis. Each stage needs "
        "a stage artifact, transcript turn, owner approval, and deterministic gate "
        "state before advancement."
    ),
}

STAGE_SCRIPTS = {
    "intent": {
        "title": "Intent Brief",
        "artifact_body": (
            f"Owner intent: {APP_INTENT}\n\n"
            "Success means the proof feels like an actual application concept, not "
            "a placeholder, and the transcript shows why this app should exist."
        ),
        "owner": (
            "I want to build a tiny but finished browser visual novel called "
            "Lantern Archive. A visitor should help a keeper restore lost memories "
            "into lantern cards. It should feel gentle, inspectable, and monetizable "
            "later through paid story packs, but for now no real payments or public "
            "launch. What do you need before we move forward?"
        ),
        "hermes": (
            "I understand the app as a concrete visual novel proof, not a generic "
            "demo. I have enough to form the intent contract: target user, emotional "
            "promise, non-backend constraint, local QA boundary, and deferred "
            "monetization path are all explicit. I will keep payments and public "
            "launch gated."
        ),
        "rationale": (
            "The owner supplied a named app, audience experience, constraints, and "
            "launch boundary. The intent stage can move to review once the intent "
            "brief is recorded."
        ),
        "questions": [
            "Is the app named and emotionally specific?",
            "Are launch and payment boundaries explicit?",
            "Is there enough context to research a viable shape?",
        ],
        "basis": ["named app intent", "local-only QA boundary", "monetization deferred"],
    },
    "research": {
        "title": "Research Notes",
        "artifact_body": (
            "Research conclusion: a static browser app can support the intended "
            "visual novel proof with local state, deterministic scenes, exportable "
            "JSON, and a disabled checkout path. Main risks are shallow story "
            "writing, unclear replay value, and overstating monetization before "
            "real validation."
        ),
        "owner": (
            "Research this properly before we choose the build shape. I care that "
            "Lantern Archive feels like a small real product: an opening scene, "
            "choices, restored memory cards, export/share value, and a later paid "
            "pack path. What should we learn and what would make this viable?"
        ),
        "hermes": (
            "Research points to a static-first app: no backend for the proof, local "
            "scene state, a generated memory-card inventory, export JSON for review, "
            "and a visible but disabled paid-pack callout. The viability test is "
            "whether the first session creates enough emotional completion and a "
            "clear next-pack desire. I would not choose a complex auth or database "
            "path for this slice."
        ),
        "rationale": (
            "The research stage identifies a simple technical shape, product risk, "
            "and monetization boundary. It gives enough evidence to select the first "
            "implementation direction."
        ),
        "questions": [
            "Can the proof work without backend infrastructure?",
            "What risk would make the app feel fake?",
            "What monetization path can be shown without taking payment?",
        ],
        "basis": ["static-first path", "local state sufficient", "paid pack path deferred"],
    },
    "selection": {
        "title": "Selection Decision",
        "artifact_body": (
            "Selected direction: static visual novel with a curated story engine, "
            "three memory cards, local progress, review export, and disabled paid "
            "pack configuration. Rejected: backend account system, generative API "
            "calls, and live checkout in this proof."
        ),
        "owner": (
            "Choose the smallest direction that still feels like a real app. I do "
            "not want a toy that only proves routing. I want the first playable "
            "slice of Lantern Archive to have a reason to exist."
        ),
        "hermes": (
            "I select a static, playable first slice: one keeper character, three "
            "recoverable memory cards, two meaningful choices, a completion state, "
            "and an exportable proof. This keeps the app inspectable while still "
            "expressing the product. I am rejecting live auth, live payments, and "
            "external AI calls for this lifecycle proof."
        ),
        "rationale": (
            "The selected approach balances emotional product quality with low QA "
            "surface area and clear blocked boundaries for credentials and launch."
        ),
        "questions": [
            "Does the chosen direction preserve the product feeling?",
            "Are rejected directions clearly documented?",
            "Is the slice small enough to QA end to end?",
        ],
        "basis": ["static playable slice", "backend rejected", "live payment rejected"],
    },
    "plan": {
        "title": "Implementation Plan",
        "artifact_body": (
            "Plan: create source files, implement scene progression, memory-card "
            "state, accessible controls, export JSON, KPI counters, disabled paid "
            "pack config, and local QA. Stop before public deploy or real provider "
            "credentials."
        ),
        "owner": (
            "Give me the plan before engineering. I want the plan to include what "
            "the app will contain, how it will be tested, what it will not do, and "
            "what credentials would be needed later."
        ),
        "hermes": (
            "The plan is: build the static app shell, implement the story engine, "
            "create a memory-card UI, add export and KPI surfaces, keep checkout "
            "disabled by config, and verify with local static, node, and browser "
            "checks. Later credentials would be hosting, analytics, and payment "
            "provider access, but those remain outside this QA run."
        ),
        "rationale": (
            "The plan is complete enough for engineering because it defines files, "
            "behavior, QA, non-goals, and credential boundaries."
        ),
        "questions": [
            "Are the expected app surfaces named?",
            "Are tests and stop boundaries explicit?",
            "Are future credentials identified without collecting them now?",
        ],
        "basis": ["file-level build plan", "QA plan", "credential boundary"],
    },
    "engineering": {
        "title": "Engineering Evidence",
        "artifact_body": (
            "Engineering evidence: source would include index.html, app.js, "
            "story-engine module, styles, config, and README. The app behavior "
            "should show progression, restored cards, export, and disabled "
            "monetization."
        ),
        "owner": (
            "Now implement the proof as if you care about it. It should not be a "
            "blank demo. I expect the first screen, scene progression, memory-card "
            "state, and a clearly disabled monetization path."
        ),
        "hermes": (
            "I would implement Lantern Archive as a static app with a full first "
            "session: opening scene, choice buttons, restored memory-card inventory, "
            "export JSON, and KPI counters. I would keep any `<paid-pack>` marker "
            "as inert display/config text until credentials and owner approval "
            "exist."
        ),
        "rationale": (
            "Engineering can proceed because the app surfaces and technical "
            "constraints are concrete, with public/payment actions still blocked."
        ),
        "questions": [
            "Does engineering produce an inspectable app surface?",
            "Does the disabled monetization path remain inert?",
            "Are app files and behavior tied to the product intent?",
        ],
        "basis": ["static app source", "memory-card interaction", "inert monetization marker"],
    },
    "qa": {
        "title": "QA Proof",
        "artifact_body": (
            "QA proof: verify required files, story progression, export schema, "
            "disabled checkout, layout readability, and local serving. Known gap: "
            "no live user evidence and no public deployment in this rehearsal."
        ),
        "owner": (
            "QA it like a reviewer will inspect it. I want to know what passed, "
            "what is still fake or mocked, and whether the app is good enough to "
            "show as a proof without overclaiming."
        ),
        "hermes": (
            "QA should pass only for local product proof claims: source exists, "
            "story progression works, export shape is inspectable, paid path is "
            "disabled, and the lifecycle evidence is linked. I will not claim live "
            "users, live revenue, or hosted production from this rehearsal."
        ),
        "rationale": (
            "The QA stage separates proven local app behavior from unproven market "
            "and hosted claims."
        ),
        "questions": [
            "Are local proof claims actually verified?",
            "Are unproven claims explicitly withheld?",
            "Is there enough evidence for owner QA review?",
        ],
        "basis": ["local proof only", "known gaps listed", "no hosted/revenue claim"],
    },
    "kpi": {
        "title": "KPI Setup",
        "artifact_body": (
            "KPI setup: track completion, restored-card count, export action, "
            "replay intent, paid-pack click intent, and qualitative feedback. "
            "Analytics credentials are missing and must be deferred or provided "
            "before real measurement."
        ),
        "owner": (
            "Set up the KPIs we would need before marketing. I want to know whether "
            "people finish the first story, care about the memory cards, export the "
            "result, and show intent for a paid pack."
        ),
        "hermes": (
            "The KPI model should track completion rate, restored-card count, export "
            "rate, replay intent, and paid-pack click intent. In this rehearsal the "
            "measurement is local and mocked; real analytics provider credentials "
            "are required before production measurement."
        ),
        "rationale": (
            "The KPI stage is ready for review only with credential deferral, because "
            "real analytics credentials are not present in this clean run."
        ),
        "questions": [
            "Are product-specific KPIs defined?",
            "Are analytics credentials treated as a gate?",
            "Is mocked measurement labeled honestly?",
        ],
        "basis": ["completion KPI", "export KPI", "analytics credential deferred"],
    },
    "marketing": {
        "title": "Marketing Draft",
        "artifact_body": (
            "Marketing draft: position Lantern Archive as a five-minute memory "
            "restoration visual novel for people who like quiet interactive fiction. "
            "No public send happens in the rehearsal."
        ),
        "owner": (
            "Draft the marketing logic, but do not send anything. I want to see the "
            "audience, promise, proof points, and what approvals or credentials are "
            "needed before distribution."
        ),
        "hermes": (
            "Marketing should target quiet interactive-fiction fans and creators "
            "who like personal archive themes. The promise is a five-minute story "
            "where choices restore memory cards. Distribution accounts, analytics, "
            "and public-send approval are required before any real campaign."
        ),
        "rationale": (
            "Marketing can be reviewed as a draft, but distribution remains blocked "
            "without credentials and explicit owner approval."
        ),
        "questions": [
            "Is the audience concrete?",
            "Is the promise tied to the product artifact?",
            "Are public sends blocked until approval?",
        ],
        "basis": ["audience defined", "positioning draft", "public send blocked"],
    },
    "iteration": {
        "title": "Iteration Note",
        "artifact_body": (
            "Mock feedback: the first scene needs a stronger emotional hook and the "
            "paid-pack hint should appear after completion, not before the visitor "
            "trusts the story. Proposed iteration: rewrite opening prompt and delay "
            "paid-pack copy."
        ),
        "owner": (
            "Pretend the first reviewer says the app is pretty but the opening scene "
            "does not yet make them care. Iterate from that feedback without losing "
            "the small-scope proof."
        ),
        "hermes": (
            "I would revise the opening to start with a specific lost memory, not a "
            "generic welcome. I would delay paid-pack language until after the third "
            "memory card is restored. This improves emotional trust without adding "
            "new infrastructure."
        ),
        "rationale": (
            "The iteration responds to product feedback while preserving the chosen "
            "static proof boundary."
        ),
        "questions": [
            "Is feedback specific enough to act on?",
            "Does the iteration preserve the proof scope?",
            "Does the change improve the product experience?",
        ],
        "basis": ["mock reviewer feedback", "opening rewrite", "paid-pack copy delayed"],
    },
    "analysis": {
        "title": "Outcome Analysis",
        "artifact_body": (
            "Analysis: the lifecycle can produce a coherent local app proof with "
            "reviewable evidence, but monetization is not proven until hosted app, "
            "analytics, payment credentials, and real user feedback are added."
        ),
        "owner": (
            "Analyze the outcome honestly. Can this become monetizable, what did we "
            "actually prove, and what is still missing before I should treat it as "
            "a real launch candidate?"
        ),
        "hermes": (
            "This run proves a coherent app concept, lifecycle gating, transcript "
            "review, and a path to monetization. It does not prove market demand, "
            "revenue, hosted performance, or payment setup. The next real step would "
            "be a hosted beta with analytics and owner-approved payment/provider "
            "credentials."
        ),
        "rationale": (
            "Analysis distinguishes product substance from launch proof and prevents "
            "the runtime from overstating monetization readiness."
        ),
        "questions": [
            "What did the lifecycle actually prove?",
            "What remains unproven before monetization?",
            "What is the next reviewable action?",
        ],
        "basis": ["local app proof", "market demand unproven", "hosted beta next"],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fill(path: Path, title: str, body: str = "Rehearsal evidence is complete.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\nStatus: complete\n\n{body}\n", encoding="utf-8")


def complete_foundation(root: Path, app_id: str) -> None:
    fill(root / "artifacts" / "general" / "soul.md", "Hermes Soul", FOUNDATION_DOCS["soul"])
    fill(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile", FOUNDATION_DOCS["owner"])
    fill(root / "apps" / app_id / "context" / "app-context.md", "App Context", FOUNDATION_DOCS["app_context"])
    fill(root / "apps" / app_id / "inventory" / "app-inventory.md", "App Inventory", FOUNDATION_DOCS["inventory"])
    fill(root / "apps" / app_id / "contract" / "gestaltian-contract.md", "Gestaltian Contract", FOUNDATION_DOCS["contract"])


def write_stage_artifact(root: Path, app_id: str, stage_id: str) -> Path:
    stage = runtime.stage_by_id(stage_id)
    path = root / "apps" / app_id / "lifecycle" / stage.directory / "artifacts" / f"{stage_id}-proof.md"
    script = STAGE_SCRIPTS[stage_id]
    fill(path, script["title"], script["artifact_body"])
    return path


def record_stage_turn(root: Path, app_id: str, stage_id: str, artifact_path: Path) -> dict[str, Any]:
    relative_artifact = runtime.relative(artifact_path, root)
    script = STAGE_SCRIPTS[stage_id]
    turn = runtime.new_conversation_turn(
        app_id,
        stage_id,
        {"role": "owner", "text": script["owner"]},
        {"role": "hermes", "text": script["hermes"]},
        agent_rationale={
            "summary": script["rationale"],
            "gate_questions": script["questions"],
            "missing_information": [],
            "decision_basis": [*script["basis"], f"stage artifact: {relative_artifact}", "foundation gate passed"],
            "chain_of_thought_captured": False,
        },
        artifact_refs=[{"path": relative_artifact, "action": "created"}],
        state_transition={
            "from_stage": stage_id,
            "from_state": "collecting",
            "to_stage": stage_id,
            "to_state": "ready_for_review",
            "initiated_by": "hermes",
            "reason": script["rationale"],
        },
        next_action=f"Owner reviews {APP_NAME} {stage_id} evidence, then may approve the stage.",
    )
    return runtime.append_conversation_turn(root, app_id, turn)


def add_missing_credential(root: Path, app_id: str, stage_id: str) -> None:
    app = runtime.load_app(root, app_id)
    requirements = app.setdefault("credential_requirements", [])
    requirements.append(
        {
            "id": f"{stage_id}-provider",
            "label": f"{stage_id.title()} provider",
            "required": True,
            "status": "missing",
            "stage": stage_id,
        }
    )
    runtime.write_app(root, app)


def sanitize_text(value: Any) -> str:
    text = str(value)
    text = text.replace(str(Path.home()), "<home>")
    text = re.sub(r"(/private)?/var/folders/\S+", "<isolated-temp-path>", text)
    text = re.sub(r"/tmp/\S+", "<tmp-path>", text)
    return text


def response_summary(response: dict[str, Any]) -> dict[str, Any]:
    payload = response.get("payload", {})
    summary: dict[str, Any] = {
        "handled": response.get("handled"),
        "error": response.get("error", ""),
        "text": sanitize_text(response.get("text", "")),
    }
    for key in (
        "app_id",
        "stage",
        "from_stage",
        "next_stage",
        "approved",
        "advanced",
        "stage_gate_blocked_apps",
    ):
        if key in payload:
            summary[key] = payload[key]
    if "stage_status" in payload:
        stage_status = payload["stage_status"]
        summary["stage_status"] = {
            "stage": stage_status.get("stage"),
            "stage_state": stage_status.get("stage_state"),
            "stage_gate_passed": stage_status.get("stage_gate_passed"),
            "stage_gate_missing": stage_status.get("stage_gate_missing", []),
        }
    if "stage_gate" in payload:
        stage_gate = payload["stage_gate"]
        summary["stage_gate"] = {
            "stage": stage_gate.get("stage"),
            "passed": stage_gate.get("passed"),
            "missing": stage_gate.get("missing", []),
            "warnings": stage_gate.get("warnings", []),
        }
    return summary


def rest_summary(status: int, response: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"status": status}
    for key in ("app_id", "stage", "approved", "advanced", "error"):
        if key in response:
            summary[key] = response[key]
    if "stage_status" in response:
        summary["stage_status"] = {
            "stage": response["stage_status"].get("stage"),
            "stage_state": response["stage_status"].get("stage_state"),
            "stage_gate_passed": response["stage_status"].get("stage_gate_passed"),
            "stage_gate_missing": response["stage_status"].get("stage_gate_missing", []),
        }
    if "telegram_command" in response:
        summary["telegram_command"] = response_summary(response["telegram_command"])
    return summary


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_rehearsal(artifact_dir: Path | None = None) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    app_id = APP_ID
    stage_ids = runtime.stage_ids()
    with tempfile.TemporaryDirectory(prefix="weave-lifecycle-rehearsal-") as tmpdir:
        root = Path(tmpdir) / "weave-root"
        runtime.setup_weave_root(root)

        def command(label: str, text: str) -> dict[str, Any]:
            response = runtime.dispatch_telegram_command(root, text)
            steps.append({"label": label, "surface": "telegram", "command": text, "response": response_summary(response)})
            return response

        def rest(label: str, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
            status, response = runtime.dispatch_rest(root, method, path, body or {})
            steps.append(
                {
                    "label": label,
                    "surface": "rest",
                    "request": {"method": method, "path": path},
                    "response": rest_summary(status, response),
                }
            )
            return status, response

        command("create app from clean state", f"/create_app {APP_NAME}")
        blocked = command("approval blocks before foundation", f"/approve_stage {app_id}")
        assert_condition(blocked["handled"] is False and "foundation context" in blocked["text"], "approval did not block before foundation")

        missing_app = command("invalid app is rejected", "/status does-not-exist")
        assert_condition(missing_app["handled"] is False, "invalid app lookup should be rejected")

        complete_foundation(root, app_id)
        blocked = command("approval blocks before intent proof", f"/approve_stage {app_id}")
        assert_condition(blocked["handled"] is False and "intent artifact" in blocked["text"], "approval did not require intent artifact")

        status = command("status exposes stage gate attention", "/status")
        assert_condition(status["payload"].get("stage_gate_blocked_apps") == [app_id], "status did not expose stage gate attention")

        artifact_path = write_stage_artifact(root, app_id, "intent")
        advanced = command("advance blocks before owner approval", f"/advance {app_id}")
        assert_condition(
            advanced["handled"] is False and advanced["error"] == "current_stage_gate_not_passing",
            "advance did not block before transcript capture",
        )
        transcript_block = command("approval blocks before transcript capture", f"/approve_stage {app_id}")
        assert_condition(transcript_block["handled"] is False and "transcript capture" in transcript_block["text"], "approval did not require transcript capture")
        record_stage_turn(root, app_id, "intent", artifact_path)
        advanced = command("advance still blocks before owner approval", f"/advance {app_id}")
        assert_condition(
            advanced["handled"] is False and advanced["error"] == "current_stage_not_approved",
            "advance did not block before owner approval",
        )

        for index, stage_id in enumerate(stage_ids):
            current = runtime.app_state(root, app_id)["stage_status"]["stage"]
            assert_condition(current == stage_id, f"expected current stage {stage_id}, got {current}")
            if stage_id != "intent":
                missing = command(f"{stage_id} approval blocks before proof", f"/approve_stage {app_id}")
                assert_condition(missing["handled"] is False, f"{stage_id} should block before proof")
                artifact_path = write_stage_artifact(root, app_id, stage_id)
                missing_transcript = command(f"{stage_id} approval blocks before transcript", f"/approve_stage {app_id}")
                assert_condition(
                    missing_transcript["handled"] is False and "transcript capture" in missing_transcript["text"],
                    f"{stage_id} should block before transcript capture",
                )
                record_stage_turn(root, app_id, stage_id, artifact_path)

            if stage_id in {"kpi", "marketing", "analysis"}:
                add_missing_credential(root, app_id, stage_id)
                blocked_capability = command(f"{stage_id} blocks without credential or deferral", f"/approve_stage {app_id} {stage_id}")
                assert_condition(
                    blocked_capability["handled"] is False and "credential capability" in blocked_capability["text"],
                    f"{stage_id} should block on credential capability",
                )
                approval = command(f"{stage_id} approval with owner credential deferral", f"/approve_stage {app_id} {stage_id} --defer-credentials")
            else:
                lifecycle = command(f"{stage_id} lifecycle ready for review", f"/lifecycle {app_id}")
                assert_condition(lifecycle["payload"]["stage_gate"]["passed"] is True, f"{stage_id} lifecycle gate should pass")
                approval = command(f"{stage_id} approval", f"/approve_stage {app_id} {stage_id}")

            assert_condition(approval["handled"] is True and approval["payload"].get("approved") is True, f"{stage_id} approval failed")
            if index + 1 < len(stage_ids):
                next_stage = stage_ids[index + 1]
                advanced = command(f"advance {stage_id} to {next_stage}", f"/advance {app_id}")
                assert_condition(advanced["handled"] is True, f"advance from {stage_id} failed")
                assert_condition(advanced["payload"].get("stage") == next_stage, f"advance did not reach {next_stage}")

        command("create secondary app for active switch edge", "/create_app Secondary App")
        switched = command("switch active app back", f"/switch_app {app_id}")
        assert_condition(switched["handled"] is True and switched["payload"]["active_app"]["app_id"] == app_id, "active switch failed")

        runtime.create_app(root, "edge-jump", "Edge Jump")
        complete_foundation(root, "edge-jump")
        write_stage_artifact(root, "edge-jump", "qa")
        previous = command("later-stage proof still requires previous approvals", "/approve_stage edge-jump")
        assert_condition(previous["handled"] is False and "previous stage approval" in previous["text"], "previous approval gate failed")

        status_code, rest_lifecycle = rest("REST lifecycle mirrors final app state", "GET", f"/apps/{app_id}/lifecycle")
        assert_condition(status_code == 200, "REST lifecycle returned non-200")
        assert_condition(rest_lifecycle["stage_status"]["stage"] == "analysis", "REST lifecycle did not reach analysis")

        status_code, rest_dispatch = rest("REST telegram dispatch exposes status", "POST", "/telegram/dispatch", {"text": f"/status {app_id}"})
        assert_condition(status_code == 200, "REST telegram dispatch failed")
        assert_condition(rest_dispatch["telegram_command"]["handled"] is True, "REST telegram command was not handled")

        final_state = runtime.app_state(root, app_id)
        approved = final_state["app"].get("approved_stages", [])
        assert_condition(approved == stage_ids, f"approved stages mismatch: {approved}")
        status_code, transcript = rest("REST transcript exposes event stream", "GET", f"/apps/{app_id}/conversation")
        assert_condition(status_code == 200, "REST transcript returned non-200")
        assert_condition(transcript["turn_count"] == len(stage_ids), "transcript turn count mismatch")
        assert_condition(transcript["event_count"] == len(stage_ids) * 8, "conversation event count mismatch")
        status_code, exported = rest("REST transcript export materializes review artifacts", "POST", f"/apps/{app_id}/conversation/export")
        assert_condition(status_code == 200, "REST transcript export returned non-200")
        review = exported["review"]
        review_artifacts: dict[str, str] = {}
        if artifact_dir is not None:
            target_dir = artifact_dir / app_id / "conversation"
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(root / "apps" / app_id / "exports" / "conversation", target_dir, dirs_exist_ok=True)
            review_artifacts = {
                "directory": str(target_dir),
                "html_review": str(target_dir / "conversation-review.html"),
                "event_stream": str(target_dir / "conversation.events.jsonl"),
                "report": str(target_dir / "conversation-report.json"),
            }

        return {
            "schema": "weave-lifecycle-rehearsal/v0.1",
            "created_at": utc_now(),
            "environment": "isolated-temp-runtime",
            "runtime_root": "<isolated-temp-root>/weave-root",
            "app_id": app_id,
            "app_name": APP_NAME,
            "app_intent": APP_INTENT,
            "conversation_model": "stage-specific scripted owner/Hermes product exchange from clean state",
            "passed": True,
            "stages_rehearsed": stage_ids,
            "final_stage": final_state["stage_status"]["stage"],
            "final_stage_state": final_state["stage_status"]["stage_state"],
            "approved_stages": approved,
            "artifact_count": len(final_state["artifacts"]),
            "conversation_turn_count": transcript["turn_count"],
            "conversation_event_count": transcript["event_count"],
            "conversation_review": {
                "schema": review["schema"],
                "turn_count": review["turn_count"],
                "event_count": review["event_count"],
                "canonical_format": review["canonical_format"],
                "primary_review_format": review["primary_review_format"],
                "exports": review["exports"],
                "checksums": review["checksums"],
                "copied_artifacts": review_artifacts,
            },
            "edge_cases": [
                "clean isolated runtime root starts without prior app context",
                "approval blocked before foundation",
                "invalid app rejected",
                "approval blocked before stage proof",
                "status exposed stage-gate attention",
                "advance blocked before owner approval",
                "credential capability required or owner-deferred",
                "later-stage proof blocked without previous approvals",
                "active app switch",
                "REST lifecycle parity",
                "REST Telegram dispatch parity",
                "REST transcript event-stream parity",
                "HTML transcript review export",
            ],
            "steps": steps,
        }


def write_report(report: dict[str, Any], path: Path | None) -> Path:
    if path is None:
        DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = DEFAULT_REPORT_DIR / f"lifecycle-rehearsal-{stamp}.json"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WEAVE lifecycle rehearsal smoke.")
    parser.add_argument("--report-out", type=Path, default=None, help="Path for the JSON proof artifact.")
    args = parser.parse_args()
    artifact_dir = None
    if args.report_out is not None:
        artifact_dir = args.report_out.parent / f"{args.report_out.stem}-artifacts"
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_dir = DEFAULT_REPORT_DIR / f"lifecycle-rehearsal-{stamp}-artifacts"
    try:
        report = run_rehearsal(artifact_dir)
    except Exception as exc:  # noqa: BLE001 - smoke script should emit one concise failure.
        failure = {
            "schema": "weave-lifecycle-rehearsal/v0.1",
            "created_at": utc_now(),
            "passed": False,
            "error": sanitize_text(exc),
        }
        path = write_report(failure, args.report_out)
        print(f"lifecycle rehearsal: fail ({path})")
        return 1
    path = write_report(report, args.report_out)
    print(f"lifecycle rehearsal: ok ({path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
