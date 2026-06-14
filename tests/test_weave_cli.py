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
