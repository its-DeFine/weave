from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md"
SKILL = ROOT / "packages" / "weave-tool" / "skills" / "compound-engineering" / "SKILL.md"
ADOPTION_PLAN = ROOT / "docs" / "WEAVE_SYMPHONY_ADOPTION_PLAN.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "docs" / "README.md"
COMPOUND_DOC = ROOT / "docs" / "COMPOUND_ENGINEERING.md"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class WeaveSymphonyAdapterCEPlanTest(unittest.TestCase):
    def test_plan_defines_adapter_boundary_and_value(self) -> None:
        text = normalized(PLAN)

        required = [
            "WEAVE is the user-facing Chief of Staff agent",
            "Symphony is the orchestra",
            "The adapter is the small, testable bridge",
            "one stable chat surface",
            "visible worker progress",
            "safe continuation after compaction, restart, or stale workers",
            "If the adapter only starts agents but does not improve visibility",
        ]

        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_plan_has_methodical_slices_and_non_claims(self) -> None:
        text = normalized(PLAN)

        required = [
            "Slice 0: Contract And Fixtures",
            "Slice 1: Local Queue Adapter",
            "Slice 2: WEAVE Workflow Prompt Renderer",
            "Slice 3: Fake Worker End-To-End",
            "Slice 4: Local Codex App-Server Smoke",
            "Slice 5: Observability And Dashboard Mapping",
            "Slice 6: Gated Live Tracker Run",
            "no Symphony process is started",
            "no real Codex app-server worker has run",
            "live tracker use remains gated",
        ]

        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_compound_engineering_skill_is_reusable_and_points_to_adapter_plan(self) -> None:
        text = normalized(SKILL)

        required = [
            "name: compound-engineering",
            "turning vague owner intent into agent-executable work",
            "Capability question",
            "Validate the target surface, not a nearby artifact",
            "WEAVE To Symphony Adapter Rule",
            "docs/WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md",
            "Never claim adapter success until the current slice has target-surface proof",
        ]

        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_adoption_plan_points_to_the_dedicated_ce_plan(self) -> None:
        text = normalized(ADOPTION_PLAN)

        self.assertIn("WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md", text)

    def test_continuous_ce_surfaces_are_discoverable(self) -> None:
        for path in [AGENTS, README, COMPOUND_DOC, SKILL]:
            text = normalized(path)
            with self.subTest(path=path.name):
                self.assertIn("WEAVE_SYMPHONY_ADAPTER_CE_PLAN.md", text)


if __name__ == "__main__":
    unittest.main()
