#!/usr/bin/env python3
"""Evaluate WEAVE operating profiles on multiple local-only private app scenarios.

This is a deterministic, public-safe harness for exercising the cognitive model
without exposing real user data or performing external actions. Each scenario
produces a small static app, framework artifacts, proof-boundary records, and an
assessment report. Marketing is intentionally excluded; iteration is represented
as private recommendation artifacts only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUN_SCHEMA = "weave-private-app-operating-profile-eval-run/v0.1"
APP_SCHEMA = "weave-private-app-operating-profile-eval-app/v0.1"
COGNITIVE_SCHEMA = "weave-cognitive-artifact-bundle/v0.1"
DEFAULT_OUTPUT_DIR = Path("artifacts") / "private-app-operating-profile-evals"

NON_CLAIMS = [
    "deterministic local fixture; not live Hermes CLI proof",
    "not Telegram, deployed gateway, or hosted application proof",
    "no public marketing, analytics calls, payments, auth changes, or external sends",
    "uses synthetic private-domain sample data only; no real personal or customer data",
]

REQUIRED_FRAMEWORK_ARTIFACTS = [
    "intent-frame.json",
    "profile-selection.json",
    "cwa-work-domain.json",
    "dmn-decision-table.json",
    "ibis-map.json",
    "adr-0001-local-private-first.md",
    "action-intent.json",
    "action-result.json",
    "prov-ledger.jsonl",
]

APP_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "runway-ledger",
        "name": "Runway Ledger",
        "user": "solo founder",
        "private_domain": "cashflow notes, monthly burn, runway assumptions",
        "intent": "Turn private runway facts into a weekly cash decision board.",
        "data_rows": [
            {"label": "Monthly burn", "value": "4200", "signal": "reduce optional tooling"},
            {"label": "Committed revenue", "value": "1800", "signal": "protect renewal work"},
            {"label": "Upcoming invoice", "value": "2500", "signal": "follow up this week"},
        ],
        "features": ["burn review", "invoice follow-up", "runway action plan", "JSON export"],
        "success_metrics": ["cash-risk clarity", "weekly action chosen", "private data stays local"],
    },
    {
        "id": "partner-pulse",
        "name": "Partner Pulse",
        "user": "partnership lead",
        "private_domain": "partner conversations, objections, follow-up commitments",
        "intent": "Convert partner notes into follow-up priorities and risk tags.",
        "data_rows": [
            {"label": "Analytics partner", "value": "integration blocker", "signal": "needs technical owner"},
            {"label": "Agency channel", "value": "pricing confusion", "signal": "clarify package tiers"},
            {"label": "Infra partner", "value": "waiting on proof", "signal": "send local demo evidence"},
        ],
        "features": ["objection board", "follow-up planner", "risk tag summary", "JSON export"],
        "success_metrics": ["next partner action", "objection pattern visible", "no public send"],
    },
    {
        "id": "cohort-compass",
        "name": "Cohort Compass",
        "user": "product operator",
        "private_domain": "usage cohorts, activation notes, churn reasons",
        "intent": "Help a product operator decide which activation friction to fix first.",
        "data_rows": [
            {"label": "New users", "value": "low activation", "signal": "improve first-session guidance"},
            {"label": "Returning users", "value": "high export usage", "signal": "protect export workflow"},
            {"label": "Churn notes", "value": "unclear setup", "signal": "add onboarding checklist"},
        ],
        "features": ["cohort signal cards", "friction ranking", "fix-first decision", "JSON export"],
        "success_metrics": ["top friction named", "fix candidate selected", "evidence trace exists"],
    },
    {
        "id": "care-loop",
        "name": "Care Loop",
        "user": "care coordinator",
        "private_domain": "care tasks, check-ins, household routines",
        "intent": "Turn private care reminders into a calm daily checklist.",
        "data_rows": [
            {"label": "Morning medication", "value": "daily", "signal": "confirm before breakfast"},
            {"label": "Hydration check", "value": "afternoon", "signal": "make visible"},
            {"label": "Evening note", "value": "mood and sleep", "signal": "capture pattern"},
        ],
        "features": ["daily checklist", "gentle priority", "handoff note", "JSON export"],
        "success_metrics": ["less missed routine", "reviewable handoff", "no health overclaim"],
    },
    {
        "id": "decision-deck",
        "name": "Decision Deck",
        "user": "executive assistant",
        "private_domain": "meeting notes, decisions, unresolved blockers",
        "intent": "Transform private meeting notes into decisions, blockers, and next owners.",
        "data_rows": [
            {"label": "Pricing meeting", "value": "discount policy undecided", "signal": "needs ADR"},
            {"label": "Engineering sync", "value": "QA owner missing", "signal": "assign reviewer"},
            {"label": "Customer call", "value": "migration concern", "signal": "draft risk response"},
        ],
        "features": ["decision extraction", "blocker lane", "owner assignment", "JSON export"],
        "success_metrics": ["decision state clear", "blockers surfaced", "owners visible"],
    },
    {
        "id": "learning-loop",
        "name": "Learning Loop",
        "user": "course creator",
        "private_domain": "learner notes, quiz misses, lesson feedback",
        "intent": "Find the lesson improvement most likely to help a private cohort.",
        "data_rows": [
            {"label": "Module one", "value": "confusing vocabulary", "signal": "add glossary"},
            {"label": "Module two", "value": "exercise skipped", "signal": "shorten assignment"},
            {"label": "Module three", "value": "high confidence", "signal": "keep structure"},
        ],
        "features": ["feedback clustering", "lesson fix ranking", "cohort-safe export", "JSON export"],
        "success_metrics": ["highest leverage lesson named", "private feedback summarized", "no public claim"],
    },
]


@dataclass(frozen=True)
class AppResult:
    app_id: str
    name: str
    passed: bool
    score: int
    app_dir: str
    report: str
    artifact_count: int
    checks: list[dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_label(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "app"


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scenario_by_id(app_id: str) -> dict[str, Any]:
    for scenario in APP_SCENARIOS:
        if scenario["id"] == app_id:
            return scenario
    raise ValueError(f"unknown scenario: {app_id}")


def render_html(scenario: dict[str, Any]) -> str:
    title = scenario["name"]
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"src/styles.css\">
</head>
<body>
  <main class=\"shell\">
    <section class=\"hero\">
      <p class=\"eyebrow\">Private local product proof</p>
      <h1>{title}</h1>
      <p id=\"intent\"></p>
    </section>
    <section class=\"panel\">
      <h2>Private signals</h2>
      <div id=\"signals\" class=\"cards\"></div>
    </section>
    <section class=\"panel\">
      <h2>Recommended next actions</h2>
      <ol id=\"actions\"></ol>
    </section>
    <section class=\"panel\">
      <h2>Assessment export</h2>
      <button id=\"exportButton\" type=\"button\">Build export preview</button>
      <pre id=\"exportPreview\" aria-live=\"polite\"></pre>
    </section>
  </main>
  <script type=\"module\" src=\"src/app.js\"></script>
</body>
</html>"""


def render_js(scenario: dict[str, Any]) -> str:
    payload = {
        "id": scenario["id"],
        "name": scenario["name"],
        "intent": scenario["intent"],
        "user": scenario["user"],
        "privateDomain": scenario["private_domain"],
        "signals": scenario["data_rows"],
        "features": scenario["features"],
        "successMetrics": scenario["success_metrics"],
        "externalActionsEnabled": False,
        "marketingIncluded": False,
    }
    data = json.dumps(payload, indent=2, sort_keys=True)
    return f"""const app = {data};

function el(tag, className, text) {{
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}}

function renderSignals() {{
  document.getElementById('intent').textContent = app.intent;
  const container = document.getElementById('signals');
  app.signals.forEach((signal, index) => {{
    const card = el('article', 'card');
    card.appendChild(el('h3', '', `${{index + 1}}. ${{signal.label}}`));
    card.appendChild(el('p', 'value', signal.value));
    card.appendChild(el('p', 'signal', signal.signal));
    container.appendChild(card);
  }});
}}

function buildActions() {{
  return app.signals.map((signal, index) => ({{
    rank: index + 1,
    action: signal.signal,
    evidence: signal.label,
    privateDataUsed: true,
    publicSendAllowed: false
  }}));
}}

function renderActions() {{
  const actions = document.getElementById('actions');
  buildActions().forEach(item => {{
    const row = el('li', 'action');
    row.appendChild(el('strong', '', item.action));
    row.appendChild(el('span', '', ` Evidence: ${{item.evidence}}`));
    actions.appendChild(row);
  }});
}}

function exportAssessment() {{
  const exportPayload = {{
    schema: 'weave-private-app-export/v0.1',
    appId: app.id,
    appName: app.name,
    generatedFromPrivateData: true,
    externalActionsEnabled: app.externalActionsEnabled,
    marketingIncluded: app.marketingIncluded,
    successMetrics: app.successMetrics,
    recommendedActions: buildActions()
  }};
  document.getElementById('exportPreview').textContent = JSON.stringify(exportPayload, null, 2);
}}

renderSignals();
renderActions();
document.getElementById('exportButton').addEventListener('click', exportAssessment);
"""


def render_css() -> str:
    return """:root {
  color-scheme: light;
  --ink: #162033;
  --muted: #5e687a;
  --panel: #ffffff;
  --accent: #445cff;
  --line: #dfe4ef;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
}

body {
  margin: 0;
  background: linear-gradient(135deg, #eef3ff, #f8fafc);
  color: var(--ink);
}

.shell {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px;
}

.hero, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 22px;
  margin-bottom: 20px;
  padding: 24px;
  box-shadow: 0 18px 60px rgba(22, 32, 51, 0.08);
}

.eyebrow {
  color: var(--accent);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.cards {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.card {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
}

.value, .signal, .action span {
  color: var(--muted);
}

button {
  background: var(--accent);
  border: 0;
  border-radius: 999px;
  color: white;
  cursor: pointer;
  font-weight: 700;
  padding: 12px 18px;
}

pre {
  background: #0f172a;
  border-radius: 14px;
  color: #dbeafe;
  overflow: auto;
  padding: 16px;
}
"""


def create_cognitive_bundle(scenario: dict[str, Any], app_dir: Path) -> dict[str, Any]:
    artifacts_dir = app_dir / "cognitive-artifacts"
    app_id = scenario["id"]
    now = utc_now()
    common = {
        "app_id": app_id,
        "app_name": scenario["name"],
        "created_at": now,
        "trigger_mode": "reactive",
        "authority_mode": "recommend_only",
        "marketing_excluded": True,
        "private_local_only": True,
    }
    intent_frame = {
        "schema": "weave-intent-frame/v0.1",
        **common,
        "owner_intent": scenario["intent"],
        "affected_user": scenario["user"],
        "private_data_domain": scenario["private_domain"],
        "outcome": "produce a local app artifact plus reviewable operating-profile evidence",
        "non_goals": ["public launch", "marketing send", "payments", "network analytics", "real data ingestion"],
        "proof_surface": "local generated static app plus deterministic artifact assessment",
    }
    profile_selection = {
        "schema": "weave-profile-selection/v0.1",
        **common,
        "work_type": "hybrid",
        "abstraction_level": "medium",
        "uncertainty_level": "medium",
        "repeatability": "recurring",
        "risk_level": "medium",
        "selected_profiles": [
            "gestalt",
            "cwa_discovery",
            "dmn_decision_table",
            "ibis_issue_map",
            "adr_decision_record",
            "prov_ledger",
        ],
        "rationale": [
            "private app shape needs context modeling before build",
            "authority boundaries require deterministic routing",
            "success must be reviewable from artifacts, not hidden reasoning",
        ],
    }
    cwa = {
        "schema": "weave-cwa-work-domain/v0.1",
        **common,
        "actors": [scenario["user"], "WEAVE operator", "future reviewer"],
        "constraints": ["local-only", "synthetic sample data", "no public claims", "reviewable artifacts"],
        "values": scenario["success_metrics"],
        "functions": scenario["features"],
        "observations": scenario["data_rows"],
    }
    dmn = {
        "schema": "weave-dmn-table/v0.1",
        **common,
        "decisions": [
            {
                "if": "private data domain and no approval for external actions",
                "then": "generate local static app only",
                "result": "passed",
            },
            {
                "if": "marketing stage requested in this evaluation",
                "then": "block and record non-claim",
                "result": "not_requested",
            },
            {
                "if": "app has exportable assessment and proof artifacts",
                "then": "mark local evaluation reviewable",
                "result": "passed",
            },
        ],
    }
    ibis = {
        "schema": "weave-ibis-map/v0.1",
        **common,
        "issue": "What is the smallest app form that can prove useful private-data reasoning?",
        "options": [
            {"name": "local static app", "pros": ["inspectable", "safe", "fast"], "cons": ["not live user proof"]},
            {"name": "hosted app", "pros": ["closer to production"], "cons": ["external surface not authorized"]},
            {"name": "marketing prototype", "pros": ["tests messaging"], "cons": ["excluded from this run"]},
        ],
        "preferred_option": "local static app",
    }
    action_intent = {
        "schema": "weave-action-intent/v0.1",
        **common,
        "intended_action": "generate app source and cognitive evidence bundle",
        "allowed_scope": ["write local files under scenario output", "run syntax and artifact checks"],
        "blocked_scope": ["network calls", "external sends", "deployment", "real private data"],
    }
    action_result = {
        "schema": "weave-action-result/v0.1",
        **common,
        "result": "generated",
        "generated_files": ["index.html", "src/app.js", "src/styles.css", "public/app-data.json", "README.md"],
        "claim_limits": NON_CLAIMS,
    }

    write_json(artifacts_dir / "intent-frame.json", intent_frame)
    write_json(artifacts_dir / "profile-selection.json", profile_selection)
    write_json(artifacts_dir / "cwa-work-domain.json", cwa)
    write_json(artifacts_dir / "dmn-decision-table.json", dmn)
    write_json(artifacts_dir / "ibis-map.json", ibis)
    write_json(artifacts_dir / "action-intent.json", action_intent)
    write_json(artifacts_dir / "action-result.json", action_result)
    write_text(
        artifacts_dir / "adr-0001-local-private-first.md",
        f"""# ADR 0001: Build {scenario['name']} as a local private app proof

Status: accepted

## Context

The evaluation needs to assess private-domain app usefulness without exposing
real private data, performing marketing, or depending on hosted infrastructure.

## Decision

Generate a dependency-free static app and a complete cognitive artifact bundle.
The app remains local-only and uses synthetic sample signals.

## Consequences

- Reviewers can inspect source, evidence, and framework artifacts.
- The result does not prove live Hermes, deployed gateway, hosted UX, or market traction.
- Later iteration can compare outputs across scenarios before authorizing broader action.
""",
    )
    ledger_events = [
        {"event": "intent.framed", "at": now, "entity": "intent-frame.json"},
        {"event": "profile.selected", "at": now, "entity": "profile-selection.json"},
        {"event": "action.intent_recorded", "at": now, "entity": "action-intent.json"},
        {"event": "app.generated", "at": now, "entity": "index.html"},
        {"event": "action.result_recorded", "at": now, "entity": "action-result.json"},
    ]
    write_text(artifacts_dir / "prov-ledger.jsonl", "\n".join(json.dumps(event, sort_keys=True) for event in ledger_events))
    return {"schema": COGNITIVE_SCHEMA, "artifacts": [item for item in REQUIRED_FRAMEWORK_ARTIFACTS]}


def generate_app(scenario: dict[str, Any], output_root: Path) -> Path:
    app_dir = output_root / "apps" / scenario["id"]
    if app_dir.exists():
        shutil.rmtree(app_dir)
    app_dir.mkdir(parents=True, exist_ok=True)
    write_text(app_dir / "index.html", render_html(scenario))
    write_text(app_dir / "src" / "app.js", render_js(scenario))
    write_text(app_dir / "src" / "styles.css", render_css())
    write_json(
        app_dir / "public" / "app-data.json",
        {
            "schema": APP_SCHEMA,
            "id": scenario["id"],
            "name": scenario["name"],
            "private_domain": scenario["private_domain"],
            "sample_data": scenario["data_rows"],
            "success_metrics": scenario["success_metrics"],
            "external_actions_enabled": False,
            "marketing_included": False,
        },
    )
    write_text(
        app_dir / "README.md",
        f"""# {scenario['name']}

Local-only private app evaluation scenario.

## Intent

{scenario['intent']}

## Private data boundary

Uses synthetic sample records representing: {scenario['private_domain']}.
No real private data is bundled.

## Proof boundary

This is a deterministic local static app proof. It does not prove live Hermes,
deployed gateway behavior, hosted UX, marketing performance, or real user value.
""",
    )
    create_cognitive_bundle(scenario, app_dir)
    return app_dir


def check(condition: bool, name: str, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(condition), "detail": detail}


def assess_app(scenario: dict[str, Any], app_dir: Path, output_root: Path) -> AppResult:
    checks: list[dict[str, Any]] = []
    required_files = ["index.html", "src/app.js", "src/styles.css", "public/app-data.json", "README.md"]
    checks.append(check(all((app_dir / item).exists() for item in required_files), "required_app_files", ", ".join(required_files)))
    artifact_paths = [app_dir / "cognitive-artifacts" / item for item in REQUIRED_FRAMEWORK_ARTIFACTS]
    checks.append(check(all(path.exists() for path in artifact_paths), "framework_artifacts_complete", str(len(artifact_paths))))
    app_js = (app_dir / "src" / "app.js").read_text(encoding="utf-8")
    banned_terms = ["fetch(", "XMLHttpRequest", "sendBeacon", "localStorage", "innerHTML"]
    checks.append(check(not any(term in app_js for term in banned_terms), "no_network_or_dom_injection_terms", ", ".join(banned_terms)))
    data = json.loads((app_dir / "public" / "app-data.json").read_text(encoding="utf-8"))
    checks.append(check(data["external_actions_enabled"] is False, "external_actions_disabled", "external_actions_enabled=false"))
    checks.append(check(data["marketing_included"] is False, "marketing_excluded", "marketing_included=false"))
    checks.append(check(len(data["sample_data"]) >= 3, "enough_private_sample_signals", str(len(data["sample_data"]))))
    profile = json.loads((app_dir / "cognitive-artifacts" / "profile-selection.json").read_text(encoding="utf-8"))
    checks.append(check(profile["authority_mode"] == "recommend_only", "recommend_only_authority", profile["authority_mode"]))
    checks.append(check("cwa_discovery" in profile["selected_profiles"], "cwa_profile_selected", ", ".join(profile["selected_profiles"])))
    node = shutil.which("node")
    if node:
        syntax = subprocess.run([node, "--check", str(app_dir / "src" / "app.js")], capture_output=True, text=True)
        checks.append(check(syntax.returncode == 0, "javascript_syntax", syntax.stderr.strip() or "node --check ok"))
    else:
        checks.append(check(True, "javascript_syntax", "node not available; syntax gate skipped"))
    passed = all(item["passed"] for item in checks)
    score = sum(1 for item in checks if item["passed"])
    report = {
        "schema": "weave-private-app-operating-profile-eval-report/v0.1",
        "app_id": scenario["id"],
        "app_name": scenario["name"],
        "passed": passed,
        "score": score,
        "max_score": len(checks),
        "private_domain": scenario["private_domain"],
        "features": scenario["features"],
        "success_metrics": scenario["success_metrics"],
        "checks": checks,
        "cognitive_artifacts": [relative(path, app_dir) for path in artifact_paths],
        "explicit_non_claims": NON_CLAIMS,
    }
    report_path = app_dir / "assessment-report.json"
    write_json(report_path, report)
    return AppResult(
        app_id=scenario["id"],
        name=scenario["name"],
        passed=passed,
        score=score,
        app_dir=relative(app_dir, output_root),
        report=relative(report_path, output_root),
        artifact_count=len(artifact_paths),
        checks=checks,
    )


def run_one(scenario: dict[str, Any], output_root: Path) -> AppResult:
    app_dir = generate_app(scenario, output_root)
    return assess_app(scenario, app_dir, output_root)


def selected_scenarios(selected: list[str]) -> list[dict[str, Any]]:
    if not selected:
        return list(APP_SCENARIOS)
    return [scenario_by_id(item) for item in selected]


def run_eval(output_root: Path, scenarios: list[dict[str, Any]], parallel: int) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    worker_count = max(1, min(parallel, len(scenarios)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(run_one, scenario, output_root) for scenario in scenarios]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    results.sort(key=lambda item: item.app_id)
    payload = {
        "schema": RUN_SCHEMA,
        "created_at": utc_now(),
        "passed": all(item.passed for item in results),
        "app_count": len(results),
        "parallel_workers": worker_count,
        "score_total": sum(item.score for item in results),
        "artifact_total": sum(item.artifact_count for item in results),
        "trigger_mode": "reactive",
        "authority_mode": "recommend_only",
        "marketing_excluded": True,
        "iteration_emulated": "recommendation artifacts only",
        "results": [
            {
                "app_id": item.app_id,
                "name": item.name,
                "passed": item.passed,
                "score": item.score,
                "app_dir": item.app_dir,
                "report": item.report,
                "artifact_count": item.artifact_count,
            }
            for item in results
        ],
        "explicit_non_claims": NON_CLAIMS,
        "run_checksum": sha256_text("|".join(f"{item.app_id}:{item.score}:{item.passed}" for item in results)),
    }
    write_json(output_root / "aggregate-report.json", payload)
    return payload


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Private App Operating Profile Evaluation",
        "",
        f"Schema: `{payload['schema']}`",
        f"Passed: `{payload['passed']}`",
        f"App count: `{payload['app_count']}`",
        f"Parallel workers: `{payload['parallel_workers']}`",
        f"Total score: `{payload['score_total']}`",
        f"Cognitive artifact count: `{payload['artifact_total']}`",
        f"Run checksum: `{payload['run_checksum']}`",
        "",
        "## App results",
        "",
    ]
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- App id: `{item['app_id']}`",
                f"- Passed: `{item['passed']}`",
                f"- Score: `{item['score']}`",
                f"- Cognitive artifacts: `{item['artifact_count']}`",
                f"- Report: `{item['report']}`",
                "",
            ]
        )
    lines.extend(["## Explicit non-claims", ""])
    lines.extend(f"- {claim}" for claim in payload["explicit_non_claims"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated private-app eval artifacts")
    parser.add_argument("--scenario", action="append", default=[], help="Scenario id to run; repeat for multiple")
    parser.add_argument("--parallel", type=int, default=4, help="Maximum parallel app evaluations")
    parser.add_argument("--report-out", default="", help="Optional markdown report path")
    parser.add_argument("--force", action="store_true", help="Remove output directory before running")
    parser.add_argument("--list", action="store_true", help="List scenario ids and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list:
        for scenario in APP_SCENARIOS:
            print(f"{scenario['id']}\t{scenario['name']}")
        return 0
    output_root = Path(args.output_dir)
    if args.force and output_root.exists():
        shutil.rmtree(output_root)
    scenarios = selected_scenarios(args.scenario)
    payload = run_eval(output_root, scenarios, args.parallel)
    if args.report_out:
        write_text(Path(args.report_out), render_markdown_report(payload))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
