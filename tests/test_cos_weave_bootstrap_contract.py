from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "docs" / "COS_WEAVE_BOOTSTRAP.md"
SKILL = ROOT / "packages" / "weave-tool" / "skills" / "cos-weave" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
FIRST_CONTACT = ROOT / "COS_WEAVE_FIRST_CONTACT.md"
LAUNCHER = ROOT / "COS_WEAVE_LAUNCHER.md"
SKELETON = ROOT / "docs" / "COS_WEAVE_REPO_SKELETON.md"
SKELETON_SAMPLE = ROOT / "docs" / "samples" / "cos-weave-skeleton"
DOCS_INDEX = ROOT / "docs" / "README.md"
LEGACY_SURFACES = ROOT / "docs" / "WEAVE_LEGACY_SURFACES.md"

FIRST_LINE_TEMPLATE = (
    "WEAVE | Home=<repo>/runs/cos-weave-home | App=<app-or-pending> | "
    "Stage=<stage> | Scope=local-file-skeleton | State=<state> | Next=<next action>"
)


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class CosWeaveBootstrapContractTests(unittest.TestCase):
    def test_prompt_first_bootstrap_surface_is_discoverable(self) -> None:
        for path in [BOOTSTRAP, SKILL, AGENTS, README, FIRST_CONTACT, LAUNCHER, SKELETON, LEGACY_SURFACES]:
            text = normalized(path)
            with self.subTest(path=path):
                self.assertIn("COS WEAVE", text)
                self.assertIn("repo", text.lower())

        bootstrap = normalized(BOOTSTRAP)
        self.assertIn("Use this repo as COS WEAVE: <WEAVE repo URL or local path>", bootstrap)
        self.assertIn("The user should not need to run a WEAVE command", bootstrap)
        self.assertIn("What The Codex Agent Must Do", bootstrap)

    def test_first_contact_contract_is_in_top_40_lines_of_readme_and_agents(self) -> None:
        for path in [README, AGENTS]:
            top_40 = "\n".join(path.read_text(encoding="utf-8").splitlines()[:40])
            with self.subTest(path=path):
                self.assertIn("Use this repo as COS WEAVE", top_40)
                self.assertIn(FIRST_LINE_TEMPLATE, top_40)
                self.assertIn("before any execution packet", top_40)
                self.assertIn("Do not start with `Execution packet`", top_40)
                self.assertIn("Scope=local-file-skeleton", top_40)

    def test_launcher_documents_projectless_remote_url_boot_order(self) -> None:
        text = LAUNCHER.read_text(encoding="utf-8")
        normalized_text = normalized(LAUNCHER)
        required = [
            "projectless Codex",
            "remote repository URL is not loaded before",
            "Before any commentary or execution packet",
            "open or clone this repository",
            "COS_WEAVE_FIRST_CONTACT.md",
            "AGENTS.md",
            "docs/COS_WEAVE_BOOTSTRAP.md",
            FIRST_LINE_TEMPLATE,
            "runs/cos-weave-home/",
            "todos.md",
            "No external orchestrator is required",
            "Validator Prompts",
            "Repo-scoped/local thread expected to work",
            "Projectless remote-URL thread expected to use the tiny launcher prompt",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        for phrase in ["manual lifecycle classification", "live tracker or Linear mutation", "production deployment"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, normalized_text)
        self.assertIn(
            "URL-only cannot control pre-read first contact in generic projectless Codex",
            normalized_text,
        )

    def test_docs_do_not_overclaim_url_only_pre_read_determinism(self) -> None:
        for path in [README, AGENTS, FIRST_CONTACT, BOOTSTRAP, LAUNCHER]:
            text = normalized(path)
            with self.subTest(path=path):
                self.assertIn("remote", text.lower())
                self.assertIn("first", text.lower())
        self.assertIn("A remote URL alone cannot deterministically change the first progress message", normalized(README))
        self.assertIn("A remote URL alone cannot reliably control pre-read first contact", normalized(AGENTS))
        self.assertIn("Remote URL-only startup cannot deterministically control", normalized(FIRST_CONTACT))
        self.assertIn("URL-only cannot control pre-read first contact in generic projectless Codex", normalized(SKILL))

    def test_first_contact_contract_is_repeated_in_skill_and_bootstrap(self) -> None:
        for path in [SKILL, BOOTSTRAP, FIRST_CONTACT]:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("Use this repo as COS WEAVE: <repo URL or local path>", text)
                self.assertIn(FIRST_LINE_TEMPLATE, text)
                self.assertIn("Do not start with `Execution packet`", text)
                self.assertIn("WEAVE-shaped", text)

    def test_default_readme_path_is_file_skeleton_before_advanced_runtime(self) -> None:
        text = README.read_text(encoding="utf-8")
        default_block = text.split("## Advanced/Legacy Runtime And TUI Surfaces", 1)[0]
        required = [
            "Default File-Skeleton State",
            "runs/cos-weave-home/",
            "lifecycle.json",
            "todos.md",
            "worker-packets/",
            "proof/",
            "blockers/",
            "review/",
            "updates/readback.json",
            "not the user-facing first-run path",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, default_block)
        forbidden = [
            "Before onboarding, pick one deployment mode",
            "bin/weave tui",
            "Managed container",
            "external orchestrator setup",
            "managed runtime setup",
        ]
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, default_block)

    def test_quickstart_and_docs_index_make_file_skeleton_default(self) -> None:
        quickstart_top = "\n".join((ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8").splitlines()[:80])
        docs_index_top = "\n".join(DOCS_INDEX.read_text(encoding="utf-8").splitlines()[:60])
        for phrase in [
            "file-skeleton-first",
            "runs/cos-weave-home/",
            "lifecycle.json",
            "todos.md",
            "worker-packets/",
            "updates/readback.json",
        ]:
            with self.subTest(surface="quickstart", phrase=phrase):
                self.assertIn(phrase, quickstart_top)
        for phrase in ["managed container", "existing-Hermes", "bin/weave tui", "external orchestrator setup"]:
            with self.subTest(surface="quickstart", phrase=phrase):
                self.assertNotIn(phrase, quickstart_top)
        self.assertIn("Default vNext reading order", docs_index_top)
        self.assertIn("COS WEAVE Launcher", docs_index_top)
        self.assertIn("COS WEAVE Repo Skeleton", docs_index_top)
        self.assertIn("lifecycle.json", docs_index_top)
        self.assertIn("worker-packets/", docs_index_top)
        self.assertIn("optional advanced references", docs_index_top)
        self.assertNotIn("orchestration-adapter", docs_index_top)

    def test_docs_index_current_section_excludes_legacy_runtime_surfaces(self) -> None:
        text = DOCS_INDEX.read_text(encoding="utf-8")
        current_section = text.split("## Current COS WEAVE vNext docs", 1)[1].split(
            "## Proof, dogfood, and optional legacy runtime workflow map", 1
        )[0]
        legacy_section = text.split("## Advanced/legacy integration references", 1)[1]

        for phrase in ["Hermes", "Runtime Home", "TUI", "Textual", "WEAVE Runtime"]:
            with self.subTest(section="current", phrase=phrase):
                self.assertNotIn(phrase, current_section)

        for phrase in ["Hermes Runtime Setup", "Runtime Home Contract", "WEAVE Runtime", "Legacy Surface Inventory"]:
            with self.subTest(section="legacy", phrase=phrase):
                self.assertIn(phrase, legacy_section)

    def test_readme_and_quickstart_label_old_runtime_surfaces_as_legacy(self) -> None:
        readme = README.read_text(encoding="utf-8")
        quickstart = (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")
        for phrase in [
            "## Optional Legacy Conversation-To-App Workflow",
            "## Optional Legacy Private App Operating-Profile Evaluations",
            "## Advanced Legacy Runtime Onboarding",
            "## Advanced Legacy Runtime Model",
        ]:
            with self.subTest(surface="README", phrase=phrase):
                self.assertIn(phrase, readme)
        for phrase in [
            "## Try the conversation-to-app workflow locally",
            "## Run private app operating-profile evaluations",
            "## Runtime Model",
        ]:
            with self.subTest(surface="README", phrase=phrase):
                self.assertNotIn(phrase, readme)

        for phrase in [
            "## 7. Optional legacy guided onboarding",
            "## 8. Optional runtime smoke",
            "## 9. Optional legacy status from Telegram commands",
        ]:
            with self.subTest(surface="quickstart", phrase=phrase):
                self.assertIn(phrase, quickstart)
        for phrase in [
            "## 7. Run guided onboarding",
            "## 8. Run the runtime smoke",
            "## 9. Inspect status from Telegram commands",
        ]:
            with self.subTest(surface="quickstart", phrase=phrase):
                self.assertNotIn(phrase, quickstart)

    def test_legacy_surface_inventory_marks_old_paths_optional(self) -> None:
        text = normalized(LEGACY_SURFACES)
        required = [
            "WEAVE vNext default startup is COS-first and file-skeleton-first",
            "They are not part of first contact, onboarding, or product acceptance",
            "TUI/Textual files remain as historical cockpit proof",
            "Hermes/runtime files remain as bounded integration references",
            "The default product no longer requires an external orchestration adapter",
            "should not read this file before it has emitted the WEAVE state line",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

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

    def test_default_bootstrap_read_list_excludes_external_orchestrator_plan(self) -> None:
        text = BOOTSTRAP.read_text(encoding="utf-8")
        required_block = text.split("## What The Codex Agent Must Do", 1)[1].split("## Optional Adapter Use", 1)[0]
        self.assertIn("docs/COS_WEAVE_REPO_SKELETON.md", required_block)
        self.assertNotIn("external orchestrator", required_block.lower())

        agents = AGENTS.read_text(encoding="utf-8")
        core_map = agents.split("## Source-Of-Truth Map", 1)[1].split("## Confidential Topology Boundary", 1)[0]
        self.assertIn("docs/COS_WEAVE_REPO_SKELETON.md", core_map)
        self.assertNotIn("external orchestrator", core_map.lower())

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
        self.assertNotIn("external orchestrator", sample_text.lower())

    def test_bootstrap_contract_does_not_make_external_orchestrator_default_acceptance(self) -> None:
        text = normalized(BOOTSTRAP)
        self.assertIn("The default vNext product surface is a visible file/folder skeleton", text)
        self.assertIn("Scope=local-file-skeleton", text)
        self.assertIn("ordinary or vague intent", text)
        self.assertIn("app state", text)
        required_block = BOOTSTRAP.read_text(encoding="utf-8").split("## What The Codex Agent Must Do", 1)[1].split("## Required Non-Claims", 1)[0]
        self.assertNotIn("external orchestrator", required_block.lower())
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
