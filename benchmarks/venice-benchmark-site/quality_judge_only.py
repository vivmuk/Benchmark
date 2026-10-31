#!/usr/bin/env python3
"""Judge-only pass: grade the 3 saved rate-limiter responses for QUALITY per dollar.
Fixes the temperature bug (openai-gpt-56-luna only accepts default temp=1).
"""
import json, os, re, sqlite3, time
from pathlib import Path

import requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
JUDGE_MODEL = "openai-gpt-56-luna"

MODELS = ["claude-opus-4-8-fast", "claude-fable-5", "claude-fable-5-1"]
PRICING = {
    "claude-opus-4-8-fast": {"input": 12.0, "output": 60.0},
    "claude-fable-5":       {"input": 12.0, "output": 60.0},
    "claude-fable-5-1":     {"input": 10.0, "output": 50.0},
    "openai-gpt-56-luna":   {"input": 1.25, "output": 7.5},
}

# where raw responses live
SOURCES = {
    "claude-opus-4-8-fast": "data/open_claude-opus-4-8-fast.json",
    "claude-fable-5":       "data/open_claude-fable-5.json",
    "claude-fable-5-1":     "data/value_per_token_open_fable51.json",
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


def judge(key, candidate):
    prompt = JUDGE_RUBRIC + "\n\nCANDIDATE RESPONSE:\n\"\"\"\n" + candidate[:14000] + "\n\"\"\""
    payload = {
        "model": JUDGE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        # NO temperature field -> default (1) which this model requires
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    r = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    d = r.json()
    if r.status_code != 200:
        return {"judge_status": "error", "judge_error": d.get("error", r.text[:300]), "score": None}
    msg = ((d.get("choices") or [{}])[0].get("message") or {})
    usage = d.get("usage") or {}
    raw = (msg.get("content") or msg.get("reasoning_content") or "").strip()
    raw = raw.strip("`")
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()
    try:
        obj = json.loads(re.search(r"\{[\s\S]*\}", raw).group(0))
    except Exception:
        return {"judge_status": "parse_error", "judge_raw": raw[:400], "score": None}
    cost = (int(usage.get("prompt_tokens") or 0) / 1e6) * PRICING[JUDGE_MODEL]["input"] + \
           (int(usage.get("completion_tokens") or 0) / 1e6) * PRICING[JUDGE_MODEL]["output"]
    obj["judge_cost_usd"] = round(cost, 6)
    obj["judge_tokens"] = int(usage.get("total_tokens") or 0)
    obj["judge_status"] = "ok"
    return obj


def main():
    key = load_key()
    final = []
    for model in MODELS:
        src = json.loads(Path(SOURCES[model]).read_text(encoding="utf-8"))
        content = src["content"]
        pr = PRICING[model]
        cost = (src["prompt_tokens"] / 1e6) * pr["input"] + \
               (src["completion_tokens"] / 1e6) * pr["output"]
        print(f"[judge] {model} (cand {len(content)} chars)", flush=True)
        j = judge(key, content)
        q = j.get("overall")
        entry = {
            "model": model,
            "completion_tokens": src["completion_tokens"],
            "total_tokens": src["total_tokens"],
            "words": len(content.split()),
            "cost_usd": round(cost, 6),
            "judge": j,
            "quality_score": q,
            "quality_per_dollar": round(q / cost, 1) if (q and cost) else None,
            "quality_per_1k_tokens": round(q / (src["total_tokens"] / 1000), 1) if q else None,
        }
        final.append(entry)
        keep = dict(entry)
        keep["judge"] = {k: v for k, v in j.items()}
        print(json.dumps(keep, indent=2, ensure_ascii=False), flush=True)
        time.sleep(0.4)

    Path("data/quality_judge_tiebreaker.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nwrote data/quality_judge_tiebreaker.json")


if __name__ == "__main__":
    main()