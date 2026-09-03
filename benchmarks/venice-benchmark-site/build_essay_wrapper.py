#!/usr/bin/env python3
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DISPLAY = {
    "claude-opus-4-8-fast": "Opus 4.8 Fast",
    "claude-fable-5": "Fable 5",
    "claude-fable-5-1": "Fable 5.1",
}
SLUG = {
    "claude-opus-4-8-fast": "opus",
    "claude-fable-5": "fable5",
    "claude-fable-5-1": "fable51",
}

def strip_fences(s):
    s = s.strip()
    s = re.sub(r"^```(?:html)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return s

essays = {}
for m in DISPLAY:
    d = json.loads((ROOT / "data" / f"essay_{m}.json").read_text(encoding="utf-8"))
    d["html"] = strip_fences(d["content"])
    essays[m] = d
    # write standalone file
    (ROOT / f"world-model-essay-{SLUG[m]}.html").write_text(
        d["html"] + "\n", encoding="utf-8")
    print("wrote", f"world-model-essay-{SLUG[m]}.html", len(d["html"]), "chars")

judge = json.loads((ROOT / "data" / "essay_judge.json").read_text(encoding="utf-8"))
verdict = judge["verdict"]

# build wrapper
rows = ""
for m in ["claude-opus-4-8-fast", "claude-fable-5", "claude-fable-5-1"]:
    d = essays[m]
    rk = next((r for r in verdict.get("rankings", []) if r["model"] == m), {})
    rows += f"""
    <tr>
      <td class="name">{DISPLAY[m]}</td>
      <td class="num">{d['completion_tokens']:,}</td>
      <td class="num">{d['total_tokens']:,}</td>
      <td class="num">${d['cost_usd']:.4f}</td>
      <td class="num">{d['latency']}s</td>
      <td class="num">{rk.get('substance','—')}</td>
      <td class="num">{rk.get('design','—')}</td>
    </tr>"""

rank_cards = ""
for r in verdict.get("rankings", []):
    m = r["model"]
    rank_cards += f"""
    <div class="rankcard">
      <div class="rchead"><span class="rcname">{DISPLAY.get(m, m)}</span>
        <span class="rcscore">S {r.get('substance')} · D {r.get('design')}</span></div>
      <p class="rcnote">{html.escape(r.get('note',''))}</p>
    </div>"""

def iframe_embed(slug):
    path = f"world-model-essay-{slug}.html"
    # read escaped html for srcdoc
    content = essays[[k for k,v in SLUG.items() if v==slug][0]]["html"]
    esc = html.escape(content, quote=True)
    return f'<iframe class="frame" srcdoc="{esc}" title="{slug}"></iframe>'

# Build each iframe
frames = ""
for m in ["claude-opus-4-8-fast", "claude-fable-5", "claude-fable-5-1"]:
    slug = SLUG[m]
    esc = html.escape(essays[m]["html"], quote=True)
    frames += f'<iframe class="frame" srcdoc="{esc}"></iframe>'

wrapper = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Models in Medical Affairs — Model Shootout</title>
<style>
  :root {{
    --teal:#00D4AA; --indigo:#1A1A2E; --cream:#FEFCF8; --gold:#D9A441;
    --grey:#7a8294; --line:#e8ecf3;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
         background:var(--cream); color:var(--indigo); line-height:1.6; }}
  header {{ background:var(--indigo); color:#fff; padding:56px 24px 40px; text-align:center; }}
  header h1 {{ font-size:2.4rem; font-weight:800; letter-spacing:-0.02em; }}
  header p {{ color:#b8c0d4; margin-top:10px; font-size:1.05rem; max-width:620px; margin-inline:auto; }}
  .kicker {{ color:var(--teal); text-transform:uppercase; letter-spacing:0.18em; font-size:0.72rem; font-weight:700; }}
  main {{ max-width:1180px; margin:0 auto; padding:36px 20px 80px; }}
  h2 {{ font-size:1.5rem; margin:40px 0 16px; font-weight:750; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:16px; padding:24px 26px;
          box-shadow:0 1px 2px rgba(26,26,46,0.04); }}
  table {{ width:100%; border-collapse:collapse; font-size:0.92rem; }}
  th, td {{ text-align:left; padding:12px 14px; border-bottom:1px solid var(--line); }}
  th {{ color:var(--grey); text-transform:uppercase; font-size:0.7rem; letter-spacing:0.08em; }}
  td.num {{ font-variant-numeric:tabular-nums; text-align:right; font-weight:600; }}
  td.name {{ font-weight:700; }}
  .winner {{ background:linear-gradient(90deg,#fff8e8,#fffdf5); }}
  .rankcard {{ border:1px solid var(--line); border-radius:14px; padding:20px 22px; margin:14px 0; background:#fff; }}
  .rchead {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
  .rcname {{ font-weight:800; font-size:1.1rem; }}
  .rcscore {{ color:var(--teal); font-weight:700; }}
  .rcnote {{ color:#4a5264; font-size:0.92rem; }}
  .summary {{ background:#f2fbf8; border:1px solid #cdeee6; border-radius:14px; padding:20px 22px; margin-top:8px; }}
  .summary strong {{ color:#007d62; }}
  .frames {{ display:flex; flex-direction:column; gap:28px; }}
  .frame {{ width:100%; height:720px; border:1px solid var(--line); border-radius:16px; background:#fff; }}
  .framelabel {{ font-weight:800; margin-bottom:8px; color:var(--indigo); }}
  .champion {{ display:inline-block; background:var(--gold); color:#241c04; font-weight:800;
              padding:2px 12px; border-radius:999px; font-size:0.85rem; margin-left:8px; }}
  footer {{ text-align:center; color:var(--grey); padding:30px; font-size:0.85rem; }}
</style>
</head>
<body>
<header>
  <div class="kicker">BenchmarkViv · Model Shootout</div>
  <h1>World Models in Medical Affairs</h1>
  <p>Three frontier models wrote the same brief into a self-contained HTML article.
     Compared on verbosity, cost, and UI craft — then graded by Grok 4.6.</p>
</header>

<main>
  <h2>Head-to-head</h2>
  <div class="card">
    <table>
      <thead><tr>
        <th>Model</th><th>Output tokens</th><th>Total tokens</th><th>Cost</th>
        <th>Latency</th><th>Substance</th><th>Design</th>
      </tr></thead>
      <tbody>{rows}
      </tbody>
    </table>
  </div>

  <h2>Grok 4.6 verdict — winner: {html.escape(verdict.get('overall_winner',''))}</h2>
  {rank_cards}
  <div class="summary">{html.escape(verdict.get('summary',''))}</div>

  <h2>The three essays</h2>
  <div class="frames">
    <div><div class="framelabel">1 · Opus 4.8 Fast</div>{frames.split('</iframe>')[0]}</iframe></div>
    <div><div class="framelabel">2 · Fable 5</div>{'</iframe>'.join(frames.split('</iframe>')[1:2])}</iframe></div>
    <div><div class="framelabel">3 · Fable 5.1</div>{'</iframe>'.join(frames.split('</iframe>')[2:3])}</iframe></div>
  </div>
</main>
<footer>BenchmarkViv · generated {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body>
</html>
"""

(ROOT / "world-model-essay.html").write_text(wrapper, encoding="utf-8")
print("wrote world-model-essay.html", len(wrapper), "chars")
print("judge tokens:", judge["completion_tokens"], "judge cost:", judge["cost_usd"])