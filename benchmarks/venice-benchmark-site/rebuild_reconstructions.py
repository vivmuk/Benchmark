#!/usr/bin/env python3
"""Rebuild data/vision/reconstructions.json from ALL vision-ok rows in results.json.

Each run_new_tracks.py call overwrites reconstructions.json with only its own
models, so partial runs leave the gallery missing earlier vision-capable models.
This reconstructs the complete set from the canonical results ledger.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "data" / "results.json"
RECON = ROOT / "data" / "vision" / "reconstructions.json"
META = ROOT / "data" / "vision" / "reverse_prompt_meta.json"

d = json.load(open(RESULTS))
disp = {m["id"]: m["display"] for m in d["models"]}
meta = json.load(open(META))

results = []
for r in d["results"]:
    if r.get("benchmark_id") != "reverse_prompt_vision":
        continue
    rid = r["model_id"]
    if r.get("status") != "ok":
        continue
    m = r.get("metrics") or {}
    results.append({
        "model_id": rid,
        "display": disp.get(rid, rid),
        "reconstructed_prompt": r.get("raw_response") or "",
        "score": r.get("score"),
        "hit_rate": m.get("hit_rate"),
        "hits": m.get("hits"),
    })

# sort by score desc
results.sort(key=lambda x: -(x["score"] or 0))

out = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "source_image": meta.get("image_path"),
    "image_model": meta.get("image_model"),
    "source_prompt": meta.get("source_prompt"),
    "judge_model": "openai-gpt-56-luna",
    "results": results,
}
RECON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
print(f"Wrote {RECON} with {len(results)} reconstruction(s) (vision-ok models)")
for r in results:
    print(f"  {r['model_id']:35s} score={r['score']} hit_rate={r.get('hit_rate')}")