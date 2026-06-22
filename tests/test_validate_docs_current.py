from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_docs_current.py"

spec = importlib.util.spec_from_file_location("validate_docs_current", VALIDATOR_PATH)
assert spec is not None
validate_docs_current = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validate_docs_current
spec.loader.exec_module(validate_docs_current)


class ValidateDocsCurrentTests(unittest.TestCase):
    def test_current_repo_docs_validate(self) -> None:
        self.assertEqual(validate_docs_current.validate_repo(ROOT), [])

    def test_concept_change_playbook_is_a_core_doc(self) -> None:
        self.assertIn(
            "docs/WEAVE_CONCEPT_CHANGE_MAINTAINER_PLAYBOOK.md",
            validate_docs_current.CORE_DOCS,
        )

    def test_v0_1_release_docs_are_core_docs(self) -> None:
        self.assertIn("CHANGELOG.md", validate_docs_current.CORE_DOCS)
        self.assertIn("docs/WEAVE_V0_1_RELEASE.md", validate_docs_current.CORE_DOCS)
        self.assertIn("docs/WEAVE_V0_1_USER_FLOW.md", validate_docs_current.CORE_DOCS)

    def test_v0_1_release_visuals_are_required(self) -> None:
        self.assertIn("assets/weave-v0.1-flow.svg", validate_docs_current.RELEASE_VISUALS)
        self.assertIn("assets/weave-v0.1-lifecycle.svg", validate_docs_current.RELEASE_VISUALS)

    def test_canonical_release_trigger_is_checked(self) -> None:
        self.assertEqual(
            validate_docs_current.CANONICAL_RELEASE_TRIGGER,
            "Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git",
        )

    def test_default_boundary_flags_stale_surface_terms(self) -> None:
        stale_term = "Sym" + "phony"
        findings = validate_docs_current.boundary_findings({"docs/example.md": f"requires {stale_term}"})

        self.assertEqual(len(findings), 1)
        self.assertIn("non-default surface", findings[0])

    def test_repo_map_requires_external_review_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            docs.mkdir()
            repo_map = docs / "WEAVE_REPO_MAP_PONYTAIL_REVIEW.md"
            repo_map.write_text(
                "### Required Before External Review\n"
                "- Nothing known remains.\n"
                "### Required Before Real Users\n",
                encoding="utf-8",
            )

            findings = validate_docs_current.check_repo_map(root)

        self.assertGreaterEqual(len(findings), 2)
        self.assertTrue(any("controller diff review" in finding for finding in findings))
        self.assertTrue(any("overclaims" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
