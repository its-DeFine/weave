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
            self.assertEqual(payload["stage_contract_state"], "verified")
            self.assertEqual(payload["stage_contract_findings"], [])
            self.assertIn("WEAVE | Home=", payload["state_line"])
            self.assertTrue((home / "apps" / payload["app_id"] / "lifecycle.json").exists())
            self.assertTrue((home / "apps" / payload["app_id"] / "worker-packets" / "WP-0001.md").exists())
            self.assertTrue((home / "updates" / "readback.json").exists())
            lifecycle = json.loads((home / "apps" / payload["app_id"] / "lifecycle.json").read_text(encoding="utf-8"))
            active_stage = next(row for row in lifecycle["stages"] if row["stage"] == "intent")
            contract = active_stage["stage_entry_contract"]
            self.assertEqual(contract["eval_ref"], "packages/weave-tool/evals/lifecycle/intent.yaml")
            self.assertEqual(contract["primitive_registry_ref"], "packages/weave-tool/primitives/registry.json")
            self.assertIn("packages/weave-tool/skills/weave-lifecycle/SKILL.md", contract["skill_refs"])
            readback = json.loads((home / "apps" / payload["app_id"] / "updates" / "readback.json").read_text(encoding="utf-8"))
            self.assertIn("consulted_contract_refs", readback)

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

    def test_research_procedure_and_readback_require_product_claim_taxonomy(self) -> None:
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
                    "Research an invoice tracker app against competitors and alternatives before building.",
                    "--json",
                ],
                output=output,
            )
            self.assertEqual(rc, 0, output.getvalue())
            payload = json.loads(output.getvalue())
            app_root = home / "apps" / payload["app_id"]

            procedure = (home / "procedures" / "lifecycle" / "02-research.md").read_text(encoding="utf-8")
            for phrase in [
                "product-market facts",
                "target users and use cases",
                "customer or audience segment",
                "alternatives and substitutes",
                "competitors and antagonists",
                "disconfirming evidence",
                "source list",
                "primitive-market-research",
                "technical feasibility evidence alone",
            ]:
                with self.subTest(surface="procedure", phrase=phrase):
                    self.assertIn(phrase, procedure)

            readback = json.loads((app_root / "updates" / "readback.json").read_text(encoding="utf-8"))
            research_readback = readback["research_readback"]
            self.assertEqual(research_readback["recommended_skill"], "primitive-market-research")
            self.assertIn("product-market facts", research_readback["required_outputs"])
            self.assertIn("competitors and antagonists", research_readback["required_outputs"])
            self.assertIn("technical feasibility evidence alone", research_readback["cannot_pass_with"])
            self.assertEqual(set(research_readback["claim_buckets"]), {"sourced_facts", "assumptions", "opinions"})

            research_state = json.loads((app_root / "lifecycle" / "02-research" / "state.json").read_text(encoding="utf-8"))
            contract = research_state["research_contract"]
            self.assertIn("alternatives and substitutes", contract["required_outputs"])
            self.assertIn("primitive-market-research", contract["recommended_skill"])

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

    def test_cos_bootstrap_returns_revise_when_stage_contracts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "broken-weave"
            home = Path(tmpdir) / "home"
            (source / "packages" / "weave-tool").mkdir(parents=True)
            payload = weave_cli.weave_cos_skeleton.bootstrap(
                source=source,
                home=home,
                surface="codex",
                intent="build a local calculator app",
                app_id="demo",
                app_name="Demo",
            )
            self.assertEqual(payload["state"], "REVISE")
            self.assertEqual(payload["stage_contract_state"], "revise")
            self.assertTrue(payload["stage_contract_findings"])
            self.assertIn("missing packages/weave-tool/evals/lifecycle/intent.yaml", payload["stage_contract_findings"])
            self.assertTrue((home / "updates" / "readback.json").exists())

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

    def test_generated_lifecycle_matches_eval_contract_order(self) -> None:
        skeleton_stages = [stage for stage, _label in weave_cli.weave_cos_skeleton.LIFECYCLE_STAGES]
        self.assertEqual(skeleton_stages, weave_cli.weave_eval.STAGE_ORDER)
        self.assertNotIn("requirements", skeleton_stages)
        self.assertIn("kpi-setup", skeleton_stages)


if __name__ == "__main__":
    unittest.main()
