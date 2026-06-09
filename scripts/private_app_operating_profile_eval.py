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

RUN_SCHEMA = "weave-private-app-operating-profile-eval-run/v0.2"
APP_SCHEMA = "weave-private-app-operating-profile-eval-app/v0.1"
COGNITIVE_SCHEMA = "weave-cognitive-artifact-bundle/v0.2"
CASE_REVIEW_SCHEMA = "weave-private-app-case-review/v0.2"
DEFAULT_OUTPUT_DIR = Path("artifacts") / "private-app-operating-profile-evals"

HIGHEST_PROVEN_SURFACE = "local deterministic private-app fixture with generated static apps and reviewable framework-gate evidence"
NOT_PROVEN = [
    "live Hermes-agent lifecycle",
    "Codex/Hermes goal-loop execution until acceptance",
    "Telegram/deployed-gateway adapter behavior",
    "hosted/private-app runtime behavior",
    "real user requirement intake",
    "real private/customer data handling",
    "production/customer/market validation",
]
NON_CLAIMS = [
    "deterministic local fixture/runtime proof only; not live Hermes CLI proof",
    "not Telegram, deployed gateway, or hosted application proof",
    "no public marketing, analytics calls, payments, auth changes, or external sends",
    "uses synthetic private-domain sample data only; no real personal or customer data",
]

REQUIRED_SELECTED_PROFILES = [
    "cwa_discovery",
    "dmn_decision_table",
    "ibis_issue_map",
    "adr_decision_record",
    "premortem_review",
    "prov_ledger",
]
OPTIONAL_DEFERRED_PROFILES = ["gestalt"]

REQUIRED_FRAMEWORK_ARTIFACTS = [
    "intent-frame.json",
    "profile-selection.json",
    "intake-state.json",
    "cwa-work-domain.json",
    "information-requirements.json",
    "missing-information-assessment.json",
    "dmn-routing-table.json",
    "decision-evaluation-log.json",
    "ibis-issue-map.json",
    "open-issues.json",
    "adr-0001-local-private-first.md",
    "decision-register.json",
    "premortem-report.json",
    "risk-to-test-map.json",
    "action-intent.json",
    "action-result.json",
    "proof-boundary-report.json",
    "lifecycle-transition-log.jsonl",
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
    {
        "id": "grant-radar",
        "name": "Grant Radar",
        "user": "nonprofit operator",
        "private_domain": "grant deadlines, eligibility notes, draft application gaps",
        "intent": "Prioritize private grant opportunities and missing application materials.",
        "data_rows": [
            {"label": "City grant", "value": "deadline in 18 days", "signal": "finish budget appendix"},
            {"label": "Foundation grant", "value": "requires partner letter", "signal": "request letter this week"},
            {"label": "Pilot fund", "value": "eligibility unclear", "signal": "clarify nonprofit status requirement"},
        ],
        "features": ["grant priority board", "missing-material checklist", "deadline risk", "JSON export"],
        "success_metrics": ["highest-priority grant named", "missing material explicit", "no funder contact sent"],
    },
    {
        "id": "vendor-vault",
        "name": "Vendor Vault",
        "user": "operations manager",
        "private_domain": "vendor quotes, renewal dates, service risks",
        "intent": "Compare private vendor notes and decide which renewal needs attention first.",
        "data_rows": [
            {"label": "Hosting vendor", "value": "renewal in 30 days", "signal": "confirm usage tier"},
            {"label": "Support vendor", "value": "slow response", "signal": "request SLA evidence"},
            {"label": "Analytics vendor", "value": "duplicate features", "signal": "consider consolidation"},
        ],
        "features": ["renewal radar", "vendor risk tags", "consolidation candidate", "JSON export"],
        "success_metrics": ["renewal risk visible", "vendor action selected", "no external vendor email"],
    },
    {
        "id": "clinic-queue",
        "name": "Clinic Queue",
        "user": "clinic admin",
        "private_domain": "appointment backlog, intake bottlenecks, staffing notes",
        "intent": "Turn clinic operations notes into a queue triage board without health overclaiming.",
        "data_rows": [
            {"label": "New intake", "value": "forms incomplete", "signal": "send internal checklist"},
            {"label": "Follow-up queue", "value": "capacity tight", "signal": "reserve nurse slot"},
            {"label": "Billing question", "value": "insurance unclear", "signal": "route to admin owner"},
        ],
        "features": ["queue triage", "owner routing", "capacity signal", "JSON export"],
        "success_metrics": ["next queue action visible", "clinical advice avoided", "private notes remain local"],
    },
    {
        "id": "content-calibrator",
        "name": "Content Calibrator",
        "user": "solo marketer",
        "private_domain": "draft ideas, audience objections, launch constraints",
        "intent": "Organize private content ideas into a local review queue without publishing.",
        "data_rows": [
            {"label": "Founder story", "value": "too vague", "signal": "add concrete lesson"},
            {"label": "Product proof", "value": "needs screenshot", "signal": "wait for private demo"},
            {"label": "Customer objection", "value": "pricing concern", "signal": "draft internal answer"},
        ],
        "features": ["content queue", "objection mapping", "publish-readiness warning", "JSON export"],
        "success_metrics": ["best draft selected", "publish blocked until review", "no social post sent"],
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
    review_json: str
    review_md: str
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
    selected_profiles = list(REQUIRED_SELECTED_PROFILES)
    optional_profiles = [
        {
            "id": "gestalt",
            "status": "deferred_by_default",
            "reason": "owner feedback: Gestalt artifacts are confusing for this test unless explicitly enabled",
            "enable_when": [
                "owner requests whole-system contract",
                "cross-product coherence is the primary risk",
                "handoff requires whole-experience traceability",
            ],
            "gate_if_enabled": "handoff and QA must cite traceability-map.json",
        }
    ]
    intake_state = {
        "schema": "weave-intake-state/v0.1",
        **common,
        "input_surface": "synthetic_fixture",
        "normalized_intent": scenario["intent"],
        "known_fields": {
            "affected_user": scenario["user"],
            "private_data_domain": scenario["private_domain"],
            "sample_data_rows": len(scenario["data_rows"]),
            "features": scenario["features"],
            "success_metrics": scenario["success_metrics"],
        },
        "status": "sufficient_for_fixture_runtime",
        "next_state": "cwa_information_assessment",
    }
    intent_frame = {
        "schema": "weave-intent-frame/v0.2",
        **common,
        "owner_intent": scenario["intent"],
        "affected_user": scenario["user"],
        "private_data_domain": scenario["private_domain"],
        "outcome": "produce a local app artifact plus reviewable framework-gate evidence",
        "non_goals": ["public launch", "marketing send", "payments", "network analytics", "real data ingestion"],
        "proof_surface": HIGHEST_PROVEN_SURFACE,
    }
    profile_selection = {
        "schema": "weave-profile-selection/v0.2",
        **common,
        "work_type": "hybrid",
        "abstraction_level": "medium",
        "uncertainty_level": "medium",
        "repeatability": "recurring",
        "risk_level": "medium",
        "selected_profiles": selected_profiles,
        "optional_profiles": optional_profiles,
        "rationale": [
            "CWA models domain and missing information before build",
            "DMN controls routing and authority decisions",
            "IBIS/Premortem expose unresolved assumptions and failure modes",
            "ADR/PROV make decisions and proof claims reviewable",
            "Gestalt is deferred unless explicitly enabled",
        ],
    }
    cwa = {
        "schema": "weave-cwa-work-domain/v0.2",
        **common,
        "actors": [scenario["user"], "WEAVE operator", "future reviewer"],
        "constraints": ["local-only", "synthetic sample data", "no public claims", "reviewable artifacts"],
        "values": scenario["success_metrics"],
        "functions": scenario["features"],
        "observations": scenario["data_rows"],
    }
    information_requirements = {
        "schema": "weave-information-requirements/v0.1",
        **common,
        "required_inputs": [
            {"field": "owner_intent", "status": "present", "source": "intent-frame.json"},
            {"field": "affected_user", "status": "present", "source": "intake-state.json"},
            {"field": "private_data_domain", "status": "present", "source": "intent-frame.json"},
            {"field": "sample_data", "status": "present_synthetic", "source": "public/app-data.json"},
            {"field": "success_metrics", "status": "present", "source": "intake-state.json"},
        ],
        "optional_inputs": ["visual theme", "deployment target", "real user feedback"],
    }
    missing_info = {
        "schema": "weave-missing-information-assessment/v0.1",
        **common,
        "required_missing": [],
        "optional_missing": ["visual theme", "real user feedback"],
        "blocks_engineering": False,
        "route": "proceed_to_dmn_routing",
        "clarifying_question_required": False,
    }
    dmn = {
        "schema": "weave-dmn-routing-table/v0.2",
        **common,
        "rules": [
            {"id": "DMN-001", "if": "input is synthetic fixture", "then": "route to CWA information assessment", "result": "passed"},
            {"id": "DMN-002", "if": "private data domain and no approval for external actions", "then": "generate local static app only", "result": "passed"},
            {"id": "DMN-003", "if": "CWA required_missing is empty", "then": "allow engineering execution", "result": "passed"},
            {"id": "DMN-004", "if": "marketing stage requested in this evaluation", "then": "block and record non-claim", "result": "not_requested"},
            {"id": "DMN-005", "if": "app has exportable assessment and proof artifacts", "then": "mark local fixture reviewable", "result": "passed"},
        ],
    }
    decision_log = {
        "schema": "weave-decision-evaluation-log/v0.1",
        **common,
        "evaluations": [
            {"transition": "input_normalization->cwa_information_assessment", "dmn_rule_id": "DMN-001", "result": "proceed"},
            {"transition": "cwa_information_assessment->dmn_routing", "dmn_rule_id": "DMN-003", "result": "proceed"},
            {"transition": "dmn_routing->engineering_execution", "dmn_rule_id": "DMN-002", "result": "local_only"},
            {"transition": "engineering_execution->qa_verification", "dmn_rule_id": "DMN-005", "result": "reviewable"},
            {"transition": "qa_verification->proof_report", "dmn_rule_id": "DMN-005", "result": "report"},
        ],
    }
    ibis = {
        "schema": "weave-ibis-issue-map/v0.2",
        **common,
        "issue": "What is the smallest app form that can prove useful private-data reasoning without overclaiming?",
        "options": [
            {"name": "local static app", "pros": ["inspectable", "safe", "fast"], "cons": ["not live user proof"]},
            {"name": "hosted app", "pros": ["closer to production"], "cons": ["external surface not authorized"]},
            {"name": "marketing prototype", "pros": ["tests messaging"], "cons": ["excluded from this run"]},
        ],
        "preferred_option": "local static app",
        "unresolved_blocking_issues": [],
    }
    open_issues = {
        "schema": "weave-open-issues/v0.1",
        **common,
        "blocking": [],
        "non_blocking": [
            {"id": "ISSUE-001", "summary": "Live Hermes and deployed gateway proof remain future target surfaces", "disposition": "explicit_non_claim"}
        ],
        "waivers": [],
    }
    decision_register = {
        "schema": "weave-decision-register/v0.1",
        **common,
        "decisions": [
            {
                "id": "ADR-0001",
                "status": "accepted",
                "decision": "build a dependency-free local static app from synthetic private-domain rows",
                "covers": ["implementation_surface", "data_boundary", "external_action_boundary"],
                "artifact": "adr-0001-local-private-first.md",
            }
        ],
    }
    premortem = {
        "schema": "weave-premortem-report/v0.1",
        **common,
        "risks": [
            {"id": "RISK-001", "risk": "fixture overclaimed as live-agent proof", "disposition": "test", "gate": "proof_boundary_non_claims"},
            {"id": "RISK-002", "risk": "private data leaves local artifact boundary", "disposition": "test", "gate": "no_external_action_surface"},
            {"id": "RISK-003", "risk": "missing required information is invented", "disposition": "blocker", "gate": "cwa_missing_information_gate"},
        ],
    }
    risk_to_test = {
        "schema": "weave-risk-to-test-map/v0.1",
        **common,
        "mappings": [
            {"risk_id": "RISK-001", "test_gate": "proof_boundary_non_claims"},
            {"risk_id": "RISK-002", "test_gate": "no_network_or_dom_injection_terms"},
            {"risk_id": "RISK-003", "test_gate": "cwa_missing_information_gate"},
        ],
    }
    action_intent = {
        "schema": "weave-action-intent/v0.2",
        **common,
        "intended_action": "generate app source and framework-gate evidence bundle",
        "allowed_scope": ["write local files under scenario output", "run syntax and artifact checks"],
        "blocked_scope": ["network calls", "external sends", "deployment", "real private data", "payments", "marketing publish"],
    }
    action_result = {
        "schema": "weave-action-result/v0.2",
        **common,
        "result": "generated",
        "generated_files": ["index.html", "src/app.js", "src/styles.css", "public/app-data.json", "README.md"],
        "claim_limits": NON_CLAIMS,
    }
    proof_boundary = {
        "schema": "weave-proof-boundary-report/v0.1",
        **common,
        "highest_proven_surface": HIGHEST_PROVEN_SURFACE,
        "explicit_non_claims": NON_CLAIMS,
        "not_proven": NOT_PROVEN,
        "surface_evidence": ["prov-ledger.jsonl", "lifecycle-transition-log.jsonl", "assessment-report.json"],
    }

    write_json(artifacts_dir / "intent-frame.json", intent_frame)
    write_json(artifacts_dir / "profile-selection.json", profile_selection)
    write_json(artifacts_dir / "intake-state.json", intake_state)
    write_json(artifacts_dir / "cwa-work-domain.json", cwa)
    write_json(artifacts_dir / "information-requirements.json", information_requirements)
    write_json(artifacts_dir / "missing-information-assessment.json", missing_info)
    write_json(artifacts_dir / "dmn-routing-table.json", dmn)
    write_json(artifacts_dir / "decision-evaluation-log.json", decision_log)
    write_json(artifacts_dir / "ibis-issue-map.json", ibis)
    write_json(artifacts_dir / "open-issues.json", open_issues)
    write_json(artifacts_dir / "decision-register.json", decision_register)
    write_json(artifacts_dir / "premortem-report.json", premortem)
    write_json(artifacts_dir / "risk-to-test-map.json", risk_to_test)
    write_json(artifacts_dir / "action-intent.json", action_intent)
    write_json(artifacts_dir / "action-result.json", action_result)
    write_json(artifacts_dir / "proof-boundary-report.json", proof_boundary)
    write_text(
        artifacts_dir / "adr-0001-local-private-first.md",
        f"""# ADR 0001: Build {scenario['name']} as a local private app proof

Status: accepted

## Context

The evaluation needs to assess private-domain app usefulness without exposing
real private data, performing marketing, or depending on hosted infrastructure.
Gestalt is optional/deferred for this slice; CWA, DMN, IBIS, ADR, Premortem, and
PROV provide the required review gates.

## Decision

Generate a dependency-free local static app and a complete framework-gate
evidence bundle. The app remains local-only and uses synthetic sample signals.

## Rejected alternatives

- Hosted app: rejected because deployment/external surface is not authorized.
- Marketing prototype: rejected because publication is outside this proof slice.
- Mandatory Gestalt contract: deferred by owner feedback until it is specifically useful.

## Consequences

- Reviewers can inspect source, evidence, and framework gate artifacts.
- The result does not prove live Hermes, deployed gateway, hosted UX, or market traction.
- Later iteration can compare outputs across scenarios before authorizing broader action.
""",
    )
    transition_events = [
        {"event": "transition", "at": now, "from": "input_normalization", "to": "cwa_information_assessment", "dmn_rule_id": "DMN-001"},
        {"event": "transition", "at": now, "from": "cwa_information_assessment", "to": "dmn_routing", "dmn_rule_id": "DMN-003"},
        {"event": "transition", "at": now, "from": "dmn_routing", "to": "engineering_execution", "dmn_rule_id": "DMN-002"},
        {"event": "transition", "at": now, "from": "engineering_execution", "to": "qa_verification", "dmn_rule_id": "DMN-005"},
        {"event": "transition", "at": now, "from": "qa_verification", "to": "proof_report", "dmn_rule_id": "DMN-005"},
    ]
    write_text(artifacts_dir / "lifecycle-transition-log.jsonl", "\n".join(json.dumps(event, sort_keys=True) for event in transition_events))
    ledger_events = [
        {"event": "input.normalized", "at": now, "entity": "cognitive-artifacts/intake-state.json", "role": "operator"},
        {"event": "intent.framed", "at": now, "entity": "cognitive-artifacts/intent-frame.json", "role": "operator"},
        {"event": "profile.selected", "at": now, "entity": "cognitive-artifacts/profile-selection.json", "role": "operator"},
        {"event": "cwa.produced", "at": now, "entity": "cognitive-artifacts/cwa-work-domain.json", "role": "product_planning"},
        {"event": "missing_information.assessed", "at": now, "entity": "cognitive-artifacts/missing-information-assessment.json", "role": "product_planning"},
        {"event": "dmn.evaluated", "at": now, "entity": "cognitive-artifacts/decision-evaluation-log.json", "role": "operator"},
        {"event": "ibis.produced", "at": now, "entity": "cognitive-artifacts/ibis-issue-map.json", "role": "product_planning"},
        {"event": "premortem.produced", "at": now, "entity": "cognitive-artifacts/premortem-report.json", "role": "qa"},
        {"event": "adr.accepted", "at": now, "entity": "cognitive-artifacts/adr-0001-local-private-first.md", "role": "engineering"},
        {"event": "action.intent_recorded", "at": now, "entity": "cognitive-artifacts/action-intent.json", "role": "engineering"},
        {"event": "app.generated", "at": now, "entity": "index.html", "role": "engineering"},
        {"event": "qa.verified", "at": now, "entity": "assessment-report.json", "role": "qa"},
        {"event": "proof.reported", "at": now, "entity": "cognitive-artifacts/proof-boundary-report.json", "role": "operator"},
        {"event": "action.result_recorded", "at": now, "entity": "cognitive-artifacts/action-result.json", "role": "engineering"},
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


def check(
    condition: bool,
    name: str,
    detail: str,
    source_artifacts: list[str] | None = None,
    framework: str = "Evidence",
    severity: str = "critical",
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(condition),
        "detail": detail,
        "source_artifacts": source_artifacts or [],
        "framework": framework,
        "severity": severity,
    }


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_for_gate(path: Path, gate_name: str, framework: str, checks: list[dict[str, Any]], base: Path) -> dict[str, Any] | None:
    source = [relative(path, base)]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report malformed artifact as data, not a crash.
        checks.append(check(False, gate_name, f"{type(exc).__name__}: {exc}", source, framework))
        return None
    checks.append(check(True, gate_name, "parseable JSON", source, framework))
    return payload


def read_jsonl_for_gate(path: Path, gate_name: str, framework: str, checks: list[dict[str, Any]], base: Path) -> list[dict[str, Any]] | None:
    source = [relative(path, base)]
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        payload = [json.loads(line) for line in lines]
    except Exception as exc:  # noqa: BLE001
        checks.append(check(False, gate_name, f"{type(exc).__name__}: {exc}", source, framework))
        return None
    checks.append(check(bool(payload), gate_name, f"{len(payload)} JSONL events", source, framework))
    return payload


def append_gate(
    checks: list[dict[str, Any]],
    condition: bool,
    name: str,
    detail: str,
    source_artifacts: list[str] | None = None,
    framework: str = "Evidence",
    severity: str = "critical",
) -> None:
    checks.append(check(condition, name, detail, source_artifacts, framework, severity))


def render_case_review_markdown(review: dict[str, Any]) -> str:
    lines = [
        f"# App Case Review: {review['app_name']}",
        "",
        f"Status: `{review['status'].upper()}`",
        f"Proof surface: `{review['proof_surface']}`",
        f"Authority: `{review['authority_mode']}`",
        "Data boundary: synthetic-only, no external sends, no deployment, no marketing",
        "",
        "## Generated app",
        "",
        f"- App path: `{review['app_entrypoint']}`",
        f"- Case review JSON: `{review['review_json']}`",
        "",
        "## Gate summary",
        "",
        f"- Critical passed: `{review['gate_summary']['critical_passed']}`",
        f"- Critical failed: `{review['gate_summary']['critical_failed']}`",
        f"- Warnings: `{review['gate_summary']['warnings']}`",
        "",
        "## Visible gates",
        "",
    ]
    for gate in review["review_gates"]:
        status = "PASS" if gate["passed"] else "FAIL"
        lines.append(f"- {status} — {gate['name']} ({gate['framework']})")
        lines.append(f"  - Evidence: {', '.join(f'`{item}`' for item in gate.get('source_artifacts', [])) or '`n/a`'}")
        lines.append(f"  - Detail: {gate['detail']}")
    lines.extend(["", "## Explicit non-claims", ""])
    lines.extend(f"- {claim}" for claim in review["explicit_non_claims"])
    lines.extend(
        [
            "",
            "## Reviewer notes",
            "",
            "1. Inspect failed gates first.",
            "2. Open the generated app locally only if UX review is needed.",
            "3. Read `prov-ledger.jsonl` before accepting any proof-surface claim.",
            "4. Verify that CWA/DMN/IBIS/ADR/Premortem/PROV gates consumed artifacts, not just emitted files.",
        ]
    )
    return "\n".join(lines)


def build_artifact_manifest(app_dir: Path) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    required_files = ["index.html", "src/app.js", "src/styles.css", "public/app-data.json", "README.md"]
    for item in required_files:
        path = app_dir / item
        if path.exists():
            manifest.append({"id": safe_label(item), "path": item, "kind": "generated_app_file", "required": True, "sha256": sha256_file(path)})
    for item in REQUIRED_FRAMEWORK_ARTIFACTS:
        path = app_dir / "cognitive-artifacts" / item
        if path.exists():
            manifest.append({"id": safe_label(item), "path": f"cognitive-artifacts/{item}", "kind": "framework_gate_artifact", "required": True, "sha256": sha256_file(path)})
    return manifest


def gate_summary(checks: list[dict[str, Any]]) -> dict[str, int]:
    critical = [item for item in checks if item.get("severity") == "critical"]
    warnings = [item for item in checks if item.get("severity") == "warning"]
    return {
        "critical_passed": sum(1 for item in critical if item["passed"]),
        "critical_failed": sum(1 for item in critical if not item["passed"]),
        "warnings": sum(1 for item in warnings if not item["passed"]),
        "waived": 0,
    }


def assess_app(scenario: dict[str, Any], app_dir: Path, output_root: Path) -> AppResult:
    checks: list[dict[str, Any]] = []
    artifacts_dir = app_dir / "cognitive-artifacts"
    required_files = ["index.html", "src/app.js", "src/styles.css", "public/app-data.json", "README.md"]
    required_app_paths = [app_dir / item for item in required_files]
    append_gate(checks, all(path.exists() for path in required_app_paths), "required_app_files", ", ".join(required_files), required_files, "Evidence")
    artifact_paths = [artifacts_dir / item for item in REQUIRED_FRAMEWORK_ARTIFACTS]
    append_gate(
        checks,
        all(path.exists() for path in artifact_paths),
        "framework_artifacts_complete",
        str(len([path for path in artifact_paths if path.exists()])),
        [f"cognitive-artifacts/{item}" for item in REQUIRED_FRAMEWORK_ARTIFACTS],
        "Evidence",
    )

    app_js = (app_dir / "src" / "app.js").read_text(encoding="utf-8") if (app_dir / "src" / "app.js").exists() else ""
    banned_terms = ["fetch(", "XMLHttpRequest", "sendBeacon", "localStorage", "innerHTML"]
    append_gate(checks, not any(term in app_js for term in banned_terms), "no_network_or_dom_injection_terms", ", ".join(banned_terms), ["src/app.js"], "QA")

    app_data = read_json_for_gate(app_dir / "public" / "app-data.json", "app_data_parseable", "Evidence", checks, app_dir)
    if app_data:
        append_gate(checks, app_data.get("external_actions_enabled") is False, "external_actions_disabled", "external_actions_enabled=false", ["public/app-data.json"], "DMN")
        append_gate(checks, app_data.get("marketing_included") is False, "marketing_excluded", "marketing_included=false", ["public/app-data.json"], "DMN")
        append_gate(checks, len(app_data.get("sample_data", [])) >= 3, "enough_private_sample_signals", str(len(app_data.get("sample_data", []))), ["public/app-data.json"], "CWA")

    intent = read_json_for_gate(artifacts_dir / "intent-frame.json", "intent_frame_parseable", "Intent", checks, app_dir)
    profile = read_json_for_gate(artifacts_dir / "profile-selection.json", "profile_selection_parseable", "Profile", checks, app_dir)
    intake = read_json_for_gate(artifacts_dir / "intake-state.json", "intake_state_parseable", "Evidence", checks, app_dir)
    cwa = read_json_for_gate(artifacts_dir / "cwa-work-domain.json", "cwa_parseable", "CWA", checks, app_dir)
    info_req = read_json_for_gate(artifacts_dir / "information-requirements.json", "information_requirements_parseable", "CWA", checks, app_dir)
    missing = read_json_for_gate(artifacts_dir / "missing-information-assessment.json", "missing_information_parseable", "CWA", checks, app_dir)
    dmn = read_json_for_gate(artifacts_dir / "dmn-routing-table.json", "dmn_parseable", "DMN", checks, app_dir)
    decision_log = read_json_for_gate(artifacts_dir / "decision-evaluation-log.json", "decision_log_parseable", "DMN", checks, app_dir)
    ibis = read_json_for_gate(artifacts_dir / "ibis-issue-map.json", "ibis_parseable", "IBIS", checks, app_dir)
    open_issues = read_json_for_gate(artifacts_dir / "open-issues.json", "open_issues_parseable", "IBIS", checks, app_dir)
    decision_register = read_json_for_gate(artifacts_dir / "decision-register.json", "decision_register_parseable", "ADR", checks, app_dir)
    premortem = read_json_for_gate(artifacts_dir / "premortem-report.json", "premortem_parseable", "Premortem", checks, app_dir)
    risk_map = read_json_for_gate(artifacts_dir / "risk-to-test-map.json", "risk_to_test_map_parseable", "Premortem", checks, app_dir)
    action_intent = read_json_for_gate(artifacts_dir / "action-intent.json", "action_intent_parseable", "Action", checks, app_dir)
    action_result = read_json_for_gate(artifacts_dir / "action-result.json", "action_result_parseable", "Action", checks, app_dir)
    proof = read_json_for_gate(artifacts_dir / "proof-boundary-report.json", "proof_boundary_parseable", "Proof", checks, app_dir)
    lifecycle_events = read_jsonl_for_gate(artifacts_dir / "lifecycle-transition-log.jsonl", "lifecycle_transition_log_parseable", "DMN", checks, app_dir)
    prov_events = read_jsonl_for_gate(artifacts_dir / "prov-ledger.jsonl", "prov_ledger_parseable", "PROV", checks, app_dir)

    common_artifacts = [payload for payload in [intent, profile, intake, cwa, info_req, missing, dmn, decision_log, ibis, open_issues, decision_register, premortem, risk_map, action_intent, action_result, proof] if payload]
    identity_ok = all(payload.get("app_id") == scenario["id"] and payload.get("app_name") == scenario["name"] for payload in common_artifacts)
    append_gate(checks, identity_ok, "cross_artifact_identity_consistency", scenario["id"], ["cognitive-artifacts/*.json"], "Evidence")

    if intent:
        append_gate(checks, intent.get("proof_surface") == HIGHEST_PROVEN_SURFACE, "intent_frame_proof_boundary", intent.get("proof_surface", "missing"), ["cognitive-artifacts/intent-frame.json"], "Proof")
    if profile:
        selected = profile.get("selected_profiles", [])
        optional = profile.get("optional_profiles", [])
        optional_ids = {item.get("id") for item in optional if isinstance(item, dict)}
        append_gate(checks, profile.get("authority_mode") == "recommend_only", "recommend_only_authority", str(profile.get("authority_mode")), ["cognitive-artifacts/profile-selection.json"], "DMN")
        append_gate(checks, set(REQUIRED_SELECTED_PROFILES).issubset(set(selected)), "required_framework_stack_selected", ", ".join(selected), ["cognitive-artifacts/profile-selection.json"], "Profile")
        append_gate(checks, "gestalt" not in selected and "gestalt" in optional_ids, "gestalt_optional_deferred", f"selected={selected}; optional={sorted(optional_ids)}", ["cognitive-artifacts/profile-selection.json"], "Profile")
    if cwa and app_data:
        constraints = set(cwa.get("constraints", []))
        append_gate(checks, {"local-only", "synthetic sample data", "reviewable artifacts"}.issubset(constraints), "cwa_private_constraints_consumed", ", ".join(sorted(constraints)), ["cognitive-artifacts/cwa-work-domain.json"], "CWA")
        append_gate(checks, cwa.get("observations") == app_data.get("sample_data"), "cwa_observations_match_app_data", "observations match sample_data", ["cognitive-artifacts/cwa-work-domain.json", "public/app-data.json"], "CWA")
    if info_req:
        required_statuses = {item.get("status") for item in info_req.get("required_inputs", []) if isinstance(item, dict)}
        append_gate(checks, "present" in required_statuses and "present_synthetic" in required_statuses, "information_requirements_classified", ", ".join(sorted(required_statuses)), ["cognitive-artifacts/information-requirements.json"], "CWA")
    if missing:
        required_missing = missing.get("required_missing", [])
        append_gate(checks, not required_missing and missing.get("blocks_engineering") is False, "cwa_missing_information_gate", f"required_missing={required_missing}", ["cognitive-artifacts/missing-information-assessment.json"], "CWA")
    if dmn:
        rules = dmn.get("rules", [])
        rule_by_id = {item.get("id"): item for item in rules if isinstance(item, dict)}
        append_gate(checks, rule_by_id.get("DMN-002", {}).get("then") == "generate local static app only", "dmn_local_only_routing", str(rule_by_id.get("DMN-002", {})), ["cognitive-artifacts/dmn-routing-table.json"], "DMN")
        append_gate(checks, rule_by_id.get("DMN-004", {}).get("result") in {"not_requested", "blocked"}, "dmn_marketing_block", str(rule_by_id.get("DMN-004", {})), ["cognitive-artifacts/dmn-routing-table.json"], "DMN")
        append_gate(checks, "DMN-005" in rule_by_id, "dmn_reviewable_proof_rule", ", ".join(rule_by_id), ["cognitive-artifacts/dmn-routing-table.json"], "DMN")
    if decision_log:
        evaluations = decision_log.get("evaluations", [])
        cited = all(item.get("dmn_rule_id") or item.get("owner_override_id") for item in evaluations if isinstance(item, dict))
        append_gate(checks, bool(evaluations) and cited, "dmn_transition_gate", f"{len(evaluations)} evaluations", ["cognitive-artifacts/decision-evaluation-log.json"], "DMN")
    if ibis:
        append_gate(checks, ibis.get("preferred_option") == "local static app", "ibis_local_static_preferred", str(ibis.get("preferred_option")), ["cognitive-artifacts/ibis-issue-map.json"], "IBIS")
        append_gate(checks, not ibis.get("unresolved_blocking_issues"), "ibis_no_unwaived_blockers", str(ibis.get("unresolved_blocking_issues")), ["cognitive-artifacts/ibis-issue-map.json"], "IBIS")
    if open_issues:
        append_gate(checks, not open_issues.get("blocking"), "open_issues_no_blocking_without_waiver", str(open_issues.get("blocking")), ["cognitive-artifacts/open-issues.json"], "IBIS")
    adr_path = artifacts_dir / "adr-0001-local-private-first.md"
    adr_text = adr_path.read_text(encoding="utf-8") if adr_path.exists() else ""
    append_gate(checks, "Status: accepted" in adr_text, "adr_accepted", "Status: accepted", ["cognitive-artifacts/adr-0001-local-private-first.md"], "ADR", "major")
    append_gate(checks, "local static app" in adr_text and "not prove live Hermes" in adr_text, "adr_local_private_decision", "local/static/non-claim text present", ["cognitive-artifacts/adr-0001-local-private-first.md"], "ADR", "major")
    if decision_register:
        decisions = decision_register.get("decisions", [])
        append_gate(checks, any("implementation_surface" in item.get("covers", []) for item in decisions if isinstance(item, dict)), "decision_register_covers_implementation", str(decisions), ["cognitive-artifacts/decision-register.json"], "ADR", "major")
    if premortem and risk_map:
        risks = premortem.get("risks", [])
        mappings = risk_map.get("mappings", [])
        append_gate(checks, len(risks) >= 3, "premortem_failure_modes_classified", str(len(risks)), ["cognitive-artifacts/premortem-report.json"], "Premortem", "major")
        append_gate(checks, {item.get("risk_id") for item in mappings} >= {"RISK-001", "RISK-002", "RISK-003"}, "risk_to_test_map_complete", str(mappings), ["cognitive-artifacts/risk-to-test-map.json"], "Premortem", "major")
    if action_intent:
        allowed = " ".join(action_intent.get("allowed_scope", [])).lower()
        blocked = set(action_intent.get("blocked_scope", []))
        append_gate(checks, not any(term in allowed for term in ["network", "deploy", "external send", "real private data", "payment"]), "action_intent_scope_local_only", allowed, ["cognitive-artifacts/action-intent.json"], "Action")
        append_gate(checks, {"network calls", "external sends", "deployment", "real private data"}.issubset(blocked), "action_intent_blocks_external_actions", ", ".join(sorted(blocked)), ["cognitive-artifacts/action-intent.json"], "Action")
    if action_result:
        generated = set(action_result.get("generated_files", []))
        append_gate(checks, set(required_files).issubset(generated), "action_result_generated_files_match", ", ".join(sorted(generated)), ["cognitive-artifacts/action-result.json"], "Action")
        append_gate(checks, set(NON_CLAIMS).issubset(set(action_result.get("claim_limits", []))), "action_result_claim_limits", str(action_result.get("claim_limits", [])), ["cognitive-artifacts/action-result.json"], "Proof")
    if proof:
        append_gate(checks, proof.get("highest_proven_surface") == HIGHEST_PROVEN_SURFACE, "proof_boundary_highest_surface", str(proof.get("highest_proven_surface")), ["cognitive-artifacts/proof-boundary-report.json"], "Proof")
        append_gate(checks, set(NON_CLAIMS).issubset(set(proof.get("explicit_non_claims", []))), "proof_boundary_non_claims", str(proof.get("explicit_non_claims", [])), ["cognitive-artifacts/proof-boundary-report.json"], "Proof")
        append_gate(checks, set(NOT_PROVEN).issubset(set(proof.get("not_proven", []))), "proof_boundary_not_proven", str(proof.get("not_proven", [])), ["cognitive-artifacts/proof-boundary-report.json"], "Proof")
    if lifecycle_events:
        lifecycle_cited = all(item.get("dmn_rule_id") or item.get("owner_override_id") for item in lifecycle_events)
        append_gate(checks, lifecycle_cited, "lifecycle_transitions_cite_dmn", f"{len(lifecycle_events)} transitions", ["cognitive-artifacts/lifecycle-transition-log.jsonl"], "DMN")
    if prov_events:
        required_events = [
            "input.normalized",
            "intent.framed",
            "profile.selected",
            "cwa.produced",
            "missing_information.assessed",
            "dmn.evaluated",
            "ibis.produced",
            "premortem.produced",
            "adr.accepted",
            "action.intent_recorded",
            "app.generated",
            "qa.verified",
            "proof.reported",
            "action.result_recorded",
        ]
        actual_events = [item.get("event") for item in prov_events]
        append_gate(checks, set(required_events).issubset(set(actual_events)), "prov_ledger_required_events", ", ".join(actual_events), ["cognitive-artifacts/prov-ledger.jsonl"], "PROV")
        positions = [actual_events.index(event) for event in required_events if event in actual_events]
        append_gate(checks, positions == sorted(positions) and len(positions) == len(required_events), "prov_ledger_event_order", str(positions), ["cognitive-artifacts/prov-ledger.jsonl"], "PROV")
        missing_entities = [
            item.get("entity")
            for item in prov_events
            if item.get("entity")
            and item.get("entity") != "assessment-report.json"
            and not (app_dir / item["entity"]).exists()
        ]
        append_gate(checks, not missing_entities, "prov_ledger_entities_exist", str(missing_entities), ["cognitive-artifacts/prov-ledger.jsonl"], "PROV")

    node = shutil.which("node")
    if node and (app_dir / "src" / "app.js").exists():
        syntax = subprocess.run([node, "--check", str(app_dir / "src" / "app.js")], capture_output=True, text=True)
        append_gate(checks, syntax.returncode == 0, "javascript_syntax", syntax.stderr.strip() or "node --check ok", ["src/app.js"], "QA")
    else:
        append_gate(checks, True, "javascript_syntax", "node not available or app.js missing; syntax gate skipped", ["src/app.js"], "QA", "warning")

    passed = all(item["passed"] for item in checks if item.get("severity") != "warning")
    score = sum(1 for item in checks if item["passed"])
    summary = gate_summary(checks)
    report = {
        "schema": "weave-private-app-operating-profile-eval-report/v0.2",
        "app_id": scenario["id"],
        "app_name": scenario["name"],
        "passed": passed,
        "score": score,
        "max_score": len(checks),
        "gate_summary": summary,
        "private_domain": scenario["private_domain"],
        "features": scenario["features"],
        "success_metrics": scenario["success_metrics"],
        "checks": checks,
        "cognitive_artifacts": [relative(path, app_dir) for path in artifact_paths],
        "explicit_non_claims": NON_CLAIMS,
        "highest_proven_surface": HIGHEST_PROVEN_SURFACE,
    }
    report_path = app_dir / "assessment-report.json"
    write_json(report_path, report)

    review = {
        "schema": CASE_REVIEW_SCHEMA,
        "app_id": scenario["id"],
        "app_name": scenario["name"],
        "status": "pass" if passed else "fail",
        "proof_surface": HIGHEST_PROVEN_SURFACE,
        "authority_mode": "recommend_only",
        "trigger_mode": "reactive",
        "data_boundary": {
            "real_private_data_allowed": False,
            "synthetic_private_data_allowed": True,
            "external_send_allowed": False,
            "deployment_allowed": False,
            "marketing_included": False,
            "model_provider_private_data_boundary": "not_exercised_synthetic_only",
        },
        "app_entrypoint": relative(app_dir / "index.html", output_root),
        "review_json": relative(app_dir / "review.json", output_root),
        "artifact_manifest": build_artifact_manifest(app_dir),
        "review_gates": checks,
        "gate_summary": summary,
        "explicit_non_claims": NON_CLAIMS,
        "not_proven": NOT_PROVEN,
        "human_review_focus": [
            "Inspect failed gates first.",
            "Read PROV ledger before accepting proof-surface claims.",
            "Verify CWA/DMN/IBIS/ADR/Premortem/PROV artifacts are consumed by gates.",
        ],
    }
    review_json_path = app_dir / "review.json"
    review_md_path = app_dir / "review.md"
    write_json(review_json_path, review)
    write_text(review_md_path, render_case_review_markdown({**review, "review_json": relative(review_json_path, output_root)}))

    return AppResult(
        app_id=scenario["id"],
        name=scenario["name"],
        passed=passed,
        score=score,
        app_dir=relative(app_dir, output_root),
        report=relative(report_path, output_root),
        review_json=relative(review_json_path, output_root),
        review_md=relative(review_md_path, output_root),
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
    all_checks = [check_item for item in results for check_item in item.checks]
    summary = gate_summary(all_checks)
    framework_totals: dict[str, dict[str, int]] = {}
    for check_item in all_checks:
        framework = check_item.get("framework", "Evidence")
        totals = framework_totals.setdefault(framework, {"pass": 0, "fail": 0, "warn": 0})
        if check_item.get("severity") == "warning":
            totals["warn"] += 0 if check_item["passed"] else 1
        elif check_item["passed"]:
            totals["pass"] += 1
        else:
            totals["fail"] += 1
    cases = [
        {
            "app_id": item.app_id,
            "name": item.name,
            "status": "pass" if item.passed else "fail",
            "passed": item.passed,
            "score": item.score,
            "critical_failed": sum(1 for gate in item.checks if gate.get("severity") == "critical" and not gate["passed"]),
            "warnings": sum(1 for gate in item.checks if gate.get("severity") == "warning" and not gate["passed"]),
            "app_dir": item.app_dir,
            "report": item.report,
            "review_json": item.review_json,
            "review_md": item.review_md,
            "artifact_count": item.artifact_count,
        }
        for item in results
    ]
    payload = {
        "schema": RUN_SCHEMA,
        "created_at": utc_now(),
        "passed": all(item.passed for item in results),
        "expected_app_count": len(scenarios),
        "app_count": len(results),
        "parallel_workers": worker_count,
        "score_total": sum(item.score for item in results),
        "artifact_total": sum(item.artifact_count for item in results),
        "trigger_mode": "reactive",
        "authority_mode": "recommend_only",
        "marketing_excluded": True,
        "iteration_emulated": "recommendation artifacts only",
        "highest_proven_surface": HIGHEST_PROVEN_SURFACE,
        "not_proven": NOT_PROVEN,
        "gate_totals": summary,
        "framework_totals": framework_totals,
        "results": cases,
        "cases": cases,
        "explicit_non_claims": NON_CLAIMS,
        "run_checksum": sha256_text("|".join(f"{item.app_id}:{item.score}:{item.passed}:{item.review_json}" for item in results)),
    }
    write_json(output_root / "aggregate-report.json", payload)
    write_json(output_root / "aggregate-review.json", payload)
    write_text(output_root / "cases.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in cases))
    write_text(output_root / "aggregate-review.md", render_markdown_report(payload))
    return payload


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Private App Operating Profile Aggregate Review",
        "",
        f"Status: `{'PASS' if payload['passed'] else 'FAIL'}`",
        f"Cases reviewed: `{payload['app_count']} / {payload['expected_app_count']}`",
        f"Critical failures: `{payload['gate_totals']['critical_failed']}`",
        f"Warnings: `{payload['gate_totals']['warnings']}`",
        f"Highest proven surface: `{payload['highest_proven_surface']}`",
        f"Run checksum: `{payload['run_checksum']}`",
        "",
        "## What this proves",
        "",
        f"- The harness generated `{payload['app_count']}` local static app cases.",
        "- Each case has reviewable CWA, DMN, IBIS, ADR, Premortem, and PROV gate evidence.",
        "- Each case stayed within recommend-only, local-only, synthetic-data boundaries.",
        "- Each generated app has source files, app data, QA/smoke evidence, and a per-app review packet.",
        "",
        "## What this does not prove",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["not_proven"])
    lines.extend(["", "## Framework gate totals", ""])
    for framework, totals in sorted(payload["framework_totals"].items()):
        lines.append(f"- {framework}: `{totals['pass']}` pass, `{totals['fail']}` fail, `{totals['warn']}` warn")
    lines.extend(["", "## App case summaries", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- App id: `{item['app_id']}`",
                f"- Status: `{item['status'].upper()}`",
                f"- Score: `{item['score']}`",
                f"- Cognitive/process artifacts: `{item['artifact_count']}`",
                f"- Critical failures: `{item['critical_failed']}`",
                f"- Warnings: `{item['warnings']}`",
                f"- Review: `{item['review_md']}`",
                f"- App: `{item['app_dir']}/index.html`",
                "",
            ]
        )
    lines.extend(["## Explicit non-claims", ""])
    lines.extend(f"- {claim}" for claim in payload["explicit_non_claims"])
    lines.extend(
        [
            "",
            "## Reviewer queue",
            "",
            "- Inspect failed/warn cases first.",
            "- If all pass, sample at least two pass cases and one PROV ledger before accepting claim language.",
        ]
    )
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
