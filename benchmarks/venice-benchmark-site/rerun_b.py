#!/usr/bin/env python3
import json, os, sqlite3, sys, time
from pathlib import Path
import requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"

B_PROMPT = (
    "Diagnose this. We run a Python web service behind Postgres. Six days ago we "
    "deployed a new background job that scans a 200,000-row table (no index on the "
    "filtered column, deleted_at). Since then, p99 latency spikes to ~8 seconds "
    "roughly every 30 minutes — always at the same cadence — even though CPU sits "
    "flat at 15%, memory is flat, and the DB itself shows near-zero load during the "
    "spikes. The only thing that saturates during each spike is our DB connection "
    "pool. Give me: (1) the most likely root cause, (2) what the exact 30-minute "
    "cadence specifically tells you, (3) the concrete fix, ranked by least-effort "
    "first. Be specific about mechanisms — don't hand-wave."
)

def load_key():
    key = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if key:
        return key
    db = Path.home() / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    j = json.loads(con.execute(
        "select store_json from auth_profile_store where store_key='primary'").fetchone()[0])
    return (j.get("profiles") or {}).get("venice:cloud", {}).get("key", "")

key = load_key()
payload = {
    "model": "claude-fable-5-1",
    "messages": [{"role": "user", "content": B_PROMPT}],
    "max_tokens": 2048,
    "temperature": 0.3,
}
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
start = time.monotonic()
r = requests.post(API_URL, headers=headers, json=payload, timeout=300)
lat = round(time.monotonic() - start, 2)
d = r.json()
msg = ((d.get("choices") or [{}])[0].get("message") or {})
content = msg.get("content") or msg.get("reasoning_content") or ""
print("status:", r.status_code, "lat:", lat)
print("keys in message:", list(msg.keys()))
print("CONTENT LEN:", len(content))
print("=" * 70)
print(content)