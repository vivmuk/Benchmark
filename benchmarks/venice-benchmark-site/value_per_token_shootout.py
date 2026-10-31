#!/usr/bin/env python3
"""Value-per-token shootout: Opus 4.8 Fast vs Fable 5 vs Fable 5.1.

Same task (warfarin/ibuprofen JSON), max_tokens lifted to effectively uncapped.
Measures: score (value 0-100), completion/total tokens, and value per token / per 1k / per USD.
"""
from __future__ import annotations

import json, os, sqlite3, time
from pathlib import Path

import requests

import run_new_tracks as nt

API_URL = "https://api.venice.ai/api/v1/chat/completions"
MODELS = ["claude-opus-4-8-fast", "claude-fable-5", "claude-fable-5-1"]
MAX_TOKENS = 128000  # effectively uncapped for this task

# live pricing (USD / 1M tokens) — from the /models endpoint seen earlier
PRICING = {
    "claude-opus-4-8-fast": {"input": 12.0, "output": 60.0},
    "claude-fable-5":       {"input": 12.0, "output": 60.0},
    "claude-fable-5-1":     {"input": 10.0, "output": 50.0},
}

DISPLAY = {
    "claude-opus-4-8-fast": "Opus 4.8 Fast",
    "claude-fable-5":       "Fable 5",
    "claude-fable-5-1":     "Fable 5.1",
}


def load_key():
    key = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if key:
        return key
    db = Path.home() / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    j = json.loads(con.execute(
        "select store_json from auth_profile_store where store_key='primary'").fetchone()[0])
    return (j.get("profiles") or {}).get("venice:cloud", {}).get("key", "")


def run(model, key):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": nt.VALUE_DENSITY["prompt"]}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    start = time.monotonic()
    r = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    lat = round(time.monotonic() - start, 2)
    d = r.json()
    if r.status_code != 200:
        return {"status": "error", "latency": lat, "error": r.text[:400]}
    msg = ((d.get("choices") or [{}])[0].get("message") or {})
    usage = d.get("usage") or {}
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    return {
        "status": "ok", "latency": lat,
        "content": content, "reasoning": reasoning,
        "finish_reason": ((d.get("choices") or [{}])[0].get("finish_reason")),
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
        "reasoning_tokens": usage.get("completion_tokens_details", {}) if isinstance(usage.get("completion_tokens_details"), dict) else usage.get("reasoning_tokens"),
        "usage_keys": list(usage.keys()),
        "msg_keys": list(msg.keys()),
    }


def main():
    key = load_key()
    results = []
    for model in MODELS:
        r = run(model, key)
        pr = PRICING[model]
        if r["status"] == "ok":
            score, details = nt.score_value_density(r["content"])
            comp = r["completion_tokens"]
            total = r["total_tokens"]
            cost = (r["prompt_tokens"] / 1e6) * pr["input"] + (comp / 1e6) * pr["output"]
            r["score"] = score
            r["value_per_token"] = round(score / total, 5) if total else None
            r["value_per_1k"] = round(score / (total / 1000), 3) if total else None
            r["value_per_usd"] = round(score / cost, 1) if cost else None
            r["cost_usd"] = round(cost, 6)
            r["eval_details"] = details
        results.append(r)
        print(f"[{model}] status={r['status']} lat={r.get('latency')} "
              f"score={r.get('score')} comp_tok={r.get('completion_tokens')} "
              f"total_tok={r.get('total_tokens')} finish={r.get('finish_reason')} "
              f"val/tok={r.get('value_per_token')} val/1k={r.get('value_per_1k')} "
              f"cost=${r.get('cost_usd')} val/USD={r.get('value_per_usd')}", flush=True)
        time.sleep(0.6)

    out = Path("data") / "value_per_token_shootout.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nwrote", out)


if __name__ == "__main__":
    main()