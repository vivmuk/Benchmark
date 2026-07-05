#!/usr/bin/env python3
"""Generate a fully self-contained benchmarkviv-standalone.html."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

def read_text(name):
    return (BASE / name).read_text(encoding="utf-8")

def read_json(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))

html = read_text("index.html")
css = read_text("assets/styles.css")
js = read_text("assets/app.js")
data = read_json("data/results.json")
game = read_text("brick-game-demo.html")

# Inline CSS
html = html.replace(
    '<link rel="stylesheet" href="assets/styles.css" />',
    f"<style>\n{css}\n</style>"
)

# Inline JS
html = html.replace(
    '<script src="assets/app.js"></script>',
    f"<script>\n{js}\n</script>"
)

# Replace data fetch with embedded data variable + make loadData use it
json_data = json.dumps(data)
html = html.replace(
    '<script>\n/* BenchmarkViv',
    f'<script>\nwindow.BENCHMARK_DATA = {json_data};\n/* BenchmarkViv'
)

# Patch loadData to use embedded data when fetch fails or data is embedded
html = html.replace(
    "const DATA_URL = \"data/results.json\";",
    "const DATA_URL = \"data:application/json;base64,\";"
)

# Better: just change loadData to use window.BENCHMARK_DATA directly
html = html.replace(
    """  async function loadData() {
    const status = $("#dataStatus");
    try {
      const res = await fetch(DATA_URL, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (!Array.isArray(json.results) || json.results.length === 0) throw new Error("No results");""",
    """  async function loadData() {
    const status = $("#dataStatus");
    try {
      const json = window.BENCHMARK_DATA || {};
      if (!Array.isArray(json.results) || json.results.length === 0) throw new Error("No results");"""
)

# Remove the catch fallback assignment since we're using embedded data
html = html.replace(
    """    } catch (err) {
      console.warn("[BenchmarkViv] fallback data:", err.message);
      state.data = FALLBACK_DATA.results;
      state.isLive = false;
      if (status) {
        status.textContent = "● Sample data";
        status.classList.add("fallback");
      }
    }""",
    """    } catch (err) {
      console.warn("[BenchmarkViv] fallback data:", err.message);
      state.data = FALLBACK_DATA.results;
      state.isLive = false;
      if (status) {
        status.textContent = "● Sample data";
        status.classList.add("fallback");
      }
    }
    state.isLive = true;
    if (status) {
      status.textContent = "● Live data";
      status.classList.remove("fallback");
    }"""
)

# Inline brick game into iframe srcdoc
import html as html_module
escaped_game = html_module.escape(game)
html = html.replace(
    '<iframe id="gameFrame" src="brick-game-demo.html" title="Brick Breaker Realism demo" loading="lazy"></iframe>',
    f'<iframe id="gameFrame" srcdoc="{escaped_game}" title="Brick Breaker Realism demo" loading="lazy"></iframe>'
)

out_path = BASE / "benchmarkviv-standalone.html"
out_path.write_text(html, encoding="utf-8")
print(f"Wrote {out_path} ({len(html):,} chars)")
