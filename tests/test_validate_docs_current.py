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

    def test_canonical_user_prompt_is_checked(self) -> None:
        self.assertEqual(
            validate_docs_current.CANONICAL_USER_PROMPT,
            "Use WEAVE release v0.1.0 from https://github.com/its-DeFine/weave.git. I want to build <ordinary app intent>.",
        )

    def test_readme_first_contact_and_deployment_gate_validate(self) -> None:
        self.assertEqual(validate_docs_current.check_first_contact_readme(ROOT), [])

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

    def test_first_contact_check_requires_cloudflare_vercel_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text(
                "## First Contact\n"
                f"{validate_docs_current.CANONICAL_USER_PROMPT}\n"
                f"{validate_docs_current.LAUNCHER_PREFIX}\n"
                "The user provides: intent.\n"
                "The agent does automatically: creates or loads `runs/cos-weave-home/`, app state, proof, readback.\n"
                "## Default File-Skeleton State\n",
                encoding="utf-8",
            )
            (root / "COS_WEAVE_FIRST_CONTACT.md").write_text(
                validate_docs_current.CANONICAL_USER_PROMPT,
                encoding="utf-8",
            )
            (root / "COS_WEAVE_LAUNCHER.md").write_text(
                validate_docs_current.CANONICAL_USER_PROMPT,
                encoding="utf-8",
            )

            findings = validate_docs_current.check_first_contact_readme(root)

        self.assertTrue(any("Deployment Gates" in finding for finding in findings))

    def test_first_contact_check_allows_wrapped_deployment_gate_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text(
                "## First Contact\n"
                f"{validate_docs_current.CANONICAL_USER_PROMPT}\n"
                f"{validate_docs_current.LAUNCHER_PREFIX}\n"
                "The user provides: intent.\n"
                "The agent does automatically: creates or loads `runs/cos-weave-home/`, app state, proof, readback.\n"
                "## Default File-Skeleton State\n"
                "## Deployment Gates\n"
                "Cloudflare and Vercel are not required for intent capture,\n"
                "planning, or local engineering. Stop before DNS changes,\n"
                "provider mutations, and production deploys. Do not paste raw\n"
                "Cloudflare, Vercel, DNS, OAuth, API, or service credentials into chat.\n"
                "## Visual Model\n",
                encoding="utf-8",
            )
            (root / "COS_WEAVE_FIRST_CONTACT.md").write_text(
                validate_docs_current.CANONICAL_USER_PROMPT,
                encoding="utf-8",
            )
            (root / "COS_WEAVE_LAUNCHER.md").write_text(
                validate_docs_current.CANONICAL_USER_PROMPT,
                encoding="utf-8",
            )

            findings = validate_docs_current.check_first_contact_readme(root)

        self.assertEqual(findings, [])

    def test_cli_surface_check_rejects_stale_help_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bin_dir = root / "bin"
            scripts_dir = root / "scripts"
            bin_dir.mkdir()
            scripts_dir.mkdir()
            (scripts_dir / "weave_cli.py").write_text("# placeholder\n", encoding="utf-8")
            wrapper = bin_dir / "weave"
            wrapper.write_text("#!/usr/bin/env sh\necho 'cos-bootstrap readback eval onboard'\n", encoding="utf-8")
            wrapper.chmod(0o755)

            findings = validate_docs_current.check_public_cli_surface(root)

        self.assertTrue(any("stale command" in finding for finding in findings))

    def test_root_dotfile_check_rejects_unused_build_context_ignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".dockerignore").write_text("runs\n", encoding="utf-8")

            findings = validate_docs_current.check_root_dotfiles(root)

        self.assertEqual(
            findings,
            [".dockerignore exists but current vNext has no container build-context command"],
        )

    def test_research_product_contract_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs" / "samples" / "cos-weave-skeleton" / "procedures" / "lifecycle").mkdir(parents=True)
            (root / "packages" / "weave-tool" / "evals" / "lifecycle").mkdir(parents=True)
            (root / "packages" / "weave-tool" / "skills" / "primitive-market-research").mkdir(parents=True)
            (root / "packages" / "weave-tool" / "skills" / "weave-lifecycle").mkdir(parents=True)
            (root / "docs" / "COS_WEAVE_REPO_SKELETON.md").write_text("Research only checks feasibility.\n", encoding="utf-8")
            (root / "docs" / "samples" / "cos-weave-skeleton" / "procedures" / "lifecycle" / "02-research.md").write_text(
                "Research Procedure\n",
                encoding="utf-8",
            )
            (root / "packages" / "weave-tool" / "evals" / "lifecycle" / "research.yaml").write_text(
                '{"stage":"Research"}\n',
                encoding="utf-8",
            )
            (root / "packages" / "weave-tool" / "skills" / "primitive-market-research" / "SKILL.md").write_text(
                "market skill\n",
                encoding="utf-8",
            )
            (root / "packages" / "weave-tool" / "skills" / "weave-lifecycle" / "SKILL.md").write_text(
                "lifecycle skill\n",
                encoding="utf-8",
            )

            findings = validate_docs_current.check_research_product_contract(root)

        self.assertGreaterEqual(len(findings), 5)
        self.assertTrue(any("product-market facts" in finding for finding in findings))
        self.assertTrue(any("not_technical_feasibility_only" in finding for finding in findings))

    def test_deployment_provider_gate_docs_require_sample_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs" / "samples" / "cos-weave-skeleton" / "apps" / "tiny-local-calculator"
            docs.mkdir(parents=True)
            for rel in [
                "README.md",
                "docs/COS_WEAVE_REPO_SKELETON.md",
                "docs/COS_WEAVE_BOOTSTRAP.md",
                "docs/COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md",
                "packages/weave-tool/skills/cos-weave/SKILL.md",
            ]:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    "deployment-gates.json Cloudflare Vercel connector MCP brokered secret_ref deployment blocked launch blocked",
                    encoding="utf-8",
                )

            findings = validate_docs_current.check_deployment_provider_gates(root)

        self.assertEqual(
            findings,
            [
                "sample missing deployment gate state: docs/samples/cos-weave-skeleton/apps/tiny-local-calculator/deployment-gates.json",
            ],
        )


if __name__ == "__main__":
    unittest.main()
