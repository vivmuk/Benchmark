#!/usr/bin/env python3
"""Build vision.html from reverse-prompt fixture + reconstructions."""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
META = json.loads((ROOT / "data/vision/reverse_prompt_meta.json").read_text(encoding="utf-8"))
RECON = json.loads((ROOT / "data/vision/reconstructions.json").read_text(encoding="utf-8"))
RESULTS = json.loads((ROOT / "data/results.json").read_text(encoding="utf-8"))

SOURCE_PROMPT = META["source_prompt"]
INSTRUCTION = META["reverse_prompt_instruction"]
CHECKLIST = META["checklist"]
IMAGE_MODEL = META.get("image_model", "nano-banana-2")
JUDGE_MODEL = META.get("judge_model") or RECON.get("judge_model") or "openai-gpt-56-luna"
GENERATED = RECON.get("generated_at") or META.get("generated_at") or ""

# Prefer web jpeg; fall back to original png
WEB_IMG = "data/vision/reverse_prompt_source.web.jpg"
if not (ROOT / WEB_IMG).exists():
    WEB_IMG = "data/vision/reverse_prompt_source.png"
FULL_IMG = "data/vision/reverse_prompt_source.png"


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def score_class(score) -> str:
    if score is None:
        return "score-na"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "score-na"
    if s >= 80:
        return "score-high"
    if s >= 50:
        return "score-mid"
    if s > 0:
        return "score-low"
    return "score-zero"


def hits_chips(hits: dict | None, checklist: list) -> str:
    if not isinstance(hits, dict) or not hits:
        return '<p class="muted">No per-attribute hit map for this run.</p>'
    parts = []
    for item in checklist:
        cid = item["id"]
        desc = item["desc"]
        val = hits.get(cid)
        if val is True:
            cls, mark = "hit-yes", "hit"
        elif val is False:
            cls, mark = "hit-no", "miss"
        else:
            cls, mark = "hit-na", "n/a"
        parts.append(
            f'<span class="hit-chip {cls}" title="{esc(desc)}">'
            f'<code>{esc(cid)}</code> <em>{esc(mark)}</em></span>'
        )
    return '<div class="hit-grid">' + "".join(parts) + "</div>"


# reconstructions sorted by score desc
recon_rows = sorted(
    RECON.get("results") or [],
    key=lambda r: (-(r.get("score") if isinstance(r.get("score"), (int, float)) else -1), r.get("model_id") or ""),
)

# skipped non-vision from results.json
skipped = [
    r
    for r in RESULTS.get("results") or []
    if r.get("benchmark_id") == "reverse_prompt_vision" and r.get("status") == "skipped"
]

checklist_html = "\n".join(
    f'<li><code>{esc(c["id"])}</code> <span>{esc(c["desc"])}</span></li>'
    for c in CHECKLIST
)

recon_cards = []
for i, r in enumerate(recon_rows, 1):
    mid = r.get("model_id") or ""
    disp = r.get("display") or mid
    score = r.get("score")
    hit_rate = r.get("hit_rate")
    prompt = r.get("reconstructed_prompt") or ""
    hits = r.get("hits") if isinstance(r.get("hits"), dict) else {}
    hit_n = sum(1 for v in hits.values() if v is True) if hits else None
    hit_tot = len(CHECKLIST)
    meta_bits = []
    if score is not None:
        meta_bits.append(f"score <strong>{esc(score)}</strong>")
    if hit_rate is not None:
        meta_bits.append(f"hit rate <strong>{esc(round(float(hit_rate) * 100, 1))}%</strong>")
    if hit_n is not None:
        meta_bits.append(f"hits <strong>{hit_n}/{hit_tot}</strong>")
    meta_line = " · ".join(meta_bits) if meta_bits else ""
    recon_cards.append(
        f"""
      <article class="vision-card reveal" id="recon-{esc(mid)}">
        <header class="vision-card-head">
          <div>
            <span class="rank">#{i:02d}</span>
            <h3>{esc(disp)}</h3>
            <p class="mono-id">{esc(mid)}</p>
          </div>
          <div class="score-pill {score_class(score)}">{esc(score if score is not None else "n/a")}</div>
        </header>
        <p class="vision-card-meta">{meta_line}</p>
        <h4>Reconstructed prompt</h4>
        <pre class="prompt-block">{esc(prompt)}</pre>
        <h4>Checklist hits</h4>
        {hits_chips(hits, CHECKLIST)}
      </article>"""
    )

skipped_html = ""
if skipped:
    items = "".join(
        f"<li><code>{esc(r.get('model_id'))}</code> — {esc(r.get('error') or 'skipped')}</li>"
        for r in skipped
    )
    skipped_html = f"""
    <div class="card vision-note">
      <h3>Not run (no vision)</h3>
      <ul class="plain-list">{items}</ul>
      <p class="muted">These models stay in results.json as <code>status=skipped</code>, not zero-scored.</p>
    </div>"""

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="BenchmarkViv Vision gallery: nano-banana-2 source image, full generation prompt, reverse-prompt instruction, attribute checklist, and every model reconstruction." />
  <title>Vision Gallery · BenchmarkViv</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="assets/styles.css?v=8" />
</head>
<body>
  <div class="gpu-bg" aria-hidden="true"><canvas id="gpuCanvas"></canvas></div>

  <nav class="navbar vt-nav">
    <div class="container">
      <a href="index.html" class="nav-logo">Benchmark<span>Viv</span></a>
      <ul class="nav-links" id="siteNav">
        <li><a href="index.html#leaderboard">Leaderboard</a></li>
        <li><a href="index.html#tracks">Tracks</a></li>
        <li><a href="vision.html" class="is-current" aria-current="page">Vision</a></li>
        <li><a href="experimental-design.html">Design</a></li>
        <li><a href="about.html">About</a></li>
      </ul>
      <a href="index.html#leaderboard" class="nav-cta">Leaderboard</a>
      <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    </div>
  </nav>

  <header class="hero vt-hero">
    <div class="hero-backdrop"></div>
    <div class="container hero-content">
      <span class="eyebrow">Reverse-Prompt Vision</span>
      <h1>Source image, every prompt, every reconstruction</h1>
      <p>
        One fixed image from <strong>{esc(IMAGE_MODEL)}</strong>. Models never see the source prompt.
        They only see the picture, then write a generation prompt. A judge scores them against a
        {len(CHECKLIST)}-attribute checklist.
      </p>
      <div class="hero-actions">
        <a href="#source-image" class="btn btn-primary">View source image</a>
        <a href="#source-prompt" class="btn btn-ghost">Source prompt</a>
        <a href="#reconstructions" class="btn btn-ghost">Reconstructions</a>
      </div>
      <p class="data-status">Fixture generated {esc(GENERATED)} · judge <code>{esc(JUDGE_MODEL)}</code></p>
    </div>
  </header>

  <section id="source-image">
    <div class="container">
      <div class="section-head">
        <h2>Source image</h2>
        <p>Generated with <code>{esc(IMAGE_MODEL)}</code>. Display copy is web-optimized JPEG; full PNG is linked below.</p>
      </div>
      <figure class="vision-figure card">
        <a href="{esc(FULL_IMG)}" target="_blank" rel="noopener">
          <img src="{esc(WEB_IMG)}" alt="Reverse-prompt source image: surreal pharmaceutical laboratory at twilight generated by {esc(IMAGE_MODEL)}" loading="eager" />
        </a>
        <figcaption>
          <span><code>{esc(WEB_IMG)}</code> (display)</span>
          <span><a href="{esc(FULL_IMG)}">Full PNG</a> · <a href="data/vision/reverse_prompt_meta.json">meta JSON</a></span>
        </figcaption>
      </figure>
    </div>
  </section>

  <section id="prompts">
    <div class="container vision-prompt-grid">
      <article class="card" id="source-prompt">
        <span class="attribute">Image generation prompt</span>
        <h2>Exact source prompt given to {esc(IMAGE_MODEL)}</h2>
        <p class="muted">This is the ground-truth prompt. Models under test do <em>not</em> receive it.</p>
        <pre class="prompt-block">{esc(SOURCE_PROMPT)}</pre>
        <p class="file-ref">Also on disk: <code>data/vision/source_prompt.txt</code></p>
      </article>

      <article class="card" id="reverse-instruction">
        <span class="attribute">Model instruction</span>
        <h2>Exact reverse-prompt instruction</h2>
        <p class="muted">Sent to every vision-capable model with the image (no source prompt).</p>
        <pre class="prompt-block">{esc(INSTRUCTION)}</pre>
      </article>
    </div>
  </section>

  <section id="checklist">
    <div class="container">
      <div class="section-head">
        <h2>Judge checklist ({len(CHECKLIST)} attributes)</h2>
        <p>Judge model <code>{esc(JUDGE_MODEL)}</code> scores reconstructed prompts against these fixed attributes. Hits are independent of prose style.</p>
      </div>
      <div class="card">
        <ol class="checklist-ol">
{checklist_html}
        </ol>
      </div>
    </div>
  </section>

  <section id="reconstructions">
    <div class="container">
      <div class="section-head">
        <h2>Model reconstructions ({len(recon_rows)})</h2>
        <p>Sorted by score. Each card shows the full reconstructed prompt and per-attribute hits when available.</p>
      </div>
      <div class="vision-recon-grid">
        {''.join(recon_cards)}
      </div>
      {skipped_html}
    </div>
  </section>

  <section id="method-note">
    <div class="container">
      <div class="card">
        <h2>How to read this page</h2>
        <ul class="plain-list">
          <li><strong>Source prompt</strong> is the only prompt used to make the image.</li>
          <li><strong>Reverse instruction</strong> is what every model was asked to do with the image alone.</li>
          <li><strong>Checklist</strong> is the scoring rubric (not shown to the model under test).</li>
          <li><strong>Reconstructions</strong> are raw model outputs; judge scores live in <code>data/results.json</code> under <code>reverse_prompt_vision</code>.</li>
          <li>Artifacts: <code>data/vision/</code> (image, meta, reconstructions.json).</li>
        </ul>
      </div>
    </div>
  </section>

  <footer class="footer">
    <div class="container">
      <p>BenchmarkViv Vision · built {esc(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))} · <a href="index.html">Leaderboard</a> · <a href="about.html">About</a></p>
    </div>
  </footer>

  <script src="assets/app.js?v=8"></script>
</body>
</html>
"""

out = ROOT / "vision.html"
out.write_text(page, encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size} bytes)")
print(f"reconstructions: {len(recon_rows)}  checklist: {len(CHECKLIST)}  skipped: {len(skipped)}")
print(f"image: {WEB_IMG}")
