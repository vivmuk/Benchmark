#!/usr/bin/env python3
"""Check which vision-ok models lack recon renders, then render missing ones via Venice image API."""
import json, os, sys, time, base64, re, io
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent
RECON = ROOT / "data" / "vision" / "reconstructions.json"
MANIFEST = ROOT / "data" / "vision" / "recon_images_manifest.json"
ING_DIR = ROOT / "data" / "vision" / "recon_images"

rec = json.load(open(RECON))
man = {}
if MANIFEST.exists():
    man = json.load(open(MANIFEST))

have = set()
for f in ING_DIR.glob("*.web.jpg"):
    have.add(f.stem.replace(".web", ""))

print("=== vision-ok models vs recon renders ===")
missing = []
for r in rec["results"]:
    mid = r["model_id"]
    has = mid in have or mid.replace("/", "-") in have
    print(f"  {mid:40s} render={'YES' if has else 'NO'} score={r['score']}")
    if not has:
        missing.append(mid)

print(f"\nMissing renders: {len(missing)}")
for m in missing:
    print("  ", m)