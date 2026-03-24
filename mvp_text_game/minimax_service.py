import json
import os
import socket
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

    def generate_content(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY is missing.")

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是文字游戏叙事函数，请仅输出JSON。"},
                {
                    "role": "user",
                    "content": (
                        "根据输入生成 JSON，格式为："
                        '{"story_paragraph":"...","next_choices":[{"id":"A","text":"...","type":"A"},'
                        '{"id":"B","text":"...","type":"B"},{"id":"C","text":"...","type":"C"}],'
                        '"state_delta":{"charm":0,"wealth":0,"reputation":0}}'
                        "\n硬性要求：story_paragraph 必须为中文长文本，不少于 200 字。"
                        "\n硬性要求：story_paragraph 需要自然分段，段落之间用换行分隔。"
                        "\n硬性要求：next_choices 必须严格包含 3 个选项，且 id 仅为 A/B/C。"
                        "\n硬性要求：next_choices 必须紧贴当前剧情推进，不能返回固定模板选项。"
                        "\n硬性要求：state_delta 必须返回 charm/wealth/reputation 的整数变化建议（可为负数）。"
                        "\n输入如下：\n"
                        f"{prompt}"
                    ),
                },
            ],
            "temperature": 0.7,
        }

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
            raise RuntimeError(f"MiniMax response missing text content: {content}")
        return text
