#!/usr/bin/env python3
"""World Models in Medical Affairs — 3-model HTML essay shootout + Grok 4.6 judge.

Each model writes its own self-contained HTML article from the same brief prompt.
No token cap (max_tokens=128000). Captures tokens/cost/latency/reasoning tell,
saves each essay immediately, then judges all three with grok-4-6.
"""
from __future__ import annotations

import json, os, re, sqlite3, time
from pathlib import Path

import requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
ROOT = Path(__file__).resolve().parent

ESSAY_MODELS = ["claude-opus-4-8-fast", "claude-fable-5", "claude-fable-5-1"]
JUDGE_MODEL = "grok-4-6"

# USD per 1M tokens (live /models pricing; grok-4-6 from fallback)
PRICING = {
    "claude-opus-4-8-fast": {"input": 12.0, "output": 60.0},
    "claude-fable-5":       {"input": 12.0, "output": 60.0},
    "claude-fable-5-1":     {"input": 10.0, "output": 50.0},
    "grok-4-6":             {"input": 2.27, "output": 6.80},
}
DISPLAY = {
    "claude-opus-4-8-fast": "Opus 4.8 Fast",
    "claude-fable-5":       "Fable 5",
    "claude-fable-5-1":     "Fable 5.1",
}

PROMPT = (
    "Write a beautiful, self-contained HTML article titled \"World Models in "
    "Medical Affairs.\" Cover the question: what are the applications of world "
    "models in medical affairs, and how will medical affairs be transformed by "
    "world models? Inline CSS only — no external stylesheets, fonts, or images. "
    "Make the design genuinely polished and the writing sharp. No length limit."
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


def chat(model, messages, max_tokens, timeout=1200):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    except Exception as e:
        return {"status": "error", "latency": round(time.monotonic() - start, 2),
                "error": str(e)[:400], "content": ""}
    lat = round(time.monotonic() - start, 2)
    d = r.json()
    msg = ((d.get("choices") or [{}])[0].get("message") or {})
    usage = d.get("usage") or {}
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    return {
        "status": "ok" if r.status_code == 200 else "error",
        "latency": lat,
        "content": content,
        "reasoning_len": len(reasoning),
        "finish_reason": ((d.get("choices") or [{}])[0].get("finish_reason")),
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
        "error": (d.get("error") or r.text[:300]) if r.status_code != 200 else None,
    }


def main():
    essays = {}
    for model in ESSAY_MODELS:
        print(f"[essay] {model}", flush=True)
        r = chat(model, [{"role": "user", "content": PROMPT}], 128000)
        pr = PRICING[model]
        cost = (r["prompt_tokens"] / 1e6) * pr["input"] + \
               (r["completion_tokens"] / 1e6) * pr["output"]
        rec = {
            "model": model, "display": DISPLAY[model],
            "status": r["status"], "latency": r["latency"],
            "finish_reason": r["finish_reason"],
            "prompt_tokens": r["prompt_tokens"],
            "completion_tokens": r["completion_tokens"],
            "total_tokens": r["total_tokens"],
            "cost_usd": round(cost, 6),
            "reasoning_len": r["reasoning_len"],
            "content_len": len(r["content"]),
            "content": r["content"],
            "error": r.get("error"),
        }
        essays[model] = rec
        # save immediately so a later timeout never loses prior work
        (ROOT / "data" / f"essay_{model}.json").write_text(
            json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  -> comp_tok={r['completion_tokens']} total={r['total_tokens']} "
              f"cost=${cost:.4f} lat={r['latency']}s finish={r['finish_reason']} "
              f"reasoning={r['reasoning_len']}", flush=True)

    # judge
    print(f"[judge] {JUDGE_MODEL}", flush=True)
    judge_prompt = (
        "You are a world-class judge of both prose and web design. Below are three "
        "self-contained HTML articles on \"World Models in Medical Affairs,\" each "
        "produced by a different AI model from the same prompt. Evaluate EACH on two "
        "axes: (A) essay substance — insight, sharpness of writing, accuracy, and "
        "how well it answers 'applications + transformation'; and (B) design/UI — "
        "polish, layout, readability, and craft of the HTML/CSS.\n\n"
        "Return ONLY JSON:\n"
        "{\n"
        "  \"rankings\": [\n"
        "    {\"model\": \"claude-opus-4-8-fast\", \"substance\": 0, \"design\": 0, \"note\": \"...\"},\n"
        "    {\"model\": \"claude-fable-5\", \"substance\": 0, \"design\": 0, \"note\": \"...\"},\n"
        "    {\"model\": \"claude-fable-5-1\", \"substance\": 0, \"design\": 0, \"note\": \"...\"}\n"
        "  ],\n"
        "  \"overall_winner\": \"<model>\",\n"
        "  \"runner_up\": \"<model>\",\n"
        "  \"summary\": \"one paragraph on who wins and why\"\n"
        "}\n"
        "Score substance and design each 0-100. Be fair, specific, and evidence-backed.\n\n"
    )
    for i, (m, rec) in enumerate(essays.items(), 1):
        judge_prompt += f"\n===== ENTRY {i}: {DISPLAY[m]} ({m}) =====\n"
        judge_prompt += rec["content"] + "\n"
    jr = chat(JUDGE_MODEL, [{"role": "user", "content": judge_prompt}], 128000)
    judge_cost = (jr["prompt_tokens"] / 1e6) * PRICING[JUDGE_MODEL]["input"] + \
                 (jr["completion_tokens"] / 1e6) * PRICING[JUDGE_MODEL]["output"]
    judge_raw = jr["content"].strip().strip("`")
    if judge_raw.startswith("json"):
        judge_raw = judge_raw[4:]
    judge_raw = judge_raw.strip()
    try:
        verdict = json.loads(re.search(r"\{[\s\S]*\}", judge_raw).group(0))
    except Exception:
        verdict = {"parse_error": True, "raw": judge_raw[:800]}
    judge_rec = {
        "model": JUDGE_MODEL, "status": jr["status"],
        "prompt_tokens": jr["prompt_tokens"], "completion_tokens": jr["completion_tokens"],
        "total_tokens": jr["total_tokens"], "cost_usd": round(judge_cost, 6),
        "latency": jr["latency"], "verdict": verdict, "raw": judge_raw,
    }
    (ROOT / "data" / "essay_judge.json").write_text(
        json.dumps(judge_rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  -> judge comp_tok={jr['completion_tokens']} cost=${judge_cost:.4f} "
          f"verdict={json.dumps(verdict)[:200]}", flush=True)
    print("DONE", flush=True)


key = load_key()
if __name__ == "__main__":
    main()