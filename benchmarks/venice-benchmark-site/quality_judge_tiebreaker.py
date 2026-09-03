#!/usr/bin/env python3
"""LLM-judge quality-per-dollar tiebreaker over the 3 open-ended rate-limiter responses.

Re-fetches Opus 4.8 Fast + Fable 5 (whose raw text was lost in the earlier crash),
loads Fable 5.1 from disk, then judges all three with openai-gpt-56-luna on a
quality rubric (not just topic coverage). Computes quality-per-dollar and
quality-per-token.
"""
from __future__ import annotations

import json, os, sqlite3, time
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


def load_key():
    key = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if key:
        return key
    db = Path.home() / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    j = json.loads(con.execute(
        "select store_json from auth_profile_store where store_key='primary'").fetchone()[0])
    return (j.get("profiles") or {}).get("venice:cloud", {}).get("key", "")


def call(model, messages, max_tokens, timeout=900):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    start = time.monotonic()
    r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    lat = round(time.monotonic() - start, 2)
    d = r.json()
    msg = ((d.get("choices") or [{}])[0].get("message") or {})
    usage = d.get("usage") or {}
    content = msg.get("content") or ""
    return {
        "status": "ok" if r.status_code == 200 else "error",
        "latency": lat, "content": content,
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
        "error": r.text[:300] if r.status_code != 200 else None,
    }


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


def judge(candidate):
    prompt = (
        JUDGE_RUBRIC + "\n\nCANDIDATE RESPONSE:\n\"\"\"\n"
        + candidate[:14000] + "\n\"\"\""
    )
    r = call(JUDGE_MODEL, [{"role": "user", "content": prompt}], 800)
    if r["status"] != "ok":
        return {"judge_status": "error", "judge_error": r.get("error"), "score": None}
    raw = r["content"].strip()
    raw = raw.strip("`")
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()
    try:
        obj = json.loads(re.search(r"\{[\s\S]*\}", raw).group(0))
    except Exception:
        return {"judge_status": "parse_error", "judge_raw": raw[:400], "score": None}
    cost = (r["prompt_tokens"] / 1e6) * PRICING[JUDGE_MODEL]["input"] + \
           (r["completion_tokens"] / 1e6) * PRICING[JUDGE_MODEL]["output"]
    obj["judge_cost_usd"] = round(cost, 6)
    obj["judge_tokens"] = r["total_tokens"]
    obj["judge_status"] = "ok"
    return obj


def main():
    # 1) re-fetch Opus + Fable 5 (Fable 5.1 already saved)
    responses = {}
    saved51 = json.loads(Path("data/value_per_token_open_fable51.json").read_text(encoding="utf-8"))
    responses["claude-fable-5-1"] = {
        "content": saved51["content"], "prompt_tokens": saved51["prompt_tokens"],
        "completion_tokens": saved51["completion_tokens"], "total_tokens": saved51["total_tokens"],
        "latency": saved51["latency"],
    }
    for model in ["claude-opus-4-8-fast", "claude-fable-5"]:
        print(f"[fetch] {model}", flush=True)
        r = call(model, [{"role": "user", "content": TASK}], 128000)
        responses[model] = {
            "content": r["content"], "prompt_tokens": r["prompt_tokens"],
            "completion_tokens": r["completion_tokens"], "total_tokens": r["total_tokens"],
            "latency": r["latency"], "status": r["status"],
        }
        Path(f"data/open_{model}.json").write_text(
            json.dumps(responses[model], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(0.5)

    # 2) judge all three
    final = []
    for model in MODELS:
        info = responses[model]
        print(f"[judge] {model} (cand {len(info['content'])} chars)", flush=True)
        j = judge(info["content"])
        pr = PRICING[model]
        cost = (info["prompt_tokens"] / 1e6) * pr["input"] + \
               (info["completion_tokens"] / 1e6) * pr["output"]
        qscore = j.get("overall")
        entry = {
            "model": model,
            "completion_tokens": info["completion_tokens"],
            "total_tokens": info["total_tokens"],
            "words": len(info["content"].split()),
            "cost_usd": round(cost, 6),
            "judge": j,
            "quality_score": qscore,
            "quality_per_dollar": round(qscore / cost, 1) if (qscore and cost) else None,
            "quality_per_1k_tokens": round(qscore / (info["total_tokens"] / 1000), 1) if qscore else None,
        }
        final.append(entry)
        print(json.dumps({k: v for k, v in entry.items() if k != "judge" or (v or {})}, indent=2, ensure_ascii=False), flush=True)
        time.sleep(0.5)

    Path("data/quality_judge_tiebreaker.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nwrote data/quality_judge_tiebreaker.json")


key = load_key()
if __name__ == "__main__":
    main()