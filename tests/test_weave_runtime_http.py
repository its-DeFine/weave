from __future__ import annotations

import functools
import http.client
import json
import socketserver
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import weave_runtime_http
import weave_runtime_slice as runtime


LOOPBACK_HOST = ".".join(["127", "0", "0", "1"])


def request(port: int, method: str, path: str, body: dict | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    conn = http.client.HTTPConnection(LOOPBACK_HOST, port, timeout=5)
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    request_headers = dict(headers or {})
    if payload is not None:
        request_headers.setdefault("Content-Type", "application/json")
    conn.request(method, path, body=payload, headers=request_headers)
    response = conn.getresponse()
    raw = response.read().decode("utf-8")
    conn.close()
    return response.status, json.loads(raw) if raw else {}


def raw_request(port: int, method: str, path: str, payload: bytes, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    conn = http.client.HTTPConnection(LOOPBACK_HOST, port, timeout=5)
    request_headers = dict(headers or {})
    request_headers.setdefault("Content-Type", "application/json")
    conn.request(method, path, body=payload, headers=request_headers)
    response = conn.getresponse()
    raw = response.read().decode("utf-8")
    conn.close()
    return response.status, json.loads(raw) if raw else {}


def fill(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\nStatus: complete\n\nRequired facts are recorded for this runtime HTTP test.\n",
        encoding="utf-8",
    )


def complete_foundation(root: Path, app_id: str) -> None:
    fill(root / "artifacts" / "general" / "soul.md", "Hermes Soul")
    fill(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile")
    fill(root / "apps" / app_id / "context" / "app-context.md", "App Context")
    fill(root / "apps" / app_id / "inventory" / "app-inventory.md", "App Inventory")
    fill(root / "apps" / app_id / "contract" / "gestaltian-contract.md", "Gestaltian Contract")


class WeaveRuntimeHttpTests(unittest.TestCase):
    def run_server(self, root: Path):
        state = weave_runtime_http.RuntimeState(
            root=root,
            command_ledger=root / "command-bus.jsonl",
            conversation_ledger=root / "conversation.jsonl",
            events_ledger=root / "events.jsonl",
            lane_claims_ledger=root / "project-lane-claims.json",
        )
        state.setup()
        handler = functools.partial(weave_runtime_http.RuntimeHandler)
        server = weave_runtime_http.RuntimeHTTPServer((LOOPBACK_HOST, 0), handler)
        server.runtime_state = state
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_health_sources_apps_and_transcript_routes_delegate_to_runtime_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            server, thread = self.run_server(root)
            port = int(server.server_address[1])
            try:
                status, health = request(port, "GET", "/health")
                self.assertEqual(status, 200)
                self.assertEqual(health["schema"], weave_runtime_http.SERVICE_SCHEMA)
                self.assertEqual(health["transport"]["auth_policy"], weave_runtime_http.AUTH_POLICY_TEST_ONLY_NONE)
                self.assertFalse(health["transport"]["auth_required"])
                self.assertIn("capability-context-index", health["source_ids"])

                status, sources = request(port, "GET", "/sources")
                self.assertEqual(status, 200)
                source_ids = {source["id"] for source in sources["source_map"]["sources"]}
                self.assertIn("capability-context-index", source_ids)

                status, created = request(port, "POST", "/apps", {"app_id": "qa-novel", "name": "QA Novel"})
                self.assertEqual(status, 201)
                self.assertEqual(created["result"]["app"]["app_id"], "qa-novel")

                complete_foundation(root, "qa-novel")
                fill(
                    root / "apps" / "qa-novel" / "lifecycle" / "01-intent" / "artifacts" / "intent.md",
                    "Intent",
                )
                status, blocked = request(port, "POST", "/apps/qa-novel/approve-stage", {"stage": "intent"})
                self.assertEqual(status, 409)
                self.assertFalse(blocked["approved"])
                self.assertIn("transcript capture: current-stage conversation turn", blocked["gate"]["missing"])

                status, form = request(port, "GET", "/apps/qa-novel/conversation/form")
                self.assertEqual(status, 200)
                self.assertEqual(form["form"]["schema"], runtime.CONVERSATION_CAPTURE_FORM_SCHEMA)

                status, turn = request(
                    port,
                    "POST",
                    "/apps/qa-novel/conversation",
                    {
                        "stage": "intent",
                        "owner_message": "Create a tiny visual novel app.",
                        "agent_reply": "I understand the app intent and recorded the artifact for review.",
                        "agent_rationale": {
                            "summary": "Intent is sufficiently captured for owner review.",
                            "gate_questions": ["Is the app goal clear?"],
                            "missing_information": [],
                            "decision_basis": ["owner named a visual novel product"],
                        },
                        "state_transition": {
                            "from_stage": "intent",
                            "from_state": "collecting",
                            "to_stage": "intent",
                            "to_state": "ready_for_review",
                        },
                        "next_action": "Owner approves the intent stage.",
                    },
                )
                self.assertEqual(status, 201)
                self.assertEqual(turn["conversation_turn"]["stage"], "intent")

                status, transcript = request(port, "GET", "/transcript?app_id=qa-novel")
                self.assertEqual(status, 200)
                self.assertEqual(transcript["turn_count"], 1)

                status, approved = request(port, "POST", "/apps/qa-novel/approve-stage", {"stage": "intent"})
                self.assertEqual(status, 200)
                self.assertTrue(approved["approved"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_bearer_auth_policy_rejects_unauthorized_requests_and_reports_transport(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            state = weave_runtime_http.RuntimeState(
                root=root,
                command_ledger=root / "command-bus.jsonl",
                conversation_ledger=root / "conversation.jsonl",
                events_ledger=root / "events.jsonl",
                lane_claims_ledger=root / "project-lane-claims.json",
                bind_host=LOOPBACK_HOST,
                auth_policy=weave_runtime_http.AUTH_POLICY_LOOPBACK_BEARER,
                auth_token="secret-test-token",
            )
            state.setup()
            server = weave_runtime_http.RuntimeHTTPServer((LOOPBACK_HOST, 0), weave_runtime_http.RuntimeHandler)
            server.runtime_state = state
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                status, unauthorized = request(port, "POST", "/apps", {"app_id": "blocked", "name": "Blocked"})
                self.assertEqual(status, 401)
                self.assertEqual(unauthorized["error"], "unauthorized")

                headers = {"Authorization": "Bearer secret-test-token"}
                status, health = request(port, "GET", "/health", headers=headers)
                self.assertEqual(status, 200)
                self.assertEqual(health["transport"]["bind_host"], LOOPBACK_HOST)
                self.assertEqual(health["transport"]["auth_policy"], weave_runtime_http.AUTH_POLICY_LOOPBACK_BEARER)
                self.assertTrue(health["transport"]["auth_required"])

                status, created = request(port, "POST", "/apps", {"app_id": "allowed", "name": "Allowed"}, headers=headers)
                self.assertEqual(status, 201)
                self.assertEqual(created["result"]["app"]["app_id"], "allowed")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


    def test_malformed_post_returns_json_400(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            server, thread = self.run_server(root)
            port = int(server.server_address[1])
            try:
                status, payload = raw_request(port, "POST", "/apps", b"{not-json")
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"], "invalid_json")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
