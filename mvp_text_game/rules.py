from dataclasses import dataclass

from models import Choice, GameState
from reason_codes import ReasonCodes
from result_types import ResultTypes


@dataclass
class RuleResult:
    success: bool
    result_type: str
    reason_codes: list[str]
    success_rate: float
    status_text: str
    charm_delta: int
    wealth_delta: int
    reputation_delta: int
    favorability_delta: int
    shura_mode: bool


def evaluate_choice(state: GameState, choice: Choice) -> RuleResult:
    shura_mode = _check_shura_trigger(state)

    # Attribute gate: too low wealth cannot sustain high-profile choice.
    if choice.type == "A" and state.wealth < 3:
        return RuleResult(
            success=False,
            result_type=ResultTypes.BLOCKED,
            reason_codes=[ReasonCodes.WEALTH_GATE_FAIL],
            success_rate=0.10,
            status_text="财力不足导致策略失败，对方明显轻视你的姿态。",
            charm_delta=-1,
            wealth_delta=0,
            reputation_delta=-2,
            favorability_delta=-5,
            shura_mode=shura_mode,
        )

    if choice.type == "A":
        return RuleResult(
            success=True,
            result_type=ResultTypes.SUCCESS,
            reason_codes=[ReasonCodes.POWER_PRESSURE_SUCCESS],
            success_rate=0.80,
            status_text="你掌控了场面节奏，话语权明显上升。",
            charm_delta=1,
            wealth_delta=-1,
            reputation_delta=1,
            favorability_delta=2,
            shura_mode=shura_mode,
        )
    if choice.type == "B":
        return RuleResult(
            success=True,
            result_type=ResultTypes.SUCCESS,
            reason_codes=[ReasonCodes.EMOTIONAL_INFLUENCE_SUCCESS],
            success_rate=0.78,
            status_text="你成功拿到情绪主动权，关系明显升温。",
            charm_delta=1,
            wealth_delta=0,
            reputation_delta=0,
            favorability_delta=4,
            shura_mode=shura_mode,
        )

    # C = defensive observation
    return RuleResult(
        success=True,
        result_type=ResultTypes.PARTIAL_SUCCESS,
        reason_codes=[ReasonCodes.TACTICAL_OBSERVATION],
        success_rate=0.68,
        status_text="你稳住局面并获得额外信息，但存在机会成本。",
        charm_delta=0,
        wealth_delta=0,
        reputation_delta=1,
        favorability_delta=1,
        shura_mode=shura_mode,
    )


def apply_result(state: GameState, result: RuleResult) -> None:
    state.charm += result.charm_delta
    state.wealth += result.wealth_delta
    state.reputation += result.reputation_delta
    state.turn += 1

    for npc in state.npcs:
        npc.favorability += result.favorability_delta
        if npc.favorability > 80:
            npc.state = "共犯"
        elif npc.favorability > 50:
            npc.state = "亲近"
        elif npc.favorability > 20:
            npc.state = "试探"
        else:
            npc.state = "戒备"


def _check_shura_trigger(state: GameState) -> bool:
    # Minimal MVP approximation: when at least two NPCs have favorability > 50.
    high_favorability_count = sum(1 for npc in state.npcs if npc.favorability > 50)
    return high_favorability_count >= 2
