from llm_client import BaseLLMClient
from models import Choice, GameState
from prompt_builder import build_prompt, build_start_prompt
from reason_codes import ReasonCodes
from result_types import ResultTypes
from rules import apply_result, evaluate_choice


class GameEngine:
    def __init__(self, llm_client: BaseLLMClient) -> None:
        self.llm_client = llm_client
        self.last_state_delta = {"charm": 0, "wealth": 0, "reputation": 0}
        self.last_result_type = ResultTypes.START
        self.last_reason_codes = []
        self.last_success_rate = 1.0
        self.last_shura_mode = False

    def start_game(self, state: GameState) -> str:
        prompt = build_start_prompt(state)
        llm_output = self.llm_client.generate(prompt)
        state.story_log.append(llm_output.story_paragraph)
        state.choices = llm_output.next_choices
        self.last_state_delta = {"charm": 0, "wealth": 0, "reputation": 0}
        self.last_result_type = ResultTypes.START
        self.last_reason_codes = [ReasonCodes.GAME_START]
        self.last_success_rate = 1.0
        self.last_shura_mode = False
        return state.story_log[-1]

    def play_turn(self, state: GameState, player_choice_id: str) -> str:
        choice = _find_choice(state, player_choice_id)
        result = evaluate_choice(state, choice)
        apply_result(state, result)

        prompt = build_prompt(state, choice, result)
        llm_output = self.llm_client.generate(prompt)
        llm_delta = _apply_llm_state_delta(state, choice, llm_output.state_delta)

        state.story_log.append(llm_output.story_paragraph)
        state.choices = llm_output.next_choices
        self.last_state_delta = llm_delta
        self.last_result_type = result.result_type
        self.last_reason_codes = result.reason_codes
        self.last_success_rate = result.success_rate
        self.last_shura_mode = result.shura_mode

        return _format_turn_output(state, result.status_text)


def _find_choice(state: GameState, choice_id: str) -> Choice:
    for choice in state.choices:
        if choice.id.upper() == choice_id.upper():
            return choice
    raise ValueError(f"Invalid choice: {choice_id}")


def _format_turn_output(state: GameState, status_text: str) -> str:
    latest_story = state.story_log[-1] if state.story_log else ""
    choices_text = "\n".join([f"{c.id}. {c.text}" for c in state.choices])
    return (
        f"\n[回合 {state.turn}] {status_text}\n"
        f"属性 => 魅力:{state.charm} 财力:{state.wealth} 声望:{state.reputation}\n"
        f"剧情 => {latest_story}\n"
        f"下一步选项:\n{choices_text}\n"
    )


def _apply_llm_state_delta(state: GameState, choice: Choice, llm_delta: dict) -> dict:
    ranges_by_type = {
        "A": {"charm": (-1, 2), "wealth": (-2, 2), "reputation": (-1, 2)},
        "B": {"charm": (-1, 3), "wealth": (-1, 1), "reputation": (-1, 2)},
        "C": {"charm": (-1, 1), "wealth": (-1, 2), "reputation": (-1, 3)},
    }
    limits = ranges_by_type.get(choice.type, {"charm": (-1, 1), "wealth": (-1, 1), "reputation": (-1, 1)})

    def _clamp(key: str) -> int:
        raw = llm_delta.get(key, 0)
        try:
            value = int(raw)
        except Exception:  # noqa: BLE001
            value = 0
        low, high = limits[key]
        return max(low, min(high, value))

    applied = {
        "charm": _clamp("charm"),
        "wealth": _clamp("wealth"),
        "reputation": _clamp("reputation"),
    }

    state.charm = max(0, state.charm + applied["charm"])
    state.wealth = max(0, state.wealth + applied["wealth"])
    state.reputation = max(0, state.reputation + applied["reputation"])
    return applied
