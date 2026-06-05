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


if __name__ == "__main__":
    unittest.main()
