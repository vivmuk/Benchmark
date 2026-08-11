#!/usr/bin/env python3
"""Generate BenchmarkViv infographic (DeepSeek V4 Flash 0731) via Venice image API."""
import json, os, re, requests, sys, base64, time

def load_key():
    txt = open("/Users/vivgatesai/.openclaw/service-env/ai.openclaw.gateway.env").read()
    m = re.search(r"^(?:export )?VENICE_API_KEY=[\'\"]?(.*?)[\'\"]?$", txt, re.M)
    return m.group(1)

KEY = load_key()

prompt = (
    "Sleek data infographic titled 'BenchmarkViv 2026'. Center hero badge: deep-teal "
    "rectangular card labeled 'DeepSeek V4 Flash 0731' with a big bold rank '#4 OF 17' "
    "and a VivIndex score bar showing '89.7 / 100'. Around it a clean horizontal bar "
    "chart comparing top models by VivIndex: GPT-5.5 = 92.5, GPT-5.6 Terra = 92.2, "
    "GPT-5.6 Sol = 90.9, DeepSeek V4 Flash 0731 = 89.7, GPT-5.6 Luna = 88.6, Kimi K3 "
    "= 86.5. A small grid of category chips on the right listing benchmark scores: "
    "Value Density 100, One-Shot UI 95, Startup-in-a-Weekend 94, Drug Interaction 89, "
    "Regulatory 80, Intent 70. Bottom banner reads 'Cost-efficient flash-tier model "
    "rivals frontier flagship quality'. Modern pharma-professional design, cream "
    "#FEFCF8 background, teal #00D4AA accents, indigo #1A1A2E text, watercolor wash, "
    "clean sans-serif, sharp legible numbers, high fidelity, no typos."
)

def gen(model):
    url = "https://api.venice.ai/api/v1/images/generations"
    payload = {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload, timeout=300)
    print(model, "status", r.status_code)
    if r.status_code != 200:
        print(r.text[:500])
        return None
    data = r.json()
    item = data.get("data", [{}])[0]
    if item.get("b64_json"):
        raw = base64.b64decode(item["b64_json"])
        out = f"infographic_{model}.png"
        open(out, "wb").write(raw)
        print("saved", out, len(raw), "bytes")
        return out
    if item.get("url"):
        print("URL:", item["url"])
        return item["url"]
    print(json.dumps(data)[:500])
    return None

if __name__ == "__main__":
    gen("gpt-image-2")
