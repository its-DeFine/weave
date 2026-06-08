#!/usr/bin/env python3
"""Run a full conversational WEAVE dogfood that produces and reviews an app.

Local-only proof. This script does not call live Hermes, Telegram, external
providers, hosting, analytics, payment systems, or public channels. It records a
stage-by-stage owner/Hermes transcript, generates a small static app from that
conversation, exercises WEAVE lifecycle gates, exports transcript review
artifacts, and writes a holistic review of strengths, failures, and next
optimizations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import weave_runtime_slice as runtime  # noqa: E402

DEFAULT_REPORT_DIR = Path.home() / "Documents" / "Codex" / "artifacts" / "weave-full-conversation-dogfood"
APP_ID = "pocket-orchard"
APP_NAME = "Pocket Orchard"
APP_INTENT = (
    "Build a local-only browser app where a tired founder plants three tiny "
    "ideas, watches them grow into a daily plan, and exports the plan as a "
    "reviewable JSON artifact. It should feel like a concrete product, not a "
    "runtime placeholder."
)
FUTURE_CREDENTIAL_STAGES = {"kpi", "marketing", "analysis"}

STAGE_SCRIPT: dict[str, dict[str, Any]] = {
    "intent": {
        "title": "Intent Contract",
        "owner": (
            "I want to see if WEAVE can really make an app from conversation. "
            "Build something small called Pocket Orchard: I give it three rough "
            "ideas, it turns them into a daily action plan, and I can export the "
            "result. Keep it local-only; no deploy, no payments, no fake traction."
        ),
        "agent": (
            "I will treat this as a real app-production run, not a demo of folders. "
            "The first proof will be a static browser app with three idea seeds, a "
            "growth/planning interaction, and exportable JSON. External launch, "
            "analytics, and monetization stay blocked until owner approval."
        ),
        "artifact": (
            "Intent: create Pocket Orchard as a local static product proof. The app "
            "must accept three ideas, transform them into an action plan, expose "
            "reviewable state, and avoid any external side effect."
        ),
        "questions": ["Is the app named?", "Is the local-only boundary explicit?", "Is success observable in the product?"],
        "basis": ["named app", "three-idea input", "local-only/product-proof boundary"],
    },
    "research": {
        "title": "Research Notes",
        "owner": (
            "Before choosing the shape, check what would make this useful instead "
            "of cute. I need a founder to leave with an actual plan, not just a "
            "garden metaphor."
        ),
        "agent": (
            "The useful core is conversion from vague ideas into ranked actions. "
            "The garden metaphor should be a thin interaction layer over practical "
            "outputs: priority, next step, expected effort, and export. A static app "
            "is enough for this proof; storage can be in memory for the run."
        ),
        "artifact": (
            "Research conclusion: usefulness depends on practical action-plan output, "
            "not visual novelty. A static app can prove the first session if it "
            "shows ranking, next actions, and export without backend state."
        ),
        "questions": ["What makes it useful?", "Can static-first prove enough?", "What is the main fake-product risk?"],
        "basis": ["action-plan utility", "static-first sufficient", "metaphor must not hide weak output"],
    },
    "selection": {
        "title": "Selection Matrix",
        "owner": (
            "Choose the smallest version that still proves the point. I do not want "
            "a giant framework; I want the app to be inspectable and obviously made "
            "from the conversation."
        ),
        "agent": (
            "I choose a dependency-free static app: one HTML file, one JS file, one "
            "CSS file, and a config JSON. It will include sample seed ideas, allow "
            "editing, generate prioritized daily actions, and export the current plan. "
            "I reject auth, database, network APIs, and payment for this proof."
        ),
        "artifact": (
            "Selected direction: dependency-free static browser app. Rejected options: "
            "backend account system, external LLM calls, live analytics, and checkout. "
            "Selection optimizes inspectability and end-to-end local proof."
        ),
        "questions": ["Is the chosen stack small enough?", "Were rejected paths explicit?", "Does the app still feel real?"],
        "basis": ["dependency-free static app", "backend rejected", "external APIs rejected"],
    },
    "plan": {
        "title": "Implementation Plan",
        "owner": (
            "Plan it in files and checks. Tell me what will be created, what will be "
            "tested, and where WEAVE should stop."
        ),
        "agent": (
            "I will create index.html, src/app.js, src/styles.css, public/config.json, "
            "and README.md. Checks will verify required files, JS syntax, disabled "
            "external actions, export schema, and transcript/lifecycle evidence. I stop "
            "before deploy, analytics, public marketing, or payments."
        ),
        "artifact": (
            "Plan: generate a static app, verify file presence and JavaScript syntax, "
            "record lifecycle proof artifacts, export the transcript review, and write "
            "a holistic post-run review. Non-goals: deploy, analytics, payment, public send."
        ),
        "questions": ["Are files named?", "Are checks named?", "Are non-goals explicit?"],
        "basis": ["file-level plan", "test plan", "hard stop boundaries"],
    },
    "engineering": {
        "title": "Engineering Output Index",
        "owner": (
            "Now actually make the app. The output should show the three ideas, turn "
            "them into action rows, and let me export the plan."
        ),
        "agent": (
            "I generated Pocket Orchard as a static app with editable seeds, a "
            "prioritized action plan, local-only state, and a JSON export button. The "
            "source is dependency-free and the config keeps deploy, analytics, and "
            "payments disabled."
        ),
        "artifact": (
            "Engineering produced the app source and source index. The generated app "
            "contains editable idea seeds, deterministic plan generation, exportable "
            "JSON, and disabled external surfaces."
        ),
        "questions": ["Were app files actually generated?", "Does source match the plan?", "Are external actions disabled?"],
        "basis": ["generated app source", "deterministic plan logic", "external actions disabled"],
    },
    "qa": {
        "title": "QA Proof",
        "owner": (
            "QA it like a skeptical reviewer. What passed, what failed, and what does "
            "this still not prove?"
        ),
        "agent": (
            "Local QA verifies required files, JavaScript syntax, export schema, "
            "disabled external surfaces, and transcript-linked lifecycle gates. It "
            "does not prove live Telegram operation, real user value, hosted performance, "
            "or revenue."
        ),
        "artifact": (
            "QA proof records deterministic checks for generated source, export shape, "
            "disabled external configuration, lifecycle stage approvals, and transcript "
            "export. Remaining unproven surfaces are explicitly listed."
        ),
        "questions": ["Did checks run?", "Are non-proofs explicit?", "Is evidence reviewable?"],
        "basis": ["local QA checks", "negative claims withheld", "reviewable proof artifacts"],
    },
    "kpi": {
        "title": "KPI Setup",
        "owner": (
            "Set up what we would measure if this went to beta. Do not pretend we "
            "already have users."
        ),
        "agent": (
            "The beta KPI model should measure completed plan exports, number of ideas "
            "entered, plan acceptance, return intent, and conversion intent for premium "
            "templates. In this proof the metrics are local placeholders only because "
            "analytics credentials and real users are absent."
        ),
        "artifact": (
            "KPI setup defines export completion, seed count, plan acceptance, return "
            "intent, and premium-template intent. Real analytics are blocked and owner-deferred."
        ),
        "questions": ["Are KPIs product-specific?", "Is measurement mocked/local?", "Are analytics credentials deferred?"],
        "basis": ["product-specific KPI model", "real analytics absent", "owner deferral required"],
    },
    "marketing": {
        "title": "Marketing Review Draft",
        "owner": (
            "Draft how we would explain it, but do not publish anything. I want to see "
            "whether the product has a coherent promise."
        ),
        "agent": (
            "The promise is: turn three messy ideas into a tiny orchard of prioritized "
            "actions in under five minutes. Audience: solo founders and creative operators "
            "who need momentum without project-management overhead. No public send is made."
        ),
        "artifact": (
            "Marketing draft: Pocket Orchard helps solo founders turn three rough ideas "
            "into a daily action plan. Public distribution is blocked pending owner approval, "
            "hosting, analytics, and feedback evidence."
        ),
        "questions": ["Is the audience concrete?", "Is the promise product-tied?", "Are public sends blocked?"],
        "basis": ["solo founder audience", "five-minute action-plan promise", "public send blocked"],
    },
    "iteration": {
        "title": "Iteration Note",
        "owner": (
            "Imagine the first reviewer says it is useful but too cute. Improve the "
            "app direction without expanding scope."
        ),
        "agent": (
            "The iteration is to make the plan output more prominent than the garden copy: "
            "lead with the daily plan, keep the orchard as lightweight feedback, and add "
            "a sharper export summary. No backend or new provider is needed."
        ),
        "artifact": (
            "Iteration: reduce metaphor weight, increase action-plan prominence, and "
            "make the export summary more useful. Scope remains static/local."
        ),
        "questions": ["Is feedback actionable?", "Does iteration preserve scope?", "Does it improve usefulness?"],
        "basis": ["mock reviewer feedback", "plan-first revision", "scope preserved"],
    },
    "analysis": {
        "title": "Outcome Analysis",
        "owner": (
            "Review the whole thing. Where was WEAVE good, where did it fake success, "
            "and what should we optimize before trusting it with real app production?"
        ),
        "agent": (
            "WEAVE is good at explicit gates, evidence capture, and local app proof. It "
            "still fakes the hardest part if we call a scripted transcript a live owner "
            "conversation. The next optimization is a live Telegram/Hermes run with the "
            "same transcript/export gates and human review of the produced app."
        ),
        "artifact": (
            "Outcome analysis: the local scripted run proves lifecycle mechanics plus app "
            "artifact production. It does not prove live conversational autonomy, market "
            "fit, deployment, analytics, payment, or real user satisfaction."
        ),
        "questions": ["What was proven?", "What was only simulated?", "What should be optimized next?"],
        "basis": ["local app produced", "scripted transcript limitation", "live run next"],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def fill(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\nStatus: complete\n\n{body}\n", encoding="utf-8")


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return {
        "command": command,
        "cwd": str(cwd.name),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "passed": result.returncode == 0,
    }


def node_command(cwd: Path, args: list[str]) -> dict[str, Any]:
    primary = ["node", *args]
    check = run_command(primary, cwd)
    empty_abort = check["returncode"] in {-6, 134} and not check["stderr"]
    if check["passed"] or not empty_abort:
        return check
    fallback = run_command(["npm", "exec", "--", "node", *args], cwd)
    fallback["fallback_for_empty_node_abort"] = True
    fallback["primary_command"] = primary
    fallback["primary_returncode"] = check["returncode"]
    return fallback


def assert_pass(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def complete_foundation(root: Path, app_id: str) -> None:
    fill(root / "artifacts" / "general" / "soul.md", "Hermes Soul", "Hermes acts as a careful product operator and lifecycle reviewer.")
    fill(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile", "The owner wants proof from real product output, not generic runtime claims.")
    fill(root / "apps" / app_id / "context" / "app-context.md", "App Context", APP_INTENT)
    fill(root / "apps" / app_id / "inventory" / "app-inventory.md", "App Inventory", "Generated static app source, lifecycle transcript, QA proof, and holistic review.")
    fill(root / "apps" / app_id / "contract" / "gestaltian-contract.md", "Gestaltian Contract", "Each stage needs proof artifact, conversation turn, gate check, and owner approval before advancement.")


def add_missing_credential(root: Path, app_id: str, stage_id: str) -> None:
    app = runtime.load_app(root, app_id)
    requirements = app.setdefault("credential_requirements", [])
    requirements.append(
        {
            "id": f"{stage_id}-external-provider",
            "label": f"{stage_id} external provider",
            "required": True,
            "status": "missing",
            "stage": stage_id,
        }
    )
    runtime.write_app(root, app)


def generate_app(app_dir: Path) -> list[Path]:
    (app_dir / "src").mkdir(parents=True, exist_ok=True)
    (app_dir / "public").mkdir(parents=True, exist_ok=True)
    (app_dir / "index.html").write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pocket Orchard</title>
  <link rel="stylesheet" href="src/styles.css" />
</head>
<body>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Local product proof</p>
      <h1>Pocket Orchard</h1>
      <p>Turn three rough ideas into a tiny, prioritized action plan.</p>
    </section>
    <section class="panel" aria-labelledby="seed-heading">
      <h2 id="seed-heading">Idea seeds</h2>
      <label>Seed 1 <input id="seed-one" value="Interview three users about onboarding friction" /></label>
      <label>Seed 2 <input id="seed-two" value="Prototype a calmer dashboard for daily focus" /></label>
      <label>Seed 3 <input id="seed-three" value="Package the best workflow as a paid template later" /></label>
      <button id="grow-plan" type="button">Grow plan</button>
      <button id="export-plan" type="button">Export JSON</button>
    </section>
    <section class="panel" aria-live="polite">
      <h2>Daily action plan</h2>
      <ol id="plan-list"></ol>
      <pre id="export-output" aria-label="Exported plan JSON"></pre>
    </section>
    <p class="boundary">Local-only proof: analytics, hosting, and payments are disabled.</p>
  </main>
  <script src="src/app.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )
    (app_dir / "src" / "styles.css").write_text(
        """body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #11251c; color: #f4ffe8; }
.shell { max-width: 920px; margin: 0 auto; padding: 48px 20px; }
.hero { padding: 28px; border-radius: 28px; background: linear-gradient(135deg, #224d35, #1c393d); box-shadow: 0 24px 80px rgba(0,0,0,.28); }
.eyebrow { color: #b9ff9d; text-transform: uppercase; letter-spacing: .14em; font-size: .78rem; }
h1 { margin: .1em 0; font-size: clamp(2.4rem, 7vw, 5.2rem); }
.panel { margin-top: 22px; padding: 24px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); border-radius: 24px; }
label { display: grid; gap: 8px; margin: 14px 0; font-weight: 700; }
input { font: inherit; border: 0; border-radius: 14px; padding: 12px 14px; }
button { margin: 12px 10px 0 0; border: 0; border-radius: 999px; padding: 12px 18px; font-weight: 800; color: #102015; background: #b9ff9d; cursor: pointer; }
li { margin: 12px 0; padding: 12px; border-radius: 16px; background: rgba(185,255,157,.12); }
pre { white-space: pre-wrap; color: #d8ffc8; }
.boundary { color: #c6d8c0; }
""",
        encoding="utf-8",
    )
    (app_dir / "src" / "app.js").write_text(
        """const planList = document.querySelector('#plan-list');
const exportOutput = document.querySelector('#export-output');
const seedInputs = ['#seed-one', '#seed-two', '#seed-three'].map((selector) => document.querySelector(selector));

function seedValue(input, index) {
  const value = input.value.trim();
  return value || `Untitled seed ${index + 1}`;
}

function buildPlan() {
  return seedInputs.map(seedValue).map((seed, index) => ({
    priority: index + 1,
    seed,
    nextAction: index === 0 ? `Validate: ${seed}` : index === 1 ? `Prototype: ${seed}` : `Defer safely: ${seed}`,
    effort: index === 0 ? '45 minutes' : index === 1 ? '90 minutes' : 'owner-approved future work',
    externalAction: false
  }));
}

function renderPlan() {
  const plan = buildPlan();
  planList.innerHTML = '';
  plan.forEach((item) => {
    const row = document.createElement('li');
    row.innerHTML = `<strong>${item.nextAction}</strong><br><span>Effort: ${item.effort}</span>`;
    planList.appendChild(row);
  });
  return plan;
}

function exportPlan() {
  const payload = {
    schema: 'pocket-orchard-plan/v0.1',
    generatedBy: 'weave-full-conversation-dogfood',
    localOnly: true,
    externalActionsEnabled: false,
    plan: renderPlan()
  };
  exportOutput.textContent = JSON.stringify(payload, null, 2);
  return payload;
}

document.querySelector('#grow-plan').addEventListener('click', renderPlan);
document.querySelector('#export-plan').addEventListener('click', exportPlan);
renderPlan();
window.PocketOrchard = { buildPlan, exportPlan };
""",
        encoding="utf-8",
    )
    (app_dir / "public" / "config.json").write_text(
        json.dumps(
            {
                "schema": "pocket-orchard-config/v0.1",
                "analyticsEnabled": False,
                "paymentsEnabled": False,
                "hostingStatus": "local-only",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (app_dir / "README.md").write_text(
        "# Pocket Orchard\n\nLocal-only static app generated by the full conversation dogfood.\n\nNo deploy, analytics, or payment surface is enabled.\n",
        encoding="utf-8",
    )
    return sorted(path for path in app_dir.rglob("*") if path.is_file())


def app_checks(app_dir: Path) -> dict[str, Any]:
    required = [
        app_dir / "index.html",
        app_dir / "src" / "app.js",
        app_dir / "src" / "styles.css",
        app_dir / "public" / "config.json",
        app_dir / "README.md",
    ]
    checks: list[dict[str, Any]] = []
    for path in required:
        checks.append({"name": f"file exists: {path.relative_to(app_dir)}", "passed": path.exists()})
        assert_pass(path.exists(), f"missing generated app file: {path}")
    config = json.loads((app_dir / "public" / "config.json").read_text(encoding="utf-8"))
    checks.append({"name": "external actions disabled", "passed": config["analyticsEnabled"] is False and config["paymentsEnabled"] is False})
    assert_pass(checks[-1]["passed"], "external actions must be disabled")
    js = (app_dir / "src" / "app.js").read_text(encoding="utf-8")
    checks.append({"name": "export schema present", "passed": "pocket-orchard-plan/v0.1" in js})
    assert_pass(checks[-1]["passed"], "export schema missing")
    node = node_command(app_dir, ["--check", "src/app.js"])
    checks.append({"name": "node syntax app.js", "passed": node["passed"], "command": node})
    assert_pass(node["passed"], f"node syntax check failed: {node}")
    return {
        "passed": True,
        "check_count": len(checks),
        "checks": checks,
        "generated_files": [str(path.relative_to(app_dir)) for path in required],
        "checksums": {str(path.relative_to(app_dir)): sha256(path) for path in required},
    }


def write_stage_artifact(root: Path, app_id: str, stage_id: str, body: str, extra: dict[str, Any] | None = None) -> Path:
    stage = runtime.stage_by_id(stage_id)
    path = root / "apps" / app_id / "lifecycle" / stage.directory / "artifacts" / f"{stage_id}-proof.md"
    appendix = ""
    if extra:
        appendix = "\n\n```json\n" + json.dumps(extra, indent=2, sort_keys=True) + "\n```\n"
    fill(path, STAGE_SCRIPT[stage_id]["title"], body + appendix)
    return path


def record_stage_turn(root: Path, app_id: str, stage_id: str, artifact_path: Path, extra_refs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    script = STAGE_SCRIPT[stage_id]
    artifact_ref = {"path": runtime.relative(artifact_path, root), "action": "created", "kind": "stage-proof"}
    turn = runtime.new_conversation_turn(
        app_id,
        stage_id,
        {"role": "owner", "source": "full-conversation-dogfood", "text": script["owner"]},
        {"role": "hermes", "source": "full-conversation-dogfood", "text": script["agent"]},
        channel="local-dogfood",
        created_by="execution-agent",
        agent_rationale={
            "summary": f"{script['title']} is ready for owner review with linked proof artifact.",
            "gate_questions": script["questions"],
            "missing_information": [],
            "decision_basis": [*script["basis"], f"stage artifact: {runtime.relative(artifact_path, root)}"],
            "chain_of_thought_captured": False,
        },
        gate_checks={"foundation_gate_passed": True, "stage_artifact_present": True, "owner_approval_required": True},
        artifact_refs=[artifact_ref, *(extra_refs or [])],
        state_transition={
            "from_stage": stage_id,
            "from_state": "collecting",
            "to_stage": stage_id,
            "to_state": "ready_for_review",
            "reason": f"{script['title']} proof generated from the dogfood conversation.",
        },
        next_action=f"Owner reviews {runtime.owner_stage_label(stage_id)} evidence and approves or requests revision.",
    )
    return runtime.append_conversation_turn(root, app_id, turn)


def command_summary(response: dict[str, Any]) -> dict[str, Any]:
    payload = response.get("payload", {})
    summary = {"handled": response.get("handled"), "error": response.get("error", "")}
    for key in ("stage", "from_stage", "next_stage", "approved", "advanced"):
        if key in payload:
            summary[key] = payload[key]
    if "stage_gate" in payload:
        summary["stage_gate"] = {
            "stage": payload["stage_gate"].get("stage"),
            "passed": payload["stage_gate"].get("passed"),
            "missing": payload["stage_gate"].get("missing", []),
            "warnings": payload["stage_gate"].get("warnings", []),
        }
    return summary


def holistic_review() -> dict[str, Any]:
    dimensions = [
        {
            "dimension": "product_result",
            "verdict": "useful_local_proof",
            "good": "The run produces a concrete static app with editable inputs, action-plan output, and export JSON.",
            "failure_modes": ["No real user touched it", "No hosted environment or device matrix was exercised"],
            "optimization": "Run browser-based exploratory QA and at least one human beta session against a hosted build.",
        },
        {
            "dimension": "conversation_realism",
            "verdict": "scripted_not_live",
            "good": "The transcript is complete across all lifecycle stages and linked to proof artifacts.",
            "failure_modes": ["Owner and agent messages are scripted", "No adaptive clarification or live misunderstanding occurred"],
            "optimization": "Run the same flow through live Telegram/Hermes with owner interruptions, corrections, and stage-review pauses.",
        },
        {
            "dimension": "lifecycle_governance",
            "verdict": "strong_mechanics_partial_judgment",
            "good": "Foundation, stage artifact, transcript capture, approval, credential deferral, and final transcript export are exercised.",
            "failure_modes": ["A mediocre markdown artifact can still pass if the gate only checks presence", "Rubric quality depends on reviewer discipline"],
            "optimization": "Add semantic artifact-quality checks and reviewer scoring against generated app behavior.",
        },
        {
            "dimension": "runtime_surface",
            "verdict": "local_runtime_only",
            "good": "Deterministic runtime commands and REST transcript export are used from a clean isolated root.",
            "failure_modes": ["Live Telegram gateway was not exercised", "No long-running runtime/container state was proven"],
            "optimization": "Replay this as a live gateway proof once owner approves runtime mutation and bot/channel scope.",
        },
        {
            "dimension": "trust_boundary",
            "verdict": "safe_local_default",
            "good": "No external network, deploy, payment, analytics, or public send occurs; missing credentials are owner-deferred.",
            "failure_modes": ["Safety is proven for the script, not for future live adapters", "Human approval UX still needs live testing"],
            "optimization": "Add live approval prompts and negative tests for attempted public/payment actions.",
        },
        {
            "dimension": "business_signal",
            "verdict": "not_market_validated",
            "good": "The app has a coherent value promise and KPI model.",
            "failure_modes": ["No traffic, retention, conversion, or willingness-to-pay evidence", "Marketing remains a draft"],
            "optimization": "Use a hosted beta with analytics and explicit owner-approved feedback collection.",
        },
    ]
    return {
        "schema": "weave-full-conversation-holistic-review/v0.1",
        "overall_verdict": "valuable local dogfood; not live conversational proof",
        "dimensions": dimensions,
        "top_optimizations": [
            "Run live Telegram/Hermes app-production conversation with the same gates.",
            "Add browser exploratory QA evidence for generated apps.",
            "Strengthen gates from artifact presence to artifact quality plus behavior proof.",
            "Keep release readiness blocked on human review and live-runtime proof.",
        ],
    }


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    stage_results: list[dict[str, Any]] = []
    stage_ids = runtime.stage_ids()
    generated_app_output = output_dir / "generated-app"
    if generated_app_output.exists():
        shutil.rmtree(generated_app_output)

    with tempfile.TemporaryDirectory(prefix="weave-full-conversation-") as tmpdir:
        root = Path(tmpdir) / "weave-root"
        runtime.setup_weave_root(root)
        runtime.create_app(root, APP_ID, APP_NAME)
        complete_foundation(root, APP_ID)
        app_repo = root / "apps" / APP_ID / "repo" / "primary"

        def cmd(label: str, text: str) -> dict[str, Any]:
            response = runtime.dispatch_telegram_command(root, text)
            commands.append({"label": label, "command": text, "response": command_summary(response)})
            return response

        blocked = cmd("approval blocks before intent artifact", f"/approve_stage {APP_ID}")
        assert_pass(blocked.get("handled") is False, "approval should block before intent artifact")

        qa_result: dict[str, Any] = {}
        generated_files: list[Path] = []
        for index, stage_id in enumerate(stage_ids):
            current = runtime.app_state(root, APP_ID)["stage_status"]["stage"]
            assert_pass(current == stage_id, f"expected current stage {stage_id}, got {current}")
            extra_refs: list[dict[str, Any]] = []
            extra_payload: dict[str, Any] | None = None
            if stage_id == "engineering":
                generated_files = generate_app(app_repo)
                extra_refs = [
                    {"path": runtime.relative(path, root), "action": "created", "kind": "generated-app-source"}
                    for path in generated_files
                ]
                extra_payload = {"generated_files": [runtime.relative(path, root) for path in generated_files]}
            if stage_id == "qa":
                qa_result = app_checks(app_repo)
                qa_artifact = root / "apps" / APP_ID / "lifecycle" / runtime.stage_by_id(stage_id).directory / "artifacts" / "qa-checks.json"
                qa_artifact.parent.mkdir(parents=True, exist_ok=True)
                qa_artifact.write_text(json.dumps(qa_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                extra_refs.append({"path": runtime.relative(qa_artifact, root), "action": "created", "kind": "qa-proof"})
                extra_payload = qa_result
            if stage_id in FUTURE_CREDENTIAL_STAGES:
                add_missing_credential(root, APP_ID, stage_id)
            artifact = write_stage_artifact(root, APP_ID, stage_id, STAGE_SCRIPT[stage_id]["artifact"], extra_payload)
            record_stage_turn(root, APP_ID, stage_id, artifact, extra_refs)
            lifecycle = cmd(f"{stage_id} lifecycle ready", f"/lifecycle {APP_ID}")
            stage_gate = lifecycle["payload"]["stage_gate"]
            approve_command = f"/approve_stage {APP_ID} {stage_id}"
            if stage_id in FUTURE_CREDENTIAL_STAGES:
                assert_pass(stage_gate["passed"] is False, f"{stage_id} should expose credential gate before deferral")
                assert_pass(
                    any("credential" in str(item).lower() for item in stage_gate.get("missing", [])),
                    f"{stage_id} should name missing credential capability",
                )
                blocked_credential = cmd(f"{stage_id} blocks without credential deferral", approve_command)
                assert_pass(blocked_credential.get("handled") is False, f"{stage_id} should require credential deferral")
                approve_command += " --defer-credentials"
            else:
                assert_pass(stage_gate["passed"] is True, f"{stage_id} gate should pass")
            approval = cmd(f"{stage_id} approval", approve_command)
            assert_pass(approval.get("handled") is True and approval["payload"].get("approved") is True, f"{stage_id} approval failed")
            result = {"stage": stage_id, "artifact": runtime.relative(artifact, root), "approved": True}
            if index + 1 < len(stage_ids):
                advanced = cmd(f"advance {stage_id}", f"/advance {APP_ID}")
                assert_pass(advanced.get("handled") is True, f"advance from {stage_id} failed")
                result["advanced_to"] = advanced["payload"].get("stage")
            stage_results.append(result)

        final_state = runtime.app_state(root, APP_ID)
        assert_pass(final_state["app"].get("approved_stages", []) == stage_ids, "not all stages were approved")
        status, exported = runtime.dispatch_rest(root, "POST", f"/apps/{APP_ID}/conversation/export", {})
        assert_pass(status == 200, "conversation export failed")
        export_dir = root / "apps" / APP_ID / "exports" / "conversation"
        transcript_output = output_dir / "conversation-review"
        if transcript_output.exists():
            shutil.rmtree(transcript_output)
        shutil.copytree(export_dir, transcript_output)
        shutil.copytree(app_repo, generated_app_output)

        app_file_checksums = {
            str(path.relative_to(generated_app_output)): sha256(path)
            for path in sorted(generated_app_output.rglob("*"))
            if path.is_file()
        }
        review = holistic_review()
        review_path = output_dir / "holistic-review.json"
        review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        return {
            "schema": "weave-full-conversation-app-dogfood/v0.1",
            "created_at": utc_now(),
            "passed": True,
            "environment": "isolated-local-runtime",
            "live_hermes_used": False,
            "conversation_model": "scripted full owner/Hermes app-production transcript",
            "app": {
                "app_id": APP_ID,
                "name": APP_NAME,
                "intent": APP_INTENT,
                "generated_app_dir": str(generated_app_output),
                "file_count": len(app_file_checksums),
                "checksums": app_file_checksums,
            },
            "lifecycle": {
                "stages": stage_ids,
                "stage_count": len(stage_ids),
                "approved_stages": final_state["app"].get("approved_stages", []),
                "final_stage": final_state["stage_status"]["stage"],
                "final_stage_state": final_state["stage_status"]["stage_state"],
                "stage_results": stage_results,
            },
            "qa": qa_result,
            "conversation_review": {
                "turn_count": exported["review"]["turn_count"],
                "event_count": exported["review"]["event_count"],
                "export_dir": str(transcript_output),
                "checksums": exported["review"].get("checksums", {}),
            },
            "holistic_review": review,
            "commands": commands,
            "explicit_non_claims": [
                "not a live Hermes or Telegram conversation",
                "not deployed or publicly released",
                "no analytics, payments, provider credentials, or external sends were used",
                "no real user or market demand evidence",
            ],
        }


def write_report(report: dict[str, Any], report_out: Path | None) -> Path:
    if report_out is None:
        DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_out = DEFAULT_REPORT_DIR / f"full-conversation-app-dogfood-{stamp}.json"
    else:
        report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full conversation-to-app WEAVE dogfood.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for generated app, transcript export, and review artifacts.")
    parser.add_argument("--report-out", type=Path, default=None, help="Path for JSON report.")
    args = parser.parse_args()
    if args.output_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir = DEFAULT_REPORT_DIR / f"full-conversation-app-dogfood-{stamp}-artifacts"
    else:
        output_dir = args.output_dir
    started = time.time()
    try:
        report = run(output_dir)
    except Exception as exc:  # noqa: BLE001
        failure = {
            "schema": "weave-full-conversation-app-dogfood/v0.1",
            "created_at": utc_now(),
            "passed": False,
            "error": str(exc),
        }
        path = write_report(failure, args.report_out)
        print(f"full conversation app dogfood: fail ({path})")
        return 1
    report["duration_seconds"] = round(time.time() - started, 3)
    path = write_report(report, args.report_out)
    print(f"full conversation app dogfood: ok ({path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
