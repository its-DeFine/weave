from __future__ import annotations

import importlib.util
import io
import json
import sys
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
            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "onboard",
                    "--weave-root",
                    str(root / "weave-root"),
                    "--hermes-home",
                    str(root / "hermes-home"),
                    "--profile-out",
                    str(root / "runtime-profile.json"),
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
            self.assertIn("Step 1/5  Runtime", text)
            self.assertIn("mode: container", text)
            self.assertIn("would verify Docker and build image", text)
            self.assertIn("Step 2/5  Telegram", text)
            self.assertIn("Create a dedicated Telegram bot with BotFather", text)
            self.assertIn("stopped before token entry", text)
            self.assertFalse((root / "runtime-profile.json").exists())
            self.assertFalse((root / "hermes-home" / ".env").exists())

    def test_onboard_interactive_configures_gateway_without_printing_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = io.StringIO()
            bot_fixture = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
            rc = weave_cli.main(
                [
                    "onboard",
                    "--weave-root",
                    str(root / "weave-root"),
                    "--hermes-home",
                    str(root / "hermes-home"),
                    "--profile-out",
                    str(root / "runtime-profile.json"),
                    "--foundation-app-id",
                    "qa-app",
                    "--foundation-app-name",
                    "QA App",
                    "--local",
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
            env_text = (root / "hermes-home" / ".env").read_text(encoding="utf-8")
            self.assertIn(f"TELEGRAM_BOT_TOKEN={bot_fixture}", env_text)
            self.assertIn("TELEGRAM_ALLOWED_USERS=12345", env_text)
            profile = json.loads((root / "runtime-profile.json").read_text(encoding="utf-8"))
            self.assertTrue(profile["gateway"]["token_loaded"])
            self.assertTrue(profile["gateway"]["runtime_config_written"])
            self.assertFalse(list((root / "weave-root" / "runtime" / "tokens").glob(".weave-telegram-token.*")))

    def test_container_start_command_mounts_repo_runtime_and_hermes_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            args = type(
                "Args",
                (),
                {
                    "weave_root": root / "weave-root",
                    "hermes_home": root / "hermes-home",
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
            self.assertIn(f"{args.weave_root}:{args.weave_root}", command)
            self.assertIn(f"{args.hermes_home}:{args.hermes_home}", command)
            self.assertEqual(command[-3:], ["gateway", "run", "--replace"])


if __name__ == "__main__":
    unittest.main()
