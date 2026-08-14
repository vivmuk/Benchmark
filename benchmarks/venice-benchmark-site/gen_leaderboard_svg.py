#!/usr/bin/env python3
"""Regenerate leaderboard_chart.svg + trends from current snapshot (37 models)."""
import json

snap = json.load(open("data/chart_snapshot.json"))
HIGHLIGHT_DISP = snap[0]["disp"]
HIGHLIGHT_RANK = 1
len_snap = len(snap)

W, H = 1000, 720
MARGIN_L = 260
MARGIN_R = 120
MARGIN_T = 90
ROW_H = 34
chart_h = MARGIN_T + len(snap) * ROW_H + 40
H = max(H, chart_h)
plot_w = W - MARGIN_L - MARGIN_R
maxv = 100.0

teal = "#00D4AA"
indigo = "#1A1A2E"
cream = "#FEFCF8"
grey = "#9aa3b2"

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, system-ui, sans-serif">')
parts.append(f'<rect width="{W}" height="{H}" fill="{cream}"/>')
parts.append(f'<text x="{MARGIN_L}" y="44" font-size="30" font-weight="700" fill="{indigo}">BenchmarkViv 2026 — VivIndex Leaderboard</text>')
parts.append(f'<text x="{MARGIN_L}" y="68" font-size="15" fill="{grey}">Weighted composite of 6 scored tracks · {HIGHLIGHT_DISP} highlighted · full {len_snap}-model roster</text>')

y = MARGIN_T
for o in snap:
    bar_w = plot_w * (o["viv"] / maxv)
    is_me = o["id"] == snap[0]["id"]
    fill = teal if is_me else "#dbe4ee"
    label = esc(o["disp"])
    score = str(o["viv"])
    parts.append(f'<text x="{MARGIN_L-14}" y="{y+22}" text-anchor="end" font-size="15" font-weight="{700 if is_me else 500}" fill="{indigo if is_me else "#434a56"}">{label}</text>')
    parts.append(f'<rect x="{MARGIN_L}" y="{y+6}" width="{bar_w:.1f}" height="22" rx="5" fill="{fill}" stroke="#0aa97f" stroke-width="{2 if is_me else 0}"/>')
    parts.append(f'<text x="{MARGIN_L+bar_w+10:.1f}" y="{y+23}" font-size="14" font-weight="700" fill="{indigo}">{score}</text>')
    y += ROW_H

ty = y + 14
parts.append(f'<rect x="{MARGIN_L}" y="{ty}" width="18" height="18" rx="4" fill="{teal}"/>')
parts.append(f'<text x="{MARGIN_L+26}" y="{ty+14}" font-size="14" fill="{indigo}">{HIGHLIGHT_DISP} — #{HIGHLIGHT_RANK} of {len_snap}</text>')
parts.append("</svg>")

out = "data/leaderboard_chart.svg"
open(out, "w").write("\n".join(parts))
print("wrote", out, "with", len(snap), "models, footer =", HIGHLIGHT_DISP, f"#{HIGHLIGHT_RANK} of {len_snap}")