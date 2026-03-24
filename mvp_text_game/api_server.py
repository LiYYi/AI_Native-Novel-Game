import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engine import GameEngine
from llm_client import MiniMaxLLMClient
from state_factory import create_initial_state

HOST = os.getenv("GAME_API_HOST", "127.0.0.1")
PORT = int(os.getenv("GAME_API_PORT", "8000"))

_state = create_initial_state()
_engine = GameEngine(MiniMaxLLMClient())


def _extract_choice(raw_choice: str) -> str:
    text = (raw_choice or "").strip().upper()
    if not text:
        return ""
    if text[0] in ("A", "B", "C"):
        return text[0]
    return text


class GameHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code: int = 200) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._set_headers(204)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
            return
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("/start", "/play"):
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))
            return

        try:
            if self.path == "/start":
                global _state
                _state = create_initial_state()
                _engine.start_game(_state)
                response = {
                    "api_schema_version": "1.1",
                    "story_text": _state.story_log[-1] if _state.story_log else "",
                    "story_length": len(_state.story_log[-1]) if _state.story_log else 0,
                    "model_used": os.getenv("MINIMAX_MODEL", "MiniMax-M2.7"),
                    "state_delta": _engine.last_state_delta,
                    "result_type": _engine.last_result_type,
                    "reason_codes": _engine.last_reason_codes,
                    "success_rate": _engine.last_success_rate,
                    "shura_mode": _engine.last_shura_mode,
                    "choices": [
                        {"id": c.id, "text": c.text, "type": c.type}
                        for c in _state.choices[:3]
                    ],
                    "turn": _state.turn,
                    "attributes": {
                        "charm": _state.charm,
                        "wealth": _state.wealth,
                        "reputation": _state.reputation,
                    },
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            payload = json.loads(raw_body)
            choice = _extract_choice(str(payload.get("choice", "")))
            if choice not in ("A", "B", "C"):
                raise ValueError("choice must be A/B/C")

            _engine.play_turn(_state, choice)

            response = {
                "api_schema_version": "1.1",
                "story_text": _state.story_log[-1] if _state.story_log else "",
                "story_length": len(_state.story_log[-1]) if _state.story_log else 0,
                "model_used": os.getenv("MINIMAX_MODEL", "MiniMax-M2.7"),
                "state_delta": _engine.last_state_delta,
                "result_type": _engine.last_result_type,
                "reason_codes": _engine.last_reason_codes,
                "success_rate": _engine.last_success_rate,
                "shura_mode": _engine.last_shura_mode,
                "choices": [
                    {"id": c.id, "text": c.text, "type": c.type}
                    for c in _state.choices[:3]
                ],
                "turn": _state.turn,
                "attributes": {
                    "charm": _state.charm,
                    "wealth": _state.wealth,
                    "reputation": _state.reputation,
                },
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8"))


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), GameHandler)
    print(f"Game API server running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
