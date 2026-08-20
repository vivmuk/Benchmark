#!/usr/bin/env python3
"""Run remaining 11 new models through core 5 benchmarks sequentially, then run_new_tracks for all 12."""
import sys, os, json, time
from pathlib import Path

SITE = Path.home() / ".openclaw/workspace/benchmarks/venice-benchmark-site"
os.chdir(str(SITE))

NEW_MODELS = [
    "qwen-3-7-max", "qwen-3-7-plus", "grok-4-20", "claude-opus-5-fast",
    "claude-opus-4-8-fast", "aion-labs-aion-3-0", "aion-labs-aion-3-0-mini",
    "nvidia-nemotron-3-super-120b-a12b", "qwen3-235b-a22b-thinking-2507",
    "minimax-m27", "gemini-3-7-flash",
]

LOG = "/tmp/phase2.log"
with open(LOG, "a") as f:
    f.write(f"\n=== Phase 2A: remaining {len(NEW_MODELS)} models ===\n")

for idx, mid in enumerate(NEW_MODELS):
    print(f"\n[{idx+1}/{len(NEW_MODELS)}] Running {mid} core 5...")
    t0 = time.time()
    rc = os.system(
        f'cd {SITE} && source /tmp/bv_env.sh && '
        f'python3 run_benchmarks.py --run-real --model {mid} --max-tokens 32768 --request-timeout 600 '
        f'>> {LOG} 2>&1'
    )
    elapsed = time.time() - t0
    ok = os.WEXITSTATUS(rc) if os.WIFEXITED(rc) else -1
    with open(LOG, "a") as f:
        f.write(f"[{idx+1}/{len(NEW_MODELS)}] {mid} {'DONE' if ok==0 else 'FAILED'} in {elapsed:.0f}s\n")

print("\n=== Phase 2A complete ===")

# Phase 2B: new tracks for all 12
os.system(f'cd {SITE} && source /tmp/bv_env.sh && '
    f'python3 run_new_tracks.py '
    f'--model gemini-3-7-flash --model qwen-3-7-max --model qwen-3-7-plus '
    f'--model grok-4-20 --model claude-opus-5-fast --model claude-opus-4-8-fast '
    f'--model deepseek-v4-flash --model aion-labs-aion-3-0 --model aion-labs-aion-3-0-mini '
    f'--model nvidia-nemotron-3-super-120b-a12b --model qwen3-235b-a22b-thinking-2507 '
    f'--model minimax-m27 '
    f'>> {LOG} 2>&1')

print("\n=== PHASE 2 COMPLETE ===")

# Summary
with open("data/results.json") as f:
    d = json.load(f)
from collections import Counter
c = Counter(r["model_id"] for r in d["results"])
full = [k for k, v in c.items() if v >= 7]
partial = {k: v for k, v in c.items() if v < 7}
print(f"Models: {len(d['models'])} | Rows: {len(d['results'])} | Total cost: ${d.get('total_estimated_cost_usd',0):.4f}")
print(f"Full coverage (7+): {len(full)}")
print(f"Partial: {partial}")