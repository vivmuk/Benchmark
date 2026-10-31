#!/usr/bin/env python3
"""Generate 3 comparison images for every Venice text-to-image model."""
import os, json, base64, time, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = os.environ["VENICE_API_KEY"]
API = "https://api.venice.ai/api/v1/image/generate"
SITE = os.path.expanduser("~/.openclaw/workspace/benchmarks/venice-benchmark-site")
OUTDIR = os.path.join(SITE, "assets", "image-benchmark")
os.makedirs(OUTDIR, exist_ok=True)

# Load constraints (built earlier)
constraints = {o["id"]: o for o in json.load(open("/tmp/image_constraints.json"))}
# Exclude non text-to-image models
EXCLUDE = {"bria-bg-remover"}
MODELS = [m for m in constraints if m not in EXCLUDE]

PROMPTS = {
    "1-open": (
        "Create a Watercolor Whimsical style detailed infographic summarizing the complete history of GenAI from 2000 all the way today"
    ),
    "2-portrait": (
        "A breathtaking portrait of the most beautiful girl in the world, standing gracefully in golden "
        "desert sands at golden hour. Long flowing hair catching the warm breeze, sun-kissed skin glowing, "
        "soft light wrapping around her, delicate flowing fabric moving with the wind, gentle confident "
        "expression, deep expressive eyes. Windswept sand dunes behind her, warm amber and honey tones, "
        "soft bokeh background, cinematic golden-hour lighting, shallow depth of field, ultra-detailed, "
        "elegant, photorealistic beauty portrait."
    ),
    "3-open": (
        "A group portrait of corporate CEOs gathered at a leadership retreat, sitting together"
    ),
}

# desired aspect ratios per category; None = omit entirely (model default) for the open intent prompts
CAT_AR = {
    "1-open": None,
    "2-portrait": ["2:3", "3:4", "9:16", "1:1"],
    "3-open": None,
}

def pick_ar(model_ar, cat_key):
    if not CAT_AR.get(cat_key):
        return None
    if not model_ar:
        return None
    for a in CAT_AR[cat_key]:
        if a in model_ar:
            return a
    if "1:1" in model_ar:
        return "1:1"
    return model_ar[0]

def truncate(prompt, plim):
    if plim and len(prompt) > plim:
        return prompt[:plim]
    return prompt

results = []
lock = threading.Lock()

def gen(model, cat_key):
    c = constraints[model]
    prompt = truncate(PROMPTS[cat_key], c.get("plim") or 10000)
    ar = pick_ar(c.get("ar") or [], cat_key)
    body = {"model": model, "prompt": prompt}
    if ar:
        body["aspect_ratio"] = ar
    # default resolution; no override
    import urllib.request
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    last_err = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            imgs = data.get("images") or []
            if not imgs:
                last_err = f"no images in response: {json.dumps(data)[:200]}"
                if attempt == 0:
                    # retry with no aspect ratio
                    body.pop("aspect_ratio", None)
                    req = urllib.request.Request(
                        API, data=json.dumps(body).encode(),
                        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                    )
                    continue
                break
            b = imgs[0]
            if "," in b and b.startswith("data:"):
                b = b.split(",", 1)[1]
            raw = base64.b64decode(b)
            fname = f"{model}-{cat_key}.jpg"
            path = os.path.join(OUTDIR, fname)
            with open(path, "wb") as f:
                f.write(raw)
            with lock:
                results.append({"model": model, "cat": cat_key, "file": fname, "aspect_ratio": ar, "ok": True})
                print(f"[OK] {model} {cat_key} ar={ar} size={len(raw)}", flush=True)
            return
        except Exception as e:
            last_err = str(e)
            if attempt == 0:
                body.pop("aspect_ratio", None)
                req = urllib.request.Request(
                    API, data=json.dumps(body).encode(),
                    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                )
                continue
    with lock:
        results.append({"model": model, "cat": cat_key, "file": None, "aspect_ratio": ar, "ok": False, "err": last_err})
        print(f"[FAIL] {model} {cat_key}: {last_err}", flush=True)

if __name__ == "__main__":
    tasks = [(m, c) for m in MODELS for c in CAT_AR]
    print(f"Starting {len(tasks)} generations across {len(MODELS)} models...", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(gen, m, c) for m, c in tasks]
        for _ in as_completed(futs):
            pass
    ok = [r for r in results if r["ok"]]
    fail = [r for r in results if not r["ok"]]
    json.dump(results, open(os.path.join(OUTDIR, "manifest.json"), "w"), indent=1)
    print(f"\nDONE in {time.time()-t0:.0f}s: {len(ok)} ok, {len(fail)} failed", flush=True)
    if fail:
        print("FAILURES:", flush=True)
        for r in fail:
            print("  ", r["model"], r["cat"], r.get("err"), flush=True)
