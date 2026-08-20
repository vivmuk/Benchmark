#!/usr/bin/env python3
"""Generate one profile page per model from data/results.json.

Outputs models/<slug>.html for every scored model. Pages share the site's
stylesheet (assets/styles.css) and follow the unified brand palette. The #1
model gets the same gold crown treatment as everywhere else.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "results.json"
OUT = ROOT / "models"

INK   = "#1A1A2E"
TEAL  = "#00D4AA"
TEAL_DARK = "#00A68A"
CREAM = "#FEFCF8"
GREY  = "#7a8294"
CARD  = "#FFFFFF"
TRACK = "#EEF1F7"
GOLD  = "#D9A441"
GOLD_DEEP = "#B8860B"

VIVINDEX_WEIGHTS = {
    "intent_understanding": 0.20,
    "one_shot_ui": 0.15,
    "startup_in_a_weekend": 0.25,
    "value_density": 0.20,
    "reverse_prompt_vision": 0.20,
}

TRACKS = [
    ("intent_understanding", "Intent Understanding"),
    ("one_shot_ui", "One-Shot UI"),
    ("startup_in_a_weekend", "Startup in a Weekend"),
    ("value_density", "Value Density @1K"),
    ("pharma_drug_interaction", "Pharma DDI"),
    ("pharma_regulatory_comprehension", "Pharma Regulatory"),
    ("reverse_prompt_vision", "Reverse-Prompt Vision"),
]

def esc(s):
    return html.escape(str(s))

def load():
    return json.load(open(DATA, encoding="utf-8"))

def vivindex_for(d, mid):
    ws, wsum = 0.0, 0.0
    n = 0
    for r in d["results"]:
        if r["model_id"] != mid:
            continue
        w = VIVINDEX_WEIGHTS.get(r["benchmark_id"])
        if w is not None and r.get("score") is not None:
            ws += w; wsum += r["score"] * w; n += 1
    return (wsum / ws) if ws > 0 else 0.0, n

def board(d):
    rows = []
    for m in d["models"]:
        vi, n = vivindex_for(d, m["id"])
        if n == 0:
            continue
        rows.append((m["display"], vi))
    rows.sort(key=lambda x: -x[1])
    return rows

def score_of(d, mid, bid):
    for r in d["results"]:
        if r["model_id"] == mid and r["benchmark_id"] == bid and r.get("score") is not None:
            return r["score"]
    return None

def status_of(d, mid, bid):
    for r in d["results"]:
        if r["model_id"] == mid and r["benchmark_id"] == bid:
            return str(r.get("status") or "").lower()
    return ""

def best_of(d, bid):
    best, name = 0, None
    for m in d["models"]:
        s = score_of(d, m["id"], bid)
        if s is not None and s > best:
            best, name = s, m["display"]
    return best, name

def metrics(d, mid):
    rows = [r for r in d["results"] if r["model_id"] == mid]
    scored = [r for r in rows if r.get("score") is not None and r["benchmark_id"] != "brick_breaker_realism"]
    tot_cost = sum(r.get("estimated_cost_usd") or 0 for r in scored)
    tot_tok = sum(r.get("total_tokens") or 0 for r in scored)
    tot_lat = sum(r.get("latency") or 0 for r in scored)
    tps = tot_tok / tot_lat if tot_lat else 0
    avg_cost = tot_cost / len(scored) if scored else 0
    vdm = next((r.get("metrics") for r in rows if r["benchmark_id"] == "value_density" and r.get("metrics")), {})
    return {
        "avg_cost": avg_cost,
        "total_cost": tot_cost,
        "tps": tps,
        "total_tokens": tot_tok,
        "v_per_1k": vdm.get("value_per_1k_tokens"),
        "score_rows": scored,
    }

def build_page(d, model):
    mid = model["id"]
    disp = model["display"]
    slug = mid.replace("_", "-")
    vi, n = vivindex_for(d, mid)
    board_all = board(d)
    rank = next((i + 1 for i, (name, _) in enumerate(board_all) if name == disp), None)
    is_top = rank == 1
    met = metrics(d, mid)
    # per-model GIF (gif arena)
    import os as _os
    gif_path = f"../data/gif_arena/{mid}.gif"
    gif_html = ""
    meta_p = ROOT / "data" / "gif_arena" / f"{mid}.meta.json"
    if (ROOT / "data" / "gif_arena" / f"{mid}.gif").exists():
        gj = {}
        if meta_p.exists():
            try: gj = json.loads(meta_p.read_text())
            except Exception: gj = {}
        axes = gj.get("scores") or gj.get("axes") or {}
        score = gj.get("overall") or gj.get("score")
        badges = " ".join(f'<span class="pill-new" style="margin-right:6px">{esc(k)}: {v}</span>' for k, v in axes.items())
        gif_html = (
            f'<section class="card p-gif" style="margin-top:1.5rem;padding:1.25rem">'
            f'<h2 style="font-size:1.05rem;margin-bottom:.7rem">🎬 GIF Arena'
            + (f' <span class="pill-new">overall {score}</span>' if score else "")
            + '</h2>'
            + f'<img src="{gif_path}" alt="{esc(disp)} dancing alpaca" loading="lazy" style="max-width:100%;border-radius:12px;box-shadow:var(--md-elev-2)" />'
            + (f'<div style="margin-top:.6rem">{badges}</div>' if badges else "")
            + '</section>'
        )
    vd = score_of(d, mid, "value_density")
    rp = score_of(d, mid, "reverse_prompt_vision")
    ddi = score_of(d, mid, "pharma_drug_interaction")
    reg = score_of(d, mid, "pharma_regulatory_comprehension")
    ddi_best, ddi_name = best_of(d, "pharma_drug_interaction")
    reg_best, reg_name = best_of(d, "pharma_regulatory_comprehension")

    track_rows = ""
    for bid, label in TRACKS:
        s = score_of(d, mid, bid)
        if s is None:
            note = "skipped — no vision" if status_of(d, mid, bid) == "skipped" else "not run"
            track_rows += f'<div class="p-track"><span class="p-track-name">{label}</span><span class="p-track-val muted">{note}</span></div>'
            continue
        pct = min(100, s)
        track_rows += (
            f'<div class="p-track"><span class="p-track-name">{label}</span>'
            f'<div class="p-track-bar"><div class="p-track-fill" style="width:{pct:.0f}%"></div></div>'
            f'<span class="p-track-val">{s:.0f}</span></div>'
        )

    board_rows = ""
    for i, (name, v) in enumerate(board_all[:5]):
        is_gold = i == 0
        is_me = name == disp
        col = "var(--gold)" if is_gold else ("var(--cobalt-dark)" if is_me else "var(--text)")
        badge = "👑 " if is_gold else ("→ " if is_me else "")
        board_rows += f'<div class="p-board-row"><span style="color:{col}">{badge}{esc(name)}</span><span class="p-board-val">{v:.1f}</span></div>'

    crown = '<span class="p-crown">👑</span>' if is_top else ""
    subtitle = f"VivIndex {vi:.1f} · rank #{rank} of {len(board_all)} models · {n}/{len(VIVINDEX_WEIGHTS)} core tracks"
    if not is_top and vi > 0:
        subtitle = f"VivIndex {vi:.1f} · rank #{rank} of {len(board_all)} models · {n}/{len(VIVINDEX_WEIGHTS)} core tracks"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{esc(disp)} — BenchmarkViv profile</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="../assets/styles.css?v=15" />
<style>
  .p-hero {{ padding: calc(var(--nav-h) + 2.5rem) 0 2rem; }}
  .p-hero h1 {{ font-size: clamp(1.6rem, 4.5vw, 2.4rem); display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }}
  .p-crown {{ filter: drop-shadow(0 2px 3px rgba(184,134,11,.5)); }}
  .p-sub {{ color: var(--text-dim); margin-top: .45rem; }}
  .p-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: .9rem; margin-top: 1.6rem; }}
  .p-card {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 1.2rem 1.15rem; box-shadow: var(--shadow); }}
  .p-card h3 {{ font-size: 1rem; margin-bottom: .9rem; }}
  .p-big {{ font: 800 clamp(2rem, 5vw, 2.8rem) var(--font-display); color: var(--cobalt-dark); line-height: 1; }}
  .p-big.gold {{ color: var(--gold); }}
  .p-track {{ display: grid; grid-template-columns: minmax(110px, 1fr) 1.4fr 44px; gap: .7rem; align-items: center; margin-bottom: .65rem; font-size: .88rem; }}
  .p-track-name {{ color: var(--text); font-weight: 550; }}
  .p-track-bar {{ height: 12px; background: var(--rule); border-radius: 999px; overflow: hidden; }}
  .p-track-fill {{ height: 100%; background: linear-gradient(90deg, var(--cobalt-dark), var(--cobalt)); border-radius: inherit; }}
  .p-track-val {{ font-weight: 700; font-variant-numeric: tabular-nums; text-align: right; }}
  .p-board-row {{ display: flex; justify-content: space-between; padding: .42rem 0; border-bottom: 1px solid var(--rule); font-weight: 600; gap: .5rem; }}
  .p-board-row:last-child {{ border-bottom: 0; }}
  .p-board-val {{ font-variant-numeric: tabular-nums; }}
  .p-kv {{ display: grid; grid-template-columns: 1fr auto; gap: .4rem .8rem; font-size: .9rem; }}
  .p-kv dt {{ color: var(--text-dim); }}
  .p-kv dd {{ margin: 0; font-weight: 650; font-variant-numeric: tabular-nums; }}
  .p-back {{ display: inline-flex; margin: 1.2rem 0 0; font: 600 .82rem var(--font-mono); color: var(--cobalt-dark); }}
  .muted {{ color: var(--text-dim); }}
  @media (max-width: 560px) {{
    .p-track {{ grid-template-columns: 1fr 1.3fr 40px; gap: .5rem; }}
    .p-card {{ padding: 1rem .9rem; }}
  }}
</style>
</head>
<body>
<nav class="navbar vt-nav"><div class="container">
  <a href="../index.html" class="nav-logo">Benchmark<span>Viv</span></a>
  <ul class="nav-links" id="siteNav">
    <li><a href="../index.html#leaderboard">Leaderboard</a></li>
    <li><a href="../index.html#tracks">Tracks</a></li>
    <li><a href="../vision.html">Vision</a></li>
    <li><a href="../experimental-design.html">Design</a></li>
    <li><a href="../about.html">About</a></li>
  </ul>
  <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
</div></nav>

<section class="p-hero">
  <div class="container">
    <a class="p-back" href="../index.html#comparison">← All models</a>
    <h1>{crown}{esc(disp)}</h1>
    <p class="p-sub">{subtitle}</p>

    <div class="p-grid">
      <div class="p-card">
        <h3>VivIndex</h3>
        <div class="p-big {'gold' if is_top else ''}">{vi:.1f}</div>
        <p class="muted" style="margin-top:.5rem;font-size:.88rem">Weighted composite of the {len(VIVINDEX_WEIGHTS)} core tracks. Board best: {board_all[0][0]} ({board_all[0][1]:.1f}).</p>
      </div>

      <div class="p-card">
        <h3>Every benchmark</h3>
        {track_rows}
      </div>

      <div class="p-card">
        <h3>Top of the board</h3>
        {board_rows}
      </div>

      <div class="p-card">
        <h3>Efficiency &amp; cost</h3>
        <dl class="p-kv">
          <dt>Avg cost / scored run</dt><dd>${met['avg_cost']:.4f}</dd>
          <dt>Total run cost</dt><dd>${met['total_cost']:.4f}</dd>
          <dt>Output speed</dt><dd>{met['tps']:.0f} tok/s</dd>
          <dt>Total tokens</dt><dd>{met['total_tokens']:,}</dd>
          <dt>Value per 1K tokens</dt><dd>{met['v_per_1k'] if met['v_per_1k'] is not None else '—'}</dd>
        </dl>
      </div>

      <div class="p-card">
        <h3>Pharma domain</h3>
        <dl class="p-kv">
          <dt>Drug-Drug Interaction</dt><dd>{ddi if ddi is not None else '—'} <span class="muted">(best {ddi_best:.0f} · {esc(ddi_name)})</span></dd>
          <dt>Regulatory</dt><dd>{reg if reg is not None else '—'} <span class="muted">(best {reg_best:.0f} · {esc(reg_name)})</span></dd>
        </dl>
      </div>

      <div class="p-card">
        <h3>Notes</h3>
        <p class="muted" style="font-size:.88rem">Non-vision models are skipped on the reverse-prompt track, not zero-scored. Values come from live Venice API runs recorded in <code>data/results.json</code>. Scores are reproducible with the published protocol.</p>
      </div>
    </div>
  </div>
</section>

<footer class="footer"><div class="container">
  <div class="footer-logo">Benchmark<span>Viv</span></div>
  <p>Independent benchmark showcase for Venice API models.</p>
  <div class="footer-links"><a href="../index.html#leaderboard">Leaderboard</a><a href="../experimental-design.html">Experimental Design</a></div>
</div></footer>

<script>
(function(){{
  var t = document.getElementById('navToggle'), n = document.getElementById('siteNav');
  if (t && n) t.addEventListener('click', function(){{ n.classList.toggle('is-open'); t.setAttribute('aria-expanded', n.classList.contains('is-open')); }});
}})();
</script>
</body>
</html>
"""
    (OUT / f"{slug}.html").write_text(page, encoding="utf-8")
    print("wrote", f"models/{slug}.html", f"(rank #{rank})")

def main():
    OUT.mkdir(exist_ok=True)
    d = load()
    for m in d["models"]:
        if vivindex_for(d, m["id"])[1] == 0:
            continue
        build_page(d, m)
    print("done")

if __name__ == "__main__":
    main()
