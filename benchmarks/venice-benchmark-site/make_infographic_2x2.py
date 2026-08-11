#!/usr/bin/env python3
"""Build BenchmarkViv infographics for a model.

Outputs:
  data/<slug>-infographic-2x2.svg/png     desktop 2x2 (media-heavy, wide screens)
  data/<slug>-infographic-mobile.svg/png  stacked single-column (phones)

The top-of-board list is computed from results.json (never hardcoded) and the
#1 model is ALWAYS highlighted in gold, independent of which model the
infographic features.
"""
import json, math, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# ---- brand tokens (shared with the site) ----
INK   = "#1A1A2E"   # indigo-black text
TEAL  = "#00D4AA"   # primary
TEAL_DARK = "#00A68A"  # deeper teal for small bars / labels
CREAM = "#FEFCF8"   # background
GREY  = "#7a8294"
CARD  = "#FFFFFF"
TRACK = "#EEF1F7"   # empty bar track
GOLD  = "#D9A441"   # rank #1 highlight
GOLD_DEEP = "#B8860B"
CROWN = "👑"         # rank #1 marker (text; keep in label strings)

VIVINDEX_WEIGHTS = {
    "intent_understanding": 0.20,
    "one_shot_ui": 0.15,
    "startup_in_a_weekend": 0.25,
    "value_density": 0.20,
    "reverse_prompt_vision": 0.20,
}

def load():
    d = json.load(open(DATA / "results.json"))
    disp = {m["id"]: m["display"] for m in d["models"]}
    return d, disp

def vivindex_for(d, mid):
    ws, wsum = 0.0, 0.0
    n = 0
    for r in d["results"]:
        if r["model_id"] != mid: continue
        w = VIVINDEX_WEIGHTS.get(r["benchmark_id"])
        if w is not None and r.get("score") is not None:
            ws += w; wsum += r["score"] * w; n += 1
    return (wsum / ws) if ws > 0 else 0.0, n

def top_board(d, n=4, must_include=None):
    """Top n models by raw VivIndex (matches the site headline rank),
    data-driven. must_include (display name) is always present, replacing the
    last slot if it didn't qualify on merit (keeps the featured model visible)."""
    rows = []
    for m in d["models"]:
        vi, cnt = vivindex_for(d, m["id"])
        if cnt == 0: continue
        rows.append((m["display"], vi, cnt == len(VIVINDEX_WEIGHTS)))
    rows.sort(key=lambda x: -x[1])
    if not must_include: return rows[:n]
    if any(r[0] == must_include for r in rows[:n]): return rows[:n]
    out = rows[:n - 1]
    me_row = next((r for r in rows if r[0] == must_include), None)
    if me_row: out.append(me_row)
    return out

def crown_svg(cx, cy, size=26):
    """A small gold crown path anchored at (cx, cy) = left of the label,
    baseline near cy (bottom of the crown sits ~at baseline)."""
    s = size
    return (
        f'<g transform="translate({cx},{cy - s + 4})">'
        f'<path d="M2 {s-8} L2 4 L{s*0.28} {s*0.5} L{s*0.5} 2 L{s*0.72} {s*0.5} L{s-2} 4 L{s-2} {s-8} Z" '
        f'fill="{GOLD_DEEP}"/>'
        f'<path d="M2 {s-6} L2 6 L{s*0.28} {s*0.52} L{s*0.5} 4 L{s*0.72} {s*0.52} L{s-2} 6 L{s-2} {s-6}" '
        f'fill="{GOLD}"/>'
        f'<rect x="2" y="{s-6}" width="{s-4}" height="3" rx="1.5" fill="{GOLD_DEEP}"/>'
        f'</g>'
    )

def score_of(d, mid, bid):
    for r in d["results"]:
        if r["model_id"] == mid and r["benchmark_id"] == bid and r.get("score") is not None:
            return r["score"]
    return None

def best_of(d, bid):
    best, name = 0, None
    for m in d["models"]:
        s = score_of(d, m["id"], bid)
        if s is not None and s > best:
            best, name = s, m["display"]
    return best, name

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

# --------------------------------------------------------------------------
# shared card content builders
# --------------------------------------------------------------------------

def build_rank_card(d, me, x, y, w, h, fonts, is_compact=False):
    """Overall Rank + VivIndex metre + top-of-board mini list with ALWAYS-gold #1."""
    E = []
    vi, _ = vivindex_for(d, me)
    vi_n = round(vi, 1)
    rank_all = top_board(d, 99)
    me_disp = next(m["display"] for m in d["models"] if m["id"] == me)
    rank = next((i + 1 for i, (name, v, _) in enumerate(rank_all) if name == me_disp), None)
    board = top_board(d, 4, must_include=me_disp)
    fs_title, fs_huge, fs_med, fs_small, fs_micro = fonts

    E.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{CARD}" stroke="#e4e9f2" stroke-width="2"/>')
    E.append(f'<text x="{x+34}" y="{y+46}" font-size="{fs_title}" font-weight="800" fill="{INK}">Overall Rank</text>')
    E.append(f'<text x="{x+34}" y="{y+72}" font-size="{fs_small}" fill="{GREY}">VivIndex weighted composite</text>')

    bx = x + 34
    ry = y + 130
    # Rank numeral + crown if #1
    gold_me = rank == 1
    rank_color = GOLD if gold_me else INK
    E.append(f'<text x="{bx}" y="{ry+56}" font-size="{fs_huge}" font-weight="900" fill="{rank_color}">#{rank}</text>')
    if gold_me:
        E.append(f'<text x="{bx + fs_huge*0.62}" y="{ry+52}" font-size="{fs_huge*0.42}" fill="{GOLD}">{CROWN}</text>')
    E.append(f'<text x="{bx + fs_huge*0.82}" y="{ry+52}" font-size="{fs_med}" font-weight="700" fill="{GREY}">of {len(rank_all)} models</text>')

    # VivIndex metre
    my = ry + 88
    mw = min(w - 2 * 34 - 60, 560)
    E.append(f'<text x="{bx}" y="{my}" font-size="{fs_small}" fill="{GREY}">VivIndex {vi_n} / 100</text>')
    E.append(f'<rect x="{bx}" y="{my+12}" width="{mw}" height="26" rx="13" fill="{TRACK}"/>')
    fill_w = mw * vi_n / 100
    E.append(f'<rect x="{bx}" y="{my+12}" width="{fill_w:.0f}" height="26" rx="13" fill="{TEAL}"/>')
    E.append(f'<text x="{bx+mw+14}" y="{my+33}" font-size="{fs_med}" font-weight="800" fill="{INK}">{vi_n}</text>')

    # ---- top of the board ----
    ly = my + 64
    E.append(f'<text x="{bx}" y="{ly}" font-size="{fs_micro}" fill="{GREY}">Top of the board:</text>')
    llw = min(w - 2 * 34 - 210, 380)
    for i, (name, v, full) in enumerate(board):
        ly += 34
        is_me = name == me_disp
        is_gold = i == 0          # ALWAYS highlight the #1 model
        col = GOLD if is_gold else (TEAL if is_me else INK)
        bar_col = GOLD if is_gold else (TEAL if is_me else "#d9e0ec")
        if is_gold:
            E.append(crown_svg(bx, ly, size=22))
            E.append(f'<text x="{bx+30}" y="{ly}" font-size="{fs_small}" font-weight="700" fill="{col}">{esc(name)}</text>')
        else:
            E.append(f'<text x="{bx}" y="{ly}" font-size="{fs_small}" font-weight="700" fill="{col}">{esc(name)}</text>')
        E.append(f'<rect x="{bx+200}" y="{ly-13}" width="{llw*(v/100):.0f}" height="16" rx="8" fill="{bar_col}"/>')
        E.append(f'<text x="{bx+200+llw*(v/100)+8:.0f}" y="{ly}" font-size="{fs_small}" font-weight="700" fill="{INK}">{v:.1f}</text>')
        if is_me:
            E.append(f'<text x="{bx+200+llw+70:.0f}" y="{ly}" font-size="{fs_micro}" font-weight="600" fill="{TEAL_DARK}">you are here</text>')
    return E

def build_tracks_card(d, me, x, y, w, h, fonts):
    E = []
    fs_title, fs_huge, fs_med, fs_small, fs_micro = fonts
    E.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{CARD}" stroke="#e4e9f2" stroke-width="2"/>')
    E.append(f'<text x="{x+34}" y="{y+46}" font-size="{fs_title}" font-weight="800" fill="{INK}">Where it wins</text>')
    E.append(f'<text x="{x+34}" y="{y+72}" font-size="{fs_small}" fill="{GREY}">Scored lanes (higher = better)</text>')
    tracks = [
        ("Value Density @1K", "value_density"),
        ("One-Shot UI Generation", "one_shot_ui"),
        ("Startup in a Weekend", "startup_in_a_weekend"),
        ("Pharma Drug Interaction", "pharma_drug_interaction"),
        ("Pharma Regulatory", "pharma_regulatory_comprehension"),
        ("Intent Understanding", "intent_understanding"),
    ]
    by = y + 110
    bw = w - 2 * 34 - 120
    for lbl, bid in tracks:
        sc = score_of(d, me, bid)
        if sc is None: continue
        E.append(f'<text x="{x+34}" y="{by}" font-size="{fs_small}" fill="{INK}">{esc(lbl)}</text>')
        E.append(f'<rect x="{x+34}" y="{by+8}" width="{bw}" height="20" rx="10" fill="{TRACK}"/>')
        E.append(f'<rect x="{x+34}" y="{by+8}" width="{bw*sc/100:.0f}" height="20" rx="10" fill="{TEAL}"/>')
        E.append(f'<text x="{x+34+bw+14:.0f}" y="{by+26}" font-size="{fs_med}" font-weight="800" fill="{INK}">{sc:.0f}</text>')
        by += 44
    return E

def build_pharma_card(d, me, x, y, w, h, fonts):
    E = []
    fs_title, fs_huge, fs_med, fs_small, fs_micro = fonts
    E.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{CARD}" stroke="#e4e9f2" stroke-width="2"/>')
    E.append(f'<text x="{x+34}" y="{y+46}" font-size="{fs_title}" font-weight="800" fill="{INK}">Pharma domain</text>')
    E.append(f'<text x="{x+34}" y="{y+72}" font-size="{fs_small}" fill="{GREY}">Drug-drug interaction + regulatory</text>')

    ddi = score_of(d, me, "pharma_drug_interaction")
    reg = score_of(d, me, "pharma_regulatory_comprehension")
    ddi_best, ddi_name = best_of(d, "pharma_drug_interaction")
    reg_best, reg_name = best_of(d, "pharma_regulatory_comprehension")

    bx = x + 34
    # two big numbers side by side
    col_w = (w - 2 * 34) / 2
    for i, (sc, lbl, best, bname) in enumerate([
        (ddi, "Drug-Drug\nInteraction", ddi_best, ddi_name),
        (reg, "Regulatory\nComprehension", reg_best, reg_name),
    ]):
        cx = bx + i * col_w
        if sc is None: continue
        E.append(f'<text x="{cx}" y="{y+124}" font-size="90" font-weight="900" fill="{INK}">{sc:.0f}</text>')
        E.append(f'<text x="{cx+104}" y="{y+116}" font-size="21" font-weight="700" fill="{GREY}">{esc(lbl)}</text>')
        E.append(f'<text x="{cx}" y="{y+168}" font-size="15" fill="{GREY}">Board best: {esc(bname)} {best:.0f}</text>')

    # vs best-in-class comparison (aligned two-row bars)
    by = y + 205
    E.append(f'<text x="{bx}" y="{by}" font-size="{fs_micro}" fill="{GREY}">vs best-in-class on each lane:</text>')
    comp = [("Drug-Drug Interaction", ddi, ddi_best), ("Regulatory", reg, reg_best)]
    bar_x = bx + 210
    bar_w = 180
    for lbl, mine, top in comp:
        by += 42
        if mine is None: continue
        E.append(f'<text x="{bx}" y="{by}" font-size="{fs_micro}" font-weight="700" fill="{INK}">{esc(lbl)}</text>')
        # track
        E.append(f'<rect x="{bar_x}" y="{by-14}" width="{bar_w}" height="18" rx="9" fill="{TRACK}"/>')
        # mine bar (full height) - teal, or gold if this is the board's best lane
        mine_col = GOLD if mine >= top else TEAL
        E.append(f'<rect x="{bar_x}" y="{by-14}" width="{bar_w*mine/100:.0f}" height="18" rx="9" fill="{mine_col}"/>')
        E.append(f'<text x="{bar_x+bar_w+10}" y="{by}" font-size="14" font-weight="800" fill="{INK}">{mine:.0f}</text>')
        # best tick (thin, below)
        E.append(f'<rect x="{bar_x}" y="{by+6}" width="{bar_w*top/100:.0f}" height="6" rx="3" fill="#0aa97f" opacity="0.55"/>')
        E.append(f'<text x="{bar_x+bar_w+10}" y="{by+14}" font-size="13" fill="{GREY}">best {top:.0f}</text>')
    return E

def build_eff_card(d, me, x, y, w, h, fonts):
    E = []
    fs_title, fs_huge, fs_med, fs_small, fs_micro = fonts
    E.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{CARD}" stroke="#e4e9f2" stroke-width="2"/>')
    E.append(f'<text x="{x+34}" y="{y+46}" font-size="{fs_title}" font-weight="800" fill="{INK}">Efficiency</text>')
    E.append(f'<text x="{x+34}" y="{y+72}" font-size="{fs_small}" fill="{GREY}">Value per token · cost · speed</text>')

    rows = [r for r in d["results"] if r["model_id"] == me]
    scored = [r for r in rows if r.get("score") is not None and r["benchmark_id"] != "brick_breaker_realism"]
    tot_cost = sum(r.get("estimated_cost_usd") or 0 for r in scored)
    tot_tok = sum(r.get("total_tokens") or 0 for r in scored)
    tot_lat = sum(r.get("latency") or 0 for r in scored)
    tps = (tot_tok / tot_lat) if tot_lat else 0
    avg_cost = tot_cost / len(scored) if scored else 0
    vdm = next((r.get("metrics") for r in rows if r["benchmark_id"] == "value_density" and r.get("metrics")), {})
    v_per_1k = vdm.get("value_per_1k_tokens")

    bx = x + 34
    E.append(f'<text x="{bx}" y="{y+130}" font-size="72" font-weight="900" fill="{INK}">100</text>')
    E.append(f'<text x="{bx+150}" y="{y+120}" font-size="22" font-weight="700" fill="{GREY}">Value Density\n@1K</text>')
    E.append(f'<text x="{bx}" y="{y+172}" font-size="15" fill="{GREY}">Perfect score, perfect compact JSON</text>')

    tw = (w - 2 * 34 - 30) / 2
    ty = y + 215
    tiles = [
        ("Value per 1k tokens", f"{v_per_1k:.1f}" if v_per_1k is not None else "—"),
        ("Avg cost / scored run", f"${avg_cost:.4f}"),
        ("Speed (out tok/s)", f"{tps:.0f}"),
        ("Total run cost", f"${tot_cost:.4f}"),
    ]
    for idx, (lbl, val) in enumerate(tiles):
        tx = bx + (idx % 2) * (tw + 30)
        t_y = ty + (idx // 2) * 86
        E.append(f'<rect x="{tx:.0f}" y="{t_y}" width="{tw:.0f}" height="70" rx="12" fill="#f4f6fb" stroke="#e4e9f2"/>')
        E.append(f'<text x="{tx+16:.0f}" y="{t_y+30}" font-size="27" font-weight="800" fill="{TEAL_DARK}">{esc(val)}</text>')
        E.append(f'<text x="{tx+16:.0f}" y="{t_y+58}" font-size="14" fill="{GREY}">{esc(lbl)}</text>')
    return E

# --------------------------------------------------------------------------
# desktop 2x2
# --------------------------------------------------------------------------

def build_desktop(d, me):
    W, H = 1700, 1250
    M = 60
    COL_W = (W - 3 * M) / 2
    ROW_H = (H - M * 3 - 150) / 2
    def cx(i): return M + (i % 2) * (COL_W + M)
    def cy(i): return 190 + (i // 2) * (ROW_H + M)

    E = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, system-ui, sans-serif">']
    E.append(f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')
    me_disp = next(m["display"] for m in d["models"] if m["id"] == me)
    E.append(f'<text x="{M}" y="78" font-size="44" font-weight="800" fill="{INK}">{esc(me_disp)}</text>')
    E.append(f'<text x="{M}" y="128" font-size="22" fill="{GREY}">BenchmarkViv 2026 · real Venice API runs · VivIndex composite rank</text>')
    E.append(f'<rect x="{M}" y="150" width="{W-2*M}" height="3" fill="{TEAL}"/>')

    fonts = (26, 120, 34, 17, 15)
    for i, builder in enumerate([
        lambda x, y, w, h: build_rank_card(d, me, x, y, w, h, fonts),
        lambda x, y, w, h: build_tracks_card(d, me, x, y, w, h, fonts),
        lambda x, y, w, h: build_pharma_card(d, me, x, y, w, h, fonts),
        lambda x, y, w, h: build_eff_card(d, me, x, y, w, h, fonts),
    ]):
        E.extend(builder(cx(i), cy(i), COL_W, ROW_H - 16))
    E.append("</svg>")
    out = DATA / f"{me}-infographic-2x2.svg"
    out.write_text("\n".join(E), encoding="utf-8")
    print("wrote", out)

# --------------------------------------------------------------------------
# mobile stacked
# --------------------------------------------------------------------------

def build_mobile(d, me):
    W, M = 1000, 40
    CARD_H = 520
    GAP = 26
    title_h = 170
    H = title_h + 4 * (CARD_H + GAP)
    def cx(): return M
    def cw(): return W - 2 * M

    E = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, system-ui, sans-serif">']
    E.append(f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')
    me_disp = next(m["display"] for m in d["models"] if m["id"] == me)
    E.append(f'<text x="{M}" y="82" font-size="64" font-weight="800" fill="{INK}">{esc(me_disp)}</text>')
    E.append(f'<text x="{M}" y="134" font-size="30" fill="{GREY}">BenchmarkViv 2026 · real Venice API runs · VivIndex composite rank</text>')
    E.append(f'<rect x="{M}" y="150" width="{W-2*M}" height="3" fill="{TEAL}"/>')
    E.append(f'<text x="{M}" y="170" font-size="20" fill="{GREY}">(scroll — stacked for mobile)</text>')

    # mobile fonts: much larger relative sizes
    fonts = (38, 150, 56, 30, 24)
    builders = [
        lambda x, y, w, h: build_rank_card(d, me, x, y, w, h, fonts, is_compact=True),
        lambda x, y, w, h: build_tracks_card(d, me, x, y, w, h, fonts),
        lambda x, y, w, h: build_pharma_card(d, me, x, y, w, h, fonts),
        lambda x, y, w, h: build_eff_card(d, me, x, y, w, h, fonts),
    ]
    for i, builder in enumerate(builders):
        y = title_h + i * (CARD_H + GAP)
        E.extend(builder(cx(), y, cw(), CARD_H))
    E.append("</svg>")
    out = DATA / f"{me}-infographic-mobile.svg"
    out.write_text("\n".join(E), encoding="utf-8")
    print("wrote", out, f"({H}px tall)")

# --------------------------------------------------------------------------

def to_png(svg_path: Path):
    try:
        import cairosvg
        png = svg_path.with_suffix(".png")
        cairosvg.svg2png(url=str(svg_path), write_to=str(png), dpi=144)
        print("wrote", png)
    except Exception as e:
        print("PNG conversion skipped:", e)

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "deepseek-v4-flash-0731"
    d, _ = load()
    build_desktop(d, which)
    build_mobile(d, which)
    to_png(DATA / f"{which}-infographic-2x2.svg")
    to_png(DATA / f"{which}-infographic-mobile.svg")

if __name__ == "__main__":
    main()
