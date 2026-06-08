from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import live_hermes_lifecycle_qa as live_qa  # noqa: E402
import weave_runtime_slice as runtime  # noqa: E402


class LiveHermesLifecycleQaEvidenceTests(unittest.TestCase):
    def test_research_selection_and_stage_contract_artifacts_are_first_class_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            app_repo = root / "apps" / live_qa.APP_ID / "repo" / "primary"
            live_qa.setup_clean_runtime(root, "gpt-5.5", "codex", "xhigh")

            refs, evidence, prompt_context = live_qa.prepare_stage_review_artifacts(root, "research", app_repo)

            ref_paths = {ref["path"] for ref in refs}
            self.assertIn(f"apps/{live_qa.APP_ID}/lifecycle/02-research/refs/stage-contract.md", ref_paths)
            self.assertIn(f"apps/{live_qa.APP_ID}/lifecycle/02-research/artifacts/research-source-log.json", ref_paths)
            self.assertIn(f"apps/{live_qa.APP_ID}/lifecycle/02-research/artifacts/research-synthesis.md", ref_paths)
            self.assertIn("Stage Contract", prompt_context)
            self.assertIn("research_evidence", evidence)
            gate = runtime.stage_gate_status(root, live_qa.APP_ID, "research")
            self.assertTrue(gate["proof_artifact_refs"])

            selection_refs, selection_evidence, _ = live_qa.prepare_stage_review_artifacts(root, "selection", app_repo)
            selection_paths = {ref["path"] for ref in selection_refs}
            self.assertIn(f"apps/{live_qa.APP_ID}/lifecycle/03-selection/artifacts/selection-matrix.json", selection_paths)
            self.assertEqual(selection_evidence["selection_evidence"]["selection_matrix"]["selected_wedge"], "playable-memory-card-slice")

    def test_implementation_outputs_and_localhost_proof_link_actual_product_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            app_repo = root / "apps" / live_qa.APP_ID / "repo" / "primary"
            live_qa.setup_clean_runtime(root, "gpt-5.5", "codex", "xhigh")
            app_repo.mkdir(parents=True, exist_ok=True)
            (app_repo / "index.html").write_text("<button id='next'>Next</button><script src='app.js'></script><link rel='stylesheet' href='styles.css'>\n", encoding="utf-8")
            (app_repo / "styles.css").write_text("body{font-family:sans-serif}.paid[disabled]{opacity:.5}\n", encoding="utf-8")
            (app_repo / "app.js").write_text("const memory=[]; function exportState(){return JSON.stringify({memory});}\n", encoding="utf-8")
            (app_repo / "README.md").write_text("# Lantern Archive\n\nExport is local. Paid pack controls remain disabled. Import is out of scope.\n", encoding="utf-8")

            verification = live_qa.verify_engineering_files(app_repo)
            implementation_refs, implementation_index = live_qa.write_implementation_output_artifacts(
                root,
                app_repo,
                generated_files={},
                verification=verification,
            )
            self.assertTrue(verification["passed"])
            self.assertIn("source_artifact_refs", implementation_index)
            self.assertTrue(any(ref.get("kind") == "product_source" for ref in implementation_refs))
            self.assertTrue(any(ref["path"].endswith("repo/primary/index.html") for ref in implementation_refs))

            localhost = live_qa.run_localhost_smoke(app_repo)
            self.assertTrue(localhost["passed"])
            qa_refs, qa_artifacts = live_qa.write_qa_proof_artifacts(root, app_repo, {"passed": True}, localhost)
            self.assertTrue(qa_artifacts["localhost_proof"]["passed"])
            self.assertTrue(any(ref.get("kind") == "localhost_proof" for ref in qa_refs))
            self.assertTrue((root / f"apps/{live_qa.APP_ID}/lifecycle/06-qa/artifacts/localhost-proof.md").exists())

    def test_rejects_agent_summary_file_generation_and_repairs_with_deterministic_file(self) -> None:
        summary_result = {
            "reply": "⚠️  Reached maximum iterations (2). Requesting summary...\nI inspected files and did not make changes.",
            "stdout_sha256": "sha256:summary",
            "session_id": "summary-session",
            "elapsed_seconds": 1.0,
        }
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch(
            "live_hermes_lifecycle_qa.run_hermes", return_value=summary_result
        ):
            app_repo = Path(tmpdir)
            content, metadata = live_qa.generate_file_with_repair(
                hermes_bin=Path("/tmp/hermes"),
                file_name="app.js",
                app_repo=app_repo,
                model="gpt-5.5",
                provider="codex",
                max_turns=2,
                timeout=1,
                yolo=True,
            )
        self.assertNotIn("Reached maximum iterations", content)
        self.assertIn("localStorage", content)
        self.assertEqual(metadata["source"], "deterministic_runtime_repair_after_live_hermes_generation_rejected")
        self.assertEqual(len(metadata["repair_attempts"]), 2)
        self.assertTrue(all(not attempt["accepted"] for attempt in metadata["repair_attempts"]))

    def test_node_checker_abort_without_stderr_is_environment_warning_not_app_failure(self) -> None:
        with mock.patch(
            "live_hermes_lifecycle_qa.subprocess.run",
            return_value=subprocess.CompletedProcess(["node"], -6, stdout="", stderr=""),
        ):
            status = live_qa.javascript_syntax_status(Path("/tmp/app-repo"))
        self.assertTrue(status["passed"])
        self.assertIn("checker_environment_warning", status)
        self.assertFalse(status["syntax_error_reported"])

        with mock.patch(
            "live_hermes_lifecycle_qa.subprocess.run",
            return_value=subprocess.CompletedProcess(["node"], 1, stdout="", stderr="SyntaxError: Unexpected token"),
        ):
            syntax_error_status = live_qa.javascript_syntax_status(Path("/tmp/app-repo"))
        self.assertFalse(syntax_error_status["passed"])
        self.assertNotIn("checker_environment_warning", syntax_error_status)


if __name__ == "__main__":
    unittest.main()
