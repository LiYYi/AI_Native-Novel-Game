import json
import os
import re
from dataclasses import dataclass
from typing import List

from minimax_service import MiniMaxService
from models import Choice


@dataclass
class LLMOutput:
    story_paragraph: str
    next_choices: List[Choice]
    state_delta: dict


class BaseLLMClient:
    def generate(self, prompt: str) -> LLMOutput:
        raise NotImplementedError


class MiniMaxLLMClient(BaseLLMClient):
    def __init__(self) -> None:
        self.service = MiniMaxService()
        self.fallback_enabled = os.getenv("MINIMAX_FALLBACK_TO_MOCK", "true").lower() == "true"
        self.min_story_chars = int(os.getenv("MIN_STORY_CHARS", "200"))

    def generate(self, prompt: str) -> LLMOutput:
        text = ""
        try:
            text = self.service.generate_content(prompt)
        except Exception as exc:  # noqa: BLE001
            if not self.fallback_enabled:
                raise
            return _fallback_output(str(exc))

        try:
            parsed = _parse_llm_output(text, min_story_chars=self.min_story_chars)
            return parsed
        except Exception as exc:  # noqa: BLE001
            # Retry once with stricter instruction when output is malformed/too short.
            retry_prompt = (
                f"{prompt}\n\n"
                f"补充要求：story_paragraph 必须不少于 {self.min_story_chars} 字，"
                "只输出合法 JSON，不要 markdown 代码块，不要额外解释。"
            )
            try:
                retry_text = self.service.generate_content(retry_prompt)
                return _parse_llm_output(retry_text, min_story_chars=self.min_story_chars)
            except Exception as retry_exc:  # noqa: BLE001
                # If the model returns valid but short narrative, ask it to continue.
                try:
                    seed_story = _extract_story_seed(retry_text if "retry_text" in locals() else text)
                    continued = self._continue_story_to_min(seed_story)
                    choices = _extract_choices_or_default(retry_text if "retry_text" in locals() else text)
                    return LLMOutput(
                        story_paragraph=continued,
                        next_choices=choices,
                        state_delta={"charm": 0, "wealth": 0, "reputation": 0},
                    )
                except Exception:
                    pass
                if self.fallback_enabled:
                    return _fallback_output(f"Invalid LLM output format: {retry_exc}", self.min_story_chars)
                raise RuntimeError(f"Invalid LLM output: {text}") from retry_exc

    def _continue_story_to_min(self, seed_story: str) -> str:
        story = _clean_text(seed_story)
        if len(story) >= self.min_story_chars:
            return story

        attempts = 0
        while len(story) < self.min_story_chars and attempts < 2:
            remain = self.min_story_chars - len(story)
            continuation_prompt = (
                "请基于以下文本继续续写，不要重复前文，不要输出JSON，"
                f"直接输出中文正文续写内容，不少于 {remain} 字：\n\n{story}"
            )
            more = self.service.generate_content(continuation_prompt)
            story = f"{story}\n\n{_clean_text(more)}"
            attempts += 1

        if len(story) < self.min_story_chars:
            raise ValueError(f"continued story too short: {len(story)} < {self.min_story_chars}")
        return story


def _parse_llm_output(raw_text: str, min_story_chars: int) -> LLMOutput:
    candidate = raw_text.strip()
    candidate = candidate.replace("```json", "").replace("```", "").strip()
    try:
        candidate = _extract_first_json_object(candidate)
        obj = json.loads(candidate)
    except ValueError:
        return _parse_plaintext_output(raw_text, min_story_chars=min_story_chars)

    story = _clean_text(str(obj.get("story_paragraph", "")))
    if not story:
        raise ValueError("story_paragraph is empty")
    if len(story) < min_story_chars:
        raise ValueError(f"story_paragraph too short: {len(story)} < {min_story_chars}")

    raw_choices = obj.get("next_choices")
    if not isinstance(raw_choices, list) or len(raw_choices) < 3:
        raise ValueError("next_choices is invalid")

    parsed_choices: List[Choice] = []
    for item in raw_choices[:3]:
        if not isinstance(item, dict):
            continue
        choice_id = _clean_choice_id(str(item.get("id", "")))
        choice_type = _clean_choice_id(str(item.get("type", choice_id)))
        choice_text = _clean_text(str(item.get("text", "")))
        if choice_id not in ("A", "B", "C"):
            continue
        if not choice_text:
            choice_text = f"选项 {choice_id}"
        parsed_choices.append(Choice(id=choice_id, text=choice_text, type=choice_type))

    if len(parsed_choices) < 3:
        raise ValueError("parsed choices less than 3")

    llm_state_delta = obj.get("state_delta")
    state_delta = _normalize_state_delta(llm_state_delta)

    return LLMOutput(
        story_paragraph=story,
        next_choices=parsed_choices,
        state_delta=state_delta,
    )


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    return text[start : end + 1]


def _clean_text(value: str) -> str:
    # Keep paragraph breaks while normalizing noisy control chars.
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[^\S\n]+", " ", normalized)
    normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)
    lines = [line.strip() for line in normalized.split("\n")]
    merged = "\n".join(lines)
    merged = re.sub(r"\n{3,}", "\n\n", merged).strip()
    return merged


def _clean_choice_id(value: str) -> str:
    value = value.strip().upper()
    return value[:1] if value else ""


def _extract_story_seed(raw_text: str) -> str:
    candidate = raw_text.strip().replace("```json", "").replace("```", "")
    try:
        json_text = _extract_first_json_object(candidate)
        obj = json.loads(json_text)
        value = _clean_text(str(obj.get("story_paragraph", "")))
        if value:
            return value
    except Exception:
        pass
    return _clean_text(candidate)


def _extract_choices_or_default(raw_text: str) -> List[Choice]:
    candidate = raw_text.strip().replace("```json", "").replace("```", "")
    try:
        json_text = _extract_first_json_object(candidate)
        obj = json.loads(json_text)
        raw_choices = obj.get("next_choices")
        if isinstance(raw_choices, list):
            parsed: List[Choice] = []
            for item in raw_choices[:3]:
                if not isinstance(item, dict):
                    continue
                cid = _clean_choice_id(str(item.get("id", "")))
                ctype = _clean_choice_id(str(item.get("type", cid)))
                ctext = _clean_text(str(item.get("text", "")))
                if cid in ("A", "B", "C"):
                    parsed.append(Choice(id=cid, text=ctext or f"选项 {cid}", type=ctype))
            if len(parsed) == 3:
                return parsed
    except Exception:
        pass

    return [
        Choice(id="A", text="推进利益交换，强化掌控感", type="A"),
        Choice(id="B", text="转向情绪沟通，提升信任", type="B"),
        Choice(id="C", text="维持观望，等待对方先出牌", type="C"),
    ]


def _parse_plaintext_output(raw_text: str, min_story_chars: int) -> LLMOutput:
    # Fallback parser for models that return plain narrative text instead of JSON.
    text = _clean_text(
        raw_text.replace("```json", "").replace("```", "")
    )
    if len(text) < min_story_chars:
        raise ValueError(f"plaintext story too short: {len(text)} < {min_story_chars}")

    # Try to extract A/B/C options from plain text.
    extracted = {}
    for choice_id in ("A", "B", "C"):
        pattern = rf"(?:^|\s){choice_id}[\.、:：]\s*(.+?)(?=(?:\s+[ABC][\.、:：]\s*)|$)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            option_text = _clean_text(match.group(1))
            if option_text:
                extracted[choice_id] = option_text[:80]

    choices = [
        Choice(id="A", text=extracted.get("A", "继续推进当前优势，扩大主动权"), type="A"),
        Choice(id="B", text=extracted.get("B", "转向情绪沟通，争取关键人物信任"), type="B"),
        Choice(id="C", text=extracted.get("C", "暂时观望，收集更多信息再行动"), type="C"),
    ]
    return LLMOutput(
        story_paragraph=text,
        next_choices=choices,
        state_delta={"charm": 0, "wealth": 0, "reputation": 0},
    )


def _normalize_state_delta(raw: object) -> dict:
    if not isinstance(raw, dict):
        return {"charm": 0, "wealth": 0, "reputation": 0}

    def _to_int(value: object) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            return 0

    return {
        "charm": _to_int(raw.get("charm")),
        "wealth": _to_int(raw.get("wealth")),
        "reputation": _to_int(raw.get("reputation")),
    }


def _fallback_output(reason: str, min_story_chars: int) -> LLMOutput:
    base_story = (
        "系统提示：在线模型暂不可用，已切换到本地兜底叙事。"
        f"（原因：{reason}）"
        "雨夜压着城市的玻璃幕墙，霓虹在潮湿空气里被拉成长线。"
        "你站在包厢中央，指尖摩挲杯壁，缓慢扫过两位目标的眼神变化。"
        "其中一人表情克制，唇角几乎没有弧度，却在你提及合作筹码时眼神明显收紧；"
        "另一人把发丝拨到耳后，呼吸变得更轻，像在等待你给出下一句能够落地的承诺。"
        "你没有急着表态，而是故意留出一拍沉默，让房间里的香水与雪松木气味先一步扩散，"
        "让她们都意识到你不会被情绪牵着走。"
        "你把话题拆成利益、风险、时机三段，先给出可验证的短期收益，再抛出可控的中期计划，"
        "最后把长期绑定包装成双方都能接受的安全选项。"
        "灯影落在你袖口，细微的布料摩擦声反而放大了此刻的压迫感。"
        "你看见其中一人的指尖停在杯沿不再敲击，意味着她从防守进入计算；"
        "另一人则把身体重心微微前倾，说明她愿意继续跟进这场博弈。"
        "你知道这一回合的关键不在热烈，而在可兑现。"
        "于是你把最后一句压低：规则由你们定，但节奏由我控。"
        "空气里没有掌声，只有更安静的注视。"
        "在这份注视中，你拿回了主动权，也把下一回合的风险提前锁进可管理区间。"
    )
    story = base_story
    while len(story) < min_story_chars:
        story += "你维持冷静与克制，继续通过微表情与停顿引导局势，让每一步都落在可计算的范围内。"

    return LLMOutput(
        story_paragraph=story,
        next_choices=[
            Choice(id="A", text="推进利益交换，强化掌控感", type="A"),
            Choice(id="B", text="转向情绪沟通，提升信任", type="B"),
            Choice(id="C", text="维持观望，等待对方先出牌", type="C"),
        ],
        state_delta={"charm": 0, "wealth": 0, "reputation": 0},
    )
