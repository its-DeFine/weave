from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "weave_cli.py"

spec = importlib.util.spec_from_file_location("weave_cli", CLI_PATH)
assert spec is not None
weave_cli = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = weave_cli
spec.loader.exec_module(weave_cli)


class WeaveCliTests(unittest.TestCase):
    def test_cos_bootstrap_creates_skeleton_from_vague_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "cos-bootstrap",
                    "--source",
                    str(REPO_ROOT),
                    "--home",
                    str(home),
                    "--intent",
                    "I want to build a simple calculator local app.",
                    "--json",
                ],
                output=output,
            )
            self.assertEqual(rc, 0, output.getvalue())
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["state"], "ACCEPT_FOR_SCOPE")
            self.assertEqual(payload["role"], "COS WEAVE")
            self.assertEqual(payload["manual_steps_required"], [])
            self.assertFalse(payload["manual_lifecycle_classification_required"])
            self.assertIn("WEAVE | Home=", payload["state_line"])
            self.assertTrue((home / "apps" / payload["app_id"] / "lifecycle.json").exists())
            self.assertTrue((home / "apps" / payload["app_id"] / "worker-packets" / "WP-0001.md").exists())
            self.assertTrue((home / "updates" / "readback.json").exists())

    def test_cos_bootstrap_handles_multiple_app_ideas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            output = io.StringIO()
            rc = weave_cli.main(
                [
                    "cos-bootstrap",
                    "--source",
                    str(REPO_ROOT),
                    "--home",
                    str(home),
                    "--intent",
                    "I have two app ideas: a recipe planner and an invoice tracker.",
                    "--json",
                ],
                output=output,
            )
            self.assertEqual(rc, 0, output.getvalue())
            payload = json.loads(output.getvalue())
            self.assertGreaterEqual(payload["app_count"], 2)
            registry = json.loads((home / "apps" / "registry.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(registry["apps"]), 2)

    def test_cos_bootstrap_blocks_url_in_local_cli_without_overclaiming(self) -> None:
        output = io.StringIO()
        rc = weave_cli.main(
            [
                "cos-bootstrap",
                "--source",
                "https://example.com/weave.git",
                "--intent",
                "build an app",
                "--json",
            ],
            output=output,
        )
        self.assertEqual(rc, 1)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["state"], "BLOCKED")
        self.assertFalse(payload["live_effects"])
        self.assertIn("does not prove deployment", " ".join(payload["non_claims"]))

    def test_readback_reconstructs_state_from_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            self.assertEqual(
                weave_cli.main(
                    [
                        "cos-bootstrap",
                        "--source",
                        str(REPO_ROOT),
                        "--home",
                        str(home),
                        "--intent",
                        "Please test and validate my dashboard.",
                    ],
                    output=io.StringIO(),
                ),
                0,
            )
            output = io.StringIO()
            rc = weave_cli.main(["readback", "--home", str(home), "--json"], output=output)
            self.assertEqual(rc, 0, output.getvalue())
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["state"], "local_skeleton_ready")
            self.assertEqual(payload["active_app"]["requested_stage"], "qa")
            self.assertIn("does not prove full lifecycle completion", payload["non_claims"])

    def test_help_lists_only_current_core_commands(self) -> None:
        output = io.StringIO()
        rc = weave_cli.main(["help"], output=output)
        text = output.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("cos-bootstrap", text)
        self.assertIn("readback", text)
        self.assertIn("eval", text)
        self.assertNotIn("onboard", text)
        self.assertNotIn("gateway", text)
        self.assertNotIn("t" + "ui", text.lower())


if __name__ == "__main__":
    unittest.main()
