from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "weave_agent_runtime_contract.py"

spec = importlib.util.spec_from_file_location("weave_agent_runtime_contract", SCRIPT_PATH)
assert spec is not None
contract_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = contract_mod
spec.loader.exec_module(contract_mod)


class WeaveAgentRuntimeContractTests(unittest.TestCase):
    def test_hermes_contract_exposes_required_adapter_methods(self) -> None:
        contract = contract_mod.hermes_contract(
            binary={"found": True, "name": "hermes", "path": "/tmp/hermes"},
            hermes_setup_state="operator_confirmed_ready",
        )

        self.assertEqual(contract["schema"], contract_mod.CONTRACT_SCHEMA)
        self.assertEqual(contract["runtime_id"], "hermes-default")
        self.assertEqual(contract["adapter_type"], "hermes_runtime")
        self.assertEqual(contract["support_state"], "supported")
        self.assertFalse(contract["secret_payload_allowed"])
        self.assertEqual(set(contract["methods"]), set(contract_mod.REQUIRED_METHODS))
        self.assertTrue(contract["methods"]["probe"]["implemented"])
        self.assertTrue(contract["methods"]["invoke"]["implemented"])
        self.assertTrue(contract["methods"]["invoke"]["requires_live_runtime"])
        self.assertTrue(contract["methods"]["capture_turn"]["implemented"])
        self.assertTrue(contract["methods"]["post_event"]["implemented"])
        self.assertTrue(contract["methods"]["doctor"]["implemented"])
        self.assertTrue(contract["current_probe"]["binary_found"])
        self.assertTrue(contract["current_probe"]["normal_chat_ready"])

    def test_codex_contract_is_explicitly_unsupported_until_adapter_exists(self) -> None:
        contract = contract_mod.codex_contract()

        self.assertEqual(contract["runtime_id"], "codex")
        self.assertEqual(contract["support_state"], "unsupported")
        self.assertIn("No tracked Codex adapter", contract["unsupported_reason"])
        self.assertTrue(contract["current_probe"]["provider_metadata_only"])
        for method in contract_mod.REQUIRED_METHODS:
            self.assertFalse(contract["methods"][method]["implemented"], method)

    def test_local_fallback_contract_cannot_satisfy_hermes_completion_claim(self) -> None:
        contract = contract_mod.local_fallback_contract()

        self.assertEqual(contract["runtime_id"], "local-fallback")
        self.assertEqual(contract["support_state"], "fallback_contract_only")
        self.assertFalse(contract["methods"]["invoke"]["implemented"])
        self.assertIn("not equivalent", contract["claim"])

    def test_runtime_catalog_lists_supported_fallback_and_unsupported_states(self) -> None:
        catalog = contract_mod.runtime_catalog("hermes-default")

        contract_mod.validate_catalog(catalog)
        self.assertEqual(catalog["current_runtime"], "hermes-default")
        self.assertEqual(catalog["runtimes"]["hermes-default"]["support_state"], "supported_unproven")
        self.assertEqual(catalog["runtimes"]["local-fallback"]["support_state"], "fallback_contract_only")
        self.assertEqual(catalog["runtimes"]["codex"]["support_state"], "unsupported")

    def test_contract_validation_rejects_missing_methods_and_secret_like_values(self) -> None:
        contract = contract_mod.hermes_contract()
        contract["methods"].pop("doctor")

        with self.assertRaises(contract_mod.AgentRuntimeContractError):
            contract_mod.validate_contract(contract)

        unsafe_contract = contract_mod.hermes_contract()
        unsafe_contract["current_probe"]["token"] = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
        with self.assertRaises(contract_mod.AgentRuntimeContractError):
            contract_mod.validate_contract(unsafe_contract)


if __name__ == "__main__":
    unittest.main()
