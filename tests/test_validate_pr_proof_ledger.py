from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_pr_proof_ledger as validator


VALID_BODY = """## Linear
ATM-250

## Proof Boundary
- Local proof: unit tests and public-safe scans.
- Runtime/live proof: not claimed.
- Unproven boundaries / non-claims: no deployment, no public send.

## Proof Ledger
- [x] `python3 -m unittest discover -s tests -p 'test_*.py'`

## Merge Criteria
- [x] Failing checks: none.
- [x] Owner/project criteria satisfied.
"""


class ValidatePrProofLedgerTests(unittest.TestCase):
    def test_accepts_complete_pr_body(self) -> None:
        validator.validate_body(VALID_BODY)

    def test_rejects_unchecked_template_items(self) -> None:
        with self.assertRaises(validator.ProofLedgerError) as ctx:
            validator.validate_body(VALID_BODY.replace("- [x] Failing checks: none.", "- [ ] Failing checks: none."))
        self.assertIn("unchecked", str(ctx.exception))

    def test_rejects_missing_runtime_boundary(self) -> None:
        body = VALID_BODY.replace("- Runtime/live proof: not claimed.\n", "")
        with self.assertRaises(validator.ProofLedgerError) as ctx:
            validator.validate_body(body)
        self.assertIn("runtime/live proof", str(ctx.exception))

    def test_skips_non_pull_request_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            event = Path(tmpdir) / "event.json"
            event.write_text(json.dumps({"ref": "refs/heads/main"}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event)}, clear=True):
                self.assertEqual(validator.main([]), 0)

    def test_reads_pull_request_event_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            event = Path(tmpdir) / "event.json"
            event.write_text(json.dumps({"pull_request": {"body": VALID_BODY}}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event)}, clear=True):
                self.assertEqual(validator.main([]), 0)


if __name__ == "__main__":
    unittest.main()
