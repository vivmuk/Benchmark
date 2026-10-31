#!/usr/bin/env python3
import os, json, base64, time
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = os.environ["VENICE_API_KEY"]
API = "https://api.venice.ai/api/v1/image/generate"
SITE = os.path.expanduser("~/.openclaw/workspace/benchmarks/venice-benchmark-site")
OUTDIR = os.path.join(SITE, "assets", "image-benchmark")

constraints = {o["id"]: o for o in json.load(open("/tmp/image_constraints.json"))}

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
    "3-ceos": (
        "A group portrait of corporate CEOs gathered at a leadership retreat, sitting together in an "
        "elegant mountain lodge with a scenic pine forest and lake backdrop. A diverse group of confident "
        "executives in smart-casual attire, engaged in warm conversation, some smiling and relaxed. "
        "Wood-paneled lodge interior, warm natural light streaming in, professional editorial corporate "
        "photography, candid authentic energy, high detail."
    ),
}

RETRY = [
    ("gpt-image-2", "1-infographic"),
    ("luma-uni-1", "1-infographic"),
    ("luma-uni-1-max", "1-infographic"),
    ("luma-uni-1-max", "3-ceos"),
]

import urllib.request

def gen(model, cat_key):
    c = constraints[model]
    prompt = PROMPTS[cat_key]
    plim = c.get("plim") or 10000
    if len(prompt) > plim:
        prompt = prompt[:plim]
    # try 1:1 first (faster/more reliable for these slow models), then 9:16
    ars = ["1:1", "9:16"] if cat_key == "1-infographic" else ["1:1", "16:9"]
    ars = [a for a in ars if a in (c.get("ar") or [])]
    if not ars:
        ars = [None]
    for attempt, ar in enumerate(ars):
        body = {"model": model, "prompt": prompt}
        if ar:
            body["aspect_ratio"] = ar
        req = urllib.request.Request(API, data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.load(r)
            imgs = data.get("images") or []
            if imgs:
                b = imgs[0]
                if "," in b:
                    b = b.split(",", 1)[1]
                raw = base64.b64decode(b)
                fname = f"{model}-{cat_key}.jpg"
                open(os.path.join(OUTDIR, fname), "wb").write(raw)
                print(f"[OK] {model} {cat_key} ar={ar} size={len(raw)}", flush=True)
                return {"model": model, "cat": cat_key, "file": fname, "aspect_ratio": ar, "ok": True}
        except Exception as e:
            print(f"[retry {attempt}] {model} {cat_key} ar={ar}: {e}", flush=True)
            continue
    print(f"[STILL FAIL] {model} {cat_key}", flush=True)
    return {"model": model, "cat": cat_key, "file": None, "aspect_ratio": None, "ok": False}

results = []
with ThreadPoolExecutor(max_workers=4) as ex:
    futs = [ex.submit(gen, m, c) for m, c in RETRY]
    for f in as_completed(futs):
        results.append(f.result())

# merge into manifest
man = json.load(open(os.path.join(OUTDIR, "manifest.json")))
for r in results:
    # remove old failed entry
    man = [x for x in man if not (x["model"] == r["model"] and x["cat"] == r["cat"] and not x.get("ok"))]
    man.append(r)
json.dump(man, open(os.path.join(OUTDIR, "manifest.json"), "w"), indent=1)
print("retry results:", [(r['model'], r['cat'], r['ok']) for r in results])
