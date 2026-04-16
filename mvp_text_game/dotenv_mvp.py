"""Load ``mvp_text_game/.env`` into ``os.environ`` for missing or blank keys."""

from __future__ import annotations

import os
from pathlib import Path

_mvp_dotenv_applied = False


def apply_mvp_dotenv() -> None:
    """Merge ``.env`` next to this package. Fills keys that are unset or empty in the environment.

    Fixes the case where the parent process exports ``MINIMAX_API_KEY=`` (empty), which would
    previously block values from ``.env`` from ever being applied.
    """
    global _mvp_dotenv_applied
    if _mvp_dotenv_applied:
        return
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        _mvp_dotenv_applied = True
        return
    with env_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not key:
                continue
            current = os.environ.get(key, "")
            if not str(current).strip():
                os.environ[key] = value
    _mvp_dotenv_applied = True
