from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_GATEWAY_PATH = REPO_ROOT / "scripts" / "setup_gateway.py"

spec = importlib.util.spec_from_file_location("setup_gateway", SETUP_GATEWAY_PATH)
assert spec is not None
setup_gateway = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = setup_gateway
spec.loader.exec_module(setup_gateway)


class SetupGatewayTests(unittest.TestCase):
    def test_configures_telegram_env_without_printing_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bot_file = root / "telegram.secret"
            bot_secret = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
            bot_file.write_text(bot_secret + "\n", encoding="utf-8")
            hermes_home = root / "hermes"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = setup_gateway.main(
                    [
                        "--hermes-home",
                        str(hermes_home),
                        "--token-file",
                        str(bot_file),
                        "--allowed-users",
                        "12345,67890",
                    ]
                )

            self.assertEqual(rc, 0)
            self.assertNotIn(bot_secret, stdout.getvalue())
            env_path = hermes_home / ".env"
            self.assertEqual(env_path.stat().st_mode & 0o777, 0o600)
            env_text = env_path.read_text(encoding="utf-8")
            self.assertIn(f"TELEGRAM_BOT_TOKEN={bot_secret}", env_text)
            self.assertIn("TELEGRAM_ALLOWED_USERS=12345,67890", env_text)
            self.assertNotIn("GATEWAY_ALLOW_ALL_USERS=true", env_text)

    def test_allows_temporary_open_discovery_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bot_file = root / "telegram.secret"
            bot_file.write_text("123456789:abcdefghijklmnopqrstuvwxyzABCDEF\n", encoding="utf-8")
            hermes_home = root / "hermes"

            result = setup_gateway.configure_gateway(
                hermes_home=hermes_home,
                bot_file=bot_file,
                allow_all_users=True,
            )

            self.assertEqual(result["allowlist_mode"], "allow_all_users")
            self.assertTrue(result["env_written"])
            env_text = (hermes_home / ".env").read_text(encoding="utf-8")
            self.assertIn("GATEWAY_ALLOW_ALL_USERS=true", env_text)
            self.assertNotIn("TELEGRAM_ALLOWED_USERS=", env_text)

    def test_rejects_missing_allowlist_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bot_file = root / "telegram.secret"
            bot_file.write_text("123456789:abcdefghijklmnopqrstuvwxyzABCDEF\n", encoding="utf-8")

            with self.assertRaises(setup_gateway.GatewaySetupError):
                setup_gateway.configure_gateway(
                    hermes_home=root / "hermes",
                    bot_file=bot_file,
                )

    def test_missing_file_error_does_not_print_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "telegram.secret"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = setup_gateway.main(
                    [
                        "--token-file",
                        str(missing),
                        "--allowed-users",
                        "12345",
                    ]
                )

            self.assertEqual(rc, 1)
            self.assertIn("token file does not exist", stdout.getvalue())
            self.assertNotIn(str(missing), stdout.getvalue())

    def test_json_output_is_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bot_file = root / "telegram.secret"
            bot_secret = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
            bot_file.write_text(bot_secret + "\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = setup_gateway.main(
                    [
                        "--hermes-home",
                        str(root / "hermes"),
                        "--token-file",
                        str(bot_file),
                        "--allowed-users",
                        "12345",
                        "--json",
                    ]
                )

            self.assertEqual(rc, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["telegram_bot_token_configured"])
            self.assertFalse(payload["token_value_printed"])
            self.assertNotIn(bot_secret, stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
