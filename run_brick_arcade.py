#!/usr/bin/env python3
"""
BenchmarkViv Arcade runner.

Runs the brick_breaker_maximum prompt against 5 models via the Venice API and
builds the data/brick_arcade.json that arcade.html consumes.

Usage:
    python3 run_brick_arcade.py                   # dry-run (no API calls)
    python3 run_brick_arcade.py --dry-run         # same as default
    python3 run_brick_arcade.py --run-real        # real API calls (~$3.58 worst case)

Output paths:
    arcade/<model>-brick.html        captured HTML for that model
    arcade/<model>-brick.raw.txt     full response if extraction failed
    data/brick_arcade.json           per-model results used by arcade.html
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# Reuse the existing scoring + pricing + sane-defaults from the main runner.
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "benchmarks" / "venice-benchmark-site"))
from run_benchmarks import (  # noqa: E402
    FALLBACK_PRICING,
    DEFAULT_PRICING,
    fetch_pricing,
    estimate_cost,
    score_brick_breaker_realism,
    API_URL,
)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

ROOT              = Path(__file__).parent
SITE_DIR          = ROOT / "benchmarks" / "venice-benchmark-site"
PROMPT_FILE       = SITE_DIR / "prompts" / "brick_breaker_maximum.md"
OUTPUT_DIR        = SITE_DIR / "arcade"
RESULTS_PATH      = SITE_DIR / "data" / "brick_arcade.json"
DATA_RESULTS_JSON = SITE_DIR / "data" / "results.json"

# 5 models, mirrors run_benchmarks.py.MODELS minus claude-fable-5 (excluded
# by MODEL_BENCHMARK_LIMITS in the main runner; this script stays simple but
# honors the same boundary).
MODELS = [
    {"id": "openai-gpt-55",      "display": "GPT-5.5"},
    {"id": "claude-opus-4-8",    "display": "Opus 4.8"},
    {"id": "zai-org-glm-5-2",    "display": "GLM 5.2"},
    {"id": "deepseek-v4-pro",    "display": "DeepSeek V4"},
    {"id": "minimax-m3-preview", "display": "MiniMax M3"},
]

MAX_TOKENS         = 16384  # Per the C-prompt directive "Don't limit them" — kept well above the
                             # historical default (2-4K); capped at 16K because the original 32K
                             # attempt stalled GPT-5.5 / Opus beyond 4 minutes with zero bytes
                             # streamed. 16K ≈ 6,000-10,000 lines of HTML/CSS/JS, which is
                             # comfortably enough headroom for an "advanced" brick break in
                             # a single prompt response.
TEMPERATURE        = 0.5    # mirrors main runner
REQUEST_TIMEOUT    = 480    # 16K output can stream for several minutes per call
RATE_LIMIT_SLEEP   = 1.0


# -------------------------------------------------------------------
# Prompt
# -------------------------------------------------------------------

def load_prompt() -> str:
    raw = PROMPT_FILE.read_text(encoding="utf-8")
    # Pull the first fenced ``` block (model-facing prompt) out of the markdown.
    m = re.search(r"```\s*\n(.*?)```", raw, re.DOTALL)
    if not m:
        raise RuntimeError(f"No fenced prompt block in {PROMPT_FILE}")
    return m.group(1).strip()


# -------------------------------------------------------------------
# Output extraction
# -------------------------------------------------------------------

FENCE_HTML_RE = re.compile(r"```(?:html)?\s*\n(.*?)```", re.DOTALL)
DOCTYPE_RE   = re.compile(r"<!DOCTYPE\s+html", re.IGNORECASE)


def extract_html(text: str) -> str | None:
    """Find the actual HTML in the response. Returns None if not found."""
    if not text:
        return None
    stripped = text.strip()
    # Model wrote the HTML directly (no fence).
    if DOCTYPE_RE.search(stripped):
        return stripped
    # Model fenced the HTML inside a code block.
    m = FENCE_HTML_RE.search(stripped)
    if m:
        return m.group(1).strip()
    # Some models wrap code fences in ```htmlCODE``` form without breaks;
    # try ```html opener specifically.
    m = re.search(r"```html\s*\n(.+?)\n```", stripped, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


# -------------------------------------------------------------------
# API call
# -------------------------------------------------------------------

def call_venice(api_key: str, model_id: str, prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "stream": False,
    }
    t0 = time.time()
    r = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    elapsed = time.time() - t0
    if r.status_code != 200:
        return {
            "ok": False,
            "latency": elapsed,
            "status": r.status_code,
            "error": r.text[:400],
            "raw": "",
        }
    body = r.json()
    try:
        choice = body["choices"][0]
        text   = choice["message"]["content"]
        usage  = body.get("usage", {}) or {}
    except (KeyError, IndexError, TypeError):
        return {
            "ok": False,
            "latency": elapsed,
            "status": 200,
            "error": "Malformed response",
            "raw": json.dumps(body)[:400],
        }
    return {
        "ok": True,
        "latency": elapsed,
        "text": text,
        "prompt_tokens":     usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens":      usage.get("total_tokens"),
    }


# -------------------------------------------------------------------
# Per-model run
# -------------------------------------------------------------------

def run_one(api_key: str | None, model: dict, prompt: str, pricing: dict) -> dict:
    """Run a single model + return a result record."""
    raw_text = ""
    if api_key:
        call = call_venice(api_key, model["id"], prompt)
        raw_text = call.get("text") or ""
        latency_s = call.get("latency") or 0.0
        prompt_t  = call.get("prompt_tokens") or 0
        comp_t    = call.get("completion_tokens") or 0
        rates     = pricing.get(model["id"]) or DEFAULT_PRICING
        cost      = (prompt_t / 1_000_000) * rates["input"] + (comp_t / 1_000_000) * rates["output"]
        ok        = bool(call.get("ok"))
        err       = call.get("error") if not ok else None
    else:
        # Sample data for dry-run path. Hand-picked to give a plausible leaderboard.
        latency_s = 21.4
        prompt_t  = 980
        comp_t    = 14_200
        rates     = pricing.get(model["id"]) or DEFAULT_PRICING
        cost      = (prompt_t / 1_000_000) * rates["input"] + (comp_t / 1_000_000) * rates["output"]
        ok        = True
        err       = None
        # Synthetic placeholder HTML for the dry-run path so the arcade page renders.
        synth_html = (
            "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"/>"
            "<title>Dry-run brick (sample)</title><style>"
            "html,body{margin:0;height:100%;background:#0A0A0F;color:#F4F2EE;"
            "font-family:Geist,sans-serif;display:grid;place-items:center}"
            "</style></head><body>"
            f"<p style=\"font:500 .9rem monospace\">dry-run sample for {model['display']}</p>"
            "</body></html>"
        )
        raw_text = synth_html

    # Try to extract real HTML and save it.
    html = extract_html(raw_text)
    out_html_path = OUTPUT_DIR / f"{model['id']}-brick.html"
    out_raw_path  = OUTPUT_DIR / f"{model['id']}-brick.raw.txt"
    saved_path = None
    if html:
        out_html_path.write_text(html, encoding="utf-8")
        saved_path = f"arcade/{out_html_path.name}"
    else:
        out_raw_path.write_text(raw_text, encoding="utf-8")
        saved_path = f"arcade/{out_raw_path.name}"

    score = score_brick_breaker_realism(html or raw_text) if ok else 0

    return {
        "model_id":          model["id"],
        "display":           model["display"],
        "status":            "ok" if ok else "error",
        "latency":           round(latency_s, 2),
        "prompt_tokens":     prompt_t,
        "completion_tokens": comp_t,
        "total_tokens":      (prompt_t + comp_t),
        "estimated_cost_usd": round(cost, 4),
        "score":             score,
        "html":              saved_path,
        "raw_chars":         len(raw_text),
        "note":              "dry-run sample HTML" if not api_key else "real Venice API run",
        "error":             err,
    }


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _read_venice_key_from_hermes_config() -> str | None:
    """Best-effort fallback: parse the active :model: api_key from ~/.hermes/config.yaml.

    The user has been told to wire any "real" Venice credentials here. We only ever
    return values that look like Venice bearer tokens (alpha+digit+_- length >= 30),
    so unrelated config entries never leak in.
    """
    candidates = [
        Path.home() / ".hermes" / "config.yaml",
        Path("/Users/vivgatesai/.hermes/config.yaml"),
    ]
    for cfg in candidates:
        if not cfg.exists():
            continue
        try:
            text = cfg.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Find the :model: block and pull its api_key first; fall through to any api_key: line.
        for pat in (
            r"^:model:\s*\n(?:\s+.+\n)*?\s+api_key:\s*['\"]?([A-Za-z0-9_\-]{30,})['\"]?",
            r"^api_key:\s*['\"]?([A-Za-z0-9_\-]{30,})['\"]?",
            r"^\s*api_key:\s*['\"]?([A-Za-z0-9_\-]{30,})['\"]?",
        ):
            m = re.search(pat, text, re.M)
            if m:
                return m.group(1)
    return None


def pricing_synthetic() -> dict:
    return {m["id"]: (FALLBACK_PRICING.get(m["id"]) or DEFAULT_PRICING) for m in MODELS}


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Use sample pricing + synthetic HTML; no API calls.")
    ap.add_argument("--run-real", action="store_true", help="Real Venice API calls; costs apply.")
    ap.add_argument("--model", help="Run only this model id (e.g. openai-gpt-55).")
    args = ap.parse_args()

    if not args.dry_run and not args.run_real:
        args.dry_run = True

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "data").mkdir(parents=True, exist_ok=True)

    prompt = load_prompt()
    print(f"Loaded prompt ({len(prompt)} chars) from {PROMPT_FILE.name}")
    print(f"max_tokens = {MAX_TOKENS}, models = {len(MODELS)}, output dir = {OUTPUT_DIR.relative_to(ROOT)}")
    print()

    api_key = None
    pricing = pricing_synthetic()
    if args.run_real:
        api_key = (
            os.environ.get("VENICE_INFERENCE_KEY")
            or os.environ.get("VENICE_API_KEY")
            or _read_venice_key_from_hermes_config()
        )
        if not api_key:
            print("ERROR: --run-real requires VENICE_INFERENCE_KEY env var or a Venice api_key in ~/.hermes/config.yaml under :model:", file=sys.stderr)
            return 2
        try:
            print("Fetching live pricing from /v1/models ...")
            pricing = fetch_pricing(api_key)
            print(f"  using live pricing for {len(pricing)} models")
        except Exception as e:
            print(f"  live pricing fetch failed ({e}); falling back to FALLBACK_PRICING")

    targets = [m for m in MODELS if not args.model or m["id"] == args.model]
    if args.model and not targets:
        print(f"ERROR: no model matches --model {args.model}", file=sys.stderr)
        return 2

    results  = []
    total_cost = 0.0
    for model in targets:
        label = f"{model['display']:<14} ({model['id']})"
        print(f"-> {label}", flush=True)
        try:
            r = run_one(api_key, model, prompt, pricing)
        except requests.exceptions.RequestException as e:
            r = {
                "model_id": model["id"], "display": model["display"], "status": "error",
                "latency": 0, "prompt_tokens": None, "completion_tokens": None,
                "total_tokens": None, "estimated_cost_usd": 0.0, "score": 0,
                "html": None, "raw_chars": 0, "note": "request exception",
                "error": str(e)[:300],
            }
        total_cost += r.get("estimated_cost_usd") or 0.0
        print(
            f"   status: {r['status']}  score={r['score']}  "
            f"lat={r['latency']}s  comp_tok={r.get('completion_tokens')}  "
            f"html={r['html'] or '(none)'}"
        )
        if r.get("error"):
            print(f"   error: {r['error'][:160]}")
        results.append(r)
        if api_key:
            time.sleep(RATE_LIMIT_SLEEP)

    print()
    print(f"Total estimated cost: ${total_cost:.4f}")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run":       bool(args.dry_run),
        "prompt_file":   str(PROMPT_FILE.relative_to(SITE_DIR)),
        "max_tokens":    MAX_TOKENS,
        "models":        MODELS,
        "results":       results,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)} ({len(results)} runs)")

    # Friendly "who won" line.
    winners = sorted(
        [r for r in results if r.get("status") == "ok"],
        key=lambda r: -r.get("score", 0),
    )[:3]
    print()
    print("Top 3 by heuristic score:")
    for i, r in enumerate(winners, 1):
        print(f"  {i}. {r['display']:<14} {r['score']}  ({r['html']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
