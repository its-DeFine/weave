from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "weave_full_contract_audit.py"
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

spec = importlib.util.spec_from_file_location("weave_full_contract_audit", SCRIPT_PATH)
assert spec is not None
audit_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = audit_mod
spec.loader.exec_module(audit_mod)


class WeaveFullContractAuditTests(unittest.TestCase):
    def test_audit_requires_prompt_pack_and_method_proof(self) -> None:
        audit = audit_mod.build_audit(run_verifiers=False)

        self.assertTrue(audit["method_pack_ready"])
        self.assertTrue(audit["runtime_profile_contract_ready"])
        blocker_ids = {item["requirement_id"] for item in audit["remaining_blockers"]}
        if not audit["gestalt_proof_ready"]:
            self.assertIn("hermes.method_proof", blocker_ids)
        if not audit["real_runtime_ready"]:
            self.assertIn("runtime.real_hermes", blocker_ids)

    def test_require_complete_tracks_full_completion_status(self) -> None:
        audit = audit_mod.build_audit(run_verifiers=False)

        if audit["full_completion_ready"]:
            audit_mod.validate_audit(audit, require_complete=True)
            return

        self.assertFalse(audit["full_completion_ready"])
        with self.assertRaises(audit_mod.AuditError):
            audit_mod.validate_audit(audit, require_complete=True)


if __name__ == "__main__":
    unittest.main()
