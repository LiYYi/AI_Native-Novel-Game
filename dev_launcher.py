#!/usr/bin/env python3
"""
Start backend on a free port, then launch Flutter with injected API URL.

Usage:
  python3 dev_launcher.py
  python3 dev_launcher.py -- flutter run -d chrome
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "mvp_text_game"
BACKEND_FILE = BACKEND_DIR / "api_server.py"


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_health(url: str, timeout_s: float = 12.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    raise RuntimeError(f"Backend health check timed out: {url}")


def main() -> int:
    flutter_cmd = ["flutter", "run"]
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        if idx + 1 < len(sys.argv):
            flutter_cmd = sys.argv[idx + 1 :]

    port = find_free_port()
    api_base = f"http://127.0.0.1:{port}"

    backend_env = os.environ.copy()
    backend_env["GAME_API_HOST"] = "127.0.0.1"
    backend_env["GAME_API_PORT"] = str(port)

    backend = subprocess.Popen(
        [sys.executable, str(BACKEND_FILE)],
        cwd=str(BACKEND_DIR),
        env=backend_env,
    )

    try:
        wait_health(f"{api_base}/health")
        print(f"[launcher] backend ready: {api_base}")

        run_cmd = flutter_cmd + [f"--dart-define=GAME_API_BASE_URL={api_base}"]
        print(f"[launcher] running: {' '.join(run_cmd)}")
        result = subprocess.run(run_cmd, cwd=str(ROOT))
        return int(result.returncode)
    finally:
        if backend.poll() is None:
            backend.send_signal(signal.SIGTERM)
            try:
                backend.wait(timeout=3)
            except subprocess.TimeoutExpired:
                backend.kill()


if __name__ == "__main__":
    raise SystemExit(main())
