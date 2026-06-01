from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import weave_runtime_slice as runtime  # noqa: E402


def fill(path: Path, title: str) -> None:
    path.write_text(
        f"# {title}\n\nStatus: complete\n\nRequired facts are recorded for this local test.\n",
        encoding="utf-8",
    )


class WeaveRuntimeSliceTests(unittest.TestCase):
    def test_setup_creates_root_registry_templates_and_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            result = runtime.setup_weave_root(root)

            self.assertEqual(result["schema"], runtime.ROOT_SCHEMA)
            self.assertTrue((root / "apps" / "registry.json").exists())
            self.assertTrue((root / "artifacts" / "general" / "soul.md").exists())
            self.assertTrue((root / "artifacts" / "general" / "owner-profile.md").exists())
            self.assertTrue((root / "runtime" / "tokens" / "local-api-token").exists())
            self.assertTrue((root / "runtime" / "profiles" / "autonomy-policy.json").exists())
            self.assertEqual(result["autonomy"]["mode"], "yolo")
            self.assertTrue(result["autonomy"]["llm_must_request_owner_authorization_for_hard_gates"])
            self.assertEqual(runtime.load_registry(root)["apps"], [])

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
            registry = runtime.load_registry(root)
            self.assertEqual(registry["apps"][0]["app_id"], "demo-app")
            gate = runtime.foundation_gate(root, "demo-app")
            self.assertFalse(gate["passed"])
            self.assertIn("soul.md", gate["incomplete"])
            self.assertIn("context/app-context.md", gate["incomplete"])

    def test_foundation_gate_passes_after_required_context_is_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            fill(root / "artifacts" / "general" / "soul.md", "Hermes Soul")
            fill(root / "artifacts" / "general" / "owner-profile.md", "Owner Profile")
            fill(root / "apps" / "demo" / "context" / "app-context.md", "App Context")
            fill(root / "apps" / "demo" / "inventory" / "app-inventory.md", "App Inventory")
            fill(root / "apps" / "demo" / "contract" / "gestaltian-contract.md", "Gestaltian Contract")

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
            self.assertIn("Communication channel: Telegram", agents)
            soul = Path(result["soul_path"]).read_text(encoding="utf-8")
            self.assertIn("WEAVE Gateway Soul Bootstrap", soul)
            context = Path(result["context_path"]).read_text(encoding="utf-8")
            self.assertIn('"required_before_app_work": true', context)
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

    def test_stage_derivation_uses_lifecycle_artifacts_and_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.create_app(root, "demo", "Demo")
            contract_artifact = root / "apps" / "demo" / "lifecycle" / "03-contract" / "artifacts" / "contract.md"
            contract_artifact.write_text("# Contract\n", encoding="utf-8")

            self.assertEqual(runtime.derive_stage(root, "demo")["stage"], "contract")

            qa_ref = root / "apps" / "demo" / "lifecycle" / "07-qa" / "refs" / "contract-ref.json"
            qa_ref.write_text(
                '{"schema":"weave-artifact-ref/v0.1","canonical_path":"apps/demo/lifecycle/03-contract/artifacts/contract.md"}\n',
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
            self.assertEqual(status["payload"]["app_count"], 1)
            self.assertEqual(status["payload"]["blocked_apps"], ["demo"])
            self.assertEqual(status["payload"]["autonomy"]["mode"], "yolo")

            autonomy = runtime.dispatch_telegram_command(root, "/autonomy")
            self.assertIn("mode: yolo", autonomy["text"])
            self.assertIn("hard_gates:", autonomy["text"])
            self.assertTrue(autonomy["payload"]["autonomy"]["llm_must_request_owner_authorization_for_hard_gates"])

            apps = runtime.dispatch_telegram_command(root, "/apps")
            self.assertIn("Demo (demo)", apps["text"])
            self.assertEqual(apps["payload"]["apps"][0]["stage"], "intent")

            app = runtime.dispatch_telegram_command(root, "/app demo")
            self.assertIn("foundation: blocking", app["text"])
            self.assertIn("foundation_gate", app["payload"])

            blockers = runtime.dispatch_telegram_command(root, "/blockers")
            self.assertIn("foundation", blockers["text"])

            changes = runtime.dispatch_telegram_command(root, "/changes demo")
            self.assertIn("window", changes["text"])

            next_action = runtime.dispatch_telegram_command(root, "/next")
            self.assertIn("foundation onboarding", next_action["text"])

            help_response = runtime.dispatch_telegram_command(root, "/help")
            self.assertIn("/status", help_response["payload"]["commands"])

            passthrough = runtime.dispatch_telegram_command(root, "normal Hermes chat")
            self.assertFalse(passthrough["handled"])
            self.assertEqual(passthrough["error"], "not_slash_command")

    def test_rest_dispatch_exposes_telegram_command_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            runtime.setup_weave_root(root)

            status, response = runtime.dispatch_rest(root, "GET", "/telegram/commands")

            self.assertEqual(status, 200)
            self.assertTrue(response["deterministic"])
            self.assertFalse(response["llm_used"])
            self.assertIn("/apps", response["commands"])


if __name__ == "__main__":
    unittest.main()
