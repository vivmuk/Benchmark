#!/usr/bin/env python3
"""
Generate one Brick Breaker game per model — identical prompt, identical settings.

Usage:
    VENICE_INFERENCE_KEY=... python3 generate_brick_games.py            # all models
    VENICE_INFERENCE_KEY=... python3 generate_brick_games.py model-id   # one model

Output: games/<model_id>.html + games/manifest.json
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
API_KEY = os.environ.get("VENICE_INFERENCE_KEY", "")

GAMES_DIR = Path("games")
MANIFEST_PATH = GAMES_DIR / "manifest.json"

MODELS = [
    {"id": "openai-gpt-55",      "display": "GPT-5.5"},
    {"id": "claude-fable-5",     "display": "Fable 5"},
    {"id": "claude-opus-4-8",    "display": "Opus 4.8"},
    {"id": "zai-org-glm-5-2",    "display": "GLM 5.2"},
    {"id": "deepseek-v4-pro",    "display": "DeepSeek V4"},
    {"id": "minimax-m3-preview", "display": "MiniMax M3"},
    {"id": "grok-4-5",           "display": "Grok 4.5"},
]

# EXACT same prompt as the brick_breaker_realism benchmark (data/results.json)
PROMPT = (
    "Create a single self-contained HTML file for a realistic Brick Breaker "
    "game with Canvas. Include: ball physics with angle reflection, paddle "
    "with mouse/keyboard/touch controls, brick grid with collision detection, "
    "score/lives/level, start/game-over/victory screens, particle effects on "
    "brick break, synthesized sound effects with Web Audio API, responsive "
    "design, dark neon aesthetic."
)

MAX_TOKENS = 16384
TEMPERATURE = 0.5
TIMEOUT = 600


def extract_html(text: str) -> str | None:
    """Pull a complete HTML document out of a model response."""
    m = re.search(r"```html\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    candidate = m.group(1).strip() if m else text.strip()
    if "<html" not in candidate.lower():
        m2 = re.search(r"<!DOCTYPE html.*", text, re.DOTALL | re.IGNORECASE)
        if m2:
            candidate = m2.group(0)
            fence_end = candidate.find("```")
            if fence_end != -1:
                candidate = candidate[:fence_end]
    low = candidate.lower()
    if "<html" in low and "</html>" in low:
        return candidate[: low.rfind("</html>") + len("</html>")]
    return None


def generate(model: dict) -> dict:
    print(f"→ {model['display']} ({model['id']}) ...", flush=True)
    t0 = time.time()
    entry = {
        "model_id": model["id"],
        "display": model["display"],
        "prompt": PROMPT,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "status": "error",
        "file": None,
        "chars": 0,
        "latency_s": None,
        "completion_tokens": None,
        "error": None,
    }
    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": model["id"],
                "messages": [{"role": "user", "content": PROMPT}],
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
            },
            timeout=TIMEOUT,
        )
        entry["latency_s"] = round(time.time() - t0, 1)
        if resp.status_code != 200:
            entry["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            print(f"  ✗ {entry['error']}")
            return entry
        data = resp.json()
        text = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage", {})
        entry["completion_tokens"] = usage.get("completion_tokens")
        html = extract_html(text)
        if not html:
            entry["error"] = f"no complete HTML document in response ({len(text)} chars)"
            (GAMES_DIR / f"{model['id']}.raw.txt").write_text(text)
            print(f"  ✗ {entry['error']} — raw saved")
            return entry
        out = GAMES_DIR / f"{model['id']}.html"
        out.write_text(html)
        entry.update(status="ok", file=out.name, chars=len(html))
        print(f"  ✓ {out.name} ({len(html):,} chars, {entry['latency_s']}s)")
    except Exception as e:  # noqa: BLE001
        entry["error"] = str(e)[:300]
        entry["latency_s"] = round(time.time() - t0, 1)
        print(f"  ✗ {entry['error']}")
    return entry


def main():
    if not API_KEY:
        sys.exit("Set VENICE_INFERENCE_KEY")
    GAMES_DIR.mkdir(exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())
    for model in MODELS:
        if only and model["id"] != only:
            continue
        manifest[model["id"]] = generate(model)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
        time.sleep(1)
    ok = [m for m in manifest.values() if m["status"] == "ok"]
    print(f"\n{len(ok)}/{len(manifest)} games generated. Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
