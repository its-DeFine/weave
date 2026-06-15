import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LifecycleArtifactContractTests(unittest.TestCase):
    def test_core_schema_files_are_valid_json_objects(self) -> None:
        expected = {
            "schemas/lifecycle-state.schema.json": "weave/lifecycle-state/v0.1",
            "schemas/world-model.schema.json": "weave/world-model/v0.1",
            "schemas/event-ledger-entry.schema.json": "weave/event-ledger-entry/v0.1",
            "schemas/owner-decision-card.schema.json": "weave/owner-decision-card/v0.1",
        }

        for relative_path, schema_const in expected.items():
            with self.subTest(schema=relative_path):
                payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
                self.assertEqual(payload["type"], "object")
                self.assertEqual(payload["properties"]["schema"]["const"], schema_const)
                self.assertIn("https://json-schema.org/draft/2020-12/schema", payload["$schema"])

    def test_docs_link_the_lifecycle_artifact_contract(self) -> None:
        docs_index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        contract = (ROOT / "docs/lifecycle-artifact-contracts-v0.1.md").read_text(encoding="utf-8")

        self.assertIn("lifecycle-artifact-contracts-v0.1.md", docs_index)
        self.assertIn("Trace: ATM-241", contract)
        self.assertIn("schemas/lifecycle-state.schema.json", contract)
        self.assertIn("schemas/world-model.schema.json", contract)
        self.assertIn("schemas/event-ledger-entry.schema.json", contract)
        self.assertIn("schemas/owner-decision-card.schema.json", contract)

    def test_stage_vocabulary_includes_full_product_lifecycle(self) -> None:
        lifecycle_schema = json.loads((ROOT / "schemas/lifecycle-state.schema.json").read_text(encoding="utf-8"))
        stages = set(lifecycle_schema["$defs"]["stage"]["enum"])

        for stage in (
            "first_run",
            "owner_profile",
            "create_app",
            "intent",
            "research",
            "selection",
            "plan",
            "engineering",
            "qa",
            "deployment",
            "kpi",
            "marketing",
            "iteration",
            "analysis",
        ):
            with self.subTest(stage=stage):
                self.assertIn(stage, stages)


if __name__ == "__main__":
    unittest.main()
