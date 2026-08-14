#!/usr/bin/env python3
"""Run Value Density + Reverse-Prompt Vision tracks and merge into results.json.

Value Density:
  Fixed completion budget (1024 tokens). Checklist score is independent of length.
  Also records value_per_1k_tokens and value_per_usd.

Reverse Prompt Vision:
  Models see a nano-banana-2 image (no source prompt) and reconstruct the prompt.
  A judge model scores reconstructed prompts against a fixed attribute checklist.
  Non-vision models are recorded as skipped (not zero-scored).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

import run_benchmarks as rb
from model_registry import MODELS

ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "data" / "results.json"
VISION_DIR = ROOT / "data" / "vision"
META_PATH = VISION_DIR / "reverse_prompt_meta.json"
IMAGE_PATH = VISION_DIR / "reverse_prompt_source.png"

VALUE_BUDGET_TOKENS = 1024
JUDGE_MODEL = "openai-gpt-56-luna"
TEMPERATURE = 0.3
REQUEST_TIMEOUT = 600

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def load_api_key() -> str:
    key = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
    if key:
        return key
    db = Path.home() / ".openclaw/agents/main/agent/openclaw-agent.sqlite"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    j = json.loads(
        con.execute(
            "select store_json from auth_profile_store where store_key='primary'"
        ).fetchone()[0]
    )
    key = (j.get("profiles") or {}).get("venice:cloud", {}).get("key")
    if not key:
        raise SystemExit("No Venice API key found")
    os.environ["VENICE_INFERENCE_KEY"] = key
    os.environ["VENICE_API_KEY"] = key
    return key


def vision_capable(api_key: str) -> dict[str, bool]:
    """Map model_id -> supportsVision from Venice /models."""
    out: dict[str, bool] = {}
    try:
        resp = requests.get(
            rb.MODELS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60,
        )
        resp.raise_for_status()
        for m in resp.json().get("data", []):
            mid = m.get("id")
            caps = (m.get("model_spec") or {}).get("capabilities") or {}
            if mid:
                out[mid] = bool(caps.get("supportsVision"))
    except Exception as exc:
        print(f"Warning: could not fetch vision caps ({exc})")
    return out


# ---------------------------------------------------------------------------
# Track definitions
# ---------------------------------------------------------------------------

VALUE_DENSITY = {
    "id": "value_density",
    "name": "Value Density @1K",
    "scoring": (
        "Fixed max_tokens=1024. Checklist of required JSON fields (0-100). "
        "Secondary: value_per_1k_tokens = score / (total_tokens/1000); "
        "value_per_usd = score / cost. Length alone cannot raise score."
    ),
    "prompt": (
        "Return ONLY a single JSON object (no markdown fences, no commentary) with exactly these keys:\n"
        "{\n"
        '  "drug_pair": string,                 // the clinically significant interacting pair\n'
        '  "severity": "Major"|"Moderate"|"Minor",\n'
        '  "mechanism": string,                 // pharmacological mechanism in <= 25 words\n'
        '  "clinical_action": string,           // concrete next step in <= 20 words\n'
        '  "monitor": [string, string],         // exactly 2 monitoring items\n'
        '  "avoid_if": string,                  // one high-risk condition in <= 15 words\n'
        '  "confidence": number                 // 0-100 integer\n'
        "}\n\n"
        "Scenario: patient on warfarin 5 mg daily for atrial fibrillation also takes "
        "ibuprofen 400 mg TID PRN for osteoarthritis. Identify the primary interaction only.\n\n"
        "Hard rules:\n"
        "- Valid JSON only\n"
        "- No extra keys\n"
        "- No prose outside JSON\n"
        "- Be precise, not verbose\n"
    ),
}

REVERSE_PROMPT = {
    "id": "reverse_prompt_vision",
    "name": "Reverse-Prompt Vision",
    "scoring": (
        "Vision models reconstruct the image generation prompt with no access to the source prompt. "
        "Judge model scores reconstructed prompt against a fixed 28-attribute checklist (0-100). "
        "Non-vision models are skipped (status=skipped), not zero-scored."
    ),
}


def score_value_density(text: str) -> tuple[int, dict]:
    """Checklist score independent of length. Returns (score, details)."""
    details = {"parse_ok": False, "hits": {}, "penalties": []}
    if not text:
        return 0, details
    raw = text.strip()
    # Strip accidental fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # Extract first JSON object if wrapped
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        details["penalties"].append("no_json_object")
        return 0, details
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        details["penalties"].append("json_parse_error")
        return 5, details  # tiny credit for attempting JSON shape
    if not isinstance(obj, dict):
        details["penalties"].append("not_object")
        return 5, details
    details["parse_ok"] = True
    score = 0

    required = [
        "drug_pair",
        "severity",
        "mechanism",
        "clinical_action",
        "monitor",
        "avoid_if",
        "confidence",
    ]
    # Presence of required keys (21)
    present = sum(1 for k in required if k in obj)
    score += int(21 * present / len(required))
    details["hits"]["required_keys"] = present

    # No extra keys (10)
    extra = [k for k in obj.keys() if k not in required]
    if not extra:
        score += 10
        details["hits"]["no_extra_keys"] = True
    else:
        details["penalties"].append(f"extra_keys:{extra[:5]}")

    pair = str(obj.get("drug_pair", "")).lower()
    if "warfarin" in pair and "ibuprofen" in pair:
        score += 18
        details["hits"]["drug_pair"] = True
    elif "warfarin" in pair or "ibuprofen" in pair:
        score += 6
        details["hits"]["drug_pair_partial"] = True

    sev = str(obj.get("severity", "")).strip().capitalize()
    if sev in ("Major", "Moderate", "Minor"):
        score += 8
        details["hits"]["severity_enum"] = sev
        if sev == "Major":
            score += 7
            details["hits"]["severity_major"] = True

    mech = str(obj.get("mechanism", "")).lower()
    mech_terms = [
        "platelet",
        "bleed",
        "nsaid",
        "anticoag",
        "pharmacodynamic",
        "gi",
        "gastric",
        "synerg",
        "prostaglandin",
    ]
    if any(t in mech for t in mech_terms):
        score += 12
        details["hits"]["mechanism"] = True
    if len(mech.split()) <= 30:
        score += 3
        details["hits"]["mechanism_concise"] = True

    action = str(obj.get("clinical_action", "")).lower()
    action_terms = [
        "avoid",
        "discontinue",
        "alternative",
        "acetaminophen",
        "paracetamol",
        "monitor inr",
        "stop",
        "replace",
    ]
    if any(t in action for t in action_terms):
        score += 8
        details["hits"]["clinical_action"] = True

    mon = obj.get("monitor")
    if isinstance(mon, list) and len(mon) == 2 and all(isinstance(x, str) and x.strip() for x in mon):
        score += 8
        details["hits"]["monitor_shape"] = True
        mon_l = " ".join(mon).lower()
        if any(t in mon_l for t in ("inr", "bleed", "hemoglobin", "cbc", "gi", "bruis")):
            score += 4
            details["hits"]["monitor_content"] = True

    avoid = str(obj.get("avoid_if", "")).lower()
    if avoid and len(avoid.split()) <= 20:
        score += 3
        details["hits"]["avoid_if"] = True

    conf = obj.get("confidence")
    if isinstance(conf, (int, float)) and 0 <= float(conf) <= 100:
        score += 3
        details["hits"]["confidence"] = True

    # Verbosity penalty if model ignored "JSON only" and dumped essay around it
    if len(text) > 1200:
        score = max(0, score - 8)
        details["penalties"].append("verbosity_wrap")

    return min(100, int(score)), details


def call_text(api_key: str, model_id: str, prompt: str, max_tokens: int) -> dict:
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": TEMPERATURE,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(
            rb.API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        latency = round(time.monotonic() - start, 3)
        if resp.status_code != 200:
            return {
                "status": "error",
                "latency": latency,
                "error": resp.text[:500],
                "raw_response": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        data = resp.json()
        usage = data.get("usage") or {}
        msg = ((data.get("choices") or [{}])[0].get("message") or {})
        content = msg.get("content") or ""
        if not str(content).strip():
            # some models put text only in reasoning; still an error for this track
            return {
                "status": "error",
                "latency": latency,
                "error": "empty content",
                "raw_response": "",
                "prompt_tokens": int(usage.get("prompt_tokens") or 0),
                "completion_tokens": int(usage.get("completion_tokens") or 0),
                "total_tokens": int(usage.get("total_tokens") or 0),
            }
        return {
            "status": "ok",
            "latency": latency,
            "raw_response": content if isinstance(content, str) else json.dumps(content),
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }
    except Exception as exc:
        return {
            "status": "error",
            "latency": round(time.monotonic() - start, 3),
            "error": str(exc)[:500],
            "raw_response": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }


def call_vision(api_key: str, model_id: str, prompt: str, image_data_url: str, max_tokens: int = 1200) -> dict:
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ],
        "max_tokens": max_tokens,
        "temperature": TEMPERATURE,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(
            rb.API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        latency = round(time.monotonic() - start, 3)
        if resp.status_code != 200:
            return {
                "status": "error",
                "latency": latency,
                "error": resp.text[:500],
                "raw_response": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        data = resp.json()
        usage = data.get("usage") or {}
        msg = ((data.get("choices") or [{}])[0].get("message") or {})
        content = msg.get("content") or ""
        if not str(content).strip():
            return {
                "status": "error",
                "latency": latency,
                "error": "empty content",
                "raw_response": "",
                "prompt_tokens": int(usage.get("prompt_tokens") or 0),
                "completion_tokens": int(usage.get("completion_tokens") or 0),
                "total_tokens": int(usage.get("total_tokens") or 0),
            }
        return {
            "status": "ok",
            "latency": latency,
            "raw_response": content if isinstance(content, str) else json.dumps(content),
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }
    except Exception as exc:
        return {
            "status": "error",
            "latency": round(time.monotonic() - start, 3),
            "error": str(exc)[:500],
            "raw_response": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }


def judge_reverse_prompt(api_key: str, source_prompt: str, checklist: list, candidate: str, pricing: dict) -> dict:
    """Judge reconstructed prompt vs checklist. Returns score + details + usage."""
    items = "\n".join(f"- {c['id']}: {c['desc']}" for c in checklist)
    judge_prompt = (
        "You are a strict visual-prompt fidelity judge.\n"
        "SOURCE PROMPT (ground truth that generated the image):\n"
        f"\"\"\"{source_prompt}\"\"\"\n\n"
        "ATTRIBUTE CHECKLIST (score each true/false whether the CANDIDATE prompt captures it):\n"
        f"{items}\n\n"
        "CANDIDATE reconstructed prompt:\n"
        f"\"\"\"{candidate[:6000]}\"\"\"\n\n"
        "Return ONLY JSON:\n"
        "{\n"
        '  "hits": {"attribute_id": true/false, ...},  // every checklist id\n'
        '  "hallucinated_major": [string],             // major objects/text invented not in source\n'
        '  "missed_text": [string],                    // important on-image text missed\n'
        '  "notes": string\n'
        "}\n"
        "Be conservative: mark true only if clearly present in the candidate."
    )
    call = call_text(api_key, JUDGE_MODEL, judge_prompt, max_tokens=1500)
    cost = rb.estimate_cost(
        JUDGE_MODEL, call.get("prompt_tokens") or 0, call.get("completion_tokens") or 0, pricing
    )
    result = {
        "judge_status": call["status"],
        "judge_error": call.get("error"),
        "judge_raw": call.get("raw_response") or "",
        "judge_tokens": call.get("total_tokens") or 0,
        "judge_cost_usd": cost,
        "score": 0,
        "hit_rate": 0.0,
        "hits": {},
    }
    if call["status"] != "ok":
        # Never leave a successful reconstruction unscored: fall back to keywords.
        fb = heuristic_judge(candidate, checklist, result)
        fb["judge_status"] = "error_then_heuristic"
        fb["judge_error"] = call.get("error")
        return fb
    raw = call["raw_response"]
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        # fallback heuristic against checklist keywords
        return heuristic_judge(candidate, checklist, result)
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return heuristic_judge(candidate, checklist, result)

    hits = obj.get("hits") or {}
    # ensure all ids
    bool_hits = {}
    for c in checklist:
        cid = c["id"]
        val = hits.get(cid)
        bool_hits[cid] = bool(val) if isinstance(val, bool) else bool(val)
    n = len(checklist) or 1
    true_n = sum(1 for v in bool_hits.values() if v)
    hit_rate = true_n / n
    # base from hit rate (0-85)
    score = int(round(hit_rate * 85))
    # penalties for major hallucinations
    hall = obj.get("hallucinated_major") or []
    if isinstance(hall, list) and hall:
        score = max(0, score - min(15, 3 * len(hall)))
    # small bonus if few misses on text
    missed = obj.get("missed_text") or []
    if isinstance(missed, list) and len(missed) == 0 and true_n >= n * 0.5:
        score = min(100, score + 5)
    # completeness bonus
    if true_n == n:
        score = min(100, score + 10)
    result.update(
        {
            "score": int(score),
            "hit_rate": round(hit_rate, 4),
            "hits": bool_hits,
            "hallucinated_major": hall if isinstance(hall, list) else [],
            "missed_text": missed if isinstance(missed, list) else [],
            "notes": obj.get("notes"),
        }
    )
    return result


def heuristic_judge(candidate: str, checklist: list, result: dict) -> dict:
    """Keyword fallback if judge JSON fails."""
    low = (candidate or "").lower()
    keywords = {
        "lab_setting": ["laboratory", "lab", "research"],
        "twilight": ["twilight", "dusk", "evening"],
        "molecule_center": ["molecule", "helix", "molecular"],
        "teal_glass": ["teal", "cyan"],
        "amber_nodes": ["amber"],
        "holographic_dashboard": ["holograph", "dashboard", "hologram"],
        "evidencegrade_title": ["evidencegrade", "evidence grade"],
        "grade_ladder": ["grade", "a-f", "ladder"],
        "citation_chart": ["citation", "confidence", "chart"],
        "arched_window": ["arch", "window"],
        "rainy_city": ["rain", "tokyo", "street"],
        "neon_kanji": ["kanji", "neon", "japanese"],
        "red_umbrella": ["red umbrella", "umbrella"],
        "black_cat": ["black cat", "cat"],
        "notebook": ["notebook", "journal"],
        "cyp3a4_note": ["cyp3a4", "cyp"],
        "fountain_pen": ["fountain pen", "pen"],
        "coffee_cup": ["coffee", "cup"],
        "cracked_saucer": ["saucer", "cracked"],
        "brass_lamps": ["brass", "lamp"],
        "green_shade": ["green glass", "green shade"],
        "reagent_bottles": ["reagent", "bottle"],
        "drug_labels": ["aspirin", "warfarin", "ibuprofen"],
        "microscope": ["microscope"],
        "monstera": ["monstera"],
        "volumetric_light": ["volumetric", "god-ray", "god ray"],
        "teal_amber_grade": ["teal", "amber"],
        "photoreal_hologram_mix": ["photoreal", "holograph"],
    }
    hits = {}
    for c in checklist:
        kws = keywords.get(c["id"], [c["desc"].split()[0].lower()])
        hits[c["id"]] = any(k in low for k in kws)
    n = len(checklist) or 1
    true_n = sum(1 for v in hits.values() if v)
    result.update(
        {
            "score": int(round(true_n / n * 100)),
            "hit_rate": round(true_n / n, 4),
            "hits": hits,
            "notes": "heuristic_fallback",
            "judge_status": "heuristic_fallback",
        }
    )
    return result


def merge_results(new_rows: list[dict], new_benchmarks: list[dict]) -> dict:
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    pairs = {(r["model_id"], r["benchmark_id"]) for r in new_rows}
    kept = [
        r
        for r in data.get("results", [])
        if (r.get("model_id"), r.get("benchmark_id")) not in pairs
    ]
    data["results"] = kept + new_rows

    # merge benchmark defs
    existing_b = {b["id"]: b for b in data.get("benchmarks", [])}
    for b in new_benchmarks:
        existing_b[b["id"]] = b
    # keep stable order: old non-new first then append new ids at end if missing order
    preferred = [
        "intent_understanding",
        "one_shot_ui",
        "brick_breaker_realism",
        "startup_in_a_weekend",
        "pharma_drug_interaction",
        "pharma_regulatory_comprehension",
        "value_density",
        "reverse_prompt_vision",
    ]
    ordered = []
    for pid in preferred:
        if pid in existing_b:
            ordered.append(existing_b.pop(pid))
    ordered.extend(existing_b.values())
    data["benchmarks"] = ordered

    data["models"] = MODELS
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["dry_run"] = False
    data["total_estimated_cost_usd"] = round(
        sum(float(r.get("estimated_cost_usd") or 0) for r in data["results"]), 6
    )
    RESULTS_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, action="append", dest="model_ids",
                        help="Run only specific model(s). Repeatable. Omit to run all.")
    args = parser.parse_args()
    selected = [m for m in MODELS if not args.model_ids or m["id"] in args.model_ids]
    if args.model_ids:
        missed = set(args.model_ids) - {m["id"] for m in selected}
        if missed:
            print(f"WARNING: requested models not in registry: {missed}")

    api_key = load_api_key()
    pricing = rb.fetch_pricing(api_key)
    vision_map = vision_capable(api_key)

    if not META_PATH.exists() or not IMAGE_PATH.exists():
        raise SystemExit("Missing vision fixture. Generate reverse_prompt_source.png first.")
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    source_prompt = meta["source_prompt"]
    checklist = meta["checklist"]
    instruction = meta["reverse_prompt_instruction"]

    # Prepare image data URL (may be large; nano-banana 2K ~10MB)
    img_bytes = IMAGE_PATH.read_bytes()
    # Downscale via PIL if huge to keep vision requests manageable
    try:
        from PIL import Image
        import io

        im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        # max width 1280 for API efficiency while keeping detail
        if im.width > 1280:
            ratio = 1280 / im.width
            im = im.resize((1280, int(im.height * ratio)), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90, optimize=True)
        img_bytes = buf.getvalue()
        mime = "image/jpeg"
        print(f"Image prepared for vision: {im.size}, {len(img_bytes)} bytes JPEG")
    except Exception as exc:
        print(f"PIL resize skipped ({exc}); using original PNG")
        mime = "image/png"
    b64 = base64.b64encode(img_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    new_rows: list[dict] = []
    bench_defs = [
        {
            "id": VALUE_DENSITY["id"],
            "name": VALUE_DENSITY["name"],
            "prompt": VALUE_DENSITY["prompt"],
            "scoring": VALUE_DENSITY["scoring"],
        },
        {
            "id": REVERSE_PROMPT["id"],
            "name": REVERSE_PROMPT["name"],
            "prompt": instruction,
            "scoring": REVERSE_PROMPT["scoring"],
            "fixture": {
                "image": meta.get("image_path"),
                "image_model": meta.get("image_model"),
                "source_prompt_path": "data/vision/source_prompt.txt",
                "checklist_count": len(checklist),
                "judge_model": JUDGE_MODEL,
            },
        },
    ]

    n_models = len(selected)
    # ---- Value density ----
    print(f"\n=== Value Density @1K ({n_models} models, max_tokens={VALUE_BUDGET_TOKENS}) ===")
    for i, model in enumerate(selected, 1):
        mid, disp = model["id"], model["display"]
        print(f"[{i}/{n_models}] {disp} value_density ...", end=" ", flush=True)
        call = call_text(api_key, mid, VALUE_DENSITY["prompt"], VALUE_BUDGET_TOKENS)
        if call["status"] == "ok":
            score, details = score_value_density(call["raw_response"])
            cost = rb.estimate_cost(
                mid, call["prompt_tokens"], call["completion_tokens"], pricing
            )
            total_tok = call["total_tokens"] or 0
            v_per_1k = round(score / (total_tok / 1000), 3) if total_tok > 0 else None
            v_per_usd = round(score / cost, 3) if cost > 0 else None
            print(
                f"ok score={score} tok={total_tok} $/run={cost:.4f} "
                f"val/1k={v_per_1k} val/$={v_per_usd}"
            )
            new_rows.append(
                {
                    "model_id": mid,
                    "benchmark_id": "value_density",
                    "status": "ok",
                    "score": score,
                    "latency": call["latency"],
                    "prompt_tokens": call["prompt_tokens"],
                    "completion_tokens": call["completion_tokens"],
                    "total_tokens": total_tok,
                    "estimated_cost_usd": cost,
                    "raw_response": call["raw_response"],
                    "error": None,
                    "metrics": {
                        "budget_max_tokens": VALUE_BUDGET_TOKENS,
                        "value_per_1k_tokens": v_per_1k,
                        "value_per_usd": v_per_usd,
                        "details": details,
                    },
                }
            )
        else:
            print(f"ERROR {str(call.get('error'))[:120]}")
            new_rows.append(
                {
                    "model_id": mid,
                    "benchmark_id": "value_density",
                    "status": "error",
                    "score": 0,
                    "latency": call["latency"],
                    "prompt_tokens": call.get("prompt_tokens") or 0,
                    "completion_tokens": call.get("completion_tokens") or 0,
                    "total_tokens": call.get("total_tokens") or 0,
                    "estimated_cost_usd": 0.0,
                    "raw_response": "",
                    "error": call.get("error"),
                    "metrics": {"budget_max_tokens": VALUE_BUDGET_TOKENS},
                }
            )
        time.sleep(0.8)

    # ---- Reverse prompt vision ----
    print(f"\n=== Reverse-Prompt Vision ({n_models} models, judge={JUDGE_MODEL}) ===")
    reconstructions = []
    for i, model in enumerate(selected, 1):
        mid, disp = model["id"], model["display"]
        supports = vision_map.get(mid)
        if supports is False:
            print(f"[{i}/{n_models}] {disp} SKIP (no vision)")
            new_rows.append(
                {
                    "model_id": mid,
                    "benchmark_id": "reverse_prompt_vision",
                    "status": "skipped",
                    "score": None,
                    "latency": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "raw_response": "",
                    "error": "model does not support vision",
                    "metrics": {"supports_vision": False},
                }
            )
            continue

        print(f"[{i}/{n_models}] {disp} reverse_prompt ...", end=" ", flush=True)
        call = call_vision(api_key, mid, instruction, data_url, max_tokens=1200)
        if call["status"] != "ok":
            print(f"ERROR {str(call.get('error'))[:120]}")
            new_rows.append(
                {
                    "model_id": mid,
                    "benchmark_id": "reverse_prompt_vision",
                    "status": "error",
                    "score": 0,
                    "latency": call["latency"],
                    "prompt_tokens": call.get("prompt_tokens") or 0,
                    "completion_tokens": call.get("completion_tokens") or 0,
                    "total_tokens": call.get("total_tokens") or 0,
                    "estimated_cost_usd": 0.0,
                    "raw_response": call.get("raw_response") or "",
                    "error": call.get("error"),
                    "metrics": {"supports_vision": True},
                }
            )
            time.sleep(0.8)
            continue

        model_cost = rb.estimate_cost(
            mid, call["prompt_tokens"], call["completion_tokens"], pricing
        )
        print(f"got {call['completion_tokens']} tok, judging ...", end=" ", flush=True)
        judged = judge_reverse_prompt(
            api_key, source_prompt, checklist, call["raw_response"], pricing
        )
        total_cost = round(model_cost + float(judged.get("judge_cost_usd") or 0), 6)
        print(
            f"score={judged['score']} hit_rate={judged.get('hit_rate')} "
            f"cost=${total_cost:.4f}"
        )
        row = {
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
                "judge_model": JUDGE_MODEL,
                "judge_status": judged.get("judge_status"),
                "judge_cost_usd": judged.get("judge_cost_usd"),
                "model_only_cost_usd": model_cost,
            },
        }
        new_rows.append(row)
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

    # save reconstructions side file
    recon_path = VISION_DIR / "reconstructions.json"
    recon_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_image": meta.get("image_path"),
                "image_model": meta.get("image_model"),
                "source_prompt": source_prompt,
                "judge_model": JUDGE_MODEL,
                "results": reconstructions,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {recon_path}")

    data = merge_results(new_rows, bench_defs)
    # summary
    vd = [r for r in new_rows if r["benchmark_id"] == "value_density" and r["status"] == "ok"]
    rp = [r for r in new_rows if r["benchmark_id"] == "reverse_prompt_vision" and r["status"] == "ok"]
    sk = [r for r in new_rows if r["benchmark_id"] == "reverse_prompt_vision" and r["status"] == "skipped"]
    print("\n=== SUMMARY ===")
    print(f"value_density ok: {len(vd)}/{n_models}")
    if vd:
        best = max(vd, key=lambda r: (r.get("metrics") or {}).get("value_per_1k_tokens") or 0)
        print(
            f"  best value/1k: {best['model_id']} "
            f"{(best.get('metrics') or {}).get('value_per_1k_tokens')} "
            f"(score={best['score']}, tok={best['total_tokens']})"
        )
    print(f"reverse_prompt ok: {len(rp)}  skipped(non-vision): {len(sk)}")
    if rp:
        best = max(rp, key=lambda r: r.get("score") or 0)
        print(f"  best reverse-prompt: {best['model_id']} score={best['score']}")
    print(f"results file total rows: {len(data['results'])} cost=${data['total_estimated_cost_usd']}")


if __name__ == "__main__":
    main()
