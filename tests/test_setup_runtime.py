from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_RUNTIME_PATH = REPO_ROOT / "scripts" / "setup_runtime.py"
PLUGIN_PATH = REPO_ROOT / "integrations" / "hermes" / "weave-runtime" / "__init__.py"

spec = importlib.util.spec_from_file_location("setup_runtime", SETUP_RUNTIME_PATH)
assert spec is not None
setup_runtime = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = setup_runtime
spec.loader.exec_module(setup_runtime)


plugin_spec = importlib.util.spec_from_file_location("weave_runtime_plugin", PLUGIN_PATH)
assert plugin_spec is not None
weave_runtime_plugin = importlib.util.module_from_spec(plugin_spec)
assert plugin_spec.loader is not None
sys.modules[plugin_spec.name] = weave_runtime_plugin
plugin_spec.loader.exec_module(weave_runtime_plugin)


class SetupRuntimeTests(unittest.TestCase):
    def test_gateway_system_prompt_tracks_current_command_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            weave_root = root / "weave-root"
            onboarding = setup_runtime.weave_runtime_slice.setup_foundation_onboarding(
                weave_root,
                "visual-novel",
                "Visual Novel",
            )

            prompt = setup_runtime.render_gateway_runtime_system_prompt(onboarding)

            self.assertIn("There is no dashboard or UI in this phase", prompt)
            self.assertIn("agent profile:", prompt)
            self.assertIn("active app profile:", prompt)
            self.assertIn("intent -> research -> selection", prompt)
            for command in setup_runtime.weave_runtime_slice.TELEGRAM_COMMANDS:
                self.assertIn(f"`{command}`", prompt)

    def test_configure_gateway_context_refreshes_without_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hermes_home = root / "hermes-home"
            weave_root = root / "weave-root"
            profile_path = root / "runtime-profile.json"

            result = setup_runtime.main(
                [
                    "--runtime",
                    "hermes-default",
                    "--weave-root",
                    str(weave_root),
                    "--gateway-hermes-home",
                    str(hermes_home),
                    "--configure-gateway-context",
                    "--profile-out",
                    str(profile_path),
                ]
            )

            self.assertEqual(result, 0)
            config = setup_runtime._load_yaml_config(hermes_home / "config.yaml")
            self.assertIn("/create_app", config["agent"]["system_prompt"])
            self.assertIn("There is no dashboard or UI", config["agent"]["system_prompt"])
            self.assertEqual(config["weave_runtime"]["root"], str(weave_root.resolve()))
            self.assertNotIn("telegram_bot_token", json.dumps(config).lower())

    def test_installs_weave_runtime_plugin_and_enables_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hermes_home = root / "hermes-home"
            weave_root = root / "weave-root"

            result = setup_runtime.install_weave_runtime_hermes_plugin(
                hermes_home,
                weave_root=weave_root,
                repo_root=REPO_ROOT,
            )

            self.assertTrue(result["enabled"])
            self.assertEqual(result["plugin"], "weave-runtime")
            plugin_dir = hermes_home / "plugins" / "weave-runtime"
            self.assertTrue((plugin_dir / "plugin.yaml").exists())
            self.assertTrue((plugin_dir / "__init__.py").exists())

            config = setup_runtime._load_yaml_config(hermes_home / "config.yaml")
            self.assertEqual(config["plugins"]["enabled"], ["weave-runtime"])
            self.assertEqual(config["weave_runtime"]["repo"], str(REPO_ROOT.resolve()))
            self.assertEqual(config["weave_runtime"]["root"], str(weave_root.resolve()))

    def test_weave_runtime_plugin_dispatches_status_from_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            weave_root = root / "weave-root"
            setup_runtime.weave_runtime_slice.setup_weave_root(weave_root)

            with mock.patch.dict(
                os.environ,
                {
                    "WEAVE_RUNTIME_REPO": str(REPO_ROOT),
                    "WEAVE_RUNTIME_ROOT": str(weave_root),
                },
                clear=False,
            ):
                result = weave_runtime_plugin._dispatch("/status")

            self.assertIn("WEAVE Status", result)
            self.assertIn("root_ready: true", result)

    def test_status_hook_handles_builtin_status(self) -> None:
        with mock.patch.object(weave_runtime_plugin, "_dispatch", return_value="ok"):
            result = weave_runtime_plugin._status_hook("command:status", {})

        self.assertEqual(result, {"decision": "handled", "message": "ok"})

    def test_weave_runtime_plugin_registers_telegram_chat_menu_for_allowed_user(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self) -> bytes:
                return b'{"ok": true, "result": true}'

        event = SimpleNamespace(
            source=SimpleNamespace(
                platform=SimpleNamespace(value="telegram"),
                chat_id="12345",
                user_id="12345",
            )
        )
        weave_runtime_plugin._REGISTERED_TELEGRAM_CHATS.clear()

        with mock.patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "123456789:abcdefghijklmnopqrstuvwxyzABCDEF",
                "TELEGRAM_ALLOWED_USERS": "12345",
            },
            clear=False,
        ):
            with mock.patch.object(
                weave_runtime_plugin.request,
                "urlopen",
                return_value=FakeResponse(),
            ) as urlopen:
                weave_runtime_plugin._pre_gateway_dispatch_hook(
                    "pre_gateway_dispatch",
                    {"event": event},
                )

        self.assertEqual(urlopen.call_count, 1)
        request_obj = urlopen.call_args.args[0]
        payload = request_obj.data.decode("utf-8")
        self.assertIn('"type": "chat"', payload)
        self.assertIn('"chat_id": 12345', payload)
        self.assertIn('"command": "sources"', payload)
        self.assertIn('"command": "weave_status"', payload)
        self.assertIn("12345", weave_runtime_plugin._REGISTERED_TELEGRAM_CHATS)


if __name__ == "__main__":
    unittest.main()
