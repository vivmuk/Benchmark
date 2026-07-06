#!/usr/bin/env python3
import os
"""Quick test for both models."""
import requests
import json
import time

API_URL = "https://api.venice.ai/api/v1/chat/completions"
API_KEY = os.environ.get("VENICE_INFERENCE_KEY", "")

def call_model(model, prompt, max_tokens=500):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    start = time.time()
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    elapsed = time.time() - start
    data = resp.json()
    
    # Extract content - handle reasoning models
    choice = data["choices"][0]["message"]
    content = choice.get("content", "")
    reasoning = choice.get("reasoning_content", "")
    
    usage = data.get("usage", {})
    tokens = f"prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}"
    
    return {
        "status": "success" if resp.status_code == 200 else f"error:{resp.status_code}",
        "time": elapsed,
        "content": content,
        "reasoning": reasoning,
        "tokens": tokens,
    }

# Test both models with a simple prompt
print("=" * 60)
print("Quick Test: Kimi K2.7-Code vs MiMo-V2.5")
print("=" * 60)

test_prompt = "What is 2+2? Answer in one sentence."
print(f"\nPrompt: {test_prompt}\n")

for name, model_id in [("Kimi K2.7-Code", "kimi-k2-7-code"), ("MiMo-V2.5", "xiaomi-mimo-v2-5")]:
    print(f"--- {name} ---")
    result = call_model(model_id, test_prompt)
    print(f"Status: {result['status']}")
    print(f"Time: {result['time']:.2f}s")
    print(f"Tokens: {result['tokens']}")
    if result['reasoning']:
        print(f"Reasoning: {result['reasoning'][:200]}")
    print(f"Content: {result['content'][:200]}")
    print()
