#!/usr/bin/env python3
"""Rerun truncated tasks and rebuild report."""
import re, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from benchmark_runner import call_model, extract_html, save, build_report, TASKS, score_task

OUT_DIR = os.path.dirname(__file__)

# Rerun base physics demo with more tokens
physics_prompt = [t for t in TASKS if t["id"] == "physics-demo"][0]["prompt"]
print("=== Rerunning base physics demo ===")
r = call_model(physics_prompt, max_tokens=12000)
print(r["status"], r["response_time"], r.get("total_tokens"))
if r["status"] == "success":
    html = extract_html(r["response"])
    save("glm-physics-demo.html", html)
    print("Saved base physics demo, length:", len(html))

# Rerun fix task and capture explanation separately
fix_prompt = [t for t in TASKS if t["id"] == "physics-fix"][0]["prompt"]
print("\n=== Rerunning bug fix task ===")
r = call_model(fix_prompt, max_tokens=12000)
print(r["status"], r["response_time"], r.get("total_tokens"))
if r["status"] == "success":
    text = r["response"]
    # Extract html block
    m = re.search(r"```html\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        html = m.group(1).strip()
    else:
        m = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        html = m.group(1).strip() if m else text
    save("glm-physics-fixed.html", html)
    explanation = text.split("```", 1)[-1].strip()
    # Remove trailing ```
    explanation = re.sub(r"```\s*$", "", explanation).strip()
    save("glm-fix-explanation.md", explanation)
    print("Saved fix and explanation, lengths:", len(html), len(explanation))

# Rebuild report
results = []
for task in TASKS:
    path = os.path.join(OUT_DIR, task["file"])
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    scores, total = score_task(task["id"], content)
    results.append({
        "id": task["id"],
        "name": task["name"],
        "file": task["file"],
        "latency": "—",
        "prompt_tokens": "—",
        "completion_tokens": "—",
        "total_tokens": "—",
        "scores": scores,
        "total_score": total,
        "path": path,
    })
build_report(results, {})
print("Report rebuilt.")
