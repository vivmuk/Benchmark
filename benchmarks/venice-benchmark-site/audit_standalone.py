#!/usr/bin/env python3
import json

d = json.load(open("data/results.json"))
s = open("benchmarkviv-standalone.html").read()

print("=== Standalone audit ===")
print(f"Models in data: {len(d['models'])}")
print(f"Standalone size: {len(s):,} chars")
print(f"window.BENCHMARK_DATA count: {s.count('window.BENCHMARK_DATA')}")
print(f"Has new models:", s.count("gemini-3-7-flash") > 0 and s.count("grok-4-20") > 0 and s.count("aion-labs-aion-3-0") > 0)
print(f"gemini-3-7-flash: {s.count('gemini-3-7-flash')}")
print(f"grok-4-20: {s.count('grok-4-20')}")
print(f"aion-labs-aion-3-0: {s.count('aion-labs-aion-3-0')}")
print(f"deepseek-v4-flash: {s.count('deepseek-v4-flash')}")
print(f"qwen3-235b: {s.count('qwen3-235b')}")
print(f"minimax-m27: {s.count('minimax-m27')}")

# changelog
if "data/changelog.json" in d:
    print(f"\nChangelog entries: {len(d.get('changelog',[]))}")

print("\nDONE")