#!/usr/bin/env python3
"""Retry reverse_prompt_vision only for models that failed on DIEM spend limit."""
from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import run_benchmarks as rb
import run_new_tracks as nt
from model_registry import MODELS

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "data" / "results.json"
VISION_DIR = ROOT / "data" / "vision"
META_PATH = VISION_DIR / "reverse_prompt_meta.json"
IMAGE_PATH = VISION_DIR / "reverse_prompt_source.png"
RECON_PATH = VISION_DIR / "reconstructions.json"

RETRY_IDS = [
    "claude-opus-5",
    "minimax-m3-preview",
    "grok-4-5",
    "inkling",
    "kimi-k3",
]


def prepare_image() -> str:
    img_bytes = IMAGE_PATH.read_bytes()
    mime = "image/png"
    try:
        from PIL import Image

        im = Image.open(BytesIO(img_bytes)).convert("RGB")
        if im.width > 1280:
            ratio = 1280 / im.width
            im = im.resize((1280, int(im.height * ratio)), Image.Resampling.LANCZOS)
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=90, optimize=True)
        img_bytes = buf.getvalue()
        mime = "image/jpeg"
        print(f"Image prepared: {im.size}, {len(img_bytes)} bytes JPEG")
    except Exception as exc:
        print(f"PIL resize skipped ({exc}); using original")
    b64 = base64.b64encode(img_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"


def main() -> None:
    api_key = nt.load_api_key()
    # smoke
    print("auth ok, key present")
    pricing = rb.fetch_pricing(api_key)
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    source_prompt = meta["source_prompt"]
    checklist = meta["checklist"]
    instruction = meta["reverse_prompt_instruction"]
    data_url = prepare_image()

    id_to_disp = {m["id"]: m.get("display", m["id"]) for m in MODELS}
    new_rows = []
    reconstructions = []

    # keep prior reconstructions for models we are not retrying
    prior = {}
    if RECON_PATH.exists():
        try:
            prior_data = json.loads(RECON_PATH.read_text(encoding="utf-8"))
            for r in prior_data.get("results") or []:
                if r.get("model_id") not in RETRY_IDS:
                    prior[r["model_id"]] = r
        except Exception:
            pass

    for i, mid in enumerate(RETRY_IDS, 1):
        disp = id_to_disp.get(mid, mid)
        print(f"[{i}/{len(RETRY_IDS)}] {disp} reverse_prompt ...", end=" ", flush=True)
        call = nt.call_vision(api_key, mid, instruction, data_url, max_tokens=1200)
        if call["status"] != "ok":
            err = str(call.get("error") or "")[:200]
            print(f"ERROR {err}")
            new_rows.append(
                {
                    "model_id": mid,
                    "benchmark_id": "reverse_prompt_vision",
                    "status": "error",
                    "score": 0,
                    "latency": call.get("latency") or 0,
                    "prompt_tokens": call.get("prompt_tokens") or 0,
                    "completion_tokens": call.get("completion_tokens") or 0,
                    "total_tokens": call.get("total_tokens") or 0,
                    "estimated_cost_usd": 0.0,
                    "raw_response": call.get("raw_response") or "",
                    "error": call.get("error"),
                    "metrics": {"supports_vision": True, "retry": "diem"},
                }
            )
            time.sleep(0.8)
            continue

        model_cost = rb.estimate_cost(
            mid, call["prompt_tokens"], call["completion_tokens"], pricing
        )
        print(f"got {call['completion_tokens']} tok, judging ...", end=" ", flush=True)
        judged = nt.judge_reverse_prompt(
            api_key, source_prompt, checklist, call["raw_response"], pricing
        )
        total_cost = round(model_cost + float(judged.get("judge_cost_usd") or 0), 6)
        print(
            f"score={judged['score']} hit_rate={judged.get('hit_rate')} "
            f"cost=${total_cost:.4f}"
        )
        new_rows.append(
            {
                "model_id": mid,
                "benchmark_id": "reverse_prompt_vision",
                "status": "ok",
                "score": judged["score"],
                "latency": call["latency"],
                "prompt_tokens": call["prompt_tokens"],
                "completion_tokens": call["completion_tokens"],
                "total_tokens": call["total_tokens"],
                "estimated_cost_usd": total_cost,
                "raw_response": call["raw_response"],
                "error": None,
                "metrics": {
                    "supports_vision": True,
                    "hit_rate": judged.get("hit_rate"),
                    "hits": judged.get("hits"),
                    "hallucinated_major": judged.get("hallucinated_major"),
                    "missed_text": judged.get("missed_text"),
                    "judge_model": nt.JUDGE_MODEL,
                    "judge_status": judged.get("judge_status"),
                    "judge_cost_usd": judged.get("judge_cost_usd"),
                    "model_only_cost_usd": model_cost,
                    "retry": "diem",
                },
            }
        )
        reconstructions.append(
            {
                "model_id": mid,
                "display": disp,
                "reconstructed_prompt": call["raw_response"],
                "score": judged["score"],
                "hit_rate": judged.get("hit_rate"),
                "hits": judged.get("hits"),
            }
        )
        time.sleep(0.8)

    # merge reconstructions
    all_recon = list(prior.values()) + reconstructions
    RECON_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_image": meta.get("image_path"),
                "image_model": meta.get("image_model"),
                "source_prompt": source_prompt,
                "judge_model": nt.JUDGE_MODEL,
                "results": all_recon,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {RECON_PATH}")

    data = nt.merge_results(new_rows, [])
    ok = [r for r in new_rows if r["status"] == "ok"]
    err = [r for r in new_rows if r["status"] != "ok"]
    print("\n=== RETRY SUMMARY ===")
    print(f"ok {len(ok)} / err {len(err)}")
    for r in ok:
        print(f"  {r['model_id']}: score={r['score']} cost=${r['estimated_cost_usd']}")
    for r in err:
        print(f"  FAIL {r['model_id']}: {str(r.get('error'))[:120]}")
    print(f"results total rows={len(data['results'])} cost=${data['total_estimated_cost_usd']}")


if __name__ == "__main__":
    main()
