import json

from models import Choice, GameState
from rules import RuleResult


def build_start_prompt(state: GameState) -> str:
    payload = {
        "game_state": {
            "turn": state.turn,
            "scene": state.scene,
            "event": state.current_event,
            "protagonist": {
                "charm": state.charm,
                "wealth": state.wealth,
                "reputation": state.reputation,
            },
            "npcs": [
                {
                    "name": n.name,
                    "favorability": n.favorability,
                    "state": n.state,
                    "preference": n.preference,
                    "psychology": n.psychology,
                }
                for n in state.npcs
            ],
            "story_log_tail": state.story_log[-1:],
        },
        "this_turn": {
            "player_choice": None,
            "rule_judgement": {
                "success": True,
                "result_type": "start",
                "reason_codes": ["GAME_START"],
                "success_rate": 1.0,
                "status_text": "开始游戏，生成第一章开场剧情与选项。",
                "delta": {
                    "charm": 0,
                    "wealth": 0,
                    "reputation": 0,
                    "favorability": 0,
                },
            },
        },
        "opening_constraints": {
            "task": "基于给定场景模板与NPC模板生成第一章开场",
            "must_include": [
                "场景氛围细节",
                "至少两位异性NPC的状态与心理暗线",
                "A/B/C三个可执行选项",
            ],
        },
        "output_contract": {
            "must_return": ["story_paragraph", "next_choices_abc", "state_delta"],
            "language": "zh-CN",
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_prompt(state: GameState, choice: Choice, result: RuleResult) -> str:
    payload = {
        "game_state": {
            "turn": state.turn,
            "scene": state.scene,
            "event": state.current_event,
            "protagonist": {
                "charm": state.charm,
                "wealth": state.wealth,
                "reputation": state.reputation,
            },
            "npcs": [
                {
                    "name": n.name,
                    "favorability": n.favorability,
                    "state": n.state,
                    "preference": n.preference,
                    "psychology": n.psychology,
                }
                for n in state.npcs
            ],
            "story_log_tail": state.story_log[-2:],
        },
        "this_turn": {
            "player_choice": {"id": choice.id, "text": choice.text, "type": choice.type},
            "rule_judgement": {
                "success": result.success,
                "result_type": result.result_type,
                "reason_codes": result.reason_codes,
                "success_rate": result.success_rate,
                "shura_mode": result.shura_mode,
                "status_text": result.status_text,
                "delta": {
                    "charm": result.charm_delta,
                    "wealth": result.wealth_delta,
                    "reputation": result.reputation_delta,
                    "favorability": result.favorability_delta,
                },
            },
        },
        "output_contract": {
            "must_return": ["story_paragraph", "next_choices_abc", "state_delta"],
            "language": "zh-CN",
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
