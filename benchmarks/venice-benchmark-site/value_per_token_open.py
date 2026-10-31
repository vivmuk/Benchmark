#!/usr/bin/env python3
"""Open-ended value-per-token shootout: Opus 4.8 Fast vs Fable 5 vs Fable 5.1.

Open-ended architecture task (models CAN pad). Deterministic 10-topic coverage
rubric scores value 0-100 independent of raw length. Measures value per token,
per completion token, and per USD, plus reasoning overhead signals.
"""
from __future__ import annotations

import json, os, sqlite3, time
from pathlib import Path

import requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
MODELS = ["claude-opus-4-8-fast", "claude-fable-5", "claude-fable-5-1"]
MAX_TOKENS = 128000

PRICING = {
    "claude-opus-4-8-fast": {"input": 12.0, "output": 60.0},
    "claude-fable-5":       {"input": 12.0, "output": 60.0},
    "claude-fable-5-1":     {"input": 10.0, "output": 50.0},
}

TASK = (
    "Design a production-grade distributed rate limiter for a multi-region API "
    "gateway serving ~50k req/s. Be thorough and specific — cover every topic that "
    "matters to a senior engineer reviewing your design. Name concrete technologies, "
    "give concrete trade-offs, and don't hand-wave. Topics to cover: rate-limiting "
    "algorithm choice, data structure, where state lives, multi-region consistency, "
    "failure/fallback behavior, the exposed API/headers, observability, edge cases "
    "(burst, clock skew, header spoofing, thundering herd), deployment and "
    "configuration, and how you'd test it.\n\n"
    "No length limit. Write as much as genuinely useful."
)

COVERAGE = {
    "algorithm": ["token bucket", "leaky bucket", "sliding window", "fixed window",
                  "gcra", "generic cell rate", "moving window", "sliding log"],
    "data_structure": ["redis", "zset", "sorted set", "lua", "hash", "memcached",
                       "counter", "bitset", "hyperloglog"],
    "state_location": ["centralized", "edge", "local", "etcd", "consul", "shared",
                       "distributed", "state store", "global"],
    "multi_region": ["multi-region", "multi region", "region", "eventual", "async",
                     "replicate", "replication", "consistency", "clock", "sync"],
    "failure_behavior": ["fail-open", "fail open", "fail-closed", "fail closed",
                         "fallback", "degrade", "circuit breaker", "graceful"],
    "api_headers": ["retry-after", "x-ratelimit", "header", "429", "status code",
                    "x-forwarded", "rate limit"],
    "observability": ["metric", "prometheus", "counter", "histogram", "grafana",
                      "slo", "latency", "alert", "p99"],
    "edge_cases": ["burst", "clock skew", "skew", "spoof", "proxy", "cdn",
                   "x-forwarded-for", "thundering herd", "cidr", "drift"],
    "deployment": ["sidecar", "envoy", "gateway", "config", "hot reload", "rolling",
                   "deployment", "kubernetes", "nginx", "rollout"],
    "testing": ["load test", "chaos", "unit test", "integration test", "canary",
                "simulate", "benchmark", "k6", "jmeter", "deterministic"],
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


def score_coverage(text: str) -> dict:
    low = (text or "").lower()
    hits, missing = {}, []
    for topic, kws in COVERAGE.items():
        if any(k in low for k in kws):
            hits[topic] = True
        else:
            hits[topic] = False
            missing.append(topic)
    n = sum(1 for v in hits.values() if v)
    score = round(n / len(COVERAGE) * 100)
    return {"score": score, "n_topics": n, "hits": hits, "missing": missing}


def run(model, key):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": TASK}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    start = time.monotonic()
    r = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    lat = round(time.monotonic() - start, 2)
    if r.status_code != 200:
        return {"status": "error", "latency": lat, "error": r.text[:400]}
    d = r.json()
    msg = ((d.get("choices") or [{}])[0].get("message") or {})
    usage = d.get("usage") or {}
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    return {
        "status": "ok", "latency": lat,
        "content": content, "reasoning_len": len(reasoning),
        "finish_reason": ((d.get("choices") or [{}])[0].get("finish_reason")),
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
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
            cov = score_coverage(r["content"])
            words = len((r["content"] or "").split())
            comp = r["completion_tokens"]
            total = r["total_tokens"]
            cost = (r["prompt_tokens"] / 1e6) * pr["input"] + (comp / 1e6) * pr["output"]
            score = cov["score"]
            r["score"] = score
            r["words"] = words
            r["value_per_token"] = round(score / total, 5) if total else None
            r["value_per_completion_token"] = round(score / comp, 5) if comp else None
            r["value_per_1k"] = round(score / (total / 1000), 3) if total else None
            r["value_per_usd"] = round(score / cost, 1) if cost else None
            r["cost_usd"] = round(cost, 6)
            r["coverage"] = cov
        results.append(r)
        print(f"[{model}] score={r.get('score')} words={r.get('words')} "
              f"comp_tok={r.get('completion_tokens')} total={r.get('total_tokens')} "
              f"finish={r.get('finish_reason')} val/tok={r.get('value_per_token')} "
              f"val/comp_tok={r.get('value_per_completion_token')} "
              f"cost=${r.get('cost_usd')} val/USD={r.get('value_per_usd')} "
              f"missing={r.get('coverage',{}).get('missing')}", flush=True)
        time.sleep(0.6)

    out = Path("data") / "value_per_token_open.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nwrote", out)


if __name__ == "__main__":
    main()