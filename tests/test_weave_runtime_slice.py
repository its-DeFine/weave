from __future__ import annotations

import json
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


class WeaveRuntimeSliceTests(unittest.TestCase):
    def test_setup_creates_root_registry_templates_and_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            result = runtime.setup_weave_root(root)

            self.assertEqual(result["schema"], runtime.ROOT_SCHEMA)
            self.assertTrue((root / "apps" / "registry.json").exists())
            self.assertTrue((root / "artifacts" / "general" / "soul.md").exists())
            self.assertTrue((root / "artifacts" / "general" / "owner-profile.md").exists())
            self.assertTrue((root / "ledger" / "events.jsonl").exists())
            self.assertTrue((root / "runtime" / "tokens" / "local-api-token").exists())
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
            self.assertEqual(result["app"]["conversation_turns_path"], "ledger/conversation-turns.jsonl")
            self.assertEqual(result["app"]["conversation_events_path"], "ledger/conversation-events.jsonl")
            self.assertIn("conversation-turn-ledger", result["app"]["capabilities"])
            self.assertIn("conversation-event-ledger", result["app"]["capabilities"])
            registry = runtime.load_registry(root)
            self.assertEqual(registry["apps"][0]["app_id"], "demo-app")
            self.assertEqual(registry["apps"][0]["app_type"], "product")
            gate = runtime.foundation_gate(root, "demo-app")
            self.assertFalse(gate["passed"])
            self.assertIn("soul.md", gate["incomplete"])
            self.assertIn("context/app-context.md", gate["incomplete"])

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

    def test_stage_derivation_uses_lifecycle_artifacts_and_refs(self) -> None:
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

            self.assertEqual(runtime.derive_stage(root, "demo")["stage"], "qa")
            artifacts = runtime.list_artifacts(root, "demo")
            self.assertEqual({item["kind"] for item in artifacts}, {"artifact", "ref"})

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
            app["approved_stages"] = ["intent", "research", "selection", "plan", "engineering", "qa", "kpi"]
            app["credential_requirements"] = [
                {"id": "marketing-provider", "label": "Marketing provider", "required": True, "status": "missing"}
            ]
            runtime.write_app(root, app)

            approval = runtime.dispatch_telegram_command(root, "/approve_stage demo marketing")
            self.assertFalse(approval["handled"])
            self.assertIn("credential capability", approval["text"])

            record_stage_turn(root, "demo", "marketing", artifact_path)
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
