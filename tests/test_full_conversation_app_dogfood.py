import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class FullConversationAppDogfoodTest(unittest.TestCase):
    def test_full_conversation_dogfood_generates_app_and_holistic_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            report = base / "full-conversation-app-dogfood.json"
            output_dir = base / "artifacts"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/full_conversation_app_dogfood.py",
                    "--report-out",
                    str(report),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(payload["passed"])
            self.assertFalse(payload["live_hermes_used"])
            self.assertEqual(payload["app"]["name"], "Pocket Orchard")
            self.assertEqual(payload["lifecycle"]["stage_count"], 10)
            self.assertEqual(payload["lifecycle"]["final_stage"], "analysis")
            self.assertEqual(payload["lifecycle"]["final_stage_state"], "approved")
            self.assertEqual(len(payload["lifecycle"]["approved_stages"]), 10)
            self.assertEqual(payload["conversation_review"]["turn_count"], 10)
            self.assertEqual(payload["conversation_review"]["event_count"], 80)
            self.assertEqual(payload["qa"]["check_count"], 8)
            self.assertEqual(payload["holistic_review"]["overall_verdict"], "valuable local dogfood; not live conversational proof")
            self.assertIn("not a live Hermes or Telegram conversation", payload["explicit_non_claims"])
            self.assertTrue((output_dir / "generated-app" / "index.html").exists())
            self.assertTrue((output_dir / "conversation-review" / "conversation-review.html").exists())
            self.assertTrue((output_dir / "holistic-review.json").exists())


if __name__ == "__main__":
    unittest.main()
