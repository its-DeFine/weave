from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


weave_runtime_slice = load_module("weave_runtime_slice")
weave_prompt_library = load_module("weave_prompt_library")
weave_backend = load_module("weave_backend")


class WeavePromptOrchestrationTests(unittest.TestCase):
    def test_prompt_library_covers_full_lifecycle_with_substage_prompts(self) -> None:
        summary = weave_prompt_library.prompt_library_summary()

        self.assertEqual(summary["schema"], "weave/prompt-library-summary/v1")
        self.assertGreaterEqual(summary["stage_count"], 15)
        self.assertGreaterEqual(summary["prompt_count"], 70)
        for stage in (
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
            "completion",
        ):
            self.assertIn(stage, summary["stages"])
            self.assertTrue(summary["stages"][stage]["required_outputs"])
            self.assertTrue(summary["stages"][stage]["subprompts"])

    def test_prompt_packet_attaches_global_prelude_context_feedback_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-state"
            weave_runtime_slice.create_app(root, "launch-studio", "Launch Studio")
            feedback = weave_prompt_library.build_feedback(
                app_id="launch-studio",
                stage="engineering",
                target_type="file",
                target_ref="apps/launch-studio/repo/primary/src/app.js",
                owner_text="Move launch risks above secondary metrics.",
                feedback_class="correction",
            )

            packet = weave_prompt_library.build_prompt_packet(
                root=root,
                app_id="launch-studio",
                stage="engineering",
                substage="file_feedback",
                latest_owner_message="Please fix the file-specific issue.",
                input_refs=["lifecycle/04-plan/artifacts/engineering-plan.md"],
                selected_context_refs=["worldmodel.md"],
                owner_profile_summary="Owner prefers direct proof-backed updates.",
                world_model_summary="Launch cockpit is the selected product.",
                feedback=feedback,
            )

            self.assertEqual(packet["schema"], weave_prompt_library.PROMPT_PACKET_SCHEMA)
            self.assertEqual(packet["stage"], "engineering")
            self.assertEqual(packet["substage"], "file_feedback")
            self.assertEqual(packet["feedback"]["target_type"], "file")
            self.assertIn("executor-manifest", packet["required_outputs"])
            self.assertIn("packet_ref", packet)
            rendered_path = root / packet["rendered_prompt_ref"]
            rendered = rendered_path.read_text(encoding="utf-8")
            self.assertIn("WEAVE Global Agent Prelude", rendered)
            self.assertIn("Move launch risks above secondary metrics", rendered)
            self.assertIn("Required Outputs", rendered)

    def test_backend_dispatch_creates_app_projection_and_revision_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-state"
            create_result = weave_backend.dispatch(root, "workspace.create_app", app_id="demo", app_name="Demo")
            self.assertTrue(create_result["ok"], create_result)
            self.assertEqual(create_result["projection"]["app"]["current_stage"], "intent")
            self.assertTrue((root / "apps" / "demo" / "worldmodel.json").exists())

            feedback_result = weave_backend.dispatch(
                root,
                "feedback.record",
                app_id="demo",
                app_name="Demo",
                payload={
                    "stage": "intent",
                    "owner_text": "Add deployment region and founder audience.",
                    "feedback_class": "new_constraint",
                },
            )

            self.assertTrue(feedback_result["ok"], feedback_result)
            self.assertTrue(feedback_result["artifacts_written"])
            prompt_ref = feedback_result["artifacts_written"][0]
            packet = json.loads((root / prompt_ref).read_text(encoding="utf-8"))
            self.assertEqual(packet["stage"], "intent")
            self.assertEqual(packet["substage"], "revise")
            self.assertEqual(packet["feedback"]["feedback_class"], "new_constraint")
            self.assertGreaterEqual(len(feedback_result["projection"]["review_queue"]["items"]), 2)

    def test_backend_lifecycle_commands_move_intent_to_research(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-state"
            self.assertTrue(weave_backend.dispatch(root, "workspace.create_app", app_id="flow", app_name="Flow")["ok"])
            self.assertTrue(
                weave_backend.dispatch(
                    root,
                    "foundation.save",
                    app_id="flow",
                    app_name="Flow",
                    payload={
                        "owner_experience": "operator",
                        "coworker_style": "direct, proof-backed",
                        "intent": "Build a launch cockpit for founders.",
                        "target_user": "founder",
                    },
                )["ok"]
            )
            submit = weave_backend.dispatch(
                root,
                "stage.submit",
                app_id="flow",
                app_name="Flow",
                payload={
                    "stage": "intent",
                    "owner_text": "Build a launch cockpit for founders.",
                    "agent_text": "Intent proof is ready.",
                    "artifact_body": "Goal: launch cockpit. Target user: founder. Success metric: owner can inspect risks. Boundary: no live effects.",
                },
            )
            self.assertTrue(submit["ok"], submit)
            self.assertTrue(submit["artifacts_written"])

            evaluate = weave_backend.dispatch(root, "stage.evaluate", app_id="flow", app_name="Flow", payload={"stage": "intent"})
            self.assertTrue(evaluate["ok"], evaluate)

            approve = weave_backend.dispatch(root, "stage.approve", app_id="flow", app_name="Flow", payload={"stage": "intent"})
            self.assertTrue(approve["ok"], approve)

            advance = weave_backend.dispatch(root, "stage.advance", app_id="flow", app_name="Flow")
            self.assertTrue(advance["ok"], advance)
            self.assertEqual(advance["projection"]["app"]["current_stage"], "research")

    def test_qa_start_prompt_requires_engineering_and_qa_context(self) -> None:
        template = weave_prompt_library.prompt_template("qa", "start")

        self.assertIn("source-manifest", template.required_context)
        self.assertIn("executor-manifest", template.required_context)
        self.assertIn("qa-plan", template.required_context)
        self.assertIn("qa-result", template.required_outputs)

    def test_backend_executor_records_missing_codex_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-state"
            weave_backend.dispatch(root, "workspace.create_app", app_id="exec-missing", app_name="Exec Missing")
            with mock.patch.object(weave_backend.shutil, "which", return_value=None):
                result = weave_backend.dispatch(
                    root,
                    "executor.run",
                    app_id="exec-missing",
                    app_name="Exec Missing",
                    payload={"owner_message": "Build the approved app."},
                )

            self.assertFalse(result["ok"])
            self.assertIn("codex_cli_missing", result["blocked_by"])
            manifest_ref = next(ref for ref in result["artifacts_written"] if ref.endswith("executor-manifest.json"))
            manifest = json.loads((root / manifest_ref).read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "failed")
            self.assertFalse(manifest["live_agent_execution"])
            self.assertFalse(manifest["secret_value_printed"])

    def test_backend_executor_success_collects_source_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-state"
            weave_backend.dispatch(root, "workspace.create_app", app_id="exec-ok", app_name="Exec OK")

            def fake_run(command, **_kwargs):
                repo = Path(command[-2])
                (repo / "index.html").write_text("<main><h1>Exec OK</h1></main>\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="done\n", stderr="")

            with mock.patch.object(weave_backend.shutil, "which", return_value="codex"), mock.patch.object(
                weave_backend.subprocess,
                "run",
                side_effect=fake_run,
            ):
                result = weave_backend.dispatch(
                    root,
                    "executor.run",
                    app_id="exec-ok",
                    app_name="Exec OK",
                    payload={"owner_message": "Build the approved app."},
                )

            self.assertTrue(result["ok"], result)
            executor_ref = next(ref for ref in result["artifacts_written"] if ref.endswith("executor-manifest.json"))
            source_ref = next(ref for ref in result["artifacts_written"] if ref.endswith("source-manifest.json"))
            executor = json.loads((root / executor_ref).read_text(encoding="utf-8"))
            source = json.loads((root / source_ref).read_text(encoding="utf-8"))
            self.assertEqual(executor["status"], "passed")
            self.assertTrue(executor["live_agent_execution"])
            self.assertEqual(source["file_count"], 1)


if __name__ == "__main__":
    unittest.main()
