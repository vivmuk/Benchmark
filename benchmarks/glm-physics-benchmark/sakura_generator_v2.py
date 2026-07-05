#!/usr/bin/env python3
"""
Generate improved Sakura website v2 with explicit petal physics requirements.
"""
import os, time, requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
API_KEY = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get("VENICE_API_KEY")
if not API_KEY:
    raise RuntimeError("VENICE_INFERENCE_KEY or VENICE_API_KEY env var must be set")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

PROMPT = """Create a single, self-contained HTML file for a premium Japanese "SAKURA" landing page.

CRITICAL: The file MUST include a working JavaScript block that animates falling sakura petals on an HTML5 canvas layered over the page. If you do not include the <script> code that actually moves petals, the file is useless.

Visual style:
- Traditional sumi-e ink wash painting style.
- Soft cream/parchment paper-textured background with subtle grain.
- Japanese cherry blossom branches drawn with SVG, using ink-brush stroke filters (feTurbulence + feDisplacementMap).
- Large elegant Japanese-inspired serif typography for "SAKURA" and a poetic tagline.
- Minimal navigation bar: Home, Story, Collection, Visit.
- Responsive, full-bleed hero section.
- Soft palette: cream, pale pink, dusty rose, charcoal ink.
- No external images; use SVG, CSS gradients, and inline JS only.

Petal physics requirements (these are MANDATORY and must be implemented in JS):
1. Use a full-screen <canvas id="petalCanvas"> absolutely positioned on top of the page with pointer-events:none.
2. Create a Petal class. Each petal has: x, y, size (2px to 8px), rotation angle, rotation speed, vertical fall speed between 0.3 and 1.2 pixels per frame, horizontal sway amplitude between 0.5 and 2.5 pixels, sway phase, and opacity between 0.4 and 0.9.
3. Petals spawn continuously at the top at a rate of roughly 1-2 petals per frame, with randomized x position across the full width.
4. Petals fall slowly downward. Update each frame using requestAnimationFrame.
5. Each petal sways horizontally using a sine function with its own phase and frequency.
6. Each petal rotates slowly as it falls.
7. Add occasional wind gusts: every 3-8 seconds, apply a brief horizontal force that pushes all petals in one direction for about 1.5 seconds, then subsides.
8. When a petal reaches the bottom, reset it to the top with new randomized properties (recycle, don't delete).
9. Petals should fade in during the first 10% of their fall and fade out during the last 10%.
10. Use at least 60 petals on screen at once.

Return ONLY the complete HTML file inside a ```html code block. Make sure the closing </html> tag is present and the <script> is complete."""

def call_model(model_id, prompt, max_tokens=12000):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }
    start = time.time()
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    elapsed = time.time() - start
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    content = data["choices"][0]["message"].get("content", "")
    usage = data.get("usage", {})
    return {
        "response": content,
        "latency": elapsed,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }

def extract_html(text):
    import re
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

models = {
    "fable-5": "claude-fable-5",
    "glm-5-2": "zai-org-glm-5-2",
}

results = []
for label, model_id in models.items():
    print(f"\n=== Generating with {label} ===")
    try:
        result = call_model(model_id, PROMPT, max_tokens=12000)
        html = extract_html(result["response"])
        filename = f"sakura-site-{label}-v2.html"
        save(filename, html)
        print(f"Saved {filename} ({len(html)} chars)")
        print(f"Latency: {result['latency']:.1f}s | Tokens: {result['total_tokens']}")
        results.append({"label": label, "file": filename, "ok": True})
    except Exception as e:
        print(f"FAILED {label}: {e}")
        results.append({"label": label, "ok": False, "error": str(e)})

save("sakura-prompt-v2.txt", PROMPT)
print("\nDone.")
for r in results:
    print(r)
