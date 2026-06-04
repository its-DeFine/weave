#!/usr/bin/env python3
"""Generate a read-only WEAVE runtime source map.

The script takes explicit local paths and records where runtime state, Hermes
session state, repo checkouts, and historical ledgers live. It never reads or
prints secret values. Private paths belong in the generated local runtime file,
not in tracked repository artifacts.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import weave_runtime_slice


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_HOME = REPO_ROOT / "runs" / "runtime-home"
DEFAULT_WEAVE_ROOT = DEFAULT_RUNTIME_HOME / "weave-state"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def line_count(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def file_meta(path: Path) -> dict[str, Any]:
    status = weave_runtime_slice.path_status(path)
    meta = dict(status)
    if path.exists():
        stat = path.stat()
        meta["mtime"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
        if path.is_file():
            meta["line_count"] = line_count(path)
    return meta


def git_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False}
    result: dict[str, Any] = {"available": False}
    commands = {
        "commit": ["git", "rev-parse", "HEAD"],
        "branch": ["git", "branch", "--show-current"],
    }
    for key, command in commands.items():
        completed = subprocess.run(command, cwd=path, capture_output=True, text=True, check=False)
        if completed.returncode == 0:
            result[key] = completed.stdout.strip()
            result["available"] = True
    status = subprocess.run(["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True, check=False)
    if status.returncode == 0:
        result["dirty"] = bool(status.stdout.strip())
    return result


def sqlite_counts(path: Path, tables: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {}
    counts: dict[str, Any] = {}
    try:
        connection = sqlite3.connect(str(path))
    except sqlite3.Error as exc:
        return {"error": str(exc)}
    try:
        for table in tables:
            try:
                counts[table] = connection.execute(f"select count(*) from {table}").fetchone()[0]
            except sqlite3.Error as exc:
                counts[table] = {"error": str(exc)}
    finally:
        connection.close()
    return counts


def source_entry(
    *,
    source_id: str,
    label: str,
    kind: str,
    role: str,
    path: Path | str,
    status: str,
    mutable: bool,
    sensitive: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "id": source_id,
        "label": label,
        "kind": kind,
        "role": role,
        "status": status,
        "path": str(path),
        "mutable": mutable,
        "sensitive": sensitive,
    }
    if sensitive:
        entry["secret_value_printed"] = False
    if isinstance(path, Path):
        entry["path_status"] = file_meta(path)
    if extra:
        entry.update(extra)
    return entry


def add_history_sources(sources: list[dict[str, Any]], history_root: Path) -> list[str]:
    ids: list[str] = []
    ledgers = [
        ("runtime-command-bus", "Command bus", "command-bus.jsonl", "runtime command ledger"),
        ("runtime-conversation-ledger", "Conversation ledger", "conversation.jsonl", "runtime conversation history"),
        ("runtime-event-ledger", "Event ledger", "events.jsonl", "runtime event ledger"),
        ("project-lane-claims", "Project lane claims", "project-lane-claims.json", "project lane coordination state"),
    ]
    for source_id, label, filename, role in ledgers:
        path = history_root / filename
        status = "active" if path.exists() else "missing"
        sources.append(
            source_entry(
                source_id=source_id,
                label=label,
                kind="jsonl" if filename.endswith(".jsonl") else "json",
                role=role,
                path=path,
                status=status,
                mutable=True,
            )
        )
        ids.append(source_id)
    return ids


def add_hermes_sources(sources: list[dict[str, Any]], hermes_home: Path) -> list[str]:
    ids: list[str] = []
    state_db = hermes_home / "state.db"
    sources.append(
        source_entry(
            source_id="hermes-state-db",
            label="Hermes session database",
            kind="sqlite",
            role="active Hermes conversation/session memory",
            path=state_db,
            status="active" if state_db.exists() else "missing",
            mutable=True,
            extra={"table_counts": sqlite_counts(state_db, ["sessions", "messages"])},
        )
    )
    ids.append("hermes-state-db")
    for source_id, label, relpath, role in [
        ("hermes-session-index", "Hermes session index", "sessions/sessions.json", "Telegram chat to session binding"),
        ("hermes-gateway-state", "Hermes gateway state", "gateway_state.json", "gateway process state"),
        ("hermes-channel-directory", "Hermes channel directory", "channel_directory.json", "configured communication channels"),
    ]:
        path = hermes_home / relpath
        sources.append(
            source_entry(
                source_id=source_id,
                label=label,
                kind="json",
                role=role,
                path=path,
                status="active" if path.exists() else "missing",
                mutable=True,
            )
        )
        ids.append(source_id)
    return ids


def add_repo_source(
    sources: list[dict[str, Any]],
    repo_root: Path,
    *,
    expected_commit: str | None,
) -> None:
    meta = git_meta(repo_root)
    status = "active" if meta.get("available") else "missing"
    if expected_commit and meta.get("commit") and not str(meta["commit"]).startswith(expected_commit):
        status = "stale"
        meta["expected_commit"] = expected_commit
    sources.append(
        source_entry(
            source_id="repo-checkout",
            label="Repository checkout",
            kind="git",
            role="tracked runtime code and public contracts",
            path=repo_root,
            status=status,
            mutable=True,
            extra={"git": meta},
        )
    )


def latest_child(path: Path) -> Path | None:
    if not path.exists():
        return None
    children = [child for child in path.iterdir() if child.is_dir()]
    if not children:
        return None
    return max(children, key=lambda child: child.stat().st_mtime)


def build_source_map(args: argparse.Namespace) -> dict[str, Any]:
    runtime_home = (getattr(args, "runtime_home", None) or DEFAULT_RUNTIME_HOME).expanduser().resolve()
    root = (getattr(args, "weave_root", None) or (runtime_home / "weave-state")).expanduser().resolve()
    weave_runtime_slice.setup_weave_root(root, autonomy_mode=args.autonomy_mode)
    sources = weave_runtime_slice.default_source_map(root)["sources"]
    history_ids = ["runtime-home", "app-registry"]

    if args.history_root:
        history_ids.extend(add_history_sources(sources, args.history_root.expanduser().resolve()))
    if args.hermes_home:
        history_ids.extend(add_hermes_sources(sources, args.hermes_home.expanduser().resolve()))
    if args.repo_root:
        add_repo_source(sources, args.repo_root.expanduser().resolve(), expected_commit=args.expected_commit)
    if args.addons_root:
        addons_root = args.addons_root.expanduser().resolve()
        latest = latest_child(addons_root)
        sources.append(
            source_entry(
                source_id="runtime-addons",
                label="Runtime add-ons",
                kind="directory",
                role="optional executor, proof, and operator tooling add-ons",
                path=addons_root,
                status="active" if addons_root.exists() else "missing",
                mutable=True,
                extra={"latest_child": str(latest) if latest else ""},
            )
        )

    return {
        "schema": weave_runtime_slice.SOURCE_MAP_SCHEMA,
        "generated_at": utc_now(),
        "canonical_source_id": "weave-root",
        "history_source_ids": sorted(set(history_ids)),
        "sources": sources,
        "next_unification_action": (
            "Load this source map into Hermes startup context and use /sources or /status "
            "to distinguish active, stale, and historical state before app work."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-home", type=Path)
    parser.add_argument("--weave-root", type=Path)
    parser.add_argument("--history-root", type=Path)
    parser.add_argument("--hermes-home", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--addons-root", type=Path)
    parser.add_argument("--expected-commit")
    parser.add_argument("--autonomy-mode", default=weave_runtime_slice.DEFAULT_AUTONOMY_MODE)
    parser.add_argument("--check", action="store_true", help="build and validate without writing")
    parser.add_argument("--json", action="store_true", help="print the generated map")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    runtime_home = (args.runtime_home or DEFAULT_RUNTIME_HOME).expanduser().resolve()
    resolved_weave_root = (args.weave_root or (runtime_home / "weave-state")).expanduser().resolve()
    source_map = build_source_map(args)
    weave_runtime_slice.validate_source_map(source_map)
    if not args.check:
        weave_runtime_slice.write_source_map(resolved_weave_root, source_map)
    if args.json:
        print(json.dumps(source_map, indent=2, sort_keys=True))
    else:
        summary = weave_runtime_slice.summarize_source_map(source_map)
        print("source map: ok")
        print(f"sources: {summary['source_count']}")
        print(f"canonical_source: {summary['canonical_source_id']}")
        print(f"written: {str(not args.check).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
