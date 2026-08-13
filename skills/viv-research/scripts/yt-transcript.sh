#!/usr/bin/env bash
# YouTube transcript: fetch captions via yt-dlp; fall back to Venice speech-to-text.
# Usage: yt-transcript.sh <youtube-url> [output-dir]
set -euo pipefail
URL="${1:?usage: yt-transcript.sh <youtube-url> [output-dir]}"
OUT="${2:-.}"
VENICE="${VENICE:-$HOME/.openclaw/workspace/skills/venice-ai/scripts/venice.py}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"

if yt-dlp --skip-download --write-auto-sub --write-subs \
    --sub-langs "en.*" --sub-format vtt "$URL" -o "%(id)s.%(ext)s" >/dev/null 2>&1 \
    && compgen -G '*.vtt' >/dev/null; then
  python3 - "$OUT" <<'PY'
import glob, html, re, sys
out = sys.argv[1]
chunks = []
for f in sorted(glob.glob("*.vtt")):
    text = open(f, encoding="utf-8", errors="ignore").read()
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or "-->" in ln or ln.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")):
            continue
        ln = re.sub(r"<[^>]+>", "", ln)
        ln = html.unescape(ln)
        if ln and (not lines or lines[-1] != ln):
            lines.append(ln)
    if lines:
        chunks.append("\n".join(lines))
full = "\n\n".join(chunks)
path = f"{out}/transcript.md" if out != "." else "transcript.md"
open(path, "w", encoding="utf-8").write(full)
print(f"saved: {path} ({len(full)} chars)")
PY
else
  echo "No captions; downloading audio for Venice transcription..." >&2
  yt-dlp -f "bestaudio/best" -x --audio-format mp3 "$URL" -o "audio.%(ext)s" >/dev/null 2>&1
  python3 "$VENICE" transcribe audio.mp3 --timestamps
fi
