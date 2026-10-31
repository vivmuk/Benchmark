#!/usr/bin/env python3
import json

d = json.load(open("data/results.json"))

print("One-Shot UI: size vs score")
print(f"{'Model':30s} {'Score':>5s} {'Bytes':>6s} {'Tok':>5s} {'Lat(s)':>7s} {'B/Scr':>7s}")
print("-" * 70)
ui_rows = [r for r in d['results'] if r['benchmark_id'] == 'one_shot_ui' and r['status'] == 'ok']
for r in sorted(ui_rows, key=lambda x: x.get('score', 0) or 0, reverse=True):
    display = next((m['display'] for m in d['models'] if m['id'] == r['model_id']), r['model_id'])
    score = r.get('score', r.get('score_auto', 0))
    tlen = len(r.get('raw_response', '') or '')
    tokens = r.get('total_tokens', 0)
    lat = r.get('latency', 0)
    eff = round(tlen / score, 1) if score > 0 else None
    print(f"{display:30s} {score:>5d} {tlen:>5d} {tokens:>5d} {lat:>7.1f} {str(eff or '?'):>7s}")

print("\n\nEfficiency ranking (lowest bytes/score = most efficient):")
sorted_by_eff = [(len(r.get('raw_response','') or '') / r.get('score',1), r) for r in ui_rows if r.get('score',0) > 0]
sorted_by_eff.sort()
for eff, r in sorted_by_eff:
    display = next((m['display'] for m in d['models'] if m['id'] == r['model_id']), r['model_id'])
    score = r.get('score', 0)
    tlen = len(r.get('raw_response', '') or '')
    print(f"{display:30s} {eff:>6.1f} b/scr score={score:>3d} bytes={tlen:>5d}")