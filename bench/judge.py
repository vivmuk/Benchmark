"""Phase 2: render model output in headless Chrome, then score it with two blind judges."""
import re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from common import *

def _chrome():
    """Newest Chromium headless shell from the Playwright cache, on macOS or Linux."""
    found = []
    for root in (Path.home() / ".cache/ms-playwright", Path.home() / "Library/Caches/ms-playwright"):
        for pattern in ("chromium_headless_shell-*/**/chrome-headless-shell", "chromium_headless_shell-*/**/headless_shell"):
            found += [p for p in root.glob(pattern) if p.is_file()]
    if found:
        return sorted(found)[-1]
    return Path("/usr/bin/chromium")


CHROME = _chrome()
SHOTS = RAW / "shots"


def shot(html, prefix, mode, port):
    """mode 'frames': three real-time frames 450ms apart. mode 'full': whole page after scrolling through it."""
    prefix.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["node", str(ROOT / "bench" / "shot.mjs"), str(CHROME), str(port), mode, str(html), str(prefix)],
                   capture_output=True, timeout=150)


def jpeg(png, out, maxside=1568):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    im.thumbnail((maxside, maxside))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=85)
    return out


ONLY_ALPACA = False


def render(sp):
    mid = sp["id"]
    for task in (("alpaca",) if ONLY_ALPACA else ("alpaca", "design")):
        r = load(RAW / task / (mid + ".json"))
        if not r or r.get("error") or incomplete(r):
            continue
        html = SITE / "out" / task / (mid + ".html")
        html.write_text(extract_html(r["text"]))
        port = 9300 + MODELS.index(mid) * 2 + (task == "design")
        if task == "alpaca":
            if not (SHOTS / ("alpaca-%s-3.png" % mid)).exists():
                shot(html, SHOTS / ("alpaca-" + mid), "frames", port)
            if (SHOTS / ("alpaca-%s-1.png" % mid)).exists():
                jpeg(SHOTS / ("alpaca-%s-1.png" % mid), SITE / "img" / "alpaca" / (mid + ".jpg"), 960)
        else:
            p = SHOTS / ("design-%s.png" % mid)
            if not p.exists():
                shot(html, SHOTS / ("design-" + mid), "full", port)
            if p.exists():
                jpeg(p, SITE / "img" / "design" / (mid + ".jpg"), 6000)


def motion_stats(mid):
    """Objective motion: pixel change across the four real-time frames, whole frame and leg band."""
    from PIL import Image, ImageChops
    fs = [SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(4)]
    if not all(f.exists() for f in fs):
        return None
    ims = [Image.open(f).convert("L").resize((320, 180)) for f in fs]
    means, changed, legs = [], [], []
    for a, b in zip(ims, ims[1:]):
        d = ImageChops.difference(a, b)
        px = list(d.getdata())
        means.append(sum(px) / len(px))
        changed.append(100.0 * sum(1 for v in px if v > 12) / len(px))
        leg = d.crop((0, int(180 * 0.55), 320, 180))
        lp = list(leg.getdata())
        legs.append(100.0 * sum(1 for v in lp if v > 12) / len(lp))
    return {"mean": round(max(means), 2), "changed_pct": round(max(changed), 2), "leg_pct": round(max(legs), 2)}


JUDGES_ALPACA = ["openai-gpt-55-pro", "gemini-3-1-pro-preview", "kimi-k3-fast-api"]

RUBRIC = {
    "alpaca": (
        "You are scoring four real-time frames (400 ms apart) of one animated HTML component, plus a measured motion readout.\n"
        "The brief: one self-contained HTML file drawing an alpaca in code, walking in a smooth believable loop, in a small tasteful scene, "
        "filling 1280x720, animating on load.\n\n"
        "Score each criterion by STARTING AT 4 and DEDUCTING 1 for every named flaw you can actually see. "
        "Integer scores only. A 4 means you could not improve that aspect. Most competent outputs land on 2 or 3; 4 is rare.\n\n"
        "1. anatomy - start 4. Deduct 1 for EACH of:\n"
        "   - a detached or floating part (head or neck separated from the body, limb not touching);\n"
        "   - a limb attached at the wrong point, or a missing limb;\n"
        "   - jointless stick legs where the body implies weight;\n"
        "   - head, neck or body out of proportion for a camelid;\n"
        "   - missing species cues (upright ears, muzzle, fleece texture, long neck).\n\n"
        "2. gait - the measured readout sets the ceiling, then you may only deduct:\n"
        "   >= 6% of pixels changing = 4; 3-6% = 3; 1-3% = 2; under 1% = 1; 0% = 0.\n"
        "   Deduct 1 if a foot slides, a leg pops between frames, or no foot is ever planted. Never raise above the ceiling.\n\n"
        "3. scene - the setting and composition, judged on its own terms:\n"
        "   4 = layered depth (foreground, middle, background), deliberate palette, focal placement that leads the eye.\n"
        "   3 = two or three planes with a coherent palette and the animal placed with intent.\n"
        "   2 = a basic backdrop: sky and ground, no depth cues, default placement.\n"
        "   1 = accidental or cluttered.\n"
        "   0 = no scene at all.\n\n"
        "4. craft - start 4. Deduct 1 for EACH of:\n"
        "   - a visible seam, stray shape or orphaned element;\n"
        "   - inconsistent light or shadow direction;\n"
        "   - a clipped or cut-off element;\n"
        "   - banding, pixel mush or jagged edges;\n"
        "   - no contact shadow under the animal.\n\n"
        "Do not reward effort and give no credit for anything you cannot see.\n"
        "Reply with one JSON object only, no prose outside it:\n"
        '{"scores":{"anatomy":0,"gait":0,"scene":0,"craft":0},'
        '"rationale":{"anatomy":"the flaws you deducted for","gait":"the band and any deduction","scene":"what you deducted for","craft":"what you deducted for"},'
        '"verdict":"one sentence naming the strongest and weakest aspect"}'
    ),
    "design": (
        "This is a full-page screenshot (1280px wide) of a landing page. The brief was: a landing page for 'Dune Line', "
        "a fictional overnight desert train to a neon city, with nav, hero, three features, a four-departure timetable, "
        "three pricing tiers, a testimonial and a footer.\n"
        "Score each 0-10:\n- typography: type choice, scale, hierarchy.\n- layout: spacing, alignment, rhythm, no broken or overlapping elements.\n"
        "- colour: palette and contrast.\n- completeness: are all seven required sections present and well formed?\n"
        "- originality: distinctive taste versus a generic template."
    ),
    "vision": (
        "Image 1 is the ORIGINAL. Image 2 is a RECREATION attempt. Judge how exactly image 2 reproduces image 1.\n"
        "Score each 0-10:\n- subjects: are the same things present (three towers with a cyan ring on the tallest, red-cloaked traveller with an alpaca, "
        "neon-outlined saguaro, turquoise pool, monorail on a glowing track, crescent moon, searchlight beams, vertical OASIS sign)?\n"
        "- layout: is each thing in the same position in the frame?\n- colour: same palette, sky gradient and lighting?\n"
        "- style: same rendering style and level of detail?\n- overall: at a glance, could it be mistaken for the same picture?"
    ),
}
KEYS = {"alpaca": ["anatomy", "gait", "scene", "craft"],
        "design": ["typography", "layout", "colour", "completeness", "originality"],
        "vision": ["subjects", "layout", "colour", "style", "overall"]}


def judge(task, mid, images):
    p = RAW / "judge" / ("%s-%s.json" % (task, mid))
    old = load(p, {})
    content = [{"type": "text", "text": RUBRIC[task] + "\n\nBe strict and use the whole scale. Reply with one JSON object only: "
                + json.dumps({k: 0 for k in KEYS[task]})[:-1] + ', "note": "one sentence"}'}]
    content += [{"type": "image_url", "image_url": {"url": data_url(i)}} for i in images]
    for j in JUDGES:
        if j in old and "scores" in old[j]:
            continue
        r = post("/chat/completions", {"model": j, "messages": [{"role": "user", "content": content}],
                                       "max_completion_tokens": 8000,
                                       "venice_parameters": {"include_venice_system_prompt": False}})
        try:
            txt = r["choices"][0]["message"]["content"]
            d = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
            old[j] = {"scores": {k: max(0, min(10, float(d[k]))) for k in KEYS[task]}, "note": str(d.get("note", ""))[:300]}
        except Exception as e:
            old[j] = {"error": repr(e)[:200], "raw": str(r)[:300]}
        save(p, old)
    print("judged", task, mid, {j: old[j].get("scores") or old[j].get("error") for j in JUDGES}, flush=True)


def judge_alpaca(mid, images, motion):
    """Three blind judges, anchored 0-4 rubric, median per criterion. Motion readout is given to the judges."""
    p = RAW / "judge" / ("alpaca-%s.json" % mid)
    old = load(p, {}) or {}
    if old.get("rubric") != "v5":
        old = {"rubric": "v5"}
    m = motion or {}
    mtext = ("Measured motion between consecutive frames: %.2f%% of pixels change (leg band %.2f%%). "
             "Under 1%% means near-static; under 3%% means weak." % (m.get("changed_pct", 0), m.get("leg_pct", 0)))
    content = [{"type": "text", "text": RUBRIC["alpaca"] + "\n\n" + mtext}]
    content += [{"type": "image_url", "image_url": {"url": data_url(i)}} for i in images]
    for j in JUDGES_ALPACA:
        if j in old and "scores" in old[j]:
            continue
        ok = False
        for attempt in range(2):
            r = post("/chat/completions", {"model": j, "messages": [{"role": "user", "content": content}],
                                           "max_completion_tokens": 8000,
                                           "venice_parameters": {"include_venice_system_prompt": False}})
            try:
                txt = r["choices"][0]["message"]["content"]
                d = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
                sc = d.get("scores") or d
                old[j] = {"scores": {k: max(0, min(4, round(float(sc[k])))) for k in KEYS["alpaca"]},
                          "rationale": {k: str((d.get("rationale") or {}).get(k, ""))[:220] for k in KEYS["alpaca"]},
                          "verdict": str(d.get("verdict", ""))[:300]}
                ok = True
                break
            except Exception as e:
                old[j] = {"error": repr(e)[:200], "raw": str(r)[:300]}
        save(p, old)
    good = [v for v in old.values() if isinstance(v, dict) and "scores" in v]
    if good:
        med = {}
        for k in KEYS["alpaca"]:
            vals = sorted(v["scores"][k] for v in good)
            med[k] = vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2
        old["median"] = med
        old["judges_used"] = len(good)
        save(p, old)
    print("judged alpaca", mid, {j: old[j].get("scores") or old[j].get("error") for j in JUDGES_ALPACA}, flush=True)


def work(sp):
    mid = sp["id"]
    render(sp)
    tmp = RAW / "judge_in"
    fs = [SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(4)]
    if all(f.exists() for f in fs):
        judge_alpaca(mid, [jpeg(f, tmp / (f.stem + ".jpg"), 1024) for f in fs], motion_stats(mid))
    if ONLY_ALPACA:
        return
    d = SHOTS / ("design-%s.png" % mid)
    if d.exists():
        judge("design", mid, [jpeg(d, tmp / (d.stem + ".jpg"), 4000)])
    rc = SITE / "img" / "recon" / (mid + ".jpg")
    if rc.exists():
        judge("vision", mid, [SITE / "img" / "source.jpg", rc])


if __name__ == "__main__":
    import sys
    sp = load(RAW / "specs.json")
    argv = sys.argv[1:]
    if "--alpaca-only" in argv:
        ONLY_ALPACA = True
        argv = [a for a in argv if a != "--alpaca-only"]
    only = argv
    todo = [sp[m] for m in MODELS if not only or m in only]
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(work, todo))
    prev = load(RAW / "motion.json", {}) or {}
    prev.update({m: motion_stats(m) for m in (only or MODELS)})
    save(RAW / "motion.json", {m: prev.get(m) for m in MODELS})
    print("PHASE2 DONE", flush=True)
