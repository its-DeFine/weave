import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SchedulerHeartbeatContractTests(unittest.TestCase):
    def test_scheduler_schema_files_are_valid_json_objects(self) -> None:
        expected = {
            "schemas/recurring-job.schema.json": "weave/recurring-job/v0.1",
            "schemas/job-run-event.schema.json": "weave/job-run-event/v0.1",
            "schemas/owner-notification.schema.json": "weave/owner-notification/v0.1",
            "schemas/kill-switch.schema.json": "weave/kill-switch/v0.1",
        }

        for relative_path, schema_const in expected.items():
            with self.subTest(schema=relative_path):
                payload = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
                self.assertEqual(payload["type"], "object")
                self.assertEqual(payload["properties"]["schema"]["const"], schema_const)
                self.assertIn("https://json-schema.org/draft/2020-12/schema", payload["$schema"])

    def test_docs_link_the_scheduler_contract(self) -> None:
        docs_index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        contract = (ROOT / "docs/scheduler-heartbeat-contract-v0.1.md").read_text(encoding="utf-8")

        self.assertIn("scheduler-heartbeat-contract-v0.1.md", docs_index)
        self.assertIn("Trace: ATM-243", contract)
        self.assertIn("schemas/recurring-job.schema.json", contract)
        self.assertIn("docs/samples/scheduler-jobs.example.json", contract)

    def test_sample_fixtures_cover_required_recurring_job_types(self) -> None:
        fixture = json.loads((ROOT / "docs/samples/scheduler-jobs.example.json").read_text(encoding="utf-8"))
        job_types = {job["job_type"] for job in fixture["jobs"]}

        for job_type in ("marketing_engagement", "feedback_intake", "competitor_scan", "staged_implementation"):
            with self.subTest(job_type=job_type):
                self.assertIn(job_type, job_types)

    def test_external_effect_boundaries_include_high_risk_actions(self) -> None:
        job_schema = json.loads((ROOT / "schemas/recurring-job.schema.json").read_text(encoding="utf-8"))
        effects = set(job_schema["$defs"]["external_effect"]["enum"])

        for effect in ("public_send", "paid_spend", "production_write", "credential_scope_change", "destructive_change"):
            with self.subTest(effect=effect):
                self.assertIn(effect, effects)


if __name__ == "__main__":
    unittest.main()
