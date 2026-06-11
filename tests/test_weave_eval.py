from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = REPO_ROOT / "scripts" / "weave_eval.py"

spec = importlib.util.spec_from_file_location("weave_eval", EVAL_PATH)
assert spec is not None
weave_eval = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = weave_eval
spec.loader.exec_module(weave_eval)


class WeaveEvalTests(unittest.TestCase):
    def test_lists_lifecycle_and_release_contracts(self) -> None:
        output = io.StringIO()
        rc = weave_eval.main(["--list"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0, text)
        self.assertIn("intent", text)
        self.assertIn("engineering", text)
        self.assertIn("release-readiness", text)

    def test_engineering_eval_without_review_requests_agent_review(self) -> None:
        output = io.StringIO()
        rc = weave_eval.main(["engineering"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0, text)
        self.assertIn("stage: Engineering", text)
        self.assertIn("unit_tests_pass: not_run", text)
        self.assertIn("decision: needs_agent_review", text)
        self.assertIn("rubric review missing", text)

    def test_review_template_contains_all_rubric_dimensions(self) -> None:
        output = io.StringIO()
        rc = weave_eval.main(["release-readiness", "--review-template"], output=output)
        self.assertEqual(rc, 0, output.getvalue())
        template = json.loads(output.getvalue())
        self.assertEqual(template["stage"], "Release Readiness")
        self.assertIn("operator_ux", template["scores"])
        self.assertIn("runtime_safety", template["scores"])
        self.assertEqual(template["scores"]["operator_ux"]["evidence"], [])

    def test_custom_contract_accepts_evidence_bound_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract = {
                "schema": "weave.lifecycle-eval/v0.1",
                "slug": "mini",
                "stage": "Mini",
                "requires_review": True,
                "require_evidence_for_scores": True,
                "advance_min_score_percent": 80,
                "hard_gates": [],
                "rubric": [
                    {"id": "correctness", "max_score": 4, "question": "works?"},
                    {"id": "evidence", "max_score": 4, "question": "proved?"},
                ],
            }
            review = {
                "schema": "weave.eval-review/v0.1",
                "stage": "Mini",
                "artifact": "current",
                "scores": {
                    "correctness": {"score": 4, "evidence": ["unit-test: ok"], "notes": ""},
                    "evidence": {"score": 3, "evidence": ["smoke: ok"], "notes": ""},
                },
            }
            contract_path = root / "contract.yaml"
            review_path = root / "review.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            review_path.write_text(json.dumps(review), encoding="utf-8")

            output = io.StringIO()
            rc = weave_eval.main(["--contract-file", str(contract_path), "--review-file", str(review_path)], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("decision: advance", text)
            self.assertIn("score: 7/8", text)

    def test_review_without_evidence_cannot_advance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract = {
                "schema": "weave.lifecycle-eval/v0.1",
                "slug": "mini",
                "stage": "Mini",
                "requires_review": True,
                "require_evidence_for_scores": True,
                "advance_min_score_percent": 80,
                "hard_gates": [],
                "rubric": [{"id": "correctness", "max_score": 4, "question": "works?"}],
            }
            review = {
                "schema": "weave.eval-review/v0.1",
                "stage": "Mini",
                "artifact": "current",
                "scores": {"correctness": {"score": 4, "evidence": [], "notes": "unsupported"}},
            }
            contract_path = root / "contract.yaml"
            review_path = root / "review.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            review_path.write_text(json.dumps(review), encoding="utf-8")

            output = io.StringIO()
            rc = weave_eval.main(["--contract-file", str(contract_path), "--review-file", str(review_path), "--strict"], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 1, text)
            self.assertIn("decision: revise", text)
            self.assertIn("rubric evidence missing: correctness", text)

    def test_command_hard_gate_runs_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract = {
                "schema": "weave.lifecycle-eval/v0.1",
                "slug": "gate-mini",
                "stage": "Gate Mini",
                "requires_review": False,
                "advance_min_score_percent": 80,
                "hard_gates": [
                    {
                        "id": "python_command_passes",
                        "kind": "command",
                        "command": f"{sys.executable} -c \"print('gate ok')\"",
                        "timeout_seconds": 30,
                    }
                ],
                "rubric": [],
            }
            contract_path = root / "contract.yaml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            output = io.StringIO()
            rc = weave_eval.main(["--contract-file", str(contract_path), "--run-gates", "--strict"], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("python_command_passes: passed", text)
            self.assertIn("gate ok", text)
            self.assertIn("decision: advance", text)

    def test_command_hard_gate_sets_nested_gate_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract = {
                "schema": "weave.lifecycle-eval/v0.1",
                "slug": "gate-depth-mini",
                "stage": "Gate Depth Mini",
                "requires_review": False,
                "advance_min_score_percent": 80,
                "hard_gates": [
                    {
                        "id": "gate_depth_visible",
                        "kind": "command",
                        "command": (
                            f"{sys.executable} -c \"import os; "
                            "raise SystemExit(0 if int(os.environ.get('WEAVE_EVAL_GATE_DEPTH', '0')) >= 1 else 4)\""
                        ),
                        "timeout_seconds": 30,
                    }
                ],
                "rubric": [],
            }
            contract_path = root / "contract.yaml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            output = io.StringIO()
            rc = weave_eval.main(["--contract-file", str(contract_path), "--run-gates", "--strict"], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("gate_depth_visible: passed", text)
            self.assertIn("decision: advance", text)

    def test_redacted_command_gate_suppresses_success_output_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            proof_path = root / "proof-output.txt"
            proof_path.write_text("private proof boundary\n", encoding="utf-8")
            contract = {
                "schema": "weave.lifecycle-eval/v0.1",
                "slug": "redacted-gate-mini",
                "stage": "Redacted Gate Mini",
                "requires_review": False,
                "advance_min_score_percent": 80,
                "hard_gates": [
                    {
                        "id": "redacted_python_command",
                        "kind": "command",
                        "command": (
                            f"{sys.executable} -c \"from pathlib import Path; "
                            f"print(Path({str(proof_path)!r}).read_text().strip())\""
                        ),
                        "timeout_seconds": 30,
                        "redact_output": True,
                    }
                ],
                "rubric": [],
            }
            contract_path = root / "contract.yaml"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            output = io.StringIO()
            rc = weave_eval.main(
                ["--contract-file", str(contract_path), "--run-gates", "--strict", "--json"],
                output=output,
            )
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            payload = json.loads(text)
            gate = payload["hard_gates"][0]
            self.assertEqual(gate["status"], "passed")
            self.assertEqual(gate["output_excerpt"], "[redacted by eval contract]")
            self.assertNotIn("private proof boundary", text)

    def test_command_hard_gate_requires_shell_run_even_with_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            contract = {
                "schema": "weave.lifecycle-eval/v0.1",
                "slug": "evidence-gate-mini",
                "stage": "Evidence Gate Mini",
                "requires_review": False,
                "advance_min_score_percent": 80,
                "hard_gates": [
                    {
                        "id": "external_ci_passed",
                        "kind": "command",
                        "command": f"{sys.executable} -c \"raise SystemExit(99)\"",
                        "timeout_seconds": 30,
                    }
                ],
                "rubric": [],
            }
            review = {
                "schema": "weave.eval-review/v0.1",
                "stage": "Evidence Gate Mini",
                "artifact": "current",
                "hard_gates": {
                    "external_ci_passed": {
                        "passed": True,
                        "evidence": ["ci-run: ok"],
                        "notes": "validated on the attached target-surface proof",
                    }
                },
            }
            contract_path = root / "contract.yaml"
            review_path = root / "review.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            review_path.write_text(json.dumps(review), encoding="utf-8")

            output = io.StringIO()
            rc = weave_eval.main(["--contract-file", str(contract_path), "--review-file", str(review_path), "--strict"], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 1, text)
            self.assertIn("external_ci_passed: not_run", text)
            self.assertIn("rerun with --run-gates", text)
            self.assertIn("decision: needs_gate_execution", text)

    def test_manual_gate_review_passed_must_be_strict_boolean(self) -> None:
        contract = {
            "schema": "weave.lifecycle-eval/v0.1",
            "slug": "manual-mini",
            "stage": "Manual Mini",
            "requires_review": True,
            "hard_gates": [{"id": "operator_signoff", "kind": "manual", "required": True}],
            "rubric": [],
        }

        false_string = weave_eval.evaluate_gates(
            contract,
            run_gates=False,
            repo_root=REPO_ROOT,
            review={"hard_gates": {"operator_signoff": {"passed": "false", "evidence": ["proof.md"]}}},
        )[0]
        self.assertEqual(false_string.status, "failed")
        self.assertFalse(false_string.passed)
        self.assertIn("boolean", false_string.detail)

        unresolved = weave_eval.evaluate_gates(
            contract,
            run_gates=False,
            repo_root=REPO_ROOT,
            review={"hard_gates": {"operator_signoff": {"passed": None, "evidence": []}}},
        )[0]
        self.assertEqual(unresolved.status, "manual")
        self.assertIsNone(unresolved.passed)

        missing_evidence = weave_eval.evaluate_gates(
            contract,
            run_gates=False,
            repo_root=REPO_ROOT,
            review={"hard_gates": {"operator_signoff": {"passed": True, "evidence": []}}},
        )[0]
        self.assertEqual(missing_evidence.status, "failed")
        self.assertFalse(missing_evidence.passed)
        self.assertIn("without evidence", missing_evidence.detail)

        null_evidence = weave_eval.evaluate_gates(
            contract,
            run_gates=False,
            repo_root=REPO_ROOT,
            review={"hard_gates": {"operator_signoff": {"passed": True, "evidence": [None]}}},
        )[0]
        self.assertEqual(null_evidence.status, "failed")
        self.assertFalse(null_evidence.passed)
        self.assertIn("without evidence", null_evidence.detail)

    def test_rubric_evidence_must_be_non_empty_strings(self) -> None:
        contract = {
            "schema": "weave.lifecycle-eval/v0.1",
            "slug": "rubric-mini",
            "stage": "Rubric Mini",
            "requires_review": True,
            "require_evidence_for_scores": True,
            "rubric": [{"id": "correctness", "max_score": 4}],
        }
        score = weave_eval.score_review(
            contract,
            {
                "schema": "weave.eval-review/v0.1",
                "stage": "Rubric Mini",
                "scores": {"correctness": {"score": 4, "evidence": [None], "notes": "not valid evidence"}},
            },
        )

        self.assertEqual(score["status"], "incomplete")
        self.assertEqual(score["evidence_gaps"], ["correctness"])
        self.assertEqual(score["dimensions"][0]["evidence"], [])

    def test_review_artifact_must_bind_to_concrete_evaluated_artifact(self) -> None:
        contract = {
            "schema": "weave.lifecycle-eval/v0.1",
            "slug": "mini",
            "stage": "Mini",
            "rubric": [],
        }
        with self.assertRaisesRegex(weave_eval.EvalError, "review artifact is required"):
            weave_eval.validate_review_binding(
                contract,
                {"schema": "weave.eval-review/v0.1", "stage": "Mini", "artifact": "", "scores": {}},
                artifact="apps/demo/lifecycle/01-intent/artifacts/intent.md",
            )
        with self.assertRaisesRegex(weave_eval.EvalError, "does not match evaluated artifact"):
            weave_eval.validate_review_binding(
                contract,
                {"schema": "weave.eval-review/v0.1", "stage": "Mini", "artifact": "other.md", "scores": {}},
                artifact="apps/demo/lifecycle/01-intent/artifacts/intent.md",
            )

        with self.assertRaisesRegex(weave_eval.EvalError, "must not be a placeholder"):
            weave_eval.validate_review_binding(
                contract,
                {
                    "schema": "weave.eval-review/v0.1",
                    "stage": "Mini",
                    "artifact": "describe artifact or path",
                    "scores": {},
                },
                artifact="current",
            )


    def test_kpi_alias_loads_kpi_setup_contract(self) -> None:
        output = io.StringIO()
        rc = weave_eval.main(["kpi", "--json"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0, text)
        payload = json.loads(text)
        self.assertEqual(payload["slug"], "kpi-setup")
        self.assertEqual(payload["stage"], "KPI Setup")

    def test_review_stage_must_match_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            review_path = Path(tmpdir) / "wrong-stage-review.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "weave.eval-review/v0.1",
                        "stage": "Engineering",
                        "scores": {},
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()
            rc = weave_eval.main(["release-readiness", "--review-file", str(review_path)], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 1)
            self.assertIn("does not match contract stage", text)


if __name__ == "__main__":
    unittest.main()
