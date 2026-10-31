#!/usr/bin/env python3
"""Re-judge the One-Shot UI (HTML) track from stored raw responses.

Fixes the old heuristic that wrongly rewarded literal words like "button",
"card", "focus" appearing ANYWHERE in the code (even in comments/JS output),
counted "?" characters, and mis-penalized long output. The corrected rubric
checks what the prompt actually asks for and whether the HTML is real, valid
runable markup.

Mode A (deterministic, always): parse-structure rubric, 0-100.
Mode B (LLM-judge): add a fixed rubric judge score from a Venice model to the
deterministic one (50/50) for a richer opinion, when --judge <model> is given.

Writes updated `one_shot_ui` scores back into data/results.json (idempotent).
"""
from __future__ import annotations

import argparse, json, re, sys, base64
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "results.json"
API = "https://api.venice.ai/api/v1/chat/completions"

RUBRIC = (
    "You are the BenchmarkViv UI judge. Score this model's answer to: 'Generate a "
    "single self-contained HTML file for a dark-mode dashboard card showing a user's "
    "daily focus score, weekly trend sparkline, and a Start Focus button. HTML/CSS/JS "
    "only, no external images.'\n"
    "Score the ACTUAL RENDERED UI from the HTML, on a 0-100 scale where you deduct for:\n"
    "- missing or broken <html>/<body>/<style>/<script> structure\n"
    "- missing the focus score, sparkline, or Start Focus button\n"
    "- not dark mode\n"
    "- non-runnable/broken/markdown-wrapped HTML\n"
    "- unresponsive layout (no viewport/media query/flex)\n"
    "Reply with ONLY a JSON object: {\"score\":0..100,\"notes\":\"one sentence\"}"
)

JUDGE_MODEL_DEFAULT = "kimi-k3-fast-api"

# Correct one-shot UI prompt spec terms (not just word soup)
REQ_DARK = ("background", "dark", "#111", "#1a1a2e", "color-scheme")
REQ_FOCUS = ("focus", "score", "daily")
REQ_SPARK = ("sparkline", "svg", "canvas", "chart", "polyline")
REQ_BUTTON = "<button"


def extract_html(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"<(?:!doctype|html)[\s>].*?</html>", text, re.S | re.I)
    if m:
        return m.group(0)
    m = re.search(r"<body[\s>].*?</body>", text, re.S | re.I)
    if m:
        return m.group(0)
    return text[:14000]


def _css_rules(html: str) -> int:
    m = re.search(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)
    if not m:
        return 0
    return len(re.findall(r"\{[^}]{1,200}\}", m.group(1)))


def det_judge(html: str) -> dict:
    """Deterministic score 0-100 from structure parsing."""
    if not html or not html.strip():
        return {"score": 0, "partial": True, "broken": True}

    low = html.lower(); score = 0.0

    # 1) Structural integrity (25)
    if "<!doctype" in low and "<html" in low and "<head" in low and "<body" in low and "</html>" in low:
        score += 25
    elif "<html" in low and "<body" in low:
        score += 15
    elif "<html" in low or "<!doctype" in low:
        score += 8

    # 2) Spec match — each present feature (30 = 8+8+7+7)
    if any(x in low for x in ("background", "dark-mode", "dark")):
        score += 8
    if any(x in low for x in ("focus", "score")):
        score += 8
    if "sparkline" in low or "svg" in low or "canvas" in low:
        score += 7
    if "<button" in low and "start focus" in low:
        score += 7

    # 3) Real CSS rules (15) — not just a <style> tag
    rules = _css_rules(html)
    score += min(15, rules * 4)

    # 4) Interactivity/JS (10)
    if re.search(r"<script[^>]*>.*?</script>", low, re.S) and (
        any(x in low for x in ("onclick", "addeventlistener", "onchange", "onsubmit", "oninput"))):
        score += 10
    elif "<script" in low:
        score += 4

    # 5) Responsive (10)
    if "viewport" in low and ("@media" in low or "flex" in low or "grid" in low):
        score += 10
    elif "viewport" in low:
        score += 6

    # 6) Runnable / not markdown-wrapped (10)
    if "```" in low and "<html" not in low:
        pass  # markdown-wrapped but has html inside -> we already grabbed it
    bal = low.count("</html>") >= 1 and low.count("<html") >= 1
    if bal:
        score += 10

    return {"score": round(score), "partial": False}


def load_key() -> str:
    for name in ("VENICE_INFERENCE_KEY", "VENICE_API_KEY"):
        v = __import__("os").environ.get(name)
        if v:
            return v
    raise RuntimeError("No Venice key in env")


def llm_judge(key: str, judge_model: str, html: str) -> int | None:
    payload = {"model": judge_model, "messages": [
        {"role": "system", "content": RUBRIC},
        {"role": "user", "content": f"Here is the HTML the model generated:\n\n{html[:9000]}"},
    ], "max_tokens": 400,
        "venice_parameters": {"disable_thinking": True, "strip_thinking_response": True}}
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {load_key()}", "Content-Type": "application/json"})
    raw = json.load(urllib.request.urlopen(req, timeout=180))["choices"][0]["message"]["content"]
    lo, hi = raw.find("{"), raw.rfind("}")
    d = json.loads(raw[lo:hi + 1]) if lo >= 0 and hi > lo else {}
    return int(d["score"]) if d.get("score") is not None else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="append")
    ap.add_argument("--judge", metavar="JUDGE_MODEL", default=None, help="enable LLM merge (50/50)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    targets = args.model or [m["id"] for m in data["models"]]
    changed = 0
    for r in data["results"]:
        if r.get("benchmark_id") != "one_shot_ui":
            continue
        if r.get("model_id") not in targets:
            continue
        html = extract_html(r.get("raw_response") or "")
        det = det_judge(html)["score"]
        final = det
        mode = "deterministic"
        if args.judge and not args.dry_run and not det_judge(html)["partial"]:
            try:
                llm = llm_judge(load_key(), args.judge, html)
                if llm is not None:
                    final = round((det * 0.5) + (llm * 0.5))
                    mode = "judge+det"
            except Exception:
                pass
        old = r.get("score")
        if old != final:
            changed += 1
        r["score"] = final
        r.setdefault("metrics", {})["ui_rubric"] = {
            "mode": mode, "deterministic": det,
            "buckets_score": final,
            "judged_at": datetime.now(timezone.utc).isoformat() if mode.startswith("judge") else None,
        }
        print(f"  {r['model_id'][:28]:28} old={old}  new={final}  ({mode})")

    if args.write and not args.dry_run:
        data["generated_at"] = datetime.now(timezone.utc).isoformat()
        DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nWrote results.json. changed={changed}")
    else:
        print(f"\n(dry run) changed={changed} — pass --write to persist")
    return 0


if __name__ == "__main__":
    sys.exit(main())