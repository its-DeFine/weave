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

    def test_allows_public_local_runtime_api_loopback_helper(self) -> None:
        hits = public_safe_repo_scan.scan_text('host = "127.0.0.1"', path="scripts/weave_runtime_api.py")
        self.assertEqual(hits, [])

    def test_flags_private_topology_terms(self) -> None:
        private_device = "p" + "c2"
        overlay_vendor = "tail" + "scale"
        runtime_host = "weave" + "-vm01"

        self.assertEqual(
            public_safe_repo_scan.scan_text(f"target {private_device}", path="docs/example.md")[0].label,
            "private-device-name",
        )
        self.assertEqual(
            public_safe_repo_scan.scan_text(f"via {overlay_vendor}", path="docs/example.md")[0].label,
            "private-overlay-vendor",
        )
        self.assertEqual(
            public_safe_repo_scan.scan_text(f"host {runtime_host}", path="docs/example.md")[0].label,
            "private-runtime-host",
        )


if __name__ == "__main__":
    unittest.main()
