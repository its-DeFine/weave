from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "context_sync_contract_smoke.py"

spec = importlib.util.spec_from_file_location("context_sync_contract_smoke", SCRIPT_PATH)
assert spec is not None
context_sync = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = context_sync
spec.loader.exec_module(context_sync)


class ContextSyncContractTests(unittest.TestCase):
    def test_public_sample_validates(self) -> None:
        packet = context_sync.load_sample()

        context_sync.validate_packet(packet)

        self.assertEqual(packet["schema"], context_sync.SCHEMA)
        self.assertFalse(packet["secret_payload_allowed"])

    def test_public_sample_has_runtime_maintenance_context(self) -> None:
        packet = context_sync.load_sample()

        self.assertIn("work_done", packet)
        self.assertIn("evidence_refs", packet)
        self.assertIn("capabilities", packet)
        self.assertIn("stop_boundaries", packet)
        self.assertGreaterEqual(len(packet["evidence_refs"]), 2)


if __name__ == "__main__":
    unittest.main()
