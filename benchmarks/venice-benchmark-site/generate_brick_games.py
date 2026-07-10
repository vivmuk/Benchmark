#!/usr/bin/env python3
"""Generate and record the standalone Arcade game for every canonical model.

Dry-run validates roster/prompt wiring only. --run-real spends API credits. The
manifest is intentionally a record of model output, never a hand-edited game.
"""
from __future__ import annotations
import argparse, json, os, re, time
from datetime import datetime, timezone
from pathlib import Path
import requests
from model_registry import MODELS

API_URL = "https://api.venice.ai/api/v1/chat/completions"
PROMPT_PATH = Path("prompts/brick_breaker_maximum.md")
OUTPUT_DIR = Path("arcade")
MANIFEST_PATH = Path("data/brick_arcade.json")
TEMPERATURE, SAFETY_MAX_TOKENS, TIMEOUT = 0.5, 32768, 600

def prompt() -> str:
    raw = PROMPT_PATH.read_text(encoding="utf-8")
    match = re.search(r"```text\n(.*?)```", raw, re.S)
    if not match: raise ValueError("No model-facing ```text block in Arcade prompt")
    return match.group(1).strip()

def extract_html(text: str) -> str | None:
    start = re.search(r"<!doctype html\b|<html\b", text, re.I)
    if not start: return None
    end = text.lower().rfind("</html>")
    return text[start.start():end + 7] if end >= start.start() else None

def validate_html(html: str | None) -> dict:
    if not html: return {"passed": False, "checks": ["complete_html_document"], "error": "No complete HTML document extracted"}
    checks = {"complete_html_document": "</html>" in html.lower(), "canvas": "<canvas" in html.lower(), "game_loop": "requestanimationframe" in html.lower(), "no_remote_urls": not bool(re.search(r"https?://|//[^/]+", html))}
    return {"passed": all(checks.values()), "checks": checks, "error": None}

def call(model_id: str, text: str, max_tokens: int) -> tuple[dict, str]:
    key=os.environ.get("VENICE_INFERENCE_KEY")
    if not key: raise RuntimeError("Set VENICE_INFERENCE_KEY for --run-real")
    at=time.time(); response=requests.post(API_URL,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":model_id,"messages":[{"role":"user","content":text}],"max_tokens":max_tokens,"temperature":TEMPERATURE},timeout=TIMEOUT)
    if response.status_code != 200: return ({"status":"error","latency":round(time.time()-at,2),"error":response.text[:400]}, "")
    data=response.json(); out=((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""; usage=data.get("usage") or {}
    return ({"status":"ok","latency":round(time.time()-at,2),"prompt_tokens":usage.get("prompt_tokens",0),"completion_tokens":usage.get("completion_tokens",0),"total_tokens":usage.get("total_tokens",0)},out)

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--run-real",action="store_true"); parser.add_argument("--model"); args=parser.parse_args()
    selected=[m for m in MODELS if not args.model or args.model in (m["id"],m["display"])]
    if not selected: raise SystemExit("Unknown model")
    text=prompt(); OUTPUT_DIR.mkdir(exist_ok=True); results=[]
    for model in selected:
        entry={"model_id":model["id"],"display":model["display"],"max_tokens":SAFETY_MAX_TOKENS,"temperature":TEMPERATURE,"html":None,"raw_chars":0,"browser_validation":{"passed":False,"checks":{},"error":"Not generated"}}
        if not args.run_real:
            entry.update(status="not_run",note="Dry run: no model invocation.")
        else:
            status,raw=call(model["id"],text,SAFETY_MAX_TOKENS); entry.update(status); entry["raw_chars"]=len(raw)
            html=extract_html(raw); validation=validate_html(html); entry["browser_validation"]=validation
            if html:
                path=OUTPUT_DIR/f'{model["id"]}-brick.html'; path.write_text(html,encoding="utf-8"); entry["html"]=str(path)
            else: (OUTPUT_DIR/f'{model["id"]}-brick.raw.txt').write_text(raw,encoding="utf-8")
        results.append(entry); print(model["display"],entry["status"])
        if args.run_real: time.sleep(1)
    payload={"generated_at":datetime.now(timezone.utc).isoformat(),"dry_run":not args.run_real,"prompt_file":str(PROMPT_PATH),"max_tokens":SAFETY_MAX_TOKENS,"models":MODELS,"results":results,"protocol":"Canonical roster; per-model maximum practical allowance up to the recorded safety ceiling. Browser validation must be completed before publishing a game as playable."}
    MANIFEST_PATH.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
if __name__ == "__main__": main()
