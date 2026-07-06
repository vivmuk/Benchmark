#!/usr/bin/env python3
"""
Generate improved Sakura website with slow-falling petals
using Fable 5 and GLM 5.2 via Venice API.
"""
import os, time, requests

API_URL = "https://api.venice.ai/api/v1/chat/completions"
API_KEY = os.environ.get("VENICE_INFERENCE_KEY") or os.environ.get(os.environ.get("VENICE_INFERENCE_KEY", ""))
if not API_KEY:
    raise RuntimeError("VENICE_INFERENCE_KEY not set")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

PROMPT = """Create a single, self-contained HTML file for a premium Japanese "SAKURA" landing page in traditional sumi-e ink wash painting style.

Aesthetic requirements:
- Soft cream/parchment paper-textured background with subtle grain.
- Japanese cherry blossom (sakura) branches drawn with SVG, using ink-brush stroke filters (feTurbulence + feDisplacementMap) and soft pink blossoms.
- Large elegant Japanese-inspired serif typography for "SAKURA" and a poetic tagline.
- Falling sakura petals using a lightweight JavaScript particle system. CRITICAL: petals must fall slowly, gently, and gracefully — like real cherry blossom petals in a light breeze. They should drift side-to-side (sinusoidal horizontal sway), rotate softly as they fall, and have varied sizes/opacity. Add occasional upward gusts and periodic breezes. Use opacity fade-in at spawn and fade-out near the bottom.
- Subtle parallax depth: background ink wash, midground branches, foreground petals.
- Minimal navigation bar: Home, Story, Collection, Visit.
- Responsive, full-bleed hero section.
- No external images; generate everything with SVG, CSS gradients, and inline JS.
- Use a soft, limited color palette: cream, pale pink, dusty rose, charcoal ink.

Return ONLY the complete HTML file inside a ```html code block."""

def call_model(model_id, prompt, max_tokens=12000):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.5,
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
        filename = f"sakura-site-{label}.html"
        save(filename, html)
        print(f"Saved {filename} ({len(html)} chars)")
        print(f"Latency: {result['latency']:.1f}s | Tokens: {result['total_tokens']}")
        results.append({"label": label, "file": filename, "ok": True})
    except Exception as e:
        print(f"FAILED {label}: {e}")
        results.append({"label": label, "ok": False, "error": str(e)})

# Also save the prompt
save("sakura-prompt.txt", PROMPT)
print("\nDone.")
for r in results:
    print(r)
