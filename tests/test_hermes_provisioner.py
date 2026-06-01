from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROVISIONER_PATH = REPO_ROOT / "scripts" / "provision_hermes.py"
SETUP_RUNTIME_PATH = REPO_ROOT / "scripts" / "setup_runtime.py"

if str(PROVISIONER_PATH.parent) not in sys.path:
    sys.path.insert(0, str(PROVISIONER_PATH.parent))

provision_spec = importlib.util.spec_from_file_location("provision_hermes", PROVISIONER_PATH)
assert provision_spec is not None
provision_hermes = importlib.util.module_from_spec(provision_spec)
assert provision_spec.loader is not None
sys.modules[provision_spec.name] = provision_hermes
provision_spec.loader.exec_module(provision_hermes)

setup_spec = importlib.util.spec_from_file_location("setup_runtime_for_hermes_tests", SETUP_RUNTIME_PATH)
assert setup_spec is not None
setup_runtime = importlib.util.module_from_spec(setup_spec)
assert setup_spec.loader is not None
sys.modules[setup_spec.name] = setup_runtime
setup_spec.loader.exec_module(setup_runtime)


def run(command: list[str], *, cwd: Path) -> str:
    result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def create_fake_hermes_repo(root: Path) -> tuple[Path, str]:
    repo = root / "fake-hermes"
    repo.mkdir()
    (repo / "hermes_cli").mkdir()
    (repo / "hermes_cli" / "__init__.py").write_text(
        '__version__ = "0.0.0-test"\n__release_date__ = "2026-05-30"\n',
        encoding="utf-8",
    )
    (repo / "hermes_cli" / "main.py").write_text(
        "def main():\n"
        "    print('Hermes Agent v0.0.0-test')\n",
        encoding="utf-8",
    )
    (repo / "run_agent.py").write_text("def main():\n    return None\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        '[project]\n'
        'name = "hermes-agent"\n'
        'version = "0.0.0-test"\n'
        'requires-python = ">=3.11"\n'
        '\n'
        '[project.scripts]\n'
        'hermes = "hermes_cli.main:main"\n'
        'hermes-agent = "run_agent:main"\n',
        encoding="utf-8",
    )
    run(["git", "init", "-q"], cwd=repo)
    run(["git", "config", "user.email", "weave@example.invalid"], cwd=repo)
    run(["git", "config", "user.name", "WEAVE Test"], cwd=repo)
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-q", "-m", "fake hermes"], cwd=repo)
    commit = run(["git", "rev-parse", "HEAD"], cwd=repo)
    return repo, commit


class HermesProvisionerTests(unittest.TestCase):
    def test_provisioner_clones_and_verifies_pinned_source_without_services(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fake_repo, commit = create_fake_hermes_repo(root)
            profile_path = root / "profile.json"

            profile = provision_hermes.provision_hermes(
                install_root=root / "install",
                repo_url="https://github.com/NousResearch/hermes-agent.git",
                commit=commit,
                source_repo=fake_repo,
                install_deps=False,
                profile_path=profile_path,
            )

            self.assertTrue(profile_path.exists())
            self.assertEqual(profile["schema"], provision_hermes.PROFILE_SCHEMA)
            self.assertEqual(profile["upstream"]["checked_out_commit"], commit)
            self.assertTrue(profile["status"]["source_verified"])
            self.assertFalse(profile["status"]["dependencies_installed"])
            self.assertFalse(profile["status"]["binary_present"])
            self.assertFalse(profile["authority"]["service_installed"])
            self.assertFalse(profile["authority"]["shell_startup_mutated"])
            self.assertFalse(profile["authority"]["secrets_loaded"])
            self.assertFalse(profile["authority"]["gateway_paired"])
            self.assertFalse(profile["authority"]["setup_wizard_ran"])

    def test_setup_runtime_can_provision_hermes_source_and_record_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fake_repo, commit = create_fake_hermes_repo(root)
            runtime_profile = root / "runtime-profile.json"
            hermes_profile = root / "hermes-profile.json"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                rc = setup_runtime.main(
                    [
                        "--install-hermes",
                        "--hermes-source-repo",
                        str(fake_repo),
                        "--hermes-commit",
                        commit,
                        "--hermes-no-install-deps",
                        "--hermes-install-root",
                        str(root / "install"),
                        "--hermes-profile-out",
                        str(hermes_profile),
                        "--profile-out",
                        str(runtime_profile),
                        "--skip-weave-root",
                    ]
                )

            self.assertEqual(rc, 0)
            self.assertIn("hermes_provisioned: true", stdout.getvalue())
            profile = json.loads(runtime_profile.read_text(encoding="utf-8"))
            self.assertEqual(profile["runtime"]["id"], "hermes-default")
            self.assertFalse(profile["runtime"]["binary"]["found"])
            self.assertTrue(profile["authority"]["network_install_performed"])
            self.assertTrue(profile["gateway"]["setup_required"])
            self.assertFalse(profile["gateway"]["gateway_started"])
            self.assertTrue(profile["hermes_provision"]["source_verified"])
            self.assertFalse(profile["hermes_provision"]["binary_present"])
            self.assertEqual(profile["hermes_provision"]["checked_out_commit"], commit)


if __name__ == "__main__":
    unittest.main()
