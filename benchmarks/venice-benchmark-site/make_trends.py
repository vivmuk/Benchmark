#!/usr/bin/env python3
"""Generate VivIndex history per model from results.json snapshots.

Reads data/results.json (current) plus data/results.json.snapshot-* files,
computes the same VivIndex composite for each model at each point in time
(renormalizing weights when older snapshots lack the vision track), and emits:

  data/trends.json        — machine-readable series
  data/trends_chart.svg   — line chart of every model's trajectory
  trends.html             — "Trends & Movers" page (site palette + nav)
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT_PAGE = ROOT / "trends.html"

WEIGHTS = {
    "intent_understanding": 0.20,
    "one_shot_ui": 0.15,
    "startup_in_a_weekend": 0.25,
    "value_density": 0.20,
    "reverse_prompt_vision": 0.20,
}

PALETTE = [
    "#00D4AA", "#D9A441", "#1A1A2E", "#7a8294", "#E4572E", "#4361EE",
    "#9D4EDD", "#2A9D8F", "#E76F51", "#B8860B", "#457B9D", "#6D6875",
    "#80B918", "#D00000", "#3A0CA3", "#F4A261", "#264653", "#7209B7",
]

SNAP_RE = re.compile(r"results\.json\.snapshot(?:-|_)([0-9]{8}(?:[0-9]{6})?)?")


def esc(s):
    return html.escape(str(s))


def snapshot_date(path: Path) -> str:
    m = SNAP_RE.search(path.name)
    if m and m.group(1):
        ts = m.group(1)
        try:
            return datetime.strptime(ts, "%Y%m%d%H%M%S").strftime("%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(ts, "%Y%m%d").strftime("%Y-%m-%d")
            except ValueError:
                pass
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def vivindex(d: dict, mid: str) -> float | None:
    ws = wsum = 0.0
    n = 0
    for r in d.get("results", []):
        if r.get("model_id") != mid or r.get("score") is None:
            continue
        w = WEIGHTS.get(r.get("benchmark_id"))
        if w is not None:
            ws += w
            wsum += r["score"] * w
            n += 1
    if ws <= 0:
        return None
    return wsum / ws  # renormalize over tracks present in that snapshot


def all_points():
    """Return {date: {"label": date, "viv": {model_id: score}}} sorted by date."""
    sources = []
    cur = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    generated = cur.get("generated_at", "")
    if generated:
        sources.append((generated[:10], cur))
    for p in sorted(DATA.glob("results.json.snapshot*")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "results" in d:
            sources.append((snapshot_date(p), d))
    # de-dupe same-date sources (keep latest per date)
    seen = {}
    for date, d in sources:
        seen[date] = d
    dates = sorted(seen)
    points = []
    for date in dates:
        d = seen[date]
        viv = {}
        for m in d.get("models", []):
            v = vivindex(d, m["id"])
            if v is not None:
                viv[m["id"]] = round(v, 1)
        points.append({"date": date, "viv": viv})
    return points


def build():
    points = all_points()
    if len(points) < 2:
        print("trends: need at least 2 dated snapshots; have", len(points))
        return

    # collect per-model series with display names
    cur = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    disp = {m["id"]: m["display"] for m in cur.get("models", [])}
    series = {}
    for pt in points:
        for mid, v in pt["viv"].items():
            series.setdefault(mid, []).append((pt["date"], v))
            disp.setdefault(mid, mid)

    # movers: earliest vs latest viv for models with >=2 distinct values
    movers = []
    for mid, pts in series.items():
        vals = [v for _, v in pts]
        first, last = vals[0], vals[-1]
        if len(set(vals)) < 2:
            continue
        movers.append({"model_id": mid, "display": disp[mid], "first": first,
                       "last": last, "delta": round(last - first, 1),
                       "dates": [d for d, _ in pts]})
    movers.sort(key=lambda x: x["delta"])

    trends_out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "dates": [pt["date"] for pt in points],
        "series": {mid: {"display": disp[mid], "points": pts} for mid, pts in series.items()},
        "movers": movers,
    }
    (DATA / "trends.json").write_text(
        json.dumps(trends_out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"trends.json: {len(series)} series, {len(points)} dates, {len(movers)} movers")

    write_chart(points, series, disp)
    legends = legend_html(series, disp)
    write_page(points, series, disp, movers, legends)


def write_chart(points, series, disp):
    dates = [pt["date"] for pt in points]
    W, H, PAD_L, PAD_R, PAD_T, PAD_B = 980, 420, 70, 18, 26, 46
    allv = [v for pt in points for v in pt["viv"].values()]
    lo, hi = min(allv), max(allv)
    lo = max(0, lo - 5)
    hi = min(100, hi + 5)
    def X(i):
        return PAD_L + i * (W - PAD_L - PAD_R) / max(1, len(dates) - 1)
    def Y(v):
        return PAD_T + (hi - v) * (H - PAD_T - PAD_B) / max(1, hi - lo)

    grid = ""
    for g in range(int(lo // 10 * 10), int(hi) + 1, 10):
        gy = Y(g)
        grid += (f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{W - PAD_R}" y2="{gy:.1f}" '
                 f'stroke="#EEF1F7" stroke-width="1"/>'
                 f'<text x="{PAD_L - 8}" y="{gy + 4:.1f}" text-anchor="end" '
                 f'font-size="11" fill="#7a8294">{g}</text>')
    xlabels = ""
    seen_dates = []
    for i, d in enumerate(dates):
        label = d[5:]  # MM-DD
        if not seen_dates or seen_dates[-1] != label:
            xlabels += (f'<text x="{X(i):.1f}" y="{H - 22}" text-anchor="middle" '
                        f'font-size="11" fill="#7a8294">{label}</text>')
            seen_dates.append(label)

    paths, legends = "", ""
    for idx, (mid, pts) in enumerate(series.items()):
        if len(pts) < 2:
            continue
        color = PALETTE[idx % len(PALETTE)]
        d = "M" + " L".join(f"{X(dates.index(dt)):.1f},{Y(v):.1f}" for dt, v in pts)
        dots = "".join(
            f'<circle cx="{X(dates.index(dt)):.1f}" cy="{Y(v):.1f}" r="3" fill="{color}">'
            f'<title>{esc(disp[mid])}: {v} ({dt})</title></circle>'
            for dt, v in pts)
        paths += f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">{dots}</path>'
        legends += (f'<span class="lg"><i style="background:{color}"></i>'
                    f'{esc(disp[mid])}</span>')

    svg = f'''<svg viewBox="0 0 {W} {H}" role="img" aria-label="VivIndex trend lines"
  xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">
  <rect width="{W}" height="{H}" fill="#ffffff" rx="14"/>
  {grid}{xlabels}{paths}
</svg>'''
    (DATA / "trends_chart.svg").write_text(svg, encoding="utf-8")
    print("trends_chart.svg written")


def legend_html(series, disp):
    out = ""
    for idx, (mid, pts) in enumerate(series.items()):
        if len(pts) < 2:
            continue
        color = PALETTE[idx % len(PALETTE)]
        out += (f'<span class="lg"><i style="background:{color}"></i>'
                f'{esc(disp[mid])}</span>')
    return out


def write_page(points, series, disp, movers, legends):
    chart = (DATA / "trends_chart.svg").read_text(encoding="utf-8")
    # re-cap the chart for inlining: strip xml decl if present
    chart = chart.replace('<?xml version="1.0" encoding="UTF-8"?>', "").strip()

    risers = "".join(
        f'<div class="mv"><span class="mv-name">▲ {esc(m["display"])}</span>'
        f'<span class="mv-delta up">+{m["delta"]:.1f}</span>'
        f'<span class="mv-sub muted">{m["first"]:.1f} → {m["last"]:.1f} · '
        f'{", ".join(d[5:] for d in m["dates"][:3])}</span></div>'
        for m in reversed(movers[-8:]))
    fallers = "".join(
        f'<div class="mv"><span class="mv-name">▼ {esc(m["display"])}</span>'
        f'<span class="mv-delta down">{m["delta"]:.1f}</span>'
        f'<span class="mv-sub muted">{m["first"]:.1f} → {m["last"]:.1f}</span></div>'
        for m in movers[:8])

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Trends &amp; Movers — BenchmarkViv</title>
<meta name="description" content="VivIndex history for every benchmarked Venice API model — who climbed, who slipped, and how the leaderboard evolved." />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="assets/styles.css?v=15" />
<style>
  .t-hero {{ padding: calc(var(--nav-h) + 2.5rem) 0 2rem; }}
  .t-hero h1 {{ font-size: clamp(1.6rem, 4.5vw, 2.4rem); }}
  .t-sub {{ color: var(--text-dim); margin-top: .45rem; max-width: 62ch; }}
  .t-card {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 1.4rem 1.3rem; box-shadow: var(--shadow); margin-top: 1.4rem; }}
  .t-card h2 {{ font-size: 1.05rem; margin-bottom: 1rem; }}
  .t-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.4rem; margin-top: 1.4rem; }}
  .lg {{ display: inline-flex; align-items: center; gap: .4rem; font-size: .78rem; color: var(--text); margin: .25rem .9rem .25rem 0; white-space: nowrap; }}
  .lg i {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}
  .mv {{ display: grid; grid-template-columns: 1fr auto; gap: .1rem .8rem; padding: .5rem 0; border-bottom: 1px solid var(--rule); }}
  .mv:last-child {{ border-bottom: 0; }}
  .mv-name {{ font-weight: 650; }}
  .mv-delta {{ font-weight: 800; font-variant-numeric: tabular-nums; }}
  .mv-delta.up {{ color: #0a8f5f; }}
  .mv-delta.down {{ color: #c2472e; }}
  .mv-sub {{ grid-column: 1 / -1; font-size: .8rem; }}
  .muted {{ color: var(--text-dim); }}
  @media (max-width: 720px) {{ .t-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<nav class="navbar vt-nav"><div class="container">
  <a href="index.html" class="nav-logo">Benchmark<span>Viv</span></a>
  <ul class="nav-links" id="siteNav">
    <li><a href="index.html#leaderboard">Leaderboard</a></li>
    <li><a href="index.html#tracks">Tracks</a></li>
    <li><a href="vision.html">Vision</a></li>
    <li><a href="trends.html" class="active">Trends</a></li>
    <li><a href="compare.html">Compare</a></li>
    <li><a href="experimental-design.html">Design</a></li>
    <li><a href="about.html">About</a></li>
  </ul>
  <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
</div></nav>

<main class="container">
  <section class="t-hero">
    <h1>Trends &amp; Movers</h1>
    <p class="t-sub">VivIndex history reconstructed from every dated results snapshot. Lines show each model&#8217;s composite score over time — who climbed, who slipped, and when the crown changed hands.</p>
  </section>

  <section class="t-card">
    <h2>VivIndex over time</h2>
    <div style="overflow-x:auto">{chart}</div>
    <div style="margin-top:.8rem">{legends}</div>
  </section>

  <div class="t-grid">
    <section class="t-card">
      <h2>▲ Risers</h2>
      {risers or '<p class="muted">No meaningful gains yet — first trend window in progress.</p>'}
    </section>
    <section class="t-card">
      <h2>▼ Fallers</h2>
      {fallers or '<p class="muted">No meaningful drops yet — first trend window in progress.</p>'}
    </section>
  </div>

  <p class="muted" style="margin:1.6rem 0 2.4rem;font-size:.85rem">
    Methodology: composite uses the five core weighted tracks (intent 20%, one-shot UI 15%,
    startup 25%, value density 20%, vision 20%) with weights renormalized in snapshots that
    predate the vision track. Dates come from snapshot timestamps; the final point is the
    current results.json.
  </p>
</main>
<script>document.querySelectorAll('.navbar .nav-toggle').forEach(b=>b.addEventListener('click',()=>{{const l=document.getElementById('siteNav');l.classList.toggle('open');b.setAttribute('aria-expanded',String(l.classList.contains('open')));}}));</script>
</body>
</html>'''
    OUT_PAGE.write_text(page, encoding="utf-8")
    print("trends.html written")


if __name__ == "__main__":
    build()
