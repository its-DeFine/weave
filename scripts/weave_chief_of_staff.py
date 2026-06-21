#!/usr/bin/env python3
"""Portable Chief of Staff state and snapshot helpers for WEAVE.

This module is local-only and public-safe. It creates inspectable WEAVE home
files, prints the compact state line, and renders a static cockpit snapshot.
It does not contact Codex, Hermes, Linear, GitHub, model providers, deployment
systems, or public channels.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


SCHEMA = "weave-chief-of-staff/v0.1"
SNAPSHOT_SCHEMA = "weave-chief-of-staff-snapshot/v0.1"
DEFAULT_SOURCE_URL = "https://github.com/its-DeFine/weave"
DEFAULT_OWNER_STYLE = "decision-first, proof-backed, concise, explicit about unknowns"
DEFAULT_STOP_BOUNDARIES = [
    "raw_secrets",
    "private_topology",
    "production_deploy",
    "public_send",
    "paid_action",
    "credential_collection",
]

LIFECYCLE_STAGES = [
    ("intent", "Intent"),
    ("requirements", "Requirements"),
    ("context_architecture", "Context / Architecture"),
    ("task_breakdown", "Task Breakdown"),
    ("build", "Build"),
    ("review", "Review"),
    ("qa", "QA"),
    ("deploy_readiness", "Deploy Readiness"),
    ("publish", "Publish"),
    ("marketing_iteration_analysis", "Marketing / Iteration / Analysis"),
]


class ChiefOfStaffError(Exception):
    """Raised when the Chief of Staff local state cannot be used safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip().lower()).strip("-.")
    return slug[:80] or "app"


def state_path(home: Path) -> Path:
    return home / "state.json"


def app_dir(home: Path, app_id: str) -> Path:
    return home / "apps" / app_id


def default_lifecycle(active_stage: str = "intent") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for stage_id, label in LIFECYCLE_STAGES:
        state = "active" if stage_id == active_stage else "not_started"
        rows.append(
            {
                "id": stage_id,
                "label": label,
                "state": state,
                "proof": "missing" if stage_id == active_stage else "not_required_yet",
            }
        )
    return rows


def default_worker_lanes() -> list[dict[str, str]]:
    return [
        {
            "id": "cos-home",
            "label": "Chief of Staff home",
            "surface": "codex_or_hermes",
            "state": "ready",
            "next": "collect owner intent and app constraints",
            "proof": "local WEAVE home exists",
        },
        {
            "id": "codex-worker",
            "label": "Codex worker lane",
            "surface": "codex",
            "state": "available_when_spawned",
            "next": "create bounded packet before repo or code work",
            "proof": "packet required before work claim",
        },
        {
            "id": "hermes-worker",
            "label": "Hermes worker lane",
            "surface": "hermes",
            "state": "gated_until_runtime_verified",
            "next": "verify adapter before live Hermes claims",
            "proof": "no live Hermes claim in this slice",
        },
    ]


def build_state(args: Any) -> dict[str, Any]:
    app_id = slugify(args.app_id)
    now = utc_now()
    surface = args.surface
    app_name = args.app_name.strip() or "New App"
    owner_name = args.owner_name.strip() or "owner"
    task_id = "WEAVE-0001"
    return {
        "schema": SCHEMA,
        "created_at": now,
        "updated_at": now,
        "live_effects": False,
        "secret_value_printed": False,
        "source": {
            "url": args.source_url,
            "current_version": args.weave_version,
            "update_mode": args.update_mode,
            "last_checked_at": "",
        },
        "home": {
            "label": "Chief of Staff",
            "surface": surface,
            "state": "ready",
            "description": "One pinned operational home for app lifecycle, tasks, proof, blockers, workers, and WEAVE updates.",
        },
        "owner": {
            "display_name": owner_name,
            "communication_style": args.communication_style.strip() or DEFAULT_OWNER_STYLE,
            "decision_boundary": "act by default for safe, reversible, in-scope work; stop at hard gates",
        },
        "adapters": {
            "codex": {
                "state": "primary_surface" if surface in {"codex", "both"} else "available_if_user_uses_codex",
                "claim": "Codex can carry the Chief of Staff prompt and spawn bounded local work packets.",
            },
            "hermes": {
                "state": "requires_runtime_verification" if surface in {"hermes", "both"} else "optional",
                "claim": "Hermes support is explicit and gated until runtime proof exists.",
            },
            "tracker": {
                "mode": args.tracker,
                "claim": "Tasks mirror to connected trackers, otherwise local tasks remain authoritative.",
            },
        },
        "active_app_id": app_id,
        "tasks": [
            {
                "task_id": task_id,
                "app_id": app_id,
                "stage": "Intent",
                "state": "NEW",
                "objective": "capture owner intent and acceptance checks",
                "next_action": "answer intent questions before creating worker packets",
                "source_of_truth": "local_weave",
                "mirror_state": "not_connected",
                "proof_path": f"tasks/{task_id}/proof.json",
                "review_path": f"tasks/{task_id}/review.md",
            }
        ],
        "apps": [
            {
                "app_id": app_id,
                "name": app_name,
                "state": "NEW",
                "current_stage": "intent",
                "next_action": "answer intent questions and define acceptance checks",
                "lifecycle": default_lifecycle(),
                "worker_lanes": default_worker_lanes(),
                "proof": [
                    {
                        "id": "state-home",
                        "state": "present",
                        "path": "state.json",
                        "claim": "local Chief of Staff state was generated",
                        "acceptance_check": "state file exists and declares no live effects",
                        "review": "not_required_for_init",
                    }
                ],
                "blockers": [
                    {
                        "id": "intent-not-complete",
                        "state": "owner_context_needed",
                        "detail": "intent, target user, constraints, acceptance checks, and deploy posture are not complete yet",
                    }
                ],
            }
        ],
        "updates": {
            "mode": args.update_mode,
            "inbox": [
                {
                    "state": "planned",
                    "summary": "daily public WEAVE update check writes here and surfaces on next Chief of Staff interaction",
                }
            ],
        },
        "source_of_truth_policy": "local WEAVE task/proof state is authoritative in v0.1; external trackers are mirrors unless explicitly selected otherwise",
        "hard_gates": DEFAULT_STOP_BOUNDARIES,
        "non_claims": [
            "does not prove live Hermes chat",
            "does not collect credentials",
            "does not deploy production",
            "does not send public messages",
            "does not spend money or run paid jobs",
        ],
    }


def active_app(state: dict[str, Any], app_id: str | None = None) -> dict[str, Any]:
    target = app_id or str(state.get("active_app_id") or "")
    for app in state.get("apps", []):
        if isinstance(app, dict) and app.get("app_id") == target:
            return app
    raise ChiefOfStaffError(f"app not found: {target}")


def compact_state_line(state: dict[str, Any], app_id: str | None = None) -> str:
    app = active_app(state, app_id)
    home = state.get("home", {})
    source = state.get("source", {})
    stage = str(app.get("current_stage") or "unknown").replace("_", " ")
    return (
        "WEAVE | "
        f"Home={home.get('label', 'Chief of Staff')} | "
        f"App={app.get('name', app.get('app_id', 'App'))} | "
        f"Stage={stage.title()} | "
        f"State={app.get('state', 'unknown')} | "
        f"Next={app.get('next_action', 'record next action')} | "
        f"Mode={source.get('update_mode', 'notify')}"
    )


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_home(home: Path, state: dict[str, Any]) -> None:
    app = active_app(state)
    task = state["tasks"][0]
    app_root = app_dir(home, str(app["app_id"]))
    write_json(state_path(home), state)
    write_text(
        home / "README.md",
        "# WEAVE Chief of Staff Home\n\n"
        + compact_state_line(state)
        + "\n\n"
        "This local home stores public-safe app state, lifecycle stage, worker lanes, blockers, proof, and update notices.\n"
        "It is not a credential store and it does not prove live runtime access by itself.\n",
    )
    write_json(
        home / "weave-version.json",
        {
            "current_version": state["source"]["current_version"],
            "source_url": state["source"]["url"],
            "mode": state["source"]["update_mode"],
            "last_checked_at": state["source"]["last_checked_at"],
        },
    )
    write_json(home / "preferences.json", {"owner": state["owner"], "hard_gates": state["hard_gates"]})
    write_json(home / "apps.json", {"active_app_id": state["active_app_id"], "apps": state["apps"]})
    write_json(home / "tasks.json", {"schema": "weave-chief-of-staff-tasks/v0.1", "tasks": state["tasks"]})
    write_text(home / "blockers.md", "# Blockers\n\n- intent-not-complete: owner context needed.\n")
    write_text(home / "proof-index.md", "# Proof Index\n\n- state-home: state.json exists; no live effects claimed.\n")
    write_text(home / "updates" / "inbox.md", "# WEAVE Update Inbox\n\n- Daily public update checks will write useful updates here.\n")
    task_root = home / "tasks" / str(task["task_id"])
    write_json(task_root / "task.json", task)
    write_text(
        task_root / "packet.md",
        "# Worker Packet\n\n"
        f"Task: {task['task_id']}\n"
        f"Stage: {task['stage']}\n"
        f"State: {task['state']}\n"
        f"Objective: {task['objective']}\n"
        "Allowed surfaces: local WEAVE files, public docs, local tests\n"
        "Forbidden actions: raw secrets, private topology, production deploy, public send, paid action\n"
        "Expected output: intent artifact and acceptance checks\n"
        f"Proof required: {task['proof_path']}\n"
        "Return states: READY_FOR_REVIEW, BLOCKED, NEEDS_PACKET_CHANGE\n"
        "Staleness rule: review if no update is recorded after the owner-visible work window\n",
    )
    write_json(
        task_root / "proof.json",
        {
            "schema": "weave-proof-envelope/v0.1",
            "task_id": task["task_id"],
            "claim": "local Chief of Staff state was generated",
            "artifact": "state.json",
            "acceptance_check": "state file exists and declares no live effects",
            "reviewed_by": "not_required_for_init",
            "state_effect": "does_not_mark_done",
            "non_claims": state["non_claims"],
            "sensitive_surfaces_avoided": True,
        },
    )
    write_text(
        task_root / "review.md",
        "# Review\n\nStatus: not reviewed.\n\n"
        "READY_FOR_REVIEW may become DONE only after a controller review records the proof envelope and acceptance check.\n",
    )
    write_json(app_root / "lifecycle.json", {"current_stage": app["current_stage"], "stages": app["lifecycle"]})
    write_text(
        app_root / "app.md",
        f"# {app['name']}\n\n"
        + compact_state_line(state)
        + "\n\n"
        "Intent is not complete until the owner provides target user, constraints, acceptance checks, and deploy posture.\n",
    )
    write_text(app_root / "intent.md", "# Intent\n\nStatus: needs owner context.\n")
    write_json(app_root / "workers.json", {"worker_lanes": app["worker_lanes"]})


def load_state(home: Path) -> dict[str, Any]:
    path = state_path(home)
    if not path.exists():
        raise ChiefOfStaffError(f"state file is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ChiefOfStaffError(f"state file is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ChiefOfStaffError("state file is not a WEAVE Chief of Staff v0.1 state")
    return payload


def render_snapshot_html(state: dict[str, Any]) -> str:
    app = active_app(state)
    line = compact_state_line(state)

    def esc(value: Any) -> str:
        return html.escape(str(value), quote=True)

    stage_items = "\n".join(
        f'<li class="stage stage-{esc(stage["state"])}"><span>{esc(stage["label"])}</span><b>{esc(stage["state"])}</b></li>'
        for stage in app["lifecycle"]
    )
    worker_items = "\n".join(
        "<li>"
        f"<strong>{esc(worker['label'])}</strong>"
        f"<span>{esc(worker['state'])}</span>"
        f"<em>{esc(worker['next'])}</em>"
        "</li>"
        for worker in app["worker_lanes"]
    )
    proof_items = "\n".join(
        f"<li><strong>{esc(item['id'])}</strong><span>{esc(item['state'])}</span><em>{esc(item['claim'])}; check: {esc(item.get('acceptance_check', 'missing'))}</em></li>"
        for item in app["proof"]
    )
    blocker_items = "\n".join(
        f"<li><strong>{esc(item['id'])}</strong><span>{esc(item['state'])}</span><em>{esc(item['detail'])}</em></li>"
        for item in app["blockers"]
    )
    gate_items = "\n".join(f"<li>{esc(gate.replace('_', ' '))}</li>" for gate in state["hard_gates"])
    non_claim_items = "\n".join(f"<li>{esc(item)}</li>" for item in state["non_claims"])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WEAVE Chief of Staff Snapshot</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172026;
      --muted: #59656f;
      --line: #c9d2dc;
      --panel: #f7f9fb;
      --paper: #ffffff;
      --blue: #245c8f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #edf1f5;
      color: var(--ink);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    header {{ display: grid; gap: 12px; margin-bottom: 18px; }}
    .state-line {{
      border: 1px solid var(--line);
      background: var(--paper);
      border-radius: 8px;
      padding: 12px 14px;
      font: 13px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      overflow-wrap: anywhere;
    }}
    h1 {{ margin: 0; font-size: 28px; line-height: 1.15; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 15px; letter-spacing: 0; }}
    .grid {{ display: grid; grid-template-columns: 1.1fr 1.4fr 1fr; gap: 14px; align-items: start; }}
    section {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
      padding: 16px;
      min-width: 0;
    }}
    .metric-row {{ display: grid; grid-template-columns: 110px 1fr; gap: 8px; font-size: 14px; margin: 8px 0; }}
    .metric-row span:first-child {{ color: var(--muted); }}
    ul {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }}
    li {{
      border: 1px solid #d9e1e8;
      border-radius: 8px;
      background: var(--panel);
      padding: 10px 12px;
      display: grid;
      gap: 4px;
      min-width: 0;
    }}
    li span, li em {{ color: var(--muted); font-style: normal; overflow-wrap: anywhere; }}
    .stage {{ grid-template-columns: 1fr auto; align-items: center; }}
    .stage b {{ font-size: 12px; font-weight: 700; text-transform: uppercase; color: var(--muted); }}
    .stage-active {{ border-color: var(--blue); background: #f0f6fb; }}
    .stage-active b {{ color: var(--blue); }}
    .blockers li {{ border-color: #ead0c8; background: #fff7f4; }}
    .gates {{ margin-top: 14px; }}
    .gates li {{ font-size: 13px; background: #fbfaf6; }}
    footer {{ margin-top: 16px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 880px) {{
      main {{ padding: 18px; }}
      .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 23px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>WEAVE Chief of Staff Snapshot</h1>
      <div class="state-line">{esc(line)}</div>
    </header>
    <div class="grid">
      <section>
        <h2>Active App</h2>
        <div class="metric-row"><span>App</span><strong>{esc(app['name'])}</strong></div>
        <div class="metric-row"><span>Stage</span><strong>{esc(app['current_stage'].replace('_', ' ').title())}</strong></div>
        <div class="metric-row"><span>State</span><strong>{esc(app['state'])}</strong></div>
        <div class="metric-row"><span>Next</span><strong>{esc(app['next_action'])}</strong></div>
        <div class="gates">
          <h2>Hard Gates</h2>
          <ul>{gate_items}</ul>
        </div>
      </section>
      <section>
        <h2>Lifecycle Rail</h2>
        <ul>{stage_items}</ul>
      </section>
      <section>
        <h2>Worker Lanes</h2>
        <ul>{worker_items}</ul>
      </section>
      <section>
        <h2>Proof</h2>
        <ul>{proof_items}</ul>
      </section>
      <section class="blockers">
        <h2>Blockers</h2>
        <ul>{blocker_items}</ul>
      </section>
      <section>
        <h2>Explicit Non-Claims</h2>
        <ul>{non_claim_items}</ul>
      </section>
    </div>
    <footer>Schema: {SNAPSHOT_SCHEMA}. Generated from local public-safe WEAVE state. No live effects.</footer>
  </main>
</body>
</html>
"""


def init_home(args: Any, output: TextIO) -> int:
    home = args.home.expanduser().resolve()
    if home.exists() and any(home.iterdir()) and not args.force:
        raise ChiefOfStaffError("chief-of-staff home is not empty; rerun with --force to overlay generated public-safe files")
    state = build_state(args)
    if args.write:
        write_home(home, state)
    if args.json:
        print(json.dumps(state, indent=2, sort_keys=True), file=output)
    else:
        print("WEAVE Chief of Staff", file=output)
        print(f"- mode: {'write' if args.write else 'preview'}", file=output)
        print(f"- home: {home}", file=output)
        print(f"- state_line: {compact_state_line(state)}", file=output)
        print("- live_effects: false", file=output)
        print("- secret_value_printed: false", file=output)
        print(f"- task: {state['tasks'][0]['task_id']} ({state['tasks'][0]['state']})", file=output)
        print("- next: answer intent questions and define acceptance checks", file=output)
    return 0


def state_line(args: Any, output: TextIO) -> int:
    state = load_state(args.home.expanduser().resolve())
    print(compact_state_line(state, args.app_id), file=output)
    return 0


def snapshot(args: Any, output: TextIO) -> int:
    home = args.home.expanduser().resolve()
    state = load_state(home)
    out = args.out.expanduser().resolve()
    rendered = render_snapshot_html(state)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    if args.json:
        print(
            json.dumps(
                {
                    "schema": SNAPSHOT_SCHEMA,
                    "home": str(home),
                    "out": str(out),
                    "state_line": compact_state_line(state),
                    "live_effects": False,
                    "secret_value_printed": False,
                },
                indent=2,
                sort_keys=True,
            ),
            file=output,
        )
    else:
        print("WEAVE Chief of Staff Snapshot", file=output)
        print(f"- out: {out}", file=output)
        print(f"- state_line: {compact_state_line(state)}", file=output)
        print("- live_effects: false", file=output)
        print("- secret_value_printed: false", file=output)
    return 0
