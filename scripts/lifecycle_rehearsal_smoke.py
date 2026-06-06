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
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import weave_runtime_slice as runtime


DEFAULT_REPORT_DIR = Path.home() / "Documents" / "Codex" / "artifacts" / "weave-lifecycle-rehearsals"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fill(path: Path, title: str, body: str = "Rehearsal evidence is complete.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\nStatus: complete\n\n{body}\n", encoding="utf-8")


def complete_foundation(root: Path, app_id: str) -> None:
    fill(root / "artifacts" / "general" / "soul.md", "Hermes Soul")
    fill(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile")
    fill(root / "apps" / app_id / "context" / "app-context.md", "App Context")
    fill(root / "apps" / app_id / "inventory" / "app-inventory.md", "App Inventory")
    fill(root / "apps" / app_id / "contract" / "gestaltian-contract.md", "Gestaltian Contract")


def write_stage_artifact(root: Path, app_id: str, stage_id: str) -> Path:
    stage = runtime.stage_by_id(stage_id)
    path = root / "apps" / app_id / "lifecycle" / stage.directory / "artifacts" / f"{stage_id}-proof.md"
    fill(
        path,
        f"{stage_id.title()} Proof",
        f"Proof for the {stage_id} lifecycle stage. This is deterministic rehearsal evidence.",
    )
    return path


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


def run_rehearsal() -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    app_id = "visual-novel"
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

        command("create app", "/create_app Visual Novel")
        blocked = command("approval blocks before foundation", f"/approve_stage {app_id}")
        assert_condition(blocked["handled"] is False and "foundation context" in blocked["text"], "approval did not block before foundation")

        missing_app = command("invalid app is rejected", "/status does-not-exist")
        assert_condition(missing_app["handled"] is False, "invalid app lookup should be rejected")

        complete_foundation(root, app_id)
        blocked = command("approval blocks before intent proof", f"/approve_stage {app_id}")
        assert_condition(blocked["handled"] is False and "intent artifact" in blocked["text"], "approval did not require intent artifact")

        status = command("status exposes stage gate attention", "/status")
        assert_condition(status["payload"].get("stage_gate_blocked_apps") == [app_id], "status did not expose stage gate attention")

        write_stage_artifact(root, app_id, "intent")
        advanced = command("advance blocks before owner approval", f"/advance {app_id}")
        assert_condition(advanced["handled"] is False and advanced["error"] == "current_stage_not_approved", "advance did not block before approval")

        for index, stage_id in enumerate(stage_ids):
            current = runtime.app_state(root, app_id)["stage_status"]["stage"]
            assert_condition(current == stage_id, f"expected current stage {stage_id}, got {current}")
            if stage_id != "intent":
                missing = command(f"{stage_id} approval blocks before proof", f"/approve_stage {app_id}")
                assert_condition(missing["handled"] is False, f"{stage_id} should block before proof")
                write_stage_artifact(root, app_id, stage_id)

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

        return {
            "schema": "weave-lifecycle-rehearsal/v0.1",
            "created_at": utc_now(),
            "environment": "isolated-temp-runtime",
            "runtime_root": "<isolated-temp-root>/weave-root",
            "app_id": app_id,
            "passed": True,
            "stages_rehearsed": stage_ids,
            "final_stage": final_state["stage_status"]["stage"],
            "final_stage_state": final_state["stage_status"]["stage_state"],
            "approved_stages": approved,
            "artifact_count": len(final_state["artifacts"]),
            "edge_cases": [
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
    try:
        report = run_rehearsal()
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
