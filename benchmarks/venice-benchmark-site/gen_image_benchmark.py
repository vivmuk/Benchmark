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
    "1-infographic": (
        "A massive detailed infographic in a whimsical watercolor illustration style, "
        "summarizing the complete history of generative AI from its origins to today. "
        "Hand-painted watercolor aesthetic with soft washes, delicate ink linework and brush textures. "
        "A flowing vertical timeline with illustrated milestones: early neural networks and perceptrons "
        "(1950s-60s), backpropagation and the AI winter, statistical language models, the rise of deep "
        "learning and GANs (2014), transformer attention models (2017), GPT language models, diffusion "
        "image generators, CLIP, multimodal models, and frontier reasoning and video models of today. "
        "Each era marked with a small hand-drawn icon, soft pastel color-coded sections, sweeping arrows, "
        "decorative flourishes and handwritten-style labels. Rich detail, legible text, warm cream paper, "
        "storybook scientific-poster feel, entirely hand-painted watercolor, no photorealism."
    ),
    "2-portrait": (
        "A breathtaking portrait of the most beautiful girl in the world, standing gracefully in golden "
        "desert sands at golden hour. Long flowing hair catching the warm breeze, sun-kissed skin glowing, "
        "soft light wrapping around her, delicate flowing fabric moving with the wind, gentle confident "
        "expression, deep expressive eyes. Windswept sand dunes behind her, warm amber and honey tones, "
        "soft bokeh background, cinematic golden-hour lighting, shallow depth of field, ultra-detailed, "
        "elegant, photorealistic beauty portrait."
    ),
    "3-ceos": (
        "A group portrait of corporate CEOs gathered at a leadership retreat, sitting together in an "
        "elegant mountain lodge with a scenic pine forest and lake backdrop. A diverse group of confident "
        "executives in smart-casual attire, engaged in warm conversation, some smiling and relaxed. "
        "Wood-paneled lodge interior, warm natural light streaming in, professional editorial corporate "
        "photography, candid authentic energy, high detail."
    ),
}

# desired aspect ratios per category, in priority order
CAT_AR = {
    "1-infographic": ["9:16", "3:4", "2:3", "1:1"],
    "2-portrait": ["2:3", "3:4", "9:16", "1:1"],
    "3-ceos": ["16:9", "3:2", "21:9", "1:1"],
}

def pick_ar(model_ar, cat_key):
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
