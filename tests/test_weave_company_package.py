from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
VALIDATOR_PATH = PACKAGE_ROOT / "scripts" / "validate_company_package.py"

spec = importlib.util.spec_from_file_location("validate_company_package", VALIDATOR_PATH)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


class WeaveCompanyPackageTests(unittest.TestCase):
    def test_package_validates_current_cos_skeleton(self) -> None:
        summary = validator.validate_package(PACKAGE_ROOT)

        self.assertEqual(summary.slug, "weave")
        self.assertEqual(summary.version, "0.1.0")
        self.assertEqual(summary.skill_count, 10)
        self.assertGreaterEqual(summary.primitive_count, 11)
        self.assertEqual(summary.eval_contract_count, 12)

    def test_company_declares_no_required_external_runtime(self) -> None:
        fields = validator.validate_company(PACKAGE_ROOT)

        self.assertEqual(fields["runtime"], "cos-file-skeleton")
        self.assertEqual(fields["runtimeFallback"], "none-required")
        self.assertEqual(fields["defaultSurface"], "codex-thread")
        self.assertEqual(fields["releaseTag"], "v0.1.0")
        self.assertEqual(fields["releaseChannel"], "public-v0.1")

    def test_only_current_skills_remain(self) -> None:
        skills = validator.validate_skills(PACKAGE_ROOT)

        self.assertIn("cos-weave", skills)
        self.assertIn("compound-engineering", skills)
        self.assertNotIn("livepeer-adapter-boundary", skills)
        self.assertNotIn("runtime-bridge", skills)
        self.assertNotIn("gestalt-runtime", skills)

        extension = PACKAGE_ROOT / "extensions" / "livepeer" / "skills" / "livepeer-adapter-boundary" / "SKILL.md"
        self.assertTrue(extension.exists())
        self.assertIn("optional domain extension", extension.read_text(encoding="utf-8"))

    def test_primitives_cover_complete_lifecycle(self) -> None:
        primitives = validator.validate_primitives(PACKAGE_ROOT)
        stages = {item["lifecycleStage"] for item in primitives}

        for stage in [
            "intent",
            "research",
            "selection",
            "plan",
            "engineering",
            "qa",
            "deployment",
            "kpi-setup",
            "marketing",
            "iteration",
            "analysis",
        ]:
            self.assertIn(stage, stages)


if __name__ == "__main__":
    unittest.main()
