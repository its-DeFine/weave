#!/usr/bin/env python3
"""Validate a WEAVE capability context index.

The validator is intentionally stdlib-only so agents can run it in stripped-down
runtime environments. It validates the fields WEAVE needs for lifecycle use; the
JSON Schema file remains the public schema reference.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "weave/context-index/v0.1"
REQUIRED_SOURCE_FIELDS = {
    "id",
    "name",
    "type",
    "url",
    "stage_use",
    "application_paths",
    "freshness",
    "summary",
}
REQUIRED_APPLICATION_PATHS = {
    "existing_api",
    "gateway_capability",
    "new_orchestrator_capability",
}
REQUIRED_SOURCE_TYPES = {
    "api",
    "documentation",
    "gateway",
    "orchestrator-capability",
}
REQUIRED_STAGE_USES = {
    "research",
    "selection",
    "plan",
    "engineering",
    "qa",
}
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SCHEMA_SOURCE_TYPES = {
    "api",
    "sdk",
    "documentation",
    "example",
    "gateway",
    "pipeline",
    "capability-discovery",
    "pricing",
    "health",
    "orchestrator-capability",
    "container",
    "model",
    "hardware",
    "conformance-test",
    "operations",
    "kpi",
    "outreach",
}
SCHEMA_STAGE_USES = {
    "intent",
    "research",
    "selection",
    "plan",
    "engineering",
    "qa",
    "kpi",
    "marketing",
    "iteration",
    "analysis",
}
SCHEMA_FRESHNESS_VALUES = {"stable_reference", "verify_before_use", "snapshot"}


class ValidationError(Exception):
    """Raised when a context index is not usable by WEAVE."""


def ensure_list(value: Any, field: str, source_id: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"source {source_id}: {field} must be a list")
    return value


def ensure_string(value: Any, field: str, source_id: str = "index") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"source {source_id}: {field} must be a non-empty string")
    return value


def ensure_string_list(value: Any, field: str, source_id: str, allowed: set[str] | None = None) -> list[str]:
    items = ensure_list(value, field, source_id)
    output: list[str] = []
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"source {source_id}: {field} entries must be non-empty strings")
        if allowed is not None and item not in allowed:
            raise ValidationError(f"source {source_id}: invalid {field}: {item}")
        output.append(item)
    return output


def validate_index(index: dict[str, Any]) -> None:
    if index.get("schema") != SCHEMA:
        raise ValidationError(f"schema must be {SCHEMA}")
    for field in ("version", "updated_at"):
        ensure_string(index.get(field), field)
    sources = index.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValidationError("sources must be a non-empty list")

    seen_ids: set[str] = set()
    all_paths: set[str] = set()
    all_types: set[str] = set()
    all_stages: set[str] = set()

    for source in sources:
        if not isinstance(source, dict):
            raise ValidationError("each source must be an object")
        source_id = str(source.get("id") or "")
        if not source_id:
            raise ValidationError("source id is required")
        if not SOURCE_ID_RE.fullmatch(source_id):
            raise ValidationError(f"source {source_id}: id must match ^[a-z0-9][a-z0-9-]*$")
        if source_id in seen_ids:
            raise ValidationError(f"duplicate source id: {source_id}")
        seen_ids.add(source_id)

        missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
        if missing:
            raise ValidationError(f"source {source_id}: missing fields: {', '.join(missing)}")

        for field in ("name", "url", "summary"):
            ensure_string(source.get(field), field, source_id)
        source_type = ensure_string(source.get("type"), "type", source_id)
        if source_type not in SCHEMA_SOURCE_TYPES:
            raise ValidationError(f"source {source_id}: invalid type: {source_type}")
        freshness = ensure_string(source.get("freshness"), "freshness", source_id)
        if freshness not in SCHEMA_FRESHNESS_VALUES:
            raise ValidationError(f"source {source_id}: invalid freshness: {freshness}")
        all_types.add(source_type)
        all_paths.update(ensure_string_list(source["application_paths"], "application_paths", source_id, REQUIRED_APPLICATION_PATHS))
        all_stages.update(ensure_string_list(source["stage_use"], "stage_use", source_id, SCHEMA_STAGE_USES))

        if freshness == "verify_before_use" and not source.get("last_verified_at"):
            raise ValidationError(f"source {source_id}: verify_before_use requires last_verified_at")

    missing_paths = sorted(REQUIRED_APPLICATION_PATHS - all_paths)
    if missing_paths:
        raise ValidationError(f"missing application paths: {', '.join(missing_paths)}")
    missing_types = sorted(REQUIRED_SOURCE_TYPES - all_types)
    if missing_types:
        raise ValidationError(f"missing source types: {', '.join(missing_types)}")
    missing_stages = sorted(REQUIRED_STAGE_USES - all_stages)
    if missing_stages:
        raise ValidationError(f"missing lifecycle stage uses: {', '.join(missing_stages)}")


def load_index(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("context index root must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=Path("docs/context-sources/livepeer-context-index.sample.json"))
    args = parser.parse_args(argv)

    try:
        validate_index(load_index(args.path))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"invalid WEAVE context index: {exc}", file=sys.stderr)
        return 1

    print(f"valid WEAVE context index: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
