from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CE_DOC = ROOT / "docs" / "COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md"
BOOTSTRAP = ROOT / "docs" / "COS_WEAVE_BOOTSTRAP.md"
SKILL = ROOT / "packages" / "weave-tool" / "skills" / "cos-weave" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class CosWeavePromptBootstrapCETests(unittest.TestCase):
    def test_ce_doc_exists_and_names_prompt_first_acceptance_bar(self) -> None:
        text = normalized(CE_DOC)
        acceptance = (
            "A normal Codex thread given only a WEAVE repo URL/path plus ordinary app intent "
            "can discover the repo bootstrap contract, begin with a WEAVE state line, become "
            "COS WEAVE, create/load the repo-owned file skeleton, create app intent/todos/ "
            "lifecycle/proof/review/readback files, record provider-specific deployment "
            "gates, and avoid manual commands, manual folder setup, manual lifecycle "
            "classification, identity-gate rituals, and full lifecycle overclaims."
        )

        self.assertIn("Status: default vNext file-skeleton CE contract", text)
        self.assertIn(acceptance, text)
        self.assertIn("The first meaningful response must begin with", text)
        self.assertIn("Scope=local-file-skeleton", text)

    def test_ce_doc_defines_capability_architecture_slices_and_proof_surfaces(self) -> None:
        text = normalized(CE_DOC)
        required = [
            "Required Surfaces",
            "docs/COS_WEAVE_REPO_SKELETON.md",
            "Slice 0: Instruction Discovery",
            "Slice 1: Skeleton Home",
            "Slice 2: App Intake",
            "Slice 3: Lifecycle Truth",
            "Slice 4: Worker Packets",
            "Slice 5: Readback After Restart",
            "Slice 6: Deployment Provider Gates",
            "observe -> validate -> govern -> review -> sync",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_ce_doc_adversarial_review_blocks_command_first_fake_proof_and_overclaiming(self) -> None:
        text = normalized(CE_DOC)
        required = [
            "Did the first response start with `WEAVE | ...`?",
            "Did the agent become COS WEAVE before implementation work?",
            "Did it create visible app files instead of a hidden process assumption?",
            "Did a missing owner name become a draft owner profile/todo instead of a gate?",
            "Did vague intent create app state immediately?",
            "Did two app ideas create two app folders under one home?",
            "Did provider gates block deployment while allowing local planning and",
            "Did the agent avoid asking the owner to run commands or classify lifecycle?",
            "Did it avoid full-lifecycle, deploy, tracker, public-send, billing, and credential overclaims?",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_ce_doc_is_linked_from_bootstrap_skill_agents_and_readme(self) -> None:
        for path in [BOOTSTRAP, SKILL, AGENTS, README]:
            text = normalized(path)
            with self.subTest(path=path):
                self.assertIn("COS_WEAVE_PROMPT_BOOTSTRAP_COMPOUND_ENGINEERING.md", text)

    def test_ce_doc_names_live_service_gate_and_stop_boundaries(self) -> None:
        text = normalized(CE_DOC)
        required = [
            "Stop as `BLOCKED` or `NEEDS_OWNER_ACTION`",
            "live workers",
            "live tracker",
            "deploy",
            "public send",
            "billing",
            "credentials",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
