from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
RUNNER_PATH = ROOT / "scripts" / "scripted_user_live_agent_runner.py"
RUNNER_SPEC = importlib.util.spec_from_file_location("scripted_user_live_agent_runner", RUNNER_PATH)
assert RUNNER_SPEC and RUNNER_SPEC.loader
runner = importlib.util.module_from_spec(RUNNER_SPEC)
sys.modules["scripted_user_live_agent_runner"] = runner
RUNNER_SPEC.loader.exec_module(runner)


class ScriptedUserLiveAgentRunnerTests(unittest.TestCase):
    def write_scenario(self, directory: Path, payload: dict) -> Path:
        path = directory / f"{payload['scenario_id']}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def run_runner(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/scripted_user_live_agent_runner.py", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=90,
        )

    def test_fixture_mode_scripts_only_user_and_branches_to_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            scenario = self.write_scenario(
                base,
                {
                    "schema": runner.SCENARIO_SCHEMA,
                    "scenario_id": "branching-timeout-demo",
                    "intent": "Build a tiny local application from scripted user prompts.",
                    "app": {
                        "id_template": "branching-timeout-demo-{run_index}",
                        "name_template": "Branching Timeout Demo {run_index}",
                    },
                    "max_executed_steps": 4,
                    "steps": [
                        {
                            "label": "slow-start",
                            "stage": "intent",
                            "user_message": "Please propose the smallest local app we can build safely.",
                            "timeout_seconds": 1,
                            "on_timeout": "goto:fallback",
                        },
                        {
                            "label": "unused-success-path",
                            "stage": "engineering",
                            "user_message": "This step should be skipped when slow-start times out.",
                            "expect": {"reply_contains_all": ["SKIPPED"]},
                        },
                        {
                            "label": "fallback",
                            "stage": "intent",
                            "user_message": "Use the fallback path and keep the app local-only.",
                            "expect": {
                                "reply_contains_all": ["local-only", "fallback"],
                                "agent_source_in": ["scripted_fixture"],
                                "turn_count_delta_at_least": 1,
                                "stage_message_count_at_most": 1,
                            },
                            "on_pass": "stop",
                        },
                    ],
                    "fixture_replies": [
                        {
                            "label": "slow-start",
                            "source": "scripted_fixture",
                            "delay_seconds": 2,
                            "text": "This slow response should timeout before being recorded.",
                        },
                        {
                            "label": "fallback",
                            "source": "scripted_fixture",
                            "text": "fallback accepted: build a local-only checklist app and do not deploy it.",
                        },
                    ],
                },
            )
            output_dir = base / "out"
            result = self.run_runner(
                "--scenario",
                str(scenario),
                "--mode",
                "fixture",
                "--agent",
                "fixture",
                "--output-dir",
                str(output_dir),
                "--run-id",
                "run-branch",
                "--force",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            aggregate = json.loads((output_dir / "run-branch" / "aggregate-report.json").read_text(encoding="utf-8"))
            self.assertTrue(aggregate["passed"])
            self.assertEqual(aggregate["instance_count"], 1)
            report_path = Path(aggregate["results"][0]["report"])
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual([step["label"] for step in report["steps"]], ["slow-start", "fallback"])
            self.assertEqual(report["steps"][0]["status"], "timeout")
            self.assertEqual(report["steps"][1]["status"], "passed")
            self.assertEqual(report["source_summary"]["operator_message_sources"][runner.SCRIPTED_USER_SOURCE], 1)
            self.assertEqual(report["source_summary"]["agent_reply_sources"]["scripted_fixture"], 1)
            self.assertIn("fixture mode is not live Hermes", "\n".join(report["explicit_non_claims"]))
            self.assertTrue((report_path.parent / "app-source-snapshot").exists())

    def test_repeat_parallel_runs_create_isolated_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            scenario = self.write_scenario(
                base,
                {
                    "schema": runner.SCENARIO_SCHEMA,
                    "scenario_id": "parallel-demo",
                    "app": {"id_template": "parallel-demo-{run_index}"},
                    "steps": [
                        {
                            "label": "intent",
                            "stage": "intent",
                            "user_message": "Create a local-only one-screen timer app.",
                            "expect": {"reply_contains_any": ["timer", "Timer"]},
                            "on_pass": "stop",
                        }
                    ],
                    "fixture_replies": [
                        {"label": "intent", "source": "scripted_fixture", "text": "A local-only Timer app is feasible."},
                        {"label": "intent", "source": "scripted_fixture", "text": "A second local-only timer run is feasible."},
                    ],
                },
            )
            output_dir = base / "out"
            result = self.run_runner(
                "--scenario",
                str(scenario),
                "--repeat",
                "2",
                "--parallel",
                "2",
                "--output-dir",
                str(output_dir),
                "--run-id",
                "run-parallel",
                "--force",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            aggregate = json.loads((output_dir / "run-parallel" / "aggregate-report.json").read_text(encoding="utf-8"))
            self.assertTrue(aggregate["passed"])
            self.assertEqual(aggregate["instance_count"], 2)
            self.assertEqual({item["app_id"] for item in aggregate["results"]}, {"parallel-demo-1", "parallel-demo-2"})
            for item in aggregate["results"]:
                self.assertEqual(item["turn_count"], 1)
                self.assertTrue(Path(item["report"]).exists())

    def test_live_mode_rejects_fixture_sources(self) -> None:
        with self.assertRaisesRegex(runner.ScenarioError, "Declared live mode cannot use fixture"):
            runner.validate_agent_reply_source_for_mode("live", "scripted_fixture")

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            scenario = self.write_scenario(
                base,
                {
                    "schema": runner.SCENARIO_SCHEMA,
                    "scenario_id": "live-guard-demo",
                    "steps": [
                        {"label": "intent", "stage": "intent", "user_message": "Try to fake live mode."}
                    ],
                    "fixture_replies": [
                        {"label": "intent", "source": "scripted_fixture", "text": "fixture reply"}
                    ],
                },
            )
            result = self.run_runner("--scenario", str(scenario), "--mode", "live", "--agent", "fixture")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--mode live cannot use --agent fixture", result.stderr)


if __name__ == "__main__":
    unittest.main()
