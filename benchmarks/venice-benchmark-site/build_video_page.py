#!/usr/bin/env python3
"""Build video-benchmark.html — three categorized sections, video players, newest-first."""
import os, re, json, urllib.request, datetime

SITE = os.path.expanduser("~/.openclaw/workspace/benchmarks/venice-benchmark-site")
OUTDIR = os.path.join(SITE, "assets", "video-benchmark")
manifest = json.load(open(os.path.join(OUTDIR, "manifest.json")))
matrix = json.load(open("data/video_matrix.json"))

req = urllib.request.Request("https://api.venice.ai/api/v1/models?type=video")
cat = json.load(urllib.request.urlopen(req, timeout=60))
cat = cat.get("data", cat) if isinstance(cat, dict) else cat
created = {m["id"]: m.get("created", 0) for m in cat}
date_of = {m["id"]: datetime.datetime.fromtimestamp(m.get("created", 0)).strftime("%b %Y") for m in cat}

models = {}
for r in manifest:
    models.setdefault(r["model"], {})[r["pid"]] = r

CATS = [("1-cinematic", "Realism", "Realism test — Golden Retriever at Golden Hour"),
        ("2-creative", "Creative", "Creative test — Tiny Astronaut on a Galaxy Puddle"),
        ("3-motion", "Image-to-Video", "Image-to-Video — Motion from the Shared Portrait"),
        ("4-lincoln", "Reference-to-Video", "Reference-to-Video — Famous-Person Identity Test")]
PROMPTS = matrix.get("t2v_prompts", {})
I2V_PROMPT = matrix["i2v_prompt"]
R2V_PROMPT = matrix["r2v_prompt"]

sorted_models = sorted(models.keys(), key=lambda mid: created.get(mid, 0), reverse=True)

img = open(os.path.join(SITE, "image-benchmark.html")).read()
sidenav = re.search(r'<nav class="sidenav".*?</nav>', img, re.S).group(0)
sidenav = sidenav.replace('aria-current="page"', '').replace(' class="is-current"', '')
head = re.search(r'(<head>.*?</head>)', img, re.S).group(1)
head = head.replace('<title>Image Models</title>', '<title>Video Models</title>')
footer = re.search(r'(<footer class="site-footer".*?</footer>)', img, re.S).group(1)

def cell(pid, r):
    label = dict((c[0], c[1]) for c in CATS)[pid]
    if r and r.get("ok") and r.get("file"):
        rel = f"assets/video-benchmark/{r['file']}"
        ar = r.get("resolution") or "native"
        dur = r.get("duration") or "default"
        return (f'<figure class="im-cell"><video controls preload="metadata" src="{rel}" '
                f'style="width:100%;border-radius:10px;background:#000;display:block"></video>'
                f'<figcaption>{label} <span class="ar">{ar} · {dur}</span></figcaption></figure>')
    if r and not r.get("ok"):
        return (f'<figure class="im-cell"><div style="padding:2rem 1rem;color:var(--text-dim);'
                f'text-align:center">failed: {(r.get("err") or "error")[:80]}</div>'
                f'<figcaption>{label} — failed</figcaption></figure>')
    return (f'<figure class="im-cell"><div style="padding:2rem 1rem;color:var(--text-faint);'
            f'text-align:center">queued for a later tranche</div>'
            f'<figcaption>{label} — pending</figcaption></figure>')

model_sections = []
for mid in sorted_models:
    cats = models[mid]
    cells = []
    for pid, label, _desc in CATS:
        cells.append(cell(pid, cats.get(pid)))
    date = date_of.get(mid, "—")
    model_sections.append(f"""
  <section class="im-model">
    <h2 class="im-name">{mid} <span class="im-date">{date}</span></h2>
    <div class="im-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem">
      {''.join(cells)}
    </div>
  </section>""")

prompt_blocks = []
for pid, label, _ in CATS:
    pt = PROMPTS.get(pid) or (I2V_PROMPT if pid == "3-motion" else (R2V_PROMPT if pid == "4-lincoln" else ""))
    if pt:
        prompt_blocks.append(f"<p><strong>{label}:</strong> {pt}</p>")

html = f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
  <div class="gpu-bg" aria-hidden="true"></div>
  {sidenav}
  <main style="position:relative;z-index:1;">
  <div class="container">
    <header style="padding: 3.5rem 0 2rem;">
      <span class="eyebrow">Venice API Evaluation</span>
      <h1>Video Models</h1>
      <p>Every text-to-video, image-to-video and reference-to-video model on the Venice catalog, each generating at its minimum duration and resolution — categorized by model type, so each is tested for what it actually does.</p>
    </header>

    <section class="im-prompts" style="margin-bottom:2rem">
      <h2 style="font-size:1.4rem;margin-bottom:0.8rem">Fixed prompts — identical for every model in the category</h2>
      {''.join(prompt_blocks)}
    </section>

    {''.join(model_sections)}
  </div>
  </main>
  {footer}
</body>
</html>
"""

open(os.path.join(SITE, "video-benchmark.html"), "w").write(html)
print(f"Wrote video-benchmark.html ({len(html)} bytes, {len(sorted_models)} models)")
