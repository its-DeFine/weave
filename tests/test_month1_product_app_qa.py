import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class Month1ProductAppQATest(unittest.TestCase):
    @unittest.skipIf(
        os.environ.get("WEAVE_EVAL_GATE_DEPTH"),
        "avoid recursively running the product QA proof inside an eval command gate",
    )
    def test_fableframe_product_qa_passes_and_records_transcript_gates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "fableframe-product-qa.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/month1_product_app_qa.py",
                    "--app-dir",
                    "apps/fableframe-studio",
                    "--report-out",
                    str(report),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["lifecycle"]["final_stage"], "analysis")
            self.assertEqual(
                payload["lifecycle"]["stage_gate_missing"],
                ["outcome and monetization analysis artifact", "transcript capture: current-stage conversation turn"],
            )
            self.assertEqual(len(payload["lifecycle"]["completed_stages"]), 9)


if __name__ == "__main__":
    unittest.main()
