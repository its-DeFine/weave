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

    def test_flags_loopback_in_review_surface(self) -> None:
        hits = public_safe_repo_scan.scan_text('host = "127.0.0.1"', path="docs/example.md")
        self.assertEqual(hits[0].label, "loopback-host")

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

    def test_allowlisted_fixture_file_still_flags_non_fixture_private_text(self) -> None:
        private_path = "/home/" + "example/secret"
        hits = public_safe_repo_scan.scan_text(
            f"runtime path {private_path}",
            path="tests/test_public_safe_repo_scan.py",
        )
        self.assertEqual(hits[0].label, "home-path")

    def test_flags_legacy_surfaces(self) -> None:
        legacy_term = "Sym" + "phony"
        hits = public_safe_repo_scan.scan_text(f"{legacy_term} adapter", path="docs/example.md")
        self.assertEqual(hits[0].label, "legacy-surface")


if __name__ == "__main__":
    unittest.main()
