#!/usr/bin/env python3
import json, os, sqlite3, time
from pathlib import Path
import requests
import importlib.util

spec = importlib.util.spec_from_file_location("vp", "value_per_token_open.py")
vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)

key = vp.load_key()
model = "claude-fable-5-1"
start = time.monotonic()
r = vp.run(model, key)  # run() uses timeout=300 internally; we re-implement below with 900
print("first attempt:", r.get("status"), r.get("error", "")[:100] if r.get("error") else "")

# Re-do with long timeout + streaming manual call
import requests as _r
payload = {
    "model": model,
    "messages": [{"role": "user", "content": vp.TASK}],
    "max_tokens": vp.MAX_TOKENS,
    "temperature": 0.3,
}
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
t0 = time.monotonic()
resp = _r.post(vp.API_URL, headers=headers, json=payload, timeout=900)
lat = round(time.monotonic() - t0, 2)
d = resp.json()
msg = ((d.get("choices") or [{}])[0].get("message") or {})
usage = d.get("usage") or {}
content = msg.get("content") or ""
pr = vp.PRICING[model]
comp = int(usage.get("completion_tokens") or 0)
prompt = int(usage.get("prompt_tokens") or 0)
total = int(usage.get("total_tokens") or 0)
cov = vp.score_coverage(content)
words = len(content.split())
cost = (prompt / 1e6) * pr["input"] + (comp / 1e6) * pr["output"]
score = cov["score"]
out = {
    "model": model, "status": "ok", "latency": lat,
    "finish_reason": ((d.get("choices") or [{}])[0].get("finish_reason")),
    "prompt_tokens": prompt, "completion_tokens": comp, "total_tokens": total,
    "words": words, "score": score,
    "value_per_token": round(score / total, 5) if total else None,
    "value_per_completion_token": round(score / comp, 5) if comp else None,
    "value_per_1k": round(score / (total / 1000), 3) if total else None,
    "value_per_usd": round(score / cost, 1) if cost else None,
    "cost_usd": round(cost, 6),
    "coverage": cov, "content": content,
}
Path("data/value_per_token_open_fable51.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "content"}, indent=2))
print("content_len", len(content))