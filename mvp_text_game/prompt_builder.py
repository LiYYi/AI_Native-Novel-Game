import json

from models import Choice, GameState
from rules import RuleResult


def _player_visible_language(state: GameState) -> str:
    return "en" if state.locale == "en" else "zh-CN"


def _opening_constraints() -> dict:
    return {
        "task": "基于给定场景模板与NPC模板生成第一章开场",
        "must_include": [
            "场景氛围细节",
            "至少两位异性NPC的状态与心理暗线",
            "A/B/C三个可执行选项",
        ],
    }


def _narrative_language_block(state: GameState) -> dict:
    return {
        "player_visible_language": _player_visible_language(state),
        "rules": (
            "面向玩家的可见文本仅包含：story_paragraph、next_choices 中每项的 text。"
            "上述内容必须使用 player_visible_language 指定的语言书写，通顺自然。"
            "输入中的场景、事件、NPC 等设定字段可使用任意语言；请理解设定并在正文中保持一致，"
            "必要时在叙事中自然呈现对应信息，勿机械翻译字段标签。"
        ),
    }


def _output_contract(state: GameState) -> dict:
    return {
        "must_return": ["story_paragraph", "next_choices_abc", "state_delta"],
        "player_visible_language": _player_visible_language(state),
    }


def _game_state_dict(state: GameState, *, story_tail_lines: int) -> dict:
    """Shared ``game_state`` object for LLM payloads (tail slice: last N log lines)."""
    tail = state.story_log[-story_tail_lines:] if story_tail_lines > 0 else []
    return {
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
        "story_log_tail": tail,
    }


def build_start_prompt(state: GameState) -> str:
    payload = {
        "game_state": _game_state_dict(state, story_tail_lines=1),
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
        "opening_constraints": _opening_constraints(),
        "narrative_language": _narrative_language_block(state),
        "output_contract": _output_contract(state),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_prompt(state: GameState, choice: Choice, result: RuleResult) -> str:
    payload = {
        "game_state": _game_state_dict(state, story_tail_lines=2),
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
        "narrative_language": _narrative_language_block(state),
        "output_contract": _output_contract(state),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
