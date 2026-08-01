#!/usr/bin/env python3
"""Build a large, framed 2x2 BenchmarkViv infographic for DeepSeek V4 Flash 0731."""
import json

d = json.load(open("data/results.json"))
ME = "deepseek-v4-flash-0731"
disp = {m["id"]: m["display"] for m in d["models"]}
rows = [r for r in d["results"] if r["model_id"] == ME]

def score(bid):
    for r in rows:
        if r["benchmark_id"] == bid and r.get("score") is not None:
            return r["score"]
    return None

intent = score("intent_understanding")
ui = score("one_shot_ui")
startup = score("startup_in_a_weekend")
ddi = score("pharma_drug_interaction")
reg = score("pharma_regulatory_comprehension")
value = score("value_density")
# brick retired from board - exclude

# cost / speed across scored text runs (exclude vision skip + brick)
scored = [r for r in rows if r.get("score") is not None and r["benchmark_id"] != "brick_breaker_realism"]
tot_cost = sum(r.get("estimated_cost_usd") or 0 for r in scored)
tot_tok = sum(r.get("total_tokens") or 0 for r in scored)
tot_lat = sum(r.get("latency") or 0 for r in scored)
tps = tot_tok / tot_lat if tot_lat else 0
avg_cost = tot_cost / len(scored)

# value density metrics
vdm = next((r.get("metrics") for r in rows if r["benchmark_id"] == "value_density" and r.get("metrics")), {})
v_per_1k = vdm.get("value_per_1k_tokens")

# Phrama best context
def best(bid):
    sc = sorted([(rr["score"], rr["model_id"]) for rr in d["results"] if rr["benchmark_id"] == bid and rr.get("score") is not None], reverse=True)
    return sc[0] if sc else None

best_ddi = best("pharma_drug_interaction")
best_reg = best("pharma_regulatory_comprehension")

# ---- layout ----
W, H = 1700, 1250
M = 60
INK = "#1A1A2E"
TEAL = "#00D4AA"
CREAM = "#FEFCF8"
GREY = "#7a8294"
CARD = "#FFFFFF"

COL_W = (W - 3*M) / 2
ROW_H = (H - M*3 - 150) / 2  # reserve 150 for title
def cx(i):  # left x of card i (0=TL,1=TR,2=BL,3=BR)
    return M + (i % 2) * (COL_W + M)
def cy(i):
    return 190 + (i // 2) * (ROW_H + M)

E = []
E.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, system-ui, sans-serif">')
E.append(f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')

# title
E.append(f'<text x="{M}" y="78" font-size="44" font-weight="800" fill="{INK}">DeepSeek V4 Flash 0731</text>')
E.append(f'<text x="{M}" y="128" font-size="22" fill="{GREY}">BenchmarkViv 2026 · real Venice API runs · VivIndex composite rank #4 of 17</text>')
E.append(f'<rect x="{M}" y="150" width="{W-2*M}" height="3" fill="{TEAL}"/>')

def card(i, title, subtitle):
    x, y = cx(i), cy(i)
    w, h = COL_W, ROW_H - 16
    E.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h:.0f}" rx="18" fill="{CARD}" stroke="#e4e9f2" stroke-width="2"/>')
    E.append(f'<text x="{x+34}" y="{y+46}" font-size="26" font-weight="800" fill="{INK}">{title}</text>')
    E.append(f'<text x="{x+34}" y="{y+72}" font-size="16" fill="{GREY}">{subtitle}</text>')
    return x, y, w, h

def esc(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# ---- Card 0 (TL): Rank + VivIndex ----
x, y, w, h = card(0, "Overall Rank", "VivIndex weighted composite")
bx = x + 34
E.append(f'<text x="{bx}" y="{y+150}" font-size="120" font-weight="900" fill="{INK}">#4</text>')
E.append(f'<text x="{bx+170}" y="{y+145}" font-size="34" font-weight="700" fill="{GREY}">of 17 models</text>')
# VivIndex metre
mx, my = bx, y + 200
mw = w - 2*bx + x  # width available
mw = 560
E.append(f'<text x="{bx}" y="{my}" font-size="17" fill="{GREY}">VivIndex 89.7 / 100</text>')
E.append(f'<rect x="{bx}" y="{my+12}" width="{mw}" height="26" rx="13" fill="#eef1f7"/>')
E.append(f'<rect x="{bx}" y="{my+12}" width="{mw*89.7/100:.0f}" height="26" rx="13" fill="{TEAL}"/>')
E.append(f'<text x="{bx+mw*89.7/100+14:.0f}" y="{my+33}" font-size="20" font-weight="800" fill="{INK}">89.7</text>')
# mini leaderboard
ly = my + 70
E.append(f'<text x="{bx}" y="{ly}" font-size="15" fill="{GREY}">Top of the board:</text>')
lead = [("GPT-5.5",92.5),("GPT-5.6 Terra",92.2),("GPT-5.6 Sol",90.9),("DeepSeek V4 Flash 0731",89.7)]
llw = 380
for lbl, v in lead:
    ly += 34
    is_me = "Flash" in lbl
    E.append(f'<text x="{bx}" y="{ly}" font-size="16" font-weight="700" fill="{TEAL if is_me else INK}">{esc(lbl)}</text>')
    E.append(f'<rect x="{bx+210}" y="{ly-13}" width="{llw*(v/100):.0f}" height="16" rx="8" fill="{TEAL if is_me else "#d9e0ec"}"/>')
    E.append(f'<text x="{bx+210+llw*(v/100)+8:.0f}" y="{ly}" font-size="14" font-weight="700" fill="{INK}">{v}</text>')

# ---- Card 1 (TR): Track scores ----
x, y, w, h = card(1, "Where it wins", "Scored lanes (higher = better)")
tracks = [("Value Density @1K", value, 100), ("One-Shot UI Generation", ui, 100),
          ("Startup in a Weekend", startup, 100), ("Pharma Drug Interaction", ddi, 100),
          ("Pharma Regulatory", reg, 100), ("Intent Understanding", intent, 100)]
by = y + 110
bw = w - 2*34 - 120
for lbl, sc, maxv in tracks:
    if sc is None: 
        continue
    E.append(f'<text x="{x+34}" y="{by}" font-size="17" fill="{INK}">{esc(lbl)}</text>')
    E.append(f'<rect x="{x+34}" y="{by+8}" width="{bw}" height="20" rx="10" fill="#eef1f7"/>')
    E.append(f'<rect x="{x+34}" y="{by+8}" width="{bw*sc/maxv:.0f}" height="20" rx="10" fill="{TEAL}"/>')
    E.append(f'<text x="{x+34+bw+14:.0f}" y="{by+26}" font-size="19" font-weight="800" fill="{INK}">{sc}</text>')
    by += 44

# ---- Card 2 (BL): Pharma domain ----
x, y, w, h = card(2, "Pharma domain", "Drug-drug interaction + regulatory")
ddi_top = "90 (GLM 5.2 / Opus 5)"
reg_top = "95 (Opus 5)"
bx = x + 34
E.append(f'<text x="{bx}" y="{y+120}" font-size="90" font-weight="900" fill="{INK}">89</text>')
E.append(f'<text x="{bx+110}" y="{y+110}" font-size="22" font-weight="700" fill="{GREY}">Drug-Drug\nInteraction</text>')
E.append(f'<text x="{bx}" y="{y+168}" font-size="15" fill="{GREY}">Board best: {esc(ddi_top)}</text>')
E.append(f'<text x="{x+w/2+20}" y="{y+120}" font-size="90" font-weight="900" fill="{INK}">80</text>')
E.append(f'<text x="{x+w/2+130}" y="{y+110}" font-size="22" font-weight="700" fill="{GREY}">Regulatory\nComprehension</text>')
E.append(f'<text x="{x+w/2+20}" y="{y+168}" font-size="15" fill="{GREY}">Board best: {esc(reg_top)}</text>')
# bar comparison
by = y + 210
E.append(f'<text x="{bx}" y="{by}" font-size="15" fill="{GREY}">vs best-in-class on each lane:</text>')
comp = [("Drug-Drug Interaction", 89, 90), ("Regulatory", 80, 95)]
for lbl, mine, top in comp:
    by += 40
    E.append(f'<text x="{bx}" y="{by}" font-size="16" font-weight="700" fill="{INK}">{esc(lbl)}</text>')
    E.append(f'<rect x="{bx+200}" y="{by-12}" width="180" height="15" rx="7" fill="#eef1f7"/>')
    E.append(f'<rect x="{bx+200}" y="{by-12}" width="{180*mine/100:.0f}" height="15" rx="7" fill="{TEAL}"/>')
    E.append(f'<text x="{bx+404}" y="{by}" font-size="14" font-weight="800" fill="{INK}">mine {mine}</text>')
    E.append(f'<rect x="{bx+200}" y="{by+4}" width="{180*top/100:.0f}" height="6" rx="3" fill="#0aa97f" opacity="0.6"/>')
    E.append(f'<text x="{bx+404}" y="{by+14}" font-size="13" fill="{GREY}">best {top}</text>')

# ---- Card 3 (BR): Efficiency / value ----
x, y, w, h = card(3, "Efficiency", "Value per token · cost · speed")
bx = x + 34
E.append(f'<text x="{bx}" y="{y+130}" font-size="72" font-weight="900" fill="{INK}">100</text>')
E.append(f'<text x="{bx+150}" y="{y+120}" font-size="22" font-weight="700" fill="{GREY}">Value Density\n@1K</text>')
E.append(f'<text x="{bx}" y="{y+172}" font-size="15" fill="{GREY}">Perfect score, perfect compact JSON</text>')
# metric tiles
tw = (w - 2*34 - 30) / 2
ty = y + 215
tiles = [
    ("Value per 1k tokens", f"{v_per_1k:.1f}"),
    ("Avg cost / scored run", f"${avg_cost:.4f}"),
    ("Speed (out tok/s)", f"{tps:.0f}"),
    ("Total run cost", f"${tot_cost:.4f}"),
]
for idx, (lbl, val) in enumerate(tiles):
    tx = bx + (idx % 2) * (tw + 30)
    t_y = ty + (idx // 2) * 86
    E.append(f'<rect x="{tx:.0f}" y="{t_y}" width="{tw:.0f}" height="70" rx="12" fill="#f4f6fb" stroke="#e4e9f2"/>')
    E.append(f'<text x="{tx+16:.0f}" y="{t_y+30}" font-size="26" font-weight="800" fill="{TEAL}">{esc(val)}</text>')
    E.append(f'<text x="{tx+16:.0f}" y="{t_y+56}" font-size="14" fill="{GREY}">{esc(lbl)}</text>')

E.append("</svg>")
open("data/deepseek-v4-flash-0731-infographic-2x2.svg", "w").write("\n".join(E))
print("wrote data/deepseek-v4-flash-0731-infographic-2x2.svg", len(E), "elements")
