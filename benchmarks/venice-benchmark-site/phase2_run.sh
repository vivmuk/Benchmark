#!/bin/bash
# Phase 2: core 5 benchmarks + new tracks for 12 new models
SITE_DIR="$HOME/.openclaw/workspace/benchmarks/venice-benchmark-site"
cd "$SITE_DIR"
source /tmp/bv_env.sh
export VENICE_INFERENCE_KEY

LOG=/tmp/phase2.log
echo "=== PHASE 2 started $(date -u +%H:%M:%SZ) ===" | tee "$LOG"

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

# ---- Phase 2A: core 5 benchmarks ----
for MODEL in "${NEW_MODELS[@]}"; do
  echo "--- 2A: $MODEL (core 5) ---" | tee -a "$LOG"
  python3 run_benchmarks.py --run-real --model "$MODEL" --max-tokens 32768 --request-timeout 600 2>&1 | tee -a "$LOG"
  echo "" | tee -a "$LOG"
done

# ---- Phase 2B: value_density + reverse_prompt_vision ----
echo "=== 2B: new tracks for 12 new models ===" | tee -a "$LOG"
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
  2>&1 | tee -a "$LOG"

echo "=== PHASE 2 COMPLETE $(date -u +%H:%M:%SZ) ===" | tee -a "$LOG"

# Summary
python3 -c "
import json
d=json.load(open('data/results.json'))
print('Models:', len(d['models']))
print('Total rows:', len(d['results']))
print('Total cost: \$%.4f' % d.get('total_estimated_cost_usd',0))
from collections import Counter
c=Counter(r['model_id'] for r in d['results'])
full=[k for k,v in c.items() if v==7]
print(f'Models with all 7 tracks: {len(full)}')
for k in full:
    print('  ', k)
print('Partial:')
for k,v in c.items():
    if v!=7:
        print('  ', k, v, 'rows')
" 2>&1 | tee -a "$LOG"