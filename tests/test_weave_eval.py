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
