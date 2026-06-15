from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import weave_runtime_slice as runtime  # noqa: E402


def fill(path: Path, title: str) -> None:
    path.write_text(
        f"# {title}\n\nStatus: complete\n\nRequired facts are recorded for this local test.\n",
        encoding="utf-8",
    )


def complete_foundation(root: Path, app_id: str) -> None:
    fill(root / "artifacts" / "general" / "soul.md", "Hermes Soul")
    fill(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile")
    fill(root / "apps" / app_id / "context" / "app-context.md", "App Context")
    fill(root / "apps" / app_id / "inventory" / "app-inventory.md", "App Inventory")
    fill(root / "apps" / app_id / "contract" / "gestaltian-contract.md", "Gestaltian Contract")


def write_stage_artifact(root: Path, app_id: str, stage_id: str, title: str | None = None) -> Path:
    stage = runtime.stage_by_id(stage_id)
    path = root / "apps" / app_id / "lifecycle" / stage.directory / "artifacts" / f"{stage_id}.md"
    fill(path, title or stage_id.title())
    return path


def record_stage_turn(root: Path, app_id: str, stage_id: str, artifact_path: Path | None = None) -> dict:
    refs = [{"path": runtime.relative(artifact_path, root), "action": "created"}] if artifact_path else []
    turn = runtime.new_conversation_turn(
        app_id,
        stage_id,
        f"Owner discussed {stage_id} stage.",
        f"Hermes recorded {stage_id} stage evidence for review.",
        agent_rationale={
            "summary": f"{stage_id} evidence is ready for owner review.",
            "gate_questions": ["Is stage evidence present?", "Is owner review required?"],
            "missing_information": [],
            "decision_basis": ["stage artifact present" if artifact_path else "stage conversation recorded"],
            "chain_of_thought_captured": False,
        },
        artifact_refs=refs,
        state_transition={
            "from_stage": stage_id,
            "from_state": "collecting",
            "to_stage": stage_id,
            "to_state": "ready_for_review",
        },
        next_action=f"Owner reviews {stage_id} and may approve the stage.",
    )
    return runtime.append_conversation_turn(root, app_id, turn)


def valid_stage_review(stage_id: str, artifact_path: str, *, reviewer: str = "test-evaluator") -> dict:
    contract, _contract_path = runtime.load_stage_eval_contract(stage_id)
    return {
        "schema": "weave.eval-review/v0.1",
        "stage": stage_id,
        "reviewer": reviewer,
        "artifact": artifact_path,
        "scores": {
            str(dim.get("id", "unnamed_dimension")): {
                "score": float(dim.get("max_score", 4)),
                "evidence": [artifact_path],
                "notes": "Local regression fixture cites the stage proof artifact.",
            }
            for dim in contract.get("rubric", [])
            if isinstance(dim, dict)
        },
        "hard_gates": {
            str(gate.get("id", "unnamed_gate")): {
                "passed": True,
                "evidence": [artifact_path],
                "notes": "Local regression fixture resolves the manual gate with proof artifact evidence.",
            }
            for gate in contract.get("hard_gates", [])
            if isinstance(gate, dict) and str(gate.get("kind", "manual")) in {"manual", "command"}
        },
        "overall_notes": "All evidence is local deterministic fixture data.",
    }


def complete_stage_evaluation(root: Path, app_id: str, stage_id: str, artifact_path: Path) -> dict:
    artifact_ref = runtime.relative(artifact_path, root)
    return runtime.complete_evaluation_from_review(root, app_id, stage_id, valid_stage_review(stage_id, artifact_ref))


class WeaveRuntimeSliceTests(unittest.TestCase):
    def test_setup_creates_root_registry_templates_and_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            old_umask = os.umask(0o022)
            try:
                result = runtime.setup_weave_root(root)
            finally:
                os.umask(old_umask)

            self.assertEqual(result["schema"], runtime.ROOT_SCHEMA)
            self.assertTrue((root / "apps" / "registry.json").exists())
            self.assertTrue((root / "artifacts" / "general" / "soul.md").exists())
            self.assertTrue((root / "artifacts" / "general" / "owner-profile.md").exists())
            self.assertTrue((root / "ledger" / "events.jsonl").exists())
            token_path = root / "runtime" / "tokens" / "local-api-token"
            self.assertTrue(token_path.exists())
            self.assertEqual(oct(token_path.stat().st_mode & 0o777), "0o600")
            self.assertEqual(oct(token_path.parent.stat().st_mode & 0o777), "0o700")
            self.assertTrue((root / "runtime" / "profiles" / "autonomy-policy.json").exists())
            self.assertTrue((root / "runtime" / "profiles" / "agent-profile.json").exists())
            self.assertTrue((root / "runtime" / "source-map.json").exists())
            self.assertEqual(result["autonomy"]["mode"], "yolo")
            self.assertEqual(result["agent_profile"]["prompt_pack"], "hermes-gestalt-runtime-pack")
            self.assertEqual(result["runtime_home_schema"], runtime.RUNTIME_HOME_SCHEMA)
            self.assertEqual(result["source_map_summary"]["canonical_source_id"], "weave-root")
            self.assertTrue(result["autonomy"]["llm_must_request_owner_authorization_for_hard_gates"])
            self.assertEqual(runtime.load_registry(root)["apps"], [])

    def test_agent_profile_records_model_and_reasoning_from_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            with mock.patch.dict(
                "os.environ",
                {
                    "WEAVE_HERMES_MODEL": "gpt-5.5",
                    "WEAVE_HERMES_REASONING_EFFORT": "xhigh",
                    "WEAVE_HERMES_PROVIDER_ADAPTER": "codex",
                },
            ):
                result = runtime.setup_weave_root(root)

            profile = result["agent_profile"]
            self.assertEqual(profile["model"], "gpt-5.5")
            self.assertEqual(profile["reasoning_effort"], "xhigh")
            self.assertEqual(profile["provider_adapter"], "codex")
            status = runtime.dispatch_telegram_command(root, "/status")
            self.assertIn("model=gpt-5.5; reasoning=xhigh; adapter=codex", status["text"])

    def test_source_map_records_active_and_sensitive_sources_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.setup_weave_root(root)

            source_map = runtime.load_source_map(root)

            self.assertEqual(source_map["schema"], runtime.SOURCE_MAP_SCHEMA)
            self.assertEqual(source_map["canonical_source_id"], "weave-root")
            source_ids = {source["id"] for source in source_map["sources"]}
            self.assertIn("runtime-home", source_ids)
            runtime_home = [source for source in source_map["sources"] if source["id"] == "runtime-home"]
            self.assertEqual(runtime_home[0]["layout_schema"], runtime.RUNTIME_HOME_SCHEMA)
            self.assertIn("app-registry", source_ids)
            self.assertIn("capability-context-index", source_ids)
            context_sources = [source for source in source_map["sources"] if source["id"] == "capability-context-index"]
            self.assertEqual(context_sources[0]["schema_ref"], runtime.CONTEXT_INDEX_SCHEMA)
            self.assertEqual(context_sources[0]["recommended_repository"], "its-DeFine/weave-context")
            self.assertIn("existing_api", context_sources[0]["application_paths"])
            self.assertIn("gateway_capability", context_sources[0]["application_paths"])
            self.assertIn("new_orchestrator_capability", context_sources[0]["application_paths"])
            token_sources = [source for source in source_map["sources"] if source["id"] == "local-api-token"]
            self.assertEqual(token_sources[0]["kind"], "secret_ref")
            self.assertTrue(token_sources[0]["sensitive"])
            self.assertFalse(token_sources[0]["secret_value_printed"])

    def test_create_app_registers_context_lifecycle_and_blocks_foundation_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.setup_weave_root(root)
            result = runtime.create_app(root, "Demo App", "Demo App")
            app_root = root / "apps" / "demo-app"

            self.assertEqual(result["app"]["app_id"], "demo-app")
            self.assertTrue((app_root / "context" / "app-context.md").exists())
            self.assertTrue((app_root / "inventory" / "app-inventory.md").exists())
            self.assertTrue((app_root / "contract" / "gestaltian-contract.md").exists())
            self.assertTrue((app_root / "lifecycle" / "01-intent" / "artifacts").is_dir())
            self.assertTrue((app_root / "lifecycle" / "02-research" / "artifacts").is_dir())
            self.assertTrue((app_root / "repo" / "primary").is_dir())
            self.assertTrue((app_root / "ledger" / "conversation-turns.jsonl").exists())
            self.assertTrue((app_root / "ledger" / "conversation-events.jsonl").exists())
            self.assertTrue((app_root / "collaboration" / "peers.json").exists())
            self.assertTrue((app_root / "collaboration" / "context-capsules.json").exists())
            self.assertTrue((app_root / "collaboration" / "discussions.json").exists())
            self.assertTrue((app_root / "collaboration" / "attention-requests.json").exists())
            self.assertTrue((app_root / "collaboration" / "ledger.jsonl").exists())
            self.assertEqual(result["app"]["conversation_turns_path"], "ledger/conversation-turns.jsonl")
            self.assertEqual(result["app"]["conversation_events_path"], "ledger/conversation-events.jsonl")
            self.assertEqual(result["app"]["collaboration_path"], "collaboration")
            self.assertEqual(result["app"]["collaboration_ledger_path"], "collaboration/ledger.jsonl")
            self.assertIn("conversation-turn-ledger", result["app"]["capabilities"])
            self.assertIn("conversation-event-ledger", result["app"]["capabilities"])
            self.assertIn("local-a2a-collaboration", result["app"]["capabilities"])
            registry = runtime.load_registry(root)
            self.assertEqual(registry["apps"][0]["app_id"], "demo-app")
            self.assertEqual(registry["apps"][0]["app_type"], "product")
            gate = runtime.foundation_gate(root, "demo-app")
            self.assertFalse(gate["passed"])
            self.assertIn("soul.md", gate["incomplete"])
            self.assertIn("context/app-context.md", gate["incomplete"])

    def test_a2a_peer_capsule_discussion_and_attention_request_are_listable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")

            peer = runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-alpha",
            )
            capsule = runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary for local peer review.",
                ["peer-alpha"],
                redacted_fields=["api_key"],
                source_refs=[{"path": "context/app-context.md", "kind": "local_context"}],
                capsule_id="capsule-intent",
            )
            discussion = runtime.open_discussion(
                root,
                "demo",
                "Review intent",
                peer_id="peer-alpha",
                capsule_id="capsule-intent",
                discussion_id="discussion-intent",
            )
            attention = runtime.create_attention_request(
                root,
                "demo",
                "discussion-intent",
                "Review requested",
                status="pending",
                attention_request_id="attention-intent",
            )

            self.assertEqual(peer["state"], "paired")
            self.assertFalse(peer["live_xmtp"])
            self.assertEqual(runtime.list_a2a_peers(root, "demo")[0]["peer_id"], "peer-alpha")
            self.assertEqual(runtime.list_context_capsules(root, "demo")[0]["capsule_id"], capsule["capsule_id"])
            self.assertEqual(runtime.list_discussions(root, "demo")[0]["discussion_id"], discussion["discussion_id"])
            self.assertEqual(
                runtime.list_attention_requests(root, "demo")[0]["attention_request_id"],
                attention["attention_request_id"],
            )
            events = runtime.read_a2a_ledger_events(root, "demo")
            self.assertEqual(
                [event["type"] for event in events],
                [
                    "a2a.peer.registered",
                    "a2a.context_capsule.created",
                    "a2a.discussion.opened",
                    "a2a.attention_request.created",
                ],
            )
            summary = runtime.a2a_disclosure_policy_summary(root, "demo")
            self.assertEqual(summary["schema"], runtime.A2A_DISCLOSURE_POLICY_SUMMARY_SCHEMA)
            self.assertTrue(summary["policy"]["local_only"])
            self.assertFalse(summary["policy"]["live_xmtp"])
            self.assertEqual(
                summary["policy"]["paired_active_peer_required_for"],
                ["context_capsule", "discussion", "attention_request", "work_packet"],
            )
            self.assertEqual(summary["peers"][0]["permitted_context_capsule_ids"], ["capsule-intent"])

    def test_attention_request_peer_must_match_discussion_peer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            for peer_id in ("peer-alpha", "peer-beta"):
                runtime.register_a2a_peer(
                    root,
                    "demo",
                    peer_id.replace("-", " ").title(),
                    f"local://{peer_id}",
                    "trusted",
                    ["discussion", "attention_request"],
                    peer_id=peer_id,
                )
            runtime.open_discussion(
                root,
                "demo",
                "Peer alpha review",
                peer_id="peer-alpha",
                discussion_id="discussion-alpha",
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "peer must match discussion peer"):
                runtime.create_attention_request(
                    root,
                    "demo",
                    "discussion-alpha",
                    "Wrong peer attention",
                    peer_id="peer-beta",
                )

    def register_work_packet_peers(self, root: Path) -> None:
        packet_types = sorted(runtime.A2A_WORK_PACKET_TYPES)
        runtime.register_a2a_peer(
            root,
            "demo",
            "WEAVE Runtime",
            "local://weave-runtime",
            "trusted-local-runtime",
            packet_types,
            peer_id="weave-runtime",
        )
        runtime.register_a2a_peer(
            root,
            "demo",
            "Partner Agent",
            "local://partner-agent",
            "trusted-test-peer",
            packet_types,
            peer_id="partner-agent",
        )

    def test_a2a_creation_helpers_reject_non_list_optional_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule"],
                peer_id="peer-alpha",
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "redacted_fields must be a list"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved app intent summary.",
                    ["peer-alpha"],
                    redacted_fields="api_key",  # type: ignore[arg-type]
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "source_refs must be a list"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved app intent summary.",
                    ["peer-alpha"],
                    source_refs={"path": "context/app-context.md"},  # type: ignore[arg-type]
                )
            self.assertEqual(runtime.list_context_capsules(root, "demo"), [])

            self.register_work_packet_peers(root)
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "A2A work packet refs must be a list"):
                runtime.new_a2a_work_packet(
                    root,
                    "demo",
                    "task_request",
                    "partner-agent",
                    "weave-runtime",
                    {"requested_action": "record_evidence_summary", "summary": "Safe local task."},
                    refs={"path": "lifecycle/01-intent/artifacts/intent.md"},  # type: ignore[arg-type]
                    packet_id="packet-bad-refs",
                    idempotency_key="bad-refs",
                )

    def test_a2a_work_packet_requires_approval_executes_and_returns_evidence_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            self.register_work_packet_peers(root)

            packet = runtime.new_a2a_work_packet(
                root,
                "demo",
                "task_request",
                "partner-agent",
                "weave-runtime",
                {
                    "requested_action": "record_evidence_summary",
                    "task": "Validate local A2A packet flow.",
                    "summary": "Local A2A task completed with evidence report.",
                },
                refs=[{"path": "lifecycle/01-intent/artifacts/intent.md", "kind": "stage_artifact"}],
                packet_id="packet-task-001",
                idempotency_key="task-001",
            )
            received = runtime.receive_a2a_work_packet(root, "demo", packet)

            self.assertTrue(received["received"])
            self.assertEqual(len(runtime.load_a2a_work_packet_queue(root, "demo", "inbox")), 1)
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "requires owner approval"):
                runtime.execute_a2a_work_packet(root, "demo", "packet-task-001")

            approved = runtime.approve_a2a_work_packet(root, "demo", "packet-task-001", note="owner approved local proof")
            self.assertEqual(approved["approval_status"], "approved")
            executed = runtime.execute_a2a_work_packet(root, "demo", "packet-task-001")

            self.assertTrue(executed["executed"])
            inbox = runtime.load_a2a_work_packet_queue(root, "demo", "inbox")
            outbox = runtime.load_a2a_work_packet_queue(root, "demo", "outbox")
            evidence = runtime.list_a2a_work_packet_evidence(root, "demo")
            self.assertEqual(inbox[0]["execution_status"], "completed")
            self.assertEqual(inbox[0]["state"], "executed")
            self.assertEqual(outbox[0]["packet_type"], "evidence_report")
            self.assertEqual(outbox[0]["source_peer_id"], "weave-runtime")
            self.assertEqual(outbox[0]["target_peer_id"], "partner-agent")
            self.assertEqual(outbox[0]["state"], "send_ready")
            self.assertEqual(evidence[0]["packet_id"], "packet-task-001")
            self.assertEqual(evidence[0]["result_packet_id"], outbox[0]["packet_id"])
            self.assertEqual(evidence[0]["status"], "completed")
            event_types = [event["type"] for event in runtime.read_a2a_ledger_events(root, "demo")]
            self.assertIn("a2a.work_packet.received", event_types)
            self.assertIn("a2a.work_packet.approved", event_types)
            self.assertIn("a2a.work_packet.evidence_recorded", event_types)
            self.assertIn("a2a.work_packet.outbox_enqueued", event_types)
            self.assertIn("a2a.work_packet.executed", event_types)

    def test_received_a2a_work_packet_cannot_arrive_preapproved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            self.register_work_packet_peers(root)
            packet = runtime.new_a2a_work_packet(
                root,
                "demo",
                "task_request",
                "partner-agent",
                "weave-runtime",
                {"requested_action": "record_evidence_summary", "summary": "Forged approval must not execute."},
                packet_id="packet-forged-approved",
                idempotency_key="forged-approved",
            )
            packet["approval_status"] = "approved"
            packet["state"] = "approved"

            received = runtime.receive_a2a_work_packet(root, "demo", packet)
            inbox = runtime.load_a2a_work_packet_queue(root, "demo", "inbox")

            self.assertTrue(received["received"])
            self.assertTrue(inbox[0]["approval_required"])
            self.assertEqual(inbox[0]["approval_status"], "required")
            self.assertEqual(inbox[0]["execution_status"], "not_started")
            self.assertEqual(inbox[0]["state"], "pending_approval")
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "requires owner approval"):
                runtime.execute_a2a_work_packet(root, "demo", "packet-forged-approved")
            event_types = [event["type"] for event in runtime.read_a2a_ledger_events(root, "demo")]
            self.assertNotIn("a2a.work_packet.approved", event_types)
            self.assertEqual(runtime.list_a2a_work_packet_evidence(root, "demo"), [])

    def test_received_a2a_work_packet_must_target_local_runtime_peer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            self.register_work_packet_peers(root)
            packet = runtime.new_a2a_work_packet(
                root,
                "demo",
                "task_request",
                "weave-runtime",
                "partner-agent",
                {"requested_action": "record_evidence_summary", "summary": "Outbound packet must not enter local inbox."},
                packet_id="packet-wrong-local-target",
                idempotency_key="wrong-local-target",
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "target must be local runtime peer"):
                runtime.receive_a2a_work_packet(root, "demo", packet)

    def test_a2a_work_packet_execution_preflights_evidence_report_before_persisting_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            packet_types = sorted(runtime.A2A_WORK_PACKET_TYPES)
            runtime.register_a2a_peer(
                root,
                "demo",
                "WEAVE Runtime",
                "local://weave-runtime",
                "trusted-local-runtime",
                packet_types,
                peer_id="weave-runtime",
            )
            runtime.register_a2a_peer(
                root,
                "demo",
                "Partner Agent",
                "local://partner-agent",
                "trusted-test-peer",
                [packet_type for packet_type in packet_types if packet_type != "evidence_report"],
                peer_id="partner-agent",
            )
            packet = runtime.new_a2a_work_packet(
                root,
                "demo",
                "task_request",
                "partner-agent",
                "weave-runtime",
                {"requested_action": "record_evidence_summary", "summary": "Evidence report permission is required."},
                packet_id="packet-no-evidence-report-permission",
                idempotency_key="no-evidence-report-permission",
            )
            runtime.receive_a2a_work_packet(root, "demo", packet)
            runtime.approve_a2a_work_packet(root, "demo", "packet-no-evidence-report-permission")

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "does not allow packet type: evidence_report"):
                runtime.execute_a2a_work_packet(root, "demo", "packet-no-evidence-report-permission")

            inbox = runtime.load_a2a_work_packet_queue(root, "demo", "inbox")
            self.assertEqual(inbox[0]["execution_status"], "not_started")
            self.assertEqual(inbox[0]["state"], "approved")
            self.assertEqual(runtime.list_a2a_work_packet_evidence(root, "demo"), [])
            self.assertEqual(runtime.load_a2a_work_packet_queue(root, "demo", "outbox"), [])

    def test_a2a_work_packet_replay_does_not_execute_twice(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            self.register_work_packet_peers(root)
            packet = runtime.new_a2a_work_packet(
                root,
                "demo",
                "task_request",
                "partner-agent",
                "weave-runtime",
                {
                    "requested_action": "record_evidence_summary",
                    "summary": "Replay protected work packet completed once.",
                },
                packet_id="packet-task-002",
                idempotency_key="task-002",
            )

            runtime.receive_a2a_work_packet(root, "demo", packet)
            runtime.approve_a2a_work_packet(root, "demo", "packet-task-002")
            first = runtime.execute_a2a_work_packet(root, "demo", "packet-task-002")
            duplicate_receive = runtime.receive_a2a_work_packet(root, "demo", packet)
            second = runtime.execute_a2a_work_packet(root, "demo", "packet-task-002")

            self.assertTrue(first["executed"])
            self.assertTrue(duplicate_receive["duplicate"])
            self.assertFalse(second["executed"])
            self.assertTrue(second["duplicate"])
            self.assertEqual(len(runtime.load_a2a_work_packet_queue(root, "demo", "inbox")), 1)
            self.assertEqual(len(runtime.load_a2a_work_packet_queue(root, "demo", "outbox")), 1)
            self.assertEqual(len(runtime.list_a2a_work_packet_evidence(root, "demo")), 1)
            event_types = [event["type"] for event in runtime.read_a2a_ledger_events(root, "demo")]
            self.assertIn("a2a.work_packet.duplicate", event_types)

    def test_a2a_work_packets_reject_live_xmtp_claims_and_secret_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            self.register_work_packet_peers(root)
            packet = runtime.new_a2a_work_packet(
                root,
                "demo",
                "task_request",
                "partner-agent",
                "weave-runtime",
                {"requested_action": "record_evidence_summary", "summary": "Safe local task."},
                packet_id="packet-task-003",
                idempotency_key="task-003",
            )
            packet["live_xmtp"] = True
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "must not claim live XMTP"):
                runtime.validate_a2a_work_packet(packet)

            packet = runtime.new_a2a_work_packet(
                root,
                "demo",
                "task_request",
                "partner-agent",
                "weave-runtime",
                {"requested_action": "record_evidence_summary", "summary": "Safe local task."},
                packet_id="packet-task-003b",
                idempotency_key="task-003b",
            )
            packet["source_peer_id"] = "Partner Agent"
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "source_peer_id is not normalized"):
                runtime.validate_a2a_work_packet(packet)

            secret_like = "sk_" + "a" * 16
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "secret-looking"):
                runtime.new_a2a_work_packet(
                    root,
                    "demo",
                    "task_request",
                    "partner-agent",
                    "weave-runtime",
                    {"requested_action": "record_evidence_summary", "summary": "Do not record " + secret_like},
                    packet_id="packet-task-004",
                    idempotency_key="task-004",
                )

    def test_a2a_disclosure_summary_rejects_tampered_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-alpha",
            )
            runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                capsule_id="capsule-intent",
            )
            runtime.open_discussion(
                root,
                "demo",
                "Capsule review",
                peer_id="peer-alpha",
                capsule_id="capsule-intent",
                discussion_id="discussion-intent",
            )
            runtime.create_attention_request(
                root,
                "demo",
                "discussion-intent",
                "Review requested",
                attention_request_id="attention-intent",
            )

            peer_path = root / "apps" / "demo" / "collaboration" / "peers.json"
            peer_data = json.loads(peer_path.read_text(encoding="utf-8"))
            peer_data["peers"][0]["state"] = "revoked"
            peer_data["peers"][0]["paired"] = False
            peer_data["peers"][0]["revoked"] = True
            peer_path.write_text(json.dumps(peer_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "requires paired active peer"):
                runtime.a2a_disclosure_policy_summary(root, "demo")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-alpha",
            )
            runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                capsule_id="capsule-intent",
            )
            runtime.open_discussion(
                root,
                "demo",
                "Capsule review",
                peer_id="peer-alpha",
                capsule_id="capsule-intent",
                discussion_id="discussion-intent",
            )

            discussion_path = root / "apps" / "demo" / "collaboration" / "discussions.json"
            discussion_data = json.loads(discussion_path.read_text(encoding="utf-8"))
            discussion_data["discussions"][0]["capsule_id"] = "capsule-missing"
            discussion_path.write_text(json.dumps(discussion_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "missing context capsule"):
                runtime.a2a_disclosure_policy_summary(root, "demo")

    def test_a2a_disclosure_summary_rejects_missing_and_unpermitted_relationships(self) -> None:
        def build_graph(root: Path) -> None:
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-alpha",
            )
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Beta",
                "local://peer-beta",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-beta",
            )
            runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                capsule_id="capsule-intent",
            )
            runtime.open_discussion(
                root,
                "demo",
                "Capsule review",
                peer_id="peer-alpha",
                capsule_id="capsule-intent",
                discussion_id="discussion-intent",
            )
            runtime.create_attention_request(
                root,
                "demo",
                "discussion-intent",
                "Review requested",
                peer_id="peer-alpha",
                attention_request_id="attention-intent",
            )

        def rewrite_record(root: Path, filename: str, key: str, changes: dict[str, object]) -> None:
            path = root / "apps" / "demo" / "collaboration" / filename
            data = json.loads(path.read_text(encoding="utf-8"))
            data[key][0].update(changes)
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        cases = [
            (
                "missing_peer",
                "context-capsules.json",
                "context_capsules",
                {"permitted_peer_ids": ["peer-missing"]},
                "missing A2A peer",
            ),
            (
                "missing_discussion",
                "attention-requests.json",
                "attention_requests",
                {"discussion_id": "discussion-missing"},
                "missing A2A discussion",
            ),
            (
                "discussion_peer_not_permitted",
                "discussions.json",
                "discussions",
                {"peer_id": "peer-beta"},
                "peer is not permitted on capsule",
            ),
            (
                "attention_peer_not_permitted",
                "attention-requests.json",
                "attention_requests",
                {"peer_id": "peer-beta"},
                "peer must match discussion peer",
            ),
        ]
        for name, filename, key, changes, error_pattern in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir) / "weave-root"
                    build_graph(root)
                    rewrite_record(root, filename, key, changes)

                    with self.assertRaisesRegex(runtime.RuntimeSliceError, error_pattern):
                        runtime.a2a_disclosure_policy_summary(root, "demo")

    def test_a2a_peer_addresses_must_be_local_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")

            loopback_address = "ws://" + ".".join(["127", "0", "0", "1"]) + ":9000"
            private_host_address = ".".join(["192", "168", "1", "10"]) + ":9000"
            for address in [
                "https://peer.example.test",
                "xmtp://peer-alpha",
                loopback_address,
                private_host_address,
            ]:
                with self.subTest(address=address):
                    with self.assertRaisesRegex(runtime.RuntimeSliceError, "address must use local://"):
                        runtime.register_a2a_peer(
                            root,
                            "demo",
                            f"Peer {address}",
                            address,
                            "trusted",
                            ["context_capsule"],
                        )

            for address in [
                "local://" + ".".join(["127", "0", "0", "1"]),
                "local://" + "local" + "host",
                "local://" + ".".join(["192", "168", "1", "10"]),
                "local://peer.internal",
                "local://peer.local",
            ]:
                with self.subTest(address=address):
                    with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                        runtime.register_a2a_peer(
                            root,
                            "demo",
                            f"Peer {address}",
                            address,
                            "trusted",
                            ["context_capsule"],
                        )
                    self.assertEqual(runtime.list_a2a_peers(root, "demo"), [])

            self.assertEqual(runtime.list_a2a_peers(root, "demo"), [])

    def test_a2a_unpaired_or_revoked_peers_cannot_receive_capsules_or_attention(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-alpha",
            )
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Beta",
                "local://peer-beta",
                "observer",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-beta",
                state="unpaired",
            )
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Gamma",
                "local://peer-gamma",
                "blocked",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-gamma",
                revoked=True,
            )
            runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                capsule_id="capsule-intent",
            )
            runtime.open_discussion(
                root,
                "demo",
                "Capsule review",
                capsule_id="capsule-intent",
                discussion_id="discussion-intent",
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "requires paired active peer"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Blocked Packet",
                    "This should not be shared with an unpaired peer.",
                    ["peer-beta"],
                    capsule_id="capsule-blocked",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "requires paired active peer"):
                runtime.create_attention_request(
                    root,
                    "demo",
                    "discussion-intent",
                    "Review requested",
                    peer_id="peer-gamma",
                    attention_request_id="attention-blocked",
                )

    def test_a2a_capsule_discussions_require_peer_discussion_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule"],
                peer_id="peer-alpha",
            )
            runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                capsule_id="capsule-intent",
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "does not allow packet type: discussion"):
                runtime.open_discussion(
                    root,
                    "demo",
                    "Capsule review",
                    capsule_id="capsule-intent",
                    discussion_id="discussion-intent",
                )

    def test_a2a_context_capsules_reject_secret_looking_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule"],
                peer_id="peer-alpha",
            )

            secret_like = "sk_" + "a" * 16
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "secret-looking"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Do not record " + secret_like + " in a capsule.",
                    ["peer-alpha"],
                    capsule_id="capsule-secret",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "secret-looking"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Safe summary.",
                    ["peer-alpha"],
                    source_refs=[{"url": "https://example.test/callback?" + "token=" + "a" * 20}],
                    capsule_id="capsule-secret-ref",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "secret-looking"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Safe summary.",
                    ["peer-alpha"],
                    redacted_fields=[secret_like],
                    capsule_id="capsule-secret-redacted-field",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "secret-looking"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Safe summary.",
                    ["peer-alpha"],
                    capsule_id=secret_like,
                )
            dash_delimited_secret = "-".join(["a" * 8, "b" * 8, "c" * 8])
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "secret-looking"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Do not record " + dash_delimited_secret + " in a capsule.",
                    ["peer-alpha"],
                    capsule_id="capsule-dash-token",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "secret-looking"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Safe summary.",
                    ["peer-alpha"],
                    source_refs=[{secret_like: "redacted"}],
                    capsule_id="capsule-secret-key-ref",
                )

    def test_a2a_context_capsules_reject_empty_peers_and_private_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule"],
                peer_id="peer-alpha",
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "at least one permitted peer"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved app intent summary.",
                    [],
                    capsule_id="capsule-empty-peers",
                )
            absolute_path = "/" + "var/tmp/proof.json"
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved app intent summary.",
                    ["peer-alpha"],
                    source_refs=[{"path": absolute_path, "kind": "local_context"}],
                    capsule_id="capsule-absolute-ref",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved app intent summary.",
                    ["peer-alpha"],
                    source_refs=[{"locator": absolute_path, "kind": "local_context"}],
                    capsule_id="capsule-absolute-locator-ref",
                )
            private_address = ".".join(["192", "168", "1", "15"])
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved app intent summary.",
                    ["peer-alpha"],
                    source_refs=[{"url": "http://" + private_address + "/artifact.json"}],
                    capsule_id="capsule-private-url-ref",
                )
            for name, ref in [
                ("file_uri", {"url": "file://" + "/tmp/proof.json"}),
                ("unqualified_host", {"url": "https://builder/artifact.json"}),
                ("ipv6_loopback", {"url": "http://[::1]/artifact.json"}),
            ]:
                with self.subTest(name=name):
                    with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                        runtime.create_context_capsule(
                            root,
                            "demo",
                            "Intent Packet",
                            "Owner-approved app intent summary.",
                            ["peer-alpha"],
                            source_refs=[ref],
                            capsule_id=f"capsule-{name}-ref",
                        )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved artifact at http://" + private_address + "/artifact.json",
                    ["peer-alpha"],
                    capsule_id="capsule-private-summary",
                )

    def test_a2a_private_locator_rejections_do_not_persist_partial_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            private_path = "/" + "var/tmp/private-proof.json"

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.register_a2a_peer(
                    root,
                    "demo",
                    "Peer " + private_path,
                    "local://peer-private-alias",
                    "trusted",
                    ["context_capsule"],
                    peer_id="peer-private-alias",
                )
            self.assertEqual(runtime.list_a2a_peers(root, "demo"), [])
            self.assertEqual(runtime.read_a2a_ledger_events(root, "demo"), [])

            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-alpha",
            )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet",
                    "Owner-approved app intent summary.",
                    ["peer-alpha"],
                    redacted_fields=[private_path],
                    capsule_id="capsule-private-redaction",
                )
            self.assertEqual(runtime.list_context_capsules(root, "demo"), [])
            self.assertEqual(len(runtime.read_a2a_ledger_events(root, "demo")), 1)

            runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                capsule_id="capsule-intent",
            )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.open_discussion(
                    root,
                    "demo",
                    "Discuss " + private_path,
                    peer_id="peer-alpha",
                    capsule_id="capsule-intent",
                    discussion_id="discussion-private-title",
                )
            self.assertEqual(runtime.list_discussions(root, "demo"), [])
            self.assertEqual(len(runtime.read_a2a_ledger_events(root, "demo")), 2)

            runtime.open_discussion(
                root,
                "demo",
                "Capsule review",
                peer_id="peer-alpha",
                capsule_id="capsule-intent",
                discussion_id="discussion-intent",
            )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.create_attention_request(
                    root,
                    "demo",
                    "discussion-intent",
                    "Review requested",
                    summary="See " + private_path,
                    attention_request_id="attention-private-summary",
                )
            self.assertEqual(runtime.list_attention_requests(root, "demo"), [])
            self.assertEqual(len(runtime.read_a2a_ledger_events(root, "demo")), 3)

    def test_a2a_ledger_rejects_private_locator_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            private_path = "/" + "var/tmp/private-proof.json"
            event = runtime.new_a2a_ledger_event(
                "a2a.context_capsule.created",
                "demo",
                "Created local A2A context capsule capsule-intent.",
                record_id="capsule-intent",
                payload={"context_capsule": {"source_refs": [{"locator": private_path}]}},
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.append_a2a_ledger_event(root, "demo", event)

    def test_a2a_generated_capsule_ids_include_redaction_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule"],
                peer_id="peer-alpha",
            )

            first = runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                redacted_fields=["api_key"],
                source_refs=[{"path": "context/app-context.md"}],
            )
            second = runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                redacted_fields=["session_token"],
                source_refs=[{"path": "context/app-context.md"}],
            )

            self.assertNotEqual(first["capsule_id"], second["capsule_id"])
            self.assertEqual(len(runtime.list_context_capsules(root, "demo")), 2)

    def test_a2a_duplicate_ids_do_not_double_create_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            runtime.register_a2a_peer(
                root,
                "demo",
                "Peer Alpha",
                "local://peer-alpha",
                "trusted",
                ["context_capsule", "discussion", "attention_request"],
                peer_id="peer-alpha",
            )

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "duplicate A2A peer id"):
                runtime.register_a2a_peer(
                    root,
                    "demo",
                    "Peer Alpha Again",
                    "local://peer-alpha-again",
                    "trusted",
                    ["context_capsule"],
                    peer_id="peer-alpha",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "duplicate A2A peer address"):
                runtime.register_a2a_peer(
                    root,
                    "demo",
                    "Peer Alpha Address Again",
                    "local://peer-alpha",
                    "trusted",
                    ["context_capsule"],
                    peer_id="peer-alpha-address-again",
                )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "at least one alphanumeric"):
                runtime.register_a2a_peer(
                    root,
                    "demo",
                    "Peer Punctuation",
                    "local://peer-punctuation",
                    "trusted",
                    ["context_capsule"],
                    peer_id="!!!",
                )

            runtime.create_context_capsule(
                root,
                "demo",
                "Intent Packet",
                "Owner-approved app intent summary.",
                ["peer-alpha"],
                capsule_id="capsule-intent",
            )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "duplicate A2A context capsule id"):
                runtime.create_context_capsule(
                    root,
                    "demo",
                    "Intent Packet Again",
                    "Owner-approved app intent summary again.",
                    ["peer-alpha"],
                    capsule_id="capsule-intent",
                )

            runtime.open_discussion(
                root,
                "demo",
                "Capsule review",
                peer_id="peer-alpha",
                capsule_id="capsule-intent",
                discussion_id="discussion-intent",
            )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "duplicate A2A discussion id"):
                runtime.open_discussion(
                    root,
                    "demo",
                    "Capsule review again",
                    peer_id="peer-alpha",
                    capsule_id="capsule-intent",
                    discussion_id="discussion-intent",
                )

            runtime.create_attention_request(
                root,
                "demo",
                "discussion-intent",
                "Review requested",
                attention_request_id="attention-intent",
            )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "duplicate A2A attention request id"):
                runtime.create_attention_request(
                    root,
                    "demo",
                    "discussion-intent",
                    "Review requested again",
                    attention_request_id="attention-intent",
                )

            self.assertEqual(len(runtime.list_a2a_peers(root, "demo")), 1)
            self.assertEqual(len(runtime.list_context_capsules(root, "demo")), 1)
            self.assertEqual(len(runtime.list_discussions(root, "demo")), 1)
            self.assertEqual(len(runtime.list_attention_requests(root, "demo")), 1)
            self.assertEqual(len(runtime.read_a2a_ledger_events(root, "demo")), 4)

    def test_foundation_gate_passes_after_required_context_is_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")

            gate = runtime.foundation_gate(root, "demo")

            self.assertTrue(gate["passed"])
            self.assertEqual(gate["missing"], [])
            self.assertEqual(gate["incomplete"], [])

    def test_setup_foundation_onboarding_generates_gateway_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"

            result = runtime.setup_foundation_onboarding(root, "Demo App", "Demo App")

            self.assertEqual(result["schema"], runtime.GATEWAY_CONTEXT_SCHEMA)
            self.assertEqual(result["app_id"], "demo-app")
            self.assertFalse(result["foundation_gate"]["passed"])
            gate_path = Path(result["foundation_gate_path"])
            self.assertTrue(gate_path.exists())
            gate = gate_path.read_text(encoding="utf-8")
            self.assertIn("soul.md", gate)
            agents = Path(result["agents_path"]).read_text(encoding="utf-8")
            self.assertIn("Unskippable Foundation Gate", agents)
            self.assertIn("Autonomy Mode", agents)
            self.assertIn("Autonomy mode: `yolo`", agents)
            self.assertIn("must ask the owner through the LLM conversation", agents)
            self.assertIn("Ask at most three blocking questions", agents)
            self.assertIn("elicitation loop", agents)
            self.assertIn("There is no dashboard", agents)
            self.assertIn("intent -> research -> selection -> plan", agents)
            self.assertIn("Communication channel: Telegram", agents)
            soul = Path(result["soul_path"]).read_text(encoding="utf-8")
            self.assertIn("WEAVE Gateway Soul Bootstrap", soul)
            context = Path(result["context_path"]).read_text(encoding="utf-8")
            self.assertIn('"required_before_app_work": true', context)
            self.assertIn('"dashboard_ui_enabled": false', context)
            self.assertIn('"agent_profile"', context)
            self.assertIn('"mode": "yolo"', context)

    def test_ledger_appends_valid_events_and_rejects_malformed_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            before = len(runtime.read_events(root, "demo"))
            event = runtime.new_event("validation.completed", "demo", "intent", "Checks passed.")

            runtime.append_event(root, "demo", event)

            self.assertEqual(len(runtime.read_events(root, "demo")), before + 1)
            live_event = runtime.new_event(
                "validation.completed",
                "demo",
                "intent",
                "Live Hermes checks passed.",
                created_by="live_hermes",
            )
            runtime.append_event(root, "demo", live_event)
            self.assertEqual(runtime.read_events(root, "demo")[-1]["created_by"], "live_hermes")
            fixture_event = runtime.new_event(
                "validation.completed",
                "demo",
                "intent",
                "Fixture should not be accepted as a live event creator.",
                created_by="scripted_fixture",
            )
            with self.assertRaisesRegex(runtime.RuntimeSliceError, "unsupported event creator"):
                runtime.append_event(root, "demo", fixture_event)
            with self.assertRaises(runtime.RuntimeSliceError):
                runtime.append_event(root, "demo", {"schema": runtime.EVENT_SCHEMA})

    def test_conversation_turn_records_raw_exchange_refs_and_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent", "Intent Packet")
            event = runtime.new_event(
                "artifact.created",
                "demo",
                "intent",
                "Intent artifact created from owner conversation.",
                artifact_refs=[{"path": runtime.relative(artifact_path, root), "action": "created"}],
            )
            runtime.append_event(root, "demo", event)
            turn = runtime.new_conversation_turn(
                "demo",
                "intent",
                {
                    "role": "owner",
                    "source": "qa_operator",
                    "text": "Make a short visual novel about a crow learning to ask for water.",
                },
                {
                    "role": "hermes",
                    "source": "live_hermes",
                    "model": "gpt-5.5",
                    "provider": "codex",
                    "session_id": "test-session",
                    "turn_kind": "stage_completion",
                    "text": "I captured the intent and created the first intent artifact for review.",
                },
                agent_rationale={
                    "summary": "Foundation documents were complete and the intent artifact now exists; owner review is the next gate.",
                    "gate_questions": ["Are foundation docs complete?", "Is the intent artifact present?"],
                    "missing_information": [],
                    "decision_basis": ["foundation gate passed", "intent artifact present"],
                    "chain_of_thought_captured": False,
                },
                gate_checks={
                    "foundation_gate_passed": True,
                    "stage_gate_passed": True,
                    "owner_approval_required": True,
                },
                artifact_refs=[{"path": runtime.relative(artifact_path, root), "action": "created"}],
                event_refs=[{"event_id": event["event_id"], "type": event["type"]}],
                state_transition={
                    "from_stage": "intent",
                    "from_state": "collecting",
                    "to_stage": "intent",
                    "to_state": "ready_for_review",
                    "initiated_by": "hermes",
                    "reason": "Intent artifact exists and foundation gate passed.",
                },
                next_action="Owner reviews the intent artifact, then may approve the intent stage.",
            )

            runtime.append_conversation_turn(root, "demo", turn)

            turns = runtime.read_conversation_turns(root, "demo")
            events = runtime.read_conversation_events(root, "demo")
            self.assertEqual(len(turns), 1)
            self.assertEqual(len(events), 8)
            self.assertEqual(turns[0]["operator_message"]["text"], turn["operator_message"]["text"])
            self.assertEqual(turns[0]["agent_reply"]["text"], turn["agent_reply"]["text"])
            self.assertEqual(events[0]["type"], "turn.operator_message")
            self.assertEqual(events[0]["content"], turn["operator_message"]["text"])
            self.assertEqual(events[1]["type"], "turn.hermes_reply")
            self.assertEqual(events[1]["content"], turn["agent_reply"]["text"])
            self.assertEqual(events[1]["payload"]["message"]["source"], "live_hermes")
            self.assertEqual(events[0]["content_sha256"], runtime.sha256_text(turn["operator_message"]["text"]))
            self.assertEqual(turns[0]["artifact_refs"][0]["path"], "apps/demo/lifecycle/01-intent/artifacts/intent.md")
            self.assertEqual(turns[0]["event_refs"][0]["event_id"], event["event_id"])
            self.assertEqual(turns[0]["state_transition"]["to_state"], "ready_for_review")
            self.assertFalse(turns[0]["agent_rationale"]["chain_of_thought_captured"])
            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertTrue(gate["transcript_capture"]["passed"])
            self.assertEqual(gate["transcript_capture"]["latest_turn_id"], turn["turn_id"])

            status, form = runtime.dispatch_rest(root, "GET", "/apps/demo/conversation/form")
            self.assertEqual(status, 200)
            self.assertEqual(form["form"]["schema"], runtime.CONVERSATION_CAPTURE_FORM_SCHEMA)
            self.assertEqual(form["form"]["deterministic_fields"]["current_stage"], "intent")
            self.assertEqual(form["form"]["deterministic_fields"]["artifact_refs"][0]["path"], "apps/demo/lifecycle/01-intent/artifacts/intent.md")
            self.assertIn("agent_rationale.summary", form["form"]["hermes_required_fields"])

            status, transcript = runtime.dispatch_rest(root, "GET", "/apps/demo/conversation")
            self.assertEqual(status, 200)
            self.assertEqual(transcript["turn_count"], 1)
            self.assertEqual(transcript["event_count"], 8)
            self.assertEqual(transcript["conversation_schema"], runtime.CONVERSATION_TURN_SCHEMA)
            self.assertEqual(transcript["conversation_event_schema"], runtime.CONVERSATION_EVENT_SCHEMA)
            self.assertIn("hidden model chain-of-thought is not captured", transcript["chain_of_thought_policy"])

            status, posted = runtime.dispatch_rest(
                root,
                "POST",
                "/apps/demo/conversation",
                {
                    "operator_message": "Can you proceed to research next?",
                    "agent_reply": {
                        "role": "hermes",
                        "source": "runtime_gate",
                        "text": "Not yet. Owner approval is still required before advancing.\n\n```md\n# raw markdown\n```\n<script>not executable</script>",
                    },
                    "agent_rationale": {
                        "summary": "The intent stage is ready, but the deterministic owner approval gate has not been recorded.",
                        "chain_of_thought_captured": False,
                    },
                    "state_transition": {
                        "from_stage": "intent",
                        "from_state": "ready_for_review",
                        "to_stage": "intent",
                        "to_state": "ready_for_review",
                    },
                    "next_action": "Use /approve_stage demo if the intent artifact is acceptable.",
                },
            )
            self.assertEqual(status, 201)
            self.assertEqual(posted["conversation_turn"]["stage"], "intent")
            self.assertEqual(posted["conversation_turn"]["artifact_refs"][0]["path"], "apps/demo/lifecycle/01-intent/artifacts/intent.md")
            self.assertTrue(posted["conversation_turn"]["gate_checks"]["foundation_gate_passed"])
            self.assertEqual(len(runtime.read_conversation_turns(root, "demo")), 2)
            self.assertEqual(len(runtime.read_conversation_events(root, "demo")), 16)

            product_source = root / "apps" / "demo" / "repo" / "primary" / "index.html"
            product_source.parent.mkdir(parents=True, exist_ok=True)
            product_source.write_text("<main>Playable product output</main>\n", encoding="utf-8")

            status, partial_posted = runtime.dispatch_rest(
                root,
                "POST",
                "/apps/demo/conversation",
                {
                    "schema": runtime.CONVERSATION_TURN_SCHEMA,
                    "stage": "intent",
                    "channel": "direct-hermes-cli",
                    "owner_message": {
                        "role": "owner",
                        "source": "qa_owner_operator_followup",
                        "text": "Follow up on the draft before owner review.",
                    },
                    "agent_reply": {
                        "role": "hermes",
                        "source": "live_hermes",
                        "model": "gpt-5.5",
                        "provider": "codex",
                        "text_summary": "Recommendations were handled and the stage is ready for review.",
                        "artifact_refs": [
                            {
                                "path": "apps/demo/lifecycle/01-intent/artifacts/intent.md",
                                "action": "updated",
                            }
                        ],
                    },
                    "artifact_refs": [
                        {
                            "path": "apps/demo/lifecycle/01-intent/artifacts/intent.md",
                            "action": "updated",
                            "kind": "stage_artifact",
                        },
                        {
                            "path": runtime.relative(product_source, root),
                            "action": "created",
                            "kind": "product_source",
                        },
                    ],
                    "agent_rationale": {
                        "summary": "Partial model-authored body should be normalized by deterministic runtime fields.",
                        "chain_of_thought_captured": False,
                    },
                },
            )
            self.assertEqual(status, 201)
            self.assertEqual(partial_posted["conversation_turn"]["agent_reply"]["text"], "Recommendations were handled and the stage is ready for review.")
            self.assertEqual(partial_posted["conversation_turn"]["artifact_refs"][0]["path"], "apps/demo/lifecycle/01-intent/artifacts/intent.md")
            self.assertEqual(len(runtime.read_conversation_turns(root, "demo")), 3)
            self.assertEqual(len(runtime.read_conversation_events(root, "demo")), 24)

            status, event_stream = runtime.dispatch_rest(root, "GET", "/apps/demo/conversation/events")
            self.assertEqual(status, 200)
            self.assertEqual(event_stream["event_count"], 24)
            self.assertEqual(event_stream["events"][9]["type"], "turn.hermes_reply")
            self.assertIn("<script>not executable</script>", event_stream["events"][9]["content"])

            status, export = runtime.dispatch_rest(root, "POST", "/apps/demo/conversation/export")
            self.assertEqual(status, 200)
            review = export["review"]
            self.assertEqual(review["schema"], runtime.CONVERSATION_REVIEW_REPORT_SCHEMA)
            self.assertEqual(review["turn_count"], 3)
            self.assertEqual(review["event_count"], 24)
            self.assertTrue(review["source_summary"]["all_agent_replies_source_labeled"])
            self.assertEqual(review["source_summary"]["agent_reply_sources"]["live_hermes"], 2)
            self.assertEqual(review["source_summary"]["agent_reply_sources"]["runtime_gate"], 1)
            html_path = root / review["exports"]["html_review"]
            event_copy_path = root / review["exports"]["event_stream"]
            report_path = root / review["exports"]["report"]
            self.assertTrue(html_path.exists())
            self.assertTrue(event_copy_path.exists())
            self.assertTrue(report_path.exists())
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Owner Message Sent To Hermes", html)
            self.assertIn("Hermes Reply", html)
            self.assertIn("Review Summary", html)
            self.assertIn("Runtime Gate Snapshot", html)
            self.assertIn("Hermes Gate Questions For Owner", html)
            self.assertIn("Artifacts Created Or Used", html)
            self.assertIn("Open artifact", html)
            self.assertIn("Preview artifact content", html)
            self.assertIn("apps/demo/lifecycle/01-intent/artifacts/intent.md", html)
            self.assertIn("apps/demo/repo/primary/index.html", html)
            self.assertIn("Playable product output", html)
            self.assertIn("product_source", html)
            self.assertIn("Selection / Selected Approach", html)
            self.assertIn("live_hermes", html)
            self.assertIn("gpt-5.5", html)
            self.assertIn("test-session", html)
            self.assertIn("stage_completion", html)
            self.assertIn("Make a short visual novel", html)
            self.assertIn("&lt;script&gt;not executable&lt;/script&gt;", html)
            self.assertNotIn("<script>not executable</script>", html)
            self.assertEqual(len(event_copy_path.read_text(encoding="utf-8").splitlines()), 24)

            slash = runtime.dispatch_telegram_command(root, "/transcript demo")
            self.assertTrue(slash["handled"])
            self.assertIn("WEAVE Transcript", slash["text"])
            self.assertIn("event_source: apps/demo/ledger/conversation-events.jsonl", slash["text"])
            self.assertIn("review_export: apps/demo/exports/conversation/conversation-review.html", slash["text"])
            self.assertIn("Make a short visual novel", slash["text"])
            self.assertIn("Foundation documents were complete", slash["text"])
            self.assertEqual(slash["payload"]["turn_count"], 3)
            self.assertEqual(slash["payload"]["conversation_events_path"], "apps/demo/ledger/conversation-events.jsonl")
            self.assertEqual(slash["payload"]["review_export_path"], "apps/demo/exports/conversation/conversation-review.html")

            app_status = runtime.dispatch_telegram_command(root, "/status demo")
            self.assertIn("Conversation Trace", app_status["text"])
            self.assertEqual(app_status["payload"]["conversation"]["turn_count"], 3)

            unsafe_value = "Use this provider credential " + "123456789:" + "abcdefghijklmnopqrstuvwxyzABCDEF"
            unsafe_turn = runtime.new_conversation_turn(
                "demo",
                "intent",
                unsafe_value,
                "I will not record raw secrets.",
            )
            with self.assertRaises(runtime.RuntimeSliceError):
                runtime.append_conversation_turn(root, "demo", unsafe_turn)

    def test_conversation_turn_reader_normalizes_partial_model_written_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            path = runtime.conversation_turn_path(root, "demo")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "schema": runtime.CONVERSATION_TURN_SCHEMA,
                        "turn_id": "partial-turn",
                        "app_id": "demo",
                        "created_at": "2026-06-07T00:00:00Z",
                        "created_by": "hermes",
                        "stage": "intent",
                        "channel": "direct-hermes-cli",
                        "owner_message": {
                            "role": "owner",
                            "source": "qa_owner_operator_followup",
                            "text": "Follow up before review.",
                        },
                        "agent_reply": {
                            "role": "hermes",
                            "source": "live_hermes",
                            "model": "gpt-5.5",
                            "provider": "codex",
                            "text_summary": "Handled the recommendation and kept launch gates closed.",
                            "artifact_refs": [
                                {
                                    "path": "apps/demo/lifecycle/01-intent/artifacts/intent-final.md",
                                    "action": "updated",
                                }
                            ],
                        },
                        "agent_rationale": {
                            "summary": "Model-authored partial record should not break review export.",
                            "chain_of_thought_captured": False,
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            turns = runtime.read_conversation_turns(root, "demo")
            self.assertEqual(len(turns), 1)
            self.assertEqual(turns[0]["turn_id"], "partial-turn")
            self.assertEqual(turns[0]["operator_message"]["text"], "Follow up before review.")
            self.assertEqual(turns[0]["agent_reply"]["text"], "Handled the recommendation and kept launch gates closed.")
            self.assertEqual(turns[0]["artifact_refs"][0]["path"], "apps/demo/lifecycle/01-intent/artifacts/intent-final.md")
            self.assertFalse(turns[0]["secret_payload_allowed"])

    def test_stage_derivation_uses_lifecycle_artifacts_not_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            selection_artifact = root / "apps" / "demo" / "lifecycle" / "03-selection" / "artifacts" / "selection.md"
            selection_artifact.write_text("# Selection\n", encoding="utf-8")

            self.assertEqual(runtime.derive_stage(root, "demo")["stage"], "selection")

            qa_ref = root / "apps" / "demo" / "lifecycle" / "07-qa" / "refs" / "contract-ref.json"
            qa_ref.parent.mkdir(parents=True, exist_ok=True)
            qa_ref.write_text(
                '{"schema":"weave-artifact-ref/v0.1","canonical_path":"apps/demo/lifecycle/03-selection/artifacts/selection.md"}\n',
                encoding="utf-8",
            )

            self.assertEqual(runtime.derive_stage(root, "demo")["stage"], "selection")
            qa_artifact = root / "apps" / "demo" / "lifecycle" / "07-qa" / "artifacts" / "qa.md"
            qa_artifact.parent.mkdir(parents=True, exist_ok=True)
            qa_artifact.write_text("# QA\n", encoding="utf-8")
            self.assertEqual(runtime.derive_stage(root, "demo")["stage"], "qa")
            artifacts = runtime.list_artifacts(root, "demo")
            self.assertEqual({item["kind"] for item in artifacts}, {"artifact", "ref"})

    def test_stage_contracts_are_reviewable_but_do_not_replace_proof_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            contract = runtime.stage_contract("selection")
            self.assertEqual(contract["schema"], "weave-lifecycle-stage-contract/v0.1")
            self.assertIn("selection matrix", " ".join(contract["output_artifacts"]))
            markdown = runtime.stage_contract_markdown("research")
            self.assertIn("Research Stage Contract", markdown)
            self.assertIn("research source log", markdown)
            ref_path = root / "apps" / "demo" / "lifecycle" / "01-intent" / "refs" / "stage-contract.md"
            ref_path.write_text(runtime.stage_contract_markdown("intent"), encoding="utf-8")

            gate = runtime.stage_gate_status(root, "demo", "intent")

            self.assertIn("intent artifact", gate["missing"])
            self.assertEqual(gate["proof_artifact_refs"], [])
            self.assertEqual(gate["artifact_refs"][0]["kind"], "ref")

    def test_rest_dispatch_exposes_local_skeleton_without_real_hermes_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")

            status, health = runtime.dispatch_rest(root, "GET", "/health")
            self.assertEqual(status, 200)
            self.assertEqual(health["bind"], "loopback-only")
            self.assertFalse(health["real_hermes_runtime"])

            status, apps = runtime.dispatch_rest(root, "GET", "/apps")
            self.assertEqual(status, 200)
            self.assertEqual(apps["apps"][0]["app_id"], "demo")

            status, state = runtime.dispatch_rest(root, "GET", "/apps/demo/state")
            self.assertEqual(status, 200)
            self.assertIn("foundation_gate", state)
            self.assertFalse(state["foundation_gate"]["passed"])

            event = runtime.new_event("window.changed", "demo", "implementation", "Window changed.")
            status, response = runtime.dispatch_rest(root, "POST", "/apps/demo/events", event)
            self.assertEqual(status, 201)
            self.assertEqual(response["event"]["type"], "window.changed")

    def test_telegram_slash_commands_are_deterministic_and_do_not_use_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            event = runtime.new_event("window.changed", "demo", "intent", "Owner-visible state changed.")
            runtime.append_event(root, "demo", event)

            status = runtime.dispatch_telegram_command(root, "/status")
            self.assertEqual(status["schema"], runtime.TELEGRAM_COMMAND_SCHEMA)
            self.assertTrue(status["deterministic"])
            self.assertFalse(status["llm_used"])
            sources = runtime.dispatch_telegram_command(root, "/sources")
            self.assertIn("Capability context index", sources["text"])
            self.assertIn("capability-context-index", sources["text"])
            self.assertEqual(status["payload"]["app_count"], 1)
            self.assertEqual(status["payload"]["blocked_apps"], ["demo"])
            self.assertEqual(status["payload"]["foundation_blocked_apps"], ["demo"])
            self.assertEqual(status["payload"]["app_blocked_apps"], [])
            self.assertEqual(status["payload"]["agent_profile"]["model"], "unknown")
            self.assertEqual(status["payload"]["autonomy"]["mode"], "yolo")
            self.assertEqual(status["payload"]["source_map"]["canonical_source_id"], "weave-root")
            self.assertIn("WEAVE Status", status["text"])
            self.assertIn("Agent", status["text"])
            self.assertIn("Hermes Setup", status["text"])
            self.assertIn("state: needs_hermes_setup", status["text"])
            self.assertIn("product_apps: 1", status["text"])
            self.assertEqual(status["payload"]["hermes_setup"]["state"], "needs_hermes_setup")

            sources = runtime.dispatch_telegram_command(root, "/sources")
            self.assertEqual(sources["schema"], runtime.TELEGRAM_COMMAND_SCHEMA)
            self.assertFalse(sources["llm_used"])
            self.assertIn("WEAVE source map", sources["text"])
            self.assertIn("App registry", sources["text"])
            self.assertEqual(sources["payload"]["summary"]["canonical_source_id"], "weave-root")

            autonomy = runtime.dispatch_telegram_command(root, "/autonomy")
            self.assertIn("mode: yolo", autonomy["text"])
            self.assertIn("hard_gates:", autonomy["text"])
            self.assertTrue(autonomy["payload"]["autonomy"]["llm_must_request_owner_authorization_for_hard_gates"])

            apps = runtime.dispatch_telegram_command(root, "/apps")
            self.assertIn("Demo (demo)", apps["text"])
            self.assertEqual(apps["payload"]["apps"][0]["stage"], "intent")
            self.assertEqual(apps["payload"]["apps"][0]["stage_state"], "collecting")

            app = runtime.dispatch_telegram_command(root, "/app demo")
            self.assertIn("WEAVE App Status", app["text"])
            self.assertIn("foundation: blocking", app["text"])
            self.assertIn("Lifecycle", app["text"])
            self.assertIn("foundation_gate", app["payload"])

            app_status = runtime.dispatch_telegram_command(root, "/status demo")
            self.assertIn("WEAVE App Status", app_status["text"])
            self.assertEqual(app_status["payload"]["app_id"], "demo")

            stage = runtime.dispatch_telegram_command(root, "/stage demo")
            self.assertIn("WEAVE Stage", stage["text"])
            self.assertEqual(stage["payload"]["stage_status"]["stage"], "intent")

            requirements = runtime.dispatch_telegram_command(root, "/requirements demo")
            self.assertIn("WEAVE Requirements", requirements["text"])
            self.assertIn("owner intent", requirements["text"])

            blockers = runtime.dispatch_telegram_command(root, "/blockers")
            self.assertIn("foundation", blockers["text"])

            changes = runtime.dispatch_telegram_command(root, "/changes demo")
            self.assertIn("window", changes["text"])

            next_action = runtime.dispatch_telegram_command(root, "/next")
            self.assertIn("foundation onboarding", next_action["text"])

            help_response = runtime.dispatch_telegram_command(root, "/help")
            self.assertIn("/status", help_response["payload"]["commands"])
            self.assertIn("/transcript", help_response["payload"]["commands"])

            passthrough = runtime.dispatch_telegram_command(root, "normal Hermes chat")
            self.assertFalse(passthrough["handled"])
            self.assertEqual(passthrough["error"], "not_slash_command")

    def test_ready_for_review_triggers_evaluation_duty_and_blocks_until_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")

            record_stage_turn(root, "demo", "intent", artifact_path)

            request_path = runtime.evaluation_request_path(root, "demo", "intent")
            duty_path = runtime.evaluation_duty_path(root, "demo", "intent")
            self.assertTrue(request_path.exists())
            self.assertTrue(duty_path.exists())
            duty = json.loads(duty_path.read_text(encoding="utf-8"))
            self.assertEqual(duty["status"], "waiting_for_agent")
            self.assertEqual(duty["state"], "evaluator-agent-command-missing")
            self.assertIn("POST a completed eval review artifact", duty["next_actions"][0])

            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertFalse(gate["passed"])
            self.assertIn("evaluation: waiting_for_agent", gate["missing"])
            lifecycle = runtime.dispatch_telegram_command(root, "/lifecycle demo")
            self.assertIn("state: ready_for_review", lifecycle["text"])
            self.assertFalse(lifecycle["payload"]["stage_gate"]["passed"])
            self.assertIn("evaluation: waiting_for_agent", lifecycle["payload"]["stage_gate"]["missing"])

            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertFalse(approval["handled"])
            self.assertIn("evaluation: waiting_for_agent", approval["text"])
            events = [event["type"] for event in runtime.read_events(root, "demo")]
            self.assertIn("lifecycle.stage_ready_for_review", events)
            self.assertIn("evaluation.requested", events)
            self.assertIn("evaluation.waiting_for_agent", events)

    def test_evaluation_request_uses_linked_ready_for_review_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            stage_dir = root / "apps" / "demo" / "lifecycle" / runtime.stage_by_id("intent").directory / "artifacts"
            linked_artifact = stage_dir / "a-linked.md"
            unlinked_artifact = stage_dir / "z-unlinked.md"
            fill(linked_artifact, "Linked Intent")
            fill(unlinked_artifact, "Unlinked Intent")

            record_stage_turn(root, "demo", "intent", linked_artifact)

            request = json.loads(runtime.evaluation_request_path(root, "demo", "intent").read_text(encoding="utf-8"))
            self.assertEqual(request["artifact"], runtime.relative(linked_artifact, root))
            self.assertEqual(request["artifact_refs"], [runtime.transcript_capture_status(root, "demo", "intent")["latest_artifact_ref"]])
            self.assertEqual(request["artifact_refs"][0]["checksum"], runtime.artifact_checksum(linked_artifact))

    def test_ready_for_review_supersedes_stale_evaluation_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            stage_dir = root / "apps" / "demo" / "lifecycle" / runtime.stage_by_id("intent").directory / "artifacts"
            old_artifact = stage_dir / "a-old.md"
            new_artifact = stage_dir / "z-new.md"
            fill(old_artifact, "Old Intent")
            record_stage_turn(root, "demo", "intent", old_artifact)
            runtime.complete_evaluation_from_review(
                root,
                "demo",
                "intent",
                valid_stage_review("intent", runtime.relative(old_artifact, root)),
            )
            self.assertTrue(runtime.stage_evaluation_status(root, "demo", "intent")["passed"])

            fill(new_artifact, "New Intent")
            record_stage_turn(root, "demo", "intent", new_artifact)

            request = json.loads(runtime.evaluation_request_path(root, "demo", "intent").read_text(encoding="utf-8"))
            self.assertEqual(request["artifact"], runtime.relative(new_artifact, root))
            status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertFalse(status["passed"])
            self.assertEqual(status["status"], "waiting_for_agent")
            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertFalse(gate["passed"])
            self.assertIn("evaluation: waiting_for_agent", gate["missing"])
            app = runtime.load_app(root, "demo")
            self.assertEqual(app["evaluation_statuses"]["intent"]["result_path"], "")

    def test_completed_result_without_review_does_not_open_approval_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            request = json.loads(runtime.evaluation_request_path(root, "demo", "intent").read_text(encoding="utf-8"))
            now = runtime.utc_now()
            runtime.write_json_artifact(
                runtime.evaluation_result_path(root, "demo", "intent"),
                {
                    "schema": "weave.eval-result/v0.1",
                    "stage": "Intent",
                    "slug": "intent",
                    "artifact": request["artifact"],
                    "contract": request["contract"],
                    "state": "verified",
                    "hard_gates": [],
                    "rubric_score": {"status": "complete", "total": 16, "max_total": 16, "percent": 100.0},
                    "decision": "advance",
                    "blockers": [],
                    "next_actions": ["advance to next lifecycle stage"],
                    "request_id": request["request_id"],
                    "transcript_turn_id": request["transcript_turn_id"],
                    "artifact_refs": request["artifact_refs"],
                    "proof_scope": "local_deterministic_runtime",
                },
            )
            runtime.write_json_artifact(
                runtime.evaluation_duty_path(root, "demo", "intent"),
                {
                    "schema": runtime.EVALUATION_DUTY_SCHEMA,
                    "request_id": request["request_id"],
                    "app_id": "demo",
                    "stage": "intent",
                    "created_at": now,
                    "updated_at": now,
                    "request_path": runtime.relative(runtime.evaluation_request_path(root, "demo", "intent"), root),
                    "review_path": runtime.relative(runtime.evaluation_review_path(root, "demo", "intent"), root),
                    "result_path": runtime.relative(runtime.evaluation_result_path(root, "demo", "intent"), root),
                    "run_gates": False,
                    "status": "completed",
                    "decision": "advance",
                    "state": "verified",
                    "blockers": [],
                    "next_actions": [],
                    "agent_command_configured": False,
                    "public_safe": True,
                    "secret_payload_allowed": False,
                    "completed_by": "forged-local-test",
                },
            )

            status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertFalse(status["passed"])
            self.assertEqual(status["status"], "stale_result")
            self.assertIn("review artifact is missing", status["blockers"][0])
            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertFalse(gate["passed"])
            self.assertIn("evaluation: stale_result", gate["missing"])
            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertFalse(approval["handled"])

    def test_deterministic_review_does_not_satisfy_command_gate_without_execution(self) -> None:
        review = runtime.deterministic_evaluation_review("engineering", "current")
        result = runtime.evaluate_review_artifact("engineering", review, "current", run_gates=False)

        self.assertEqual(result["decision"], "needs_gate_execution")
        self.assertIn("unit_tests_pass", result["blockers"][0])
        command_gate_statuses = {gate["gate_id"]: gate["status"] for gate in result["hard_gates"]}
        self.assertEqual(command_gate_statuses["unit_tests_pass"], "not_run")
        self.assertEqual(command_gate_statuses["diff_check_clean"], "not_run")
        self.assertEqual(command_gate_statuses["no_secret_leakage"], "not_run")

    def test_forged_matching_review_and_result_do_not_open_approval_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            request = json.loads(runtime.evaluation_request_path(root, "demo", "intent").read_text(encoding="utf-8"))
            review = valid_stage_review("intent", request["artifact"])
            forged_result = runtime.evaluate_review_artifact("intent", review, request["artifact"], run_gates=False)
            forged_result.update(
                {
                    "request_id": request["request_id"],
                    "transcript_turn_id": request["transcript_turn_id"],
                    "artifact_refs": request["artifact_refs"],
                    "proof_scope": "local_deterministic_runtime",
                    "decision": "advance",
                    "state": "verified",
                    "rubric_score": {"status": "scored", "total": 0, "max_total": 16, "percent": 0.0},
                    "blockers": [],
                    "next_actions": ["advance to next lifecycle stage"],
                }
            )
            review_path = runtime.evaluation_review_path(root, "demo", "intent")
            result_path = runtime.evaluation_result_path(root, "demo", "intent")
            runtime.write_json_artifact(review_path, review)
            runtime.write_json_artifact(result_path, forged_result)
            now = runtime.utc_now()
            runtime.write_json_artifact(
                runtime.evaluation_duty_path(root, "demo", "intent"),
                {
                    "schema": runtime.EVALUATION_DUTY_SCHEMA,
                    "request_id": request["request_id"],
                    "app_id": "demo",
                    "stage": "intent",
                    "created_at": now,
                    "updated_at": now,
                    "request_path": runtime.relative(runtime.evaluation_request_path(root, "demo", "intent"), root),
                    "review_path": runtime.relative(review_path, root),
                    "result_path": runtime.relative(result_path, root),
                    "review_checksum": runtime.artifact_checksum(review_path),
                    "result_checksum": runtime.artifact_checksum(result_path),
                    "run_gates": False,
                    "status": "completed",
                    "decision": "advance",
                    "state": "verified",
                    "blockers": [],
                    "next_actions": [],
                    "agent_command_configured": False,
                    "public_safe": True,
                    "secret_payload_allowed": False,
                    "completed_by": "forged-local-test",
                },
            )

            status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertFalse(status["passed"])
            self.assertEqual(status["status"], "stale_result")
            self.assertIn("inconsistent", status["blockers"][0])
            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertFalse(gate["passed"])
            self.assertIn("evaluation: stale_result", gate["missing"])
            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertFalse(approval["handled"])

    def test_run_gates_status_rebinds_manual_gates_to_current_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            request = json.loads(runtime.evaluation_request_path(root, "demo", "intent").read_text(encoding="utf-8"))
            passing_review = valid_stage_review("intent", request["artifact"])
            forged_result = runtime.evaluate_review_artifact("intent", passing_review, request["artifact"], run_gates=False)
            forged_result.update(
                {
                    "request_id": request["request_id"],
                    "transcript_turn_id": request["transcript_turn_id"],
                    "artifact_refs": request["artifact_refs"],
                    "proof_scope": "local_deterministic_runtime",
                }
            )
            failing_review = valid_stage_review("intent", request["artifact"])
            first_gate = next(iter(failing_review["hard_gates"].values()))
            first_gate["passed"] = False
            first_gate["evidence"] = [request["artifact"]]
            first_gate["notes"] = "Manual gate is explicitly unresolved in the current review."
            review_path = runtime.evaluation_review_path(root, "demo", "intent")
            result_path = runtime.evaluation_result_path(root, "demo", "intent")
            runtime.write_json_artifact(review_path, failing_review)
            runtime.write_json_artifact(result_path, forged_result)
            now = runtime.utc_now()
            runtime.write_json_artifact(
                runtime.evaluation_duty_path(root, "demo", "intent"),
                {
                    "schema": runtime.EVALUATION_DUTY_SCHEMA,
                    "request_id": request["request_id"],
                    "app_id": "demo",
                    "stage": "intent",
                    "created_at": now,
                    "updated_at": now,
                    "request_path": runtime.relative(runtime.evaluation_request_path(root, "demo", "intent"), root),
                    "review_path": runtime.relative(review_path, root),
                    "result_path": runtime.relative(result_path, root),
                    "review_checksum": runtime.artifact_checksum(review_path),
                    "result_checksum": runtime.artifact_checksum(result_path),
                    "run_gates": True,
                    "status": "completed",
                    "decision": "advance",
                    "state": "verified",
                    "blockers": [],
                    "next_actions": [],
                    "agent_command_configured": False,
                    "public_safe": True,
                    "secret_payload_allowed": False,
                    "completed_by": "forged-local-test",
                },
            )

            status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertFalse(status["passed"])
            self.assertEqual(status["status"], "stale_result")
            self.assertIn("inconsistent", status["blockers"][0])

    def test_evaluation_review_rejection_does_not_create_partial_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            review = valid_stage_review("intent", "current")
            private_path = "/" + "var/tmp/private-proof.json"
            first_gate = next(iter(review["hard_gates"].values()))
            first_gate["evidence"] = [private_path]

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.complete_evaluation_from_review(root, "demo", "intent", review)
            self.assertFalse(runtime.evaluation_request_path(root, "demo", "intent").exists())
            self.assertFalse(runtime.evaluation_review_path(root, "demo", "intent").exists())
            self.assertFalse(runtime.evaluation_result_path(root, "demo", "intent").exists())

    def test_evaluation_review_rejects_private_locator_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            artifact_ref = runtime.relative(artifact_path, root)
            review = valid_stage_review("intent", artifact_ref)
            private_path = "/" + "var/tmp/private-proof.json"
            first_gate = next(iter(review["hard_gates"].values()))
            first_gate["evidence"] = [private_path]

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                runtime.complete_evaluation_from_review(root, "demo", "intent", review)
            self.assertFalse(runtime.evaluation_review_path(root, "demo", "intent").exists())
            self.assertFalse(runtime.evaluation_result_path(root, "demo", "intent").exists())

    def test_evaluation_json_artifacts_reject_private_locator_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            private_address = ".".join(["192", "168", "1", "25"])
            payloads = [
                "proof at http://" + private_address + "/result.json",
                "trace wrote '/tmp/private-proof.json'",
                "review_file=/var/tmp/private-proof.json",
            ]
            for index, payload in enumerate(payloads):
                path = Path(tmpdir) / f"result-{index}.json"
                with self.subTest(payload=payload):
                    with self.assertRaisesRegex(runtime.RuntimeSliceError, "private locator"):
                        runtime.write_json_artifact(
                            path,
                            {
                                "schema": "weave.eval-result/v0.1",
                                "public_safe": True,
                                "secret_payload_allowed": False,
                                "output_excerpt": payload,
                            },
                        )
                    self.assertFalse(path.exists())

    def test_evaluator_agent_review_is_validated_and_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            artifact_ref = runtime.relative(artifact_path, root)
            review = valid_stage_review("intent", artifact_ref, reviewer="valid-review-agent")
            agent = Path(tmpdir) / "valid_review_agent.py"
            agent.write_text(
                "import json, os\n"
                f"review = json.loads({json.dumps(json.dumps(review))})\n"
                "with open(os.environ['WEAVE_EVAL_REVIEW_FILE'], 'w', encoding='utf-8') as handle:\n"
                "    json.dump(review, handle)\n",
                encoding="utf-8",
            )

            with mock.patch.dict(
                os.environ,
                {
                    "WEAVE_EVALUATOR_AGENT_COMMAND": f"{sys.executable} {agent}",
                    "WEAVE_EVALUATOR_AGENT_TIMEOUT_SECONDS": "30",
                },
            ):
                duty = runtime.run_evaluation_duty(root, "demo", "intent")

            self.assertEqual(duty["status"], "completed")
            self.assertEqual(duty["decision"], "advance")
            review_path = runtime.evaluation_review_path(root, "demo", "intent")
            result_path = runtime.evaluation_result_path(root, "demo", "intent")
            self.assertTrue(review_path.exists())
            self.assertTrue(result_path.exists())
            stored_review = json.loads(review_path.read_text(encoding="utf-8"))
            self.assertEqual(stored_review["reviewer"], "valid-review-agent")
            status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertTrue(status["passed"])
            self.assertEqual(status["result_path"], runtime.relative(result_path, root))

    def test_evaluator_agent_private_review_is_rejected_before_canonical_storage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            artifact_ref = runtime.relative(artifact_path, root)
            review = valid_stage_review("intent", artifact_ref, reviewer="private-review-agent")
            private_path = "/" + "var/tmp/private-proof.json"
            first_gate = next(iter(review["hard_gates"].values()))
            first_gate["evidence"] = [private_path]
            agent = Path(tmpdir) / "private_review_agent.py"
            agent.write_text(
                "import json, os\n"
                f"review = json.loads({json.dumps(json.dumps(review))})\n"
                "with open(os.environ['WEAVE_EVAL_REVIEW_FILE'], 'w', encoding='utf-8') as handle:\n"
                "    json.dump(review, handle)\n",
                encoding="utf-8",
            )

            with mock.patch.dict(
                os.environ,
                {
                    "WEAVE_EVALUATOR_AGENT_COMMAND": f"{sys.executable} {agent}",
                    "WEAVE_EVALUATOR_AGENT_TIMEOUT_SECONDS": "30",
                },
            ):
                duty = runtime.run_evaluation_duty(root, "demo", "intent")

            self.assertEqual(duty["status"], "failed")
            self.assertEqual(duty["state"], "evaluator-review-invalid")
            self.assertIn("private locator", duty["blockers"][0])
            self.assertFalse(runtime.evaluation_review_path(root, "demo", "intent").exists())
            self.assertFalse(runtime.evaluation_result_path(root, "demo", "intent").exists())
            stored_duty = json.loads(runtime.evaluation_duty_path(root, "demo", "intent").read_text(encoding="utf-8"))
            self.assertFalse(runtime.contains_private_locator(stored_duty))
            status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertEqual(status["status"], "failed")
            self.assertFalse(status["passed"])
            events = [event["type"] for event in runtime.read_events(root, "demo")]
            self.assertIn("evaluation.failed", events)

    def test_evaluator_agent_malformed_review_fails_without_leaking_temp_path(self) -> None:
        for label, review_payload, expected_blocker in (
            ("malformed", "{bad", "evaluator review artifact is invalid"),
            ("non_object", "[]", "JSON object"),
        ):
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir) / "weave-root"
                    runtime.create_app(root, "demo", "Demo")
                    complete_foundation(root, "demo")
                    artifact_path = write_stage_artifact(root, "demo", "intent")
                    record_stage_turn(root, "demo", "intent", artifact_path)
                    agent = Path(tmpdir) / f"{label}_review_agent.py"
                    agent.write_text(
                        "import os\n"
                        f"open(os.environ['WEAVE_EVAL_REVIEW_FILE'], 'w', encoding='utf-8').write({json.dumps(review_payload)})\n",
                        encoding="utf-8",
                    )

                    with mock.patch.dict(
                        os.environ,
                        {
                            "WEAVE_EVALUATOR_AGENT_COMMAND": f"{sys.executable} {agent}",
                            "WEAVE_EVALUATOR_AGENT_TIMEOUT_SECONDS": "30",
                        },
                    ):
                        duty = runtime.run_evaluation_duty(root, "demo", "intent")

                    self.assertEqual(duty["status"], "failed")
                    self.assertEqual(duty["state"], "evaluator-review-invalid")
                    self.assertIn(expected_blocker, duty["blockers"][0])
                    self.assertFalse(runtime.evaluation_review_path(root, "demo", "intent").exists())
                    self.assertFalse(runtime.evaluation_result_path(root, "demo", "intent").exists())
                    stored_duty = json.loads(runtime.evaluation_duty_path(root, "demo", "intent").read_text(encoding="utf-8"))
                    self.assertFalse(runtime.contains_private_locator(stored_duty))
                    status = runtime.stage_evaluation_status(root, "demo", "intent")
                    self.assertEqual(status["status"], "failed")
                    self.assertFalse(status["passed"])
                    events = [event["type"] for event in runtime.read_events(root, "demo")]
                    self.assertIn("evaluation.failed", events)

    def test_no_secret_leakage_gate_id_is_metadata_not_secret_value(self) -> None:
        self.assertFalse(
            runtime.contains_secret_like_value(
                {
                    "hard_gates": {
                        "no_secret_leakage": {
                            "passed": True,
                            "evidence": ["scan-artifact: ok"],
                            "notes": "secret scanner proof stayed public-safe",
                        }
                    }
                }
            )
        )
        self.assertTrue(
            runtime.contains_secret_like_value(
                {
                    "hard_gates": {
                        "no_secret_leakage": {
                            "passed": True,
                            "evidence": ["sk_" + "a" * 16],
                        }
                    }
                }
            )
        )

    def test_evaluation_review_storage_records_decision_and_opens_approval_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            artifact_ref = runtime.relative(artifact_path, root)

            status, response = runtime.dispatch_rest(
                root,
                "POST",
                "/apps/demo/evaluation/review",
                {"stage": "intent", "review": valid_stage_review("intent", artifact_ref)},
            )

            self.assertEqual(status, 200)
            self.assertTrue(response["completed"])
            self.assertEqual(response["result"]["decision"], "advance")
            self.assertEqual(response["result"]["state"], "verified")
            self.assertEqual(response["duty"]["status"], "completed")
            self.assertTrue(runtime.evaluation_review_path(root, "demo", "intent").exists())
            self.assertTrue(runtime.evaluation_result_path(root, "demo", "intent").exists())
            stored_status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertTrue(stored_status["passed"])
            self.assertEqual(stored_status["decision"], "advance")
            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertTrue(gate["passed"])
            self.assertEqual(gate["missing"], [])
            app = runtime.load_app(root, "demo")
            self.assertEqual(app["evaluation_statuses"]["intent"]["status"], "completed")
            events = [event["type"] for event in runtime.read_events(root, "demo")]
            self.assertIn("evaluation.review_recorded", events)
            self.assertIn("evaluation.completed", events)

    def test_evaluation_review_rejects_unbound_artifact_for_current_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            artifact_ref = runtime.relative(artifact_path, root)
            review = valid_stage_review("intent", artifact_ref)
            review["artifact"] = ""

            with self.assertRaisesRegex(runtime.RuntimeSliceError, "review artifact is required"):
                runtime.dispatch_rest(root, "POST", "/apps/demo/evaluation/review", {"stage": "intent", "review": review})

            self.assertFalse(runtime.evaluation_review_path(root, "demo", "intent").exists())
            self.assertFalse(runtime.evaluation_result_path(root, "demo", "intent").exists())
            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertFalse(gate["passed"])
            self.assertIn("evaluation:", " ".join(gate["missing"]))

    def test_evaluation_status_rejects_mutated_artifact_after_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            artifact_ref = runtime.relative(artifact_path, root)
            runtime.complete_evaluation_from_review(root, "demo", "intent", valid_stage_review("intent", artifact_ref))
            self.assertTrue(runtime.stage_evaluation_status(root, "demo", "intent")["passed"])

            artifact_path.write_text(
                "# Intent Mutated After Eval\n\nStatus: changed after the evaluator reviewed this artifact.\n",
                encoding="utf-8",
            )

            status = runtime.stage_evaluation_status(root, "demo", "intent")
            self.assertFalse(status["passed"])
            self.assertEqual(status["status"], "stale_result")
            self.assertIn("artifact checksum", status["blockers"][0])
            gate = runtime.stage_gate_status(root, "demo", "intent")
            self.assertFalse(gate["passed"])
            self.assertIn("evaluation: stale_result", gate["missing"])
            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertFalse(approval["handled"])

    def test_lifecycle_approval_and_advance_are_stage_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")

            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertFalse(approval["handled"])
            self.assertEqual(approval["error"], "stage_gate_blocking")
            self.assertIn("foundation context", approval["text"])

            complete_foundation(root, "demo")
            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertFalse(approval["handled"])
            self.assertIn("intent artifact", approval["text"])

            status = runtime.dispatch_telegram_command(root, "/status")
            self.assertIn("stage_gate_blocked_apps: 1", status["text"])
            self.assertEqual(status["payload"]["stage_gate_blocked_apps"], ["demo"])

            blockers = runtime.dispatch_telegram_command(root, "/blockers")
            self.assertIn("stage gate intent artifact", blockers["text"])
            next_action = runtime.dispatch_telegram_command(root, "/next")
            self.assertIn("complete lifecycle gate", next_action["text"])

            artifact_path = write_stage_artifact(root, "demo", "intent")
            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertFalse(approval["handled"])
            self.assertIn("transcript capture", approval["text"])

            record_stage_turn(root, "demo", "intent", artifact_path)
            evaluation_blocked_advance = runtime.dispatch_telegram_command(root, "/advance demo")
            self.assertFalse(evaluation_blocked_advance["handled"])
            self.assertEqual(evaluation_blocked_advance["error"], "current_stage_gate_not_passing")

            complete_stage_evaluation(root, "demo", "intent", artifact_path)
            premature_advance = runtime.dispatch_telegram_command(root, "/advance demo")
            self.assertFalse(premature_advance["handled"])
            self.assertEqual(premature_advance["error"], "current_stage_not_approved")

            lifecycle = runtime.dispatch_telegram_command(root, "/lifecycle demo")
            self.assertIn("state: ready_for_review", lifecycle["text"])
            self.assertTrue(lifecycle["payload"]["stage_gate"]["passed"])

            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")
            self.assertTrue(approval["handled"])
            self.assertTrue(approval["payload"]["approved"])
            self.assertEqual(approval["payload"]["stage"], "intent")

            advanced = runtime.dispatch_telegram_command(root, "/advance demo")
            self.assertTrue(advanced["handled"])
            self.assertEqual(advanced["payload"]["from_stage"], "intent")
            self.assertEqual(advanced["payload"]["stage"], "research")

            app = runtime.load_app(root, "demo")
            self.assertEqual(app["current_stage"], "research")
            self.assertEqual(app["stage_source"], "approved_advance")
            self.assertIn("intent", app["approved_stages"])

    def test_rest_lifecycle_controls_match_telegram_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            artifact_ref = runtime.relative(artifact_path, root)
            status, evaluation = runtime.dispatch_rest(
                root,
                "POST",
                "/apps/demo/evaluation/review",
                {"stage": "intent", "review": valid_stage_review("intent", artifact_ref)},
            )
            self.assertEqual(status, 200)
            self.assertEqual(evaluation["result"]["decision"], "advance")

            status, telegram_approval = runtime.dispatch_rest(
                root,
                "POST",
                "/telegram/dispatch",
                {"text": "/approve_stage demo"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(telegram_approval["telegram_command"]["payload"]["approved"])

            status, telegram_advance = runtime.dispatch_rest(
                root,
                "POST",
                "/telegram/dispatch",
                {"text": "/advance demo"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(telegram_advance["telegram_command"]["payload"]["stage"], "research")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "intent")
            record_stage_turn(root, "demo", "intent", artifact_path)
            complete_stage_evaluation(root, "demo", "intent", artifact_path)

            status, approval = runtime.dispatch_rest(root, "POST", "/apps/demo/approve-stage", {})
            self.assertEqual(status, 200)
            self.assertTrue(approval["approved"])

            status, advanced = runtime.dispatch_rest(root, "POST", "/apps/demo/advance", {})
            self.assertEqual(status, 200)
            self.assertTrue(advanced["advanced"])
            self.assertEqual(advanced["stage"], "research")

            status, lifecycle = runtime.dispatch_rest(root, "GET", "/apps/demo/lifecycle")
            self.assertEqual(status, 200)
            self.assertEqual(lifecycle["stage_status"]["stage"], "research")
            self.assertIn("stage_gate", lifecycle)

    def test_lifecycle_stage_gate_requires_prior_stage_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            write_stage_artifact(root, "demo", "qa")

            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo")

            self.assertFalse(approval["handled"])
            self.assertIn("previous stage approval", approval["text"])
            self.assertIn("intent", approval["text"])

    def test_credential_stage_gate_can_be_owner_deferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            complete_foundation(root, "demo")
            artifact_path = write_stage_artifact(root, "demo", "marketing")
            app = runtime.load_app(root, "demo")
            app["current_stage"] = "marketing"
            app["stage_source"] = "approved_advance"
            # Marketing cannot be approved until deployment and KPI have both
            # been explicitly approved; this fixture is about credential
            # deferral, so the prior-stage gate is satisfied on purpose.
            app["approved_stages"] = ["intent", "research", "selection", "plan", "engineering", "qa", "deployment", "kpi"]
            app["credential_requirements"] = [
                {"id": "marketing-provider", "label": "Marketing provider", "required": True, "status": "missing"}
            ]
            runtime.write_app(root, app)

            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo marketing")
            self.assertFalse(approval["handled"])
            self.assertIn("credential capability", approval["text"])

            record_stage_turn(root, "demo", "marketing", artifact_path)
            complete_stage_evaluation(root, "demo", "marketing", artifact_path)
            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo marketing --defer-credentials")
            self.assertTrue(approval["handled"])
            self.assertTrue(approval["payload"]["approved"])
            app = runtime.load_app(root, "demo")
            self.assertEqual(app["credential_requirements"][0]["status"], "deferred")
            self.assertIn("marketing", app["approved_stages"])

    def test_status_counts_app_blockers_after_foundation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.setup_foundation_onboarding(root, "demo", "Demo")
            required = {
                root / "artifacts" / "general" / "soul.md": "# Soul\n\nStatus: complete\n",
                root / "artifacts" / "general" / "owner-profile.md": "# Owner Profile\n\nStatus: complete\n",
                root / "apps" / "demo" / "context" / "app-context.md": "# App Context\n\nStatus: complete\n",
                root / "apps" / "demo" / "inventory" / "app-inventory.md": "# App Inventory\n\nStatus: complete\n",
                root / "apps" / "demo" / "contract" / "gestaltian-contract.md": "# Contract\n\nStatus: complete\n",
            }
            for path, content in required.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            app = runtime.load_app(root, "demo")
            app["blockers"] = ["Unify stale runtime status surface."]
            runtime.write_app(root, app)

            status = runtime.dispatch_telegram_command(root, "/status")

            self.assertIn("blocked_apps: 1", status["text"])
            self.assertIn("foundation_blocked_apps: 0", status["text"])
            self.assertIn("app_blocked_apps: 1", status["text"])
            self.assertIn("Resolve blocker for demo", status["text"])
            self.assertEqual(status["payload"]["blocked_apps"], ["demo"])
            self.assertEqual(status["payload"]["foundation_blocked_apps"], [])
            self.assertEqual(status["payload"]["app_blocked_apps"], ["demo"])

    def test_create_and_switch_app_commands_manage_active_product_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.setup_weave_root(root)

            created = runtime.dispatch_telegram_command(root, "/create_app Visual Novel")

            self.assertTrue(created["handled"])
            self.assertEqual(created["payload"]["active_app"]["app_id"], "visual-novel")
            self.assertEqual(runtime.load_active_app(root)["app_id"], "visual-novel")
            self.assertIn("Created product app", created["text"])

            status = runtime.dispatch_telegram_command(root, "/status")
            self.assertIn("active_app: visual-novel", status["text"])

            second = runtime.dispatch_telegram_command(root, "/create_app Puzzle Tool")
            self.assertEqual(second["payload"]["active_app"]["app_id"], "puzzle-tool")

            switched = runtime.dispatch_telegram_command(root, "/switch_app visual-novel")
            self.assertEqual(switched["payload"]["active_app"]["app_id"], "visual-novel")

            active_app_wall = runtime.dispatch_telegram_command(root, "/app")
            self.assertEqual(active_app_wall["payload"]["app_id"], "visual-novel")

    def test_system_apps_are_hidden_from_default_apps_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "weave", "WEAVE")
            runtime.create_app(root, "visual-novel", "Visual Novel")

            apps = runtime.dispatch_telegram_command(root, "/apps")
            self.assertNotIn("WEAVE (weave)", apps["text"])
            self.assertIn("Visual Novel (visual-novel)", apps["text"])
            self.assertEqual([app["app_id"] for app in apps["payload"]["apps"]], ["visual-novel"])

            all_apps = runtime.dispatch_telegram_command(root, "/apps --all")
            self.assertIn("WEAVE (weave)", all_apps["text"])
            self.assertEqual(len(all_apps["payload"]["apps"]), 2)

    def test_rest_dispatch_exposes_telegram_command_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.setup_weave_root(root)

            status, response = runtime.dispatch_rest(root, "GET", "/telegram/commands")

            self.assertEqual(status, 200)
            self.assertTrue(response["deterministic"])
            self.assertFalse(response["llm_used"])
            self.assertIn("/apps", response["commands"])

            status, response = runtime.dispatch_rest(root, "GET", "/runtime/sources")
            self.assertEqual(status, 200)
            self.assertEqual(response["source_map"]["schema"], runtime.SOURCE_MAP_SCHEMA)


if __name__ == "__main__":
    unittest.main()
