from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "docs" / "COS_WEAVE_BOOTSTRAP.md"
SKILL = ROOT / "packages" / "weave-tool" / "skills" / "cos-weave" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
ADAPTER_PLAN = ROOT / "docs" / "WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class CosWeaveBootstrapContractTests(unittest.TestCase):
    def test_prompt_first_bootstrap_surface_is_discoverable(self) -> None:
        for path in [BOOTSTRAP, SKILL, AGENTS, README, ADAPTER_PLAN]:
            text = normalized(path)
            with self.subTest(path=path):
                self.assertIn("COS WEAVE", text)
                self.assertIn("repo", text.lower())

        bootstrap = normalized(BOOTSTRAP)
        self.assertIn("Use this repo as COS WEAVE: <WEAVE repo URL or local path>", bootstrap)
        self.assertIn("The user should not need to run a WEAVE command", bootstrap)
        self.assertIn("What The Codex Agent Must Do", bootstrap)

    def test_generic_agent_has_enough_steps_from_repo_path_and_intent(self) -> None:
        text = normalized(BOOTSTRAP)
        required = [
            "Open or clone the WEAVE source",
            "Read `AGENTS.md`, this file",
            "Announce the thread as COS WEAVE",
            "Create or load a public-safe WEAVE home automatically",
            "Search safe local/non-secret context",
            "Ask first-run owner/app questions in plain language",
            "Infer lifecycle stage from ordinary user intent",
            "Create or load the app/application workspace under WEAVE home",
            "Ask about Linear/tracker access only when the workflow needs it",
            "Use deterministic prompts/procedures for lifecycle steps",
            "Use the WEAVE-to-Symphony adapter only when orchestration is explicitly selected",
            "Report one of `ACCEPT_FOR_SCOPE`, `REVISE`, `BLOCKED`, or `NEEDS_OWNER_ACTION`",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_bootstrap_contract_does_not_make_symphony_default_acceptance(self) -> None:
        text = normalized(BOOTSTRAP)
        self.assertIn("Symphony is optional later orchestration infrastructure, not a default first-run requirement", text)
        self.assertIn("This does not prove the default first-run product flow by itself", text)
        self.assertIn("ordinary or vague intent", text)
        self.assertIn("app state", text)

    def test_bootstrap_contract_blocks_manual_symfony_adapter_user_work(self) -> None:
        text = normalized(BOOTSTRAP)
        forbidden_user_work = [
            "name a lifecycle stage",
            "create a queue root",
            "dispatch a worker",
            "understand Symphony",
            "paste a long internal prompt",
            "`weave_symphony_adapter.py`",
            "queue-root setup commands",
            "dispatch commands",
            "proof-envelope commands",
            "Symphony service commands",
            "lifecycle classification commands",
        ]
        for phrase in forbidden_user_work:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_non_claims_and_blocked_states_are_explicit(self) -> None:
        text = normalized(BOOTSTRAP)
        required = [
            "no live Symphony service execution",
            "no live Codex app-server execution",
            "no live tracker or Linear mutation",
            "no production deploy",
            "no public send",
            "no billing, payment, or paid call",
            "no credential access or secret handling",
            "Return `BLOCKED` or `NEEDS_OWNER_ACTION`, not a traceback",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_skill_says_internal_commands_are_not_product_ux(self) -> None:
        text = normalized(SKILL)
        self.assertIn("Repo-local commands and adapter helpers may be used by the agent as implementation details", text)
        self.assertIn("They are not the product UX", text)
        self.assertIn("Do not make the user run WEAVE commands", text)
        self.assertIn("Do not require Symphony for default first-run COS WEAVE", text)


if __name__ == "__main__":
    unittest.main()
