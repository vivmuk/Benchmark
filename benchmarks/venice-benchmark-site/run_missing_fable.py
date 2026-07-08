#!/usr/bin/env python3
"""Run only missing Fable 5 tracks and merge into data/results.json."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import run_benchmarks as rb

MODEL_ID = "claude-fable-5"
RESULTS_PATH = Path("data") / "results.json"


def main() -> None:
    api_key = os.environ.get(rb.API_KEY_ENV) or os.environ.get("VENICE_API_KEY")
    if not api_key:
        raise SystemExit(f"ERROR: set {rb.API_KEY_ENV} or VENICE_API_KEY")
    os.environ[rb.API_KEY_ENV] = api_key

    model = next(m for m in rb.MODELS if m["id"] == MODEL_ID)
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    existing = [r for r in data["results"] if r.get("model_id") == MODEL_ID]
    have = {r["benchmark_id"] for r in existing}
    missing = [b for b in rb.BENCHMARKS if b["id"] not in have]
    print("have:", sorted(have))
    print("missing:", [b["id"] for b in missing])
    if not missing:
        print("Nothing to run.")
        return

    pricing = rb.fetch_pricing(api_key)
    new_rows = []
    for i, bench in enumerate(missing, 1):
        print(
            f"[{i}/{len(missing)}] {model['display']} -> {bench['name']} ...",
            end=" ",
            flush=True,
        )
        call = rb.call_venice(api_key, model["id"], bench["prompt"])
        if call["status"] == "ok":
            score = rb.SCORERS[bench["id"]](call["raw_response"])
            cost = rb.estimate_cost(
                model["id"], call["prompt_tokens"], call["completion_tokens"], pricing
            )
            print(
                f"ok score={score} latency={call['latency']}s "
                f"tokens={call['total_tokens']} cost=${cost:.6f}"
            )
        else:
            score, cost = 0, 0.0
            print(f"ERROR {str(call.get('error', ''))[:160]}")
        new_rows.append(
            {
                "model_id": model["id"],
                "benchmark_id": bench["id"],
                "status": call["status"],
                "score": score,
                "latency": call["latency"],
                "prompt_tokens": call["prompt_tokens"],
                "completion_tokens": call["completion_tokens"],
                "total_tokens": call["total_tokens"],
                "estimated_cost_usd": cost,
                "raw_response": call["raw_response"],
                "error": call.get("error"),
            }
        )
        if i < len(missing):
            time.sleep(rb.RATE_LIMIT_SLEEP_SECONDS)

    others = [r for r in data["results"] if r.get("model_id") != MODEL_ID]
    fable_rows = existing + new_rows
    order = {b["id"]: i for i, b in enumerate(rb.BENCHMARKS)}
    fable_rows.sort(key=lambda r: order.get(r["benchmark_id"], 99))
    data["results"] = others + fable_rows
    data["models"] = rb.MODELS
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["dry_run"] = False
    data["total_estimated_cost_usd"] = round(
        sum(float(r.get("estimated_cost_usd") or 0) for r in data["results"]), 6
    )
    RESULTS_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {RESULTS_PATH}")
    for r in fable_rows:
        print(f"  {r['benchmark_id']:28} score={r['score']}")


if __name__ == "__main__":
    main()
