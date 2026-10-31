#!/usr/bin/env python3
"""Head-to-head: claude-fable-5 vs claude-fable-5-1 on 3 fresh capabilities.

A) User understanding   B) Problem solving   C) Tool calling (real function-calling)
"""
from __future__ import annotations

import json, os, sqlite3, sys, time
from pathlib import Path

import requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
MODELS = ["claude-fable-5", "claude-fable-5-1"]
OUT = Path(__file__).resolve().parent / "data" / "fable_head_to_head.json"


def load_key() -> str:
    key = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if key:
        return key
    db = Path.home() / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    j = json.loads(con.execute(
        "select store_json from auth_profile_store where store_key='primary'"
    ).fetchone()[0])
    return (j.get("profiles") or {}).get("venice:cloud", {}).get("key", "")


# ---------------------------------------------------------------------------
# A) USER UNDERSTANDING
# ---------------------------------------------------------------------------
A_PROMPT = (
    "I keep getting told our roadmap keeps slipping, but nobody tells me why until "
    "the weekly sync, and by then it's already two weeks late. I don't want another "
    "dashboard. Actually, maybe I do — I don't know anymore. The team says they're "
    "fine, but tickets keep piling up and I can feel the pressure building. Can you "
    "just fix it for me?\n\n"
    "Do THREE things: (1) identify the real underlying needs, not the surface ask; "
    "(2) ask the clarifying questions you'd need before proposing anything; "
    "(3) then give your working hypothesis and a minimal next step."
)

# ---------------------------------------------------------------------------
# B) PROBLEM SOLVING
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# C) TOOL CALLING (real function calling)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search available flights between two cities on a date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Book a specific flight by id.",
            "parameters": {
                "type": "object",
                "properties": {"flight_id": {"type": "string"}},
                "required": ["flight_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search hotels in a city for a date range with min stars.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "checkin": {"type": "string", "description": "YYYY-MM-DD"},
                    "checkout": {"type": "string", "description": "YYYY-MM-DD"},
                    "min_stars": {"type": "integer"},
                },
                "required": ["city", "checkin", "checkout"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_hotel",
            "description": "Book a specific hotel by id.",
            "parameters": {
                "type": "object",
                "properties": {"hotel_id": {"type": "string"}},
                "required": ["hotel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_flight",
            "description": "Cancel a previously booked flight.",
            "parameters": {
                "type": "object",
                "properties": {"flight_id": {"type": "string"}},
                "required": ["flight_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_itinerary",
            "description": "Email the final itinerary to a recipient.",
            "parameters": {
                "type": "object",
                "properties": {"recipient": {"type": "string"}},
                "required": ["recipient"],
            },
        },
    },
]

C_SYSTEM = (
    "You are a travel booking assistant. Use the provided tools to satisfy the "
    "user's request. Call tools with correct arguments. Do not call tools that are "
    "not needed."
)
C_USER = (
    "Book business travel for Dr. Mehta: fly Boston (BOS) to Chicago (ORD) on "
    "2026-09-14, returning 2026-09-16, stay in a 4-star Chicago hotel those two "
    "nights, and send the itinerary to mehta@hospital.org. Please start now."
)


def call_text(key, model, prompt, max_tokens=2048):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        lat = round(time.monotonic() - start, 2)
        if r.status_code != 200:
            return {"status": "error", "latency": lat, "error": r.text[:400], "raw": ""}
        d = r.json()
        u = d.get("usage") or {}
        msg = ((d.get("choices") or [{}])[0].get("message") or {})
        content = msg.get("content") or msg.get("reasoning_content") or ""
        return {
            "status": "ok", "latency": lat,
            "raw": content if isinstance(content, str) else json.dumps(content),
            "prompt_tokens": int(u.get("prompt_tokens") or 0),
            "completion_tokens": int(u.get("completion_tokens") or 0),
            "total_tokens": int(u.get("total_tokens") or 0),
        }
    except Exception as e:
        return {"status": "error", "latency": round(time.monotonic() - start, 2),
                "error": str(e)[:400], "raw": ""}


def call_tools(key, model):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": C_SYSTEM},
            {"role": "user", "content": C_USER},
        ],
        "tools": TOOLS,
        "tool_choice": "auto",
        "max_tokens": 2048,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        lat = round(time.monotonic() - start, 2)
        if r.status_code != 200:
            return {"status": "error", "latency": lat, "error": r.text[:500], "tool_calls": [], "content": ""}
        d = r.json()
        u = d.get("usage") or {}
        msg = ((d.get("choices") or [{}])[0].get("message") or {})
        tcs = msg.get("tool_calls") or []
        return {
            "status": "ok", "latency": lat,
            "tool_calls": tcs,
            "content": msg.get("content") or "",
            "prompt_tokens": int(u.get("prompt_tokens") or 0),
            "completion_tokens": int(u.get("completion_tokens") or 0),
            "total_tokens": int(u.get("total_tokens") or 0),
        }
    except Exception as e:
        return {"status": "error", "latency": round(time.monotonic() - start, 2),
                "error": str(e)[:500], "tool_calls": [], "content": ""}


def main():
    key = load_key()
    if not key:
        print("no key"); sys.exit(1)
    out = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "models": {}, "tools": TOOLS}
    for model in MODELS:
        print(f"\n{'='*70}\nMODEL: {model}\n{'='*70}", flush=True)
        a = call_text(key, model, A_PROMPT)
        print(f"[A] status={a['status']} lat={a.get('latency')} tok={a.get('total_tokens')}", flush=True)
        b = call_text(key, model, B_PROMPT)
        print(f"[B] status={b['status']} lat={b.get('latency')} tok={b.get('total_tokens')}", flush=True)
        c = call_tools(key, model)
        print(f"[C] status={c['status']} lat={c.get('latency')} n_tool_calls={len(c.get('tool_calls') or [])}", flush=True)
        out["models"][model] = {"A": a, "B": b, "C": c}
        time.sleep(0.5)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()