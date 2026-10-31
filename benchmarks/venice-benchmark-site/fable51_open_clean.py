#!/usr/bin/env python3
import json, os, sqlite3, time
from pathlib import Path
import requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
MODEL = "claude-fable-5-1"
PRICING = {"input": 10.0, "output": 50.0}

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


def score_coverage(text):
    low = (text or "").lower()
    hits = {t: any(k in low for k in kws) for t, kws in COVERAGE.items()}
    n = sum(hits.values())
    return {"score": round(n / len(COVERAGE) * 100), "n_topics": n,
            "hits": hits, "missing": [t for t, v in hits.items() if not v]}


key = load_key()
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": TASK}],
    "max_tokens": 128000,
    "temperature": 0.3,
}
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
t0 = time.monotonic()
r = requests.post(API_URL, headers=headers, json=payload, timeout=900)
lat = round(time.monotonic() - t0, 2)
print("status", r.status_code, "lat", lat, flush=True)
d = r.json()
msg = ((d.get("choices") or [{}])[0].get("message") or {})
usage = d.get("usage") or {}
content = msg.get("content") or ""
comp = int(usage.get("completion_tokens") or 0)
prompt = int(usage.get("prompt_tokens") or 0)
total = int(usage.get("total_tokens") or 0)
cov = score_coverage(content)
words = len(content.split())
cost = (prompt / 1e6) * PRICING["input"] + (comp / 1e6) * PRICING["output"]
score = cov["score"]
out = {
    "model": MODEL, "status": "ok", "latency": lat,
    "finish_reason": ((d.get("choices") or [{}])[0].get("finish_reason")),
    "prompt_tokens": prompt, "completion_tokens": comp, "total_tokens": total,
    "words": words, "score": score,
    "value_per_token": round(score / total, 5) if total else None,
    "value_per_completion_token": round(score / comp, 5) if comp else None,
    "value_per_1k": round(score / (total / 1000), 3) if total else None,
    "value_per_usd": round(score / cost, 1) if cost else None,
    "cost_usd": round(cost, 6),
    "coverage": cov, "content": content,
    "usage_keys": list(usage.keys()), "msg_keys": list(msg.keys()),
}
Path("data/value_per_token_open_fable51.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
summary = {k: v for k, v in out.items() if k != "content"}
print(json.dumps(summary, indent=2))