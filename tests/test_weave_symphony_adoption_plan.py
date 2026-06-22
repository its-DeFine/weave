from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "WEAVE_SYMPHONY_ADOPTION_PLAN.md"


class WeaveSymphonyAdoptionPlanTest(unittest.TestCase):
    def test_records_weave_as_agent_and_symphony_as_orchestra(self) -> None:
        text = " ".join(PLAN.read_text(encoding="utf-8").split())

        required = [
            "WEAVE is the user-facing agent and product policy",
            "Symphony is the orchestra",
            "thin adapter",
            "WEAVE Chief of Staff session receives user intent",
            "A queue adapter presents that `WorkItem` to Symphony",
            "The Codex prompt is a WEAVE workflow prompt",
            "WEAVE reads Symphony state plus proof envelopes",
        ]

        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_dashboard_and_compound_engineering_boundaries_are_explicit(self) -> None:
        text = " ".join(PLAN.read_text(encoding="utf-8").split())

        required = [
            "Phoenix dashboard is an operational dashboard",
            "not the WEAVE product UX",
            "compound engineering pass",
            "smallest runnable integration proof",
            "This plan does not prove the WEAVE-to-Symphony queue adapter",
            "This plan does not prove the Phoenix dashboard has been extended",
        ]

        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
