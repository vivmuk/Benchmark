#!/usr/bin/env python3
"""
generate_infographics.py — field-notes infographics: per-item (daily) + summary (weekly).

Reads a JSON archive (database.json) and generates, via the Venice image API
(grok-imagine-image-2-0, aspect 9:16 @2K), two kinds of images:

  1. Daily: one infographic per item  -> {out}/ep{NN}-{slug}.png
  2. Weekly: one summary per 7-day week from series start -> {out}/weekly-week{N}.png

Idempotent: existing files are skipped (state = file existence). Output is
mirrored into a site dir (for Railway/GH Pages deploys) + a manifest.json written.

USAGE: python3 generate_infographics.py [--db database.json] [--out infographics]
       [--site SITE_DIR] [--brand "MESSY ACTION"] [--series "100 Days of Messy Action"] [--limit N]
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL = "grok-imagine-image-2-0"
ENDPOINT = "https://api.venice.ai/api/v1/image/generate"
# Verified 2026-08-13: model spec promptCharacterLimit = 7500; a 2120-char prompt
# generated fine. (The 1500-char cap applies ONLY to /images/generations.)
PROMPT_CAP = 7000  # safe margin under the 7500 limit


def api_key():
    """Read VENICE_API_KEY from the gateway env file."""
    r = subprocess.run(
        ["grep", "-o", "VENICE_API_KEY=[^ ]*",
         os.path.expanduser("~/.openclaw/service-env/ai.openclaw.gateway.env")],
        capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("VENICE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("VENICE_API_KEY not found in ~/.openclaw/service-env/ai.openclaw.gateway.env")


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:40] or "item"


def clamp(p):
    return p[:PROMPT_CAP].rstrip() + ("…" if len(p) > PROMPT_CAP else "")


def generate(prompt, key, out_path, attempts=3):
    body = json.dumps({
        "model": MODEL,
        "prompt": clamp(prompt),
        "aspect_ratio": "9:16",
        "resolution": "2K",
        "format": "png",
        "safe_mode": False,
    }).encode()
    for a in range(1, attempts + 1):
        try:
            req = urllib.request.Request(ENDPOINT, data=body, headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            })
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode())
            imgs = data.get("images") or data.get("data", [{}])[0].get("b64_json")
            if isinstance(imgs, list) and imgs and isinstance(imgs[0], str):
                imgs = imgs[0]
            if isinstance(imgs, list) and imgs and isinstance(imgs[0], dict):
                imgs = imgs[0].get("b64_json")
            if not imgs:
                raise RuntimeError(f"no image in response: {str(data)[:200]}")
            raw = base64.b64decode(imgs)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(raw)
            print(f"OK  {os.path.basename(out_path)} ({len(raw)//1024} KB, attempt {a})")
            return True
        except Exception as e:
            print(f"FAIL attempt {a} for {os.path.basename(out_path)}: {e}", file=sys.stderr)
            if a < attempts:
                time.sleep(8 * a)
    return False


def daily_prompt(e, total, brand="MESSY ACTION", series="100 Days of Messy Action"):
    return (
        f"Vertical 9:16 Instagram infographic, hand-drawn 'field notes' journal aesthetic for the "
        f"'{series}' series. Cream paper background (#FEFCF8) with torn edges, washi tape, "
        f"sticky notes and coffee-stain textures; handwriting-style annotations, arrows and underlines in teal "
        f"#00D4AA and indigo #1A1A2E. Top header band: '{brand} — EPISODE {e['ep']}' with date {e['date']} in a stamp. "
        f"Big bold title: '{e['title']}'. Center field-note card with the key message: '{e['key_message']}'. "
        f"Quote in a hand-drawn speech bubble: '{e['quote']}'. Small tag chip: #{e['tag']}. "
        f"Footer: '{series} — episode {e['ep']} of {total}'. Clean readable typography, not cluttered."
    )


def weekly_prompt(eps, week_label, total, brand="MESSY ACTION", series="100 Days of Messy Action"):
    lines = [f"- {e['date']} ep{int(e['ep'])}: {e['title']} — {e['key_message']}" for e in eps]
    listing = " | ".join(lines)
    return (
        f"Vertical 9:16 Instagram summary infographic, hand-drawn 'field notes' journal aesthetic for the "
        f"'{series}' 100-episode series. Cream paper background (#FEFCF8), torn edges, washi tape, "
        f"sticky notes, coffee stains; teal #00D4AA and indigo #1A1A2E handwritten annotations, arrows, underlines. "
        f"Top banner: '{brand} — WEEKLY FIELD NOTES' and '{week_label}'. Center: a notebook page titled "
        f"'This week's field notes' listing each episode of the week: {listing}. "
        f"Bottom badge: 'Week of the 100-day series — {total} episodes so far'. Hand-drawn, warm, inspiring, "
        f"clean readable typography, not cluttered."
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(DEFAULT_DIR, "database.json"), help="input JSON archive")
    ap.add_argument("--out", default=os.path.join(DEFAULT_DIR, "infographics"), help="output dir")
    ap.add_argument("--site", default=os.path.expanduser("~/.openclaw/workspace/messy-action-site/infographics"),
                    help="mirror dir for deploys (empty = no mirror)")
    ap.add_argument("--brand", default="MESSY ACTION", help="brand text in prompts")
    ap.add_argument("--series", default="100 Days of Messy Action", help="series title in prompts")
    ap.add_argument("--limit", type=int, default=0, help="max images to generate (0 = unlimited)")
    args = ap.parse_args()

    db = json.load(open(args.db))
    eps = sorted(db["episodes"], key=lambda e: e["ep"])
    key = api_key()
    os.makedirs(args.out, exist_ok=True)
    total = len(eps)
    made = 0
    failures = []

    # --- daily per-episode infographics ---
    for e in eps:
        fname = f"ep{int(e['ep']):02d}-{slugify(e['title'])}.png"
        out = os.path.join(args.out, fname)
        if os.path.exists(out):
            print(f"SKIP {fname} (exists)")
            continue
        if generate(daily_prompt(e, total, args.brand, args.series), key, out):
            made += 1
        else:
            failures.append(fname)
        if args.limit and made >= args.limit:
            break

    # --- weekly summaries (one per 7-day week from series start) ---
    if eps:
        start = dt.date.fromisoformat(eps[0]["date"])
    weeks = {}
    for e in eps:
        d = dt.date.fromisoformat(e["date"])
        wnum = (d - start).days // 7 + 1
        weeks.setdefault(wnum, []).append(e)
    for wnum, weps in sorted(weeks.items()):
        d0 = dt.date.fromisoformat(weps[0]["date"])
        d1 = dt.date.fromisoformat(weps[-1]["date"])
        label = f"Week {wnum} ({d0.strftime('%b %-d')}–{d1.strftime('%b %-d')})"
        out = os.path.join(args.out, f"weekly-week{wnum}.png")
        if os.path.exists(out):
            print(f"SKIP weekly-week{wnum} (exists)")
            continue
        if generate(weekly_prompt(weps, label, total, args.brand, args.series), key, out):
            made += 1
        else:
            failures.append(os.path.basename(out))
        if args.limit and made >= args.limit:
            break

    # --- mirror to site dir for deploy + write manifest ---
    files = sorted(os.listdir(args.out))
    copied = 0
    if args.site:
        os.makedirs(args.site, exist_ok=True)
        for f in files:
            src, dst = os.path.join(args.out, f), os.path.join(args.site, f)
            if os.path.isfile(src) and (not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)):
                shutil.copy2(src, dst)
                copied += 1
    manifest = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "dailies": [f for f in files if f.startswith("ep") and f.endswith(".png")],
        "weekly": [f for f in files if f.startswith("weekly-") and f.endswith(".png")],
    }
    for d in (args.out, args.site):
        if d:
            with open(os.path.join(d, "manifest.json"), "w") as fh:
                json.dump(manifest, fh, indent=1)
    print(f"MIRRORED {copied} files to {args.site}; manifest written "
          f"(dailies={len(manifest['dailies'])}, weekly={len(manifest['weekly'])})")
    print(f"DONE: {made} generated, {len(failures)} failed" + (f" — {failures}" if failures else ""))


if __name__ == "__main__":
    main()
