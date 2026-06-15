import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CapabilityBrokerContractTests(unittest.TestCase):
    def test_capability_schema_files_are_valid_json_objects(self) -> None:
        expected = {
            "schemas/capability-inventory.schema.json": "weave/capability-inventory/v0.1",
            "schemas/capability-grant.schema.json": "weave/capability-grant/v0.1",
            "schemas/capability-audit-event.schema.json": "weave/capability-audit-event/v0.1",
        }

        for relative_path, schema_const in expected.items():
            with self.subTest(schema=relative_path):
                payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
                self.assertEqual(payload["type"], "object")
                self.assertEqual(payload["properties"]["schema"]["const"], schema_const)
                self.assertIn("https://json-schema.org/draft/2020-12/schema", payload["$schema"])

    def test_docs_link_the_capability_broker_contract(self) -> None:
        docs_index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        contract = (ROOT / "docs/capability-broker-contract-v0.1.md").read_text(encoding="utf-8")

        self.assertIn("capability-broker-contract-v0.1.md", docs_index)
        self.assertIn("Trace: ATM-242", contract)
        self.assertIn("schemas/capability-inventory.schema.json", contract)
        self.assertIn("schemas/capability-grant.schema.json", contract)
        self.assertIn("schemas/capability-audit-event.schema.json", contract)

    def test_agent_visible_schemas_do_not_require_raw_credential_fields(self) -> None:
        forbidden_required_fields = {"token", "password", "private_key", "credential", "refresh_token"}

        for relative_path in (
            "schemas/capability-inventory.schema.json",
            "schemas/capability-grant.schema.json",
            "schemas/capability-audit-event.schema.json",
        ):
            with self.subTest(schema=relative_path):
                payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
                required = set(payload.get("required", []))
                self.assertTrue(required.isdisjoint(forbidden_required_fields))

    def test_grant_schema_keeps_external_effect_boundaries_explicit(self) -> None:
        grant_schema = json.loads((ROOT / "schemas/capability-grant.schema.json").read_text(encoding="utf-8"))
        effects = set(grant_schema["$defs"]["external_effect"]["enum"])

        for effect in (
            "none",
            "read_only",
            "staging_write",
            "production_write",
            "public_send",
            "paid_spend",
            "credential_scope_change",
            "destructive_change",
        ):
            with self.subTest(effect=effect):
                self.assertIn(effect, effects)


if __name__ == "__main__":
    unittest.main()
