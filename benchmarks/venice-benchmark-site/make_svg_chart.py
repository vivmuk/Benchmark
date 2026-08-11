#!/usr/bin/env python3
"""Generate an accurate SVG bar chart of the BenchmarkViv VivIndex leaderboard,
highlighting DeepSeek V4 Flash 0731."""
import json

snap = json.load(open("data/chart_snapshot.json"))

W, H = 1000, 720
MARGIN_L = 260
MARGIN_R = 120
MARGIN_T = 90
ROW_H = 34
gap = 8
chart_h = MARGIN_T + len(snap) * ROW_H + 40
H = max(H, chart_h)
plot_w = W - MARGIN_L - MARGIN_R
maxv = 100.0

rows = []
y = MARGIN_T
for o in snap:
    rows.append((o, y))
    y += ROW_H

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
parts.append(f'<text x="{MARGIN_L}" y="68" font-size="15" fill="{grey}">Weighted composite of 6 scored tracks · DeepSeek V4 Flash 0731 highlighted</text>')

for o, y in rows:
    bar_w = plot_w * (o["viv"] / maxv)
    is_me = o["id"] == "deepseek-v4-flash-0731"
    fill = teal if is_me else "#dbe4ee"
    label = esc(o["disp"])
    score = str(o["viv"])
    parts.append(f'<text x="{MARGIN_L-14}" y="{y+22}" text-anchor="end" font-size="15" font-weight="{700 if is_me else 500}" fill="{indigo if is_me else "#434a56"}">{label}</text>')
    parts.append(f'<rect x="{MARGIN_L}" y="{y+6}" width="{bar_w:.1f}" height="22" rx="5" fill="{fill}" stroke="#0aa97f" stroke-width="{2 if is_me else 0}"/>')
    parts.append(f'<text x="{MARGIN_L+bar_w+10:.1f}" y="{y+23}" font-size="14" font-weight="700" fill="{indigo}">{score}</text>')

# footer
ty = y + 14
parts.append(f'<rect x="{MARGIN_L}" y="{ty}" width="18" height="18" rx="4" fill="{teal}"/>')
parts.append(f'<text x="{MARGIN_L+26}" y="{ty+14}" font-size="14" fill="{indigo}">DeepSeek V4 Flash 0731 — #{next(i+1 for i,o in enumerate(snap) if o["id"]=="deepseek-v4-flash-0731")} of {len(snap)}</text>')
parts.append("</svg>")

open("data/leaderboard_chart.svg", "w").write("\n".join(parts))
print("wrote data/leaderboard_chart.svg", len(parts), "elements")
