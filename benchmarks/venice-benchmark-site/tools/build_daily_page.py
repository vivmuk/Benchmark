#!/usr/bin/env python3
"""Build/update the Daily Video tab (video-daily.html) + inject nav item site-wide.

Usage: python3 tools/build_daily_page.py   (run from benchmarks/venice-benchmark-site/)
Reads assets/daily-videos/manifest.json (newest entry = featured video).
Idempotent: safe to run daily after adding a manifest entry.
"""
import json
import re
import glob

NAV_ANCHOR = 'href="video-benchmark.html"'
NAV_ITEM = (
    '<li><a href="video-daily.html"><svg class="sb-ico" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
    'aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" />'
    '<path d="M10 9l5 3l-5 3z" /></svg><span>Daily Video</span></a></li>'
)

manifest = json.load(open('assets/daily-videos/manifest.json'))
videos = sorted(manifest['videos'], key=lambda v: v['date'], reverse=True)
latest = videos[0]

TEMPLATE = open('video-benchmark.html').read()

MAIN_CONTENT = '''<main style="position:relative;z-index:1;">
  <div class="container">
    <section style="max-width:980px;margin:0 auto;padding:2.5rem 1.5rem 3rem">
      <h1 style="font-size:2rem;margin-bottom:.4rem">Daily Video</h1>
      <p style="color:#9aa3b2;margin-bottom:1.6rem">One AI-generated video every day — made on Venice, featured here. Today's pick plays below; the archive grows beneath it.</p>
      <div id="daily-hero" style="margin-bottom:1rem"></div>
      <div id="daily-meta" style="display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem"></div>
      <p id="daily-prompt" style="color:#9aa3b2;font-size:.95rem;margin-bottom:2rem"></p>
      <h2 style="font-size:1.3rem;margin-bottom:.8rem">Archive</h2>
      <div id="daily-archive" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem"></div>
    </section>
  </div>
  <script>
  (function () {
    fetch('assets/daily-videos/manifest.json').then(function (r) { return r.json(); }).then(function (m) {
      var vids = m.videos.slice().sort(function (a, b) { return b.date.localeCompare(a.date); });
      var esc = function (s) { var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; };
      function show(v) {
        var hero = document.getElementById('daily-hero');
        hero.innerHTML = '';
        var el = document.createElement('video');
        el.controls = true; el.playsInline = true; el.preload = 'metadata';
        el.style.width = '100%'; el.style.borderRadius = '14px'; el.style.display = 'block';
        el.style.background = '#0d0d18'; el.src = v.file;
        hero.appendChild(el);
        var meta = document.getElementById('daily-meta');
        meta.innerHTML = [v.date, v.model, v.duration, v.resolution].map(function (t) {
          return '<span style="background:rgba(0,212,170,.12);color:#00D4AA;padding:.25rem .7rem;border-radius:999px;font-size:.8rem">' + esc(t) + '</span>';
        }).join('');
        document.getElementById('daily-prompt').textContent = v.prompt || '';
      }
      show(vids[0]);
      var arch = document.getElementById('daily-archive');
      vids.slice(1).forEach(function (v) {
        var card = document.createElement('button');
        card.type = 'button';
        card.style.cssText = 'text-align:left;background:#141428;border:1px solid rgba(0,212,170,.25);border-radius:12px;padding:.8rem;color:#FEFCF8;cursor:pointer';
        card.innerHTML = '<div style="font-weight:600;margin-bottom:.3rem">' + esc(v.title || v.date) + '</div>' +
          '<div style="color:#9aa3b2;font-size:.8rem">' + esc(v.date) + ' &middot; ' + esc(v.model) + '</div>';
        card.addEventListener('click', function () { show(v); window.scrollTo({ top: 0, behavior: 'smooth' }); });
        arch.appendChild(card);
      });
      if (!vids.slice(1).length) arch.innerHTML = '<p style="color:#9aa3b2">First entry — the archive starts tomorrow.</p>';
    });
  })();
  </script>
</main>'''

page = re.sub(r'<main[^>]*>.*?</main>', lambda m: MAIN_CONTENT, TEMPLATE, count=1, flags=re.S)
page = re.sub(r'<title>.*?</title>', '<title>Daily Video — BenchmarkViv</title>', page, count=1, flags=re.S)

def inject_nav(html):
    if 'video-daily.html' in html:
        return html
    i = html.find(NAV_ANCHOR)
    if i == -1:
        return html
    j = html.find('</li>', i)
    return html[:j + 5] + '\n    ' + NAV_ITEM + html[j + 5:]

page = inject_nav(page)
open('video-daily.html', 'w').write(page)
print('video-daily.html written; featured:', latest['date'], latest['model'])

changed = []
for path in sorted(glob.glob('*.html')):
    if path == 'video-daily.html':
        continue
    html = open(path).read()
    new = inject_nav(html)
    if new != html:
        open(path, 'w').write(new)
        changed.append(path)
print('nav injected into', len(changed), 'pages:', ', '.join(changed) if changed else '(none)')
