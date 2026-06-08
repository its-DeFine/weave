from __future__ import annotations

import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import weave_runtime_slice as runtime  # noqa: E402
import weave_runtime_source_map as source_map_script  # noqa: E402


class WeaveRuntimeSourceMapTests(unittest.TestCase):
    def test_generator_attaches_history_and_hermes_sources_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            weave_root = base / "weave-root"
            history_root = base / "history"
            hermes_home = base / "hermes-home"
            repo_root = base / "repo"
            addons_root = base / "addons"
            for directory in (history_root, hermes_home, repo_root, addons_root):
                directory.mkdir()
            (history_root / "conversation.jsonl").write_text('{"message":"one"}\n', encoding="utf-8")
            (history_root / "command-bus.jsonl").write_text("", encoding="utf-8")
            (history_root / "events.jsonl").write_text("", encoding="utf-8")
            (history_root / "project-lane-claims.json").write_text('{"claims":[]}\n', encoding="utf-8")
            (hermes_home / "sessions").mkdir()
            (hermes_home / "sessions" / "sessions.json").write_text("{}", encoding="utf-8")
            (hermes_home / "gateway_state.json").write_text("{}", encoding="utf-8")
            (hermes_home / "channel_directory.json").write_text("{}", encoding="utf-8")

            args = Namespace(
                weave_root=weave_root,
                history_root=history_root,
                hermes_home=hermes_home,
                repo_root=repo_root,
                addons_root=addons_root,
                expected_commit=None,
                autonomy_mode="yolo",
            )

            source_map = source_map_script.build_source_map(args)
            runtime.validate_source_map(source_map)
            ids = {source["id"] for source in source_map["sources"]}

            self.assertEqual(source_map["schema"], runtime.SOURCE_MAP_SCHEMA)
            self.assertIn("runtime-conversation-ledger", ids)
            self.assertIn("hermes-session-index", ids)
            self.assertIn("repo-checkout", ids)
            self.assertIn("runtime-addons", ids)
            sensitive = [source for source in source_map["sources"] if source.get("sensitive")]
            self.assertTrue(sensitive)
            self.assertTrue(all(source["secret_value_printed"] is False for source in sensitive))


if __name__ == "__main__":
    unittest.main()
