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


def render(sp):
    mid = sp["id"]
    for task in ("alpaca", "design"):
        r = load(RAW / task / (mid + ".json"))
        if not r or r.get("error") or incomplete(r):
            continue
        html = SITE / "out" / task / (mid + ".html")
        html.write_text(extract_html(r["text"]))
        port = 9300 + MODELS.index(mid) * 2 + (task == "design")
        if task == "alpaca":
            if not (SHOTS / ("alpaca-%s-2.png" % mid)).exists():
                shot(html, SHOTS / ("alpaca-" + mid), "frames", port)
            if (SHOTS / ("alpaca-%s-1.png" % mid)).exists():
                jpeg(SHOTS / ("alpaca-%s-1.png" % mid), SITE / "img" / "alpaca" / (mid + ".jpg"), 960)
        else:
            p = SHOTS / ("design-%s.png" % mid)
            if not p.exists():
                shot(html, SHOTS / ("design-" + mid), "full", port)
            if p.exists():
                jpeg(p, SITE / "img" / "design" / (mid + ".jpg"), 6000)


def frames_differ(mid):
    """Objective motion check: mean absolute pixel difference between walk-cycle frames."""
    from PIL import Image, ImageChops, ImageStat
    fs = [SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(3)]
    if not all(f.exists() for f in fs):
        return None
    ims = [Image.open(f).convert("L").resize((320, 180)) for f in fs]
    return round(max(ImageStat.Stat(ImageChops.difference(ims[0], ims[i])).mean[0] for i in (1, 2)), 3)


RUBRIC = {
    "alpaca": ("These three images are consecutive moments (about 0.45s apart) from one animated HTML component. "
               "The brief was: a beautiful animated alpaca walking in a small tasteful scene, drawn in code.\n"
               "Score each 0-10:\n- alpaca: is it clearly and correctly an alpaca (long neck, fleece, small head, upright ears, four legs, sound anatomy)?\n"
               "- motion: do the legs and body change between frames in a way consistent with a believable walk? Identical frames = 0.\n"
               "- beauty: craft, colour, polish of the illustration.\n- scene: quality and taste of the surrounding scene and composition."),
    "design": ("This is a full-page screenshot (1280px wide) of a landing page. The brief was: a landing page for 'Dune Line', "
               "a fictional overnight desert train to a neon city, with nav, hero, three features, a four-departure timetable, "
               "three pricing tiers, a testimonial and a footer.\n"
               "Score each 0-10:\n- typography: type choice, scale, hierarchy.\n- layout: spacing, alignment, rhythm, no broken or overlapping elements.\n"
               "- colour: palette and contrast.\n- completeness: are all seven required sections present and well formed?\n"
               "- originality: distinctive taste versus a generic template."),
    "vision": ("Image 1 is the ORIGINAL. Image 2 is a RECREATION attempt. Judge how exactly image 2 reproduces image 1.\n"
               "Score each 0-10:\n- subjects: are the same things present (three towers with a cyan ring on the tallest, red-cloaked traveller with an alpaca, "
               "neon-outlined saguaro, turquoise pool, monorail on a glowing track, crescent moon, searchlight beams, vertical OASIS sign)?\n"
               "- layout: is each thing in the same position in the frame?\n- colour: same palette, sky gradient and lighting?\n"
               "- style: same rendering style and level of detail?\n- overall: at a glance, could it be mistaken for the same picture?"),
}
KEYS = {"alpaca": ["alpaca", "motion", "beauty", "scene"],
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


def work(sp):
    mid = sp["id"]
    render(sp)
    tmp = RAW / "judge_in"
    fs = [SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(3)]
    if all(f.exists() for f in fs):
        judge("alpaca", mid, [jpeg(f, tmp / (f.stem + ".jpg"), 1024) for f in fs])
    d = SHOTS / ("design-%s.png" % mid)
    if d.exists():
        judge("design", mid, [jpeg(d, tmp / (d.stem + ".jpg"), 4000)])
    rc = SITE / "img" / "recon" / (mid + ".jpg")
    if rc.exists():
        judge("vision", mid, [SITE / "img" / "source.jpg", rc])


if __name__ == "__main__":
    import sys
    sp = load(RAW / "specs.json")
    only = sys.argv[1:]
    todo = [sp[m] for m in MODELS if not only or m in only]
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(work, todo))
    prev = load(RAW / "motion.json", {}) or {}
    prev.update({m: frames_differ(m) for m in (only or MODELS)})
    save(RAW / "motion.json", {m: prev.get(m) for m in MODELS})
    print("PHASE2 DONE", flush=True)
