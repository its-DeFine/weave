#!/usr/bin/env python3
"""Validate the public-safe workstation context sync sample."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = REPO_ROOT / "docs" / "samples" / "workstation-context-sync.sample.json"
SCHEMA = "weave-workstation-context-sync/v0.1"

PRIVATE_TEXT_RE = re.compile(
    r"(/Users/|/home/|/opt/|127\.0\.0\.1|192\.168\.|100\.\d{1,3}\.|weave-vm\d+|"
    + "agent"
    + r"-ops)",
    re.IGNORECASE,
)
BAD_VALUE_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{20,}|"
    r"[A-Z0-9_]*(API[_-]?KEY|SECRET|TOKEN|PASSWORD|PRIVATE[_-]?KEY)[A-Z0-9_]*\s*=\s*[^\s]+)",
    re.IGNORECASE,
)


class ContextSyncContractError(Exception):
    pass


def flatten(value: Any) -> list[str]:
    if isinstance(value, dict):
        text = []
        for key, item in value.items():
            text.append(str(key))
            text.extend(flatten(item))
        return text
    if isinstance(value, list):
        text = []
        for item in value:
            text.extend(flatten(item))
        return text
    return [str(value)]


def require_string(packet: dict[str, Any], field: str) -> None:
    if not isinstance(packet.get(field), str) or not packet[field]:
        raise ContextSyncContractError(f"{field} must be a non-empty string")


def require_string_list(packet: dict[str, Any], field: str) -> None:
    value = packet.get(field)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ContextSyncContractError(f"{field} must be a non-empty string list")


def validate_packet(packet: dict[str, Any]) -> None:
    for field in [
        "schema",
        "packet_id",
        "app_id",
        "app_name",
        "lifecycle_stage",
        "summary",
        "deadline_or_window",
    ]:
        require_string(packet, field)
    if packet["schema"] != SCHEMA:
        raise ContextSyncContractError(f"schema must be {SCHEMA}")
    for field in ["work_done", "evidence_refs", "capabilities", "blockers", "stop_boundaries"]:
        require_string_list(packet, field)
    decisions = packet.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise ContextSyncContractError("decisions must be a non-empty list")
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ContextSyncContractError("decision entries must be objects")
        for field in ["label", "status", "note"]:
            if not isinstance(decision.get(field), str) or not decision[field]:
                raise ContextSyncContractError(f"decision.{field} must be a non-empty string")
    if packet.get("secret_payload_allowed") is not False:
        raise ContextSyncContractError("secret_payload_allowed must be false")
    combined = "\n".join(flatten(packet))
    if PRIVATE_TEXT_RE.search(combined):
        raise ContextSyncContractError("sample contains private host or filesystem text")
    if BAD_VALUE_RE.search(combined):
        raise ContextSyncContractError("sample contains secret-like text")


def load_sample(path: Path = SAMPLE_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContextSyncContractError("sample must be a JSON object")
    return data


def main() -> int:
    try:
        validate_packet(load_sample())
    except (OSError, json.JSONDecodeError, ContextSyncContractError) as exc:
        print(f"context sync contract smoke: FAILED: {exc}", file=sys.stderr)
        return 1
    print("context sync contract smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
