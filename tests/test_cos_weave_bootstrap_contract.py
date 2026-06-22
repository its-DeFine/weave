from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "docs" / "COS_WEAVE_BOOTSTRAP.md"
SKILL = ROOT / "packages" / "weave-tool" / "skills" / "cos-weave" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
ADAPTER_PLAN = ROOT / "docs" / "WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md"
SKELETON = ROOT / "docs" / "COS_WEAVE_REPO_SKELETON.md"
SKELETON_SAMPLE = ROOT / "docs" / "samples" / "cos-weave-skeleton"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class CosWeaveBootstrapContractTests(unittest.TestCase):
    def test_prompt_first_bootstrap_surface_is_discoverable(self) -> None:
        for path in [BOOTSTRAP, SKILL, AGENTS, README, ADAPTER_PLAN, SKELETON]:
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
            "docs/COS_WEAVE_REPO_SKELETON.md",
            "announce the thread as COS WEAVE",
            "Create or load a public-safe WEAVE home automatically",
            "Search safe local/non-secret context",
            "Ask first-run owner/app questions in plain language",
            "Infer lifecycle stage from ordinary user intent",
            "Create or load the app/application workspace under WEAVE home",
            "Ask about Linear/tracker access only when the workflow needs it",
            "Use deterministic prompts/procedures for lifecycle steps",
            "Report one of `ACCEPT_FOR_SCOPE`, `REVISE`, `BLOCKED`, or `NEEDS_OWNER_ACTION`",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_default_bootstrap_read_list_excludes_symphony_adapter_plan(self) -> None:
        text = BOOTSTRAP.read_text(encoding="utf-8")
        required_block = text.split("## What The Codex Agent Must Do", 1)[1].split("## Optional Adapter Use", 1)[0]
        self.assertIn("docs/COS_WEAVE_REPO_SKELETON.md", required_block)
        self.assertNotIn("WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md", required_block)

        agents = AGENTS.read_text(encoding="utf-8")
        core_map = agents.split("## Source-Of-Truth Map", 1)[1].split("Optional/later integration references:", 1)[0]
        self.assertIn("docs/COS_WEAVE_REPO_SKELETON.md", core_map)
        self.assertNotIn("WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md", core_map)

    def test_repo_skeleton_contract_is_dead_simple_file_state(self) -> None:
        text = normalized(SKELETON)
        required = [
            "runs/cos-weave-home/",
            "apps/",
            "registry.json",
            "<app-id>/",
            "intent.md",
            "lifecycle.json",
            "todos.md",
            "worker-packets/",
            "proof/",
            "review/",
            "updates/",
            "Missing owner preferences are questions and todos, not a hard blocker",
            "Optional orchestration backends may be added later, but they are not required",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_repo_skeleton_sample_is_file_browsable_and_default_only(self) -> None:
        required = [
            "README.md",
            "apps/registry.json",
            "apps/tiny-local-calculator/app.json",
            "apps/tiny-local-calculator/intent.md",
            "apps/tiny-local-calculator/lifecycle.json",
            "apps/tiny-local-calculator/todos.md",
            "apps/tiny-local-calculator/worker-packets/WP-0001.md",
            "apps/tiny-local-calculator/proof/proof-tray.json",
            "apps/tiny-local-calculator/blockers/blocker-tray.json",
            "apps/tiny-local-calculator/review/review-queue.json",
            "apps/tiny-local-calculator/updates/readback.json",
        ]
        for rel in required:
            with self.subTest(rel=rel):
                self.assertTrue((SKELETON_SAMPLE / rel).exists(), rel)

        sample_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(SKELETON_SAMPLE.rglob("*"))
            if path.is_file()
        )
        self.assertIn("tiny local calculator", sample_text.lower())
        self.assertIn("observe -> validate -> govern -> review -> sync", sample_text)
        self.assertNotIn("Symphony", sample_text)

    def test_bootstrap_contract_does_not_make_symphony_default_acceptance(self) -> None:
        text = normalized(BOOTSTRAP)
        self.assertIn("The default vNext product surface is a visible file/folder skeleton", text)
        self.assertIn("Scope=local-file-skeleton", text)
        self.assertIn("ordinary or vague intent", text)
        self.assertIn("app state", text)
        required_block = BOOTSTRAP.read_text(encoding="utf-8").split("## What The Codex Agent Must Do", 1)[1].split("## Required Non-Claims", 1)[0]
        self.assertNotIn("Symphony", required_block)
        self.assertNotIn("adapter", required_block.lower())

    def test_bootstrap_contract_blocks_manual_setup_user_work(self) -> None:
        text = normalized(BOOTSTRAP)
        forbidden_user_work = [
            "run a WEAVE command",
            "name a lifecycle stage",
            "create folders",
            "dispatch a worker",
            "paste a long internal prompt",
            "avoid manual commands/manual lifecycle requirements",
        ]
        for phrase in forbidden_user_work:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_non_claims_and_blocked_states_are_explicit(self) -> None:
        text = normalized(BOOTSTRAP)
        required = [
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
        self.assertIn("Repo-local helpers may be used by the agent as implementation details", text)
        self.assertIn("They are not the product UX", text)
        self.assertIn("Do not make the user run WEAVE commands", text)
        self.assertIn("Stop at live/public/paid/credential/destructive gates without approval", text)


if __name__ == "__main__":
    unittest.main()
