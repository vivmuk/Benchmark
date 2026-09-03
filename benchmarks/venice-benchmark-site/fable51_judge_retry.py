#!/usr/bin/env python3
import json, os, re, sqlite3, time
from pathlib import Path
import requests

def load_key():
    key = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if key:
        return key
    db = Path.home() / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    j = json.loads(con.execute(
        "select store_json from auth_profile_store where store_key='primary'").fetchone()[0])
    return (j.get("profiles") or {}).get("venice:cloud", {}).get("key", "")

JUDGE_RUBRIC = (
    "You are a strict senior-systems-engineer evaluator. Grade the CANDIDATE response "
    "to the rate-limiter design task on QUALITY (not length, not coverage alone). "
    "Score each dimension 0-10, then give an overall 0-100.\n\n"
    "DIMENSIONS:\n"
    "- technical_accuracy: are the mechanisms correct and defensible?\n"
    "- actionability: concrete configs, commands, thresholds a team could act on now\n"
    "- depth_of_tradeoffs: does it weigh real alternatives (GCRA vs token bucket, "
    "  Redis vs etcd, fail-open vs fail-closed) with costs?\n"
    "- precision: specific technologies, numbers, failure modes — no hand-waving\n"
    "- concision: is every sentence load-bearing, or is there padding/repetition?\n"
    "- overall: would a senior engineer approve this as a design doc?\n\n"
    "Return ONLY JSON:\n"
    '{"technical_accuracy": int, "actionability": int, "depth_of_tradeoffs": int, '
    '"precision": int, "concision": int, "overall": int, '
    '"key_strength": string, "key_weakness": string}'
)

key = load_key()
src = json.loads(Path("data/value_per_token_open_fable51.json").read_text(encoding="utf-8"))
content = src["content"]
prompt = JUDGE_RUBRIC + "\n\nCANDIDATE RESPONSE:\n\"\"\"\n" + content[:14000] + "\n\"\"\""
payload = {"model": "openai-gpt-56-luna",
           "messages": [{"role": "user", "content": prompt}],
           "max_tokens": 4000}
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

for attempt in range(1, 5):
    r = requests.post("https://api.venice.ai/api/v1/chat/completions",
                      headers=headers, json=payload, timeout=300)
    d = r.json()
    msg = ((d.get("choices") or [{}])[0].get("message") or {})
    raw = (msg.get("content") or msg.get("reasoning_content") or "").strip()
    finish = (d.get("choices") or [{}])[0].get("finish_reason")
    u = d.get("usage") or {}
    print(f"attempt {attempt}: finish={finish} content_len={len(raw)} "
          f"reasoning_len={len(msg.get('reasoning_content') or '')} "
          f"comp_tok={u.get('completion_tokens')}", flush=True)
    if raw:
        raw2 = raw.strip("`")
        if raw2.startswith("json"):
            raw2 = raw2[4:]
        raw2 = raw2.strip()
        try:
            obj = json.loads(re.search(r"\{[\s\S]*\}", raw2).group(0))
            print("PARSED " + json.dumps(obj, indent=2))
            Path("data/fable51_judge_retry.json").write_text(
                json.dumps(obj, indent=2) + "\n", encoding="utf-8")
            break
        except Exception as e:
            print("parse fail:", e, "raw head:", raw[:200])
    time.sleep(2)