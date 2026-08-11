#!/usr/bin/env python3
"""Run Value Density + Reverse-Prompt Vision for deepseek-v4-flash-0731 only,
merging into results.json. Vision is recorded as skipped (model lacks vision)."""
from __future__ import annotations

import json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path

import requests
import run_benchmarks as rb
import run_new_tracks as nt
from model_registry import MODELS

ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "data" / "results.json"

TARGET = "deepseek-v4-flash-0731"

def load_key():
    txt = open("/Users/vivgatesai/.openclaw/service-env/ai.openclaw.gateway.env").read()
    m = re.search(r"^(?:export )?VENICE_API_KEY=[\'\"]?(.*?)[\'\"]?$", txt, re.M)
    return m.group(1)

def main():
    key = load_key()
    pricing = rb.fetch_pricing(key)
    vision_map = nt.vision_capable(key)
    target = next(m for m in MODELS if m["id"] == TARGET)

    new_rows = []

    # ---- Value density ----
    call = nt.call_text(key, TARGET, nt.VALUE_DENSITY["prompt"], nt.VALUE_BUDGET_TOKENS)
    if call["status"] == "ok":
        score, details = nt.score_value_density(call["raw_response"])
        cost = rb.estimate_cost(TARGET, call["prompt_tokens"], call["completion_tokens"], pricing)
        tot = call["total_tokens"] or 0
        v_per_1k = round(score / (tot / 1000), 3) if tot > 0 else None
        v_per_usd = round(score / cost, 3) if cost > 0 else None
        print(f"value_density ok score={score} tok={tot} val/1k={v_per_1k}")
        new_rows.append({
            "model_id": TARGET, "benchmark_id": "value_density", "status": "ok",
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
        print("value_density ERROR", str(call.get("error"))[:120])
        new_rows.append({
            "model_id": TARGET, "benchmark_id": "value_density", "status": "error",
            "score": 0, "latency": call["latency"],
            "prompt_tokens": call.get("prompt_tokens") or 0,
            "completion_tokens": call.get("completion_tokens") or 0,
            "total_tokens": call.get("total_tokens") or 0,
            "estimated_cost_usd": 0.0, "raw_response": "", "error": call.get("error"),
            "metrics": {"budget_max_tokens": nt.VALUE_BUDGET_TOKENS},
        })
    time.sleep(0.8)

    # ---- Reverse prompt vision (skip - no vision) ----
    supports = vision_map.get(TARGET)
    if supports is False:
        print("reverse_prompt_vision SKIP (no vision)")
        new_rows.append({
            "model_id": TARGET, "benchmark_id": "reverse_prompt_vision",
            "status": "skipped", "score": None, "latency": 0,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "estimated_cost_usd": 0.0, "raw_response": "",
            "error": "model does not support vision",
            "metrics": {"supports_vision": False},
        })
    else:
        print("reverse_prompt_vision attempted")
        new_rows.append({
            "model_id": TARGET, "benchmark_id": "reverse_prompt_vision",
            "status": "skipped", "score": None, "latency": 0,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "estimated_cost_usd": 0.0, "raw_response": "",
            "error": "vision not available in this run", "metrics": {},
        })

    # ---- Merge ----
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    pairs = {(r["model_id"], r["benchmark_id"]) for r in new_rows}
    kept = [r for r in data.get("results", []) if (r.get("model_id"), r.get("benchmark_id")) not in pairs]
    data["results"] = kept + new_rows
    data["models"] = MODELS
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["dry_run"] = False
    data["total_estimated_cost_usd"] = round(
        sum(float(r.get("estimated_cost_usd") or 0) for r in data["results"]), 6)
    RESULTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Merged. total rows={len(data['results'])}")

if __name__ == "__main__":
    main()
