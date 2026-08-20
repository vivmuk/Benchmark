#!/usr/bin/env python3
"""Generate a fully self-contained benchmarkviv-standalone.html.

The index.html source uses cache-busted URLs `assets/styles.css?v=4`, so the
replacement patterns tolerate an optional query string. Earlier versions of
this script used the bare URL strings and silently returned a near-empty copy.
"""
import json
import re
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

# 1. Inline CSS (tolerant of cache-buster ?v=N)
css_pattern = re.compile(
    r'<link\s+rel="stylesheet"\s+href="assets/styles\.css(?:\?v=\d+)?"\s*/?>'
)
new_html, n_css = css_pattern.subn(f"<style>\n{css}\n</style>", html)
print(f"  inline CSS                -> {n_css} replacement(s)")
html = new_html

# 2. Inline JS (tolerant of cache-buster ?v=N)
js_pattern = re.compile(
    r'<script\s+src="assets/app\.js(?:\?v=\d+)?"\s*></script>'
)
new_html, n_js = js_pattern.subn(f"<script>\n{js}\n</script>", html)
print(f"  inline app.js              -> {n_js} replacement(s)")
html = new_html

# 3. Inject BENCHMARK_DATA into <head>.
# `ensure_ascii=False` avoids Python's `\uXXXX` escapes in the JSON output that
# would otherwise be mis-parsed as re template escapes by re.subn.
# `</script>` inside raw responses (generated HTML from UI/arcade tracks) would
# terminate the inline script tag and dump raw text into the page. Escape the
# closing tag as `\u003c/script` (the JSON string escape, which JS decodes
# back to the literal). Same for `<!--` to stay safe against legacy comment
# shenanigans in HTML parsers.
json_data = json.dumps(data, ensure_ascii=False)
json_data = json_data.replace("</script", "\\u003c/script").replace("<!--", "\\u003c!--")
inject_script = f'<script>window.BENCHMARK_DATA = {json_data};</script>'
new_html, n_inject = re.subn(
    r"<head>\s*", lambda m: "<head>\n" + inject_script + "\n", html, count=1
)
print(f"  attach BENCHMARK_DATA in <head>  -> {n_inject} replacement(s)")
html = new_html

# 4. Rewrite loadData() to read from window.BENCHMARK_DATA first.
loadData_old = '''  async function loadData() {
    const status = $("#dataStatus");
    try {
      const res = await fetch(DATA_URL, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (!Array.isArray(json.results) || json.results.length === 0) throw new Error("No results");'''
loadData_new = '''  async function loadData() {
    const status = $("#dataStatus");
    try {
      const json = window.BENCHMARK_DATA || {};
      if (!Array.isArray(json.results) || json.results.length === 0) throw new Error("No results");'''
if loadData_old in html:
    html = html.replace(loadData_old, loadData_new)
    print("  patch loadData()           -> 1 replacement(s)")
else:
    print("  patch loadData()           -> pattern not found (may already be patched)")

# 5. Append "Live data" status indicator.
catch_old = '''    } catch (err) {
      console.warn("[BenchmarkViv] fallback data:", err.message);
      state.data = FALLBACK_DATA.results;
      state.isLive = false;
      if (status) {
        status.textContent = "● Sample data";
        status.classList.add("fallback");
      }
    }'''
catch_new = catch_old + '''
    state.isLive = true;
    if (status) {
      status.textContent = "● Live data";
      status.classList.remove("fallback");
    }'''
if catch_old in html and "● Live data" not in html:
    html = html.replace(catch_old, catch_new)
    print("  patch catch block (Live)   -> 1 replacement(s)")
else:
    print("  patch catch block (Live)   -> pattern not found (may already be patched)")

# 6. Arcade/game iframe removed from site.
print("  skip game iframe            -> arcade removed")

out_path = BASE / "benchmarkviv-standalone.html"
out_path.write_text(html, encoding="utf-8")
print(f"\nWrote {out_path} ({len(html):,} chars)")

# ─── Build about-standalone.html ────────────────────────────────────────────
# Mirrors the same procedure for the about page: CSS + app.js inlined,
# CHANGELOG_DATA spliced into <head>, so offline readers get the same render.
print("\n─── Building about-standalone.html ───")
if (BASE / "about.html").exists():
    about_html = read_text("about.html")
    changelog = read_json("data/changelog.json")

    new_about, _ = css_pattern.subn(f"<style>\n{css}\n</style>", about_html)
    about_html = new_about
    new_about, _ = js_pattern.subn(f"<script>\n{js}\n</script>", about_html)
    about_html = new_about

    # Splice CHANGELOG_DATA into <head> so the page works offline (same
    # ensure_ascii=False trick to avoid Python re.template `\uXXXX` clash).
    changelog_json = json.dumps(changelog, ensure_ascii=False)
    inject_changelog = f'<script>window.CHANGELOG_DATA = {changelog_json};</script>'
    new_about, _ = re.subn(
        r"<head>\s*", f"<head>\n{inject_changelog}\n", about_html, count=1
    )
    about_html = new_about

    about_out = BASE / "about-standalone.html"
    about_out.write_text(about_html, encoding="utf-8")
    print(f"  Wrote {about_out} ({len(about_html):,} chars)")
else:
    print("  about.html not present; skipping about-standalone.html")
