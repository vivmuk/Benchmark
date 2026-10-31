#!/usr/bin/env bash
# Batch-convert research assets to Markdown with MarkItDown.
# Usage: ingest.sh <input-dir> [output-dir]
set -euo pipefail
IN="${1:?usage: ingest.sh <input-dir> [output-dir]}"
OUT="${2:-$IN/md}"
mkdir -p "$OUT"
converted=0; failed=0; skipped=0
while IFS= read -r -d '' f; do
  rel="${f#$IN/}"
  out="$OUT/${rel%.*}.md"
  mkdir -p "$(dirname "$out")"
  if [[ -f "$out" ]]; then
    echo "-- exists: $rel"
    skipped=$((skipped+1))
    continue
  fi
  echo ">> $rel"
  if markitdown "$f" -o "$out" 2>/dev/null; then
    converted=$((converted+1))
  else
    echo "!! failed (skipped): $rel"
    failed=$((failed+1))
  fi
done < <(find "$IN" -type f \( -iname '*.pdf' -o -iname '*.docx' -o -iname '*.doc' -o -iname '*.pptx' -o -iname '*.xlsx' -o -iname '*.xls' -o -iname '*.html' -o -iname '*.htm' -o -iname '*.epub' -o -iname '*.csv' -o -iname '*.json' -o -iname '*.xml' \) -print0)
echo "Done: $converted converted, $skipped cached, $failed failed -> $OUT"
