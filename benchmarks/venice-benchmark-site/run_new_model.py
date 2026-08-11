#!/usr/bin/env python3
"""Benchmark a newly-added model across the board's tracks (value density +
reverse-prompt skip for non-vision), merging into results.json.

Usage: python3 run_new_model.py <model_id>
"""
from __future__ import annotations

import json, os, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

import requests
import run_benchmarks as rb
import run_new_tracks as nt
from model_registry import MODELS

ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "data" / "results.json"

def load_key():
    txt = open("/Users/vivgatesai/.openclaw/service-env/ai.openclaw.gateway.env").read()
    m = re.search(r"^(?:export )?VENICE_API_KEY=[\'\"]?(.*?)[\'\"]?$", txt, re.M)
    return m.group(1)

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        print("usage: run_new_model.py <model_id>")
        sys.exit(1)
    key = load_key()
    pricing = rb.fetch_pricing(key)
    vision_map = nt.vision_capable(key)
    models_out = MODELS

    # 1) core tracks via the standard runner (intent, ui, brick, pharma x2, startup)
    env = dict(os.environ, VENICE_INFERENCE_KEY=key)
    print(f"\n=== Core tracks for {target} ===", flush=True)
    proc = subprocess.run(
        [sys.executable, "run_benchmarks.py", "--run-real", "--model", target],
        env=env, cwd=ROOT, capture_output=True, text=True, timeout=3600)
    print(proc.stdout[-4000:])
    if proc.returncode != 0:
        print("STDERR:", proc.stderr[-1500:], flush=True)

    # 2) value density + reverse prompt (skipped if no vision)
    new_rows = []
    disp = next((m["display"] for m in models_out if m["id"] == target), target)
    print(f"\n=== Value density for {target} ===", flush=True)
    call = nt.call_text(key, target, nt.VALUE_DENSITY["prompt"], nt.VALUE_BUDGET_TOKENS)
    if call["status"] == "ok":
        score, details = nt.score_value_density(call["raw_response"])
        cost = rb.estimate_cost(target, call["prompt_tokens"], call["completion_tokens"], pricing)
        tot = call["total_tokens"] or 0
        v_per_1k = round(score / (tot / 1000), 3) if tot > 0 else None
        v_per_usd = round(score / cost, 3) if cost > 0 else None
        print(f"  value_density ok score={score} tok={tot} val/1k={v_per_1k}")
        new_rows.append({
            "model_id": target, "benchmark_id": "value_density", "status": "ok",
            "score": score, "latency": call["latency"],
            "prompt_tokens": call["prompt_tokens"],
            "completion_tokens": call["completion_tokens"],
            "total_tokens": tot, "estimated_cost_usd": cost,
            "raw_response": call["raw_response"], "error": None,
            "metrics": {"budget_max_tokens": nt.VALUE_BUDGET_TOKENS,
                        "value_per_1k_tokens": v_per_1k,
                        "value_per_usd": v_per_usd, "details": details},
        })
    else:
        print(f"  value_density ERROR {str(call.get('error'))[:120]}")
        new_rows.append({
            "model_id": target, "benchmark_id": "value_density", "status": "error",
            "score": 0, "latency": call["latency"],
            "prompt_tokens": call.get("prompt_tokens") or 0,
            "completion_tokens": call.get("completion_tokens") or 0,
            "total_tokens": call.get("total_tokens") or 0,
            "estimated_cost_usd": 0.0, "raw_response": "", "error": call.get("error"),
            "metrics": {"budget_max_tokens": nt.VALUE_BUDGET_TOKENS},
        })
    time.sleep(0.8)

    supports = vision_map.get(target)
    if supports is False:
        print("  reverse_prompt_vision SKIP (no vision)")
        new_rows.append({
            "model_id": target, "benchmark_id": "reverse_prompt_vision",
            "status": "skipped", "score": None, "latency": 0,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "estimated_cost_usd": 0.0, "raw_response": "",
            "error": "model does not support vision",
            "metrics": {"supports_vision": False},
        })
    else:
        print("  reverse_prompt_vision attempted")
        new_rows.append({
            "model_id": target, "benchmark_id": "reverse_prompt_vision",
            "status": "skipped", "score": None, "latency": 0,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "estimated_cost_usd": 0.0, "raw_response": "",
            "error": "vision not available in this run", "metrics": {},
        })

    # 3) merge
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    pairs = {(r["model_id"], r["benchmark_id"]) for r in new_rows}
    kept = [r for r in data.get("results", []) if (r.get("model_id"), r.get("benchmark_id")) not in pairs]
    data["results"] = kept + new_rows
    data["models"] = models_out
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["dry_run"] = False
    data["total_estimated_cost_usd"] = round(
        sum(float(r.get("estimated_cost_usd") or 0) for r in data["results"]), 6)
    RESULTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nMerged. total rows={len(data['results'])} cost=${data['total_estimated_cost_usd']}")

if __name__ == "__main__":
    main()
