from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages" / "weave-tool"
VALIDATOR_PATH = PACKAGE_ROOT / "scripts" / "validate_company_package.py"
SETUP_RUNTIME_PATH = REPO_ROOT / "scripts" / "setup_runtime.py"

spec = importlib.util.spec_from_file_location("validate_company_package", VALIDATOR_PATH)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)

setup_spec = importlib.util.spec_from_file_location("setup_runtime", SETUP_RUNTIME_PATH)
assert setup_spec is not None
setup_runtime = importlib.util.module_from_spec(setup_spec)
assert setup_spec.loader is not None
sys.modules[setup_spec.name] = setup_runtime
setup_spec.loader.exec_module(setup_runtime)


class WeaveCompanyPackageTests(unittest.TestCase):
    def test_package_validates(self) -> None:
        summary = validator.validate_package(PACKAGE_ROOT)

        self.assertEqual(summary.slug, "weave")
        self.assertEqual(summary.version, "2026.05.13-console")
        self.assertEqual(summary.agent_count, 7)
        self.assertEqual(summary.task_count, 9)
        self.assertEqual(summary.skill_count, 12)
        self.assertEqual(summary.primitive_count, 9)

    def test_hermes_is_the_default_ceo(self) -> None:
        agents = validator.validate_agents(PACKAGE_ROOT)
        ceos = [agent for agent in agents if agent.get("reportsTo") == "null"]

        self.assertEqual(len(ceos), 1)
        self.assertEqual(ceos[0]["slug"], "ceo-hermes")
        self.assertEqual(ceos[0]["adapterType"], "hermes_runtime")

    def test_company_declares_hermes_default_runtime(self) -> None:
        fields = validator.validate_company(PACKAGE_ROOT)

        self.assertEqual(fields["runtime"], "hermes-default")
        self.assertEqual(fields["runtimeFallback"], "openclaw-solo")
        self.assertEqual(fields["version"], "2026.05.13-console")
        self.assertEqual(fields["releaseDate"], "2026-05-13")
        self.assertEqual(fields["releaseTag"], "v2026.05.13-console")

    def test_openclaw_remains_fallback_runtime(self) -> None:
        agents = validator.validate_agents(PACKAGE_ROOT)
        fallback = next(agent for agent in agents if agent.get("slug") == "ceo-openclaw")

        self.assertEqual(fallback["adapterType"], "openclaw_gateway")
        self.assertEqual(fallback["reportsTo"], "ceo-hermes")

    def test_setup_runtime_defaults_to_hermes(self) -> None:
        profile = setup_runtime.runtime_profile("hermes-default", "definitely-missing-hermes")

        self.assertEqual(profile["package"]["default_runtime"], "hermes-default")
        self.assertEqual(profile["package"]["fallback_runtime"], "openclaw-solo")
        self.assertEqual(profile["runtime"]["id"], "hermes-default")
        self.assertTrue(profile["runtime"]["is_default"])
        self.assertEqual(profile["runtime"]["agent_slug"], "ceo-hermes")
        self.assertEqual(profile["runtime"]["adapter_type"], "hermes_runtime")
        self.assertFalse(profile["runtime"]["binary"]["found"])
        self.assertTrue(profile["authority"]["public_safe"])
        self.assertFalse(profile["authority"]["network_install_performed"])
        self.assertFalse(profile["authority"]["service_installed"])
        self.assertFalse(profile["authority"]["secrets_loaded"])

    def test_setup_runtime_can_select_openclaw_fallback(self) -> None:
        profile = setup_runtime.runtime_profile("openclaw-solo", "definitely-missing-openclaw")

        self.assertEqual(profile["runtime"]["id"], "openclaw-solo")
        self.assertFalse(profile["runtime"]["is_default"])
        self.assertEqual(profile["runtime"]["agent_slug"], "ceo-openclaw")
        self.assertEqual(profile["runtime"]["adapter_type"], "openclaw_gateway")

    def test_setup_runtime_rejects_unknown_runtime(self) -> None:
        with self.assertRaises(setup_runtime.RuntimeSetupError):
            setup_runtime.runtime_profile("unknown-runtime")

    def test_setup_runtime_check_mode_does_not_write_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "runtime-profile.json"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = setup_runtime.main(["--check", "--profile-out", str(profile_path)])

            self.assertEqual(rc, 0)
            self.assertFalse(profile_path.exists())
            profile = json.loads(stdout.getvalue())
            self.assertEqual(profile["runtime"]["id"], "hermes-default")
            self.assertEqual(profile["runtime"]["agent_slug"], "ceo-hermes")

    def test_repo_version_file_matches_company(self) -> None:
        fields = validator.validate_company(PACKAGE_ROOT)
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()

        self.assertEqual(version, fields["version"])

    def test_agent_skill_references_are_shipped(self) -> None:
        skills = validator.validate_skills(PACKAGE_ROOT)
        agents = validator.validate_agents(PACKAGE_ROOT, skills)

        self.assertIn("engineering-execution", skills)
        self.assertIn("runtime-app-attachment", skills)
        self.assertIn("security-release-review", skills)
        for agent in agents:
            path = PACKAGE_ROOT / "agents" / agent["slug"] / "AGENTS.md"
            for skill in validator.parse_sequence_field(path, "skills"):
                self.assertIn(skill, skills)

    def test_lifecycle_dependencies_are_ordered(self) -> None:
        tasks = {task["slug"]: task for task in validator.validate_tasks(PACKAGE_ROOT)}

        self.assertEqual(tasks["research-gate"]["dependsOn"], "intent-contract")
        self.assertEqual(tasks["selection-gate"]["dependsOn"], "research-gate")
        self.assertEqual(tasks["plan-gate"]["dependsOn"], "selection-gate")
        self.assertEqual(tasks["engineering-first-primitive"]["dependsOn"], "plan-gate")
        self.assertEqual(tasks["qa-runtime-readiness"]["dependsOn"], "engineering-first-primitive")
        self.assertEqual(tasks["kpi-setup-gate"]["dependsOn"], "qa-runtime-readiness")
        self.assertEqual(tasks["marketing-gate"]["dependsOn"], "kpi-setup-gate")
        self.assertEqual(tasks["iteration-from-analytics"]["dependsOn"], "kpi-setup-gate")

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

    def test_public_operator_ui_sample_is_instantiable(self) -> None:
        ui_root = REPO_ROOT / "operator-ui"
        for name in ("index.html", "styles.css", "app.js", "sample-runtime.json"):
            self.assertTrue((ui_root / name).exists(), name)

        sample = json.loads((ui_root / "sample-runtime.json").read_text(encoding="utf-8"))
        self.assertEqual(sample["schema"], "weave-operator-ui-sample/v0.2")
        self.assertEqual(sample["runtime"]["name"], "Hermes default")
        self.assertEqual(sample["runtime"]["releaseVersion"], "2026.05.13-console")
        self.assertEqual(sample["runtime"]["externalRuntimeBoundary"], "public-safe dry-run")
        self.assertGreaterEqual(len(sample["apps"]), 3)
        self.assertEqual(sample["apps"][0]["currentStage"], "marketing")
        self.assertEqual(
            [stage["id"] for stage in sample["apps"][0]["stages"]],
            ["intent", "research", "selection", "plan", "engineering", "qa", "kpi", "marketing"],
        )
        self.assertEqual(
            [phase["id"] for phase in sample["apps"][0]["iterationLoop"]],
            ["iteration", "analysis"],
        )
        self.assertIn("approval", sample["apps"][0]["blocker"]["title"].lower())
        self.assertIn("parallel", sample["apps"][0]["summary"].lower())
        self.assertEqual(
            {card["id"] for card in sample["apps"][0]["workCards"]},
            {"plan", "review", "execute"},
        )


if __name__ == "__main__":
    unittest.main()
