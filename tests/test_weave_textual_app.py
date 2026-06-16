from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import unittest
from argparse import Namespace
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


weave_textual_app = load_module("weave_textual_app")


async def wait_for_idle(app, pilot, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while app.activity.get("state") == "running" and time.time() < deadline:
        await pilot.pause(0.05)
    if app.activity.get("state") == "running":
        raise AssertionError("Textual app action did not leave running state")


class WeaveTextualUtilityTests(unittest.TestCase):
    def test_safe_preview_blocks_outside_refs_and_truncates_inside_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "state"
            root.mkdir()
            inside = root / "artifact.md"
            inside.write_text("a" * 2000, encoding="utf-8")

            preview = weave_textual_app.safe_preview(root, "artifact.md", limit=30)

            self.assertIn("preview truncated", preview)
            self.assertIn("outside the WEAVE root", weave_textual_app.safe_preview(root, "../outside.md"))
            self.assertIn("file is missing", weave_textual_app.safe_preview(root, "missing.md"))


@unittest.skipUnless(weave_textual_app.textual_available(), "Textual dependency is not installed")
class WeaveTextualAppTests(unittest.IsolatedAsyncioTestCase):
    async def test_textual_app_creates_app_and_prompt_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = Namespace(
                weave_root=Path(tmpdir) / "weave-state",
                app_id="textual-demo",
                app_name="Textual Demo",
                owner_experience="operator",
                coworker_style="direct, proof-backed",
                intent="Build a Textual proof cockpit.",
                target_user="founder",
            )
            app = weave_textual_app.build_app(args)

            async with app.run_test() as pilot:
                await pilot.pause()
                app.action_create_app()
                await pilot.pause()
                app.action_prepare_prompt()
                await pilot.pause()

            packet_dir = (
                args.weave_root
                / "apps"
                / "textual-demo"
                / "lifecycle"
                / "01-intent"
                / "artifacts"
                / "prompt-packets"
            )
            self.assertTrue(args.weave_root.exists())
            self.assertEqual(len(list(packet_dir.glob("*.json"))), 1)
            self.assertEqual(len(list(packet_dir.glob("*.md"))), 1)

    async def test_textual_app_exposes_named_views_and_persists_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = Namespace(
                weave_root=Path(tmpdir) / "weave-state",
                app_id="textual-views",
                app_name="Textual Views",
                owner_experience="operator",
                coworker_style="direct, proof-backed",
                intent="Build a launch cockpit with inspectable artifacts and files.",
                target_user="founder",
            )
            app = weave_textual_app.build_app(args)

            async with app.run_test(size=(120, 36)) as pilot:
                await pilot.pause()
                app.action_create_app()
                app.query_one("#composer").value = args.intent
                app.action_save_setup()
                app.action_submit_stage()
                repo = args.weave_root / "apps" / "textual-views" / "repo" / "primary"
                repo.mkdir(parents=True, exist_ok=True)
                (repo / "index.html").write_text("<main><h1>Launch</h1></main>\n", encoding="utf-8")

                for view, action_name in (
                    ("overview", "action_view_overview"),
                    ("stages", "action_view_stages"),
                    ("artifacts", "action_view_artifacts"),
                    ("files", "action_view_files"),
                    ("reviews", "action_view_reviews"),
                    ("help", "action_view_help"),
                    ("resume", "action_view_resume"),
                ):
                    getattr(app, action_name)()
                    await pilot.pause()
                    self.assertEqual(app.view, view)
                    session_path = args.weave_root / "apps" / "textual-views" / "ui" / "textual-session.json"
                    session = json.loads(session_path.read_text(encoding="utf-8"))
                    self.assertEqual(session["active_view"], view)

                session_path = args.weave_root / "apps" / "textual-views" / "ui" / "textual-session.json"
                session = json.loads(session_path.read_text(encoding="utf-8"))
                self.assertEqual(session["active_view"], "resume")

            reopened = weave_textual_app.build_app(args)
            self.assertEqual(reopened.view, "resume")

    async def test_lifecycle_rail_enter_and_click_open_stage_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = Namespace(
                weave_root=Path(tmpdir) / "weave-state",
                app_id="textual-nav",
                app_name="Textual Nav",
                owner_experience="operator",
                coworker_style="direct, proof-backed",
                intent="Build a lifecycle cockpit.",
                target_user="founder",
            )
            app = weave_textual_app.build_app(args)

            async with app.run_test(size=(120, 36)) as pilot:
                await pilot.pause()
                self.assertEqual(app.route, "first_run")
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                self.assertEqual(app.route, "owner_profile")
                self.assertEqual(app.view, "overview")

                clicked = await pilot.click("#stage-list", offset=(3, 6))
                await pilot.pause()
                self.assertEqual(app.route, "app")
                self.assertIn(clicked, {True, False})

    async def test_active_route_persists_for_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = Namespace(
                weave_root=Path(tmpdir) / "weave-state",
                app_id="textual-route-resume",
                app_name="Textual Route Resume",
                owner_experience="operator",
                coworker_style="direct, proof-backed",
                intent="Build a lifecycle cockpit.",
                target_user="founder",
            )
            app = weave_textual_app.build_app(args)

            async with app.run_test(size=(120, 36)) as pilot:
                await pilot.pause()
                app.activate_route("research")
                await pilot.pause()

            reopened = weave_textual_app.build_app(args)
            self.assertEqual(reopened.route, "research")

    async def test_executor_action_exposes_running_and_completion_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = Namespace(
                weave_root=Path(tmpdir) / "weave-state",
                app_id="textual-progress",
                app_name="Textual Progress",
                owner_experience="operator",
                coworker_style="direct, proof-backed",
                intent="Build a lifecycle cockpit.",
                target_user="founder",
                codex_timeout=30,
            )
            app = weave_textual_app.build_app(args)
            original_dispatch = weave_textual_app.weave_backend.dispatch

            def slow_dispatch(root, command, **kwargs):
                if command == "executor.run":
                    time.sleep(0.12)
                    return {
                        "ok": False,
                        "message": "simulated executor blocker",
                        "projection": weave_textual_app.weave_backend.dashboard_projection(
                            root,
                            app_id=kwargs.get("app_id", ""),
                            app_name=kwargs.get("app_name", "New App"),
                        ),
                    }
                return original_dispatch(root, command, **kwargs)

            async with app.run_test(size=(120, 36)) as pilot:
                await pilot.pause()
                app.action_create_app()
                app.activate_route("engineering")
                with mock.patch.object(weave_textual_app.weave_backend, "dispatch", side_effect=slow_dispatch):
                    app.action_run_executor()
                    self.assertEqual(app.activity["state"], "running")
                    await wait_for_idle(app, pilot)
                self.assertEqual(app.activity["state"], "failed")
                self.assertIn("simulated executor blocker", app.activity["message"])

    async def test_textual_app_can_drive_first_stage_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = Namespace(
                weave_root=Path(tmpdir) / "weave-state",
                app_id="textual-flow",
                app_name="Textual Flow",
                owner_experience="operator",
                coworker_style="direct, proof-backed",
                intent="Build a launch cockpit for founders. Success means the owner can inspect risks before launch.",
                target_user="founder",
            )
            app = weave_textual_app.build_app(args)

            async with app.run_test() as pilot:
                await pilot.pause()
                app.action_create_app()
                app.action_save_setup()
                app.query_one("#composer").value = "Goal: launch cockpit. Target user: founder. Success metric: inspect launch risks. Boundary: no live effects."
                app.action_submit_stage()
                app.action_evaluate_stage()
                app.action_approve_stage()
                app.action_advance_stage()
                await pilot.pause()

            metadata = args.weave_root / "apps" / "textual-flow" / "app.weave.json"
            self.assertTrue(metadata.exists())
            self.assertIn('"current_stage": "research"', metadata.read_text(encoding="utf-8"))

    async def test_textual_app_can_drive_lifecycle_through_qa_with_file_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = Namespace(
                weave_root=Path(tmpdir) / "weave-state",
                app_id="textual-qa-flow",
                app_name="Textual QA Flow",
                owner_experience="operator",
                coworker_style="direct, proof-backed",
                intent="Build a launch cockpit for founders with QA and SEO evidence.",
                target_user="founder",
                codex_timeout=30,
                run_engineering_gates=True,
            )
            app = weave_textual_app.build_app(args)

            def fake_run(command, **_kwargs):
                repo = Path(command[-2])
                (repo / "src").mkdir(parents=True, exist_ok=True)
                (repo / "public").mkdir(parents=True, exist_ok=True)
                (repo / "index.html").write_text(
                    "<!doctype html><main><h1>Launch Cockpit</h1></main><script src=\"src/app.js\"></script>\n",
                    encoding="utf-8",
                )
                (repo / "src" / "app.js").write_text("document.addEventListener('DOMContentLoaded', () => {});\n", encoding="utf-8")
                (repo / "src" / "styles.css").write_text("main { color: #111; }\n", encoding="utf-8")
                (repo / "public" / "config.json").write_text(json.dumps({"analytics": False}) + "\n", encoding="utf-8")
                (repo / "README.md").write_text("# Launch Cockpit\n\nLocal-only proof.\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="done\n", stderr="")

            def passing_gates(contract, **_kwargs):
                weave_eval = weave_textual_app.weave_backend.weave_runtime_slice.weave_eval
                return [
                    weave_eval.GateResult(
                        gate_id=str(gate.get("id", "unnamed_gate")),
                        status="passed",
                        passed=True,
                        required=bool(gate.get("required", True)),
                        detail="unit test gate patched as passed",
                        command=str(gate.get("command", "")) or None,
                        exit_code=0,
                    )
                    for gate in contract.get("hard_gates", [])
                ]

            async with app.run_test() as pilot:
                await pilot.pause()
                app.action_create_app()
                app.query_one("#composer").value = args.intent
                app.action_save_setup()
                for stage in ("intent", "research", "selection", "plan"):
                    app.query_one("#composer").value = (
                        f"{stage} proof: launch cockpit for founders, local-only boundary, QA/SEO evidence, and owner review."
                    )
                    app.action_prepare_prompt()
                    app.action_submit_stage()
                    app.action_evaluate_stage()
                    app.action_approve_stage()
                    app.action_advance_stage()
                with mock.patch.object(weave_textual_app.weave_backend.shutil, "which", return_value="codex"), mock.patch.object(
                    weave_textual_app.weave_backend.subprocess,
                    "run",
                    side_effect=fake_run,
                ), mock.patch.object(
                    weave_textual_app.weave_backend.weave_runtime_slice.weave_eval,
                    "evaluate_gates",
                    side_effect=passing_gates,
                ):
                    app.query_one("#composer").value = args.intent
                    app.action_prepare_prompt()
                    app.action_run_executor()
                    await wait_for_idle(app, pilot)

                    feedback = weave_textual_app.parse_feedback_target(
                        "file:apps/textual-qa-flow/repo/primary/src/app.js: move launch risks above metrics.",
                        default_stage="engineering",
                    )
                    app.run_backend_command("feedback.record", feedback)
                    app.action_evaluate_stage()
                    app.action_approve_stage()
                    app.action_advance_stage()

                    app.query_one("#composer").value = "QA proof: validate website source, manifests, SEO, and local-only boundaries."
                    app.action_prepare_prompt()
                    app.action_submit_stage()
                    app.action_evaluate_stage()
                    app.action_approve_stage()
                await pilot.pause()

            metadata = json.loads((args.weave_root / "apps" / "textual-qa-flow" / "app.weave.json").read_text(encoding="utf-8"))
            self.assertIn("qa", metadata["approved_stages"])
            self.assertEqual(metadata["current_stage"], "qa")
            feedback_packets = list(
                (args.weave_root / "apps" / "textual-qa-flow" / "lifecycle" / "05-engineering" / "artifacts" / "prompt-packets").glob("*.json")
            )
            self.assertGreaterEqual(len(feedback_packets), 2)
            self.assertTrue(
                any(json.loads(path.read_text(encoding="utf-8")).get("substage") == "file_feedback" for path in feedback_packets),
                "engineering file feedback should create a file_feedback prompt packet",
            )
            source_manifest = (
                args.weave_root
                / "apps"
                / "textual-qa-flow"
                / "lifecycle"
                / "05-engineering"
                / "artifacts"
                / "source-manifest.json"
            )
            self.assertTrue(source_manifest.exists())


if __name__ == "__main__":
    unittest.main()
