import unittest

from models import Choice, GameState, NPC
from reason_codes import ReasonCodes
from rules import evaluate_choice
from state_factory import create_initial_state


class RulesTest(unittest.TestCase):
    def test_wealth_gate_fail_for_a_choice(self) -> None:
        state = create_initial_state()
        state.wealth = 1
        result = evaluate_choice(state, Choice(id="A", text="测试A", type="A"))

        self.assertFalse(result.success)
        self.assertEqual(result.result_type, "blocked")
        self.assertIn(ReasonCodes.WEALTH_GATE_FAIL, result.reason_codes)
        self.assertLess(result.success_rate, 0.2)

    def test_b_choice_success_reason_code(self) -> None:
        state = create_initial_state()
        result = evaluate_choice(state, Choice(id="B", text="测试B", type="B"))

        self.assertTrue(result.success)
        self.assertEqual(result.result_type, "success")
        self.assertIn(ReasonCodes.EMOTIONAL_INFLUENCE_SUCCESS, result.reason_codes)

    def test_shura_mode_trigger_when_two_npcs_above_50(self) -> None:
        state = GameState(
            charm=3,
            wealth=5,
            reputation=2,
            npcs=[
                NPC(name="A", favorability=60),
                NPC(name="B", favorability=55),
            ],
            story_log=["test"],
            scene="scene",
            current_event="event",
            turn=0,
            choices=[],
        )
        result = evaluate_choice(state, Choice(id="C", text="测试C", type="C"))
        self.assertTrue(result.shura_mode)


if __name__ == "__main__":
    unittest.main()
