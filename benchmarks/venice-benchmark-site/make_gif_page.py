#!/usr/bin/env python3
"""Build gif-arena.html: side-by-side rendered GIFs + scores + source links.

Reads data/gif_arena/*.gif (rendered), *_meta.json (prompt/model info) and
scores.json (judge output). Ranks by gif_score (or by file size when no scores
exist), crowns the winner, and links each model's profile page.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARENA = ROOT / "data" / "gif_arena"
OUT = ROOT / "gif-arena.html"

# canonical display names from the scored registry (fall back to slug)
REGISTRY = {}
try:
    import sys
    sys.path.insert(0, str(ROOT))
    from model_registry import MODELS
    REGISTRY = {m["id"]: m["display"] for m in MODELS}
except Exception:
    pass


def display_name(slug: str) -> str:
    mid = slug.replace("-", "_")
    if mid in REGISTRY:
        return REGISTRY[mid]
    # registry ids already contain dashes for some entries
    if slug in REGISTRY:
        return REGISTRY[slug]
    return slug.replace("-", " ").title()

AXES = [
    ("alpaca_recognizability", "Alpaca-ness"),
    ("dance_quality", "Dance quality"),
    ("technical_polish", "Polish"),
    ("creativity", "Creativity"),
    ("code_quality", "Code"),
]

def esc(s):
    return html.escape(str(s))


def main() -> int:
    scores = {}
    sp = ARENA / "scores.json"
    if sp.exists():
        scores = json.loads(sp.read_text(encoding="utf-8"))
    entries = []
    for gif in sorted(ARENA.glob("*.gif")):
        slug = gif.stem
        meta = {}
        mp = ARENA / f"{slug}.meta.json"
        if mp.exists():
            meta = json.loads(mp.read_text(encoding="utf-8"))
        score = scores.get(slug, {})
        vi = sum(score.get(k, 0) for k in
                 ["alpaca_recognizability", "dance_quality", "technical_polish",
                  "creativity", "code_quality"])
        entries.append({
            "slug": slug,
            "display": meta.get("display") or display_name(slug),
            "gif": gif,
            "size": gif.stat().st_size,
            "score": score,
            "composite": score.get("gif_score", 0),
            "axis_sum": vi,
            "meta": meta,
        })
    entries.sort(key=lambda e: -e["composite"])
    if not entries:
        print("gif-arena: no GIFs found — run run_gif_track.py + render_gifs.py first")
        return 1

    winner = entries[0]
    cards = ""
    for i, e in enumerate(entries):
        is_win = i == 0 and e["composite"] > 0
        gif_rel = f"data/gif_arena/{e['slug']}.gif"
        profile = f"models/{e['slug']}.html"
        has_profile = (ROOT / profile).exists()
        score_rows = ""
        if e["score"].get("gif_score") is not None:
            for k, label in AXES:
                v = e["score"].get(k)
                if v is None:
                    continue
                score_rows += (
                    f'<div class="g-stats"><span>{label}</span>'
                    f'<div class="g-bar"><i style="width:{min(100, v)}%"></i></div>'
                    f'<b>{v:.0f}</b></div>')
            comp = e["composite"]
            score_rows += (
                f'<div class="g-stats g-total"><span>GIF Score</span>'
                f'<div class="g-bar"><i style="width:{min(100, comp)}%"></i></div>'
                f'<b>{comp:.1f}</b></div>')
        else:
            score_rows = '<p class="muted" style="font-size:.85rem;margin:.4rem 0 0">Not judged yet — scores added once the LLM judge runs.</p>'

        crown = '<span class="g-crown">👑</span>' if is_win else ""
        prof = (f'<span class="g-src"><a href="{profile}">VivIndex profile →</a></span>'
                if has_profile else "")
        src_link = f'<a href="data/gif_arena/{e["slug"]}.html" target="_blank" rel="noopener">source HTML ↗</a>'

        cards += f'''
<article class="g-card{' g-win' if is_win else ''}">
  <header class="g-head">
    <h3>{crown}{esc(e['display'])}</h3>
    <span class="g-meta muted">{e['size']/1024:.0f} KB GIF · {esc(e['score'].get('mode',''))}</span>
  </header>
  <img class="g-gif" src="{gif_rel}" alt="{esc(e['display'])} dancing-alpaca animation" loading="lazy" />
  <div class="g-actions">{src_link} {prof}</div>
  {score_rows}
</article>'''

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>GIF Arena — BenchmarkViv</title>
<meta name="description" content="Code-to-GIF benchmark: models generate a dancing-alpaca HTML animation, rendered and judged side by side." />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="assets/styles.css?v=15" />
<style>
  .g-hero {{ padding: calc(var(--nav-h) + 2.5rem) 0 2rem; }}
  .g-hero h1 {{ font-size: clamp(1.6rem, 4.5vw, 2.4rem); }}
  .g-sub {{ color: var(--text-dim); margin-top: .45rem; max-width: 68ch; }}
  .g-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.1rem; margin-top: 1.6rem; }}
  .g-card {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 16px; padding: 1.1rem; box-shadow: var(--shadow); }}
  .g-win {{ border: 2px solid var(--gold); box-shadow: 0 6px 22px rgba(217,164,65,.22); }}
  .g-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: .6rem; }}
  .g-head h3 {{ font-size: 1.02rem; }}
  .g-crown {{ filter: drop-shadow(0 2px 3px rgba(184,134,11,.5)); }}
  .g-meta {{ font-size: .78rem; }}
  .g-gif {{ width: 100%; border-radius: 12px; border: 1px solid var(--rule); margin: .7rem 0 .5rem; background: #fff; }}
  .g-actions {{ display: flex; gap: 1rem; font: 600 .8rem var(--font-mono); margin-bottom: .35rem; }}
  .g-actions a {{ color: var(--cobalt-dark); }}
  .g-stats {{ display: grid; grid-template-columns: 90px 1fr 32px; gap: .55rem; align-items: center; font-size: .8rem; padding: .18rem 0; }}
  .g-stats b {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .g-bar {{ height: 8px; background: var(--rule); border-radius: 999px; overflow: hidden; }}
  .g-bar i {{ display: block; height: 100%; background: linear-gradient(90deg, var(--cobalt-dark), var(--cobalt)); }}
  .g-total {{ border-top: 1px solid var(--rule); margin-top: .3rem; padding-top: .45rem; font-weight: 700; }}
  .g-total .g-bar i {{ background: linear-gradient(90deg, var(--gold-deep, #B8860B), var(--gold)); }}
  .g-prompt {{ margin-top: 1.8rem; padding: 1.1rem 1.2rem; border: 1px dashed var(--rule); border-radius: 14px; font-size: .9rem; color: var(--text-dim); }}
  @media (max-width: 560px) {{ .g-stats {{ grid-template-columns: 76px 1fr 30px; }} }}
</style>
</head>
<body>
<nav class="navbar vt-nav"><div class="container">
  <a href="index.html" class="nav-logo">Benchmark<span>Viv</span></a>
  <ul class="nav-links" id="siteNav">
    <li><a href="index.html#leaderboard">Leaderboard</a></li>
    <li><a href="index.html#tracks">Tracks</a></li>
    <li><a href="vision.html">Vision</a></li>
    <li><a href="trends.html">Trends</a></li>
    <li><a href="compare.html">Compare</a></li>
    <li><a href="gif-arena.html" class="active">GIF Arena</a></li>
    <li><a href="experimental-design.html">Design</a></li>
    <li><a href="about.html">About</a></li>
  </ul>
  <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
</div></nav>

<main class="container">
  <section class="g-hero">
    <h1>GIF Arena 🦙💃</h1>
    <p class="g-sub">The code-to-GIF track: every model got the same prompt — build a self-contained HTML page of a cute alpaca dancing, no external assets, looping forever. Each entry was rendered in headless Chrome, captured to frames, and encoded to a real GIF. Judge the dancing for yourself.</p>
  </section>

  <section class="g-grid">{cards}</section>

  <div class="g-prompt">
    <b>The challenge prompt:</b> “Create a single self-contained HTML document (no external files, no CDN, no images) that shows a cute alpaca dancing. Make it genuinely impressive: a recognizable fluffy alpaca with a long neck, ears, and pom-pom tail, performing a lively dance with body bounces, limb waves, and a fun loop. Use inline CSS and JavaScript animation. The page should animate on load forever… Output ONLY the complete HTML document.”
  </div>
</main>
<script>document.querySelectorAll('.navbar .nav-toggle').forEach(b=>b.addEventListener('click',()=>{{const l=document.getElementById('siteNav');l.classList.toggle('open');b.setAttribute('aria-expanded',String(l.classList.contains('open')));}}));</script>
</body>
</html>'''
    OUT.write_text(page, encoding="utf-8")
    print(f"gif-arena.html written ({len(entries)} entries, winner: {winner['slug']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
