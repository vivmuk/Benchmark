#!/usr/bin/env python3
"""Export BenchmarkViv results as CSV + a summary JSON for badges.

  data/benchmarkviv-results.csv  — one row per (model, benchmark) result
  data/summary.json              — {top_model, top_viv, n_models, generated_at}
                                   used by shields.io dynamic badges
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CSV_OUT = DATA / "benchmarkviv-results.csv"
SUM_OUT = DATA / "summary.json"

WEIGHTS = {
    "intent_understanding": 0.20,
    "one_shot_ui": 0.15,
    "startup_in_a_weekend": 0.25,
    "value_density": 0.20,
    "reverse_prompt_vision": 0.20,
}


def main():
    d = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    disp = {m["id"]: m["display"] for m in d.get("models", [])}

    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model_id", "display", "benchmark_id", "status", "score",
                    "latency_s", "prompt_tokens", "completion_tokens",
                    "total_tokens", "estimated_cost_usd"])
        for r in d["results"]:
            w.writerow([r["model_id"], disp.get(r["model_id"], r["model_id"]),
                        r["benchmark_id"], r.get("status", ""),
                        r.get("score", ""), round(r.get("latency") or 0, 3),
                        r.get("prompt_tokens", ""), r.get("completion_tokens", ""),
                        r.get("total_tokens", ""),
                        round(r.get("estimated_cost_usd") or 0, 6)])

    # VivIndex per model (same weighting as the leaderboard)
    rows = []
    for m in d.get("models", []):
        mid = m["id"]
        ws = wsum = 0.0
        for r in d["results"]:
            if r["model_id"] != mid or r.get("score") is None:
                continue
            wgt = WEIGHTS.get(r["benchmark_id"])
            if wgt is not None:
                ws += wgt
                wsum += r["score"] * wgt
        if ws > 0:
            rows.append((mid, wsum / ws))
    rows.sort(key=lambda x: -x[1])
    top_id, top_viv = rows[0] if rows else (None, 0)

    summary = {
        "top_model": disp.get(top_id, top_id) if top_id else None,
        "top_model_id": top_id,
        "top_viv": round(top_viv, 1),
        "n_models": len(rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    SUM_OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"CSV rows: {len(d['results'])} -> {CSV_OUT.name}")
    print(f"summary: {summary}")


if __name__ == "__main__":
    main()
