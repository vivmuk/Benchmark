#!/usr/bin/env python3
"""BenchmarkViv GIF Arena — code-to-GIF track.

Each model gets the same prompt: build a self-contained HTML page animating
something deliberately hard (dancing alpaca). The model's HTML is saved,
rendered headlessly (Chrome frames -> ffmpeg GIF), and scored by an LLM judge.

Pipeline:
  1. run_gif_track.py --prompt --models a,b,c   (or --all)  -> calls Venice API
  2. render_gifs.py                             -> Chrome frames -> *.gif
  3. judge_gifs.py                              -> LLM scores per model
  4. make_gif_page.py                           -> gif-arena.html on the site

Use --dry-run to skip API calls and generate placeholder outputs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "gif_arena"
API = "https://api.venice.ai/api/v1/chat/completions"

DEFAULT_PROMPT = (
    "Create a single self-contained HTML document (no external files, no CDN, "
    "no images) that shows a cute alpaca dancing. Make it genuinely impressive: "
    "a recognizable fluffy alpaca with a long neck, ears, and pom-pom tail, "
    "performing a lively dance with body bounces, limb waves, and a fun loop. "
    "Use inline CSS and JavaScript animation (CSS keyframes or canvas). "
    "The page should animate on load forever, look polished with a nice "
    "background and colors, and be at least 15 seconds of continuous motion. "
    "Output ONLY the complete HTML document inside a single markdown code block."
)

DEFAULT_MODELS = [
    "kimi-k3-fast-api", "deepseek-v4-flash-0731", "openai-gpt-56-sol-pro",
    "claude-opus-5", "minimax-m3-preview",
]

JUDGE_SYSTEM = (
    "You are the BenchmarkViv GIF Arena judge. Rate the animation quality of a "
    "dancing-alpaca HTML page on five axes, each 0-100: "
    "alpaca_recognizability (does it look like an alpaca), dance_quality (is the "
    "choreography lively and varied), technical_polish (smooth animation, "
    "layout, no broken rendering), creativity (visual flair, background, style), "
    "code_quality (clean, well-structured, no hacks). "
    "Reply with ONLY a JSON object: "
    '{"alpaca_recognizability":0,"dance_quality":0,"technical_polish":0,'
    '"creativity":0,"code_quality":0,"gif_score":0,"notes":"one sentence"} '
    "where gif_score is the weighted composite (recognizability 25%, dance 25%, "
    "polish 20%, creativity 15%, code 15%)."
)


def load_key() -> str:
    """Read the Venice inference key from known env locations without echoing."""
    for env_name in ("VENICE_INFERENCE_KEY",):
        v = os.environ.get(env_name)
        if v:
            return v
    for path in (
        Path.home() / ".openclaw" / "service-env" / "ai.openclaw.gateway.env",
        Path.home() / ".paperclip" / "instances" / "default" / ".env",
    ):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("VENICE_INFERENCE_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            continue
    raise RuntimeError("VENICE_INFERENCE_KEY not found")


def fetch(key: str, url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def extract_html(text: str) -> str:
    """Pull HTML out of a model response (strip fences / stray prose)."""
    if "```" in text:
        blocks = text.split("```")
        for i in range(1, len(blocks), 2):
            chunk = blocks[i]
            if "html" in chunk[:12].lower().lstrip():
                chunk = chunk.split("\n", 1)[1] if "\n" in chunk else chunk
            if "<html" in chunk.lower() or "<!doctype" in chunk.lower() or "<canvas" in chunk.lower():
                return chunk.strip()
        # fallback: longest fenced block
        return max((blocks[i] for i in range(1, len(blocks), 2)), key=len).strip()
    # no fences: try the html region
    lo = text.lower().find("<!doctype")
    if lo < 0:
        lo = text.lower().find("<html")
    if lo >= 0:
        hi = text.lower().rfind("</html>")
        if hi > lo:
            return text[lo:hi + 7]
    return text.strip()


def load_models(raw: str | None) -> list[str]:
    if raw:
        return [m.strip() for m in raw.split(",") if m.strip()]
    return DEFAULT_MODELS


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", help="comma-separated model ids")
    ap.add_argument("--all", action="store_true", help="all models from results.json")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--dry-run", action="store_true", help="no API calls")
    ap.add_argument("--model-id", default="deepseek-v4-flash-0731",
                    help="model used to ask the other models (judge/worker pool)")
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)

    if args.all:
        d = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))
        models = [m["id"] for m in d["models"] if m["id"] != args.model_id]
    else:
        models = load_models(args.models)

    for mid in models:
        slug = mid.replace("_", "-")
        out = DATA / f"{slug}.html"
        meta = DATA / f"{slug}.meta.json"
        if out.exists() and "--force" not in sys.argv:
            print(f"skip  {slug} (exists)")
            continue
        if args.dry_run:
            out.write_text(
                f"<!doctype html><html><body><h1>{slug}</h1>"
                f"<p>dry-run placeholder — run without --dry-run to generate</p>"
                f"</body></html>", encoding="utf-8")
            meta.write_text(json.dumps(
                {"model_id": mid, "dry_run": True,
                 "generated_at": datetime.now(timezone.utc).isoformat()},
                indent=2), encoding="utf-8")
            print(f"dry   {slug}")
            continue
        key = load_key()
        payload = {
            "model": mid,
            "messages": [
                {"role": "system",
                 "content": "You generate flawless self-contained HTML/JS/CSS demos."},
                {"role": "user", "content": args.prompt},
            ],
            "max_tokens": 6000,
            # deepseek-family models burn the whole budget in reasoning
            # otherwise and emit empty content (finish=length, content=0)
            "venice_parameters": {"disable_thinking": True,
                                  "strip_thinking_response": True},
        }
        try:
            resp = fetch(key, API, payload)
            text = resp["choices"][0]["message"]["content"] or ""
            if not text.strip():
                print(f"SKIP  {slug}: empty response (finish={resp['choices'][0].get('finish_reason')})")
                continue
        except Exception as exc:
            print(f"FAIL  {slug}: {exc}")
            continue
        html_doc = extract_html(text)
        out.write_text(html_doc, encoding="utf-8")
        meta.write_text(json.dumps(
            {"model_id": mid, "model_used": mid,
             "prompt": args.prompt[:200],
             "generated_at": datetime.now(timezone.utc).isoformat(),
             "chars": len(html_doc),
             "raw_preview": text[:500]}, indent=2), encoding="utf-8")
        print(f"done  {slug}  ({len(html_doc)} chars)")

    print(f"\nHTML saved in {DATA}. Next: render_gifs.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
