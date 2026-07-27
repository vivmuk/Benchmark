#!/usr/bin/env python3
"""Generate nano-banana-2 images from each reverse-prompt reconstruction.

Uses the SAME image model as the original fixture (nano-banana-2).
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VISION = ROOT / "data" / "vision"
OUT_DIR = VISION / "recon_images"
RECON_PATH = VISION / "reconstructions.json"
META_PATH = VISION / "reverse_prompt_meta.json"
MANIFEST_PATH = VISION / "recon_images_manifest.json"

IMAGE_MODEL = "nano-banana-2"  # must match original fixture
API_URL = "https://api.venice.ai/api/v1/image/generate"
# Original source was cinematic 16:9
ASPECT = "16:9"
RESOLUTION = "1K"  # ~$0.10 each; keep spend bounded
EST_USD = 0.10


def load_key() -> str:
    key = os.environ.get("VENICE_API_KEY") or os.environ.get("VENICE_INFERENCE_KEY")
    if key:
        return key.strip()
    env_path = Path.home() / ".config/railway/venice-rati-key.env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() in {"VENICE_API_KEY", "VENICE_INFERENCE_KEY"}:
                return v.strip().strip('"').strip("'")
    raise SystemExit("No Venice API key in env or venice-rati-key.env")


def generate(api_key: str, prompt: str) -> bytes:
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "aspect_ratio": ASPECT,
        "resolution": RESOLUTION,
        "format": "png",
        "safe_mode": False,
        "hide_watermark": True,
        "return_binary": False,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BenchmarkViv-recon-images/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {err[:500]}") from e

    images = data.get("images") or data.get("data") or []
    if not images:
        raise RuntimeError(f"No images in response keys={list(data.keys())[:12]}")
    first = images[0]
    if isinstance(first, dict):
        b64 = first.get("b64_json") or first.get("base64") or first.get("image")
        if not b64 and first.get("url"):
            with urllib.request.urlopen(first["url"], timeout=120) as r:
                return r.read()
    else:
        b64 = first
    if not b64:
        raise RuntimeError(f"Could not extract image bytes: {str(first)[:200]}")
    if isinstance(b64, str) and b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)


def to_web_jpeg(png_bytes: bytes, max_w: int = 1280) -> bytes:
    from PIL import Image

    im = Image.open(BytesIO(png_bytes)).convert("RGB")
    if im.width > max_w:
        r = max_w / im.width
        im = im.resize((max_w, int(im.height * r)), Image.Resampling.LANCZOS)
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=86, optimize=True)
    return buf.getvalue()


def main() -> None:
    api_key = load_key()
    recon = json.loads(RECON_PATH.read_text(encoding="utf-8"))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    fixture_model = meta.get("image_model")
    if fixture_model and fixture_model != IMAGE_MODEL:
        print(f"WARNING: fixture model is {fixture_model}, script uses {IMAGE_MODEL}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = recon.get("results") or []
    print(f"Generating {len(rows)} images with {IMAGE_MODEL} ({RESOLUTION}, {ASPECT})")
    print(f"Est. cost ~ ${len(rows) * EST_USD:.2f}")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "image_model": IMAGE_MODEL,
        "resolution": RESOLUTION,
        "aspect_ratio": ASPECT,
        "source_fixture_model": fixture_model,
        "estimated_cost_usd_per_image": EST_USD,
        "results": [],
    }
    if MANIFEST_PATH.exists():
        try:
            old = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            by_old = {r.get("model_id"): r for r in old.get("results") or []}
        except Exception:
            by_old = {}
    else:
        by_old = {}

    ok = fail = skip = 0
    total_est = 0.0
    for i, row in enumerate(rows, 1):
        mid = row.get("model_id") or f"model_{i}"
        prompt = (row.get("reconstructed_prompt") or "").strip()
        png_name = f"{mid}.png"
        jpg_name = f"{mid}.web.jpg"
        png_path = OUT_DIR / png_name
        jpg_path = OUT_DIR / jpg_name

        entry = {
            "model_id": mid,
            "display": row.get("display") or mid,
            "score": row.get("score"),
            "prompt_chars": len(prompt),
            "png": f"data/vision/recon_images/{png_name}",
            "web_jpg": f"data/vision/recon_images/{jpg_name}",
            "image_model": IMAGE_MODEL,
            "status": "pending",
        }

        if not prompt:
            entry["status"] = "skipped"
            entry["error"] = "empty reconstructed prompt"
            manifest["results"].append(entry)
            skip += 1
            print(f"[{i}/{len(rows)}] {mid}: SKIP empty prompt")
            continue

        # Resume if PNG exists; make web jpeg if needed
        if png_path.exists() and png_path.stat().st_size > 1000:
            try:
                if not jpg_path.exists() or jpg_path.stat().st_size < 1000:
                    jpg_path.write_bytes(to_web_jpeg(png_path.read_bytes()))
                entry["status"] = "ok"
                entry["resumed"] = True
                entry["png_bytes"] = png_path.stat().st_size
                entry["jpg_bytes"] = jpg_path.stat().st_size
                manifest["results"].append(entry)
                ok += 1
                print(f"[{i}/{len(rows)}] {mid}: RESUME existing")
                continue
            except Exception as exc:
                print(f"[{i}/{len(rows)}] {mid}: resume convert failed ({exc}); regenerating")

        print(f"[{i}/{len(rows)}] {mid}: generating ({len(prompt)} chars)...", flush=True)
        try:
            png_bytes = generate(api_key, prompt)
            png_path.write_bytes(png_bytes)
            jpg_bytes = to_web_jpeg(png_bytes)
            jpg_path.write_bytes(jpg_bytes)
            entry["status"] = "ok"
            entry["png_bytes"] = len(png_bytes)
            entry["jpg_bytes"] = len(jpg_bytes)
            entry["estimated_cost_usd"] = EST_USD
            total_est += EST_USD
            ok += 1
            print(f"  OK png={len(png_bytes)} jpg={len(jpg_bytes)}")
        except Exception as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)[:400]
            fail += 1
            print(f"  FAIL {exc}")
            # brief backoff on rate limits
            if "429" in str(exc):
                time.sleep(8)
        manifest["results"].append(entry)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(1.2)

    manifest["summary"] = {
        "ok": ok,
        "fail": fail,
        "skip": skip,
        "estimated_cost_usd": round(total_est, 4),
    }
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Attach image paths onto reconstructions.json for the gallery builder
    by_img = {r["model_id"]: r for r in manifest["results"] if r.get("status") == "ok"}
    for row in rows:
        mid = row.get("model_id")
        img = by_img.get(mid)
        if img:
            row["generated_image"] = img.get("web_jpg")
            row["generated_image_png"] = img.get("png")
            row["generated_image_model"] = IMAGE_MODEL
        else:
            row.pop("generated_image", None)
            row.pop("generated_image_png", None)
    recon["recon_image_model"] = IMAGE_MODEL
    recon["recon_images_generated_at"] = manifest["generated_at"]
    RECON_PATH.write_text(json.dumps(recon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nDone: ok={ok} fail={fail} skip={skip} est_cost=${total_est:.2f}")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
