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
            "A normal Codex thread given only a WEAVE repo URL/path plus ordinary intent can "
            "discover the repo bootstrap contract, become COS WEAVE, create/load local WEAVE "
            "state, explain the Chief-of-Staff role, infer lifecycle state, create or load "
            "app/application state, ask only needed plain-language onboarding questions, and "
            "report proof/readback/non-claims without asking the user to run commands, "
            "classify lifecycle stages, create queue roots, or understand Symphony."
        )

        self.assertIn("Status: prompt-first compound-engineering contract", text)
        self.assertIn(acceptance, text)
        self.assertIn("The owner should not run a bootstrap command", text)
        self.assertIn("The expected user prompt is one line", text)
        self.assertIn("Use this repo as COS WEAVE: <WEAVE repo URL or local path>", text)

    def test_ce_doc_defines_capability_architecture_slices_and_proof_surfaces(self) -> None:
        text = normalized(CE_DOC)
        required = [
            "Capability Question",
            "What repo-contained instructions must exist so a generic Codex agent can self-bootstrap?",
            "Architecture Boundary",
            "COS WEAVE is user-facing. Symphony is optional behind-the-scenes orchestration",
            "Slice 0: Instruction Discovery",
            "Slice 1: COS WEAVE Home",
            "Slice 2: Vague Intent To First-Run COS State",
            "Slice 3: Internal Worker Packet Or Visible Worker",
            "Slice 4: Optional WEAVE-To-Symphony Adapter Proof",
            "Slice 5: Prompt-First End-To-End Rehearsal",
            "Slice 6: Gated Live Symphony/Codex App-Server",
            "Proof surface:",
            "Non-claim:",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_ce_doc_adversarial_review_blocks_command_first_fake_proof_and_overclaiming(self) -> None:
        text = normalized(CE_DOC)
        required = [
            "Did the product relapse into command-first UX?",
            "Did any instruction ask the user to run adapter, queue, dispatch, or Symphony commands?",
            "Did the agent ask the user to classify lifecycle stage manually?",
            "Did a clean adapter/calculator E2E get mistaken for first-run product proof?",
            "Did local proof overclaim live Symphony, live Codex app-server, tracker, deploy, public-send, billing, or credential success?",
            "Did the default first-run path require Symphony before WEAVE could help?",
            "Is there hidden setup burden",
            "Does readback preserve proof path and non-claims?",
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
            "Future Live-Service Gate",
            "Live Symphony/Codex app-server proof is a separate gated slice",
            "Stop as `BLOCKED` or `NEEDS_OWNER_ACTION`",
            "live Symphony",
            "live Codex app-server",
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
