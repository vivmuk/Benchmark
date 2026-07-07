#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/benchmarks/venice-benchmark-site"
exec python3 -m http.server "${PORT:-8080}" --bind 0.0.0.0
