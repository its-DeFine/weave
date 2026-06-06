#!/usr/bin/env python3
"""Validate a WEAVE capability context index.

The validator is intentionally stdlib-only so agents can run it in stripped-down
runtime environments. It validates the fields WEAVE needs for lifecycle use; the
JSON Schema file remains the public schema reference.
"""

from __future__ import annotations

import argparse
import json
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


class ValidationError(Exception):
    """Raised when a context index is not usable by WEAVE."""


def ensure_list(value: Any, field: str, source_id: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"source {source_id}: {field} must be a list")
    return value


def validate_index(index: dict[str, Any]) -> None:
    if index.get("schema") != SCHEMA:
        raise ValidationError(f"schema must be {SCHEMA}")
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
        if source_id in seen_ids:
            raise ValidationError(f"duplicate source id: {source_id}")
        seen_ids.add(source_id)

        missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
        if missing:
            raise ValidationError(f"source {source_id}: missing fields: {', '.join(missing)}")

        all_types.add(str(source["type"]))
        all_paths.update(str(item) for item in ensure_list(source["application_paths"], "application_paths", source_id))
        all_stages.update(str(item) for item in ensure_list(source["stage_use"], "stage_use", source_id))

        if str(source.get("freshness")) == "verify_before_use" and not source.get("last_verified_at"):
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
