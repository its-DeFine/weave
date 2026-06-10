from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "packages" / "weave-tool" / "process-profiles" / "private-app-parallel-assessment.json"
SCHEMA_PATH = REPO_ROOT / "packages" / "weave-tool" / "process-profiles" / "schemas" / "operating-profile.schema.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "private_app_operating_profile_eval.py"

spec = importlib.util.spec_from_file_location("private_app_operating_profile_eval", SCRIPT_PATH)
assert spec is not None
private_app_eval = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = private_app_eval
spec.loader.exec_module(private_app_eval)

REQUIRED_FRAMEWORK_ARTIFACTS = list(private_app_eval.REQUIRED_FRAMEWORK_ARTIFACTS)
REQUIRED_SELECTED_PROFILES = set(private_app_eval.REQUIRED_SELECTED_PROFILES)


class PrivateAppOperatingProfileEvalTests(unittest.TestCase):
    def test_force_delete_output_root_refuses_unmarked_non_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "not-an-eval-root"
            output_root.mkdir()
            (output_root / "keep.txt").write_text("unrelated work\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unmarked output root"):
                private_app_eval.force_delete_output_root(output_root)

            self.assertTrue((output_root / "keep.txt").exists())

    def test_force_delete_output_root_allows_marked_harness_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "not-an-eval-root"
            output_root.mkdir()
            (output_root / private_app_eval.OUTPUT_ROOT_MARKER).write_text("marker\n", encoding="utf-8")
            (output_root / "generated.json").write_text("{}\n", encoding="utf-8")

            private_app_eval.force_delete_output_root(output_root)

            self.assertFalse(output_root.exists())

    def test_force_delete_output_root_refuses_protected_roots(self) -> None:
        with self.assertRaisesRegex(ValueError, "protected output root"):
            private_app_eval.force_delete_output_root(REPO_ROOT)

    def test_profile_contract_is_reviewable_private_first_and_gestalt_deferred(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["schema"]["const"], "weave-operating-profile/v0.2")
        self.assertEqual(profile["schema"], "weave-operating-profile/v0.2")
        self.assertEqual(profile["id"], "private-app-parallel-assessment")
        self.assertEqual(profile["trigger_mode"], "reactive")
        self.assertEqual(profile["authority_mode"], "recommend_only")
        self.assertEqual(profile["target_surface"], private_app_eval.HIGHEST_PROVEN_SURFACE)
        self.assertEqual(profile["proof_boundaries"]["highest_proven_surface"], profile["target_surface"])
        self.assertIn("live Hermes-agent lifecycle", profile["proof_boundaries"]["not_proven"])
        self.assertIn("Telegram/deployed-gateway adapter behavior", profile["proof_boundaries"]["not_proven"])
        self.assertIn("not live Hermes CLI proof", profile["non_claims"])
        self.assertIn("not Telegram or deployed gateway proof", profile["non_claims"])
        self.assertFalse(profile["private_data_policy"]["real_private_data_allowed"])
        self.assertTrue(profile["private_data_policy"]["synthetic_private_data_allowed"])
        self.assertFalse(profile["private_data_policy"]["external_send_allowed"])
        self.assertFalse(profile["evaluation"]["marketing_included"])
        self.assertEqual(profile["evaluation"]["minimum_app_count"], 10)

        framework_ids = {item["id"] for item in profile["framework_stack"]}
        self.assertEqual(
            framework_ids,
            {
                "cwa_discovery",
                "dmn_decision_table",
                "ibis_issue_map",
                "adr_decision_record",
                "premortem_review",
                "prov_ledger",
            },
        )
        self.assertNotIn("gestalt", framework_ids)
        optional_frameworks = {item["id"]: item for item in profile["optional_frameworks"]}
        self.assertEqual(optional_frameworks["gestalt"]["status"], "deferred_by_default")

        gate_ids = {item["id"] for item in profile["hard_gates"]}
        self.assertTrue(
            {
                "cwa_missing_information_gate",
                "dmn_transition_gate",
                "ibis_blocker_gate",
                "adr_decision_gate",
                "premortem_risk_gate",
                "prov_claim_gate",
            }.issubset(gate_ids)
        )
        for gate in profile["hard_gates"]:
            self.assertTrue(gate["consumes"], gate)
            self.assertTrue(gate["controls"], gate)

        role_ids = {item["id"] for item in profile["company_process"]["roles"]}
        self.assertTrue({"operator", "product_planning", "engineering", "qa", "owner_manual_feedback"}.issubset(role_ids))
        state_ids = [item["id"] for item in profile["company_process"]["lifecycle_states"]]
        self.assertEqual(
            state_ids,
            [
                "input_normalization",
                "cwa_information_assessment",
                "dmn_routing",
                "ibis_premortem_handoff",
                "engineering_execution",
                "qa_verification",
                "proof_report",
            ],
        )
        for artifact in REQUIRED_FRAMEWORK_ARTIFACTS:
            self.assertIn(artifact, profile["required_artifacts"])

    def test_parallel_private_app_eval_generates_ten_apps_and_consumed_review_gates(self) -> None:
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
            self.assertEqual(payload["schema"], "weave-private-app-operating-profile-eval-run/v0.2")
            self.assertEqual(payload["app_count"], 10)
            self.assertEqual(payload["expected_app_count"], 10)
            self.assertEqual(payload["parallel_workers"], 3)
            self.assertEqual(payload["artifact_total"], 10 * len(REQUIRED_FRAMEWORK_ARTIFACTS))
            self.assertEqual(payload["authority_mode"], "recommend_only")
            self.assertTrue(payload["marketing_excluded"])
            self.assertEqual(payload["gate_totals"]["critical_failed"], 0)
            self.assertIn("not Telegram, deployed gateway, or hosted application proof", payload["explicit_non_claims"])
            self.assertIn("live Hermes-agent lifecycle", payload["not_proven"])
            self.assertTrue((output_dir / private_app_eval.OUTPUT_ROOT_MARKER).exists())
            self.assertTrue((output_dir / "aggregate-review.json").exists())
            self.assertTrue((output_dir / "aggregate-review.md").exists())
            self.assertTrue((output_dir / "cases.jsonl").exists())
            self.assertTrue(markdown_report.exists())
            self.assertIn("Private App Operating Profile Aggregate Review", markdown_report.read_text(encoding="utf-8"))

            seen_ids = {item["app_id"] for item in payload["results"]}
            seen_names = {item["name"] for item in payload["results"]}
            self.assertEqual(len(seen_ids), 10)
            self.assertEqual(len(seen_names), 10)

            expected_gate_names = {
                "intent_frame_parseable",
                "profile_selection_parseable",
                "required_framework_stack_selected",
                "gestalt_optional_deferred",
                "cwa_private_constraints_consumed",
                "cwa_missing_information_gate",
                "dmn_local_only_routing",
                "dmn_marketing_block",
                "dmn_transition_gate",
                "ibis_local_static_preferred",
                "ibis_no_unwaived_blockers",
                "adr_accepted",
                "decision_register_covers_implementation",
                "premortem_failure_modes_classified",
                "risk_to_test_map_complete",
                "action_intent_scope_local_only",
                "action_intent_blocks_external_actions",
                "action_result_claim_limits",
                "prov_ledger_required_events",
                "prov_ledger_event_order",
                "proof_boundary_non_claims",
                "proof_boundary_not_proven",
            }

            private_domains = set()
            for item in payload["results"]:
                app_dir = output_dir / item["app_dir"]
                self.assertTrue(app_dir.exists(), item)
                for required in ["index.html", "src/app.js", "src/styles.css", "public/app-data.json", "README.md", "review.json", "review.md"]:
                    self.assertTrue((app_dir / required).exists(), required)
                app_js = (app_dir / "src" / "app.js").read_text(encoding="utf-8")
                self.assertIn("externalActionsEnabled", app_js)
                for banned in ["innerHTML", "fetch(", "XMLHttpRequest", "sendBeacon", "localStorage"]:
                    self.assertNotIn(banned, app_js)

                app_data = json.loads((app_dir / "public/app-data.json").read_text(encoding="utf-8"))
                self.assertFalse(app_data["external_actions_enabled"])
                self.assertFalse(app_data["marketing_included"])
                self.assertGreaterEqual(len(app_data["sample_data"]), 3)
                private_domains.add(app_data["private_domain"])

                assessment = json.loads((output_dir / item["report"]).read_text(encoding="utf-8"))
                self.assertTrue(assessment["passed"])
                self.assertEqual(assessment["app_id"], item["app_id"])
                self.assertEqual(assessment["score"], len(assessment["checks"]))
                self.assertFalse(any(not check["passed"] for check in assessment["checks"] if check.get("severity") != "warning"))
                self.assertEqual(len(assessment["cognitive_artifacts"]), len(REQUIRED_FRAMEWORK_ARTIFACTS))

                check_names = {check["name"] for check in assessment["checks"]}
                self.assertTrue(expected_gate_names.issubset(check_names), expected_gate_names - check_names)
                for check in assessment["checks"]:
                    if check["name"] in expected_gate_names:
                        self.assertTrue(check.get("source_artifacts"), check)

                review = json.loads((output_dir / item["review_json"]).read_text(encoding="utf-8"))
                self.assertEqual(review["schema"], "weave-private-app-case-review/v0.2")
                self.assertEqual(review["proof_surface"], private_app_eval.HIGHEST_PROVEN_SURFACE)
                self.assertFalse(review["data_boundary"]["real_private_data_allowed"])
                self.assertFalse(review["data_boundary"]["external_send_allowed"])
                self.assertGreaterEqual(len(review["artifact_manifest"]), len(REQUIRED_FRAMEWORK_ARTIFACTS))

                artifacts_dir = app_dir / "cognitive-artifacts"
                for artifact in REQUIRED_FRAMEWORK_ARTIFACTS:
                    self.assertTrue((artifacts_dir / artifact).exists(), artifact)
                profile_selection = json.loads((artifacts_dir / "profile-selection.json").read_text(encoding="utf-8"))
                self.assertEqual(profile_selection["authority_mode"], "recommend_only")
                self.assertTrue(REQUIRED_SELECTED_PROFILES.issubset(set(profile_selection["selected_profiles"])))
                self.assertNotIn("gestalt", profile_selection["selected_profiles"])
                self.assertEqual(profile_selection["optional_profiles"][0]["id"], "gestalt")
                self.assertEqual(profile_selection["optional_profiles"][0]["status"], "deferred_by_default")

            self.assertEqual(len(private_domains), 10)

    def test_framework_artifact_mutations_fail_named_review_gates_without_crashing(self) -> None:
        def mutated_checks(relative_path: str, mutator) -> dict[str, bool]:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_root = Path(tmpdir)
                scenario = private_app_eval.APP_SCENARIOS[0]
                result = private_app_eval.run_one(scenario, output_root)
                self.assertTrue(result.passed)
                app_dir = output_root / result.app_dir
                target = app_dir / relative_path
                if callable(mutator):
                    payload = json.loads(target.read_text(encoding="utf-8"))
                    target.write_text(json.dumps(mutator(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
                else:
                    target.write_text(mutator, encoding="utf-8")
                reassessed = private_app_eval.assess_app(scenario, app_dir, output_root)
                self.assertFalse(reassessed.passed, relative_path)
                return {check["name"]: check["passed"] for check in reassessed.checks}

        checks = mutated_checks("cognitive-artifacts/profile-selection.json", "{not json")
        self.assertFalse(checks["profile_selection_parseable"])

        checks = mutated_checks(
            "cognitive-artifacts/missing-information-assessment.json",
            lambda payload: {**payload, "required_missing": ["owner budget"], "blocks_engineering": True},
        )
        self.assertFalse(checks["cwa_missing_information_gate"])

        checks = mutated_checks("cognitive-artifacts/dmn-routing-table.json", "{not json")
        self.assertFalse(checks["dmn_parseable"])

        checks = mutated_checks(
            "cognitive-artifacts/ibis-issue-map.json",
            lambda payload: {**payload, "preferred_option": "hosted app", "unresolved_blocking_issues": ["deployment authorization missing"]},
        )
        self.assertFalse(checks["ibis_local_static_preferred"])
        self.assertFalse(checks["ibis_no_unwaived_blockers"])

        checks = mutated_checks(
            "cognitive-artifacts/action-intent.json",
            lambda payload: {**payload, "allowed_scope": ["write local files", "network calls"], "blocked_scope": ["deployment"]},
        )
        self.assertFalse(checks["action_intent_scope_local_only"])
        self.assertFalse(checks["action_intent_blocks_external_actions"])

        checks = mutated_checks("cognitive-artifacts/prov-ledger.jsonl", "")
        self.assertFalse(checks["prov_ledger_parseable"])

        checks = mutated_checks(
            "cognitive-artifacts/proof-boundary-report.json",
            lambda payload: {**payload, "highest_proven_surface": "live Hermes deployed gateway proof", "not_proven": []},
        )
        self.assertFalse(checks["proof_boundary_highest_surface"])
        self.assertFalse(checks["proof_boundary_not_proven"])


if __name__ == "__main__":
    unittest.main()
