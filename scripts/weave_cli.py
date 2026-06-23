#!/usr/bin/env python3
"""Small WEAVE CLI for COS-first local skeleton validation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import TextIO

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import weave_cos_skeleton
import weave_eval


class CliError(Exception):
    """Raised when the WEAVE CLI cannot complete a requested local action."""


def print_line(output: TextIO, text: str = "") -> None:
    print(text, file=output)


def cos_bootstrap_message(home: Path, source: Path, intent: str, readback: dict[str, object]) -> str:
    state_line = str(readback["state_line"])
    return (
        f"{state_line}\n"
        "I am COS WEAVE in this Codex thread. I use this repository as a visible "
        "file skeleton for app intent, lifecycle state, todos, worker packets, "
        "proof, blockers, review, and readback.\n"
        f"WEAVE home: {home}\n"
        f"Source repo: {source}\n"
        f"Owner intent: {intent}\n"
        f"Proof path: {readback['proof_path']}\n"
        f"Next safe action: {readback['next_action']}\n"
        "No live workers, tracker mutation, deploy, public send, billing, "
        "credential access, or production effect is claimed."
    )


def blocked_payload(args: argparse.Namespace, source: Path, reason: str, owner_action: str) -> dict[str, object]:
    home = args.home.expanduser() if args.home else Path("runs") / "cos-weave-home"
    return {
        "schema": "weave-cos-bootstrap/v0.1",
        "state": "BLOCKED",
        "surface": args.surface,
        "home": str(home),
        "source": str(source),
        "intent": args.intent,
        "reason": reason,
        "owner_action": owner_action,
        "manual_steps_required": [],
        "live_effects": False,
        "non_claims": [
            "does not prove live worker execution",
            "does not prove tracker mutation",
            "does not prove deployment, public send, billing, or credential access",
        ],
    }


def print_payload(payload: dict[str, object], output: TextIO, *, as_json: bool) -> None:
    if as_json:
        print_line(output, json.dumps(payload, indent=2, sort_keys=True))
        return

    print_line(output, "WEAVE COS Bootstrap")
    for key in [
        "state",
        "home",
        "source",
        "intent",
        "app_id",
        "app_count",
        "proof_path",
        "readback_path",
        "requested_lifecycle_stage",
        "reason",
        "owner_action",
    ]:
        if key in payload:
            print_line(output, f"- {key}: {payload[key]}")
    print_line(output, "- manual_commands_required: false")
    print_line(output, "- manual_lifecycle_classification_required: false")
    print_line(output, "- live_effects: false")
    print_line(output)
    if payload.get("onboarding_questions"):
        print_line(output, "Onboarding questions:")
        for question in payload["onboarding_questions"]:  # type: ignore[index]
            print_line(output, f"- {question}")
        print_line(output)
    if payload.get("cos_message"):
        print_line(output, str(payload["cos_message"]))


def local_source_from_arg(raw: str) -> Path | None:
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw.strip()):
        return None
    return Path(raw).expanduser()


def cos_bootstrap(args: argparse.Namespace, output: TextIO) -> int:
    source_raw = str(args.source).strip()
    source = local_source_from_arg(source_raw)
    if source is None:
        payload = blocked_payload(
            args,
            Path(source_raw),
            "URL bootstrap is documented for a Codex agent, but this local CLI does not clone network sources",
            "Use the launcher prompt in COS_WEAVE_LAUNCHER.md or provide a local repository path.",
        )
        print_payload(payload, output, as_json=args.json)
        return 1

    home = args.home.expanduser() if args.home else source / "runs" / "cos-weave-home"
    if not source.exists() or not source.is_dir():
        payload = blocked_payload(args, source, "source path does not exist", "Provide an existing local WEAVE repository path.")
        print_payload(payload, output, as_json=args.json)
        return 1
    if not (source / "AGENTS.md").exists() or not (source / "docs" / "COS_WEAVE_BOOTSTRAP.md").exists():
        payload = blocked_payload(
            args,
            source,
            "source path does not look like a WEAVE repository",
            "Provide a local WEAVE repository path with AGENTS.md and docs/COS_WEAVE_BOOTSTRAP.md.",
        )
        print_payload(payload, output, as_json=args.json)
        return 1

    payload = weave_cos_skeleton.bootstrap(
        source=source,
        home=home,
        surface=args.surface,
        intent=args.intent,
        app_id=args.app_id,
        app_name=args.app_name,
    )
    payload["cos_message"] = cos_bootstrap_message(
        home,
        source,
        args.intent,
        {
            "state_line": payload["state_line"],
            "proof_path": payload["proof_path"],
            "next_action": payload["readback"]["next_action"],
        },
    )
    weave_cos_skeleton.write_json(home / "cos-bootstrap" / "latest.json", payload)
    print_payload(payload, output, as_json=args.json)
    return 0


def readback(args: argparse.Namespace, output: TextIO) -> int:
    home = args.home.expanduser()
    if not (home / "state.json").exists():
        raise CliError(f"WEAVE home is missing or incomplete: {home}")
    payload = weave_cos_skeleton.readback(home)
    if args.json:
        print_line(output, json.dumps(payload, indent=2, sort_keys=True))
        return 0
    active = payload.get("active_app", {})
    print_line(output, "WEAVE Readback")
    print_line(output, f"- home: {payload['home']}")
    print_line(output, f"- state: {payload['state']}")
    print_line(output, f"- active_app_id: {payload['active_app_id']}")
    if isinstance(active, dict):
        print_line(output, f"- current_stage: {active.get('current_stage', 'unknown')}")
        print_line(output, f"- requested_stage: {active.get('requested_stage', 'unknown')}")
    print_line(output, f"- next_action: {payload['next_action']}")
    print_line(output, "- non_claims:")
    for item in payload.get("non_claims", []):
        print_line(output, f"  - {item}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="weave", description="WEAVE local skeleton tools")
    subparsers = parser.add_subparsers(dest="command")

    bootstrap = subparsers.add_parser("cos-bootstrap", help="create or update a local COS WEAVE file skeleton")
    bootstrap.add_argument("--source", required=True, help="local WEAVE repository path")
    bootstrap.add_argument("--home", type=Path, default=None, help="optional WEAVE home path")
    bootstrap.add_argument("--surface", choices=("codex", "other", "unknown"), default="codex")
    bootstrap.add_argument("--intent", required=True)
    bootstrap.add_argument("--app-id")
    bootstrap.add_argument("--app-name")
    bootstrap.add_argument("--json", action="store_true")

    rb = subparsers.add_parser("readback", help="read current state from a COS WEAVE home")
    rb.add_argument("--home", type=Path, required=True)
    rb.add_argument("--json", action="store_true")

    eval_parser = subparsers.add_parser("eval", help="run evidence-bound lifecycle or release-readiness evals")
    eval_parser.add_argument("eval_stage", nargs="?", help="lifecycle stage or release-readiness")
    eval_parser.add_argument("--list", dest="list_eval_contracts", action="store_true")
    eval_parser.add_argument("--contract-file", type=Path)
    eval_parser.add_argument("--review-file", type=Path)
    eval_parser.add_argument("--review-template", action="store_true")
    eval_parser.add_argument("--artifact", default="current")
    eval_parser.add_argument("--run-gates", action="store_true")
    eval_parser.add_argument("--strict", action="store_true")
    eval_parser.add_argument("--json", action="store_true")
    return parser


def print_help_alias(parser: argparse.ArgumentParser, argv: list[str], output: TextIO) -> int:
    if len(argv) == 1:
        parser.print_help(output)
        print_line(output, "")
        print_line(output, "Core commands:")
        print_line(output, "  bin/weave cos-bootstrap --source . --intent 'build a local calculator app'")
        print_line(output, "  bin/weave readback --home runs/cos-weave-home")
        print_line(output, "  bin/weave eval --list")
        return 0
    topic = argv[1]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction) and topic in action.choices:
            action.choices[topic].print_help(output)
            return 0
    raise CliError(f"unknown help topic: {topic}")


def eval_command(args: argparse.Namespace, output: TextIO) -> int:
    eval_args: list[str] = []
    if args.eval_stage:
        eval_args.append(args.eval_stage)
    if args.list_eval_contracts:
        eval_args.append("--list")
    if args.contract_file:
        eval_args.extend(["--contract-file", str(args.contract_file)])
    if args.review_file:
        eval_args.extend(["--review-file", str(args.review_file)])
    if args.review_template:
        eval_args.append("--review-template")
    if args.artifact:
        eval_args.extend(["--artifact", args.artifact])
    if args.run_gates:
        eval_args.append("--run-gates")
    if args.strict:
        eval_args.append("--strict")
    if args.json:
        eval_args.append("--json")
    return weave_eval.main(eval_args, output=output)


def main(argv: list[str] | None = None, *, output: TextIO = sys.stdout) -> int:
    parser = build_parser()
    argv_list = sys.argv[1:] if argv is None else list(argv)
    try:
        if argv_list and argv_list[0] == "help":
            return print_help_alias(parser, argv_list, output)
        args = parser.parse_args(argv_list)
        if args.command == "cos-bootstrap":
            return cos_bootstrap(args, output)
        if args.command == "readback":
            return readback(args, output)
        if args.command == "eval":
            return eval_command(args, output)
        parser.print_help(output)
        return 0
    except CliError as exc:
        print_line(output, f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
