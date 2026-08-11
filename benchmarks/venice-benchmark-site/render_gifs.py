#!/usr/bin/env python3
"""Render saved GIF Arena HTML entries into animated GIFs.

For each data/gif_arena/<slug>.html, drive Chrome via puppeteer-core (CDP) to
capture real-time frames, then pipe them to ffmpeg to build <slug>.gif
(12s @ 12fps = 144 frames, looped).

Requires: Chrome + ffmpeg + tools/node_modules (puppeteer-core, already
installed on this host).

Usage:
  python3 render_gifs.py            # render every *.html in data/gif_arena
  python3 render_gifs.py --slug a --slug b
  python3 render_gifs.py --fps 15 --seconds 8 --width 720
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARENA = ROOT / "data" / "gif_arena"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PUPPETEER = ROOT / "tools" / "capture_frames.js"

CAPTURE_JS = r"""
const puppeteer = require('puppeteer-core');

(async () => {
  const [url, outDir, fpsStr, secsStr, widthStr] = process.argv.slice(2);
  const fps = parseInt(fpsStr, 10), secs = parseInt(secsStr, 10);
  const width = parseInt(widthStr, 10);
  const out = require('path').resolve(outDir);
  const fs = require('fs');
  fs.mkdirSync(out, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: process.env.GIF_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars',
           '--force-color-profile=srgb', '--window-size=' + width + ',800']
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height: 800, deviceScaleFactor: 1 });
    page.on('pageerror', e => console.error('pageerror:', e.message));
    // console logs from the page (animation bugs often show here)
    page.on('console', m => { if (m.type() === 'error') console.error('page console.error:', m.text()); });

    const errors = [];
    await page.goto(url, { waitUntil: 'load', timeout: 15000 }).catch(e => errors.push('goto: ' + e.message));
    // let the animation warm up before capturing
    await new Promise(r => setTimeout(r, 1200));

    const total = fps * secs;
    const intervalMs = 1000 / fps;
    const t0 = Date.now();
    let written = 0;
    // capture by looping real time so animations run at true speed
    while (written < total && Date.now() - t0 < (secs + 4) * 1000) {
      const frame = Date.now() - t0;
      if (frame >= written * intervalMs) {
        const name = 'f' + String(written).padStart(4, '0') + '.png';
        await page.screenshot({ path: require('path').join(out, name) });
        written++;
      }
      await new Promise(r => setTimeout(r, Math.max(8, Math.floor(intervalMs / 3))));
    }
    console.log('captured ' + written + ' frames');
    if (errors.length) console.error(errors.join('\n'));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error('FATAL', e); process.exit(1); });
"""


def ensure_capture_script() -> Path:
    if not PUPPETEER.exists():
        PUPPETEER.write_text(CAPTURE_JS, encoding="utf-8")
    return PUPPETEER


def render_one(slug: str, fps: int, seconds: int, width: int) -> tuple[str, int]:
    src = ARENA / f"{slug}.html"
    if not src.exists():
        print(f"skip  {slug}: no {src.name}")
        return "", 0
    nframes = fps * seconds
    with tempfile.TemporaryDirectory(prefix="gifarena-") as td:
        tmp = Path(td)
        frames_dir = tmp / "frames"
        script = ensure_capture_script()
        r = subprocess.run(
            ["node", str(script), "file://" + str(src.resolve()),
             str(frames_dir), str(fps), str(seconds), str(width)],
            capture_output=True, timeout=(seconds + 30))
        if r.returncode != 0:
            print(f"skip  {slug}: capture failed\n  {r.stdout.decode()[:200]}\n  {r.stderr.decode()[:400]}")
            return "", 0
        frame_files = sorted(frames_dir.glob("f*.png"))
        if len(frame_files) < 6:
            print(f"skip  {slug}: only {len(frame_files)} frames")
            return "", 0

        out = ARENA / f"{slug}.gif"
        listfile = tmp / "frames.txt"
        lines = []
        for f in frame_files:
            lines.append(f"file '{f.resolve()}'\nduration {1/fps:.4f}\n")
        lines.append(f"file '{frame_files[-1].resolve()}'\n")
        listfile.write_text("".join(lines), encoding="utf-8")

        pal = tmp / "palette.png"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
             "-vf", "palettegen=stats_mode=diff", str(pal)],
            capture_output=True, timeout=120)
        r = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
             "-i", str(pal), "-lavfi", "paletteuse=dither=bayer:bayer_scale=5",
             "-loop", "0", str(out)],
            capture_output=True, timeout=180)
        if not out.exists() or out.stat().st_size < 5000:
            print(f"skip  {slug}: ffmpeg failed\n  {r.stderr.decode()[:400]}")
            return "", 0
        size = out.stat().st_size
        print(f"gif   {slug}  {size/1024:.0f} KB  ({len(frame_files)} frames)")
        return out.name, size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append")
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--seconds", type=int, default=9)
    ap.add_argument("--width", type=int, default=720)
    args = ap.parse_args()

    ARENA.mkdir(parents=True, exist_ok=True)
    slugs = args.slug or [p.stem for p in sorted(ARENA.glob("*.html"))
                          if not p.name.endswith(".meta.json")]
    results = {}
    for s in slugs:
        name, size = render_one(s, args.fps, args.seconds, args.width)
        if name:
            results[s] = {"gif": name, "size": size}
    (ARENA / "_render_status.json").write_text(
        json.dumps({"fps": args.fps, "seconds": args.seconds,
                    "rendered": results}, indent=2), encoding="utf-8")
    print(f"\nrendered {len(results)} GIF(s) -> {ARENA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
