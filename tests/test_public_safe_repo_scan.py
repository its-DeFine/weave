from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import public_safe_repo_scan  # noqa: E402


class PublicSafeRepoScanTests(unittest.TestCase):
    def test_flags_local_paths(self) -> None:
        hits = public_safe_repo_scan.scan_text("see /Users/example/private", path="docs/example.md")
        self.assertEqual(hits[0].label, "local-user-path")

    def test_allows_public_local_ui_loopback_helper(self) -> None:
        hits = public_safe_repo_scan.scan_text('host = "127.0.0.1"', path="scripts/run_operator_ui.py")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
