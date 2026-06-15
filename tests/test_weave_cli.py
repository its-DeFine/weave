from __future__ import annotations

import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "weave_cli.py"

spec = importlib.util.spec_from_file_location("weave_cli", CLI_PATH)
assert spec is not None
weave_cli = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = weave_cli
spec.loader.exec_module(weave_cli)


class WeaveCliTests(unittest.TestCase):
    def test_onboard_dry_run_prints_guided_flow_and_stops_before_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_home = root / "runtime-home"
            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "onboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--foundation-app-id",
                    "qa-app",
                    "--foundation-app-name",
                    "QA App",
                    "--dry-run",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("WEAVE Onboarding", text)
            self.assertIn("Step 1/6  Hermes Setup", text)
            self.assertIn("would require normal Hermes setup confirmation or explicit --slash-only", text)
            self.assertIn("Step 2/6  Runtime", text)
            self.assertIn("mode: container", text)
            self.assertIn("would verify Docker and build image", text)
            self.assertIn(f"would use runtime home: {runtime_home.resolve()}", text)
            self.assertIn("Step 3/6  Telegram", text)
            self.assertIn("Create a dedicated Telegram bot with BotFather", text)
            self.assertIn("stopped before token entry", text)
            self.assertFalse((runtime_home / "runtime-profile.json").exists())
            self.assertFalse((runtime_home / "hermes-home" / ".env").exists())

    def test_onboard_requires_hermes_setup_confirmation_unless_slash_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "onboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--foundation-app-id",
                    "qa-app",
                    "--foundation-app-name",
                    "QA App",
                    "--local",
                ],
                input_stream=io.StringIO("12345\n"),
                output=output,
                hidden_reader=lambda _prompt: "123456789:abcdefghijklmnopqrstuvwxyzABCDEF",
            )

            text = output.getvalue()
            self.assertEqual(rc, 1)
            self.assertIn("Step 1/6  Hermes Setup", text)
            self.assertIn("normal Hermes setup must be completed", text)
            self.assertFalse((runtime_home / "hermes-home" / ".env").exists())

    def test_onboard_interactive_configures_gateway_without_printing_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_home = root / "runtime-home"
            output = io.StringIO()
            bot_fixture = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
            rc = weave_cli.main(
                [
                    "onboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--foundation-app-id",
                    "qa-app",
                    "--foundation-app-name",
                    "QA App",
                    "--local",
                    "--slash-only",
                ],
                input_stream=io.StringIO("12345\n"),
                output=output,
                hidden_reader=lambda _prompt: bot_fixture,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("onboarding complete", text)
            self.assertNotIn("No raw token", text)
            self.assertNotIn(bot_fixture, text)
            env_text = (runtime_home / "hermes-home" / ".env").read_text(encoding="utf-8")
            self.assertIn(f"TELEGRAM_BOT_TOKEN={bot_fixture}", env_text)
            self.assertIn("TELEGRAM_ALLOWED_USERS=12345", env_text)
            profile = json.loads((runtime_home / "runtime-profile.json").read_text(encoding="utf-8"))
            self.assertEqual(profile["runtime_home"]["path"], str(runtime_home.resolve()))
            self.assertEqual(profile["runtime_home"]["weave_state_path"], str((runtime_home / "weave-state").resolve()))
            self.assertTrue(profile["gateway"]["token_loaded"])
            self.assertTrue(profile["gateway"]["runtime_config_written"])
            self.assertEqual(profile["hermes_setup"]["state"], "slash_only")
            self.assertFalse(profile["hermes_setup"]["normal_chat_assumed_ready"])
            self.assertFalse(list((runtime_home / "weave-state" / "runtime" / "tokens").glob(".weave-telegram-token.*")))

    def test_container_start_command_mounts_repo_runtime_and_hermes_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            args = type(
                "Args",
                (),
                {
                    "weave_root": root / "weave-root",
                    "hermes_home": root / "hermes-home",
                    "runtime_home": root / "runtime-home",
                    "container_name": "weave-test",
                    "container_image": "weave-hermes-runtime:test",
                },
            )()
            (args.weave_root / "runtime" / "hermes-gateway").mkdir(parents=True)
            args.hermes_home.mkdir(parents=True)
            (args.hermes_home / ".env").write_text("WEAVE_AUTONOMY_MODE=yolo\n", encoding="utf-8")

            with mock.patch.object(weave_cli.shutil, "which", return_value="/usr/bin/docker"):
                command = weave_cli.container_start_command(args)

            self.assertIn("run", command)
            self.assertIn("--env-file", command)
            self.assertIn("--restart", command)
            self.assertIn("unless-stopped", command)
            self.assertIn(f"{REPO_ROOT}:{REPO_ROOT}:ro", command)
            self.assertIn(f"{args.runtime_home}:{args.runtime_home}", command)
            self.assertIn(f"{args.weave_root}:{args.weave_root}", command)
            self.assertIn(f"{args.hermes_home}:{args.hermes_home}", command)
            self.assertIn(f"WEAVE_RUNTIME_HOME={args.runtime_home}", command)
            self.assertEqual(command[-3:], ["gateway", "run", "--replace"])

    def test_dashboard_missing_runtime_home_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "missing-runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "dashboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--no-container-check",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE TUI Operator Console (read-only)", text)
            self.assertIn("WEAVE Dashboard (read-only)", text)
            self.assertIn("[Operator Flow]", text)
            self.assertIn("[Inconsistency Radar]", text)
            self.assertIn("Onboarding: missing", text)
            self.assertIn("root_ready=false", text)
            self.assertIn("runtime profile missing or unreadable", text)
            self.assertIn("WEAVE state root is not initialized", text)
            self.assertIn("run weave onboard", text)
            self.assertFalse(runtime_home.exists())

    def test_dashboard_reports_runtime_apps_adapter_and_proof_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            bot_fixture = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
            onboard_output = io.StringIO()
            rc = weave_cli.main(
                [
                    "onboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--foundation-app-id",
                    "qa-app",
                    "--foundation-app-name",
                    "QA App",
                    "--local",
                    "--slash-only",
                ],
                input_stream=io.StringIO("12345\n"),
                output=onboard_output,
                hidden_reader=lambda _prompt: bot_fixture,
            )
            self.assertEqual(rc, 0, onboard_output.getvalue())

            dashboard_output = io.StringIO()
            rc = weave_cli.main(
                [
                    "dashboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--no-container-check",
                    "--json",
                ],
                output=dashboard_output,
            )

            text = dashboard_output.getvalue()
            payload = json.loads(text)
            self.assertEqual(rc, 0, text)
            self.assertEqual(payload["schema"], "weave-dashboard/v0.1")
            self.assertTrue(payload["read_only"])
            self.assertFalse(payload["live_effects"])
            self.assertIn("operator_flow", payload)
            self.assertIn("inconsistencies", payload)
            self.assertIn("evals", payload)
            self.assertTrue(payload["runtime"]["root_ready"])
            self.assertEqual(payload["runtime"]["adapter"]["runtime_id"], "hermes-default")
            self.assertTrue(payload["runtime"]["adapter"]["present"])
            self.assertEqual(payload["apps"]["product_count"], 1)
            self.assertEqual(payload["apps"]["rows"][0]["app_id"], "qa-app")
            self.assertEqual(payload["proof"]["live_hermes_adapter_proof"], "missing")
            self.assertGreaterEqual(payload["evals"]["contract_count"], 1)
            flow_ids = [step["id"] for step in payload["operator_flow"]]
            self.assertEqual(
                flow_ids,
                [
                    "onboarding",
                    "hermes_setup",
                    "gateway",
                    "app_portfolio",
                    "lifecycle",
                    "transcript",
                    "proof_evals",
                    "next_action",
                ],
            )
            inconsistency_ids = [item["id"] for item in payload["inconsistencies"]]
            self.assertIn("live_hermes_adapter_proof_missing", inconsistency_ids)
            self.assertIn("full_adapter_bridge_not_proven", inconsistency_ids)
            self.assertIn("full invoke/capture adapter bridge is not proven", payload["gaps"])
            self.assertNotIn(bot_fixture, text)

    def test_tui_preview_is_read_only_and_digestible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "tui",
                    "--runtime-home",
                    str(runtime_home),
                    "--scripted-demo",
                    "--no-color",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE TUI", text)
            self.assertIn("local operator cockpit", text)
            self.assertIn("First run", text)
            self.assertIn("previewed", text)
            self.assertIn("external_effects_executed: none", text)
            self.assertIn("SEO: checklist and local QA artifact will be written", text)
            self.assertFalse(runtime_home.exists())

    def test_tui_scripted_handoff_writes_flow_through_qa_with_website_seo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()
            codex_proof = {
                "schema": weave_cli.weave_tui.CODEX_PROOF_SCHEMA,
                "updated_at": "2026-06-15T00:00:00Z",
                "status": "passed",
                "binary_found": True,
                "command_label": "codex --help",
                "exit_code": 0,
                "output_summary": {"stdout_present": True, "stderr_present": False, "stdout_line_count": 1, "stderr_line_count": 0},
                "error_summary": "",
                "live_agent_execution": False,
                "claims": ["Codex CLI metadata command executed locally"],
                "non_claims": ["does not prove Codex auth", "does not prove model invocation", "does not prove Hermes primitives"],
                "public_safe": True,
                "secret_value_printed": False,
            }

            with mock.patch.object(weave_cli.weave_tui, "run_codex_probe", return_value=codex_proof):
                rc = weave_cli.main(
                    [
                        "tui",
                        "--runtime-home",
                        str(runtime_home),
                        "--app-id",
                        "tui-smoke",
                        "--app-name",
                        "TUI Smoke",
                        "--app-surface",
                        "website",
                        "--control-mode",
                        "handoff",
                        "--executor",
                        "fixture",
                        "--scripted-demo",
                        "--write",
                        "--no-color",
                    ],
                    output=output,
                )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("Control: handoff", text)
            self.assertIn("Intent-Plan", text)
            self.assertIn("Owner decision", text)
            self.assertIn("Engineering", text)
            self.assertIn("Real app QA", text)
            self.assertIn("Lifecycle QA bundle", text)
            self.assertIn("Launch gates", text)
            self.assertIn("eval needs_gate_execution", text)
            self.assertIn("Codex proof passed", text)
            self.assertIn("executor: fixture", text)
            self.assertIn("SEO: checklist and real local SEO QA artifact written", text)

            weave_root = runtime_home / "weave-state"
            app_root = weave_root / "apps" / "tui-smoke"
            engineering_dir = app_root / "lifecycle" / "05-engineering" / "artifacts"
            qa_dir = app_root / "lifecycle" / "06-qa" / "artifacts"
            launch_dir = app_root / "lifecycle" / "07-deployment" / "artifacts"
            app_source_dir = app_root / "repo" / "primary"

            self.assertTrue((engineering_dir / "local-implementation-scaffold.md").exists())
            self.assertTrue((engineering_dir / "codex-adapter-proof.json").exists())
            self.assertTrue((engineering_dir / "app-executor-manifest.json").exists())
            self.assertTrue((engineering_dir / "generated-app-manifest.json").exists())
            self.assertTrue((engineering_dir / "seo-checklist.md").exists())
            for filename in ("index.html", "src/app.js", "src/styles.css", "public/config.json", "README.md"):
                self.assertTrue((app_source_dir / filename).exists(), filename)
                self.assertGreater((app_source_dir / filename).stat().st_size, 0, filename)
            self.assertTrue((qa_dir / "real-app-qa.json").exists())
            self.assertTrue((qa_dir / "qa-proof-manifest.json").exists())
            self.assertTrue((qa_dir / "seo-qa.json").exists())
            self.assertTrue((qa_dir / "tui-session-manifest.json").exists())
            self.assertTrue((launch_dir / "launch-ops-manifest.json").exists())

            codex = json.loads((engineering_dir / "codex-adapter-proof.json").read_text(encoding="utf-8"))
            self.assertEqual(codex["status"], "passed")
            self.assertFalse(codex["live_agent_execution"])

            executor = json.loads((engineering_dir / "app-executor-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(executor["executor"], "fixture")
            self.assertEqual(executor["status"], "passed")
            self.assertFalse(executor["live_agent_execution"])

            source_manifest = json.loads((engineering_dir / "generated-app-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(source_manifest["executor"], "fixture")
            self.assertEqual(source_manifest["status"], "passed")
            self.assertEqual(sorted(source_manifest["files"]), sorted(["index.html", "src/app.js", "src/styles.css", "public/config.json", "README.md"]))

            real_qa = json.loads((qa_dir / "real-app-qa.json").read_text(encoding="utf-8"))
            self.assertEqual(real_qa["summary"]["status"], "passed")
            self.assertEqual(real_qa["summary"]["route"], "owner_review")
            self.assertEqual(real_qa["executor"], "fixture")
            self.assertGreaterEqual(real_qa["summary"]["check_count"], 20)

            qa_manifest = json.loads((qa_dir / "qa-proof-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(qa_manifest["summary"]["route"], "owner_review")
            self.assertEqual(
                qa_manifest["proof_types"],
                ["web_frontend", "backend_api", "cli_tui", "agent_runtime_transcript", "data_pipeline", "infrastructure"],
            )

            tui_manifest = json.loads((qa_dir / "tui-session-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(tui_manifest["control_mode"], "hands-off")
            self.assertEqual(tui_manifest["control_label"], "handoff")
            self.assertEqual(tui_manifest["executor"], "fixture")
            self.assertEqual(tui_manifest["external_effects_executed"], [])
            self.assertIn("credentials", tui_manifest["hard_boundaries_stopped"])

            app = weave_cli.weave_tui.weave_runtime_slice.load_app(weave_root, "tui-smoke")
            self.assertEqual(app["current_stage"], "deployment")
            self.assertEqual(app["stage_state"], "blocked")
            self.assertIn("launch capabilities deferred", app["blockers"])

    def test_tui_fixture_source_failure_stops_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "tui",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "tui-broken",
                    "--app-name",
                    "TUI Broken",
                    "--app-surface",
                    "website",
                    "--control-mode",
                    "handoff",
                    "--executor",
                    "fixture",
                    "--fixture-broken-app",
                    "--skip-codex-proof",
                    "--scripted-demo",
                    "--write",
                    "--no-color",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 1, text)
            self.assertIn("Real app QA", text)
            self.assertIn("failed, route engineering", text)

            app_root = runtime_home / "weave-state" / "apps" / "tui-broken"
            qa_dir = app_root / "lifecycle" / "06-qa" / "artifacts"
            launch_dir = app_root / "lifecycle" / "07-deployment" / "artifacts"
            real_qa = json.loads((qa_dir / "real-app-qa.json").read_text(encoding="utf-8"))
            self.assertEqual(real_qa["summary"]["status"], "failed")
            self.assertEqual(real_qa["summary"]["route"], "engineering")
            self.assertGreater(real_qa["summary"]["failed_count"], 0)
            self.assertFalse((launch_dir / "launch-ops-manifest.json").exists())
            self.assertFalse((qa_dir / "tui-session-manifest.json").exists())

            app = weave_cli.weave_tui.weave_runtime_slice.load_app(runtime_home / "weave-state", "tui-broken")
            self.assertEqual(app["current_stage"], "engineering")
            self.assertEqual(app["stage_state"], "blocked")

    def test_tui_codex_executor_failure_is_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()
            failed_exec = weave_cli.subprocess.CompletedProcess(["codex"], 7, "", "failed")

            with mock.patch.object(weave_cli.weave_tui.shutil, "which", return_value="codex"), mock.patch.object(
                weave_cli.weave_tui.subprocess, "run", return_value=failed_exec
            ):
                rc = weave_cli.main(
                    [
                        "tui",
                        "--runtime-home",
                        str(runtime_home),
                        "--app-id",
                        "tui-codex-fail",
                        "--app-name",
                        "TUI Codex Fail",
                        "--app-surface",
                        "website",
                        "--control-mode",
                        "handoff",
                        "--executor",
                        "codex",
                        "--skip-codex-proof",
                        "--scripted-demo",
                        "--write",
                        "--no-color",
                    ],
                    output=output,
                )

            text = output.getvalue()
            self.assertEqual(rc, 1, text)
            self.assertIn("codex executor failed", text)

            engineering_dir = runtime_home / "weave-state" / "apps" / "tui-codex-fail" / "lifecycle" / "05-engineering" / "artifacts"
            executor = json.loads((engineering_dir / "app-executor-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(executor["executor"], "codex")
            self.assertEqual(executor["status"], "failed")
            self.assertEqual(executor["failure_class"], "agent_execution")
            self.assertTrue(executor["binary_found"])
            self.assertFalse((engineering_dir / "generated-app-manifest.json").exists())

    def test_first_run_preview_is_digestible_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "first-run",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--owner-experience",
                    "non-engineer founder",
                    "--coworker-style",
                    "short, direct, proof-backed",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE First Run Console", text)
            self.assertIn("[Signal]", text)
            self.assertIn("[Proof Boundary]", text)
            self.assertIn("live_effects: false", text)
            self.assertIn("secret_value_printed: false", text)
            self.assertIn("non-engineer founder", text)
            self.assertIn("short, direct, proof-backed", text)
            self.assertFalse(runtime_home.exists())

    def test_first_run_write_creates_valid_local_lifecycle_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "first-run",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--owner-experience",
                    "hands-on product owner",
                    "--coworker-style",
                    "decision-first and explicit about assumptions",
                    "--control-mode",
                    "hands-on",
                    "--write",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("[Written]", text)
            self.assertIn("artifact_valid: true", text)
            self.assertNotIn("123456789:abcdefghijklmnopqrstuvwxyzABCDEF", text)
            artifact_path = (
                runtime_home
                / "weave-state"
                / "apps"
                / "demo-app"
                / "lifecycle"
                / "01-intent"
                / "artifacts"
                / "first-run-lifecycle-bundle.json"
            )
            self.assertTrue(artifact_path.exists())
            bundle = json.loads(artifact_path.read_text(encoding="utf-8"))
            weave_cli.weave_first_run.validate_lifecycle_artifacts.validate_bundle(bundle)
            self.assertEqual(bundle["lifecycle_state"]["current_stage"], "intent")
            self.assertEqual(bundle["world_model"]["owner_preferences"]["control_mode"], "hands-on")
            self.assertEqual(bundle["capability_grants"][0]["external_effect"], "local_write")
            active_app = json.loads((runtime_home / "weave-state" / "runtime" / "profiles" / "active-app.json").read_text(encoding="utf-8"))
            self.assertEqual(active_app["app_id"], "demo-app")
            owner_profile = (runtime_home / "weave-state" / "artifacts" / "general" / "owner-profile.md").read_text(encoding="utf-8")
            self.assertIn("hands-on product owner", owner_profile)
            self.assertIn("Provider credentials", owner_profile)

    def test_first_run_attach_existing_requires_initialized_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "first-run",
                    "--runtime-home",
                    str(runtime_home),
                    "--setup-choice",
                    "attach-existing",
                    "--write",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 1, text)
            self.assertIn("attach-existing requires an initialized WEAVE root", text)
            self.assertFalse(runtime_home.exists())

    def test_early_lifecycle_preview_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "early-lifecycle",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--intent",
                    "Build a public-safe local product proof",
                    "--target-user",
                    "operator reviewing a local proof",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE Early Lifecycle Runner", text)
            self.assertIn("Intent -> Research -> Selection -> Plan", text)
            self.assertIn("[Proof Boundary]", text)
            self.assertIn("root_ready: false", text)
            self.assertIn("live_effects: false", text)
            self.assertFalse(runtime_home.exists())

    def test_early_lifecycle_write_advances_through_plan_with_valid_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "early-lifecycle",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--intent",
                    "Build a public-safe local product proof",
                    "--target-user",
                    "operator reviewing a local proof",
                    "--deployment-region",
                    "global",
                    "--marketing-budget",
                    "none",
                    "--create-app",
                    "--write",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("intent: approved -> research", text)
            self.assertIn("research: approved -> selection", text)
            self.assertIn("selection: approved -> plan", text)
            self.assertIn("plan: approved -> engineering", text)
            self.assertIn("artifact_valid: true", text)
            weave_root = runtime_home / "weave-state"
            runtime = weave_cli.weave_early_lifecycle.weave_runtime_slice
            app = runtime.load_app(weave_root, "demo-app")
            self.assertEqual(app["current_stage"], "engineering")
            self.assertEqual(app["stage_state"], "collecting")
            self.assertEqual(app["approved_stages"], ["intent", "research", "selection", "plan"])

            turns = runtime.read_conversation_turns(weave_root, "demo-app")
            self.assertEqual(len(turns), 4)
            for stage_id in ("intent", "research", "selection", "plan"):
                artifact_path = (
                    weave_root
                    / "apps"
                    / "demo-app"
                    / "lifecycle"
                    / runtime.stage_by_id(stage_id).directory
                    / "artifacts"
                    / f"early-{stage_id}.md"
                )
                self.assertTrue(artifact_path.exists(), stage_id)
                status = runtime.stage_evaluation_status(weave_root, "demo-app", stage_id)
                self.assertTrue(status["passed"], stage_id)

            plan_text = (
                weave_root
                / "apps"
                / "demo-app"
                / "lifecycle"
                / "04-plan"
                / "artifacts"
                / "early-plan.md"
            ).read_text(encoding="utf-8")
            for expected in ("Deployment Plan", "QA Plan", "KPI Plan", "Marketing Plan", "Iteration Plan", "Capability Gaps"):
                self.assertIn(expected, plan_text)

            bundle_path = weave_root / "apps" / "demo-app" / "lifecycle" / "04-plan" / "artifacts" / "early-lifecycle-bundle.json"
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            weave_cli.weave_early_lifecycle.validate_lifecycle_artifacts.validate_bundle(bundle)
            self.assertEqual(bundle["lifecycle_state"]["current_stage"], "engineering")
            self.assertEqual(bundle["owner_decision_cards"][0]["status"], "answered")
            self.assertIn("deployment provider not connected", bundle["world_model"]["capability_gaps"])

    def test_engineering_decisions_preview_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "engineering-decisions",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--control-mode",
                    "hands-off",
                    "--hard-boundary",
                    "production_deploy",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE Engineering Decision Queue", text)
            self.assertIn("hard_boundaries: production_deploy", text)
            self.assertIn("requires_owner: true", text)
            self.assertFalse(runtime_home.exists())

    def test_engineering_decisions_hands_off_still_blocks_at_hard_boundary_then_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            prepare = io.StringIO()
            rc = weave_cli.main(
                [
                    "early-lifecycle",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--intent",
                    "Build a public-safe local product proof",
                    "--create-app",
                    "--write",
                ],
                output=prepare,
            )
            self.assertEqual(rc, 0, prepare.getvalue())

            blocked_output = io.StringIO()
            rc = weave_cli.main(
                [
                    "engineering-decisions",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--control-mode",
                    "hands-off",
                    "--hard-boundary",
                    "production_deploy",
                    "--write",
                ],
                output=blocked_output,
            )

            blocked_text = blocked_output.getvalue()
            self.assertEqual(rc, 0, blocked_text)
            self.assertIn("decision_status: open", blocked_text)
            self.assertIn("resume_allowed: false", blocked_text)
            self.assertIn("stage_state: blocked", blocked_text)
            weave_root = runtime_home / "weave-state"
            runtime = weave_cli.weave_engineering_decisions.weave_runtime_slice
            app = runtime.load_app(weave_root, "demo-app")
            self.assertEqual(app["stage_state"], "blocked")
            self.assertIn("owner decision: engineering-decision-001", app["blockers"])

            queue_path = weave_root / "apps" / "demo-app" / "lifecycle" / "05-engineering" / "artifacts" / "owner-decision-queue.json"
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            self.assertFalse(queue["resume"]["allowed"])
            self.assertEqual(queue["decisions"][0]["hard_boundary_flags"], ["production_deploy"])
            self.assertEqual(queue["notifications"][0]["status"], "open")

            bundle_path = weave_root / "apps" / "demo-app" / "lifecycle" / "05-engineering" / "artifacts" / "engineering-decision-bundle.json"
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            weave_cli.weave_engineering_decisions.validate_lifecycle_artifacts.validate_bundle(bundle)
            self.assertEqual(bundle["lifecycle_state"]["attention"]["state"], "owner_input_needed")

            resolved_output = io.StringIO()
            rc = weave_cli.main(
                [
                    "engineering-decisions",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--control-mode",
                    "hands-off",
                    "--hard-boundary",
                    "production_deploy",
                    "--owner-response",
                    "Approved local-safe path only",
                    "--write",
                ],
                output=resolved_output,
            )

            resolved_text = resolved_output.getvalue()
            self.assertEqual(rc, 0, resolved_text)
            self.assertIn("decision_status: answered", resolved_text)
            self.assertIn("resume_allowed: true", resolved_text)
            self.assertIn("stage_state: collecting", resolved_text)
            app = runtime.load_app(weave_root, "demo-app")
            self.assertEqual(app["stage_state"], "collecting")
            self.assertNotIn("owner decision: engineering-decision-001", app["blockers"])
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            self.assertTrue(queue["resume"]["allowed"])
            self.assertEqual(queue["notifications"][0]["status"], "resolved")
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            weave_cli.weave_engineering_decisions.validate_lifecycle_artifacts.validate_bundle(bundle)
            self.assertEqual(bundle["owner_decision_cards"][0]["status"], "answered")
            self.assertEqual(bundle["lifecycle_state"]["attention"]["state"], "no_attention_needed")

    def test_engineering_decisions_hands_off_safe_assumption_can_continue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            prepare = io.StringIO()
            rc = weave_cli.main(
                [
                    "early-lifecycle",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--intent",
                    "Build a public-safe local product proof",
                    "--create-app",
                    "--write",
                ],
                output=prepare,
            )
            self.assertEqual(rc, 0, prepare.getvalue())

            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "engineering-decisions",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--control-mode",
                    "hands-off",
                    "--write",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("decision_status: deferred", text)
            self.assertIn("resume_allowed: true", text)
            weave_root = runtime_home / "weave-state"
            queue_path = weave_root / "apps" / "demo-app" / "lifecycle" / "05-engineering" / "artifacts" / "owner-decision-queue.json"
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            self.assertEqual(queue["assumptions"][0]["status"], "active")
            app = weave_cli.weave_engineering_decisions.weave_runtime_slice.load_app(weave_root, "demo-app")
            self.assertEqual(app["stage_state"], "collecting")

    def test_qa_proof_preview_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "qa-proof",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--surface",
                    "mixed",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE QA Proof Runner", text)
            self.assertIn("surface: mixed", text)
            self.assertIn("web_frontend", text)
            self.assertFalse(runtime_home.exists())

    def test_qa_proof_mixed_surface_writes_manifest_bundle_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "qa-proof",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--surface",
                    "mixed",
                    "--create-app",
                    "--write",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("status: passed", text)
            self.assertIn("route: owner_review", text)
            self.assertIn("checks: 6", text)
            weave_root = runtime_home / "weave-state"
            qa_dir = weave_root / "apps" / "demo-app" / "lifecycle" / "06-qa" / "artifacts"
            manifest = json.loads((qa_dir / "qa-proof-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["summary"]["route"], "owner_review")
            self.assertEqual(
                manifest["proof_types"],
                ["web_frontend", "backend_api", "cli_tui", "agent_runtime_transcript", "data_pipeline", "infrastructure"],
            )
            self.assertTrue((qa_dir / "web-dom-snapshot.html").exists())
            self.assertTrue((qa_dir / "cli-terminal-evidence.json").exists())
            bundle = json.loads((qa_dir / "qa-proof-lifecycle-bundle.json").read_text(encoding="utf-8"))
            weave_cli.weave_qa_proof.validate_lifecycle_artifacts.validate_bundle(bundle)
            app = weave_cli.weave_qa_proof.weave_runtime_slice.load_app(weave_root, "demo-app")
            self.assertEqual(app["current_stage"], "qa")
            self.assertEqual(app["stage_state"], "ready_for_review")

    def test_qa_proof_cli_failure_routes_to_engineering(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "qa-proof",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--surface",
                    "cli",
                    "--command",
                    "python3 -c 'raise SystemExit(2)'",
                    "--create-app",
                    "--write",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("status: failed", text)
            self.assertIn("route: engineering", text)
            weave_root = runtime_home / "weave-state"
            manifest = json.loads(
                (weave_root / "apps" / "demo-app" / "lifecycle" / "06-qa" / "artifacts" / "qa-proof-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["summary"]["failure_classes"], ["code"])
            app = weave_cli.weave_qa_proof.weave_runtime_slice.load_app(weave_root, "demo-app")
            self.assertEqual(app["current_stage"], "engineering")
            self.assertEqual(app["stage_state"], "blocked")
            self.assertIn("qa failed: route to engineering", app["blockers"])

    def test_launch_ops_preview_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "launch-ops",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE Launch Ops", text)
            self.assertIn("deployment_provider: deferred", text)
            self.assertIn("external_effects_executed: none", text)
            self.assertFalse(runtime_home.exists())

    def test_launch_ops_writes_gated_later_lifecycle_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()

            rc = weave_cli.main(
                [
                    "launch-ops",
                    "--runtime-home",
                    str(runtime_home),
                    "--app-id",
                    "demo-app",
                    "--app-name",
                    "Demo App",
                    "--deployment-region",
                    "global",
                    "--marketing-budget",
                    "none",
                    "--create-app",
                    "--write",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("status: blocked_on_capability", text)
            self.assertIn("jobs: 4", text)
            weave_root = runtime_home / "weave-state"
            runtime = weave_cli.weave_launch_ops.weave_runtime_slice
            app = runtime.load_app(weave_root, "demo-app")
            self.assertEqual(app["current_stage"], "deployment")
            self.assertEqual(app["stage_state"], "blocked")
            self.assertEqual(app["launch_ops"]["external_effects_executed"], [])
            self.assertIn("launch capabilities deferred", app["blockers"])

            manifest_path = weave_root / "apps" / "demo-app" / "lifecycle" / "07-deployment" / "artifacts" / "launch-ops-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["external_effects_executed"], [])
            statuses = {item["id"]: item["status"] for item in manifest["capability_inventory"]["capabilities"]}
            self.assertEqual(statuses["deployment-provider"], "deferred")
            self.assertEqual(statuses["analytics-provider"], "deferred")
            self.assertEqual(statuses["marketing-accounts"], "deferred")
            self.assertEqual(len(manifest["jobs"]), 4)
            self.assertTrue(any(job["external_effect"] == "paid_spend" and job["status"] == "blocked" for job in manifest["jobs"]))
            self.assertEqual(manifest["kill_switches"][0]["status"], "enabled")
            self.assertEqual(manifest["owner_notifications"][0]["status"], "open")

            bundle_path = weave_root / "apps" / "demo-app" / "lifecycle" / "07-deployment" / "artifacts" / "launch-ops-lifecycle-bundle.json"
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            weave_cli.weave_launch_ops.validate_lifecycle_artifacts.validate_bundle(bundle)
            self.assertEqual(bundle["lifecycle_state"]["attention"]["state"], "blocked_on_capability")
            self.assertEqual(len(bundle["recurring_jobs"]), 4)

    def test_runtime_qa_dry_run_writes_manifest_without_docker_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_home = root / "runtime-home"
            manifest_path = root / "runtime-qa-plan.json"
            output = io.StringIO()

            with mock.patch.object(weave_cli, "run_process") as run_mock, mock.patch.object(weave_cli.shutil, "which") as which_mock:
                rc = weave_cli.main(
                    [
                        "runtime-qa",
                        "--runtime-home",
                        str(runtime_home),
                        "--qa-run-id",
                        "qa-test-run",
                        "--app-id",
                        "qa-app",
                        "--container-name",
                        "weave-qa-container",
                        "--container-image",
                        "weave-hermes-runtime:test",
                        "--dry-run",
                        "--out",
                        str(manifest_path),
                    ],
                    output=output,
                )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            run_mock.assert_not_called()
            which_mock.assert_not_called()
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "weave.runtime-qa-manifest/v0.1")
            self.assertEqual(manifest["qa_run_id"], "qa-test-run")
            self.assertTrue(manifest["dry_run"])
            self.assertEqual(manifest["claim_boundary"], "plan-only")
            self.assertTrue(manifest["teardown_policy"]["required"])
            self.assertTrue(manifest["teardown_policy"]["archive_required_before_remove"])
            self.assertTrue(manifest["rehydrate_policy"]["requires_secret_relink"])
            self.assertTrue(manifest["rehydrate_policy"]["requires_verify_runtime"])
            self.assertTrue(set(weave_cli.RUNTIME_QA_RESOURCE_STATES).issubset(manifest["resource_states"]))
            self.assertEqual({resource["current_state"] for resource in manifest["resources"]}, {"planned_only"})
            self.assertTrue(any(command["command"][0] == "docker" for command in manifest["planned_commands"]))
            self.assertFalse(any(command["executes_in_dry_run"] for command in manifest["planned_commands"]))
            self.assertIn("no_docker_executed: true", text)

    def test_runtime_export_import_skips_secret_material_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_home = root / "runtime-home"
            imported_home = root / "imported-runtime-home"
            archive = root / "runtime-export.tar.gz"
            bot_fixture = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"

            onboard_output = io.StringIO()
            rc = weave_cli.main(
                [
                    "onboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--foundation-app-id",
                    "qa-app",
                    "--foundation-app-name",
                    "QA App",
                    "--local",
                    "--slash-only",
                ],
                input_stream=io.StringIO("12345\n"),
                output=onboard_output,
                hidden_reader=lambda _prompt: bot_fixture,
            )
            self.assertEqual(rc, 0, onboard_output.getvalue())

            export_output = io.StringIO()
            rc = weave_cli.main(
                ["export-runtime", "--runtime-home", str(runtime_home), "--out", str(archive)],
                output=export_output,
            )
            self.assertEqual(rc, 0, export_output.getvalue())
            self.assertIn("secrets_exported: false", export_output.getvalue())

            with tarfile.open(archive, "r:gz") as tar:
                names = tar.getnames()
                self.assertNotIn("runtime-home/hermes-home/.env", names)
                self.assertFalse(any("/tokens/" in name for name in names))
                contents = []
                for member in tar.getmembers():
                    if member.isfile():
                        handle = tar.extractfile(member)
                        if handle is not None:
                            contents.append(handle.read().decode("utf-8", errors="ignore"))
                self.assertNotIn(bot_fixture, "\n".join(contents))

            import_output = io.StringIO()
            rc = weave_cli.main(
                ["import-runtime", str(archive), "--runtime-home", str(imported_home)],
                output=import_output,
            )
            self.assertEqual(rc, 0, import_output.getvalue())
            self.assertIn("secrets_imported: false", import_output.getvalue())

            verify_output = io.StringIO()
            rc = weave_cli.main(["verify-runtime", "--runtime-home", str(imported_home)], output=verify_output)
            self.assertEqual(rc, 0, verify_output.getvalue())
            self.assertIn("secret_relink_required: true", verify_output.getvalue())

    def test_hermes_confirm_ready_records_non_secret_setup_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_home = root / "runtime-home"

            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "hermes",
                    "--runtime-home",
                    str(runtime_home),
                    "confirm-ready",
                ],
                output=output,
            )

            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("state: operator_confirmed_ready", text)
            self.assertIn("route_verification_owner: hermes", text)
            self.assertIn("secret_value_printed: false", text)

    def test_help_alias_supports_top_level_and_command_topics(self) -> None:
        output = io.StringIO()
        rc = weave_cli.main(["help"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0, text)
        self.assertIn("WEAVE command line", text)
        self.assertIn("weave help [command]", text)
        self.assertIn("weave eval --list", text)

        output = io.StringIO()
        rc = weave_cli.main(["help", "onboard"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0, text)
        self.assertIn("--existing-hermes", text)
        self.assertIn("--slash-only", text)

    def test_eval_command_lists_contracts(self) -> None:
        output = io.StringIO()
        rc = weave_cli.main(["eval", "--list"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0, text)
        self.assertIn("engineering", text)
        self.assertIn("release-readiness", text)

    def test_eval_command_prints_review_template(self) -> None:
        output = io.StringIO()
        rc = weave_cli.main(["eval", "engineering", "--review-template"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0, text)
        template = json.loads(text)
        self.assertEqual(template["stage"], "Engineering")
        self.assertIn("correctness", template["scores"])

    def test_existing_hermes_dry_run_is_mode_aware(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "onboard",
                    "--runtime-home",
                    str(runtime_home),
                    "--existing-hermes",
                    "--runtime-binary",
                    "/usr/bin/hermes",
                    "--dry-run",
                ],
                output=output,
            )
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("mode: existing Hermes attach", text)
            self.assertIn("WEAVE will not install Hermes", text)
            self.assertIn("would attach WEAVE plugin/config", text)
            self.assertIn("bin/weave onboard --existing-hermes", text)
            self.assertFalse((runtime_home / "runtime-profile.json").exists())

    def test_attach_hermes_alias_reuses_existing_hermes_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "attach-hermes",
                    "--runtime-home",
                    str(runtime_home),
                    "--runtime-binary",
                    "/usr/bin/hermes",
                    "--dry-run",
                ],
                output=output,
            )
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("mode: existing Hermes attach", text)
            self.assertIn("bin/weave onboard --existing-hermes", text)

    def test_doctor_reports_next_action_without_printing_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()
            rc = weave_cli.main(["doctor", "--runtime-home", str(runtime_home)], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE Doctor", text)
            self.assertIn("deterministic_layer_ready: false", text)
            self.assertIn("secret_value_printed: false", text)
            self.assertIn("bin/weave onboard", text)

    def test_command_runs_deterministic_slash_command_locally(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_home = Path(tmpdir) / "runtime-home"
            output = io.StringIO()
            rc = weave_cli.main(["command", "--runtime-home", str(runtime_home), "/status"], output=output)
            text = output.getvalue()
            self.assertEqual(rc, 0, text)
            self.assertIn("WEAVE Status", text)
            self.assertIn("deterministic", text.lower())
            self.assertTrue((runtime_home / "weave-state" / "apps" / "registry.json").exists())


if __name__ == "__main__":
    unittest.main()
