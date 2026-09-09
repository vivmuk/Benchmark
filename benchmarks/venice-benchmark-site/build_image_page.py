#!/usr/bin/env python3
"""Build image-benchmark.html — matches site design, sorted by release date desc."""
import os, json

SITE = os.path.expanduser("~/.openclaw/workspace/benchmarks/venice-benchmark-site")
OUTDIR = os.path.join(SITE, "assets", "image-benchmark")
manifest = json.load(open(os.path.join(OUTDIR, "manifest.json")))
created = json.load(open("/tmp/image_created.json"))

from collections import OrderedDict
models = OrderedDict()
for r in manifest:
    models.setdefault(r["model"], {})[r["cat"]] = r

CATS = ["1-infographic", "2-portrait", "3-ceos"]
CAT_TITLES = {
    "1-infographic": "Infographic — History of Generative AI (watercolor)",
    "2-portrait": "Portrait — Girl in the Sands",
    "3-ceos": "Group — CEOs at a Retreat",
}
CAT_SHORT = {
    "1-infographic": "Infographic",
    "2-portrait": "Portrait",
    "3-ceos": "CEOs",
}
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

# Sort models by created timestamp descending (newest first)
def sort_key(mid):
    return created.get(mid, {}).get("created") or 0
sorted_models = sorted(models.keys(), key=sort_key, reverse=True)

rows = []
for model in sorted_models:
    cats = models[model]
    meta = created.get(model, {})
    date = meta.get("date") or "—"
    cells = []
    for cat in CATS:
        r = cats.get(cat)
        if r and r.get("ok"):
            rel = f"assets/image-benchmark/{r['file']}"
            ar = r.get("aspect_ratio") or "default"
            cells.append(
                f'<figure class="im-cell">'
                f'<img loading="lazy" src="{rel}" alt="{model} {cat}" '
                f'data-full="{rel}" data-label="{model} — {CAT_SHORT[cat]}">'
                f'<figcaption>{CAT_SHORT[cat]} <span class="ar">{ar}</span></figcaption>'
                f'</figure>'
            )
        else:
            cells.append(
                f'<figure class="im-cell fail"><div class="x">✕</div>'
                f'<figcaption>{CAT_SHORT[cat]} — failed</figcaption></figure>'
            )
    rows.append(
        f'<section class="im-model">'
        f'<h2 class="im-name">{model} <span class="im-date">{date}</span></h2>'
        f'<div class="im-row">{"".join(cells)}</div></section>'
    )

n_ok = sum(1 for r in manifest if r.get("ok"))
n_fail = sum(1 for r in manifest if not r.get("ok"))

prompt_cards = ""
for cat in CATS:
    prompt_cards += (
        f'<details class="im-prompt" open><summary>{CAT_SHORT[cat]} — {CAT_TITLES[cat]}</summary>'
        f'<p>{PROMPTS[cat]}</p></details>'
    )

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Image Models — BenchmarkViv</title>
<meta name="description" content="Side-by-side image benchmark: three fixed prompts rendered by every Venice API text-to-image model, ordered by release date." />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="assets/styles.css?v=17" />
<style>
  .im-hero {{ padding: calc(var(--nav-h) + 2.5rem) 0 1.5rem; border-bottom: 1px solid var(--rule); }}
  .im-hero h1 {{ font-size: clamp(1.6rem, 4.5vw, 2.5rem); margin-bottom: .4rem; }}
  .im-sub {{ color: var(--text-dim); max-width: 68ch; line-height: 1.55; font-size: 1rem; }}
  .im-sub strong {{ color: var(--text); }}
  .im-prompts {{ margin-top: 1.6rem; display: flex; flex-direction: column; gap: .7rem; }}
  .im-prompts h2 {{ font: 600 .8rem var(--font-mono); text-transform: uppercase; letter-spacing: .06em; color: var(--text-dim); margin: 0; }}
  .im-prompt {{ background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); padding: .75rem 1rem; box-shadow: var(--shadow); }}
  .im-prompt summary {{ cursor: pointer; font-weight: 600; color: var(--text); font-size: .92rem; }}
  .im-prompt p {{ margin: .55rem 0 0; font: 400 .86rem/1.6 var(--font-mono); color: var(--text-dim); }}
  .im-meta {{ margin: 1.3rem 0; font: 500 .86rem var(--font-mono); color: var(--text-dim); }}
  .im-meta b {{ color: var(--text); }}
  .im-model {{ padding: 1.6rem 0; border-bottom: 1px solid var(--rule); }}
  .im-name {{ margin: 0 0 .9rem; font: 700 1.02rem var(--font-mono); color: var(--text); display: flex; align-items: baseline; gap: .7rem; flex-wrap: wrap; }}
  .im-date {{ font: 500 .76rem var(--font-mono); color: var(--cobalt); background: var(--acid-soft); padding: .15rem .55rem; border-radius: 999px; }}
  .im-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; }}
  .im-cell {{ margin: 0; }}
  .im-cell img {{
    width: 100%; height: auto; border-radius: var(--radius); display: block; cursor: zoom-in;
    box-shadow: var(--shadow); background: var(--surface); border: 1px solid var(--rule);
    transition: transform .15s var(--ease), box-shadow .15s var(--ease);
  }}
  .im-cell img:hover {{ transform: scale(1.015); box-shadow: 0 12px 30px -15px rgba(18,18,26,.4); }}
  .im-cell figcaption {{ font: 500 .76rem var(--font-mono); color: var(--text-dim); margin-top: .4rem; text-align: center; }}
  .im-cell figcaption .ar {{ color: var(--cobalt); font-weight: 700; }}
  .im-cell.fail .x {{
    aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center;
    background: #fdecec; color: #c0392b; font-size: 2rem; border-radius: var(--radius); border: 1px solid var(--rule);
  }}
  /* lightbox */
  #lb {{ display: none; position: fixed; inset: 0; background: rgba(10,10,18,.93); z-index: 9999;
    overflow: hidden; touch-action: none; }}
  #lb.open {{ display: flex; flex-direction: column; align-items: center; justify-content: center; }}
  #lb img {{ max-width: 100%; max-height: 100%; user-select: none; -webkit-user-drag: none;
    transform-origin: center center; cursor: grab; transition: transform .08s linear; border-radius: 2px; }}
  #lb img.dragging {{ cursor: grabbing; transition: none; }}
  #lb .lb-label {{ position: absolute; top: 16px; left: 18px; color: #fff; font: 500 .84rem var(--font-mono);
    background: rgba(0,0,0,.5); padding: .32rem .65rem; border-radius: 6px; }}
  #lb .lb-close {{ position: absolute; top: 12px; right: 18px; color: #fff; font-size: 2rem; cursor: pointer;
    background: none; border: none; line-height: 1; padding: .2rem .5rem; }}
  #lb .lb-hint {{ position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%); color: #ddd;
    font: 400 .76rem var(--font-mono); background: rgba(0,0,0,.5); padding: .3rem .7rem; border-radius: 20px; white-space: nowrap; }}
  @media (max-width: 720px) {{
    .im-row {{ grid-template-columns: 1fr; }}
    .lb-hint {{ white-space: normal; text-align: center; }}
  }}
</style>
</head>
<body>
<nav class="navbar vt-nav">
  <div class="container">
    <a href="index.html" class="nav-logo">Benchmark<span>Viv</span></a>
    <ul class="nav-links" id="siteNav">
      <li><a href="index.html#leaderboard">Leaderboard</a></li>
      <li><a href="index.html#tracks">Tracks</a></li>
      <li><a href="vision.html">Vision</a></li>
      <li><a href="trends.html">Trends</a></li>
      <li><a href="compare.html">Compare</a></li>
      <li><a href="evolution.html">Evolution</a></li>
      <li><a href="gif-arena.html">GIF Arena</a></li>
      <li><a href="image-benchmark.html" class="active">Image Models</a></li>
      <li><a href="system-prompt.html">System Prompts</a></li>
      <li><a href="prompt-lab.html">Prompt Lab</a></li>
      <li><a href="experimental-design.html">Design</a></li>
      <li><a href="about.html">About</a></li>
    </ul>
    <a href="experimental-design.html" class="nav-cta">Experimental Design</a>
    <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</nav>

<main class="container">
  <section class="im-hero">
    <h1>Image Models</h1>
    <p class="im-sub">Three <strong>fixed prompts</strong> rendered by every text-to-image model in the Venice API, ordered by <strong>release date (newest first)</strong>. Click any image to zoom &amp; pan.</p>
    <div class="im-prompts">
      <h2>Fixed prompts — identical for every model</h2>
      {prompt_cards}
    </div>
    <div class="im-meta"><b>{len(sorted_models)} models</b> · <b>{n_ok} images</b> generated · <b>{n_fail}</b> failed</div>
  </section>

  {''.join(rows)}
</main>

<div id="lb">
  <button class="lb-close" aria-label="Close">×</button>
  <span class="lb-label"></span>
  <img alt="zoom">
  <span class="lb-hint">Scroll to zoom · drag to pan · double-click to reset · Esc to close</span>
</div>

<footer class="site-footer">
  <div class="container">
    <div class="footer-logo">Benchmark<span>Viv</span></div>
    <p>Independent benchmark showcase for Venice API models.</p>
    <div class="footer-links">
      <a href="experimental-design.html">Experimental Design</a>
      <a href="index.html#leaderboard">Leaderboard</a>
    </div>
  </div>
</footer>

<script src="assets/app.js?v=14"></script>
<script>
(function(){{
  var lb = document.getElementById('lb');
  var img = lb.querySelector('img');
  var label = lb.querySelector('.lb-label');
  var close = lb.querySelector('.lb-close');
  var scale = 1, tx = 0, ty = 0;
  var dragging = false, sx = 0, sy = 0, stx = 0, sty = 0;

  function apply() {{ img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')'; }}
  function reset() {{ scale = 1; tx = 0; ty = 0; apply(); }}
  function open(src, lab) {{ img.src = src; label.textContent = lab; reset(); lb.classList.add('open'); }}
  function closeLb() {{ lb.classList.remove('open'); }}

  document.querySelectorAll('.im-cell img').forEach(function(el){{
    el.addEventListener('click', function(){{
      open(el.dataset.full || el.src, el.dataset.label || '');
    }});
  }});

  close.addEventListener('click', closeLb);
  lb.addEventListener('click', function(e){{ if (e.target === lb) closeLb(); }});
  document.addEventListener('keydown', function(e){{ if (e.key === 'Escape') closeLb(); }});

  img.addEventListener('wheel', function(e){{
    if (!lb.classList.contains('open')) return;
    e.preventDefault();
    scale = Math.min(8, Math.max(0.5, scale * (e.deltaY < 0 ? 1.15 : 1/1.15)));
    apply();
  }}, {{ passive: false }});

  img.addEventListener('mousedown', function(e){{
    dragging = true; img.classList.add('dragging');
    sx = e.clientX; sy = e.clientY; stx = tx; sty = ty;
  }});
  window.addEventListener('mousemove', function(e){{
    if (!dragging) return;
    tx = stx + (e.clientX - sx); ty = sty + (e.clientY - sy); apply();
  }});
  window.addEventListener('mouseup', function(){{ dragging = false; img.classList.remove('dragging'); }});

  img.addEventListener('touchstart', function(e){{
    if (e.touches.length === 1) {{ dragging = true; sx = e.touches[0].clientX; sy = e.touches[0].clientY; stx = tx; sty = ty; }}
  }});
  window.addEventListener('touchmove', function(e){{
    if (!dragging || e.touches.length !== 1) return;
    tx = stx + (e.touches[0].clientX - sx); ty = sty + (e.touches[0].clientY - sy); apply();
  }}, {{ passive: true }});
  window.addEventListener('touchend', function(){{ dragging = false; }});

  img.addEventListener('dblclick', function(e){{ e.preventDefault(); reset(); }});
}})();
</script>
</body>
</html>
"""

out = os.path.join(SITE, "image-benchmark.html")
with open(out, "w") as f:
    f.write(html)
print(f"Wrote {out} ({len(html)} bytes, {len(sorted_models)} models sorted newest-first, {n_ok} ok / {n_fail} fail)")
print("Top 5:", ", ".join(sorted_models[:5]))
