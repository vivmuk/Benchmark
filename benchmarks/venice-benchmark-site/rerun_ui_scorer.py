#!/usr/bin/env python3
"""Re-score all existing one_shot_ui rows using the improved scorer."""
import json, re, sys

# Copy of the new scorer from run_benchmarks.py
def score_one_shot_ui(text: str) -> int:
    if not text or not text.strip():
        return 0
    lower = text.lower()
    has_doctype = "<!doctype" in lower
    has_html_tag = "<html" in lower
    has_head = "<head" in lower
    has_body = "<body" in lower
    has_closing_html = "</html>" in lower
    structure_score = 0
    if has_doctype and has_html_tag and has_head and has_body and has_closing_html:
        structure_score = 35
    elif has_doctype and has_html_tag and has_body and has_closing_html:
        structure_score = 25
    elif has_html_tag and has_body:
        structure_score = 15
    elif has_html_tag or has_doctype:
        structure_score = 5
    if not has_html_tag:
        return 0
    css_rules_found = 0
    if "<style" in lower:
        style_start = lower.find("<style")
        style_section = lower[style_start:lower.find("</style>", style_start)] if "</style>" in lower else lower[style_start:]
        css_rules_found = style_section.count("{") + style_section.count("@")
        if css_rules_found >= 3:
            css_score = 15
        elif css_rules_found >= 1:
            css_score = 8
        else:
            css_score = 0
    else:
        css_score = 0
    js_found = "<script" in lower and "</script>" in lower
    has_event = any(e in lower for e in ("onclick", "onchange", "oninput", "onsubmit", "addEventListener"))
    if js_found and has_event:
        js_score = 15
    elif js_found:
        js_score = 8
    else:
        js_score = 0
    has_button = "button" in lower
    has_form_input = "input" in lower or "<form" in lower
    has_card = "card" in lower or "container" in lower
    has_focus_display = ("focus" in lower or "score" in lower) or ("sparkline" in lower or "chart" in lower)
    ui_score = sum([5 if has_button else 0, 5 if has_form_input else 0, 5 if has_card else 0, 5 if has_focus_display else 0])
    has_viewport = "viewport" in lower or "meta name" in lower
    has_media_query = "@media" in lower
    has_flex = "flex" in lower or "grid" in lower
    responsive_score = 0
    if has_viewport and has_media_query:
        responsive_score = 5
    elif has_viewport and has_flex:
        responsive_score = 3
    elif has_viewport:
        responsive_score = 2
    length_penalty = 0
    if len(text) > 3000 and (not has_head or not has_body):
        length_penalty = -10
    words = text.split()
    html_ratio = sum(1 for w in words if w.startswith("<")) / max(len(words), 1)
    if html_ratio < 0.15 and len(words) > 50:
        length_penalty = min(length_penalty, -10)
    total = structure_score + css_score + js_score + ui_score + responsive_score + length_penalty
    return max(0, min(100, int(total)))


d = json.load(open("data/results.json"))
changes = 0
for r in d["results"]:
    if r.get("benchmark_id") == "one_shot_ui" and r.get("status") == "ok":
        raw = r.get("raw_response") or ""
        old_score = r.get("score") or r.get("score_auto") or 0
        new_score = score_one_shot_ui(raw)
        if old_score != new_score:
            r["score"] = new_score
            r["score_auto"] = new_score
            print(f"  {r['model_id']:40s} {old_score:>3d} -> {new_score:>3d}")
            changes += 1

if changes:
    d["generated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    json.dump(d, open("data/results.json", "w"), indent=2, ensure_ascii=False)
    print(f"\nUpdated {changes} one_shot_ui scores. Written to data/results.json")
else:
    print("No changes needed")