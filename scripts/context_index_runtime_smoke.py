#!/usr/bin/env python3
"""Exercise the WEAVE context index through the loopback runtime API.

This is a local-only smoke test. It starts the first-slice REST server on
loopback, uses the generated bearer token internally, creates a sample WIP app,
records a context snapshot event, and verifies that `/runtime/sources` exposes
the capability context index.
"""

from __future__ import annotations

import functools
import http.client
import argparse
import json
import socketserver
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

import validate_context_index
import weave_runtime_api
import weave_runtime_slice


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT_INDEX_PATH = REPO_ROOT / "docs/context-sources/livepeer-context-index.sample.json"
LOOPBACK_HOST = ".".join(["127", "0", "0", "1"])


def request(port: int, method: str, path: str, token: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    conn = http.client.HTTPConnection(LOOPBACK_HOST, port, timeout=5)
    payload = json.dumps(body or {}).encode("utf-8") if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=headers)
    response = conn.getresponse()
    raw = response.read().decode("utf-8")
    conn.close()
    data = json.loads(raw) if raw else {}
    return response.status, data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-index", type=Path, default=DEFAULT_CONTEXT_INDEX_PATH)
    parser.add_argument("--report-out", type=Path, help="write a JSON proof report")
    args = parser.parse_args(argv)

    context_index_path = args.context_index.expanduser().resolve()
    validate_context_index.validate_index(validate_context_index.load_index(context_index_path))
    report: dict[str, Any] = {
        "schema": "weave/context-index-runtime-smoke/v0.1",
        "context_index": str(context_index_path),
        "checks": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "weave-root"
        weave_runtime_slice.setup_weave_root(root)
        token = (root / "runtime/tokens/local-api-token").read_text(encoding="utf-8").strip()
        handler = functools.partial(weave_runtime_api.RuntimeApiHandler, weave_root=root)
        with socketserver.TCPServer((LOOPBACK_HOST, 0), handler) as server:
            port = int(server.server_address[1])
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                status, health = request(port, "GET", "/health", token)
                assert status == 200, health
                assert health["real_hermes_runtime"] is False, health
                report["checks"].append({"name": "health", "status": status, "payload": health})

                status, sources = request(port, "GET", "/runtime/sources", token)
                assert status == 200, sources
                source_ids = {source["id"] for source in sources["source_map"]["sources"]}
                assert "capability-context-index" in source_ids, sources
                report["checks"].append(
                    {
                        "name": "runtime_sources",
                        "status": status,
                        "source_ids": sorted(source_ids),
                    }
                )

                status, created = request(
                    port,
                    "POST",
                    "/apps",
                    token,
                    {"app_id": "wip-livepeer", "name": "WIP Livepeer App"},
                )
                assert status == 201, created
                report["checks"].append(
                    {
                        "name": "create_wip_app",
                        "status": status,
                        "app_id": created["result"]["app"]["app_id"],
                    }
                )

                context_event = weave_runtime_slice.new_event(
                    "artifact.created",
                    "wip-livepeer",
                    "research",
                    "Capability context snapshot recorded for WIP Livepeer App.",
                    payload={
                        "context_snapshot": {
                            "index_path": str(context_index_path),
                            "schema": "weave/context-index/v0.1",
                            "application_paths_checked": [
                                "existing_api",
                                "gateway_capability",
                                "new_orchestrator_capability",
                            ],
                            "sources_used": [
                                "livepeer-docs-index",
                                "livepeer-ai-api",
                                "livepeer-ai-gateway",
                                "livepeer-open-ai-stack",
                            ],
                        }
                    },
                )
                status, appended = request(port, "POST", "/apps/wip-livepeer/events", token, context_event)
                assert status == 201, appended
                report["checks"].append(
                    {
                        "name": "append_context_snapshot",
                        "status": status,
                        "event_type": appended["event"]["type"],
                        "stage": appended["event"]["stage"],
                    }
                )

                status, events = request(port, "GET", "/apps/wip-livepeer/events", token)
                assert status == 200, events
                assert events["events"][-1]["payload"]["context_snapshot"]["application_paths_checked"] == [
                    "existing_api",
                    "gateway_capability",
                    "new_orchestrator_capability",
                ]
                report["checks"].append(
                    {
                        "name": "read_context_snapshot",
                        "status": status,
                        "application_paths_checked": events["events"][-1]["payload"]["context_snapshot"][
                            "application_paths_checked"
                        ],
                        "sources_used": events["events"][-1]["payload"]["context_snapshot"]["sources_used"],
                    }
                )

                status, app_state = request(port, "GET", "/apps/wip-livepeer/state", token)
                assert status == 200, app_state
                assert app_state["app"]["app_id"] == "wip-livepeer"
                assert app_state["foundation_gate"]["passed"] is False
                report["checks"].append(
                    {
                        "name": "read_wip_app_state",
                        "status": status,
                        "app_id": app_state["app"]["app_id"],
                        "stage": app_state["stage"]["stage"],
                        "foundation_gate_passed": app_state["foundation_gate"]["passed"],
                    }
                )
            finally:
                server.shutdown()
                thread.join(timeout=5)

    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("context index runtime smoke: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"context index runtime smoke: failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
