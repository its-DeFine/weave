#!/usr/bin/env python3
"""Validate that a pull request records proof, boundaries, and merge criteria.

The check intentionally reads only the GitHub event payload or an explicit local
body file. It does not call GitHub APIs, so forked PRs and local rehearsals keep
the same public-safe behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ISSUE_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
SECTION_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
CHECKED_BOX_RE = re.compile(r"^\s*-\s*\[[xX]\]\s+", re.MULTILINE)
UNCHECKED_BOX_RE = re.compile(r"^\s*-\s*\[\s\]\s+", re.MULTILINE)
COMMAND_RE = re.compile(r"`([^`]+)`")
RISK_WORDS = ("failed", "failing", "skipped", "blocked", "waived")


class ProofLedgerError(Exception):
    """Raised when the PR body is missing required proof-ledger content."""


def load_body_from_event(event_path: Path) -> tuple[str, bool]:
    """Return the PR body and whether this was a pull_request event.

    Push events have no reviewable PR body. Those should skip cleanly rather
    than forcing fake proof content into commit messages.
    """

    payload = json.loads(event_path.read_text(encoding="utf-8"))
    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        return "", False
    return str(pull_request.get("body") or ""), True


def body_from_args(args: argparse.Namespace) -> tuple[str, bool]:
    if args.body:
        return args.body, True
    if args.body_file:
        return args.body_file.read_text(encoding="utf-8"), True
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path:
        return load_body_from_event(Path(event_path))
    return "", False


def normalized_sections(body: str) -> set[str]:
    return {match.group(1).strip().lower() for match in SECTION_RE.finditer(body)}


def has_section(sections: set[str], *needles: str) -> bool:
    return any(any(needle in section for needle in needles) for section in sections)


def command_lines(body: str) -> list[str]:
    commands: list[str] = []
    for command in COMMAND_RE.findall(body):
        # Only shell-like command snippets count as proof. Inline labels such as
        # `local proof` are useful prose but not executable evidence.
        if command.startswith(("python", "python3", "git ", "gh ", "bin/", "./", "npm ", "pnpm ", "yarn ")):
            commands.append(command)
    return commands


def validate_body(body: str) -> None:
    missing: list[str] = []
    sections = normalized_sections(body)
    lowered = body.lower()

    if not ISSUE_RE.search(body):
        missing.append("issue link or identifier such as ATM-250")
    if not has_section(sections, "proof ledger", "proof"):
        missing.append("Proof Ledger section")
    if not has_section(sections, "proof boundary", "proof boundaries", "non-claims", "unproven"):
        missing.append("Proof Boundary / Non-claims section")
    if not has_section(sections, "merge criteria", "merge readiness"):
        missing.append("Merge Criteria section")
    if "local proof" not in lowered:
        missing.append("local proof boundary label")
    if "runtime/live proof" not in lowered and "live proof" not in lowered:
        missing.append("runtime/live proof boundary label")
    if "unproven" not in lowered and "non-claim" not in lowered:
        missing.append("unproven boundary or non-claim statement")
    if "failing checks" not in lowered:
        missing.append("failing checks disposition")
    if "owner/project criteria" not in lowered and "owner criteria" not in lowered:
        missing.append("owner/project criteria disposition")
    if not CHECKED_BOX_RE.search(body):
        missing.append("at least one checked proof or merge checkbox")
    if UNCHECKED_BOX_RE.search(body):
        missing.append("no unchecked PR-template checkboxes may remain")
    if not command_lines(body):
        missing.append("at least one executable proof command in backticks")

    # If a PR says something failed/skipped/blocked, it must also say whether
    # that is accepted. This preserves the distinction between known gaps and
    # silent bypasses without trying to interpret every possible CI wording.
    if any(word in lowered for word in RISK_WORDS) and "accepted" not in lowered and "none" not in lowered:
        missing.append("accepted disposition for failed/skipped/blocked checks")

    if missing:
        raise ProofLedgerError("missing PR proof ledger fields: " + "; ".join(missing))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a WEAVE PR proof ledger.")
    parser.add_argument("--body-file", type=Path, help="Read PR body markdown from a local file.")
    parser.add_argument("--body", help="Validate this body text directly.")
    args = parser.parse_args(argv)

    try:
        body, is_pr = body_from_args(args)
        if not is_pr:
            print("PR proof ledger check skipped: not a pull_request event")
            return 0
        validate_body(body)
    except (OSError, json.JSONDecodeError, ProofLedgerError) as exc:
        print(f"PR proof ledger check failed: {exc}", file=sys.stderr)
        return 1
    print("PR proof ledger check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
