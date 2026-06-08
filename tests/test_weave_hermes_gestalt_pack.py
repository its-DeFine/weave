from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "weave_hermes_gestalt_pack.py"
if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

spec = importlib.util.spec_from_file_location("weave_hermes_gestalt_pack", SCRIPT_PATH)
assert spec is not None
pack = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = pack
spec.loader.exec_module(pack)


class WeaveHermesGestaltPackTests(unittest.TestCase):
    def test_pack_validates_required_modes_and_outputs(self) -> None:
        manifest = pack.validate_pack()

        self.assertEqual(manifest["pack_id"], "hermes-gestalt-runtime-pack")
        self.assertEqual(manifest["runtime"], "nousresearch-hermes-agent")
        self.assertIn("Contract Mode", manifest["required_modes"])
        self.assertIn("Build-Ready Handoff Packet", manifest["required_outputs"])

    def test_simulated_idea_to_handoff_produces_gestalt_artifacts(self) -> None:
        proof = pack.simulated_idea_to_handoff("Create a local repair tracker.")

        pack.validate_proof(proof)
        self.assertEqual(
            proof["mode_sequence"],
            ["Contract Mode", "Premortem Mode", "Implementation Mode", "Contract Update Mode"],
        )
        self.assertIn("gestalt_kernel", proof["artifacts"])
        self.assertIn("gestaltian_contract", proof["artifacts"])
        self.assertIn("build_ready_handoff_packet", proof["artifacts"])
        self.assertFalse(proof["secret_payload_allowed"])

    def test_validate_proof_rejects_missing_handoff(self) -> None:
        proof = pack.simulated_idea_to_handoff("Create a local repair tracker.")
        del proof["artifacts"]["build_ready_handoff_packet"]

        with self.assertRaises(pack.GestaltPackError):
            pack.validate_proof(proof)

    def test_cli_can_write_and_require_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "proof.json"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(pack.main(["--simulate-run", "--write-evidence", "--evidence-path", str(evidence)]), 0)
                self.assertEqual(pack.main(["--validate", "--require-evidence", "--evidence-path", str(evidence)]), 0)

            payload = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], pack.PROOF_SCHEMA)


if __name__ == "__main__":
    unittest.main()
