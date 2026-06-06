#!/usr/bin/env python3
"""Operational HTTP service for the WEAVE runtime.

This file is the deployable VM/remote-runtime wrapper around
``weave_runtime_slice``. It intentionally keeps the older command-bus endpoints
alive while routing product-app lifecycle, slash-command, source-map, and
conversation transcript requests to the current runtime slice.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

SCRIPT_ROOT = Path(__file__).resolve().parent
RUNTIME_REPO = os.environ.get("WEAVE_RUNTIME_REPO")
IMPORT_ROOTS = [SCRIPT_ROOT]
if RUNTIME_REPO:
    IMPORT_ROOTS.insert(0, Path(RUNTIME_REPO).expanduser().resolve() / "scripts")
for import_root in IMPORT_ROOTS:
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import weave_runtime_slice


SERVICE_SCHEMA = "weave-runtime-http/v0.2"
COMMAND_SCHEMA = "weave-agent-command/v0.1"
CONVERSATION_SCHEMA = "weave-runtime-conversation/v0.1"
COMMAND_STATE_SCHEMA = "weave-runtime-v1-command-state/v0.1"
OPS_EVENT_SCHEMA = "weave-runtime-v1-ops-event/v0.1"
EXECUTOR_RESULT_SCHEMA = "weave-openclaw-command-result/v0.1"
LANE_CLAIMS_SCHEMA = "weave-project-lane-claims/v0.1"
LANE_COORDINATION_SCHEMA = "weave-project-lane-coordination/v0.1"

DEFAULT_STATE_DIR = Path(os.environ.get("WEAVE_RUNTIME_STATE_DIR", str(Path.home() / ".weave" / "runtime")))
DEFAULT_COMMAND_LEDGER = DEFAULT_STATE_DIR / "command-bus.jsonl"
DEFAULT_CONVERSATION_LEDGER = DEFAULT_STATE_DIR / "conversation.jsonl"
DEFAULT_EVENTS_LEDGER = DEFAULT_STATE_DIR / "events.jsonl"
DEFAULT_LANE_CLAIMS_LEDGER = DEFAULT_STATE_DIR / "project-lane-claims.json"

ALLOWED_COMMAND_TYPES = {
    "brief_stage_context",
    "request_research",
    "request_engineering",
    "request_qa",
    "request_devops_prepare",
    "report_blocker",
    "request_owner_approval",
    "record_decision",
    "record_evidence",
    "mission_register",
    "mission_advance",
    "mission_verify_request",
    "mission_grant_credits",
    "ads_plan_create",
    "ads_request_owner_approval",
    "ads_google_create_paused_draft",
    "ads_report",
    "record_lane_claim",
}
AUTO_DONE_COMMAND_TYPES = {
    "brief_stage_context",
    "record_decision",
    "record_evidence",
    "ads_plan_create",
    "ads_report",
    "record_lane_claim",
}
EXECUTOR_COMMAND_TYPES = {
    "request_research",
    "request_engineering",
    "request_qa",
    "request_devops_prepare",
}
OWNER_APPROVAL_COMMAND_TYPES = {
    "ads_request_owner_approval",
    "ads_google_create_paused_draft",
    "request_owner_approval",
}
SENSITIVE_NAME_PATTERN = re.compile(
    r"(api[_-]?key|secret|token|password|passcode|credential|private[_-]?key|seed|2fa|otp)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-or-v1-[A-Za-z0-9_-]{16,}|sk_live_[A-Za-z0-9]{16,}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{20,}|"
    r"\b[0-9]{8,12}:[A-Za-z0-9_-]{24,}\b)",
    re.IGNORECASE,
)
SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"\b([A-Z0-9_]*(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSCODE|CREDENTIAL|PRIVATE[_-]?KEY|SEED|2FA|OTP)"
    r"[A-Z0-9_]*)\s*=\s*([^\s\"']{4,})",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    try:
        path.chmod(0o600)
    except PermissionError:
        pass


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                records.append(value)
    return records


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def write_private_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except PermissionError:
        pass


def contains_secret_payload(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if SENSITIVE_NAME_PATTERN.search(str(key)) and item not in (None, "", False):
                return True
            if contains_secret_payload(item):
                return True
        return False
    if isinstance(value, list):
        return any(contains_secret_payload(item) for item in value)
    if isinstance(value, str):
        return bool(SENSITIVE_VALUE_PATTERN.search(value) or SENSITIVE_ASSIGNMENT_PATTERN.search(value))
    return False


def parse_limit(params: dict[str, list[str]], *, default: int = 100, maximum: int = 500) -> int:
    raw = params.get("limit", [str(default)])[0]
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(value, maximum))


def filtered_records(records: list[dict[str, Any]], params: dict[str, list[str]]) -> list[dict[str, Any]]:
    app_id = params.get("app_id", params.get("target_app_id", [None]))[0]
    command_id = params.get("command_id", [None])[0]
    result_status = params.get("result_status", [None])[0]
    output = records
    if app_id:
        output = [record for record in output if record.get("target_app_id") == app_id or record.get("app_id") == app_id]
    if command_id:
        output = [
            record
            for record in output
            if record.get("command_id") == command_id or record.get("source_command_id") == command_id
        ]
    if result_status:
        output = [record for record in output if record.get("result_status") == result_status]
    return output[-parse_limit(params) :]


def command_result(command: dict[str, Any]) -> tuple[str, str | None]:
    if command.get("requires_owner_approval") is True:
        return "blocked", "owner_approval_required"
    command_type = str(command.get("command_type") or "")
    if command_type in EXECUTOR_COMMAND_TYPES:
        return "pending", "external_executor_required"
    if command_type in AUTO_DONE_COMMAND_TYPES:
        return "done", None
    if command_type in OWNER_APPROVAL_COMMAND_TYPES:
        return "blocked", "owner_attention_required"
    if command_type in {"report_blocker"}:
        return "blocked", "reported_blocker"
    return "blocked", "unsupported_runtime_command"


def legacy_message(
    *,
    app_id: str,
    app_name: str,
    lifecycle_stage: str,
    sender_id: str,
    sender_kind: str,
    receiver_id: str,
    channel: str,
    message_type: str,
    text: str,
    command_id: str | None = None,
    evidence_refs: list[str] | None = None,
    requires_owner_approval: bool = False,
) -> dict[str, Any]:
    created = utc_now()
    return {
        "schema": CONVERSATION_SCHEMA,
        "message_id": f"msg-{created.lower().replace(':', '').replace('-', '').replace('z', 'z')}-{uuid.uuid4().hex[:8]}",
        "created_at": created,
        "app_id": app_id,
        "app_name": app_name,
        "lifecycle_stage": lifecycle_stage,
        "sender_id": sender_id,
        "sender_kind": sender_kind,
        "receiver_id": receiver_id,
        "channel": channel,
        "message_type": message_type,
        "text": text,
        "command_id": command_id,
        "evidence_refs": evidence_refs or [],
        "requires_owner_approval": bool(requires_owner_approval),
        "secret_payload_allowed": False,
    }


def command_state_event(
    command: dict[str, Any],
    *,
    transition: str,
    ack_status: str,
    result_status: str,
    stop_reason: str | None,
    evidence_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": COMMAND_STATE_SCHEMA,
        "generated_at": utc_now(),
        "runtime_id": "weave-runtime-http",
        "transition": transition,
        "command_id": command.get("command_id"),
        "command_type": command.get("command_type"),
        "target_app_id": command.get("target_app_id"),
        "ack_status": ack_status,
        "result_status": result_status,
        "stop_reason": stop_reason,
        "evidence_ref": evidence_ref,
        "requires_owner_approval": bool(command.get("requires_owner_approval")),
    }


def ops_event(command: dict[str, Any], *, result_status: str, stop_reason: str | None) -> dict[str, Any]:
    return {
        "schema": OPS_EVENT_SCHEMA,
        "event_type": "weave_runtime_progress",
        "generated_at": utc_now(),
        "lane": "weave-runtime",
        "state": result_status,
        "managed_app_ref": str(command.get("target_app_id") or "managed-app"),
        "command_type": command.get("command_type"),
        "stop_reason": stop_reason,
        "artifact_ref": str(command.get("evidence_ref") or command.get("payload_ref")),
        "private_artifact_ref_present": bool(command.get("evidence_ref") or command.get("payload_ref")),
        "public_safe": True,
    }


def process_running(pattern: str) -> bool:
    try:
        result = subprocess.run(["pgrep", "-f", pattern], text=True, capture_output=True, check=False)
    except OSError:
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


class RuntimeState:
    def __init__(
        self,
        root: Path,
        command_ledger: Path,
        conversation_ledger: Path,
        events_ledger: Path,
        lane_claims_ledger: Path,
    ) -> None:
        self.root = root
        self.command_ledger = command_ledger
        self.conversation_ledger = conversation_ledger
        self.events_ledger = events_ledger
        self.lane_claims_ledger = lane_claims_ledger

    def setup(self) -> None:
        weave_runtime_slice.setup_weave_root(self.root)

    def health(self) -> dict[str, Any]:
        self.setup()
        status_code, slice_status = weave_runtime_slice.dispatch_rest(self.root, "GET", "/runtime/status")
        source_code, source_payload = weave_runtime_slice.dispatch_rest(self.root, "GET", "/runtime/sources")
        source_ids: list[str] = []
        if source_code == 200:
            sources = source_payload.get("source_map", {}).get("sources", [])
            source_ids = sorted(str(source.get("id")) for source in sources if isinstance(source, dict))
        supervised = process_running("weave_runtime_supervised_executor.py")
        gateway = process_running("hermes_cli.main gateway run")
        return {
            "schema": SERVICE_SCHEMA,
            "ok": True,
            "service": "weave-runtime-http",
            "generated_at": utc_now(),
            "host": socket.gethostname(),
            "pid": os.getpid(),
            "runtime_root": str(self.root),
            "ledgers": {
                "command_bus": str(self.command_ledger),
                "conversation": str(self.conversation_ledger),
                "events": str(self.events_ledger),
                "project_lane_claims": str(self.lane_claims_ledger),
            },
            "counts": {
                "commands": len(read_jsonl(self.command_ledger)),
                "conversation_messages": len(read_jsonl(self.conversation_ledger)),
                "events": len(read_jsonl(self.events_ledger)),
                "apps": len(weave_runtime_slice.list_apps(self.root)),
            },
            "authority": {
                "external_actions": "blocked_unless_owner_authorized",
                "secrets": "rejected",
                "payments": "blocked",
                "paperclip": "excluded",
            },
            "execution": {
                "executor_lane": "external_executor_required_for_mutating_work",
                "executor_command_types": sorted(EXECUTOR_COMMAND_TYPES),
                "supervised_executor_installed": supervised,
                "gateway_running": gateway,
            },
            "runtime_slice": slice_status if status_code == 200 else {"error": "runtime_status_unavailable"},
            "source_ids": source_ids,
        }

    def append_legacy_conversation(self, body: dict[str, Any]) -> dict[str, Any]:
        if contains_secret_payload(body):
            raise ValueError("conversation appears to contain a secret or credential payload")
        message = legacy_message(
            app_id=str(body.get("app_id") or "managed-app"),
            app_name=str(body.get("app_name") or body.get("app_id") or "managed-app"),
            lifecycle_stage=str(body.get("lifecycle_stage") or body.get("stage") or "runtime"),
            sender_id=str(body.get("sender_id") or "workstation-agent"),
            sender_kind=str(body.get("sender_kind") or "workstation_agent"),
            receiver_id=str(body.get("receiver_id") or "weave-runtime"),
            channel=str(body.get("channel") or "cli"),
            message_type=str(body.get("message_type") or "operator_message"),
            text=str(body.get("text") or body.get("message") or ""),
            command_id=body.get("command_id") if isinstance(body.get("command_id"), str) else None,
            evidence_refs=list(body.get("evidence_refs") or []),
            requires_owner_approval=bool(body.get("requires_owner_approval")),
        )
        append_jsonl(self.conversation_ledger, message)
        return message

    def append_legacy_command(self, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        required = {
            "schema",
            "command_id",
            "created_at",
            "sender_agent_id",
            "receiver_agent_id",
            "target_app_id",
            "command_type",
            "authority_scope",
            "payload_ref",
            "deadline_or_window",
            "requires_owner_approval",
            "ack_status",
            "result_status",
            "secret_payload_allowed",
        }
        missing = sorted(required - set(body))
        if missing:
            return 400, {"ok": False, "error": "invalid_command", "errors": [f"missing required field: {field}" for field in missing]}
        if body.get("schema") != COMMAND_SCHEMA:
            return 400, {"ok": False, "error": "invalid_command", "errors": [f"schema must be {COMMAND_SCHEMA}"]}
        if body.get("command_type") not in ALLOWED_COMMAND_TYPES:
            return 400, {"ok": False, "error": "invalid_command", "errors": [f"unsupported command_type: {body.get('command_type')}"]}
        if body.get("secret_payload_allowed") is not False or contains_secret_payload(body):
            return 400, {"ok": False, "error": "secret_payload_rejected"}

        append_jsonl(self.command_ledger, body)
        app_id = str(body.get("target_app_id") or "managed-app")
        app_name = str(body.get("target_app_name") or app_id)
        stage = str(body.get("lifecycle_stage") or "runtime")
        operator_text = str(body.get("operator_message") or body.get("payload_ref") or "")
        append_jsonl(
            self.conversation_ledger,
            legacy_message(
                app_id=app_id,
                app_name=app_name,
                lifecycle_stage=stage,
                sender_id=str(body.get("sender_agent_id") or "operator-console"),
                sender_kind="operator_console",
                receiver_id="weave-runtime",
                channel="operator_console",
                message_type="operator_message",
                text=operator_text,
                command_id=str(body.get("command_id")),
                evidence_refs=[str(body["evidence_ref"])] if body.get("evidence_ref") else [],
                requires_owner_approval=bool(body.get("requires_owner_approval")),
            ),
        )

        result_status, stop_reason = command_result(body)
        ack_status = "acknowledged"
        append_jsonl(
            self.events_ledger,
            command_state_event(
                body,
                transition="ack",
                ack_status=ack_status,
                result_status="pending" if result_status == "done" else result_status,
                stop_reason=stop_reason,
            ),
        )
        append_jsonl(
            self.events_ledger,
            command_state_event(
                body,
                transition="result" if result_status != "pending" else "executor_dispatch",
                ack_status=ack_status,
                result_status=result_status,
                stop_reason=stop_reason,
                evidence_ref=body.get("evidence_ref") if isinstance(body.get("evidence_ref"), str) else None,
            ),
        )
        append_jsonl(self.events_ledger, ops_event(body, result_status=result_status, stop_reason=stop_reason))
        append_jsonl(
            self.conversation_ledger,
            legacy_message(
                app_id=app_id,
                app_name=app_name,
                lifecycle_stage=stage,
                sender_id="weave-runtime",
                sender_kind="weave_runtime_agent",
                receiver_id=str(body.get("sender_agent_id") or "operator-console"),
                channel="runtime_agent",
                message_type="blocker" if result_status == "blocked" else "status",
                text=f"Command {body.get('command_id')} recorded by WEAVE runtime: {result_status}"
                + (f" ({stop_reason})" if stop_reason else ""),
                command_id=str(body.get("command_id")),
                evidence_refs=[str(self.events_ledger)],
                requires_owner_approval=stop_reason == "owner_approval_required",
            ),
        )
        status = 202 if result_status in {"done", "blocked", "pending"} else 400
        return status, {
            "ok": result_status in {"done", "blocked", "pending"},
            "route": "weave-runtime-http",
            "command_id": body.get("command_id"),
            "result_status": result_status,
            "stop_reason": stop_reason,
            "ledgers": {
                "command_bus": str(self.command_ledger),
                "conversation": str(self.conversation_ledger),
                "events": str(self.events_ledger),
                "project_lane_claims": str(self.lane_claims_ledger),
            },
        }

    def append_executor_event(self, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if contains_secret_payload(body):
            return 400, {"ok": False, "error": "secret_payload_rejected"}
        append_jsonl(self.events_ledger, body)
        if body.get("schema") == EXECUTOR_RESULT_SCHEMA:
            app_id = str(body.get("target_app_id") or "managed-app")
            append_jsonl(
                self.conversation_ledger,
                legacy_message(
                    app_id=app_id,
                    app_name=app_id,
                    lifecycle_stage="runtime-execution",
                    sender_id=str(body.get("openclaw_executor_id") or "external-executor"),
                    sender_kind="execution_agent",
                    receiver_id="weave-runtime",
                    channel="runtime_agent",
                    message_type="agent_reply" if body.get("result_status") == "done" else "blocker",
                    text=f"Executor result for {body.get('command_id') or body.get('source_command_id')}: "
                    f"{body.get('result_status')}. {body.get('result_text')}",
                    command_id=str(body.get("command_id") or body.get("source_command_id") or ""),
                    evidence_refs=list(body.get("evidence_refs") or []),
                    requires_owner_approval=body.get("result_status") == "blocked",
                ),
            )
        return 202, {"ok": True, "event_schema": body.get("schema"), "events_ledger": str(self.events_ledger)}


class RuntimeHandler(BaseHTTPRequestHandler):
    server_version = "WeaveRuntimeHTTP/0.2"

    @property
    def state(self) -> RuntimeState:
        return self.server.runtime_state  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.respond(HTTPStatus.NO_CONTENT, None)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        self.state.setup()
        if path == "/health":
            self.respond(HTTPStatus.OK, self.state.health())
            return
        if path == "/conversation":
            messages = filtered_records(read_jsonl(self.state.conversation_ledger), params)
            self.respond(HTTPStatus.OK, {"ok": True, "messages": messages})
            return
        if path == "/commands":
            commands = filtered_records(read_jsonl(self.state.command_ledger), params)
            self.respond(HTTPStatus.OK, {"ok": True, "commands": commands})
            return
        if path == "/events":
            events = filtered_records(read_jsonl(self.state.events_ledger), params)
            self.respond(HTTPStatus.OK, {"ok": True, "events": events})
            return
        if path == "/lane-claims":
            self.respond(HTTPStatus.OK, {"ok": True, "ledger": str(self.state.lane_claims_ledger), "claims": read_json(self.state.lane_claims_ledger)})
            return
        if path == "/lane-coordination":
            self.respond(HTTPStatus.OK, {"ok": True, "ledger": str(self.state.lane_claims_ledger), "coordination": "compatibility-summary-only"})
            return
        if path in {"/status", "/help", "/sources", "/apps", "/runtime/status", "/runtime/sources", "/telegram/commands"}:
            self.respond_slice("GET", self.map_get_path(path, params), {})
            return
        if path == "/lifecycle":
            app_id = self.query_app_id(params)
            if not app_id:
                self.respond(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "app_id_required"})
                return
            self.respond_slice("GET", f"/apps/{app_id}/lifecycle", {})
            return
        if path == "/transcript":
            app_id = self.query_app_id(params)
            if not app_id:
                self.respond(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "app_id_required"})
                return
            self.respond_slice("GET", f"/apps/{app_id}/conversation", {})
            return
        self.respond_slice("GET", path, {})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()
        if path in {"/", "/command", "/runtime-command"}:
            status, payload = self.state.append_legacy_command(body)
            self.respond(HTTPStatus(status), payload)
            return
        if path == "/conversation":
            try:
                message = self.state.append_legacy_conversation(body)
            except ValueError as exc:
                self.respond(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid_conversation", "detail": str(exc)})
                return
            self.respond(HTTPStatus.ACCEPTED, {"ok": True, "message": message, "ledger": str(self.state.conversation_ledger)})
            return
        if path == "/executor-event":
            status, payload = self.state.append_executor_event(body)
            self.respond(HTTPStatus(status), payload)
            return
        self.respond_slice("POST", path, body)

    def map_get_path(self, path: str, params: dict[str, list[str]]) -> str:
        if path == "/status":
            app_id = self.query_app_id(params)
            if app_id:
                return f"/apps/{app_id}/state"
            return "/runtime/status"
        if path == "/help":
            return "/telegram/commands"
        if path == "/sources":
            return "/runtime/sources"
        return path

    def query_app_id(self, params: dict[str, list[str]]) -> str:
        active = weave_runtime_slice.load_active_app(self.state.root)
        return (
            params.get("app_id", params.get("target_app_id", params.get("id", [""])))[0]
            or active.get("app_id")
            or ""
        )

    def respond_slice(self, method: str, path: str, body: dict[str, Any]) -> None:
        try:
            status, payload = weave_runtime_slice.dispatch_rest(self.state.root, method, path, body)
        except weave_runtime_slice.RuntimeSliceError as exc:
            status, payload = 400, {"ok": False, "error": "runtime_slice_error", "detail": str(exc)}
        self.respond(HTTPStatus(status), payload)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0") or "0")
        if length > 256_000:
            raise ValueError("request too large")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def respond(self, status: HTTPStatus, payload: dict[str, Any] | None) -> None:
        self.send_response(int(status))
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-methods", "GET,POST,OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")
        self.send_header("cache-control", "no-store")
        if payload is None:
            self.end_headers()
            return
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class RuntimeHTTPServer(ThreadingHTTPServer):
    runtime_state: RuntimeState


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("WEAVE_RUNTIME_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("WEAVE_RUNTIME_PORT", "18788")))
    parser.add_argument("--root", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--command-ledger", type=Path, default=DEFAULT_COMMAND_LEDGER)
    parser.add_argument("--conversation-ledger", type=Path, default=DEFAULT_CONVERSATION_LEDGER)
    parser.add_argument("--events-ledger", type=Path, default=DEFAULT_EVENTS_LEDGER)
    parser.add_argument("--lane-claims-ledger", type=Path, default=DEFAULT_LANE_CLAIMS_LEDGER)
    args = parser.parse_args()

    state = RuntimeState(
        root=args.root.expanduser().resolve(),
        command_ledger=args.command_ledger.expanduser().resolve(),
        conversation_ledger=args.conversation_ledger.expanduser().resolve(),
        events_ledger=args.events_ledger.expanduser().resolve(),
        lane_claims_ledger=args.lane_claims_ledger.expanduser().resolve(),
    )
    state.setup()
    server = RuntimeHTTPServer((args.host, args.port), RuntimeHandler)
    server.runtime_state = state
    print(json.dumps({"schema": SERVICE_SCHEMA, "event": "started", "host": args.host, "port": args.port, "root": str(state.root)}, sort_keys=True))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
