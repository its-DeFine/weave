#!/usr/bin/env python3
"""Read-only WEAVE runtime dashboard.

The dashboard is a local inspection surface. It reads runtime-home files and
existing WEAVE ledgers, but it does not create missing state, start services,
send Telegram messages, invoke Hermes, or print secrets.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import weave_hermes_setup
import weave_runtime_slice


DASHBOARD_SCHEMA = "weave-dashboard/v0.1"
REPO_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def path_state(path: Path) -> str:
    if path.exists() and path.is_dir():
        return "directory"
    if path.exists() and path.is_file():
        return "file"
    return "missing"


def load_json_if_present(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"error": str(exc)}, "invalid_json"
    if not isinstance(parsed, dict):
        return {"error": "json root is not an object"}, "invalid_json"
    return parsed, "loaded"


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def count_eval_contracts() -> int:
    eval_root = REPO_ROOT / "packages" / "weave-tool" / "evals"
    if not eval_root.exists():
        return 0
    return sum(1 for path in eval_root.rglob("*.yaml") if path.is_file())


def short_list(values: list[Any], limit: int = 3) -> list[str]:
    items = [str(value) for value in values if str(value).strip()]
    if len(items) <= limit:
        return items
    return items[:limit] + [f"... {len(items) - limit} more"]


def adapter_summary(profile: dict[str, Any]) -> dict[str, Any]:
    adapter = {}
    runtime = profile.get("runtime")
    if isinstance(runtime, dict):
        raw_adapter = runtime.get("adapter_contract")
        if isinstance(raw_adapter, dict):
            adapter = raw_adapter
    methods = adapter.get("methods") if isinstance(adapter.get("methods"), dict) else {}
    invoke = methods.get("invoke") if isinstance(methods.get("invoke"), dict) else {}
    probe = adapter.get("current_probe") if isinstance(adapter.get("current_probe"), dict) else {}
    return {
        "present": bool(adapter),
        "schema": adapter.get("schema", ""),
        "runtime_id": adapter.get("runtime_id", "missing"),
        "support_state": adapter.get("support_state", "missing"),
        "invoke_state": invoke.get("current_state", "missing"),
        "invoke_requires_owner_approval": bool(invoke.get("requires_owner_approval")),
        "live_qa_completed": probe.get("live_qa_completed") is True,
    }


def gateway_summary(
    profile: dict[str, Any],
    *,
    hermes_home: Path,
    weave_root: Path,
    container_name: str,
    check_container: bool,
) -> dict[str, Any]:
    gateway = profile.get("gateway") if isinstance(profile.get("gateway"), dict) else {}
    env_path = hermes_home / ".env"
    workdir = weave_root / "runtime" / "hermes-gateway"
    container = {
        "checked": check_container,
        "state": "not_checked",
        "detail": "",
    }
    if check_container:
        docker = shutil.which("docker")
        if not docker:
            container["state"] = "unknown"
            container["detail"] = "container engine unavailable"
        else:
            result = subprocess.run(
                [
                    docker,
                    "ps",
                    "-a",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.Names}}\t{{.Status}}\t{{.Image}}",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                container["state"] = "unknown"
                container["detail"] = (result.stderr or result.stdout or "").strip()
            else:
                detail = result.stdout.strip()
                container["state"] = "not_found" if not detail else "found"
                container["detail"] = detail
    return {
        "env_state": path_state(env_path),
        "env_secret_value_printed": False,
        "workdir_state": path_state(workdir),
        "configured": bool(gateway.get("runtime_config_written")),
        "token_loaded": bool(gateway.get("token_loaded")),
        "allowlist_mode": gateway.get("allowlist_mode", "unknown"),
        "gateway_started_claim": bool(gateway.get("gateway_started")),
        "plugin_installed": bool(gateway.get("weave_plugin_installed")),
        "plugin_enabled": bool(gateway.get("weave_plugin_enabled")),
        "container": container,
    }


def app_next_action(*, foundation_passed: bool, blockers: list[str], stage_gate_missing: list[str]) -> str:
    if not foundation_passed:
        return "Hermes should collect foundation answers and update required context."
    if blockers:
        return f"Resolve blocker: {blockers[0]}"
    if stage_gate_missing:
        return f"Complete current-stage gate: {stage_gate_missing[0]}"
    return "No deterministic blocker is recorded for this app."


def flow_step(
    step_id: str,
    label: str,
    state: str,
    detail: str,
    next_action: str,
    *,
    command: str = "",
) -> dict[str, str]:
    return {
        "id": step_id,
        "label": label,
        "state": state,
        "detail": detail,
        "next_action": next_action,
        "command": command,
    }


def inconsistency(
    item_id: str,
    severity: str,
    state: str,
    detail: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "id": item_id,
        "severity": severity,
        "state": state,
        "detail": detail,
        "next_action": next_action,
    }


def collect_app_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    if not weave_runtime_slice.root_ready(root):
        return [], errors
    try:
        registry = weave_runtime_slice.load_registry(root)
    except weave_runtime_slice.RuntimeSliceError as exc:
        return [], [str(exc)]
    rows: list[dict[str, Any]] = []
    for entry in registry.get("apps", []):
        app_id = str(entry.get("app_id") or "").strip()
        if not app_id:
            continue
        try:
            app = weave_runtime_slice.load_app(root, app_id)
            stage = weave_runtime_slice.normalize_stage_id(
                str(app.get("current_stage") or entry.get("stage") or "intent"),
                default="intent",
            )
            foundation = weave_runtime_slice.foundation_gate(root, app_id)
            stage_gate = weave_runtime_slice.stage_gate_status(root, app_id, stage)
            blockers = short_list(app.get("blockers", []), 5)
            stage_gate_missing = short_list(stage_gate.get("missing", []), 5)
            foundation_passed = foundation.get("passed") is True
            app_type = "system" if weave_runtime_slice.is_system_app(app) else str(app.get("app_type") or "product")
            rows.append(
                {
                    "app_id": app["app_id"],
                    "name": app["name"],
                    "app_type": app_type,
                    "stage": stage,
                    "stage_state": app.get("stage_state", "collecting"),
                    "foundation": "passed" if foundation_passed else "blocking",
                    "foundation_missing": short_list(foundation.get("missing", []) + foundation.get("incomplete", []), 5),
                    "stage_gate_passed": stage_gate.get("passed") is True,
                    "stage_gate_missing": stage_gate_missing,
                    "blockers": blockers,
                    "conversation_turn_count": count_jsonl(weave_runtime_slice.conversation_turn_path(root, app_id)),
                    "conversation_event_count": count_jsonl(weave_runtime_slice.conversation_event_path(root, app_id)),
                    "event_count": count_jsonl(weave_runtime_slice.event_path(root, app_id)),
                    "artifact_count": len(weave_runtime_slice.list_artifacts(root, app_id)),
                    "blocked": (not foundation_passed) or bool(blockers) or bool(stage_gate_missing),
                    "next_action": app_next_action(
                        foundation_passed=foundation_passed,
                        blockers=blockers,
                        stage_gate_missing=stage_gate_missing,
                    ),
                    "last_changed_at": entry.get("last_changed_at", app.get("created_at", "")),
                }
            )
        except weave_runtime_slice.RuntimeSliceError as exc:
            errors.append(f"{app_id}: {exc}")
    return rows, errors


def build_operator_flow(
    *,
    profile_state: str,
    root_ready: bool,
    hermes_setup: dict[str, Any],
    gateway: dict[str, Any],
    adapter: dict[str, Any],
    product_apps: list[dict[str, Any]],
    blocked_apps: list[dict[str, Any]],
    active_app_id: str,
    total_turns: int,
    eval_contract_count: int,
    next_action: str,
) -> list[dict[str, str]]:
    selected_app = next((row for row in product_apps if row["app_id"] == active_app_id), None)
    if selected_app is None and product_apps:
        selected_app = product_apps[0]
    onboarding_ready = root_ready and profile_state == "loaded"
    gateway_state = "running" if gateway["container"]["state"] == "found" else "configured" if gateway["configured"] else "missing"
    if gateway_state == "configured" and not gateway["token_loaded"]:
        gateway_state = "blocked"
    lifecycle_state = "missing"
    lifecycle_detail = "no product app workspace"
    lifecycle_next = "create a product app workspace"
    if selected_app:
        lifecycle_state = "blocked" if selected_app["blocked"] else "ready"
        lifecycle_detail = (
            f"{selected_app['app_id']} stage={selected_app['stage']} "
            f"state={selected_app['stage_state']} foundation={selected_app['foundation']} "
            f"gate_passed={selected_app['stage_gate_passed']}"
        )
        lifecycle_next = selected_app["next_action"]
    return [
        flow_step(
            "onboarding",
            "Onboarding",
            "ready" if onboarding_ready else "missing",
            f"profile={profile_state}; root_ready={str(root_ready).lower()}",
            "continue" if onboarding_ready else "run bin/weave onboard",
            command="bin/weave onboard",
        ),
        flow_step(
            "hermes_setup",
            "Hermes Setup",
            "ready" if hermes_setup.get("normal_chat_assumed_ready") else "blocked",
            f"state={hermes_setup.get('state', 'unknown')}; route_owner={hermes_setup.get('route_verification_owner', 'hermes')}",
            "continue" if hermes_setup.get("normal_chat_assumed_ready") else "confirm Hermes chat or use slash-only mode",
            command="bin/weave hermes status",
        ),
        flow_step(
            "gateway",
            "Gateway Attachment",
            gateway_state,
            (
                f"configured={str(gateway['configured']).lower()}; token_loaded={str(gateway['token_loaded']).lower()}; "
                f"container={gateway['container']['state']}"
            ),
            "continue" if gateway_state == "running" else "pair/start gateway when live Telegram is intentionally needed",
            command="bin/weave status",
        ),
        flow_step(
            "app_portfolio",
            "App Portfolio",
            "ready" if product_apps else "missing",
            f"product_apps={len(product_apps)}; active_app={active_app_id or 'none'}; blocked={len(blocked_apps)}",
            "continue" if product_apps else "create a product app workspace",
            command="bin/weave command /apps",
        ),
        flow_step(
            "lifecycle",
            "Current App Lifecycle",
            lifecycle_state,
            lifecycle_detail,
            lifecycle_next,
            command="bin/weave command /app",
        ),
        flow_step(
            "transcript",
            "Transcript Capture",
            "ready" if total_turns else "missing",
            f"conversation_turns={total_turns}",
            "continue" if total_turns else "capture a current-stage owner/Hermes turn before approval",
            command="bin/weave command /transcript",
        ),
        flow_step(
            "proof_evals",
            "Proof And Evals",
            "not_proven" if adapter["present"] and not adapter["live_qa_completed"] else "ready" if adapter["live_qa_completed"] else "missing",
            (
                f"eval_contracts={eval_contract_count}; adapter={adapter['support_state']}; "
                f"live_qa_completed={adapter['live_qa_completed']}"
            ),
            "run owner-gated adapter proof later" if not adapter["live_qa_completed"] else "continue",
            command="bin/weave eval --list",
        ),
        flow_step(
            "next_action",
            "Next Action",
            "attention" if next_action else "ready",
            next_action or "none",
            next_action or "none",
        ),
    ]


def build_inconsistencies(
    *,
    profile_state: str,
    root_ready: bool,
    hermes_setup: dict[str, Any],
    gateway: dict[str, Any],
    adapter: dict[str, Any],
    product_apps: list[dict[str, Any]],
    active_app_id: str,
    total_turns: int,
    app_errors: list[str],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if profile_state != "loaded":
        items.append(
            inconsistency(
                "runtime_profile_missing",
                "high",
                "missing",
                "runtime-profile.json is missing or unreadable",
                "run bin/weave onboard",
            )
        )
    if not root_ready:
        items.append(
            inconsistency(
                "weave_root_not_initialized",
                "high",
                "missing",
                "WEAVE state root has no app registry",
                "run bin/weave onboard",
            )
        )
    if not hermes_setup.get("normal_chat_assumed_ready"):
        items.append(
            inconsistency(
                "hermes_chat_not_confirmed",
                "medium",
                "blocked",
                f"Hermes setup state is {hermes_setup.get('state', 'unknown')}",
                "confirm normal Hermes chat or mark slash-only intentionally",
            )
        )
    if gateway["configured"] and not gateway["token_loaded"]:
        items.append(
            inconsistency(
                "gateway_configured_without_token",
                "medium",
                "blocked",
                "gateway runtime config exists but Telegram token is not loaded",
                "pair a dedicated bot only when Telegram operation is intended",
            )
        )
    if adapter["present"] and not adapter["live_qa_completed"]:
        items.append(
            inconsistency(
                "live_hermes_adapter_proof_missing",
                "high",
                "not_proven",
                "adapter contract is present but no live Hermes adapter proof is recorded",
                "run owner-gated live adapter QA later",
            )
        )
    if adapter["present"]:
        items.append(
            inconsistency(
                "full_adapter_bridge_not_proven",
                "high",
                "not_proven",
                "invoke/capture/post-event bridge is not proven end to end",
                "build Hermes adapter bridge after console truth surface",
            )
        )
    if not product_apps:
        items.append(
            inconsistency(
                "no_product_app",
                "medium",
                "missing",
                "no product app workspace is registered",
                "create or import a product app workspace",
            )
        )
    if product_apps and active_app_id == "none":
        items.append(
            inconsistency(
                "active_app_not_selected",
                "low",
                "missing",
                "product apps exist but no active app is selected",
                "select an active app before guided app work",
            )
        )
    if product_apps and total_turns == 0:
        items.append(
            inconsistency(
                "transcript_capture_missing",
                "high",
                "missing",
                "no app conversation turns are captured",
                "capture the owner/Hermes turn before lifecycle approval",
            )
        )
    for error in app_errors:
        items.append(inconsistency("app_state_error", "high", "invalid", error, "repair app state"))
    return items


def dashboard_snapshot(
    *,
    runtime_home: Path,
    weave_root: Path,
    hermes_home: Path,
    profile_path: Path,
    container_name: str,
    check_container: bool = True,
) -> dict[str, Any]:
    profile, profile_state = load_json_if_present(profile_path)
    root_ready = weave_runtime_slice.root_ready(weave_root)
    app_rows, app_errors = collect_app_rows(weave_root)
    product_apps = [row for row in app_rows if row["app_type"] != "system"]
    system_apps = [row for row in app_rows if row["app_type"] == "system"]
    blocked_apps = [row for row in product_apps if row["blocked"]]
    active_app = {}
    if root_ready:
        try:
            active_app = weave_runtime_slice.load_active_app(weave_root)
        except weave_runtime_slice.RuntimeSliceError as exc:
            active_app = {"schema": weave_runtime_slice.ACTIVE_APP_SCHEMA, "app_id": "", "source": "error", "error": str(exc)}
    hermes_setup = weave_hermes_setup.hermes_setup_status(hermes_home)
    adapter = adapter_summary(profile)
    gateway = gateway_summary(
        profile,
        hermes_home=hermes_home,
        weave_root=weave_root,
        container_name=container_name,
        check_container=check_container,
    )
    total_turns = sum(row["conversation_turn_count"] for row in app_rows)
    total_conversation_events = sum(row["conversation_event_count"] for row in app_rows)
    eval_contract_count = count_eval_contracts()
    gaps: list[str] = []
    if profile_state != "loaded":
        gaps.append("runtime profile missing or unreadable")
    if not root_ready:
        gaps.append("WEAVE state root is not initialized")
    if not hermes_setup.get("normal_chat_assumed_ready"):
        gaps.append("normal Hermes chat is not confirmed")
    if not adapter["present"]:
        gaps.append("agent runtime adapter contract is missing")
    elif not adapter["live_qa_completed"]:
        gaps.append("live Hermes adapter proof is missing")
    if adapter["present"]:
        gaps.append("full invoke/capture adapter bridge is not proven")
    if not product_apps:
        gaps.append("no product app workspace is registered")
    gaps.extend(app_errors)
    next_action = "run weave onboard" if not root_ready else "review gaps and complete the first blocking item"
    if product_apps and not blocked_apps and adapter["live_qa_completed"]:
        next_action = "no dashboard blocker is visible"
    active_app_id = active_app.get("app_id") or "none"
    operator_flow = build_operator_flow(
        profile_state=profile_state,
        root_ready=root_ready,
        hermes_setup=hermes_setup,
        gateway=gateway,
        adapter=adapter,
        product_apps=product_apps,
        blocked_apps=blocked_apps,
        active_app_id=active_app_id,
        total_turns=total_turns,
        eval_contract_count=eval_contract_count,
        next_action=next_action,
    )
    inconsistencies = build_inconsistencies(
        profile_state=profile_state,
        root_ready=root_ready,
        hermes_setup=hermes_setup,
        gateway=gateway,
        adapter=adapter,
        product_apps=product_apps,
        active_app_id=active_app_id,
        total_turns=total_turns,
        app_errors=app_errors,
    )
    return {
        "schema": DASHBOARD_SCHEMA,
        "generated_at": utc_now(),
        "read_only": True,
        "live_effects": False,
        "operator_flow": operator_flow,
        "inconsistencies": inconsistencies,
        "runtime": {
            "runtime_home": str(runtime_home),
            "runtime_home_state": path_state(runtime_home),
            "weave_root": str(weave_root),
            "weave_root_state": path_state(weave_root),
            "root_ready": root_ready,
            "hermes_home": str(hermes_home),
            "hermes_home_state": path_state(hermes_home),
            "profile_path": str(profile_path),
            "profile_state": profile_state,
            "hermes_setup": hermes_setup,
            "adapter": adapter,
            "gateway": gateway,
        },
        "apps": {
            "active_app": active_app.get("app_id") or "none",
            "product_count": len(product_apps),
            "system_count": len(system_apps),
            "blocked_count": len(blocked_apps),
            "rows": app_rows,
        },
        "proof": {
            "runtime_event_count": count_jsonl(weave_root / "ledger" / "events.jsonl"),
            "conversation_turn_count": total_turns,
            "conversation_event_count": total_conversation_events,
            "live_hermes_adapter_proof": "present" if adapter["live_qa_completed"] else "missing",
            "full_adapter_bridge": "not_proven",
        },
        "evals": {
            "contract_count": eval_contract_count,
            "state": "available" if eval_contract_count else "missing",
            "command": "bin/weave eval --list",
        },
        "gaps": gaps,
        "next_action": next_action,
    }


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def render_dashboard(snapshot: dict[str, Any]) -> str:
    runtime = snapshot["runtime"]
    apps = snapshot["apps"]
    proof = snapshot["proof"]
    hermes_setup = runtime["hermes_setup"]
    adapter = runtime["adapter"]
    gateway = runtime["gateway"]
    container = gateway["container"]
    lines = [
        "WEAVE TUI Operator Console (read-only)",
        "surface: WEAVE Dashboard (read-only)",
        f"schema: {snapshot['schema']}",
        f"generated_at: {snapshot['generated_at']}",
        f"live_effects: {bool_text(snapshot['live_effects'])}",
        "",
        "[Operator Flow]",
    ]
    for step in snapshot.get("operator_flow", []):
        command = f"; command={step['command']}" if step.get("command") else ""
        lines.append(f"- {step['label']}: {step['state']}; {step['detail']}{command}")
        lines.append(f"  next: {step['next_action']}")
    lines.extend(
        [
            "",
            "[Inconsistency Radar]",
        ]
    )
    inconsistencies = snapshot.get("inconsistencies", [])
    if inconsistencies:
        for item in inconsistencies:
            lines.append(f"- {item['severity']} {item['id']}: {item['state']}; {item['detail']}")
            lines.append(f"  next: {item['next_action']}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "[Runtime]",
            f"runtime_home: {runtime['runtime_home']} ({runtime['runtime_home_state']})",
            f"weave_state: {runtime['weave_root']} ({runtime['weave_root_state']}; root_ready={bool_text(runtime['root_ready'])})",
            f"hermes_home: {runtime['hermes_home']} ({runtime['hermes_home_state']})",
            f"profile: {runtime['profile_path']} ({runtime['profile_state']})",
            "",
            "[Hermes]",
            f"setup_state: {hermes_setup.get('state', 'unknown')}",
            f"normal_chat_assumed_ready: {bool_text(hermes_setup.get('normal_chat_assumed_ready'))}",
            f"route_verification_owner: {hermes_setup.get('route_verification_owner', 'hermes')}",
            f"secret_value_printed: {bool_text(hermes_setup.get('secret_value_printed'))}",
            "",
            "[Gateway]",
            f"configured: {bool_text(gateway['configured'])}",
            f"token_loaded: {bool_text(gateway['token_loaded'])}",
            f"allowlist_mode: {gateway['allowlist_mode']}",
            f"env_state: {gateway['env_state']}; secret_value_printed={bool_text(gateway['env_secret_value_printed'])}",
            f"workdir_state: {gateway['workdir_state']}",
            f"plugin: installed={bool_text(gateway['plugin_installed'])}; enabled={bool_text(gateway['plugin_enabled'])}",
            f"container: {container['state']}; checked={bool_text(container['checked'])}; detail={container['detail'] or 'none'}",
            "",
            "[Adapter]",
            f"present: {bool_text(adapter['present'])}",
            f"runtime_id: {adapter['runtime_id']}",
            f"support_state: {adapter['support_state']}",
            f"invoke_state: {adapter['invoke_state']}",
            f"live_qa_completed: {bool_text(adapter['live_qa_completed'])}",
            "",
            "[Apps]",
            f"active_app: {apps['active_app']}",
            f"product_apps: {apps['product_count']}",
            f"system_apps_hidden: {apps['system_count']}",
            f"blocked_product_apps: {apps['blocked_count']}",
        ]
    )
    product_rows = [row for row in apps["rows"] if row["app_type"] != "system"]
    if product_rows:
        for row in product_rows[:10]:
            missing = row["foundation_missing"] or row["stage_gate_missing"] or row["blockers"]
            missing_text = "; missing=" + ", ".join(missing) if missing else ""
            lines.append(
                f"- {row['name']} ({row['app_id']}): stage={row['stage']}; "
                f"state={row['stage_state']}; foundation={row['foundation']}; "
                f"gate_passed={bool_text(row['stage_gate_passed'])}; turns={row['conversation_turn_count']}; "
                f"events={row['event_count']}; artifacts={row['artifact_count']}{missing_text}"
            )
            lines.append(f"  next: {row['next_action']}")
        if len(product_rows) > 10:
            lines.append(f"- ... {len(product_rows) - 10} more product apps")
    else:
        lines.append("- none registered")
    lines.extend(
        [
            "",
            "[Proof]",
            f"runtime_events: {proof['runtime_event_count']}",
            f"conversation_turns: {proof['conversation_turn_count']}",
            f"conversation_events: {proof['conversation_event_count']}",
            f"live_hermes_adapter_proof: {proof['live_hermes_adapter_proof']}",
            f"full_adapter_bridge: {proof['full_adapter_bridge']}",
            f"eval_contracts: {snapshot['evals']['contract_count']}",
            "",
            "[Gaps]",
        ]
    )
    if snapshot["gaps"]:
        lines.extend(f"- {gap}" for gap in snapshot["gaps"])
    else:
        lines.append("- none")
    lines.extend(["", "[Next]", f"- {snapshot['next_action']}"])
    return "\n".join(lines) + "\n"


def print_dashboard(snapshot: dict[str, Any], *, output: TextIO, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(snapshot, indent=2, sort_keys=True), file=output)
        return
    print(render_dashboard(snapshot), end="", file=output)
