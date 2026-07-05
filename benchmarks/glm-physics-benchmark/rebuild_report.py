#!/usr/bin/env python3
"""Rebuild report from existing artifacts."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from benchmark_runner import build_report, TASKS, score_task

OUT_DIR = os.path.dirname(__file__)
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
        "total_tokens": 0,
        "scores": scores,
        "total_score": total,
        "path": path,
    })
build_report(results, {})
print("Report rebuilt.")
