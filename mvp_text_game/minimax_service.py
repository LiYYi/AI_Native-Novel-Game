import copy
import json
import os
import socket
import time
import urllib.error
import urllib.request


class MiniMaxService:
    """Independent MiniMax service: prompt in, text out."""

    def __init__(self) -> None:
        self._load_dotenv_if_needed()
        self.api_key = os.getenv("MINIMAX_API_KEY", "")
        self.api_url = os.getenv("MINIMAX_API_URL", "https://api.minimax.chat/v1/text/chatcompletion_v2")
        self.model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
        self.timeout_seconds = int(os.getenv("MINIMAX_TIMEOUT_SECONDS", "30"))
        self.log_llm_io = os.getenv("MINIMAX_LOG_LLM_IO", "true").lower() == "true"
        # When true, response logs include message.reasoning_* (verbose). Default false trims them from logs only.
        self.log_full_minimax_response = (
            os.getenv("MINIMAX_LOG_FULL_RESPONSE", "false").lower() == "true"
        )

    def _load_dotenv_if_needed(self) -> None:
        # Minimal .env loader to avoid adding extra dependencies.
        if os.getenv("MINIMAX_API_KEY"):
            return
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.exists(env_path):
            return
        with open(env_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value

    @staticmethod
    def _system_content() -> str:
        return "你是文字游戏叙事函数，请仅输出JSON。"

    def _user_content(self, prompt: str) -> str:
        min_story = int(os.getenv("MIN_STORY_CHARS", "200"))
        return (
            "根据下方输入的 JSON 生成回复 JSON，结构固定为："
            '{"story_paragraph":"...","next_choices":[{"id":"A","text":"...","type":"A"},'
            '{"id":"B","text":"...","type":"B"},{"id":"C","text":"...","type":"C"}],'
            '"state_delta":{"charm":0,"wealth":0,"reputation":0}}'
            f"\n硬性要求：story_paragraph 为面向玩家的长叙事，不少于 {min_story} 个字符"
            "（字符数按输入 JSON 里 output_contract.player_visible_language 所指语言计算；"
            "中文一般计汉字，英文计字母与空格等）。"
            "\n硬性要求：story_paragraph 需要自然分段，段落之间用换行分隔。"
            "\n硬性要求：next_choices 必须严格包含 3 个选项，且 id 仅为 A/B/C。"
            "\n硬性要求：next_choices 每项 text 的语言必须与 output_contract.player_visible_language 一致，"
            "且紧贴当前剧情推进，不能返回与剧情无关的固定模板句。"
            "\n硬性要求：state_delta 必须返回 charm/wealth/reputation 的整数变化建议（可为负数）。"
            "\n语言说明：输入里的场景、NPC 等字段语言与玩家可见语言可以不同；"
            "请理解设定并在 story_paragraph / next_choices[].text 中自行选用 player_visible_language 表达。"
            "\n输入如下：\n"
            f"{prompt}"
        )

    def _build_body(self, prompt: str) -> dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._system_content()},
                {"role": "user", "content": self._user_content(prompt)},
            ],
            "temperature": 0.7,
        }

    def _log_request(self, body: dict) -> None:
        if not self.log_llm_io:
            return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 88)
        print(f"[MiniMax][REQUEST] {ts}")
        print(f"model: {self.model}")
        print("messages:")
        print(json.dumps(body["messages"], ensure_ascii=False, indent=2))
        print("=" * 88 + "\n")

    def _log_response(self, parsed: dict) -> None:
        """Log API response. By default omit reasoning_* fields under choices[].message."""
        if not self.log_llm_io:
            return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 88)
        print(f"[MiniMax][RESPONSE] {ts}")
        if self.log_full_minimax_response:
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        else:
            slim = copy.deepcopy(parsed)
            for ch in slim.get("choices") or []:
                msg = ch.get("message")
                if isinstance(msg, dict):
                    msg.pop("reasoning_content", None)
                    msg.pop("reasoning_details", None)
                    msg.pop("audio_content", None)
            print(json.dumps(slim, ensure_ascii=False, indent=2))
            print(
                "(Omitted message.reasoning_* from log; set MINIMAX_LOG_FULL_RESPONSE=true for full JSON.)"
            )
        print("=" * 88 + "\n")

    def _extract_text_from_completion(self, parsed: dict) -> str:
        base_resp = parsed.get("base_resp") or {}
        status_code = base_resp.get("status_code")
        status_msg = base_resp.get("status_msg")
        if status_code not in (None, 0):
            if status_code == 1008:
                raise RuntimeError(
                    "MiniMax balance is insufficient (status_code=1008). "
                    "Please recharge or switch to fallback mode."
                )
            raise RuntimeError(
                f"MiniMax API error (status_code={status_code}, status_msg={status_msg})."
            )

        text = parsed.get("reply") or parsed.get("output_text") or ""
        if not text and "choices" in parsed and parsed["choices"]:
            text = parsed["choices"][0].get("message", {}).get("content", "")
        if not text:
            raise RuntimeError(f"MiniMax response missing text content: {parsed!r}")
        return text

    def generate_content(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY is missing.")

        body = self._build_body(prompt)
        self._log_request(body)

        request = urllib.request.Request(
            self.api_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                content = response.read().decode("utf-8")
        except (TimeoutError, socket.timeout) as exc:
            raise RuntimeError(
                f"MiniMax request timed out after {self.timeout_seconds}s."
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"MiniMax request failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"MiniMax request failed unexpectedly: {exc}") from exc

        parsed = json.loads(content)
        self._log_response(parsed)
        return self._extract_text_from_completion(parsed)
