from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "packages" / "weave-tool" / "process-profiles" / "private-app-parallel-assessment.json"
SCHEMA_PATH = REPO_ROOT / "packages" / "weave-tool" / "process-profiles" / "schemas" / "operating-profile.schema.json"
REQUIRED_FRAMEWORK_ARTIFACTS = [
    "intent-frame.json",
    "profile-selection.json",
    "cwa-work-domain.json",
    "dmn-decision-table.json",
    "ibis-map.json",
    "adr-0001-local-private-first.md",
    "action-intent.json",
    "action-result.json",
    "prov-ledger.jsonl",
]


class PrivateAppOperatingProfileEvalTests(unittest.TestCase):
    def test_profile_contract_is_reviewable_and_private_first(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["schema"]["const"], "weave-operating-profile/v0.1")
        self.assertEqual(profile["schema"], "weave-operating-profile/v0.1")
        self.assertEqual(profile["id"], "private-app-parallel-assessment")
        self.assertEqual(profile["trigger_mode"], "reactive")
        self.assertEqual(profile["authority_mode"], "recommend_only")
        self.assertFalse(profile["private_data_policy"]["real_private_data_allowed"])
        self.assertTrue(profile["private_data_policy"]["synthetic_private_data_allowed"])
        self.assertFalse(profile["private_data_policy"]["external_send_allowed"])
        self.assertFalse(profile["evaluation"]["marketing_included"])
        framework_ids = {item["id"] for item in profile["framework_stack"]}
        self.assertEqual(
            framework_ids,
            {
                "gestalt",
                "cwa_discovery",
                "dmn_decision_table",
                "ibis_issue_map",
                "adr_decision_record",
                "prov_ledger",
            },
        )
        for artifact in REQUIRED_FRAMEWORK_ARTIFACTS:
            self.assertIn(artifact, profile["required_artifacts"])

    def test_parallel_private_app_eval_generates_apps_and_cognitive_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            output_dir = base / "private-app-evals"
            markdown_report = base / "private-app-evals.md"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/private_app_operating_profile_eval.py",
                    "--output-dir",
                    str(output_dir),
                    "--report-out",
                    str(markdown_report),
                    "--parallel",
                    "3",
                    "--force",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads((output_dir / "aggregate-report.json").read_text(encoding="utf-8"))

            self.assertTrue(payload["passed"])
            self.assertEqual(payload["schema"], "weave-private-app-operating-profile-eval-run/v0.1")
            self.assertEqual(payload["app_count"], 6)
            self.assertEqual(payload["parallel_workers"], 3)
            self.assertEqual(payload["artifact_total"], 54)
            self.assertEqual(payload["authority_mode"], "recommend_only")
            self.assertTrue(payload["marketing_excluded"])
            self.assertIn("not Telegram, deployed gateway, or hosted application proof", payload["explicit_non_claims"])
            self.assertTrue(markdown_report.exists())
            self.assertIn("Private App Operating Profile Evaluation", markdown_report.read_text(encoding="utf-8"))

            for item in payload["results"]:
                app_dir = output_dir / item["app_dir"]
                self.assertTrue(app_dir.exists(), item)
                self.assertTrue((app_dir / "index.html").exists())
                app_js = (app_dir / "src" / "app.js").read_text(encoding="utf-8")
                self.assertIn("externalActionsEnabled", app_js)
                self.assertNotIn("innerHTML", app_js)
                self.assertNotIn("fetch(", app_js)

                assessment = json.loads((output_dir / item["report"]).read_text(encoding="utf-8"))
                self.assertTrue(assessment["passed"])
                self.assertEqual(assessment["app_id"], item["app_id"])
                self.assertEqual(assessment["score"], len(assessment["checks"]))
                self.assertFalse(any(not check["passed"] for check in assessment["checks"]))
                self.assertEqual(len(assessment["cognitive_artifacts"]), len(REQUIRED_FRAMEWORK_ARTIFACTS))

                artifacts_dir = app_dir / "cognitive-artifacts"
                for artifact in REQUIRED_FRAMEWORK_ARTIFACTS:
                    self.assertTrue((artifacts_dir / artifact).exists(), artifact)
                profile_selection = json.loads((artifacts_dir / "profile-selection.json").read_text(encoding="utf-8"))
                self.assertEqual(profile_selection["authority_mode"], "recommend_only")
                self.assertIn("cwa_discovery", profile_selection["selected_profiles"])
                action_intent = json.loads((artifacts_dir / "action-intent.json").read_text(encoding="utf-8"))
                self.assertIn("network calls", action_intent["blocked_scope"])
                ledger_lines = (artifacts_dir / "prov-ledger.jsonl").read_text(encoding="utf-8").splitlines()
                self.assertGreaterEqual(len(ledger_lines), 5)


if __name__ == "__main__":
    unittest.main()
