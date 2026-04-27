from __future__ import annotations

import importlib.util
import sys
import tempfile
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
    def test_package_validates(self) -> None:
        summary = validator.validate_package(PACKAGE_ROOT)

        self.assertEqual(summary.slug, "weave")
        self.assertEqual(summary.agent_count, 6)
        self.assertEqual(summary.task_count, 6)
        self.assertEqual(summary.primitive_count, 9)

    def test_openclaw_is_the_only_ceo(self) -> None:
        agents = validator.validate_agents(PACKAGE_ROOT)
        ceos = [agent for agent in agents if agent.get("reportsTo") == "null"]

        self.assertEqual(len(ceos), 1)
        self.assertEqual(ceos[0]["slug"], "ceo-openclaw")
        self.assertEqual(ceos[0]["adapterType"], "openclaw_gateway")

    def test_paperclip_extension_uses_openclaw_gateway_agents(self) -> None:
        validator.validate_paperclip_extension(PACKAGE_ROOT)

    def test_lifecycle_dependencies_are_ordered(self) -> None:
        tasks = {task["slug"]: task for task in validator.validate_tasks(PACKAGE_ROOT)}

        self.assertEqual(tasks["engineering-first-primitive"]["dependsOn"], "research-gate")
        self.assertEqual(tasks["qa-runtime-readiness"]["dependsOn"], "engineering-first-primitive")
        self.assertEqual(tasks["outreach-distribution-gate"]["dependsOn"], "qa-runtime-readiness")
        self.assertEqual(tasks["kpi-analytics-loop"]["dependsOn"], "outreach-distribution-gate")
        self.assertEqual(tasks["iteration-from-analytics"]["dependsOn"], "kpi-analytics-loop")

    def test_validator_rejects_host_specific_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            host_path = "/" + "Users/example/secret"
            (root / "COMPANY.md").write_text(
                f"---\nschema: agentcompanies/v1\nkind: company\nslug: weave\n---\n{host_path}\n",
                encoding="utf-8",
            )

            with self.assertRaises(validator.PackageValidationError):
                validator.scan_forbidden_text(root)


if __name__ == "__main__":
    unittest.main()
