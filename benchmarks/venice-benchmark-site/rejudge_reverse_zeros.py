#!/usr/bin/env python3
"""Re-judge reverse_prompt_vision rows that have score=0 from judge_status=error."""
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import run_benchmarks as rb
import run_new_tracks as rnt

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "data" / "results.json"
RECON = ROOT / "data" / "vision" / "reconstructions.json"
META = ROOT / "data" / "vision" / "reverse_prompt_meta.json"


def main() -> None:
    api_key = rnt.load_api_key()
    pricing = rb.fetch_pricing(api_key)
    meta = json.loads(META.read_text(encoding="utf-8"))
    source_prompt = meta["source_prompt"]
    checklist = meta["checklist"]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    shutil.copy2(RESULTS, RESULTS.with_suffix(f".json.snapshot-pre-rejudge-{stamp}"))
    shutil.copy2(RECON, RECON.with_suffix(f".json.snapshot-pre-rejudge-{stamp}"))

    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    recon = json.loads(RECON.read_text(encoding="utf-8"))
    recon_by = {r.get("model_id"): r for r in recon.get("results") or []}

    targets = []
    for row in data.get("results") or []:
        if row.get("benchmark_id") != "reverse_prompt_vision":
            continue
        if row.get("status") != "ok":
            continue
        metrics = row.get("metrics") or {}
        score = row.get("score")
        jstatus = metrics.get("judge_status")
        hits = metrics.get("hits") or {}
        if score == 0 and (jstatus == "error" or not hits):
            cand = (row.get("raw_response") or "").strip()
            if not cand and recon_by.get(row.get("model_id")):
                cand = (recon_by[row["model_id"]].get("reconstructed_prompt") or "").strip()
            if cand:
                targets.append((row, cand))

    print(f"Re-judging {len(targets)} rows with judge={rnt.JUDGE_MODEL}")
    updates = []
    for row, cand in targets:
        mid = row["model_id"]
        print(f"  {mid}: judging ({len(cand)} chars)...", end=" ", flush=True)
        judged = None
        for attempt in range(1, 4):
            judged = rnt.judge_reverse_prompt(api_key, source_prompt, checklist, cand, pricing)
            if judged.get("judge_status") in ("ok", "heuristic_fallback", "error_then_heuristic") and (
                judged.get("hits") or judged.get("score", 0) > 0 or judged.get("judge_status") != "error"
            ):
                # accept if we have hits or non-error fallback
                if judged.get("hits") or judged.get("judge_status") != "error":
                    break
            print(f"retry{attempt}", end=" ", flush=True)
            time.sleep(1.5 * attempt)
        assert judged is not None
        old_score = row.get("score")
        old_judge_cost = float((row.get("metrics") or {}).get("judge_cost_usd") or 0)
        new_judge_cost = float(judged.get("judge_cost_usd") or 0)
        model_only = float((row.get("metrics") or {}).get("model_only_cost_usd") or 0)
        if not model_only:
            # derive from total - old judge
            model_only = max(0.0, float(row.get("estimated_cost_usd") or 0) - old_judge_cost)

        row["score"] = int(judged["score"])
        row["estimated_cost_usd"] = round(model_only + new_judge_cost, 6)
        metrics = dict(row.get("metrics") or {})
        metrics.update(
            {
                "hit_rate": judged.get("hit_rate"),
                "hits": judged.get("hits") or {},
                "hallucinated_major": judged.get("hallucinated_major"),
                "missed_text": judged.get("missed_text"),
                "judge_model": rnt.JUDGE_MODEL,
                "judge_status": judged.get("judge_status"),
                "judge_error": judged.get("judge_error"),
                "judge_cost_usd": new_judge_cost,
                "model_only_cost_usd": model_only,
                "rejudged_at": datetime.now(timezone.utc).isoformat(),
                "notes": judged.get("notes"),
            }
        )
        row["metrics"] = metrics
        # keep status ok
        row["status"] = "ok"
        row["error"] = None

        # update reconstructions.json
        rr = recon_by.get(mid)
        if rr is not None:
            rr["score"] = int(judged["score"])
            rr["hit_rate"] = judged.get("hit_rate")
            rr["hits"] = judged.get("hits") or {}
            rr["hallucinated_major"] = judged.get("hallucinated_major")
            rr["missed_text"] = judged.get("missed_text")
            rr["notes"] = judged.get("notes")
            rr["judge_status"] = judged.get("judge_status")

        true_n = sum(1 for v in (judged.get("hits") or {}).values() if v)
        print(
            f"{old_score} -> {judged['score']}  hits={true_n}/{len(checklist)}  "
            f"status={judged.get('judge_status')}"
        )
        updates.append({"model_id": mid, "old": old_score, "new": judged["score"], "status": judged.get("judge_status")})

    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["total_estimated_cost_usd"] = round(
        sum(float(r.get("estimated_cost_usd") or 0) for r in data.get("results") or []), 6
    )
    RESULTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    recon["rejudged_at"] = datetime.now(timezone.utc).isoformat()
    RECON.write_text(json.dumps(recon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\nSummary:")
    for u in updates:
        print(f"  {u['model_id']}: {u['old']} -> {u['new']} ({u['status']})")
    print(f"Wrote {RESULTS}")
    print(f"Wrote {RECON}")


if __name__ == "__main__":
    main()
