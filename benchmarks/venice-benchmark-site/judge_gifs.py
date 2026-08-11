#!/usr/bin/env python3
"""LLM-judge the rendered GIF Arena entries.

Each model's raw HTML + meta is scored by the judge model on five axes
(alpaca recognizability, dance quality, technical polish, creativity, code
quality) -> weighted gif_score. Results go to data/gif_arena/scores.json
and feed make_gif_page.py.

Try to read the actual rendered GIF as an image when the judge model supports
vision; otherwise judge from the HTML source.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARENA = ROOT / "data" / "gif_arena"
API = "https://api.venice.ai/api/v1/chat/completions"

JUDGE_SYSTEM = (
    "You are the BenchmarkViv GIF Arena judge. Rate a dancing-alpaca HTML "
    "animation on five axes, each 0-100: alpaca_recognizability (does it look "
    "like an alpaca?), dance_quality (lively, varied choreography), "
    "technical_polish (smooth, no broken layout), creativity (visual flair, "
    "background, style), code_quality (clean, self-contained, maintainable). "
    "Reply with ONLY a JSON object, no commentary: "
    '{"alpaca_recognizability":0,"dance_quality":0,"technical_polish":0,'
    '"creativity":0,"code_quality":0,"gif_score":0,"notes":"one sentence"}. '
    "gif_score = recognizability*0.25 + dance*0.25 + polish*0.20 + creativity*0.15 + code*0.15."
)

VISION_MODELS = {"gpt-image-2", "openai-gpt-56-sol-pro", "claude-opus-5", "kimi-k3-fast-api"}


def load_key() -> str:
    v = os.environ.get("VENICE_INFERENCE_KEY")
    if v:
        return v
    for path in (Path.home() / ".openclaw" / "service-env" / "ai.openclaw.gateway.env",
                 Path.home() / ".paperclip" / "instances" / "default" / ".env"):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("VENICE_INFERENCE_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            continue
    raise RuntimeError("VENICE_INFERENCE_KEY not found")


def chat(key: str, model: str, messages: list) -> str:
    payload = {"model": model, "messages": messages, "max_tokens": 800,
               # keep the judge from burning its budget on reasoning
               "venice_parameters": {"disable_thinking": True,
                                     "strip_thinking_response": True}}
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)["choices"][0]["message"]["content"]


def parse_score(text: str) -> dict:
    t = text.strip()
    lo, hi = t.find("{"), t.rfind("}")
    if lo >= 0 and hi > lo:
        t = t[lo:hi + 1]
    try:
        return json.loads(t)
    except Exception:
        return {"parse_error": text[:200]}


def judge_one(key: str, judge_model: str, slug: str, use_vision: bool) -> dict | None:
    src = ARENA / f"{slug}.html"
    if not src.exists():
        print(f"skip  {slug}: no html")
        return None
    html_src = src.read_text(encoding="utf-8")[:12000]
    content = f"Score this self-contained HTML animation:\n\n{html_src}"

    if use_vision:
        gif = ARENA / f"{slug}.gif"
        if gif.exists():
            with open(gif, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            content = (
                f"Here is a rendered GIF of the animation AND its source. "
                f"Score the animation.\nGIF (first frame): [image]\nHTML:\n{html_src[:8000]}")
            messages = [
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": content},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/gif;base64,{b64}"}},
                ]},
            ]
            try:
                raw = chat(key, judge_model, messages)
                score = parse_score(raw)
                score["judge_model"] = judge_model
                score["mode"] = "vision"
                return score
            except Exception as exc:
                print(f"  {slug}: vision judge failed ({exc}), falling back to source")
    try:
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": content},
        ]
        raw = chat(key, judge_model, messages)
        score = parse_score(raw)
        score["judge_model"] = judge_model
        score["mode"] = "source"
        return score
    except Exception as exc:
        print(f"FAIL  {slug}: {exc}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append")
    ap.add_argument("--judge-model", default="kimi-k3-fast-api")
    ap.add_argument("--no-vision", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    slugs = args.slug or sorted(
        p.stem for p in ARENA.glob("*.html") if not p.name.endswith(".meta.json"))
    scores_path = ARENA / "scores.json"
    scores = json.loads(scores_path.read_text(encoding="utf-8")) if scores_path.exists() else {}

    key = None if args.dry_run else load_key()
    for slug in slugs:
        use_vision = (not args.no_vision) and args.judge_model in VISION_MODELS
        if args.dry_run:
            scores[slug] = {"dry_run": True, "gif_score": 0}
            print(f"dry   {slug}")
            continue
        score = judge_one(key, args.judge_model, slug, use_vision)
        if score:
            scores[slug] = {**score, "judged_at": datetime.now(timezone.utc).isoformat()}
            print(f"judged {slug}: gif_score={score.get('gif_score')} "
                  f"({score.get('mode')})")
    scores_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
