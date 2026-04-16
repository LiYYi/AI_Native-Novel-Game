# Text Game MVP (Python)

Minimal runnable game loop with clear modules:

- `models.py`: data models
- `state_factory.py`: initial game state
- `rules.py`: deterministic state-machine rules
- `prompt_builder.py`: structured prompt payload
- `minimax_service.py`: independent MiniMax service (prompt -> generated content)
- `llm_client.py`: parse MiniMax output into game objects
- `engine.py`: turn orchestration
- `main.py`: CLI entry

## Run (MiniMax)

```bash
export MINIMAX_API_KEY=your_key
export MINIMAX_API_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
export MINIMAX_MODEL=MiniMax-M2.7-highspeed
export MINIMAX_FALLBACK_TO_MOCK=true
export MIN_STORY_CHARS=200
export MINIMAX_TIMEOUT_SECONDS=90
# Optional: separate model reasoning from final reply (API support may vary)
export MINIMAX_REASONING_SPLIT=true
# Optional: add brief prompts to discourage verbose reasoning in the visible reply
export MINIMAX_COMPACT_REASONING_PROMPT=true
cd mvp_text_game
python3 main.py
```

## Run HTTP API for Flutter

```bash
cd mvp_text_game
python3 api_server.py
```

## One-command Dev Launcher (auto backend + free port)

From project root:

```bash
python3 dev_launcher.py
```

Custom flutter command:

```bash
python3 dev_launcher.py -- flutter run -d chrome
```

This launcher will:
- auto pick an available backend port
- start `mvp_text_game/api_server.py`
- inject `--dart-define=GAME_API_BASE_URL=http://127.0.0.1:<port>`
- stop backend when Flutter exits

## Run Rule Tests

```bash
cd mvp_text_game
python3 -m unittest discover -s tests -p "test_*.py"
```

API endpoint:

- `POST /start` — JSON response (MiniMax `generate_content`).
- `POST /play` — body: `{"choice":"A"}` (A/B/C); one `application/json` response.
- Response fields:
  - `story_text`: new story text
  - `choices`: next choices (A/B/C)
  - `api_schema_version`: API contract version
  - `state_delta`: applied numeric change
  - `result_type`: success/partial_success/blocked
  - `reason_codes`: rule reasons list
  - `success_rate`: current success rate (0-1)

> Notes:
> - The MiniMax response schema may differ by account/model version.
> - If response field names differ, adjust extraction in `MiniMaxLLMClient.generate()`.
> - When balance is insufficient, fallback is enabled by default (`MINIMAX_FALLBACK_TO_MOCK=true`).
