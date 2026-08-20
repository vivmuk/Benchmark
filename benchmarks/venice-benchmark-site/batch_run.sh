#!/bin/bash
# BenchmarkViv batch runner - Phase 1 (partial models) + Phase 2 (new models)
# Launched via terminal(background=true, notify_on_complete=true)
set -e

SITE_DIR="$HOME/.openclaw/workspace/benchmarks/venice-benchmark-site"
LOG_FILE="/tmp/benchmark_batch_run.log"

cd "$SITE_DIR"
source /tmp/bv_env.sh
export VENICE_INFERENCE_KEY

echo "============================================" | tee -a "$LOG_FILE"
echo "Benchmark batch run started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== PHASE 1: Value Density + Reverse Prompt for 7 partial models ===" | tee -a "$LOG_FILE"
echo "Models: deepseek-v4-flash-0731-fast, qwen-3-8-max, qwen-3-8-2-4t-a95b," | tee -a "$LOG_FILE"
echo "        claude-sonnet-5, gemini-3-6-flash, grok-4-6, nvidia-nemotron-3-5-lightning-30b-a3b" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

python3 run_new_tracks.py \
  --model deepseek-v4-flash-0731-fast \
  --model qwen-3-8-max \
  --model qwen-3-8-2-4t-a95b \
  --model claude-sonnet-5 \
  --model gemini-3-6-flash \
  --model grok-4-6 \
  --model nvidia-nemotron-3-5-lightning-30b-a3b \
  2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== PHASE 2A: 5 core benchmarks for 12 new models ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# New models to add (they already have value_density + reverse_prompt from phase 2B)
NEW_MODELS=(
  "gemini-3-7-flash"
  "qwen-3-7-max"
  "qwen-3-7-plus"
  "grok-4-20"
  "claude-opus-5-fast"
  "claude-opus-4-8-fast"
  "deepseek-v4-flash"
  "aion-labs-aion-3-0"
  "aion-labs-aion-3-0-mini"
  "nvidia-nemotron-3-super-120b-a12b"
  "qwen3-235b-a22b-thinking-2507"
  "minimax-m27"
)

for MODEL in "${NEW_MODELS[@]}"; do
  echo "    Running $MODEL (core 5) ---" | tee -a "$LOG_FILE"
  python3 run_benchmarks.py --run-real --model "$MODEL" --max-tokens 32768 --request-timeout 600 \
    2>&1 | tee -a "$LOG_FILE"
  echo "" | tee -a "$LOG_FILE"
done

echo "" | tee -a "$LOG_FILE"
echo "=== PHASE 2B: Value density + Reverse prompt for 12 new models ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

python3 run_new_tracks.py \
  --model gemini-3-7-flash \
  --model qwen-3-7-max \
  --model qwen-3-7-plus \
  --model grok-4-20 \
  --model claude-opus-5-fast \
  --model claude-opus-4-8-fast \
  --model deepseek-v4-flash \
  --model aion-labs-aion-3-0 \
  --model aion-labs-aion-3-0-mini \
  --model nvidia-nemotron-3-super-120b-a12b \
  --model qwen3-235b-a22b-thinking-2507 \
  --model minimax-m27 \
  2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"
echo "Benchmark batch run COMPLETE: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"

# Quick summary
python3 -c "
import json
d=json.load(open('data/results.json'))
print()
print('=== FINAL SUMMARY ===')
print(f'Models: {len(d.get(\"models\",[]))}')
print(f'Benchmarks: {len(d.get(\"benchmarks\",[]))}')
for b in d.get('benchmarks',[]):
    print(f'  {b[\"id\"]}: {b[\"name\"]}')
print(f'Rows: {len(d.get(\"results\",[]))}')
print(f'Total cost: \${d.get(\"total_estimated_cost_usd\",0):.4f}')
# Count models with full coverage
from collections import Counter
bc=Counter()
for r in d.get('results',[]):
    bc[r.get('model_id','')] += 1
print(f'Models with all 7 benchmarks: {sum(1 for v in bc.values() if v==7)}')
print(f'Models with partial: {sum(1 for v in bc.values() if v<7)}')
" 2>&1 | tee -a "$LOG_FILE"