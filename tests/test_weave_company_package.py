from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import shutil
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
        self.assertEqual(summary.task_count, 10)
        self.assertEqual(summary.skill_count, 13)
        self.assertEqual(summary.primitive_count, 9)
        self.assertEqual(summary.prompt_pack_count, 1)
        self.assertEqual(summary.eval_contract_count, 12)

    def test_hermes_is_the_default_ceo(self) -> None:
        agents = validator.validate_agents(PACKAGE_ROOT)
        ceos = [agent for agent in agents if agent.get("reportsTo") == "null"]

        self.assertEqual(len(ceos), 1)
        self.assertEqual(ceos[0]["slug"], "ceo-hermes")
        self.assertEqual(ceos[0]["adapterType"], "hermes_runtime")
        self.assertEqual(ceos[0]["promptPack"], "hermes-gestalt-runtime-pack")

    def test_company_declares_hermes_default_runtime(self) -> None:
        fields = validator.validate_company(PACKAGE_ROOT)

        self.assertEqual(fields["runtime"], "hermes-default")
        self.assertEqual(fields["runtimeFallback"], "local-fallback")
        self.assertEqual(fields["version"], "2026.05.13-console")
        self.assertEqual(fields["releaseDate"], "2026-05-13")
        self.assertEqual(fields["releaseTag"], "v2026.05.13-console")

    def test_local_fallback_remains_fallback_runtime(self) -> None:
        agents = validator.validate_agents(PACKAGE_ROOT)
        fallback = next(agent for agent in agents if agent.get("slug") == "ceo-fallback")

        self.assertEqual(fallback["adapterType"], "local_fallback_gateway")
        self.assertEqual(fallback["reportsTo"], "ceo-hermes")

    def test_setup_runtime_defaults_to_hermes(self) -> None:
        profile = setup_runtime.runtime_profile("hermes-default", "definitely-missing-hermes")

        self.assertEqual(profile["package"]["default_runtime"], "hermes-default")
        self.assertEqual(profile["package"]["fallback_runtime"], "local-fallback")
        self.assertEqual(profile["runtime"]["id"], "hermes-default")
        self.assertTrue(profile["runtime"]["is_default"])
        self.assertEqual(profile["runtime"]["agent_slug"], "ceo-hermes")
        self.assertEqual(profile["runtime"]["adapter_type"], "hermes_runtime")
        self.assertFalse(profile["runtime"]["binary"]["found"])
        adapter_contract = profile["runtime"]["adapter_contract"]
        self.assertEqual(adapter_contract["schema"], "weave-agent-runtime-contract/v0.1")
        self.assertEqual(adapter_contract["runtime_id"], "hermes-default")
        self.assertEqual(adapter_contract["support_state"], "supported_unproven")
        self.assertTrue(adapter_contract["methods"]["invoke"]["implemented"])
        self.assertTrue(adapter_contract["methods"]["capture_turn"]["implemented"])
        self.assertEqual(profile["agent_runtime_catalog"]["runtimes"]["codex"]["support_state"], "unsupported")
        self.assertEqual(profile["runtime_home"]["schema"], "weave-runtime-home/v0.1")
        self.assertIn("weave-state", profile["runtime_home"]["weave_state_path"])
        self.assertIn("hermes-home", profile["runtime_home"]["hermes_home_path"])
        self.assertIn("not exported by default", profile["runtime_home"]["secret_migration_policy"])
        self.assertTrue(profile["authority"]["public_safe"])
        self.assertFalse(profile["authority"]["network_install_performed"])
        self.assertFalse(profile["authority"]["service_installed"])
        self.assertFalse(profile["authority"]["secrets_loaded"])
        self.assertEqual(profile["authority"]["autonomy"]["mode"], "yolo")
        self.assertTrue(profile["authority"]["autonomy"]["llm_must_request_owner_authorization_for_hard_gates"])
        self.assertEqual(profile["gateway"]["channel"], "telegram")
        self.assertTrue(profile["gateway"]["setup_required"])
        self.assertEqual(profile["gateway"]["setup_command"], "scripts/setup_runtime.py --gateway-token-file")
        self.assertEqual(profile["gateway"]["standalone_setup_command"], "scripts/setup_gateway.py")
        self.assertFalse(profile["gateway"]["token_loaded"])
        self.assertFalse(profile["gateway"]["allowlist_configured"])
        self.assertIsNone(profile["gateway"]["allowlist_mode"])
        self.assertFalse(profile["gateway"]["paired"])
        self.assertFalse(profile["gateway"]["gateway_started"])
        self.assertEqual(profile["gateway"]["autonomy_mode"], "yolo")
        self.assertTrue(profile["foundation_onboarding"]["setup_required"])
        self.assertFalse(profile["foundation_onboarding"]["active"])
        self.assertEqual(profile["foundation_onboarding"]["question_limit"], 3)

    def test_setup_runtime_can_select_local_fallback(self) -> None:
        profile = setup_runtime.runtime_profile("local-fallback", "definitely-missing-local-fallback")

        self.assertEqual(profile["runtime"]["id"], "local-fallback")
        self.assertFalse(profile["runtime"]["is_default"])
        self.assertEqual(profile["runtime"]["agent_slug"], "ceo-fallback")
        self.assertEqual(profile["runtime"]["adapter_type"], "local_fallback_gateway")
        self.assertEqual(profile["runtime"]["adapter_contract"]["support_state"], "fallback_contract_only")
        self.assertFalse(profile["runtime"]["adapter_contract"]["methods"]["invoke"]["implemented"])

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
            self.assertTrue(profile["gateway"]["setup_required"])
            self.assertTrue(profile["foundation_onboarding"]["setup_required"])

    def test_setup_runtime_creates_foundation_onboarding_workdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_path = root / "runtime-profile.json"
            weave_root = root / "weave-root"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = setup_runtime.main(
                    [
                        "--profile-out",
                        str(profile_path),
                        "--weave-root",
                        str(weave_root),
                        "--foundation-app-id",
                        "Demo App",
                        "--foundation-app-name",
                        "Demo App",
                    ]
                )

            self.assertEqual(rc, 0)
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(profile["runtime_home"]["profile_path"], str(profile_path.resolve()))
            foundation = profile["foundation_onboarding"]
            self.assertTrue(foundation["active"])
            self.assertEqual(foundation["app_id"], "demo-app")
            self.assertFalse(foundation["gate_passed"])
            self.assertTrue(Path(foundation["foundation_gate_path"]).exists())
            self.assertTrue((Path(foundation["gateway_workdir"]) / "AGENTS.md").exists())
            agents = (Path(foundation["gateway_workdir"]) / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Unskippable Foundation Gate", agents)
            self.assertIn("Autonomy mode: `yolo`", agents)
            self.assertIn("Telegram", agents)
            self.assertEqual(profile["authority"]["autonomy"]["mode"], "yolo")
            self.assertIn("foundation_onboarding_active: true", stdout.getvalue())
            self.assertIn("autonomy_mode: yolo", stdout.getvalue())

    def test_setup_runtime_configures_gateway_context_for_single_allowed_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_path = root / "runtime-profile.json"
            weave_root = root / "weave-root"
            hermes_home = root / "hermes"
            bot_file = root / "telegram.secret"
            bot_secret = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
            bot_file.write_text(bot_secret + "\n", encoding="utf-8")
            hermes_home.mkdir()
            (hermes_home / "config.yaml").write_text(
                "model:\n"
                "  provider: openai-codex\n"
                "  default: gpt-5.5\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = setup_runtime.main(
                    [
                        "--profile-out",
                        str(profile_path),
                        "--weave-root",
                        str(weave_root),
                        "--gateway-hermes-home",
                        str(hermes_home),
                        "--gateway-token-file",
                        str(bot_file),
                        "--gateway-allowed-users",
                        "12345",
                    ]
                )

            self.assertEqual(rc, 0)
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            env_text = (hermes_home / ".env").read_text(encoding="utf-8")
            self.assertIn("TELEGRAM_HOME_CHANNEL=12345", env_text)
            self.assertIn("WEAVE_AUTONOMY_MODE=yolo", env_text)
            gateway = profile["gateway"]
            self.assertTrue(gateway["runtime_config_written"])
            self.assertTrue(gateway["terminal_cwd_configured"])
            self.assertTrue(gateway["agent_system_prompt_configured"])
            self.assertTrue(gateway["weave_plugin_installed"])
            self.assertTrue(gateway["weave_plugin_enabled"])
            config_text = (hermes_home / "config.yaml").read_text(encoding="utf-8")
            config = setup_runtime._load_yaml_config(hermes_home / "config.yaml")
            self.assertIn("terminal:", config_text)
            self.assertEqual(config["model"]["provider"], "openai-codex")
            self.assertEqual(config["plugins"]["enabled"], ["weave-runtime"])
            self.assertIn(str(Path(profile["foundation_onboarding"]["gateway_workdir"]).resolve()), config_text)
            self.assertIn("WEAVE foundation onboarding is mandatory", config_text)
            self.assertIn("Autonomy mode is `yolo`", config_text)
            self.assertIn("hard approval gate", config_text)
            self.assertIn("gateway_home_channel_configured: true", stdout.getvalue())

    def test_setup_runtime_can_configure_gateway_from_approved_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_path = root / "runtime-profile.json"
            hermes_home = root / "hermes"
            bot_file = root / "telegram.secret"
            bot_secret = "123456789:abcdefghijklmnopqrstuvwxyzABCDEF"
            bot_file.write_text(bot_secret + "\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = setup_runtime.main(
                    [
                        "--profile-out",
                        str(profile_path),
                        "--skip-weave-root",
                        "--gateway-hermes-home",
                        str(hermes_home),
                        "--gateway-token-file",
                        str(bot_file),
                        "--gateway-allowed-users",
                        "12345,67890",
                    ]
                )

            self.assertEqual(rc, 0)
            self.assertNotIn(bot_secret, stdout.getvalue())
            env_text = (hermes_home / ".env").read_text(encoding="utf-8")
            self.assertIn(f"TELEGRAM_BOT_TOKEN={bot_secret}", env_text)
            self.assertIn("TELEGRAM_ALLOWED_USERS=12345,67890", env_text)
            self.assertIn("WEAVE_AUTONOMY_MODE=yolo", env_text)
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertTrue(profile["gateway"]["token_loaded"])
            self.assertTrue(profile["gateway"]["allowlist_configured"])
            self.assertEqual(profile["gateway"]["allowlist_mode"], "allowed_users")
            self.assertEqual(profile["gateway"]["autonomy_mode"], "yolo")
            self.assertFalse(profile["gateway"]["gateway_started"])

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
        self.assertIn("gestalt-runtime", skills)
        for agent in agents:
            path = PACKAGE_ROOT / "agents" / agent["slug"] / "AGENTS.md"
            for skill in validator.parse_sequence_field(path, "skills"):
                self.assertIn(skill, skills)

    def test_hermes_prompt_pack_is_shipped_and_valid(self) -> None:
        self.assertEqual(validator.validate_prompt_packs(PACKAGE_ROOT), 1)

    def test_primitive_registry_is_cross_application_not_askuno_manifest(self) -> None:
        registry = json.loads((PACKAGE_ROOT / "primitives" / "registry.json").read_text(encoding="utf-8"))

        self.assertEqual(validator.validate_primitives(PACKAGE_ROOT), 9)
        self.assertEqual(registry["application"], "weave-lifecycle-runtime")
        self.assertEqual(registry["registryScope"], "cross-application-lifecycle-primitives")
        self.assertNotEqual(registry["application"], "askuno-runtime-proof")

    def test_lifecycle_eval_contracts_are_shipped_and_valid(self) -> None:
        self.assertEqual(validator.validate_eval_contracts(PACKAGE_ROOT), 12)

    def test_qa_eval_contract_requires_runtime_teardown_policy_and_resource_states(self) -> None:
        contract = json.loads((PACKAGE_ROOT / "evals" / "lifecycle" / "qa.yaml").read_text(encoding="utf-8"))
        runtime_qa = contract["runtime_agent_qa"]

        self.assertTrue(runtime_qa["teardown_policy_required"])
        self.assertEqual(runtime_qa["manifest_schema"], "weave.runtime-qa-manifest/v0.1")
        self.assertEqual(runtime_qa["cleanup_policy_schema"], "weave.runtime-cleanup-policy/v0.1")
        self.assertTrue(validator.REQUIRED_RUNTIME_QA_RESOURCE_STATES.issubset(runtime_qa["resource_states_required"]))
        self.assertIn("runtime resource lifecycle manifest when applicable", contract["required_inputs"])
        self.assertIn("teardown policy and cleanup evidence when applicable", contract["required_inputs"])

    def test_validate_eval_contracts_rejects_runtime_qa_without_teardown_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shutil.copytree(PACKAGE_ROOT / "evals", root / "evals")
            qa_path = root / "evals" / "lifecycle" / "qa.yaml"
            contract = json.loads(qa_path.read_text(encoding="utf-8"))
            contract["runtime_agent_qa"]["teardown_policy_required"] = False
            qa_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaises(validator.PackageValidationError):
                validator.validate_eval_contracts(root)

    def test_validate_eval_contracts_rejects_runtime_qa_missing_resource_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shutil.copytree(PACKAGE_ROOT / "evals", root / "evals")
            qa_path = root / "evals" / "lifecycle" / "qa.yaml"
            contract = json.loads(qa_path.read_text(encoding="utf-8"))
            contract["runtime_agent_qa"]["resource_states_required"].remove("teardown_requested")
            qa_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaises(validator.PackageValidationError):
                validator.validate_eval_contracts(root)

    def test_lifecycle_dependencies_are_ordered(self) -> None:
        tasks = {task["slug"]: task for task in validator.validate_tasks(PACKAGE_ROOT)}

        self.assertEqual(tasks["research-gate"]["dependsOn"], "intent-contract")
        self.assertEqual(tasks["selection-gate"]["dependsOn"], "research-gate")
        self.assertEqual(tasks["plan-gate"]["dependsOn"], "selection-gate")
        self.assertEqual(tasks["engineering-first-primitive"]["dependsOn"], "plan-gate")
        self.assertEqual(tasks["qa-runtime-readiness"]["dependsOn"], "engineering-first-primitive")
        self.assertEqual(tasks["deployment-readiness-gate"]["dependsOn"], "qa-runtime-readiness")
        self.assertEqual(tasks["kpi-setup-gate"]["dependsOn"], "deployment-readiness-gate")
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

    def test_telegram_slash_command_contract_is_documented(self) -> None:
        docs = (REPO_ROOT / "docs" / "telegram-slash-commands.md").read_text(encoding="utf-8")
        for command in setup_runtime.weave_runtime_slice.TELEGRAM_COMMANDS:
            self.assertIn(command, docs)
        self.assertIn("llm_used: false", docs)
        self.assertIn("deterministic: true", docs)
        self.assertIn("/autonomy", docs)


if __name__ == "__main__":
    unittest.main()
