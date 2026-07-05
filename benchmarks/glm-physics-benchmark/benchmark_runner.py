#!/usr/bin/env python3
"""
GLM 5.2 Physics + Sakura Benchmark
Directly calls Venice AI API and saves all generated artifacts.
"""

import json
import os
import re
import time
import html
import requests
from datetime import datetime

API_URL = "https://api.venice.ai/api/v1/chat/completions"
API_KEY = os.environ.get("VENICE_INFERENCE_KEY", "VENICE_INFERENCE_KEY_eSo1FVcIDqp9rr5CI6LLpLUmq2tu721fEasyCWPmcV")
MODEL_ID = "zai-org-glm-5-2"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def call_model(prompt, max_tokens=8192, temperature=0.4):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    start = time.time()
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=240)
        elapsed = time.time() - start
        if resp.status_code != 200:
            return {
                "status": f"error:{resp.status_code}",
                "error": f"HTTP {resp.status_code}: {resp.text[:500]}",
                "response_time": elapsed,
                "response": "",
                "tokens": "N/A",
            }
        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        usage = data.get("usage", {})
        return {
            "status": "success",
            "response_time": elapsed,
            "response": content,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
    except Exception as e:
        elapsed = time.time() - start
        return {"status": "error", "error": str(e), "response_time": elapsed, "response": "", "tokens": "N/A"}


def extract_html(text):
    """Extract content between ```html ... ``` or ``` ... ```, else return whole text."""
    m = re.search(r"```html\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def save(name, content):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


TASKS = [
    {
        "id": "physics-demo",
        "name": "HTML5 Canvas Physics Demo",
        "file": "glm-physics-demo.html",
        "prompt": """Create a single self-contained HTML file with an HTML5 Canvas physics demo.

Requirements:
- Show multiple cars driving across a 2D bridge over water.
- Each car must have: velocity, rotating wheels, suspension bounce (vertical oscillation simulating bumps), and headlights/taillights.
- Include a parallax scrolling background: sky, distant mountains/hills, water, bridge structure, road.
- Cars should loop across the screen continuously.
- Use requestAnimationFrame.
- No external images. Draw everything with Canvas API.
- Add a subtle title overlay "Bridge Traffic Physics".
- Make it visually polished: gradients, shadows, reflections on water.

Return ONLY the complete HTML file inside a ```html code block.""",
        "rubric": {"correctness": 25, "visual": 25, "physics": 30, "constraints": 10, "code": 10},
    },
    {
        "id": "sakura-site",
        "name": "Sakura One-Shot Website",
        "file": "glm-sakura-site.html",
        "prompt": """Create a single self-contained HTML file for a premium Japanese "SAKURA" themed landing page in traditional sumi-e ink wash painting style.

Requirements:
- Soft cream/parchment paper-textured background with subtle grain.
- Japanese cherry blossom (sakura) branches drawn with SVG, using ink-brush stroke filters and soft pink blossoms.
- Large elegant Japanese-inspired serif typography for "SAKURA".
- Animated falling sakura petals using a lightweight JavaScript particle system.
- Subtle parallax depth: background ink wash, midground branches, foreground petals.
- Minimal navigation bar: Home, Story, Collection, Visit.
- Responsive, full-bleed hero section with centered title and a short poetic tagline.
- No external images or fonts (use Google Fonts links allowed, but prefer system fallbacks).
- Everything must work in a single HTML file.

Return ONLY the complete HTML file inside a ```html code block.""",
        "rubric": {"correctness": 20, "visual": 30, "physics": 15, "constraints": 15, "code": 20},
    },
    {
        "id": "physics-enhanced",
        "name": "Enhanced Interactive Physics Demo",
        "file": "glm-physics-demo-enhanced.html",
        "prompt": """Below is the HTML file for a Canvas physics demo. Enhance it by adding:
1. A click-to-spawn car interaction: when the user clicks on the canvas, a new car spawns at that x-position if it is on the road.
2. A speed slider control (range input) that globally adjusts how fast all cars move.
3. A day/night toggle button that changes sky gradients, turns headlights/taillights on/off appropriately, and adjusts overall brightness.
4. Keep all existing features (multiple cars, bridge, parallax, wheel rotation, suspension bounce, water reflections).

Return ONLY the complete enhanced HTML file inside a ```html code block.

CODE TO ENHANCE:
""",
        "depends_on": "glm-physics-demo.html",
        "rubric": {"correctness": 25, "visual": 20, "physics": 20, "constraints": 15, "code": 20},
    },
    {
        "id": "physics-fix",
        "name": "Physics Bug Fix",
        "file": "glm-physics-fixed.html",
        "prompt": """Below is a deliberately broken snippet from the Canvas physics demo. Identify and fix the bug(s). The cars should drive across the screen, wheels should rotate, and the parallax background should scroll smoothly. 

Return the corrected complete HTML file inside a ```html code block, followed by a short explanation of what was wrong and how you fixed it.

BROKEN CODE:
```html
<!DOCTYPE html>
<html>
<head><title>Broken Cars</title></head>
<body>
<canvas id="c" width="800" height="400"></canvas>
<script>
const ctx = document.getElementById('c').getContext('2d');
let cars = [{x: -50, y: 280, speed: 2, color: 'red'}];
function draw() {
  ctx.fillStyle = 'skyblue';
  ctx.fillRect(0,0,800,400);
  ctx.fillStyle = 'gray';
  ctx.fillRect(0,300,800,50);
  cars.forEach(car => {
    car.x += car.speed;
    ctx.fillStyle = car.color;
    ctx.fillRect(car.x, car.y, 60, 30);
    // wheels
    ctx.beginPath();
    ctx.arc(car.x + 12, car.y + 30, 8, 0, Math.PI * 2);
    ctx.arc(car.x + 48, car.y + 30, 8, 0, Math.PI * 2);
    ctx.fill();
    if (car.x > 800) car.x = -60;
  });
  requestAnimationFrame(draw());
}
draw();
</script>
</body>
</html>
```""",
        "rubric": {"correctness": 30, "visual": 15, "physics": 25, "constraints": 10, "code": 20},
    },
    {
        "id": "physics-explain",
        "name": "Physics Implementation Explanation",
        "file": "glm-physics-explanation.md",
        "prompt": """Explain how the HTML5 Canvas car physics demo works. Cover:
1. The animation loop (requestAnimationFrame).
2. How car position and velocity are updated.
3. How wheel rotation and suspension bounce are simulated.
4. How parallax scrolling background layers are implemented.
5. How water reflection effects can be achieved.

Keep it concise but technically accurate, suitable for a developer who wants to understand the implementation. Return as Markdown.""",
        "rubric": {"correctness": 25, "visual": 5, "physics": 35, "constraints": 5, "code": 30},
    },
]


def score_task(task_id, result_text):
    """Heuristic scoring based on keyword/content analysis."""
    text = result_text.lower()
    scores = {}
    if task_id in ("physics-demo", "physics-enhanced", "physics-fix"):
        scores["correctness"] = 20 if "<html" in text and "<canvas" in text and "<script" in text else 10
        scores["visual"] = 0
        for kw in ["gradient", "shadow", "reflection", "sky", "water", "bridge", "color"]:
            scores["visual"] += 4 if kw in text else 0
        scores["visual"] = min(25, scores["visual"])
        scores["physics"] = 0
        for kw in ["requestanimationframe", "velocity", "speed", "rotate", "wheel", "bounce", "suspension", "parallax"]:
            scores["physics"] += 4 if kw in text else 0
        scores["physics"] = min(30, scores["physics"])
        scores["constraints"] = 10 if "<img" not in text else 5
        scores["code"] = 10 if len(result_text) > 1500 else 5
    elif task_id == "sakura-site":
        scores["correctness"] = 15 if "<html" in text and "<script" in text else 8
        scores["visual"] = 0
        for kw in ["sakura", "petal", "branch", "flower", "gradient", "serif", "typography", "parallax"]:
            scores["visual"] += 4 if kw in text else 0
        scores["visual"] = min(30, scores["visual"])
        scores["physics"] = 12 if "petal" in text and ("animate" in text or "requestanimationframe" in text) else 6
        scores["constraints"] = 12 if "<img" not in text or "data:" in text else 6
        scores["code"] = 15 if len(result_text) > 2000 else 8
    else:  # explanation
        scores["correctness"] = 20
        scores["visual"] = 5
        scores["physics"] = 0
        for kw in ["requestanimationframe", "velocity", "wheel", "rotation", "bounce", "suspension", "parallax", "reflection"]:
            scores["physics"] += 5 if kw in text else 0
        scores["physics"] = min(35, scores["physics"])
        scores["constraints"] = 5
        scores["code"] = 25 if len(result_text) > 500 else 12
    total = sum(scores.values())
    return scores, total


def run():
    results = []
    artifacts = {}

    for task in TASKS:
        print(f"\n=== Running: {task['name']} ===")
        prompt = task["prompt"]
        if "depends_on" in task:
            dep_path = os.path.join(OUT_DIR, task["depends_on"])
            if os.path.exists(dep_path):
                with open(dep_path, "r", encoding="utf-8") as f:
                    dep_code = f.read()
                prompt = prompt + "\n" + dep_code
            else:
                print(f"Dependency not found: {dep_path}")

        result = call_model(prompt, max_tokens=12000)

        if result["status"] == "success":
            content = extract_html(result["response"]) if task["file"].endswith(".html") else result["response"]
            path = save(task["file"], content)
            artifacts[task["id"]] = path
            scores, total = score_task(task["id"], content)
            print(f"Saved: {path}")
            print(f"Latency: {result['response_time']:.2f}s | Tokens: {result['total_tokens']}")
            print(f"Score: {total}/100 {scores}")
            results.append({
                "id": task["id"],
                "name": task["name"],
                "file": task["file"],
                "latency": round(result["response_time"], 2),
                "prompt_tokens": result["prompt_tokens"],
                "completion_tokens": result["completion_tokens"],
                "total_tokens": result["total_tokens"],
                "scores": scores,
                "total_score": total,
                "path": path,
            })
        else:
            print(f"FAILED: {result['error']}")
            save(task["file"], f"<!-- ERROR -->\n{result['error']}")
            results.append({
                "id": task["id"],
                "name": task["name"],
                "file": task["file"],
                "latency": round(result["response_time"], 2),
                "error": result["error"],
                "total_score": 0,
                "path": os.path.join(OUT_DIR, task["file"]),
            })

    build_report(results, artifacts)
    return results


def build_report(results, artifacts):
    total_score = sum(r.get("total_score", 0) for r in results)
    avg = total_score / len(results) if results else 0
    total_tokens = sum((r["total_tokens"] if isinstance(r.get("total_tokens"), int) else 0) for r in results)
    total_time = sum((r["latency"] if isinstance(r.get("latency"), (int, float)) else 0) for r in results)

    rows = ""
    for r in results:
        if "error" in r:
            rows += f"<tr><td>{html.escape(r['name'])}</td><td colspan='7' style='color:red'>{html.escape(r['error'])}</td></tr>\n"
        else:
            rows += f"""<tr>
                <td>{html.escape(r['name'])}</td>
                <td>{r['latency']}s</td>
                <td>{r['prompt_tokens']}</td>
                <td>{r['completion_tokens']}</td>
                <td>{r['total_tokens']}</td>
                <td>{r['total_score']}/100</td>
                <td><a href="{r['file']}" target="_blank">Open</a></td>
            </tr>\n"""

    fix_explanation = ""
    fix_path = os.path.join(OUT_DIR, "glm-fix-explanation.md")
    if os.path.exists(fix_path):
        fix_explanation = open(fix_path, "r", encoding="utf-8").read()
    else:
        # Extract explanation from fixed file response if it was included inline
        fix_html_path = os.path.join(OUT_DIR, "glm-physics-fixed.html")
        if os.path.exists(fix_html_path):
            fix_html = open(fix_html_path, "r", encoding="utf-8").read()
            # If explanation is in markdown after html block, save separately
            if "</html>" in fix_html:
                parts = fix_html.split("</html>", 1)
                save("glm-physics-fixed.html", parts[0] + "</html>")
                explanation = parts[1].strip()
                save("glm-fix-explanation.md", explanation)
                fix_explanation = explanation

    report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GLM 5.2 Physics + Sakura Benchmark Report</title>
<style>
  :root {{ --bg:#FEFCF8; --ink:#1A1A2E; --teal:#00D4AA; --muted:#6b6b7b; }}
  body {{ font-family: Inter, system-ui, sans-serif; background: var(--bg); color: var(--ink); max-width: 1100px; margin: 0 auto; padding: 2rem; line-height: 1.6; }}
  h1, h2 {{ font-family: Georgia, serif; }}
  h1 {{ color: var(--teal); }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ padding: 0.75rem; border-bottom: 1px solid #ddd; text-align: left; }}
  th {{ background: #f3f3f3; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .card {{ background: white; border-radius: 12px; padding: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  .card big {{ display: block; font-size: 1.8rem; font-weight: 700; color: var(--teal); }}
  iframe {{ width: 100%; height: 360px; border: 1px solid #ddd; border-radius: 12px; margin: 1rem 0; background: white; }}
  pre {{ background: #f4f4f4; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9rem; }}
  .prompt {{ background: #fff; border-left: 4px solid var(--teal); padding: 1rem; border-radius: 0 8px 8px 0; }}
</style>
</head>
<body>
<h1>GLM 5.2 Physics + Sakura Benchmark</h1>
<p>Run started: {datetime.utcnow().isoformat()} UTC | Model: <code>zai-org-glm-5-2</code></p>

<div class="summary">
  <div class="card"><big>{avg:.1f}</big>Average Score / 100</div>
  <div class="card"><big>{total_tokens:,}</big>Total Tokens</div>
  <div class="card"><big>{total_time:.1f}s</big>Total Wall Time</div>
  <div class="card"><big>{len(results)}</big>Tasks</div>
</div>

<h2>Task Results</h2>
<table>
<tr><th>Task</th><th>Latency</th><th>Prompt Tok</th><th>Completion Tok</th><th>Total Tok</th><th>Score</th><th>Artifact</th></tr>
{rows}
</table>

<h2>Physics Demo (GLM 5.2 generated)</h2>
<iframe src="glm-physics-demo.html" title="Physics Demo"></iframe>

<h2>Enhanced Interactive Physics Demo</h2>
<iframe src="glm-physics-demo-enhanced.html" title="Enhanced Physics Demo"></iframe>

<h2>Sakura One-Shot Website</h2>
<iframe src="glm-sakura-site.html" title="Sakura Site"></iframe>

<h2>How the Sakura Website Was Built (with Fable 5)</h2>
<p>The original post highlights Fable 5's ability to produce <strong>one-shot web designs</strong>.
Fable 5's large output window lets it emit a complete, self-contained HTML file in a single generation:
embedded SVG ink branches, CSS paper texture, JS petal physics, parallax layers, and responsive layout.
No iterative coding or external assets required.</p>

<h3>Prompt that would create the Sakura site</h3>
<div class="prompt">
<pre><code>Create a single self-contained HTML file for a premium Japanese "SAKURA" themed landing page in traditional sumi-e ink wash painting style. Use a soft cream/parchment paper texture background with subtle grain, SVG cherry blossom branches with ink-brush stroke filters, elegant Japanese-inspired serif typography for "SAKURA", animated falling petals via a lightweight JS particle system, subtle parallax depth, minimal navigation, and responsive full-bleed hero. No external images.</code></pre>
</div>

<h2>Bug Fix Explanation</h2>
<div class="prompt">
<pre><code>{html.escape(fix_explanation) if fix_explanation else "Explanation extracted from generated output."}</code></pre>
</div>

<h2>Conclusion</h2>
<p>GLM 5.2 (via Venice API as <code>zai-org-glm-5-2</code>) scored <strong>{avg:.1f}/100</strong> on this combined artistic + physics benchmark.
It is a capable low-cost model for producing interactive Canvas demos and aesthetic landing pages from rich natural-language prompts,
though polish and physical realism may require a second iteration pass for production quality.</p>

</body>
</html>"""

    save("glm-physics-benchmark-report.html", report)
    print("\nReport saved:", os.path.join(OUT_DIR, "glm-physics-benchmark-report.html"))


if __name__ == "__main__":
    run()
