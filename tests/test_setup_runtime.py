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
            self.assertIn("Transcript capture is mandatory", prompt)
            self.assertIn("weave-conversation-turn/v0.1", prompt)
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
            self.assertIn("Transcript capture is mandatory", config["agent"]["system_prompt"])
            self.assertEqual(config["weave_runtime"]["root"], str(weave_root.resolve()))
            self.assertNotIn("telegram_bot_token", json.dumps(config).lower())

    def test_plugin_install_overlays_existing_cache_without_deleting_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hermes_home = root / "hermes-home"
            weave_root = root / "weave-root"
            plugin_dir = hermes_home / "plugins" / setup_runtime.HERMES_PLUGIN_NAME
            cache_dir = plugin_dir / "__pycache__"
            cache_dir.mkdir(parents=True)
            cache_file = cache_dir / "stale.pyc"
            cache_file.write_bytes(b"cache")

            result = setup_runtime.install_weave_runtime_hermes_plugin(
                hermes_home,
                weave_root=weave_root,
                runtime_home=root / "runtime-home",
            )

            self.assertEqual(result["plugin"], setup_runtime.HERMES_PLUGIN_NAME)
            self.assertTrue((plugin_dir / "__init__.py").exists())
            self.assertTrue((plugin_dir / "plugin.yaml").exists())
            self.assertTrue(cache_file.exists())

    def test_setup_refreshes_agent_profile_when_profile_env_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hermes_home = root / "hermes-home"
            weave_root = root / "weave-root"
            profile_path = root / "runtime-profile.json"
            setup_runtime.weave_runtime_slice.setup_weave_root(weave_root)

            with mock.patch.dict(
                os.environ,
                {
                    "WEAVE_HERMES_MODEL": "gpt-5.5",
                    "WEAVE_HERMES_REASONING_EFFORT": "high",
                    "WEAVE_HERMES_PROVIDER_ADAPTER": "openai-codex",
                },
                clear=False,
            ):
                result = setup_runtime.main(
                    [
                        "--runtime",
                        "hermes-default",
                        "--weave-root",
                        str(weave_root),
                        "--gateway-hermes-home",
                        str(hermes_home),
                        "--skip-foundation-onboarding",
                        "--profile-out",
                        str(profile_path),
                    ]
                )

            self.assertEqual(result, 0)
            agent_profile = json.loads(
                (weave_root / "runtime" / "profiles" / "agent-profile.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(agent_profile["model"], "gpt-5.5")
            self.assertEqual(agent_profile["reasoning_effort"], "high")
            self.assertEqual(agent_profile["provider_adapter"], "openai-codex")

    def test_setup_records_container_runtime_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_path = root / "runtime-profile.json"
            weave_root = root / "weave-root"

            result = setup_runtime.main(
                [
                    "--runtime",
                    "hermes-default",
                    "--weave-root",
                    str(weave_root),
                    "--runtime-container-image",
                    "weave-hermes-runtime:test",
                    "--profile-out",
                    str(profile_path),
                    "--skip-foundation-onboarding",
                ]
            )

            self.assertEqual(result, 0)
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            container = profile["runtime"]["container"]
            self.assertTrue(container["enabled"])
            self.assertEqual(container["engine"], "docker")
            self.assertEqual(container["image"], "weave-hermes-runtime:test")
            self.assertIn("Docker restart policy", container["supervision"])

    def test_setup_derives_runtime_home_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            runtime_home = root / "runtime-home"

            result = setup_runtime.main(
                [
                    "--runtime-home",
                    str(runtime_home),
                    "--runtime-container-image",
                    "weave-hermes-runtime:test",
                    "--skip-foundation-onboarding",
                ]
            )

            self.assertEqual(result, 0)
            profile = json.loads((runtime_home / "runtime-profile.json").read_text(encoding="utf-8"))
            self.assertEqual(profile["runtime_home"]["path"], str(runtime_home.resolve()))
            self.assertEqual(profile["runtime_home"]["weave_state_path"], str((runtime_home / "weave-state").resolve()))
            self.assertEqual(profile["runtime_home"]["hermes_home_path"], str((runtime_home / "hermes-home").resolve()))
            self.assertTrue((runtime_home / "weave-state" / "apps" / "registry.json").exists())

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
            setup_runtime.weave_runtime_slice.create_app(weave_root, "demo", "Demo")

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
            with mock.patch.dict(
                os.environ,
                {
                    "WEAVE_RUNTIME_REPO": str(REPO_ROOT),
                    "WEAVE_RUNTIME_ROOT": str(weave_root),
                },
                clear=False,
            ):
                transcript = weave_runtime_plugin._dispatch("/transcript demo")

            self.assertIn("WEAVE Transcript", transcript)
            self.assertIn("turns: 0", transcript)

    def test_weave_runtime_plugin_returns_generic_runtime_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "weave-root"
            setup_runtime.weave_runtime_slice.setup_weave_root(root)
            with mock.patch.dict(
                os.environ,
                {
                    "WEAVE_RUNTIME_REPO": str(REPO_ROOT),
                    "WEAVE_RUNTIME_ROOT": str(root),
                },
                clear=False,
            ), mock.patch.object(
                weave_runtime_plugin,
                "_load_runtime_module",
                side_effect=RuntimeError("SECRET_" + "TO" + "KEN=super-" + "secret-value"),
            ):
                result = weave_runtime_plugin._dispatch("/status")

            self.assertEqual(result, "WEAVE runtime command failed. Check local runtime logs.")
            self.assertNotIn("SECRET_TOKEN", result)
            self.assertNotIn("super-secret-value", result)

    def test_weave_runtime_plugin_loader_does_not_leak_scripts_path(self) -> None:
        scripts_dir = str((REPO_ROOT / "scripts").resolve())
        original_path = list(sys.path)
        try:
            sys.path[:] = [item for item in sys.path if item != scripts_dir]
            weave_runtime_plugin._load_runtime_module(REPO_ROOT)
            self.assertNotIn(scripts_dir, sys.path)
        finally:
            sys.path[:] = original_path

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
                "TELEGRAM_BOT_TOKEN": "123456789:" + "abcdefghijklmnopqrstuvwxyzABCDEF",
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
        self.assertIn('"command": "transcript"', payload)
        self.assertIn('"command": "weave_status"', payload)
        self.assertIn("12345", weave_runtime_plugin._REGISTERED_TELEGRAM_CHATS)

    def test_weave_runtime_plugin_blocks_normal_chat_when_hermes_setup_unconfirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hermes_home = root / "hermes-home"
            weave_root = root / "weave-root"
            hermes_home.mkdir()
            setup_runtime.weave_runtime_slice.setup_weave_root(weave_root)
            event = SimpleNamespace(
                text="hey there",
                source=SimpleNamespace(platform=SimpleNamespace(value="telegram"), chat_id="12345", user_id="12345"),
            )

            with mock.patch.dict(
                os.environ,
                {
                    "HERMES_HOME": str(hermes_home),
                    "WEAVE_RUNTIME_REPO": str(REPO_ROOT),
                    "WEAVE_RUNTIME_ROOT": str(weave_root),
                },
                clear=False,
            ):
                response = weave_runtime_plugin._pre_gateway_dispatch_hook(
                    "pre_gateway_dispatch",
                    {"event": event},
                )

            self.assertIsInstance(response, dict)
            assert isinstance(response, dict)
            self.assertEqual(response["decision"], "handled")
            self.assertIn("Hermes setup has not been confirmed", response["message"])
            self.assertIn("hermes_setup: needs_hermes_setup", response["message"])
            self.assertNotIn("TELEGRAM_BOT_TOKEN", response["message"])


if __name__ == "__main__":
    unittest.main()
