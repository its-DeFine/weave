from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_lifecycle_artifacts.py"

spec = importlib.util.spec_from_file_location("validate_lifecycle_artifacts", SCRIPT_PATH)
assert spec is not None
validate_lifecycle_artifacts = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validate_lifecycle_artifacts
spec.loader.exec_module(validate_lifecycle_artifacts)


class ValidateLifecycleArtifactsTests(unittest.TestCase):
    def sample(self) -> dict:
        return validate_lifecycle_artifacts.load_bundle(REPO_ROOT / "docs/samples/lifecycle-artifacts.example.json")

    def test_public_sample_validates(self) -> None:
        validate_lifecycle_artifacts.validate_bundle(self.sample())

    def test_current_stage_must_exist_in_lifecycle_rows(self) -> None:
        bundle = self.sample()
        bundle["lifecycle_state"]["current_stage"] = "deployment"

        with self.assertRaisesRegex(validate_lifecycle_artifacts.ValidationError, "current_stage"):
            validate_lifecycle_artifacts.validate_bundle(bundle)

    def test_lifecycle_decision_refs_must_have_decision_cards(self) -> None:
        bundle = self.sample()
        bundle["owner_decision_cards"] = []

        with self.assertRaisesRegex(validate_lifecycle_artifacts.ValidationError, "missing decision cards"):
            validate_lifecycle_artifacts.validate_bundle(bundle)

    def test_high_risk_grant_requires_owner_approval(self) -> None:
        bundle = self.sample()
        high_risk_grant = copy.deepcopy(bundle["capability_grants"][0])
        high_risk_grant["grant_id"] = "grant-production-001"
        high_risk_grant["external_effect"] = "production_write"
        high_risk_grant["approved_by"] = "policy"
        bundle["capability_grants"].append(high_risk_grant)

        with self.assertRaisesRegex(validate_lifecycle_artifacts.ValidationError, "owner approval"):
            validate_lifecycle_artifacts.validate_bundle(bundle)

    def test_job_run_notification_refs_must_exist(self) -> None:
        bundle = self.sample()
        bundle["job_run_events"][0]["notification_refs"] = ["notification:missing-review"]

        with self.assertRaisesRegex(validate_lifecycle_artifacts.ValidationError, "missing notifications"):
            validate_lifecycle_artifacts.validate_bundle(bundle)

    def test_cli_accepts_public_sample(self) -> None:
        result = validate_lifecycle_artifacts.main(["docs/samples/lifecycle-artifacts.example.json"])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
